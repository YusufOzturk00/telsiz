"""Tests for the Whisper hallucination filter."""

import pytest

from telsiz.filters import FilterOptions, is_hallucination


def check(text, no_speech_prob=0.05, avg_logprob=-0.3, compression_ratio=1.2):
    return is_hallucination(
        text,
        no_speech_prob=no_speech_prob,
        avg_logprob=avg_logprob,
        compression_ratio=compression_ratio,
    )


def test_normal_speech_passes():
    assert not check("They are rushing B, two of them have AWP")


@pytest.mark.parametrize("text", ["", "   ", "...", " - "])
def test_empty_or_punctuation_only_is_rejected(text):
    assert check(text)


@pytest.mark.parametrize(
    "text",
    [
        "Thank you.",
        "Thanks for watching!",
        "you",
        "Продолжение следует...",
        "Спасибо за просмотр!",
        "Дякую за перегляд!",
        "Altyazı M.K.",
    ],
)
def test_known_silence_hallucinations_are_rejected(text):
    assert check(text)


@pytest.mark.parametrize(
    "text",
    [
        "Субтитры сделал DimaTorzok",
        "Napisy stworzone przez społeczność Amara.org",
        "Untertitel der Amara.org-Community",
    ],
)
def test_subtitle_credits_are_rejected(text):
    assert check(text)


def test_blacklisted_phrase_inside_real_sentence_passes():
    assert not check("Thank you for the flash, I got him")


def test_high_no_speech_probability_with_low_confidence_is_rejected():
    assert check("hmm", no_speech_prob=0.8, avg_logprob=-1.5)


def test_high_no_speech_probability_but_confident_text_passes():
    assert not check("plant the bomb", no_speech_prob=0.8, avg_logprob=-0.2)


def test_high_compression_ratio_is_rejected():
    assert check("some looping text", compression_ratio=3.1)


def test_normal_repetition_passes():
    assert not check("go go go")


@pytest.mark.parametrize(
    "text",
    [
        "B B B B B B B B",
        "rush b rush b rush b rush b rush b rush b",
    ],
)
def test_looping_tokens_are_rejected(text):
    assert check(text)


def test_thresholds_are_configurable():
    strict = FilterOptions(compression_ratio_threshold=1.5)

    assert is_hallucination(
        "abc", no_speech_prob=0.0, avg_logprob=0.0, compression_ratio=2.0, options=strict
    )
