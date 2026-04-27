r"""Write conversation .md files into the daemon's RAW_ROOT.

The daemon's watchdog (`daemon/refine_daemon.py:1955`) picks up any
new `*.md` file under RAW_ROOT (recursive) and feeds it through the
refine pipeline. This module is the MCP-side companion: take a
text blob from the host LLM (Claude Desktop / Cursor / etc.), wrap
it into the file shape the daemon's parser expects, and drop it in
the right place.

**Format matters.** The daemon parses message turns via:

    _MSG_SPLIT_RE = re.compile(r"^## (user|assistant)\s*$", re.MULTILINE | re.IGNORECASE)

i.e. **`## user` / `## assistant` H2 headers, lowercase**. We
emit exactly that — not `# User` H1 (which would be silently
unparsed and treated as one giant chunk). See
`private/MCP_SCAFFOLDING_PLAN.md` § 7.2 for the audit notes that
caught this.

**Defensive turn-shape coercion.** If the host LLM passes free-form
prose without turn markers, we wrap it as a single `## user` block
so the slicer doesn't choke. If the host passes "User:" / "Assistant:"
prefix-line format (common in chat-export mental models), we
upgrade to H2. If H1 (`# User`), we re-headerize to H2.
"""
from __future__ import annotations

import os
import re
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Tuple


_H1_USER_RE = re.compile(r"^# *user\s*$", re.MULTILINE | re.IGNORECASE)
_H1_ASSISTANT_RE = re.compile(r"^# *assistant\s*$", re.MULTILINE | re.IGNORECASE)
_PREFIX_USER_RE = re.compile(r"^user:\s*", re.MULTILINE | re.IGNORECASE)
_PREFIX_ASSISTANT_RE = re.compile(r"^assistant:\s*", re.MULTILINE | re.IGNORECASE)
_H2_TURN_RE = re.compile(r"^## (user|assistant)\s*$", re.MULTILINE | re.IGNORECASE)


def _has_h2_turns(text: str) -> bool:
    return bool(_H2_TURN_RE.search(text))


def _has_h1_turns(text: str) -> bool:
    return bool(_H1_USER_RE.search(text) or _H1_ASSISTANT_RE.search(text))


def _has_prefix_turns(text: str) -> bool:
    return bool(_PREFIX_USER_RE.search(text) or _PREFIX_ASSISTANT_RE.search(text))


def coerce_to_turns(text: str) -> str:
    """Coerce any reasonable input shape into the daemon's expected
    `## user` / `## assistant` H2 format. Idempotent on already-correct
    input.

    Order matters: check most-specific format first.
    """
    if _has_h2_turns(text):
        return text  # already correct

    if _has_h1_turns(text):
        # Re-headerize H1 → H2, preserving capitalization-insensitive match
        text = _H1_USER_RE.sub("## user", text)
        text = _H1_ASSISTANT_RE.sub("## assistant", text)
        return text

    if _has_prefix_turns(text):
        # "User: hi" → "## user\nhi"; "Assistant: hi" → "## assistant\nhi"
        text = _PREFIX_USER_RE.sub("## user\n", text)
        text = _PREFIX_ASSISTANT_RE.sub("## assistant\n", text)
        return text

    # No turn structure detected — wrap entire text as one user turn
    return "## user\n\n" + text.strip()


def _safe_id(s: str) -> str:
    """Slug-safe fragment for filenames."""
    return re.sub(r"[^A-Za-z0-9_-]", "", s)[:36] or "anon"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _today_iso() -> str:
    return date.today().isoformat()


def _build_frontmatter(
    title: str | None,
    source: str,
    conv_id: str,
) -> str:
    """YAML frontmatter the daemon's slicer reads.

    Mirrors the keys `throughline_cli/adapters/common.py:render_markdown`
    emits — minus a few we don't have access to from MCP context
    (e.g. source_updated_at == source_conversation_id).
    """
    today = _today_iso()
    now = _now_iso()
    safe_title = (title or "").replace('"', '\\"')
    lines = ["---"]
    if title:
        lines.append(f'title: "{safe_title}"')
    lines.append(f"date: {today}")
    lines.append(f"updated: {now}")
    lines.append(f'source_platform: "{source}"')
    lines.append(f'source_conversation_id: "{conv_id}"')
    lines.append(f'import_source: "mcp-{today}"')
    lines.append("---")
    return "\n".join(lines)


def _target_path(out_dir: Path, conv_date: date, conv_id: str) -> Path:
    """`$RAW_ROOT/YYYY-MM/YYYY-MM-DD_<id>.md` — same convention the
    OpenWebUI / ChatGPT / Claude export adapters use.
    """
    month_dir = out_dir / f"{conv_date.year:04d}-{conv_date.month:02d}"
    return month_dir / f"{conv_date.isoformat()}_{_safe_id(conv_id)}.md"


