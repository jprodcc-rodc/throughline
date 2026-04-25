"""Tests for the wizard's UX-optimization additions:

- `--express` mode: single-command install with auto-detected
  defaults, no prompts.
- `--dry-run` flag: show what would happen without committing.
- Step 16 monthly cost projection: surface the most-asked
  question ("how much will this cost me?") at decision time.
"""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# Cost helpers
# ============================================================

class TestPerConvCost:
    """The wizard surfaces per-conversation cost + daily cap, NOT
    a monthly extrapolation. Real usage is bursty (heavy week +
    idle weeks); a "$X/month" figure would misrepresent it for
    most users."""

    def test_skim_cheap(self):
        from throughline_cli.wizard import _per_conv_cost
        assert _per_conv_cost("skim") < _per_conv_cost("normal")

    def test_deep_expensive(self):
        from throughline_cli.wizard import _per_conv_cost
        # Deep MUST be substantially more expensive than normal.
        assert _per_conv_cost("deep") > _per_conv_cost("normal") * 2

    def test_unknown_tier_falls_back(self):
        from throughline_cli.wizard import _per_conv_cost
        assert _per_conv_cost("future_tier") == _per_conv_cost("normal")

    def test_format_includes_per_conv_and_cap(self):
        """The cost line must mention BOTH the unit cost (so users
        can scale to their actual usage) and the daily cap (so they
        know the worst case)."""
        from throughline_cli.wizard import _format_cost_line
        line = _format_cost_line("normal", 20.0)
        assert "per conversation" in line.lower()
        assert "20" in line  # daily cap dollar figure
        assert "midnight" in line  # cap-reset behaviour

    def test_format_no_monthly_extrapolation(self):
        """Regression: don't pretend we know the user's monthly
        usage. Bursty patterns make any "$N/month" or "$N/day"
        projection misleading. (The string "max/day" is fine — that
        describes the cap, not a fictional daily spend rate.)"""
        import re
        from throughline_cli.wizard import _format_cost_line
        line = _format_cost_line("normal", 20.0)
        assert "month" not in line.lower()
        # Forbidden: "$<number>/day" or "$<number>/month".
        assert not re.search(r"\$[\d.]+\s*/\s*(day|month)",
                              line, re.IGNORECASE), (
            f"line implies a fictional daily/monthly spend rate: {line}")

    def test_format_includes_max_refines_per_day(self):
        """Helpful concrete number: at the configured cap, how many
        refines per day max? Lets the user sanity-check whether
        their cap matches their expected usage."""
        from throughline_cli.wizard import _format_cost_line
        line = _format_cost_line("normal", 20.0)
        # Normal tier: $0.04/conv → cap=$20 → max ~500/day
        assert "500" in line


# ============================================================
# --express mode
# ============================================================

