"""ChatGPT data export adapter.

Input shapes accepted (auto-detected):
  - ZIP containing `conversations.json` (+ chat.html, message_feedback.json,
    model_comparisons.json, user.json — the adjacent metadata files are
    ignored)
  - Loose `conversations.json`
  - Directory containing `conversations.json`

Output: one Markdown file per conversation under
    $OUT/YYYY-MM/YYYY-MM-DD_{conv_uuid}.md
matching the OpenWebUI exporter shape so the daemon's queue_existing_raw
picks them up unchanged on next start.

Conversation schema: ChatGPT stores each conversation as a `mapping`
tree of message nodes rather than a linear list. Each node has
    id, parent, children[], message: {role, content, create_time, ...}
where `children` captures ChatGPT's edit-and-regenerate branching.
To get a linear user/assistant alternation we walk from root along
`children[-1]` at each branch, which tracks the most recently edited
path (i.e. the one the user actually kept on the ChatGPT UI side).

Message content shapes (content_type field):
  text              parts is a list of strings
  code              text (string)
  multimodal_text   parts is a list where each item is either a string
                    or a dict {content_type: image_asset_pointer, ...}
  execution_output  text
  tether_quote      text
  model_editable_context | user_editable_context — metadata only, skip
  system_error | tool_result | etc — tool-adjacent, skip for v0.2 MVP
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


CONV_JSON_NAMES = ("conversations.json",)


# Content-type values that are metadata / internal and should NOT
# appear in the user-visible MD. Extensible as new OpenAI export
# variants surface.
_SKIP_CONTENT_TYPES = frozenset((
    "model_editable_context",
    "user_editable_context",
    "system_error",
    "tether_browsing_display",
    "tether_quote",           # skip: it's a citation UI element, not content
))


# ------ source-shape detection ------

_ZIP_TEMPDIRS: list[Path] = []


def _find_json(path: Path) -> Path:
    path = path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"ChatGPT export path does not exist: {path}")

    if path.is_file() and path.suffix.lower() == ".zip":
        return _extract_json_from_zip(path)

    if path.is_file() and path.suffix.lower() == ".json":
        return path

    if path.is_dir():
        for name in CONV_JSON_NAMES:
            candidate = path / name
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            f"No {' or '.join(CONV_JSON_NAMES)} in directory: {path}"
        )

    raise ValueError(f"Unrecognised ChatGPT export path shape: {path}")


def _extract_json_from_zip(zip_path: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="throughline-chatgpt-"))
    _ZIP_TEMPDIRS.append(tmp)
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            leaf = Path(member).name
            if leaf in CONV_JSON_NAMES:
                dest = tmp / leaf
                with zf.open(member) as src, dest.open("wb") as dst:
                    dst.write(src.read())
                return dest
    raise FileNotFoundError(
        f"ZIP {zip_path.name} does not contain conversations.json"
    )


# ------ mapping-tree walk ------

def _walk_mapping(conv: dict) -> list[dict]:
    """Flatten the mapping tree into a linear list of message dicts.

    ChatGPT stores each conversation as:
        mapping: { node_id: { id, parent, children[], message }, ... }
    with exactly one root (parent == null) and leaves having empty
    children arrays. Branches exist because a user can edit a prompt
    and regenerate — each regeneration becomes a new child.

    We walk from root, picking `children[-1]` at each fork. That's the
    convention ChatGPT's own UI uses: the most recently added child is
    the visible one. Mapping-tree parsing is the trickiest part of
    this adapter; a 90%-correct walk is fine for v0.2.0 since only
    the most-recent branch is usually what the user wants archived.
    """
    mapping = conv.get("mapping")
    if not isinstance(mapping, dict) or not mapping:
        return []

    # Find the root (parent is None).
    roots = [nid for nid, node in mapping.items()
             if isinstance(node, dict) and node.get("parent") is None]
    if not roots:
        # Fallback: pick any node and climb until we find a parentless one.
        first = next(iter(mapping.values()))
        roots = [first.get("id")] if isinstance(first, dict) else []
    if not roots:
        return []

    out: list[dict] = []
    seen: set[str] = set()
    cur_id = roots[0]
    while cur_id and cur_id not in seen:
        seen.add(cur_id)
        node = mapping.get(cur_id)
        if not isinstance(node, dict):
            break
        msg = node.get("message")
        if isinstance(msg, dict):
            out.append(msg)
        children = node.get("children") or []
        if not children:
            break
        # Pick the last child (most-recent branch per ChatGPT UI convention).
        cur_id = children[-1]
    return out


# ------ message text extraction ------

def _extract_text(msg: dict) -> str:
    """Extract user-visible text for one ChatGPT message, handling the
    several `content_type` shapes OpenAI has shipped."""
    content = msg.get("content")
    if not isinstance(content, dict):
        return ""
    ctype = content.get("content_type", "text")
    if ctype in _SKIP_CONTENT_TYPES:
        return ""

    # Tool / code blocks: single `text` field.
    if ctype in ("code", "execution_output"):
        t = content.get("text")
        if isinstance(t, str) and t.strip():
            # Preserve as fenced code for readability.
            lang = content.get("language", "")
            fence = "```" + (lang if isinstance(lang, str) else "")
            return f"{fence}\n{t}\n```"
        return ""

    # Text / multimodal_text — parts is a list of strings and/or dicts.
    parts = content.get("parts")
    if isinstance(parts, list):
        pieces: list[str] = []
        for p in parts:
            if isinstance(p, str):
                if p.strip():
                    pieces.append(p)
            elif isinstance(p, dict):
                # Multimodal: image pointer, file citation, etc.
                sub_ct = p.get("content_type", "")
                if sub_ct == "image_asset_pointer":
                    pieces.append(f"[Image: {p.get('asset_pointer', '?')}]")
                elif isinstance(p.get("text"), str):
                    pieces.append(p["text"])
        return "\n\n".join(pieces)

    # Older fallback: content.text as a string.
    if isinstance(content.get("text"), str):
        return content["text"]
    return ""


def _normalise_role(raw: object) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    r = raw.lower().strip()
    if r in ("user",):
        return "user"
    if r in ("assistant",):
        return "assistant"
    # ChatGPT also has 'system' (hidden instructions) and 'tool' (code
    # interpreter, browsing, DALL-E). System messages are almost always
    # empty/boilerplate; tool output is kept as 'assistant' visible text
    # (ChatGPT UI renders it the same way).
    if r in ("tool",):
        return "assistant"
    return None


# ------ conversation-level extractors ------

def _extract_date(conv: dict) -> date:
    for k in ("create_time", "created_at", "update_time", "updated_at"):
        v = conv.get(k)
        # ChatGPT stores these as UNIX timestamps (float), not ISO strings.
        if isinstance(v, (int, float)) and v > 0:
            try:
                return datetime.fromtimestamp(v).date()
            except (OSError, ValueError):
                continue
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
            except ValueError:
                continue
    return date.today()


def _extract_conv_id(conv: dict) -> str:
    for k in ("id", "conversation_id", "uuid"):
        v = conv.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return "unknown"


def _extract_title(conv: dict) -> str:
    for k in ("title", "name"):
        v = conv.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _extract_messages(conv: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for msg in _walk_mapping(conv):
        author = msg.get("author") or {}
        role_raw = author.get("role") if isinstance(author, dict) else None
        role = _normalise_role(role_raw)
        if role is None:
            continue
        text = _extract_text(msg)
        if not text.strip():
            continue
        out.append((role, text))
    return out


# ------ main driver ------

def iter_conversations(json_path: Path) -> Iterator[dict]:
    """Parse conversations.json and yield each conversation dict.

    The file is always a single top-level JSON array across every
    ChatGPT export batch we've seen; we still defend against an
    accidental single-object export.
    """
    text = json_path.read_text(encoding="utf-8").strip()
    if not text:
        return
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return
    if isinstance(parsed, list):
        for item in parsed:
            yield item
    elif isinstance(parsed, dict):
        yield parsed


def run(input_path: Path,
        out_dir: Optional[Path] = None,
        dry_run: bool = False,
        import_tag: Optional[str] = None,
        limit: Optional[int] = None,
        state_dir: Optional[Path] = None) -> ImportSummary:
    json_path = _find_json(input_path)
    out = out_dir or resolve_out_dir(None)
    tag = import_tag or make_import_tag("chatgpt")
    summary = ImportSummary(source="chatgpt", import_tag=tag,
                            out_dir=str(out), dry_run=dry_run)
    emitted_ids: list[str] = []

    for i, conv in enumerate(iter_conversations(json_path)):
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
                "source_platform": "chatgpt",
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


# ------ CLI ------

def cli(argv: list[str]) -> int:
    if not argv:
        print("Usage: python -m throughline_cli import chatgpt <path> [options]",
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
    from .. import ui
    ui.section_title(f"ChatGPT import · {summary.import_tag}")
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
