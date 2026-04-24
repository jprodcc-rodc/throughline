"""End-to-end integration tests for the daemon's LLM call path.

Covers the full provider-resolution pipeline the DAEMON uses (not
the wizard, which has its own test suite):

    config.toml / env var
           |
           v
    active_provider.resolve_endpoint_and_key()
           |
           v
    daemon.refine_daemon._LLM_URL / _LLM_KEY / _LLM_EXTRA_HEADERS
           |
           v
    daemon.refine_daemon.call_llm_json()
           |
           v
    urllib.request.urlopen()  (mocked at this boundary)

Before U28 these were untested end-to-end; a user flipping provider
via config.toml would have no guarantee the daemon actually used
it. These tests pin that round-trip.
"""
from __future__ import annotations

import importlib
import json
import sys
import urllib.error
from pathlib import Path
from typing import Any, Dict

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import providers as pr


# -----------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------


def _clear_provider_keys(monkeypatch):
    for preset in pr.list_presets():
        monkeypatch.delenv(preset.env_var, raising=False)
    for var in ("THROUGHLINE_LLM_PROVIDER", "THROUGHLINE_LLM_URL",
                 "OPENROUTER_URL"):
        monkeypatch.delenv(var, raising=False)


def _reload_refine_daemon():
    """Re-import `daemon.refine_daemon` so module-level _LLM_* are
    recomputed from the current env + config.toml. Returns the
    reloaded module."""
    # Drop the cached module + its dependencies so module-load side
    # effects (which read env) re-run under the test's env setup.
    for mod_name in (
        "daemon.refine_daemon",
        "throughline_cli.active_provider",
    ):
        if mod_name in sys.modules:
            del sys.modules[mod_name]
    return importlib.import_module("daemon.refine_daemon")


