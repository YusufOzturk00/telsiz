"""M1 acceptance: real Whisper + Argos models on the CC0/public-domain clips.

Run with ``pytest -m slow`` (needs the whisper and argos extras; the first run
downloads models).
"""

import re
import tomllib
from pathlib import Path

import pytest

from telsiz.audio.file_source import FileSource
from telsiz.language import LanguageSelector
from telsiz.pipeline import Pipeline, PipelineSettings
from telsiz.quality.metrics import word_error_rate
from telsiz.vad import UtteranceSegmenter

pytestmark = pytest.mark.slow

FIXTURES = Path(__file__).parent / "fixtures"
MANIFEST = FIXTURES / "manifest.toml"
ALLOWED = ["en", "ru", "uk", "pl", "de", "tr"]
CLIPS = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))["clips"] if MANIFEST.is_file() else []
CYRILLIC = re.compile(r"[А-Яа-яЁёІіЇїЄєҐґ]")


@pytest.fixture(scope="module")
def recognizer():
    pytest.importorskip("faster_whisper")
    from telsiz.asr import WhisperOptions, WhisperRecognizer

    return WhisperRecognizer(WhisperOptions(model="small"))


@pytest.fixture(scope="module")
def translator():
    pytest.importorskip("ctranslate2")
    from telsiz.translate.argos import create_argos_translator

    engine = create_argos_translator()
    engine.prepare(["en", "ru"], "tr")
    return engine


@pytest.mark.parametrize("clip", CLIPS, ids=[c["file"] for c in CLIPS])
def test_clip_is_detected_transcribed_and_translated(clip, recognizer, translator):
    from telsiz.vad import SileroDetector

    pipeline = Pipeline(
        recognizer, translator, LanguageSelector(ALLOWED), PipelineSettings(target_lang="tr")
    )
    events = list(
        pipeline.run(FileSource(FIXTURES / clip["file"]), UtteranceSegmenter(SileroDetector()))
    )

    assert events, "no speech was recognized"
    assert {e.source_lang for e in events} == {clip["language"]}
    original = " ".join(e.original for e in events)
    translated = " ".join(e.translated or "" for e in events)
    assert word_error_rate(clip["text"], original, clip["language"]) < 0.35
    assert translated.strip()
    assert translated != original
    assert not CYRILLIC.search(translated)
