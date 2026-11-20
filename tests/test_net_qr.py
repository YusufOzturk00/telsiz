"""Tests for LAN address and QR helpers."""

import ipaddress

import pytest

from telsiz.util.net import lan_ip, new_token, phone_url


def test_phone_url_contains_address_port_and_token():
    assert phone_url("192.168.1.20", 8765, "abc") == "http://192.168.1.20:8765/?token=abc"


def test_lan_ip_is_an_ipv4_address():
    ipaddress.IPv4Address(lan_ip())


def test_tokens_are_long_random_and_url_safe():
    tokens = {new_token() for _ in range(50)}

    assert len(tokens) == 50
    assert all(len(t) >= 22 and t.replace("-", "").replace("_", "").isalnum() for t in tokens)


def test_qr_svg_and_ascii():
    pytest.importorskip("qrcode")
    from telsiz.util.qr import qr_ascii, qr_svg

    url = "http://192.168.1.20:8765/?token=abc"

    assert "<svg" in qr_svg(url)
    assert len(qr_ascii(url).splitlines()) > 10
