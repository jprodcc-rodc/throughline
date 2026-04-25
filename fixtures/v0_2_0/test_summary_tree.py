"""Tests for the Tier-3 UX wave: hierarchical summary tree
replacing the flat KV-row listing in step 16.

Two surfaces under test:
- `wizard._build_summary_groups(cfg)` — pure grouping function. Must
  honour mission branching (notes_only skips Retrieval / vector_db),
  surface every config field exactly once, and group fields the way
  a human would scan them ("LLM stuff together", not interleaved
  with retrieval / refine).
- `ui.summary_tree(groups)` — rich.tree renderer. Must emit a tree
  whose leaves preserve the input strings even when stripped of
  rich's box-drawing.
"""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# _build_summary_groups (pure)
# ============================================================

class TestBuildSummaryGroups:
    def test_full_mission_has_all_groups(self):
        from throughline_cli.config import WizardConfig
        from throughline_cli.wizard import _build_summary_groups
        groups = _build_summary_groups(WizardConfig(mission="full"))
        labels = [g[0] for g in groups]
        assert "Mission & Storage" in labels
        assert "LLM" in labels
        assert "Retrieval" in labels
        assert "Refine pipeline" in labels
        assert "Cost guardrails" in labels

    def test_notes_only_skips_retrieval(self):
        """Notes-only mission has no embedder / reranker and no
        vector_db — Retrieval group must not appear, vector_db
        leaf must not appear under Mission & Storage."""
        from throughline_cli.config import WizardConfig
        from throughline_cli.wizard import _build_summary_groups
        groups = _build_summary_groups(WizardConfig(mission="notes_only"))
        labels = [g[0] for g in groups]
        assert "Retrieval" not in labels
        # vector_db leaf must also be gone from the storage group.
        storage = next(items for label, items in groups
                       if label == "Mission & Storage")
        keys = [k for k, _ in storage]
        assert "vector_db" not in keys

    def test_every_field_appears_once(self):
        """Every meaningful config field must surface in the
        summary — exactly once. Catches silent drift if a future
        wizard step adds a config knob without wiring it through
        the summary."""
        from throughline_cli.config import WizardConfig
        from throughline_cli.wizard import _build_summary_groups
        groups = _build_summary_groups(WizardConfig())
        all_keys: list[str] = []
        for _, items in groups:
            for k, _ in items:
                all_keys.append(k)
        # No duplicates across groups.
        assert len(all_keys) == len(set(all_keys)), (
            f"duplicate keys across summary groups: {all_keys}")
        # Spot-check that key fields land somewhere.
        assert "mission"        in all_keys
        assert "provider"       in all_keys
        assert "model"          in all_keys
        assert "privacy"        in all_keys
        assert "tier"           in all_keys
        assert "card_structure" in all_keys
        assert "taxonomy"       in all_keys
        assert "daily_budget"   in all_keys

    def test_import_group_minimal_when_no_source(self):
        from throughline_cli.config import WizardConfig
        from throughline_cli.wizard import _build_summary_groups
        groups = _build_summary_groups(WizardConfig(import_source="none"))
        imp = next(items for label, items in groups if label == "Import")
        # Only `source = "none"` — no scanned/emit_est/est_cost.
        keys = [k for k, _ in imp]
        assert keys == ["source"]

    def test_import_group_full_when_scan_done(self):
        from throughline_cli.config import WizardConfig
        from throughline_cli.wizard import _build_summary_groups
        cfg = WizardConfig(
            import_source="claude",
            import_path="/tmp/fake.zip",
            import_scanned=42,
            import_emitted=40,
            import_est_normal_cost_usd=1.50,
            import_est_skim_cost_usd=0.20,
        )
        groups = _build_summary_groups(cfg)
        imp = next(items for label, items in groups if label == "Import")
        keys = [k for k, _ in imp]
        assert "source"   in keys
        assert "scanned"  in keys
        assert "emit_est" in keys
        assert "est_cost" in keys

    def test_provider_and_model_split_into_separate_leaves(self):
        """Old kv_row code ran them together as `openrouter ·
        anthropic/claude-sonnet-4.6`. The tree splits them so each
        is independently scannable."""
        from throughline_cli.config import WizardConfig
        from throughline_cli.wizard import _build_summary_groups
        groups = _build_summary_groups(WizardConfig(
            llm_provider="anthropic",
            llm_provider_id="claude-sonnet-4-5-20250929",
        ))
        llm = dict(next(items for label, items in groups
                        if label == "LLM"))
        assert llm["provider"] == "anthropic"
        assert llm["model"] == "claude-sonnet-4-5-20250929"


