"""Tests for `python -m throughline_cli doctor`.

Each individual check is a pure function returning a CheckResult — so
the unit tests just call them with controlled env vars / tmp paths
and assert on the result shape. The runner (`run_all_checks`) and the
CLI exit code are tested via the public entry point.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import doctor as d


# ------- individual checks -------

class TestPythonVersion:
    def test_passes_on_311_plus(self):
        # We're running on >=3.11 in CI + dev, so this just exercises
        # the ok path.
        r = d.check_python_version()
        assert r.status == "ok"
        assert "Python" in r.detail


class TestRequiredImports:
    def test_all_present(self):
        # Test environment has the runtime deps installed.
        r = d.check_required_imports()
        assert r.status == "ok"


class TestOptionalImports:
    def test_returns_a_result(self):
        r = d.check_optional_imports()
        # Either ok (some present) or warn (none present).
        assert r.status in ("ok", "warn")
        assert "present" in r.detail


class TestConfigFile:
    def test_present(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text("mission = \"full\"\n",
                                                encoding="utf-8")
        r = d.check_config_file()
        assert r.status == "ok"

    def test_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "nope"))
        r = d.check_config_file()
        assert r.status == "fail"
        assert "install.py" in r.fix


class TestStateDir:
    def test_present(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        r = d.check_state_dir()
        assert r.status == "ok"

    def test_missing_warn(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "absent"))
        r = d.check_state_dir()
        assert r.status == "warn"


class TestQdrantReachable:
    def test_unreachable(self, monkeypatch):
        # Point at a port nothing is listening on.
        monkeypatch.setenv("QDRANT_URL", "http://127.0.0.1:1")
        r = d.check_qdrant_reachable()
        assert r.status == "fail"
        assert "docker run" in r.fix

    def test_reachable_via_mock(self, monkeypatch):
        class _Resp:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def read(self): return b""

        monkeypatch.setattr("urllib.request.urlopen",
                             lambda *a, **k: _Resp())
        monkeypatch.setenv("QDRANT_URL", "http://example.test")
        r = d.check_qdrant_reachable()
        assert r.status == "ok"


class TestRagServerReachable:
    def test_unreachable_is_warn(self, monkeypatch):
        """rag_server may legitimately not be running — warn, not fail."""
        monkeypatch.setenv("RAG_SERVER_URL", "http://127.0.0.1:1")
        r = d.check_rag_server_reachable()
        assert r.status == "warn"


class TestDaemonState:
    def test_recent(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        (tmp_path / "refine_state.json").write_text("{}", encoding="utf-8")
        r = d.check_daemon_state()
        assert r.status == "ok"

    def test_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        r = d.check_daemon_state()
        assert r.status == "warn"
        assert "refine_daemon.py" in r.fix

    def test_stale_file(self, tmp_path, monkeypatch):
        import os
        import time
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        f = tmp_path / "refine_state.json"
        f.write_text("{}", encoding="utf-8")
        # Backdate by 5 days.
        old = time.time() - 5 * 86400
        os.utime(f, (old, old))
        r = d.check_daemon_state()
        assert r.status == "warn"
        assert "stale" in r.detail


class TestEmbedderModelCache:
    def test_non_local_embedder_skips(self, monkeypatch):
        monkeypatch.setenv("EMBEDDER", "openai")
        r = d.check_embedder_model_cache()
        assert r.status == "ok"
        assert "no model download required" in r.detail

    def test_local_missing_warns(self, monkeypatch, tmp_path):
        monkeypatch.setenv("EMBEDDER", "bge-m3")
        monkeypatch.setenv("HF_HOME", str(tmp_path))
        r = d.check_embedder_model_cache()
        assert r.status == "warn"
        assert "huggingface-cli download" in r.fix

    def test_local_present(self, monkeypatch, tmp_path):
        monkeypatch.setenv("EMBEDDER", "bge-m3")
        monkeypatch.setenv("HF_HOME", str(tmp_path))
        (tmp_path / "hub" / "models--BAAI--bge-m3").mkdir(parents=True)
        r = d.check_embedder_model_cache()
        assert r.status == "ok"


class TestLlmProviderKey:
    """U28 · doctor check for provider key presence."""

    def _clear_keys(self, monkeypatch):
        from throughline_cli import providers as pr
        for preset in pr.list_presets():
            monkeypatch.delenv(preset.env_var, raising=False)
        monkeypatch.delenv("THROUGHLINE_LLM_PROVIDER", raising=False)

    def test_openrouter_key_set(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        self._clear_keys(monkeypatch)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or")
        r = d.check_llm_provider_key()
        assert r.status == "ok"
        assert "OpenRouter" in r.detail

    def test_siliconflow_key_set(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        self._clear_keys(monkeypatch)
        monkeypatch.setenv("SILICONFLOW_API_KEY", "sk-sf")
        r = d.check_llm_provider_key()
        assert r.status == "ok"
        assert "SiliconFlow" in r.detail
        assert "SILICONFLOW_API_KEY" in r.detail

    def test_no_key_warns_not_fails(self, tmp_path, monkeypatch):
        """Fresh install, no provider key yet — warn, don't fail,
        so the overall `doctor` exit code stays 0 on first run."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        self._clear_keys(monkeypatch)
        r = d.check_llm_provider_key()
        assert r.status == "warn"
        assert "not set" in r.detail

    def test_config_picks_provider_warn_missing_key(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text(
            'llm_provider = "moonshot"\n', encoding="utf-8")
        self._clear_keys(monkeypatch)
        r = d.check_llm_provider_key()
        assert r.status == "warn"
        assert "Moonshot" in r.detail
        assert "MOONSHOT_API_KEY" in r.fix

    def test_unknown_provider_id_warn(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        self._clear_keys(monkeypatch)
        monkeypatch.setenv("THROUGHLINE_LLM_PROVIDER", "typo-ai")
        r = d.check_llm_provider_key()
        # Unknown provider: active_provider.resolve_provider_id() returns
        # "typo-ai" as-is; the check flags it.
        assert r.status == "warn"


class TestTaxonomyObservations:
    def test_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        r = d.check_taxonomy_observations()
        assert r.status == "warn"

    def test_counts_rows(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        (tmp_path / "taxonomy_observations.jsonl").write_text(
            "{}\n{}\n{}\n", encoding="utf-8")
        r = d.check_taxonomy_observations()
        assert r.status == "ok"
        assert "3 observation" in r.detail


# ------- runner / CLI -------

class TestRunner:
    def test_run_all_returns_check_results(self):
        results = d.run_all_checks()
        assert len(results) == len(d.DEFAULT_CHECKS)
        for r in results:
            assert isinstance(r, d.CheckResult)
            assert r.status in ("ok", "warn", "fail")

    def test_custom_check_list(self):
        custom = [lambda: d.CheckResult("custom", "ok", "always passes")]
        results = d.run_all_checks(custom)
        assert len(results) == 1
        assert results[0].name == "custom"


class TestCli:
    def test_help(self, capsys):
        rc = d.main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "doctor" in out
        assert "--quiet" in out

    def test_unknown_arg(self, capsys):
        rc = d.main(["--zztop"])
        assert rc == 2

    def test_json_output_parses(self, capsys, tmp_path, monkeypatch):
        # Force two quick checks to keep test deterministic.
        monkeypatch.setattr(d, "DEFAULT_CHECKS", [
            lambda: d.CheckResult("a", "ok", "fine"),
            lambda: d.CheckResult("b", "fail", "broken", fix="run foo"),
        ])
        rc = d.main(["--json"])
        assert rc == 1  # at least one fail
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 2
        assert data[0]["name"] == "a"
        assert data[1]["fix"] == "run foo"

    def test_exit_code_0_when_all_pass(self, monkeypatch):
        monkeypatch.setattr(d, "DEFAULT_CHECKS", [
            lambda: d.CheckResult("ok-only", "ok"),
        ])
        rc = d.main([])
        assert rc == 0

    def test_exit_code_1_on_any_fail(self, monkeypatch):
        monkeypatch.setattr(d, "DEFAULT_CHECKS", [
            lambda: d.CheckResult("yes", "ok"),
            lambda: d.CheckResult("no", "fail", fix="x"),
        ])
        rc = d.main([])
        assert rc == 1

    def test_exit_code_0_when_only_warn(self, monkeypatch):
        """Warnings don't block. Otherwise CI would fail any time
        the rag_server isn't running, which is most of the time."""
        monkeypatch.setattr(d, "DEFAULT_CHECKS", [
            lambda: d.CheckResult("yes", "ok"),
            lambda: d.CheckResult("rag", "warn", fix="start it"),
        ])
        rc = d.main([])
        assert rc == 0
