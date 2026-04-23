"""Tests for U27.1 — minimal skeletal taxonomy + wizard step 14 defaults.

Covers:
- config/taxonomy.minimal.py loads as a Python module and exposes
  the VALID_X_SET / VALID_Y_SET / VALID_Z_SET constants in the
  expected shape.
- Step 14 default selection honours the card-count heuristic:
  - no imports / zero cards -> minimal (U27 path)
  - large import (>= 100 cards emitted) -> derive_from_imports (U13)
  - small import -> minimal (growth-path preferred over weak U13)
- Minimal set is tight (<= 5 x-domains) so future growth has room.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli.config import WizardConfig
from throughline_cli.wizard import step_14_taxonomy


# ---- taxonomy.minimal.py structural tests ----

class TestMinimalModule:
    def _load(self):
        p = REPO_ROOT / "config" / "taxonomy.minimal.py"
        spec = importlib.util.spec_from_file_location("taxonomy_minimal", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_loads_cleanly(self):
        m = self._load()
        assert hasattr(m, "VALID_X_SET")
        assert hasattr(m, "VALID_Y_SET")
        assert hasattr(m, "VALID_Z_SET")

    def test_x_is_tight_enough_to_grow(self):
        """The whole point is room for growth. <=5 X-domains; above
        that we're no longer a 'skeletal starter'."""
        m = self._load()
        assert isinstance(m.VALID_X_SET, set)
        assert len(m.VALID_X_SET) <= 5

    def test_contains_misc_catchall(self):
        """Misc is load-bearing for the observer: cards that land
        here are the strongest growth signal. Don't drop it from the
        skeleton."""
        m = self._load()
        assert "Misc" in m.VALID_X_SET

    def test_y_and_z_non_empty(self):
        m = self._load()
        assert len(m.VALID_Y_SET) >= 3
        assert len(m.VALID_Z_SET) >= 2

    def test_values_are_str(self):
        m = self._load()
        for s in (m.VALID_X_SET, m.VALID_Y_SET, m.VALID_Z_SET):
            for item in s:
                assert isinstance(item, str)
                assert item.strip()


# ---- wizard step 14 default selection ----

def _stub_input(responses):
    it = iter(responses)

    def _fake_input(_prompt=""):
        return next(it)
    return _fake_input


class TestStep14Defaults:
    def test_default_minimal_on_cold_start(self, monkeypatch):
        cfg = WizardConfig()
        cfg.import_source = "none"
        cfg.import_emitted = 0
        # Empty input → takes the default. Expect minimal.
        monkeypatch.setattr("builtins.input", _stub_input([""]))
        step_14_taxonomy(cfg)
        assert cfg.taxonomy_source == "minimal"

    def test_default_minimal_on_small_import(self, monkeypatch):
        cfg = WizardConfig()
        cfg.import_source = "claude"
        cfg.import_emitted = 40  # < 100 threshold
        monkeypatch.setattr("builtins.input", _stub_input([""]))
        step_14_taxonomy(cfg)
        assert cfg.taxonomy_source == "minimal"

    def test_default_derive_on_large_import(self, monkeypatch):
        cfg = WizardConfig()
        cfg.import_source = "chatgpt"
        cfg.import_emitted = 250  # above 100 threshold
        monkeypatch.setattr("builtins.input", _stub_input([""]))
        step_14_taxonomy(cfg)
        assert cfg.taxonomy_source == "derive_from_imports"

    def test_explicit_minimal_choice(self, monkeypatch):
        cfg = WizardConfig()
        cfg.import_source = "chatgpt"
        cfg.import_emitted = 5000  # would default to derive, but user picks minimal
        # '1' = Minimal starter (now first in the list).
        monkeypatch.setattr("builtins.input", _stub_input(["1"]))
        step_14_taxonomy(cfg)
        assert cfg.taxonomy_source == "minimal"

    def test_explicit_derive_choice(self, monkeypatch):
        cfg = WizardConfig()
        cfg.import_source = "none"
        cfg.import_emitted = 0  # cold start, would default to minimal
        # '2' = Derive from vault.
        monkeypatch.setattr("builtins.input", _stub_input(["2"]))
        step_14_taxonomy(cfg)
        assert cfg.taxonomy_source == "derive_from_vault"

    def test_fallback_template_choice(self, monkeypatch):
        cfg = WizardConfig()
        # '4' = JD template (after minimal/derive_vault/derive_imports).
        monkeypatch.setattr("builtins.input", _stub_input(["4"]))
        step_14_taxonomy(cfg)
        assert cfg.taxonomy_source == "jd"


# ---- config default ----

class TestConfigDefault:
    def test_wizardconfig_default_is_minimal(self):
        """Fresh config with no wizard run should default to minimal
        — it's the safest starting point for unknown users."""
        cfg = WizardConfig()
        assert cfg.taxonomy_source == "minimal"
