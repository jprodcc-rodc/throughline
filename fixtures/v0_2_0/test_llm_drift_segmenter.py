"""Tests for mcp_server.llm_drift_segmenter."""
from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest


# ---------- env-var resolution ----------

class TestResolveEndpoint:
    def test_default(self, monkeypatch):
        for k in ("OPENROUTER_API_KEY", "OPENROUTER_URL",
                  "OPENAI_API_KEY", "OPENAI_BASE_URL"):
            monkeypatch.delenv(k, raising=False)
        from mcp_server.llm_drift_segmenter import resolve_endpoint_and_key, DEFAULT_URL

        url, key = resolve_endpoint_and_key()
        assert url == DEFAULT_URL
        assert key is None

    def test_segmenter_model_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_SEGMENTER_MODEL", "anthropic/claude-haiku")
        from mcp_server.llm_drift_segmenter import resolve_model

        assert resolve_model() == "anthropic/claude-haiku"


# ---------- _parse_segmentation ----------

class TestParseSegmentation:
    def test_clean(self):
        from mcp_server.llm_drift_segmenter import _parse_segmentation

        raw = json.dumps({
            "drift_kind": "healthy_evolution",
            "phases": [
                {
                    "phase_name": "Phase 1",
                    "stance": "Stance A",
                    "started_card_index": 0,
                    "ended_card_index": 1,
                    "transition_reason": "New evidence emerged.",
                },
                {
                    "phase_name": "Phase 2",
                    "stance": "Stance B",
                    "started_card_index": 2,
                    "ended_card_index": 3,
                    "transition_reason": "",
                },
            ],
        })
        out = _parse_segmentation(raw, n_cards=4)
        assert out["drift_kind"] == "healthy_evolution"
        assert len(out["phases"]) == 2

    def test_invalid_drift_kind_raises(self):
        from mcp_server.llm_drift_segmenter import _parse_segmentation, LLMSegmenterError

        raw = json.dumps({
            "drift_kind": "made_up",
            "phases": [{"started_card_index": 0, "ended_card_index": 0,
                        "phase_name": "x", "stance": "y", "transition_reason": ""}],
        })
        with pytest.raises(LLMSegmenterError):
            _parse_segmentation(raw, n_cards=1)

    def test_out_of_bounds_phase_skipped(self):
        from mcp_server.llm_drift_segmenter import _parse_segmentation

        raw = json.dumps({
            "drift_kind": "healthy_evolution",
            "phases": [
                {"started_card_index": 0, "ended_card_index": 1,
                 "phase_name": "valid", "stance": "x", "transition_reason": ""},
                {"started_card_index": 5, "ended_card_index": 7,  # OOB
                 "phase_name": "invalid", "stance": "x", "transition_reason": ""},
            ],
        })
        out = _parse_segmentation(raw, n_cards=2)
        # Only the valid phase survives
        assert len(out["phases"]) == 1
        assert out["phases"][0]["phase_name"] == "valid"

    def test_all_phases_invalid_raises(self):
        from mcp_server.llm_drift_segmenter import _parse_segmentation, LLMSegmenterError

        raw = json.dumps({
            "drift_kind": "healthy_evolution",
            "phases": [{"started_card_index": 5, "ended_card_index": 7,
                        "phase_name": "x", "stance": "y", "transition_reason": ""}],
        })
        with pytest.raises(LLMSegmenterError):
            _parse_segmentation(raw, n_cards=2)

    def test_strips_fences(self):
        from mcp_server.llm_drift_segmenter import _parse_segmentation

        raw = (
            "```json\n"
            + json.dumps({
                "drift_kind": "healthy_evolution",
                "phases": [{"started_card_index": 0, "ended_card_index": 0,
                            "phase_name": "x", "stance": "y", "transition_reason": ""}],
            })
            + "\n```"
        )
        out = _parse_segmentation(raw, n_cards=1)
        assert out["drift_kind"] == "healthy_evolution"


# ---------- segment_cluster happy path ----------

def _mock_response(content: str):
    body = {"choices": [{"message": {"content": content}}]}

    class _CtxMgr:
        def __enter__(self):
            return io.BytesIO(json.dumps(body).encode("utf-8"))
        def __exit__(self, *a):
            return False

    return _CtxMgr()


