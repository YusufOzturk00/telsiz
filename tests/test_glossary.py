"""Tests for the game-term glossary applied around translation."""

from telsiz.glossary import Glossary, default_glossary_path


def make(**kwargs):
    defaults = {"expansions": {}, "keep": [], "keep_exact": [], "phrases": {}}
    defaults.update(kwargs)
    return Glossary(**defaults)


def test_abbreviations_are_expanded_as_whole_words():
    glossary = make(expansions={"en": {"nt": "nice try", "ez": "easy"}})

    protected = glossary.protect("NT nt, ez round, I want it", "en", "tr")

    assert protected.text == "nice try nice try, easy round, I want it"


def test_expansions_only_apply_to_their_language():
    glossary = make(expansions={"en": {"nt": "nice try"}})

    assert glossary.protect("nt", "ru", "tr").text == "nt"


def test_kept_terms_are_hidden_from_the_translator_and_restored():
    glossary = make(keep=["flash", "AWP"])

    protected = glossary.protect("flash me, he has an awp", "en", "tr")

    assert protected.text == "ZX1 me, he has an ZX2"
    assert glossary.restore(protected, "bana ZX1 at, onda ZX2 var") == "bana flash at, onda AWP var"


def test_kept_terms_respect_word_boundaries():
    glossary = make(keep=["flash"])

    assert glossary.protect("flashing lights", "en", "tr").text == "flashing lights"


def test_exact_terms_need_exact_capitalization():
    glossary = make(keep_exact=["A long", "CT"])

    protected = glossary.protect("one A long, it's a long way to CT", "en", "tr")

    assert protected.text == "one ZX1, it's a long way to ZX2"


def test_longer_terms_win_over_shorter_ones():
    glossary = make(keep=["buy", "force buy"])

    protected = glossary.protect("force buy now", "en", "tr")

    assert protected.text == "ZX1 now"
    assert glossary.restore(protected, "ZX1 şimdi") == "force buy şimdi"


def test_phrases_are_replaced_by_their_fixed_translation():
    glossary = make(phrases={("en", "tr"): {"my bad": "benim hatam"}})

    protected = glossary.protect("My bad, I whiffed", "en", "tr")

    assert protected.text == "ZX1, I whiffed"
    assert glossary.restore(protected, "ZX1, ıskaladım") == "Benim hatam, ıskaladım"


def test_phrases_for_another_target_are_ignored():
    glossary = make(phrases={("en", "de"): {"my bad": "mein Fehler"}})

    assert glossary.protect("my bad", "en", "tr").text == "my bad"


def test_expansion_feeds_phrase_lookup():
    glossary = make(
        expansions={"en": {"nt": "nice try"}},
        phrases={("en", "tr"): {"nice try": "iyi denemeydi"}},
    )

    protected = glossary.protect("nt guys", "en", "tr")

    assert protected.text == "ZX1 guys"
    assert glossary.restore(protected, "ZX1 arkadaşlar") == "iyi denemeydi arkadaşlar"


def test_restore_keeps_turkish_suffixes_and_ignores_placeholder_case():
    glossary = make(keep_exact=["B long"])

    protected = glossary.protect("go B long", "en", "tr")

    assert glossary.restore(protected, "zx1'e git") == "B long'e git"


def test_restore_without_placeholders_returns_translation():
    glossary = make(keep=["flash"])
    protected = glossary.protect("flash", "en", "tr")

    assert glossary.restore(protected, "flaş") == "flaş"


def test_text_without_terms_is_unchanged():
    glossary = make(keep=["flash"])

    protected = glossary.protect("hello there", "en", "tr")

    assert protected.text == "hello there"
    assert protected.replacements == []


def test_load_reads_toml(tmp_path):
    path = tmp_path / "glossary.toml"
    path.write_text(
        """
[expand.en]
nt = "nice try"

[keep]
terms = ["flash"]
exact = ["CT"]

[phrases.en.tr]
"my bad" = "benim hatam"
""",
        encoding="utf-8",
    )

    glossary = Glossary.load(path)

    assert glossary.expansions == {"en": {"nt": "nice try"}}
    assert glossary.keep == ["flash"]
    assert glossary.keep_exact == ["CT"]
    assert glossary.phrases == {("en", "tr"): {"my bad": "benim hatam"}}


def test_bundled_glossary_loads_and_knows_game_terms():
    glossary = Glossary.load(default_glossary_path())

    protected = glossary.protect("Smoke CT, he has an AWP. nt", "en", "tr")

    assert "AWP" not in protected.text
    assert "CT" not in protected.text
    assert "nt" not in protected.text.split()


def test_restore_capitalizes_like_the_source_sentence():
    glossary = make(phrases={("en", "tr"): {"nice try": "iyi denemeydi"}})

    protected = glossary.protect("Nice try, guys", "en", "tr")

    assert glossary.restore(protected, "ZX1, çocuklar") == "İyi denemeydi, çocuklar"


def test_restore_keeps_lowercase_when_the_source_was_lowercase():
    glossary = make(phrases={("en", "tr"): {"nice try": "iyi denemeydi"}})

    protected = glossary.protect("nice try", "en", "tr")

    assert glossary.restore(protected, "ZX1") == "iyi denemeydi"
