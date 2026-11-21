"""Tests for the live runner (capture thread + processing thread)."""

import threading
import time

import numpy as np
import pytest

from telsiz.audio.base import AudioChunk
from telsiz.events import VoiceEvent
from telsiz.live import LiveRunner, latency_summary
from telsiz.vad import UtteranceSegmenter

RATE = 16000


class LoudnessDetector:
    frame_samples = 512

    def __call__(self, frames):
        blocks = frames.reshape(-1, self.frame_samples)
        return np.clip(np.sqrt(np.mean(blocks**2, axis=1)) * 10, 0, 1).astype(np.float32)


def speech_then_silence(speech_s=1.0, silence_s=1.0, chunk_s=0.1):
    rng = np.random.default_rng(0)
    chunks = []
    for _ in range(int(speech_s / chunk_s)):
        chunks.append((0.3 * rng.standard_normal(int(RATE * chunk_s))).astype(np.float32))
    for _ in range(int(silence_s / chunk_s)):
        chunks.append(np.zeros(int(RATE * chunk_s), np.float32))
    return chunks


class ScriptedSource:
    """Yields the given blocks, then waits until stopped (like a live device)."""

    def __init__(self, blocks, fail_first=False):
        self.blocks = blocks
        self.fail_first = fail_first
        self.stopped = threading.Event()

    def chunks(self):
        if self.fail_first:
            self.fail_first = False
            raise RuntimeError("device lost")
        for block in self.blocks:
            yield AudioChunk(block, RATE)
        self.stopped.wait(5)

    def stop(self):
        self.stopped.set()


class FakePipeline:
    def __init__(self):
        self.utterances = []

    def process_utterance(self, utt):
        self.utterances.append(utt)
        n = len(self.utterances)
        return VoiceEvent("en", 0.9, f"text {n}", f"metin {n}", "tr", 5, ts=1.0)


class ManualClock:
    """Each call returns the next tick; capture and publish times are predictable."""

    def __init__(self, step=0.1):
        self.now = 100.0
        self.step = step
        self.lock = threading.Lock()

    def __call__(self):
        with self.lock:
            self.now += self.step
            return self.now


def run_until(runner, published, count, timeout=5.0):
    done = threading.Event()
    runner_publish = runner._publish

    def publish(event):
        runner_publish(event)
        if len(published) >= count:
            done.set()

    runner._publish = publish
    runner.start()
    assert done.wait(timeout), f"only {len(published)} events published"
    runner.stop()


def make(source, clock=None, **kwargs):
    published = []
    runner = LiveRunner(
        source_factory=lambda: source,
        pipeline=FakePipeline(),
        segmenter=UtteranceSegmenter(LoudnessDetector()),
        publish=published.append,
        clock=clock or ManualClock(),
        retry_delay=0.01,
        **kwargs,
    )
    return runner, published


def test_utterances_become_published_events():
    blocks = speech_then_silence() + speech_then_silence()
    runner, published = make(ScriptedSource(blocks))

    run_until(runner, published, 2)

    assert [e.original for e in published] == ["text 1", "text 2"]


def test_latency_is_measured_from_the_end_of_speech():
    runner, published = make(ScriptedSource(speech_then_silence()))

    run_until(runner, published, 1)

    # Each capture and each publish advance the fake clock by 0.1 s, so the
    # latency is real, positive and covers the VAD's silence wait (~0.5 s).
    latency = published[0].latency_ms
    assert latency >= 400
    assert latency < 5000


def test_capture_errors_reconnect_to_the_device():
    source = ScriptedSource(speech_then_silence(), fail_first=True)
    runner, published = make(source)

    run_until(runner, published, 1)

    assert published[0].original == "text 1"
    assert runner.reconnects == 1


def test_stop_flushes_speech_in_progress():
    source = ScriptedSource(speech_then_silence(speech_s=1.0, silence_s=0.0))
    runner, published = make(source)

    runner.start()
    source.stopped.wait(0.5)
    runner.stop()

    assert [e.original for e in published] == ["text 1"]


def test_stop_without_start_is_harmless():
    runner, _ = make(ScriptedSource([]))

    runner.stop()


def test_latency_summary():
    summary = latency_summary([100, 200, 300, 400, 1000])

    assert summary == {"count": 5, "median_ms": 300, "p90_ms": 1000, "max_ms": 1000}


def test_latency_summary_empty():
    assert latency_summary([]) == {"count": 0}


@pytest.fixture(autouse=True)
def _no_thread_leaks():
    before = threading.active_count()
    yield
    assert threading.active_count() <= before + 1


# --- staying live -------------------------------------------------------------------


class SettableClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class SlowFirstPipeline(FakePipeline):
    """The first recognition blocks until released, like a GPU busy with the game."""

    def __init__(self):
        super().__init__()
        self.busy = threading.Event()
        self.release = threading.Event()

    def process_utterance(self, utt):
        if not self.utterances:
            self.busy.set()
            assert self.release.wait(5)
        return super().process_utterance(utt)


def test_falls_behind_then_skips_to_live_audio(caplog):
    clock = SettableClock()
    pipeline = SlowFirstPipeline()
    stopped = threading.Event()
    runners = []

    class Source:
        def chunks(self):
            for block in speech_then_silence():  # recognized slowly
                yield AudioChunk(block, RATE)
            assert pipeline.busy.wait(5)
            for block in speech_then_silence():  # queued meanwhile: stale by the time it is read
                yield AudioChunk(block, RATE)
            clock.now += 20
            pipeline.release.set()
            deadline = time.monotonic() + 5
            while runners[0].skipped_s == 0 and time.monotonic() < deadline:
                time.sleep(0.01)
            for block in speech_then_silence():  # live again
                yield AudioChunk(block, RATE)
            stopped.wait(5)

        def stop(self):
            stopped.set()

    published = []
    runner = LiveRunner(
        lambda: Source(),
        pipeline,
        UtteranceSegmenter(LoudnessDetector()),
        published.append,
        clock=clock,
        max_lag_s=5.0,
    )
    runners.append(runner)

    run_until(runner, published, 2)

    assert [e.original for e in published] == ["text 1", "text 2"]
    assert len(pipeline.utterances) == 2  # the stale speech was never recognized
    assert runner.skipped_s > 1.5
    assert "skipped" in caplog.text


class NoiseOnlyPipeline:
    def process_utterance(self, utt):
        return None


def test_clips_that_are_not_speech_are_counted():
    source = ScriptedSource(speech_then_silence())
    published = []
    runner = LiveRunner(
        lambda: source,
        NoiseOnlyPipeline(),
        UtteranceSegmenter(LoudnessDetector()),
        published.append,
        clock=ManualClock(),
    )

    runner.start()
    deadline = time.monotonic() + 5
    while runner.non_speech_clips == 0 and time.monotonic() < deadline:
        time.sleep(0.01)
    runner.stop()

    assert published == []
    assert runner.non_speech_clips == 1
    assert runner.non_speech_ms >= 0
