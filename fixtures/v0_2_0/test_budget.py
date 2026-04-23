"""Tests for U3 — daemon daily budget cap enforcement.

Covers `daemon.budget`:

- `load_budget()`    config.toml precedence + env var override + no-file fallback
- `today_key()`      matches `_record_cost`'s date format
- `load_daily_total()` sums all step costs for today
- `budget_exceeded()`  cap semantics: None / 0.0 / positive
- `remaining_budget()` dollars-left math

Extracted into its own module so tests can exercise the arithmetic
without touching the refine daemon's import surface.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from daemon import budget


def _write_stats(path: Path, *,
                  today: str,
                  per_step_cost: dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"by_date": {today: {
        name: {"calls": 1, "input_tokens": 0, "output_tokens": 0, "cost": c}
        for name, c in per_step_cost.items()
    }}}
    path.write_text(json.dumps(data), encoding="utf-8")


class TestLoadBudget:
    def test_env_var_wins(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        (cfg_dir / "config.toml").write_text(
            'daily_budget_usd = 5.0\n', encoding="utf-8")
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        monkeypatch.setenv("THROUGHLINE_MAX_DAILY_USD", "12.5")
        assert budget.load_budget() == 12.5

    def test_config_fallback(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        (cfg_dir / "config.toml").write_text(
            'daily_budget_usd = 7.25\n', encoding="utf-8")
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        monkeypatch.delenv("THROUGHLINE_MAX_DAILY_USD", raising=False)
        assert budget.load_budget() == 7.25

    def test_no_file_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "empty"))
        monkeypatch.delenv("THROUGHLINE_MAX_DAILY_USD", raising=False)
        assert budget.load_budget() is None

    def test_malformed_config_no_crash(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        (cfg_dir / "config.toml").write_text(
            '[this is not valid toml\n', encoding="utf-8")
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        monkeypatch.delenv("THROUGHLINE_MAX_DAILY_USD", raising=False)
        # Must not raise; falls through to None.
        assert budget.load_budget() is None

    def test_env_empty_string_ignored(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        (cfg_dir / "config.toml").write_text(
            'daily_budget_usd = 3.0\n', encoding="utf-8")
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        monkeypatch.setenv("THROUGHLINE_MAX_DAILY_USD", "")
        assert budget.load_budget() == 3.0

    def test_zero_budget_is_valid(self, tmp_path, monkeypatch):
        """Explicit zero is a kill-switch, not 'no config'."""
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        (cfg_dir / "config.toml").write_text(
            'daily_budget_usd = 0.0\n', encoding="utf-8")
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        monkeypatch.delenv("THROUGHLINE_MAX_DAILY_USD", raising=False)
        assert budget.load_budget() == 0.0


class TestTodayKey:
    def test_format_matches_record_cost(self):
        # Must match daemon._record_cost's strftime format or cost
        # stats and budget lookups will miss each other.
        k = budget.today_key(datetime(2026, 4, 24, 15, 30, 0))
        assert k == "2026-04-24"


class TestLoadDailyTotal:
    def test_missing_file_zero(self, tmp_path):
        assert budget.load_daily_total(tmp_path / "no.json") == 0.0

    def test_missing_today_zero(self, tmp_path):
        p = tmp_path / "stats.json"
        _write_stats(p, today="2026-01-01", per_step_cost={"refine": 5.0})
        assert budget.load_daily_total(p, today="2026-04-24") == 0.0

    def test_sums_all_steps(self, tmp_path):
        p = tmp_path / "stats.json"
        _write_stats(p, today="2026-04-24", per_step_cost={
            "Refiner": 1.23,
            "Slicer": 0.45,
            "DomainRouter": 0.07,
        })
        assert budget.load_daily_total(p, today="2026-04-24") == 1.75

    def test_tolerates_malformed_entry(self, tmp_path):
        p = tmp_path / "stats.json"
        p.write_text(json.dumps({"by_date": {"2026-04-24": {
            "ok_step": {"cost": 1.0},
            "bad_step": {"cost": "not-a-number"},
            "also_bad": "not-a-dict",
        }}}), encoding="utf-8")
        assert budget.load_daily_total(p, today="2026-04-24") == 1.0

    def test_malformed_file_zero(self, tmp_path):
        p = tmp_path / "stats.json"
        p.write_text("{not json}", encoding="utf-8")
        assert budget.load_daily_total(p) == 0.0


class TestBudgetExceeded:
    def test_none_cap_never_exceeds(self, tmp_path):
        p = tmp_path / "stats.json"
        _write_stats(p, today="2026-04-24",
                     per_step_cost={"a": 1000.0})
        assert budget.budget_exceeded(None, p, today="2026-04-24") is False

    def test_zero_cap_exceeds_on_any_spend(self, tmp_path):
        p = tmp_path / "stats.json"
        _write_stats(p, today="2026-04-24",
                     per_step_cost={"a": 0.01})
        assert budget.budget_exceeded(0.0, p, today="2026-04-24") is True

    def test_zero_cap_with_zero_spend(self, tmp_path):
        """Zero cap + zero spend = NOT exceeded (fresh day edge)."""
        assert budget.budget_exceeded(0.0, tmp_path / "no.json",
                                       today="2026-04-24") is False

    def test_under_cap(self, tmp_path):
        p = tmp_path / "stats.json"
        _write_stats(p, today="2026-04-24",
                     per_step_cost={"a": 3.0, "b": 2.0})
        assert budget.budget_exceeded(10.0, p, today="2026-04-24") is False

    def test_at_cap(self, tmp_path):
        p = tmp_path / "stats.json"
        _write_stats(p, today="2026-04-24",
                     per_step_cost={"a": 10.0})
        # >= is the contract; at the cap counts as exceeded.
        assert budget.budget_exceeded(10.0, p, today="2026-04-24") is True

    def test_over_cap(self, tmp_path):
        p = tmp_path / "stats.json"
        _write_stats(p, today="2026-04-24",
                     per_step_cost={"a": 20.0})
        assert budget.budget_exceeded(10.0, p, today="2026-04-24") is True

    def test_day_rollover_resets(self, tmp_path):
        """Yesterday's $50 spend doesn't block today's refines."""
        p = tmp_path / "stats.json"
        _write_stats(p, today="2026-04-23",
                     per_step_cost={"a": 50.0})
        assert budget.budget_exceeded(10.0, p, today="2026-04-24") is False


class TestRemainingBudget:
    def test_none_cap_returns_none(self, tmp_path):
        assert budget.remaining_budget(None, tmp_path / "x.json") is None

    def test_under_cap(self, tmp_path):
        p = tmp_path / "stats.json"
        _write_stats(p, today="2026-04-24",
                     per_step_cost={"a": 3.0})
        assert budget.remaining_budget(10.0, p, today="2026-04-24") == 7.0

    def test_over_cap_clamped_to_zero(self, tmp_path):
        p = tmp_path / "stats.json"
        _write_stats(p, today="2026-04-24",
                     per_step_cost={"a": 50.0})
        assert budget.remaining_budget(10.0, p, today="2026-04-24") == 0.0
