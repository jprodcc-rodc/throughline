"""Tests for daemon.card_body_parser.

Coverage targets:
- English-only headers (per public refiner prompt schema)
- Bilingual emoji + Chinese + English-in-parens headers (per
  author's real vault)
- Mixed-dialect cards (paranoia case; should still produce
  consistent canonical names)
- Recall callout strip (the ``> [!info] 🧠 神经突触连结`` block must
  not leak into the last section's content)
- H2 sub-headers don't split sections
- Unknown headers fall through to ``_unknown_<slug>``
- Edge cases: empty body, no headers, preamble before first header,
  duplicate headers
- ``get_section`` convenience accessor

Each canonical section name we test for here is one a downstream
Reflection Pass stage will need. If a stage adds a new section
need, add a test here first then update the canonical map.
"""
from __future__ import annotations

import textwrap

import pytest


# ---------- Imports work in minimal env ----------

def test_module_imports():
    from daemon.card_body_parser import parse_body_sections, get_section

    assert callable(parse_body_sections)
    assert callable(get_section)


# ---------- English-only headers (public schema) ----------

class TestEnglishHeaders:
    def test_full_english_card_parses(self):
        from daemon.card_body_parser import parse_body_sections

        body = textwrap.dedent(
            """\
            # Scene & Pain Point
            Pain content here.

            # Core Knowledge & First Principles
            First-principles body.

            # Detailed Execution Plan
            Execution body.

            # Pitfalls & Boundaries
            Pitfall body.

            # Insights & Mental Models
            Mental model body.

            # Length Summary
            5 paragraphs.
            """
        )
        sections = parse_body_sections(body)
        assert "scene_and_pain_point" in sections
        assert "first_principles" in sections
        assert "execution_plan" in sections
        assert "pitfalls_and_boundaries" in sections
        assert "mental_models" in sections
        assert "length_summary" in sections

        assert sections["first_principles"].startswith("First-principles")

    def test_sidebar_headers(self):
        from daemon.card_body_parser import parse_body_sections

        body = textwrap.dedent(
            """\
            # Scene & Pain Point
            Body.

            ---

            # Self-Critique
            Critique body.

            # Cross-References
            Refs body.

            # Open Questions
            - Q1?
            - Q2?
            """
        )
        sections = parse_body_sections(body)
        assert "self_critique" in sections
        assert "cross_references" in sections
        assert "open_questions" in sections
        assert "Q1?" in sections["open_questions"]


# ---------- Bilingual headers (real author vault) ----------

class TestBilingualHeaders:
    def test_full_bilingual_card_parses(self):
        from daemon.card_body_parser import parse_body_sections

        body = textwrap.dedent(
            """\
            # 🎯 场景与痛点 (Context & Anchor)
            场景内容

            # 🧠 核心知识与底层原理 (First Principles)
            原理内容

            # 🛠️ 详细执行方案 (Execution & Code)
            执行方案

            # 🚧 避坑与边界 (Pitfalls & Gotchas)
            避坑内容

            # 💡 心智模型 (Mental Models)
            心智模型

            # 📏 篇幅总结
            6 段。
            """
        )
        sections = parse_body_sections(body)
        # Same canonical names as the English-only dialect — this
        # is the whole point of normalization.
        assert "scene_and_pain_point" in sections
        assert "first_principles" in sections
        assert "execution_plan" in sections
        assert "pitfalls_and_boundaries" in sections
        assert "mental_models" in sections
        assert "length_summary" in sections

    def test_execution_variant_without_code(self):
        """Some real cards use '(Execution)' instead of
        '(Execution & Code)'. Both should resolve to the same
        canonical section."""
        from daemon.card_body_parser import parse_body_sections

        body = "# 🛠️ 详细执行方案 (Execution)\nbody"
        sections = parse_body_sections(body)
        assert "execution_plan" in sections

    def test_chinese_only_headers(self):
        """Many real cards in the author's vault use Chinese-only
        headers without any English parens. Should canonicalize the
        same way as the bilingual variants. Calibrated 2026-04-28
        against real-vault dump in
        docs/POSITION_METADATA_SCHEMA.md § "Vault format addendum"."""
        from daemon.card_body_parser import parse_body_sections

        body = textwrap.dedent(
            """\
            # 🎯 场景与痛点
            场景。

            # 🧠 核心知识与底层原理
            原理。

            # 🛠️ 详细执行方案
            执行。

            # 🚧 避坑与迭代路径
            避坑。

            # 💡 启发与思维模型
            模型。
            """
        )
        sections = parse_body_sections(body)
        assert "scene_and_pain_point" in sections
        assert "first_principles" in sections
        assert "execution_plan" in sections
        # Chinese-only "避坑与迭代路径" maps to same canonical as
        # "避坑与边界 (Pitfalls & Gotchas)" since both fill the
        # role of capturing what could go wrong.
        assert "pitfalls_and_boundaries" in sections
        # "启发与思维模型" maps to mental_models (same as
        # "心智模型 (Mental Models)").
        assert "mental_models" in sections


