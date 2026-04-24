"""Tests for `throughline_cli.active_provider` — the non-wizard
(daemon, scripts) path that resolves which LLM provider should
handle a call.

Precedence tested:
    1. THROUGHLINE_LLM_PROVIDER env
    2. llm_provider in config.toml
    3. first provider with env-var key set
    4. 'openrouter' fallback
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import active_provider as ap
from throughline_cli import providers as pr


def _clear_all_keys(monkeypatch):
    """Wipe every provider API-key env var so tests start clean."""
    for preset in pr.list_presets():
        monkeypatch.delenv(preset.env_var, raising=False)
    monkeypatch.delenv("OPENROUTER_URL", raising=False)
    monkeypatch.delenv("THROUGHLINE_LLM_URL", raising=False)
    monkeypatch.delenv("THROUGHLINE_LLM_PROVIDER", raising=False)


class TestResolveProviderId:
    def test_env_var_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("THROUGHLINE_LLM_PROVIDER", "deepseek")
        # Even though a conflicting key is set, env wins.
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        assert ap.resolve_provider_id() == "deepseek"

    def test_config_toml(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text(
            'llm_provider = "moonshot"\n', encoding="utf-8")
        _clear_all_keys(monkeypatch)
        monkeypatch.delenv("THROUGHLINE_LLM_PROVIDER", raising=False)
        assert ap.resolve_provider_id() == "moonshot"

    def test_autodetect_siliconflow(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-sf")
        assert ap.resolve_provider_id() == "siliconflow"

    def test_final_fallback_openrouter(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_all_keys(monkeypatch)
        # Nothing set at all — legal state for a fresh install.
        assert ap.resolve_provider_id() == "openrouter"

    def test_malformed_config_toml(self, tmp_path, monkeypatch):
        """Broken config.toml must not crash — falls through to
        autodetect + openrouter."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text(
            "[this is garbage TOML", encoding="utf-8")
        _clear_all_keys(monkeypatch)
        # No crash; falls through.
        assert ap.resolve_provider_id() == "openrouter"


class TestResolveEndpointAndKey:
    def test_openrouter_shape(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        url, key, extra, pid = ap.resolve_endpoint_and_key()
        assert "openrouter.ai" in url
        assert url.endswith("/chat/completions")
        assert key == "sk-or"
        assert "HTTP-Referer" in extra
        assert pid == "openrouter"

    def test_deepseek_shape(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
        url, key, extra, pid = ap.resolve_endpoint_and_key()
        assert "deepseek.com" in url
        assert key == "sk-ds"
        # Bare DeepSeek doesn't need OpenRouter headers.
        assert "HTTP-Referer" not in extra
        assert pid == "deepseek"

    def test_legacy_openrouter_url_override(self, tmp_path, monkeypatch):
        """Pre-U28 users had OPENROUTER_URL pointing at a custom
        proxy. Keep it working."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        monkeypatch.setenv("OPENROUTER_URL",
                            "https://proxy.example/v1/chat/completions")
        url, _, _, _ = ap.resolve_endpoint_and_key()
        assert url == "https://proxy.example/v1/chat/completions"

    def test_legacy_url_without_suffix(self, tmp_path, monkeypatch):
        """If OPENROUTER_URL points at the /v1 base without the
        /chat/completions suffix, append it."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        monkeypatch.setenv("OPENROUTER_URL", "https://proxy.example/v1")
        url, _, _, _ = ap.resolve_endpoint_and_key()
        assert url == "https://proxy.example/v1/chat/completions"

    def test_config_picks_siliconflow(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text(
            'llm_provider = "siliconflow"\n', encoding="utf-8")
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-sf")
        url, key, _, pid = ap.resolve_endpoint_and_key()
        assert "siliconflow.cn" in url
        assert key == "sk-sf"
        assert pid == "siliconflow"

    def test_missing_key_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("THROUGHLINE_LLM_PROVIDER", "moonshot")
        # MOONSHOT_API_KEY intentionally not set.
        url, key, _, pid = ap.resolve_endpoint_and_key()
        assert "moonshot.cn" in url
        assert key is None
        assert pid == "moonshot"

    def test_unknown_provider_falls_back(self, tmp_path, monkeypatch):
        """Typo'd provider id -> openrouter fallback with legacy
        key chain."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("THROUGHLINE_LLM_PROVIDER", "typo-ai")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        url, key, extra, pid = ap.resolve_endpoint_and_key()
        assert "openrouter.ai" in url
        assert key == "sk-or"
        assert "HTTP-Referer" in extra
        assert pid == "openrouter"
