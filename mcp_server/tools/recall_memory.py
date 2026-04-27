"""recall_memory — Phase 1 stub.

Real implementation lands in Week 2: HTTP POST to localhost
rag_server's `/v1/rag` endpoint, returns top-k cards with scores.
See `private/MCP_SCAFFOLDING_PLAN.md` § 3.2.

Per locked decision Q1: `include_personal_context` defaults to
False — predictable, less token use, user opts in.
"""
from __future__ import annotations


def recall_memory(
    query: str,
    limit: int = 5,
    include_personal_context: bool = False,
    domain_filter: str | None = None,
) -> dict:
    """Retrieve cards from the user's throughline vault that are
    relevant to a query. Returns the cards' titles, content, and
    metadata for the host LLM to read.

    Call this when:
    - The user asks about something that may be in their vault
      ("what did I decide about X?", "what's my framework for Y?").
    - The user references past thinking ("like we discussed
      before", "based on what I said last month").
    - The user starts a topic where personal context matters
      (medical, financial, relationship, project-specific).
    - You're about to give generic advice that throughline likely
      has user-specific context for.

    Do NOT call:
    - For factual questions answerable from training data.
    - For coding / technical questions unrelated to the user's
      personal context.
    - On every turn — only when the query has retrieval-relevant
      shape.

    Args:
        query: The natural-language query. Will be embedded +
            re-ranked.
        limit: Max cards to return. Default 5.
        include_personal_context: If True, also pull in profile
            cards (allergies, current projects, durable preferences).
            Use sparingly — adds tokens. Default False.
        domain_filter: Optional taxonomy domain to restrict to,
            e.g. 'Health/Medicine' or 'Tech/AI'.

    Returns:
        dict with keys: cards (list of {title, content, domain,
        date, score}), personal_context (str | None),
        total_matched (int).
    """
    return {
        "cards": [],
        "personal_context": None,
        "total_matched": 0,
        "_status": "stub",
        "_message": (
            "recall_memory is scaffolded but not yet implemented. "
            "Real logic lands in Week 2 (HTTP client to localhost "
            "rag_server /v1/rag)."
        ),
    }
