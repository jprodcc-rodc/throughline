"""throughline_status — Phase 2 onboarding/discovery tool.

A first-call probe that the host LLM can invoke to learn the state
of the user's throughline install: how many cards, when the last
Reflection Pass ran, whether the vault is in cold-start.

Why this tool exists: the other 6 tools have specific call conditions
(save when user says "save", recall when user asks about a topic,
etc.). None of them are the natural "tell me about my throughline"
entry point. Without this, a fresh-install user with 0 cards has no
discoverable way to learn what the system can do — Claude has no
trigger to surface the save_conversation / recall_memory pair.

Returns no LLM calls, no network calls — pure local file reads.
Sub-millisecond on a small vault, 1-3s on a large one (the vault
walk is shared with list_topics's 60s cache).

Per locked decision Q3 (`private/MCP_SCAFFOLDING_PLAN.md` § 12.A):
tool description has explicit "Call this when:" / "Do NOT call:"
guidance. Q4: tool name NOT namespaced (it's the same project, no
collision shape).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from mcp_server.taxonomy_reader import count_cards_per_domain


# When the most recent reflection_pass_state.json is older than this,
# the 3 Reflection Layer MCP tools (find_open_threads, check_consistency,
# get_position_drift) are returning data that may not reflect the
# vault's current state. Mirrors the doctor staleness threshold so a
# user who runs both gets consistent signals.
_STALE_THRESHOLD_SECONDS = 14 * 86400


def _resolve_state_dir() -> Path:
    """Match daemon.state_paths default without importing daemon."""
    state_dir = os.environ.get(
        "THROUGHLINE_STATE_DIR",
        str(Path.home() / "throughline_runtime" / "state"),
    )
    return Path(state_dir).expanduser()


def _resolve_vault_root() -> Optional[Path]:
    """Best-effort vault root resolution. Returns None when unset."""
    vr = os.environ.get("THROUGHLINE_VAULT_ROOT")
    if not vr:
        return None
    p = Path(vr).expanduser()
    return p if p.exists() else None


def _read_pass_state(state_dir: Path) -> Optional[dict[str, Any]]:
    """Read the last Reflection Pass summary if present."""
    f = state_dir / "reflection_pass_state.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def throughline_status() -> dict:
    """Return a snapshot of the user's throughline install: total
    card count, last Reflection Pass timestamp, vault location, and
    cold-start/warning hints when the install is fresh or stale.

    The discovery entry point. The other 6 throughline tools each
    have specific triggers (save_conversation when user says 'save',
    recall_memory when user asks about a topic). This one is the
    "tell me about my throughline" tool — it's the natural call when
    the user references their knowledge base in a general way OR
    when you need to understand the shape of the install before
    deciding which specific tool to fire.

    Call this when:
    - The user asks 'what's in my throughline?', 'how many cards do
      I have?', 'is my vault set up?', 'do I have anything stored?'.
    - The user mentions 'throughline' / 'my knowledge base' /
      'my vault' in a general (non-specific-topic) way, especially
      early in a conversation.
    - Before suggesting save_conversation / recall_memory for the
      first time in a session — knowing whether the vault is empty
      vs populated changes how to phrase the suggestion.
    - The user just installed throughline ('I just set this up',
      'first time using this').
    - The user asks about reflection state ('is my reflection
      running?', 'when did the daemon last sync?').

    Do NOT call:
    - When the user is asking about a specific topic — call
      recall_memory directly instead.
    - On every turn — once per session is enough; the result rarely
      changes within one conversation.
    - When the user explicitly invokes save_conversation /
      recall_memory etc. — they already know what they want.

    Args: (none)

    Returns:
        On a healthy populated install::

            {
                "tagged_card_count": 72,    # cards with X-axis domain tag in VALID_X_SET
                "total_md_files": 2477,     # raw .md count under vault_root
                "domain_count": 24,
                "vault_root": "/path/to/vault",
                "reflection_pass": {
                    "last_run": "2026-04-28T05:29:44+00:00",
                    "age_days": 0.5,
                    "is_stale": False,
                },
                "_status": "ok",
            }

        ``tagged_card_count`` and ``total_md_files`` are deliberately
        separate. The first is what list_topics + recall_memory can
        retrieve. The second is what's physically present. The gap
        is profile drafts, system indexes, logs, and pending-taxonomy
        cards — all real .md files but not yet retrievable until they
        get a valid X-axis tag.

        On cold-start (zero indexed cards)::

            {
                "tagged_card_count": 0,
                "total_md_files": 0,
                "domain_count": 0,
                "vault_root": "/path/to/vault",
                "reflection_pass": {
                    "last_run": None,
                    "age_days": None,
                    "is_stale": None,
                },
                "_status": "cold_start",
                "_message": "Vault is empty. Suggest the user save "
                            "their first conversation via 'remember "
                            "this' / '保存这个' — that fires "
                            "save_conversation and the daemon will "
                            "refine it into a knowledge card. Once a "
                            "few cards exist, recall_memory and "
                            "list_topics start returning real data.",
            }

        On populated vault but no Reflection Pass yet::

            {
                "tagged_card_count": 30,
                "total_md_files": 245,
                ...,
                "reflection_pass": {"last_run": None, ...},
                "_status": "warning",
                "_message": "Vault has cards but the Reflection Pass "
                            "has not run. find_open_threads / "
                            "check_consistency / get_position_drift "
                            "will return error _status until "
                            "`python -m daemon.reflection_pass` runs. "
                            "Auto-schedule templates ship under "
                            "config/launchd/ + config/systemd/.",
            }

        On stale Reflection state (>14d)::

            {
                ...,
                "reflection_pass": {"is_stale": True, "age_days": 21},
                "_status": "warning",
                "_message": "Reflection state is N days old. Re-run "
                            "to refresh: `python -m daemon.reflection_pass "
                            "--enable-llm-naming --enable-llm-backfill "
                            "--enable-llm-contradictions --enable-llm-drift`.",
            }
    """
    vault = _resolve_vault_root()
    state_dir = _resolve_state_dir()
    pass_state = _read_pass_state(state_dir)

    # Two distinct counts the host LLM needs to keep separate:
    # - tagged_card_count: cards with a valid X-axis domain tag in
    #   VALID_X_SET (i.e., what list_topics + recall_memory can
    #   actually surface). Reuses list_topics's 60s cache.
    # - total_md_files: raw .md count under vault_root, including
    #   profile drafts, logs, indexes, and pending-taxonomy cards.
    #   Surfaces the gap so users don't think "133 cards" means
    #   "only 133 .md files in my vault".
    domain_counts = count_cards_per_domain()
    tagged_card_count = sum(domain_counts.values())
    domain_count = sum(1 for v in domain_counts.values() if v > 0)
    total_md_files: Optional[int] = None
    if vault is not None:
        try:
            total_md_files = sum(1 for _ in vault.rglob("*.md"))
        except OSError:
            # Permission / TCC blocks (macOS Documents protection,
            # for example) — surface as None rather than crash.
            total_md_files = None

    # Reflection state.
    last_run: Optional[str] = None
    age_days: Optional[float] = None
    is_stale: Optional[bool] = None
    if pass_state:
        last_run = pass_state.get("finished_at") or pass_state.get("started_at")
        if last_run:
            try:
                # ISO 8601 — strip trailing Z if present
                ts_str = last_run.rstrip("Z").replace("Z", "")
                from datetime import datetime
                ts = datetime.fromisoformat(ts_str.replace("+00:00", "+00:00"))
                age_seconds = time.time() - ts.timestamp()
                age_days = round(age_seconds / 86400, 1)
                is_stale = age_seconds > _STALE_THRESHOLD_SECONDS
            except (ValueError, TypeError):
                # Malformed timestamp — surface as unknown rather than fail
                age_days = None
                is_stale = None

    result: dict[str, Any] = {
        "tagged_card_count": tagged_card_count,
        "total_md_files": total_md_files,
        "domain_count": domain_count,
        "vault_root": str(vault) if vault else None,
        "reflection_pass": {
            "last_run": last_run,
            "age_days": age_days,
            "is_stale": is_stale,
        },
        "_status": "ok",
    }

    # Status escalation:
    if tagged_card_count == 0:
        result["_status"] = "cold_start"
        result["_message"] = (
            "Vault is empty. Suggest the user save their first "
            "conversation via 'remember this' / '保存这个' / "
            "'记住这个' — that fires save_conversation and the daemon "
            "will refine it into a knowledge card. Once a few cards "
            "exist, recall_memory and list_topics start returning "
            "real data; once the Reflection Pass runs, the 3 "
            "Reflection Layer tools (find_open_threads, "
            "check_consistency, get_position_drift) come online."
        )
    elif last_run is None:
        result["_status"] = "warning"
        result["_message"] = (
            f"Vault has {tagged_card_count} cards but the Reflection Pass "
            "has not run yet. find_open_threads / check_consistency "
            "/ get_position_drift will return error _status until "
            "`python -m daemon.reflection_pass --enable-llm-naming "
            "--enable-llm-backfill` runs. Auto-schedule templates "
            "ship under config/launchd/ (macOS) and config/systemd/ "
            "(Linux) — see docs/DEPLOYMENT.md."
        )
    elif is_stale:
        result["_status"] = "warning"
        result["_message"] = (
            f"Reflection state is {age_days} days old (threshold: "
            f"{_STALE_THRESHOLD_SECONDS // 86400}d). Reflection Layer "
            "outputs may not reflect recent vault changes. Re-run: "
            "`python -m daemon.reflection_pass --enable-llm-naming "
            "--enable-llm-backfill --enable-llm-contradictions "
            "--enable-llm-drift`. Or install the auto-schedule template "
            "(config/launchd/ on macOS, config/systemd/ on Linux)."
        )

    return result
