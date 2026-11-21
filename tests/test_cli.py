"""Tests for the command-line entry point."""

import json
import subprocess
import sys

import pytest

import telsiz
from telsiz.__main__ import main
from telsiz.events import VoiceEvent


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


def test_package_version_matches_pyproject():
    # The release workflow names the zip after this version and checks the git tag.
    import tomllib
    from pathlib import Path

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    declared = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["version"]

    assert telsiz.__version__ == declared


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


# --- --input mode -------------------------------------------------------------


def fake_events():
    return [
        VoiceEvent("en", 0.97, "They're rushing B", "B'ye koşuyorlar", "tr", 820, ts=1.0),
        VoiceEvent("tr", 0.99, "tamam", "tamam", "tr", 300, ts=2.0),
        VoiceEvent("de", 0.9, "Hallo", None, "tr", 200, ts=3.0),
    ]


class FakeRunner:
    def __init__(self, events=None, error=None):
        self.events = events if events is not None else fake_events()
        self.error = error
        self.config = None
        self.path = None

    def __call__(self, config, path):
        self.config, self.path = config, path
        if self.error:
            raise self.error
        return iter(self.events)


@pytest.fixture
def wav(tmp_path):
    path = tmp_path / "talk.wav"
    path.write_bytes(b"RIFF")  # content is irrelevant to the fake runner
    return path


def test_input_prints_one_line_per_event(wav, capsys):
    runner = FakeRunner()

    assert main(["--input", str(wav)], run_file=runner) == 0

    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "[EN 0.97] They're rushing B → B'ye koşuyorlar  (820 ms)"
    assert lines[1] == "[TR 0.99] tamam  (300 ms)"
    assert lines[2] == "[DE 0.90] Hallo → (no translation)  (200 ms)"
    assert runner.path == wav


def test_json_flag_prints_event_json_lines(wav, capsys):
    assert main(["--input", str(wav), "--json"], run_file=FakeRunner()) == 0

    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [r["original"] for r in rows] == ["They're rushing B", "tamam", "Hallo"]


def test_command_line_options_override_config(wav, tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text('target_lang = "de"\n[asr]\nbeam_size = 3\n', encoding="utf-8")
    runner = FakeRunner([])

    argv = ["--input", str(wav), "--config", str(config_path), "--target", "en"]
    main([*argv, "--model", "medium", "--device", "cpu"], run_file=runner)

    assert runner.config.target_lang == "en"
    assert runner.config.asr.model == "medium"
    assert runner.config.asr.device == "cpu"
    assert runner.config.asr.beam_size == 3


def test_missing_input_file_is_an_error(tmp_path, capsys):
    assert main(["--input", str(tmp_path / "nope.wav")], run_file=FakeRunner()) == 2
    assert "not found" in capsys.readouterr().err


def test_missing_optional_dependencies_give_install_hint(wav, capsys):
    runner = FakeRunner(error=ImportError("No module named 'faster_whisper'"))

    assert main(["--input", str(wav)], run_file=runner) == 1
    assert 'pip install "telsiz[all]"' in capsys.readouterr().err


# --- --live mode --------------------------------------------------------------


class FakeLive:
    def __init__(self, code=0):
        self.code = code
        self.calls = []

    def __call__(self, config, *, phone, open_browser, show):
        self.calls.append({"config": config, "phone": phone, "open_browser": open_browser})
        show(fake_events()[0])
        return self.code


def test_live_starts_the_live_app_with_defaults(capsys):
    live = FakeLive()

    assert main(["--live"], run_live=live) == 0

    [call] = live.calls
    assert call["phone"] is False
    assert call["open_browser"] is True
    assert call["config"].server.port == 8765
    assert "B'ye koşuyorlar" in capsys.readouterr().out


def test_live_options(capsys):
    live = FakeLive()

    main(["--live", "--phone", "--port", "9000", "--no-browser", "--json"], run_live=live)

    [call] = live.calls
    assert call["phone"] is True
    assert call["open_browser"] is False
    assert call["config"].server.port == 9000
    assert json.loads(capsys.readouterr().out.splitlines()[0])["type"] == "voice"


# --- packaged Telsiz.exe ------------------------------------------------------------


def run_packaged(argv, tmp_path, **kwargs):
    from telsiz.__main__ import packaged_main

    live = kwargs.pop("live", FakeLive())
    kwargs.setdefault("owns_console", False)
    code = packaged_main(argv, app_dir=tmp_path, run_live=live, **kwargs)
    return code, live


def test_double_clicking_the_packaged_app_starts_listening(tmp_path):
    code, live = run_packaged([], tmp_path)

    assert code == 0
    [call] = live.calls
    assert call["phone"] is False  # the phone (LAN) stays opt-in
    assert call["open_browser"] is True


def test_packaged_app_reads_config_toml_next_to_the_exe(tmp_path):
    (tmp_path / "config.toml").write_text('target_lang = "de"\n', encoding="utf-8")

    _, live = run_packaged(["--live", "--phone"], tmp_path)

    [call] = live.calls
    assert call["config"].target_lang == "de"
    assert call["phone"] is True


def test_packaged_app_prefers_an_explicit_config(tmp_path):
    (tmp_path / "config.toml").write_text('target_lang = "de"\n', encoding="utf-8")
    other = tmp_path / "other.toml"
    other.write_text('target_lang = "pl"\n', encoding="utf-8")

    _, live = run_packaged(["--live", "--config", str(other)], tmp_path)

    assert live.calls[0]["config"].target_lang == "pl"


def test_packaged_app_keeps_its_own_window_open_until_enter(tmp_path):
    prompts = []

    code, _ = run_packaged([], tmp_path, owns_console=True, wait=prompts.append)

    assert code == 0
    assert len(prompts) == 1 and "Enter" in prompts[0]


def test_packaged_app_help_returns_instead_of_exiting(tmp_path, capsys):
    code, live = run_packaged(["--help"], tmp_path)

    assert code == 0
    assert live.calls == []
    assert "usage: telsiz" in capsys.readouterr().out


def test_live_exit_code_is_passed_through():
    assert main(["--live"], run_live=FakeLive(code=3)) == 3


def test_input_and_live_cannot_be_combined(wav, capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--input", str(wav), "--live"], run_live=FakeLive())

    assert exc_info.value.code == 2


def test_phone_requires_live(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--phone"], run_live=FakeLive())

    assert exc_info.value.code == 2
    assert "--live" in capsys.readouterr().err


def test_live_capture_options():
    live = FakeLive()

    main(["--live", "--capture", "system", "--app", "vlc.exe"], run_live=live)

    [call] = live.calls
    assert call["config"].capture.mode == "system"
    assert call["config"].capture.process_name == "vlc.exe"


def test_live_listens_to_the_game_by_default():
    live = FakeLive()

    main(["--live"], run_live=live)

    [call] = live.calls
    assert call["config"].capture.mode == "auto"
    assert call["config"].capture.process_name == "cs2.exe"


@pytest.mark.parametrize("flag", [["--capture", "system"], ["--app", "vlc.exe"]])
def test_capture_options_require_live(flag, capsys):
    with pytest.raises(SystemExit):
        main(flag, run_live=FakeLive())
    assert "--live" in capsys.readouterr().err
