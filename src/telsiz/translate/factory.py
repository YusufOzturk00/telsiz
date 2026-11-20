"""Create the configured translator, picking one automatically if asked."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from telsiz.config import Config
from telsiz.system import choose_translation, total_ram_gb

log = logging.getLogger(__name__)

_UNSET: Any = object()


def _default_nllb(model: str, device: str, cpu_threads: int) -> Any:
    from telsiz.translate.nllb import create_nllb_translator

    return create_nllb_translator(model, device=device, cpu_threads=cpu_threads)


def _default_argos(device: str, cpu_threads: int) -> Any:
    from telsiz.translate.argos import create_argos_translator

    return create_argos_translator(device=device, cpu_threads=cpu_threads)


def create_translator(
    config: Config,
    *,
    ram_gb: float | None = _UNSET,
    make_nllb: Callable[[str, str, int], Any] | None = None,
    make_argos: Callable[[str, int], Any] | None = None,
) -> Any:
    """``engine = "auto"`` picks by installed RAM; a failing NLLB falls back to Argos."""
    make_nllb = make_nllb or _default_nllb
    make_argos = make_argos or _default_argos
    device = config.translate.device
    threads = config.performance.cpu_threads

    engine, model = config.translate.engine, config.translate.nllb_model
    if engine == "auto":
        choice = choose_translation(total_ram_gb() if ram_gb is _UNSET else ram_gb)
        log.info("Translation: %s", choice.reason)
        engine, model = choice.engine, choice.nllb_model or model

    if engine == "nllb":
        try:
            translator = make_nllb(model, device, threads)
            log.info("Translation engine: %s (weights CC-BY-NC-4.0, non-commercial)", model)
            return translator
        except Exception as exc:  # download or load failure: keep translating with Argos
            log.warning("Could not load %s (%s); using Argos instead", model, exc)
    log.info("Translation engine: Argos")
    return make_argos(device, threads)
