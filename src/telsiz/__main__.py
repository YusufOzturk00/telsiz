"""Command-line entry point: ``python -m telsiz`` or ``telsiz``."""

from __future__ import annotations

import argparse
import dataclasses
import logging
import sys
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

from telsiz import __version__
from telsiz.config import Config, load_config, validate
from telsiz.events import VoiceEvent

DESCRIPTION = "Real-time voice chat translator for CS2"

FileRunner = Callable[[Config, Path], Iterator[VoiceEvent]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telsiz", description=DESCRIPTION)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--input", type=Path, metavar="WAV", help="translate a .wav file")
    parser.add_argument("--target", metavar="LANG", help="target language code, e.g. tr")
    parser.add_argument("--config", type=Path, metavar="TOML", help="settings file")
    parser.add_argument(
        "--model", help="Whisper model: small, medium or large-v3-turbo (default: small)"
    )
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], help="inference device")
    parser.add_argument("--json", action="store_true", help="print events as JSON lines")
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug logging")
    return parser


def apply_overrides(config: Config, args: argparse.Namespace) -> Config:
    asr = config.asr
    if args.model:
        asr = dataclasses.replace(asr, model=args.model)
    if args.device:
        asr = dataclasses.replace(asr, device=args.device)
    config = dataclasses.replace(config, asr=asr)
    if args.target:
        config = dataclasses.replace(config, target_lang=args.target)
    return validate(config)


def format_event(event: VoiceEvent) -> str:
    head = f"[{event.source_lang.upper()} {event.source_lang_confidence:.2f}] {event.original}"
    tail = f"  ({event.latency_ms} ms)"
    if event.translated is None:
        return f"{head} → (no translation){tail}"
    if event.source_lang == event.target_lang:
        return f"{head}{tail}"
    return f"{head} → {event.translated}{tail}"


def _setup_output(verbose: bool) -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.WARNING, format="telsiz: %(message)s", stream=sys.stderr)
    logging.getLogger("telsiz").setLevel(logging.DEBUG if verbose else logging.INFO)


def _default_runner(config: Config, path: Path) -> Iterator[VoiceEvent]:
    from telsiz.pipeline import run_file

    return run_file(config, path)


def main(argv: Sequence[str] | None = None, run_file: FileRunner | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.input is None:
        parser.print_help()
        return 0

    _setup_output(args.verbose)
    try:
        config = apply_overrides(load_config(args.config), args)
    except (OSError, ValueError) as exc:
        print(f"telsiz: invalid configuration: {exc}", file=sys.stderr)
        return 2
    if not args.input.is_file():
        print(f"telsiz: input file not found: {args.input}", file=sys.stderr)
        return 2

    runner = run_file or _default_runner
    try:
        for event in runner(config, args.input):
            print(event.to_json() if args.json else format_event(event), flush=True)
    except ImportError as exc:
        print(
            f"telsiz: a pipeline dependency is missing ({exc}).\n"
            'Install it with: pip install "telsiz[all]"',
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
