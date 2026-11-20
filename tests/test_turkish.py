"""Tests for Turkish suffix harmony after restored glossary terms."""

import pytest

from telsiz.turkish import harmonize_suffix


@pytest.mark.parametrize(
    ("reading", "suffix", "expected"),
    [
        # dative -(y)a / -(y)e
        ("be long", "e", "a"),
        ("be", "a", "ye"),
        ("siti", "e", "ye"),
        ("konektır", "e", "a"),
        ("eko", "e", "ya"),
        ("mid", "a", "e"),
        # locative -da/-de/-ta/-te (hardening after voiceless consonants)
        ("be long", "de", "da"),
        ("ritek", "de", "te"),
        ("em dört", "da", "te"),
        ("eko", "de", "da"),
        # ablative
        ("ritek", "dan", "ten"),
        # accusative -(y)ı/i/u/ü
        ("avp", "i", "ı"),
        ("mid", "ı", "i"),
        ("eko", "ı", "yu"),
        ("em dört", "i", "ü"),
        # genitive -(n)ın
        ("be", "ın", "nin"),
        ("avp", "nın", "ın"),
        # instrumental -(y)la/-(y)le
        ("avp", "yle", "la"),
        ("eko", "la", "yla"),
        # chains and plural
        ("be long", "deki", "daki"),
        ("smok", "ler", "lar"),
        ("fleş", "ı", "i"),
    ],
)
def test_suffix_follows_vowel_harmony_and_sound_rules(reading, suffix, expected):
    assert harmonize_suffix(reading, suffix) == expected


def test_suffix_without_vowels_is_left_alone():
    assert harmonize_suffix("be", "s") == "s"


def test_empty_suffix():
    assert harmonize_suffix("be", "") == ""
