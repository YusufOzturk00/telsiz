"""Voice activity detection: cut the 16 kHz stream into speech utterances."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Protocol

import numpy as np

SAMPLE_RATE = 16_000


class SpeechDetector(Protocol):
    """Scores fixed-size frames with a speech probability in [0, 1]."""

    frame_samples: int

    def __call__(self, frames: np.ndarray) -> np.ndarray:
        """``frames`` has a length that is a multiple of ``frame_samples``."""
        ...


class SileroDetector:
    """Silero VAD (MIT), using the ONNX model bundled with faster-whisper."""

    frame_samples = 512

    def __init__(self) -> None:
        from faster_whisper.vad import get_vad_model

        self._model = get_vad_model()

    def __call__(self, frames: np.ndarray) -> np.ndarray:
        probs = self._model(np.ascontiguousarray(frames, dtype=np.float32))
        return np.asarray(probs, dtype=np.float32).ravel()


@dataclass(frozen=True)
class Utterance:
    audio: np.ndarray  # 16 kHz mono float32
    start: float  # seconds since the stream started
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class SegmenterOptions:
    threshold: float = 0.5
    min_silence_ms: int = 500
    speech_pad_ms: int = 200
    min_speech_ms: int = 250
    max_utterance_s: float = 6.0  # long speech shows up sooner; split at a quiet moment

    @property
    def neg_threshold(self) -> float:
        """Below this a frame counts as silence (hysteresis, as in Silero's own helper)."""
        return max(self.threshold - 0.15, 0.01)


class UtteranceSegmenter:
    """Groups speech frames into utterances.

    An utterance ends after ``min_silence_ms`` of silence and keeps
    ``speech_pad_ms`` of audio on both sides. Utterances with less than
    ``min_speech_ms`` of speech are dropped. Utterances longer than
    ``max_utterance_s`` are split, preferably at a quiet moment.
    """

    def __init__(
        self,
        detector: SpeechDetector,
        options: SegmenterOptions | None = None,
        sample_rate: int = SAMPLE_RATE,
    ) -> None:
        self._detector = detector
        self._opts = options or SegmenterOptions()
        self._rate = sample_rate
        self._frame = detector.frame_samples
        frame_ms = 1000 * self._frame / sample_rate
        self._pad_frames = round(self._opts.speech_pad_ms / frame_ms)
        self._min_silence_frames = math.ceil(self._opts.min_silence_ms / frame_ms)
        self._min_speech_frames = math.ceil(self._opts.min_speech_ms / frame_ms)
        self._max_frames = int(self._opts.max_utterance_s * sample_rate / self._frame)

        self._pending = np.zeros(0, dtype=np.float32)  # samples not yet scored
        self._next_sample = 0  # stream position of the next scored frame
        self._preroll: deque[np.ndarray] = deque(maxlen=self._pad_frames or None)
        self._reset_utterance()

    @property
    def options(self) -> SegmenterOptions:
        return self._opts

    def _reset_utterance(self) -> None:
        self._frames: list[np.ndarray] = []
        self._probs: list[float] = []
        self._start_sample = 0
        self._silence_run = 0
        self._in_speech = False

    def feed(self, samples: np.ndarray) -> list[Utterance]:
        data = np.concatenate([self._pending, np.asarray(samples, dtype=np.float32)])
        usable = len(data) - len(data) % self._frame
        self._pending = data[usable:]
        if usable == 0:
            return []
        probs = self._detector(data[:usable])
        out: list[Utterance] = []
        for i, prob in enumerate(probs):
            frame = data[i * self._frame : (i + 1) * self._frame]
            out.extend(self._on_frame(frame, float(prob)))
        return out

    def flush(self) -> list[Utterance]:
        out: list[Utterance] = []
        if self._in_speech:
            if len(self._pending):
                self._frames.append(self._pending)
            keep = len(self._frames) - max(self._silence_run - self._pad_frames, 0)
            out.extend(self._emit(keep))
        self._pending = np.zeros(0, dtype=np.float32)
        self._preroll.clear()
        self._reset_utterance()
        return out

    def discard(self) -> None:
        """Forget the speech in progress (used when audio is skipped to catch up)."""
        self._pending = np.zeros(0, dtype=np.float32)
        self._preroll.clear()
        self._reset_utterance()

    def _on_frame(self, frame: np.ndarray, prob: float) -> list[Utterance]:
        position = self._next_sample
        self._next_sample += len(frame)
        opts = self._opts

        if not self._in_speech:
            if prob >= opts.threshold:
                self._in_speech = True
                self._frames = [*self._preroll, frame]
                self._probs = [0.0] * len(self._preroll) + [prob]
                self._start_sample = position - len(self._preroll) * self._frame
                self._preroll.clear()
            elif self._pad_frames:
                self._preroll.append(frame)
            return []

        self._frames.append(frame)
        self._probs.append(prob)
        if prob >= opts.threshold:
            self._silence_run = 0
        elif prob < opts.neg_threshold:
            self._silence_run += 1

        if self._silence_run >= self._min_silence_frames:
            keep = len(self._frames) - self._silence_run + self._pad_frames
            leftover = self._frames[keep:]
            out = self._emit(keep)
            self._reset_utterance()
            self._preroll.extend(leftover)
            return out

        if len(self._frames) >= self._max_frames:
            return self._split_long_utterance()
        return []

    def _split_long_utterance(self) -> list[Utterance]:
        probs = np.asarray(self._probs)
        window_start = int(len(probs) * 0.7)
        smoothed = np.convolve(probs, np.ones(3) / 3, mode="same")
        dip = window_start + int(np.argmin(smoothed[window_start:]))
        cut = dip if smoothed[dip] < self._opts.threshold else len(self._frames)

        out = self._emit(cut)
        rest_frames, rest_probs = self._frames[cut:], self._probs[cut:]
        self._start_sample += cut * self._frame
        self._frames, self._probs = rest_frames, rest_probs
        self._silence_run = 0
        if not self._frames:
            self._in_speech = False
        return out

    def _emit(self, keep: int) -> list[Utterance]:
        frames = self._frames[:keep]
        voiced = sum(p >= self._opts.threshold for p in self._probs[:keep])
        if not frames or voiced < self._min_speech_frames:
            return []
        audio = np.concatenate(frames)
        start = self._start_sample / self._rate
        return [Utterance(audio=audio, start=start, end=start + len(audio) / self._rate)]
