# Self-growing taxonomy — design

> **Status (2026-04-27):** v0.2.0 shipped the minimum closed loop
> (seed → signal → observer → review CLI). v0.2.x then shipped
> doctor surfacing of pending candidates (`5528434`) and zero-usage
> leaf detection (`ec32dae`). Only **batch retag** (`taxonomy retag
> --since DATE --domain X`) remains deferred to v0.3.
>
> **Why this exists:** the one-shot `scripts/derive_taxonomy.py`
> generates a taxonomy from a user's existing content. That fits
> users like the original author (2300+ cards at install) but
> wrong-sizes the ~75% of prospective users with 0–100 cards. Those
> users need a **skeletal starter** that grows as content arrives.
>
> This doc is the refined spec after two design passes. See
> [`ROADMAP.md`](../ROADMAP.md) for the v0.3 plan and
> [`fixtures/phase6/SESSION_STATE.md`](../fixtures/phase6/SESSION_STATE.md)
> for shipped-in-v0.2.x deltas.

---

## User-story coverage

| User state | Strategy |
|---|---|
| 0 cards (cold start) | Skeletal template (`taxonomy.minimal.py`, ~5 broad domains) |
| 20–100 imported cards | Skeletal template → observer collects signal → first growth prompt after ~1 week |
| 100–500 imported | Optionally use the one-shot derive script for a head start → then observer continues |
| 2300+ (author) | One-shot derive → observer picks up new topics as they emerge |

The one-shot derive and the growing-observer paths are
**complementary**, not competing. Wizard step 14 offers both; the
skeletal template is the default for <100 cards.

---

## Architecture — four layers

### Layer 1 · Skeletal seed

Ship `config/taxonomy.minimal.py` with a ~5-domain set broad enough
to catch anything without forcing false specificity:

```python
VALID_X_SET = {"Tech", "Creative", "Health", "Life", "Misc"}
VALID_Y_SET = {"y/SOP", "y/Decision", "y/Mechanism", "y/Reference"}
VALID_Z_SET = {"z/Node", "z/Pipeline", "z/Boundary"}
```

Wizard step 14 picks this when the user chooses
`derive_from_imports` but has fewer than N cards available, OR when
`template_minimal` is selected outright.

Goal: zero false specificity on day one; catch 100% of content
under one of five labels until the observer has enough signal to
propose a split.

### Layer 2 · Observer (daemon-side)

The refiner's output currently fills a single constrained field:

```
primary_x: must match VALID_X_SET   // current behaviour
```

Under strict constraint the refiner cannot surface "I'd prefer
something else". We need TWO fields:

```
primary_x        : string, MUST match VALID_X_SET (routing invariant)
proposed_x_ideal : string, refiner's UNCONSTRAINED preferred tag
```

Both are always emitted. When `primary_x == proposed_x_ideal` the
fit is perfect. When they differ, `proposed_x_ideal` is the growth
signal.

The daemon appends per-refine tuples to:

```
state/taxonomy_observations.jsonl
```

Line format:

```json
{"ts": "2026-04-24T10:00:00Z", "card_id": "abc123",
 "title": "Building MCP agents",
 "primary_x": "Misc", "proposed_x_ideal": "AI/Agent"}
```

**All detection state lives here.** No in-memory counters, no
periodic cron job. Appending is append-only; scanning happens only
when the user invokes the CLI.

### Layer 3 · Detector (on-demand, CLI-invoked)

When the user runs `python -m throughline_cli taxonomy`, the
detector:

1. **Reads** `state/taxonomy_observations.jsonl` for the last 14
   days (window configurable).
2. **Filters** rows where `primary_x != proposed_x_ideal`
   (drift rows).
3. **Normalises** `proposed_x_ideal` — lowercase, singular-form,
   `_`/`-`/` ` → `/`, collapse whitespace — so
   `AI/Agent` / `ai/agents` / `AI Agent` all count as one tag. (MVP
   = string normalisation; v0.3 can upgrade to bge-m3 embedding
   clustering.)
