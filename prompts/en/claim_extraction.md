# Claim Extraction Prompt

Used by the Reflection Pass daemon (P0-2 Task 2.3) to extract
structured `Claim` objects from a conversation slice. Output is
consumed by the drift detection algorithm and stored alongside
`position_signal` per card. Schema reconciliation with existing
`position_signal` is documented in `docs/CLAIM_STANCE_SCORING.md`.

**Status**: scaffold. Not yet wired into the daemon. Tracked by
`fixtures/v0_2_0/test_claim_extraction_prompt.py` for structural
contract.

---

## System prompt

```
You extract structured claims from conversation transcripts. A claim
is a proposition the USER asserts, prefers, or believes — not facts
they ask about, not the assistant's statements, not hypotheticals.

For each user-asserted claim, output a JSON object with these fields:

- subject: the entity the claim is about (a thing, person, project,
  concept). Use the user's exact phrasing.
- subject_canonical: the canonical lowercase snake_case form. Same
  thing referenced different ways ("Postgres", "PG", "postgresql")
  must collapse to the same canonical (e.g. "postgres"). When in
  doubt, snake_case the raw subject.
- predicate: the relationship verb. One of: is | should_use |
  suitable_for | prefers | dislikes | requires | avoids |
  recommends | rejects | depends_on | is_an_instance_of
- object: optional. The other end of the predicate. Often null
  for is/prefers; populated for suitable_for/should_use ("Postgres
  suitable_for OLTP workloads" → object = "OLTP workloads").
- stance: float in [-1.0, +1.0]
  - +1.0: strong endorsement ("X is the only choice", "must use X")
  - +0.5: mild preference ("I lean X", "X is probably better")
  - 0.0: neutral / unable to determine
  - -0.5: mild dispreference ("not sure about X", "X has issues")
  - -1.0: strong rejection ("X is wrong", "never use X")
- hedging: float in [0.0, 1.0]
  - 0.0: certain ("X is Y", flat assertion)
  - 0.3: light hedge ("I think X is Y", "X is generally Y")
  - 0.5: moderate ("X might be Y", "I'm leaning toward X is Y")
  - 0.8: high uncertainty ("maybe X is Y, not sure", "perhaps...")
  - 1.0: explicit non-commitment ("I genuinely don't know")
- raw_text: the exact span from the transcript that justifies this
  claim. Quote directly; preserve original capitalization.
- reasoning: array of short strings, the user's stated WHY (the
  "because..." clauses or implicit reasons surfacing nearby).
  Empty array if user gave no reasoning.
- kind: one of:
  - stance: an opinion / preference (drift-trackable)
  - fact: a factual claim about reality (NOT drift-trackable —
    facts get updated, not drifted)
  - preference: a personal preference distinct from a stance
    (e.g. "I prefer dark mode" — affects behavior but not drift)
  - commitment: a binding decision the user has made
    ("I've decided", "I'm going with X")

DO NOT extract:
- Factual questions ("what is X?", "how does Y work?") — these are
  not claims.
- Hypotheticals ("if we did X...", "what if Y") — unless directly
  followed by a commitment ("...let's go with that").
- Assistant statements — only the user.
- Mentioned facts the user is reporting, not endorsing
  ("the article said X" → quoted_other, skip).
- Trivia, small talk, acknowledgements ("ok", "got it", "thanks").

OUTPUT FORMAT: a JSON array of Claim objects. If no extractable
claims exist in the transcript, output an empty array `[]`.

Do not include anything but the JSON. No commentary, no markdown,
no preamble.
```

---

## Worked examples

The model sees these in-context to ground edge cases. Real prompt
includes all five.

### Example 1 — strong stance + reasoning

**Input transcript:**

```
[user, 2026-04-15T10:23:00Z, turn=t_001]
After running the LTV math, I'm against usage-based pricing for
the early-stage SaaS. Churn risk is too severe pre-PMF and runway
can't tolerate revenue volatility. We're going flat-rate.
```

**Expected output:**

```json
[
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
    "kind": "stance"
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
    "kind": "commitment"
  }
]
```

### Example 2 — hedged tentative position

**Input transcript:**

```
[user, 2026-04-16T14:02:00Z, turn=t_002]
I think Postgres is probably the right call here, but I'm not
totally sure — maybe SQLite would be simpler given our scale?
```

**Expected output:**

