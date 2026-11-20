"""Per-user locations for downloaded models and settings."""

from __future__ import annotations

import os
from pathlib import Path


def data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home() / ".local" / "share"
    return root / "telsiz"


def models_dir() -> Path:
    return data_dir() / "models"
