"""Claude.ai data export adapter.

Input shapes accepted (auto-detected):
  - ZIP file containing `conversations.jsonl` (+ other metadata files)
  - Loose `conversations.jsonl` file
  - Directory containing `conversations.jsonl`

Output: one Markdown file per conversation under
    $OUT/YYYY-MM/YYYY-MM-DD_{conv_uuid}.md
matching the OpenWebUI exporter shape so the daemon picks them up via
its existing `queue_existing_raw()` catch-up path on next start.

Claude's JSONL schema varies slightly between export batches. We
defensively handle these fields:
    uuid | id | conversation_id         -> conversation id
    name | title                        -> conversation title
    created_at | create_time | ts       -> primary timestamp
    updated_at | update_time            -> optional updated timestamp
    chat_messages | messages            -> list of turns
Each message attempts in order:
    text  (string)                      -> direct
    content (string)                    -> direct
    content (list of {type, text})      -> join text blocks
    message (string)                    -> direct
Fallback: stringify the message dict.

Sender roles map:
    human | user           -> "user"
    assistant | ai | claude-> "assistant"
    anything else          -> "system"  (dropped from output for v0.2.0;
                                         system messages are rare in
                                         Claude exports and usually
                                         empty.)
"""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional

from . import common
from .common import (
    ImportSummary, estimate_tokens, make_import_tag,
    render_markdown, resolve_out_dir, target_path, write_manifest,
)


CONV_JSONL_NAMES = ("conversations.jsonl", "conversations.json")


# ------ source-shape detection ------

def _find_jsonl(path: Path) -> Path:
    """Resolve the CLI argument to a concrete JSONL file on disk.

    Accepts: .jsonl file / .zip file / directory containing the file.
    ZIP contents are extracted to a tempdir; the caller is responsible
    for not deleting the returned path while still reading. We keep the
    tempdir alive by stashing a reference on the returned Path object
    as a module attribute (simple, works for one import at a time).
    """
    path = path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Claude export path does not exist: {path}")

    if path.is_file() and path.suffix.lower() == ".zip":
        return _extract_jsonl_from_zip(path)

    if path.is_file() and path.suffix.lower() in (".jsonl", ".json"):
        return path

    if path.is_dir():
        for name in CONV_JSONL_NAMES:
            candidate = path / name
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            f"No {' or '.join(CONV_JSONL_NAMES)} found in directory: {path}"
        )

    raise ValueError(f"Unrecognised Claude export path shape: {path}")


# Module-level anchor to prevent the tempdir being garbage-collected
# before the caller finishes reading the extracted JSONL. Path objects
# are immutable on Windows so we can't stash the tempdir reference on
# the returned Path; a module-private list is simpler and still scoped
# to process lifetime (the CLI exits after one run).
_ZIP_TEMPDIRS: list[Path] = []


def _extract_jsonl_from_zip(zip_path: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="throughline-claude-"))
    _ZIP_TEMPDIRS.append(tmp)
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            leaf = Path(member).name
            if leaf in CONV_JSONL_NAMES:
                # Extract only the JSONL; skip adjacent metadata files.
                dest = tmp / leaf
                with zf.open(member) as src, dest.open("wb") as dst:
                    dst.write(src.read())
                return dest
    raise FileNotFoundError(
        f"ZIP {zip_path.name} does not contain conversations.jsonl"
    )


# ------ record parsing ------

def _extract_text(msg: dict) -> str:
    """Try several Claude-export content shapes."""
    if isinstance(msg.get("text"), str):
        return msg["text"]
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for block in c:
            if isinstance(block, dict):
                if block.get("type") in ("text", None) and isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif isinstance(block.get("content"), str):
                    parts.append(block["content"])
        if parts:
            return "\n\n".join(parts)
    if isinstance(msg.get("message"), str):
        return msg["message"]
    # Last-resort stringify — keeps information but flags as malformed
    # for the summary counter.
    return ""


def _normalise_role(raw: object) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    r = raw.lower().strip()
    if r in ("human", "user"):
        return "user"
    if r in ("assistant", "ai", "claude", "bot"):
        return "assistant"
    return None  # system / tool / unknown — drop from user/assistant stream


def _extract_date(conv: dict) -> date:
    for k in ("created_at", "create_time", "ts", "timestamp", "updated_at"):
        v = conv.get(k)
        if isinstance(v, str):
            try:
                # Allow trailing Z + optional milliseconds.
                v_norm = v.replace("Z", "+00:00")
                return datetime.fromisoformat(v_norm).date()
            except ValueError:
                continue
    return date.today()


def _extract_conv_id(conv: dict) -> str:
    for k in ("uuid", "id", "conversation_id", "conv_id"):
        v = conv.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return "unknown"


