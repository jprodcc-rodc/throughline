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
# Cost projection helper
# ============================================================

class TestCostProjection:
    def test_skim_tier_cheap(self):
        from throughline_cli.wizard import _project_monthly_cost
        m, d = _project_monthly_cost("skim")
        assert d > 0
        assert m == d * 30
        # Skim is the cheap tier — should be well under $5/month at
        # 10 conv/day (the default).
        assert m < 5

    def test_normal_tier_midrange(self):
        from throughline_cli.wizard import _project_monthly_cost
        m, _ = _project_monthly_cost("normal")
        assert 5 <= m <= 50  # ~$12 at 10 conv/day

    def test_deep_tier_expensive(self):
        from throughline_cli.wizard import _project_monthly_cost
        m_normal, _ = _project_monthly_cost("normal")
        m_deep, _ = _project_monthly_cost("deep")
        # Deep tier MUST be substantially more expensive than normal
        # — otherwise the prose contradicts itself.
        assert m_deep > m_normal * 2

    def test_unknown_tier_falls_back_to_normal(self):
        from throughline_cli.wizard import _project_monthly_cost
        m_unknown, _ = _project_monthly_cost("future_tier")
        m_normal, _ = _project_monthly_cost("normal")
        assert m_unknown == m_normal

    def test_convs_per_day_scales_linearly(self):
        from throughline_cli.wizard import _project_monthly_cost
        m_10, _ = _project_monthly_cost("normal", convs_per_day=10)
        m_40, _ = _project_monthly_cost("normal", convs_per_day=40)
        assert abs(m_40 - 4 * m_10) < 0.01


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
# Regression: cost projection is in the step 16 summary panel
# ============================================================

class TestStep16CostProjection:
    def test_cost_projection_appears_in_summary(self, tmp_path,
                                                       monkeypatch):
        """Step 16 must surface the monthly cost projection so users
        commit with informed expectations."""
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
        assert "month" in joined.lower()
        # The default tier is `normal` ($0.04/conv * 10/day * 30 ≈ $12)
        assert "12" in joined or "$" in joined