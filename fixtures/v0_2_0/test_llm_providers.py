"""Tests for U28 — llm.py provider-aware path.

Pins that call_chat(provider_id=...) resolves the right endpoint,
reads the right env var, sends the right bearer token, and injects
provider-specific extra headers (OpenRouter's HTTP-Referer/X-Title).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import llm


def _fake_ok_response(content: str = "hello"):
    class _Resp:
        def read(self_inner):
            return json.dumps({
                "choices": [{"message": {"content": content}}]
            }).encode("utf-8")
        def __enter__(self_inner):
            return self_inner
        def __exit__(self_inner, *a):
            pass
    return _Resp()


class TestProviderAwareEndpoint:
    def test_openrouter(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        captured = {}

        def fake_open(req, timeout=None):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            return _fake_ok_response()

        monkeypatch.setattr("urllib.request.urlopen", fake_open)
        out = llm.call_chat("anthropic/claude-sonnet-4.6", "S", "U",
                             provider_id="openrouter")
        assert out == "hello"
        assert "openrouter.ai" in captured["url"]
        assert captured["url"].endswith("/chat/completions")
        headers = {k.lower(): v for k, v in captured["headers"].items()}
        assert headers.get("authorization") == "Bearer sk-or"
        # OpenRouter-specific extra headers injected.
        assert "http-referer" in headers
        assert "x-title" in headers

    def test_deepseek(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
        captured = {}

        def fake_open(req, timeout=None):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            return _fake_ok_response()

        monkeypatch.setattr("urllib.request.urlopen", fake_open)
        llm.call_chat("deepseek-chat", "S", "U",
                       provider_id="deepseek")
        assert "deepseek.com" in captured["url"]
        headers = {k.lower(): v for k, v in captured["headers"].items()}
        assert headers.get("authorization") == "Bearer sk-ds"
        # DeepSeek doesn't need the OpenRouter referer header.
        assert "http-referer" not in headers

    def test_siliconflow(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-sf")
        captured = {}

        def fake_open(req, timeout=None):
            captured["url"] = req.full_url
            return _fake_ok_response()

        monkeypatch.setattr("urllib.request.urlopen", fake_open)
        llm.call_chat("Qwen/Qwen2.5-72B-Instruct", "S", "U",
                       provider_id="siliconflow")
        assert "siliconflow.cn" in captured["url"]


class TestGetApiKeyProviderAware:
    def test_explicit_provider(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
        assert llm.get_api_key("deepseek") == "sk-ds"
        assert llm.get_api_key("openrouter") is None

    def test_no_provider_uses_legacy_chain(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        assert llm.get_api_key() == "sk-or"

    def test_legacy_fallback_to_openai(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-oa")
        assert llm.get_api_key() == "sk-oa"


class TestGetEndpointProviderAware:
    def test_explicit(self):
        url = llm.get_endpoint("deepseek")
        assert url == "https://api.deepseek.com/v1/chat/completions"

    def test_no_provider_default(self, monkeypatch):
        monkeypatch.delenv("THROUGHLINE_LLM_URL", raising=False)
        assert llm.get_endpoint() == llm.DEFAULT_ENDPOINT

    def test_no_provider_env_override(self, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_LLM_URL", "https://custom/v1")
        assert llm.get_endpoint() == "https://custom/v1"


class TestMissingKeyError:
    def test_explicit_provider_gives_provider_hint(self, monkeypatch):
        for var in ("OPENROUTER_API_KEY", "SILICONFLOW_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        with pytest.raises(llm.LLMError) as ei:
            llm.call_chat("Qwen/Qwen2.5-72B-Instruct", "S", "U",
                           provider_id="siliconflow")
        msg = str(ei.value)
        assert "SILICONFLOW_API_KEY" in msg
        assert "siliconflow.cn" in msg  # signup URL included

    def test_no_provider_gives_legacy_hint(self, monkeypatch):
        for preset_env in ("OPENROUTER_API_KEY", "OPENAI_API_KEY"):
            monkeypatch.delenv(preset_env, raising=False)
        with pytest.raises(llm.LLMError) as ei:
            llm.call_chat("x", "S", "U")
        msg = str(ei.value)
        assert "OPENROUTER_API_KEY" in msg

    def test_unknown_provider_falls_to_legacy_error(self, monkeypatch):
        """If someone passes a typo'd provider_id, they get the
        generic legacy error, not a crash."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(llm.LLMError) as ei:
            llm.call_chat("x", "S", "U", provider_id="typo-ai")
        assert "OPENROUTER_API_KEY" in str(ei.value)


class TestBackwardCompatNoProviderId:
    """The pre-U28 call signature (no provider_id) must keep working
    so derive_taxonomy.py and any downstream scripts don't break."""

    def test_still_works(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-legacy")
        captured = {}

        def fake_open(req, timeout=None):
            captured["url"] = req.full_url
            return _fake_ok_response()

        monkeypatch.setattr("urllib.request.urlopen", fake_open)
        llm.call_chat("anthropic/claude-sonnet-4.6", "S", "U")
        assert "openrouter.ai" in captured["url"]
