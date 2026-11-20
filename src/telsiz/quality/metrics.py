"""Word error rate (speech recognition) and chrF (translation) scores."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)

# Whisper writes "$1.87" and "60" where a book says "one dollar and eighty-seven
# cents" and "sixty". For English, both sides are brought to digits first so
# formatting differences are not counted as recognition errors.
_EN_UNIT_WORDS = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen",
)  # fmt: skip
_EN_TENS_WORDS = ("twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
_EN_UNITS = {word: value for value, word in enumerate(_EN_UNIT_WORDS)}
_EN_TENS = {word: 10 * value for value, word in enumerate(_EN_TENS_WORDS, start=2)}
_EN_SINGULAR = {"dollars": "dollar", "cents": "cent"}
_CURRENCY = re.compile(r"\$(\d+)(?:\.(\d{2}))?")


def _expand_currency(match: re.Match[str]) -> str:
    cents = f" {int(match[2])} cent" if match[2] else ""
    return f" {int(match[1])} dollar{cents} "


def _english_numbers(words: list[str]) -> list[str]:
    out = []
    i = 0
    while i < len(words):
        word = words[i]
        if word in _EN_TENS:
            value = _EN_TENS[word]
            following = words[i + 1] if i + 1 < len(words) else ""
            if 0 < _EN_UNITS.get(following, 0) < 10:
                value += _EN_UNITS[following]
                i += 1
            out.append(str(value))
        elif word in _EN_UNITS:
            out.append(str(_EN_UNITS[word]))
        else:
            out.append(_EN_SINGULAR.get(word, word))
        i += 1
    return out


def _words(text: str, language: str | None = None) -> list[str]:
    text = text.lower()
    if language == "en":
        text = _CURRENCY.sub(_expand_currency, text)
    words = _PUNCT.sub(" ", text).split()
    return _english_numbers(words) if language == "en" else words


def word_error_rate(reference: str, hypothesis: str, language: str | None = None) -> float:
    """(substitutions + deletions + insertions) / reference words, case/punctuation-insensitive.

    With ``language="en"``, spelled-out numbers and dollar amounts are normalized.
    """
    ref, hyp = _words(reference, language), _words(hypothesis, language)
    if not ref:
        raise ValueError("Reference must contain at least one word")
    previous = list(range(len(hyp) + 1))
    for i, ref_word in enumerate(ref, start=1):
        current = [i] + [0] * len(hyp)
        for j, hyp_word in enumerate(hyp, start=1):
            current[j] = min(
                previous[j] + 1,  # deletion
                current[j - 1] + 1,  # insertion
                previous[j - 1] + (ref_word != hyp_word),  # substitution
            )
        previous = current
    return previous[-1] / len(ref)


_CHAR_ORDER = 6
_BETA = 2.0

Stats = list[tuple[int, int, int]]  # per n: (matches, hypothesis n-grams, reference n-grams)


def _char_ngrams(text: str, n: int) -> Counter[str]:
    chars = "".join(text.split())  # chrF ignores whitespace
    return Counter(chars[i : i + n] for i in range(len(chars) - n + 1))


def _stats(hypothesis: str, reference: str) -> Stats:
    out = []
    for n in range(1, _CHAR_ORDER + 1):
        hyp, ref = _char_ngrams(hypothesis, n), _char_ngrams(reference, n)
        matches = sum((hyp & ref).values())
        out.append((matches, sum(hyp.values()), sum(ref.values())))
    return out


def _score(stats: Stats) -> float:
    precisions, recalls = [], []
    for matches, hyp_total, ref_total in stats:
        if hyp_total and ref_total:
            precisions.append(matches / hyp_total)
            recalls.append(matches / ref_total)
    if not precisions:
        return 0.0
    p = sum(precisions) / len(precisions)
    r = sum(recalls) / len(recalls)
    if p + r == 0:
        return 0.0
    b2 = _BETA**2
    return 100.0 * (1 + b2) * p * r / (b2 * p + r)


def chrf(hypothesis: str, reference: str) -> float:
    """Sentence-level chrF (character 6-grams, beta=2), 0-100."""
    return _score(_stats(hypothesis, reference))


def corpus_chrf(pairs: Iterable[tuple[str, str]]) -> float:
    """chrF over (hypothesis, reference) pairs with pooled n-gram statistics."""
    totals = [[0, 0, 0] for _ in range(_CHAR_ORDER)]
    for hypothesis, reference in pairs:
        for total, stat in zip(totals, _stats(hypothesis, reference), strict=True):
            for k in range(3):
                total[k] += stat[k]
    return _score([tuple(t) for t in totals])
