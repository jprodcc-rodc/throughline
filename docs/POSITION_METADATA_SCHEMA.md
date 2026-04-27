# Position Metadata Schema — design

**Status:** v0.3 design draft. **Schema is the foundation** the
Reflection Layer's three sub-functions all share. Every other piece
— Reflection Pass daemon, the 3 MCP tools (`find_open_threads` /
`check_consistency` / `get_position_drift`), and refiner prompt
modifications — depends on this schema being right.

**Why a separate doc:** the schema appears in 4 places (refiner
prompt output, card frontmatter, daemon reflection pass, MCP tool
return shapes), so changing it later means changing 4 things at
once. Better to lock the shape now, even if implementation lands
incrementally.

**Engineering gate context:** Topic clustering ≥75% pairwise
accuracy on the author's vault was the gate for Phase 2 starting.
**Cleared 2026-04-28 at 0.975** (best threshold 0.70). Schema
design proceeds.

---

## Where the schema lives

Three layers:

```
┌──────────────────────────────────────────────────────────────┐
│  1. Refiner emits per-card stance        (refiner prompt)    │
│     position_signal: {topic_cluster, stance, reasoning, ...} │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  2. Card frontmatter persists it          (vault YAML)       │
│     # vault/.../card.md frontmatter block                    │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  3. Reflection Pass daemon aggregates     (daemon → metadata)│
│     - Cluster cards by topic                                 │
│     - Detect contradictions / drift / open threads           │
│     - Write aggregate to card metadata                       │
│       (status: open_thread, contradicts: [...], etc.)        │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│  4. MCP tools read precomputed metadata    (no LLM hot path) │
└──────────────────────────────────────────────────────────────┘
```

**Hot path observation:** the MCP tools query *precomputed* metadata.
LLM cost happens during the daemon pass (offline), not when the
host LLM calls the tool. This is why the daemon exists at all — a
realtime pass would 10× the cost and add seconds of latency to
every tool call.

---

## Field-by-field schema

```yaml
# ── existing fields (Phase 1, do not touch) ────────────────────
title: "..."
tags: ["Health/Biohack", "y/Mechanism", "z/Node"]
primary_x: "Health/Biohack"
proposed_x_ideal: "Health/Biohack"
visible_x_tags: [...]
form_y: "y/Mechanism"
z_axis: "z/Node"
knowledge_identity: "personal_persistent"
claim_provenance: [...]
cross_refs: [...]
open_questions: [...]      # already emitted by refiner; daemon
                           # promotes some of these to status:open_thread

# ── NEW Phase 2 fields ─────────────────────────────────────────
position_signal:
  topic_cluster: "pricing_strategy"        # daemon-canonicalized; see § Topic Cluster Resolution
  stance: "against usage-based for early-stage SaaS"
  reasoning:                                # ordered, most-load-bearing first
    - "LTV math is unpredictable in early stage"
    - "churn risk severe pre-PMF"
    - "runway can't tolerate revenue volatility"
  conditions: "early-stage, pre-PMF"        # null if unconditional
  confidence: "asserted"                    # asserted | tentative | exploratory | quoted_other
  emit_source: "user_stated"                # user_stated | user_implied | refiner_inferred
  topic_assignment: "refiner_emitted"       # refiner_emitted | daemon_clustered |
                                            # daemon_overrode_refiner

# Daemon-managed fields (refiner does NOT emit these; daemon writes them)
reflection:
  status: "open_thread"                     # open_thread | concluded |
                                            # superseded | inactive | null
  status_reason: "open_questions persisted unresolved across 5+ subsequent cards"
  superseded_by: null                       # path to later card if stance was updated
  contradicts:                              # paths to cards on same topic with conflicting stance
    - "vault/30_Biz_Ops/.../earlier_card.md"
  drift_phase: 2                            # which trajectory phase this card belongs to (per get_position_drift)
  last_pass: "2026-04-28T14:32:11Z"        # last Reflection Pass that updated this card

temporal:
  conversation_date: "2026-01-15"
  position_evolution_node: 3                # n-th card on this topic_cluster, daemon-assigned
```

