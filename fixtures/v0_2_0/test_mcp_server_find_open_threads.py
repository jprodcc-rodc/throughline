"""Tests for mcp_server.tools.find_open_threads (real impl).

The tool reads ``reflection_open_threads.json`` written by stage 5
of the Reflection Pass. These tests build synthetic state files
and verify the tool's surface contract:

- missing state file -> _status: error with hint
- malformed state file -> _status: error
- valid file, no topic filter -> all threads, sorted by last_touched DESC
- valid file, topic filter -> case-insensitive substring match
- limit clamps results
- empty topic match returns clean empty + ok message
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    """Point THROUGHLINE_STATE_DIR at a tmp dir + return the path
    where the state file lands."""
    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
    return tmp_path


def _write_state(state_dir: Path, entries: list[dict]) -> Path:
    """Build the open_threads state file with given entries."""
    payload = {
        "generated_at": "2026-04-28T12:00:00+00:00",
        "vault_root": "/test/vault",
        "dry_run": False,
        "open_threads": entries,
    }
    p = state_dir / "reflection_open_threads.json"
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p


# ---------- Missing / malformed state ----------

class TestMissingState:
    def test_no_state_file_returns_error(self, state_dir):
        from mcp_server.tools.find_open_threads import find_open_threads

        result = find_open_threads()
        assert result["_status"] == "error"
        assert "has not run yet" in result["_message"]
        assert result["open_threads"] == []
        assert result["total_open_threads"] == 0

    def test_malformed_json_returns_error(self, state_dir):
        from mcp_server.tools.find_open_threads import find_open_threads

        (state_dir / "reflection_open_threads.json").write_text(
            "not json at all", encoding="utf-8"
        )
        result = find_open_threads()
        assert result["_status"] == "error"
        assert "has not run yet" in result["_message"]

    def test_state_with_non_list_threads(self, state_dir):
        from mcp_server.tools.find_open_threads import find_open_threads

        (state_dir / "reflection_open_threads.json").write_text(
            json.dumps({"open_threads": "not a list"}),
            encoding="utf-8",
        )
        result = find_open_threads()
        assert result["_status"] == "error"
        assert "malformed" in result["_message"].lower()


# ---------- Happy path ----------

class TestHappyPath:
    def test_returns_all_threads_when_no_filter(self, state_dir):
        from mcp_server.tools.find_open_threads import find_open_threads

        _write_state(state_dir, [
            {
                "card_path": "10_Tech/a.md",
                "topic_cluster": "pricing_strategy",
                "open_questions": ["how to handle freemium?"],
                "last_touched": "2026-01-15",
                "context_summary": "Discussed LTV math",
            },
            {
                "card_path": "20_Health/b.md",
                "topic_cluster": "b1_thiamine_therapy",
                "open_questions": ["dose escalation schedule?"],
                "last_touched": "2026-02-20",
                "context_summary": "B1 protocol",
            },
        ])

        result = find_open_threads()
        assert result["_status"] == "ok"
        assert result["total_open_threads"] == 2
        # Sort DESC by last_touched -> b1 first
        assert result["open_threads"][0]["topic_cluster"] == "b1_thiamine_therapy"
        assert result["open_threads"][1]["topic_cluster"] == "pricing_strategy"

    def test_topic_filter_substring_match(self, state_dir):
        from mcp_server.tools.find_open_threads import find_open_threads

        _write_state(state_dir, [
            {
                "card_path": "a.md", "topic_cluster": "pricing_strategy",
                "open_questions": ["q1?"], "last_touched": "2026-01-01",
                "context_summary": "",
            },
            {
                "card_path": "b.md", "topic_cluster": "b1_thiamine_therapy",
                "open_questions": ["q2?"], "last_touched": "2026-02-01",
                "context_summary": "",
            },
            {
                "card_path": "c.md", "topic_cluster": "b12_supplementation",
                "open_questions": ["q3?"], "last_touched": "2026-03-01",
                "context_summary": "",
            },
        ])

        result = find_open_threads(topic="b1")
        assert result["_status"] == "ok"
        # Substring match: "b1" is in "b1_thiamine_therapy" but NOT
        # in "b12_supplementation" (which has "b12" not "b1")
        # WAIT — "b1" IS a substring of "b12". So both should match.
        # That's the documented behavior: substring not word-match.
        paths = [e["card_path"] for e in result["open_threads"]]
        assert "b.md" in paths
        assert "c.md" in paths
        assert "a.md" not in paths

    def test_topic_filter_case_insensitive(self, state_dir):
        from mcp_server.tools.find_open_threads import find_open_threads

        _write_state(state_dir, [
            {
                "card_path": "a.md", "topic_cluster": "Pricing_Strategy",
                "open_questions": ["q?"], "last_touched": "2026-01-01",
                "context_summary": "",
            },
        ])

        result = find_open_threads(topic="PRICING")
        assert result["_status"] == "ok"
        assert len(result["open_threads"]) == 1

    def test_topic_no_match_returns_ok_with_message(self, state_dir):
        from mcp_server.tools.find_open_threads import find_open_threads

        _write_state(state_dir, [
            {
                "card_path": "a.md", "topic_cluster": "pricing_strategy",
                "open_questions": ["q?"], "last_touched": "2026-01-01",
                "context_summary": "",
            },
        ])

        result = find_open_threads(topic="nonexistent")
        assert result["_status"] == "ok"
        assert result["open_threads"] == []
        # total_open_threads still 0 in the message-result
        # (consistent with shape contract)
        assert "_message" in result
        assert "match topic" in result["_message"]

    def test_limit_clamps_results(self, state_dir):
        from mcp_server.tools.find_open_threads import find_open_threads

        entries = [
            {
                "card_path": f"{i}.md",
                "topic_cluster": "topic",
                "open_questions": [f"q{i}"],
                "last_touched": f"2026-01-{i:02d}",
                "context_summary": "",
            }
            for i in range(1, 11)  # 10 threads
        ]
        _write_state(state_dir, entries)

        result = find_open_threads(limit=3)
        assert result["_status"] == "ok"
        # total is the FULL count regardless of limit
        assert result["total_open_threads"] == 10
        # but returned list is clamped to limit
        assert len(result["open_threads"]) == 3
        # And these are the most-recent 3 (DESC by last_touched)
        last_touched = [e["last_touched"] for e in result["open_threads"]]
        assert last_touched == ["2026-01-10", "2026-01-09", "2026-01-08"]

    def test_empty_state_returns_ok(self, state_dir):
        """State file exists but has empty open_threads list."""
        from mcp_server.tools.find_open_threads import find_open_threads

        _write_state(state_dir, [])
        result = find_open_threads()
        assert result["_status"] == "ok"
        assert result["total_open_threads"] == 0
        assert result["open_threads"] == []


# ---------- Internal helpers ----------

def test_resolve_state_file_uses_env_var(monkeypatch, tmp_path):
    from mcp_server.tools.find_open_threads import _resolve_state_file

    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "custom"))
    p = _resolve_state_file()
    assert "custom" in str(p)
    assert p.name == "reflection_open_threads.json"


def test_filter_by_topic_empty_needle_returns_all():
    from mcp_server.tools.find_open_threads import _filter_by_topic

    entries = [
        {"topic_cluster": "a"},
        {"topic_cluster": "b"},
    ]
    assert _filter_by_topic(entries, "") == entries
    assert _filter_by_topic(entries, "   ") == entries
