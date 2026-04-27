"""``python -m daemon.reflection_pass --explain CARD_PATH`` impl.

Single-card diagnostic: takes a path, runs pipeline up through
stage 5 (using cached state files where available, no LLM calls),
and prints everything the daemon thinks about that card —
cluster membership, sister cards, back-fill status, open-thread
classification, what writeback would add.

Pure read. Useful when an MCP tool returns an unexpected result
for a specific card and the operator wants to see exactly why.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from daemon.state_paths import (
    all_state_files,
    card_timestamp,
    default_backfill_state_file,
    default_cluster_names_file,
    default_open_threads_file,
    default_positions_file,
    default_writeback_preview_file,
)


def _load_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _normalize_card_path(card_path: str, vault_root: Optional[Path] = None) -> str:
    """Resolve user-supplied path to the canonical absolute string
    used in state files. Accepts:
    - absolute path
    - relative-to-vault path
    - filename (matched by suffix)
    """
    p = Path(card_path).expanduser()
    if p.is_absolute() and p.exists():
        return str(p)
    if vault_root and (vault_root / card_path).exists():
        return str(vault_root / card_path)
    return str(p)


def _find_in_positions(card_path: str, positions: dict) -> tuple[Optional[dict], Optional[dict]]:
    """Locate (cluster, card) pair in the positions state file."""
    if not isinstance(positions, dict):
        return None, None
    needle = card_path.replace("\\", "/")
    for cluster in positions.get("clusters", []):
        for card in cluster.get("cards", []):
            cp = card.get("card_path", "").replace("\\", "/")
            if cp == needle or cp.endswith(needle.split("/")[-1]):
                return cluster, card
    return None, None


def _find_open_threads_entry(card_path: str, open_threads: dict) -> Optional[dict]:
    if not isinstance(open_threads, dict):
        return None
    needle = card_path.replace("\\", "/")
    for entry in open_threads.get("open_threads", []):
        cp = entry.get("card_path", "").replace("\\", "/")
        if cp == needle or cp.endswith(needle.split("/")[-1]):
            return entry
    return None


def _find_writeback_diff(card_path: str, preview: dict) -> Optional[dict]:
    if not isinstance(preview, dict):
        return None
    needle = card_path.replace("\\", "/")
    for diff in preview.get("diffs", []):
        cp = diff.get("card_path", "").replace("\\", "/")
        if cp == needle or cp.endswith(needle.split("/")[-1]):
            return diff
    return None


def _find_in_backfill(card_path: str, backfill: dict) -> Optional[dict]:
    """Backfill keys are 'path|mtime'; match the path part."""
    if not isinstance(backfill, dict):
        return None
    needle = card_path.replace("\\", "/")
    for key, val in backfill.items():
        path_part = key.split("|", 1)[0].replace("\\", "/")
        if path_part == needle or path_part.endswith(needle.split("/")[-1]):
            return val
    return None


def explain(card_path: str) -> str:
    """Build a multi-section diagnostic report for a single card."""
    lines: list[str] = []
    lines.append(f"Reflection diagnostic: {card_path}")
    lines.append("=" * 72)
    lines.append("")

    # Resolve the card on disk
    resolved = _normalize_card_path(card_path)
    p = Path(resolved)
    if not p.exists():
        lines.append(f"  ✗ file not found at {resolved}")
        lines.append("    (path may be in state files but not on disk anymore)")
    else:
        lines.append(f"  ✓ file exists: {p}")
        try:
            stat = p.stat()
            lines.append(f"    size: {stat.st_size} bytes")
            lines.append(f"    mtime: {stat.st_mtime}")
        except OSError:
            pass

    # Load each state file
    cluster_names = _load_json(default_cluster_names_file()) or {}
    backfill = _load_json(default_backfill_state_file()) or {}
    open_threads = _load_json(default_open_threads_file()) or {}
    positions = _load_json(default_positions_file()) or {}
    preview = _load_json(default_writeback_preview_file()) or {}

    lines.append("")
    lines.append("# State file presence")
    files = all_state_files()
    for name, path in files.items():
        marker = "✓" if path.exists() else "✗"
        lines.append(f"  {marker} {name:24s}  {path}")

    # Position / cluster membership
    lines.append("")
    lines.append("# Cluster membership (from reflection_positions.json)")
    cluster, card_in_positions = _find_in_positions(resolved, positions)
    if cluster is None:
        lines.append("  ✗ card not found in positions state file")
        lines.append("    → either Reflection Pass hasn't run, OR card is")
        lines.append("      filtered out by stage 1.5 (no slice_id / managed_by)")
    else:
        cid = cluster.get("cluster_id", "?")
        cname = cluster.get("topic_cluster") or f"cluster_{cid}"
        lines.append(f"  cluster_id: {cid}")
        lines.append(f"  topic_cluster: {cname}")
        lines.append(f"  cluster size: {cluster.get('size', '?')}")
        if card_in_positions:
            lines.append(f"  card stance: {card_in_positions.get('stance')!r}")
            lines.append(f"  card date: {card_in_positions.get('date')!r}")
            lines.append(f"  is_backfilled: {card_in_positions.get('is_backfilled')}")
            lines.append(f"  is_open_thread: {card_in_positions.get('is_open_thread')}")
            qs = card_in_positions.get("open_questions", [])
            if qs:
                lines.append(f"  open_questions ({len(qs)}):")
                for q in qs:
                    lines.append(f"    • {q[:100]}")
        # Sister cards in the same cluster
        sisters = [
            c for c in cluster.get("cards", [])
            if c.get("card_path", "").replace("\\", "/") != resolved.replace("\\", "/")
        ]
        if sisters:
            lines.append(f"  sister cards in cluster ({len(sisters)}):")
            for s in sisters[:8]:
                title = s.get("title", "?")[:50]
                date = s.get("date", "?")[:20]
                lines.append(f"    [{date:<20s}] {title}")
            if len(sisters) > 8:
                lines.append(f"    ... ({len(sisters) - 8} more)")

    # Back-fill cache
    lines.append("")
    lines.append("# Back-fill cache (from reflection_backfill_state.json)")
    bf = _find_in_backfill(resolved, backfill)
    if bf is None:
        lines.append("  ✗ no back-fill cached for this card")
        lines.append("    → either --enable-llm-backfill hasn't run for this card,")
        lines.append("      OR card mtime changed since last back-fill (cache invalidated)")
    else:
        lines.append(f"  ✓ cached")
        lines.append(f"  claim_summary: {bf.get('claim_summary', '?')!r}")
        qs = bf.get("open_questions", [])
        lines.append(f"  open_questions ({len(qs)}):")
        for q in qs:
            lines.append(f"    • {q[:100]}")

    # Open thread status
    lines.append("")
    lines.append("# Open thread status (from reflection_open_threads.json)")
    ot = _find_open_threads_entry(resolved, open_threads)
    if ot is None:
        lines.append("  ✗ not flagged as open-thread")
        lines.append("    → either no unresolved questions, OR all questions")
        lines.append("      addressed by later cards in the cluster, OR")
        lines.append("      back-fill hasn't produced any questions for this card")
    else:
        lines.append(f"  ✓ flagged as open-thread")
        lines.append(f"  topic_cluster: {ot.get('topic_cluster', '?')}")
        lines.append(f"  last_touched: {ot.get('last_touched', '?')}")
        qs = ot.get("open_questions", [])
        lines.append(f"  unresolved questions ({len(qs)}):")
        for q in qs:
            lines.append(f"    • {q[:100]}")

    # Writeback preview
    lines.append("")
    lines.append("# Writeback preview (from reflection_writeback_preview.json)")
    wb = _find_writeback_diff(resolved, preview)
    if wb is None:
        lines.append("  ✗ no preview entry for this card")
        lines.append("    → no frontmatter additions would be written")
    else:
        additions = wb.get("additions", {})
        skipped = wb.get("skipped_fields", [])
        lines.append(f"  fields would be added: {list(additions.keys())}")
        if "position_signal" in additions:
            ps = additions["position_signal"]
            lines.append(f"    position_signal:")
            lines.append(f"      topic_cluster: {ps.get('topic_cluster')}")
            lines.append(f"      stance: {(ps.get('stance') or '')[:80]!r}")
            lines.append(f"      reasoning bullets: {len(ps.get('reasoning', []))}")
        if "open_questions" in additions:
            qs = additions["open_questions"]
            lines.append(f"    open_questions ({len(qs)}):")
            for q in qs[:3]:
                lines.append(f"      • {q[:80]}")
        if "reflection" in additions:
            r = additions["reflection"]
            lines.append(f"    reflection: status={r.get('status')!r}")
        if skipped:
            lines.append(f"  fields already in frontmatter (not overwritten): {skipped}")

    lines.append("")
    return "\n".join(lines)
