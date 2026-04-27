"""`python -m mcp_server --doctor` — verify MCP prerequisites.

Runs a small battery of checks the user can paste into a bug
report when MCP tools fail mysteriously. Doesn't touch user data,
doesn't make LLM calls, exits 0 if everything green or 1 if any
red.

Designed to mirror the throughline-base `python -m throughline_cli
doctor` pattern (an installed-and-passing test suite for runtime
prerequisites). Six MCP-relevant checks:

1. fastmcp installed (Phase 1 hard dep, locked Q12.A)
2. RAW_ROOT directory exists (daemon's input queue)
3. VAULT_ROOT directory exists (daemon's output)
4. rag_server reachable on configured URL (recall_memory needs it)
5. daemon.taxonomy importable (list_topics needs it)
6. recent daemon log activity (proxy for "daemon is running")

All checks emit a `[ok | warn | fail]` line + a remediation hint
when not green. Output is plain text; no rich formatting needed.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from mcp_server import __version__
from mcp_server.config import get_raw_root, get_state_dir, get_vault_root
from mcp_server.rag_client import get_base_url


_GREEN_OK = "[ok]"
_YELLOW_WARN = "[warn]"
_RED_FAIL = "[fail]"


def _emit(status: str, name: str, detail: str = "", fix: str = "") -> None:
    line = f"  {status} {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    if fix:
        print(f"        fix: {fix}")


def _check_fastmcp() -> bool:
    try:
        import fastmcp  # noqa: F401
        return True
    except ImportError:
        _emit(
            _RED_FAIL,
            "fastmcp installed",
            "package not found",
            "pip install throughline-mcp  (or: pip install fastmcp)",
        )
        return False
    finally:
        pass


def _check_raw_root() -> bool:
    raw = get_raw_root()
    if raw.exists() and raw.is_dir():
        _emit(_GREEN_OK, "RAW_ROOT exists", str(raw))
        return True
    _emit(
        _RED_FAIL,
        "RAW_ROOT exists",
        f"missing: {raw}",
        "run `python install.py --express` once to initialise paths",
    )
    return False


def _check_vault_root() -> bool:
    vault = get_vault_root()
    if vault.exists() and vault.is_dir():
        _emit(_GREEN_OK, "VAULT_ROOT exists", str(vault))
        return True
    _emit(
        _YELLOW_WARN,
        "VAULT_ROOT exists",
        f"missing: {vault}",
        "ok if you haven't run the daemon yet; will be created on first refine",
    )
    return True  # not blocking


def _check_rag_server() -> bool:
    base = get_base_url()
    health = base + "/v1/rag/health"
    try:
        with urllib.request.urlopen(health, timeout=5) as resp:
            if resp.status == 200:
                _emit(_GREEN_OK, "rag_server reachable", base)
                return True
            _emit(
                _YELLOW_WARN,
                "rag_server reachable",
                f"HTTP {resp.status} from {health}",
                "rag_server returned a non-200; check rag_server logs",
            )
            return False
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        _emit(
            _RED_FAIL,
            "rag_server reachable",
            f"unreachable at {base} ({exc})",
            "start: `python rag_server/rag_server.py` "
            "(or set THROUGHLINE_RAG_URL if not on default localhost:8000)",
        )
        return False


def _check_daemon_taxonomy_import() -> bool:
    try:
        from daemon.taxonomy import VALID_X_SET
        if isinstance(VALID_X_SET, list) and len(VALID_X_SET) > 0:
            _emit(
                _GREEN_OK,
                "daemon.taxonomy importable",
                f"{len(VALID_X_SET)} domains in VALID_X_SET",
            )
            return True
        _emit(
            _YELLOW_WARN,
            "daemon.taxonomy importable",
            "VALID_X_SET is empty",
            "check config/taxonomy.py override or the bundled default",
        )
        return False
    except ImportError as exc:
        _emit(
            _RED_FAIL,
            "daemon.taxonomy importable",
            f"import failed: {exc}",
            "ensure throughline base package is installed: pip install -e .",
        )
        return False


def _check_daemon_recent_activity() -> bool:
    """Heuristic: refine_state.json modified within the last 7 days
    suggests the daemon has been running. Not a strict liveness
    check (a long-idle daemon is fine), but a "this install is in
    use" signal."""
    state_file = get_state_dir() / "refine_state.json"
    if not state_file.exists():
        _emit(
            _YELLOW_WARN,
            "daemon recent activity",
            "no state file yet",
            "ok if daemon hasn't been started; "
            "`python daemon/refine_daemon.py` to start",
        )
        return True
    try:
        mtime = state_file.stat().st_mtime
        age_days = (time.time() - mtime) / 86400
        if age_days < 7:
            _emit(
                _GREEN_OK,
                "daemon recent activity",
                f"state file {age_days:.1f}d old",
            )
            return True
        _emit(
            _YELLOW_WARN,
            "daemon recent activity",
            f"state file {age_days:.0f}d old",
            "daemon may not be running; check process list",
        )
        return True
    except OSError as exc:
        _emit(
            _YELLOW_WARN,
            "daemon recent activity",
            f"can't stat state file: {exc}",
        )
        return True


def run_doctor() -> int:
    """Run all checks. Return 0 if everything green/warn, 1 if any
    red fail."""
    print(f"throughline-mcp doctor (version {__version__})")
    print()
    print("Runtime prerequisites")
    print("─" * 40)

    fastmcp_ok = _check_fastmcp()
    raw_ok = _check_raw_root()
    vault_ok = _check_vault_root()
    rag_ok = _check_rag_server()
    taxonomy_ok = _check_daemon_taxonomy_import()
    daemon_ok = _check_daemon_recent_activity()

    # Hard-fail criteria: fastmcp + RAW_ROOT + rag_server + taxonomy
    # are required for save / recall / list. Vault + daemon-activity
    # are warnings only (the daemon doesn't have to be running for
    # save_conversation to queue a file).
    hard_fail = not (fastmcp_ok and raw_ok and rag_ok and taxonomy_ok)

    print()
    if hard_fail:
        print("doctor: one or more required checks FAILED.")
        print(
            "Fix the [fail] items above; warnings are usually OK to leave."
        )
        return 1

    print("doctor: all required checks PASSED.")
    if not vault_ok or not daemon_ok:
        print("(some warnings — usually OK if you're just installing.)")
    return 0


if __name__ == "__main__":
    sys.exit(run_doctor())
