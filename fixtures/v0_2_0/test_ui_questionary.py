"""Tests for the questionary-based picker + spinner helpers added
to `throughline_cli.ui` (Tier 1 + Tier 2 UX wave).

The strategy: tests run with non-TTY stdin (pytest captures it), so
the auto-detect drops to legacy code paths. That keeps the existing
50+ `monkeypatch("builtins.input", ...)` tests working unchanged.
This file pins the auto-detect behaviour itself so a future refactor
can't silently flip it on inside CI.
"""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# _use_questionary auto-detect
# ============================================================

class TestUseQuestionaryDetection:
    def test_pytest_captures_stdin_so_legacy_path(self):
        """pytest captures stdin → not a TTY → legacy path. This
        guarantees every existing input-mocking test keeps working
        without modification."""
        from throughline_cli.ui import _use_questionary
        assert _use_questionary() is False

    def test_legacy_ui_env_var_forces_legacy(self, monkeypatch):
        """Even on a real TTY, THROUGHLINE_LEGACY_UI=1 disables
        questionary — escape hatch for terminals that mishandle the
        arrow-key navigation."""
        monkeypatch.setenv("THROUGHLINE_LEGACY_UI", "1")
        # Even if we faked a TTY, the env var would win.
        from throughline_cli.ui import _use_questionary
        assert _use_questionary() is False

    def test_questionary_missing_returns_false(self, monkeypatch):
        """If `questionary` isn't installed, gracefully fall back to
        the legacy picker — wizard must never crash on optional dep
        absence."""
        import builtins
        real_import = builtins.__import__

        def guard(name, *a, **kw):
            if name == "questionary" or name.startswith("questionary."):
                raise ImportError("simulated absence")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        # Force the TTY check to pass so we hit the questionary
        # import line.
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        from throughline_cli import ui
        assert ui._use_questionary() is False


# ============================================================
# Legacy pick_option still works (existing tests rely on it)
# ============================================================

class TestPickOptionLegacyPath:
    def test_legacy_path_returns_default_on_enter(self, monkeypatch):
        """Pressing Enter at the legacy prompt accepts the default
        — a key invariant the existing wizard tests rely on."""
        from throughline_cli.ui import _pick_option_legacy
        monkeypatch.setattr("builtins.input", lambda *_: "")
        result = _pick_option_legacy(
            "Pick:",
            [("a", "Alpha", ""), ("b", "Bravo", "")],
            default_key="b",
        )
        assert result == "b"

    def test_legacy_path_returns_chosen(self, monkeypatch):
        from throughline_cli.ui import _pick_option_legacy
        monkeypatch.setattr("builtins.input", lambda *_: "1")
        result = _pick_option_legacy(
            "Pick:",
            [("a", "Alpha", ""), ("b", "Bravo", "")],
            default_key="b",
        )
        assert result == "a"

    def test_legacy_path_invalid_falls_back_to_default(self, monkeypatch):
        from throughline_cli.ui import _pick_option_legacy
        monkeypatch.setattr("builtins.input", lambda *_: "abc")
        result = _pick_option_legacy(
            "Pick:",
            [("a", "Alpha", ""), ("b", "Bravo", "")],
            default_key="a",
        )
        assert result == "a"


# ============================================================
# status() spinner — non-TTY path (pytest)
# ============================================================

class TestStatusContextManager:
    def test_non_tty_returns_null_status(self):
        """pytest is non-TTY → status() must return the no-op
        wrapper, not rich's animated spinner. The wrapper still
        exposes the enter/exit/update API so call sites are
        identical."""
        from throughline_cli.ui import status, _NullStatus
        cm = status("Doing a thing...")
        assert isinstance(cm, _NullStatus)

    def test_status_context_manager_works(self, capsys):
        """The null status must support the context-manager pattern
        (enter / exit) that real call sites use, and emit the
        message once on enter."""
        from throughline_cli.ui import status
        with status("Calling LLM...") as s:
            assert s is not None
        out = capsys.readouterr().out
        assert "Calling LLM" in out

    def test_status_update_works(self, capsys):
        """`status().update(msg)` is supposed to work whether the
        backing implementation is rich or our null shim. Verify the
        null shim handles the call without raising + emits the
        update."""
        from throughline_cli.ui import status
        with status("Phase 1") as s:
            s.update("Phase 2")
        out = capsys.readouterr().out
        assert "Phase 1" in out
        assert "Phase 2" in out


# ============================================================
# Public pick_option dispatch — pytest path is legacy
# ============================================================

class TestPickOptionDispatch:
    def test_dispatch_to_legacy_under_pytest(self, monkeypatch):
        """Calling `pick_option` from pytest hits the legacy path
        (because stdin isn't a TTY). The 50+ existing
        `monkeypatch.setattr('builtins.input', ...)` tests pass
        through unchanged."""
        from throughline_cli import ui
        monkeypatch.setattr("builtins.input", lambda *_: "2")
        result = ui.pick_option(
            "Pick:",
            [("a", "Alpha", ""), ("b", "Bravo", ""), ("c", "Charlie", "")],
            default_key="a",
        )
        assert result == "b"


# ============================================================
# ask_yes_no still works in non-TTY mode
# ============================================================

class TestAskYesNoLegacy:
    def test_yes(self, monkeypatch):
        from throughline_cli import ui
        monkeypatch.setattr("builtins.input", lambda *_: "y")
        assert ui.ask_yes_no("OK?", default=False) is True

    def test_no(self, monkeypatch):
        from throughline_cli import ui
        monkeypatch.setattr("builtins.input", lambda *_: "n")
        assert ui.ask_yes_no("OK?", default=True) is False

    def test_enter_takes_default(self, monkeypatch):
        from throughline_cli import ui
        monkeypatch.setattr("builtins.input", lambda *_: "")
        assert ui.ask_yes_no("OK?", default=True) is True
        assert ui.ask_yes_no("OK?", default=False) is False
