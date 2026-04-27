"""Stage 8 — Reflection Pass writeback (preview module).

Assembles the frontmatter additions that stage 8 would write to
each card based on stages 3-5 in-memory results
(``_backfill``, ``_open_thread``, ``_open_thread_questions``,
``_cluster_id``). This module currently produces a *preview* —
the JSON of "what would be written" — without touching any file
on disk.

The actual atomic frontmatter rewrite (YAML round-trip preserving
formatting + temp-file replace) lands in a separate commit because
mutating user-vault files is the highest-blast-radius operation
in the daemon and deserves its own smoke-test cycle.

Schema produced (per ``docs/POSITION_METADATA_SCHEMA.md``):

::

    position_signal:
      topic_cluster: "..."
      stance: "..."             # from _backfill.claim_summary
      reasoning: []             # parsed from First Principles section
      conditions: null
      confidence: "asserted"
      emit_source: "refiner_inferred"
      topic_assignment: "daemon_clustered"

    open_questions: [...]       # from _backfill.open_questions

    reflection:
      status: "open_thread" | "concluded"
      last_pass: "<ISO timestamp>"
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional


def _extract_reasoning_from_body(body: str) -> list[str]:
    """Pull the bullet/list items from the First Principles section
    so we don't have to LLM-extract reasoning. Uses card_body_parser
    for section split, then a simple bullet regex.

    Returns up to 5 reasoning bullets. Empty list when section is
    missing or has no recognizable bullets — better empty than
    fabricated.
    """
    try:
        from daemon.card_body_parser import get_section
    except ImportError:
        return []

    section = get_section(body, "first_principles") or ""
    if not section.strip():
        return []

    # Match Markdown bullet lines: -, *, +, or numbered like "1."
    # plus leading whitespace.
    bullets = re.findall(
        r"^\s*(?:[-*+]|\d+\.)\s+(.+?)\s*$",
        section,
        flags=re.MULTILINE,
    )
    # Trim, drop sub-bullets that are too long (likely paragraphs),
    # cap at 5 entries.
    cleaned = []
    for b in bullets:
        text = b.strip()
        if 3 <= len(text) <= 280:
            cleaned.append(text)
        if len(cleaned) >= 5:
            break
    return cleaned


def assemble_position_signal(
    card: dict[str, Any],
    cluster_name: Optional[str],
) -> Optional[dict[str, Any]]:
    """Build the position_signal dict that would land in frontmatter.

    Returns None when stage-4 back-fill didn't produce a
    claim_summary for this card (no signal to write).
    """
    backfill = card.get("_backfill") or {}
    claim = backfill.get("claim_summary")
    if not claim:
        return None

    body = str(card.get("body", ""))
    reasoning = _extract_reasoning_from_body(body)

    cid = card.get("_cluster_id")
    cluster_label = (
        cluster_name
        if cluster_name
        else (f"cluster_{cid}" if cid is not None else "unknown")
    )

    return {
        "topic_cluster": cluster_label,
        "stance": claim,
        "reasoning": reasoning,
        "conditions": None,
        "confidence": "asserted",
        "emit_source": "refiner_inferred",
        "topic_assignment": (
            "daemon_clustered" if not cluster_name else "daemon_canonicalized"
        ),
    }


def assemble_reflection(card: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Build the reflection dict that would land in frontmatter."""
    is_open = bool(card.get("_open_thread"))
    questions = card.get("_open_thread_questions") or []

    # Cards that haven't been through any of stages 3-5 don't get a
    # reflection block — preserve the "no signal yet" state.
    backfill = card.get("_backfill")
    if not backfill and not is_open and not questions:
        return None

    status = "open_thread" if is_open else "concluded"
    return {
        "status": status,
        "last_pass": datetime.now(timezone.utc).isoformat(),
    }


def compute_writeback_diff(
    card: dict[str, Any],
    cluster_name: Optional[str],
) -> dict[str, Any]:
    """Compute what frontmatter fields would be added/changed for
    this card. Does not mutate the card.

    Returns dict shape::

        {
            "card_path": "...",
            "additions": {
                "position_signal": {...},  # only if not already present
                "open_questions": [...],   # only if not already present
                "reflection": {...},
            },
            "skipped_fields": ["position_signal"],  # already present
        }
    """
    fm = card.get("frontmatter") or {}
    if not isinstance(fm, dict):
        fm = {}

    additions: dict[str, Any] = {}
    skipped: list[str] = []

    # position_signal
    if "position_signal" in fm and fm["position_signal"]:
        skipped.append("position_signal")
    else:
        ps = assemble_position_signal(card, cluster_name)
        if ps is not None:
            additions["position_signal"] = ps

    # open_questions (top-level field)
    backfill = card.get("_backfill") or {}
    bq = backfill.get("open_questions") or []
    if "open_questions" in fm and fm["open_questions"]:
        skipped.append("open_questions")
    elif bq:
        additions["open_questions"] = list(bq)

    # reflection
    refl = assemble_reflection(card)
    if refl is not None:
        # Always overwrite reflection — it's daemon-managed, not
        # user-edited. Each pass refreshes status + last_pass.
        additions["reflection"] = refl

    return {
        "card_path": card.get("path", ""),
        "additions": additions,
        "skipped_fields": skipped,
    }


def build_writeback_preview(
    cards: list[dict[str, Any]],
    cluster_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Build a list of writeback diffs for every card that would
    actually be modified. Cards with no additions are filtered out
    so the preview file stays focused on real changes."""
    out = []
    for card in cards:
        cid = str(card.get("_cluster_id", ""))
        cluster_name = cluster_names.get(cid)
        diff = compute_writeback_diff(card, cluster_name)
        if diff["additions"]:
            out.append(diff)
    return out
