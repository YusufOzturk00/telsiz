"""Local translation with Argos Translate models.

Argos model packages (``.argosmodel``) are zip files holding a CTranslate2
model and a SentencePiece or BPE tokenizer. We run them directly with
``ctranslate2`` (MIT) and the tokenizers in :mod:`telsiz.translate.tokenizers`
instead of using the ``argostranslate`` package, which depends on ``minisbd`` (AGPL-3.0) and pulls
in torch, spaCy and Stanza.

Languages without a direct model are translated through English.
"""

from __future__ import annotations

import io
import json
import logging
import re
import urllib.request
import zipfile
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Protocol

from telsiz.paths import models_dir
from telsiz.translate.base import TranslationUnavailable
from telsiz.translate.tokenizers import load_tokenizer

log = logging.getLogger(__name__)

DEFAULT_INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"
PIVOT = "en"

Pair = tuple[str, str]

_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in _SENTENCE_END.split(text.strip()) if part.strip()]


class SentenceModel(Protocol):
    def translate(self, sentences: Sequence[str]) -> list[str]: ...


class ArgosModel:
    """One Argos package loaded into CTranslate2."""

    def __init__(self, path: Path, device: str = "cpu", cpu_threads: int = 0) -> None:
        import ctranslate2

        metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        self._target_prefix: str | None = metadata.get("target_prefix") or None
        self._tokenizer = load_tokenizer(path, metadata["from_code"], metadata["to_code"])
        self._translator = ctranslate2.Translator(
            str(path / "model"), device=device, inter_threads=1, intra_threads=cpu_threads
        )

    def translate(self, sentences: Sequence[str]) -> list[str]:
        if not sentences:
            return []
        tokens = [self._tokenizer.encode(s) for s in sentences]
        prefix = [[self._target_prefix]] * len(tokens) if self._target_prefix else None
        results = self._translator.translate_batch(
            tokens,
            target_prefix=prefix,
            beam_size=4,
            length_penalty=0.2,
            replace_unknowns=True,
            max_batch_size=32,
        )
        out = []
        for result in results:
            hypothesis = result.hypotheses[0]
            if prefix:
                hypothesis = hypothesis[1:]
            out.append(self._tokenizer.decode(hypothesis))
        return out


class ArgosTranslator:
    def __init__(
        self,
        available_pairs: Callable[[], Iterable[Pair]],
        load_model: Callable[[str, str], SentenceModel],
        pivot: str = PIVOT,
        installed_pairs: Callable[[], Iterable[Pair]] | None = None,
    ) -> None:
        self._available_pairs = available_pairs
        self._load_model = load_model
        self._pivot = pivot
        # When given, prepare() only loads these; others download on first use.
        self._installed_pairs = installed_pairs
        self._pairs: set[Pair] | None = None
        self._models: dict[Pair, SentenceModel] = {}
        self._failed: dict[Pair, TranslationUnavailable] = {}

    def _known_pairs(self) -> set[Pair]:
        if self._pairs is None:
            self._pairs = set(self._available_pairs())
        return self._pairs

    def route(self, source: str, target: str) -> list[Pair]:
        if source == target:
            return []
        pairs = self._known_pairs()
        if (source, target) in pairs:
            return [(source, target)]
        via = self._pivot
        if (source, via) in pairs and (via, target) in pairs:
            return [(source, via), (via, target)]
        raise TranslationUnavailable(f"No Argos model route from {source!r} to {target!r}")

    def _model(self, pair: Pair) -> SentenceModel:
        if pair in self._failed:
            raise self._failed[pair]
        if pair not in self._models:
            try:
                self._models[pair] = self._load_model(*pair)
            except TranslationUnavailable as exc:
                self._failed[pair] = exc
                raise
        return self._models[pair]

    def prepare(self, sources: list[str], target: str) -> None:
        """Load installed models for these sources now; never fails on a single language."""
        installed = set(self._installed_pairs()) if self._installed_pairs else None
        for source in sources:
            try:
                steps = self.route(source, target)
            except TranslationUnavailable as exc:
                log.warning("%s", exc)
                continue
            for pair in steps:
                if installed is not None and pair not in installed:
                    log.info("Argos model %s->%s will be downloaded when first needed", *pair)
                    continue
                try:
                    self._model(pair)
                except TranslationUnavailable as exc:
                    log.warning("%s", exc)

    def translate(self, text: str, source: str, target: str) -> str:
        steps = self.route(source, target)
        sentences = split_sentences(text)
        if not steps or not sentences:
            return text
        for pair in steps:
            sentences = self._model(pair).translate(sentences)
        return " ".join(sentences)


