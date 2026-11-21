"""Run the pipeline on a live audio source.

Two threads keep capture and processing apart: the capture thread only reads
audio and stamps each chunk with the wall-clock time it arrived; the worker
thread resamples, segments, transcribes and translates. A slow Whisper call
therefore delays the subtitles but never drops audio.

End-to-end latency is measured from the end of speech (utterance end minus
the VAD padding, mapped back to wall-clock time through the chunk stamps) to
the moment the event is published.

Subtitles that arrive long after the words were spoken are useless in a round.
When processing falls more than ``max_lag_s`` behind (a busy GPU, a long
recognition), the queued audio is skipped and processing resumes at live audio.
"""

from __future__ import annotations

import dataclasses
import logging
import math
import queue
import statistics
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Protocol

from telsiz.audio.base import AudioChunk
from telsiz.audio.resample import TARGET_RATE, Resampler, to_mono
from telsiz.events import VoiceEvent
from telsiz.vad import Utterance, UtteranceSegmenter

log = logging.getLogger(__name__)


class LiveSource(Protocol):
    def chunks(self) -> Iterator[AudioChunk]: ...

    def stop(self) -> None: ...


class UtteranceProcessor(Protocol):
    def process_utterance(self, utt: Utterance) -> VoiceEvent | None: ...


@dataclass(frozen=True)
class _Captured:
    chunk: AudioChunk
    at: float  # clock() when the chunk arrived (= wall time of its last sample)


_STOP = object()


def latency_summary(latencies: list[int]) -> dict[str, int]:
    if not latencies:
        return {"count": 0}
    ordered = sorted(latencies)
    p90 = ordered[max(0, math.ceil(0.9 * len(ordered)) - 1)]
    return {
        "count": len(ordered),
        "median_ms": round(statistics.median(ordered)),
        "p90_ms": p90,
        "max_ms": ordered[-1],
    }


