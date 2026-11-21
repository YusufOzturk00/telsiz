"""Speech recognition and language identification with faster-whisper."""

from __future__ import annotations

import ctypes
import hashlib
import importlib.util
import logging
import math
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


# faster-whisper's default retry chain: when a decode looks unsure (low average log
# probability) or repetitive, the clip is decoded again with sampling at each
# temperature, five candidates each time.
FALLBACK_TEMPERATURES: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)

# Whisper pads every clip to a 30 s window, but live clips are at most ~6 s long. On
# the CPU the encoder spent most of its time on that padding. Shorter windows, measured
# on the test clips (cut by the live VAD, clean and with voice-chat noise, int8, 4 threads):
#   small           30 s: WER 39 %, 1.57 s per clip   10 s: WER 38 %, 0.39 s
#   large-v3-turbo  30 s: WER 26 %, 6.44 s per clip   15 s: WER 26 %, 2.18 s
# Shorter still costs accuracy (small 10 s -> clip + 1 s: 44 %; turbo 15 s -> 10 s: 39 %).
FULL_WINDOW_S = 30.0
CPU_WINDOWS_S: dict[str, float] = {"small": 10.0, "large-v3-turbo": 15.0, "turbo": 15.0}
FRAMES_PER_SECOND = 100  # Whisper's log-mel frames (10 ms hop)


def resolve_window(window_s: float, model: str, device: str) -> float:
    """Seconds of audio the encoder sees per clip; ``window_s`` > 0 is the user's choice."""
    if window_s > 0:
        return window_s
    if device == "cpu":
        return CPU_WINDOWS_S.get(model, FULL_WINDOW_S)
    return FULL_WINDOW_S  # unmeasured model, or a GPU (fast enough for the full window)


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
    # Off: decode each clip once. In CS2 matches the retry chain re-decoded ~27 % of
    # clips (game noise makes Whisper unsure) and took ~4.7 s instead of ~2.2 s per
    # line, without better text.
    temperature_fallback: bool = False
    window_s: float = 0.0  # encoder window; 0 = by model and device (resolve_window)
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


class EncoderCache:
    """Runs Whisper's encoder once per clip, on a window shorter than 30 s if asked.

    Language detection and transcription each run the encoder, the most expensive
    step, on the same window. Caching the last result by content halves the work per
    utterance (and the CPU or GPU time taken from the game). ``window_frames`` trims
    the zero padding faster-whisper adds up to 30 s, but never the clip itself.
    """

    def __init__(
        self, encode: Callable[[np.ndarray], Any], window_frames: int | None = None
    ) -> None:
        self._encode = encode
        self._window = window_frames
        self._key: tuple[tuple[int, ...], bytes] | None = None
        self._value: Any = None
        self.hits = 0

    def __call__(self, features: np.ndarray) -> Any:
        data = np.ascontiguousarray(features)
        key = (data.shape, hashlib.blake2b(data.tobytes(), digest_size=16).digest())
        if key == self._key:
            self.hits += 1
            return self._value
        self._value = self._encode(self._trim(data))
        self._key = key
        return self._value

    def _trim(self, features: np.ndarray) -> np.ndarray:
        total = features.shape[-1]
        if self._window is None or self._window >= total:
            return features
        frame_has_sound = np.any(features != 0, axis=tuple(range(features.ndim - 1)))
        sounding = np.flatnonzero(frame_has_sound)
        content = int(sounding[-1]) + 1 if sounding.size else 0
        whole_seconds = math.ceil(content / FRAMES_PER_SECOND) * FRAMES_PER_SECOND
        frames = max(self._window, whole_seconds)
        return features if frames >= total else np.ascontiguousarray(features[..., :frames])


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
        self.window_s = resolve_window(self.options.window_s, self.model_name, self.device)
        root = self.options.download_root or models_dir() / "whisper"
        log.info(
            "Loading Whisper %r on %s (%s, %g s window); first run downloads the model",
            self.model_name,
            self.device,
            self.compute_type,
            self.window_s,
        )
        self._model = factory(
            self.model_name, self.device, self.compute_type, str(root), self.options.cpu_threads
        )
        if callable(getattr(self._model, "encode", None)) and hasattr(
            self._model, "feature_extractor"
        ):
            window = None
            if self.window_s < FULL_WINDOW_S:
                window = round(self.window_s * FRAMES_PER_SECOND)
            self._model.encode = EncoderCache(self._model.encode, window)

    def detect_language(self, audio: np.ndarray) -> dict[str, float]:
        model = self._model
        if not isinstance(getattr(model, "encode", None), EncoderCache):
            _, _, all_probs = model.detect_language(audio)
            return {lang: float(prob) for lang, prob in all_probs}
        # Encode exactly the window transcribe() will decode (it drops the last feature
        # frame), so the encoder cache serves transcribe() and the clip is encoded once.
        from faster_whisper.audio import pad_or_trim

        extractor = model.feature_extractor
        features = extractor(audio)
        frames = min(extractor.nb_max_frames, features.shape[-1] - 1)
        encoded = model.encode(pad_or_trim(features[:, :frames]))
        results = model.model.detect_language(encoded)[0]
        return {token[2:-2]: float(prob) for token, prob in results}

    def transcribe(self, audio: np.ndarray, language: str) -> Transcription:
        segments, _ = self._model.transcribe(
            audio,
            language=language,
            beam_size=self.options.beam_size,
            temperature=FALLBACK_TEMPERATURES if self.options.temperature_fallback else 0.0,
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
