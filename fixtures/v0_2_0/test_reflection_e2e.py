"""End-to-end integration test: synthetic vault → full Reflection
Pass → MCP tools.

Builds a synthetic vault with multiple JD-prefixed dirs and a
realistic mix of:
- refined cards (slice_id, with bilingual sections, with date)
- profile cards (managed_by set)
- system files (no slice_id, no managed_by — should be filtered)
- hand notes (no frontmatter — already filtered by JD walk)

Mocks all external dependencies (rag_server clustering, LLM
namer, LLM extractor) with deterministic fakes. Runs the full
8-stage pipeline. Asserts:

- pass_state file written with correct counters
- positions file has expected cluster shape
- open_threads file has expected cards flagged
- writeback_preview has expected diffs
- find_open_threads MCP tool reads the state file correctly
- check_consistency MCP tool finds the right cluster
- get_position_drift MCP tool returns chronological trajectory

This is the "production smoke" surface — if anything in the
pipeline drifts incompatibly, this test breaks.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def synth_vault(tmp_path, monkeypatch):
    """Build a minimal but realistic synthetic vault. Returns a tuple
    (vault, state, state_kwargs) where state_kwargs is a dict of
    state-file paths to pass to run_pass programmatically."""
    vault = tmp_path / "vault"
    state = tmp_path / "state"
    vault.mkdir()
    state.mkdir()

    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state))
    monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))

    def _write_card(rel: str, content: str):
        p = vault / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    # Two refined cards on "pricing" — first chronologically
    _write_card(
        "30_Biz/early_pricing.md",
        textwrap.dedent(
            """\
            ---
            title: Early pricing thoughts
            slice_id: abc-1
            date: 2026-01-15
            ---
            # 🎯 场景与痛点 (Context & Anchor)
            Considering pricing for early-stage SaaS.

            # 🧠 核心知识与底层原理 (First Principles)
            - LTV math is unpredictable in early stage
            - Churn risk severe pre-PMF

            # 🛠️ 详细执行方案 (Execution & Code)
            Stick with value-based pricing for now.

            # 🚧 避坑与边界 (Pitfalls & Gotchas)
            - Don't lock in usage-based without LTV data
            """
        ),
    )

    _write_card(
        "30_Biz/late_pricing.md",
        textwrap.dedent(
            """\
            ---
            title: Pricing reconsidered post-PMF
            slice_id: abc-2
            date: 2026-03-15
            ---
            # 🎯 场景与痛点 (Context & Anchor)
            Three months into PMF; revisiting pricing.

            # 🧠 核心知识与底层原理 (First Principles)
            - Now that LTV is stable, usage-based is viable
            - Runway no longer the constraint

            # 🛠️ 详细执行方案 (Execution & Code)
            Switch to usage-based pricing.
            """
        ),
    )

    # Health cluster — B1 thiamine cards
    _write_card(
        "20_Health/b1_protocol.md",
        textwrap.dedent(
            """\
            ---
            title: B1 thiamine therapy protocol
            slice_id: hth-1
            date: 2026-02-01
            ---
            # 🎯 场景与痛点 (Context & Anchor)
            Setting up B1 protocol for nerve repair.

            # 🧠 核心知识与底层原理 (First Principles)
            - High-dose B1 needed post-bariatric
            - Daily injection for first 30 days

            # 🚧 避坑与迭代路径 (Debugging & Iteration)
            - Watch for refeeding syndrome
            """
        ),
    )

    _write_card(
        "20_Health/b1_dose_review.md",
        textwrap.dedent(
            """\
            ---
            title: B1 dose escalation review
            slice_id: hth-2
            date: 2026-03-10
            ---
            # 🎯 场景与痛点 (Context & Anchor)
            30-day review of B1 protocol.

            # 🧠 核心知识与底层原理 (First Principles)
            - Dose escalation worked as planned
            - Continue maintenance phase
            """
        ),
    )

    # Profile card (managed_by set, no slice_id)
    _write_card(
        "00_Buffer/00.05_Profile/personal_master.md",
        textwrap.dedent(
            """\
            ---
            title: Personal master record
            managed_by: manual_profile_interview
            date: 2026-04-01
            ---
            # 🎯 场景与痛点 (Context & Anchor)
            Master record of personal context for all interactions.
            """
        ),
    )

    # System file (no slice_id, no managed_by — filtered by stage 1.5)
    _write_card(
        "00_Buffer/00.02_Data_Ingest/auto_refine_log.md",
        textwrap.dedent(
            """\
            ---
            title: Auto Refine Log
            ---
            # Auto Refine Log
            entries...
            """
        ),
    )

    # Hand-written note (no frontmatter — filtered by walk)
    _write_card(
        "10_Tech/random_thoughts.md",
        "Just some unstructured thoughts here, no frontmatter at all.\n"
    )

    return vault, state


# ---------- Stage-by-stage pipeline ----------

class TestPipelineNoLLM:
    """No-LLM dry-run path: clustering still happens (we mock that
    too), stages 3 + 4 stay stubbed because no extractor / namer
    is passed."""

    def test_full_pass_writes_all_state_files(self, synth_vault):
        from daemon.reflection_pass import run_pass

        vault, state = synth_vault

        # Mock clustering: assign by domain prefix
        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            grouped: dict[str, list] = {}
            for c in cards:
                # Use first JD-prefixed dir as cluster_id
                rel = Path(c["path"]).relative_to(vault)
                domain = next(
                    p for p in rel.parts
                    if p[:2].isdigit() and p[2:3] == "_"
                )
                cid = domain  # use the domain string as cluster_id
                grouped.setdefault(cid, []).append(c)
                c["_cluster_id"] = cid
            result.cards_clustered = len(cards)
            result.clusters_count = len(grouped)
            return grouped

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            result = run_pass(vault_root=vault, dry_run=False)

        # Counters: 7 .md files under JD layout (6 with fm + 1 without).
        # 5 reflectable (4 slice_id + 1 managed_by).
        # 2 excluded (auto_refine_log + random_thoughts no-fm).
        assert result.cards_scanned == 7
        assert result.cards_reflectable == 5
        assert result.cards_excluded == 2

        # State files written
        assert (state / "reflection_pass_state.json").exists()
        assert (state / "reflection_open_threads.json").exists()
        assert (state / "reflection_positions.json").exists()
        assert (state / "reflection_writeback_preview.json").exists()

    def test_state_files_match_real_data(self, synth_vault):
        from daemon.reflection_pass import run_pass

        vault, state = synth_vault

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            grouped: dict[str, list] = {}
            for c in cards:
                rel = Path(c["path"]).relative_to(vault)
                domain = next(p for p in rel.parts if p[:2].isdigit())
                grouped.setdefault(domain, []).append(c)
                c["_cluster_id"] = domain
            result.cards_clustered = len(cards)
            result.clusters_count = len(grouped)
            return grouped

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            run_pass(vault_root=vault, dry_run=False)

        positions = json.loads(
            (state / "reflection_positions.json").read_text(encoding="utf-8")
        )
        clusters = positions["clusters"]

        # 3 clusters: 30_Biz / 20_Health / 00_Buffer
        assert len(clusters) == 3
        # Each cluster has size matching member count
        sizes = sorted(c["size"] for c in clusters)
        assert sizes == [1, 2, 2]  # 1 profile, 2 health, 2 biz

        # No back-fill happened → all stances null
        all_cards = [card for c in clusters for card in c["cards"]]
        assert all(card["stance"] is None for card in all_cards)
        assert all(not card["is_backfilled"] for card in all_cards)


class TestPipelineWithMockedLLM:
    """LLM-using path: stages 3 + 4 fire with deterministic mocks.
    Confirms the full state-file output shape when LLMs return
    something sensible."""

    def test_full_pass_with_namer_and_extractor(self, synth_vault):
        from daemon.reflection_pass import run_pass

        vault, state = synth_vault

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            grouped: dict[str, list] = {}
            for c in cards:
                rel = Path(c["path"]).relative_to(vault)
                domain = next(p for p in rel.parts if p[:2].isdigit())
                grouped.setdefault(domain, []).append(c)
                c["_cluster_id"] = domain
            result.cards_clustered = len(cards)
            result.clusters_count = len(grouped)
            return grouped

        # Mock namer: returns name based on first card's title
        def fake_namer(titles):
            t = titles[0].lower()
            if "pricing" in t:
                return "pricing_strategy"
            if "b1" in t or "thiamine" in t:
                return "b1_thiamine_therapy"
            return "personal_master"

        # Mock extractor: returns claim + question for each card
        def fake_extractor(title, body):
            return {
                "claim_summary": f"Stance derived from: {title[:30]}",
                "open_questions": [f"What about {title[:20]}?"],
            }

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            result = run_pass(
                vault_root=vault, dry_run=False,
                namer=fake_namer,
                extractor=fake_extractor,
            )

        # Counters reflect LLM stages firing
        assert result.cluster_names_resolved == 3
        assert result.backfill_completed == 5

        # Positions file shows back-filled stances + cluster names
        positions = json.loads(
            (state / "reflection_positions.json").read_text(encoding="utf-8")
        )
        clusters = positions["clusters"]
        assert all(c.get("topic_cluster") for c in clusters)
        all_cards = [card for c in clusters for card in c["cards"]]
        assert all(card["is_backfilled"] for card in all_cards)
        assert all(card["stance"] for card in all_cards)

        # Writeback preview shows additions
        preview = json.loads(
            (state / "reflection_writeback_preview.json").read_text(encoding="utf-8")
        )
        assert preview["cards_would_be_modified"] == 5
        for diff in preview["diffs"]:
            assert "position_signal" in diff["additions"]
            assert "open_questions" in diff["additions"]
            assert "reflection" in diff["additions"]


class TestMCPToolsReadE2E:
    """Once daemon has run, MCP tools should return real content."""

    def test_check_consistency_finds_right_cluster(self, synth_vault):
        from daemon.reflection_pass import run_pass
        from mcp_server.tools.check_consistency import check_consistency

        vault, state = synth_vault

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            grouped: dict[str, list] = {}
            for c in cards:
                rel = Path(c["path"]).relative_to(vault)
                domain = next(p for p in rel.parts if p[:2].isdigit())
                grouped.setdefault(domain, []).append(c)
                c["_cluster_id"] = domain
            result.cards_clustered = len(cards)
            result.clusters_count = len(grouped)
            return grouped

        def fake_namer(titles):
            t = titles[0].lower()
            if "pricing" in t: return "pricing_strategy"
            if "b1" in t or "thiamine" in t: return "b1_thiamine_therapy"
            return "personal_master"

        def fake_extractor(title, body):
            return {
                "claim_summary": f"Stance: {title}",
                "open_questions": [],
            }

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            run_pass(
                vault_root=vault, dry_run=False,
                namer=fake_namer, extractor=fake_extractor,
            )

        # Statement about pricing → match pricing cluster
        result = check_consistency(statement="going with pricing strategy")
        assert result["_status"] == "ok"
        assert len(result["contradictions"]) >= 1
        assert result["contradictions"][0]["topic_cluster"] == "pricing_strategy"
        # Most recent first (DESC by date) — late_pricing is 2026-03-15
        assert "late_pricing" in result["contradictions"][0]["card_path"] \
            or "late" in result["contradictions"][0]["card_path"]

    def test_get_position_drift_chronological(self, synth_vault):
        from daemon.reflection_pass import run_pass
        from mcp_server.tools.get_position_drift import get_position_drift

        vault, state = synth_vault

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            grouped: dict[str, list] = {}
            for c in cards:
                rel = Path(c["path"]).relative_to(vault)
                domain = next(p for p in rel.parts if p[:2].isdigit())
                grouped.setdefault(domain, []).append(c)
                c["_cluster_id"] = domain
            result.cards_clustered = len(cards)
            result.clusters_count = len(grouped)
            return grouped

        def fake_namer(titles):
            t = titles[0].lower()
            if "pricing" in t: return "pricing_strategy"
            if "b1" in t or "thiamine" in t: return "b1_thiamine_therapy"
            return "personal_master"

        def fake_extractor(title, body):
            return {"claim_summary": f"Stance: {title}", "open_questions": []}

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            run_pass(
                vault_root=vault, dry_run=False,
                namer=fake_namer, extractor=fake_extractor,
            )

        result = get_position_drift(topic="pricing")
        assert result["_status"] == "ok"
        # 2 cards in pricing cluster, both back-filled
        assert len(result["trajectory"]) == 2
        # Chronological: early first, late second
        assert result["trajectory"][0]["started"] == "2026-01-15"
        assert result["trajectory"][1]["started"] == "2026-03-15"
        # ended chains correctly
        assert result["trajectory"][0]["ended"] == "2026-03-15"
        assert result["trajectory"][1]["ended"] is None

    def test_find_open_threads_state_present(self, synth_vault):
        from daemon.reflection_pass import run_pass
        from mcp_server.tools.find_open_threads import find_open_threads

        vault, state = synth_vault

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            grouped: dict[str, list] = {}
            for c in cards:
                rel = Path(c["path"]).relative_to(vault)
                domain = next(p for p in rel.parts if p[:2].isdigit())
                grouped.setdefault(domain, []).append(c)
                c["_cluster_id"] = domain
            result.cards_clustered = len(cards)
            result.clusters_count = len(grouped)
            return grouped

        def fake_extractor(title, body):
            # Each card gets a unique question
            return {
                "claim_summary": "Stance",
                "open_questions": [f"unique_question_about_{title.replace(' ', '_')}_unresolved"],
            }

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            run_pass(
                vault_root=vault, dry_run=False,
                extractor=fake_extractor,
            )

        # All cards have unique questions — none get resolved by
        # later cards (titles differ enough that token overlap < 0.75).
        # So all back-filled cards should be flagged as open-thread.
        result = find_open_threads()
        assert result["_status"] == "ok"
        assert result["total_open_threads"] >= 1


class TestStateFilePersistence:
    """Re-running the pass should reuse caches."""

    def test_namer_cache_hits_on_rerun(self, synth_vault):
        from daemon.reflection_pass import run_pass

        vault, state = synth_vault

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            grouped: dict[str, list] = {}
            for c in cards:
                rel = Path(c["path"]).relative_to(vault)
                domain = next(p for p in rel.parts if p[:2].isdigit())
                grouped.setdefault(domain, []).append(c)
                c["_cluster_id"] = domain
            result.cards_clustered = len(cards)
            result.clusters_count = len(grouped)
            return grouped

        namer_calls = []
        def fake_namer(titles):
            namer_calls.append(titles[0])
            return f"named_{titles[0][:10].replace(' ', '_').lower()}"

        # First pass: namer fires for each cluster
        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            run_pass(
                vault_root=vault, dry_run=False,
                namer=fake_namer,
            )

        first_call_count = len(namer_calls)
        assert first_call_count == 3  # 3 clusters

        # Second pass: same cluster membership → cache hits, no new
        # namer calls
        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            run_pass(
                vault_root=vault, dry_run=False,
                namer=fake_namer,
            )

        # No new calls
        assert len(namer_calls) == first_call_count
