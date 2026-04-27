"""Tests for mcp_server.tools.check_consistency (real impl).

The tool reads ``reflection_positions.json``. These tests build
synthetic state files and verify behavior:

- missing state → error with hint
- empty statement → error
- relevant cluster found → contradictions list with framing question
- no cluster matches → ok with empty list
- cluster found but no back-filled stances → degraded ok message
- soft_mode toggles framing question shape
- contradictions sort DESC by date
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


# ---------- missing / malformed state ----------

def test_no_state_file_returns_error(state_dir):
    from mcp_server.tools.check_consistency import check_consistency

    result = check_consistency(statement="we should use Postgres")
    assert result["_status"] == "error"
    assert "has not run yet" in result["_message"]


def test_empty_statement_returns_error(state_dir):
    from mcp_server.tools.check_consistency import check_consistency

    _write_state(state_dir, [])
    result = check_consistency(statement="")
    assert result["_status"] == "error"
    assert "empty" in result["_message"].lower()


def test_malformed_state_returns_error(state_dir):
    from mcp_server.tools.check_consistency import check_consistency

    (state_dir / "reflection_positions.json").write_text(
        "not json", encoding="utf-8"
    )
    result = check_consistency(statement="anything")
    assert result["_status"] == "error"


# ---------- happy path ----------

class TestCheckConsistencyHappy:
    def test_finds_matching_cluster_returns_contradictions(self, state_dir):
        from mcp_server.tools.check_consistency import check_consistency

        _write_state(state_dir, [
            {
                "cluster_id": "0",
                "topic_cluster": "pricing_strategy",
                "size": 2,
                "cards": [
                    {
                        "card_path": "30_Biz/early.md",
                        "title": "Pricing strategy first take",
                        "stance": "Against usage-based for early-stage SaaS",
                        "reasoning": [
                            "LTV math is unpredictable",
                            "Churn risk severe pre-PMF",
                        ],
                        "open_questions": [],
                        "date": "2026-01-15",
                        "is_open_thread": False,
                        "is_backfilled": True,
                    },
                ],
            },
            {
                "cluster_id": "1",
                "topic_cluster": "database_choice",
                "size": 1,
                "cards": [
                    {
                        "card_path": "10_Tech/db.md",
                        "title": "Database choice",
                        "stance": "Use Postgres over MySQL",
                        "reasoning": ["JSONB", "ecosystem"],
                        "open_questions": [],
                        "date": "2025-12-01",
                        "is_open_thread": False,
                        "is_backfilled": True,
                    },
                ],
            },
        ])

        result = check_consistency(
            statement="I'm going with usage-based pricing strategy",
        )
        assert result["_status"] == "ok"
        # Should match the pricing cluster, not the database one
        assert len(result["contradictions"]) == 1
        c = result["contradictions"][0]
        assert c["topic_cluster"] == "pricing_strategy"
        assert "usage-based" in c["prior_stance"]
        assert "LTV math is unpredictable" in c["prior_reasoning"]
        # Soft mode framing
        assert "still apply" in c["framing_question"]

    def test_soft_mode_default_framing(self, state_dir):
        from mcp_server.tools.check_consistency import check_consistency

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "freemium_conversion",
            "size": 1,
            "cards": [{
                "card_path": "x.md",
                "title": "freemium conversion strategy",
                "stance": "Against freemium for B2B SaaS",
                "reasoning": [],
                "open_questions": [],
                "date": "2026-01-01",
                "is_open_thread": False,
                "is_backfilled": True,
            }],
        }])

        result = check_consistency(
            statement="going with freemium conversion strategy",
        )
        assert result["_status"] == "ok"
        question = result["contradictions"][0]["framing_question"]
        # Soft mode: phrased as a question
        assert "?" in question
        assert "still apply" in question

    def test_hard_mode_framing(self, state_dir):
        from mcp_server.tools.check_consistency import check_consistency

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "freemium_conversion",
            "size": 1,
            "cards": [{
                "card_path": "x.md",
                "title": "freemium conversion strategy",
                "stance": "Against freemium for B2B SaaS",
                "reasoning": [],
                "open_questions": [],
                "date": "2026-01-01",
                "is_open_thread": False,
                "is_backfilled": True,
            }],
        }])

        result = check_consistency(
            statement="going with freemium conversion",
            soft_mode=False,
        )
        question = result["contradictions"][0]["framing_question"]
        assert "contradicts" in question.lower()

    def test_no_match_returns_ok_empty(self, state_dir):
        from mcp_server.tools.check_consistency import check_consistency

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "pricing_strategy",
            "size": 1,
            "cards": [{
                "card_path": "x.md",
                "title": "Pricing",
                "stance": "X",
                "reasoning": [],
                "open_questions": [],
                "date": "2026-01-01",
                "is_open_thread": False,
                "is_backfilled": True,
            }],
        }])

        result = check_consistency(
            statement="completely unrelated topic about Mars colonization",
        )
        assert result["_status"] == "ok"
        assert result["contradictions"] == []
        assert "No prior positions" in result["_message"]

    def test_cluster_match_but_no_backfilled_stances(self, state_dir):
        """Cluster has cards on the topic but none have been
        back-filled yet → tell the user honestly to run back-fill."""
        from mcp_server.tools.check_consistency import check_consistency

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "freemium_conversion",
            "size": 2,
            "cards": [
                {
                    "card_path": "a.md",
                    "title": "freemium conversion analysis",
                    "stance": None,  # not back-filled
                    "reasoning": [],
                    "open_questions": [],
                    "date": "2026-01-01",
                    "is_open_thread": False,
                    "is_backfilled": False,
                },
                {
                    "card_path": "b.md",
                    "title": "freemium conversion follow-up",
                    "stance": None,
                    "reasoning": [],
                    "open_questions": [],
                    "date": "2026-02-01",
                    "is_open_thread": False,
                    "is_backfilled": False,
                },
            ],
        }])

        result = check_consistency(
            statement="going with freemium conversion strategy",
        )
        assert result["_status"] == "ok"
        assert result["contradictions"] == []
        assert "back-filled stance" in result["_message"]
        assert "enable-llm-backfill" in result["_message"]

    def test_contradictions_sorted_desc_by_date(self, state_dir):
        from mcp_server.tools.check_consistency import check_consistency

        _write_state(state_dir, [{
            "cluster_id": "0",
            "topic_cluster": "pricing_strategy",
            "size": 3,
            "cards": [
                {
                    "card_path": "a.md",
                    "title": "pricing strategy take 1",
                    "stance": "stance A",
                    "reasoning": [],
                    "open_questions": [],
                    "date": "2026-01-01",
                    "is_open_thread": False,
                    "is_backfilled": True,
                },
                {
                    "card_path": "c.md",
                    "title": "pricing strategy take 3",
                    "stance": "stance C",
                    "reasoning": [],
                    "open_questions": [],
                    "date": "2026-03-01",
                    "is_open_thread": False,
                    "is_backfilled": True,
                },
                {
                    "card_path": "b.md",
                    "title": "pricing strategy take 2",
                    "stance": "stance B",
                    "reasoning": [],
                    "open_questions": [],
                    "date": "2026-02-01",
                    "is_open_thread": False,
                    "is_backfilled": True,
                },
            ],
        }])

        result = check_consistency(statement="pricing strategy decision")
        dates = [c["prior_date"] for c in result["contradictions"]]
        assert dates == ["2026-03-01", "2026-02-01", "2026-01-01"]