### Why these specific fields

**`topic_cluster`** is *the* foundational identifier. Every other
Phase 2 surface keys off this. It is:

- **Free-form on emit** (refiner doesn't know the canonical name)
- **Daemon-canonicalized** post-clustering: the daemon assigns the
  canonical cluster label (see § Topic Cluster Resolution)
- **Stable across cards** so historical positions can be grouped

**`stance`** is one short sentence describing the user's posture.
*Not* the topic, *not* the reasoning. The contradiction surfacer
needs this to compare positions across time.

**`reasoning`** is the *why*. This is what makes throughline's
Contradiction Surfacing different from "you said X then you said
not-X" — the user gets the original reasons back, framed as a
question, so they can either reaffirm or recognize drift.

**`conditions`** captures position scope ("early-stage, pre-PMF").
Without this the contradiction surfacer false-positives when the
context legitimately changed: a position held "while pre-PMF" is
not contradicted by a different position held "post-PMF".

**`confidence`** tags how certainly the user held this. Important
because:

- `asserted` ("I think X") → fair game for contradiction check
- `tentative` ("maybe X, not sure") → not a position; skip
- `exploratory` ("let me think — X?") → reasoning state, skip
- `quoted_other` ("the article said X") → not the user's position;
  skip

This filter keeps `check_consistency` from misfiring on
brainstorms.

**`emit_source`** tells the daemon how reliable this signal is:

- `user_stated`: user said it explicitly. High confidence.
- `user_implied`: user behavior implied it but didn't state.
  Medium confidence.
- `refiner_inferred`: refiner's best guess from context. Low
  confidence — the daemon may discount or skip.

**`topic_assignment`** tracks provenance of the topic_cluster
itself:

- `refiner_emitted`: refiner gave us the cluster name; daemon
  accepted it
- `daemon_clustered`: refiner emitted no cluster (back-compat for
  pre-Phase-2 cards); daemon assigned via embedding similarity
- `daemon_overrode_refiner`: refiner emitted a cluster but daemon
  re-clustered and overrode (rare)

**`reflection.status`** is daemon-managed. The MCP tool
`find_open_threads` queries cards with `status: open_thread`. The
refiner does NOT emit this — the daemon decides based on:

- `open_questions` array on the card AND
- absence of resolution in subsequent cards on same topic_cluster

**`drift_phase`** assigns each card to a phase in its topic's
trajectory (per `get_position_drift`). Daemon-computed.

**`last_pass`** is a pass watermark. Lets the daemon do incremental
updates and lets MCP tools surface a "last refreshed N hours ago"
hint.

---

## Topic Cluster Resolution

The single biggest source of complexity in this schema is reconciling
two sources of topic_cluster:

1. **Refiner emits `topic_cluster: "pricing_strategy"`** based on
   the slice's content. Free-form, unconstrained vocabulary.
2. **Daemon clusters cards via bge-m3 embedding similarity** during
   the Reflection Pass.

These will sometimes disagree:

| Refiner emit | Daemon cluster | Resolution |
|---|---|---|
| `"pricing_strategy"` | `"pricing_strategy"` | accept; `topic_assignment: refiner_emitted` |
| `"saas_pricing"` | `"pricing_strategy"` | daemon canonicalizes; `topic_assignment: daemon_overrode_refiner`. Refiner-emitted name preserved in `proposed_topic_cluster` (similar to `proposed_x_ideal` pattern) for future taxonomy growth observer |
| missing (legacy card) | `"pricing_strategy"` | `topic_assignment: daemon_clustered` |
| `"pricing_strategy"` | (low confidence — singleton) | accept refiner; mark `topic_assignment: refiner_emitted`; flag for review when more cards arrive |

**Canonicalization rule** (daemon side): cluster names are
*lowercase snake_case* canonical. The clustering pipeline in
`mcp_server/topic_clustering.py` produces an integer cluster_id;
the daemon assigns a human-readable name to each cluster_id by
LLM-summarizing the union of `title` + `topic_cluster` emissions
across the cluster's members.

**Why not let refiner do all clustering:** the refiner sees one
slice at a time. It can't know that the user has 14 prior cards on
this topic. The daemon's job is the cross-card view.

**Why let refiner emit at all:** when the refiner gets the cluster
right, the daemon's job collapses to a sanity check (cheap). When
the refiner doesn't have prior context, it can leave it null and
the daemon clusters from scratch (slightly more expensive). Best
of both.

---

## Backward compatibility

**The author's vault has 2,300+ cards from v0.1.x / v0.2.x.** None
of them have `position_signal`. The Reflection Layer must work
across the whole vault, not just new cards.

**Strategy:** treat missing `position_signal` as a back-fill
opportunity, not a blocker.

Three back-fill paths, in increasing cost:

### Path A: Daemon-only inference (cheapest)

For legacy cards: the daemon's Reflection Pass extracts a minimal
`position_signal` from existing fields:

- `topic_cluster` ← embedding cluster (already computed)
- `stance` ← LLM summary of card body, 1-sentence "what does this
  card claim?" (per-card LLM call, cheap)
- `reasoning` ← from card's "Core Knowledge" section (extracted via
  parser, no LLM)
