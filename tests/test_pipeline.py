"""End-to-end pipeline tests with fake recognizer and translator."""

import numpy as np
import pytest

from helpers import write_wav
from telsiz.asr import Transcription
from telsiz.audio.file_source import FileSource
from telsiz.language import LanguageSelector
from telsiz.pipeline import Pipeline, PipelineSettings
from telsiz.translate.base import TranslationUnavailable
from telsiz.vad import Utterance, UtteranceSegmenter

ALLOWED = ["en", "ru", "tr"]


class LoudnessDetector:
    frame_samples = 512

    def __call__(self, frames):
        blocks = frames.reshape(-1, self.frame_samples)
        return np.clip(np.sqrt(np.mean(blocks**2, axis=1)) * 10, 0, 1).astype(np.float32)


class FakeRecognizer:
    """Returns scripted results in order."""

    def __init__(self, *scripted):
        self.scripted = list(scripted)
        self.forced_languages = []

    def _current(self):
        return self.scripted[0]

    def detect_language(self, audio):
        return self._current()["probs"]

    def transcribe(self, audio, language):
        self.forced_languages.append(language)
        item = self.scripted.pop(0)
        return Transcription(
            text=item["text"],
            language=language,
            no_speech_prob=item.get("no_speech", 0.05),
            avg_logprob=-0.2,
            compression_ratio=1.3,
        )


class FakeTranslator:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def translate(self, text, source, target):
        self.calls.append((text, source, target))
        if self.fail:
            raise TranslationUnavailable("nope")
        return f"<{target}>{text}"

    def prepare(self, sources, target):
        pass


def utterance(seconds=2.0, end=2.0):
    return Utterance(np.zeros(int(seconds * 16000), np.float32), end - seconds, end)


def make(recognizer, translator=None, **settings):
    return Pipeline(
        recognizer,
        translator or FakeTranslator(),
        LanguageSelector(ALLOWED),
        PipelineSettings(target_lang="tr", **settings),
        clock=lambda: 1732100000.5,
    )


def test_utterance_becomes_translated_event():
    recognizer = FakeRecognizer({"probs": {"en": 0.9, "ru": 0.1}, "text": "Rush B"})
    translator = FakeTranslator()

    event = make(recognizer, translator).process_utterance(utterance())

    assert event.source_lang == "en"
    assert event.source_lang_confidence == pytest.approx(0.9)
    assert event.original == "Rush B"
    assert event.translated == "<tr>Rush B"
    assert event.target_lang == "tr"
    assert event.ts == 1732100000.5
    assert event.latency_ms >= 0
    assert translator.calls == [("Rush B", "en", "tr")]


def test_transcription_uses_the_selected_language():
    recognizer = FakeRecognizer({"probs": {"ja": 0.8, "ru": 0.2}, "text": "Они идут на Б"})

    event = make(recognizer).process_utterance(utterance())

    assert recognizer.forced_languages == ["ru"]
    assert event.source_lang == "ru"


def test_same_language_is_shown_untranslated_by_default():
    translator = FakeTranslator()
    recognizer = FakeRecognizer({"probs": {"tr": 0.95}, "text": "B'ye geliyorlar"})

    event = make(recognizer, translator).process_utterance(utterance())

    assert event.translated == "B'ye geliyorlar"
    assert translator.calls == []


def test_same_language_can_be_hidden():
    recognizer = FakeRecognizer({"probs": {"tr": 0.95}, "text": "selam"})

    assert make(recognizer, same_language="hide").process_utterance(utterance()) is None


def test_hallucinations_are_dropped_before_translation():
    translator = FakeTranslator()
    recognizer = FakeRecognizer({"probs": {"en": 0.9}, "text": "Thank you."})

    assert make(recognizer, translator).process_utterance(utterance()) is None
    assert translator.calls == []


def test_translation_failure_still_reports_the_original():
    recognizer = FakeRecognizer({"probs": {"en": 0.9}, "text": "Rush B"})

    event = make(recognizer, FakeTranslator(fail=True)).process_utterance(utterance())

    assert event.original == "Rush B"
    assert event.translated is None


def test_run_processes_a_wav_file_end_to_end(tmp_path):
    rng = np.random.default_rng(0)
    rate = 44100
    burst = (0.3 * rng.standard_normal((rate, 2))).astype(np.float32)
    gap = np.zeros((rate, 2), np.float32)
    path = write_wav(tmp_path / "talk.wav", np.concatenate([gap, burst, gap, burst, gap]), rate)
    recognizer = FakeRecognizer(
        {"probs": {"en": 0.9}, "text": "Rush B"},
        {"probs": {"ru": 0.9}, "text": "Они идут на Б"},
    )
    pipeline = make(recognizer)

    events = list(pipeline.run(FileSource(path), UtteranceSegmenter(LoudnessDetector())))

    assert [e.original for e in events] == ["Rush B", "Они идут на Б"]
    assert [e.source_lang for e in events] == ["en", "ru"]


def test_glossary_protects_game_terms_around_translation():
    from telsiz.glossary import Glossary

    glossary = Glossary(expansions={}, keep=["AWP"], keep_exact=[], phrases={})
    translator = FakeTranslator()
    recognizer = FakeRecognizer({"probs": {"en": 0.9}, "text": "he has an AWP"})

    event = make(recognizer, translator, glossary=glossary).process_utterance(utterance())

    assert translator.calls == [("he has an ZX1", "en", "tr")]
    assert event.translated == "<tr>he has an AWP"
    assert event.original == "he has an AWP"


def test_stage_timings_are_recorded():
    recognizer = FakeRecognizer({"probs": {"en": 0.9}, "text": "Rush B"})
    pipeline = make(recognizer)

    pipeline.process_utterance(utterance())

    assert set(pipeline.last_timings) == {"asr_ms", "translation_ms"}
    assert all(v >= 0 for v in pipeline.last_timings.values())
