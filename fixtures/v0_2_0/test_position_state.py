"""Tests for mcp_server.position_state shared helpers."""
from __future__ import annotations

import json

import pytest


# ---------- tokenize ----------

class TestTokenize:
    def test_english_unigrams(self):
        from mcp_server.position_state import tokenize

        out = tokenize("how does freemium conversion work")
        assert "freemium" in out
        assert "conversion" in out
        assert "work" in out
        assert "how" not in out  # stopword
        assert "does" not in out

    def test_chinese_bigrams(self):
        from mcp_server.position_state import tokenize

        out = tokenize("如何处理用药剂量")
        assert "处理" in out
        assert "用药" in out
        assert "剂量" in out

    def test_mixed_language(self):
        from mcp_server.position_state import tokenize

        out = tokenize("freemium 转化策略 vs 订阅")
        assert "freemium" in out
        assert "转化" in out
        assert "策略" in out

    def test_empty_returns_empty_set(self):
        from mcp_server.position_state import tokenize

        assert tokenize("") == set()
        assert tokenize("   ") == set()


# ---------- score_cluster_match ----------

class TestScoreClusterMatch:
    def test_perfect_match(self):
        from mcp_server.position_state import score_cluster_match, tokenize

        cluster = {
            "topic_cluster": "pricing_strategy",
            "cards": [{"title": "freemium conversion", "stance": "X"}],
        }
        score = score_cluster_match(
            tokenize("freemium conversion"),
            cluster,
        )
        assert score >= 0.5

    def test_no_overlap_zero(self):
        from mcp_server.position_state import score_cluster_match, tokenize

        cluster = {
            "topic_cluster": "database_choice",
            "cards": [{"title": "Postgres vs MySQL", "stance": "X"}],
        }
        score = score_cluster_match(
            tokenize("astrophysics black holes"),
            cluster,
        )
        assert score == 0.0

    def test_empty_needle_returns_zero(self):
        from mcp_server.position_state import score_cluster_match

        cluster = {"topic_cluster": "x", "cards": [{"title": "x"}]}
        assert score_cluster_match(set(), cluster) == 0.0

    def test_empty_cluster_returns_zero(self):
        from mcp_server.position_state import score_cluster_match, tokenize

        cluster = {"topic_cluster": "", "cards": []}
        assert score_cluster_match(tokenize("anything"), cluster) == 0.0


# ---------- find_best_cluster ----------

class TestFindBestCluster:
    def test_picks_highest_overlap(self):
        from mcp_server.position_state import find_best_cluster

        state = {
            "clusters": [
                {
                    "cluster_id": "0",
                    "topic_cluster": "database_choice",
                    "cards": [{"title": "postgres mysql comparison"}],
                },
                {
                    "cluster_id": "1",
                    "topic_cluster": "pricing_strategy",
                    "cards": [{"title": "freemium conversion playbook"}],
                },
            ]
        }
        out = find_best_cluster("freemium conversion strategy", state)
        assert out is not None
        assert out["cluster_id"] == "1"

    def test_min_score_threshold(self):
        from mcp_server.position_state import find_best_cluster

        state = {
            "clusters": [
                {
                    "cluster_id": "0",
                    "topic_cluster": "database_choice",
                    "cards": [{"title": "postgres vs mysql"}],
                },
            ]
        }
        # No real overlap; threshold filters out
        out = find_best_cluster("astrophysics black holes", state, min_score=0.3)
        assert out is None

    def test_empty_needle(self):
        from mcp_server.position_state import find_best_cluster

        state = {"clusters": [{"topic_cluster": "x", "cards": []}]}
        assert find_best_cluster("", state) is None


# ---------- find_cluster_by_topic ----------

class TestFindClusterByTopic:
    def test_substring_match_prefers_name(self):
        from mcp_server.position_state import find_cluster_by_topic

        state = {
            "clusters": [
                {
                    "cluster_id": "0",
                    "topic_cluster": "pricing_strategy",
                    "cards": [{"title": "irrelevant title", "stance": "x"}],
                },
                {
                    "cluster_id": "1",
                    "topic_cluster": "database_choice",
                    "cards": [{"title": "pricing pricing pricing", "stance": "x"}],
                },
            ]
        }
        # Substring on cluster_name should win even though card titles
        # in cluster 1 contain the needle more.
        out = find_cluster_by_topic("pricing", state)
        assert out["cluster_id"] == "0"

    def test_falls_back_to_token_overlap(self):
        from mcp_server.position_state import find_cluster_by_topic

        state = {
            "clusters": [
                {
                    "cluster_id": "0",
                    "topic_cluster": None,  # name missing
                    "cards": [{"title": "freemium conversion"}],
                },
            ]
        }
        out = find_cluster_by_topic("freemium conversion", state)
        assert out is not None
        assert out["cluster_id"] == "0"


# ---------- load_positions ----------

def test_load_returns_none_on_missing(tmp_path, monkeypatch):
    from mcp_server.position_state import load_positions

    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
    assert load_positions() is None


def test_load_returns_none_on_malformed(tmp_path, monkeypatch):
    from mcp_server.position_state import load_positions

    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
    (tmp_path / "reflection_positions.json").write_text(
        "not json", encoding="utf-8"
    )
    assert load_positions() is None


def test_load_returns_dict_on_valid(tmp_path, monkeypatch):
    from mcp_server.position_state import load_positions

    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
    (tmp_path / "reflection_positions.json").write_text(
        json.dumps({"clusters": []}), encoding="utf-8"
    )
    assert load_positions() == {"clusters": []}


def test_load_returns_none_if_root_not_dict(tmp_path, monkeypatch):
    from mcp_server.position_state import load_positions

    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
    (tmp_path / "reflection_positions.json").write_text(
        json.dumps([1, 2, 3]), encoding="utf-8"
    )
    assert load_positions() is None


def test_resolve_uses_env_var(tmp_path, monkeypatch):
    from mcp_server.position_state import resolve_positions_file

    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "custom"))
    p = resolve_positions_file()
    assert "custom" in str(p)
    assert p.name == "reflection_positions.json"
