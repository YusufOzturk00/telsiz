"""Tests for game-only capture (process loopback) with a fake helper and process list."""

import io
import logging
import threading

import numpy as np
import pytest

from telsiz.audio.capture import CaptureFactory
from telsiz.audio.process_loopback import (
    HEADER,
    HELPER_ENV,
    MAGIC,
    ProcessLoopbackSource,
    ProcessLoopbackUnavailable,
    find_helper,
    unavailable_reason,
)
from telsiz.audio.processes import ProcessEntry, find_process, is_running, list_processes

RATE = 48000
CHANNELS = 2
CHUNK_FRAMES = 4800  # 0.1 s


# --- process list -------------------------------------------------------------------


def test_find_process_is_case_insensitive():
    processes = [ProcessEntry(4, 0, "System"), ProcessEntry(812, 600, "CS2.EXE")]

    assert find_process("cs2.exe", processes) == 812
    assert find_process("vlc.exe", processes) is None


def test_find_process_picks_the_root_of_a_process_tree():
    processes = [
        ProcessEntry(300, 200, "chrome.exe"),  # child of the root below
        ProcessEntry(200, 50, "chrome.exe"),  # root: its parent is explorer
        ProcessEntry(50, 1, "explorer.exe"),
        ProcessEntry(310, 200, "chrome.exe"),
    ]

    assert find_process("chrome.exe", processes) == 200


def test_is_running_checks_the_name_because_pids_are_reused():
    processes = [ProcessEntry(812, 1, "notepad.exe")]

    assert is_running(812, "notepad.exe", processes)
    assert not is_running(812, "cs2.exe", processes)
    assert not is_running(999, "notepad.exe", processes)


def test_list_processes_sees_this_python():
    import os
    import sys

    processes = list_processes()
    if sys.platform != "win32":
        assert processes == []
        return
    assert any(p.pid == os.getpid() and p.name.lower().startswith("python") for p in processes)


# --- fake helper --------------------------------------------------------------------


class BlockingPipe(io.RawIOBase):
    """Gives its data, then blocks like a live pipe until the process is terminated."""

    def __init__(self, data: bytes, closed: threading.Event, end_with_eof: bool):
        self._data = bytearray(data)
        self._closed = closed
        self._eof = end_with_eof

    def read(self, size=-1):
        if self._data:
            size = len(self._data) if size < 0 else size
            part = bytes(self._data[:size])
            del self._data[:size]
            return part
        if not self._eof:
            assert self._closed.wait(5), "the helper was never stopped"
        return b""


class FakeHelper:
    def __init__(self, stdout=b"", stderr=b"", code=0, live=True):
        self.terminated = threading.Event()
        self.stdout = BlockingPipe(stdout, self.terminated, end_with_eof=not live)
        self.stderr = io.BytesIO(stderr)
        self._code = code
        self._live = live

    def poll(self):
        if self._live and not self.terminated.is_set():
            return None
        return self._code

    def wait(self, timeout=None):
        if self._live:
            assert self.terminated.wait(timeout or 5)
        return self._code

    def terminate(self):
        self._code = 1 if self._live else self._code
        self.terminated.set()


def pcm(blocks):
    """Header plus ``blocks`` chunks of stereo int16, block i filled with value 1000*(i+1)."""
    body = b"".join(
        np.full((CHUNK_FRAMES, CHANNELS), 1000 * (i + 1), dtype="<i2").tobytes()
        for i in range(blocks)
    )
    return HEADER.pack(MAGIC, RATE, CHANNELS, 16, 0) + body


class World:
    """The process list as the source sees it; the test starts and closes the game."""

    def __init__(self, running=True):
        self.running = running
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return [ProcessEntry(77, 1, "cs2.exe")] if self.running else []


def make_source(world, helpers, **kwargs):
    spawned = []

    def spawn(args):
        spawned.append(list(args))
        return helpers.pop(0)

    source = ProcessLoopbackSource(
        helper="telsiz-loopback.exe",
        processes=world,
        spawn=spawn,
        poll_seconds=0.01,
        **kwargs,
    )
    return source, spawned


# --- ProcessLoopbackSource ----------------------------------------------------------


def test_streams_the_game_audio_as_float_chunks():
    world = World()
    helper = FakeHelper(pcm(3))
    source, spawned = make_source(world, [helper])

    chunks = []
    for chunk in source.chunks():
        chunks.append(chunk)
        if len(chunks) == 3:
            source.stop()

    assert spawned == [["telsiz-loopback.exe", "--pid", "77"]]
    assert [c.sample_rate for c in chunks] == [RATE] * 3
    assert all(c.samples.shape == (CHUNK_FRAMES, CHANNELS) for c in chunks)
    assert chunks[0].samples.dtype == np.float32
    assert chunks[1].samples[0, 0] == pytest.approx(2000 / 32768)
    assert helper.terminated.is_set()