def write_conversation(
    text: str,
    raw_root: Path,
    title: str | None = None,
    source: str = "claude_desktop",
    conv_id: str | None = None,
) -> Tuple[Path, str]:
    """Write a conversation .md to RAW_ROOT in the daemon's expected
    shape. Returns (path_written, conv_id_used).

    Raises:
        FileNotFoundError: if RAW_ROOT doesn't exist (daemon not
            initialized; let the caller surface a friendly message).
        OSError: filesystem errors (permission, disk full, etc.).
    """
    if not raw_root.exists():
        raise FileNotFoundError(
            f"RAW_ROOT not found: {raw_root}. "
            f"Run `python -m throughline_cli doctor` to verify install."
        )

    if not text or not text.strip():
        raise ValueError("text must be non-empty")

    conv_id = conv_id or f"mcp-{datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
    coerced_body = coerce_to_turns(text)
    frontmatter = _build_frontmatter(title, source, conv_id)

    file_body_parts = [frontmatter, ""]
    if title:
        file_body_parts.append(f"# {title}")
        file_body_parts.append("")
    file_body_parts.append(coerced_body)
    file_body = "\n".join(file_body_parts).rstrip() + "\n"

    target = _target_path(raw_root, date.today(), conv_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(file_body, encoding="utf-8")

    return target, conv_id


def estimate_cost_usd(text: str, tier: str = "normal") -> float:
    """Rough USD estimate for refining this conversation. Mirrors
    `throughline_cli/wizard.py:_TIER_COST_PER_CONV` numbers.

    Crude char/4 → tokens, then per-tier $/conversation midpoint.
    """
    tier_cost = {
        "skim": 0.005,
        "normal": 0.040,
        "deep": 0.200,
    }.get(tier, 0.040)
    # If text is unusually long (>~10K tokens), scale upward.
    tokens = max(1, len(text) // 4)
    if tokens > 10_000:
        tier_cost *= tokens / 5_000
    return round(tier_cost, 4)


# =========================================================
# wait_for_refine — poll daemon's refine_state.json
# =========================================================

import json as _json  # noqa: E402  (intentional: cheap top-level guard)
import time as _time   # noqa: E402

# Statuses the daemon writes to refine_state.json at the END of
# processing a raw file. See `daemon/refine_daemon.py` lines around
# 1781 / 1792 / 1800 / 1824 / 1831 / 1847 / 1853.
_TERMINAL_STATUSES: frozenset[str] = frozenset({
    "ok",                     # cards written
    "no_cards_written",       # daemon ran but no slice survived
    "permanent_reject",       # daemon explicitly rejected
    "source_model_skipped",   # pack_source_model_guard opt-out
    "ephemeral_skipped",      # ephemeral-short heuristic
    "echo_blocked",           # Echo Guard caught a redundant refine
    "slice_failed",           # slicer LLM call failed
    "no_keep_slices",         # all slices marked keep=false
})


def wait_for_terminal_status(
    raw_path: Path,
    state_dir: Path,
    timeout_s: float = 60.0,
    poll_interval_s: float = 1.0,
) -> tuple[str, dict | None]:
    """Poll `<state_dir>/refine_state.json` until the daemon writes a
    terminal status for `raw_path`, or until `timeout_s` expires.

    Args:
        raw_path: Absolute path of the raw .md file we just wrote.
            Daemon's state file keys are forward-slash-normalised
            absolute paths; we normalise the same way.
        state_dir: Directory containing `refine_state.json` (matches
            daemon's `STATE_DIR`, normally
            `~/throughline_runtime/state/`).
        timeout_s: Max wait. Default 60s — covers ~95% of refines on
            cloud LLMs at normal tier.
        poll_interval_s: Sleep between polls. Default 1s.

    Returns:
        (status, entry) tuple.
        - `status`: one of the terminal status strings from the
          daemon, or the string ``"timeout"`` if the wait expired
          before any terminal status was written.
        - `entry`: the per-file dict from refine_state.json (with
          `raw_hash`, `status`, optional `cards`, optional `updated`)
          on terminal success; `None` on timeout.
    """
    state_file = state_dir / "refine_state.json"
    key = str(raw_path).replace(os.sep, "/")
    deadline = _time.time() + timeout_s

    while _time.time() < deadline:
        if state_file.exists():
            try:
                data = _json.loads(state_file.read_text(encoding="utf-8"))
            except (OSError, _json.JSONDecodeError):
                # Daemon may be mid-write (atomic but tiny windows
                # exist). Sleep + retry.
                _time.sleep(poll_interval_s)
                continue
            files_state = data.get("files", {})
            entry = files_state.get(key)
            if entry and entry.get("status") in _TERMINAL_STATUSES:
                return (entry["status"], entry)
        _time.sleep(poll_interval_s)

    return ("timeout", None)