class TestExpressMode:
    def test_no_key_returns_2_and_does_not_write(self, tmp_path,
                                                       monkeypatch, capsys):
        """No detected provider env var → exit 2, helpful message,
        no config file."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        # Make detect_configured_provider() return None.
        for var in ("OPENROUTER_API_KEY", "OPENAI_API_KEY",
                     "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY",
                     "TOGETHER_API_KEY", "FIREWORKS_API_KEY",
                     "GROQ_API_KEY", "XAI_API_KEY",
                     "SILICONFLOW_API_KEY", "MOONSHOT_API_KEY",
                     "DASHSCOPE_API_KEY", "ZHIPU_API_KEY",
                     "DOUBAO_API_KEY", "THROUGHLINE_LLM_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        # Reload providers so its env-detection picks up the cleared
        # state. (providers module reads env at call time, not import,
        # so this isn't strictly necessary — but be safe.)
        for mod in list(sys.modules):
            if mod in ("throughline_cli.providers",
                        "throughline_cli.wizard"):
                del sys.modules[mod]
        from throughline_cli.wizard import run_express
        rc = run_express(dry_run=True)
        assert rc == 2
        # Config must NOT have been written.
        config_path = tmp_path / ".throughline" / "config.toml"
        assert not config_path.exists()
        out = capsys.readouterr().out
        assert "no LLM key detected" in out.lower() or \
               "none are set" in out.lower()

    def test_with_openai_key_writes_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        # Clear competing providers so OpenAI wins detection.
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        for mod in list(sys.modules):
            if mod in ("throughline_cli.providers",
                        "throughline_cli.wizard",
                        "throughline_cli.config"):
                del sys.modules[mod]

        from throughline_cli.wizard import run_express
        rc = run_express(dry_run=False)
        assert rc == 0

        # Config was written + has the right shape.
        config_path = tmp_path / ".throughline" / "config.toml"
        assert config_path.exists()
        content = config_path.read_text(encoding="utf-8")
        assert 'llm_provider = "openai"' in content
        assert 'mission = "full"' in content
        assert 'refine_tier = "normal"' in content

        # And it validates clean.
        from throughline_cli import config as cfg_mod
        import tomllib
        raw = tomllib.loads(content)
        assert cfg_mod.validate(raw) == []

    def test_dry_run_does_not_write(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        for mod in list(sys.modules):
            if mod in ("throughline_cli.providers",
                        "throughline_cli.wizard",
                        "throughline_cli.config"):
                del sys.modules[mod]

        from throughline_cli.wizard import run_express
        rc = run_express(dry_run=True)
        assert rc == 0
        config_path = tmp_path / ".throughline" / "config.toml"
        # DRY RUN: no file.
        assert not config_path.exists()

    def test_express_does_not_autodetect_local_providers(self, tmp_path,
                                                                  monkeypatch):
        """`detect_configured_provider()` deliberately skips ollama /
        lm_studio / generic — local providers don't typically expose
        an API key, so an env-var-set signal isn't meaningful.
        Express mode for ollama users falls through to the
        no-key-detected branch (and the message tells them to run the
        full wizard); regression-test that the path doesn't silently
        write a misconfigured cloud config."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        for var in ("OPENROUTER_API_KEY", "OPENAI_API_KEY",
                     "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        # Setting OLLAMA_API_KEY does NOT trigger autodetect.
        monkeypatch.setenv("OLLAMA_API_KEY", "anything")
        for mod in list(sys.modules):
            if mod in ("throughline_cli.providers",
                        "throughline_cli.wizard",
                        "throughline_cli.config"):
                del sys.modules[mod]

        from throughline_cli.wizard import run_express
        rc = run_express(dry_run=False)
        assert rc == 2
        assert not (tmp_path / ".throughline" / "config.toml").exists()


class TestExpressArgvDispatch:
    def test_main_routes_express_flag(self, tmp_path, monkeypatch):
        """The wizard's main() should route --express → run_express
        without falling through to run_wizard."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        for mod in list(sys.modules):
            if mod in ("throughline_cli.providers",
                        "throughline_cli.wizard",
                        "throughline_cli.config"):
                del sys.modules[mod]

        # Replace run_wizard so a fall-through error is loud.
        from throughline_cli import wizard as wiz
        called = {"run_wizard": 0, "run_express": 0}
        real_run_express = wiz.run_express

        def fake_run_wizard(*a, **kw):
            called["run_wizard"] += 1

        def fake_run_express(*a, **kw):
            called["run_express"] += 1
            return real_run_express(*a, **kw)

        monkeypatch.setattr(wiz, "run_wizard", fake_run_wizard)
        monkeypatch.setattr(wiz, "run_express", fake_run_express)
        rc = wiz.main(["--express", "--dry-run"])
        assert rc == 0
        assert called["run_express"] == 1
        assert called["run_wizard"] == 0

    def test_main_routes_express_dry_run(self, tmp_path, monkeypatch):
        """--dry-run combined with --express must not write config."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        for mod in list(sys.modules):
            if mod in ("throughline_cli.providers",
                        "throughline_cli.wizard",
                        "throughline_cli.config"):
                del sys.modules[mod]

        from throughline_cli.wizard import main
        rc = main(["--express", "--dry-run"])
        assert rc == 0
        assert not (tmp_path / ".throughline" / "config.toml").exists()

    def test_main_help_mentions_express(self, capsys):
        from throughline_cli.wizard import main
        rc = main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "--express" in out
        assert "--dry-run" in out


