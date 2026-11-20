"""Settings loaded from ``config.toml`` (see ``config.example.toml``)."""

from __future__ import annotations

import dataclasses
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from telsiz.asr import DEFAULT_PROMPTS
from telsiz.filters import FilterOptions
from telsiz.vad import SegmenterOptions

DEVICES = ("auto", "cuda", "cpu")
ENGINES = ("argos",)
SAME_LANGUAGE_MODES = ("show", "hide")


@dataclass(frozen=True)
class AsrConfig:
    model: str = "small"
    device: str = "auto"
    compute_type: str = "auto"
    beam_size: int = 5
    prompts: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_PROMPTS))


@dataclass(frozen=True)
class LanguageConfig:
    min_confidence: float = 0.6
    min_duration_s: float = 1.2
    sticky_window_s: float = 30.0


@dataclass(frozen=True)
class ServerConfig:
    port: int = 8765
    open_browser: bool = True  # open the subtitle page when --live starts


@dataclass(frozen=True)
class GlossaryConfig:
    enabled: bool = True
    path: str = ""  # empty: the bundled data/glossary.toml


@dataclass(frozen=True)
class TranslateConfig:
    engine: str = "argos"
    device: str = "cpu"


@dataclass(frozen=True)
class Config:
    target_lang: str = "tr"
    allowed_source_langs: list[str] = field(
        default_factory=lambda: ["en", "ru", "uk", "pl", "de", "tr"]
    )
    same_language: str = "show"  # show the original text, or hide it
    asr: AsrConfig = field(default_factory=AsrConfig)
    language: LanguageConfig = field(default_factory=LanguageConfig)
    vad: SegmenterOptions = field(default_factory=SegmenterOptions)
    filter: FilterOptions = field(default_factory=FilterOptions)
    translate: TranslateConfig = field(default_factory=TranslateConfig)
    glossary: GlossaryConfig = field(default_factory=GlossaryConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


_SECTIONS: dict[str, type] = {
    "asr": AsrConfig,
    "language": LanguageConfig,
    "vad": SegmenterOptions,
    "filter": FilterOptions,
    "translate": TranslateConfig,
    "glossary": GlossaryConfig,
    "server": ServerConfig,
}


def _coerce(name: str, default: Any, value: Any) -> Any:
    if isinstance(default, bool) or default is None:
        return value
    if isinstance(default, float) and isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, type(default)):
        raise ValueError(f"Setting {name} must be {type(default).__name__}, got {value!r}")
    return value


def _build(cls: type, data: dict[str, Any], prefix: str) -> Any:
    defaults = cls()
    known = {f.name for f in dataclasses.fields(cls)}
    values: dict[str, Any] = {}
    for key, value in data.items():
        name = f"{prefix}{key}"
        if key not in known:
            raise ValueError(f"Unknown setting {name}")
        current = getattr(defaults, key)
        if cls is Config and key in _SECTIONS:
            if not isinstance(value, dict):
                raise ValueError(f"[{key}] must be a table")
            values[key] = _build(_SECTIONS[key], value, f"{key}.")
        elif cls is AsrConfig and key == "prompts":
            if not isinstance(value, dict):
                raise ValueError(f"[{name}] must be a table")
            values[key] = {**current, **{str(k): str(v) for k, v in value.items()}}
        else:
            values[key] = _coerce(name, current, value)
    return dataclasses.replace(defaults, **values)


def validate(config: Config) -> Config:
    if not config.allowed_source_langs:
        raise ValueError("allowed_source_langs must not be empty")
    if config.same_language not in SAME_LANGUAGE_MODES:
        raise ValueError(f"same_language must be one of {SAME_LANGUAGE_MODES}")
    if config.translate.engine not in ENGINES:
        raise ValueError(f"translate.engine must be one of {ENGINES}")
    for name, device in (
        ("asr.device", config.asr.device),
        ("translate.device", config.translate.device),
    ):
        if device not in DEVICES:
            raise ValueError(f"{name} must be one of {DEVICES}")
    if not 1024 <= config.server.port <= 65535:
        raise ValueError("server.port must be between 1024 and 65535")
    return config


def load_config(path: Path | str | None) -> Config:
    """Load settings; ``None`` means defaults. Unknown keys are errors (catches typos)."""
    if path is None:
        return Config()
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    return validate(_build(Config, data, ""))