# ---------- Recall callout stripping ----------

class TestRecallCalloutStrip:
    def test_strips_callout_from_last_section(self):
        """The running daemon appends a ``> [!info] 🧠 神经突触连结``
        block to body. Phase 2 must not treat it as user content."""
        from daemon.card_body_parser import parse_body_sections

        body = textwrap.dedent(
            """\
            # 📏 篇幅总结
            4 次手术。

            > [!info] 🧠 神经突触连结 (google/gemini-3-flash-preview):
            > ⏱️ Rerank 4.5s + LLM 3.9s = 8.4s
            > - [[some other card]] : *some recall annotation*
            > - [[another card]] : *another annotation*
            """
        )
        sections = parse_body_sections(body)
        last_content = sections["length_summary"]
        assert "4 次手术" in last_content
        assert "神经突触连结" not in last_content
        assert "Rerank" not in last_content

    def test_callout_stripped_even_in_middle_section(self):
        """If the callout somehow lands in a non-last section
        (rare), still strip — DOTALL match goes to end of body."""
        from daemon.card_body_parser import parse_body_sections

        body = textwrap.dedent(
            """\
            # Scene & Pain Point
            Body.
            > [!info] 🧠 神经突触连结 (model):
            > recall content
            """
        )
        sections = parse_body_sections(body)
        # Callout should be removed from section content.
        assert "神经突触连结" not in sections.get("scene_and_pain_point", "")


# ---------- H2 sub-headers should not split sections ----------

def test_h2_does_not_split_section():
    from daemon.card_body_parser import parse_body_sections

    body = textwrap.dedent(
        """\
        # 🛠️ 详细执行方案 (Execution & Code)
        Setup steps.

        ## Sub-section A
        Sub content A.

        ## Sub-section B
        Sub content B.

        # 🚧 避坑与边界 (Pitfalls & Gotchas)
        Warning content.
        """
    )
    sections = parse_body_sections(body)
    exec_content = sections["execution_plan"]
    # H2s and their content are part of the execution_plan section.
    assert "Sub-section A" in exec_content
    assert "Sub-section B" in exec_content
    assert "Warning content" in sections["pitfalls_and_boundaries"]


# ---------- Unknown headers ----------

def test_unknown_header_uses_unknown_prefix():
    from daemon.card_body_parser import parse_body_sections

    body = textwrap.dedent(
        """\
        # 🎯 场景与痛点 (Context & Anchor)
        Known body.

        # Some Custom Section That Isn't In The Map
        Custom body.
        """
    )
    sections = parse_body_sections(body)
    assert "scene_and_pain_point" in sections
    unknown_keys = [k for k in sections if k.startswith("_unknown_")]
    assert len(unknown_keys) == 1
    assert "Custom body." in sections[unknown_keys[0]]


# ---------- Edge cases ----------

