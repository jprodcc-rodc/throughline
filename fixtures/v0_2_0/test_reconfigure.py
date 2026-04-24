"""Tests for wizard --reconfigure mode (issue #8).

Covers:
- _parse_step_selection accepts `5`, `5,7`, `9-13`, `5,9-13,15`,
  rejects garbage.
- main() short-circuits to --step N when given (existing behaviour).
- main() detects existing config.toml and shows the picker.
- main() with --force skips the picker and runs the full flow.
- main() with --reconfigure forces the picker even on fresh installs.
- run_wizard(step_filter=[...]) runs only the picked steps.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


def _stub_input(responses):
    it = iter(responses)

    def _fake(_prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise AssertionError(
                f"input() called more than {len(responses)} times"
            )
    return _fake


class TestParseStepSelection:
    def test_single(self):
        from throughline_cli.wizard import _parse_step_selection
        assert _parse_step_selection("5") == [5]

    def test_csv(self):
        from throughline_cli.wizard import _parse_step_selection
        assert _parse_step_selection("5,7,11") == [5, 7, 11]

    def test_range(self):
        from throughline_cli.wizard import _parse_step_selection
        assert _parse_step_selection("9-13") == [9, 10, 11, 12, 13]

    def test_mixed(self):
        from throughline_cli.wizard import _parse_step_selection
        assert _parse_step_selection("5,9-13,15") == [5, 9, 10, 11, 12, 13, 15]

    def test_dedup_and_sort(self):
        from throughline_cli.wizard import _parse_step_selection
        # 9-11 overlaps with 10,11; output is sorted unique.
        assert _parse_step_selection("11,9-11,10") == [9, 10, 11]

    def test_whitespace_tolerated(self):
        from throughline_cli.wizard import _parse_step_selection
        assert _parse_step_selection(" 5 , 7 ") == [5, 7]

    def test_out_of_range_silently_dropped(self):
        from throughline_cli.wizard import _parse_step_selection
        # 99 is out of [1, 16]; silently dropped so copy-paste
        # errors don't fail outright.
        assert _parse_step_selection("5,99,7") == [5, 7]

    def test_empty_raises(self):
        from throughline_cli.wizard import _parse_step_selection
        with pytest.raises(ValueError):
            _parse_step_selection("")

    def test_only_out_of_range_raises(self):
        from throughline_cli.wizard import _parse_step_selection
        with pytest.raises(ValueError):
            _parse_step_selection("99,100")

    def test_garbage_raises(self):
        from throughline_cli.wizard import _parse_step_selection
        with pytest.raises(ValueError):
            _parse_step_selection("abc")

    def test_descending_range_raises(self):
        from throughline_cli.wizard import _parse_step_selection
        with pytest.raises(ValueError):
            _parse_step_selection("13-9")


class TestMainDispatch:
    def test_help_still_works(self, capsys):
        from throughline_cli.wizard import main
        rc = main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "--reconfigure" in out
        assert "--force" in out

    def test_step_N_shortcircuits_picker(self, tmp_path, monkeypatch):
        """If the user passes --step N, picker must NOT appear — their
        intent is already explicit."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text(
            'mission = "full"\n'
            'llm_provider = "openrouter"\n',
            encoding="utf-8",
        )
        # If picker ran, input() would be consumed. Provide none.
        called = {"run": None}

        def _fake_run(cfg=None, only_step=None, step_filter=None):
            called["run"] = (only_step, step_filter)
            return cfg

        from throughline_cli import wizard
        monkeypatch.setattr(wizard, "run_wizard", _fake_run)
        rc = wizard.main(["--step", "5"])
        assert rc == 0
        assert called["run"] == (5, None)

    def test_force_skips_picker_runs_full(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text(
            'mission = "full"\n'
            'llm_provider = "openrouter"\n',
            encoding="utf-8",
        )

        def _fake_run(cfg=None, only_step=None, step_filter=None):
            assert only_step is None
            assert step_filter is None  # full run
            return cfg

        from throughline_cli import wizard
        monkeypatch.setattr(wizard, "run_wizard", _fake_run)
        rc = wizard.main(["--force"])
        assert rc == 0

    def test_reconfigure_picker_pick_specific(self, tmp_path, monkeypatch):
        """User picks option 1 (pick specific steps), enters '5,15'."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text(
            'mission = "full"\n'
            'llm_provider = "openrouter"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr("builtins.input", _stub_input(["1", "5,15"]))

        captured = {}

        def _fake_run(cfg=None, only_step=None, step_filter=None):
            captured["step_filter"] = step_filter
            return cfg

        from throughline_cli import wizard
        monkeypatch.setattr(wizard, "run_wizard", _fake_run)
        rc = wizard.main([])
        assert rc == 0
        # Picker auto-appends step 16 so save() always runs.
        assert captured["step_filter"] == [5, 15, 16]

    def test_reconfigure_picker_pick_all(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text(
            'mission = "full"\n'
            'llm_provider = "openrouter"\n',
            encoding="utf-8",
        )
        # Choice "2" = run all 16.
        monkeypatch.setattr("builtins.input", _stub_input(["2"]))

        captured = {}

        def _fake_run(cfg=None, only_step=None, step_filter=None):
            captured["step_filter"] = step_filter
            return cfg

        from throughline_cli import wizard
        monkeypatch.setattr(wizard, "run_wizard", _fake_run)
        rc = wizard.main([])
        assert rc == 0
        # "Run all" collapses to a full run (no step_filter).
        assert captured["step_filter"] is None

    def test_reconfigure_picker_cancel(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text(
            'mission = "full"\n'
            'llm_provider = "openrouter"\n',
            encoding="utf-8",
        )
        # "4" = cancel.
        monkeypatch.setattr("builtins.input", _stub_input(["4"]))

        def _fake_run_should_not_be_called(*a, **k):
            raise AssertionError("run_wizard called after user cancelled")

        from throughline_cli import wizard
        monkeypatch.setattr(wizard, "run_wizard",
                             _fake_run_should_not_be_called)
        rc = wizard.main([])
        assert rc == 0  # clean exit

    def test_reconfigure_picker_bad_input_loops(self, tmp_path, monkeypatch):
        """Invalid selection text should prompt again, not crash."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        (tmp_path / "config.toml").write_text(
            'mission = "full"\n'
            'llm_provider = "openrouter"\n',
            encoding="utf-8",
        )
        # Pick specific (1), then garbage ("abc"), then valid ("7").
        monkeypatch.setattr(
            "builtins.input",
            _stub_input(["1", "abc", "7"]),
        )

        captured = {}

        def _fake_run(cfg=None, only_step=None, step_filter=None):
            captured["step_filter"] = step_filter
            return cfg

        from throughline_cli import wizard
        monkeypatch.setattr(wizard, "run_wizard", _fake_run)
        rc = wizard.main([])
        assert rc == 0
        assert captured["step_filter"] == [7, 16]  # +16 auto-appended

    def test_fresh_install_skips_picker(self, tmp_path, monkeypatch):
        """No existing config.toml and no --reconfigure flag -> picker
        must not run. Picker would hang on input() if called here."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / "never-existed"))

        def _fake_run(cfg=None, only_step=None, step_filter=None):
            assert step_filter is None
            return cfg

        from throughline_cli import wizard
        monkeypatch.setattr(wizard, "run_wizard", _fake_run)
        rc = wizard.main([])
        assert rc == 0

    def test_reconfigure_flag_forces_picker_on_fresh_install(self, tmp_path, monkeypatch):
        """Even with no existing config, --reconfigure should bring
        the picker up (user knows what they're doing)."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / "fresh"))
        # Choice 4 = cancel, just confirm the picker ran.
        monkeypatch.setattr("builtins.input", _stub_input(["4"]))

        from throughline_cli import wizard
        monkeypatch.setattr(wizard, "run_wizard",
                             lambda *a, **k: None)
        rc = wizard.main(["--reconfigure"])
        assert rc == 0


class TestRunWizardStepFilter:
    """run_wizard() with step_filter= must run ONLY those steps."""

    def test_step_filter_runs_only_listed_steps(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        monkeypatch.setattr("builtins.input", _stub_input([""] * 20))

        # Replace every step function with a tracker so we can see
        # which ones actually executed.
        from throughline_cli import wizard
        tracker: list[int] = []

        def _make_tracker(n):
            def _fn(cfg):
                tracker.append(n)
                return None
            return _fn

        patched_steps = [(n, _make_tracker(n)) for n, _ in wizard.ALL_STEPS]
        monkeypatch.setattr(wizard, "ALL_STEPS", patched_steps)

        wizard.run_wizard(step_filter=[5, 15])

        assert tracker == [5, 15]

    def test_step_filter_empty_runs_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))
        from throughline_cli import wizard
        tracker: list[int] = []

        def _make_tracker(n):
            def _fn(cfg):
                tracker.append(n)
                return None
            return _fn

        patched_steps = [(n, _make_tracker(n)) for n, _ in wizard.ALL_STEPS]
        monkeypatch.setattr(wizard, "ALL_STEPS", patched_steps)

        wizard.run_wizard(step_filter=[])
        assert tracker == []
