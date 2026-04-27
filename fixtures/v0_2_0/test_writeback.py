"""Tests for daemon.writeback (preview-only stage 8 module).

Coverage:
- _extract_reasoning_from_body parses bullets from First Principles
  section (English + Chinese variants), respects 5-bullet cap,
  drops too-short / too-long entries
- assemble_position_signal returns None when no _backfill, builds
  full schema when backfill present, falls back to cluster_<N>
  label when no name available
- assemble_reflection: status open_thread when flagged, concluded
  otherwise, None when no signal at all
- compute_writeback_diff: skips fields that already exist in
  frontmatter, includes only meaningful additions, always refreshes
  reflection
- build_writeback_preview filters out cards with empty additions
"""
from __future__ import annotations

import textwrap

import pytest


# ---------- _extract_reasoning_from_body ----------

class TestExtractReasoning:
    def test_english_first_principles_bullets(self):
        from daemon.writeback import _extract_reasoning_from_body

        body = textwrap.dedent(
            """\
            # Scene & Pain Point
            Pain.

            # Core Knowledge & First Principles
            - LTV math is unpredictable in early stage
            - Churn risk severe pre-PMF
            - Runway can't tolerate revenue volatility

            # Detailed Execution Plan
            steps.
            """
        )
        out = _extract_reasoning_from_body(body)
        assert "LTV math is unpredictable in early stage" in out
        assert "Churn risk severe pre-PMF" in out
        assert "Runway can't tolerate revenue volatility" in out

    def test_chinese_first_principles_bullets(self):
        from daemon.writeback import _extract_reasoning_from_body

        body = textwrap.dedent(
            """\
            # 🧠 核心知识与底层原理 (First Principles)
            - LTV 数学不可预测
            - 早期 PMF 前流失风险高
            - 跑道经不起营收波动

            # 🛠️ 详细执行方案 (Execution)
            执行。
            """
        )
        out = _extract_reasoning_from_body(body)
        assert "LTV 数学不可预测" in out
        assert "早期 PMF 前流失风险高" in out

    def test_caps_at_5_bullets(self):
        from daemon.writeback import _extract_reasoning_from_body

        body = "# Core Knowledge & First Principles\n" + "\n".join(
            f"- bullet {i}" for i in range(20)
        )
        out = _extract_reasoning_from_body(body)
        assert len(out) == 5

    def test_drops_too_short_bullets(self):
        from daemon.writeback import _extract_reasoning_from_body

        body = textwrap.dedent(
            """\
            # Core Knowledge & First Principles
            - x
            - too short
            - This is a properly-sized first principle.
            """
        )
        out = _extract_reasoning_from_body(body)
        # "x" rejected (< 3 chars); rest kept
        assert "x" not in out
        assert "too short" in out
        assert "This is a properly-sized first principle." in out

    def test_drops_too_long_bullets(self):
        """Multi-paragraph 'bullets' (rare but possible) get dropped
        — they're not 'reasoning' in the structured sense."""
        from daemon.writeback import _extract_reasoning_from_body

        too_long = "x " * 200  # 400 chars
        body = (
            "# Core Knowledge & First Principles\n"
            f"- short bullet\n"
            f"- {too_long}\n"
        )
        out = _extract_reasoning_from_body(body)
        assert "short bullet" in out
        assert too_long.strip() not in out

    def test_no_first_principles_section_returns_empty(self):
        from daemon.writeback import _extract_reasoning_from_body

        body = "# Some Other Section\n- bullet\n"
        assert _extract_reasoning_from_body(body) == []

    def test_section_with_no_bullets_returns_empty(self):
        from daemon.writeback import _extract_reasoning_from_body

        body = (
            "# Core Knowledge & First Principles\n"
            "Just prose, no bullets here.\n"
        )
        assert _extract_reasoning_from_body(body) == []

    def test_numbered_list_also_recognized(self):
        from daemon.writeback import _extract_reasoning_from_body

        body = textwrap.dedent(
            """\
            # Core Knowledge & First Principles
            1. First numbered item
            2. Second numbered item
            """
        )
        out = _extract_reasoning_from_body(body)
        assert "First numbered item" in out
        assert "Second numbered item" in out


