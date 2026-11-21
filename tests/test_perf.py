"""Tests for keeping Telsiz in the background while a game runs."""

import sys

import pytest

from telsiz.perf import set_process_priority


class FakeKernel32:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def GetCurrentProcess(self):  # noqa: N802 (Win32 name)
        return -1

    def SetPriorityClass(self, handle, priority_class):  # noqa: N802 (Win32 name)
        self.calls.append((handle, priority_class))
        return 1 if self.ok else 0


def test_below_normal_lowers_only_our_own_process():
    kernel32 = FakeKernel32()

    assert set_process_priority("below_normal", kernel32=kernel32) is True
    assert kernel32.calls == [(-1, 0x4000)]  # current-process pseudo handle, BELOW_NORMAL


def test_idle_priority_class():
    kernel32 = FakeKernel32()

    set_process_priority("idle", kernel32=kernel32)

    assert kernel32.calls == [(-1, 0x40)]


def test_normal_priority_changes_nothing():
    kernel32 = FakeKernel32()

    assert set_process_priority("normal", kernel32=kernel32) is False
    assert kernel32.calls == []


def test_failed_call_is_reported():
    assert set_process_priority("below_normal", kernel32=FakeKernel32(ok=False)) is False


def test_unknown_priority_is_rejected():
    with pytest.raises(ValueError):
        set_process_priority("realtime", kernel32=FakeKernel32())


@pytest.mark.skipif(sys.platform != "win32", reason="Windows priority classes")
def test_really_lowers_the_priority_on_windows():
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32")
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.GetPriorityClass.argtypes = [wintypes.HANDLE]
    kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    me = kernel32.GetCurrentProcess()
    before = kernel32.GetPriorityClass(me)
    try:
        assert set_process_priority("below_normal") is True
        assert kernel32.GetPriorityClass(me) == 0x4000
    finally:
        kernel32.SetPriorityClass(me, before)
