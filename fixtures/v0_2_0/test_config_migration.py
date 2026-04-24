"""Tests for `throughline_cli.config` schema migrations.

Covers the silent upgrade path for pre-U28 config.toml files that
lack `llm_provider`. The migration must be non-destructive
(preserves every other field) and idempotent (running load twice
doesn't change anything after the first rewrite).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import config as cfg_mod
from throughline_cli import providers as pr


def _clear_provider_keys(monkeypatch):
    for preset in pr.list_presets():
        monkeypatch.delenv(preset.env_var, raising=False)


class TestPreU28Migration:
    def test_missing_llm_provider_backfills_openrouter(self, tmp_path, monkeypatch):
        """Pre-U28 config with no llm_provider field + no env var set
        -> migration picks the documented default ('openrouter')."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        # Write a pre-U28 config (no llm_provider, no schema version).
        (tmp_path / "config.toml").write_text(
            'mission = "full"\n'
            'llm_provider_id = "anthropic/claude-sonnet-4.6"\n'
            'refine_tier = "normal"\n'
            'daily_budget_usd = 10.0\n',
            encoding="utf-8",
        )
        cfg = cfg_mod.load()
        assert cfg.llm_provider == "openrouter"
        # Unchanged fields survived.
        assert cfg.mission == "full"
        assert cfg.llm_provider_id == "anthropic/claude-sonnet-4.6"
        assert cfg.refine_tier == "normal"
        assert cfg.daily_budget_usd == 10.0
        # Schema version stamped.
        assert cfg.config_schema_version == 2

    def test_missing_llm_provider_autodetects_from_env(self, tmp_path, monkeypatch):
        """Pre-U28 config + SILICONFLOW_API_KEY set in env -> the
        migration should notice and route to siliconflow rather than
        the documented openrouter default."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-sf")
        (tmp_path / "config.toml").write_text(
            'mission = "full"\n', encoding="utf-8")
        cfg = cfg_mod.load()
        assert cfg.llm_provider == "siliconflow"

    def test_migration_rewrites_config_to_disk(self, tmp_path, monkeypatch):
        """After migration, the on-disk file should contain the new
        llm_provider field + schema version. Next load reads it
        directly without re-running the migration."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
        p = tmp_path / "config.toml"
        p.write_text('mission = "full"\n', encoding="utf-8")

        cfg_mod.load()

        rewritten = p.read_text(encoding="utf-8")
        assert 'llm_provider = "deepseek"' in rewritten
        assert 'config_schema_version = 2' in rewritten

    def test_existing_llm_provider_is_preserved(self, tmp_path, monkeypatch):
        """If llm_provider is already set, migration must NOT overwrite
        it — even if the env var points at a different provider."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        monkeypatch.setenv("MOONSHOT_API_KEY", "sk-mn")
        (tmp_path / "config.toml").write_text(
            'llm_provider = "deepseek"\n'
            'mission = "full"\n',
            encoding="utf-8",
        )
        cfg = cfg_mod.load()
        # The user's chosen provider wins over autodetect.
        assert cfg.llm_provider == "deepseek"

    def test_already_migrated_is_noop(self, tmp_path, monkeypatch):
        """Current-schema config -> load must not touch the file."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        p = tmp_path / "config.toml"
        p.write_text(
            'mission = "full"\n'
            'llm_provider = "openrouter"\n'
            'config_schema_version = 2\n',
            encoding="utf-8",
        )
        mtime_before = p.stat().st_mtime_ns
        cfg_mod.load()
        # Give the OS enough time to register a write; if migration
        # wrote, mtime changes.
        mtime_after = p.stat().st_mtime_ns
        assert mtime_before == mtime_after

    def test_missing_file_still_returns_defaults(self, tmp_path, monkeypatch):
        """Migration must not crash on a fresh install that has no
        config.toml at all."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "absent"))
        _clear_provider_keys(monkeypatch)
        cfg = cfg_mod.load()
        # Defaults, no crash.
        assert cfg.mission == "full"
        assert cfg.llm_provider == "openrouter"

    def test_malformed_migration_does_not_crash_load(self, tmp_path, monkeypatch):
        """If providers module is broken at migration time (shouldn't
        happen in practice), load still returns a usable cfg."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        p = tmp_path / "config.toml"
        p.write_text('mission = "full"\n', encoding="utf-8")

        # Force detect_configured_provider to explode.
        def _bad_detect():
            raise RuntimeError("simulated provider registry crash")

        monkeypatch.setattr(pr, "detect_configured_provider", _bad_detect)
        # Must not raise.
        cfg = cfg_mod.load()
        # Fallback path: cfg has SOME llm_provider set, just maybe not
        # the one autodetect would have chosen.
        assert isinstance(cfg.llm_provider, str)
        assert cfg.llm_provider  # non-empty


