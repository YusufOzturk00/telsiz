"""Turkish suffix fixes after restored glossary terms.

The translator attaches case suffixes to a placeholder ("ZX1'e") without
knowing how the real term sounds. Given a Turkish reading of the term
("be long" for "B long", "siti" for "CT"), the suffix is rebuilt with:

* vowel harmony (two-way a/e, four-way ı/i/u/ü),
* buffer letters after vowels (dative "ye", accusative "yı", genitive "nın",
  instrumental "yla"),
* consonant hardening after voiceless sounds ("de" -> "te").
"""

from __future__ import annotations

VOWELS = "aeıioöuü"
BACK = "aıou"
ROUNDED = "oöuü"
VOICELESS = "çfhkpsşt"
FOUR_WAY = "ıiuü"


def _four_way(previous: str) -> str:
    if previous in BACK:
        return "u" if previous in ROUNDED else "ı"
    return "ü" if previous in ROUNDED else "i"


def _harmonize(core: str, previous: str, ends_voiceless: bool) -> str:
    out = []
    for index, char in enumerate(core):
        if char in "ae":
            char = "a" if previous in BACK else "e"
            previous = char
        elif char in FOUR_WAY:
            char = _four_way(previous)
            previous = char
        elif char in "oö":
            previous = char
        elif index == 0 and char in "dt":
            char = "t" if ends_voiceless else "d"
        out.append(char)
    return "".join(out)


def harmonize_suffix(reading: str, suffix: str) -> str:
    """Rewrite ``suffix`` so it fits a word pronounced like ``reading``."""
    if not suffix:
        return suffix
    sound = reading.strip().lower()
    vowels = [c for c in sound if c in VOWELS]
    previous = vowels[-1] if vowels else "e"
    ends_vowel = bool(sound) and sound[-1] in VOWELS
    ends_voiceless = bool(sound) and sound[-1] in VOICELESS

    core = suffix.lower()
    # Drop the buffer letter the translator chose; it is re-added below if needed.
    y_buffer = core[:1] == "y" and (core[1:2] in tuple(VOWELS) or core[1:3] in ("la", "le"))
    n_buffer = core[:1] == "n" and core[1:2] in tuple(FOUR_WAY) and core[2:3] == "n"
    if y_buffer or n_buffer:
        core = core[1:]

    tail = ""
    if len(core) > 2 and core.endswith("ki"):  # "-daki" style: "ki" never harmonizes
        core, tail = core[:-2], "ki"

    buffer = ""
    if ends_vowel:
        if core[:1] in FOUR_WAY and core[1:2] == "n":
            buffer = "n"  # genitive
        elif core[:1] in VOWELS or core in ("la", "le"):
            buffer = "y"  # dative, accusative, instrumental
    return buffer + _harmonize(core, previous, ends_voiceless) + tail
