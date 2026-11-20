"""Tests for live-mode helpers."""

import socket

from telsiz.serve import port_available


def test_port_available_detects_a_busy_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        port = busy.getsockname()[1]

        assert port_available("127.0.0.1", port) is False


def test_port_available_for_a_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    assert port_available("127.0.0.1", port) is True
