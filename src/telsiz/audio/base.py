"""Audio source protocol shared by file, system-loopback and process-loopback capture."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class AudioChunk:
    """A block of audio.

    ``samples`` is float32 in [-1, 1], shaped ``(frames,)`` or ``(frames, channels)``.
    """

    samples: np.ndarray
    sample_rate: int


class AudioSource(Protocol):
    def chunks(self) -> Iterator[AudioChunk]:
        """Yield audio chunks until the source ends."""
        ...
