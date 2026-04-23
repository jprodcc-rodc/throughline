"""Tests for U22 prompt family loader.

Covers:
- Exact-match load returns the fenced body of the right file.
- Missing family falls back through the family chain to generic.
- Fully missing (name, variant) raises FileNotFoundError with a
  helpful message listing the files tried.
- available_variants() discovers variants per name+family.
- _extract_prompt_body handles the standard `# Title \n ```body``` \n notes`
  shape, the no-fence shape, and the unclosed-fence shape defensively.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import prompts as p


# ------- _extract_prompt_body unit tests -------

class TestExtractPromptBody:
    def test_fenced_block_extracted(self):
        text = (
            "# Title\n"
            "some docs\n"
            "---\n"
            "```\n"
            "ACTUAL PROMPT LINE 1\n"
            "ACTUAL PROMPT LINE 2\n"
            "```\n"
            "---\n"
            "notes tail\n"
        )
        assert p._extract_prompt_body(text) == (
            "ACTUAL PROMPT LINE 1\n"
            "ACTUAL PROMPT LINE 2"
        )

    def test_fence_with_language_hint(self):
        text = "# T\n```text\nBODY\n```\n"
        assert p._extract_prompt_body(text) == "BODY"

    def test_no_fence_returns_stripped_whole(self):
        text = "No fences here.\nJust prose."
        assert p._extract_prompt_body(text) == "No fences here.\nJust prose."

    def test_unclosed_fence_returns_whole_file(self):
        text = "# Title\n```\nUNCLOSED\nmore text"
        # Should fall back to full file rather than truncate.
        assert "UNCLOSED" in p._extract_prompt_body(text)


# ------- load_prompt integration tests against real files -------

class TestLoadPrompt:
    def test_claude_variant_loads(self):
        body = p.load_prompt("refiner", "normal", "claude")
        # Claude variant uses XML tags.
        assert "<task>" in body
        assert "<output_schema>" in body
        assert "<body_skeleton>" in body
        # Shared invariants: six-section headings must be present
        # whether the wrapper is XML or Markdown.
        assert "# Scene & Pain Point" in body
        assert "# Length Summary" in body

    def test_generic_variant_loads(self):
        body = p.load_prompt("refiner", "normal", "generic")
        # Generic variant uses Markdown headers, no XML wrapper.
        assert "## Task" in body
        assert "## Output Schema" in body
        assert "<task>" not in body
        # Same six-section content, just wrapped differently.
        assert "# Scene & Pain Point" in body
        assert "# Length Summary" in body

    def test_gpt_falls_back_to_generic(self):
        # There is no refiner.normal.gpt.md yet — loader should fall
        # through the family chain and return the generic body.
        body_gpt = p.load_prompt("refiner", "normal", "gpt")
        body_generic = p.load_prompt("refiner", "normal", "generic")
        assert body_gpt == body_generic

    def test_gemini_falls_back_to_generic(self):
        body_gemini = p.load_prompt("refiner", "normal", "gemini")
        body_generic = p.load_prompt("refiner", "normal", "generic")
        assert body_gemini == body_generic

    def test_nonexistent_variant_raises(self):
        with pytest.raises(FileNotFoundError) as excinfo:
            p.load_prompt("refiner", "nonesuch", "claude")
        msg = str(excinfo.value)
        assert "refiner" in msg
        assert "nonesuch" in msg
        # Error message must list what was tried.
        assert "Tried fallback chain" in msg

    def test_unknown_family_still_tries_generic(self):
        # Novel family name (e.g. future 'mistral') should fall to generic.
        body = p.load_prompt("refiner", "normal", "mistral")
        expected = p.load_prompt("refiner", "normal", "generic")
        assert body == expected


# ------- available_variants -------

class TestAvailableVariants:
    def test_returns_normal_for_claude(self):
        variants = p.available_variants("refiner", "claude")
        assert "normal" in variants

    def test_returns_normal_for_generic(self):
        variants = p.available_variants("refiner", "generic")
        assert "normal" in variants

    def test_returns_rag_optimized_for_claude(self):
        variants = p.available_variants("refiner", "claude")
        assert "rag_optimized" in variants

    def test_returns_rag_optimized_for_generic(self):
        variants = p.available_variants("refiner", "generic")
        assert "rag_optimized" in variants

    def test_returns_sorted(self):
        variants = p.available_variants("refiner", "claude")
        assert variants == sorted(variants)

    def test_unknown_name_returns_empty(self):
        variants = p.available_variants("this-prompt-does-not-exist", "claude")
        assert variants == []

    def test_full_tier_matrix_complete(self):
        """All four tier variants should be available after C3 ships."""
        for fam in ("claude", "generic"):
            vs = set(p.available_variants("refiner", fam))
            assert {"skim", "normal", "deep", "rag_optimized"}.issubset(vs), (
                f"{fam} missing variants: {{skim, normal, deep, rag_optimized}} - {vs}"
            )


class TestSkimVariant:
    def test_claude_loads(self):
        body = p.load_prompt("refiner", "skim", "claude")
        assert "<task>" in body
        assert "flashcard" in body.lower()
        assert "600 characters" in body  # length cap
        # No 6-section skeleton in skim.
        assert "# Scene & Pain Point" not in body

    def test_generic_loads(self):
        body = p.load_prompt("refiner", "skim", "generic")
        assert "## Task" in body
        assert "flashcard" in body.lower()

    def test_drop_on_brainstorm_present(self):
        for fam in ("claude", "generic"):
            body = p.load_prompt("refiner", "skim", fam)
            assert '"dropped"' in body
            assert "brainstorm_no_decision" in body


class TestDeepVariant:
    def test_claude_loads(self):
        body = p.load_prompt("refiner", "deep", "claude")
        assert "<task>" in body
        # Deep has sidebar sections.
        assert "# Self-Critique" in body
        assert "# Cross-References" in body
        assert "# Open Questions" in body
        # And the full 6-section body remains.
        assert "# Scene & Pain Point" in body

    def test_generic_loads(self):
        body = p.load_prompt("refiner", "deep", "generic")
        assert "## Task" in body
        assert "Self-Critique" in body

    def test_top_level_sidebar_fields(self):
        """Deep tier emits self_critique / cross_refs / open_questions
        as top-level JSON fields so the daemon can index without
        Markdown parsing."""
        for fam in ("claude", "generic"):
            body = p.load_prompt("refiner", "deep", fam)
            for field in ("self_critique", "cross_refs", "open_questions"):
                assert field in body, f"{fam} deep missing field {field}"


class TestFullTierFallbackBehaviour:
    """User picks an arbitrary family (gpt/gemini/grok) with any tier —
    the loader must always return SOMETHING usable via generic fallback."""

    @pytest.mark.parametrize("family", ["gpt", "gemini", "claude", "generic"])
    @pytest.mark.parametrize("variant", ["skim", "normal", "deep", "rag_optimized"])
    def test_every_family_x_variant_resolves(self, family, variant):
        body = p.load_prompt("refiner", variant, family)
        assert len(body) > 100  # non-empty, non-stub


# ------- rag_optimized variant (U25) -------

class TestRagOptimizedVariant:
    def test_claude_variant_loads(self):
        body = p.load_prompt("refiner", "rag_optimized", "claude")
        # Claude wrapper retained.
        assert "<task>" in body
        assert "<priorities>" in body
        assert "<body_format>" in body
        # Dense retrieval-card schema.
        assert "entities" in body
        assert "claims" in body
        # Intentional absence of six-section scaffolding.
        assert "Scene & Pain Point" not in body
        assert "Length Summary" not in body
        assert "Core Knowledge & First Principles" not in body

    def test_generic_variant_loads(self):
        body = p.load_prompt("refiner", "rag_optimized", "generic")
        assert "## Task" in body
        assert "## Priorities" in body
        assert "<task>" not in body
        assert "entities" in body
        assert "claims" in body
        assert "Scene & Pain Point" not in body

    def test_gpt_falls_back_to_generic(self):
        body_gpt = p.load_prompt("refiner", "rag_optimized", "gpt")
        body_generic = p.load_prompt("refiner", "rag_optimized", "generic")
        assert body_gpt == body_generic

    def test_body_format_documented(self):
        """The body_markdown contract must be machine-parseable: the
        downstream daemon retention gate reads `entities` + `claims`,
        and the embedder chunks on the bullet list. The prompt must
        therefore document this format literally."""
        for family in ("claude", "generic"):
            body = p.load_prompt("refiner", "rag_optimized", family)
            # The prompt must spell out the body shape.
            assert "Entities:" in body, (
                f"{family} variant must include 'Entities:' line in body_format"
            )

    def test_anti_pollution_rule_present(self):
        """Dense retrieval is precision-sensitive; hallucinated claims
        ruin embeddings. Both variants must carry the anti-pollution
        rule explicitly."""
        for family in ("claude", "generic"):
            body = p.load_prompt("refiner", "rag_optimized", family)
            assert "invent" in body.lower() or "fabrication" in body.lower()

    def test_drop_on_pure_speculation(self):
        """RAG-only mode must not emit speculation-only cards — they
        poison the retrieval index. Both variants must instruct the
        model to emit a dropped-card sentinel instead."""
        for family in ("claude", "generic"):
            body = p.load_prompt("refiner", "rag_optimized", family)
            assert '"dropped"' in body
            assert '"only_speculation"' in body

    def test_single_call_cost_documented(self):
        """The cost profile (~$0.001/conv, single call, no slicer/router)
        is the entire point of this variant. Keep the mention in the
        prompt file so future contributors see it."""
        for family in ("claude", "generic"):
            body = p.load_prompt("refiner", "rag_optimized", family)
            assert "single" in body.lower() or "one" in body.lower()


# ------- family fallback chain -------

class TestFamilyFallback:
    def test_claude_chain(self):
        assert p.FAMILY_FALLBACK["claude"] == ["claude", "generic"]

    def test_generic_terminal(self):
        # generic does not fall back to anything else.
        assert p.FAMILY_FALLBACK["generic"] == ["generic"]

    def test_all_non_generic_end_in_generic(self):
        for fam, chain in p.FAMILY_FALLBACK.items():
            if fam == "generic":
                continue
            assert chain[-1] == "generic", (
                f"{fam} fallback chain does not end in generic: {chain}"
            )


# ------- consistency between variants -------

class TestFamilyConsistency:
    """Both family variants of the same (name, variant) must preserve
    the load-bearing content invariants — section headings, JSON schema
    fields, the anti-pollution rule. Only the *wrapper* differs."""

    def test_same_taxonomy_tokens(self):
        claude = p.load_prompt("refiner", "normal", "claude")
        generic = p.load_prompt("refiner", "normal", "generic")
        for placeholder in ("{valid_x}", "{valid_y}", "{valid_z}"):
            assert placeholder in claude, f"claude missing {placeholder}"
            assert placeholder in generic, f"generic missing {placeholder}"

    def test_same_section_headings(self):
        claude = p.load_prompt("refiner", "normal", "claude")
        generic = p.load_prompt("refiner", "normal", "generic")
        for heading in (
            "# Scene & Pain Point",
            "# Core Knowledge & First Principles",
            "# Detailed Execution Plan",
            "# Pitfalls & Boundaries",
            "# Insights & Mental Models",
            "# Length Summary",
        ):
            assert heading in claude, f"claude missing section: {heading}"
            assert heading in generic, f"generic missing section: {heading}"

    def test_same_knowledge_identity_values(self):
        claude = p.load_prompt("refiner", "normal", "claude")
        generic = p.load_prompt("refiner", "normal", "generic")
        for ki in (
            "universal",
            "personal_persistent",
            "personal_ephemeral",
            "contextual",
        ):
            assert ki in claude
            assert ki in generic

    def test_same_provenance_tags(self):
        claude = p.load_prompt("refiner", "normal", "claude")
        generic = p.load_prompt("refiner", "normal", "generic")
        for tag in (
            "user_stated",
            "user_confirmed",
            "llm_unverified",
            "llm_speculation",
        ):
            assert tag in claude
            assert tag in generic


class TestRagOptimizedFamilyConsistency:
    """Same load-bearing invariants the Normal variant has, applied to
    RAG-optimized — the wrapper differs, the output schema must not."""

    def test_same_taxonomy_tokens(self):
        claude = p.load_prompt("refiner", "rag_optimized", "claude")
        generic = p.load_prompt("refiner", "rag_optimized", "generic")
        for placeholder in ("{valid_x}", "{valid_y}", "{valid_z}"):
            assert placeholder in claude
            assert placeholder in generic

    def test_same_schema_fields(self):
        claude = p.load_prompt("refiner", "rag_optimized", "claude")
        generic = p.load_prompt("refiner", "rag_optimized", "generic")
        for field in (
            "title", "entities", "claims",
            "primary_x", "visible_x_tags", "form_y", "z_axis",
            "knowledge_identity", "body_markdown",
            "claim_sources", "pack_meta",
        ):
            assert field in claude, f"claude rag_optimized missing {field}"
            assert field in generic, f"generic rag_optimized missing {field}"

    def test_same_knowledge_identity_values(self):
        claude = p.load_prompt("refiner", "rag_optimized", "claude")
        generic = p.load_prompt("refiner", "rag_optimized", "generic")
        for ki in (
            "universal", "personal_persistent",
            "personal_ephemeral", "contextual",
        ):
            assert ki in claude
            assert ki in generic

    def test_same_provenance_tags(self):
        claude = p.load_prompt("refiner", "rag_optimized", "claude")
        generic = p.load_prompt("refiner", "rag_optimized", "generic")
        for tag in (
            "user_stated", "user_confirmed",
            "llm_unverified", "llm_speculation",
        ):
            assert tag in claude
            assert tag in generic
