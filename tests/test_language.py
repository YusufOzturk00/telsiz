"""Tests for language selection."""

import pytest

from telsiz.language import LanguageSelector

ALLOWED = ["en", "ru", "uk", "pl", "de", "tr"]


def test_picks_highest_allowed_language_and_renormalizes():
    selector = LanguageSelector(ALLOWED)

    decision = selector.choose({"en": 0.4, "ja": 0.4, "ru": 0.2}, duration_s=3.0, now=3.0)

    assert decision.language == "en"
    assert decision.confidence == pytest.approx(0.4 / 0.6)
    assert not decision.sticky


def test_ignores_languages_outside_the_allowed_list():
    selector = LanguageSelector(["en", "ru"])

    decision = selector.choose({"es": 0.9, "ru": 0.06, "en": 0.04}, duration_s=3.0, now=3.0)

    assert decision.language == "ru"


def test_short_utterance_uses_recent_dominant_language():
    selector = LanguageSelector(ALLOWED)
    selector.choose({"ru": 0.95, "en": 0.05}, duration_s=3.0, now=10.0)

    decision = selector.choose({"pl": 0.7, "ru": 0.3}, duration_s=0.8, now=12.0)

    assert decision.language == "ru"
    assert decision.sticky
    assert decision.confidence == pytest.approx(0.3)


def test_low_confidence_uses_recent_dominant_language():
    selector = LanguageSelector(ALLOWED)
    selector.choose({"ru": 0.9, "uk": 0.1}, duration_s=2.0, now=5.0)

    decision = selector.choose({"uk": 0.55, "ru": 0.45}, duration_s=4.0, now=9.0)

    assert decision.language == "ru"
    assert decision.sticky


def test_without_history_uncertain_guess_is_kept():
    selector = LanguageSelector(ALLOWED)

    decision = selector.choose({"uk": 0.55, "ru": 0.45}, duration_s=0.5, now=1.0)

    assert decision.language == "uk"
    assert not decision.sticky


def test_history_older_than_window_is_forgotten():
    selector = LanguageSelector(ALLOWED, window_s=30.0)
    selector.choose({"ru": 0.95, "en": 0.05}, duration_s=3.0, now=10.0)

    decision = selector.choose({"pl": 0.7, "ru": 0.3}, duration_s=0.8, now=45.0)

    assert decision.language == "pl"
    assert not decision.sticky


def test_dominant_language_is_weighted_by_speech_duration():
    selector = LanguageSelector(ALLOWED)
    selector.choose({"en": 0.9}, duration_s=6.0, now=6.0)
    selector.choose({"ru": 0.9}, duration_s=1.5, now=8.0)
    selector.choose({"ru": 0.9}, duration_s=1.5, now=10.0)

    assert selector.dominant(now=11.0) == "en"


def test_sticky_decisions_do_not_feed_the_history():
    selector = LanguageSelector(ALLOWED)
    selector.choose({"ru": 0.9}, duration_s=2.0, now=2.0)
    for t in range(3, 10):
        selector.choose({"pl": 0.5, "ru": 0.5}, duration_s=0.5, now=float(t))

    assert selector.dominant(now=10.0) == "ru"


def test_no_allowed_language_in_probabilities_falls_back():
    selector = LanguageSelector(["en", "ru"])

    decision = selector.choose({"ja": 1.0}, duration_s=3.0, now=1.0)

    assert decision.language == "en"
    assert decision.confidence == 0.0


def test_requires_at_least_one_allowed_language():
    with pytest.raises(ValueError):
        LanguageSelector([])
