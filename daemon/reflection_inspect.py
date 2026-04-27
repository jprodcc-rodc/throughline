"""``python -m daemon.reflection_pass --inspect`` implementation.

Pretty-prints summaries of all Reflection Pass state files so the
operator can verify what's there, what's stale, and what needs
re-running. Pure read; never mutates.

Each state file gets a one-paragraph summary; outputs aligned for
quick scanning.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from daemon.state_paths import all_state_files


def _load_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _humanize_age(iso: str) -> str:
    """Convert an ISO timestamp to a "N hours/days ago" string."""
    if not iso:
        return "?"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    now = datetime.now(timezone.utc)
    delta = now - dt
    total = int(delta.total_seconds())
    if total < 60:
        return f"{total}s ago"
    if total < 3600:
        return f"{total // 60}m ago"
    if total < 86400:
        return f"{total // 3600}h ago"
    return f"{total // 86400}d ago"


def _file_size_human(path: Path) -> str:
    try:
        n = path.stat().st_size
    except OSError:
        return "?"
    if n < 1024:
        return f"{n}B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f}K"
    return f"{n / 1024 / 1024:.1f}M"


def _summarize_pass_state(data: dict) -> list[str]:
    out = [
        f"  cards scanned:         {data.get('cards_scanned', '?')}",
        f"  cards reflectable:     {data.get('cards_reflectable', '?')}",
        f"  cards excluded:        {data.get('cards_excluded', '?')}",
        f"  clusters formed:       {data.get('clusters_count', '?')}",
        f"  cluster names:         {data.get('cluster_names_resolved', '?')} resolved",
        f"  back-fills:            {data.get('backfill_completed', '?')} completed",
        f"  open threads:          {data.get('open_threads_detected', '?')} detected",
        f"  contradictions:        {data.get('contradictions_detected', '?')} detected",
        f"  drift phases:          {data.get('drift_phases_computed', '?')} computed",
        f"  cards updated:         {data.get('cards_updated', '?')}",
        f"  dry_run:               {data.get('dry_run', '?')}",
    ]
    started = data.get("started_at", "")
    if started:
        out.append(f"  started:               {started}  ({_humanize_age(started)})")
    if data.get("errors"):
        out.append(f"  errors:                {len(data['errors'])}")
    return out


def _summarize_cluster_names(data: dict) -> list[str]:
    if not isinstance(data, dict):
        return ["  (malformed)"]
    out = [f"  {len(data)} entries cached"]
    if data:
        out.append("  sample names:")
        for k, v in list(data.items())[:5]:
            cid = k.split("|", 1)[0] if "|" in k else k
            out.append(f"    cluster_{cid}: {v}")
        if len(data) > 5:
            out.append(f"    ... ({len(data) - 5} more)")
    return out


def _summarize_backfill(data: dict) -> list[str]:
    if not isinstance(data, dict):
        return ["  (malformed)"]
    out = [f"  {len(data)} cards back-filled"]
    if data:
        sample_count = 0
        out.append("  sample stances:")
        for k, v in data.items():
            if not isinstance(v, dict):
                continue
            cs = v.get("claim_summary", "")
            qs = v.get("open_questions", [])
            path_part = k.split("|", 1)[0]
            short = Path(path_part).name if "/" in path_part or "\\" in path_part else path_part
            out.append(
                f"    [{short[:30]:<30}] {(cs or '')[:60]} "
                f"(+{len(qs)} q)"
            )
            sample_count += 1
            if sample_count >= 5:
                break
        if len(data) > 5:
            out.append(f"    ... ({len(data) - 5} more)")
    return out


def _summarize_open_threads(data: dict) -> list[str]:
    if not isinstance(data, dict):
        return ["  (malformed)"]
    threads = data.get("open_threads", [])
    out = [f"  {len(threads)} open threads"]
    gen = data.get("generated_at", "")
    if gen:
        out.append(f"  generated_at: {gen}  ({_humanize_age(gen)})")
    if data.get("dry_run"):
        out.append("  (dry-run output)")
    if threads:
        out.append("  sample:")
        for entry in threads[:5]:
            tc = entry.get("topic_cluster", "?")
            qs = entry.get("open_questions", [])
            out.append(f"    [{tc[:30]:<30}] {len(qs)} unresolved")
            for q in qs[:2]:
                out.append(f"      • {q[:80]}")
        if len(threads) > 5:
            out.append(f"    ... ({len(threads) - 5} more)")
    return out


def _summarize_positions(data: dict) -> list[str]:
    if not isinstance(data, dict):
        return ["  (malformed)"]
    clusters = data.get("clusters", [])
    total_cards = sum(c.get("size", 0) for c in clusters)
    backfilled = sum(
        1 for c in clusters
        for card in c.get("cards", [])
        if card.get("is_backfilled")
    )
    open_threads = sum(
        1 for c in clusters
        for card in c.get("cards", [])
        if card.get("is_open_thread")
    )
    named = sum(1 for c in clusters if c.get("topic_cluster"))
    out = [
        f"  {len(clusters)} clusters / {total_cards} cards",
        f"  {named}/{len(clusters)} clusters named",
        f"  {backfilled}/{total_cards} cards back-filled",
        f"  {open_threads} cards flagged open-thread",
    ]
    gen = data.get("generated_at", "")
    if gen:
        out.append(f"  generated_at: {gen}  ({_humanize_age(gen)})")
    if clusters:
        # Show top 5 by size
        ranked = sorted(clusters, key=lambda c: -c.get("size", 0))[:5]
        out.append("  largest clusters:")
        for c in ranked:
            label = c.get("topic_cluster") or f"cluster_{c.get('cluster_id', '?')}"
            out.append(f"    [{label[:40]:<40}] {c.get('size', 0)} cards")
    return out


def _summarize_writeback_preview(data: dict) -> list[str]:
    if not isinstance(data, dict):
        return ["  (malformed)"]
    diffs = data.get("diffs", [])
    out = [
        f"  {data.get('cards_would_be_modified', '?')} cards would be modified",
        f"  dry_run: {data.get('dry_run', '?')}",
    ]
    gen = data.get("generated_at", "")
    if gen:
        out.append(f"  generated_at: {gen}  ({_humanize_age(gen)})")
    if diffs:
        out.append("  fields-to-add distribution:")
        from collections import Counter
        field_counts: Counter[str] = Counter()
        for d in diffs:
            for f in d.get("additions", {}):
                field_counts[f] += 1
        for f, n in field_counts.most_common():
            out.append(f"    {n:4d} cards would gain '{f}'")
    return out


_SUMMARIZERS: dict[str, Any] = {
    "pass_state": _summarize_pass_state,
    "cluster_names": _summarize_cluster_names,
    "backfill_cache": _summarize_backfill,
    "open_threads": _summarize_open_threads,
    "positions": _summarize_positions,
    "writeback_preview": _summarize_writeback_preview,
}


def render_inspect_report() -> str:
    """Build the multi-section inspect report. Returns the full
    string; CLI prints it directly."""
    files = all_state_files()
    lines: list[str] = ["Reflection Pass state inspection", "=" * 72, ""]

    for name, path in files.items():
        size = _file_size_human(path) if path.exists() else "—"
        present = "✓" if path.exists() else "✗"
        lines.append(f"[{present}] {name:24s}  {size:>8s}  {path}")
    lines.append("")
    lines.append("=" * 72)

    for name, path in files.items():
        if not path.exists():
            continue
        lines.append("")
        lines.append(f"# {name}  ({_file_size_human(path)})")
        lines.append(f"  path: {path}")
        data = _load_json(path)
        if data is None:
            lines.append("  (file unreadable or not JSON)")
            continue
        summarizer = _SUMMARIZERS.get(name)
        if summarizer:
            lines.extend(summarizer(data))
        else:
            # Fallback for state files without a custom summarizer
            # (contradictions, drift — not yet implemented)
            if isinstance(data, dict):
                lines.append(f"  keys: {list(data.keys())}")
            elif isinstance(data, list):
                lines.append(f"  list with {len(data)} entries")

    return "\n".join(lines)