4. **Filters** normalised tags already in `config/taxonomy_rejected.json`
   (user has explicitly said "never suggest this").
5. **Clusters** by normalised tag. For each cluster, compute:
   - count (n cards)
   - day-span (first ts to last ts)
   - sample titles (first 3)
6. **Applies thresholds**:
   - `count >= 5`  (configurable `TAXONOMY_GROWTH_MIN_COUNT`)
   - `day-span >= 3 days` (configurable
     `TAXONOMY_GROWTH_MIN_DAYS`; prevents one-evening binges from
     triggering permanent taxonomy churn)
7. **Groups by parent** (`AI/Agent` → parent `AI`; ungrouped
   `Climbing` → proposed new parent `Climbing`).

Returns a list of candidates:

```python
[
  GrowthCandidate(
      tag="AI/Agent", parent="AI", parent_exists=True,
      count=8, day_span_days=11,
      sample_titles=["Building MCP agents", "Tool-use patterns",
                     "MCP protocol design"],
  ),
  GrowthCandidate(
      tag="Hobby/Climbing", parent="Hobby", parent_exists=False,
      count=5, day_span_days=9,
      sample_titles=["Indoor gym first day", "Knot recap", "Grip tape"],
  ),
]
```

### Layer 4 · User review (CLI, strictly gated)

Two commands:

```bash
python -m throughline_cli taxonomy
# NON-interactive status. Prints:
#   - current VALID_X_SET contents
#   - growth candidates (grouped by parent, with sample titles)
#   - nothing-to-review if no candidate passes thresholds

python -m throughline_cli taxonomy review
# INTERACTIVE walk-through. For each candidate:
#   Candidate 1/2: AI/Agent (under existing AI parent)
#     8 cards · 11 days · sample titles: [...]
#     Action: [a]dd  [r]eject forever  [n]ame-as-different  [s]kip
```

Actions:

- **Add** — append tag to `VALID_X_SET` in the active `taxonomy.py`;
  log the change in `state/taxonomy_history.jsonl`; old cards stay
  tagged with whatever `primary_x` they had (retag is opt-in via
  the batch-retag CLI).
- **Reject forever** — append normalised form to
  `config/taxonomy_rejected.json`; detector will never suggest it
  again.
