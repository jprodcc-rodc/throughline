"""Tests for the wizard's "← Back to previous step" feature.

User-asked: "需要加一个返回上一步的功能" — mid-wizard back nav so a
user who realizes at step 7 they want to change step 3 doesn't
have to Ctrl+C and start over.

Implementation:
- `ui.BackRequest` — exception type. Raised by `pick_option(...,
  show_back=True)` when the user picks the prepended "← Back" entry.
- Orchestrator (`run_wizard`) catches `BackRequest` and rewinds the
  step pointer by 1.
- Steps 3-14 (the major picker steps) opt into `show_back=True`;
  step 2 (the first interactive step) does not (nothing to go
  back to).
- At the first active step, BackRequest re-fires that step instead
  of unwinding past index 0.
"""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# Unit: ui.pick_option with show_back raises BackRequest
# ============================================================

class TestPickOptionRaisesBack:
    def test_back_choice_raises_backrequest(self, monkeypatch):
        """When show_back=True and the user picks the back entry
        (numeric position 1 in the legacy picker), pick_option
        raises BackRequest instead of returning a key."""
        from throughline_cli import ui
        # Position '1' in the legacy picker = the prepended back entry.
        monkeypatch.setattr("builtins.input", lambda *_: "1")
        try:
            ui.pick_option(
                "Pick:",
                [("a", "Alpha", ""), ("b", "Bravo", "")],
                default_key="a",
                show_back=True,
            )
            raise AssertionError("expected BackRequest")
        except ui.BackRequest:
            pass  # expected

    def test_normal_choice_returns_key(self, monkeypatch):
        """Picking any non-back entry returns the key normally —
        back is opt-in via the prepended entry, not a side effect."""
        from throughline_cli import ui
        # Position '2' = Alpha (back is at 1, then options).
        monkeypatch.setattr("builtins.input", lambda *_: "2")
        result = ui.pick_option(
            "Pick:",
            [("a", "Alpha", ""), ("b", "Bravo", "")],
            default_key="a",
            show_back=True,
        )
        assert result == "a"

    def test_show_back_default_is_off(self, monkeypatch):
        """Existing call sites that don't pass show_back must NOT
        get a back entry — backward compatibility with the 50+
        wizard-input mocks that pre-date this feature."""
        from throughline_cli import ui
        monkeypatch.setattr("builtins.input", lambda *_: "1")
        # No show_back arg — default False, no back entry prepended.
        result = ui.pick_option(
            "Pick:",
            [("a", "Alpha", ""), ("b", "Bravo", "")],
            default_key="a",
        )
        assert result == "a"


# ============================================================
# Integration: run_wizard rewinds on BackRequest
# ============================================================

