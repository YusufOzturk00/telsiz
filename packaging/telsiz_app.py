"""Entry script of the packaged Telsiz.exe (see packaging/telsiz.spec)."""

import sys

from telsiz.__main__ import packaged_main

if __name__ == "__main__":
    sys.exit(packaged_main())
