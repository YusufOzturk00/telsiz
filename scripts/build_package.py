"""Build the Windows package: dist/Telsiz-<version>-windows-x64.zip.

    pip install -e ".[all,package]"
    python scripts/build_package.py [--helper PATH] [--no-zip]

Runs PyInstaller with packaging/telsiz.spec, then adds telsiz-loopback.exe (built
from native/process_loopback with CMake), the phone launcher, the example settings,
the license and the third-party notices, and zips the folder.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
WORK = ROOT / "build" / "pyinstaller"
DEFAULT_HELPER = ROOT / "native/process_loopback/build/Release/telsiz-loopback.exe"

PHONE_LAUNCHER = """@echo off
rem Starts Telsiz with the phone page on your local network (Wi-Fi).
rem Windows may ask whether Telsiz may use the network: allow private networks only.
start "Telsiz" "%~dp0Telsiz.exe" --live --phone
"""

# Parts of the package that are not Python distributions, and what is downloaded later.
EXTRA_NOTICES = """\
Other components
================

Python runtime: Python Software Foundation License.
  https://docs.python.org/3/license.html

FFmpeg libraries shipped inside PyAV (av.libs): LGPL-2.1-or-later, dynamically linked.
  Source: https://ffmpeg.org/download.html

Silero VAD model (inside faster-whisper): MIT. https://github.com/snakers4/silero-vad

telsiz-loopback.exe: Telsiz's own code (MIT), based on Microsoft's
ApplicationLoopback sample (MIT). https://github.com/microsoft/Windows-classic-samples

Downloaded on first use, not part of this package:
- Whisper models (faster-whisper conversions of OpenAI Whisper): MIT.
- NLLB-200 translation models (Meta): CC-BY-NC-4.0, non-commercial use only.
- Argos Translate models: see https://www.argosopentech.com (licenses per model).
"""


def run_pyinstaller() -> Path:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(ROOT / "packaging/telsiz.spec"),
            "--noconfirm",
            "--clean",
            "--distpath",
            str(DIST),
            "--workpath",
            str(WORK),
        ],
        check=True,
        cwd=ROOT,
    )
    return DIST / "Telsiz"


def license_text(dist: metadata.Distribution) -> str:
    texts = []
    for file in dist.files or []:
        name = file.name.upper()
        if name.startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE")):
            try:
                texts.append(file.read_text(encoding="utf-8").strip())
            except (OSError, UnicodeDecodeError):
                continue
    return "\n\n".join(texts)


def license_name(dist: metadata.Distribution) -> str:
    meta = dist.metadata
    expression = meta.get("License-Expression")
    if expression:
        return expression
    declared = (meta.get("License") or "").strip()
    if declared and len(declared) < 80 and "\n" not in declared:
        return declared
    classifiers = [
        c.split("::")[-1].strip()
        for c in meta.get_all("Classifier") or []
        if c.startswith("License")
    ]
    return ", ".join(classifiers) or "see the license text below"


def write_notices(app: Path) -> None:
    bundled = (WORK / "telsiz" / "bundled-packages.txt").read_text(encoding="utf-8").split()
    owners = metadata.packages_distributions()
    names = sorted({dist for module in bundled for dist in owners.get(module, [])} - {"telsiz"})
    parts = [
        "Telsiz bundles the following open source software.",
        "Telsiz itself is MIT-licensed (see LICENSE).",
        "",
    ]
    for name in names:
        dist = metadata.distribution(name)
        parts += [
            "=" * 78,
            f"{dist.metadata['Name']} {dist.version}  ({license_name(dist)})",
            "=" * 78,
            license_text(dist) or "(no license file in the distribution)",
            "",
        ]
    parts.append(EXTRA_NOTICES)
    (app / "THIRD_PARTY_NOTICES.txt").write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--helper", type=Path, default=DEFAULT_HELPER)
    parser.add_argument("--no-zip", action="store_true", help="leave only the folder")
    args = parser.parse_args()
    if not args.helper.is_file():
        print(
            f"telsiz-loopback.exe not found at {args.helper}; build native/process_loopback "
            "first (see its README) or pass --helper",
            file=sys.stderr,
        )
        return 1

    sys.path.insert(0, str(ROOT / "src"))
    from telsiz import __version__

    app = run_pyinstaller()
    shutil.copy2(args.helper, app / "telsiz-loopback.exe")
    (app / "Telsiz - Telefon.cmd").write_text(PHONE_LAUNCHER, encoding="ascii", newline="\r\n")
    for name in ("config.example.toml", "LICENSE", "README.md"):
        shutil.copy2(ROOT / name, app / name)
    write_notices(app)

    size = sum(f.stat().st_size for f in app.rglob("*") if f.is_file()) / 1e6
    print(f"Package folder: {app} ({size:.0f} MB)")
    if not args.no_zip:
        archive = shutil.make_archive(
            str(DIST / f"Telsiz-{__version__}-windows-x64"), "zip", DIST, "Telsiz"
        )
        print(f"Zip: {archive} ({Path(archive).stat().st_size / 1e6:.0f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
