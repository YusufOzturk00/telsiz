"""Command-line entry point: ``python -m telsiz`` or ``telsiz``."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from telsiz import __version__

DESCRIPTION = "Real-time voice chat translator for CS2"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telsiz", description=DESCRIPTION)
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    # The translation pipeline arrives in M1; until then show usage.
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
