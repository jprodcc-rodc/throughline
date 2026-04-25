"""Tests for the cross-step validation warnings added to the wizard
post-2026-04-26 audit:

- Step 3: optional-dep proactive check (lancedb / chroma / sqlite-vec
  / duckdb-vss / pgvector all need a `pip install` before they work
  for real); pgvector additionally needs PGVECTOR_DSN/DATABASE_URL.
- Step 6: privacy=local_only + cloud LLM provider conflict.

These are warnings, not blocks — the wizard still saves config so
the user can opt in to the conflict knowingly. Tests verify the
warning is *visible*, not that it short-circuits.
"""
from __future__ import annotations

import builtins
import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# step_03 — optional-dep awareness
# ============================================================

class TestStep3OptionalDepCheck:
    def test_qdrant_no_dep_check(self):
        """qdrant uses stdlib urllib; nothing optional to check."""
        from throughline_cli import wizard
        available, hint = wizard._check_vector_db_available("qdrant")
        assert available is True
        assert hint == ""

    def test_lancedb_when_missing(self, monkeypatch):
        """When `lancedb` isn't importable, the helper reports it
        unavailable with a `pip install` hint."""
        real_import = builtins.__import__

        def guard(name, *a, **kw):
            if name in ("lancedb", "pyarrow"):
                raise ImportError("simulated")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        from throughline_cli import wizard
        available, hint = wizard._check_vector_db_available("lancedb")
        assert available is False
        assert "lancedb" in hint.lower()

    def test_sqlite_vec_when_missing(self, monkeypatch):
        real_import = builtins.__import__

        def guard(name, *a, **kw):
            if name == "sqlite_vec":
                raise ImportError("simulated")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        from throughline_cli import wizard
        available, hint = wizard._check_vector_db_available("sqlite_vec")
        assert available is False
        assert "sqlite-vec" in hint.lower() or "sqlite_vec" in hint.lower()

    def test_pgvector_when_missing(self, monkeypatch):
        real_import = builtins.__import__

        def guard(name, *a, **kw):
            if name == "psycopg":
                raise ImportError("simulated")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        from throughline_cli import wizard
        available, hint = wizard._check_vector_db_available("pgvector")
        assert available is False
        assert "psycopg" in hint.lower()

    def test_unknown_vector_db_no_hint(self):
        """For backends not in the dep map (e.g. qdrant, future
        plug-ins), the helper returns available=True / no hint."""
        from throughline_cli import wizard
        available, hint = wizard._check_vector_db_available("future_backend_x")
        assert available is True


# ============================================================
# step_06 — local_only + cloud-provider conflict
# ============================================================

class TestStep6PrivacyConflict:
    """Step 6 itself is interactive (calls pick_option). To test the
    warning logic we mirror the conditions and assert via the
    _LOCAL_PROVIDERS set + a fake ui that captures info_line calls."""

    def test_local_provider_set_includes_ollama_lm_studio_generic(self):
        from throughline_cli import wizard
        assert "ollama" in wizard._LOCAL_PROVIDERS
        assert "lm_studio" in wizard._LOCAL_PROVIDERS
        assert "generic" in wizard._LOCAL_PROVIDERS

    def test_cloud_providers_not_in_local_set(self):
        """Sanity: known cloud providers must NOT be in the local set,
        otherwise the conflict warning silently fails to fire."""
        from throughline_cli import wizard
        for cloud in ("openai", "anthropic", "openrouter", "deepseek",
                       "siliconflow", "moonshot"):
            assert cloud not in wizard._LOCAL_PROVIDERS, (
                f"{cloud!r} accidentally listed as local — "
                f"local_only conflict warning will be silenced.")

    def test_step6_warns_on_local_only_with_cloud_provider(self, monkeypatch,
                                                                 capsys):
        """End-to-end: with mocked pick_option returning local_only +
        cfg already at llm_provider=openai, step 6 must surface the
        conflict via ui.info_line."""
        from throughline_cli import wizard
        from throughline_cli.config import WizardConfig

        captured: list[str] = []
        monkeypatch.setattr(wizard.ui, "step_header",
                              lambda *a, **k: None)
        monkeypatch.setattr(wizard.ui, "pick_option",
                              lambda *a, **k: "local_only")
        monkeypatch.setattr(wizard.ui, "info_line",
                              lambda msg: captured.append(str(msg)))

        cfg = WizardConfig(llm_provider="openai")
        wizard.step_06_privacy(cfg)
        joined = "\n".join(captured)
        assert "Conflict" in joined or "local_only" in joined.lower()
        assert "openai" in joined or "cloud" in joined.lower()

    def test_step6_silent_on_local_only_with_ollama(self, monkeypatch):
        """The conflict shouldn't fire when both sides are local."""
        from throughline_cli import wizard
        from throughline_cli.config import WizardConfig

        captured: list[str] = []
        monkeypatch.setattr(wizard.ui, "step_header",
                              lambda *a, **k: None)
        monkeypatch.setattr(wizard.ui, "pick_option",
                              lambda *a, **k: "local_only")
        monkeypatch.setattr(wizard.ui, "info_line",
                              lambda msg: captured.append(str(msg)))

        cfg = WizardConfig(llm_provider="ollama")
        wizard.step_06_privacy(cfg)
        joined = "\n".join(captured)
        assert "Conflict" not in joined

    def test_step6_warns_on_cloud_max_with_local_provider(self, monkeypatch):
        """The inverse — cloud_max + local provider is a probable
        misconfiguration too."""
        from throughline_cli import wizard
        from throughline_cli.config import WizardConfig

        captured: list[str] = []
        monkeypatch.setattr(wizard.ui, "step_header",
                              lambda *a, **k: None)
        monkeypatch.setattr(wizard.ui, "pick_option",
                              lambda *a, **k: "cloud_max")
        monkeypatch.setattr(wizard.ui, "info_line",
                              lambda msg: captured.append(str(msg)))

        cfg = WizardConfig(llm_provider="ollama")
        wizard.step_06_privacy(cfg)
        joined = "\n".join(captured)
        assert "Heads-up" in joined or "ollama" in joined.lower()


