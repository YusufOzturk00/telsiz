"""Tokenizers used by Argos model packages.

Newer packages ship ``sentencepiece.model``. Some (for example uk->en 1.9)
ship ``bpe.model`` instead: Moses tokenization followed by subword-nmt BPE
with ``@@`` continuation markers, the same steps argostranslate performs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from telsiz.translate.base import TranslationUnavailable

BPE_SEPARATOR = "@@"


class Tokenizer(Protocol):
    def encode(self, sentence: str) -> list[str]: ...

    def decode(self, tokens: list[str]) -> str: ...


class SentencePieceTokenizer:
    def __init__(self, model_file: Path) -> None:
        import sentencepiece

        self._sp = sentencepiece.SentencePieceProcessor(model_file=str(model_file))

    def encode(self, sentence: str) -> list[str]:
        return self._sp.encode(sentence, out_type=str)

    def decode(self, tokens: list[str]) -> str:
        return self._sp.decode(tokens).strip()


class BPETokenizer:
    def __init__(self, codes_file: Path, source: str, target: str) -> None:
        from sacremoses import MosesDetokenizer, MosesPunctNormalizer, MosesTokenizer
        from subword_nmt.apply_bpe import BPE

        self._normalizer = MosesPunctNormalizer(source)
        self._tokenizer = MosesTokenizer(source)
        self._detokenizer = MosesDetokenizer(target)
        with open(codes_file, encoding="utf-8") as codes:
            self._bpe = BPE(codes, separator=BPE_SEPARATOR)

    def encode(self, sentence: str) -> list[str]:
        words = self._tokenizer.tokenize(self._normalizer.normalize(sentence))
        return self._bpe.segment_tokens(words)

    def decode(self, tokens: list[str]) -> str:
        joined = " ".join(tokens).replace(f"{BPE_SEPARATOR} ", "")
        joined = joined.removesuffix(BPE_SEPARATOR)
        return self._detokenizer.detokenize(joined.split()).strip()


def load_tokenizer(package_dir: Path, source: str, target: str) -> Tokenizer:
    """Pick the tokenizer an Argos package was trained with."""
    if (package_dir / "sentencepiece.model").is_file():
        return SentencePieceTokenizer(package_dir / "sentencepiece.model")
    if (package_dir / "bpe.model").is_file():
        return BPETokenizer(package_dir / "bpe.model", source, target)
    raise TranslationUnavailable(f"{package_dir.name}: no supported tokenizer model")