# argos-net.com answers urllib's default "Python-urllib/x.y" agent with HTTP 403.
# Identify honestly as a downloader instead of impersonating a browser.
_USER_AGENT = "model-downloader/1.0"


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def _version_key(entry: dict) -> tuple[int, ...]:
    return tuple(int(p) for p in re.findall(r"\d+", str(entry.get("package_version", "0"))))


class ArgosPackageManager:
    """Finds, downloads and unpacks Argos packages into ``root``."""

    def __init__(
        self,
        root: Path | None = None,
        index_url: str = DEFAULT_INDEX_URL,
        fetch: Callable[[str], bytes] = _download,
    ) -> None:
        self.root = Path(root) if root else models_dir() / "argos"
        self.index_url = index_url
        self._fetch = fetch
        self._index_cache: list[dict] | None = None

    def installed(self) -> dict[Pair, Path]:
        found: dict[Pair, Path] = {}
        if not self.root.is_dir():
            return found
        for meta in self.root.glob("*/metadata.json"):
            data = json.loads(meta.read_text(encoding="utf-8"))
            found[(data["from_code"], data["to_code"])] = meta.parent
        return found

    def _index(self) -> list[dict]:
        if self._index_cache is not None:
            return self._index_cache
        cached = self.root / "index.json"
        if cached.is_file():
            self._index_cache = json.loads(cached.read_text(encoding="utf-8"))
            return self._index_cache
        try:
            raw = self._fetch(self.index_url)
            entries = json.loads(raw)
        except (OSError, ValueError) as exc:
            log.warning("Could not fetch the Argos package index: %s", exc)
            return []
        self.root.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(raw)
        self._index_cache = entries
        return entries

    def available_pairs(self) -> set[Pair]:
        pairs = set(self.installed())
        pairs.update((e["from_code"], e["to_code"]) for e in self._index())
        return pairs

    def ensure(self, source: str, target: str) -> Path:
        installed = self.installed()
        if (source, target) in installed:
            return installed[(source, target)]
        candidates = [
            e for e in self._index() if (e["from_code"], e["to_code"]) == (source, target)
        ]
        if not candidates:
            raise TranslationUnavailable(f"No Argos package for {source}->{target}")
        entry = max(candidates, key=_version_key)
        url = entry["links"][0]
        log.info("Downloading Argos model %s->%s from %s", source, target, url)
        return self._extract(self._fetch(url))

    def _extract(self, data: bytes) -> Path:
        root = self.root.resolve()
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
            for name in names:
                destination = (root / name).resolve()
                if not destination.is_relative_to(root):
                    raise ValueError(f"Refusing unsafe path in Argos package: {name!r}")
            metadata = [n for n in names if n.endswith("metadata.json") and n.count("/") == 1]
            if not metadata:
                raise ValueError("Argos package has no top-level metadata.json")
            root.mkdir(parents=True, exist_ok=True)
            archive.extractall(root)
        return root / metadata[0].split("/")[0]


def create_argos_translator(
    root: Path | None = None, device: str = "cpu", cpu_threads: int = 0
) -> ArgosTranslator:
    manager = ArgosPackageManager(root)
    return ArgosTranslator(
        manager.available_pairs,
        lambda source, target: ArgosModel(
            manager.ensure(source, target), device=device, cpu_threads=cpu_threads
        ),
        installed_pairs=lambda: manager.installed().keys(),
    )
