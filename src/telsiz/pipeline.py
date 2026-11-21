"""Audio source -> VAD -> Whisper -> language rules -> filter -> translator -> events."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from telsiz.asr import SpeechRecognizer
from telsiz.audio.base import AudioSource
from telsiz.audio.resample import Resampler, to_mono
from telsiz.config import Config
from telsiz.events import VoiceEvent
from telsiz.filters import FilterOptions, is_hallucination
from telsiz.glossary import Glossary, default_glossary_path
from telsiz.language import LanguageSelector
from telsiz.translate.base import TranslationUnavailable, Translator
from telsiz.vad import Utterance, UtteranceSegmenter

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineSettings:
    target_lang: str
    same_language: str = "show"
    filter_options: FilterOptions = field(default_factory=FilterOptions)
    glossary: Glossary | None = None


class Pipeline:
    def __init__(
        self,
        recognizer: SpeechRecognizer,
        translator: Translator,
        selector: LanguageSelector,
        settings: PipelineSettings,
        clock: Callable[[], float] = time.time,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.recognizer = recognizer
        self.translator = translator
        self.selector = selector
        self.settings = settings
        self._clock = clock
        self._timer = timer
        self.last_timings: dict[str, int] = {}

    def process_utterance(self, utt: Utterance) -> VoiceEvent | None:
        started = self._timer()
        target = self.settings.target_lang

        probs = self.recognizer.detect_language(utt.audio)
        decision = self.selector.choose(probs, utt.duration, now=utt.end)
        result = self.recognizer.transcribe(utt.audio, decision.language)
        recognized = self._timer()
        self.last_timings = {"asr_ms": round((recognized - started) * 1000), "translation_ms": 0}

        if is_hallucination(
            result.text,
            no_speech_prob=result.no_speech_prob,
            avg_logprob=result.avg_logprob,
            compression_ratio=result.compression_ratio,
            options=self.settings.filter_options,
        ):
            log.debug("Dropped likely hallucination: %r", result.text)
            return None

        if decision.language == target:
            if self.settings.same_language == "hide":
                return None
            translated: str | None = result.text
        else:
            try:
                translated = self._translate(result.text, decision.language, target)
            except TranslationUnavailable as exc:
                log.warning("%s", exc)
                translated = None
            self.last_timings["translation_ms"] = round((self._timer() - recognized) * 1000)

        return VoiceEvent(
            source_lang=decision.language,
            source_lang_confidence=round(decision.confidence, 3),
            original=result.text,
            translated=translated,
            target_lang=target,
            latency_ms=round((self._timer() - started) * 1000),
            ts=self._clock(),
        )

    def _translate(self, text: str, source: str, target: str) -> str:
        glossary = self.settings.glossary
        if glossary is None:
            return self.translator.translate(text, source, target)
        protected = glossary.protect(text, source, target)
        translated = self.translator.translate(protected.text, source, target)
        return glossary.restore(protected, translated)

    def run(self, source: AudioSource, segmenter: UtteranceSegmenter) -> Iterator[VoiceEvent]:
        resampler: Resampler | None = None
        for chunk in source.chunks():
            if resampler is None or resampler.in_rate != chunk.sample_rate:
                resampler = Resampler(chunk.sample_rate)
            for utt in segmenter.feed(resampler.process(to_mono(chunk))):
                yield from self._emit(utt)
        for utt in segmenter.flush():
            yield from self._emit(utt)

    def _emit(self, utt: Utterance) -> Iterator[VoiceEvent]:
        event = self.process_utterance(utt)
        if event is not None:
            yield event


def build_pipeline(config: Config) -> tuple[Pipeline, UtteranceSegmenter]:
    """Load the real models described by ``config``. Slow: downloads on first use."""
    from telsiz.asr import WhisperOptions, WhisperRecognizer
    from telsiz.translate.factory import create_translator
    from telsiz.vad import SileroDetector

    recognizer = WhisperRecognizer(
        WhisperOptions(
            model=config.asr.model,
            device=config.asr.device,
            compute_type=config.asr.compute_type,
            beam_size=config.asr.beam_size,
            temperature_fallback=config.asr.temperature_fallback,
            window_s=config.asr.window_s,
            cpu_threads=config.performance.cpu_threads,
            prompts={k: v for k, v in config.asr.prompts.items() if v},
        )
    )
    translator = create_translator(config)
    sources = [lang for lang in config.allowed_source_langs if lang != config.target_lang]
    translator.prepare(sources, config.target_lang)

    selector = LanguageSelector(
        config.allowed_source_langs,
        min_confidence=config.language.min_confidence,
        min_duration_s=config.language.min_duration_s,
        window_s=config.language.sticky_window_s,
    )
    glossary = None
    if config.glossary.enabled:
        glossary = Glossary.load(config.glossary.path or default_glossary_path())
    settings = PipelineSettings(config.target_lang, config.same_language, config.filter, glossary)
    pipeline = Pipeline(recognizer, translator, selector, settings)
    return pipeline, UtteranceSegmenter(SileroDetector(), config.vad)


def run_file(config: Config, path: Path) -> Iterator[VoiceEvent]:
    """Build the real components from ``config`` and translate one WAV file."""
    from telsiz.audio.file_source import FileSource

    pipeline, segmenter = build_pipeline(config)
    yield from pipeline.run(FileSource(path), segmenter)
