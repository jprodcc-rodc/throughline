"""P0-2 Task 2.1: pin the Claim schema's behavior.

Covers:
- Field validation (range bounds on stance/hedging, snake_case
  enforcement on subject_canonical, predicate/kind enum membership)
- Roundtrip: JSON → Claim → JSON preserves shape
- Empty + populated reasoning arrays
- Optional persistence fields (id, card_id, timestamp, source_turn_id)
- The 5 worked examples from prompts/en/claim_extraction.md must
  parse cleanly — this is the prompt-to-schema sync contract: if
  someone updates one, the other must follow.
- coerce_canonical fallback for non-canonical extractor output
- merge_alias idempotency
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from mcp_server.claim_schema import (
    Claim,
    SCHEMA_VERSION,
    claim_json_schema,
    coerce_canonical,
    is_canonical,
    merge_alias,
    parse_claims_array,
    serialize_claims_array,
)


# ── basic shape ───────────────────────────────────────────────────────────


def _minimal_claim_dict() -> dict:
    """A minimal valid Claim used as the base for negative tests."""
    return {
        "subject": "Postgres",
        "subject_canonical": "postgres",
        "predicate": "suitable_for",
        "stance": 0.5,
        "hedging": 0.2,
        "raw_text": "Postgres is suitable here",
        "kind": "stance",
    }


def test_minimal_claim_validates():
    c = Claim(**_minimal_claim_dict())
    assert c.subject == "Postgres"
    assert c.subject_canonical == "postgres"
    assert c.stance == 0.5
    assert c.hedging == 0.2
    assert c.kind == "stance"
    assert c.reasoning == []  # default empty
    assert c.object is None
    assert c.id is None


def test_full_claim_with_persistence_fields():
    d = _minimal_claim_dict()
    d.update({
        "object": "OLTP workloads",
        "reasoning": ["fast writes", "rich indexing"],
        "id": "abc123",
        "card_id": "card_001",
        "timestamp": "2026-04-29T10:00:00Z",
        "source_turn_id": "t_002",
    })
    c = Claim(**d)
    assert c.object == "OLTP workloads"
    assert c.reasoning == ["fast writes", "rich indexing"]
    assert c.id == "abc123"
    assert c.timestamp == "2026-04-29T10:00:00Z"


# ── range validation: stance + hedging ────────────────────────────────────


@pytest.mark.parametrize("bad_stance", [-1.5, 1.5, 2.0, -2.0, 100.0])
def test_stance_must_be_in_range(bad_stance):
    d = _minimal_claim_dict()
    d["stance"] = bad_stance
    with pytest.raises(ValidationError):
        Claim(**d)


@pytest.mark.parametrize("good_stance", [-1.0, -0.5, 0.0, 0.5, 1.0])
def test_stance_boundaries_inclusive(good_stance):
    d = _minimal_claim_dict()
    d["stance"] = good_stance
    Claim(**d)  # must not raise


@pytest.mark.parametrize("bad_hedging", [-0.1, 1.1, -1.0, 2.0])
def test_hedging_must_be_in_range(bad_hedging):
    d = _minimal_claim_dict()
    d["hedging"] = bad_hedging
    with pytest.raises(ValidationError):
        Claim(**d)


@pytest.mark.parametrize("good_hedging", [0.0, 0.5, 1.0])
def test_hedging_boundaries_inclusive(good_hedging):
    d = _minimal_claim_dict()
    d["hedging"] = good_hedging
    Claim(**d)


# ── enum membership: predicate + kind ─────────────────────────────────────


def test_predicate_must_be_in_enum():
    d = _minimal_claim_dict()
    d["predicate"] = "frobnicates"  # not a legal predicate
    with pytest.raises(ValidationError):
        Claim(**d)


@pytest.mark.parametrize("p", [
    "is", "should_use", "suitable_for", "prefers", "dislikes",
    "requires", "avoids", "recommends", "rejects", "depends_on",
    "is_an_instance_of",
])
def test_each_legal_predicate_accepted(p):
    d = _minimal_claim_dict()
    d["predicate"] = p
    Claim(**d)


def test_kind_must_be_in_enum():
    d = _minimal_claim_dict()
    d["kind"] = "stance_decision"  # not legal
    with pytest.raises(ValidationError):
        Claim(**d)


@pytest.mark.parametrize("k", ["stance", "fact", "preference", "commitment"])
def test_each_legal_kind_accepted(k):
    d = _minimal_claim_dict()
    d["kind"] = k
    Claim(**d)


# ── subject_canonical: snake_case enforcement ─────────────────────────────


@pytest.mark.parametrize("good", [
    "postgres",
    "usage_based_pricing",
    "react_native",
    "_self",
    "claim_3d_modeling",  # digits OK after first char
])
def test_canonical_accepted(good):
    d = _minimal_claim_dict()
    d["subject_canonical"] = good
    Claim(**d)


@pytest.mark.parametrize("bad", [
    "Postgres",          # uppercase
    "usage-based-pricing",  # hyphens
    "Has Space",
    "3d_modeling",       # leading digit
    "postgres.io",       # dot
    "",                  # empty
])
def test_canonical_rejected(bad):
    d = _minimal_claim_dict()
    d["subject_canonical"] = bad
    with pytest.raises(ValidationError):
        Claim(**d)


def test_is_canonical_helper():
    assert is_canonical("postgres") is True
    assert is_canonical("usage_based") is True
    assert is_canonical("Postgres") is False
    assert is_canonical("3d_x") is False
    assert is_canonical("") is False


# ── coerce_canonical fallback -----------------------------------------------


@pytest.mark.parametrize("raw, expected", [
    ("Postgres", "postgres"),
    ("USAGE-based pricing", "usage_based_pricing"),
    ("react native", "react_native"),
    ("foo--bar___baz", "foo_bar_baz"),
    ("3d_modeling", "_3d_modeling"),  # digit-prefix gets _ prefix
    ("", "unknown"),  # empty input falls back
])
def test_coerce_canonical(raw, expected):
    assert coerce_canonical(raw) == expected


def test_coerce_canonical_chinese_fallback():
    # CJK input: stripped to nothing → "unknown" (canonical form is
    # for cross-language alias merging; raw text preserves Chinese
    # via the `subject` field).
    assert coerce_canonical("用药清单") == "unknown"


# ── reasoning array constraints --------------------------------------------


def test_reasoning_caps_at_5():
    d = _minimal_claim_dict()
    d["reasoning"] = [f"clause {i}" for i in range(6)]
    with pytest.raises(ValidationError):
        Claim(**d)


def test_reasoning_empty_string_rejected():
    d = _minimal_claim_dict()
    d["reasoning"] = ["good", "", "also good"]
    with pytest.raises(ValidationError):
        Claim(**d)


# ── extra fields rejected (catches LLM drift) ------------------------------


def test_extra_fields_rejected():
    d = _minimal_claim_dict()
    d["confidence_score"] = 0.9  # not a real field
    with pytest.raises(ValidationError):
        Claim(**d)


# ── parse_claims_array / serialize_claims_array ----------------------------


def test_parse_empty_array():
    assert parse_claims_array("[]") == []


def test_parse_single_claim_array():
    payload = json.dumps([_minimal_claim_dict()])
    result = parse_claims_array(payload)
    assert len(result) == 1
    assert result[0].subject == "Postgres"


def test_parse_rejects_non_array():
    # If the LLM emits an object instead of array, parse_claims_array
    # must fail loudly so the caller can retry / log / drop.
    payload = json.dumps(_minimal_claim_dict())
    with pytest.raises((ValueError, json.JSONDecodeError)):
        parse_claims_array(payload)


def test_roundtrip_preserves_shape():
    """Round-trip: dict → Claim → JSON → Claim → dict should be
    bytewise stable on the user-emitted fields."""
    original = [
        _minimal_claim_dict(),
        {**_minimal_claim_dict(),
         "subject": "FlatRate", "subject_canonical": "flat_rate",
         "stance": -0.5, "kind": "preference",
         "reasoning": ["because runway"]},
    ]
    claims = [Claim(**d) for d in original]
    serialized = serialize_claims_array(claims)
    reparsed = parse_claims_array(serialized)
    assert len(reparsed) == 2
    assert reparsed[0].subject == "Postgres"
    assert reparsed[1].reasoning == ["because runway"]


# ── 5-worked-example sync contract ----------------------------------------
#
# The 5 worked examples in prompts/en/claim_extraction.md ARE the
# prompt-to-schema sync. If you change the schema, you must update
# the prompt's expected outputs. If you change the prompt's worked
# examples, you must update these tests. This pinning catches drift
# between prompt and schema.


# Example 1: strong stance + reasoning + commitment (multi-claim turn)
EXAMPLE_1 = [
    {
        "subject": "usage-based pricing",
        "subject_canonical": "usage_based_pricing",
        "predicate": "suitable_for",
        "object": "early-stage SaaS",
        "stance": -0.85,
        "hedging": 0.05,
        "raw_text": "I'm against usage-based pricing for the early-stage SaaS",
        "reasoning": [
            "LTV math results",
            "churn risk severe pre-PMF",
            "runway can't tolerate revenue volatility"
        ],
        "kind": "stance",
    },
    {
        "subject": "flat-rate pricing",
        "subject_canonical": "flat_rate_pricing",
        "predicate": "should_use",
        "object": "early-stage SaaS",
        "stance": 0.85,
        "hedging": 0.05,
        "raw_text": "We're going flat-rate",
        "reasoning": [],
        "kind": "commitment",
    },
]

# Example 2: hedged tentative position
EXAMPLE_2 = [
    {
        "subject": "Postgres",
        "subject_canonical": "postgres",
        "predicate": "suitable_for",
        "object": None,
        "stance": 0.3,
        "hedging": 0.7,
        "raw_text": "I think Postgres is probably the right call here, but I'm not totally sure",
        "reasoning": [],
        "kind": "stance",
    },
]

# Example 3: factual question -> empty extraction
EXAMPLE_3: list[dict] = []

# Example 4: quoted_other -> empty extraction
EXAMPLE_4: list[dict] = []

# Example 5: strong principle / quantifier
EXAMPLE_5 = [
    {
        "subject": "Friday deploys",
        "subject_canonical": "friday_deploys",
        "predicate": "rejects",
        "object": None,
        "stance": -1.0,
        "hedging": 0.0,
        "raw_text": "We never deploy on Fridays in this org. No exceptions",
        "reasoning": [
            "Friday rollback cost too high",
            "weekend team offline"
        ],
        "kind": "stance",
    },
]


@pytest.mark.parametrize("example", [
    EXAMPLE_1, EXAMPLE_2, EXAMPLE_3, EXAMPLE_4, EXAMPLE_5,
])
def test_prompt_worked_examples_validate(example):
    """Every worked example output in prompts/en/claim_extraction.md
    must round-trip through the Claim schema. If this test fails,
    one of the two has drifted."""
    serialized = json.dumps(example)
    parsed = parse_claims_array(serialized)
    assert len(parsed) == len(example)


# ── alias merge ------------------------------------------------------------


def test_merge_alias_creates_canonical_entry():
    aliases: dict[str, list[str]] = {}
    merge_alias(aliases, "postgres", "Postgres")
    assert aliases == {"postgres": ["Postgres"]}


def test_merge_alias_idempotent():
    aliases = {"postgres": ["PG"]}
    merge_alias(aliases, "postgres", "PG")  # already there
    merge_alias(aliases, "postgres", "Postgres")  # new
    merge_alias(aliases, "postgres", "PG")  # again
    assert aliases == {"postgres": ["PG", "Postgres"]}


def test_merge_alias_strips_whitespace():
    aliases: dict[str, list[str]] = {}
    merge_alias(aliases, "postgres", "  Postgres  ")
    assert aliases == {"postgres": ["Postgres"]}


def test_merge_alias_skips_empty():
    aliases: dict[str, list[str]] = {}
    merge_alias(aliases, "postgres", "   ")
    assert aliases == {"postgres": []}


# ── schema metadata --------------------------------------------------------


def test_schema_version_is_semver():
    parts = SCHEMA_VERSION.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_json_schema_has_required_fields():
    schema = claim_json_schema()
    # Every required field must appear in `required` per JSON Schema
    required_set = set(schema.get("required", []))
    for f in ["subject", "subject_canonical", "predicate", "stance",
              "hedging", "raw_text", "kind"]:
        assert f in required_set, f"{f!r} missing from JSON schema required"
    # Optional persistence fields must NOT be in `required`
    for f in ["id", "card_id", "timestamp", "source_turn_id"]:
        assert f not in required_set, (
            f"{f!r} is daemon-attached, not LLM-emitted; must be optional"
        )