class TestEdgeCases:
    def test_empty_body_returns_empty_dict(self):
        from daemon.card_body_parser import parse_body_sections

        assert parse_body_sections("") == {}

    def test_whitespace_only_body_returns_empty_dict(self):
        from daemon.card_body_parser import parse_body_sections

        assert parse_body_sections("   \n  \n") == {}

    def test_no_headers_treats_as_preamble(self):
        from daemon.card_body_parser import parse_body_sections

        body = "Just some paragraph with no markdown headers at all."
        sections = parse_body_sections(body)
        assert "_preamble" in sections
        assert sections["_preamble"] == body.strip()

    def test_preamble_before_first_header(self):
        from daemon.card_body_parser import parse_body_sections

        body = textwrap.dedent(
            """\
            (💡 这是 TLDR 段)

            # 🎯 场景与痛点 (Context & Anchor)
            场景。
            """
        )
        sections = parse_body_sections(body)
        assert "_preamble" in sections
        assert "TLDR" in sections["_preamble"]
        assert "scene_and_pain_point" in sections

    def test_duplicate_headers_last_wins(self):
        """Hand-written notes occasionally have duplicated H1
        headers. Last occurrence wins so we don't silently merge
        unrelated content."""
        from daemon.card_body_parser import parse_body_sections

        body = textwrap.dedent(
            """\
            # 🎯 场景与痛点 (Context & Anchor)
            First occurrence.

            # 🎯 场景与痛点 (Context & Anchor)
            Second occurrence.
            """
        )
        sections = parse_body_sections(body)
        assert "First occurrence" not in sections["scene_and_pain_point"]
        assert "Second occurrence" in sections["scene_and_pain_point"]


# ---------- get_section convenience accessor ----------

class TestGetSection:
    def test_returns_section_when_present(self):
        from daemon.card_body_parser import get_section

        body = "# 🧠 核心知识与底层原理 (First Principles)\n\noriginal content"
        assert "original content" in get_section(body, "first_principles")

    def test_returns_none_when_absent(self):
        from daemon.card_body_parser import get_section

        body = "# 🎯 场景与痛点 (Context & Anchor)\n\nbody"
        assert get_section(body, "open_questions") is None

    def test_returns_none_for_empty_body(self):
        from daemon.card_body_parser import get_section

        assert get_section("", "first_principles") is None


# ---------- Real-vault smoke shape ----------

def test_real_vault_card_shape():
    """Test against a faithful copy of the structure observed in
    the author's vault during the 2026-04-28 smoke check
    (vault_smoke_check.py output sample). Catches regressions if
    the parser drifts from the actual vault format."""
    from daemon.card_body_parser import parse_body_sections

    body = textwrap.dedent(
        """\
        # 🎯 场景与痛点 (Context & Anchor)
        2026-04-14 采访核实的完整手术史。

        # 🛠️ 详细执行方案 (Execution)

        | # | 手术 | 时间 | 原因 |
        |---|---|---|---|
        | 1 | 鼻中隔偏曲矫正 | 2022 年底 | 28 年偏曲，改善 OSA |
        | 2 | 袖状胃切除术 | 2024 年 12 月底 | 肥胖、代谢综合征 |

        # 🚧 避坑与边界 (Pitfalls & Gotchas)
        - 从未做过 FESS 鼻窦手术
        - 袖状胃术后需终身营养监测和补充

        # 📏 篇幅总结
        4 次手术（含 1 次计划中），2026-04 采访核实。


        > [!info] 🧠 神经突触连结 (google/gemini-3-flash-preview):
        > ⏱️ Rerank 4.5s + LLM 3.9s = 8.4s
        > - [[利用历史手术记录构建难治性鼻窦炎医保报销证据链]] : *some annotation*
        """
    )
    sections = parse_body_sections(body)
    assert "scene_and_pain_point" in sections
    assert "execution_plan" in sections
    assert "pitfalls_and_boundaries" in sections
    assert "length_summary" in sections
    # Recall callout stripped:
    assert "神经突触连结" not in sections["length_summary"]
    # Pitfalls section captures the bullet list:
    assert "FESS 鼻窦手术" in sections["pitfalls_and_boundaries"]