class LiveRunner:
    def __init__(
        self,
        source_factory: Callable[[], LiveSource],
        pipeline: UtteranceProcessor,
        segmenter: UtteranceSegmenter,
        publish: Callable[[VoiceEvent], None],
        *,
        clock: Callable[[], float] = time.monotonic,
        retry_delay: float = 1.0,
        max_lag_s: float = 5.0,
    ) -> None:
        self._source_factory = source_factory
        self._pipeline = pipeline
        self._segmenter = segmenter
        self._publish = publish
        self._clock = clock
        self._retry_delay = retry_delay
        self._max_lag_s = max_lag_s
        self._pad_s = segmenter.options.speech_pad_ms / 1000

        self._queue: queue.Queue[object] = queue.Queue()
        self._stopping = threading.Event()
        self._source: LiveSource | None = None
        self._source_lock = threading.Lock()
        self._threads: list[threading.Thread] = []
        self.reconnects = 0
        self.latencies: list[int] = []
        self.skipped_s = 0.0  # audio skipped to catch up with live
        self.non_speech_clips = 0  # clips recognized but dropped (noise, hallucinations)
        self.non_speech_ms = 0  # time spent on those clips

    # --- lifecycle -------------------------------------------------------------------

    def start(self) -> None:
        self._threads = [
            threading.Thread(target=self._capture, name="telsiz-capture", daemon=True),
            threading.Thread(target=self._work, name="telsiz-worker", daemon=True),
        ]
        for thread in self._threads:
            thread.start()

    def stop(self, timeout: float = 30.0) -> None:
        """Stop capturing, finish the speech in progress and wait for both threads."""
        self._stopping.set()
        with self._source_lock:
            if self._source is not None:
                self._source.stop()
        for thread in self._threads:
            thread.join(timeout)

    def wait(self) -> None:
        """Block until the source ends (or stop() is called from another thread)."""
        for thread in self._threads:
            while thread.is_alive():
                thread.join(0.5)

    # --- capture thread ------------------------------------------------------------

    def _capture(self) -> None:
        try:
            while not self._stopping.is_set():
                source = self._source_factory()
                with self._source_lock:
                    self._source = source
                    if self._stopping.is_set():
                        source.stop()
                try:
                    for chunk in source.chunks():
                        self._queue.put(_Captured(chunk, self._clock()))
                    return  # the source ended (stopped, or a finite source)
                except (RuntimeError, OSError) as exc:
                    if self._stopping.is_set():
                        return
                    self.reconnects += 1
                    log.warning("Audio capture failed (%s); reconnecting", exc)
                    self._stopping.wait(self._retry_delay)
        finally:
            self._queue.put(_STOP)

    # --- worker thread -------------------------------------------------------------

    def _work(self) -> None:
        resampler: Resampler | None = None
        position = 0.0  # seconds of 16 kHz audio fed to the segmenter
        marks: deque[tuple[float, float]] = deque(maxlen=3000)  # (position, wall time)
        while True:
            item = self._queue.get()
            if item is _STOP:
                break
            assert isinstance(item, _Captured)
            if self._max_lag_s > 0 and self._lag_s(item) > self._max_lag_s:
                item = self._skip_to_live(item)
                if item is _STOP:
                    break
                assert isinstance(item, _Captured)
                self._segmenter.discard()
                resampler = None
            chunk = item.chunk
            if resampler is None or resampler.in_rate != chunk.sample_rate:
                resampler = Resampler(chunk.sample_rate)
            samples = resampler.process(to_mono(chunk))
            position += len(samples) / TARGET_RATE
            marks.append((position, item.at))
            for utt in self._segmenter.feed(samples):
                self._handle(utt, marks)
        for utt in self._segmenter.flush():
            self._handle(utt, marks)

    def _lag_s(self, item: _Captured) -> float:
        """How long ago the audio in ``item`` was captured."""
        return self._clock() - item.at

    def _skip_to_live(self, item: _Captured) -> object:
        """Drop everything queued; return the newest chunk (or _STOP)."""
        skipped = 0.0
        latest: object = item
        while True:
            try:
                nxt = self._queue.get_nowait()
            except queue.Empty:
                break
            assert isinstance(latest, _Captured)
            skipped += len(latest.chunk.samples) / latest.chunk.sample_rate
            latest = nxt
            if nxt is _STOP:
                break
        self.skipped_s += skipped
        log.warning(
            "Fell %.0f s behind live audio; skipped %.0f s so subtitles stay current",
            self._lag_s(item),
            skipped,
        )
        return latest

    def _handle(self, utt: Utterance, marks: deque[tuple[float, float]]) -> None:
        started = self._clock()
        try:
            event = self._pipeline.process_utterance(utt)
        except Exception:
            log.exception("Failed to process an utterance")
            return
        if event is None:
            spent = round((self._clock() - started) * 1000)
            self.non_speech_clips += 1
            self.non_speech_ms += spent
            log.debug("%.1f s clip was not speech (%d ms)", utt.duration, spent)
            return
        speech_end = _wall_time(max(utt.end - self._pad_s, utt.start), marks)
        if speech_end is not None:
            latency = max(0, round((self._clock() - speech_end) * 1000))
            event = dataclasses.replace(event, latency_ms=latency)
        self.latencies.append(event.latency_ms)
        timings = getattr(self._pipeline, "last_timings", {})
        log.info(
            "[%s] %d ms end-to-end (recognition %s ms, translation %s ms): %s",
            event.source_lang.upper(),
            event.latency_ms,
            timings.get("asr_ms", "?"),
            timings.get("translation_ms", "?"),
            event.original,
        )
        self._publish(event)


def _wall_time(position: float, marks: deque[tuple[float, float]]) -> float | None:
    """Wall-clock time at which stream ``position`` (seconds) was captured."""
    for end, at in marks:
        if end >= position:
            return at - (end - position)
    return marks[-1][1] if marks else None
