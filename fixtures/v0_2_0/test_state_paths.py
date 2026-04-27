"""Tests for daemon.state_paths centralized helpers."""
from __future__ import annotations

import pytest


# ---------- env-var resolution ----------

class TestDefaults:
    def test_state_dir_uses_env_var(self, monkeypatch, tmp_path):
        from daemon.state_paths import default_state_dir

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "custom"))
        p = default_state_dir()
        assert "custom" in str(p)

    def test_state_dir_default_under_home(self, monkeypatch):
        from daemon.state_paths import default_state_dir

        monkeypatch.delenv("THROUGHLINE_STATE_DIR", raising=False)
        p = default_state_dir()
        assert "throughline_runtime" in str(p)
        assert "state" in str(p)

    def test_vault_root_uses_env_var(self, monkeypatch, tmp_path):
        from daemon.state_paths import default_vault_root

        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path / "vault"))
        p = default_vault_root()
        assert "vault" in str(p)

    @pytest.mark.parametrize("fname,expected_filename", [
        ("default_state_file", "reflection_pass_state.json"),
        ("default_cluster_names_file", "reflection_cluster_names.json"),
        ("default_backfill_state_file", "reflection_backfill_state.json"),
        ("default_open_threads_file", "reflection_open_threads.json"),
        ("default_positions_file", "reflection_positions.json"),
        ("default_writeback_preview_file", "reflection_writeback_preview.json"),
        ("default_contradictions_file", "reflection_contradictions.json"),
        ("default_drift_file", "reflection_drift.json"),
    ])
    def test_default_files_have_correct_filename(self, fname, expected_filename):
        import daemon.state_paths as sp

        f = getattr(sp, fname)
        assert f().name == expected_filename

    def test_all_state_files_returns_full_dict(self, monkeypatch, tmp_path):
        from daemon.state_paths import all_state_files

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        out = all_state_files()
        # All 8 keys present (pass_state, cluster_names, backfill_cache,
        # open_threads, positions, writeback_preview, contradictions, drift)
        assert len(out) == 8
        # Each value resolves under our tmp_path
        for name, p in out.items():
            assert str(tmp_path) in str(p)

    def test_lazy_resolution(self, monkeypatch, tmp_path):
        """env-var changes between calls take effect — paths resolved
        at call time, not import time."""
        from daemon.state_paths import default_state_file

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "first"))
        first = default_state_file()
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "second"))
        second = default_state_file()
        assert "first" in str(first)
        assert "second" in str(second)


# ---------- card_timestamp ----------

class TestCardTimestamp:
    def test_uses_frontmatter_date(self):
        from daemon.state_paths import card_timestamp

        c = {"frontmatter": {"date": "2026-01-15"}, "path": "/x"}
        assert card_timestamp(c) == "2026-01-15"

    def test_falls_back_to_updated(self):
        from daemon.state_paths import card_timestamp

        c = {"frontmatter": {"updated": "2026-02-20"}, "path": "/x"}
        assert card_timestamp(c) == "2026-02-20"

    def test_date_takes_precedence(self):
        from daemon.state_paths import card_timestamp

        c = {
            "frontmatter": {"date": "2026-01-15", "updated": "2026-03-01"},
            "path": "/x",
        }
        assert card_timestamp(c) == "2026-01-15"

    def test_falls_back_to_mtime(self, tmp_path):
        from daemon.state_paths import card_timestamp

        p = tmp_path / "card.md"
        p.write_text("body", encoding="utf-8")
        c = {"frontmatter": {}, "path": str(p)}
        assert card_timestamp(c).startswith("mtime-")

    def test_zero_when_nothing_resolvable(self):
        from daemon.state_paths import card_timestamp

        c = {"frontmatter": {}, "path": "/nonexistent_path_xyz"}
        assert card_timestamp(c) == "0"

    def test_handles_non_dict_frontmatter(self):
        from daemon.state_paths import card_timestamp

        c = {"frontmatter": "garbled", "path": "/nonexistent"}
        assert card_timestamp(c) == "0"

    def test_open_threads_alias_still_works(self):
        """Back-compat: daemon.open_threads._card_timestamp is the
        old name; should still work via re-export."""
        from daemon.open_threads import _card_timestamp

        c = {"frontmatter": {"date": "2026-04-01"}, "path": "/x"}
        assert _card_timestamp(c) == "2026-04-01"