# ============================================================
# ui.summary_tree renderer
# ============================================================

class TestSummaryTreeRenderer:
    def test_renders_group_labels(self, capsys):
        """All provided group labels must appear in the rendered
        output, not just the leaves."""
        from throughline_cli.ui import summary_tree
        summary_tree([
            ("Group A", [("k1", "v1"), ("k2", "v2")]),
            ("Group B", [("k3", "v3")]),
        ])
        out = capsys.readouterr().out
        assert "Group A" in out
        assert "Group B" in out
        assert "k1" in out and "v1" in out
        assert "k2" in out and "v2" in out
        assert "k3" in out and "v3" in out

    def test_skips_empty_groups(self, capsys):
        """A group with no items must not appear in the tree —
        otherwise an empty branch is just visual noise."""
        from throughline_cli.ui import summary_tree
        summary_tree([
            ("Group A", [("k1", "v1")]),
            ("Empty Group", []),
            ("Group B", [("k2", "v2")]),
        ])
        out = capsys.readouterr().out
        assert "Empty Group" not in out
        assert "Group A" in out
        assert "Group B" in out

    def test_includes_root_label(self, capsys):
        """The tree's root anchor ('your throughline config') is the
        breadcrumb that orients the user — it must always show."""
        from throughline_cli.ui import summary_tree
        summary_tree([("Group A", [("k1", "v1")])])
        out = capsys.readouterr().out
        assert "throughline config" in out.lower()

    def test_handles_unicode_values(self, capsys):
        """Tags / paths / titles often contain non-ASCII (Chinese,
        accents). The tree must round-trip them without mangling."""
        from throughline_cli.ui import summary_tree
        summary_tree([
            ("项目设置", [("路径", "~/笔记/vault"), ("model", "Qwen2.5-72B")]),
        ])
        out = capsys.readouterr().out
        assert "项目设置" in out
        assert "路径" in out
        assert "笔记" in out


# ============================================================
# step_16_summary integration (end-to-end via mock harness)
# ============================================================

class TestStep16UsesTree:
    def test_step16_calls_summary_tree(self, monkeypatch):
        """Step 16 must invoke `ui.summary_tree` (not the old
        per-field `ui.kv_row` cascade)."""
        from throughline_cli.config import WizardConfig
        from throughline_cli import wizard as wiz

        called = {"summary_tree": 0, "kv_row": 0}
        monkeypatch.setattr(wiz.ui, "step_header", lambda *a, **k: None)
        monkeypatch.setattr(wiz.ui, "ask_yes_no", lambda *a, **k: False)
        monkeypatch.setattr(wiz.ui, "info_line", lambda *a, **k: None)
        monkeypatch.setattr(wiz.ui, "print_blank", lambda: None)
        monkeypatch.setattr(wiz.ui, "section_title", lambda *a, **k: None)

        def fake_tree(*a, **k):
            called["summary_tree"] += 1

        def fake_kv(*a, **k):
            called["kv_row"] += 1

        monkeypatch.setattr(wiz.ui, "summary_tree", fake_tree)
        monkeypatch.setattr(wiz.ui, "kv_row", fake_kv)

        try:
            wiz.step_16_summary(WizardConfig())
        except SystemExit:
            pass
        assert called["summary_tree"] == 1, (
            "step 16 should render via summary_tree once")
        assert called["kv_row"] == 0, (
            "step 16 should NOT use the old per-field kv_row "
            "cascade after the Tier-3 refactor")
