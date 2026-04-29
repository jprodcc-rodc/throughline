# Drift Judge Prompt

Used by `mcp_server.drift_detector.detect_drift()` and
`detect_consistency_issues()` as the LLM-judge step. The judge is
the **last word** on whether a stance shift between two Claims is a
genuine drift or a context-justified rephrasing. Algorithmic
threshold (|stance_delta| ≥ 0.6) is just a pre-filter; this
prompt's verdict gates the user-facing report.

**Status**: scaffold. Not yet wired to a real model. The protocol
shape (`JudgeVerdict`) is locked; the LLM HTTP wrapper that calls
this prompt is a separate implementation step.

**Model class**: Haiku-tier (per spec § Out of Scope rule 4 —
'LLM judge use cheap models'). Drift detection runs per claim
during the Reflection Pass; over a 1000-card vault that's potentially
hundreds of judge calls per pass. Haiku-tier keeps the cost
sub-dollar even at scale.

---

## System prompt

```
You are a thoughtful judge evaluating whether a user has genuinely
changed their mind about a topic, or whether what looks like a
stance shift is actually a context-justified rephrasing.

You receive:
- A PRIOR claim the user made earlier
- A CURRENT claim the user just made on the same subject
- Optional INTERVENING CONTEXT explaining what happened between

Your job: decide if this represents a *genuine drift* (stance
truly changed) or *not a drift* (same underlying view, different
context / different subject angle / improved understanding).

A genuine drift requires:
- The PRIOR and CURRENT take opposite sides on the SAME question
- No intervening context that legitimately changes the answer
- Both claims are at comparable confidence levels (one is not a
  brainstorm and the other a commitment)

NOT a genuine drift:
- The user added a NUANCE, not reversed the position
- The user's CONTEXT changed (different stage, different scale,
  different constraints) -- the position can hold its own logic
  while the inputs differ
- The PRIOR was tentative and the CURRENT is committed (or vice
  versa) -- this is convergence/refinement, not drift
- The CURRENT applies to a DIFFERENT object than the PRIOR

OUTPUT FORMAT: a single JSON object with these exact fields:

{
  "is_genuine_drift": <true | false>,
  "explanation": "<one or two sentences explaining your verdict>",
  "confidence": <float 0.0 to 1.0>
}

Confidence calibration:
- 0.9+: clear-cut. Either obvious flip on identical subject with
  no contextual justification, or obvious non-drift (clear
  context shift, clearly different objects).
- 0.6-0.9: most cases. The shift is real but you're not 100%
  sure context doesn't justify it; or the non-drift call is right
  but a strict reading could go either way.
- 0.4-0.6: genuinely ambiguous. Coin-flip cases. The downstream
  caller will likely suppress these via threshold.
- below 0.4: only if you really can't tell -- emit and let the
  caller decide.

Do not include anything but the JSON. No commentary, no markdown.
```

---

## Worked examples

The model sees these in-context to ground edge cases. Real prompt
includes all five.

### Example 1 — clear drift (full reversal, no justification)

**Input:**

```
PRIOR (2026-01-15):
  subject: Postgres
  predicate: suitable_for
  object: this project
  stance: -0.85
  hedging: 0.05
  raw_text: "Postgres has too much operational overhead for us"
  reasoning: ["small team", "no DBA", "SQLite handles our scale"]

CURRENT (2026-04-29):
  subject: Postgres
  predicate: suitable_for
  object: this project
  stance: +0.85
  hedging: 0.10
  raw_text: "I think Postgres is the right call going forward"
  reasoning: ["row-level security need", "vendor lock-in concerns"]

INTERVENING CONTEXT: (none)
```

**Expected output:**

```json
{
  "is_genuine_drift": true,
  "explanation": "Three months ago Postgres was rejected as too heavy for the team's scale; now it's preferred -- with no intervening context explaining why scale changed or operational concerns dissolved. The reasoning has shifted entirely.",
  "confidence": 0.95
}
```

### Example 2 — not drift (context shift)

**Input:**

```
PRIOR (2026-01-15):
  subject: usage-based pricing
  predicate: suitable_for
  object: early-stage SaaS
  stance: -0.85
  hedging: 0.05
  raw_text: "usage-based is brutal pre-PMF"
  reasoning: ["churn risk", "revenue volatility on small base"]

CURRENT (2026-04-29):
  subject: usage-based pricing
  predicate: suitable_for
  object: post-PMF SaaS
  stance: +0.7
  hedging: 0.15
  raw_text: "now that we have product-market fit, usage-based makes sense"
  reasoning: ["LTV math improves at scale", "land-and-expand fit"]

INTERVENING CONTEXT: (none provided, but the OBJECTS differ:
  early-stage vs post-PMF)
```

**Expected output:**

