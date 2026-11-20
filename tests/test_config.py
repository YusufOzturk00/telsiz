"""Tests for config.toml loading."""

from pathlib import Path

import pytest

from telsiz.asr import DEFAULT_PROMPTS
from telsiz.config import Config, load_config

EXAMPLE = Path(__file__).resolve().parents[1] / "config.example.toml"


def write(tmp_path, text):
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_defaults_without_a_file():
    config = load_config(None)

    assert config.target_lang == "tr"
    assert config.allowed_source_langs == ["en", "ru", "uk", "pl", "de", "tr"]
    assert config.asr.model == "small"
    assert config.asr.device == "auto"
    assert config.language.min_confidence == 0.6
    assert config.language.min_duration_s == 1.2
    assert config.language.sticky_window_s == 30.0
    assert config.vad.max_utterance_s == 10.0
    assert config.filter.no_speech_threshold == 0.6
    assert config.same_language == "show"
    assert config.translate.engine == "argos"


def test_example_file_matches_the_defaults():
    assert load_config(EXAMPLE) == Config()


def test_file_values_override_defaults(tmp_path):
    path = write(
        tmp_path,
        """
target_lang = "de"
allowed_source_langs = ["en", "ru"]
same_language = "hide"

[asr]
model = "large-v3-turbo"
device = "cuda"

[language]
min_confidence = 0.7

[vad]
max_utterance_s = 8.0
""",
    )

    config = load_config(path)

    assert config.target_lang == "de"
    assert config.allowed_source_langs == ["en", "ru"]
    assert config.same_language == "hide"
    assert config.asr.model == "large-v3-turbo"
    assert config.asr.device == "cuda"
    assert config.asr.beam_size == 5
    assert config.language.min_confidence == 0.7
    assert config.vad.max_utterance_s == 8.0
    assert config.vad.speech_pad_ms == 200


def test_prompts_merge_with_defaults(tmp_path):
    path = write(tmp_path, '[asr.prompts]\nru = "Раш Б"\n')

    prompts = load_config(path).asr.prompts

    assert prompts["ru"] == "Раш Б"
    assert prompts["en"] == DEFAULT_PROMPTS["en"]


def test_unknown_keys_are_reported(tmp_path):
    path = write(tmp_path, "[asr]\nmodle = 'small'\n")

    with pytest.raises(ValueError, match="asr.modle"):
        load_config(path)


@pytest.mark.parametrize(
    "text",
    [
        'same_language = "maybe"',
        '[translate]\nengine = "google"',
        "allowed_source_langs = []",
        '[asr]\ndevice = "tpu"',
    ],
)
def test_invalid_values_are_rejected(tmp_path, text):
    with pytest.raises(ValueError):
        load_config(write(tmp_path, text))


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.toml")
