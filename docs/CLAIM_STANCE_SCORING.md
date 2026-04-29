# Claim Stance Scoring — design integration with `position_signal`

**Status:** v0.3 design draft for P0-2 stance-based drift detection.
Companion to `POSITION_METADATA_SCHEMA.md` (which defines the
`position_signal` block already shipped in Phase 2).

**Why this doc exists separately:** P0-2 of the deep-optimization
spec calls for a `Claim Triple` schema with **numeric stance
scoring** (–1.0 to +1.0) so drift can be detected by stance
delta, not by embedding distance. throughline already has a
production schema (`position_signal`) with **categorical**
stance/confidence on 72+ cards. This doc reconciles the two
without breaking what shipped.

**Engineering gate context:** Topic clustering accuracy gate
cleared 2026-04-28 at 0.975. P0-1 (tool-triggering eval) closed
2026-04-29 at 4/4 PASS. P0-2 implementation is gate-cleared work.

---

## The integration problem

| Concept | spec P0-2 (Claim Triple) | existing (`position_signal`) |
|---|---|---|
| stance representation | `stance: float` ∈ [–1.0, +1.0] | `stance: str` (one-sentence semantic) |
| confidence representation | `hedging: float` ∈ [0.0, 1.0] | `confidence: enum {asserted, tentative, exploratory, quoted_other}` |
| granularity | per-claim (multiple per turn possible) | per-card aggregate (one per card) |
| structure | `subject`, `subject_canonical`, `predicate`, `object` | implicit in `topic_cluster` + `stance` text |
| use case | algorithmic drift detection (stance delta + LLM judge) | display + LLM-side reasoning surface |

The spec's numeric stance is what makes algorithmic drift detection
possible. Without it, "drift" reduces to embedding distance over
stance text — which the spec correctly identifies as a topic
signal, not a stance signal.

But the existing `position_signal` is what 72+ cards already carry,
what the refiner prompts already emit, and what the 3 Reflection
MCP tools already consume. Replacing it would require re-refining
the entire vault.

## The decision: extend, don't replace

Add **numeric scoring fields** alongside the existing categorical
fields on `position_signal`. The string `stance` and categorical
`confidence` remain for display + LLM consumption; the numeric
`stance_score` and `hedging_score` enable algorithmic drift.

```yaml
position_signal:
  # ── existing fields (do not touch) ─────────────────────────
  topic_cluster: "pricing_strategy"
  stance: "against usage-based for early-stage SaaS"   # human-readable
  reasoning:
    - "LTV math is unpredictable in early stage"
    - "churn risk severe pre-PMF"
  conditions: "early-stage, pre-PMF"
  confidence: "asserted"
  emit_source: "user_stated"
  topic_assignment: "refiner_emitted"

  # ── NEW P0-2 fields (additive; absent on legacy cards) ─────
  stance_score: -0.7          # –1.0 strong oppose .. 0 neutral .. +1.0 strong support
  hedging_score: 0.1          # 0.0 certain .. 1.0 highly uncertain
  predicate: "suitable_for"   # is | should_use | suitable_for | prefers | dislikes | ...
  object: "early-stage SaaS"  # optional; extracted when present
  subject: "usage-based pricing"          # what the stance is ABOUT
  subject_canonical: "usage_based_pricing" # alias-merged, snake_case
```

### Why numeric AND categorical, not one or the other

- **Categorical for display + filter**: `confidence: tentative`
  filters out brainstorms cleanly; `confidence: quoted_other`
  filters out "the article said X" attributions. These are
  load-bearing classification decisions the LLM should make at
  emit time. A continuous score forces a threshold pick.
- **Numeric for algorithm**: `stance_delta = current.stance_score
  - prior.stance_score` is the drift detector's primary signal.
  Categorical "asserted vs tentative" doesn't give you a delta.

The two co-exist with mappings:

| `confidence` (existing) | typical `hedging_score` (new) |
|---|---|
| `asserted` | 0.0 – 0.2 |
| `tentative` | 0.4 – 0.7 |
| `exploratory` | 0.7 – 1.0 |
| `quoted_other` | n/a (skip — not user's stance) |

---

## Backward compatibility

72+ cards already have `position_signal` without the new numeric
fields. The drift algorithm must handle their absence gracefully:

1. **Missing `stance_score`, has `confidence` + `stance`**:
   the drift judge LLM gets the categorical fields and the stance
   text directly, no algorithmic delta. Roughly equivalent to
   pre-P0-2 behavior.
2. **Missing both**: card was never refined for Phase 2 — skip in
   drift detection (treat as no historical position).
3. **Both present**: full algorithmic + LLM judge path.

Refiner prompt update to emit numeric scores is gated on this
design doc landing + a Phase 2.5 implementation pass. **This doc
specifies but does not yet ship the refiner change**; that's a
separate commit set.

---

## Subject canonicalization (`subject_canonical`)

The spec calls for an alias map at `vault/.throughline/aliases.json`
keyed by canonical form, with the LLM extractor querying + updating
it during extraction:

```json
{
  "postgres": ["pg", "postgresql", "Postgres", "PG"],
  "kubernetes": ["k8s", "K8s", "kube"],
  "usage_based_pricing": ["usage-based pricing", "metered billing"]
}
```

The extractor:
1. On extraction, embeds the raw subject; cosine-compares against
   existing canonical forms in the map.
2. If similarity > 0.85 to an existing canonical, attach to it.
3. If below, create a new canonical (snake_case the raw form),
   add to map.
4. Write back the updated map.

This file is per-vault, not committed by the daemon, lives next to
existing `.throughline/` runtime state. Stays small (low hundreds
of canonicals for a multi-thousand-card vault).

---

## Drift detection algorithm (P0-2 Task 2.3 — DEFERRED)

This doc specifies the schema. The actual detection algorithm
(Task 2.3 of the spec) is deferred to a fresh implementation
session because:

- It needs LLM-judge integration with real test fixtures
- Mock-only tests are insufficient (need to validate against
  Sonnet/Haiku judge behavior)
- Adds significant test infrastructure (LLM-judge prompt fixtures,
  golden-output assertions)

The algorithm shape is in
`private/SPEC_DEEP_OPTIMIZATION.md` § P0-2 Task 2.3:

```python
def detect_drift(current_claim, vault) -> DriftReport | None:
    history = vault.find_claims(
        subject_canonical=current_claim.subject_canonical,
        predicate_similar_to=current_claim.predicate,
        before=current_claim.timestamp,
    )
    if not history:
        return None
    most_recent = history[-1]
    stance_delta = current_claim.stance_score - most_recent.stance_score
    SIGNIFICANT = 0.6
    if abs(stance_delta) < SIGNIFICANT:
        return None
    severity = abs(stance_delta) * (
        1 - max(current_claim.hedging_score, most_recent.hedging_score)
    )
    verdict = llm_judge_drift(
        prior_claim=most_recent,
        current_claim=current_claim,
        intervening_context=vault.context_between(most_recent, current_claim),
    )
    if verdict.is_genuine_drift:
        return DriftReport(severity=severity, prior=most_recent,
                           current=current_claim,
                           explanation=verdict.explanation)
    return None
```

**Key invariants** the deferred implementation must preserve:
- Embedding is for **retrieval** (find candidate priors), never
  for drift judgment.
- LLM judge is the **last** word — algorithmic threshold is a
  pre-filter, not a verdict.
- LLM judge uses a cheap model (Haiku-tier per spec § Out of
  Scope rule 4).

---

## Open design questions (defer until implementation)

1. **Per-claim vs per-card storage.** The spec says one card can
   produce multiple claims. The existing `position_signal` is
   one-per-card. Options:
   - Store the *strongest* claim in `position_signal`, additional
     claims in a `claims: [...]` array (additive)
   - Promote `position_signal` to `claims[0]`, use array uniformly
   - Keep `position_signal` for the dominant claim; only spawn
     `claims[]` when the card has genuinely multiple stances
   Current preference: option 3 (least churn, handles the 95%
   single-stance case without overhead).

2. **Aliases file location.** `vault/.throughline/aliases.json`
   per spec, but throughline daemon already writes runtime state
   to `~/throughline_runtime/state/` (per `daemon/state_paths.py`).
   Deciding between vault-side (portable) and runtime-side
   (per-machine) needs a quick design call.

3. **Granularity vs LLM cost.** Multi-claim extraction per card
   is more accurate but costs more LLM tokens at refine time.
   Single-claim is cheaper. Empirical decision after running on
   author's vault — punt to implementation phase.

---

## Next session entry points (P0-2 implementation)

When a fresh session picks up P0-2 Task 2.3 + 2.4:

1. Read this doc + `prompts/en/claim_extraction.md` (extraction
   prompt scaffold with worked examples).
2. Decide open question #1 above (per-claim vs per-card).
3. Write `mcp_server/claim_schema.py` (or `daemon/claim.py` —
   needs decision per "early decision: mcp_server doesn't depend
   on daemon" boundary): TypedDict + JSON schema validator.
4. Update one refiner prompt variant (start with
   `refiner.deep.claude.md`) to emit numeric `stance_score` +
   `hedging_score` alongside existing fields.
5. Implement `detect_drift()` per algorithm above; LLM-judge
   plumbing reuses `daemon/llm_judge.py`'s pattern.
6. Re-run topic-clustering experiment + add a drift-detection
   accuracy harness paralleling
   `evals/tool-triggering/run_eval.py`'s structure.