# ---------- assemble_position_signal ----------

class TestAssemblePositionSignal:
    def test_returns_none_when_no_backfill(self):
        from daemon.writeback import assemble_position_signal

        card = {"path": "a.md", "title": "A", "body": "x"}
        assert assemble_position_signal(card, None) is None

    def test_returns_none_when_no_claim_summary(self):
        from daemon.writeback import assemble_position_signal

        card = {
            "path": "a.md", "title": "A", "body": "x",
            "_backfill": {"claim_summary": "", "open_questions": []},
        }
        assert assemble_position_signal(card, None) is None

    def test_full_assembly_with_cluster_name(self):
        from daemon.writeback import assemble_position_signal

        card = {
            "path": "a.md", "title": "A",
            "body": (
                "# Core Knowledge & First Principles\n"
                "- reason 1\n- reason 2\n"
            ),
            "_backfill": {
                "claim_summary": "Use B1 daily",
                "open_questions": [],
            },
            "_cluster_id": 7,
        }
        ps = assemble_position_signal(card, "b1_thiamine_therapy")
        assert ps["topic_cluster"] == "b1_thiamine_therapy"
        assert ps["stance"] == "Use B1 daily"
        assert ps["reasoning"] == ["reason 1", "reason 2"]
        assert ps["confidence"] == "asserted"
        assert ps["emit_source"] == "refiner_inferred"
        assert ps["topic_assignment"] == "daemon_canonicalized"
        assert ps["conditions"] is None

    def test_no_cluster_name_uses_cluster_id_fallback(self):
        from daemon.writeback import assemble_position_signal

        card = {
            "path": "a.md", "title": "A", "body": "body",
            "_backfill": {"claim_summary": "X", "open_questions": []},
            "_cluster_id": 12,
        }
        ps = assemble_position_signal(card, None)
        assert ps["topic_cluster"] == "cluster_12"
        assert ps["topic_assignment"] == "daemon_clustered"

    def test_no_cluster_id_at_all(self):
        from daemon.writeback import assemble_position_signal

        card = {
            "path": "a.md", "title": "A", "body": "body",
            "_backfill": {"claim_summary": "X", "open_questions": []},
        }
        ps = assemble_position_signal(card, None)
        assert ps["topic_cluster"] == "unknown"


# ---------- assemble_reflection ----------

class TestAssembleReflection:
    def test_open_thread_status(self):
        from daemon.writeback import assemble_reflection

        card = {
            "_open_thread": True,
            "_open_thread_questions": ["q?"],
            "_backfill": {"claim_summary": "X", "open_questions": ["q?"]},
        }
        r = assemble_reflection(card)
        assert r["status"] == "open_thread"
        assert "last_pass" in r

    def test_concluded_status(self):
        from daemon.writeback import assemble_reflection

        card = {
            "_open_thread": False,
            "_open_thread_questions": [],
            "_backfill": {"claim_summary": "X", "open_questions": []},
        }
        r = assemble_reflection(card)
        assert r["status"] == "concluded"

    def test_none_when_no_signal(self):
        """Card with no stage-3/4/5 mutations → no reflection block.
        Don't write empty metadata."""
        from daemon.writeback import assemble_reflection

        card = {"path": "a.md", "title": "A", "body": "x"}
        assert assemble_reflection(card) is None


# ---------- compute_writeback_diff ----------

