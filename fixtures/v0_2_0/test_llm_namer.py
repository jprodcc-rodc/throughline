"""Tests for mcp_server.llm_namer.

Covers:
- env-var resolution (URL / key / model)
- _sanitize_name on all the wrapping shapes LLMs emit
- name_cluster happy path with mocked urlopen
- name_cluster error paths: missing key, network unreachable,
  malformed JSON, missing choices, unusable model output
- titles trimming (≤20) + per-title length cap (200 chars)

No real network calls; ``urllib.request.urlopen`` is mocked at
the boundary so tests run offline.
"""
from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest


# ---------- _sanitize_name ----------

class TestSanitizeName:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("pricing_strategy", "pricing_strategy"),
            ("Pricing_Strategy", "pricing_strategy"),
            ("  pricing_strategy  ", "pricing_strategy"),
            ('"pricing_strategy"', "pricing_strategy"),
            ("'pricing_strategy'", "pricing_strategy"),
            ("`pricing_strategy`", "pricing_strategy"),
            ("**pricing_strategy**", "pricing_strategy"),
            ("Topic: pricing_strategy", "pricing_strategy"),
            ("Name: pricing_strategy", "pricing_strategy"),
            ("Cluster: pricing_strategy.", "pricing_strategy"),
            ("Label: pricing_strategy,", "pricing_strategy"),
            ("pricing strategy", "pricing_strategy"),
            ("Pricing Strategy", "pricing_strategy"),
            ("pricing-strategy", "pricing_strategy"),
            ("pricing_strategy\nand other stuff", "pricing_strategy"),
            ("pricing_strategy.", "pricing_strategy"),
            # Already snake_case variants
            ("b1_thiamine_therapy", "b1_thiamine_therapy"),
            ("diablo_4_build_optimization", "diablo_4_build_optimization"),
        ],
    )
    def test_sanitize_recovers_name(self, raw, expected):
        from mcp_server.llm_namer import _sanitize_name

        assert _sanitize_name(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "   ",
            "***",
            "...",
            # Starts with digit (not valid identifier)
            "1pricing",
        ],
    )
    def test_sanitize_returns_empty_on_unrecoverable(self, raw):
        from mcp_server.llm_namer import _sanitize_name

        assert _sanitize_name(raw) == ""

    def test_sanitize_caps_at_80_chars(self):
        """Pathological long names get rejected."""
        from mcp_server.llm_namer import _sanitize_name

        # 81 chars
        raw = "a" * 81
        assert _sanitize_name(raw) == ""


# ---------- env-var resolution ----------

