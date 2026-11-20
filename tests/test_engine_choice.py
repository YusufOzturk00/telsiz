"""Tests for picking the translation engine from the PC's memory."""

import pytest

from telsiz.config import Config, TranslateConfig
from telsiz.system import choose_translation, total_ram_gb
from telsiz.translate.factory import create_translator


@pytest.mark.parametrize(
    ("ram_gb", "expected"),
    [
        (31.7, ("nllb", "nllb-1.3b")),  # a "32 GB" PC
        (23.6, ("nllb", "nllb-1.3b")),  # "24 GB"
        (15.7, ("nllb", "nllb-600m")),  # "16 GB"
        (11.8, ("nllb", "nllb-600m")),  # "12 GB"
        (7.8, ("argos", None)),  # "8 GB"
        (None, ("argos", None)),  # unknown: play it safe
    ],
)
def test_engine_follows_installed_memory(ram_gb, expected):
    choice = choose_translation(ram_gb)

    assert (choice.engine, choice.nllb_model) == expected
    assert choice.reason


def test_total_ram_reads_windows_memory_status():
    class FakeKernel32:
        def GlobalMemoryStatusEx(self, status_pointer):  # noqa: N802 (Win32 name)
            status_pointer._obj.ullTotalPhys = 16 * 1024**3
            return 1

    assert total_ram_gb(kernel32=FakeKernel32()) == pytest.approx(16.0)  # GiB, as Windows shows


def test_total_ram_unknown_when_the_call_fails():
    class Failing:
        def GlobalMemoryStatusEx(self, status_pointer):  # noqa: N802
            return 0

    assert total_ram_gb(kernel32=Failing()) is None


# --- factory ---------------------------------------------------------------------


class Made:
    def __init__(self, kind, model=None):
        self.kind, self.model = kind, model


def factory_for(config, ram_gb, nllb_fails=False):
    def make_nllb(model, device, cpu_threads):
        if nllb_fails:
            raise OSError("download failed")
        return Made("nllb", model)

    def make_argos(device, cpu_threads):
        return Made("argos")

    return create_translator(config, ram_gb=ram_gb, make_nllb=make_nllb, make_argos=make_argos)


def config(engine="auto", nllb_model="nllb-600m"):
    return Config(translate=TranslateConfig(engine=engine, nllb_model=nllb_model))


def test_auto_engine_on_a_big_pc_uses_nllb_1_3b():
    made = factory_for(config(), ram_gb=31.7)

    assert (made.kind, made.model) == ("nllb", "nllb-1.3b")


def test_auto_engine_on_a_16_gb_pc_uses_nllb_600m():
    made = factory_for(config(), ram_gb=15.7)

    assert (made.kind, made.model) == ("nllb", "nllb-600m")


def test_explicit_engine_wins_over_auto_choice():
    assert factory_for(config("argos"), ram_gb=64).kind == "argos"
    made = factory_for(config("nllb", "nllb-1.3b"), ram_gb=8)
    assert (made.kind, made.model) == ("nllb", "nllb-1.3b")


def test_nllb_failure_falls_back_to_argos():
    made = factory_for(config(), ram_gb=31.7, nllb_fails=True)

    assert made.kind == "argos"
