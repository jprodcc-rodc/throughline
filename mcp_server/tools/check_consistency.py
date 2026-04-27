"""check_consistency — Phase 2 v0.3 real implementation.

Reads the position database written by Reflection Pass
(``reflection_positions.json``), finds the cluster best matching
the user's statement, and returns historical positions in that
cluster as **candidate contradictions** for the host LLM to weigh.

Architectural choice: this tool does NOT decide whether the
historical positions actually contradict the user's new statement.
That requires LLM-grade semantic comparison and a thoughtful
soft-mode framing. The tool surfaces the *raw* historical signal;
the host LLM (Claude Desktop / Cursor / Continue.dev) does the
last-mile judgment in conversation. This keeps the tool fast,
deterministic, cache-friendly, and free of moralizing — exactly
the contract the design doc described as "soft mode default".

When the LLM-based contradiction detection (stage 6) lands, that
becomes an *enrichment* layer that filters the candidate list,
not a replacement for the tool surface.

Per locked decision Q3 (private/MCP_SCAFFOLDING_PLAN.md § 12.A):
docstring carries explicit "Call this when:" / "Do NOT call:"
guidance. Q4: tool name is NOT namespaced.
"""
from __future__ import annotations

from typing import Any

from mcp_server.position_state import (
    find_best_cluster,
    load_positions,
    resolve_positions_file,
)


def _frame_question(stance: str, soft_mode: bool) -> str:
    """Generate the framing question that wraps a prior position.
    Soft mode (default) phrases as a question the user can respond
    to honestly; hard mode states it as a contradiction."""
    if soft_mode:
        return (
            "Does the earlier reasoning still apply, or has something "
            "changed that makes it no longer relevant?"
        )
    return f"This contradicts your prior position: {stance}"


def check_consistency(
    statement: str,
    soft_mode: bool = True,
) -> dict:
    """Check whether a position the user just stated has historical
    counterparts the user may want to confront — and surface those
    historical positions **alongside their original reasoning** so
    the user can decide whether to update, drift, or reaffirm.

    The Reflection Layer's most counter-intuitive tool. Unlike
    every other AI-memory product, this one pushes back instead of
    agreeing. By design **not sycophantic**: when the user
    contradicts their past thinking, this surfaces the conflict
    rather than silently absorbing the new position.

    Call this when:
    - User expresses a clear position, decision, or commitment
      ("I'm going with usage-based pricing", "I think we should
      pivot", "my view is that the database should be Postgres").
    - User uses position-asserting phrases ("I think", "I've
      decided", "my view is", "we should").
    - User seems to be making a significant choice that will shape
      downstream work.

    Do NOT call:
    - On every assertion. The signal is *position-asserting on a
      topic the user has thought about before*, not every "I think
      this looks good" passing remark.
    - When the user is asking a question rather than asserting.
    - When the user has flagged uncertainty ("I'm not sure but...")
      — that's a reasoning state, not a position.

    Args:
        statement: The position statement to check (typically the
            user's most recent assertion).
        soft_mode: If True (default), prior positions surface as
            questions ("does the earlier reasoning still apply?").
            If False, surfaces as assertions for users who want
            stronger pushback. Most users should keep default.

    Returns:
        On success when a related cluster is found::

            {
                "contradictions": [
                    {
                        "card_path": "vault/.../card.md",
                        "topic_cluster": "pricing_strategy",
                        "prior_stance": "against usage-based for ...",
                        "prior_reasoning": ["LTV math is...", ...],
                        "prior_date": "2026-01-15",
                        "framing_question": "Does the earlier ..."
                    },
                    ...
                ],
                "_status": "ok",
            }

        When no historical cluster is relevant::

            {
                "contradictions": [],
                "_status": "ok",
                "_message": "No prior positions on this topic.",
            }

        When Reflection Pass hasn't run yet::

            {
                "contradictions": [],
                "_status": "error",
                "_message": "Reflection Pass has not run yet ...",
            }
    """
    statement = (statement or "").strip()
    if not statement:
        return {
            "contradictions": [],
            "_status": "error",
            "_message": "check_consistency: statement is empty.",
        }

    state_path = resolve_positions_file()
    state = load_positions(state_path)
    if state is None:
        return {
            "contradictions": [],
            "_status": "error",
            "_message": (
                f"Reflection Pass has not run yet (no state file at "
                f"{state_path}). Run `python -m daemon.reflection_pass "
                "--enable-llm-backfill` to populate."
            ),
        }

    cluster = find_best_cluster(statement, state, min_score=0.3)
    if cluster is None:
        return {
            "contradictions": [],
            "_status": "ok",
            "_message": "No prior positions on this topic.",
        }

    cluster_label = (
        cluster.get("topic_cluster")
        or f"cluster_{cluster.get('cluster_id', '?')}"
    )

    contradictions: list[dict[str, Any]] = []
    for card in cluster.get("cards", []):
        # Only surface cards that actually have a back-filled stance.
        # Without stance there's no position to confront.
        stance = card.get("stance")
        if not stance:
            continue
        contradictions.append({
            "card_path": card.get("card_path", ""),
            "topic_cluster": cluster_label,
            "prior_stance": stance,
            "prior_reasoning": card.get("reasoning", []) or [],
            "prior_date": card.get("date", ""),
            "framing_question": _frame_question(stance, soft_mode),
        })

    if not contradictions:
        # Cluster matched but no card has a back-filled stance yet
        # → no actionable signal. Tell the user honestly rather
        # than returning empty silently.
        return {
            "contradictions": [],
            "_status": "ok",
            "_message": (
                f"Topic '{cluster_label}' has prior cards, but none "
                "have back-filled stance data yet. Run "
                "`python -m daemon.reflection_pass --enable-llm-backfill` "
                "to extract positions."
            ),
        }

    # Sort by date DESC so the most-recent prior position surfaces
    # first — typically the most-relevant comparison.
    contradictions.sort(key=lambda c: str(c.get("prior_date", "")), reverse=True)

    return {
        "contradictions": contradictions,
        "_status": "ok",
    }
