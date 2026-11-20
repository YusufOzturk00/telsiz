"""Speech recognition and language identification with faster-whisper."""

from __future__ import annotations

import ctypes
import importlib.util
import logging
import os
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from telsiz.paths import models_dir

log = logging.getLogger(__name__)

# Whisper's initial prompt biases recognition towards these words. It helps with
# game terms and with accented or broken English that the model would otherwise
# "correct" into common words.
DEFAULT_PROMPTS: dict[str, str] = {
    "en": (
        "Counter-Strike 2 team voice chat. Rush B, rotate, they're A long, B apps, mid, "
        "short, ramp, banana, connector, jungle, palace, heaven, CT, T spawn. Eco, force buy, "
        "full buy, save. AWP, AK, M4, Deagle, flash, smoke, molly, nade. Plant, defuse, "
        "bomb, one shot, lit, tagged, entry, trade, clutch."
    ),
}


@dataclass(frozen=True)
class Transcription:
    text: str
    language: str
    no_speech_prob: float
    avg_logprob: float
    compression_ratio: float


class SpeechRecognizer(Protocol):
    def detect_language(self, audio: np.ndarray) -> dict[str, float]: ...

    def transcribe(self, audio: np.ndarray, language: str) -> Transcription: ...


@dataclass(frozen=True)
class WhisperOptions:
    # auto (large-v3-turbo on a GPU, small on the CPU) | small | medium | large-v3-turbo
    model: str = "auto"
    device: str = "auto"  # auto | cuda | cpu
    compute_type: str = "auto"
    beam_size: int = 5
    cpu_threads: int = 4  # cap CPU use so the game keeps its cores; 0 = library default
    prompts: Mapping[str, str] = field(default_factory=lambda: dict(DEFAULT_PROMPTS))
    download_root: Path | None = None


def resolve_device(device: str, compute_type: str, *, cuda_usable: bool) -> tuple[str, str]:
    """Pick the device and numeric precision for CTranslate2."""
    if device not in ("auto", "cuda", "cpu"):
        raise ValueError(f"Unknown device {device!r}; use auto, cuda or cpu")
    if device == "cuda" and not cuda_usable:
        raise RuntimeError("CUDA was requested but no usable GPU / CUDA libraries were found")
    chosen = "cuda" if device == "cuda" or (device == "auto" and cuda_usable) else "cpu"
    if compute_type == "auto":
        # int8 weights + float16 math: measured as accurate as float16 (WER 11 % vs 10 %)
        # but ~25 % faster and lighter on the GPU the game is using.
        compute_type = "int8_float16" if chosen == "cuda" else "int8"
    return chosen, compute_type


def resolve_model(model: str, device: str) -> str:
    """``auto``: large-v3-turbo on a GPU (accurate and fast there), small on the CPU."""
    if model != "auto":
        return model
    return "large-v3-turbo" if device == "cuda" else "small"


_registered_dll_dirs: set[Path] = set()


def _register_dll_dir(path: Path) -> None:
    if path in _registered_dll_dirs:
        return
    _registered_dll_dirs.add(path)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(path))
    # Some CUDA libraries are loaded lazily by name, which only searches PATH.
    os.environ["PATH"] = str(path) + os.pathsep + os.environ.get("PATH", "")


def add_nvidia_dll_dirs(roots: Iterable[Path] | None = None) -> list[Path]:
    """Make DLLs from the pip ``nvidia-*-cu12`` packages loadable. Returns the dirs added."""
    if roots is None:
        spec = importlib.util.find_spec("nvidia")
        roots = [Path(p) for p in (spec.submodule_search_locations or [])] if spec else []
    found = []
    for root in roots:
        for package in sorted(Path(root).iterdir()):
            bin_dir = package / "bin"
            if bin_dir.is_dir():
                _register_dll_dir(bin_dir)
                found.append(bin_dir)
    return found


def cuda_usable() -> bool:
    """True when a CUDA GPU is present and the cuBLAS/cuDNN libraries can be loaded."""
    try:
        import ctranslate2
    except ImportError:
        return False
    if ctranslate2.get_cuda_device_count() == 0:
        return False
    add_nvidia_dll_dirs()
    if sys.platform == "win32":
        for dll in ("cublas64_12.dll", "cudnn64_9.dll"):
            try:
                ctypes.WinDLL(dll)
            except OSError:
                log.info("GPU found but %s is missing; using CPU", dll)
                return False
    return True


def _create_faster_whisper_model(
    name: str, device: str, compute_type: str, download_root: str | None, cpu_threads: int
) -> Any:
    from faster_whisper import WhisperModel

    return WhisperModel(
        name,
        device=device,
        compute_type=compute_type,
        download_root=download_root,
        cpu_threads=cpu_threads,
    )


ModelFactory = Callable[[str, str, str, "str | None", int], Any]


class WhisperRecognizer:
    def __init__(
        self, options: WhisperOptions | None = None, model_factory: ModelFactory | None = None
    ) -> None:
        self.options = options or WhisperOptions()
        factory = model_factory or _create_faster_whisper_model
        usable = cuda_usable() if self.options.device != "cpu" else False
        self.device, self.compute_type = resolve_device(
            self.options.device, self.options.compute_type, cuda_usable=usable
        )
        self.model_name = resolve_model(self.options.model, self.device)
        root = self.options.download_root or models_dir() / "whisper"
        log.info(
            "Loading Whisper %r on %s (%s); first run downloads the model",
            self.model_name,
            self.device,
            self.compute_type,
        )
        self._model = factory(
            self.model_name, self.device, self.compute_type, str(root), self.options.cpu_threads
        )

    def detect_language(self, audio: np.ndarray) -> dict[str, float]:
        _, _, all_probs = self._model.detect_language(audio)
        return {lang: float(prob) for lang, prob in all_probs}

    def transcribe(self, audio: np.ndarray, language: str) -> Transcription:
        segments, _ = self._model.transcribe(
            audio,
            language=language,
            beam_size=self.options.beam_size,
            initial_prompt=self.options.prompts.get(language),
            condition_on_previous_text=False,
            without_timestamps=True,
            vad_filter=False,
        )
        segments = list(segments)
        if not segments:
            return Transcription("", language, 1.0, -10.0, 0.0)
        return Transcription(
            text=" ".join(s.text.strip() for s in segments).strip(),
            language=language,
            no_speech_prob=max(s.no_speech_prob for s in segments),
            avg_logprob=float(np.mean([s.avg_logprob for s in segments])),
            compression_ratio=max(s.compression_ratio for s in segments),
        )
