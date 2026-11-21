"""Find a running program by its exe name, from the system's process list.

This only *reads the list* Windows keeps of running programs (a Toolhelp snapshot,
the same list Task Manager shows). No process is ever opened: there is no
``OpenProcess`` call, so the game is never touched. psutil is deliberately not used
because it opens processes to read their exe path.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessEntry:
    pid: int
    parent_pid: int
    name: str  # exe file name, e.g. "cs2.exe"


_TH32CS_SNAPPROCESS = 0x00000002
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
_MAX_PATH = 260


class _ProcessEntry32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * _MAX_PATH),
    ]


def list_processes() -> list[ProcessEntry]:
    """Snapshot of running programs (PID, parent PID, exe name). Empty off Windows."""
    if sys.platform != "win32":
        return []
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry32W)]
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry32W)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    snapshot = kernel32.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
    if not snapshot or snapshot == _INVALID_HANDLE_VALUE:
        raise OSError(ctypes.get_last_error(), "Could not list running programs")
    entries: list[ProcessEntry] = []
    try:
        entry = _ProcessEntry32W()
        entry.dwSize = ctypes.sizeof(_ProcessEntry32W)
        ok = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            entries.append(
                ProcessEntry(entry.th32ProcessID, entry.th32ParentProcessID, entry.szExeFile)
            )
            ok = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return entries


def find_process(name: str, processes: list[ProcessEntry]) -> int | None:
    """PID of the program called ``name`` (case-insensitive), or None.

    Programs such as browsers run several processes with the same name; the one whose
    parent is not one of them is the root, and capturing its process tree covers all.
    """
    wanted = name.casefold()
    matches = [p for p in processes if p.name.casefold() == wanted]
    if not matches:
        return None
    pids = {p.pid for p in matches}
    roots = [p for p in matches if p.parent_pid not in pids]
    return min(roots or matches, key=lambda p: p.pid).pid


def is_running(pid: int, name: str, processes: list[ProcessEntry]) -> bool:
    """Whether ``pid`` still belongs to ``name`` (PIDs are reused after a program exits)."""
    wanted = name.casefold()
    return any(p.pid == pid and p.name.casefold() == wanted for p in processes)
