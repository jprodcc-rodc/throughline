"""Tests for `daemon.refine_daemon.refine_kept_slices` — the
extracted per-slice refine loop.

Task J. The extraction pulls the cost-sensitive bit of
`process_raw_file` into a pure-ish function that tests can drive
without watchdog setup, without filesystem state management, and
without parsing raw conversations from disk.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Import lazily so env setup (below) runs before module-load.


def _mk_kept_slice():
    """Build a realistic SliceSpec for the refiner to chew on."""
    from daemon.refine_daemon import SliceSpec
    return SliceSpec(
        start_idx=0,
        end_idx=2,
        title_hint="PyTorch MPS setup",
        keep=True,
        slice_text=(
            "USER: How do I set up PyTorch MPS?\n"
            "ASSISTANT: Use torch.device('mps') ...\n"
        ),
    )


def _mk_conv(tmp_path):
    from daemon.refine_daemon import RawConversation, Message
    return RawConversation(
        conv_id="test-conv-001",
        raw_path=tmp_path / "raw" / "2026-04-25" / "test.md",
        messages=[
            Message(role="user", content="How do I set up PyTorch MPS?"),
            Message(role="assistant", content="Use torch.device('mps')."),
        ],
    )


def _mk_refined():
    from daemon.refine_daemon import RefinedResult
    return RefinedResult(
        title="PyTorch MPS setup for small transformers",
        primary_x="AI/LLM",
        visible_x_tags=["AI/LLM"],
        form_y="y/SOP",
        z_axis="z/Node",
        knowledge_identity="universal",
        body_markdown=(
            "# Scene & Pain Point\nNeed MPS on M2.\n\n"
            "# Core Knowledge & First Principles\nUnified memory.\n\n"
            "# Detailed Execution Plan\ntorch.device('mps')\n\n"
            "# Pitfalls & Boundaries\nbitsandbytes is CUDA-only.\n\n"
            "# Insights & Mental Models\nmps = default for small models.\n\n"
            "# Length Summary\nUse mps on M2 with fallback env.\n"
        ),
        claim_sources=["user_stated"],
        proposed_x_ideal="AI/LLM",
    )


class TestRefineKeptSlicesHappyPath:
    def test_one_slice_writes_one_card(self, tmp_path, monkeypatch):
        """Given a kept slice + a mocked refiner that returns a
        realistic card, the extracted function writes one card and
        returns a count of 1."""
        # Redirect vault + state + raw roots to tmp.
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("THROUGHLINE_RAW_ROOT", str(tmp_path / "raw"))

        # Force-reload so the VAULT_ROOT et al pick up our tmp paths.
        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        conv = _mk_conv(tmp_path)
        kept = [_mk_kept_slice()]
        refined = _mk_refined()

        # Stub the refiner + retention guard.
        with patch.object(rd, "refine_with_retention_guard",
                           return_value=(refined, 0, 0)), \
             patch.object(rd, "_check_duplicate_in_qdrant",
                           return_value=None), \
             patch.object(rd, "route_domain", return_value="70_AI"), \
             patch.object(rd, "route_subpath",
                           return_value="70_AI/70.01_LLM_Brain/70.01.01_Theory_&_Models"):
            count = rd.refine_kept_slices(
                conv=conv, kept=kept,
                pack=None, pack_name="",
                policies={"dedup_enabled": True},
                intent_mode={},
            )

        assert count == 1
        # Formal card landed at the routed path (70_AI/...).
        written = list(vault.rglob("70_AI/**/*.md"))
        assert len(written) == 1
        # A buffer stub also lands under 00_Buffer/ — not a failure,
        # just a write_dual_note side effect we don't count here.

    def test_dedup_hit_skips_write(self, tmp_path, monkeypatch):
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))

        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        conv = _mk_conv(tmp_path)
        kept = [_mk_kept_slice()]
        refined = _mk_refined()

        with patch.object(rd, "refine_with_retention_guard",
                           return_value=(refined, 0, 0)), \
             patch.object(rd, "_check_duplicate_in_qdrant",
                           return_value={"title": "prior card",
                                         "score": 0.95}):
            count = rd.refine_kept_slices(
                conv=conv, kept=kept,
                policies={"dedup_enabled": True},
                intent_mode={},
            )

        assert count == 0
        assert not list(vault.rglob("*.md"))

    def test_dedup_disabled_bypasses_check(self, tmp_path, monkeypatch):
        """policies.dedup_enabled=False should skip the Qdrant
        duplicate check entirely (no call)."""
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))

        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        conv = _mk_conv(tmp_path)
        refined = _mk_refined()

        dedup_called = {"n": 0}

        def fake_dedup(*a, **k):
            dedup_called["n"] += 1
            return None

        with patch.object(rd, "refine_with_retention_guard",
                           return_value=(refined, 0, 0)), \
             patch.object(rd, "_check_duplicate_in_qdrant", fake_dedup), \
             patch.object(rd, "route_domain", return_value="70_AI"), \
             patch.object(rd, "route_subpath",
                           return_value="70_AI/70.01_LLM_Brain/70.01.01_Theory_&_Models"):
            count = rd.refine_kept_slices(
                conv=conv, kept=[_mk_kept_slice()],
                policies={"dedup_enabled": False},
                intent_mode={},
            )

        assert count == 1
        assert dedup_called["n"] == 0


class TestRefineKeptSlicesErrorPaths:
    def test_refiner_exception_is_logged_not_fatal(self, tmp_path, monkeypatch):
        """One slice raising doesn't kill the batch — subsequent
        slices keep running."""
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))

        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        conv = _mk_conv(tmp_path)
        ok = _mk_refined()
        calls = {"n": 0}

        def maybe_raise(*a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("simulated refiner timeout")
            return (ok, 0, 0)

        with patch.object(rd, "refine_with_retention_guard", maybe_raise), \
             patch.object(rd, "_check_duplicate_in_qdrant",
                           return_value=None), \
             patch.object(rd, "route_domain", return_value="70_AI"), \
             patch.object(rd, "route_subpath",
                           return_value="70_AI/70.01_LLM_Brain/70.01.01_Theory_&_Models"), \
             patch.object(rd, "log_maintenance_issue") as logm:
            count = rd.refine_kept_slices(
                conv=conv,
                kept=[_mk_kept_slice(), _mk_kept_slice()],
                policies={"dedup_enabled": True},
                intent_mode={},
            )

        assert count == 1  # second slice recovered
        # Issue logged for the failed slice.
        assert logm.called

    def test_refiner_returns_none_is_skipped(self, tmp_path, monkeypatch):
        """Retention gate returning None must skip cleanly (not
        write, not log an issue)."""
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))

        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        conv = _mk_conv(tmp_path)

        with patch.object(rd, "refine_with_retention_guard",
                           return_value=(None, 0, 0)):
            count = rd.refine_kept_slices(
                conv=conv, kept=[_mk_kept_slice()],
                policies={"dedup_enabled": True},
                intent_mode={},
            )

        assert count == 0


class TestRefineKeptSlicesEmpty:
    def test_empty_kept_list_returns_zero(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path / "vault"))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))

        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        conv = _mk_conv(tmp_path)
        count = rd.refine_kept_slices(conv=conv, kept=[])
        assert count == 0


class TestRefineKeptSlicesObservesTaxonomy:
    def test_successful_write_records_observation(self, tmp_path, monkeypatch):
        """Every written card appends one line to
        state/taxonomy_observations.jsonl (U27.3 invariant)."""
        vault = tmp_path / "vault"
        vault.mkdir()
        state = tmp_path / "state"
        state.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state))

        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
            if mod.startswith("daemon.taxonomy_observer"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        conv = _mk_conv(tmp_path)
        refined = _mk_refined()

        with patch.object(rd, "refine_with_retention_guard",
                           return_value=(refined, 0, 0)), \
             patch.object(rd, "_check_duplicate_in_qdrant",
                           return_value=None), \
             patch.object(rd, "route_domain", return_value="70_AI"), \
             patch.object(rd, "route_subpath",
                           return_value="70_AI/70.01_LLM_Brain/70.01.01_Theory_&_Models"):
            rd.refine_kept_slices(
                conv=conv, kept=[_mk_kept_slice()],
                policies={"dedup_enabled": True},
                intent_mode={},
            )

        obs_path = state / "taxonomy_observations.jsonl"
        assert obs_path.exists()
        lines = obs_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        rec = json.loads(lines[0])
        assert rec["primary_x"] == "AI/LLM"
        assert rec["proposed_x_ideal"] == "AI/LLM"
        assert rec["title"] == "PyTorch MPS setup for small transformers"
