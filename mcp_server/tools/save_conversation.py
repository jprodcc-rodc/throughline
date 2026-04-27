"""save_conversation — Phase 1 stub.

Real implementation lands in Week 1 commit 2: writes a timestamped
.md to `$THROUGHLINE_RAW_ROOT/`, daemon watchdog picks up
automatically. See `private/MCP_SCAFFOLDING_PLAN.md` § 3.1 for
the schema and § 7.2 for the defensive turn-shape coercion.
"""
from __future__ import annotations


def save_conversation(
    text: str,
    title: str | None = None,
    source: str = "claude_desktop",
    wait_for_refine: bool = False,
) -> dict:
    """Save the current conversation (or a snippet of it) into
    throughline's refine pipeline. The daemon will refine it into
    a 6-section knowledge card and add it to the user's vault.

    Call this when:
    - The user explicitly asks to "save", "remember", "捕获",
      or similar.
    - The user signals an important decision, conclusion, or
      personal-context fact they want captured ("I've decided X",
      "from now on Y", "remember that I'm allergic to Z").
    - At natural breakpoints in a long reasoning session, with
      user confirmation.

    Do NOT call:
    - On every turn / proactively without user signal — the user
      curates what gets saved.
    - When the user is mid-thought; wait for closure.
    - For trivia or small talk.

    Args:
        text: The conversation segment to save. Markdown is
            preserved. If this is a multi-turn excerpt, format as
            User: ... / Assistant: ... blocks.
        title: Optional human-readable title. If omitted, the daemon
            derives one from the content.
        source: Source label (default 'claude_desktop'). Stored in
            frontmatter for provenance.
        wait_for_refine: If True, block until the daemon has
            refined and indexed the card (~10-30s). If False
            (default), return as soon as the raw .md is queued.

    Returns:
        dict with keys: queued (bool), raw_path (str),
        card_path (str | None — only if wait_for_refine=True),
        estimated_cost_usd (float).
    """
    return {
        "queued": False,
        "raw_path": "",
        "card_path": None,
        "estimated_cost_usd": 0.0,
        "_status": "stub",
        "_message": (
            "save_conversation is scaffolded but not yet implemented. "
            "Real logic lands in the next MCP commit (Week 1 commit 2)."
        ),
    }
