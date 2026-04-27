"""check_consistency — Phase 2 v0.3 scaffolding stub.

Real implementation lands in a subsequent commit alongside the
Reflection Pass daemon and the `position_signal` frontmatter schema.
Stub returns the documented shape with `_status: "stub"` so MCP
clients can wire up and test the tool surface end-to-end.

Reflection Layer design rationale: see `docs/REFLECTION_LAYER_DESIGN.md`
§ "Contradiction Surfacing". Engineering risk #3 (false-positive
contradictions) is mitigated by **soft mode** by default: this tool
returns prior positions as questions, not assertions, leaving it to
the host LLM to frame the conflict gently.

Per locked decision Q3: tool description has explicit "Call this
when:" / "Do NOT call:" guidance.
"""
from __future__ import annotations


def check_consistency(
    statement: str,
    soft_mode: bool = True,
) -> dict:
    """Check whether a position the user just stated contradicts
    a position they held in the past — and surface the prior
    position **alongside its original reasoning** so the user can
    decide whether to update, drift, or reaffirm.

    This is the Reflection Layer's most counter-intuitive tool. It
    is the only AI-memory tool that pushes back rather than agrees.
    It is by design **not sycophantic**: when the user contradicts
    their past thinking, it surfaces the conflict for the user to
    examine rather than silently absorbing the new position.

    Call this when:
    - User expresses a clear position, decision, or commitment
      ("I'm going with usage-based pricing", "I think we should
      pivot", "my view is that the database should be Postgres").
    - User uses position-asserting phrases ("I think", "I've
      decided", "my view is", "we should").
    - User seems to be making a significant choice that will
      shape downstream work.

    Do NOT call:
    - On every assertion. The signal is *position-asserting on a
      topic the user has thought about before*, not every "I think
      this looks good" passing remark.
    - When the user is asking a question rather than asserting.
    - When the user has flagged uncertainty ("I'm not sure but...")
      — that's a reasoning state, not a position.

    Args:
        statement: The position statement to check (typically the
            user's most recent assertion). The tool extracts the
            stance + topic from the statement before checking.
        soft_mode: If True (default), prior positions surface as
            questions ("does the earlier reasoning still apply?").
            If False, surfaces as assertions for users who want
            stronger pushback. Most users should keep default.

    Returns:
        On success when a contradicting position is found::

            {
                "contradictions": [
                    {
                        "card_path": "vault/30_Biz_Ops/...md",
                        "topic_cluster": "pricing_strategy",
                        "prior_stance": "against usage-based for "
                                        "early-stage SaaS",
                        "prior_reasoning": [
                            "LTV math is unpredictable",
                            "churn risk is severe in early stage",
                            "runway can't support revenue volatility",
                        ],
                        "prior_conditions": "early-stage, pre-PMF",
                        "prior_date": "2026-01-15",
                        "framing_question": "Has something changed "
                                            "that makes those reasons "
                                            "no longer apply, or is "
                                            "this a direction worth "
                                            "re-examining?",
                    },
                    ...
                ],
                "_status": "ok",
            }

        On success when no contradiction is found::

            {
                "contradictions": [],
                "_status": "ok",
                "_message": "No prior conflicting positions on this "
                            "topic.",
            }

        Phase 2 stub (current behavior)::

            {
                "contradictions": [],
                "_status": "stub",
                "_message": "check_consistency will be implemented "
                            "in v0.3. See docs/REFLECTION_LAYER_DESIGN.md.",
            }
    """
    return {
        "contradictions": [],
        "_status": "stub",
        "_message": (
            "check_consistency will be implemented in v0.3 alongside "
            "the Reflection Pass daemon and the position_signal "
            "frontmatter schema. See docs/REFLECTION_LAYER_DESIGN.md."
        ),
    }