- `conditions` ← null (rarely recoverable)
- `confidence` ← `asserted` (default; we trust user's vault)
- `emit_source` ← `refiner_inferred` (signals lower trust)
- `topic_assignment` ← `daemon_clustered`

Cost: 1 LLM call per legacy card, batchable. Author's vault is
~2,300 cards × ~$0.001 per Sonnet call = ~$2.30 one-time.

### Path B: Refiner re-runs (expensive but cleanest)

Re-refine every legacy card with the new refiner prompt that emits
`position_signal`. Cost: ~$0.05 per card × 2,300 = ~$115. Not
worth it for the back-fill case; reserve for cases where Path A
inference quality proves insufficient.

### Path C: User-initiated annotation (no LLM)

A dedicated CLI command lets the user accept / edit / reject
inferred `position_signal` per card. Useful for important cards
where Path A's inference is wrong. Voluntary; doesn't gate
Reflection Layer rollout.

**Default:** Path A on first Reflection Pass after v0.3 install.
User can re-trigger Path A any time. Path B is opt-in. Path C is a
later-version polish.

---

## Refiner prompt modification spec

**Do NOT change refiner prompts in this commit.** Each of the 8
refiner variants (deep × normal × skim × rag_optimized × claude/generic)
has its own test surface; changing 8 prompts at once risks
quality regressions in 8 different ways.

This section is the *spec* for the change, to be implemented in a
separate commit per variant.

### Output schema additions

Add to the existing JSON schema:

```diff
 ## Output Schema (JSON)

 - `title`              specific, keyword-rich
 - `primary_x`          ...
 - `proposed_x_ideal`   ...
 ...
 - `open_questions`     array of 0-5 explicit unresolved questions
+- `position_signal`    object (may be null), see § Position Signal below
 - `pack_meta`          object (may be empty {{}})
```

### Position Signal section (new in prompt)

```markdown
## Position Signal

Emit `position_signal` ONLY when the slice contains a clear stance
the user is asserting on a topic that's likely to recur in their
work / life.

DO emit when:
- User says "I think X", "I've decided", "my view is", "we should",
  "I'm going with"
- User makes a significant choice that will shape downstream work
- User expresses a structured opinion with reasoning (not just a
  passing reaction)

DO NOT emit when:
- User is asking a question
- User is brainstorming or thinking out loud
- User is summarizing what someone else said (article, person)
- The "stance" would be trivially true ("I think water is wet")
- The slice is technical reference or how-to with no opinion

Schema:

    position_signal:
      topic_cluster: "pricing_strategy"      # short snake_case;
                                             # daemon canonicalizes later
      stance: "against usage-based for early-stage SaaS"
      reasoning:                             # most-load-bearing first
        - "LTV math is unpredictable in early stage"
        - "churn risk severe pre-PMF"
        - "runway can't tolerate revenue volatility"
      conditions: "early-stage, pre-PMF"     # or null if unconditional
      confidence: "asserted"                 # asserted | tentative |
                                             #  exploratory | quoted_other
      emit_source: "user_stated"             # user_stated | user_implied |
                                             # refiner_inferred

When in doubt, emit `null`. False-negative (no emit when user did
state a position) is recoverable next pass; false-positive (emit
when user was musing) creates spurious contradictions later.
```

### Test surface for prompt change

Per refiner variant:

- 5 fixture slices with strong position signal → expect non-null
  emit
- 5 fixture slices with technical reference / brainstorm → expect
  null emit
- 3 fixture slices with quoted-other content → expect
  `confidence: quoted_other` or null
- Schema validation: emitted JSON parses, all required fields
  present when non-null

8 refiner variants × 13 fixtures = 104 test cases. Reasonable per
variant. Implementable when the daemon-side consumption is wired
up — premature otherwise.

---

## Reflection Pass daemon — schema interaction

The daemon does the cross-card aggregation. Per pass:

1. **Load all cards** (or only changed-since-last-pass on
   incremental).
2. **Cluster** via `mcp_server.topic_clustering.cluster_cards()`.
   Existing `position_signal.topic_cluster` is a soft hint; daemon
   may override.
3. **Resolve canonical cluster names** (LLM call per cluster, not
   per card; ~50 calls for ~2,300 cards).
4. **Fill missing position_signal** via Path A back-fill (LLM call
   per legacy card).
5. **Detect open threads:** for each card with
   `open_questions`, scan subsequent cards on same topic_cluster.
   If no later card resolves the question, set
   `reflection.status: open_thread`.
6. **Detect contradictions:** for each card with
   `position_signal.confidence: asserted`, scan other cards on
   same topic_cluster. If a later card has a stance whose
   `reasoning` contradicts the earlier reasoning, add to
   `reflection.contradicts`.
7. **Compute drift trajectories:** for each topic_cluster with ≥3
   cards, sort by `temporal.conversation_date`, detect stance
   transitions, label phases, write `reflection.drift_phase` per
   card.
8. **Write back** to vault frontmatter via the same atomic-write
   path the daemon already uses for taxonomy updates.

---

## Failure modes

**1. Topic cluster mis-assigned.**

Cascading: every other Reflection Layer surface on a mis-clustered
card is wrong. Mitigations:

- 75% pairwise accuracy gate (cleared)
- LLM-judge for boundary cases (`mcp_server/topic_clustering.py`
  already supports `llm_judge` callable; CLI wiring in subsequent
  commit)
- Per-card `topic_assignment: daemon_overrode_refiner` flag lets
  the user spot-check daemon decisions
- User can edit `position_signal.topic_cluster` manually; daemon
  respects user edits on subsequent passes (`emit_source:
  user_stated` post-edit)

**2. Refiner emits `position_signal` for non-positions.**

Pollutes `check_consistency` with spurious contradictions.
Mitigations:

- Strict refiner guidance ("DO NOT emit when…")
- `confidence: tentative | exploratory | quoted_other` filter on
  the daemon side
- Per-call user feedback ("not a contradiction") tracked, surfaces
  to refiner-prompt iteration

**3. Soft-mode false positives still annoy.**

Even with safeguards, edge cases trigger spurious contradiction
surfaces. Mitigations:

- Soft mode default (frame as question, not assertion)
- `check_consistency.soft_mode=False` opt-in for users wanting
  stronger pushback
- Threshold tuning in production based on user feedback rate

**4. Schema migration breaks downstream tools.**

Mitigations:

- All Phase 2 fields are *additive*; no Phase 1 field is changed
- Missing `position_signal` is a valid card state; tools handle
  null gracefully
- Schema versioned implicitly by presence/absence; explicit
  `schema_version` field deferred until v0.3 → v0.4 transition

---

## What's NOT in this schema (deliberate)

- **Position embeddings.** The daemon could embed each `stance` for
  fast similarity search. Not yet — adds complexity, the bge-m3
  embedding of card body already gives us enough signal for v0.3.
- **Sentiment / emotion tags.** A "mood swing" detection feature
  was floated in earlier design. Out of scope; the four-kinds-of-
  drift table in the design doc is informative, not enforced. The
  daemon detects drift; classifying drift kind is left to the user.
- **Cross-topic links.** When a position on topic A implies a
  position on topic B, schema could link them. Out of scope; v0.3
  treats topics as independent.
- **Multi-user vaults.** All `position_signal` is single-user. Team
  vaults are out of scope per `private/PLAN_90D.md` (single-user
  is the entire product axis).

---

## Implementation milestones

Each milestone is a separate commit; this doc gates none of them
individually but should be reviewed when any milestone touches
schema-shape decisions.

1. ✅ **Schema doc.** Locks shape. (`e4548e6`)
2. ✅ **Reflection Pass daemon scaffolding.** Empty pass + frontmatter
   parse + vault walk + state-file plumbing. (`f99cf59`)
3. ✅ **Topic cluster canonicalization.** Daemon labels clusters via
   LLM (opt-in); persists cluster_signature → name cache.
   (`97920d1`, commit B)
4. ✅ **Open thread detection.** Daemon writes
   `_open_thread` + `_open_thread_questions` in-memory; serializes
   to `reflection_open_threads.json`. `find_open_threads` MCP tool
   reads the state file. (`d7f007d`, commit D)
5. ✅ **Path A back-fill.** Daemon LLM-extracts claim_summary +
   open_questions per legacy card (opt-in); persists `path|mtime`
   → essence cache. (`ab2ae3f`, commit C)
6. ☐ **Refiner prompt updates** (8 variants × 13 fixtures = 104
   test cases). Spec captured in this doc § "Refiner prompt
   modification spec"; not yet implemented.
7. ☐ **Contradiction detection.** LLM judgment on stance pairs
   in same cluster. Tool surface for `check_consistency` is
   ALREADY shipped reading `reflection_positions.json`; stage 7
   when implemented enriches that file. (`dbd2bde` shipped the
   tool, `_stage_detect_contradictions` remains stub.)
8. ☐ **Drift trajectory.** LLM segmentation of stance phases.
   Tool surface for `get_position_drift` is ALREADY shipped;
   stage 7 when implemented enriches the state file. (`dbd2bde`
   shipped the tool, `_stage_compute_drift` remains stub.)
9. ☐ **End-to-end smoke test** on author's vault with real LLM.
   Currently blocked on a working OPENROUTER_API_KEY; mock-test
   coverage stands in. The 12-commit Phase 2 series ships
   without firing a single real LLM call.

**Bonus milestones not in original plan but landed:**

- ✅ **Reflectable filter (stage 1.5).** Excludes 2,405 / 2,477
  vault files (system logs, profile drafts, no-frontmatter notes)
  from Reflection Pass. Only cards with `slice_id` or
  non-empty `managed_by` participate. (`3be15bd`)
- ✅ **Card body section parser.** Bilingual headers (English-only
  + Chinese-emoji-English + Chinese-only). 80.4% real-vault
  coverage on frontmatter cards / 100% on slicer-output cards.
  (`d972c4b`)
- ✅ **Vault-format addendum.** Real-vault calibration; see
  § "Vault format addendum" below. (`411a01a`)
- ✅ **Stage 8 writeback preview.** Computes diff per card; writes
  preview JSON; **never mutates vault files**. Real atomic
  frontmatter rewrite is gated to a future commit. (`69b7326`)
- ✅ **All 3 MCP tools real impl.** check_consistency +
  get_position_drift wired to `reflection_positions.json`.
  Phase 2 user-facing surface complete. (`dbd2bde`)
- ✅ **Public-docs sync.** ROADMAP, CHANGELOG, README reflect
  Phase 2 ship state. (`638f3ec`)

Order is deliberate: schema → daemon foundation → cluster names →
open threads (smallest end-to-end loop) → back-fill → contradiction
(highest false-positive risk; ship after smaller surfaces prove
out) → drift (most complex aggregation; last).

---

## Vault format addendum (calibrated 2026-04-28 against author vault)

Smoke-checking this schema against the author's actual production
vault (2,477 cards, 163 with frontmatter) revealed three deltas
from the design assumptions above:

**1. Frontmatter is sparser than the public refiner prompts emit.**

Real per-card frontmatter set:

```yaml
title:              # 157/163 cards
date:               # 136
tags:               # 133
knowledge_identity: # 120
managed_by:         # 72
source_platform:    # 63
source_conversation_id: # 63
slice_id:           # 63
route_to:           # 63
# plus low-frequency: triage_status, formal_path, source_md5,
# trigger_tags, last_auto_rebuild, sources, type, etc.
```

Specifically **absent**:

- `primary_x`, `proposed_x_ideal` (taxonomy emit)
- `open_questions` (the array Open Threads detection was designed
  to scan)
- `claim_provenance` (the per-claim provenance list)

The author's running daemon (`refine_thinker_daemon_v9.py`,
private) does not emit these fields — it pre-dates the public
refiner prompt schema. Path A back-fill therefore needs to fill
**all three** of: `position_signal`, `open_questions`, and
(optionally) the taxonomy fields, not just `position_signal`.

