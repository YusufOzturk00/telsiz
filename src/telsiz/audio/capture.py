"""Choose the live audio source: the game only when possible, else all PC audio."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Protocol

from telsiz.audio.base import AudioChunk
from telsiz.audio.process_loopback import (
    ProcessLoopbackSource,
    ProcessLoopbackUnavailable,
    find_helper,
    unavailable_reason,
    windows_build,
)
from telsiz.config import CAPTURE_MODES

log = logging.getLogger(__name__)


class LiveSource(Protocol):
    def chunks(self) -> Iterator[AudioChunk]: ...

    def stop(self) -> None: ...


def _system_source() -> LiveSource:
    from telsiz.audio.system_loopback import SystemLoopbackSource

    return SystemLoopbackSource()


class _FallbackGuard:
    """Wraps the game source; if Windows refuses process loopback, switch to system audio."""

    def __init__(self, source: ProcessLoopbackSource, on_unavailable: Callable[[str], None]):
        self._source = source
        self._on_unavailable = on_unavailable

    def stop(self) -> None:
        self._source.stop()

    def chunks(self) -> Iterator[AudioChunk]:
        try:
            yield from self._source.chunks()
        except ProcessLoopbackUnavailable as exc:
            self._on_unavailable(str(exc))
            raise  # the live runner reconnects, and the next source is system audio


class CaptureFactory:
    """Called by the live runner for each (re)connection; returns a fresh source.

    ``auto`` captures only ``process_name`` through process loopback and falls back to
    all PC audio (WASAPI system loopback) when this Windows or setup cannot do that.
    """

    def __init__(
        self,
        mode: str = "auto",
        process_name: str = "cs2.exe",
        helper_path: str = "",
        *,
        find_helper: Callable[[str], Path | None] = find_helper,
        build: Callable[[], int | None] = windows_build,
        system_source: Callable[[], LiveSource] = _system_source,
        game_source: Callable[[Path, str], ProcessLoopbackSource] = ProcessLoopbackSource,
    ) -> None:
        if mode not in CAPTURE_MODES:
            raise ValueError(f"capture mode must be one of {CAPTURE_MODES}")
        self.process_name = process_name
        self._system_source = system_source
        self._game_source = game_source
        self._helper: Path | None = None
        self.fallback_reason: str | None = None
        if mode == "auto":
            self._helper = find_helper(helper_path)
            reason = unavailable_reason(self._helper, build())
            if reason:
                self._fall_back(reason)

    @property
    def game_only(self) -> bool:
        return self._helper is not None and self.fallback_reason is None

    def describe(self) -> str:
        if self.game_only:
            return f"Listening to {self.process_name} only."
        return "Listening to all audio this PC plays."

    def _fall_back(self, reason: str) -> None:
        self.fallback_reason = reason
        log.warning("%s; listening to all PC audio instead", reason)

    def __call__(self) -> LiveSource:
        if self.game_only:
            assert self._helper is not None
            return _FallbackGuard(
                self._game_source(self._helper, self.process_name), self._fall_back
            )
        return self._system_source()
