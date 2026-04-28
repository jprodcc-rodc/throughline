"""find_loose_ends — Phase 2 implementation, surfaces unfinished thinking.

Renamed from ``find_open_threads`` (2026-04-28) to differentiate
from Anthropic's Cowork **persistent agent thread** (2026-04-09 GA),
which is a TASK execution agent that runs in an isolated VM and
performs autonomous workflows. throughline's loose ends are the
opposite shape: introspective surfacing of **unfinished reasoning
in your knowledge base** — questions you raised in past
conversations that never got resolved. No agent, no execution,
just visibility into stuck thoughts.

Reads the state file written by ``daemon.reflection_pass`` stage 5
(``reflection_open_threads.json`` on disk — kept under that name
for backward compat with vaults that already have it) and surfaces
cards with unresolved open questions to the host LLM.

The Reflection Pass daemon does the expensive work offline:
- back-fill open_questions per card via LLM (stage 4)
- detect resolution by token-overlap structural scan (stage 5)
- write the result file

This tool is a thin reader. No LLM calls, no vault scan, just JSON
read + optional topic filter + result shaping. Sub-millisecond.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


def _resolve_state_file() -> Path:
    """Match ``daemon.reflection_pass.default_open_threads_file()``
    without importing daemon (mcp_server stays decoupled)."""
    state_dir = os.environ.get(
        "THROUGHLINE_STATE_DIR",
        str(Path.home() / "throughline_runtime" / "state"),
    )
    return Path(state_dir).expanduser() / "reflection_open_threads.json"


def _load_state(path: Path) -> Optional[dict[str, Any]]:
    """Load state file. Returns None when missing / unreadable /
    not-a-dict; caller surfaces the absence as an error result."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def _filter_by_topic(
    entries: list[dict[str, Any]],
    topic: str,
) -> list[dict[str, Any]]:
    """Case-insensitive substring match on topic_cluster. Lets users
    type 'pricing' and match 'pricing_strategy', 'b1' and match
    'b1_thiamine_therapy', etc."""
    needle = topic.lower().strip()
    if not needle:
        return entries
    return [
        e for e in entries
        if needle in str(e.get("topic_cluster", "")).lower()
    ]


def find_loose_ends(
    topic: Optional[str] = None,
    limit: int = 5,
) -> dict:
    """Find unfinished thinking the user may want to resume — open
    questions without a follow-up answer, hypotheses left without
    a conclusion, branches the user started exploring but never
    closed. throughline's Reflection Pass daemon (stage 5) tags
    these structurally; this tool surfaces them.

    NOT to be confused with Claude Desktop's Cowork "persistent
    agent thread" feature (which is a TASK execution agent running
    autonomous workflows in an isolated VM). loose_ends are
    *introspective* — surfacing UNFINISHED REASONING from your
    own past chats. No agent, no execution, just visibility into
    stuck thoughts so you can pick them back up.

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

    Example trigger conversations:

    - User: "Let's revisit pricing again" — call
      ``find_loose_ends(topic="pricing")``.
    - User: "Where did I leave off on the database migration?" —
      call ``find_loose_ends(topic="database migration")``.
    - User: "What was I thinking about freemium conversion?" —
      call ``find_loose_ends(topic="freemium")``.
    - User: "I need to think through the auth layer" — if the
      user has reasoned about auth before (you can check via
      list_topics first if unsure), call
      ``find_loose_ends(topic="auth")``.

    Args:
        topic: Optional topic filter. Case-insensitive substring
            match against ``topic_cluster``. ``"pricing"`` matches
            ``"pricing_strategy"`` etc.
        limit: Max open threads to return (default 5). Most-recently
            touched surface first.

    Returns:
        On success::

            {
                "open_threads": [
                    {
                        "card_path": "vault/.../card.md",
                        "topic_cluster": "pricing_strategy",
                        "open_questions": ["how to handle freemium...?"],
                        "last_touched": "2026-02-12",
                        "context_summary": "Analyzed LTV math; "
                                           "stopped before resolving "
                                           "freemium.",
                    },
                    ...
                ],
                "total_open_threads": 7,
                "_status": "ok",
            }

        When the Reflection Pass hasn't run yet (no state file)::

            {
                "open_threads": [],
                "total_open_threads": 0,
                "_status": "error",
                "_message": "Reflection Pass has not run yet. Run "
                            "`python -m daemon.reflection_pass "
                            "--enable-llm-backfill` to populate.",
            }

        When the topic filter matches no threads::

            {
                "open_threads": [],
                "total_open_threads": 0,
                "_status": "ok",
                "_message": "No open threads match topic 'xyz'.",
            }
    """
    state_path = _resolve_state_file()
    state = _load_state(state_path)

    if state is None:
        return {
            "open_threads": [],
            "total_open_threads": 0,
            "_status": "error",
            "_message": (
                f"Reflection Pass has not run yet (no state file at "
                f"{state_path}). Run `python -m daemon.reflection_pass "
                "--enable-llm-backfill` to populate."
            ),
        }

    entries = state.get("open_threads", [])
    if not isinstance(entries, list):
        return {
            "open_threads": [],
            "total_open_threads": 0,
            "_status": "error",
            "_message": (
                f"State file at {state_path} is malformed (open_threads "
                "is not a list). Re-run the Reflection Pass."
            ),
        }

    total = len(entries)

    if topic:
        filtered = _filter_by_topic(entries, topic)
    else:
        filtered = list(entries)

    # Sort by last_touched descending (most recent first).
    # Strings sort lexicographically; ISO date strings already sort
    # correctly. Cards using "mtime-NNN" fallback also sort consistently
    # (mtime-9999 > mtime-100 lexically? No — but those would be edge
    # cases; for ISO dates this works.).
    filtered.sort(
        key=lambda e: str(e.get("last_touched", "")),
        reverse=True,
    )

    if limit and limit > 0:
        filtered = filtered[: limit]

    if topic and not filtered:
        return {
            "open_threads": [],
            "total_open_threads": 0,
            "_status": "ok",
            "_message": f"No open threads match topic {topic!r}.",
        }

    return {
        "open_threads": filtered,
        "total_open_threads": total,
        "_status": "ok",
    }
