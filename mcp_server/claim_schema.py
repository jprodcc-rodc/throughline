"""Claim schema for P0-2 stance-based drift detection.

Per docs/CLAIM_STANCE_SCORING.md. A `Claim` is what the LLM
extracts from a conversation slice (per prompts/en/claim_extraction.md);
it carries numeric stance + hedging scores so the drift detector
can compute stance-delta over time. Coexists with the existing
`position_signal` block on each card; this schema models the
per-claim units, not the per-card aggregate.

The schema lives in `mcp_server/` (not `daemon/`) because:
- mcp_server cannot depend on daemon (locked architectural rule)
- daemon CAN depend on mcp_server, so daemon's refiner can import
  this module when emitting numeric scores
- Existing pattern: `mcp_server/topic_clustering.py` and
  `mcp_server/position_state.py` already house algorithmic / data-
  model code shared with daemon-side consumers.

Keeping pydantic as the validation engine matches the rest of the
project (FastAPI + the daemon's existing pydantic models). The
transitive dep already lives in mcp_server's runtime via the
`throughline` parent install.
"""
from __future__ import annotations

import json
import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── enum surfaces ────────────────────────────────────────────────────────

# `predicate` legal values. Aligned with the extraction prompt at
# prompts/en/claim_extraction.md. Add new values by also updating
# the prompt + bumping the schema VERSION below.
Predicate = Literal[
    "is",
    "should_use",
    "suitable_for",
    "prefers",
    "dislikes",
    "requires",
    "avoids",
    "recommends",
    "rejects",
    "depends_on",
    "is_an_instance_of",
]

# `kind` distinguishes drift-trackable stances from non-drift content.
# Drift detector only operates on `stance` and `commitment` claims;
# `fact` and `preference` are recorded but not delta-compared.
Kind = Literal["stance", "fact", "preference", "commitment"]


# ── canonicalization helpers ─────────────────────────────────────────────

# subject_canonical must be lowercase snake_case ASCII (lowercased
# alphanumerics + underscores; leading char must be alpha or underscore;
# digits OK after the first char). The extractor's first guess gets
# regex-checked here; if invalid, the daemon's reconciliation step
# rewrites it before persisting.
_CANONICAL_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def is_canonical(s: str) -> bool:
    """Return True iff `s` is a valid subject_canonical form."""
    return bool(_CANONICAL_RE.match(s))


def coerce_canonical(s: str) -> str:
    """Best-effort coerce arbitrary text to snake_case canonical.

    Used when the extractor emits a non-canonical guess and the
    daemon needs to normalize before alias lookup. Strips diacritics,
    replaces non-ASCII / non-alnum with underscore, collapses runs,
    lowercases. CJK characters are dropped (they don't fit snake_case
    ASCII; the canonical form is for cross-language alias merging).

    Empty or all-non-ASCII input returns "unknown" rather than ""
    since the schema requires non-empty.
    """
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s or not s[0].isalpha() and s[0] != "_":
        s = "_" + s if s else "unknown"
    return s if is_canonical(s) else "unknown"


# ── the schema ───────────────────────────────────────────────────────────

# Schema version. Bump on any breaking change to field names, types,
# or value enums. Extraction prompt + storage format must align with
# the version that wrote them.
SCHEMA_VERSION = "0.1.0"


