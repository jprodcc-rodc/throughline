"""Centralized resolution of Reflection Pass state file paths.

Each ``default_*_file()`` function returns the path under
``$THROUGHLINE_STATE_DIR/`` (default
``~/throughline_runtime/state/``). Resolved lazily — env-var lookups
happen at call time so tests can monkeypatch ``THROUGHLINE_STATE_DIR``
and have it take effect on the next call.

Centralizing here avoids the previous spread of similar helpers
throughout ``daemon/reflection_pass.py``.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def default_state_dir() -> Path:
    """``$THROUGHLINE_STATE_DIR`` or ``~/throughline_runtime/state/``."""
    return Path(
        os.getenv(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()


def default_vault_root() -> Path:
    """``$THROUGHLINE_VAULT_ROOT`` or ``~/ObsidianVault/``."""
    return Path(
        os.getenv(
            "THROUGHLINE_VAULT_ROOT",
            str(Path.home() / "ObsidianVault"),
        )
    ).expanduser()


def default_state_file() -> Path:
    """Per-pass watermark + summary."""
    return default_state_dir() / "reflection_pass_state.json"


def default_cluster_names_file() -> Path:
    """``cluster_signature -> canonical_name`` cache (stage 3)."""
    return default_state_dir() / "reflection_cluster_names.json"


def default_backfill_state_file() -> Path:
    """``card_path|mtime -> {claim_summary, open_questions}`` cache
    (stage 4)."""
    return default_state_dir() / "reflection_backfill_state.json"


def default_open_threads_file() -> Path:
    """Cards with unresolved open questions (stage 5 output;
    consumed by ``find_open_threads`` MCP tool)."""
    return default_state_dir() / "reflection_open_threads.json"


def default_positions_file() -> Path:
    """Comprehensive per-cluster card position database (consumed
    by ``check_consistency`` + ``get_position_drift`` MCP tools).
    Refreshed on every pass."""
    return default_state_dir() / "reflection_positions.json"


def default_writeback_preview_file() -> Path:
    """Diff of what stage 8 would write to vault frontmatter
    (preview-only; real writeback gated behind --commit-writeback)."""
    return default_state_dir() / "reflection_writeback_preview.json"


def default_contradictions_file() -> Path:
    """Per-card contradiction findings (stage 6 output;
    consumed by ``check_consistency`` MCP tool when stage 6 is
    enabled, else the tool falls back to returning all cluster
    positions for the host LLM to weigh)."""
    return default_state_dir() / "reflection_contradictions.json"


def default_drift_file() -> Path:
    """Per-cluster drift trajectory with phase segmentation
    (stage 7 output; consumed by ``get_position_drift`` MCP
    tool when stage 7 is enabled, else the tool returns
    per-card trajectory)."""
    return default_state_dir() / "reflection_drift.json"


def all_state_files() -> dict[str, Path]:
    """Return a mapping of human-readable names to default paths
    for diagnostics and tooling (--inspect, doctor, etc.)."""
    return {
        "pass_state": default_state_file(),
        "cluster_names": default_cluster_names_file(),
        "backfill_cache": default_backfill_state_file(),
        "open_threads": default_open_threads_file(),
        "positions": default_positions_file(),
        "writeback_preview": default_writeback_preview_file(),
        "contradictions": default_contradictions_file(),
        "drift": default_drift_file(),
    }


# ---------- shared chronology helper ----------

def card_timestamp(card: dict) -> str:
    """Return a sortable string for chronological ordering.

    Priority:
    1. ``frontmatter.date``
    2. ``frontmatter.updated``
    3. ``mtime-<int>`` from file mtime
    4. ``"0"`` sentinel (sorts earliest)

    Used across stages 5/6/7 + state-file payload assembly. Hoisted
    here so the daemon and (future) MCP tools can share one
    definition without circular-import risk.
    """
    fm = card.get("frontmatter") or {}
    if isinstance(fm, dict):
        date = fm.get("date") or fm.get("updated")
        if date:
            return str(date)
    path = card.get("path", "")
    if path:
        try:
            return f"mtime-{int(Path(path).stat().st_mtime)}"
        except OSError:
            pass
    return "0"
