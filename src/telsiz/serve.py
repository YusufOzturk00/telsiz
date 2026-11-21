"""``python -m telsiz --live``: game (or PC) audio -> pipeline -> web page (and phone)."""

from __future__ import annotations

import dataclasses
import logging
import socket
import sys
import webbrowser
from collections.abc import Callable
from typing import TYPE_CHECKING

from telsiz.config import Config
from telsiz.events import VoiceEvent

if TYPE_CHECKING:
    from telsiz.live import LiveRunner

log = logging.getLogger(__name__)


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def live_recognition_config(config: Config) -> Config:
    """Listening to a game: recognize speech on the CPU unless a device was chosen.

    Measured in CS2 (RTX 4060, Ryzen 5 7500F): while the game is in front during a
    match it keeps the graphics card so busy that recognizing one 4 s sentence took
    ~26 s on the GPU (with any priority) but ~3 s on the CPU, and the GPU only caught
    up after alt-tab. Recognition on the CPU also leaves the game its graphics memory.
    """
    if config.capture.mode != "auto" or config.asr.device != "auto":
        return config
    log.info(
        "Listening to the game: speech recognition runs on the CPU, because during a "
        "match the game keeps the graphics card busy (use --device cuda to override)"
    )
    return dataclasses.replace(config, asr=dataclasses.replace(config.asr, device="cpu"))


def run_live(
    config: Config, *, phone: bool, open_browser: bool, show: Callable[[VoiceEvent], None]
) -> int:
    """Run until Ctrl+C. Returns a process exit code."""
    import uvicorn

    from telsiz.audio.capture import CaptureFactory
    from telsiz.bus import EventBus
    from telsiz.live import LiveRunner
    from telsiz.perf import set_process_priority
    from telsiz.pipeline import build_pipeline
    from telsiz.server.app import ServerSettings, create_app
    from telsiz.util.net import lan_ip, new_token

    port = config.server.port
    ip = lan_ip() if phone else None
    if phone and ip == "127.0.0.1":
        log.warning("No local network found; phone mode is off, this PC only")
        ip = None
    settings = ServerSettings(port=port, lan_ip=ip, token=new_token() if ip else None)
    if not port_available(settings.bind_host, port):
        print(
            f"telsiz: port {port} is already in use. Close the other program or pick another "
            "port with --port.",
            file=sys.stderr,
        )
        return 2

    set_process_priority(config.performance.priority)
    config = live_recognition_config(config)
    log.info("Loading models (the first run downloads them)...")
    pipeline, segmenter = build_pipeline(config)

    bus = EventBus()
    bus.add_listener(show)
    capture = CaptureFactory(
        config.capture.mode, config.capture.process_name, config.capture.helper_path
    )
    runner = LiveRunner(
        capture, pipeline, segmenter, bus.publish, max_lag_s=config.performance.max_lag_s
    )
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(bus, settings),
            host=settings.bind_host,
            port=port,
            log_level="warning",
        )
    )

    print(f"Subtitles on this PC: {settings.local_url}", flush=True)
    if settings.phone_url:
        from telsiz.util.qr import qr_ascii

        print(f"Phone (same Wi-Fi): {settings.phone_url}", flush=True)
        print(qr_ascii(settings.phone_url), flush=True)
        print(
            "Windows may ask whether Python may use the network: allow it for private "
            "networks only.",
            flush=True,
        )
    elif not phone:
        how = (
            "start 'Telsiz - Telefon' in the Telsiz folder"
            if getattr(sys, "frozen", False)
            else "start with --phone"
        )
        print(f"To see the subtitles on your phone too, {how}.", flush=True)
    print(f"{capture.describe()} Press Ctrl+C to stop.", flush=True)

    runner.start()
    if open_browser:
        webbrowser.open(settings.local_url)
    try:
        server.run()
    except KeyboardInterrupt:
        pass  # Ctrl+C: stop quietly
    finally:
        print("Stopping...", flush=True)
        runner.stop()
        _log_summary(runner)
    return 0


def _log_summary(runner: LiveRunner) -> None:
    from telsiz.live import latency_summary

    summary = latency_summary(runner.latencies)
    if summary["count"]:
        log.info(
            "End-to-end latency over %d lines: median %d ms, p90 %d ms, max %d ms",
            summary["count"],
            summary["median_ms"],
            summary["p90_ms"],
            summary["max_ms"],
        )
    if runner.non_speech_clips:
        log.info(
            "%d sound clips were not speech (%.1f s spent recognizing them)",
            runner.non_speech_clips,
            runner.non_speech_ms / 1000,
        )
    if runner.skipped_s:
        log.info("Skipped %.0f s of audio to stay live", runner.skipped_s)
