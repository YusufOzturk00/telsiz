"""Tests for the command-line entry point."""

import subprocess
import sys

import pytest

import telsiz
from telsiz.__main__ import main


def test_help_exits_successfully_and_describes_the_app(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "usage: telsiz" in out
    assert "Real-time voice chat translator for CS2" in out


def test_version_prints_package_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"telsiz {telsiz.__version__}"


def test_no_arguments_prints_usage_and_returns_zero(capsys):
    assert main([]) == 0
    assert "usage: telsiz" in capsys.readouterr().out


def test_unknown_argument_is_rejected(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--no-such-option"])

    assert exc_info.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_python_dash_m_telsiz_help_runs():
    result = subprocess.run(
        [sys.executable, "-m", "telsiz", "--help"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "usage: telsiz" in result.stdout
