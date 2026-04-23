"""Subcommand dispatcher for `python -m throughline_cli`.

Subcommands:
    install    — run the 16-step install wizard (default)
    import     — run an import adapter (claude / chatgpt / gemini)

Single-word entry point. Each subcommand owns its own argv parsing;
this dispatcher just picks the handler and ensures stdio is UTF-8 so
the rich panels / rules / emoji render correctly on Windows consoles.
"""
from __future__ import annotations

import sys

from . import ui


USAGE = """\
Usage:
    python -m throughline_cli install [--step N]
    python -m throughline_cli import <source> <path> [options]
    python -m throughline_cli taxonomy [review | reject TAG]

Subcommands:
    install    Run the 16-step install wizard (also the default if
               no subcommand given).
    import     Turn a chat export into raw Markdown the daemon consumes.
    taxonomy   Review self-growing taxonomy signals (U27 loop).

For subcommand help:
    python -m throughline_cli import --help
    python -m throughline_cli taxonomy --help
"""


def main(argv: list[str]) -> int:
    ui.ensure_utf8_stdio()
    if not argv:
        from . import wizard
        return wizard.main([])
    head = argv[0]
    rest = argv[1:]
    if head in ("install", "wizard"):
        from . import wizard
        return wizard.main(rest)
    if head == "import":
        from . import adapters
        return adapters.main(rest)
    if head == "taxonomy":
        from . import taxonomy
        return taxonomy.main(rest)
    if head in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    print(f"Unknown subcommand: {head!r}\n", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