class TestReadOnlyFilesystem:
    """Migration should not prevent load() from returning even if the
    config dir is read-only (Docker secret mount, locked file, etc.)."""

    def test_read_only_rewrite_is_silent(self, tmp_path, monkeypatch):
        """We can't easily chmod on Windows; simulate by making save()
        raise OSError and confirm load() still returns a cfg."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        (tmp_path / "config.toml").write_text(
            'mission = "full"\n', encoding="utf-8")

        def _readonly_save(_):
            raise OSError("simulated read-only FS")

        monkeypatch.setattr(cfg_mod, "save", _readonly_save)
        cfg = cfg_mod.load()
        # Migration still populated in-memory.
        assert cfg.llm_provider == "openrouter"


class TestFieldPreservation:
    """Widespread migration regression is the scariest kind. This test
    writes a maxed-out config, migrates it, and confirms every field
    survived."""

    def test_every_field_preserved_across_migration(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        _clear_provider_keys(monkeypatch)
        # Write a pre-U28 config that sets many non-default fields
        # but leaves llm_provider out.
        (tmp_path / "config.toml").write_text(
            'mission = "rag_only"\n'
            'vector_db = "chroma"\n'
            'api_key_source = "keyring"\n'
            'llm_provider_id = "anthropic/claude-opus-4.7"\n'
            'privacy = "local_only"\n'
            'embedder = "openai"\n'
            'reranker = "cohere"\n'
            'prompt_family = "gpt"\n'
            'import_source = "claude"\n'
            'import_path = "/tmp/export.zip"\n'
            'refine_tier = "deep"\n'
            'card_structure = "detailed"\n'
            'dial_tone = "formal"\n'
            'dial_length = "long"\n'
            'dial_sections = ["scenario", "summary"]\n'
            'dial_register = "plain"\n'
            'dial_keep_verbatim = true\n'
            'taxonomy_source = "derive_from_imports"\n'
            'daily_budget_usd = 7.5\n',
            encoding="utf-8",
        )
        cfg = cfg_mod.load()
        assert cfg.mission == "rag_only"
        assert cfg.vector_db == "chroma"
        assert cfg.api_key_source == "keyring"
        assert cfg.llm_provider_id == "anthropic/claude-opus-4.7"
        assert cfg.privacy == "local_only"
        assert cfg.embedder == "openai"
        assert cfg.reranker == "cohere"
        assert cfg.prompt_family == "gpt"
        assert cfg.import_source == "claude"
        assert cfg.import_path == "/tmp/export.zip"
        assert cfg.refine_tier == "deep"
        assert cfg.card_structure == "detailed"
        assert cfg.dial_tone == "formal"
        assert cfg.dial_length == "long"
        assert cfg.dial_sections == ["scenario", "summary"]
        assert cfg.dial_register == "plain"
        assert cfg.dial_keep_verbatim is True
        assert cfg.taxonomy_source == "derive_from_imports"
        assert cfg.daily_budget_usd == 7.5
        # New field backfilled.
        assert cfg.llm_provider == "openrouter"