# ============================================================
# step_03 — pgvector DSN check
# ============================================================

class TestStep3PgvectorDsnCheck:
    def test_pgvector_warns_when_dsn_unset(self, monkeypatch):
        """Picking pgvector without PGVECTOR_DSN or DATABASE_URL
        warns the user. Without this, the daemon happily writes to
        `postgresql://localhost/throughline` which crashes if no
        local Postgres is running."""
        from throughline_cli import wizard
        from throughline_cli.config import WizardConfig

        monkeypatch.delenv("PGVECTOR_DSN", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)

        captured: list[str] = []
        monkeypatch.setattr(wizard.ui, "step_header",
                              lambda *a, **k: None)
        monkeypatch.setattr(wizard.ui, "pick_option",
                              lambda *a, **k: "pgvector")
        monkeypatch.setattr(wizard.ui, "info_line",
                              lambda msg: captured.append(str(msg)))

        cfg = WizardConfig()
        wizard.step_03_vector_db(cfg)
        joined = "\n".join(captured)
        # Either the dep-missing warning or the DSN warning fires.
        # Both are valid signals the install isn't wired up.
        assert "PGVECTOR_DSN" in joined or "psycopg" in joined.lower()

    def test_pgvector_silent_when_dsn_set(self, monkeypatch):
        from throughline_cli import wizard
        from throughline_cli.config import WizardConfig

        monkeypatch.setenv("PGVECTOR_DSN", "postgresql://test/db")
        # Skip the dep check so we're isolated to the DSN logic.
        monkeypatch.setattr(wizard, "_check_vector_db_available",
                              lambda v: (True, ""))

        captured: list[str] = []
        monkeypatch.setattr(wizard.ui, "step_header",
                              lambda *a, **k: None)
        monkeypatch.setattr(wizard.ui, "pick_option",
                              lambda *a, **k: "pgvector")
        monkeypatch.setattr(wizard.ui, "info_line",
                              lambda msg: captured.append(str(msg)))

        cfg = WizardConfig()
        wizard.step_03_vector_db(cfg)
        joined = "\n".join(captured)
        assert "PGVECTOR_DSN" not in joined


# ============================================================
# step_03 — silent when chosen backend is fine
# ============================================================

class TestStep3NoFalsePositives:
    def test_qdrant_silent(self, monkeypatch):
        from throughline_cli import wizard
        from throughline_cli.config import WizardConfig

        captured: list[str] = []
        monkeypatch.setattr(wizard.ui, "step_header",
                              lambda *a, **k: None)
        monkeypatch.setattr(wizard.ui, "pick_option",
                              lambda *a, **k: "qdrant")
        monkeypatch.setattr(wizard.ui, "info_line",
                              lambda msg: captured.append(str(msg)))
        wizard.step_03_vector_db(WizardConfig())
        # Empty info_line stream — qdrant has no install gate.
        assert captured == []
