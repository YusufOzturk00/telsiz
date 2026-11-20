"""Spoken-language selection on top of Whisper's language probabilities.

Rules (CLAUDE.md section 7):

* Only languages from the allowed list are considered; their probabilities
  are renormalized so they sum to 1.
* For short utterances or low confidence, the language that dominated the
  last ``window_s`` seconds is used instead ("stickiness").
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageDecision:
    language: str
    confidence: float  # renormalized probability of the chosen language
    sticky: bool  # True when the recent dominant language overrode the guess


class LanguageSelector:
    def __init__(
        self,
        allowed: Sequence[str],
        min_confidence: float = 0.6,
        min_duration_s: float = 1.2,
        window_s: float = 30.0,
    ) -> None:
        if not allowed:
            raise ValueError("At least one allowed source language is required")
        self.allowed = list(dict.fromkeys(allowed))
        self.min_confidence = min_confidence
        self.min_duration_s = min_duration_s
        self.window_s = window_s
        self._history: deque[tuple[float, str, float]] = deque()  # (time, language, duration)

    def choose(self, probs: Mapping[str, float], duration_s: float, now: float) -> LanguageDecision:
        allowed_probs = {lang: max(float(probs.get(lang, 0.0)), 0.0) for lang in self.allowed}
        total = sum(allowed_probs.values())
        dominant = self.dominant(now)

        if total <= 0.0:
            return LanguageDecision(dominant or self.allowed[0], 0.0, dominant is not None)

        normalized = {lang: p / total for lang, p in allowed_probs.items()}
        best = max(normalized, key=normalized.__getitem__)
        uncertain = duration_s < self.min_duration_s or normalized[best] < self.min_confidence
        if uncertain and dominant is not None:
            return LanguageDecision(dominant, normalized[dominant], sticky=True)

        if not uncertain:
            self._history.append((now, best, duration_s))
        return LanguageDecision(best, normalized[best], sticky=False)

    def dominant(self, now: float) -> str | None:
        """Language with the most confident speech time within the window."""
        while self._history and now - self._history[0][0] > self.window_s:
            self._history.popleft()
        totals: dict[str, float] = {}
        for _, lang, duration in self._history:
            totals[lang] = totals.get(lang, 0.0) + duration
        if not totals:
            return None
        return max(totals, key=totals.__getitem__)
