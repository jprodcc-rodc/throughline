"""Tests for mcp_server.tools.get_position_drift (real impl).

Mirrors check_consistency tests structurally:
- missing state → error
- empty topic → error
- exact substring match on cluster name
- token-overlap fallback when name doesn't contain needle
- granularity = 'transitions' (default; back-filled only) vs
  'all_cards' (everything)
- 'ended' field set to next card's date / null on last
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
    return tmp_path


def _write_state(state_dir: Path, clusters: list[dict]) -> Path:
    payload = {
        "generated_at": "2026-04-28T12:00:00+00:00",
        "vault_root": "/test/vault",
        "dry_run": False,
        "clusters": clusters,
    }
    p = state_dir / "reflection_positions.json"
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


# ---------- error paths ----------

def test_no_state_returns_error(state_dir):
    from mcp_server.tools.get_position_drift import get_position_drift

    result = get_position_drift(topic="pricing")
    assert result["_status"] == "error"
    assert "has not run yet" in result["_message"]


def test_empty_topic_returns_error(state_dir):
    from mcp_server.tools.get_position_drift import get_position_drift

    _write_state(state_dir, [])
    result = get_position_drift(topic="")
    assert result["_status"] == "error"
    assert "empty" in result["_message"].lower()


# ---------- happy path ----------

class TestDriftHappy:
    def test_substring_match_on_cluster_name(self, state_dir):
        from mcp_server.tools.get_position_drift import get_position_drift

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "pricing_strategy",
            "size": 2,
            "cards": [
                {
                    "card_path": "a.md", "title": "Take 1",
                    "stance": "Stance A", "reasoning": ["r1"],
                    "open_questions": [], "date": "2026-01-01",
                    "is_open_thread": False, "is_backfilled": True,
                },
                {
                    "card_path": "b.md", "title": "Take 2",
                    "stance": "Stance B", "reasoning": ["r2"],
                    "open_questions": [], "date": "2026-02-01",
                    "is_open_thread": False, "is_backfilled": True,
                },
            ],
        }])

        result = get_position_drift(topic="pricing")
        assert result["_status"] == "ok"
        assert result["topic"] == "pricing_strategy"
        assert len(result["trajectory"]) == 2
        assert result["trajectory"][0]["stance"] == "Stance A"
        assert result["trajectory"][1]["stance"] == "Stance B"

    def test_ended_field_chains_through_dates(self, state_dir):
        from mcp_server.tools.get_position_drift import get_position_drift

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "framework",
            "size": 3,
            "cards": [
                {
                    "card_path": "a.md", "title": "Phase 1",
                    "stance": "S1", "reasoning": [],
                    "open_questions": [], "date": "2025-04-15",
                    "is_open_thread": False, "is_backfilled": True,
                },
                {
                    "card_path": "b.md", "title": "Phase 2",
                    "stance": "S2", "reasoning": [],
                    "open_questions": [], "date": "2025-10-20",
                    "is_open_thread": False, "is_backfilled": True,
                },
                {
                    "card_path": "c.md", "title": "Phase 3",
                    "stance": "S3", "reasoning": [],
                    "open_questions": [], "date": "2026-01-30",
                    "is_open_thread": False, "is_backfilled": True,
                },
            ],
        }])

        result = get_position_drift(topic="framework")
        traj = result["trajectory"]
        assert traj[0]["started"] == "2025-04-15"
        assert traj[0]["ended"] == "2025-10-20"
        assert traj[1]["started"] == "2025-10-20"
        assert traj[1]["ended"] == "2026-01-30"
        # Last entry has ended = None (current phase)
        assert traj[2]["started"] == "2026-01-30"
        assert traj[2]["ended"] is None

    def test_no_match_returns_ok_empty(self, state_dir):
        from mcp_server.tools.get_position_drift import get_position_drift

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "pricing_strategy",
            "size": 1,
            "cards": [{
                "card_path": "a.md", "title": "Pricing",
                "stance": "S", "reasoning": [], "open_questions": [],
                "date": "2026-01-01",
                "is_open_thread": False, "is_backfilled": True,
            }],
        }])

        result = get_position_drift(topic="completely_unrelated")
        assert result["_status"] == "ok"
        assert result["trajectory"] == []
        assert "No cards" in result["_message"]

    def test_transitions_filters_unbackfilled(self, state_dir):
        """Default granularity (transitions) skips cards without
        back-filled stance — they're not meaningful trajectory
        points."""
        from mcp_server.tools.get_position_drift import get_position_drift

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "x_topic",
            "size": 3,
            "cards": [
                {
                    "card_path": "a.md", "title": "x_topic before",
                    "stance": "S1", "reasoning": [],
                    "open_questions": [], "date": "2026-01-01",
                    "is_open_thread": False, "is_backfilled": True,
                },
                {
                    "card_path": "b.md", "title": "x_topic mid",
                    "stance": None,  # not back-filled
                    "reasoning": [], "open_questions": [],
                    "date": "2026-02-01",
                    "is_open_thread": False, "is_backfilled": False,
                },
                {
                    "card_path": "c.md", "title": "x_topic after",
                    "stance": "S2", "reasoning": [],
                    "open_questions": [], "date": "2026-03-01",
                    "is_open_thread": False, "is_backfilled": True,
                },
            ],
        }])

        result = get_position_drift(topic="x_topic")
        assert len(result["trajectory"]) == 2
        # Skip middle (no stance)
        assert result["trajectory"][0]["stance"] == "S1"
        assert result["trajectory"][1]["stance"] == "S2"

    def test_all_backfilled_missing_falls_through_to_message(self, state_dir):
        """Cluster has cards but none back-filled → degraded ok
        with hint."""
        from mcp_server.tools.get_position_drift import get_position_drift

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "no_data_topic",
            "size": 1,
            "cards": [{
                "card_path": "a.md", "title": "no_data_topic card",
                "stance": None, "reasoning": [],
                "open_questions": [], "date": "2026-01-01",
                "is_open_thread": False, "is_backfilled": False,
            }],
        }])

        result = get_position_drift(topic="no_data_topic")
        assert result["_status"] == "ok"
        assert result["trajectory"] == []
        assert "back-filled" in result["_message"]

    def test_drift_kind_is_unsegmented_in_v1(self, state_dir):
        """Stage 7 hasn't landed → drift_kind defaults to
        'unsegmented'. Tool surface keeps the field so future
        stage-7 enrichment doesn't break clients."""
        from mcp_server.tools.get_position_drift import get_position_drift

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "any",
            "size": 1,
            "cards": [{
                "card_path": "a.md", "title": "any card",
                "stance": "S", "reasoning": [], "open_questions": [],
                "date": "2026-01-01",
                "is_open_thread": False, "is_backfilled": True,
            }],
        }])

        result = get_position_drift(topic="any")
        assert result["drift_kind"] == "unsegmented"

    def test_invalid_granularity_falls_back_to_transitions(self, state_dir):
        from mcp_server.tools.get_position_drift import get_position_drift

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "topic_x",
            "size": 1,
            "cards": [{
                "card_path": "a.md", "title": "topic_x card",
                "stance": "S", "reasoning": [], "open_questions": [],
                "date": "2026-01-01",
                "is_open_thread": False, "is_backfilled": True,
            }],
        }])

        # Bogus granularity should not crash
        result = get_position_drift(topic="topic_x", granularity="banana")
        assert result["_status"] == "ok"
        assert len(result["trajectory"]) == 1
