"""Tests for `python -m throughline_cli uninstall`.

We can't actually `rm -rf` the user's real dirs in tests, so every
path is redirected via env vars to a tmp_path. The uninstall logic
is sequenced through the same code the real CLI runs.
"""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import uninstall as u


class TestHelpAndUsage:
    def test_help(self, capsys):
        rc = u.main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "uninstall" in out
        assert "--drop-collection" in out

    def test_unknown_arg(self, capsys):
        rc = u.main(["--zztop"])
        assert rc == 2


class TestDryRunChangesNothing:
    def test_dry_run_lists_targets(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        state_dir = tmp_path / "state"
        log_dir = tmp_path / "logs"
        raw_dir = tmp_path / "raw"
        for d in (cfg_dir, state_dir, log_dir, raw_dir):
            d.mkdir()
            (d / "sentinel.txt").write_text("x")

        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state_dir))
        monkeypatch.setenv("THROUGHLINE_LOG_DIR", str(log_dir))
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(raw_dir))

        captured: list[str] = []
        rc = u.main(["--dry-run", "--yes"],
                     reader=lambda _: "n",
                     out=captured.append)
        assert rc == 0
        text = " ".join(captured)
        assert "would remove" in text
        # Nothing was actually deleted.
        for d in (cfg_dir, state_dir, log_dir, raw_dir):
            assert (d / "sentinel.txt").exists()


class TestRemovesDefaultPaths:
    def test_yes_removes_config_state_logs_raw(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        state_dir = tmp_path / "state"
        log_dir = tmp_path / "logs"
        raw_dir = tmp_path / "raw"
        for d in (cfg_dir, state_dir, log_dir, raw_dir):
            d.mkdir()
            (d / "sentinel.txt").write_text("x")

        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state_dir))
        monkeypatch.setenv("THROUGHLINE_LOG_DIR", str(log_dir))
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(raw_dir))

        captured: list[str] = []
        rc = u.main(["--yes"], out=captured.append)
        assert rc == 0
        for d in (cfg_dir, state_dir, log_dir, raw_dir):
            assert not d.exists(), f"{d} should have been removed"

    def test_keep_config_preserves_config_dir(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        state_dir = tmp_path / "state"
        cfg_dir.mkdir()
        state_dir.mkdir()
        (cfg_dir / "config.toml").write_text("x")

        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state_dir))
        # Point the other two at paths that don't exist.
        monkeypatch.setenv("THROUGHLINE_LOG_DIR", str(tmp_path / "absent_logs"))
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "absent_raw"))

        rc = u.main(["--yes", "--keep-config"], out=lambda _s: None)
        assert rc == 0
        assert cfg_dir.exists()
        assert not state_dir.exists()


class TestQdrantCollectionGate:
    def test_no_drop_by_default(self, tmp_path, monkeypatch):
        """Without --drop-collection, the Qdrant API must NOT be
        called. The CLI should print a skip line."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "c"))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "s"))
        monkeypatch.setenv("THROUGHLINE_LOG_DIR", str(tmp_path / "l"))
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "r"))

        def must_not_open(*a, **k):
            raise AssertionError(
                "urllib.urlopen called without --drop-collection"
            )

        monkeypatch.setattr("urllib.request.urlopen", must_not_open)

        captured: list[str] = []
        rc = u.main(["--yes"], out=captured.append)
        assert rc == 0
        text = " ".join(captured)
        assert "keep:" in text
        assert "Qdrant collection" in text

    def test_drop_flag_calls_delete(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "c"))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "s"))
        monkeypatch.setenv("THROUGHLINE_LOG_DIR", str(tmp_path / "l"))
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "r"))
        monkeypatch.setenv("QDRANT_URL", "http://fake:6333")
        monkeypatch.setenv("RAG_COLLECTION", "test_coll")

        called = {"url": None, "method": None}

        class _Resp:
            status = 200
            def read(self): return b""
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, timeout=None):
            called["url"] = req.full_url
            called["method"] = req.get_method()
            return _Resp()

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

        rc = u.main(["--yes", "--drop-collection"], out=lambda _s: None)
        assert rc == 0
        assert called["method"] == "DELETE"
        assert "test_coll" in called["url"]

    def test_drop_handles_404_cleanly(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "c"))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "s"))
        monkeypatch.setenv("THROUGHLINE_LOG_DIR", str(tmp_path / "l"))
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "r"))

        import io
        import urllib.error

        def fake_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(
                req.full_url, 404, "Not found", {}, io.BytesIO(b""))

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

        captured: list[str] = []
        rc = u.main(["--yes", "--drop-collection"], out=captured.append)
        assert rc == 0
        # Doesn't blow up; reports skip.
        text = " ".join(captured)
        assert "not found" in text or "skip" in text


class TestInteractivePrompts:
    def test_user_says_no_keeps_dir(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        (cfg_dir / "config.toml").write_text("x")
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "absent"))
        monkeypatch.setenv("THROUGHLINE_LOG_DIR", str(tmp_path / "absent2"))
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "absent3"))

        rc = u.main([],
                     reader=lambda _: "n",
                     out=lambda _s: None)
        assert rc == 0
        assert cfg_dir.exists()
        assert (cfg_dir / "config.toml").exists()


class TestMissingPathsAreNoOps:
    def test_no_dirs_exist_is_not_an_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "never"))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "never2"))
        monkeypatch.setenv("THROUGHLINE_LOG_DIR", str(tmp_path / "never3"))
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "never4"))

        captured: list[str] = []
        rc = u.main(["--yes"], out=captured.append)
        assert rc == 0
        text = " ".join(captured)
        # All four targets should report "skip".
        assert text.count("skip:") >= 4
