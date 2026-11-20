"""Translator interface shared by all engines (argos, nllb, deepl)."""

from __future__ import annotations

from typing import Protocol


class TranslationUnavailable(RuntimeError):
    """The engine cannot translate between the requested languages."""


class Translator(Protocol):
    def translate(self, text: str, source: str, target: str) -> str:
        """Translate ``text`` from ISO 639-1 ``source`` to ``target``."""
        ...

    def prepare(self, sources: list[str], target: str) -> None:
        """Load (and if needed download) everything required up front."""
        ...