```json
[
  {
    "subject": "Postgres",
    "subject_canonical": "postgres",
    "predicate": "suitable_for",
    "object": null,
    "stance": 0.3,
    "hedging": 0.7,
    "raw_text": "I think Postgres is probably the right call here, but I'm not totally sure",
    "reasoning": [],
    "kind": "stance"
  }
]
```

(SQLite mention is hypothetical — "maybe X would be" — not a
claim. Only the Postgres lean is extractable.)

### Example 3 — looks like a claim, isn't (factual question)

**Input transcript:**

```
[user, 2026-04-17T09:15:00Z, turn=t_003]
What's the difference between Postgres and CockroachDB consistency
models? I want to understand them before deciding.
```

**Expected output:**

```json
[]
```

(No stance asserted. The "before deciding" signals a future commitment
but no current claim to extract.)

### Example 4 — quoted_other (skip)

**Input transcript:**

```
[user, 2026-04-18T11:30:00Z, turn=t_004]
The DHH article was arguing that monoliths are still fine in 2026.
I haven't really thought about it but the framing was interesting.
```

**Expected output:**

```json
[]
```

(User is reporting a position, not endorsing it. "I haven't really
thought about it" explicitly disclaims commitment. Skip per the
quoted_other rule.)

### Example 5 — strong principle / quantifier

**Input transcript:**

```
[user, 2026-04-19T16:45:00Z, turn=t_005]
We never deploy on Fridays in this org. No exceptions, no matter
how small the change. The cost of a Friday rollback is too high
when half the team is offline for the weekend.
```

**Expected output:**

```json
[
  {
    "subject": "Friday deploys",
    "subject_canonical": "friday_deploys",
    "predicate": "rejects",
    "object": null,
    "stance": -1.0,
    "hedging": 0.0,
    "raw_text": "We never deploy on Fridays in this org. No exceptions",
    "reasoning": [
      "Friday rollback cost too high",
      "weekend team offline"
    ],
    "kind": "stance"
  }
]
```

---

## Edge cases the implementation must handle

These show up in the author's vault and need testing during
implementation:

1. **Mixed-language claims.** User writes Chinese: "我觉得用 Rust
   写这个性能必须够". Extract with same schema; `subject_canonical`
   is still snake_case ASCII. `raw_text` preserves Chinese.
2. **Multi-turn cumulative claim.** User builds a position across
   3 turns; only the third is the firm commitment. Extract one
   claim, source the third turn, but the reasoning array can pull
   from earlier turns.
3. **Claim about the user themselves.** "I'm someone who needs
   strict structure". `subject = "I"`, `subject_canonical = "self"`
   (special). These map to the user's profile in personal_context;
   drift on self-claims means the user's self-model evolved.
4. **Conditional claims.** "X is best for early-stage". The
   `conditions` field on `position_signal` already captures this;
   the claim's `object` carries the condition when it fits as
   syntactic object ("suitable_for early-stage"). When it
   doesn't, leave object null and rely on the card's
   `position_signal.conditions`.

---

## Calibration notes for prompt iteration

When the LLM extractor's output diverges from a human-labeled
gold, the cause is usually one of:

- **Stance score too aggressive on hedge words**. Watch "I think"
  / "probably" / "I lean" — stance should drop toward 0.3-0.5,
  hedging should rise to 0.5-0.7.
- **kind = stance vs commitment confusion**. If the user said "I'm
  going with X", that's commitment. "I prefer X" is stance.
- **Subject canonicalization drift**. New aliases must be reconciled
  via the `aliases.json` lookup pass after extraction. The prompt
  emits a guess; the reconciliation step is post-LLM.
- **Reasoning array too long**. Cap at 3 short clauses. Long
  reasoning belongs in `position_signal.reasoning` (separate field
  on the card), not on every individual claim.

---

## Pending work (defer to implementation session)

1. Chinese-locale variant `prompts/zh/claim_extraction.md` mirroring
   examples in Chinese — needed for the author's mixed-locale vault.
2. Provider variants (`claude.md` / `generic.md` like the existing
   refiner prompts) — current prompt is generic enough for both.
3. Wire into `daemon/refine_daemon.py` as a stage between slice +
   refine, calling Haiku-tier model per spec § Out of Scope rule 4.
4. Validation step: after LLM emit, run JSON schema validator
   against `core/claim.py` (or wherever the schema lives — see
   open design question #2 in `docs/CLAIM_STANCE_SCORING.md`).
