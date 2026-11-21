"""Facts about this PC used to pick sensible defaults (read-only system queries)."""

from __future__ import annotations

import ctypes
import os
import sys
from dataclasses import dataclass
from typing import Any


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def total_ram_gb(kernel32: Any | None = None) -> float | None:
    """Installed memory in GiB (what Windows shows as "16 GB"), or None if unknown."""
    if kernel32 is None and sys.platform != "win32":
        try:
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
        except (AttributeError, ValueError, OSError):
            return None
    kernel32 = kernel32 or ctypes.windll.kernel32
    status = _MemoryStatusEx()
    status.dwLength = ctypes.sizeof(_MemoryStatusEx)
    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return status.ullTotalPhys / 1024**3


@dataclass(frozen=True)
class TranslationChoice:
    engine: str  # "nllb" | "argos"
    nllb_model: str | None
    reason: str


# Thresholds sit a little below 24 / 12 GB because Windows reports slightly less
# than the installed memory ("32 GB" -> ~31.7).
_BIG_PC_GB = 22.0
_MID_PC_GB = 11.0


def choose_translation(ram_gb: float | None) -> TranslationChoice:
    """Best translation engine that leaves the game enough memory.

    NLLB-1.3B needs ~1.6 GB of RAM, NLLB-600M ~0.8 GB and Argos ~0.4 GB.
    """
    if ram_gb is None:
        return TranslationChoice("argos", None, "memory size unknown -> Argos (lightest)")
    if ram_gb >= _BIG_PC_GB:
        return TranslationChoice("nllb", "nllb-1.3b", f"{ram_gb:.0f} GB RAM -> NLLB-1.3B")
    if ram_gb >= _MID_PC_GB:
        return TranslationChoice("nllb", "nllb-600m", f"{ram_gb:.0f} GB RAM -> NLLB-600M")
    return TranslationChoice("argos", None, f"{ram_gb:.0f} GB RAM -> Argos (lightest)")
