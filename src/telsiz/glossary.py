"""Game-term glossary applied around machine translation.

Before translation:

1. Gamer abbreviations are expanded ("nt" -> "nice try").
2. Game terms players say as-is ("AWP", "eco", "A long") and phrases with a
   fixed translation ("my bad" -> "benim hatam") are swapped for placeholders
   such as ``ZX1``. Argos keeps these intact (numbers and brackets fared worse
   in tests) and even attaches Turkish case suffixes to them ("ZX1'e").

After translation the placeholders are replaced with the kept term or the
fixed translation.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

_PLACEHOLDER = re.compile(r"ZX(\d+)", re.IGNORECASE)
_SPACE = re.compile(r"\s+")

Pair = tuple[str, str]


@dataclass(frozen=True)
class Protected:
    text: str  # what the translator sees
    replacements: list[str] = field(default_factory=list)  # value for ZX1, ZX2, ...


def _term_regex(term: str, exact: bool) -> str:
    body = r"\s+".join(re.escape(word) for word in term.split())
    pattern = rf"(?<!\w){body}(?!\w)"
    return pattern if exact else f"(?i:{pattern})"


def _norm(text: str) -> str:
    return _SPACE.sub(" ", text.strip())


@dataclass(frozen=True)
class Glossary:
    expansions: Mapping[str, Mapping[str, str]]  # source language -> {abbreviation: words}
    keep: list[str]  # kept as said, matched case-insensitively
    keep_exact: list[str]  # kept as said, matched with exact capitalization
    phrases: Mapping[Pair, Mapping[str, str]]  # (source, target) -> {phrase: translation}

    @classmethod
    def load(cls, path: Path | str) -> Glossary:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
        phrases = {
            (source, target): dict(table)
            for source, targets in data.get("phrases", {}).items()
            for target, table in targets.items()
        }
        keep = data.get("keep", {})
        return cls(
            expansions={lang: dict(table) for lang, table in data.get("expand", {}).items()},
            keep=list(keep.get("terms", [])),
            keep_exact=list(keep.get("exact", [])),
            phrases=phrases,
        )

    def _expand(self, text: str, source: str) -> str:
        table = self.expansions.get(source)
        if not table:
            return text
        lookup = {abbr.lower(): words for abbr, words in table.items()}
        alternatives = sorted(table, key=len, reverse=True)
        pattern = "|".join(_term_regex(a, exact=False) for a in alternatives)
        return re.sub(pattern, lambda m: lookup[m.group(0).lower()], text)

    def protect(self, text: str, source: str, target: str) -> Protected:
        text = self._expand(text, source)

        exact: dict[str, str] = {_norm(t): t for t in self.keep_exact}
        loose: dict[str, str] = {_norm(t).lower(): t for t in self.keep}
        loose.update(
            {_norm(p).lower(): tr for p, tr in self.phrases.get((source, target), {}).items()}
        )
        entries = [(t, True) for t in exact] + [(t, False) for t in loose]
        if not entries:
            return Protected(text)
        entries.sort(key=lambda e: len(e[0]), reverse=True)
        pattern = re.compile("|".join(_term_regex(term, is_exact) for term, is_exact in entries))

        replacements: list[str] = []

        def swap(match: re.Match[str]) -> str:
            found = _norm(match.group(0))
            value = exact.get(found) or loose[found.lower()]
            replacements.append(value)
            return f"ZX{len(replacements)}"

        return Protected(pattern.sub(swap, text), replacements)

    def restore(self, protected: Protected, translated: str) -> str:
        values = protected.replacements

        def back(match: re.Match[str]) -> str:
            index = int(match.group(1)) - 1
            return values[index] if 0 <= index < len(values) else match.group(0)

        return _PLACEHOLDER.sub(back, translated) if values else translated


def default_glossary_path() -> Path:
    """The bundled ``data/glossary.toml`` (inside the wheel, or at the repo root)."""
    packaged = Path(__file__).with_name("data") / "glossary.toml"
    if packaged.is_file():
        return packaged
    return Path(__file__).resolve().parents[2] / "data" / "glossary.toml"