- **Name-as-different** — user supplies preferred form
  (`Tech/AI-Agent` or whatever), which gets added instead. The
  original `AI/Agent` observations are kept in the log but won't
  re-propose (the user's preferred form is functionally equivalent).
- **Skip** — do nothing this round; same candidate may resurface
  next CLI invocation unless `TAXONOMY_SKIP_COOLDOWN_DAYS` is set.

**Everything is gated.** No silent writes, no "provisional" state,
no 7-day auto-accept window. Reversibility is via the user manually
editing `taxonomy.py` + removing tags from `taxonomy_history.jsonl`.

---

## v0.2.0 implementation split

| Component | Scope | Size | Ships in |
|---|---|---|---|
| **Seed** | `config/taxonomy.minimal.py` + wizard step 14 uses it when cards < 100 | S | v0.2.0 |
| **Signal** | Refiner prompts (8 files) grow `proposed_x_ideal` field in output schema | S (cross-file) | v0.2.0 |
| **Observer** | Daemon writes `state/taxonomy_observations.jsonl` on every refine | S | v0.2.0 |
| **Review CLI** | `taxonomy` + `taxonomy review` + `taxonomy reject` | M | v0.2.0 |
| **Doctor surfacing** | Doctor reports "N candidates pending" + Filter outlet hint | S | **shipped v0.2.x** (`5528434`) |
| **Batch retag** | `taxonomy retag --since DATE --domain X` batch re-refine | M (costs $) | v0.3 |
| **Zero-usage detection** | Flags taxonomy leaves with no cards routed to them, + deprecation hint | L | **shipped v0.2.x** (`ec32dae`) |

MVP closed loop: seed → signal → observer → review CLI. A user
picking `taxonomy.minimal` at wizard install, running throughline
for a week, then invoking `throughline_cli taxonomy review` to
expand from 5 domains to 7 → full round-trip works.

---

## Key correctness properties

### P1 · Never write taxonomy without explicit user action

The daemon's observer appends to a log; nothing else. The detector
reads; nothing else. Only `throughline_cli taxonomy review` with
user input `a` for a specific candidate writes to `taxonomy.py`.
Everything else is read-only.

### P2 · Grandfathering

Adding a new leaf never renames existing leaves. Cards tagged with
the old `primary_x` retain that tag. Retagging is opt-in (via the
batch-retag CLI) and costs money (one refine per card).

### P3 · No silent noise-triggered growth

Thresholds protect against:
- **volume binges** (`count >= 5` filters one-off topics)
- **time binges** (`day-span >= 3 days` filters one-evening sprees)
- **user veto** (`config/taxonomy_rejected.json` is absolute)

### P4 · Sideways compatibility with the one-shot derive script

`scripts/derive_taxonomy.py` writes `taxonomy.py`. The
`taxonomy review` command writes to the same file (append-only).
Both share the rendered-module format; the user can switch between
tools freely.

### P5 · Idempotent observer

Appending identical observations on re-processing a card is
tolerated — the detector deduplicates by `card_id` within the
window. Daemon crashes / restarts do not double-count.

---

## What this does NOT do (v0.2.x scope cuts)

- **No auto-merge** (`AI/LLM` + `AI/Agent` into `AI/LLM-Agent`). Users
  have strong opinions; merges are manual.
- **No auto-deprecate.** Zero-usage leaf detection (shipped v0.2.x)
  *flags* unused leaves and surfaces them in `doctor`, but the
  `taxonomy.py` change is still gated behind explicit user action.
  Users get attached to folders; we surface, the user decides.
- **No scheduled polling.** Detector only runs on `throughline_cli
  taxonomy` and `throughline_cli doctor`. The doctor surfacing
  (shipped v0.2.x) reports "N candidates pending"; integration with
  OpenWebUI's `__event_emitter__` for an in-chat weekly hint remains
  v0.3 work.
- **No cross-language clustering.** If a user's refiner emits tags
  in multiple natural languages (`AI/Agent` + `AI/代理`), they
  don't cluster. v0.3+ with bge-m3 embedding similarity.
- **No retroactive re-refine.** Old cards stay tagged with whatever
  `primary_x` they had when first refined. User opts in explicitly
  via the batch-retag CLI (v0.3).

---

## Open questions for review

1. **Thresholds.** Are `count >= 5` and `day-span >= 3 days` right
   defaults? Tuning knob exposed via env var.
2. **Normalisation scope.** Should `AI/Agent` and `Tech/AI/Agent`
   cluster? (Current plan: no — different parent structures are
   distinct signals.)
3. **Parent creation gating.** Should `Hobby/Climbing` with only 5
   cards be enough to propose *creating* the parent `Hobby`, or
   should parent-creation require a higher threshold? Tentative: same
   threshold; parent proposal is visible in the CLI output so the
   user makes the call.
4. **Review CLI UX.** Should `taxonomy review` show all candidates
   as a batch or one-by-one? Batch is faster for power users;
   one-by-one is safer for first-timers. v0.2.0: one-by-one
   (conservative).

---

## Test strategy

Mocking-friendly split:

- **Unit:** normaliser, threshold filter, clustering, manifest writer.
- **Integration:** feed synthetic observation log → assert correct
  candidate list.
- **Prompt test:** load new refiner prompts and assert
  `proposed_x_ideal` field appears in the schema description.
- **CLI:** mock `input()` for interactive review; mock filesystem
  for the taxonomy write + history log.

Target: ~40 tests across seed / signal / observer / review CLI when
all ship.