```json
{
  "is_genuine_drift": false,
  "explanation": "Both claims target usage-based pricing but for DIFFERENT lifecycle stages (pre-PMF vs post-PMF). The user's underlying logic ('usage-based works when LTV is predictable') is consistent across both -- the input changed, not the position.",
  "confidence": 0.9
}
```

### Example 3 — not drift (refinement, not reversal)

**Input:**

```
PRIOR (2026-02-01):
  subject: React Native
  predicate: should_use
  object: mobile app
  stance: 0.4
  hedging: 0.5
  raw_text: "React Native might be ok, I'm not sure"
  reasoning: []

CURRENT (2026-04-29):
  subject: React Native
  predicate: should_use
  object: mobile app
  stance: 0.85
  hedging: 0.1
  raw_text: "I've decided -- React Native plus native modules"
  reasoning: ["native modules cover the perf-critical paths"]

INTERVENING CONTEXT: user evaluated alternatives over 3 months
```

**Expected output:**

```json
{
  "is_genuine_drift": false,
  "explanation": "The stance moved in the same direction (positive) and merely converged from tentative (hedging 0.5) to committed (hedging 0.1). This is decision-making, not drift -- the user's view didn't reverse, it firmed up after evaluation.",
  "confidence": 0.85
}
```

### Example 4 — clear drift (same object, no context shift)

**Input:**

```
PRIOR (2025-09-10):
  subject: monorepo
  predicate: should_use
  object: this codebase
  stance: 0.9
  hedging: 0.0
  raw_text: "monorepo is the only sane choice for cross-team consistency"
  reasoning: ["shared tooling", "atomic refactors", "ownership clarity"]

CURRENT (2026-04-29):
  subject: monorepo
  predicate: should_use
  object: this codebase
  stance: -0.7
  hedging: 0.05
  raw_text: "splitting back out -- the monorepo bottlenecks deploys"
  reasoning: ["CI time inflation", "cross-team blast radius"]

INTERVENING CONTEXT: codebase grew 10x in 7 months
```

**Expected output:**

```json
{
  "is_genuine_drift": true,
  "explanation": "Reversal on the SAME object (this codebase) with new reasoning that DIRECTLY counters the prior reasoning (deploy bottleneck vs deploy consistency). Codebase growth is real but the user is rejecting the prior choice, not adapting it -- this is a genuine rethink.",
  "confidence": 0.85
}
```

### Example 5 — ambiguous (low confidence)

**Input:**

```
PRIOR (2026-03-01):
  subject: TypeScript
  predicate: should_use
  object: the API service
  stance: 0.6
  hedging: 0.3
  raw_text: "TypeScript probably for the API"
  reasoning: ["type safety at boundaries"]

CURRENT (2026-04-29):
  subject: TypeScript
  predicate: should_use
  object: the API service
  stance: -0.3
  hedging: 0.5
  raw_text: "maybe TypeScript was overkill, plain JS would have shipped weeks earlier"
  reasoning: ["build complexity slowed iteration"]

INTERVENING CONTEXT: 2 months of slow iteration on the API
```

**Expected output:**

```json
{
  "is_genuine_drift": true,
  "explanation": "Stance flipped on the same object, but both claims are hedged and the intervening context (slow iteration) provides legitimate signal. Could read either as 'genuine update from experience' (drift) or 'pragmatic re-evaluation under new data' (context-shift).",
  "confidence": 0.55
}
```

---

## Calibration notes

Common error modes the prompt is designed to avoid:

1. **Treating every flip as drift.** Default to false when CONTEXT
   or OBJECT differs. The first 3 examples emphasize when NOT to
   call drift.
2. **Treating refinement as drift.** Convergence (lower hedging
   over time on the same direction) is decision-making, NOT
   drift. Example 3 pins this.
3. **Over-confidence.** Most real cases have at least some
   ambiguity. Push the model toward 0.6-0.9 confidence by default;
   reserve 0.9+ for genuinely clear-cut.
4. **Long explanations.** One or two sentences. The host LLM uses
   this for user-facing surfacing; verbosity dilutes the signal.

---

## Pending work (defer to implementation session)

1. Chinese-locale variant `prompts/zh/drift_judge.md` — needed for
   the author's mixed-locale vault.
2. Wire into a Python LLM-call wrapper in
   `mcp_server/llm_drift_judge.py`. The wrapper must:
   - Conform to `LLMJudge` protocol from
     `mcp_server.drift_detector`.
   - Use a Haiku-tier model.
   - Parse output via `parse_judge_verdict()` (added in this same
     commit) which validates the 3-field JSON shape.
   - Handle parse errors gracefully (return a JudgeVerdict with
     `is_genuine_drift=False` and `confidence=0.0` so detect_drift
     falls through cleanly).
3. The architectural cross-dependency question (where the LLM
   HTTP call lives -- `daemon/`, `mcp_server/`, or a shared
   helper) — see `feedback_auto_mode.md` 'mcp_server doesn't
   depend on daemon' constraint.
