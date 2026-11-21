"""Tests for live-mode helpers."""

import socket

import pytest

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


def test_listening_to_the_game_recognizes_on_the_cpu():
    from telsiz.config import Config
    from telsiz.serve import live_recognition_config

    config = live_recognition_config(Config())

    assert config.asr.device == "cpu"


@pytest.mark.parametrize(
    ("mode", "device", "expected"),
    [("system", "auto", "auto"), ("auto", "cuda", "cuda"), ("auto", "cpu", "cpu")],
)
def test_explicit_choices_are_kept(mode, device, expected):
    import dataclasses

    from telsiz.config import Config
    from telsiz.serve import live_recognition_config

    base = Config()
    config = dataclasses.replace(
        base,
        capture=dataclasses.replace(base.capture, mode=mode),
        asr=dataclasses.replace(base.asr, device=device),
    )

    assert live_recognition_config(config).asr.device == expected
