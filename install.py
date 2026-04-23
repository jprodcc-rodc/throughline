"""Entry-point shim: run the v0.2.0 install wizard.

Usage:
    python install.py                 # full 16-step wizard
    python install.py --step 7        # re-run only step 7 (Retrieval backend)

The wizard code lives in `throughline_cli/`. This file exists so new
users can clone + run immediately without a pip install or environment
setup beyond the regular `pip install -r requirements.txt`.
"""
from __future__ import annotations

import sys

from throughline_cli.wizard import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
