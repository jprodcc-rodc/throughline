"""list_topics — Phase 1 Week 2 commit 4 implementation.

Reads the active VALID_X_SET from `daemon.taxonomy` + optionally
walks the vault to count cards per domain. No LLM calls, no API
hits. Vault scan cached for 60s.

Per locked decision Q3: tool description has explicit "Call this
when:" / "Do NOT call:" guidance.
"""
from __future__ import annotations

from mcp_server.taxonomy_reader import (
    count_cards_per_domain,
    list_domains,
)


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
        prefix: Optional domain prefix filter. `'Health'` returns
            `Health/Medicine`, `Health/Biohack`, etc. Exact-match
            also works.
        include_card_counts: If True (default), walks the vault to
            count cards per domain. Adds ~1-3s on first call,
            cached for 60s after. Set False if you only need the
            domain list.

    Returns:
        On success::

            {
                "domains": [{"path": "Health/Biohack",
                             "card_count": 47}, ...],
                "total_cards": 312,
                "_status": "ok",
            }

        When the daemon's taxonomy module can't be imported (rare
        — install issue)::

            {
                "domains": [],
                "total_cards": 0,
                "_status": "error",
                "_message": "throughline daemon taxonomy not "
                            "loadable; run `python -m throughline_cli "
                            "doctor`",
            }
    """
    domains = list_domains(prefix=prefix)

    if not domains:
        # Either the user passed a prefix that matched nothing,
        # OR the daemon import failed entirely. Distinguish.
        all_domains = list_domains(prefix=None)
        if not all_domains:
            return {
                "domains": [],
                "total_cards": 0,
                "_status": "error",
                "_message": (
                    "throughline daemon taxonomy not loadable; "
                    "run `python -m throughline_cli doctor` to "
                    "verify install."
                ),
            }
        # Prefix matched no domains — return empty list with ok status
        return {
            "domains": [],
            "total_cards": 0,
            "_status": "ok",
        }

    if include_card_counts:
        counts = count_cards_per_domain()
        result_domains = [
            {"path": d, "card_count": counts.get(d, 0)}
            for d in domains
        ]
        total_cards = sum(counts.get(d, 0) for d in domains)
    else:
        result_domains = [{"path": d, "card_count": None} for d in domains]
        total_cards = 0

    return {
        "domains": result_domains,
        "total_cards": total_cards,
        "_status": "ok",
    }
