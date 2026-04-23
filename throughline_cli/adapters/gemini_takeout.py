"""Google Takeout Gemini Apps adapter.

Input: Google Takeout ZIP containing
    Takeout/<我的活动|My Activity>/Gemini Apps/<我的活动记录|MyActivity>.json

The file names use localised Chinese on Chinese-language Takeout
exports and English on English ones; we scan for any JSON inside a
"Gemini Apps"-suffixed directory in the ZIP, which works across
locales. Google explicitly documents this format as unstable /
undocumented — the adapter is defensive: unrecognised records are
skipped with a malformed counter bump rather than crashing.

Event schema (2026-04):
    {
      "header":    "Gemini Apps",
      "title":     "Prompted <user question>",
      "time":      "ISO-8601 with trailing Z",
      "products":  ["Gemini Apps"],
      "safeHtmlItem": [{"html": "<escaped HTML of Gemini's reply>"}],
      # optional:
      "attachedFiles": [...], "imageFile": "...", "subtitles": [...]
    }
    Some events omit safeHtmlItem (no response captured); those are
    skipped.

Unlike Claude/ChatGPT there is NO conversation boundary in the source
— each event is ONE user query + ONE model reply, orphan of any
thread. Per the v0.2.0 architecture (see docs/ONBOARDING_DATA_IMPORT.md
and docs/ROADMAP.md U24/U25 decisions), the daemon's slicer needs
multi-turn input; emitting one event per MD would fragment and inflate
refine cost. So this adapter groups events into **calendar-day buckets**:
each emitted .md is one day's worth of Gemini interactions rendered as
user/assistant alternation in time order.

The cross-day semantic continuation stitch (ROADMAP U2 refinement —
"if today's first event is topically similar to yesterday's last,
merge") is deferred: it requires the local bge-m3 rag_server running,
which isn't necessarily up at import time. Daily grouping is the
80/20 solution.
"""
from __future__ import annotations

import html as html_mod
import json
import re
import sys
import tempfile
import zipfile
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Optional

from .common import (
    ImportSummary, estimate_tokens, make_import_tag,
    render_markdown, resolve_out_dir, target_path, write_manifest,
)


# ------ source-shape detection ------

_ZIP_TEMPDIRS: list[Path] = []

# Gemini Apps directory name can be localised; the leaf JSON name too.
# Match on the PARENT directory containing 'Gemini' in the path and a
# JSON file inside it.
_GEMINI_DIR_PATTERNS = ("Gemini Apps", "Gemini apps", "gemini_apps")


def _find_activity_json(path: Path) -> Path:
    """Resolve the input path to the Gemini Apps activity JSON file.

    Accepts:
      - .zip file — extract the right JSON to a tempdir
      - .json file — use directly
      - directory — scan for Gemini Apps / *.json
    """
    path = path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Gemini Takeout path does not exist: {path}")

    if path.is_file() and path.suffix.lower() == ".zip":
        return _extract_json_from_zip(path)

    if path.is_file() and path.suffix.lower() == ".json":
        return path

    if path.is_dir():
        for p in path.rglob("*.json"):
            if _is_gemini_apps_path(p):
                return p
        # Permissive fallback: take the largest JSON in the tree.
        jsons = list(path.rglob("*.json"))
        if jsons:
            return max(jsons, key=lambda p: p.stat().st_size)
        raise FileNotFoundError(
            f"No Gemini Apps JSON found under directory: {path}"
        )

    raise ValueError(f"Unrecognised Gemini Takeout path shape: {path}")


def _is_gemini_apps_path(p: Path) -> bool:
    parts = [x.lower() for x in p.parts]
    return any(token.lower() in parts for token in _GEMINI_DIR_PATTERNS) \
        and p.suffix.lower() == ".json"


def _extract_json_from_zip(zip_path: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="throughline-gemini-"))
    _ZIP_TEMPDIRS.append(tmp)

    with zipfile.ZipFile(zip_path) as zf:
        # Prefer entries under a 'Gemini Apps' dir; fall back to largest
        # .json if name localisation defeats the pattern match.
        best = None
        best_size = -1
        for info in zf.infolist():
            if info.filename.lower().endswith(".json") \
               and any(tok.lower() in info.filename.lower()
                       for tok in _GEMINI_DIR_PATTERNS):
                if info.file_size > best_size:
                    best = info
                    best_size = info.file_size
        if best is None:
            # Permissive: largest JSON in the archive.
            for info in zf.infolist():
                if info.filename.lower().endswith(".json"):
                    if info.file_size > best_size:
                        best = info
                        best_size = info.file_size
        if best is None:
            raise FileNotFoundError(
                f"ZIP {zip_path.name} has no JSON files"
            )
        dest = tmp / "gemini_activity.json"
        with zf.open(best) as src, dest.open("wb") as dst:
            dst.write(src.read())
        return dest


