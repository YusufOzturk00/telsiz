"""Capture everything the PC plays through WASAPI loopback (PyAudioWPatch).

This is the same operating-system API OBS and Discord use for desktop audio;
it never touches the game process.

WASAPI loopback delivers *no* data while nothing is playing. Left alone, the
VAD would never see the silence that ends an utterance and a blocking read
could not be stopped. So the stream is polled, and when the device has been
quiet for longer than two chunks, silent chunks are generated to keep the
stream in step with the wall clock.
"""

from __future__ import annotations

import importlib
import threading
import time
from collections.abc import Callable, Iterator
from types import ModuleType
from typing import Any

import numpy as np

from telsiz.audio.base import AudioChunk


class SystemLoopbackSource:
    def __init__(
        self,
        chunk_seconds: float = 0.1,
        pyaudio_module: ModuleType | Any | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        poll_seconds: float = 0.01,
    ) -> None:
        self.chunk_seconds = chunk_seconds
        self._module = pyaudio_module
        self._clock = clock
        self._sleep = sleep
        self._poll = poll_seconds
        self._stop = threading.Event()
        self._started_at: float | None = None
        self.device_name: str | None = None

    @property
    def elapsed_seconds(self) -> float:
        return 0.0 if self._started_at is None else self._clock() - self._started_at

    def stop(self) -> None:
        """Thread-safe; ends ``chunks()`` within one poll interval."""
        self._stop.set()

    def chunks(self) -> Iterator[AudioChunk]:
        module = self._module or importlib.import_module("pyaudiowpatch")
        audio = module.PyAudio()
        try:
            try:
                device = audio.get_default_wasapi_loopback()
            except (OSError, LookupError) as exc:
                raise RuntimeError(
                    "No WASAPI loopback device found for the default speakers/headset"
                ) from exc
            rate = int(device["defaultSampleRate"])
            channels = int(device["maxInputChannels"])
            frames = max(1, int(rate * self.chunk_seconds))
            self.device_name = str(device["name"])
            stream = audio.open(
                format=module.paFloat32,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=int(device["index"]),
                frames_per_buffer=frames,
            )
            try:
                yield from self._read_loop(stream, rate, channels, frames)
            finally:
                stream.stop_stream()
                stream.close()
        finally:
            audio.terminate()

    def _read_loop(
        self, stream: Any, rate: int, channels: int, frames: int
    ) -> Iterator[AudioChunk]:
        self._started_at = self._clock()
        emitted = 0
        while not self._stop.is_set():
            if stream.get_read_available() >= frames:
                data = stream.read(frames, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.float32).reshape(-1, channels).copy()
                emitted += len(samples)
                yield AudioChunk(samples, rate)
                continue
            behind = (self._clock() - self._started_at) * rate - emitted
            if behind >= 2 * frames:
                emitted += frames
                yield AudioChunk(np.zeros((frames, channels), dtype=np.float32), rate)
            else:
                self._sleep(self._poll)
