"""Keep Telsiz in the background so the game keeps its frame rate.

Only Telsiz's own process is changed: its Windows priority class is lowered
so the scheduler prefers the game when both want the CPU. Nothing touches the
game process (CLAUDE.md section 2).
"""

from __future__ import annotations

import ctypes
import logging
import sys
from typing import Any

log = logging.getLogger(__name__)

PRIORITY_CLASSES = {
    "normal": None,  # leave as is
    "below_normal": 0x4000,  # BELOW_NORMAL_PRIORITY_CLASS
    "idle": 0x40,  # IDLE_PRIORITY_CLASS
}


def _kernel32() -> Any:
    """kernel32 with real HANDLE types.

    Without them ctypes passes the pseudo-handle from GetCurrentProcess() as a 32-bit
    int, which 64-bit Windows does not accept, and SetPriorityClass fails.
    """
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.GetCurrentProcess.argtypes = []
    kernel32.SetPriorityClass.restype = wintypes.BOOL
    kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    return kernel32


def set_process_priority(level: str, kernel32: Any | None = None) -> bool:
    """Lower this process's priority. Returns True when it was changed."""
    if level not in PRIORITY_CLASSES:
        raise ValueError(f"Unknown priority {level!r}; use one of {sorted(PRIORITY_CLASSES)}")
    priority_class = PRIORITY_CLASSES[level]
    if priority_class is None:
        return False
    if kernel32 is None:
        if sys.platform != "win32":
            return False
        kernel32 = _kernel32()
    if not kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), priority_class):
        log.warning("Could not lower Telsiz's process priority")
        return False
    log.info("Telsiz runs at %s priority so the game comes first", level.replace("_", " "))
    return True
