"""list_topics — Phase 1 stub.

Real implementation lands in Week 2: reads `config/taxonomy.py`
VALID_X_SET (or active user taxonomy from `~/.throughline/`) and
optionally counts cards per domain by walking the vault. No LLM
calls, no API hits — cheap.

See `private/MCP_SCAFFOLDING_PLAN.md` § 3.3.
"""
from __future__ import annotations


def list_topics(
    prefix: str | None = None,
    include_card_counts: bool = True,
) -> dict:
    """List the taxonomy domains the user has organized their
    knowledge into. Useful when the user asks 'what do I know
    about?' or 'what topics have I covered?', or when you need to
    figure out an appropriate domain for a save_conversation call.

    Call this when:
    - The user asks about their knowledge structure.
    - You need to pick a domain_filter for recall_memory.
    - You're trying to understand the shape of the user's vault.

    Do NOT call:
    - Speculatively at the start of every conversation — wait for
      a signal that the user cares about taxonomy or you need
      domain context for another tool call.
    - When the user is asking about a specific topic — call
      recall_memory directly instead.

    Args:
        prefix: Optional filter, e.g. 'Health/' returns just health
            sub-domains.
        include_card_counts: If True, includes card counts per
            domain. Default True.

    Returns:
        dict with keys: domains (list of {path, card_count}),
        total_cards (int).
    """
    return {
        "domains": [],
        "total_cards": 0,
        "_status": "stub",
        "_message": (
            "list_topics is scaffolded but not yet implemented. "
            "Real logic lands in Week 2 (reads config/taxonomy.py + "
            "walks vault for card counts)."
        ),
    }
