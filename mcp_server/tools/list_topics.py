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
    knowledge into. The X-axis taxonomy — what subject buckets exist
    + how many cards live in each. Use this to discover the shape
    of the vault before recall_memory or save_refined_card.

    CALL THIS PROACTIVELY WHEN:
    - User asks meta-questions about their knowledge structure
      ('what topics do I have?', 'what do I know about?', 'show me
      my domains', '我都有哪些知识?', 'list my topics').
    - You need to pick a `domain` for save_refined_card and aren't
      sure which X-axis bucket fits — call list_topics first, then
      save with the most appropriate bucket.
    - You need a `domain_filter` for recall_memory to narrow the
      search ('recall my Health cards' → list_topics → confirm
      'Health/Biohack' exists → recall_memory(domain_filter=...)).
    - User asks for an inventory / dashboard view ('how big is my
      vault?', 'show me the breakdown').
    - User is curious about coverage / gaps ('what areas am I
      thin on?', 'what topics have only a few cards?').

    DO NOT CALL WHEN:
    - User asks about a specific topic — call recall_memory directly
      with that topic; don't speculatively list everything first.
    - Speculatively at the start of every conversation — only fire
      when the user's intent is explicitly meta-taxonomy or you
      genuinely need a domain to pass to another tool.
    - On every save — if you already know a reasonable domain for
      this card from prior context, just use it.
    - User just installed throughline ('first time using this') —
      use throughline_status instead, which shows install state +
      cold-start hints, not just a domain list.

    EXAMPLE TRIGGERS:
    User: "What topics do I have cards on?"
      → list_topics()
    User: "Show me my Health domain breakdown."
      → list_topics(prefix="Health")
    User: "我都存过哪些类别?"
      → list_topics()
    User: "Save this AI prompting trick."
      → list_topics(prefix="AI") to confirm 'AI/LLM' exists
        → save_refined_card(domain="AI/LLM", ...)
    User: "How many cards do I have total?"
      → list_topics(include_card_counts=True)

    EXAMPLE NON-TRIGGERS:
    User: "What did I write about Tailscale?"
      (specific topic; call recall_memory directly)
    User: "Hi, just installed this."
      (use throughline_status — cold-start aware)
    User: "Save this conversation."
      (if domain is obvious from context, save_refined_card directly)

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

        On success but the vault is empty (cold-start hint)::

            {
                "domains": [{"path": "Health/Biohack",
                             "card_count": 0}, ...],
                "total_cards": 0,
                "_status": "ok",
                "_message": "Vault has 0 cards. Suggest saving "
                            "conversations via 'remember this' / "
                            "'保存这个' ...",
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

    result: dict = {
        "domains": result_domains,
        "total_cards": total_cards,
        "_status": "ok",
    }
    # Cold-start hint: if the daemon's taxonomy is loaded but no card
    # has been written yet, tell the host LLM so it can teach the user
    # how to populate the vault rather than reciting an empty domain
    # list. Only fires when card-counts are available (without them
    # we can't distinguish a fresh vault from include_card_counts=False).
    if include_card_counts and total_cards == 0:
        result["_message"] = (
            "Vault has 0 cards. Suggest saving conversations via "
            "'remember this' / '保存这个' / '记住这个' — that fires "
            "save_conversation and the daemon refines into the vault. "
            "Once a few cards exist, list_topics will return real "
            "card_count distributions."
        )
    return result
