"""Word error rate (speech recognition) and chrF (translation) scores."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def _words(text: str) -> list[str]:
    return _PUNCT.sub(" ", text.lower()).split()


def word_error_rate(reference: str, hypothesis: str) -> float:
    """(substitutions + deletions + insertions) / reference words, case/punctuation-insensitive."""
    ref, hyp = _words(reference), _words(hypothesis)
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
