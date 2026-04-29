"""P0-2 Task 2.2 scaffold: structural contract for the claim
extraction prompt.

The prompt itself is at `prompts/en/claim_extraction.md`. These
tests verify the prompt has the structural sections P0-2 Task 2.2
requires:

    - System prompt block describing what to extract
    - At least 5 worked examples (per spec)
    - Schema field definitions (subject, predicate, stance, hedging,
      kind, etc.) so the LLM knows what to emit

These are *file-shape* tests. Real extraction quality is gated on
the daemon implementation (P0-2 Task 2.3) + LLM calls; that work
lives elsewhere.

Companion design doc: `docs/CLAIM_STANCE_SCORING.md`.
"""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = REPO_ROOT / "prompts" / "en" / "claim_extraction.md"
DESIGN_PATH = REPO_ROOT / "docs" / "CLAIM_STANCE_SCORING.md"


# ---------- file existence ------------------------------------------------


def test_extraction_prompt_exists():
    assert PROMPT_PATH.exists(), (
        f"P0-2 Task 2.2 requires {PROMPT_PATH.relative_to(REPO_ROOT)} "
        "to ship as the canonical claim-extraction prompt."
    )


def test_design_doc_exists():
    assert DESIGN_PATH.exists(), (
        f"P0-2 architectural decisions live in "
        f"{DESIGN_PATH.relative_to(REPO_ROOT)}."
    )


# ---------- prompt structural contract -----------------------------------


@pytest.fixture(scope="module")
def prompt_text() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize("schema_field", [
    "subject",
    "subject_canonical",
    "predicate",
    "object",
    "stance",
    "hedging",
    "raw_text",
    "reasoning",
    "kind",
])
def test_prompt_documents_schema_field(prompt_text, schema_field):
    """Each Claim schema field must be documented in the prompt so
    the LLM knows what to emit."""
    assert schema_field in prompt_text, (
        f"{schema_field} must be documented in the extraction prompt"
    )


@pytest.mark.parametrize("kind_value", [
    "stance",
    "fact",
    "preference",
    "commitment",
])
def test_prompt_lists_all_claim_kinds(prompt_text, kind_value):
    """The prompt must enumerate every legal value of `kind`."""
    assert kind_value in prompt_text, (
        f"kind={kind_value} must be enumerated in the extraction prompt"
    )


def test_prompt_has_at_least_5_worked_examples(prompt_text):
    """Spec § P0-2 Task 2.2: prompt must include 5 worked examples,
    including reverse cases (looks-like-a-claim-but-isn't)."""
    # `### Example N —` is the canonical header in this prompt
    example_count = prompt_text.count("### Example ")
    assert example_count >= 5, (
        f"Spec requires >=5 worked examples; found {example_count}"
    )


def test_prompt_has_skip_rules(prompt_text):
    """The DO NOT extract section must address questions, hypotheticals,
    assistant statements, and quoted_other facts — the four most common
    false-positive sources per spec."""
    assert "DO NOT extract" in prompt_text, (
        "Prompt must have an explicit DO NOT extract section"
    )
    for skip_signal in ["question", "ypothetical", "ssistant"]:
        assert skip_signal in prompt_text, (
            f"DO NOT extract section must cover {skip_signal!r}"
        )


def test_prompt_specifies_numeric_stance_range(prompt_text):
    """Spec § P0-2 Task 2.1: stance must be -1.0 to +1.0 numeric."""
    assert "-1.0" in prompt_text and "+1.0" in prompt_text, (
        "stance must be specified as numeric -1.0 to +1.0 per spec"
    )


def test_prompt_specifies_numeric_hedging_range(prompt_text):
    """Spec § P0-2 Task 2.1: hedging must be 0.0 to 1.0 numeric."""
    assert "0.0" in prompt_text and "1.0" in prompt_text, (
        "hedging must be specified as numeric 0.0 to 1.0 per spec"
    )


def test_prompt_specifies_json_array_output(prompt_text):
    """The prompt must instruct the LLM to emit a JSON array (so
    multi-claim turns work and zero-claim turns return [])."""
    assert "JSON array" in prompt_text, (
        "Output format must be a JSON array, not single object"
    )
    assert "empty array" in prompt_text or "`[]`" in prompt_text, (
        "Prompt must specify the empty-array case for zero claims"
    )


# ---------- design-doc structural contract -------------------------------


@pytest.fixture(scope="module")
def design_text() -> str:
    return DESIGN_PATH.read_text(encoding="utf-8")


def test_design_doc_addresses_position_signal_integration(design_text):
    """The design doc must explicitly explain how the new Claim
    schema integrates with the existing position_signal — the most
    important architectural decision in P0-2."""
    assert "position_signal" in design_text, (
        "Design doc must reconcile new Claim schema with existing "
        "position_signal block"
    )
    assert "stance_score" in design_text, (
        "Design doc must specify the new numeric stance_score field"
    )
    assert "hedging_score" in design_text, (
        "Design doc must specify the new numeric hedging_score field"
    )


def test_design_doc_specifies_backward_compat(design_text):
    """72+ cards already have position_signal without the new
    fields. The design must address what happens to them."""
    assert "ackward compat" in design_text, (
        "Design doc must address backward compat for legacy "
        "position_signal cards"
    )


def test_design_doc_defers_task_2_3(design_text):
    """Per the scope split: this iteration ships the schema + prompt
    scaffold. Task 2.3 (drift detection algorithm) is explicitly
    deferred to a fresh implementation session."""
    assert "Task 2.3" in design_text, (
        "Design doc must reference the deferred Task 2.3 work"
    )
    assert "DEFERRED" in design_text or "deferred" in design_text, (
        "Design doc must explicitly mark Task 2.3 as deferred"
    )