class Claim(BaseModel):
    """A single user-asserted proposition extracted from a conversation
    slice. Drift detection compares Claims with matching
    subject_canonical + similar predicate over time.

    Required fields are emitted by the LLM extractor. Optional
    persistence fields (id, card_id, timestamp, source_turn_id) are
    attached by the daemon when the Claim is stored alongside its
    parent card.
    """

    model_config = ConfigDict(
        extra="forbid",  # reject unknown fields (catches LLM drift)
        str_strip_whitespace=True,
    )

    # ── required: emitted by extractor ─────────────────────────────
    subject: str = Field(min_length=1, description=(
        "The entity the claim is about. User's exact phrasing."
    ))
    subject_canonical: str = Field(min_length=1, description=(
        "Lowercase snake_case ASCII canonical form for alias "
        "matching across cards / languages."
    ))
    predicate: Predicate
    object: Optional[str] = Field(default=None, description=(
        "Optional other end of the predicate relation. Often null "
        "for is/prefers; populated for suitable_for/should_use."
    ))
    stance: float = Field(ge=-1.0, le=1.0, description=(
        "-1.0 strong reject .. 0 neutral .. +1.0 strong endorse"
    ))
    hedging: float = Field(ge=0.0, le=1.0, description=(
        "0.0 certain assertion .. 1.0 explicit non-commitment"
    ))
    raw_text: str = Field(min_length=1, description=(
        "Exact span from the transcript justifying the claim. "
        "Quoted directly; preserves original capitalization + locale."
    ))
    reasoning: list[str] = Field(default_factory=list, description=(
        "User's stated 'because...' clauses. Empty array if user "
        "gave no reasoning."
    ))
    kind: Kind

    # ── optional: attached by daemon at persistence time ───────────
    id: Optional[str] = Field(default=None, description=(
        "Unique claim ID (uuid4 hex). Set by daemon, not extractor."
    ))
    card_id: Optional[str] = Field(default=None, description=(
        "Reverse reference to the card this claim was extracted "
        "from. Daemon-set."
    ))
    timestamp: Optional[str] = Field(default=None, description=(
        "ISO 8601 conversation timestamp. Daemon copies from card "
        "frontmatter `date` field."
    ))
    source_turn_id: Optional[str] = Field(default=None, description=(
        "Which turn within the card this claim came from. Lets "
        "drift detector cite the exact moment."
    ))

    # ── validators ─────────────────────────────────────────────────

    @field_validator("subject_canonical")
    @classmethod
    def _validate_canonical(cls, v: str) -> str:
        if not is_canonical(v):
            raise ValueError(
                f"subject_canonical must be lowercase snake_case "
                f"ASCII ([a-z_][a-z0-9_]*); got {v!r}"
            )
        return v

    @field_validator("reasoning")
    @classmethod
    def _validate_reasoning(cls, v: list[str]) -> list[str]:
        # Reasoning entries are short clauses; cap the list to keep
        # the per-claim record tight. Spec calibration note recommends
        # cap at 3, but allow up to 5 for cards where the user gave
        # multiple anchored reasons.
        if len(v) > 5:
            raise ValueError(
                f"reasoning must have at most 5 entries; got {len(v)}"
            )
        for i, item in enumerate(v):
            if not isinstance(item, str) or not item.strip():
                raise ValueError(
                    f"reasoning[{i}] must be a non-empty string"
                )
        return v


# ── helpers --------------------------------------------------------------


def parse_claims_array(text: str) -> list[Claim]:
    """Parse the LLM's JSON array output into validated Claim objects.

    The extraction prompt (prompts/en/claim_extraction.md) instructs
    the LLM to emit a JSON array. Empty arrays are valid (zero-claim
    turns return []). Any malformed claim raises pydantic
    ValidationError; the caller decides whether to retry, log, or
    drop the malformed claim.
    """
    raw = json.loads(text)
    if not isinstance(raw, list):
        raise ValueError(
            f"Expected JSON array; got {type(raw).__name__}"
        )
    return [Claim.model_validate(item) for item in raw]


def serialize_claims_array(claims: list[Claim]) -> str:
    """Round-trip serialize a list of Claims back to the extractor's
    output shape. Used for storing extracted Claims to disk and for
    test fixtures."""
    return json.dumps(
        [c.model_dump(exclude_none=True) for c in claims],
        ensure_ascii=False,
        indent=2,
    )


def claim_json_schema() -> dict[str, Any]:
    """Return the JSON Schema for Claim. Useful when wiring the
    extractor into a structured-output API (e.g. Anthropic's
    output_config.format) or generating documentation."""
    return Claim.model_json_schema()


# ── alias merge support (subject canonicalization) -----------------------


def merge_alias(
    aliases: dict[str, list[str]],
    canonical: str,
    raw: str,
) -> dict[str, list[str]]:
    """Merge a raw subject string into the aliases map under a
    canonical key. Idempotent: re-adding an existing alias is a
    no-op. Returns the updated map (mutates the input as well).

    The aliases map is the structure described in
    docs/CLAIM_STANCE_SCORING.md § Subject canonicalization. It
    lives at vault/.throughline/aliases.json and is grown
    incrementally as the extractor encounters new alias forms.
    """
    if canonical not in aliases:
        aliases[canonical] = []
    raw_stripped = raw.strip()
    if raw_stripped and raw_stripped not in aliases[canonical]:
        aliases[canonical].append(raw_stripped)
    return aliases
