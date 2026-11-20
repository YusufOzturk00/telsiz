"""LAN address, access token and phone URL for phone mode."""

from __future__ import annotations

import secrets
import socket


def lan_ip() -> str:
    """This PC's address on the local network (falls back to 127.0.0.1).

    Connecting a UDP socket only selects the outgoing interface; no packet is sent.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("10.254.254.254", 1))
            return probe.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def new_token() -> str:
    """A fresh random access token for this run (128 bits, URL-safe)."""
    return secrets.token_urlsafe(16)


def phone_url(ip: str, port: int, token: str) -> str:
    return f"http://{ip}:{port}/?token={token}"
