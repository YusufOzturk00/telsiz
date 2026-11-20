"""Local translation with Meta's NLLB-200 (distilled) on CTranslate2.

NLLB translates between its 200 languages directly, so Russian or Ukrainian
reach Turkish without the English pivot Argos needs.

License note: the NLLB-200 model weights are CC-BY-NC-4.0 (non-commercial).
Telsiz's code stays MIT; the weights are downloaded by the user at runtime and
are not shipped with Telsiz.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from telsiz.paths import models_dir
from telsiz.translate.argos import split_sentences
from telsiz.translate.base import TranslationUnavailable

log = logging.getLogger(__name__)

# ISO 639-1 -> NLLB (FLORES-200) codes for languages Telsiz is likely to meet.
NLLB_CODES = {
    "en": "eng_Latn",
    "ru": "rus_Cyrl",
    "uk": "ukr_Cyrl",
    "pl": "pol_Latn",
    "de": "deu_Latn",
    "tr": "tur_Latn",
    "fr": "fra_Latn",
    "es": "spa_Latn",
    "pt": "por_Latn",
    "it": "ita_Latn",
    "nl": "nld_Latn",
    "cs": "ces_Latn",
    "sk": "slk_Latn",
    "ro": "ron_Latn",
    "hu": "hun_Latn",
    "bg": "bul_Cyrl",
    "sr": "srp_Cyrl",
    "kk": "kaz_Cyrl",
    "be": "bel_Cyrl",
    "lt": "lit_Latn",
    "lv": "lvs_Latn",
    "et": "est_Latn",
    "fi": "fin_Latn",
    "sv": "swe_Latn",
    "da": "dan_Latn",
    "no": "nob_Latn",
    "az": "azj_Latn",
    "ka": "kat_Geor",
    "ar": "arb_Arab",
    "fa": "pes_Arab",
    "zh": "zho_Hans",
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
}

# Hugging Face repositories with CTranslate2 int8 conversions (CC-BY-NC-4.0 weights).
NLLB_MODELS = {
    "nllb-600m": "JustFrederik/nllb-200-distilled-600M-ct2-int8",
    "nllb-1.3b": "OpenNMT/nllb-200-distilled-1.3B-ct2-int8",
}
_FILES = ["config.json", "model.bin", "shared_vocabulary.*", "tokenizer.json", "*.md"]


def nllb_model_dir(name: str) -> Path:
    """Download (once) and return the folder of an NLLB model."""
    if name not in NLLB_MODELS:
        raise ValueError(f"Unknown NLLB model {name!r}; use one of {sorted(NLLB_MODELS)}")
    target = models_dir() / "nllb" / name
    if not (target / "model.bin").is_file():
        from huggingface_hub import snapshot_download

        log.info("Downloading %s (%s); this happens once", name, NLLB_MODELS[name])
        snapshot_download(NLLB_MODELS[name], local_dir=target, allow_patterns=_FILES)
    return target


class NLLBTranslator:
    def __init__(
        self,
        model_dir: Path | None = None,
        *,
        device: str = "cpu",
        cpu_threads: int = 0,
        compute_type: str = "auto",
        beam_size: int = 4,
        tokenizer: Any | None = None,
        translator: Any | None = None,
    ) -> None:
        if tokenizer is None or translator is None:
            if model_dir is None:
                raise ValueError("model_dir is required without an injected model")
            import ctranslate2
            from tokenizers import Tokenizer

            tokenizer = tokenizer or Tokenizer.from_file(str(model_dir / "tokenizer.json"))
            if compute_type == "auto":  # the saved int8_float16 is not efficient on the CPU
                compute_type = "int8" if device == "cpu" else "int8_float16"
            translator = translator or ctranslate2.Translator(
                str(model_dir),
                device=device,
                compute_type=compute_type,
                inter_threads=1,
                intra_threads=cpu_threads,
            )
        self._tokenizer = tokenizer
        self._translator = translator
        self._beam_size = beam_size

    def prepare(self, sources: list[str], target: str) -> None:
        """The single multilingual model is already loaded."""
        for lang in [*sources, target]:
            if lang not in NLLB_CODES:
                log.warning("NLLB has no code configured for %r", lang)

    def translate(self, text: str, source: str, target: str) -> str:
        if source == target:
            return text
        try:
            src, tgt = NLLB_CODES[source], NLLB_CODES[target]
        except KeyError as exc:
            raise TranslationUnavailable(f"NLLB cannot translate {source!r} to {target!r}") from exc
        sentences = split_sentences(text)
        if not sentences:
            return text
        batch = [
            [src, *self._tokenizer.encode(s, add_special_tokens=False).tokens, "</s>"]
            for s in sentences
        ]
        results = self._translator.translate_batch(
            batch,
            target_prefix=[[tgt]] * len(batch),
            beam_size=self._beam_size,
            max_decoding_length=256,
        )
        out = []
        for result in results:
            tokens = result.hypotheses[0][1:]  # drop the target language code
            ids = [i for i in map(self._tokenizer.token_to_id, tokens) if i is not None]
            out.append(self._tokenizer.decode(ids, skip_special_tokens=True).strip())
        return " ".join(out)


def create_nllb_translator(
    model: str = "nllb-600m", device: str = "cpu", cpu_threads: int = 0
) -> NLLBTranslator:
    return NLLBTranslator(nllb_model_dir(model), device=device, cpu_threads=cpu_threads)
