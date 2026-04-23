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

# Content-block types that represent Claude's internal reasoning or
# tool chatter, NOT user-visible response text. We must skip these —
# some export batches leak the thinking summary into the message's
# top-level `text` field, so top-level text is NOT trustworthy when
# `content` blocks are present.
_INTERNAL_BLOCK_TYPES = frozenset(("thinking", "tool_use", "tool_result",
                                    "artifact", "reasoning"))


def _extract_text(msg: dict) -> str:
    """Extract the user-visible text of one message, skipping
    thinking / artifact / tool blocks.

    Precedence (matters — Claude's 2026-04 export has message-level
    `text` that is actually the THINKING summary, so content blocks
    must win):
        1. `content` list of blocks, filtering out internal types.
        2. `content` as a plain string (older batches).
        3. message-level `text` (oldest batches).
        4. message-level `message` string (rare).

    Returns "" if nothing usable is found.
    """
    c = msg.get("content")
    if isinstance(c, list):
        parts: list[str] = []
        for block in c:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "text")
            if btype in _INTERNAL_BLOCK_TYPES:
                continue
            if isinstance(block.get("text"), str):
                t = block["text"].strip()
                if t:
                    parts.append(t)
            elif isinstance(block.get("content"), str):
                t = block["content"].strip()
                if t:
                    parts.append(t)
        if parts:
            return "\n\n".join(parts)
    if isinstance(c, str):
        return c
    if isinstance(msg.get("text"), str):
        return msg["text"]
    if isinstance(msg.get("message"), str):
        return msg["message"]
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


def _longest_fence(text: str) -> int:
    """Longest run of consecutive backticks anywhere in text, used to
    pick an outer fence length that can't be closed by inner content."""
    max_run = 0
    run = 0
    for ch in text:
        if ch == "`":
            run += 1
            if run > max_run:
                max_run = run
        else:
            run = 0
    return max_run


def _render_attachments(msg: dict) -> str:
    """Append file + attachment metadata to the message body.

    - `attachments` carries text-extracted uploads (txt / md / py / pdf
      via OCR). Their `extracted_content` IS load-bearing — it's what
      the user actually pasted / uploaded to Claude, and dropping it
      loses significant context. Include it inline as a fenced block
      tagged with the filename.
    - `files` carries image / binary uploads. Claude's export does not
      include the file bytes — only `file_name` + `file_uuid`. We
      can't recover the image, but a one-line note preserves the
      'image was here' signal so the daemon's refiner knows visual
      context existed.
    """
    parts: list[str] = []
    for att in (msg.get("attachments") or []):
        if not isinstance(att, dict):
            continue
        name = (att.get("file_name") or "").strip() or "unnamed-attachment"
        ftype = att.get("file_type") or ""
        content = att.get("extracted_content")
        if isinstance(content, str) and content.strip():
            header = f"[Attached {ftype} file: {name}]" if ftype else f"[Attached file: {name}]"
            # Use 4-backtick fence so 3-backtick fences inside the
            # attachment (common for .md / tutorial uploads) don't
            # accidentally close our outer wrapper in Obsidian.
            # If an attachment happens to contain 4+ backticks we
            # auto-escalate to 5.
            fence = "`" * (max(3, _longest_fence(content)) + 1)
            parts.append(f"{header}\n\n{fence}\n{content}\n{fence}")
        else:
            parts.append(f"[Attached file: {name}]  (no extracted content)")
    for f in (msg.get("files") or []):
        if not isinstance(f, dict):
            continue
        name = (f.get("file_name") or "").strip() or "unnamed-file"
        parts.append(f"[Attached image/file: {name}]  (binary not in export)")
    return "\n\n".join(parts)


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
        attachments = _render_attachments(m)
        # Compose: text + attachment render. Either can be empty —
        # drop the message only if BOTH are empty (6-retry case
        # still skipped because no text and no attachments).
        body_parts = [p for p in (text.strip(), attachments.strip()) if p]
        if not body_parts:
            continue
        out.append((role, "\n\n".join(body_parts)))
    return out


# ------ main driver ------

def iter_conversations(jsonl_path: Path) -> Iterator[dict]:
    """Yield one parsed conv dict, tolerant of three real-world shapes.

    Claude's export has changed across batches. As of 2026-04 the file
    is named `conversations.json` and contains a single JSON array of
    conversation objects. Earlier batches used `conversations.jsonl`
    (one conversation per line). We handle both, plus the rare
    single-conversation JSON object case:

    1. Whole-file JSON, array     -> yield each element
    2. Whole-file JSON, object    -> yield once
    3. Neither (whole-file parse fails) -> line-by-line JSONL fallback

    Parsing happens on the full text in memory; Claude exports are at
    most a few hundred MB even for heavy users.
    """
    text = jsonl_path.read_text(encoding="utf-8")
    text_stripped = text.strip()
    if text_stripped:
        try:
            parsed = json.loads(text_stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            for item in parsed:
                yield item
            return
        if isinstance(parsed, dict):
            yield parsed
            return

    # Fallback: JSONL (one conversation per line).
    for raw in text.splitlines():
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


# ------ single-conversation preview (used by U17 wizard preview gate) ------

def preview_one(input_path: Path) -> Optional[tuple[str, list[tuple[str, str]], str]]:
    """Parse the first non-empty conversation; return
    (title, messages, conv_id) or None if the file has nothing usable.
    Does NOT write to disk."""
    resolved = _find_jsonl(input_path)
    for conv in iter_conversations(resolved):
        if not isinstance(conv, dict):
            continue
        msgs = _extract_messages(conv)
        if msgs:
            return (
                _extract_title(conv),
                msgs,
                _extract_conv_id(conv),
            )
    return None


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
