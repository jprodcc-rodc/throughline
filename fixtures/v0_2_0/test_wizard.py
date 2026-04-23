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

    def test_fresh_with_n_loops_back(self, monkeypatch, tmp_path):
        cfg = WizardConfig()
        cfg.mission = "full"
        real = tmp_path / "export.zip"
        real.write_bytes(b"fake-zip-bytes")
        # '5' -> fresh, 'n' -> loop back to source picker,
        # '1' -> chatgpt, <real path> -> validated by step 9's new loop.
        monkeypatch.setattr(
            "builtins.input",
            _stub_input(["5", "n", "1", str(real)]),
        )
        step_09_import_source(cfg)
        assert cfg.import_source == "chatgpt"
        assert cfg.import_path == str(real)


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


# ---------- step 10 adapter integration ----------

class TestStep10AdapterIntegration:
    """Step 10 is where the wizard stops being a stub: real adapter
    dry-run is invoked on the user-provided export path. Tests use
    real tiny fixtures for each of the three adapters and verify the
    scan counters land on the config."""

    def _write_claude_jsonl(self, tmp_path):
        import json
        p = tmp_path / "claude.jsonl"
        p.write_text(json.dumps({
            "uuid": "a-1", "name": "Hi", "created_at": "2024-01-15T10:00:00Z",
            "chat_messages": [
                {"sender": "human", "text": "hello"},
                {"sender": "assistant", "text": "hi back"},
            ],
        }) + "\n", encoding="utf-8")
        return p

    def _write_chatgpt_json(self, tmp_path):
        import json
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps([{
            "id": "c-1", "title": "Hi",
            "create_time": 1705315200.0,
            "mapping": {
                "root": {"id": "root", "parent": None,
                          "children": ["u1"], "message": None},
                "u1": {"id": "u1", "parent": "root", "children": ["a1"],
                        "message": {"author": {"role": "user"},
                                    "content": {"content_type": "text",
                                                "parts": ["hello"]}}},
                "a1": {"id": "a1", "parent": "u1", "children": [],
                        "message": {"author": {"role": "assistant"},
                                    "content": {"content_type": "text",
                                                "parts": ["hi back"]}}},
            },
        }]), encoding="utf-8")
        return p

    def _write_gemini_json(self, tmp_path):
        import json
        p = tmp_path / "MyActivity.json"
        p.write_text(json.dumps([{
            "header": "Gemini Apps",
            "title": "Prompted hello",
            "time": "2024-01-15T10:00:00Z",
            "products": ["Gemini Apps"],
            "safeHtmlItem": [{"html": "<p>hi back</p>"}],
        }]), encoding="utf-8")
        return p

    def _patch_inputs(self, monkeypatch, responses):
        it = iter(responses)

        def fake_input(_prompt=""):
            return next(it)
        monkeypatch.setattr("builtins.input", fake_input)

    def test_step10_populates_config_for_claude(self, monkeypatch, tmp_path):
        from throughline_cli.wizard import step_10_import_scan
        cfg = WizardConfig()
        cfg.import_source = "claude"
        cfg.import_path = str(self._write_claude_jsonl(tmp_path))
        step_10_import_scan(cfg)
        assert cfg.import_scanned == 1
        assert cfg.import_emitted == 1
        assert cfg.import_est_tokens > 0
        assert cfg.import_est_normal_cost_usd >= 0
        assert cfg.import_est_skim_cost_usd <= cfg.import_est_normal_cost_usd

    def test_step10_populates_config_for_chatgpt(self, monkeypatch, tmp_path):
        from throughline_cli.wizard import step_10_import_scan
        cfg = WizardConfig()
        cfg.import_source = "chatgpt"
        cfg.import_path = str(self._write_chatgpt_json(tmp_path))
        step_10_import_scan(cfg)
        assert cfg.import_scanned == 1
        assert cfg.import_emitted == 1

    def test_step10_populates_config_for_gemini(self, monkeypatch, tmp_path):
        from throughline_cli.wizard import step_10_import_scan
        cfg = WizardConfig()
        cfg.import_source = "gemini"
        cfg.import_path = str(self._write_gemini_json(tmp_path))
        step_10_import_scan(cfg)
        # Gemini day-buckets: 1 event -> 1 day MD.
        assert cfg.import_scanned == 1
        assert cfg.import_emitted == 1

    def test_step10_skipped_for_none_source(self):
        from throughline_cli.wizard import step_10_import_scan
        cfg = WizardConfig()
        cfg.import_source = "none"
        result = step_10_import_scan(cfg)
        assert result == "SKIPPED"
        assert cfg.import_scanned == 0

    def test_step10_handles_bad_path_gracefully(self, tmp_path):
        """If the adapter raises (bad zip, missing file), the wizard
        should catch the exception and let the user continue — not
        crash the whole installer."""
        from throughline_cli.wizard import step_10_import_scan
        cfg = WizardConfig()
        cfg.import_source = "claude"
        cfg.import_path = str(tmp_path / "nonexistent.jsonl")
        # Must not raise.
        step_10_import_scan(cfg)
        assert cfg.import_scanned == 0
        assert cfg.import_emitted == 0


class TestStep9PathValidation:
    """Step 9 should loop back on bad paths rather than passing a
    broken path to step 10."""

    def test_valid_path_accepted(self, monkeypatch, tmp_path):
        from throughline_cli.wizard import step_09_import_source
        cfg = WizardConfig()
        cfg.mission = "full"
        real_path = tmp_path / "export.zip"
        real_path.write_bytes(b"fake")
        # '2' = Claude, then the path.
        monkeypatch.setattr("builtins.input",
                            _stub_input(["2", str(real_path)]))
        step_09_import_source(cfg)
        assert cfg.import_source == "claude"
        assert cfg.import_path == str(real_path.expanduser())

    def test_bad_path_retry_then_give_up_goes_to_fresh(self, monkeypatch,
                                                       tmp_path):
        """User enters bad path, says no-retry — wizard should switch
        import_source to 'none' and cold-start ask y/N. Default Y
        accepts cold start."""
        from throughline_cli.wizard import step_09_import_source
        cfg = WizardConfig()
        cfg.mission = "full"
        # '2' Claude, bad path, 'n' to retry, then cold-start warning
        # confirm (default Y from empty input).
        monkeypatch.setattr(
            "builtins.input",
            _stub_input(["2", "/nonexistent/foo.zip", "n"]),
        )
        step_09_import_source(cfg)
        assert cfg.import_source == "none"
        assert cfg.import_path is None

    def test_multiple_sources_defers_to_single_then_none(self, monkeypatch):
        """v0.2.0 doesn't support 'multiple' in-wizard; it should
        gracefully fall back to 'none' with a note about the manual
        follow-up command."""
        from throughline_cli.wizard import step_09_import_source
        cfg = WizardConfig()
        cfg.mission = "full"
        # '4' = Multiple, then cold-start confirm (default Y).
        monkeypatch.setattr(
            "builtins.input",
            _stub_input(["4"]),
        )
        step_09_import_source(cfg)
        assert cfg.import_source == "none"