class TestRunWizardRewinds:
    def _make_mock_ui(self):
        """Mock ui that captures every step entry and returns
        scripted answers for pick_option."""
        from throughline_cli.ui import BackRequest as _Br

        captured: list[str] = []

        class _Mock:
            BackRequest = _Br  # mirror real attr (alias to avoid shadow)

            def step_header(self, step, total, title):
                captured.append(f"STEP_{step}_{title}")

            def banner(self): pass
            def info_line(self, *a, **k): pass
            def warn_box(self, *a, **k): pass
            def panel_example(self, *a, **k): pass
            def kv_row(self, *a, **k): pass
            def summary_tree(self, *a, **k): pass
            def section_title(self, *a, **k): pass
            def progress_ticker(self, *a, **k): pass
            def print_blank(self): pass
            def subrule(self, *a, **k): pass
            def intro(self, *a, **k): pass
            def ask_text(self, q, default=""): return default
            def ask_yes_no(self, q, default=True): return default

            def status(self, msg):
                class _Null:
                    def __enter__(s): return s
                    def __exit__(s, *e): return False
                    def update(s, m): pass
                return _Null()

            class _Console:
                def print(self, *a, **k): pass

            console = _Console()

            # The interesting mock: pick_option raises BackRequest
            # the FIRST time step 4 fires, then returns the default
            # on all subsequent calls. Models a user who lands on
            # step 4, presses back, ends up on step 3, then walks
            # forward again.
            _step_4_first_call = True

            def pick_option(self, prompt, options, default_key,
                              show_back=False):
                if "LLM provider" in prompt and self._step_4_first_call:
                    self._step_4_first_call = False
                    if show_back:
                        raise _Br()
                return default_key

        return _Mock(), captured

    def test_back_at_step_4_returns_to_step_3(self, tmp_path, monkeypatch):
        """Walk full wizard. Step 4's first invocation raises
        BackRequest; orchestrator rewinds to step 3; step 4 re-fires
        and this time returns the default. Net effect: step 3 was
        visited TWICE."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        for mod in list(sys.modules):
            if mod in ("throughline_cli.wizard",
                        "throughline_cli.config"):
                del sys.modules[mod]

        from throughline_cli import wizard as wiz
        from throughline_cli.config import WizardConfig

        mock, captured = self._make_mock_ui()
        monkeypatch.setattr(wiz, "ui", mock)

        wiz.run_wizard(cfg=WizardConfig(import_source="none"),
                        dry_run=True)

        # Step 3 must have fired at least twice (once before back,
        # once after re-entering forward).
        step_3_visits = [c for c in captured if c.startswith("STEP_3_")]
        assert len(step_3_visits) >= 2, (
            f"expected step 3 to fire twice (initial + after back), "
            f"got {len(step_3_visits)}: {captured}")

    def test_back_at_first_active_step_re_fires(self, tmp_path, monkeypatch):
        """If BackRequest fires at step 0 (the first active step),
        the orchestrator can't rewind further — instead it logs an
        info note and re-fires the same step. Verified by running
        only_step=3 + having step 3 raise BackRequest once."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        for mod in list(sys.modules):
            if mod in ("throughline_cli.wizard",
                        "throughline_cli.config"):
                del sys.modules[mod]

        from throughline_cli import wizard as wiz
        from throughline_cli.ui import BackRequest as _Br
        from throughline_cli.config import WizardConfig

        captured: list[str] = []
        first_call = {"v": True}

        class _Mock:
            BackRequest = _Br

            def step_header(self, step, total, title):
                captured.append(f"STEP_{step}")

            def banner(self): pass
            def info_line(self, *a, **k): pass
            def warn_box(self, *a, **k): pass
            def panel_example(self, *a, **k): pass
            def kv_row(self, *a, **k): pass
            def summary_tree(self, *a, **k): pass
            def section_title(self, *a, **k): pass
            def progress_ticker(self, *a, **k): pass
            def print_blank(self): pass
            def subrule(self, *a, **k): pass
            def intro(self, *a, **k): pass
            def ask_text(self, q, default=""): return default
            def ask_yes_no(self, q, default=True): return default

            def status(self, msg):
                class _Null:
                    def __enter__(s): return s
                    def __exit__(s, *e): return False
                    def update(s, m): pass
                return _Null()

            class _Console:
                def print(self, *a, **k): pass

            console = _Console()

            def pick_option(self, prompt, options, default_key,
                              show_back=False):
                if first_call["v"] and show_back:
                    first_call["v"] = False
                    raise _Br()
                return default_key

        monkeypatch.setattr(wiz, "ui", _Mock())
        wiz.run_wizard(cfg=WizardConfig(import_source="none",
                                          mission="full"),
                        only_step=3,
                        dry_run=True)
        # Step 3 should have fired twice — once raised back, once
        # re-fired from the "can't go back further" branch.
        step_3_visits = [c for c in captured if c == "STEP_3"]
        assert len(step_3_visits) == 2, (
            f"expected step 3 to fire twice (back + re-fire), got "
            f"{len(step_3_visits)}: {captured}")
