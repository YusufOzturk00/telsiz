"""Tests for Argos package tokenizers (SentencePiece or Moses + BPE)."""

import pytest

from telsiz.translate.base import TranslationUnavailable

pytest.importorskip("sacremoses")
pytest.importorskip("subword_nmt")

from telsiz.translate.tokenizers import BPETokenizer, load_tokenizer  # noqa: E402

CODES = "#version: 0.2\nr u\nru s\nrus h</w>\nr o\nro t\n"


@pytest.fixture
def bpe(tmp_path):
    path = tmp_path / "bpe.model"
    path.write_text(CODES, encoding="utf-8")
    return BPETokenizer(path, source="en", target="en")


def test_bpe_splits_words_into_subword_pieces(bpe):
    tokens = bpe.encode("rush rotate")

    assert tokens[0] == "rush"
    assert tokens[1].endswith("@@")  # "rotate" is not a whole merge, so it is split
    assert "".join(t.removesuffix("@@") for t in tokens[1:]) == "rotate"


def test_bpe_separates_punctuation_like_moses(bpe):
    tokens = bpe.encode("rush, rotate!")

    assert "," in tokens
    assert "!" in tokens


def test_bpe_decode_joins_pieces_and_detokenizes(bpe):
    assert bpe.decode(bpe.encode("Rush B, rotate now!")) == "Rush B, rotate now!"


def test_bpe_round_trips_apostrophes(bpe):
    assert bpe.decode(bpe.encode("they're at A")) == "they're at A"


def test_load_tokenizer_picks_bpe_when_package_has_bpe_model(tmp_path):
    (tmp_path / "bpe.model").write_text(CODES, encoding="utf-8")

    tokenizer = load_tokenizer(tmp_path, source="uk", target="en")

    assert isinstance(tokenizer, BPETokenizer)


def test_load_tokenizer_without_known_model_raises(tmp_path):
    with pytest.raises(TranslationUnavailable):
        load_tokenizer(tmp_path, source="uk", target="en")
