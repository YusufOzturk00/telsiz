"""FastAPI app: the subtitle page, a WebSocket event stream and phone pairing.

Security (CLAUDE.md section 8):

* By default the server listens on 127.0.0.1 only.
* In phone mode it listens on the LAN and every request from another device
  must carry the per-run access token; this PC itself does not need it.
* WebSocket handshakes from other websites are refused (Origin check), and
  unknown Host headers are refused, so a web page in the browser cannot read
  the stream through 127.0.0.1 or DNS rebinding.
* Pages are sent with ``Referrer-Policy: no-referrer`` so the token in the
  phone URL is never passed on, and a strict Content-Security-Policy.
"""

from __future__ import annotations

import asyncio
import ipaddress
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import anyio
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from telsiz.bus import EventBus
from telsiz.util.net import phone_url

STATIC_DIR = Path(__file__).with_name("static")

_CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
    "connect-src 'self' ws: wss:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
)
_POLICY_VIOLATION = 1008


@dataclass(frozen=True)
class ServerSettings:
    port: int = 8765
    lan_ip: str | None = None  # set in phone mode
    token: str | None = None  # required from other devices in phone mode

    @property
    def phone_mode(self) -> bool:
        return self.lan_ip is not None

    @property
    def bind_host(self) -> str:
        return "0.0.0.0" if self.phone_mode else "127.0.0.1"

    @property
    def local_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"

    @property
    def phone_url(self) -> str | None:
        if self.lan_ip is None or self.token is None:
            return None
        return phone_url(self.lan_ip, self.port, self.token)


def _is_this_pc(host: str | None) -> bool:
    if not host:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def create_app(bus: EventBus, settings: ServerSettings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        bus.bind(asyncio.get_running_loop())
        yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    hosts = ["127.0.0.1", "localhost"] + ([settings.lan_ip] if settings.lan_ip else [])
    origins = {f"http://{host}:{settings.port}" for host in hosts}
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = _CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    def allowed(client_host: str | None, token: str | None) -> bool:
        if not settings.phone_mode or _is_this_pc(client_host):
            return True
        expected = settings.token or ""
        return bool(token) and bool(expected) and secrets.compare_digest(token, expected)

    @app.get("/", response_model=None)
    async def index(request: Request, token: str | None = None) -> Response:
        client = request.client.host if request.client else None
        if not allowed(client, token):
            return PlainTextResponse(
                "Telsiz: missing or wrong access token. Scan the QR code on the PC again.",
                status_code=403,
            )
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/pairing", response_model=None)
    async def pairing(request: Request) -> Response:
        if not _is_this_pc(request.client.host if request.client else None):
            return PlainTextResponse("Only available on this PC", status_code=403)
        return JSONResponse({"phone_url": settings.phone_url})

    @app.get("/qr.svg", response_model=None)
    async def qr(request: Request) -> Response:
        if not _is_this_pc(request.client.host if request.client else None):
            return PlainTextResponse("Only available on this PC", status_code=403)
        url = settings.phone_url
        if url is None:
            return PlainTextResponse("Phone mode is off", status_code=404)
        from telsiz.util.qr import qr_svg

        return Response(qr_svg(url), media_type="image/svg+xml")

    @app.websocket("/ws")
    async def stream(websocket: WebSocket) -> None:
        origin = websocket.headers.get("origin")
        client = websocket.client.host if websocket.client else None
        if (origin and origin not in origins) or not allowed(
            client, websocket.query_params.get("token")
        ):
            await websocket.close(code=_POLICY_VIOLATION)
            return
        await websocket.accept()
        events = bus.subscribe()
        try:
            # Send events until the client goes away; a task group cancels both
            # halves cleanly, including when the server itself is shutting down.
            async with anyio.create_task_group() as group:

                async def pump() -> None:
                    try:
                        async for event in events:
                            await websocket.send_text(event.to_json())
                    except (WebSocketDisconnect, RuntimeError):
                        pass
                    group.cancel_scope.cancel()

                async def until_closed() -> None:
                    while (await websocket.receive())["type"] != "websocket.disconnect":
                        pass
                    group.cancel_scope.cancel()

                group.start_soon(pump)
                group.start_soon(until_closed)
        finally:
            await events.aclose()

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app
