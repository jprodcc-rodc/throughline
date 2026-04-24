"""`python -m throughline_cli cost` — spend dashboard.

Reads `state/cost_stats.json` (written by `daemon._record_cost`
on every successful LLM call) and prints a human-readable
breakdown. No extra tracking — this is pure presentation.

Usage:
    python -m throughline_cli cost                  # today
    python -m throughline_cli cost today
    python -m throughline_cli cost week             # last 7 days
    python -m throughline_cli cost month            # last 30 days
    python -m throughline_cli cost all              # every recorded day
    python -m throughline_cli cost --json           # machine-readable

Output format:
    period: 2026-04-25  (today)
    total : $1.83

      Slicer           42 calls · $0.31
      Refiner         128 calls · $1.24
      DomainRouter     41 calls · $0.11
      SubpathRouter    35 calls · $0.10
      EchoJudge        12 calls · $0.07

      by model:
        anthropic/claude-sonnet-4.6  203 calls · $1.52
        anthropic/claude-haiku-4.5    55 calls · $0.31

Budget status (optional, if THROUGHLINE_MAX_DAILY_USD / config.toml):
    budget: $5.00/day · $3.17 remaining today
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


def _state_dir() -> Path:
    return Path(
        os.environ.get(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()


def _cost_stats_path() -> Path:
    return _state_dir() / "cost_stats.json"


def _load_stats() -> Dict[str, Any]:
    p = _cost_stats_path()
    if not p.exists():
        return {"by_date": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"by_date": {}}


def _parse_date(s: str) -> Optional[datetime]:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None


def _dates_for_period(period: str,
                      now: Optional[datetime] = None) -> List[str]:
    """Return the YYYY-MM-DD keys that fall within `period`."""
    now = now or datetime.now()
    if period == "today":
        return [now.strftime("%Y-%m-%d")]
    if period == "week":
        return [(now - timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(7)]
    if period == "month":
        return [(now - timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(30)]
    if period == "all":
        return None  # sentinel: caller uses every key in stats
    raise ValueError(f"unknown period: {period!r}")


def aggregate(stats: Dict[str, Any], period: str,
              now: Optional[datetime] = None) -> Dict[str, Any]:
    """Return a dict: total USD, per-step rollup, per-model rollup,
    day count."""
    by_date = stats.get("by_date") or {}
    target = _dates_for_period(period, now=now)
    if target is None:
        keys = list(by_date.keys())
    else:
        keys = [k for k in target if k in by_date]

    total = 0.0
    by_step: Dict[str, Dict[str, float]] = {}
    by_model: Dict[str, Dict[str, float]] = {}

    for date_key in keys:
        day = by_date.get(date_key) or {}
        for step_name, rec in day.items():
            if not isinstance(rec, dict):
                continue
            cost = float(rec.get("cost") or 0.0)
            calls = int(rec.get("calls") or 0)
            in_tok = int(rec.get("input_tokens") or 0)
            out_tok = int(rec.get("output_tokens") or 0)
            total += cost
            step_row = by_step.setdefault(step_name, {
                "calls": 0, "cost": 0.0,
                "input_tokens": 0, "output_tokens": 0,
            })
            step_row["calls"] += calls
            step_row["cost"] += cost
            step_row["input_tokens"] += in_tok
            step_row["output_tokens"] += out_tok
            # by-model breakdown (optional; older records may lack
            # the per-model row).
            model = rec.get("model")
            if isinstance(model, str):
                model_row = by_model.setdefault(model, {
                    "calls": 0, "cost": 0.0,
                })
                model_row["calls"] += calls
                model_row["cost"] += cost

    return {
        "period": period,
        "days_covered": len(keys),
        "total": round(total, 4),
        "by_step": by_step,
        "by_model": by_model,
    }


def _resolve_budget() -> Optional[float]:
    """Pull the budget cap via the same resolver the daemon uses."""
    try:
        from daemon.budget import load_budget
        return load_budget()
    except Exception:
        return None


def _spent_today_usd() -> float:
    try:
        from daemon.budget import load_daily_total
        return load_daily_total()
    except Exception:
        return 0.0


USAGE = """\
throughline cost — LLM spend dashboard.

Usage:
    python -m throughline_cli cost [period] [options]

Period (optional; defaults to `today`):
    today       Spend since 00:00 local time (the default).
    week        Last 7 days.
    month       Last 30 days.
    all         Every recorded day.
    <YYYY-MM-DD> Exact date.

