"""Configuration resolution for the MCP server.

Reads paths from the same environment variables / defaults the
daemon reads — single source of truth, no separate config file
for MCP. If `~/.throughline/config.toml` exists it can extend this
later; v1 just mirrors `daemon/refine_daemon.py:101-104`.

Why not just import from daemon? Pulling daemon in transitively
loads watchdog + the full refine pipeline; that's overkill for
the MCP server which only needs a few path strings. Keep this
file dependency-free.
"""
from __future__ import annotations

import os
from pathlib import Path


def get_raw_root() -> Path:
    """Where the daemon's watchdog looks for new conversation .md
    files. Matches `daemon/refine_daemon.py:102` exactly so the
    MCP server and the daemon agree on the same directory.
    """
    return Path(
        os.getenv(
            "THROUGHLINE_RAW_ROOT",
            str(Path.home() / "throughline_runtime" / "sources" / "openwebui_raw"),
        )
    ).expanduser()


def get_vault_root() -> Path:
    """Where refined cards land. Matches
    `daemon/refine_daemon.py:101`.
    """
    return Path(
        os.getenv(
            "THROUGHLINE_VAULT_ROOT",
            str(Path.home() / "ObsidianVault"),
        )
    ).expanduser()


def get_state_dir() -> Path:
    """Where daemon state files live. Matches
    `daemon/refine_daemon.py:103`.
    """
    return Path(
        os.getenv(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()
