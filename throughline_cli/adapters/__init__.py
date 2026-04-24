"""Import adapters — turn third-party chat exports into OpenWebUI-shape
raw Markdown that the refine daemon consumes unchanged.

Current adapters:
    claude   — Claude.ai `conversations.jsonl` exports (ZIP or loose)

Planned:
    chatgpt  — ChatGPT `conversations.json` + `mapping` tree
    gemini   — Google Takeout `MyActivity.json` with daily-bucket stitch

Each adapter owns its source-format quirks and emits files of the form
    $OUT/YYYY-MM/YYYY-MM-DD_{conv_uuid}.md
with frontmatter carrying an `import_source` tag so bulk-purge is
reversible later.

CLI entry:
    python -m throughline_cli import <source> <path> [options]
"""
from __future__ import annotations

import sys

from .common import ImportSummary  # re-export

__all__ = ["main", "ImportSummary"]


USAGE = """\
throughline import — bring an existing chat-history export into throughline.

Usage:
    python -m throughline_cli import <source> [path] [options]

Sources:
    claude    Claude.ai data export (ZIP or conversations.jsonl|json)
    chatgpt   ChatGPT data export   (ZIP or conversations.json)
    gemini    Google Takeout Gemini Apps (ZIP or MyActivity JSON)
    sample    Bundled 10-conversation synthetic export (zero arg path).
              For first-time users to see the loop without exporting
              their own data. Auto-tagged `sample-YYYY-MM-DD` so it's
              easy to bulk-purge later.

Options:
    --out PATH       Output root (default: $THROUGHLINE_RAW_ROOT or
                     ~/throughline_runtime/sources/openwebui_raw)
    --dry-run        Scan + estimate cost, do NOT write any files
    --tag NAME       Override the auto-generated import_source tag
                     (default: <source>-YYYY-MM-DD)
    --limit N        Process at most N conversations (for quick tests)
"""


def _sample_path() -> str:
    """Resolve the bundled sample export path. Lives next to the
    repo's `samples/` directory."""
    from pathlib import Path
    return str(Path(__file__).resolve().parents[2] / "samples"
                / "claude_sample.jsonl")


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0 if argv else 2
    source = argv[0]
    rest = argv[1:]
    if source == "claude":
        from . import claude_export
        return claude_export.cli(rest)
    if source == "chatgpt":
        from . import chatgpt_export
        return chatgpt_export.cli(rest)
    if source == "gemini":
        from . import gemini_takeout
        return gemini_takeout.cli(rest)
    if source == "sample":
        # Drive the Claude adapter against the bundled file. Forward
        # any extra options (--dry-run / --out / --tag) the user
        # passed; the path is supplied automatically.
        from . import claude_export
        from datetime import datetime
        sample = _sample_path()
        # Auto-tag with today's date so multiple sample imports don't
        # collide and bulk-purge of just the samples is one tag.
        tag = f"sample-{datetime.now().strftime('%Y-%m-%d')}"
        # Don't clobber a user-supplied --tag.
        if "--tag" not in rest:
            rest = rest + ["--tag", tag]
        return claude_export.cli([sample] + rest)
    print(f"Unknown source: {source!r}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2
