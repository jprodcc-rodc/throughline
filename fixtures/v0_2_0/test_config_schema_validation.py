"""Tests for `throughline_cli.config.validate()` + the
`check_config_schema` doctor check.

Guarantees the validator surfaces:
  - typos / unknown fields (with suggestion when distance ≤ 2)
  - enum drift (value not in the known-values set)
  - gross type mismatches
... while leaving a clean config totally silent so it stays
zero-friction on normal runs.
"""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# =========================================================
# Core validator
# =========================================================

class TestValidateCleanConfig:
    def test_empty_dict_is_clean(self):
        from throughline_cli import config as cfg
        assert cfg.validate({}) == []

    def test_default_shape_is_clean(self):
        """A dict matching every default value should validate."""
        from throughline_cli import config as cfg
        from dataclasses import asdict
        clean = asdict(cfg.WizardConfig())
        assert cfg.validate(clean) == []


class TestValidateUnknownKeys:
    def test_typo_gets_suggestion(self):
        from throughline_cli import config as cfg
        # `dailey_budget_usd` is 2 chars from `daily_budget_usd`.
        issues = cfg.validate({"dailey_budget_usd": 5})
        assert len(issues) == 1
        assert issues[0].kind == "unknown_key"
        assert issues[0].key == "dailey_budget_usd"
        assert issues[0].suggestion == "daily_budget_usd"

    def test_completely_foreign_key_no_suggestion(self):
        from throughline_cli import config as cfg
        issues = cfg.validate({"xyzzy_foo_bar_baz": "value"})
        assert len(issues) == 1
        assert issues[0].kind == "unknown_key"
        # Too far from anything → no suggestion.
        assert issues[0].suggestion == ""

    def test_case_typo_gets_canonical_form(self):
        from throughline_cli import config as cfg
        issues = cfg.validate({"Mission": "full"})
        assert len(issues) == 1
        assert issues[0].suggestion == "mission"


class TestValidateEnumMismatch:
    def test_bad_privacy_value_caught(self):
        from throughline_cli import config as cfg
        issues = cfg.validate({"privacy": "cloudmax"})
        assert len(issues) == 1
        assert issues[0].kind == "enum_mismatch"
        assert issues[0].suggestion == "cloud_max"

    def test_bad_mission_value_caught(self):
        from throughline_cli import config as cfg
        issues = cfg.validate({"mission": "full_flywheel"})
        assert len(issues) == 1
        assert issues[0].kind == "enum_mismatch"
        # `full_flywheel` is beyond the suggestion-distance threshold;
        # the issue is still reported, just without a guess.
        assert issues[0].suggestion == ""

    def test_close_typo_mission_suggestion(self):
        """A close typo (edit distance ≤ 2) DOES produce a
        suggestion."""
        from throughline_cli import config as cfg
        issues = cfg.validate({"mission": "fulll"})
        assert len(issues) == 1
        assert issues[0].suggestion == "full"

    def test_good_enum_values_silent(self):
        from throughline_cli import config as cfg
        for v in ("local_only", "hybrid", "cloud_max"):
            assert cfg.validate({"privacy": v}) == []

    def test_lancedb_is_valid_vector_db(self):
        """Regression guard: LanceDB joined the vector_db set in
        v0.2.x. Make sure validation doesn't flag it."""
        from throughline_cli import config as cfg
        assert cfg.validate({"vector_db": "lancedb"}) == []


class TestValidateLLMProvider:
    """llm_provider is validated dynamically against the U28
    provider registry — not a static enum."""

    def test_known_provider_is_clean(self):
        from throughline_cli import config as cfg
        for pid in ("openrouter", "anthropic", "openai", "ollama"):
            assert cfg.validate({"llm_provider": pid}) == [], pid

    def test_typo_in_provider_suggested(self):
        from throughline_cli import config as cfg
        issues = cfg.validate({"llm_provider": "anthropc"})
        assert len(issues) == 1
        assert issues[0].kind == "enum_mismatch"
        assert issues[0].suggestion == "anthropic"

    def test_foreign_provider_flagged_without_suggestion(self):
        from throughline_cli import config as cfg
        issues = cfg.validate({"llm_provider": "mistral-direct"})
        # Not in the registry; too far from any known id for a
        # suggestion, but still flagged.
        assert len(issues) == 1
        assert issues[0].kind == "enum_mismatch"


class TestValidateTypeMismatch:
    def test_budget_as_string_flagged(self):
        from throughline_cli import config as cfg
        issues = cfg.validate({"daily_budget_usd": "twenty"})
        assert len(issues) == 1
        assert issues[0].kind == "type_mismatch"

    def test_int_where_float_expected_is_ok(self):
        """TOML distinguishes `20` from `20.0`, but semantically
        they're the same for budget purposes."""
        from throughline_cli import config as cfg
        assert cfg.validate({"daily_budget_usd": 20}) == []

    def test_bool_field_type_checked(self):
        from throughline_cli import config as cfg
        issues = cfg.validate({"dial_keep_verbatim": "true"})
        assert len(issues) == 1
        assert issues[0].kind == "type_mismatch"


class TestValidateMultipleIssues:
    def test_all_issues_reported(self):
        from throughline_cli import config as cfg
        issues = cfg.validate({
            "mission":         "full_flywheel",   # enum
            "dailey_budget_usd": 5,               # typo
            "privacy":         "local_only",      # clean
            "daily_budget_usd": "twenty",         # type
        })
        kinds = sorted(i.kind for i in issues)
        assert kinds == ["enum_mismatch", "type_mismatch", "unknown_key"]


# =========================================================
# Doctor integration
# =========================================================

def _write_cfg(tmp_path: Path, body: str) -> Path:
    d = tmp_path / ".throughline"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "config.toml"
    p.write_text(body, encoding="utf-8")
    return p


class TestDoctorConfigSchemaCheck:
    def test_missing_file_warns(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "empty"))
        from throughline_cli import doctor
        r = doctor.check_config_schema()
        assert r.status == "warn"
        assert "no config" in r.detail.lower() or "nothing" in r.detail.lower()

    def test_clean_config_passes(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / ".throughline"))
        _write_cfg(tmp_path, '''\
mission = "full"
vector_db = "qdrant"
privacy = "hybrid"
daily_budget_usd = 20.0
''')
        from throughline_cli import doctor
        r = doctor.check_config_schema()
        assert r.status == "ok"

    def test_typo_key_warns(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / ".throughline"))
        _write_cfg(tmp_path, 'dailey_budget_usd = 5\n')
        from throughline_cli import doctor
        r = doctor.check_config_schema()
        assert r.status == "warn"
        assert "unknown_key" in r.detail or "dailey" in r.fix
        assert "daily_budget_usd" in r.fix  # suggestion landed

    def test_bad_enum_warns_with_suggestion(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / ".throughline"))
        _write_cfg(tmp_path, 'privacy = "cloudmax"\n')
        from throughline_cli import doctor
        r = doctor.check_config_schema()
        assert r.status == "warn"
        assert "enum_mismatch" in r.detail or "privacy" in r.detail
        assert "cloud_max" in r.fix

    def test_unparseable_toml_fails(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / ".throughline"))
        _write_cfg(tmp_path, 'this is { not valid TOML [\n')
        from throughline_cli import doctor
        r = doctor.check_config_schema()
        assert r.status == "fail"

    def test_check_is_registered(self):
        """`check_config_schema` must be in DEFAULT_CHECKS so it
        fires on every doctor run."""
        from throughline_cli import doctor
        names = [c.__name__ for c in doctor.DEFAULT_CHECKS]
        assert "check_config_schema" in names
