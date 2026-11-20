"""Shared test helpers (imported by tests; pytest puts tests/ on sys.path)."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np


def sine(freq: float, seconds: float, rate: int, amplitude: float = 0.5) -> np.ndarray:
    t = np.arange(int(seconds * rate)) / rate
    return (amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def write_wav(path: Path, samples: np.ndarray, rate: int, sampwidth: int = 2) -> Path:
    """Write float samples in [-1, 1] (shape (n,) or (n, channels)) as integer PCM."""
    data = samples if samples.ndim == 2 else samples[:, None]
    channels = data.shape[1]
    if sampwidth == 1:
        raw = np.clip(data * 127 + 128, 0, 255).astype(np.uint8).tobytes()
    elif sampwidth == 2:
        raw = np.clip(data * 32767, -32768, 32767).astype("<i2").tobytes()
    elif sampwidth == 3:
        ints = np.clip(data * 8388607, -8388608, 8388607).astype("<i4")
        raw = ints.reshape(-1, 1).view(np.uint8)[:, :3].tobytes()
    elif sampwidth == 4:
        raw = np.clip(data * 2147483647, -2147483648, 2147483647).astype("<i4").tobytes()
    else:
        raise ValueError(sampwidth)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sampwidth)
        w.setframerate(rate)
        w.writeframes(raw)
    return path