**2. Body structure uses Chinese section headers, not the
prompt-doc English ones.**

Public refiner prompt documents these section headers:

```
# Scene & Pain Point
# Core Knowledge & First Principles
# Detailed Execution Plan
# Pitfalls & Boundaries
# Insights & Mental Models
# Length Summary
```

Author's actual vault uses Chinese-prefixed equivalents:

```
# 🎯 场景与痛点 (Context & Anchor)
# 🧠 核心知识与底层原理 (First Principles)
# 🛠️ 详细执行方案 (Execution & Code)
# 🚧 避坑与边界 (Pitfalls & Gotchas)
# 💡 心智模型 (Mental Models)
# 📏 篇幅总结
```

These are bilingual: emoji + Chinese name + English in parens. The
Reflection Pass daemon's body parsers must match the bilingual
form, not the English-only form documented in
`prompts/en/refiner.deep.generic.md`. Specifically:

- Open question extraction during Path A back-fill: parse the
  `# 🚧 避坑与边界` section *or* call LLM on the full body — both
  fine; structural is cheaper if accurate
- Reasoning extraction: parse `# 🧠 核心知识与底层原理` section

This is not a schema change; it's a parser-target change. Updates
land in stage-4 (back-fill) implementation.

**3. Existing recall-callout block is already attached to cards.**

163 cards already have a `> [!info] 🧠 神经突触连结` callout
appended to body — this is the existing recall result block from
the running daemon. Phase 2 must not collide with it; the
Reflection Pass daemon writes only to *frontmatter*
(`position_signal` + `reflection.*`), never appends to body.

---

## Cross-references

- `docs/REFLECTION_LAYER_DESIGN.md` — public-facing rationale for
  why the Reflection Layer exists and what it delivers
- `docs/TOPIC_CLUSTERING_EXPERIMENT.md` — how the engineering gate
  was designed and run
- `mcp_server/topic_clustering.py` — clustering algorithm
- `mcp_server/clustering_accuracy.py` — gate metrics
- `mcp_server/tools/find_open_threads.py` — Phase 2 tool stub
- `mcp_server/tools/check_consistency.py` — Phase 2 tool stub
- `mcp_server/tools/get_position_drift.py` — Phase 2 tool stub
- `private/MCP_SCAFFOLDING_PLAN.md` § 12.A — locked decisions
  (Q1-Q4) that constrain MCP tool surfaces
- `private/PLAN_90D.md` — Phase 2 strategic position