class TestSegmentCluster:
    def test_empty_cards_raises(self, monkeypatch):
        from mcp_server.llm_drift_segmenter import segment_cluster, LLMSegmenterError

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with pytest.raises(LLMSegmenterError):
            segment_cluster([])

    def test_single_card_returns_trivial_segmentation(self, monkeypatch):
        """1-card cluster gets 1-phase no-LLM segmentation."""
        from mcp_server.llm_drift_segmenter import segment_cluster

        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # No key set; would fail on LLM call. Single card path
        # short-circuits.
        out = segment_cluster([{
            "title": "T", "stance": "S", "reasoning": ["r"], "date": "2026-01"
        }])
        assert out["drift_kind"] == "unsegmented"
        assert len(out["phases"]) == 1
        assert out["phases"][0]["started_card_index"] == 0
        assert out["phases"][0]["ended_card_index"] == 0

    def test_segments_multi_card_cluster(self, monkeypatch):
        from mcp_server import llm_drift_segmenter

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        mock_content = json.dumps({
            "drift_kind": "healthy_evolution",
            "phases": [
                {
                    "phase_name": "Early",
                    "stance": "Stance A",
                    "started_card_index": 0,
                    "ended_card_index": 1,
                    "transition_reason": "PMF reached.",
                },
                {
                    "phase_name": "Late",
                    "stance": "Stance B",
                    "started_card_index": 2,
                    "ended_card_index": 2,
                    "transition_reason": "",
                },
            ],
        })

        cards = [
            {"title": "T1", "stance": "S1", "reasoning": ["r1"], "date": "2025"},
            {"title": "T2", "stance": "S1.5", "reasoning": ["r2"], "date": "2025-06"},
            {"title": "T3", "stance": "S2", "reasoning": ["r3"], "date": "2026"},
        ]

        with patch.object(
            llm_drift_segmenter.urllib.request, "urlopen",
            return_value=_mock_response(mock_content),
        ):
            out = llm_drift_segmenter.segment_cluster(cards, topic="my_topic")

        assert out["drift_kind"] == "healthy_evolution"
        assert len(out["phases"]) == 2

    def test_missing_key_raises(self, monkeypatch):
        from mcp_server.llm_drift_segmenter import segment_cluster, LLMSegmenterUnavailable

        for k in ("OPENROUTER_API_KEY", "OPENAI_API_KEY"):
            monkeypatch.delenv(k, raising=False)
        with pytest.raises(LLMSegmenterUnavailable):
            segment_cluster(
                [{"title": "T1", "stance": "S1", "reasoning": [], "date": "2025"},
                 {"title": "T2", "stance": "S2", "reasoning": [], "date": "2026"}]
            )

    def test_url_error_raises_unavailable(self, monkeypatch):
        from urllib.error import URLError
        from mcp_server import llm_drift_segmenter

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_drift_segmenter.urllib.request, "urlopen",
            side_effect=URLError("dns fail"),
        ):
            with pytest.raises(llm_drift_segmenter.LLMSegmenterUnavailable):
                llm_drift_segmenter.segment_cluster(
                    [{"title": "T1", "stance": "S1", "reasoning": [], "date": "2025"},
                     {"title": "T2", "stance": "S2", "reasoning": [], "date": "2026"}]
                )

    def test_includes_cards_in_prompt(self, monkeypatch):
        from mcp_server import llm_drift_segmenter

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        captured = {}
        def fake_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _mock_response(json.dumps({
                "drift_kind": "healthy_evolution",
                "phases": [{"started_card_index": 0, "ended_card_index": 1,
                            "phase_name": "x", "stance": "y", "transition_reason": ""}],
            }))

        cards = [
            {"title": "Specific Title One", "stance": "S1", "reasoning": ["r1"], "date": "2025"},
            {"title": "Specific Title Two", "stance": "S2", "reasoning": ["r2"], "date": "2026"},
        ]
        with patch.object(
            llm_drift_segmenter.urllib.request, "urlopen",
            side_effect=fake_urlopen,
        ):
            llm_drift_segmenter.segment_cluster(cards, topic="my_topic")

        user_msg = captured["body"]["messages"][1]["content"]
        assert "Specific Title One" in user_msg
        assert "Specific Title Two" in user_msg
        assert "my_topic" in user_msg
