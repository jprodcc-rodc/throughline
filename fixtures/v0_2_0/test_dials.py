"""Tests for U23 — 5-dial preview-edit panel + shared dial renderer.

Covers:
- `daemon.dials.Dials` defaults + `is_default()`.
- `load_dials_from_config()` reads config.toml and falls back
  gracefully on every kind of corruption.
- `render_dial_modifier()` — empty when defaults, structured text
  when any dial is non-default.
- Wizard `_dial_panel()` drives cfg via monkeypatched input().
- End-to-end: wizard save → daemon dial load round-trip.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from daemon import dials as d
from throughline_cli.config import WizardConfig


# ------- Dials dataclass -------

class TestDialsDefaults:
    def test_default_fields(self):
        x = d.Dials()
        assert x.tone == "neutral"
        assert x.length == "medium"
        assert x.register == "technical"
        assert x.keep_verbatim is False
        assert sorted(x.sections) == sorted(d.ALL_SECTIONS)

    def test_is_default_true_for_defaults(self):
        assert d.Dials().is_default() is True

    def test_is_default_false_when_any_tweaked(self):
        for tweak in [
            d.Dials(tone="formal"),
            d.Dials(length="short"),
            d.Dials(register="eli5"),
            d.Dials(keep_verbatim=True),
            d.Dials(sections=["scenario"]),
        ]:
            assert tweak.is_default() is False


# ------- render_dial_modifier -------

class TestRenderDialModifier:
    def test_empty_when_defaults(self):
        assert d.render_dial_modifier(d.Dials()) == ""

    def test_none_arg_treated_as_defaults(self):
        assert d.render_dial_modifier(None) == ""

    def test_tone_injects_text(self):
        txt = d.render_dial_modifier(d.Dials(tone="casual"))
        assert "<user_dials>" in txt
        assert "casual" in txt.lower()

    def test_length_injects_bounds(self):
        txt = d.render_dial_modifier(d.Dials(length="short"))
        assert "500" in txt  # short = < 500 chars

    def test_register_eli5(self):
        txt = d.render_dial_modifier(d.Dials(register="eli5"))
        assert "analog" in txt.lower() or "everyday" in txt.lower()

    def test_keep_verbatim_mentions_literal(self):
        txt = d.render_dial_modifier(d.Dials(keep_verbatim=True))
        assert "verbatim" in txt.lower() or "literal" in txt.lower()

    def test_sections_lists_kept_and_dropped(self):
        kept_only = d.Dials(sections=["scenario", "core_knowledge"])
        txt = d.render_dial_modifier(kept_only)
        assert "Scene & Pain Point" in txt
        # dropped sections also spelled out so refiner doesn't try
        # to slip them in anyway
        assert "Length Summary" in txt

    def test_wraps_in_user_dials_tag(self):
        """The daemon's Claude-family base prompt uses XML tags; our
        modifier must match the style so prompt parsing stays clean."""
        txt = d.render_dial_modifier(d.Dials(tone="formal"))
        assert txt.startswith("\n<user_dials>") or "<user_dials>" in txt
        assert "</user_dials>" in txt


# ------- load_dials_from_config -------

def _write_toml(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class TestLoadDialsFromConfig:
    def test_missing_file_returns_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "none"))
        assert d.load_dials_from_config().is_default()

    def test_reads_all_fields(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        _write_toml(cfg_dir / "config.toml",
            'dial_tone = "formal"\n'
            'dial_length = "long"\n'
            'dial_register = "eli5"\n'
            'dial_keep_verbatim = true\n'
            'dial_sections = ["scenario", "summary"]\n')
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        loaded = d.load_dials_from_config()
        assert loaded.tone == "formal"
        assert loaded.length == "long"
        assert loaded.register == "eli5"
        assert loaded.keep_verbatim is True
        assert loaded.sections == ["scenario", "summary"]

    def test_invalid_tone_falls_back(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        _write_toml(cfg_dir / "config.toml", 'dial_tone = "shouty"\n')
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        # Invalid value → default retained.
        assert d.load_dials_from_config().tone == "neutral"

    def test_unknown_section_pruned(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        _write_toml(cfg_dir / "config.toml",
                    'dial_sections = ["scenario", "bogus", "summary"]\n')
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        loaded = d.load_dials_from_config()
        assert loaded.sections == ["scenario", "summary"]

    def test_empty_section_list_keeps_default(self, tmp_path, monkeypatch):
        """An empty list would drop ALL sections → schema breaks.
        Loader retains the default 6 in that case."""
        cfg_dir = tmp_path / "cfg"
        _write_toml(cfg_dir / "config.toml",
                    'dial_sections = []\n')
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        assert sorted(d.load_dials_from_config().sections) == \
               sorted(d.ALL_SECTIONS)

    def test_malformed_toml_returns_defaults(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        _write_toml(cfg_dir / "config.toml", "[not valid\n")
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(cfg_dir))
        assert d.load_dials_from_config().is_default()


# ------- Wizard _dial_panel integration -------

class TestWizardDialPanel:
    def _stub_input(self, monkeypatch, answers):
        it = iter(answers)
        monkeypatch.setattr("builtins.input", lambda _="": next(it))

    def test_all_defaults_pressed(self, monkeypatch):
        """Enter-Enter-Enter keeps existing cfg values."""
        from throughline_cli.wizard import _dial_panel
        cfg = WizardConfig()
        # pick_option accepts "" to take default; ask_yes_no accepts ""
        # to take default. Feed 5 empties + the "drop sections?" prompt.
        self._stub_input(monkeypatch, ["", "", "", "", ""])
        _dial_panel(cfg)
        # Nothing changed.
        assert cfg.dial_tone == "neutral"
        assert cfg.dial_length == "medium"
        assert cfg.dial_register == "technical"
        assert cfg.dial_keep_verbatim is False
        assert sorted(cfg.dial_sections) == sorted(d.ALL_SECTIONS)

    def test_tone_flipped(self, monkeypatch):
        from throughline_cli.wizard import _dial_panel
        cfg = WizardConfig()
        # tone=1 (formal), length default, register default,
        # keep_verbatim default, drop-sections? no.
        self._stub_input(monkeypatch, ["1", "", "", "", ""])
        _dial_panel(cfg)
        assert cfg.dial_tone == "formal"

    def test_keep_verbatim_flipped(self, monkeypatch):
        from throughline_cli.wizard import _dial_panel
        cfg = WizardConfig()
        # tone default, length default, register default,
        # keep_verbatim=y, drop-sections? no.
        self._stub_input(monkeypatch, ["", "", "", "y", ""])
        _dial_panel(cfg)
        assert cfg.dial_keep_verbatim is True

    def test_section_dropping(self, monkeypatch):
        """Drop-sections=yes → per-section loop keeps 'y' sections only."""
        from throughline_cli.wizard import _dial_panel
        cfg = WizardConfig()
        # 4 dial Enters, drop-sections=y, then 6 section keep/drop answers:
        # keep scenario(y), drop core(n), keep execution(y), drop avoid(n),
        # keep insight(y), drop summary(n).
        self._stub_input(monkeypatch,
                          ["", "", "", "",            # tone/len/reg/verbatim
                           "y",                        # drop sections?
                           "y", "n", "y", "n", "y", "n"])  # 6 sections
        _dial_panel(cfg)
        assert cfg.dial_sections == ["scenario", "execution", "insight"]

    def test_all_sections_dropped_retains_current(self, monkeypatch):
        """Refusing every section would break the schema — loader keeps
        the current selection instead."""
        from throughline_cli.wizard import _dial_panel
        cfg = WizardConfig()
        original = list(cfg.dial_sections)
        self._stub_input(monkeypatch,
                          ["", "", "", "",
                           "y",
                           "n", "n", "n", "n", "n", "n"])
        _dial_panel(cfg)
        assert cfg.dial_sections == original


# ------- Wizard save → daemon load round-trip -------

class TestRoundTrip:
    def test_wizard_values_reach_daemon(self, tmp_path, monkeypatch):
        """User tweaks dials, config saves; daemon on next refine reads
        the same file and the modifier reflects the change."""
        from throughline_cli import config as cfgmod
        cfg = WizardConfig()
        cfg.dial_tone = "casual"
        cfg.dial_length = "short"
        cfg.dial_keep_verbatim = True
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        cfgmod.save(cfg)
        # Daemon-side load.
        loaded = d.load_dials_from_config()
        assert loaded.tone == "casual"
        assert loaded.length == "short"
        assert loaded.keep_verbatim is True
        tail = d.render_dial_modifier(loaded)
        assert "casual" in tail.lower()
        assert "500" in tail  # short length bound
        assert "verbatim" in tail.lower() or "literal" in tail.lower()
