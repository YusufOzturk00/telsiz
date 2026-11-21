"""Command-line entry point: ``python -m telsiz`` or ``telsiz``."""

from __future__ import annotations

import argparse
import contextlib
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
LiveRunnerFn = Callable[..., int]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telsiz", description=DESCRIPTION)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--input", type=Path, metavar="WAV", help="translate a .wav file")
    mode.add_argument(
        "--live", action="store_true", help="translate what this PC plays, shown in the browser"
    )
    parser.add_argument(
        "--phone", action="store_true", help="with --live: also open the page on your phone (LAN)"
    )
    parser.add_argument(
        "--capture",
        choices=["auto", "system"],
        help="with --live: auto = only the game if possible (default), system = all PC audio",
    )
    parser.add_argument(
        "--app", metavar="EXE", help="with --live: program to listen to (default: cs2.exe)"
    )
    parser.add_argument("--port", type=int, help="with --live: web page port (default: 8765)")
    parser.add_argument(
        "--no-browser", action="store_true", help="with --live: do not open the browser"
    )
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
    if getattr(args, "port", None):
        config = dataclasses.replace(
            config, server=dataclasses.replace(config.server, port=args.port)
        )
    capture = config.capture
    if getattr(args, "capture", None):
        capture = dataclasses.replace(capture, mode=args.capture)
    if getattr(args, "app", None):
        capture = dataclasses.replace(capture, process_name=args.app)
    config = dataclasses.replace(config, capture=capture)
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


def _default_live(config: Config, **kwargs: object) -> int:
    from telsiz.serve import run_live

    return run_live(config, **kwargs)  # type: ignore[arg-type]


def main(
    argv: Sequence[str] | None = None,
    run_file: FileRunner | None = None,
    run_live: LiveRunnerFn | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.live and (args.phone or args.port or args.no_browser or args.capture or args.app):
        parser.error("--phone, --port, --no-browser, --capture and --app only work with --live")
    if args.input is None and not args.live:
        parser.print_help()
        return 0

    _setup_output(args.verbose)
    try:
        config = apply_overrides(load_config(args.config), args)
    except (OSError, ValueError) as exc:
        print(f"telsiz: invalid configuration: {exc}", file=sys.stderr)
        return 2

    def show(event: VoiceEvent) -> None:
        print(event.to_json() if args.json else format_event(event), flush=True)

    if args.live:
        live = run_live or _default_live
        try:
            return live(
                config,
                phone=args.phone,
                open_browser=config.server.open_browser and not args.no_browser,
                show=show,
            )
        except ImportError as exc:
            print(
                f"telsiz: a live-mode dependency is missing ({exc}).\n"
                'Install it with: pip install "telsiz[all]"',
                file=sys.stderr,
            )
            return 1

    if not args.input.is_file():
        print(f"telsiz: input file not found: {args.input}", file=sys.stderr)
        return 2

    runner = run_file or _default_runner
    try:
        for event in runner(config, args.input):
            show(event)
    except ImportError as exc:
        print(
            f"telsiz: a pipeline dependency is missing ({exc}).\n"
            'Install it with: pip install "telsiz[all]"',
            file=sys.stderr,
        )
        return 1
    return 0


def _console_is_ours() -> bool:
    """True when this process has a console window of its own (started by double-click)."""
    if sys.platform != "win32":
        return False
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32")
    kernel32.GetConsoleProcessList.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
    kernel32.GetConsoleProcessList.restype = wintypes.DWORD
    processes = (wintypes.DWORD * 4)()
    return kernel32.GetConsoleProcessList(processes, 4) == 1


def packaged_main(
    argv: Sequence[str] | None = None,
    *,
    app_dir: Path | None = None,
    owns_console: bool | None = None,
    wait: Callable[[str], object] = input,
    run_file: FileRunner | None = None,
    run_live: LiveRunnerFn | None = None,
) -> int:
    """Entry point of the packaged ``Telsiz.exe``.

    A double-click (no arguments) starts listening with the page on this PC; the phone
    (local network) stays opt-in. ``config.toml`` next to the exe is used if present.
    A window opened just for Telsiz waits for Enter before closing, so messages stay
    readable.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        args = ["--live"]
    folder = app_dir if app_dir is not None else Path(sys.executable).parent
    local_config = folder / "config.toml"
    if local_config.is_file() and not any(a.startswith("--config") for a in args):
        args += ["--config", str(local_config)]
    try:
        code = main(args, run_file=run_file, run_live=run_live)
    except SystemExit as exc:  # --help, --version, a usage error
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    except KeyboardInterrupt:
        code = 0
    if owns_console is None:
        owns_console = _console_is_ours()
    if owns_console:
        with contextlib.suppress(EOFError, KeyboardInterrupt):
            wait("\nPress Enter to close this window.")
    return code


if __name__ == "__main__":
    sys.exit(main())
