"""recall_memory — Phase 1 Week 2 commit 3 implementation.

Calls localhost rag_server's `/v1/rag` endpoint, maps the response
to the MCP-documented shape, and applies a client-side domain
filter (since the RAG endpoint doesn't support tag-based filtering
server-side as of v0.2.x — it filters by `knowledge_identity` only).

Per locked decision Q1: `include_personal_context` defaults to
False — predictable, less token use, user opts in. When True, the
tool sets `pp_boost=1.0` so personal_persistent cards rank higher,
and surfaces any personal_persistent cards in the result set as a
concatenated `personal_context` string.

Per locked decision Q3: tool description has explicit "Call this
when:" / "Do NOT call:" guidance.

Failure modes handled:
- RAG server unreachable → status='error' with start-rag_server hint
- RAG server returned non-200 / error field → status='error' with
  the server-side message
- Empty query → status='error'
"""
from __future__ import annotations

from typing import Any

from mcp_server.rag_client import (
    RAGClientError,
    RAGServerError,
    RAGServerUnreachable,
    search,
)


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
            re-ranked by the rag_server.
        limit: Max cards to return. Default 5. Maps to
            rag_server's `top_k`.
        include_personal_context: If True, sets `pp_boost=1.0` so
            personal_persistent cards (allergies, current projects,
            durable preferences) rank higher in the same result
            set, AND populates the `personal_context` return field
            with a concatenation of any such cards' bodies.
            Default False (locked decision Q1).
        domain_filter: Optional taxonomy domain to restrict to,
            e.g. 'Health' or 'Health/Medicine'. Applied client-side
            via prefix match on the X-axis tag (the first tag in
            the card's `tags[]` that doesn't start with `y/` or
            `z/`). The rag_server itself doesn't support tag
            filtering as of v0.2.x.

    Returns:
        On success::

            {
                "cards": [{"title": str, "content": str,
                           "domain": str, "date": str,
                           "score": float}, ...],
                "personal_context": str | None,
                "total_matched": int,
                "_status": "ok",
            }

        On success but zero matches (cold-start or no-match)::

            {
                "cards": [],
                "personal_context": None,
                "total_matched": 0,
                "_status": "ok",
                "_message": "No matching cards. If the user's vault is "
                            "new, suggest saving conversations via "
                            "'remember this' / '保存这个' ...",
            }

        On error::

            {
                "cards": [],
                "personal_context": None,
                "total_matched": 0,
                "_status": "error",
                "_message": "...",
            }
    """
    if not query or not query.strip():
        return {
            "cards": [],
            "personal_context": None,
            "total_matched": 0,
            "_status": "error",
            "_message": "query must be non-empty",
        }

    try:
        rag_response = search(
            query=query,
            limit=limit,
            pp_boost=1.0 if include_personal_context else None,
        )
    except RAGServerUnreachable as exc:
        return {
            "cards": [],
            "personal_context": None,
            "total_matched": 0,
            "_status": "error",
            "_message": str(exc),
        }
    except RAGServerError as exc:
        return {
            "cards": [],
            "personal_context": None,
            "total_matched": 0,
            "_status": "error",
            "_message": str(exc),
        }
    except RAGClientError as exc:
        return {
            "cards": [],
            "personal_context": None,
            "total_matched": 0,
            "_status": "error",
            "_message": f"rag_server response error: {exc}",
        }

    raw_results = rag_response.get("results", [])

    # Apply domain_filter client-side (RAG endpoint doesn't filter
    # on tags as of v0.2.x).
    if domain_filter:
        raw_results = [r for r in raw_results
                       if _matches_domain(r.get("tags", []), domain_filter)]

    cards = [
        {
            "title": r.get("title", ""),
            "content": r.get("body_full") or r.get("body_preview", ""),
            "domain": _extract_domain(r.get("tags", [])),
            "date": r.get("date", ""),
            "score": r.get("final_score", 0.0),
        }
        for r in raw_results
    ]

    personal_context: str | None = None
    if include_personal_context:
        personal_context = _build_personal_context(raw_results)

    result: dict = {
        "cards": cards,
        "personal_context": personal_context,
        "total_matched": rag_response.get("total_candidates", len(cards)),
        "_status": "ok",
    }
    if not cards:
        # Cold-start hint: distinguishes "0 results" from "RAG error" so
        # the host LLM can teach the user how to populate the vault
        # instead of saying "I couldn't find anything" and stopping.
        result["_message"] = (
            "No matching cards. If the user's vault is new, suggest "
            "saving conversations via 'remember this' / '保存这个' / "
            "'记住这个' — that fires save_conversation and the daemon "
            "will refine into the vault. If the vault has cards but "
            "this query missed, try a broader query."
        )
    return result


# ---------- helpers ----------

def _is_axis_tag(tag: str) -> bool:
    """y/* and z/* are form/relation axis tags, not domain tags."""
    return tag.startswith("y/") or tag.startswith("z/")


def _extract_domain(tags: list[str]) -> str:
    """First non-axis tag IS the X-axis domain (e.g.
    'Health/Biohack' from ['Health/Biohack', 'y/Mechanism', 'z/Node']).
    Returns empty string if no domain tag."""
    for t in tags:
        if not _is_axis_tag(t):
            return t
    return ""


def _matches_domain(tags: list[str], filter_: str) -> bool:
    """Prefix-match the X-axis domain. `filter='Health'` matches
    'Health' and 'Health/Biohack'; `filter='Health/Medicine'`
    matches only 'Health/Medicine'."""
    domain = _extract_domain(tags)
    if not domain:
        return False
    if domain == filter_:
        return True
    return domain.startswith(filter_ + "/")


def _build_personal_context(results: list[dict[str, Any]]) -> str | None:
    """Concatenate body_preview of personal_persistent cards into
    a single string for the host LLM. Returns None if no personal
    cards in result set."""
    pieces = [
        r.get("body_preview", "").strip()
        for r in results
        if r.get("knowledge_identity") == "personal_persistent"
        and r.get("body_preview")
    ]
    if not pieces:
        return None
    return "\n\n---\n\n".join(pieces)
