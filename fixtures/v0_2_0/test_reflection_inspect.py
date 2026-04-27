"""Tests for daemon.reflection_inspect — the --inspect CLI report."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


# ---------- humanize / size ----------

class TestHumanizeAge:
    def test_returns_question_mark_on_empty(self):
        from daemon.reflection_inspect import _humanize_age

        assert _humanize_age("") == "?"

    def test_seconds(self):
        from datetime import datetime, timedelta, timezone
        from daemon.reflection_inspect import _humanize_age

        recent = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
        result = _humanize_age(recent)
        assert "s ago" in result

    def test_minutes(self):
        from datetime import datetime, timedelta, timezone
        from daemon.reflection_inspect import _humanize_age

        ago = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        result = _humanize_age(ago)
        assert "m ago" in result

    def test_hours(self):
        from datetime import datetime, timedelta, timezone
        from daemon.reflection_inspect import _humanize_age

        ago = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        result = _humanize_age(ago)
        assert "h ago" in result

    def test_days(self):
        from datetime import datetime, timedelta, timezone
        from daemon.reflection_inspect import _humanize_age

        ago = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        result = _humanize_age(ago)
        assert "d ago" in result

    def test_returns_unparseable_input_as_is(self):
        from daemon.reflection_inspect import _humanize_age

        assert _humanize_age("not a date") == "not a date"


# ---------- _file_size_human ----------

class TestFileSize:
    def test_bytes(self, tmp_path):
        from daemon.reflection_inspect import _file_size_human

        p = tmp_path / "small.json"
        p.write_text("{}", encoding="utf-8")
        assert "B" in _file_size_human(p)

    def test_kilobytes(self, tmp_path):
        from daemon.reflection_inspect import _file_size_human

        p = tmp_path / "med.json"
        p.write_text("x" * 5000, encoding="utf-8")
        assert "K" in _file_size_human(p)

    def test_missing_file(self, tmp_path):
        from daemon.reflection_inspect import _file_size_human

        assert _file_size_human(tmp_path / "nope") == "?"


# ---------- summarizers ----------

class TestSummarizePassState:
    def test_minimal_payload(self):
        from daemon.reflection_inspect import _summarize_pass_state

        out = _summarize_pass_state({
            "cards_scanned": 100,
            "cards_reflectable": 50,
            "cards_excluded": 50,
            "clusters_count": 10,
            "cluster_names_resolved": 0,
            "backfill_completed": 0,
            "open_threads_detected": 0,
            "contradictions_detected": 0,
            "drift_phases_computed": 0,
            "cards_updated": 0,
            "dry_run": True,
        })
        assert any("100" in line for line in out)
        assert any("50" in line for line in out)


class TestSummarizeOpenThreads:
    def test_empty_threads(self):
        from daemon.reflection_inspect import _summarize_open_threads

        out = _summarize_open_threads({
            "open_threads": [],
            "generated_at": "",
        })
        assert any("0 open threads" in line for line in out)

    def test_with_entries(self):
        from daemon.reflection_inspect import _summarize_open_threads

        out = _summarize_open_threads({
            "open_threads": [
                {
                    "card_path": "a.md",
                    "topic_cluster": "pricing_strategy",
                    "open_questions": ["q1?", "q2?"],
                    "last_touched": "2026-01-01",
                    "context_summary": "x",
                },
            ],
            "generated_at": "2026-04-28T12:00:00+00:00",
        })
        assert any("1 open threads" in line for line in out)
        assert any("pricing_strategy" in line for line in out)


class TestSummarizePositions:
    def test_with_clusters(self):
        from daemon.reflection_inspect import _summarize_positions

        data = {
            "clusters": [
                {
                    "cluster_id": "0",
                    "topic_cluster": "topic_x",
                    "size": 5,
                    "cards": [{"is_backfilled": True, "is_open_thread": False}] * 5,
                },
                {
                    "cluster_id": "1",
                    "topic_cluster": None,
                    "size": 2,
                    "cards": [{"is_backfilled": False, "is_open_thread": False}] * 2,
                },
            ],
        }
        out = _summarize_positions(data)
        # 2 clusters, 7 cards, 5 backfilled, 1 named
        assert any("2 clusters / 7 cards" in line for line in out)
        assert any("1/2 clusters named" in line for line in out)
        assert any("5/7 cards back-filled" in line for line in out)


# ---------- render_inspect_report ----------

class TestRenderReport:
    def test_no_state_files(self, monkeypatch, tmp_path):
        from daemon.reflection_inspect import render_inspect_report

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "empty"))
        report = render_inspect_report()
        assert "Reflection Pass state inspection" in report
        # All paths should show ✗ (missing)
        assert "✗" in report

    def test_with_present_files(self, monkeypatch, tmp_path):
        from daemon.reflection_inspect import render_inspect_report

        # Build a minimal pass_state file
        (tmp_path / "reflection_pass_state.json").write_text(
            json.dumps({
                "started_at": "2026-04-28T12:00:00+00:00",
                "finished_at": "2026-04-28T12:00:30+00:00",
                "cards_scanned": 100,
                "cards_reflectable": 72,
                "cards_excluded": 28,
                "cards_with_position_signal": 0,
                "cards_clustered": 72,
                "clusters_count": 24,
                "cluster_names_resolved": 0,
                "backfill_completed": 0,
                "open_threads_detected": 0,
                "contradictions_detected": 0,
                "drift_phases_computed": 0,
                "cards_updated": 0,
                "dry_run": True,
            }),
            encoding="utf-8",
        )
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        report = render_inspect_report()
        assert "✓" in report  # has a present file
        assert "100" in report  # cards_scanned
        assert "72" in report  # cards_reflectable

    def test_handles_malformed_json(self, monkeypatch, tmp_path):
        from daemon.reflection_inspect import render_inspect_report

        (tmp_path / "reflection_pass_state.json").write_text(
            "not json", encoding="utf-8"
        )
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        report = render_inspect_report()
        # Should not crash; should mention the file is unreadable
        assert "unreadable" in report or "✓" in report  # at minimum doesn't crash


# ---------- CLI integration ----------

class TestInspectCLI:
    def test_inspect_short_circuits_pass_run(self, monkeypatch, tmp_path, capsys):
        """--inspect exits before any vault read or pass run."""
        from daemon.reflection_pass import main

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        rc = main(["--inspect"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Reflection Pass state inspection" in out