def test_waits_for_the_game_and_reconnects_after_it_closes(caplog):
    caplog.set_level(logging.INFO, logger="telsiz")
    world = World(running=False)
    first, second = FakeHelper(pcm(1)), FakeHelper(pcm(1))
    source, spawned = make_source(world, [first, second])

    def start_game_later():
        while world.calls < 3:
            threading.Event().wait(0.005)
        world.running = True

    threading.Thread(target=start_game_later, daemon=True).start()
    seen = []
    for chunk in source.chunks():
        seen.append(chunk)
        if len(seen) == 1:
            world.running = False  # the game closes; the watcher stops the helper
        elif len(seen) == 2:
            world.running = True  # ...and starts again
        elif len(seen) == 3:
            source.stop()

    assert len(spawned) == 2
    assert first.terminated.is_set() and second.terminated.is_set()
    tail = seen[1]
    assert tail.sample_rate == RATE
    assert not tail.samples.any()  # silence ends the speech that was in progress
    assert "Waiting for cs2.exe to start" in caplog.text
    assert "cs2.exe closed" in caplog.text


def test_unsupported_windows_raises_unavailable():
    world = World()
    helper = FakeHelper(
        stderr=b"process loopback activation failed: 0x80070057", code=3, live=False
    )
    source, _ = make_source(world, [helper])

    with pytest.raises(ProcessLoopbackUnavailable, match="0x80070057"):
        list(source.chunks())


def test_helper_crash_is_a_runtime_error():
    world = World()
    helper = FakeHelper(pcm(1), stderr=b"capture failed", code=4, live=False)
    source, _ = make_source(world, [helper])

    with pytest.raises(RuntimeError, match="code 4: capture failed"):
        list(source.chunks())


def test_unknown_stream_format_is_rejected():
    world = World()
    helper = FakeHelper(HEADER.pack(b"NOPE", RATE, CHANNELS, 16, 0))
    source, _ = make_source(world, [helper])

    with pytest.raises(RuntimeError, match="unknown stream format"):
        list(source.chunks())
    assert helper.terminated.is_set()


def test_stop_while_waiting_for_the_game():
    world = World(running=False)
    source, spawned = make_source(world, [])
    threading.Timer(0.05, source.stop).start()

    assert list(source.chunks()) == []
    assert spawned == []


# --- helper discovery and support check ---------------------------------------------


def test_find_helper_uses_the_configured_path_only(tmp_path):
    exe = tmp_path / "telsiz-loopback.exe"
    exe.write_bytes(b"")

    assert find_helper(str(exe)) == exe
    assert find_helper(str(tmp_path / "missing.exe")) is None


def test_find_helper_looks_in_the_usual_places(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.delenv(HELPER_ENV, raising=False)
    installed = tmp_path / "telsiz" / "bin" / "telsiz-loopback.exe"
    installed.parent.mkdir(parents=True)
    installed.write_bytes(b"")

    found = find_helper()
    assert found is not None and found.is_file()

    custom = tmp_path / "custom.exe"
    custom.write_bytes(b"")
    monkeypatch.setenv(HELPER_ENV, str(custom))
    assert find_helper() == custom


@pytest.mark.parametrize(
    ("helper", "build", "expected"),
    [
        ("x.exe", 22631, None),
        ("x.exe", 19041, None),
        ("x.exe", 18363, "Windows 10 2004 or newer"),
        (None, 22631, "telsiz-loopback.exe was not found"),
        ("x.exe", None, "needs Windows"),
    ],
)
def test_unavailable_reason(helper, build, expected):
    reason = unavailable_reason(helper, build)
    if expected is None:
        assert reason is None
    else:
        assert expected in reason


# --- CaptureFactory -----------------------------------------------------------------


class Sentinel:
    def __init__(self, name):
        self.name = name

    def chunks(self):
        return iter(())

    def stop(self):
        pass


class RaisingGame:
    def __init__(self, helper, process_name):
        self.helper, self.process_name = helper, process_name

    def chunks(self):
        raise ProcessLoopbackUnavailable("activation failed: 0x80070057")
        yield  # pragma: no cover

    def stop(self):
        pass


def factory(mode="auto", helper="loop.exe", build=22631, game=None):
    return CaptureFactory(
        mode,
        "cs2.exe",
        find_helper=lambda configured: helper,
        build=lambda: build,
        system_source=lambda: Sentinel("system"),
        game_source=game or (lambda helper, name: Sentinel(f"game:{helper}:{name}")),
    )


def test_auto_listens_to_the_game_only():
    capture = factory()

    source = capture()
    assert capture.game_only
    assert source._source.name == "game:loop.exe:cs2.exe"
    assert capture.describe() == "Listening to cs2.exe only."


def test_system_mode_listens_to_everything():
    capture = factory(mode="system")

    assert capture().name == "system"
    assert not capture.game_only
    assert capture.fallback_reason is None
    assert capture.describe() == "Listening to all audio this PC plays."


@pytest.mark.parametrize(("helper", "build"), [(None, 22631), ("loop.exe", 18363)])
def test_auto_falls_back_to_system_audio_with_a_warning(helper, build, caplog):
    capture = factory(helper=helper, build=build)

    assert capture().name == "system"
    assert capture.fallback_reason
    assert "listening to all PC audio instead" in caplog.text


def test_falls_back_when_windows_refuses_process_loopback(caplog):
    capture = factory(game=RaisingGame)

    with pytest.raises(ProcessLoopbackUnavailable):
        list(capture().chunks())

    assert not capture.game_only
    assert capture().name == "system"  # the live runner's reconnect gets system audio
    assert "0x80070057" in caplog.text


def test_unknown_capture_mode_is_rejected():
    with pytest.raises(ValueError):
        factory(mode="game")
