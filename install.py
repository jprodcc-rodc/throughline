"""Entry-point shim: run the v0.2.0 install wizard.

Usage:
    python install.py                 # full 16-step wizard
    python install.py --step 7        # re-run only step 7 (Retrieval backend)

The wizard code lives in `throughline_cli/`. This file exists so new
users can clone + run immediately without needing to know the package
layout.
"""
from __future__ import annotations

import sys


def _graceful_import():
    try:
        from throughline_cli.wizard import main
        return main
    except ImportError as exc:
        msg = str(exc).lower()
        if "rich" in msg:
            print("throughline install wizard needs the `rich` package.")
            print("Run one of:")
            print("    pip install rich")
            print("    pip install -r requirements.txt")
            sys.exit(2)
        raise


if __name__ == "__main__":
    raise SystemExit(_graceful_import()(sys.argv[1:]))
