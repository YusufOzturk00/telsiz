"""Capture only the game's audio through Windows process loopback.

The capture itself runs in ``telsiz-loopback.exe`` (``native/process_loopback``), a
small helper built from source by CI. It asks the Windows audio engine for the sound
one process tree plays, the API OBS and Discord use; the game process is never
opened. This module finds the game in the process list, starts the helper, reads its
PCM stream and follows the game: when it closes, capture waits until it starts again.
"""

from __future__ import annotations

import logging
import os
import struct
import subprocess
import sys
import threading
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import IO, Protocol

import numpy as np

from telsiz.audio.base import AudioChunk
from telsiz.audio.processes import ProcessEntry, find_process, is_running, list_processes
from telsiz.paths import data_dir

log = logging.getLogger(__name__)

HELPER_NAME = "telsiz-loopback.exe"
HELPER_ENV = "TELSIZ_LOOPBACK_HELPER"
MIN_WINDOWS_BUILD = 19041  # Windows 10 2004

HEADER = struct.Struct("<4sIHHI")
MAGIC = b"TLSZ"
EXIT_UNAVAILABLE = 3
_TAIL_SECONDS = 1.0  # silence after the game closes, so the speech in progress ends


class ProcessLoopbackUnavailable(RuntimeError):
    """This Windows cannot capture a single application's audio."""


class HelperProcess(Protocol):
    stdout: IO[bytes] | None
    stderr: IO[bytes] | None

    def poll(self) -> int | None: ...

    def wait(self, timeout: float | None = None) -> int: ...

    def terminate(self) -> None: ...


def _spawn(args: Sequence[str]) -> HelperProcess:
    return subprocess.Popen(
        list(args),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def windows_build() -> int | None:
    if sys.platform != "win32":
        return None
    return sys.getwindowsversion().build


def helper_candidates(configured: str = "") -> list[Path]:
    """Places to look for the helper, in order."""
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured))
    if os.environ.get(HELPER_ENV):
        candidates.append(Path(os.environ[HELPER_ENV]))
    if getattr(sys, "frozen", False):  # packaged app: next to telsiz.exe
        candidates.append(Path(sys.executable).parent / HELPER_NAME)
    repo = Path(__file__).resolve().parents[3]  # source checkout
    build = repo / "native" / "process_loopback" / "build"
    candidates += [build / "Release" / HELPER_NAME, build / HELPER_NAME]
    candidates.append(data_dir() / "bin" / HELPER_NAME)
    return candidates


def find_helper(configured: str = "") -> Path | None:
    if configured:  # an explicit path must be right; do not silently use another exe
        path = Path(configured)
        return path if path.is_file() else None
    return next((p for p in helper_candidates() if p.is_file()), None)


def unavailable_reason(helper: Path | None, build: int | None) -> str | None:
    """Why game-only capture cannot work here, or None if it can be tried."""
    if build is None:
        return "game-only capture needs Windows"
    if build < MIN_WINDOWS_BUILD:
        return f"game-only capture needs Windows 10 2004 or newer (this is build {build})"
    if helper is None:
        return f"{HELPER_NAME} was not found (see native/process_loopback/README.md)"
    return None


def _read_exact(stream: IO[bytes], size: int) -> bytes:
    data = b""
    while len(data) < size:
        part = stream.read(size - len(data))
        if not part:
            break
        data += part
    return data


class ProcessLoopbackSource:
    """Audio of one program (default ``cs2.exe``) and its child processes."""

    def __init__(
        self,
        helper: Path,
        process_name: str = "cs2.exe",
        *,
        chunk_seconds: float = 0.1,
        poll_seconds: float = 2.0,
        processes: Callable[[], list[ProcessEntry]] = list_processes,
        spawn: Callable[[Sequence[str]], HelperProcess] = _spawn,
    ) -> None:
        self.helper = helper
        self.process_name = process_name
        self.chunk_seconds = chunk_seconds
        self._poll = poll_seconds
        self._processes = processes
        self._spawn = spawn
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._proc: HelperProcess | None = None
        self.pid: int | None = None

    def stop(self) -> None:
        """Thread-safe; ends ``chunks()`` promptly."""
        self._stop.set()
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                self._proc.terminate()

    def chunks(self) -> Iterator[AudioChunk]:
        waiting_logged = False
        while not self._stop.is_set():
            pid = find_process(self.process_name, self._processes())
            if pid is None:
                if not waiting_logged:
                    log.info("Waiting for %s to start...", self.process_name)
                    waiting_logged = True
                self._stop.wait(self._poll)
                continue
            waiting_logged = False
            self.pid = pid
            log.info("Listening to %s only (PID %d)", self.process_name, pid)
            rate = yield from self._capture(pid)
            self.pid = None
            if self._stop.is_set():
                return
            log.info("%s closed; waiting for it to start again", self.process_name)
            waiting_logged = True
            if rate:
                yield AudioChunk(np.zeros(int(rate * _TAIL_SECONDS), dtype=np.float32), rate)

    def _capture(self, pid: int) -> Iterator[AudioChunk]:
        """Stream one helper run. Returns the sample rate (0 if no audio came)."""
        proc = self._spawn([str(self.helper), "--pid", str(pid)])
        with self._lock:
            self._proc = proc
            if self._stop.is_set():
                proc.terminate()
        game_gone = threading.Event()
        watcher = threading.Thread(
            target=self._watch, args=(pid, proc, game_gone), name="telsiz-game-watch", daemon=True
        )
        watcher.start()
        try:
            assert proc.stdout is not None
            header = _read_exact(proc.stdout, HEADER.size)
            if len(header) < HEADER.size:
                self._raise_for_exit(proc, game_gone)
                return 0
            magic, rate, channels, bits, _ = HEADER.unpack(header)
            if magic != MAGIC or bits != 16 or channels < 1 or rate <= 0:
                raise RuntimeError(f"{HELPER_NAME} sent an unknown stream format")
            frame_bytes = 2 * channels
            block = max(1, int(rate * self.chunk_seconds)) * frame_bytes
            while True:
                data = _read_exact(proc.stdout, block)
                usable = len(data) - len(data) % frame_bytes
                if usable:
                    pcm = np.frombuffer(data[:usable], dtype="<i2").reshape(-1, channels)
                    yield AudioChunk(pcm.astype(np.float32) / 32768.0, rate)
                if len(data) < block:
                    break
            self._raise_for_exit(proc, game_gone)
            return rate
        finally:
            with self._lock:
                self._proc = None
            if proc.poll() is None:
                proc.terminate()
            proc.wait(timeout=5)
            game_gone.set()  # ends the watcher
            watcher.join(timeout=5)

    def _raise_for_exit(self, proc: HelperProcess, game_gone: threading.Event) -> None:
        """The helper's stream ended: fine if we stopped it, an error otherwise."""
        code = proc.wait(timeout=5)
        if self._stop.is_set() or game_gone.is_set():
            return
        error = proc.stderr.read().decode(errors="replace").strip() if proc.stderr else ""
        if code == EXIT_UNAVAILABLE:
            raise ProcessLoopbackUnavailable(error or "process loopback is not available")
        raise RuntimeError(f"{HELPER_NAME} exited with code {code}: {error or 'no details'}")

    def _watch(self, pid: int, proc: HelperProcess, game_gone: threading.Event) -> None:
        """Stop the helper when the game exits (the audio engine would just send silence)."""
        while not game_gone.wait(self._poll):
            if proc.poll() is not None:
                return
            try:
                running = is_running(pid, self.process_name, self._processes())
            except OSError:
                continue
            if not running:
                game_gone.set()
                proc.terminate()
                return
