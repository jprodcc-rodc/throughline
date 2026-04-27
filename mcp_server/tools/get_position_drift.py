"""get_position_drift — Phase 2 v0.3 real implementation.

Reads the position database written by Reflection Pass
(``reflection_positions.json``) and returns the chronological
trajectory of cards on the requested topic.

V1 (this commit): each back-filled card on the topic shows up as
its own trajectory entry. Each entry has stance, reasoning, date,
plus next-card-date as ``ended``. Phase segmentation (when stage
7 lands) will reduce this from "one entry per card" to "one entry
per coherent stance phase" — but the tool surface and field
shape don't change. The host LLM does the heavy presentation work.

This is the metacognitive infrastructure piece. For ND users who
experience their own cognition as inconsistent, an external
record of how thinking has evolved — with the reasoning behind
each shift — turns "I'm flaky" into "my framework went through
three reasoned phases".
"""
from __future__ import annotations

from typing import Any

from mcp_server.position_state import (
    find_cluster_by_topic,
    load_positions,
    resolve_positions_file,
)


def get_position_drift(
    topic: str,
    granularity: str = "transitions",
) -> dict:
    """Show how the user's thinking on a specific topic has evolved
    over time — each card's stance, when it happened, and what
    reasoning supported it.

    Returns the **full trajectory**, not just the current position.
    The point is to make intellectual evolution visible.

    Call this when:
    - User asks about their "current framework" or "current view"
      on a topic ("what's my current take on pricing?", "where am
      I now on database choice?").
    - User wants to see thinking history ("how has my thinking on
      X evolved?", "show me the arc on Y").
    - User seems uncertain whether their view has changed ("I'm
      not sure if I still believe...", "I think I used to think...").
    - User is building a writeup, retrospective, or decision doc
      that benefits from showing evolution rather than just
      conclusion.

    Do NOT call:
    - For factual lookups — call `recall_memory` instead.
    - For unfinished reasoning — call `find_open_threads` instead.
    - For checking a specific assertion against past — call
      `check_consistency` instead.

    Args:
        topic: Topic name to trace. Substring-matched against
            cluster names; falls back to token-overlap on titles
            when no name match. Use `list_topics` first to see
            available topic clusters.
        granularity: Either "transitions" (default — only major
            stance shifts; V1 returns per-card entries until
            stage 7 segmentation lands) or "all_cards" (every card
            on this topic in chronological order).

    Returns:
        On success::

            {
                "topic": "...",
                "trajectory": [
                    {
                        "phase_name": "...",
                        "stance": "...",
                        "reasoning": [...],
                        "started": "2025-04-15",
                        "ended": "2025-10-20",  # or null for current
                        "card_count": 1,        # V1; stage 7 will increase
                        "card_path": "vault/.../card.md",
                    },
                    ...
                ],
                "drift_kind": "unsegmented",  # stage 7 will refine
                "current_phase": <last index>,
                "_status": "ok",
            }

        When no cluster matches the topic::

            {
                "topic": "...",
                "trajectory": [],
                "_status": "ok",
                "_message": "No cards clustered to this topic. ..."
            }

        When Reflection Pass hasn't run yet::

            {
                "topic": "...",
                "trajectory": [],
                "_status": "error",
                "_message": "Reflection Pass has not run yet ...",
            }
    """
    topic_clean = (topic or "").strip()
    if not topic_clean:
        return {
            "topic": topic,
            "trajectory": [],
            "_status": "error",
            "_message": "get_position_drift: topic is empty.",
        }

    state_path = resolve_positions_file()
    state = load_positions(state_path)
    if state is None:
        return {
            "topic": topic,
            "trajectory": [],
            "_status": "error",
            "_message": (
                f"Reflection Pass has not run yet (no state file at "
                f"{state_path}). Run `python -m daemon.reflection_pass "
                "--enable-llm-backfill` to populate."
            ),
        }

    cluster = find_cluster_by_topic(topic_clean, state)
    if cluster is None:
        return {
            "topic": topic,
            "trajectory": [],
            "_status": "ok",
            "_message": (
                "No cards clustered to this topic. Try `list_topics` "
                "to see available topic clusters."
            ),
        }

    cards = cluster.get("cards", [])

    # Apply granularity. With current data we don't have phase
    # segmentation; both granularities return per-card entries
    # until stage 7 lands.
    if granularity not in ("transitions", "all_cards"):
        granularity = "transitions"

    eligible = cards
    if granularity == "transitions":
        # Without segmentation, "transitions" filters to cards that
        # have a back-filled stance (so each entry is a meaningful
        # data point). all_cards includes everything.
        eligible = [c for c in cards if c.get("stance")]

    if not eligible:
        cluster_label = (
            cluster.get("topic_cluster")
            or f"cluster_{cluster.get('cluster_id', '?')}"
        )
        return {
            "topic": topic,
            "trajectory": [],
            "_status": "ok",
            "_message": (
                f"Topic '{cluster_label}' has cards but no back-filled "
                "stance data. Run "
                "`python -m daemon.reflection_pass --enable-llm-backfill` "
                "to populate stances."
            ),
        }

    # State file already sorted cards chronologically per cluster.
    # Build trajectory entries.
    trajectory: list[dict[str, Any]] = []
    for i, card in enumerate(eligible):
        ended = (
            eligible[i + 1].get("date")
            if i + 1 < len(eligible)
            else None
        )
        trajectory.append({
            "phase_name": card.get("title", ""),
            "stance": card.get("stance") or "",
            "reasoning": card.get("reasoning", []) or [],
            "started": card.get("date", ""),
            "ended": ended,
            "card_count": 1,
            "card_path": card.get("card_path", ""),
        })

    return {
        "topic": (
            cluster.get("topic_cluster")
            or f"cluster_{cluster.get('cluster_id', '?')}"
        ),
        "trajectory": trajectory,
        "drift_kind": "unsegmented",
        "current_phase": len(trajectory) - 1 if trajectory else 0,
        "_status": "ok",
    }
