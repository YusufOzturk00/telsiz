"""Tests for the utterance segmenter (with a fake speech detector)."""

import numpy as np
import pytest

from telsiz.vad import SegmenterOptions, Utterance, UtteranceSegmenter

RATE = 16000


class EnergyDetector:
    """Fake detector: a frame is speech when it is loud."""

    frame_samples = 512

    def __call__(self, frames: np.ndarray) -> np.ndarray:
        blocks = frames.reshape(-1, self.frame_samples)
        rms = np.sqrt(np.mean(blocks**2, axis=1))
        return np.clip(rms * 10, 0.0, 1.0).astype(np.float32)


def build(*parts: tuple[str, float]) -> np.ndarray:
    """Concatenate ("speech" | "silence" | "quiet", seconds) parts into a signal."""
    rng = np.random.default_rng(0)
    out = []
    for kind, seconds in parts:
        n = int(seconds * RATE)
        if kind == "speech":
            out.append((0.3 * rng.standard_normal(n)).astype(np.float32))
        elif kind == "quiet":  # borderline frame: low but non-zero probability
            out.append((0.03 * rng.standard_normal(n)).astype(np.float32))
        else:
            out.append(np.zeros(n, dtype=np.float32))
    return np.concatenate(out)


def segment(signal: np.ndarray, **options) -> list[Utterance]:
    seg = UtteranceSegmenter(EnergyDetector(), SegmenterOptions(**options))
    return seg.feed(signal) + seg.flush()


def test_silence_produces_no_utterances():
    assert segment(build(("silence", 3.0))) == []


def test_single_burst_becomes_one_padded_utterance():
    [utt] = segment(build(("silence", 1.0), ("speech", 1.0), ("silence", 1.5)))

    assert utt.start == pytest.approx(0.8, abs=0.07)  # 200 ms pre-roll
    assert utt.end == pytest.approx(2.2, abs=0.07)  # 200 ms tail
    assert utt.duration == pytest.approx(len(utt.audio) / RATE)
    assert utt.audio.dtype == np.float32


def test_long_pause_splits_into_two_utterances():
    utts = segment(
        build(
            ("silence", 0.5), ("speech", 1.0), ("silence", 1.0), ("speech", 1.0), ("silence", 1.0)
        )
    )

    assert len(utts) == 2
    assert utts[1].start > utts[0].end


def test_short_pause_does_not_split():
    utts = segment(
        build(
            ("silence", 0.5), ("speech", 1.0), ("silence", 0.2), ("speech", 1.0), ("silence", 1.0)
        )
    )

    assert len(utts) == 1


def test_short_blip_is_dropped():
    assert segment(build(("silence", 1.0), ("speech", 0.1), ("silence", 1.0))) == []


def test_long_speech_is_split_at_max_length():
    utts = segment(build(("speech", 25.0), ("silence", 1.0)), max_utterance_s=10.0)

    assert len(utts) == 3
    assert all(u.duration <= 10.0 + 1e-6 for u in utts)
    assert sum(u.duration for u in utts) == pytest.approx(25.2, abs=0.1)


def test_forced_split_prefers_a_quiet_moment():
    # 8 s speech, a brief quiet dip (too short to end the utterance), 4 s speech.
    signal = build(("speech", 8.0), ("quiet", 0.15), ("speech", 4.0), ("silence", 1.0))

    first, second = segment(signal, max_utterance_s=10.0)[:2]

    assert first.end == pytest.approx(8.07, abs=0.15)
    assert second.start == pytest.approx(first.end, abs=1e-6)


def test_flush_emits_speech_still_in_progress():
    seg = UtteranceSegmenter(EnergyDetector())

    assert seg.feed(build(("silence", 0.5), ("speech", 1.0))) == []
    [utt] = seg.flush()

    assert utt.end == pytest.approx(1.5, abs=0.07)


def test_feeding_in_pieces_matches_one_call():
    signal = build(
        ("silence", 0.7), ("speech", 1.3), ("silence", 0.9), ("speech", 2.1), ("silence", 0.6)
    )
    whole = segment(signal)

    seg = UtteranceSegmenter(EnergyDetector())
    pieces = []
    rng = np.random.default_rng(1)
    pos = 0
    while pos < len(signal):
        step = int(rng.integers(1, 3000))
        pieces += seg.feed(signal[pos : pos + step])
        pos += step
    pieces += seg.flush()

    assert [(u.start, u.end) for u in pieces] == [(u.start, u.end) for u in whole]
    for a, b in zip(pieces, whole, strict=True):
        np.testing.assert_array_equal(a.audio, b.audio)


def test_silero_detector_scores_frames():
    pytest.importorskip("faster_whisper")
    from telsiz.vad import SileroDetector

    detector = SileroDetector()
    probs = detector(np.zeros(detector.frame_samples * 4, dtype=np.float32))

    assert probs.shape == (4,)
    assert np.all(probs < 0.5)
