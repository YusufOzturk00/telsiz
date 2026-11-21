"""``python -m telsiz --live``: game (or PC) audio -> pipeline -> web page (and phone)."""

from __future__ import annotations

import logging
import socket
import sys
import webbrowser
from collections.abc import Callable

from telsiz.config import Config
from telsiz.events import VoiceEvent

log = logging.getLogger(__name__)


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def run_live(
    config: Config, *, phone: bool, open_browser: bool, show: Callable[[VoiceEvent], None]
) -> int:
    """Run until Ctrl+C. Returns a process exit code."""
    import uvicorn

    from telsiz.audio.capture import CaptureFactory
    from telsiz.bus import EventBus
    from telsiz.live import LiveRunner, latency_summary
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
    log.info("Loading models (the first run downloads them)...")
    pipeline, segmenter = build_pipeline(config)

    bus = EventBus()
    bus.add_listener(show)
    capture = CaptureFactory(
        config.capture.mode, config.capture.process_name, config.capture.helper_path
    )
    runner = LiveRunner(capture, pipeline, segmenter, bus.publish)
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
    print(f"{capture.describe()} Press Ctrl+C to stop.", flush=True)

    runner.start()
    if open_browser:
        webbrowser.open(settings.local_url)
    try:
        server.run()
    finally:
        runner.stop()
        summary = latency_summary(runner.latencies)
        if summary["count"]:
            log.info(
                "End-to-end latency over %d lines: median %d ms, p90 %d ms, max %d ms",
                summary["count"],
                summary["median_ms"],
                summary["p90_ms"],
                summary["max_ms"],
            )
    return 0