Options:
    --json      Machine-readable output instead of the table.
    -h, --help  Print this help and exit.

Reads: state/cost_stats.json (written by the daemon on every LLM
call). No network, no state change. Safe to run repeatedly.
"""


def _render_human(agg: Dict[str, Any],
                   budget: Optional[float],
                   spent_today: float,
                   out: Callable[[str], None]) -> None:
    out("")
    out(f"  period: [bold]{agg['period']}[/]  "
        f"({agg['days_covered']} day(s) with data)")
    out(f"  total : [bold]${agg['total']:.4f}[/]")
    out("")

    if agg["by_step"]:
        out("  [dim]by step:[/]")
        # Sort by cost descending.
        rows = sorted(agg["by_step"].items(),
                       key=lambda kv: -kv[1]["cost"])
        for step, rec in rows:
            out(f"    {step:<18} {rec['calls']:>5} calls · "
                f"${rec['cost']:.4f}")
        out("")

    if agg["by_model"]:
        out("  [dim]by model:[/]")
        rows = sorted(agg["by_model"].items(),
                       key=lambda kv: -kv[1]["cost"])
        for model, rec in rows:
            short_model = model if len(model) < 40 else (model[:37] + "...")
            out(f"    {short_model:<42} {rec['calls']:>5} calls · "
                f"${rec['cost']:.4f}")
        out("")

    if budget is not None:
        remaining = max(0.0, round(budget - spent_today, 4))
        status = f"${budget:.2f}/day · ${remaining:.4f} remaining today"
        if spent_today >= budget:
            status += "  [red](cap reached — daemon pausing refines)[/]"
        out(f"  [dim]budget:[/] {status}")
    else:
        out("  [dim]budget:[/] no cap set (THROUGHLINE_MAX_DAILY_USD or "
            "daily_budget_usd)")


def _render_json(agg: Dict[str, Any],
                  budget: Optional[float],
                  spent_today: float) -> None:
    print(json.dumps({
        **agg,
        "budget_usd": budget,
        "spent_today_usd": spent_today,
    }, indent=2))


def main(argv: List[str],
          *,
          out: Optional[Callable[[str], None]] = None,
          stats_override: Optional[Dict[str, Any]] = None,
          now: Optional[datetime] = None) -> int:
    if out is None:
        try:
            from . import ui
            out = lambda s: ui.console.print(s)  # noqa: E731
        except Exception:
            out = print

    fmt = "human"
    period: Optional[str] = None
    for a in argv:
        if a in ("-h", "--help", "help"):
            print(USAGE)
            return 0
        if a == "--json":
            fmt = "json"
            continue
        if a in ("today", "week", "month", "all"):
            period = a
            continue
        if _parse_date(a):
            period = a
            continue
        print(f"Unknown argument: {a!r}\n", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2

    period = period or "today"
    stats = stats_override if stats_override is not None else _load_stats()

    # A specific date is handled as "all" + filter post-aggregation.
    if _parse_date(period):
        target_key = period
        period_label = period
        agg = {
            "period": period_label,
            "days_covered": 1 if target_key in (stats.get("by_date") or {}) else 0,
            "total": 0.0,
            "by_step": {},
            "by_model": {},
        }
        day = (stats.get("by_date") or {}).get(target_key) or {}
        for step_name, rec in day.items():
            if not isinstance(rec, dict):
                continue
            cost = float(rec.get("cost") or 0.0)
            agg["total"] += cost
            agg["by_step"][step_name] = {
                "calls": int(rec.get("calls") or 0),
                "cost": cost,
                "input_tokens": int(rec.get("input_tokens") or 0),
                "output_tokens": int(rec.get("output_tokens") or 0),
            }
            model = rec.get("model")
            if isinstance(model, str):
                mrow = agg["by_model"].setdefault(
                    model, {"calls": 0, "cost": 0.0})
                mrow["calls"] += int(rec.get("calls") or 0)
                mrow["cost"] += cost
        agg["total"] = round(agg["total"], 4)
    else:
        agg = aggregate(stats, period, now=now)

    budget = _resolve_budget()
    spent_today = _spent_today_usd()

    if fmt == "json":
        _render_json(agg, budget, spent_today)
    else:
        _render_human(agg, budget, spent_today, out)
    return 0
