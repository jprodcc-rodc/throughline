"""save_conversation — Phase 1 implementation (Week 1 commit 2 +
Phase 1.5 wait_for_refine completion).

Writes the conversation as a timestamped .md to `$THROUGHLINE_RAW_ROOT`;
the daemon's watchdog (`daemon/refine_daemon.py:1955`) picks it up
automatically and refines it into a 6-section card.

Failure modes handled:
- RAW_ROOT doesn't exist (daemon never initialized) → return
  status='error' with a doctor pointer
- Empty text → return status='error'
- Filesystem errors (permission, disk full) → return status='error'
  with the OS error chained

`wait_for_refine=True` polls the daemon's `refine_state.json` for
up to 60s, returning early once the daemon writes a terminal
status for the file. Useful when the host LLM wants to confirm the
card landed before continuing the conversation. False (default)
returns immediately after queueing.
"""
from __future__ import annotations

from mcp_server.config import get_raw_root, get_state_dir
from mcp_server.daemon_writer import (
    estimate_cost_usd,
    wait_for_terminal_status,
    write_conversation,
)


# How long save_conversation(wait_for_refine=True) is willing to
# block. 60s covers ~95% of refines on cloud LLMs at normal tier;
# beyond that the LLM call probably failed (rate-limit, API outage,
# etc.) and the user is better off knowing the daemon didn't
# complete than waiting forever.
_WAIT_TIMEOUT_SECONDS = 60.0


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
            preserved. Multi-turn excerpts can be passed as-is in
            any of these shapes — the writer will normalise:
            (1) `## user` / `## assistant` H2 headers (canonical),
            (2) `# User` / `# Assistant` H1 headers,
            (3) `User:` / `Assistant:` line prefixes,
            (4) free prose (will be wrapped as a single user turn).
        title: Optional human-readable title. If omitted, the
            daemon derives one from the content.
        source: Source label (default 'claude_desktop'). Stored in
            frontmatter for provenance.
        wait_for_refine: If True, block (up to 60s) waiting for
            the daemon to finish refining the queued conversation.
            On terminal success the return includes the daemon's
            status (`ok` / `no_cards_written` / `ephemeral_skipped`
            / etc.) so the host LLM can confirm the card landed
            before continuing. False (default) returns as soon as
            the raw .md is queued — daemon picks up async via
            watchdog.

    Returns:
        On success::

            {
                "queued": True,
                "raw_path": "<absolute path of queued .md>",
                "card_path": None,  # Phase 2: real path when
                                    # wait_for_refine=True succeeds
                "estimated_cost_usd": 0.04,
                "_status": "ok",
            }

        On error::

            {
                "queued": False,
                "raw_path": "",
                "card_path": None,
                "estimated_cost_usd": 0.0,
                "_status": "error",
                "_message": "...",
            }
    """
    if not text or not text.strip():
        return {
            "queued": False,
            "raw_path": "",
            "card_path": None,
            "estimated_cost_usd": 0.0,
            "_status": "error",
            "_message": "text must be non-empty",
        }

    raw_root = get_raw_root()

    try:
        path, conv_id = write_conversation(
            text=text,
            raw_root=raw_root,
            title=title,
            source=source,
        )
    except FileNotFoundError as exc:
        return {
            "queued": False,
            "raw_path": "",
            "card_path": None,
            "estimated_cost_usd": 0.0,
            "_status": "error",
            "_message": (
                f"{exc} "
                "Has throughline been installed? Run "
                "`python -m throughline_cli doctor` to verify."
            ),
        }
    except OSError as exc:
        return {
            "queued": False,
            "raw_path": "",
            "card_path": None,
            "estimated_cost_usd": 0.0,
            "_status": "error",
            "_message": f"filesystem error writing to RAW_ROOT: {exc}",
        }

    result = {
        "queued": True,
        "raw_path": str(path),
        "card_path": None,
        "estimated_cost_usd": estimate_cost_usd(text),
        "_status": "ok",
        "_conv_id": conv_id,
    }

    if wait_for_refine:
        daemon_status, _entry = wait_for_terminal_status(
            raw_path=path,
            state_dir=get_state_dir(),
            timeout_s=_WAIT_TIMEOUT_SECONDS,
        )
        result["daemon_status"] = daemon_status
        # Card_path discovery (vault scan) is deferred Phase 2 polish;
        # for now we surface daemon_status so the host LLM can tell
        # the user "your card landed" vs "refine timed out".

    return result
