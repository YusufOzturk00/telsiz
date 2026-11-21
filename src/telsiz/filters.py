"""Reject typical Whisper hallucinations on silence and noise."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Whole-utterance outputs Whisper is known to invent for silence/noise,
# compared after lowercasing and removing punctuation.
_EXACT = {
    # English
    "you",
    "thank you",
    "thank you very much",
    "thanks for watching",
    "thank you for watching",
    "please subscribe",
    "subscribe to my channel",
    # Russian
    "продолжение следует",
    "спасибо за просмотр",
    "спасибо за внимание",
    # Ukrainian
    "дякую за перегляд",
    "дякую за увагу",
    # Polish
    "dziękuję za obejrzenie",
    # German
    "vielen dank fürs zuschauen",
    # Turkish
    "izlediğiniz için teşekkürler",
    "abone olmayı unutmayın",
}

# Fragments of subtitle credits from Whisper's training data; reject anywhere.
_FRAGMENTS = (
    "amara.org",
    "dimatorzok",
    "субтитр",
    "subtitles by",
    "napisy stworzone",
    "untertitel",
    "altyazı m.k",
)

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_SPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class FilterOptions:
    no_speech_threshold: float = 0.6
    log_prob_threshold: float = -1.0
    compression_ratio_threshold: float = 2.4
    max_ngram_repeats: int = 5  # an n-gram repeated more often than this is a loop


def _normalize(text: str) -> str:
    return _SPACE.sub(" ", _PUNCT.sub(" ", text.lower())).strip()


def _has_loop(words: list[str], max_repeats: int) -> bool:
    for n in (1, 2, 3):
        for start in range(len(words) - n + 1):
            gram = words[start : start + n]
            repeats = 1
            pos = start + n
            while words[pos : pos + n] == gram:
                repeats += 1
                pos += n
            if repeats > max_repeats:
                return True
    return False


def is_hallucination(
    text: str,
    *,
    no_speech_prob: float,
    avg_logprob: float,
    compression_ratio: float,
    options: FilterOptions | None = None,
) -> bool:
    opts = options or FilterOptions()
    normalized = _normalize(text)
    if not normalized:
        return True
    if normalized in _EXACT:
        return True
    lowered = text.lower()
    if any(fragment in lowered for fragment in _FRAGMENTS):
        return True
    if no_speech_prob > opts.no_speech_threshold and avg_logprob < opts.log_prob_threshold:
        return True
    if compression_ratio > opts.compression_ratio_threshold:
        return True
    return _has_loop(normalized.split(), opts.max_ngram_repeats)
