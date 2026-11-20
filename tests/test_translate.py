"""Tests for the translator interface and the Argos engine (with fake models)."""

import io
import json
import zipfile

import pytest

from telsiz.translate.argos import ArgosPackageManager, ArgosTranslator, split_sentences
from telsiz.translate.base import TranslationUnavailable

# --- sentence splitting -------------------------------------------------------


def test_split_sentences_on_terminal_punctuation():
    assert split_sentences("They rush B. Two AWPs! You ok?") == [
        "They rush B.",
        "Two AWPs!",
        "You ok?",
    ]


def test_split_sentences_keeps_unpunctuated_text_whole():
    assert split_sentences("  he going b no money eco  ") == ["he going b no money eco"]


def test_split_sentences_empty():
    assert split_sentences("   ") == []


# --- routing ------------------------------------------------------------------


class FakeModel:
    def __init__(self, pair):
        self.pair = pair
        self.calls = []

    def translate(self, sentences):
        self.calls.append(list(sentences))
        return [f"{s}|{self.pair[0]}>{self.pair[1]}" for s in sentences]


class FakeLoader:
    def __init__(self, pairs):
        self.pairs = set(pairs)
        self.loaded = {}

    def available_pairs(self):
        return self.pairs

    def __call__(self, source, target):
        assert (source, target) in self.pairs
        assert (source, target) not in self.loaded, "model loaded twice"
        self.loaded[(source, target)] = FakeModel((source, target))
        return self.loaded[(source, target)]


def make_translator(pairs):
    loader = FakeLoader(pairs)
    return ArgosTranslator(loader.available_pairs, loader), loader


def test_direct_pair_is_used():
    translator, loader = make_translator({("en", "tr"), ("en", "ru"), ("ru", "en")})

    assert translator.translate("Rush B.", "en", "tr") == "Rush B.|en>tr"
    assert set(loader.loaded) == {("en", "tr")}


def test_missing_pair_pivots_through_english():
    translator, _ = make_translator({("en", "tr"), ("ru", "en")})

    assert translator.translate("Они идут на Б.", "ru", "tr") == "Они идут на Б.|ru>en|en>tr"


def test_each_sentence_is_translated_in_one_batch():
    translator, loader = make_translator({("en", "tr")})

    out = translator.translate("Rush B. Go go go!", "en", "tr")

    assert out == "Rush B.|en>tr Go go go!|en>tr"
    assert loader.loaded[("en", "tr")].calls == [["Rush B.", "Go go go!"]]


def test_same_language_is_returned_unchanged():
    translator, loader = make_translator({("en", "tr")})

    assert translator.translate("selam", "tr", "tr") == "selam"
    assert loader.loaded == {}


def test_models_are_loaded_once():
    translator, _ = make_translator({("en", "tr")})

    translator.translate("a", "en", "tr")
    translator.translate("b", "en", "tr")  # FakeLoader asserts it is not loaded twice


def test_unsupported_pair_raises():
    translator, _ = make_translator({("en", "tr")})

    with pytest.raises(TranslationUnavailable):
        translator.translate("Hallo", "de", "tr")


def test_route_reports_steps():
    translator, _ = make_translator({("en", "tr"), ("ru", "en")})

    assert translator.route("ru", "tr") == [("ru", "en"), ("en", "tr")]
    assert translator.route("en", "tr") == [("en", "tr")]
    assert translator.route("tr", "tr") == []


def test_prepare_loads_models_for_all_routes():
    translator, loader = make_translator({("en", "tr"), ("ru", "en")})

    translator.prepare(["en", "ru", "tr"], "tr")

    assert set(loader.loaded) == {("en", "tr"), ("ru", "en")}


def test_prepare_only_loads_installed_models():
    loader = FakeLoader({("en", "tr"), ("ru", "en")})
    translator = ArgosTranslator(
        loader.available_pairs, loader, installed_pairs=lambda: {("en", "tr")}
    )

    translator.prepare(["en", "ru"], "tr")

    assert set(loader.loaded) == {("en", "tr")}
    # A missing model is fetched the first time that language is actually heard.
    assert translator.translate("Да", "ru", "tr") == "Да|ru>en|en>tr"
    assert set(loader.loaded) == {("en", "tr"), ("ru", "en")}