# ------ event parsing ------

_PROMPTED_PREFIXES = (
    "Prompted ",     # English UI
    "已提示 ",        # zh-CN (observed variant)
    "已給予提示 ",    # zh-TW
)


def _strip_prompted_prefix(title: str) -> str:
    """Gemini's activity log prefixes user queries with a localised
    'Prompted ' marker. Strip it so the emitted MD reads as a real
    question."""
    if not isinstance(title, str):
        return ""
    for prefix in _PROMPTED_PREFIXES:
        if title.startswith(prefix):
            return title[len(prefix):]
    return title


def _html_to_markdown(html_str: str) -> str:
    """Convert Gemini's safeHtmlItem HTML to clean Markdown.

    Uses markdownify (BeautifulSoup-based); handles nested tags,
    entities, code blocks, and anchors correctly — unlike regex which
    trips on these all the time.
    """
    if not html_str:
        return ""
    try:
        from markdownify import markdownify as _md
    except ImportError:
        # Graceful degradation: strip tags naively, unescape entities.
        text = re.sub(r"<[^>]+>", "", html_str)
        return html_mod.unescape(text).strip()
    return _md(html_str, heading_style="ATX", bullets="-").strip()


def _extract_response_md(event: dict) -> str:
    items = event.get("safeHtmlItem") or []
    if not isinstance(items, list):
        return ""
    html_parts: list[str] = []
    for item in items:
        if isinstance(item, dict) and isinstance(item.get("html"), str):
            html_parts.append(item["html"])
    if not html_parts:
        return ""
    combined = "\n\n".join(html_parts)
    return _html_to_markdown(combined)


def _extract_event_time(event: dict) -> Optional[datetime]:
    raw = event.get("time")
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _render_attached_files(event: dict) -> str:
    """Gemini records user-uploaded file names (WeChat screenshots,
    ComfyUI outputs, etc). Binaries are NOT in the JSON — they sit as
    peer files in the ZIP — so we only preserve the filename as a
    placeholder so the daemon's refiner knows visual context existed."""
    parts: list[str] = []
    for f in (event.get("attachedFiles") or []):
        if isinstance(f, dict):
            name = (f.get("name") or f.get("file_name") or "").strip()
            if name:
                parts.append(f"[Attached file: {name}]")
        elif isinstance(f, str) and f.strip():
            parts.append(f"[Attached file: {f}]")
    img = event.get("imageFile")
    if isinstance(img, str) and img.strip():
        parts.append(f"[Image generated: {img}]")
    elif isinstance(img, dict):
        name = (img.get("name") or img.get("file_name") or "").strip()
        if name:
            parts.append(f"[Image generated: {name}]")
    return "\n".join(parts)


# ------ day-bucketing ------

def iter_events(json_path: Path) -> Iterator[dict]:
    text = json_path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return
    if isinstance(parsed, list):
        yield from parsed
    elif isinstance(parsed, dict):
        yield parsed


def _group_by_day(events: list[dict]) -> dict[date, list[dict]]:
    """Group events by local calendar day of their `time` field.

    Events with unparseable time go into today() — they're rare in
    Gemini exports but we preserve rather than drop them so the user
    can see the data and decide.
    """
    buckets: dict[date, list[dict]] = defaultdict(list)
    for e in events:
        t = _extract_event_time(e)
        day = t.date() if t else date.today()
        buckets[day].append(e)
    # Sort each day's events by time so conversation order is preserved.
    for day, evs in buckets.items():
        evs.sort(key=lambda e: _extract_event_time(e) or datetime.min.replace(tzinfo=None))
    return buckets


def _day_to_conversation(day: date, events: list[dict]) -> tuple[str, list[tuple[str, str]], str]:
    """Reduce one day's events to (title, messages, conv_id).

    title       : a human-readable summary like 'Gemini — 2026-02-17 (N events)'
    messages    : list of (role, text) for render_markdown
    conv_id     : stable slug used in filename + manifest
    """
    messages: list[tuple[str, str]] = []
    for e in events:
        if not isinstance(e, dict):
            continue
        query = _strip_prompted_prefix(e.get("title", "")).strip()
        response = _extract_response_md(e)
        attachments = _render_attached_files(e).strip()

        if query:
            user_body = "\n\n".join(p for p in (query, attachments) if p)
            messages.append(("user", user_body))
        if response:
            messages.append(("assistant", response))

    title = f"Gemini — {day.isoformat()} ({len([e for e in events if e.get('safeHtmlItem')])} events)"
    conv_id = f"gemini-{day.isoformat()}"
    return title, messages, conv_id


