"""find_open_threads — Phase 2 v0.3 scaffolding stub.

Real implementation in subsequent commit. The stub returns the
documented shape with `_status: "stub"` so MCP clients can wire up
and test the tool surface end-to-end before the Reflection Pass
daemon lands the actual `status: open_thread` metadata it queries.

Reflection Layer design rationale: see `docs/REFLECTION_LAYER_DESIGN.md`.
Engineering gate (≥75% topic-clustering pairwise accuracy on author's
vault): cleared 2026-04-28 at 0.975 (best threshold 0.70). With the
gate cleared, Phase 2 implementation is unblocked.

Per locked decision Q3 (`private/MCP_SCAFFOLDING_PLAN.md` § 12.A):
tool description has explicit "Call this when:" / "Do NOT call:"
guidance. Phase-2 tools follow the same convention.
"""
from __future__ import annotations


def find_open_threads(
    topic: str | None = None,
    limit: int = 5,
) -> dict:
    """Find unfinished thinking the user may want to resume — open
    questions without a follow-up answer, hypotheses left without
    a conclusion, branches the user started exploring but never
    closed. throughline's daemon tags these as `status: open_thread`
    in card metadata; this tool surfaces them.

    Call this when:
    - User starts a new conversation on a familiar topic
      ("I want to think about pricing again", "let's revisit
      that database migration plan").
    - User asks "what was I thinking about X?" or "where did I
      leave off on Y?".
    - User seems to be re-starting reasoning that may have already
      begun ("ok so on freemium conversion...") — surfacing the
      prior open thread saves them re-deriving from zero.
    - First message of a session and the user references a topic
      area without context — there may be a stale thread to pick
      up.

    Do NOT call:
    - Speculatively on every message. The signal is the user
      *signaling intent to reason about something familiar*. Random
      topical mentions don't qualify.
    - When the user is asking a discrete factual question — call
      `recall_memory` instead.
    - When the user has just expressed a clear position — call
      `check_consistency` instead.

    Args:
        topic: Optional topic filter. If given, only returns open
            threads in cards clustered to that topic. If None,
            returns the most recent open threads across all topics
            (capped by `limit`).
        limit: Max open threads to return (default 5). Open threads
            with most-recent activity surface first.

    Returns:
        On success::

            {
                "open_threads": [
                    {
                        "card_path": "vault/30_Biz_Ops/...md",
                        "topic_cluster": "pricing_strategy",
                        "open_question": "how to handle freemium "
                                         "conversion?",
                        "last_touched": "2026-02-12",
                        "context_summary": "Analyzed LTV math and "
                                           "competitor data; stopped "
                                           "before resolving freemium.",
                    },
                    ...
                ],
                "total_open_threads": 7,
                "_status": "ok",
            }

        Phase 2 stub (current behavior, no real detection yet)::

            {
                "open_threads": [],
                "total_open_threads": 0,
                "_status": "stub",
                "_message": "find_open_threads will be implemented "
                            "in v0.3 alongside the Reflection Pass "
                            "daemon. See docs/REFLECTION_LAYER_DESIGN.md.",
            }

        When the Reflection Pass daemon hasn't run yet on the user's
        vault::

            {
                "open_threads": [],
                "total_open_threads": 0,
                "_status": "error",
                "_message": "Reflection Pass has not run yet. Run "
                            "`python -m throughline_cli reflect` "
                            "or wait for the next scheduled pass.",
            }
    """
    return {
        "open_threads": [],
        "total_open_threads": 0,
        "_status": "stub",
        "_message": (
            "find_open_threads will be implemented in v0.3 "
            "alongside the Reflection Pass daemon. "
            "See docs/REFLECTION_LAYER_DESIGN.md."
        ),
    }
