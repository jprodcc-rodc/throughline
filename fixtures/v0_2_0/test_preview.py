"""Tests for U17 preview gate (wizard step 13) and the llm.py helper.

LLM calls are mocked at urllib.request.urlopen so no real HTTP
traffic / API key needed in CI. The mock returns realistic
openai-compatible JSON shapes so the parsing path gets exercised.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import llm
from throughline_cli.config import WizardConfig


def _fake_urlopen(reply_content: str):
    """Build a fake urlopen context manager returning the given
    string as the assistant content. Returns the patch target."""
    response_payload = json.dumps({
        "id": "chatcmpl-fake",
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": reply_content},
            "finish_reason": "stop",
        }],
    }).encode("utf-8")

    class _FakeResp:
        def __init__(self, body):
            self._body = body
        def read(self):
            return self._body
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    return _FakeResp(response_payload)


# ========== llm.py core ==========

class TestCallChat:
    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(llm.LLMError, match="no API key"):
            llm.call_chat("anthropic/claude-haiku-4.5",
                          "system", "user")

    def test_happy_path_returns_content(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        resp = _fake_urlopen('{"title": "ok"}')
        with patch("throughline_cli.llm.urllib.request.urlopen",
                   return_value=resp):
            out = llm.call_chat("anthropic/claude-haiku-4.5",
                                "system prompt", "user msg")
        assert out == '{"title": "ok"}'

    def test_sends_expected_payload_shape(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        captured = {}

        def fake(req, timeout):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _fake_urlopen("{}")

        with patch("throughline_cli.llm.urllib.request.urlopen", fake):
            llm.call_chat("anthropic/claude-haiku-4.5",
                          "S", "U",
                          response_format={"type": "json_object"})

        assert "openrouter.ai" in captured["url"]
        # Header keys on an urllib Request are title-cased; check
        # loosely.
        auth = next((v for k, v in captured["headers"].items()
                     if k.lower() == "authorization"), "")
        assert auth == "Bearer sk-test"
        body = captured["body"]
        assert body["model"] == "anthropic/claude-haiku-4.5"
        assert body["messages"][0] == {"role": "system", "content": "S"}
        assert body["messages"][1] == {"role": "user", "content": "U"}
        assert body["response_format"] == {"type": "json_object"}
        assert body["temperature"] == 0.0

    def test_http_error_wrapped_as_llm_error(self, monkeypatch):
        import urllib.error
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        def raise_http(req, timeout):
            raise urllib.error.HTTPError(
                req.full_url, 401, "Unauthorized", {},
                io.BytesIO(b'{"error": "bad key"}'),
            )

        with patch("throughline_cli.llm.urllib.request.urlopen", raise_http):
            with pytest.raises(llm.LLMError, match="401"):
                llm.call_chat("anthropic/claude-haiku-4.5", "S", "U")

    def test_network_error_wrapped(self, monkeypatch):
        import urllib.error
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        def raise_net(req, timeout):
            raise urllib.error.URLError("connection refused")

        with patch("throughline_cli.llm.urllib.request.urlopen", raise_net):
            with pytest.raises(llm.LLMError, match="network"):
                llm.call_chat("anthropic/claude-haiku-4.5", "S", "U")

    def test_non_json_response_wrapped(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        class BadResp:
            def read(self):
                return b"<html>error</html>"
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False

        with patch("throughline_cli.llm.urllib.request.urlopen",
                   return_value=BadResp()):
            with pytest.raises(llm.LLMError, match="non-JSON"):
                llm.call_chat("x", "S", "U")

    def test_env_var_precedence(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-only")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        assert llm.get_api_key() == "sk-openai-only"
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-openrouter-preferred")
        assert llm.get_api_key() == "sk-openrouter-preferred"

    def test_custom_endpoint_env(self, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_LLM_URL",
                            "https://custom.example.com/v1/chat")
        assert llm.get_endpoint() == "https://custom.example.com/v1/chat"


# ========== wizard step 13 integration ==========

class TestStep13Preview:
    def _build_cfg_with_claude_sample(self, tmp_path, import_path=None):
        import json
        if import_path is None:
            import_path = tmp_path / "claude.jsonl"
            import_path.write_text(json.dumps({
                "uuid": "conv-1",
                "name": "MPS setup question",
                "created_at": "2024-01-15T10:00:00Z",
                "chat_messages": [
                    {"sender": "human", "text": "How do I enable MPS?"},
                    {"sender": "assistant", "text": "Use torch.device('mps')."},
                ],
            }) + "\n", encoding="utf-8")
        cfg = WizardConfig()
        cfg.import_source = "claude"
        cfg.import_path = str(import_path)
        cfg.prompt_family = "claude"
        cfg.refine_tier = "normal"
        cfg.llm_provider_id = "anthropic/claude-sonnet-4.6"
        cfg.mission = "full"
        return cfg

    def test_skipped_for_none_source(self):
        from throughline_cli.wizard import step_13_preview
        cfg = WizardConfig()
        cfg.import_source = "none"
        assert step_13_preview(cfg) == "SKIPPED"

    def test_parses_sample_and_shows_raw_without_api_key(self, monkeypatch, tmp_path):
        from throughline_cli.wizard import step_13_preview
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        cfg = self._build_cfg_with_claude_sample(tmp_path)
        # Must not raise, must not call urllib.
        with patch("throughline_cli.llm.urllib.request.urlopen") as opener:
            step_13_preview(cfg)
            opener.assert_not_called()

    def test_calls_llm_when_key_present(self, monkeypatch, tmp_path):
        from throughline_cli.wizard import step_13_preview
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        cfg = self._build_cfg_with_claude_sample(tmp_path)

        mock_card = {
            "title": "Enable MPS on M2",
            "body_markdown": "# Enable MPS\n\nUse torch.device('mps').",
            "primary_x": "AI/LLM",
        }
        resp = _fake_urlopen(json.dumps(mock_card))
        # Drive the y/N at the end of the step: default Y, which takes
        # empty input.
        monkeypatch.setattr("builtins.input", lambda *_a, **_k: "")
        with patch("throughline_cli.llm.urllib.request.urlopen",
                   return_value=resp):
            step_13_preview(cfg)

    def test_llm_error_does_not_crash(self, monkeypatch, tmp_path):
        from throughline_cli.wizard import step_13_preview
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        cfg = self._build_cfg_with_claude_sample(tmp_path)

        def raise_llm(*a, **kw):
            import urllib.error
            raise urllib.error.URLError("connection refused")

        with patch("throughline_cli.llm.urllib.request.urlopen", raise_llm):
            # Must not raise; wizard should log + continue.
            step_13_preview(cfg)

    def test_no_renderable_conversation_skips_cleanly(self, monkeypatch, tmp_path):
        from throughline_cli.wizard import step_13_preview
        cfg = self._build_cfg_with_claude_sample(
            tmp_path,
            import_path=tmp_path / "empty.jsonl",
        )
        (tmp_path / "empty.jsonl").write_text("", encoding="utf-8")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert step_13_preview(cfg) == "SKIPPED"

    def test_rag_only_uses_rag_optimized_variant(self, monkeypatch, tmp_path):
        from throughline_cli.wizard import _variant_for_cfg
        cfg = self._build_cfg_with_claude_sample(tmp_path)
        cfg.mission = "rag_only"
        assert _variant_for_cfg(cfg) == "rag_optimized"


# ========== adapter preview_one() ==========

class TestPreviewOne:
    def test_claude_preview_one(self, tmp_path):
        import json
        p = tmp_path / "claude.jsonl"
        p.write_text(json.dumps({
            "uuid": "abc",
            "name": "T",
            "chat_messages": [
                {"sender": "human", "text": "q"},
                {"sender": "assistant", "text": "a"},
            ],
        }) + "\n", encoding="utf-8")
        from throughline_cli.adapters import claude_export
        out = claude_export.preview_one(p)
        assert out is not None
        title, messages, cid = out
        assert cid == "abc"
        assert len(messages) == 2

    def test_chatgpt_preview_one(self, tmp_path):
        import json
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps([{
            "id": "c-1",
            "title": "T",
            "create_time": 1700000000.0,
            "mapping": {
                "root": {"id": "root", "parent": None,
                          "children": ["u1"], "message": None},
                "u1": {"id": "u1", "parent": "root", "children": ["a1"],
                        "message": {"author": {"role": "user"},
                                    "content": {"content_type": "text",
                                                "parts": ["q"]}}},
                "a1": {"id": "a1", "parent": "u1", "children": [],
                        "message": {"author": {"role": "assistant"},
                                    "content": {"content_type": "text",
                                                "parts": ["a"]}}},
            },
        }]), encoding="utf-8")
        from throughline_cli.adapters import chatgpt_export
        out = chatgpt_export.preview_one(p)
        assert out is not None
        title, messages, cid = out
        assert cid == "c-1"
        assert len(messages) == 2

    def test_gemini_preview_one(self, tmp_path):
        import json
        p = tmp_path / "MyActivity.json"
        p.write_text(json.dumps([{
            "header": "Gemini Apps",
            "title": "Prompted hi",
            "time": "2024-01-15T10:00:00Z",
            "products": ["Gemini Apps"],
            "safeHtmlItem": [{"html": "<p>reply</p>"}],
        }]), encoding="utf-8")
        from throughline_cli.adapters import gemini_takeout
        out = gemini_takeout.preview_one(p)
        assert out is not None
        title, messages, cid = out
        assert cid == "gemini-2024-01-15"
        assert any("hi" in m[1] for m in messages)

    def test_preview_one_none_on_empty_input(self, tmp_path):
        p = tmp_path / "claude.jsonl"
        p.write_text("", encoding="utf-8")
        from throughline_cli.adapters import claude_export
        assert claude_export.preview_one(p) is None