# ------ main driver ------

def run(input_path: Path,
        out_dir: Optional[Path] = None,
        dry_run: bool = False,
        import_tag: Optional[str] = None,
        limit: Optional[int] = None,
        state_dir: Optional[Path] = None) -> ImportSummary:
    """Drive Gemini Takeout -> raw MD conversion.

    `limit` caps the number of EVENTS processed (not days). Useful for
    quick smoke tests on large exports (a 30K-event Gemini user can
    test with --limit 100 without waiting for the full ingest).
    """
    json_path = _find_activity_json(input_path)
    out = out_dir or resolve_out_dir(None)
    tag = import_tag or make_import_tag("gemini")
    summary = ImportSummary(source="gemini", import_tag=tag,
                            out_dir=str(out), dry_run=dry_run)

    # Pull all events first (we need the full set to day-bucket
    # correctly). For typical exports (< 100K events) this is fine
    # memory-wise; iter_events itself is a generator for the rare
    # huge case but we materialise here.
    events: list[dict] = []
    for i, e in enumerate(iter_events(json_path)):
        if limit is not None and i >= limit:
            break
        summary.scanned += 1
        if not isinstance(e, dict):
            summary.skipped_malformed += 1
            continue
        events.append(e)

    buckets = _group_by_day(events)
    emitted_ids: list[str] = []

    for day in sorted(buckets.keys()):
        day_events = buckets[day]
        title, messages, conv_id = _day_to_conversation(day, day_events)
        if not messages:
            summary.skipped_no_content += len(day_events)
            continue
        body = render_markdown(
            title=title,
            messages=messages,
            metadata={
                "title": title,
                "date": day.isoformat(),
                "source_platform": "gemini",
                "source_conversation_id": conv_id,
                "import_source": tag,
            },
        )
        summary.total_tokens_estimate += estimate_tokens(body)
        if dry_run:
            summary.emitted += 1
            if len(summary.sample_paths) < 3:
                summary.sample_paths.append(
                    str(target_path(out, day, conv_id))
                )
            continue
        path = target_path(out, day, conv_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        summary.emitted += 1
        emitted_ids.append(conv_id)
        if len(summary.sample_paths) < 3:
            summary.sample_paths.append(str(path))

    if not dry_run and summary.emitted > 0:
        write_manifest(out, summary, emitted_ids, state_dir=state_dir)
    return summary


# ------ single-day preview (U17) ------

def preview_one(input_path: Path) -> Optional[tuple[str, list[tuple[str, str]], str]]:
    """Return the first day-bucket's (title, messages, conv_id) — the
    equivalent of a preview 'conversation' for Gemini's event-log
    source. None if no day has renderable content."""
    resolved = _find_activity_json(input_path)
    events = [e for e in iter_events(resolved) if isinstance(e, dict)]
    if not events:
        return None
    buckets = _group_by_day(events)
    for day in sorted(buckets.keys()):
        title, messages, conv_id = _day_to_conversation(day, buckets[day])
        if messages:
            return (title, messages, conv_id)
    return None


# ------ CLI ------

def cli(argv: list[str]) -> int:
    if not argv:
        print("Usage: python -m throughline_cli import gemini <path> [options]",
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
    ui.section_title(f"Gemini import · {summary.import_tag}")
    ui.kv_row("scanned events",    str(summary.scanned))
    ui.kv_row("emitted day MDs",   str(summary.emitted))
    ui.kv_row("skipped (empty)",   str(summary.skipped_no_content))
    ui.kv_row("skipped (bad)",     str(summary.skipped_malformed))
    ui.kv_row("est. tokens",       f"{summary.total_tokens_estimate:,}")
    ui.kv_row("est. Normal cost",  f"${summary.estimated_usd_normal():.2f}")
    ui.kv_row("est. Skim cost",    f"${summary.estimated_usd_skim():.2f}")
    ui.kv_row("out dir",           summary.out_dir)
    if summary.manifest_path:
        ui.kv_row("manifest",      summary.manifest_path)
    if summary.sample_paths:
        ui.info_line("sample files:")
        for p in summary.sample_paths:
            ui.info_line(f"  {p}")
    if summary.dry_run:
        ui.info_line("[yellow](dry-run: nothing was written)[/]")