class TestComputeWritebackDiff:
    def test_full_writeback_for_empty_card(self):
        from daemon.writeback import compute_writeback_diff

        card = {
            "path": "a.md", "title": "A",
            "body": "# Core Knowledge & First Principles\n- r1\n- r2\n",
            "frontmatter": {"title": "A"},  # has title only
            "_backfill": {
                "claim_summary": "stance",
                "open_questions": ["q1?", "q2?"],
            },
            "_open_thread": True,
            "_open_thread_questions": ["q1?"],
            "_cluster_id": 3,
        }
        diff = compute_writeback_diff(card, "topic_x")

        assert diff["card_path"] == "a.md"
        assert "position_signal" in diff["additions"]
        assert "open_questions" in diff["additions"]
        assert diff["additions"]["open_questions"] == ["q1?", "q2?"]
        assert "reflection" in diff["additions"]
        assert diff["additions"]["reflection"]["status"] == "open_thread"

    def test_skips_existing_position_signal(self):
        """If frontmatter already has position_signal, don't
        overwrite — flag as skipped."""
        from daemon.writeback import compute_writeback_diff

        card = {
            "path": "a.md", "title": "A", "body": "body",
            "frontmatter": {
                "position_signal": {"topic_cluster": "existing"},
            },
            "_backfill": {
                "claim_summary": "would override but won't",
                "open_questions": [],
            },
            "_cluster_id": 1,
        }
        diff = compute_writeback_diff(card, "new_topic")
        assert "position_signal" in diff["skipped_fields"]
        assert "position_signal" not in diff["additions"]

    def test_skips_existing_open_questions(self):
        from daemon.writeback import compute_writeback_diff

        card = {
            "path": "a.md", "title": "A", "body": "body",
            "frontmatter": {"open_questions": ["pre-existing q?"]},
            "_backfill": {
                "claim_summary": "X",
                "open_questions": ["new q?"],
            },
            "_cluster_id": 1,
        }
        diff = compute_writeback_diff(card, None)
        assert "open_questions" in diff["skipped_fields"]
        assert "open_questions" not in diff["additions"]

    def test_reflection_always_overwrites(self):
        """reflection is daemon-managed metadata — last_pass is
        refreshed every pass even if a prior reflection exists."""
        from daemon.writeback import compute_writeback_diff

        card = {
            "path": "a.md", "title": "A", "body": "body",
            "frontmatter": {
                "reflection": {"status": "stale", "last_pass": "old"},
            },
            "_backfill": {"claim_summary": "X", "open_questions": []},
            "_open_thread": False,
            "_cluster_id": 1,
        }
        diff = compute_writeback_diff(card, None)
        assert "reflection" in diff["additions"]
        assert diff["additions"]["reflection"]["status"] == "concluded"

    def test_empty_card_produces_no_additions(self):
        """Card without back-fill or open-thread mutations produces
        empty additions — caller filters these out from preview."""
        from daemon.writeback import compute_writeback_diff

        card = {
            "path": "a.md", "title": "A", "body": "body",
            "frontmatter": {"title": "A"},
        }
        diff = compute_writeback_diff(card, None)
        assert diff["additions"] == {}


# ---------- build_writeback_preview ----------

class TestBuildPreview:
    def test_filters_out_unmodified_cards(self):
        from daemon.writeback import build_writeback_preview

        cards = [
            # Card 1: would be modified (has _backfill)
            {
                "path": "a.md", "title": "A", "body": "x",
                "frontmatter": {},
                "_backfill": {"claim_summary": "S", "open_questions": []},
                "_cluster_id": 0,
            },
            # Card 2: no signal, no addition
            {
                "path": "b.md", "title": "B", "body": "x",
                "frontmatter": {},
            },
        ]
        preview = build_writeback_preview(cards, {})
        assert len(preview) == 1
        assert preview[0]["card_path"] == "a.md"

    def test_uses_cluster_names_dict(self):
        from daemon.writeback import build_writeback_preview

        cards = [
            {
                "path": "a.md", "title": "A", "body": "x",
                "frontmatter": {},
                "_backfill": {"claim_summary": "S", "open_questions": []},
                "_cluster_id": 5,
            },
        ]
        preview = build_writeback_preview(cards, {"5": "named_topic"})
        assert preview[0]["additions"]["position_signal"]["topic_cluster"] == "named_topic"
