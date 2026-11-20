"""Measure language detection and word error rate on the test clips.

    python scripts/eval_asr.py [--model small] [--device auto] [--out report.md]

Each clip is tested clean and through two simulated voice-chat profiles,
with and without the game-term prompt for English. Needs the ``whisper``
extra; downloads the Whisper model on first run.
"""

from __future__ import annotations

import argparse
import sys
import time
import tomllib
from pathlib import Path

import numpy as np

from telsiz.asr import DEFAULT_PROMPTS, WhisperOptions, WhisperRecognizer
from telsiz.audio.file_source import FileSource
from telsiz.audio.resample import Resampler, to_mono
from telsiz.language import LanguageSelector
from telsiz.quality.degrade import VoiceChatProfile, simulate_voice_chat
from telsiz.quality.metrics import word_error_rate

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = ["en", "ru", "uk", "pl", "de", "tr"]
CONDITIONS = {
    "clean": None,
    "voice chat": VoiceChatProfile(),
    "bad voice chat": VoiceChatProfile(snr_db=5.0, drive=4.0, packet_loss=0.05),
}


def load_clip(path: Path) -> np.ndarray:
    chunks = list(FileSource(path).chunks())
    resampler = Resampler(chunks[0].sample_rate)
    return np.concatenate([resampler.process(to_mono(c)) for c in chunks])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixtures", type=Path, default=ROOT / "tests/fixtures")
    parser.add_argument("--model", default="small")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    clips = tomllib.loads((args.fixtures / "manifest.toml").read_text(encoding="utf-8"))["clips"]
    with_prompt = WhisperRecognizer(WhisperOptions(model=args.model, device=args.device))
    no_prompt = WhisperRecognizer(WhisperOptions(model=args.model, device=args.device, prompts={}))

    lines = [
        f"# Speech recognition check: Whisper {args.model} on {with_prompt.device}",
        "",
        "| Clip | Condition | Prompt | Detected | WER | Time | Transcript |",
        "|---|---|---|---|---|---|---|",
    ]
    for clip in clips:
        audio = load_clip(args.fixtures / clip["file"])
        for condition, profile in CONDITIONS.items():
            sample = audio if profile is None else simulate_voice_chat(audio, profile, seed=7)
            variants = [("yes", with_prompt)]
            if clip["language"] in DEFAULT_PROMPTS:
                variants.append(("no", no_prompt))
            for prompt_label, recognizer in variants:
                started = time.perf_counter()
                probs = recognizer.detect_language(sample)
                decision = LanguageSelector(ALLOWED).choose(probs, len(sample) / 16000, now=0.0)
                result = recognizer.transcribe(sample, decision.language)
                elapsed = (time.perf_counter() - started) * 1000
                wer = word_error_rate(clip["text"], result.text)
                mark = "" if decision.language == clip["language"] else " ❌"
                lines.append(
                    f"| {clip['file']} | {condition} | {prompt_label} "
                    f"| {decision.language} {decision.confidence:.2f}{mark} | {wer:.0%} "
                    f"| {elapsed:.0f} ms | {result.text} |"
                )

    report = "\n".join(lines) + "\n"
    sys.stdout.reconfigure(encoding="utf-8")
    print(report)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
