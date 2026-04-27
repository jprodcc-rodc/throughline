"""Tests for mcp_server.llm_extractor.

Mirrors test_llm_namer.py structure: env-var resolution, response
parsing edge cases, happy path, error paths. All HTTP calls mocked.
"""
from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest


# ---------- env-var resolution ----------

class TestResolveEndpoint:
    def test_default_when_unset(self, monkeypatch):
        for k in ("OPENROUTER_API_KEY", "OPENROUTER_URL",
                  "OPENAI_API_KEY", "OPENAI_BASE_URL"):
            monkeypatch.delenv(k, raising=False)
        from mcp_server.llm_extractor import resolve_endpoint_and_key, DEFAULT_URL

        url, key = resolve_endpoint_and_key()
        assert url == DEFAULT_URL
        assert key is None

    def test_openrouter_key_wins_over_openai(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
        monkeypatch.setenv("OPENAI_API_KEY", "oai-key")
        from mcp_server.llm_extractor import resolve_endpoint_and_key

        _, key = resolve_endpoint_and_key()
        assert key == "or-key"

    def test_openai_fallback_used_when_openrouter_unset(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "oai-key")
        from mcp_server.llm_extractor import resolve_endpoint_and_key

        _, key = resolve_endpoint_and_key()
        assert key == "oai-key"

    def test_openai_base_url_appended(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_URL", raising=False)
        monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.test/v1")
        from mcp_server.llm_extractor import resolve_endpoint_and_key

        url, _ = resolve_endpoint_and_key()
        assert url == "https://api.example.test/v1/chat/completions"

    def test_resolve_model_default(self, monkeypatch):
        for k in ("THROUGHLINE_EXTRACTOR_MODEL", "THROUGHLINE_NAMER_MODEL"):
            monkeypatch.delenv(k, raising=False)
        from mcp_server.llm_extractor import resolve_model, DEFAULT_MODEL

        assert resolve_model() == DEFAULT_MODEL

    def test_extractor_model_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_EXTRACTOR_MODEL", "anthropic/claude-haiku")
        monkeypatch.setenv("THROUGHLINE_NAMER_MODEL", "google/gemini")
        from mcp_server.llm_extractor import resolve_model

        assert resolve_model() == "anthropic/claude-haiku"

    def test_namer_model_used_as_fallback(self, monkeypatch):
        monkeypatch.delenv("THROUGHLINE_EXTRACTOR_MODEL", raising=False)
        monkeypatch.setenv("THROUGHLINE_NAMER_MODEL", "google/gemini")
        from mcp_server.llm_extractor import resolve_model

        assert resolve_model() == "google/gemini"


# ---------- _parse_response ----------

class TestParseResponse:
    def test_clean_json(self):
        from mcp_server.llm_extractor import _parse_response

        raw = '{"claim_summary": "X", "open_questions": ["Q1?"]}'
        out = _parse_response(raw)
        assert out["claim_summary"] == "X"
        assert out["open_questions"] == ["Q1?"]

    def test_strips_markdown_fences(self):
        from mcp_server.llm_extractor import _parse_response

        raw = '```json\n{"claim_summary": "X", "open_questions": []}\n```'
        out = _parse_response(raw)
        assert out["claim_summary"] == "X"
        assert out["open_questions"] == []

    def test_strips_unlabeled_fence(self):
        from mcp_server.llm_extractor import _parse_response

        raw = '```\n{"claim_summary": "X", "open_questions": []}\n```'
        out = _parse_response(raw)
        assert out["claim_summary"] == "X"

    def test_recovers_from_extra_prose(self):
        """Some models prepend 'Here is the JSON:' despite the system
        prompt. Trim to first { and last }."""
        from mcp_server.llm_extractor import _parse_response

        raw = ('Here is the JSON: {"claim_summary": "X", '
               '"open_questions": ["Q?"]} done.')
        out = _parse_response(raw)
        assert out["claim_summary"] == "X"

    def test_strips_empty_questions(self):
        """Empty / whitespace-only entries get filtered."""
        from mcp_server.llm_extractor import _parse_response

        raw = '{"claim_summary": "X", "open_questions": ["Q?", "", "  ", "Q2?"]}'
        out = _parse_response(raw)
        assert out["open_questions"] == ["Q?", "Q2?"]

    def test_strips_question_whitespace(self):
        from mcp_server.llm_extractor import _parse_response

        raw = '{"claim_summary": "X", "open_questions": ["  Q1?  "]}'
        out = _parse_response(raw)
        assert out["open_questions"] == ["Q1?"]

    @pytest.mark.parametrize(
        "raw",
        [
            "not json at all",
            "{}",  # missing claim_summary
            '{"claim_summary": ""}',  # empty
            '{"claim_summary": "X", "open_questions": "not a list"}',
            "[1, 2, 3]",  # not a dict
        ],
    )
    def test_malformed_raises(self, raw):
        from mcp_server.llm_extractor import _parse_response, LLMExtractorError

        with pytest.raises(LLMExtractorError):
            _parse_response(raw)

    def test_missing_open_questions_treated_as_empty(self):
        """Lenient: if model omits open_questions entirely, treat as
        []. Better than rejecting an otherwise-good extraction."""
        from mcp_server.llm_extractor import _parse_response

        out = _parse_response('{"claim_summary": "X"}')
        assert out["claim_summary"] == "X"
        assert out["open_questions"] == []

    def test_skips_non_string_questions(self):
        """Defensive: model emitting nulls / numbers in the list
        shouldn't crash; just drop them."""
        from mcp_server.llm_extractor import _parse_response

        raw = '{"claim_summary": "X", "open_questions": ["Q?", null, 42, "Q2?"]}'
        out = _parse_response(raw)
        assert out["open_questions"] == ["Q?", "Q2?"]


# ---------- happy path ----------

def _mock_response(content: str):
    body = {
        "choices": [{"message": {"role": "assistant", "content": content}}],
    }

    class _CtxMgr:
        def __enter__(self):
            return io.BytesIO(json.dumps(body).encode("utf-8"))
        def __exit__(self, *a):
            return False

    return _CtxMgr()


class TestExtractCardEssence:
    def test_happy_path(self, monkeypatch):
        from mcp_server import llm_extractor

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        mock_content = json.dumps({
            "claim_summary": "Use B1 daily for nerve repair",
            "open_questions": ["What's the right dose escalation?"],
        })

        with patch.object(
            llm_extractor.urllib.request,
            "urlopen",
            return_value=_mock_response(mock_content),
        ):
            out = llm_extractor.extract_card_essence(
                "B1 thiamine therapy",
                "Long body of card content...",
            )

        assert out["claim_summary"] == "Use B1 daily for nerve repair"
        assert out["open_questions"] == ["What's the right dose escalation?"]

    def test_includes_title_in_user_prompt(self, monkeypatch):
        from mcp_server import llm_extractor

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        captured = {}
        def fake_urlopen(req, timeout):
            captured["body"] = req.data
            return _mock_response(json.dumps({
                "claim_summary": "X", "open_questions": []
            }))

        with patch.object(
            llm_extractor.urllib.request, "urlopen",
            side_effect=fake_urlopen,
        ):
            llm_extractor.extract_card_essence(
                "Specific Card Title",
                "Body content here.",
            )

        body = json.loads(captured["body"].decode("utf-8"))
        user_msg = body["messages"][1]["content"]
        assert "Specific Card Title" in user_msg
        assert "Body content here" in user_msg

    def test_body_truncation(self, monkeypatch):
        from mcp_server import llm_extractor

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        captured = {}
        def fake_urlopen(req, timeout):
            captured["body"] = req.data
            return _mock_response(json.dumps({
                "claim_summary": "X", "open_questions": []
            }))

        long_body = "x" * 10000  # 10K chars
        with patch.object(
            llm_extractor.urllib.request, "urlopen",
            side_effect=fake_urlopen,
        ):
            llm_extractor.extract_card_essence(
                "T", long_body, body_chars=2000,
            )

        body = json.loads(captured["body"].decode("utf-8"))
        user_msg = body["messages"][1]["content"]
        # Body excerpt should be ≤ body_chars; user msg also has title prefix
        # so total length is ≤ body_chars + ~50
        assert len(user_msg) <= 2100
        # Should not contain 10K x's
        assert user_msg.count("x") <= 2000

    def test_explicit_kwargs_override_env(self, monkeypatch):
        from mcp_server import llm_extractor

        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        captured = {}
        def fake_urlopen(req, timeout):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            return _mock_response(json.dumps({
                "claim_summary": "X", "open_questions": []
            }))

        with patch.object(
            llm_extractor.urllib.request, "urlopen",
            side_effect=fake_urlopen,
        ):
            llm_extractor.extract_card_essence(
                "T", "B",
                api_key="sk-explicit",
                url="https://override.test/v1/chat",
                model="custom/model",
            )

        assert captured["url"] == "https://override.test/v1/chat"
        # Find the auth header (case-insensitive key)
        auth = next(
            v for k, v in captured["headers"].items()
            if k.lower() == "authorization"
        )
        assert auth == "Bearer sk-explicit"


# ---------- error paths ----------

class TestExtractorErrors:
    def test_empty_title(self, monkeypatch):
        from mcp_server.llm_extractor import (
            extract_card_essence, LLMExtractorError,
        )
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with pytest.raises(LLMExtractorError):
            extract_card_essence("", "body content")

    def test_empty_body(self, monkeypatch):
        from mcp_server.llm_extractor import (
            extract_card_essence, LLMExtractorError,
        )
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with pytest.raises(LLMExtractorError):
            extract_card_essence("Title", "")

    def test_missing_key(self, monkeypatch):
        from mcp_server.llm_extractor import (
            extract_card_essence, LLMExtractorUnavailable,
        )
        for k in ("OPENROUTER_API_KEY", "OPENAI_API_KEY"):
            monkeypatch.delenv(k, raising=False)
        with pytest.raises(LLMExtractorUnavailable):
            extract_card_essence("T", "B")

    def test_url_error_raises_unavailable(self, monkeypatch):
        from mcp_server import llm_extractor
        from urllib.error import URLError

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_extractor.urllib.request, "urlopen",
            side_effect=URLError("dns fail"),
        ):
            with pytest.raises(llm_extractor.LLMExtractorUnavailable):
                llm_extractor.extract_card_essence("T", "B")

    def test_malformed_envelope_raises(self, monkeypatch):
        from mcp_server import llm_extractor

        class _Resp:
            def __enter__(self):
                return io.BytesIO(b"not json")
            def __exit__(self, *a):
                return False

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_extractor.urllib.request, "urlopen",
            return_value=_Resp(),
        ):
            with pytest.raises(llm_extractor.LLMExtractorError):
                llm_extractor.extract_card_essence("T", "B")

    def test_missing_choices(self, monkeypatch):
        from mcp_server import llm_extractor

        class _Resp:
            def __enter__(self):
                return io.BytesIO(b'{"error": "no model"}')
            def __exit__(self, *a):
                return False

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_extractor.urllib.request, "urlopen",
            return_value=_Resp(),
        ):
            with pytest.raises(llm_extractor.LLMExtractorError):
                llm_extractor.extract_card_essence("T", "B")

    def test_unparseable_content_raises(self, monkeypatch):
        from mcp_server import llm_extractor

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_extractor.urllib.request, "urlopen",
            return_value=_mock_response("complete garbage no json"),
        ):
            with pytest.raises(llm_extractor.LLMExtractorError):
                llm_extractor.extract_card_essence("T", "B")
