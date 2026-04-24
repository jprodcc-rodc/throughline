"""Tests for `python -m throughline_cli cost`."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import cost


def _mk_stats(days: dict) -> dict:
    """Build a stats dict the same way daemon._record_cost does.
    `days` is {date_key: {step: {calls, cost, input_tokens, output_tokens,
    model?}}}."""
    return {"by_date": days}


class TestDatesForPeriod:
    def test_today(self):
        now = datetime(2026, 4, 25, 12, 0, 0)
        assert cost._dates_for_period("today", now=now) == ["2026-04-25"]

    def test_week_has_seven(self):
        now = datetime(2026, 4, 25)
        out = cost._dates_for_period("week", now=now)
        assert len(out) == 7
        assert "2026-04-25" in out
        assert "2026-04-19" in out  # 6 days back

    def test_month_has_thirty(self):
        now = datetime(2026, 4, 25)
        out = cost._dates_for_period("month", now=now)
        assert len(out) == 30

    def test_all_returns_none_sentinel(self):
        assert cost._dates_for_period("all") is None

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            cost._dates_for_period("fortnight")


class TestAggregate:
    def test_single_day_today(self):
        now = datetime(2026, 4, 25)
        stats = _mk_stats({
            "2026-04-25": {
                "Refiner": {
                    "calls": 10, "cost": 1.23,
                    "input_tokens": 1000, "output_tokens": 400,
                    "model": "anthropic/claude-sonnet-4.6",
                },
                "Slicer": {
                    "calls": 5, "cost": 0.47,
                    "input_tokens": 500, "output_tokens": 100,
                    "model": "anthropic/claude-sonnet-4.6",
                },
            },
        })
        agg = cost.aggregate(stats, "today", now=now)
        assert agg["days_covered"] == 1
        assert agg["total"] == pytest.approx(1.70, abs=1e-4)
        assert agg["by_step"]["Refiner"]["calls"] == 10
        assert agg["by_model"]["anthropic/claude-sonnet-4.6"]["calls"] == 15
        assert agg["by_model"]["anthropic/claude-sonnet-4.6"]["cost"] \
            == pytest.approx(1.70, abs=1e-4)

    def test_week_rolls_up_across_days(self):
        now = datetime(2026, 4, 25)
        stats = _mk_stats({
            "2026-04-25": {"Refiner": {"calls": 2, "cost": 0.20}},
            "2026-04-24": {"Refiner": {"calls": 3, "cost": 0.30}},
            "2026-04-23": {"Slicer":  {"calls": 1, "cost": 0.05}},
            "2026-04-10": {"Refiner": {"calls": 9, "cost": 0.90}},  # outside 7-day window
        })
        agg = cost.aggregate(stats, "week", now=now)
        # 4-10 should NOT be counted (>7 days back).
        assert agg["total"] == pytest.approx(0.55, abs=1e-4)
        assert agg["by_step"]["Refiner"]["calls"] == 5
        assert agg["by_step"]["Slicer"]["calls"] == 1

    def test_all_includes_every_recorded_day(self):
        stats = _mk_stats({
            "2025-01-01": {"Refiner": {"calls": 100, "cost": 10.0}},
            "2026-04-25": {"Refiner": {"calls": 1, "cost": 0.01}},
        })
        agg = cost.aggregate(stats, "all")
        assert agg["days_covered"] == 2
        assert agg["total"] == pytest.approx(10.01, abs=1e-4)

    def test_missing_cost_field_is_zero(self):
        stats = _mk_stats({
            "2026-04-25": {"Refiner": {"calls": 3}},  # no cost field
        })
        agg = cost.aggregate(stats, "today",
                              now=datetime(2026, 4, 25))
        assert agg["total"] == 0.0
        assert agg["by_step"]["Refiner"]["calls"] == 3

    def test_empty_stats(self):
        agg = cost.aggregate({"by_date": {}}, "today",
                              now=datetime(2026, 4, 25))
        assert agg["total"] == 0.0
        assert agg["by_step"] == {}
        assert agg["days_covered"] == 0


class TestMainCLI:
    def test_help(self, capsys):
        rc = cost.main(["--help"])
        assert rc == 0
        assert "cost" in capsys.readouterr().out.lower()

    def test_unknown_arg(self, capsys):
        rc = cost.main(["--zztop"])
        assert rc == 2

    def test_default_is_today(self, capsys):
        stats = _mk_stats({
            "2026-04-25": {"Refiner": {"calls": 1, "cost": 0.5,
                                         "model": "m"}},
        })
        captured: list[str] = []
        rc = cost.main([], stats_override=stats,
                        now=datetime(2026, 4, 25),
                        out=captured.append)
        assert rc == 0
        text = " ".join(captured)
        assert "today" in text
        assert "0.5000" in text or "$0.50" in text

    def test_json_output(self, capsys):
        stats = _mk_stats({
            "2026-04-25": {"Refiner": {"calls": 2, "cost": 0.4,
                                         "model": "m"}},
        })
        rc = cost.main(["week", "--json"], stats_override=stats,
                        now=datetime(2026, 4, 25))
        assert rc == 0
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["total"] == pytest.approx(0.4, abs=1e-4)
        assert "by_step" in parsed
        assert "by_model" in parsed

    def test_specific_date(self):
        stats = _mk_stats({
            "2026-04-20": {"Refiner": {"calls": 7, "cost": 1.17,
                                         "model": "m"}},
            "2026-04-25": {"Slicer": {"calls": 3, "cost": 0.15}},
        })
        captured: list[str] = []
        rc = cost.main(["2026-04-20"], stats_override=stats,
                        out=captured.append)
        assert rc == 0
        text = " ".join(captured)
        assert "2026-04-20" in text
        assert "1.1700" in text
        # Other day's spend NOT included.
        assert "0.1500" not in text

    def test_no_stats_file_zero(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "empty"))
        captured: list[str] = []
        rc = cost.main([], out=captured.append)
        assert rc == 0
        text = " ".join(captured)
        assert "0.0000" in text or "$0.00" in text

    def test_budget_status_printed_when_set(self, tmp_path, monkeypatch):
        """When a budget is configured, output includes the remaining
        line."""
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        (cfg_dir / "config.toml").write_text(
            "daily_budget_usd = 5.0\n", encoding="utf-8")
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        (tmp_path / "state").mkdir()
        (tmp_path / "state" / "cost_stats.json").write_text(
            json.dumps({"by_date": {
                datetime.now().strftime("%Y-%m-%d"): {
                    "Refiner": {"calls": 1, "cost": 2.5, "model": "m"},
                },
            }}),
            encoding="utf-8",
        )

        captured: list[str] = []
        rc = cost.main([], out=captured.append)
        assert rc == 0
        text = " ".join(captured)
        assert "budget" in text.lower()
        assert "$5" in text
        # Remaining: 5 - 2.5 = 2.5
        assert "2.5" in text


class TestLoadStatsTolerance:
    def test_malformed_json_returns_empty(self, tmp_path, monkeypatch):
        state = tmp_path / "state"
        state.mkdir()
        (state / "cost_stats.json").write_text("{not json",
                                                 encoding="utf-8")
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state))
        stats = cost._load_stats()
        assert stats == {"by_date": {}}
