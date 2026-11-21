# PyInstaller spec for the Windows package: one folder with Telsiz.exe.
# Build it with: python scripts/build_package.py
#
# Not bundled on purpose:
# - Models (Whisper, NLLB, Argos): downloaded on first use into %LOCALAPPDATA%\telsiz.
# - NVIDIA CUDA libraries: while listening to the game, recognition runs on the CPU.
# - telsiz-loopback.exe: built from source by CMake; build_package.py copies it in.

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

ROOT = Path(SPECPATH).parent  # noqa: F821 (defined by PyInstaller)

datas = [
    (str(ROOT / "src/telsiz/server/static"), "telsiz/server/static"),
    (str(ROOT / "data/glossary.toml"), "telsiz/data"),
]
datas += collect_data_files("faster_whisper")  # the Silero VAD model
datas += collect_data_files("sacremoses")  # tokenizer tables for Argos models

binaries = collect_dynamic_libs("ctranslate2")

hiddenimports = [
    name for name in collect_submodules("telsiz") if not name.startswith("telsiz.quality")
] + collect_submodules("uvicorn")

analysis = Analysis(  # noqa: F821
    [str(ROOT / "packaging/telsiz_app.py")],
    pathex=[str(ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "IPython", "matplotlib", "telsiz.quality"],
    noarchive=False,
)

# Top-level packages in the build, for the third-party notices (build_package.py).
bundled = {name.split(".")[0] for name, _, _ in analysis.pure}
bundled |= {Path(dest).parts[0].split(".")[0] for dest, _, _ in analysis.binaries}
Path(workpath, "bundled-packages.txt").write_text("\n".join(sorted(bundled)), encoding="utf-8")  # noqa: F821
pyz = PYZ(analysis.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Telsiz",
    console=True,  # the console shows the QR code, the lines and what Telsiz chose
    version=None,
)
COLLECT(  # noqa: F821
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="Telsiz",
)