def test_prepare_skips_models_that_cannot_be_loaded():
    def loader(source, target):
        if source == "uk":
            raise TranslationUnavailable("unsupported package")
        return FakeModel((source, target))

    translator = ArgosTranslator(lambda: {("en", "tr"), ("uk", "en")}, loader)

    translator.prepare(["en", "uk"], "tr")  # must not raise

    assert translator.translate("go", "en", "tr") == "go|en>tr"


# --- package download / install -------------------------------------------------


def make_package(name="translate-en_tr-1_5", extra=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(f"{name}/metadata.json", json.dumps({"from_code": "en", "to_code": "tr"}))
        zf.writestr(f"{name}/sentencepiece.model", b"sp")
        zf.writestr(f"{name}/model/model.bin", b"bin")
        for member, data in (extra or {}).items():
            zf.writestr(member, data)
    return buf.getvalue()


INDEX = [
    {"from_code": "en", "to_code": "tr", "package_version": "1.0", "links": ["https://x/old"]},
    {"from_code": "en", "to_code": "tr", "package_version": "1.5", "links": ["https://x/en_tr"]},
    {"from_code": "ru", "to_code": "en", "package_version": "1.9", "links": ["https://x/ru_en"]},
]


class FakeFetch:
    def __init__(self, files):
        self.files = files
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        return self.files[url]


def test_available_pairs_come_from_the_index(tmp_path):
    fetch = FakeFetch({"https://index": json.dumps(INDEX).encode()})
    manager = ArgosPackageManager(tmp_path, index_url="https://index", fetch=fetch)

    assert manager.available_pairs() == {("en", "tr"), ("ru", "en")}


def test_ensure_downloads_newest_version_and_extracts(tmp_path):
    fetch = FakeFetch(
        {"https://index": json.dumps(INDEX).encode(), "https://x/en_tr": make_package()}
    )
    manager = ArgosPackageManager(tmp_path, index_url="https://index", fetch=fetch)

    path = manager.ensure("en", "tr")

    assert (path / "metadata.json").is_file()
    assert (path / "model" / "model.bin").is_file()
    assert "https://x/old" not in fetch.urls


def test_ensure_reuses_installed_package(tmp_path):
    fetch = FakeFetch(
        {"https://index": json.dumps(INDEX).encode(), "https://x/en_tr": make_package()}
    )
    manager = ArgosPackageManager(tmp_path, index_url="https://index", fetch=fetch)
    first = manager.ensure("en", "tr")

    fresh = ArgosPackageManager(tmp_path, index_url="https://index", fetch=FakeFetch({}))

    assert fresh.ensure("en", "tr") == first
    assert ("en", "tr") in fresh.available_pairs()


def test_ensure_rejects_paths_escaping_the_target_dir(tmp_path):
    evil = make_package(extra={"../evil.txt": b"pwned"})
    fetch = FakeFetch({"https://index": json.dumps(INDEX).encode(), "https://x/en_tr": evil})
    manager = ArgosPackageManager(tmp_path / "models", index_url="https://index", fetch=fetch)

    with pytest.raises(ValueError, match="unsafe"):
        manager.ensure("en", "tr")
    assert not (tmp_path / "evil.txt").exists()


def test_ensure_unknown_pair_raises(tmp_path):
    fetch = FakeFetch({"https://index": json.dumps(INDEX).encode()})
    manager = ArgosPackageManager(tmp_path, index_url="https://index", fetch=fetch)

    with pytest.raises(TranslationUnavailable):
        manager.ensure("de", "tr")


def test_offline_index_falls_back_to_installed_packages(tmp_path):
    def offline(url):
        raise OSError("no network")

    manager = ArgosPackageManager(tmp_path, index_url="https://index", fetch=offline)

    assert manager.available_pairs() == set()


def test_downloads_send_a_user_agent(monkeypatch):
    from telsiz.translate import argos

    seen = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"data"

    def fake_urlopen(request, timeout):
        seen["agent"] = request.get_header("User-agent")
        return Response()

    monkeypatch.setattr(argos.urllib.request, "urlopen", fake_urlopen)

    assert argos._download("https://example.invalid/x") == b"data"
    assert seen["agent"] and "urllib" not in seen["agent"].lower()
