"""Tests for U28 — multi-provider LLM support.

Pins the provider registry shape and the resolver semantics:
- every preset has the contract fields populated
- alias / autodetect / generic-fallback all work as advertised
- env-var drift doesn't regress
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import providers as p


# ---------- Registry shape ----------

class TestRegistryShape:
    def test_at_least_ten_presets(self):
        """v0.2.x ships with 16 presets (8 global + 5 cn + 2 local + 1 generic).
        Pin a lower bound so an accidental delete doesn't go unnoticed."""
        assert len(p.list_presets()) >= 10

    def test_every_preset_has_required_fields(self):
        for preset in p.list_presets():
            assert preset.id, "preset missing id"
            assert preset.name, f"{preset.id} missing name"
            assert preset.env_var, f"{preset.id} missing env_var"
            # `generic` has empty base_url (user supplies); others must have one.
            if preset.id != "generic":
                assert preset.base_url, f"{preset.id} missing base_url"
            # `generic` and `lm_studio` may have empty model list; others
            # should surface at least one default.
            if preset.id not in ("generic",):
                assert preset.models or preset.id == "lm_studio"

    def test_env_vars_are_screaming_snake_case(self):
        """API-key env vars are conventionally UPPERCASE_WITH_UNDERSCORES."""
        for preset in p.list_presets():
            ev = preset.env_var
            assert ev == ev.upper(), f"{preset.id}: env var {ev} not uppercase"
            assert " " not in ev, f"{preset.id}: env var has space"

    def test_base_urls_no_trailing_slash(self):
        """resolve_base_url rstrips trailing slash anyway, but the
        registry should ship canonical values."""
        for preset in p.list_presets():
            if preset.base_url:
                assert not preset.base_url.endswith("/"), (
                    f"{preset.id}: base_url has trailing /"
                )

    def test_regions_partitioned(self):
        """Every preset belongs to exactly one of our four regions."""
        valid = {"global", "cn", "local", "custom"}
        for preset in p.list_presets():
            assert preset.region in valid, (
                f"{preset.id}: unknown region {preset.region!r}"
            )

    def test_region_coverage(self):
        """Sanity check that each region has at least one entry."""
        by_region = {r: p.presets_by_region(r)
                      for r in ("global", "cn", "local", "custom")}
        for r, presets in by_region.items():
            assert presets, f"no presets in region {r}"


# ---------- get_preset ----------

class TestGetPreset:
    def test_openrouter_found(self):
        preset = p.get_preset("openrouter")
        assert preset.env_var == "OPENROUTER_API_KEY"
        assert preset.base_url.startswith("https://openrouter.ai")

    def test_case_insensitive(self):
        assert p.get_preset("OpenRouter").id == "openrouter"

    def test_whitespace_trimmed(self):
        assert p.get_preset("  openrouter  ").id == "openrouter"

    def test_unknown_raises_with_known_list(self):
        with pytest.raises(ValueError) as ei:
            p.get_preset("banana-ai")
        msg = str(ei.value)
        assert "banana-ai" in msg
        assert "openrouter" in msg  # known list leaked into error


# ---------- detect_configured_provider ----------

class TestAutoDetect:
    def test_no_key_set_returns_none(self, monkeypatch):
        for preset in p.list_presets():
            monkeypatch.delenv(preset.env_var, raising=False)
        assert p.detect_configured_provider() is None

    def test_openrouter_key_wins(self, monkeypatch):
        for preset in p.list_presets():
            monkeypatch.delenv(preset.env_var, raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-oa")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        # OpenRouter listed first in detection order → wins over OpenAI
        # so users with both set don't silently get swapped.
        assert p.detect_configured_provider() == "openrouter"

    def test_openai_only(self, monkeypatch):
        for preset in p.list_presets():
            monkeypatch.delenv(preset.env_var, raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-oa")
        assert p.detect_configured_provider() == "openai"

    def test_siliconflow_picked_up(self, monkeypatch):
        for preset in p.list_presets():
            monkeypatch.delenv(preset.env_var, raising=False)
        monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-sf")
        assert p.detect_configured_provider() == "siliconflow"


# ---------- resolve_base_url ----------

class TestResolveBaseUrl:
    def test_openrouter(self):
        assert p.resolve_base_url("openrouter").endswith("openrouter.ai/api/v1")

    def test_siliconflow(self):
        assert "siliconflow.cn" in p.resolve_base_url("siliconflow")

    def test_generic_falls_back_to_env_var(self, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_LLM_URL", "https://custom.example/v1")
        assert p.resolve_base_url("generic") == "https://custom.example/v1"

    def test_generic_default_is_openrouter(self, monkeypatch):
        monkeypatch.delenv("THROUGHLINE_LLM_URL", raising=False)
        # Falls back to OpenRouter as the documented safe default.
        assert "openrouter" in p.resolve_base_url("generic")


# ---------- resolve_api_key ----------

class TestResolveApiKey:
    def test_returns_none_when_unset(self, monkeypatch):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        assert p.resolve_api_key("deepseek") is None

    def test_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
        assert p.resolve_api_key("deepseek") == "sk-ds"

    def test_trims_whitespace(self, monkeypatch):
        monkeypatch.setenv("MOONSHOT_API_KEY", "   sk-mn   ")
        assert p.resolve_api_key("moonshot") == "sk-mn"


# ---------- register_preset (plug-in point) ----------

class TestRegisterPreset:
    def test_can_add_then_resolve(self):
        custom = p.ProviderPreset(
            id="my-cluster",
            name="My corporate cluster",
            base_url="https://llm.corp.example/v1",
            env_var="CORP_LLM_KEY",
            signup_url="",
            models=(("corp-model-7b", "Corp 7B"),),
        )
        p.register_preset(custom)
        try:
            resolved = p.get_preset("my-cluster")
            assert resolved.base_url == "https://llm.corp.example/v1"
        finally:
            p._REGISTRY.pop("my-cluster", None)


# ---------- Chinese-market coverage ----------

class TestChinaMarketPresets:
    """Chinese-market providers are a significant motivation for the
    refactor. Spot-check that each one is present and wired correctly."""

    @pytest.mark.parametrize("provider_id,env_var,base_host", [
        ("siliconflow", "SILICONFLOW_API_KEY", "siliconflow.cn"),
        ("moonshot",    "MOONSHOT_API_KEY",    "moonshot.cn"),
        ("dashscope",   "DASHSCOPE_API_KEY",   "dashscope.aliyuncs.com"),
        ("zhipu",       "ZHIPU_API_KEY",       "bigmodel.cn"),
        ("doubao",      "ARK_API_KEY",         "volces.com"),
    ])
    def test_cn_preset_shape(self, provider_id, env_var, base_host):
        preset = p.get_preset(provider_id)
        assert preset.region == "cn"
        assert preset.env_var == env_var
        assert base_host in preset.base_url


# ---------- local / self-hosted coverage ----------

class TestLocalPresets:
    def test_ollama(self):
        preset = p.get_preset("ollama")
        assert preset.region == "local"
        assert "11434" in preset.base_url

    def test_lm_studio(self):
        preset = p.get_preset("lm_studio")
        assert preset.region == "local"
        assert "1234" in preset.base_url


# ---------- legacy_key_lookup (backward compat) ----------

class TestLegacyCompat:
    def test_openrouter_first(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-oa")
        assert p.legacy_key_lookup() == "sk-or"

    def test_openai_fallback(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-oa")
        assert p.legacy_key_lookup() == "sk-oa"

    def test_neither(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert p.legacy_key_lookup() is None
