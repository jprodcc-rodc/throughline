"""Tests for mcp_server.llm_judge."""
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
        from mcp_server.llm_judge import resolve_endpoint_and_key, DEFAULT_URL

        url, key = resolve_endpoint_and_key()
        assert url == DEFAULT_URL
        assert key is None

    def test_openrouter_wins(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
        monkeypatch.setenv("OPENAI_API_KEY", "oai-key")
        from mcp_server.llm_judge import resolve_endpoint_and_key

        _, key = resolve_endpoint_and_key()
        assert key == "or-key"

    def test_judge_model_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_JUDGE_MODEL", "anthropic/claude-haiku")
        monkeypatch.setenv("THROUGHLINE_NAMER_MODEL", "google/gemini")
        from mcp_server.llm_judge import resolve_model

        assert resolve_model() == "anthropic/claude-haiku"

    def test_namer_model_used_as_fallback(self, monkeypatch):
        monkeypatch.delenv("THROUGHLINE_JUDGE_MODEL", raising=False)
        monkeypatch.setenv("THROUGHLINE_NAMER_MODEL", "google/gemini")
        from mcp_server.llm_judge import resolve_model

        assert resolve_model() == "google/gemini"


# ---------- _parse_judgment ----------

class TestParseJudgment:
    def test_clean(self):
        from mcp_server.llm_judge import _parse_judgment

        raw = (
            '{"is_contradiction": true, "kind": "direct_reversal",'
            ' "reasoning_diff": "Earlier said X; later says not-X."}'
        )
        out = _parse_judgment(raw)
        assert out["is_contradiction"] is True
        assert out["kind"] == "direct_reversal"
        assert "X" in out["reasoning_diff"]

    def test_strips_fences(self):
        from mcp_server.llm_judge import _parse_judgment

        raw = (
            "```json\n"
            '{"is_contradiction": false, "kind": "evolution", "reasoning_diff": "x"}\n'
            "```"
        )
        out = _parse_judgment(raw)
        assert out["is_contradiction"] is False

    def test_recovers_from_extra_prose(self):
        from mcp_server.llm_judge import _parse_judgment

        raw = (
            'Here is my judgment: {"is_contradiction": false, '
            '"kind": "scope_narrowing", "reasoning_diff": "Different scope"}'
        )
        out = _parse_judgment(raw)
        assert out["kind"] == "scope_narrowing"

    @pytest.mark.parametrize(
        "raw",
        [
            "not json",
            "{}",  # missing fields
            '{"is_contradiction": "true", "kind": "x"}',  # wrong type
            '{"is_contradiction": true, "kind": "invalid_kind"}',  # bad kind
            '{"is_contradiction": true}',  # missing kind
        ],
    )
    def test_malformed_raises(self, raw):
        from mcp_server.llm_judge import _parse_judgment, LLMJudgeError

        with pytest.raises(LLMJudgeError):
            _parse_judgment(raw)

    def test_missing_reasoning_diff_defaults_to_empty(self):
        from mcp_server.llm_judge import _parse_judgment

        raw = '{"is_contradiction": false, "kind": "agreement"}'
        out = _parse_judgment(raw)
        assert out["reasoning_diff"] == ""


# ---------- judge_pair happy path ----------

def _mock_response(content: str):
    body = {"choices": [{"message": {"content": content}}]}

    class _CtxMgr:
        def __enter__(self):
            return io.BytesIO(json.dumps(body).encode("utf-8"))
        def __exit__(self, *a):
            return False

    return _CtxMgr()


class TestJudgePairHappy:
    def test_judges_contradiction(self, monkeypatch):
        from mcp_server import llm_judge

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        mock_content = json.dumps({
            "is_contradiction": True,
            "kind": "direct_reversal",
            "reasoning_diff": "Earlier: against X. Later: for X. No new conditions.",
        })

        with patch.object(
            llm_judge.urllib.request, "urlopen",
            return_value=_mock_response(mock_content),
        ):
            out = llm_judge.judge_pair(
                {"stance": "against usage-based", "reasoning": ["LTV unclear"], "date": "2026-01"},
                {"stance": "for usage-based", "reasoning": [], "date": "2026-03"},
                topic="pricing_strategy",
            )

        assert out["is_contradiction"] is True
        assert out["kind"] == "direct_reversal"

    def test_evolution_not_contradiction(self, monkeypatch):
        from mcp_server import llm_judge

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        with patch.object(
            llm_judge.urllib.request, "urlopen",
            return_value=_mock_response(json.dumps({
                "is_contradiction": False,
                "kind": "evolution",
                "reasoning_diff": "Later builds on earlier with new data",
            })),
        ):
            out = llm_judge.judge_pair(
                {"stance": "use SQL", "reasoning": [], "date": "2025"},
                {"stance": "use SQL with read replicas", "reasoning": [], "date": "2026"},
                topic="database",
            )

        assert out["is_contradiction"] is False
        assert out["kind"] == "evolution"

    def test_includes_topic_in_prompt(self, monkeypatch):
        from mcp_server import llm_judge

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        captured = {}
        def fake_urlopen(req, timeout):
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _mock_response(json.dumps({
                "is_contradiction": False,
                "kind": "agreement",
                "reasoning_diff": "x",
            }))

        with patch.object(
            llm_judge.urllib.request, "urlopen", side_effect=fake_urlopen
        ):
            llm_judge.judge_pair(
                {"stance": "S1", "reasoning": ["r1"], "date": "2026-01"},
                {"stance": "S2", "reasoning": ["r2"], "date": "2026-03"},
                topic="my_specific_topic",
            )

        user_msg = captured["body"]["messages"][1]["content"]
        assert "my_specific_topic" in user_msg
        assert "S1" in user_msg
        assert "S2" in user_msg
        assert "r1" in user_msg
        assert "r2" in user_msg


# ---------- judge_pair errors ----------

class TestJudgePairErrors:
    def test_empty_stance(self, monkeypatch):
        from mcp_server.llm_judge import judge_pair, LLMJudgeError

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with pytest.raises(LLMJudgeError):
            judge_pair({"stance": ""}, {"stance": "x"})

    def test_missing_key(self, monkeypatch):
        from mcp_server.llm_judge import judge_pair, LLMJudgeUnavailable

        for k in ("OPENROUTER_API_KEY", "OPENAI_API_KEY"):
            monkeypatch.delenv(k, raising=False)
        with pytest.raises(LLMJudgeUnavailable):
            judge_pair({"stance": "X"}, {"stance": "Y"})

    def test_url_error(self, monkeypatch):
        from urllib.error import URLError
        from mcp_server import llm_judge

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_judge.urllib.request, "urlopen",
            side_effect=URLError("dns fail"),
        ):
            with pytest.raises(llm_judge.LLMJudgeUnavailable):
                llm_judge.judge_pair({"stance": "X"}, {"stance": "Y"})

    def test_invalid_kind_in_response(self, monkeypatch):
        from mcp_server import llm_judge

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_judge.urllib.request, "urlopen",
            return_value=_mock_response(json.dumps({
                "is_contradiction": True,
                "kind": "made_up_kind",
                "reasoning_diff": "x",
            })),
        ):
            with pytest.raises(llm_judge.LLMJudgeError):
                llm_judge.judge_pair({"stance": "X"}, {"stance": "Y"})
