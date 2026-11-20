"""Read PCM ``.wav`` files, for tests and offline demos."""

from __future__ import annotations

import wave
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from telsiz.audio.base import AudioChunk


def _pcm_to_float(raw: bytes, sampwidth: int, channels: int) -> np.ndarray:
    if sampwidth == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif sampwidth == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif sampwidth == 3:
        packed = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        widened = np.zeros((len(packed), 4), dtype=np.uint8)
        widened[:, 1:] = packed  # little-endian: shift the 24-bit value into the top bytes
        data = widened.view("<i4").ravel().astype(np.float32) / 2147483648.0
    elif sampwidth == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth} bytes")
    return data.reshape(-1, channels)


class FileSource:
    """Yields a WAV file in fixed-length chunks, shaped ``(frames, channels)``."""

    def __init__(self, path: str | Path, chunk_seconds: float = 0.5) -> None:
        self.path = Path(path)
        self.chunk_seconds = chunk_seconds

    def chunks(self) -> Iterator[AudioChunk]:
        with wave.open(str(self.path), "rb") as wav:
            rate = wav.getframerate()
            channels = wav.getnchannels()
            sampwidth = wav.getsampwidth()
            frames_per_chunk = max(1, int(rate * self.chunk_seconds))
            while True:
                raw = wav.readframes(frames_per_chunk)
                if not raw:
                    break
                yield AudioChunk(_pcm_to_float(raw, sampwidth, channels), rate)
