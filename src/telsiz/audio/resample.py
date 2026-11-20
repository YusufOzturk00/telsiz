"""Convert captured audio to the 16 kHz mono float32 stream Whisper and Silero expect."""

from __future__ import annotations

import numpy as np
from scipy.signal import firwin, lfilter

from telsiz.audio.base import AudioChunk

TARGET_RATE = 16_000


def to_mono(chunk: AudioChunk) -> np.ndarray:
    """Average all channels into one float32 channel."""
    samples = np.asarray(chunk.samples, dtype=np.float32)
    if samples.ndim == 1:
        return samples
    return samples.mean(axis=1, dtype=np.float32)


class Resampler:
    """Streaming sample-rate converter.

    Downsampling first applies a low-pass FIR filter (to avoid aliasing), then
    linearly interpolates at the new rate. Filter state and the interpolation
    phase carry over between calls, so feeding audio in pieces gives the same
    result as feeding it all at once.
    """

    def __init__(self, in_rate: int, out_rate: int = TARGET_RATE, num_taps: int = 101) -> None:
        if in_rate <= 0 or out_rate <= 0:
            raise ValueError("Sample rates must be positive")
        self.in_rate = in_rate
        self.out_rate = out_rate
        self._step = in_rate / out_rate  # input samples per output sample
        self._taps: np.ndarray | None = None
        self._zi: np.ndarray | None = None
        if in_rate > out_rate:
            self._taps = firwin(num_taps, cutoff=0.45 * out_rate, fs=in_rate)
            self._zi = np.zeros(num_taps - 1)
        self._prev: float | None = None
        # Position of the next output sample, relative to index 0 of the next buffer.
        self._t = 0.0

    def process(self, samples: np.ndarray) -> np.ndarray:
        x = np.asarray(samples, dtype=np.float64)
        if self.in_rate == self.out_rate:
            return x.astype(np.float32)
        if x.size == 0:
            return np.zeros(0, dtype=np.float32)

        if self._taps is not None:
            x, self._zi = lfilter(self._taps, 1.0, x, zi=self._zi)

        buf = x if self._prev is None else np.concatenate(([self._prev], x))
        last = len(buf) - 1
        count = 0 if self._t > last else int(np.floor((last - self._t) / self._step)) + 1
        positions = self._t + self._step * np.arange(count)
        out = np.interp(positions, np.arange(len(buf)), buf)

        # The next buffer starts with the current last sample.
        self._t = self._t + self._step * count - last
        self._prev = float(buf[-1])
        return out.astype(np.float32)
