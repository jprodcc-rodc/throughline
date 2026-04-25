"""Tests for throughline_cli.anthropic_adapter — the native
Messages API adapter that replaces the previous /v1/openai shim.

Pins:
- Request shape (url, headers, body JSON structure)
- Response parsing (content array -> text, usage field rename)
- Prompt-caching control block on the system prompt
- Backward-compatible return shape so downstream parse_json_loose +
  _record_cost don't need to branch
- Error paths (HTTP 4xx/5xx, non-JSON, empty content)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import anthropic_adapter as aa


# -----------------------------------------------------------------
# _build_request_body
# -----------------------------------------------------------------

class TestBuildRequestBody:
    def test_system_is_top_level_field_not_a_message(self):
        body = aa._build_request_body(
            model="claude-sonnet-4-5-20250929",
            system_prompt="You are helpful.",
            user_message="Explain keto rebound.",
            temperature=0.0,
            max_tokens=500,
        )
        assert "system" in body
        # Anthropic expects user-role messages only (no role=system).
        assert all(m["role"] != "system" for m in body["messages"])

    def test_user_message_is_sole_message(self):
        body = aa._build_request_body(
            model="m", system_prompt="s", user_message="u",
            temperature=0.0, max_tokens=100,
        )
        assert len(body["messages"]) == 1
        assert body["messages"][0] == {"role": "user", "content": "u"}

    def test_max_tokens_required_and_int(self):
        body = aa._build_request_body(
            model="m", system_prompt="s", user_message="u",
            temperature=0.0, max_tokens=999,
        )
        assert body["max_tokens"] == 999
        assert isinstance(body["max_tokens"], int)

    def test_prompt_caching_on_by_default(self):
        """System block should be an array with cache_control when
        caching is enabled (the default)."""
        body = aa._build_request_body(
            model="m", system_prompt="S", user_message="u",
            temperature=0.0, max_tokens=100,
        )
        assert isinstance(body["system"], list)
        assert body["system"][0]["type"] == "text"
        assert body["system"][0]["text"] == "S"
        assert body["system"][0]["cache_control"] == {"type": "ephemeral"}

    def test_prompt_caching_off_gives_string_system(self):
        body = aa._build_request_body(
            model="m", system_prompt="S", user_message="u",
            temperature=0.0, max_tokens=100,
            enable_prompt_caching=False,
        )
        assert body["system"] == "S"

    def test_response_format_ignored(self):
        """Anthropic has no JSON mode; response_format is a no-op.
        Callers can still pass it through for OpenAI compatibility."""
        body = aa._build_request_body(
            model="m", system_prompt="s", user_message="u",
            temperature=0.0, max_tokens=100,
            response_format={"type": "json_object"},
        )
        # No response_format in the output body.
        assert "response_format" not in body


# -----------------------------------------------------------------
# _parse_response
# -----------------------------------------------------------------

class TestParseResponse:
    def test_extracts_text_from_single_block(self):
        raw = json.dumps({
            "content": [{"type": "text", "text": "hello world"}],
            "usage": {"input_tokens": 12, "output_tokens": 5},
        })
        text, usage = aa._parse_response(raw)
        assert text == "hello world"
        assert usage == {"prompt_tokens": 12, "completion_tokens": 5}

    def test_concatenates_multiple_text_blocks(self):
        """Anthropic occasionally splits a response into multiple
        text blocks (e.g. around tool-use). Adapter stitches them
        back together."""
        raw = json.dumps({
            "content": [
                {"type": "text", "text": "part one "},
                {"type": "text", "text": "part two"},
            ],
            "usage": {"input_tokens": 10, "output_tokens": 4},
        })
        text, _ = aa._parse_response(raw)
        assert text == "part one part two"

    def test_skips_non_text_blocks(self):
        """Tool-use blocks shouldn't leak into the string return."""
        raw = json.dumps({
            "content": [
                {"type": "text", "text": "answer: "},
                {"type": "tool_use", "id": "abc", "name": "calc",
                 "input": {}},
                {"type": "text", "text": "42"},
            ],
            "usage": {"input_tokens": 20, "output_tokens": 8},
        })
        text, _ = aa._parse_response(raw)
        assert text == "answer: 42"

    def test_renames_usage_fields(self):
        """Anthropic uses input_tokens/output_tokens. Downstream
        _record_cost keys off prompt_tokens/completion_tokens, so
        we rename here."""
        raw = json.dumps({
            "content": [{"type": "text", "text": "x"}],
            "usage": {"input_tokens": 500, "output_tokens": 200},
        })
        _, usage = aa._parse_response(raw)
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "input_tokens" not in usage
        assert usage["prompt_tokens"] == 500
        assert usage["completion_tokens"] == 200

    def test_missing_usage_defaults_to_zero(self):
        raw = json.dumps({
            "content": [{"type": "text", "text": "x"}],
        })
        _, usage = aa._parse_response(raw)
        assert usage == {"prompt_tokens": 0, "completion_tokens": 0}

    def test_non_json_raises(self):
        with pytest.raises(aa.AnthropicAdapterError) as ei:
            aa._parse_response("not json {")
        assert "non-JSON" in str(ei.value)

    def test_empty_content_raises(self):
        raw = json.dumps({"content": [], "usage": {}})
        with pytest.raises(aa.AnthropicAdapterError) as ei:
            aa._parse_response(raw)
        assert "no text" in str(ei.value).lower()

    def test_truncated_response_carries_flag(self):
        """`stop_reason: max_tokens` means Anthropic ran out of
        tokens mid-emit. The adapter surfaces this via a
        `_truncated: True` flag on the usage dict — caller can
        warn the user instead of letting the truncated body fail
        downstream JSON parsing with a misleading 'bad JSON' error."""
        raw = json.dumps({
            "content": [{"type": "text", "text": '{"unterminated json'}],
            "usage": {"input_tokens": 100, "output_tokens": 4000},
            "stop_reason": "max_tokens",
        })
        text, usage = aa._parse_response(raw)
        assert text.startswith("{")
        assert usage.get("_truncated") is True
        # Other fields preserved.
        assert usage["prompt_tokens"] == 100
        assert usage["completion_tokens"] == 4000

    def test_normal_stop_reason_no_truncation_flag(self):
        raw = json.dumps({
            "content": [{"type": "text", "text": "complete output"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "stop_reason": "end_turn",
        })
        text, usage = aa._parse_response(raw)
        assert "_truncated" not in usage


# -----------------------------------------------------------------
# call_messages
# -----------------------------------------------------------------

def _fake_response(body_dict):
    class _Resp:
        def __init__(self):
            self._body = json.dumps(body_dict).encode("utf-8")
        def read(self): return self._body
        def __enter__(self): return self
        def __exit__(self, *a): pass
    return _Resp()


class TestCallMessages:
    def test_hits_messages_endpoint(self, monkeypatch):
        captured = {}

        def fake_open(req, timeout=None):
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["headers"] = dict(req.header_items())
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _fake_response({
                "content": [{"type": "text", "text": "ok"}],
                "usage": {"input_tokens": 5, "output_tokens": 1},
            })

        monkeypatch.setattr("urllib.request.urlopen", fake_open)
        text, usage = aa.call_messages(
            model="claude-sonnet-4-5-20250929",
            system_prompt="S", user_message="U",
            api_key="sk-ant-123",
            base_url="https://api.anthropic.com/v1",
            temperature=0.0, max_tokens=100,
        )
        assert text == "ok"
        assert usage == {"prompt_tokens": 5, "completion_tokens": 1}
        assert captured["url"] == "https://api.anthropic.com/v1/messages"
        assert captured["method"] == "POST"

    def test_uses_x_api_key_not_bearer(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=None: captured.__setitem__(
                "headers", dict(req.header_items())) or _fake_response({
                    "content": [{"type": "text", "text": "x"}],
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                }),
        )
        aa.call_messages(
            model="m", system_prompt="s", user_message="u",
            api_key="sk-ant-xyz",
            base_url="https://api.anthropic.com/v1",
            temperature=0.0, max_tokens=10,
        )
        headers = {k.lower(): v for k, v in captured["headers"].items()}
        # Anthropic uses x-api-key, NOT Authorization: Bearer.
        assert headers.get("x-api-key") == "sk-ant-xyz"
        assert "authorization" not in headers

    def test_sends_version_header(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=None: captured.__setitem__(
                "headers", dict(req.header_items())) or _fake_response({
                    "content": [{"type": "text", "text": "x"}],
                    "usage": {},
                }),
        )
        aa.call_messages(
            model="m", system_prompt="s", user_message="u",
            api_key="k", base_url="https://api.anthropic.com/v1",
            temperature=0.0, max_tokens=10,
        )
        headers = {k.lower(): v for k, v in captured["headers"].items()}
        assert headers.get("anthropic-version") == aa.ANTHROPIC_API_VERSION

    def test_prompt_caching_beta_header_sent(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=None: captured.__setitem__(
                "headers", dict(req.header_items())) or _fake_response({
                    "content": [{"type": "text", "text": "x"}],
                    "usage": {},
                }),
        )
        aa.call_messages(
            model="m", system_prompt="s", user_message="u",
            api_key="k", base_url="https://api.anthropic.com/v1",
            temperature=0.0, max_tokens=10,
        )
        headers = {k.lower(): v for k, v in captured["headers"].items()}
        assert "prompt-caching" in headers.get("anthropic-beta", "")

    def test_http_error_wrapped(self, monkeypatch):
        import urllib.error

        def fake_open(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 401, "Unauthorized",
                {}, io.BytesIO(b'{"type":"error","error":{"message":"bad key"}}'))

        monkeypatch.setattr("urllib.request.urlopen", fake_open)
        with pytest.raises(aa.AnthropicAdapterError) as ei:
            aa.call_messages(
                model="m", system_prompt="s", user_message="u",
                api_key="k", base_url="https://api.anthropic.com/v1",
                temperature=0.0, max_tokens=10,
            )
        msg = str(ei.value)
        assert "401" in msg
        assert "bad key" in msg

    def test_network_error_wrapped(self, monkeypatch):
        import urllib.error

        def fake_open(req, timeout=None):
            raise urllib.error.URLError("dns failure")

        monkeypatch.setattr("urllib.request.urlopen", fake_open)
        with pytest.raises(aa.AnthropicAdapterError) as ei:
            aa.call_messages(
                model="m", system_prompt="s", user_message="u",
                api_key="k", base_url="https://api.anthropic.com/v1",
                temperature=0.0, max_tokens=10,
            )
        assert "network" in str(ei.value)


# -----------------------------------------------------------------
# Dispatch from llm.call_chat
# -----------------------------------------------------------------

class TestLlmCallChatDispatchesToAdapter:
    def test_provider_anthropic_routes_to_adapter(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-xyz")
        captured = {}

        def fake_open(req, timeout=None):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            return _fake_response({
                "content": [{"type": "text", "text": '{"ok": true}'}],
                "usage": {"input_tokens": 10, "output_tokens": 2},
            })

        monkeypatch.setattr("urllib.request.urlopen", fake_open)

        from throughline_cli import llm
        out = llm.call_chat(
            "claude-sonnet-4-5-20250929",
            "S", "U",
            provider_id="anthropic",
        )
        # Adapter returns raw text; call_chat passes it through.
        assert out == '{"ok": true}'
        # URL routes through /messages, not /chat/completions.
        assert captured["url"].endswith("/messages")
        # x-api-key, not Bearer.
        hlc = {k.lower(): v for k, v in captured["headers"].items()}
        assert hlc.get("x-api-key") == "sk-ant-xyz"
        assert "authorization" not in hlc
