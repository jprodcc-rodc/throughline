"""P0-2: pin the drift judge prompt's structural contract + the
JudgeVerdict JSON parser.

The judge prompt at prompts/en/drift_judge.md is the LLM-callable
spec. The actual LLM HTTP wrapper is a separate concern (deferred
because it requires a daemon-mcp_server architectural decision);
this test file pins the prompt's structural shape AND the parser
that consumes the LLM's JSON output.

When the LLM wrapper lands, the wrapper composes:

    raw_text = call_llm(prompt=load(prompts/en/drift_judge.md), ...)
    return parse_judge_verdict(raw_text)

so the prompt + parser are the two halves of the contract this
file pins.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_server.drift_detector import (
    JudgeVerdict,
    parse_judge_verdict,
    safe_parse_judge_verdict,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = REPO_ROOT / "prompts" / "en" / "drift_judge.md"


# ── prompt file contract ────────────────────────────────────────────────


def test_drift_judge_prompt_exists():
    assert PROMPT_PATH.exists(), (
        f"P0-2 LLM judge requires {PROMPT_PATH.relative_to(REPO_ROOT)}"
    )


@pytest.fixture(scope="module")
def prompt_text() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize("required_field", [
    "is_genuine_drift",
    "explanation",
    "confidence",
])
def test_prompt_specifies_all_verdict_fields(prompt_text, required_field):
    """The prompt must instruct the LLM to emit each JudgeVerdict
    field. Drift between prompt and parser would silently break
    the wrapper."""
    assert required_field in prompt_text, (
        f"prompt must instruct emitting {required_field!r} in JSON output"
    )


def test_prompt_specifies_json_object_output(prompt_text):
    """Singular JSON object, not array; not free-form text."""
    assert "JSON object" in prompt_text


def test_prompt_has_at_least_5_worked_examples(prompt_text):
    """5 calibration examples per spec convention -- including at
    least one each of: clear-drift, clear-not-drift (context shift),
    refinement-not-drift, ambiguous-low-confidence."""
    example_count = prompt_text.count("### Example ")
    assert example_count >= 5, (
        f"Spec convention requires >=5 worked examples; found "
        f"{example_count}"
    )


def test_prompt_addresses_context_shift_case(prompt_text):
    """The most common false-positive in drift judging is treating
    a context-justified shift (different lifecycle stage, different
    object) as drift. The prompt must explicitly call this out."""
    # 'context' must appear with shift / change framing
    assert "ontext" in prompt_text
    # 'object' as a discriminator must be mentioned
    assert "object" in prompt_text.lower() or "OBJECT" in prompt_text


def test_prompt_addresses_refinement_not_drift(prompt_text):
    """Convergence (lower hedging over time, same direction) is
    decision-making not drift. The prompt's NOT-A-DRIFT section
    must call this out."""
    assert "refinement" in prompt_text.lower() or (
        "convergence" in prompt_text.lower()
    ) or "tentative" in prompt_text.lower()


def test_prompt_specifies_confidence_calibration(prompt_text):
    """Reserve 0.9+ for clear-cut; default to 0.6-0.9. Without this
    calibration the model over-confidences every verdict."""
    assert "0.9" in prompt_text
    assert "0.6" in prompt_text or "0.5" in prompt_text


def test_prompt_specifies_haiku_tier(prompt_text):
    """Per spec rule 4: judge should run on a cheap model."""
    assert "Haiku" in prompt_text or "haiku" in prompt_text


# ── parse_judge_verdict ────────────────────────────────────────────────


def test_parse_valid_drift_verdict():
    text = json.dumps({
        "is_genuine_drift": True,
        "explanation": "stance reversed without context shift",
        "confidence": 0.92,
    })
    v = parse_judge_verdict(text)
    assert isinstance(v, JudgeVerdict)
    assert v.is_genuine_drift is True
    assert v.explanation == "stance reversed without context shift"
    assert v.confidence == 0.92


def test_parse_valid_not_drift_verdict():
    text = json.dumps({
        "is_genuine_drift": False,
        "explanation": "different lifecycle stage justifies",
        "confidence": 0.85,
    })
    v = parse_judge_verdict(text)
    assert v.is_genuine_drift is False


def test_parse_strips_explanation_whitespace():
    text = json.dumps({
        "is_genuine_drift": True,
        "explanation": "   trimmed.   ",
        "confidence": 0.5,
    })
    v = parse_judge_verdict(text)
    assert v.explanation == "trimmed."


def test_parse_accepts_int_confidence():
    """LLMs sometimes emit int 1 instead of 1.0. Coerce."""
    text = json.dumps({
        "is_genuine_drift": True,
        "explanation": "x",
        "confidence": 1,
    })
    v = parse_judge_verdict(text)
    assert v.confidence == 1.0


def test_parse_rejects_non_json():
    with pytest.raises(ValueError):
        parse_judge_verdict("not a json blob")


def test_parse_rejects_array():
    text = json.dumps([{"is_genuine_drift": True, "explanation": "x",
                        "confidence": 0.5}])
    with pytest.raises(ValueError):
        parse_judge_verdict(text)


def test_parse_rejects_scalar():
    text = json.dumps("just a string")
    with pytest.raises(ValueError):
        parse_judge_verdict(text)


@pytest.mark.parametrize("missing", ["is_genuine_drift", "explanation",
                                      "confidence"])
def test_parse_rejects_missing_field(missing):
    full = {"is_genuine_drift": True, "explanation": "x", "confidence": 0.5}
    del full[missing]
    with pytest.raises(ValueError):
        parse_judge_verdict(json.dumps(full))


@pytest.mark.parametrize("bad_drift", [0, 1, "true", "false", None,
                                        [True], {"a": 1}])
def test_parse_rejects_non_bool_drift(bad_drift):
    """is_genuine_drift must be a JSON bool, not int / str / null."""
    text = json.dumps({
        "is_genuine_drift": bad_drift,
        "explanation": "x",
        "confidence": 0.5,
    })
    with pytest.raises(ValueError):
        parse_judge_verdict(text)


@pytest.mark.parametrize("bad_explanation", ["", "   ", None, 42, ["a"]])
def test_parse_rejects_bad_explanation(bad_explanation):
    text = json.dumps({
        "is_genuine_drift": True,
        "explanation": bad_explanation,
        "confidence": 0.5,
    })
    with pytest.raises(ValueError):
        parse_judge_verdict(text)


@pytest.mark.parametrize("bad_conf", [-0.1, 1.5, "0.5", None, True, False,
                                       [0.5]])
def test_parse_rejects_bad_confidence(bad_conf):
    """confidence must be in [0.0, 1.0] and not bool/str/null/list."""
    text = json.dumps({
        "is_genuine_drift": True,
        "explanation": "x",
        "confidence": bad_conf,
    })
    with pytest.raises(ValueError):
        parse_judge_verdict(text)


@pytest.mark.parametrize("good_conf", [0.0, 0.5, 1.0])
def test_parse_accepts_boundary_confidence(good_conf):
    text = json.dumps({
        "is_genuine_drift": True,
        "explanation": "x",
        "confidence": good_conf,
    })
    v = parse_judge_verdict(text)
    assert v.confidence == good_conf


# ── safe_parse_judge_verdict ──────────────────────────────────────────


def test_safe_parse_returns_safe_default_on_garbage():
    v = safe_parse_judge_verdict("totally not json")
    assert v.is_genuine_drift is False
    assert v.confidence == 0.0
    assert "unparseable" in v.explanation


def test_safe_parse_returns_safe_default_on_missing_field():
    v = safe_parse_judge_verdict(
        json.dumps({"is_genuine_drift": True, "explanation": "x"})
    )
    # confidence missing -> safe default
    assert v.is_genuine_drift is False
    assert v.confidence == 0.0


def test_safe_parse_returns_real_verdict_on_valid_input():
    v = safe_parse_judge_verdict(json.dumps({
        "is_genuine_drift": True,
        "explanation": "real flip",
        "confidence": 0.85,
    }))
    assert v.is_genuine_drift is True
    assert v.confidence == 0.85
    assert v.explanation == "real flip"


# ── prompt-to-parser sync contract ────────────────────────────────────


def test_prompt_worked_example_outputs_round_trip(prompt_text):
    """The 5 worked example output blocks in prompts/en/drift_judge.md
    must be valid JudgeVerdict-shaped JSON. If you update the
    prompt's expected outputs, this test will catch a parser drift."""
    # Find every fenced ```json block in the prompt and try to
    # parse_judge_verdict each. Skip blocks that aren't JudgeVerdict-
    # shaped (e.g. input claim blocks).
    json_blocks = []
    in_json = False
    current: list[str] = []
    for line in prompt_text.splitlines():
        if line.strip() == "```json":
            in_json = True
            current = []
            continue
        if line.strip() == "```" and in_json:
            json_blocks.append("\n".join(current))
            in_json = False
            continue
        if in_json:
            current.append(line)

    # At least 5 (one per example output) -- some prompts may include
    # input blocks too but those don't use ```json fence.
    verdict_blocks = []
    for block in json_blocks:
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and "is_genuine_drift" in parsed:
            verdict_blocks.append(block)

    assert len(verdict_blocks) >= 5, (
        f"Expected at least 5 verdict-shaped JSON blocks in prompt; "
        f"found {len(verdict_blocks)}"
    )

    for block in verdict_blocks:
        # Each must round-trip through the parser without raising.
        parse_judge_verdict(block)