class TestResolveEndpoint:
    def test_default_url_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_URL", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        # Also clear the OpenAI-compat fallback env vars so the
        # default-resolution path is exercised honestly.
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from mcp_server.llm_namer import resolve_endpoint_and_key, DEFAULT_URL

        url, key = resolve_endpoint_and_key()
        assert url == DEFAULT_URL
        assert key is None

    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_URL", "https://example.test/v1/chat")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test123")
        from mcp_server.llm_namer import resolve_endpoint_and_key

        url, key = resolve_endpoint_and_key()
        assert url == "https://example.test/v1/chat"
        assert key == "sk-test123"

    def test_empty_url_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_URL", "")
        from mcp_server.llm_namer import resolve_endpoint_and_key, DEFAULT_URL

        url, _ = resolve_endpoint_and_key()
        assert url == DEFAULT_URL

    def test_openai_api_key_fallback(self, monkeypatch):
        """When OPENROUTER_API_KEY is not set but OPENAI_API_KEY is,
        use OPENAI_API_KEY (matches the standard 'use OpenAI client
        lib pointed at any OpenAI-compatible endpoint' pattern)."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-or-v1-fallback")
        from mcp_server.llm_namer import resolve_endpoint_and_key

        _, key = resolve_endpoint_and_key()
        assert key == "sk-or-v1-fallback"

    def test_openrouter_takes_precedence_over_openai(self, monkeypatch):
        """When both env vars set, OPENROUTER_API_KEY wins."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-explicit")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fallback-loses")
        from mcp_server.llm_namer import resolve_endpoint_and_key

        _, key = resolve_endpoint_and_key()
        assert key == "sk-or-explicit"

    def test_openai_base_url_fallback(self, monkeypatch):
        """OPENAI_BASE_URL gets /chat/completions appended when
        absent. OpenAI ecosystem convention is OPENAI_BASE_URL =
        'https://openrouter.ai/api/v1' (no path); we add the path."""
        monkeypatch.delenv("OPENROUTER_URL", raising=False)
        monkeypatch.setenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
        from mcp_server.llm_namer import resolve_endpoint_and_key

        url, _ = resolve_endpoint_and_key()
        assert url == "https://openrouter.ai/api/v1/chat/completions"

    def test_openai_base_url_already_includes_path(self, monkeypatch):
        """If OPENAI_BASE_URL already has /chat/completions (rare
        but legal), don't double-append."""
        monkeypatch.delenv("OPENROUTER_URL", raising=False)
        monkeypatch.setenv(
            "OPENAI_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
        )
        from mcp_server.llm_namer import resolve_endpoint_and_key

        url, _ = resolve_endpoint_and_key()
        assert url == "https://openrouter.ai/api/v1/chat/completions"

    def test_openrouter_url_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_URL", "https://explicit.test/v1/chat")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://other.test/v1")
        from mcp_server.llm_namer import resolve_endpoint_and_key

        url, _ = resolve_endpoint_and_key()
        assert url == "https://explicit.test/v1/chat"

    def test_resolve_model_default(self, monkeypatch):
        monkeypatch.delenv("THROUGHLINE_NAMER_MODEL", raising=False)
        from mcp_server.llm_namer import resolve_model, DEFAULT_MODEL

        assert resolve_model() == DEFAULT_MODEL

    def test_resolve_model_override(self, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_NAMER_MODEL", "anthropic/claude-haiku")
        from mcp_server.llm_namer import resolve_model

        assert resolve_model() == "anthropic/claude-haiku"


# ---------- name_cluster happy path ----------

def _mock_response(content: str) -> io.BytesIO:
    """Build an OpenAI-compat chat-completions response payload."""
    body = {
        "id": "chatcmpl-test",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 5},
    }
    raw = json.dumps(body).encode("utf-8")
    fp = io.BytesIO(raw)

    class _CtxMgr:
        def __enter__(self):
            return fp
        def __exit__(self, *a):
            return False

    return _CtxMgr()


class TestNameClusterHappy:
    def test_names_cluster_from_titles(self, monkeypatch):
        from mcp_server import llm_namer

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        with patch.object(
            llm_namer.urllib.request,
            "urlopen",
            return_value=_mock_response("pricing_strategy"),
        ):
            name = llm_namer.name_cluster([
                "SaaS pricing strategy for early-stage startups",
                "How usage-based pricing affects LTV",
                "Freemium conversion strategy",
            ])

        assert name == "pricing_strategy"

    def test_sanitizes_decorated_output(self, monkeypatch):
        """Model wraps name in quotes; sanitizer recovers."""
        from mcp_server import llm_namer

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        with patch.object(
            llm_namer.urllib.request,
            "urlopen",
            return_value=_mock_response('"b1_thiamine_therapy"'),
        ):
            name = llm_namer.name_cluster(["B1 deficiency", "Thiamine dose"])

        assert name == "b1_thiamine_therapy"

    def test_payload_includes_first_20_titles(self, monkeypatch):
        """Many-title clusters get trimmed to first 20 to bound
        prompt size without losing semantic value."""
        from mcp_server import llm_namer

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        captured = {}

        def fake_urlopen(req, timeout):
            captured["data"] = req.data
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            return _mock_response("foo_topic")

        titles = [f"title number {i}" for i in range(50)]
        with patch.object(llm_namer.urllib.request, "urlopen", side_effect=fake_urlopen):
            llm_namer.name_cluster(titles)

        body = json.loads(captured["data"].decode("utf-8"))
        user_msg = body["messages"][1]["content"]
        # Should mention 50 total but show 20 titles
        assert "Cluster contains 50 cards" in user_msg
        assert "Showing 20 titles" in user_msg

    def test_per_title_length_cap(self, monkeypatch):
        """Long titles are truncated to keep prompt size bounded."""
        from mcp_server import llm_namer

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        captured = {}
        def fake_urlopen(req, timeout):
            captured["body"] = req.data.decode("utf-8")
            return _mock_response("foo")

        long = "x" * 500
        with patch.object(llm_namer.urllib.request, "urlopen", side_effect=fake_urlopen):
            llm_namer.name_cluster([long])

        # Body should not contain 500 'x's — trimmed to ≤200.
        body = json.loads(captured["body"])
        user = body["messages"][1]["content"]
        # Count consecutive 'x's anywhere
        x_runs = [s for s in user.split() if set(s) == {"x"}]
        max_run = max((len(s) for s in x_runs), default=0)
        assert max_run <= 200