def _extract_title(conv: dict) -> str:
    for k in ("name", "title", "summary"):
        v = conv.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _extract_messages(conv: dict) -> list[tuple[str, str]]:
    msgs = conv.get("chat_messages") or conv.get("messages") or []
    if not isinstance(msgs, list):
        return []
    out: list[tuple[str, str]] = []
    for m in msgs:
        if not isinstance(m, dict):
            continue
        role = _normalise_role(m.get("sender") or m.get("role"))
        if role is None:
            continue
        text = _extract_text(m)
        if not text.strip():
            continue
        out.append((role, text))
    return out


# ------ main driver ------

def iter_conversations(jsonl_path: Path) -> Iterator[dict]:
    """Yield one parsed conv dict per line, skipping blank + malformed."""
    with jsonl_path.open("r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                continue


def run(input_path: Path,
        out_dir: Optional[Path] = None,
        dry_run: bool = False,
        import_tag: Optional[str] = None,
        limit: Optional[int] = None,
        state_dir: Optional[Path] = None) -> ImportSummary:
    """Drive one Claude export -> raw MD conversion.

    Separate from cli() so tests can call this directly with a Path.
    """
    jsonl = _find_jsonl(input_path)
    out = out_dir or resolve_out_dir(None)
    tag = import_tag or make_import_tag("claude")
    summary = ImportSummary(source="claude", import_tag=tag,
                            out_dir=str(out), dry_run=dry_run)
    emitted_ids: list[str] = []

    for i, conv in enumerate(iter_conversations(jsonl)):
        if limit is not None and i >= limit:
            break
        summary.scanned += 1
        if not isinstance(conv, dict):
            summary.skipped_malformed += 1
            continue
        conv_id = _extract_conv_id(conv)
        conv_date = _extract_date(conv)
        title = _extract_title(conv)
        messages = _extract_messages(conv)
        if not messages:
            summary.skipped_no_content += 1
            continue
        body = render_markdown(
            title=title,
            messages=messages,
            metadata={
                "title": title,
                "date": conv_date.isoformat(),
                "source_platform": "claude",
                "source_conversation_id": conv_id,
                "import_source": tag,
            },
        )
        summary.total_tokens_estimate += estimate_tokens(body)
        if dry_run:
            summary.emitted += 1
            if len(summary.sample_paths) < 3:
                summary.sample_paths.append(
                    str(target_path(out, conv_date, conv_id))
                )
            continue
        path = target_path(out, conv_date, conv_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        summary.emitted += 1
        emitted_ids.append(conv_id)
        if len(summary.sample_paths) < 3:
            summary.sample_paths.append(str(path))

    if not dry_run and summary.emitted > 0:
        write_manifest(out, summary, emitted_ids, state_dir=state_dir)
    return summary


# ------ CLI dispatch (invoked by throughline_cli.adapters:main) ------

def cli(argv: list[str]) -> int:
    """Handle `python -m throughline_cli import claude <path> [options]`."""
    if not argv:
        print("Usage: python -m throughline_cli import claude <path> [options]",
              file=sys.stderr)
        return 2
    input_path = Path(argv[0])
    out_dir: Optional[Path] = None
    dry_run = False
    tag: Optional[str] = None
    limit: Optional[int] = None

    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--out":
            out_dir = Path(argv[i + 1]).expanduser()
            i += 2
        elif a == "--dry-run":
            dry_run = True
            i += 1
        elif a == "--tag":
            tag = argv[i + 1]
            i += 2
        elif a == "--limit":
            limit = int(argv[i + 1])
            i += 2
        else:
            print(f"Unknown option: {a}", file=sys.stderr)
            return 2

    try:
        summary = run(input_path, out_dir=out_dir, dry_run=dry_run,
                      import_tag=tag, limit=limit)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    _print_summary(summary)
    return 0


def _print_summary(summary: ImportSummary) -> None:
    # Import here to avoid requiring rich on import-time; cli is called
    # from __main__ where rich is already in scope.
    from .. import ui
    ui.section_title(f"Claude import · {summary.import_tag}")
    ui.kv_row("scanned",          str(summary.scanned))
    ui.kv_row("emitted",          str(summary.emitted))
    ui.kv_row("skipped (empty)",  str(summary.skipped_no_content))
    ui.kv_row("skipped (bad)",    str(summary.skipped_malformed))
    ui.kv_row("est. tokens",      f"{summary.total_tokens_estimate:,}")
    ui.kv_row("est. Normal cost", f"${summary.estimated_usd_normal():.2f}")
    ui.kv_row("est. Skim cost",   f"${summary.estimated_usd_skim():.2f}")
    ui.kv_row("out dir",          summary.out_dir)
    if summary.manifest_path:
        ui.kv_row("manifest",     summary.manifest_path)
    if summary.sample_paths:
        ui.info_line("sample files:")
        for p in summary.sample_paths:
            ui.info_line(f"  {p}")
    if summary.dry_run:
        ui.info_line("[yellow](dry-run: nothing was written)[/]")
