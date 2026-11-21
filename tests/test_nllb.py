"""Tests for the NLLB-200 translator (with a fake tokenizer and model)."""

from types import SimpleNamespace

import pytest

from telsiz.translate.base import TranslationUnavailable
from telsiz.translate.nllb import NLLB_CODES, NLLBTranslator


class FakeTokenizer:
    """Splits on spaces; ids are positions in a growing vocabulary."""

    def __init__(self):
        self.vocab = ["</s>"]

    def _id(self, token):
        if token not in self.vocab:
            self.vocab.append(token)
        return self.vocab.index(token)

    def encode(self, text, add_special_tokens=True):
        assert add_special_tokens is False
        return SimpleNamespace(tokens=text.split())

    def token_to_id(self, token):
        return self._id(token)

    def decode(self, ids, skip_special_tokens=True):
        words = [self.vocab[i] for i in ids]
        if skip_special_tokens:
            words = [w for w in words if w != "</s>" and w not in NLLB_CODES.values()]
        return " ".join(words)


class FakeCT2:
    def __init__(self):
        self.calls = []

    def translate_batch(self, batch, target_prefix=None, **kwargs):
        self.calls.append({"batch": batch, "target_prefix": target_prefix, **kwargs})
        results = []
        for tokens, prefix in zip(batch, target_prefix, strict=True):
            words = [t.upper() for t in tokens[1:-1]]  # drop source code and </s>
            results.append(SimpleNamespace(hypotheses=[prefix + words]))
        return results


def make():
    ct2 = FakeCT2()
    return NLLBTranslator(tokenizer=FakeTokenizer(), translator=ct2), ct2


def test_source_gets_language_code_and_end_token_target_gets_prefix():
    translator, ct2 = make()

    out = translator.translate("они идут", "ru", "tr")

    assert out == "ОНИ ИДУТ"
    [call] = ct2.calls
    assert call["batch"] == [["rus_Cyrl", "они", "идут", "</s>"]]
    assert call["target_prefix"] == [["tur_Latn"]]


def test_russian_goes_straight_to_turkish_without_a_pivot():
    translator, ct2 = make()

    translator.translate("да", "ru", "tr")

    assert len(ct2.calls) == 1  # one model call, no English step


def test_sentences_are_translated_in_one_batch():
    translator, ct2 = make()

    out = translator.translate("Rush B. Go go go!", "en", "tr")

    assert out == "RUSH B. GO GO GO!"
    assert len(ct2.calls[0]["batch"]) == 2


def test_same_language_is_returned_unchanged():
    translator, ct2 = make()

    assert translator.translate("selam", "tr", "tr") == "selam"
    assert ct2.calls == []


def test_unknown_language_is_unavailable():
    translator, _ = make()

    with pytest.raises(TranslationUnavailable):
        translator.translate("hola", "xx", "tr")


def test_empty_text():
    translator, ct2 = make()

    assert translator.translate("   ", "en", "tr") == "   "
    assert ct2.calls == []


def test_language_codes_cover_the_default_source_languages():
    for code in ("en", "ru", "uk", "pl", "de", "tr"):
        assert code in NLLB_CODES
