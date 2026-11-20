"""Tests for the Whisper wrapper (with a fake model)."""

from types import SimpleNamespace

import numpy as np
import pytest

from telsiz.asr import (
    DEFAULT_PROMPTS,
    WhisperOptions,
    WhisperRecognizer,
    add_nvidia_dll_dirs,
    resolve_device,
    resolve_model,
)

AUDIO = np.zeros(16000, dtype=np.float32)


class FakeModel:
    def __init__(self, segments=None, languages=None):
        self.segments = segments if segments is not None else []
        self.languages = languages or [("en", 0.8), ("ru", 0.15), ("de", 0.05)]
        self.transcribe_calls = []

    def detect_language(self, audio):
        return self.languages[0][0], self.languages[0][1], self.languages

    def transcribe(self, audio, **kwargs):
        self.transcribe_calls.append(kwargs)
        return iter(self.segments), SimpleNamespace(language=kwargs.get("language"))


def segment(text, no_speech=0.1, logprob=-0.3, ratio=1.1):
    return SimpleNamespace(
        text=text, no_speech_prob=no_speech, avg_logprob=logprob, compression_ratio=ratio
    )


def make(fake, **options):
    created = {}

    def factory(name, device, compute_type, download_root, cpu_threads):
        created.update(name=name, device=device, compute_type=compute_type, cpu_threads=cpu_threads)
        return fake

    recognizer = WhisperRecognizer(WhisperOptions(device="cpu", **options), model_factory=factory)
    return recognizer, created


def test_detect_language_returns_probability_map():
    recognizer, _ = make(FakeModel())

    assert recognizer.detect_language(AUDIO) == {"en": 0.8, "ru": 0.15, "de": 0.05}


def test_transcribe_joins_segments_and_reports_worst_scores():
    model = FakeModel(
        [segment(" They're rushing B.", 0.1, -0.2, 1.1), segment(" Two AWPs. ", 0.3, -0.6, 1.9)]
    )
    recognizer, _ = make(model)

    result = recognizer.transcribe(AUDIO, "en")

    assert result.text == "They're rushing B. Two AWPs."
    assert result.language == "en"
    assert result.no_speech_prob == pytest.approx(0.3)
    assert result.avg_logprob == pytest.approx(-0.4)
    assert result.compression_ratio == pytest.approx(1.9)


def test_transcribe_with_no_segments_means_no_speech():
    recognizer, _ = make(FakeModel([]))

    result = recognizer.transcribe(AUDIO, "en")

    assert result.text == ""
    assert result.no_speech_prob == 1.0


def test_transcribe_forces_language_and_uses_game_prompt_for_english():
    model = FakeModel([segment("hi")])
    recognizer, _ = make(model)

    recognizer.transcribe(AUDIO, "en")
    recognizer.transcribe(AUDIO, "ru")

    english, russian = model.transcribe_calls
    assert english["language"] == "en"
    assert english["initial_prompt"] == DEFAULT_PROMPTS["en"]
    assert "AWP" in english["initial_prompt"]
    assert russian["language"] == "ru"
    assert russian["initial_prompt"] is None
    assert english["condition_on_previous_text"] is False


def test_custom_prompts_override_defaults():
    model = FakeModel([segment("hi")])
    recognizer, _ = make(model, prompts={"ru": "Раш Б, флешка"})

    recognizer.transcribe(AUDIO, "ru")
    recognizer.transcribe(AUDIO, "en")

    assert model.transcribe_calls[0]["initial_prompt"] == "Раш Б, флешка"
    assert model.transcribe_calls[1]["initial_prompt"] is None


def test_model_is_created_with_resolved_device():
    _, created = make(FakeModel(), model="large-v3-turbo")

    assert created == {
        "name": "large-v3-turbo",
        "device": "cpu",
        "compute_type": "int8",
        "cpu_threads": 4,
    }


def test_resolve_device_auto_prefers_cuda_when_usable():
    # int8 weights with float16 math: as accurate as float16 here, faster, lighter on the GPU
    assert resolve_device("auto", "auto", cuda_usable=True) == ("cuda", "int8_float16")
    assert resolve_device("auto", "auto", cuda_usable=False) == ("cpu", "int8")


def test_resolve_device_explicit_choices():
    assert resolve_device("cpu", "auto", cuda_usable=True) == ("cpu", "int8")
    assert resolve_device("cuda", "int8_float16", cuda_usable=True) == ("cuda", "int8_float16")


def test_resolve_device_cuda_requested_but_unusable_raises():
    with pytest.raises(RuntimeError, match="CUDA"):
        resolve_device("cuda", "auto", cuda_usable=False)


def test_resolve_device_rejects_unknown_device():
    with pytest.raises(ValueError):
        resolve_device("tpu", "auto", cuda_usable=False)


def test_add_nvidia_dll_dirs_finds_bin_folders(tmp_path, monkeypatch):
    for lib in ("cublas", "cudnn"):
        (tmp_path / "nvidia" / lib / "bin").mkdir(parents=True)
    (tmp_path / "nvidia" / "empty").mkdir()
    added = []
    monkeypatch.setattr("telsiz.asr._register_dll_dir", added.append)

    found = add_nvidia_dll_dirs([tmp_path / "nvidia"])

    assert sorted(p.parent.name for p in found) == ["cublas", "cudnn"]
    assert added == found


def test_auto_model_is_turbo_on_gpu_and_small_on_cpu():
    assert resolve_model("auto", "cuda") == "large-v3-turbo"
    assert resolve_model("auto", "cpu") == "small"
    assert resolve_model("medium", "cuda") == "medium"


def test_auto_model_is_resolved_before_loading():
    _, created = make(FakeModel(), model="auto")

    assert created["name"] == "small"  # make() forces device="cpu"


def test_cpu_threads_are_passed_to_the_model():
    _, created = make(FakeModel(), cpu_threads=2)

    assert created["cpu_threads"] == 2
