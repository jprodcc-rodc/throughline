"""get_position_drift — Phase 2 v0.3 scaffolding stub.

Real implementation lands in a subsequent commit alongside the
Reflection Pass daemon and the `position_signal` frontmatter schema.
Stub returns the documented shape with `_status: "stub"`.

Reflection Layer design rationale: see `docs/REFLECTION_LAYER_DESIGN.md`
§ "Drift Detection". This is the metacognitive infrastructure piece —
particularly load-bearing for ND users who experience their own
cognition as inconsistent ("I keep changing my mind") and benefit
from external evidence that the change has reasoning behind it.

Per locked decision Q3: tool description has explicit "Call this
when:" / "Do NOT call:" guidance.
"""
from __future__ import annotations


def get_position_drift(
    topic: str,
    granularity: str = "transitions",
) -> dict:
    """Show how the user's thinking on a specific topic has evolved
    over time — each major stance shift, when it happened, and what
    reasoning supported each transition.

    Returns the **full trajectory**, not just the current position.
    The point is to make intellectual evolution visible. For ND
    users, this externalizes a record of thinking-as-process rather
    than thinking-as-static-belief — turning "I'm flaky" into "my
    framework has gone through three reasoned phases".

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
        topic: Topic name to trace. Should match a topic_cluster
            value the daemon has assigned. Use `list_topics` first
            if unsure of available topics.
        granularity: Either "transitions" (default — only major
            stance shifts) or "all_cards" (every card on this
            topic in chronological order, even if no shift).

    Returns:
        On success::

            {
                "topic": "product_evaluation_framework",
                "trajectory": [
                    {
                        "phase_name": "technical feasibility first",
                        "stance": "no technical moat = no product",
                        "reasoning": ["..."],
                        "started": "2025-04-15",
                        "ended": "2025-10-20",
                        "card_count": 14,
                    },
                    {
                        "phase_name": "market size first",
                        "stance": "small market however deep can't "
                                  "sustain a team",
                        "reasoning": ["..."],
                        "started": "2025-10-20",
                        "ended": "2026-01-30",
                        "card_count": 9,
                        "transition_trigger": "card vault/.../...md "
                                              "where reasoning shifted",
                    },
                    {
                        "phase_name": "founder-market-fit first",
                        "stance": "only people who actually care can "
                                  "survive pre-PMF",
                        "reasoning": ["..."],
                        "started": "2026-01-30",
                        "ended": null,  # current
                        "card_count": 7,
                    },
                ],
                "drift_kind": "healthy_evolution",
                "current_phase": 2,
                "_status": "ok",
            }

        When no cards are clustered to this topic::

            {
                "topic": "...",
                "trajectory": [],
                "_status": "ok",
                "_message": "No cards clustered to this topic. "
                            "Try `list_topics` to see available "
                            "topic clusters.",
            }

        Phase 2 stub (current behavior)::

            {
                "topic": "...",
                "trajectory": [],
                "_status": "stub",
                "_message": "get_position_drift will be implemented "
                            "in v0.3. See docs/REFLECTION_LAYER_DESIGN.md.",
            }
    """
    return {
        "topic": topic,
        "trajectory": [],
        "_status": "stub",
        "_message": (
            "get_position_drift will be implemented in v0.3 "
            "alongside the Reflection Pass daemon and the "
            "position_signal frontmatter schema. "
            "See docs/REFLECTION_LAYER_DESIGN.md."
        ),
    }