# ============================================================
# Full wizard --dry-run (all 16 steps, no save)
# ============================================================

class TestFullWizardDryRun:
    """`python install.py --dry-run` walks every step but does NOT
    write config.toml and does NOT run the import adapter. Same
    semantics as `--express --dry-run` but for the interactive
    wizard."""

    def test_run_wizard_dry_run_does_not_save(self, tmp_path, monkeypatch):
        """Walk a full mocked wizard run with dry_run=True and
        assert no config.toml is written."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        # Reload modules so env var takes effect.
        for mod in list(sys.modules):
            if mod in ("throughline_cli.wizard", "throughline_cli.config"):
                del sys.modules[mod]

        from throughline_cli import wizard as wiz
        from throughline_cli.config import WizardConfig

        # Mock the ui surface so the steps don't block on input.
        # Mirrors the _ScriptedUI used by combinatorial tests.
        captured: list = []

        class _Mock:
            def step_header(self, *a, **kw): pass
            def intro(self, *a, **kw): pass
            def info_line(self, msg, *a, **kw):
                captured.append(str(msg))
            def warn_box(self, *a, **kw): pass
            def panel_example(self, *a, **kw): pass
            def kv_row(self, *a, **kw): pass
            def summary_tree(self, *a, **kw): pass
            def section_title(self, *a, **kw): pass
            def banner(self, *a, **kw): pass
            def progress_ticker(self, *a, **kw): pass
            def print_blank(self, *a, **kw): pass
            def subrule(self, *a, **kw): pass
            def pick_option(self, q, options, default_key):
                return default_key
            def ask_yes_no(self, q, default=True):
                return default
            def ask_text(self, q, default=""):
                return default

            def status(self, msg):
                class _Null:
                    def __enter__(s): return s
                    def __exit__(s, *e): return False
                    def update(s, m): pass
                return _Null()

            class _Console:
                def print(self, *a, **kw): pass

            console = _Console()

        monkeypatch.setattr(wiz, "ui", _Mock())

        # Run with dry_run=True.
        wiz.run_wizard(cfg=WizardConfig(import_source="none"),
                        dry_run=True)

        # Critical: no config.toml in the redirected dir.
        config_path = tmp_path / ".throughline" / "config.toml"
        assert not config_path.exists(), (
            "dry_run=True must NOT write config.toml")
        # Critical: the dry-run footer message fired.
        joined = "\n".join(captured)
        assert "DRY RUN" in joined or "not written" in joined.lower()

    def test_run_wizard_normal_does_save(self, tmp_path, monkeypatch):
        """Inverse: dry_run=False (the default) MUST write config."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        for mod in list(sys.modules):
            if mod in ("throughline_cli.wizard", "throughline_cli.config"):
                del sys.modules[mod]

        from throughline_cli import wizard as wiz
        from throughline_cli.config import WizardConfig

        class _Mock:
            def step_header(self, *a, **kw): pass
            def intro(self, *a, **kw): pass
            def info_line(self, *a, **kw): pass
            def warn_box(self, *a, **kw): pass
            def panel_example(self, *a, **kw): pass
            def kv_row(self, *a, **kw): pass
            def summary_tree(self, *a, **kw): pass
            def section_title(self, *a, **kw): pass
            def banner(self, *a, **kw): pass
            def progress_ticker(self, *a, **kw): pass
            def print_blank(self, *a, **kw): pass
            def subrule(self, *a, **kw): pass
            def pick_option(self, q, options, default_key): return default_key
            def ask_yes_no(self, q, default=True): return default
            def ask_text(self, q, default=""): return default

            def status(self, msg):
                class _Null:
                    def __enter__(s): return s
                    def __exit__(s, *e): return False
                    def update(s, m): pass
                return _Null()

            class _Console:
                def print(self, *a, **kw): pass

            console = _Console()

        monkeypatch.setattr(wiz, "ui", _Mock())
        wiz.run_wizard(cfg=WizardConfig(import_source="none"))
        assert (tmp_path / ".throughline" / "config.toml").exists()

    def test_dry_run_flag_resets_after_run(self, tmp_path, monkeypatch):
        """The module-level `_DRY_RUN_ACTIVE` flag must be cleared
        after run_wizard returns, so a subsequent programmatic call
        without dry_run= doesn't accidentally inherit it."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        for mod in list(sys.modules):
            if mod in ("throughline_cli.wizard", "throughline_cli.config"):
                del sys.modules[mod]

        from throughline_cli import wizard as wiz
        from throughline_cli.config import WizardConfig

        class _Mock:
            def step_header(self, *a, **kw): pass
            def intro(self, *a, **kw): pass
            def info_line(self, *a, **kw): pass
            def warn_box(self, *a, **kw): pass
            def panel_example(self, *a, **kw): pass
            def kv_row(self, *a, **kw): pass
            def summary_tree(self, *a, **kw): pass
            def section_title(self, *a, **kw): pass
            def banner(self, *a, **kw): pass
            def progress_ticker(self, *a, **kw): pass
            def print_blank(self, *a, **kw): pass
            def subrule(self, *a, **kw): pass
            def pick_option(self, q, options, default_key): return default_key
            def ask_yes_no(self, q, default=True): return default
            def ask_text(self, q, default=""): return default

            def status(self, msg):
                class _Null:
                    def __enter__(s): return s
                    def __exit__(s, *e): return False
                    def update(s, m): pass
                return _Null()

            class _Console:
                def print(self, *a, **kw): pass

            console = _Console()

        monkeypatch.setattr(wiz, "ui", _Mock())
        wiz.run_wizard(cfg=WizardConfig(import_source="none"), dry_run=True)
        # After dry-run completes, the flag must be back to False so
        # later code paths (tests, scripts) aren't poisoned.
        assert wiz._DRY_RUN_ACTIVE is False

    def test_main_routes_dry_run_to_full_wizard(self, tmp_path, monkeypatch):
        """`python install.py --dry-run` (no --express) routes through
        the full wizard with dry_run=True."""
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR",
                            str(tmp_path / ".throughline"))
        for mod in list(sys.modules):
            if mod in ("throughline_cli.wizard", "throughline_cli.config"):
                del sys.modules[mod]

        from throughline_cli import wizard as wiz

        called = {"dry_run": None}

        def fake_run_wizard(cfg=None, only_step=None, step_filter=None,
                              dry_run=False):
            called["dry_run"] = dry_run

        monkeypatch.setattr(wiz, "run_wizard", fake_run_wizard)
        # Force the path that hits the fresh-install branch.
        monkeypatch.setattr("throughline_cli.config.config_path",
                              lambda: tmp_path / "no-such-config.toml")

        rc = wiz.main(["--dry-run", "--force"])
        assert rc == 0
        assert called["dry_run"] is True


# ============================================================
# Regression: cost projection is in the step 16 summary panel
# ============================================================

class TestStep16CostProjection:
    def test_cost_line_appears_in_summary(self, tmp_path, monkeypatch):
        """Step 16 must surface per-conversation cost + daily cap so
        users commit with informed expectations — without any fake
        monthly extrapolation that ignores bursty real-world usage."""
        from throughline_cli.config import WizardConfig
        from throughline_cli import wizard as wiz

        captured: list = []
        monkeypatch.setattr(wiz.ui, "step_header", lambda *a, **k: None)
        monkeypatch.setattr(wiz.ui, "kv_row", lambda *a, **k: None)
        monkeypatch.setattr(wiz.ui, "ask_yes_no",
                              lambda *a, **k: False)  # abort before save
        monkeypatch.setattr(wiz.ui, "info_line",
                              lambda msg: captured.append(str(msg)))
        monkeypatch.setattr(wiz.ui, "print_blank", lambda: None)
        monkeypatch.setattr(wiz.ui, "section_title", lambda *a, **k: None)

        cfg = WizardConfig()
        try:
            wiz.step_16_summary(cfg)
        except SystemExit:
            pass  # the abort branch sys.exit(0)s
        joined = "\n".join(captured)
        # Must mention per-conversation unit + daily cap.
        assert "per conversation" in joined.lower()
        assert "midnight" in joined.lower()
        # Must NOT pretend to know monthly usage.
        assert "month" not in joined.lower()