def _fake_ok_response(*, content: str = '{"x": 1}',
                       prompt_tokens: int = 100,
                       completion_tokens: int = 50,
                       status: int = 200):
    """Minimal OpenAI-shape response with usage."""
    body = json.dumps({
        "choices": [{"message": {"content": content}}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    }).encode("utf-8")

    class _Resp:
        def __init__(self): self.status = status
        def read(self): return body
        def __enter__(self): return self
        def __exit__(self, *a): pass

    return _Resp()


# -----------------------------------------------------------------
# Round-trip through each provider
# -----------------------------------------------------------------


class TestDaemonRoutesThroughConfiguredProvider:
    """config.toml / env pick the provider; the daemon's LLM call
    must land at the right URL with the right key + headers."""

    def test_openrouter_from_env(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-live")
        rd = _reload_refine_daemon()

        assert rd._LLM_PROVIDER_ID == "openrouter"
        assert "openrouter.ai" in rd._LLM_URL
        assert rd._LLM_URL.endswith("/chat/completions")
        assert rd._LLM_KEY == "sk-or-live"
        # Provider-specific headers resolved.
        assert "HTTP-Referer" in rd._LLM_EXTRA_HEADERS

        captured: Dict[str, Any] = {}

        def fake_open(req, timeout=None):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            captured["body"] = json.loads(req.data.decode("utf-8"))
            return _fake_ok_response(content='{"result": "ok"}')

        monkeypatch.setattr("urllib.request.urlopen", fake_open)

        out = rd.call_llm_json(
            model="anthropic/claude-sonnet-4.6",
            system_prompt="S", user_prompt="U",
            temperature=0.0, max_tokens=100,
        )
        assert out == {"result": "ok"}
        assert "openrouter.ai" in captured["url"]
        auth = {k.lower(): v for k, v in captured["headers"].items()}
        assert auth["authorization"] == "Bearer sk-or-live"
        # OpenRouter routing metadata preserved.
        assert "http-referer" in auth
        # Daemon's own X-Title NOT clobbered by provider headers.
        assert auth["x-title"] == "throughline-refine-daemon"
        assert captured["body"]["model"] == "anthropic/claude-sonnet-4.6"

    def test_deepseek_from_config_toml(self, tmp_path, monkeypatch):
        """Config-driven: user has DEEPSEEK_API_KEY set and
        config.toml says llm_provider = deepseek."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        (tmp_path / "config.toml").write_text(
            'llm_provider = "deepseek"\n', encoding="utf-8")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds-live")
        rd = _reload_refine_daemon()

        assert rd._LLM_PROVIDER_ID == "deepseek"
        assert "deepseek.com" in rd._LLM_URL

        captured: Dict[str, Any] = {}

        def fake_open(req, timeout=None):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            return _fake_ok_response()

        monkeypatch.setattr("urllib.request.urlopen", fake_open)
        rd.call_llm_json(
            model="deepseek-chat",
            system_prompt="S", user_prompt="U",
            temperature=0.0, max_tokens=100,
        )
        assert "deepseek.com" in captured["url"]
        # DeepSeek doesn't need OpenRouter's referer header.
        headers = {k.lower(): v for k, v in captured["headers"].items()}
        assert "http-referer" not in headers
        assert headers["authorization"] == "Bearer sk-ds-live"

    def test_anthropic_via_native_messages_api(self, tmp_path, monkeypatch):
        """Daemon with provider=anthropic must route through the
        native /v1/messages adapter, not the OpenAI-compat shim.
        x-api-key auth; cost_stats records usage correctly despite
        Anthropic's different field names."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        (tmp_path / "config.toml").write_text(
            'llm_provider = "anthropic"\n', encoding="utf-8")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        # State dir for cost_stats output.
        state_dir = tmp_path / "state"
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state_dir))

        rd = _reload_refine_daemon()
        assert rd._LLM_PROVIDER_ID == "anthropic"

        captured: Dict[str, Any] = {}

        def fake_open(req, timeout=None):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            captured["body"] = json.loads(req.data.decode("utf-8"))
            body = json.dumps({
                "content": [{"type": "text",
                             "text": '{"refined": "ok"}'}],
                "usage": {"input_tokens": 321,
                          "output_tokens": 45},
            }).encode("utf-8")

            class _Resp:
                def read(self): return body
                def __enter__(self): return self
                def __exit__(self, *a): pass

            return _Resp()

        monkeypatch.setattr("urllib.request.urlopen", fake_open)

        out = rd.call_llm_json(
            model="claude-sonnet-4-5-20250929",
            system_prompt="S", user_prompt="U",
            temperature=0.0, max_tokens=1000,
            step_name="Refiner",
        )
        assert out == {"refined": "ok"}
        # Endpoint: /messages, not /chat/completions.
        assert captured["url"].endswith("/messages")
        # Auth: x-api-key, not Bearer.
        hdrs = {k.lower(): v for k, v in captured["headers"].items()}
        assert hdrs.get("x-api-key") == "sk-ant-test"
        assert "authorization" not in hdrs
        # Version pinned.
        assert hdrs.get("anthropic-version")
        # Request body has system at top level.
        assert "system" in captured["body"]
        # Cost stats survived the rename: Anthropic returns
        # input_tokens/output_tokens but _record_cost sees
        # prompt_tokens/completion_tokens.
        stats = json.loads(rd.COST_STATS_FILE.read_text(encoding="utf-8"))
        day = list(stats["by_date"].values())[0]
        assert day["Refiner"]["input_tokens"] == 321
        assert day["Refiner"]["output_tokens"] == 45

    def test_siliconflow_from_env_override(self, tmp_path, monkeypatch):
        """THROUGHLINE_LLM_PROVIDER env wins over config.toml."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        (tmp_path / "config.toml").write_text(
            'llm_provider = "openrouter"\n', encoding="utf-8")
        monkeypatch.setenv("THROUGHLINE_LLM_PROVIDER", "siliconflow")
        monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-sf-live")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-bystander")
        rd = _reload_refine_daemon()

        assert rd._LLM_PROVIDER_ID == "siliconflow"
        assert "siliconflow.cn" in rd._LLM_URL

        captured: Dict[str, Any] = {}
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=None: captured.__setitem__(
                "url", req.full_url) or _fake_ok_response(),
        )
        rd.call_llm_json(
            model="Qwen/Qwen2.5-72B-Instruct",
            system_prompt="S", user_prompt="U",
            temperature=0.0, max_tokens=100,
        )
        assert "siliconflow.cn" in captured["url"]


# -----------------------------------------------------------------
# Legacy compatibility
# -----------------------------------------------------------------


class TestLegacyBackwardCompat:
    """Users who set only OPENROUTER_URL (pre-U28 override) must
    keep working without touching config."""

    def test_openrouter_url_override_still_honoured(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        monkeypatch.setenv(
            "OPENROUTER_URL",
            "https://my-proxy.example/v1/chat/completions")
        rd = _reload_refine_daemon()

        assert rd._LLM_URL == "https://my-proxy.example/v1/chat/completions"

        captured: Dict[str, Any] = {}
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=None: captured.__setitem__(
                "url", req.full_url) or _fake_ok_response(),
        )
        rd.call_llm_json(model="m", system_prompt="S", user_prompt="U",
                          temperature=0.0, max_tokens=10)
        assert captured["url"] == "https://my-proxy.example/v1/chat/completions"


# -----------------------------------------------------------------
# Missing-key path
# -----------------------------------------------------------------


class TestMissingKeyErrorIsReadable:
    def test_provider_chosen_but_key_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        monkeypatch.setenv("THROUGHLINE_LLM_PROVIDER", "moonshot")
        # MOONSHOT_API_KEY NOT set.
        rd = _reload_refine_daemon()

        # Resolver should surface the empty key at module load.
        assert rd._LLM_KEY is None
        assert rd._LLM_PROVIDER_ID == "moonshot"

        with pytest.raises(RuntimeError) as ei:
            rd.call_llm_json(model="moonshot-v1-32k",
                              system_prompt="S", user_prompt="U",
                              temperature=0.0, max_tokens=10)
        msg = str(ei.value).lower()
        assert "moonshot" in msg
        assert "api key" in msg


# -----------------------------------------------------------------
# Retry behaviour
# -----------------------------------------------------------------


class TestRetryThenSucceed:
    def test_daemon_retries_on_transient_http_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        rd = _reload_refine_daemon()

        # First two calls raise, third succeeds.
        calls = {"n": 0}

        def flaky(req, timeout=None):
            calls["n"] += 1
            if calls["n"] < 3:
                raise urllib.error.URLError("transient")
            return _fake_ok_response(content='{"ok": true}')

        monkeypatch.setattr("urllib.request.urlopen", flaky)
        # Patch time.sleep so the retries don't actually sleep.
        monkeypatch.setattr("time.sleep", lambda _s: None)

        out = rd.call_llm_json(model="m", system_prompt="S", user_prompt="U",
                                temperature=0.0, max_tokens=10, retries=2)
        assert out == {"ok": True}
        assert calls["n"] == 3


# -----------------------------------------------------------------
# Usage-tracking side effect
# -----------------------------------------------------------------


class TestCostStatsSideEffect:
    def test_success_records_cost(self, tmp_path, monkeypatch):
        """When step_name is supplied, a successful call must append
        to cost_stats.json. Cost accuracy is out of scope for this
        integration test — we just assert the file grew."""
        state_dir = tmp_path / "state"
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state_dir))
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "cfg"))
        _clear_provider_keys(monkeypatch)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        rd = _reload_refine_daemon()

        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=None: _fake_ok_response(
                prompt_tokens=500, completion_tokens=200,
            ),
        )

        stats_file = rd.COST_STATS_FILE
        assert not stats_file.exists()

        rd.call_llm_json(
            model="anthropic/claude-sonnet-4.6",
            system_prompt="S", user_prompt="U",
            temperature=0.0, max_tokens=1000,
            step_name="Refiner",
        )

        assert stats_file.exists()
        stats = json.loads(stats_file.read_text(encoding="utf-8"))
        assert "by_date" in stats
        any_day = list(stats["by_date"].values())[0]
        assert "Refiner" in any_day
        assert any_day["Refiner"]["calls"] == 1
        assert any_day["Refiner"]["input_tokens"] == 500
        assert any_day["Refiner"]["output_tokens"] == 200
