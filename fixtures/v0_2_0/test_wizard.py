"""Tests for the v0.2.0 install wizard skeleton (U14 + U24).

The skeleton itself is interactive, so these tests exercise the pure
pieces: config save/load round-trip, mission-branching step selection,
and the TOML value encoder.

Interactive step functions are verified by stubbing `input` via
monkeypatch; each step accepts the Enter-default, and the config
field under test ends up at its default value.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Make the repo root importable.
HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import config as cfg_mod
from throughline_cli.config import WizardConfig
from throughline_cli.wizard import (
    ALL_STEPS,
    effective_step_list,
    step_02_mission,
    step_03_vector_db,
    step_05_llm_provider,
    step_06_privacy,
    step_07_retrieval,
    step_09_import_source,
    step_11_refine_tier,
    step_12_card_structure,
)


# ----- Pure-function tests -----

class TestEffectiveStepList:
    def test_full_mission_runs_all_16(self):
        steps = effective_step_list("full")
        assert steps == list(range(1, 17))

    def test_rag_only_skips_card_structure_step(self):
        steps = effective_step_list("rag_only")
        assert 12 not in steps
        assert len(steps) == 15

    def test_notes_only_skips_rag_infra(self):
        steps = effective_step_list("notes_only")
        # vector_db (3), retrieval backend (7), import_scan (10) are skipped
        for s in (3, 7, 10):
            assert s not in steps
        assert len(steps) == 13


class TestTomlEncoder:
    def test_bool(self):
        assert cfg_mod._toml_value(True) == "true"
        assert cfg_mod._toml_value(False) == "false"

    def test_int_and_float(self):
        assert cfg_mod._toml_value(42) == "42"
        assert cfg_mod._toml_value(3.14) == "3.14"

    def test_none_is_empty_string(self):
        assert cfg_mod._toml_value(None) == '""'

    def test_string_with_quote_and_backslash(self):
        assert cfg_mod._toml_value('a"b\\c') == '"a\\"b\\\\c"'

    def test_list_of_strings(self):
        assert cfg_mod._toml_value(["x", "y"]) == '["x", "y"]'

    def test_unhandled_type_raises(self):
        with pytest.raises(TypeError):
            cfg_mod._toml_value({"k": "v"})


class TestConfigRoundtrip:
    def test_defaults_round_trip(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        cfg = WizardConfig()
        cfg.mission = "rag_only"
        cfg.daily_budget_usd = 12.5
        cfg.dial_sections = ["scenario", "summary"]
        p = cfg_mod.save(cfg)
        assert p.exists()
        loaded = cfg_mod.load()
        assert loaded.mission == "rag_only"
        assert loaded.daily_budget_usd == 12.5
        assert loaded.dial_sections == ["scenario", "summary"]

    def test_load_with_no_file_returns_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        cfg = cfg_mod.load()
        assert cfg.mission == "full"
        assert cfg.card_structure == "standard"


# ----- Step-function tests via monkeypatched input -----

def _stub_input(responses: list[str]):
    """Return a callable that returns responses in order, then raises."""
    it = iter(responses)

    def _fake_input(_prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise AssertionError(f"input() called more times than stubbed")
    return _fake_input


class TestMissionStep:
    def test_default_is_full(self, monkeypatch):
        cfg = WizardConfig()
        monkeypatch.setattr("builtins.input", _stub_input([""]))
        step_02_mission(cfg)
        assert cfg.mission == "full"
        assert cfg.card_structure == "standard"

    def test_rag_only_overrides_structure_and_tier(self, monkeypatch):
        cfg = WizardConfig()
        monkeypatch.setattr("builtins.input", _stub_input(["2"]))
        step_02_mission(cfg)
        assert cfg.mission == "rag_only"
        assert cfg.card_structure == "rag_optimized"
        assert cfg.refine_tier == "skim"

    def test_notes_only_blanks_rag_infra(self, monkeypatch):
        cfg = WizardConfig()
        monkeypatch.setattr("builtins.input", _stub_input(["3"]))
        step_02_mission(cfg)
        assert cfg.mission == "notes_only"
        assert cfg.vector_db == "none"
        assert cfg.embedder == "none"
        assert cfg.reranker == "none"


class TestVectorDbBranch:
    def test_skipped_for_notes_only(self, monkeypatch):
        cfg = WizardConfig()
        cfg.mission = "notes_only"
        # No input should be consumed, but prepare one just in case.
        monkeypatch.setattr("builtins.input", _stub_input([]))
        result = step_03_vector_db(cfg)
        assert result == "SKIPPED"

    def test_runs_for_full(self, monkeypatch):
        cfg = WizardConfig()
        cfg.mission = "full"
        monkeypatch.setattr("builtins.input", _stub_input([""]))
        step_03_vector_db(cfg)
        # Default for hybrid / cloud_max privacy is qdrant.
        assert cfg.vector_db == "qdrant"


class TestProviderAutoDerivesPromptFamily:
    @pytest.mark.parametrize("choice,expected", [
        ("1", "claude"),   # anthropic sonnet
        ("4", "gpt"),      # openai gpt-5-mini
        ("5", "gemini"),   # google gemini
        ("6", "generic"),  # xai grok
        ("7", "generic"),  # deepseek
    ])
    def test_family_derivation(self, monkeypatch, choice, expected):
        cfg = WizardConfig()
        monkeypatch.setattr("builtins.input", _stub_input([choice]))
        step_05_llm_provider(cfg)
        assert cfg.prompt_family == expected


class TestImportSourceColdStartLoop:
    def test_fresh_requires_explicit_confirm(self, monkeypatch):
        cfg = WizardConfig()
        cfg.mission = "full"
        # '5' = No, start fresh; 'y' = accept cold-start warning.
        monkeypatch.setattr("builtins.input", _stub_input(["5", "y"]))
        step_09_import_source(cfg)
        assert cfg.import_source == "none"
        assert cfg.import_path is None

    def test_fresh_with_n_loops_back(self, monkeypatch):
        cfg = WizardConfig()
        cfg.mission = "full"
        # '5' -> fresh, 'n' -> loop, then '1' -> chatgpt, path.
        monkeypatch.setattr(
            "builtins.input",
            _stub_input(["5", "n", "1", "~/Downloads/x.zip"]),
        )
        step_09_import_source(cfg)
        assert cfg.import_source == "chatgpt"
        assert cfg.import_path == "~/Downloads/x.zip"


class TestRagOnlyTierIsSkim:
    def test_tier_step_skipped_for_rag_only(self, monkeypatch):
        cfg = WizardConfig()
        cfg.mission = "rag_only"
        monkeypatch.setattr("builtins.input", _stub_input([]))
        result = step_11_refine_tier(cfg)
        assert result == "SKIPPED"

    def test_structure_step_skipped_for_rag_only(self, monkeypatch):
        cfg = WizardConfig()
        cfg.mission = "rag_only"
        monkeypatch.setattr("builtins.input", _stub_input([]))
        result = step_12_card_structure(cfg)
        assert result == "SKIPPED"


class TestStepRegistry:
    def test_exactly_16_steps(self):
        assert len(ALL_STEPS) == 16
        step_ids = [n for n, _ in ALL_STEPS]
        assert step_ids == list(range(1, 17))

    def test_all_callables(self):
        for _, fn in ALL_STEPS:
            assert callable(fn)
