"""Tests for the local web server (second screen and phone).

WebSocket URLs are absolute because the test client otherwise sends
"Host: testserver", which the trusted-host check rightly refuses.
"""

import json
import threading

import pytest

pytest.importorskip("fastapi")

from starlette.testclient import TestClient  # noqa: E402
from starlette.websockets import WebSocketDisconnect  # noqa: E402

from telsiz.bus import EventBus  # noqa: E402
from telsiz.events import VoiceEvent  # noqa: E402
from telsiz.server.app import ServerSettings, create_app  # noqa: E402

PORT = 8765
TOKEN = "s3cret-token"
LAN_IP = "192.168.1.20"
LOCAL = ("127.0.0.1", 50000)
PHONE = ("192.168.1.55", 50000)


def event(text):
    return VoiceEvent("ru", 0.93, text, f"<{text}>", "tr", 900, ts=1.0)


def client(bus, *, lan=False, peer=LOCAL, host="127.0.0.1"):
    settings = ServerSettings(
        port=PORT, lan_ip=LAN_IP if lan else None, token=TOKEN if lan else None
    )
    return TestClient(create_app(bus, settings), base_url=f"http://{host}:{PORT}", client=peer)


def test_index_is_served_to_the_local_browser():
    with client(EventBus()) as c:
        response = c.get("/")

    assert response.status_code == 200
    assert "Telsiz" in response.text
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'self'" in response.headers["content-security-policy"]


def test_static_assets_are_served():
    with client(EventBus()) as c:
        assert c.get("/static/app.js").status_code == 200
        assert c.get("/static/style.css").status_code == 200
        icon = c.get("/static/icon.svg")
        assert icon.status_code == 200
        assert icon.headers["content-type"].startswith("image/svg+xml")
        assert 'rel="icon" href="/static/icon.svg"' in c.get("/").text


def test_websocket_streams_history_then_live_events():
    bus = EventBus()
    bus.publish(event("старое"))
    with (
        client(bus) as c,
        c.websocket_connect(
            f"ws://127.0.0.1:{PORT}/ws", headers={"origin": f"http://127.0.0.1:{PORT}"}
        ) as ws,
    ):
        first = json.loads(ws.receive_text())
        threading.Thread(target=bus.publish, args=(event("новое"),)).start()
        second = json.loads(ws.receive_text())

    assert first["original"] == "старое"
    assert second["original"] == "новое"
    assert second["translated"] == "<новое>"
    assert second["type"] == "voice"


def test_websocket_from_a_foreign_website_is_rejected():
    with (
        client(EventBus()) as c,
        pytest.raises(WebSocketDisconnect) as exc,
        c.websocket_connect(
            f"ws://127.0.0.1:{PORT}/ws", headers={"origin": "https://evil.example"}
        ) as ws,
    ):
        ws.receive_text()

    assert exc.value.code == 1008


def test_unknown_host_header_is_rejected():
    with client(EventBus(), host="attacker.example") as c:
        assert c.get("/").status_code == 400


# --- phone mode (LAN + token) ------------------------------------------------------


def test_phone_without_token_is_rejected():
    with client(EventBus(), lan=True, peer=PHONE, host=LAN_IP) as c:
        assert c.get("/").status_code == 403
        assert c.get("/?token=wrong").status_code == 403


def test_phone_with_token_gets_the_page_and_the_stream():
    bus = EventBus()
    bus.publish(event("привет"))
    origin = {"origin": f"http://{LAN_IP}:{PORT}"}
    with client(bus, lan=True, peer=PHONE, host=LAN_IP) as c:
        assert c.get(f"/?token={TOKEN}").status_code == 200
        with c.websocket_connect(f"ws://{LAN_IP}:{PORT}/ws?token={TOKEN}", headers=origin) as ws:
            assert json.loads(ws.receive_text())["original"] == "привет"


def test_phone_websocket_without_token_is_rejected():
    origin = {"origin": f"http://{LAN_IP}:{PORT}"}
    with (
        client(EventBus(), lan=True, peer=PHONE, host=LAN_IP) as c,
        pytest.raises(WebSocketDisconnect) as exc,
        c.websocket_connect(f"ws://{LAN_IP}:{PORT}/ws", headers=origin) as ws,
    ):
        ws.receive_text()

    assert exc.value.code == 1008


def test_this_pc_does_not_need_the_token_in_phone_mode():
    with client(EventBus(), lan=True) as c:
        assert c.get("/").status_code == 200


def test_pairing_info_and_qr_are_only_for_this_pc():
    with client(EventBus(), lan=True) as c:
        info = c.get("/api/pairing").json()
        svg = c.get("/qr.svg")

    assert info["phone_url"] == f"http://{LAN_IP}:{PORT}/?token={TOKEN}"
    assert svg.status_code == 200
    assert svg.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in svg.text

    with client(EventBus(), lan=True, peer=PHONE, host=LAN_IP) as c:
        assert c.get(f"/api/pairing?token={TOKEN}").status_code == 403
        assert c.get(f"/qr.svg?token={TOKEN}").status_code == 403


def test_pairing_info_without_phone_mode():
    with client(EventBus()) as c:
        assert c.get("/api/pairing").json() == {"phone_url": None}
        assert c.get("/qr.svg").status_code == 404
