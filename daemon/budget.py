"""U3 · Daily budget cap enforcement.

The daemon tracks per-call cost in `state/cost_stats.json` via
`refine_daemon._record_cost`. This module reads that file and answers
one question: *have we already spent too much today?*

If yes, the worker skips the current raw file WITHOUT updating
state — the file stays unprocessed, and either the next day's clock
tick, the next daemon restart, or a manual touch re-delivers it.
That's intentional: silently dropping work is worse than deferring
it; partial-refine state is worse than either.

Extracted into its own module so the CLI (`throughline_cli budget`,
future) and unit tests can exercise it without the full daemon
import surface (watchdog, Qdrant, embedder, …).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def _config_path() -> Path:
    override = os.environ.get("THROUGHLINE_CONFIG_DIR")
    base = Path(override).expanduser() if override else (Path.home() / ".throughline")
    return base / "config.toml"


def _state_dir() -> Path:
    return Path(
        os.getenv(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()


def default_cost_stats_file() -> Path:
    return _state_dir() / "cost_stats.json"


def load_budget() -> Optional[float]:
    """Resolve the active daily cap.

    Precedence:
      1. `THROUGHLINE_MAX_DAILY_USD` env var (highest — ops overrides config)
      2. `daily_budget_usd` in `~/.throughline/config.toml` (wizard value)
      3. `None` → no cap enforced

    None means "unlimited" (default for users who never ran the wizard).
    A value of 0 is treated as "pause all refines" — explicit zero is a
    valid kill-switch.
    """
    env = os.environ.get("THROUGHLINE_MAX_DAILY_USD")
    if env is not None and env.strip() != "":
        try:
            return float(env)
        except ValueError:
            pass
    p = _config_path()
    if not p.exists():
        return None
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:  # pragma: no cover
            import tomli as tomllib  # type: ignore
        with p.open("rb") as fh:
            data = tomllib.load(fh)
        raw = data.get("daily_budget_usd")
        if raw is None:
            return None
        return float(raw)
    except (OSError, ValueError) as e:
        # Malformed config shouldn't brick the daemon. Fall through to
        # "no cap" so work proceeds.
        try:
            sys.stderr.write(f"[budget] config read failed: {e}\n")
        except Exception:
            pass
        return None


def today_key(now: Optional[datetime] = None) -> str:
    """Local-date key used by `_record_cost`. Kept in sync on purpose."""
    return (now or datetime.now()).strftime("%Y-%m-%d")


def load_daily_total(stats_path: Optional[Path] = None,
                      today: Optional[str] = None) -> float:
    """Sum every step's cost for today's key. Returns 0.0 when the
    file is missing, malformed, or today has no entries."""
    p = stats_path if stats_path is not None else default_cost_stats_file()
    if not p.exists():
        return 0.0
    try:
        stats: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0.0
    by_date = stats.get("by_date") or {}
    day = by_date.get(today or today_key()) or {}
    total = 0.0
    for step in day.values():
        if isinstance(step, dict):
            try:
                total += float(step.get("cost") or 0.0)
            except (TypeError, ValueError):
                continue
    return round(total, 6)


def budget_exceeded(budget_usd: Optional[float] = None,
                     stats_path: Optional[Path] = None,
                     today: Optional[str] = None) -> bool:
    """True when today's spend meets or exceeds the cap.

    - `None` cap           → always False (no cap)
    - `0.0` cap            → True iff any spend has happened today
                              (explicit kill-switch)
    - `cap > 0`            → True iff `load_daily_total() >= cap`
    """
    cap = budget_usd if budget_usd is not None else load_budget()
    if cap is None:
        return False
    spent = load_daily_total(stats_path=stats_path, today=today)
    if cap == 0.0:
        return spent > 0.0
    return spent >= cap


def remaining_budget(budget_usd: Optional[float] = None,
                      stats_path: Optional[Path] = None,
                      today: Optional[str] = None) -> Optional[float]:
    """Dollars left before today's cap. None when no cap is configured."""
    cap = budget_usd if budget_usd is not None else load_budget()
    if cap is None:
        return None
    spent = load_daily_total(stats_path=stats_path, today=today)
    return max(0.0, round(cap - spent, 6))