# ---------- name_cluster error paths ----------

class TestNameClusterErrors:
    def test_missing_api_key_raises_unavailable(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        from mcp_server.llm_namer import name_cluster, LLMNamerUnavailable

        with pytest.raises(LLMNamerUnavailable):
            name_cluster(["title"])

    def test_empty_titles_raises_error(self, monkeypatch):
        from mcp_server.llm_namer import name_cluster, LLMNamerError

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with pytest.raises(LLMNamerError):
            name_cluster([])

    def test_url_error_raises_unavailable(self, monkeypatch):
        from mcp_server import llm_namer
        from urllib.error import URLError

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_namer.urllib.request, "urlopen",
            side_effect=URLError("connection refused"),
        ):
            with pytest.raises(llm_namer.LLMNamerUnavailable):
                llm_namer.name_cluster(["title"])

    def test_malformed_json_raises_error(self, monkeypatch):
        from mcp_server import llm_namer

        class _BadResp:
            def __enter__(self):
                return io.BytesIO(b"not json at all")
            def __exit__(self, *a):
                return False

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_namer.urllib.request, "urlopen", return_value=_BadResp()
        ):
            with pytest.raises(llm_namer.LLMNamerError):
                llm_namer.name_cluster(["title"])

    def test_missing_choices_raises_error(self, monkeypatch):
        from mcp_server import llm_namer

        # Valid JSON but missing the choices structure
        class _Resp:
            def __enter__(self):
                return io.BytesIO(b'{"error": "no model"}')
            def __exit__(self, *a):
                return False

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_namer.urllib.request, "urlopen", return_value=_Resp()
        ):
            with pytest.raises(llm_namer.LLMNamerError):
                llm_namer.name_cluster(["title"])

    def test_unsanitizable_output_raises_error(self, monkeypatch):
        """Model emits something that can't be coerced to snake_case
        (e.g., empty string or pathological garbage). Caller gets a
        clear error rather than a silently-wrong name."""
        from mcp_server import llm_namer

        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        with patch.object(
            llm_namer.urllib.request, "urlopen",
            return_value=_mock_response("***"),
        ):
            with pytest.raises(llm_namer.LLMNamerError):
                llm_namer.name_cluster(["title"])

    def test_explicit_api_key_overrides_env(self, monkeypatch):
        """api_key= kwarg supersedes env."""
        from mcp_server import llm_namer

        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        with patch.object(
            llm_namer.urllib.request, "urlopen",
            return_value=_mock_response("foo_topic"),
        ):
            name = llm_namer.name_cluster(
                ["title"],
                api_key="sk-explicit",
            )
        assert name == "foo_topic"
