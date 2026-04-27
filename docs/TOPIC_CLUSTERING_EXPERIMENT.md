# Topic clustering accuracy experiment

The Reflection Layer (Open Threads / Contradiction Surfacing /
Drift Detection — see [`REFLECTION_LAYER_DESIGN.md`](REFLECTION_LAYER_DESIGN.md))
ships only after topic clustering hits ≥75% pairwise accuracy on
the maintainer's vault. This is the engineering gate that
prevents false-positive contradictions from killing user trust on
first use.

This doc walks through running the experiment yourself.

---

## Why this gate exists

The Reflection Layer's three sub-functions all depend on grouping
cards by topic. If clustering puts unrelated cards in the same
cluster, `check_consistency` will surface false contradictions:

> *"You're going with usage-based pricing? Three months ago you
> argued for value-based pricing on the topic of [unrelated
> security architecture decision]."*

Users see one of those and uninstall. The accuracy gate is real.

---

## What you need

1. **A real vault** with refined cards in
   `$THROUGHLINE_VAULT_ROOT/**/<card>.md` (frontmatter + body).
   The maintainer's reference vault has ≥2,300 cards; for an
   experiment, sample 100-200.
2. **rag_server running** locally (`python rag_server/rag_server.py`).
   The experiment calls `/v1/embeddings` for bge-m3 vectors.
3. **A ground-truth file** — JSON mapping a sample of card
   relpaths to topic labels. Producing this file is the actual
   work of the experiment; see § "Producing ground truth" below.

---

## Producing ground truth

Pick **100-200 cards** as your evaluation sample. Smaller and
the metric is too noisy; larger and labeling burns out fast.

For each sampled card, assign a **topic label** — a short string
that captures what the card is *about*, more granular than the
X-axis tag. Examples:

| X-axis tag (auto) | Topic label (you assign) |
|---|---|
| `Health/Biohack` | `keto_rebound_mechanisms` |
| `Health/Biohack` | `sleep_apnea_decision` |
| `Tech/AI` | `mcp_server_design` |
| `Tech/AI` | `mcp_tool_descriptions` |
| `Tech/AI` | `topic_clustering_design` |
| `Biz/Monetization` | `pricing_strategy` |
| `Biz/Monetization` | `freemium_conversion` |

Two cards get the **same label** iff they're on the *same topic*
in the way the Reflection Layer needs to detect contradictions
within. "Pricing" is too broad; "freemium conversion economics"
is right-grained.

### Three ways to produce labels

1. **Manual (highest quality, slow)** — open each card, type a
   label. ~30 seconds per card; 100 cards = ~50 min.
2. **LLM-assisted (fast, needs review)** — send card titles +
   first 200 chars to an LLM, ask for a short topic label.
   Review and collapse near-duplicate labels (`pricing_strategy`
   vs `pricing_decision` should be one label, not two).
3. **Hybrid** — LLM proposes for an initial pass, you fix the
   borderline cases.

Save the result as a JSON file:

```json
{
  "cards": {
    "10_Tech/2026-01-15_mcp_server_scaffold.md": "mcp_server_design",
    "10_Tech/2026-01-22_mcp_tool_iteration.md": "mcp_tool_descriptions",
    "10_Tech/2026-02-01_topic_clustering.md": "topic_clustering_design",
    "20_Health/2026-04-02_keto_rebound.md": "keto_rebound_mechanisms",
    "20_Health/2026-04-15_keto_calorie_creep.md": "keto_rebound_mechanisms",
    ...
  }
}
```

Card paths are **vault-relative with forward-slashes**. Labels
are arbitrary strings; the metric is "do clustering and ground
truth agree on which pairs share a label", not "did clustering
pick the right name for the cluster".

---

## Running the experiment

```bash
# Make sure rag_server is up
python rag_server/rag_server.py &

# Single-threshold run
python -m mcp_server.clustering_experiment \
    --vault ~/ObsidianVault \
    --ground-truth ground_truth.json \
    --threshold 0.75
```

Output:

```
loaded 156 ground-truth labels from /path/to/ground_truth.json
vault: /home/you/ObsidianVault

=== threshold = 0.75 ===
AccuracyReport (FAIL the 75% gate)
  pairwise_accuracy:   0.682
  homogeneity:         0.840
  completeness:        0.612
  v_measure:           0.706
  cards:               156
  predicted clusters:  41
  truth clusters:      29
  pairs total:         12090
  pairs agreed:        8245
  false positives:     412   (predicted-same but truth-different — these cause false-positive contradictions)
  false negatives:     3433  (predicted-different but truth-same — these cause missed Open Threads)
```

### Sweep mode

```bash
python -m mcp_server.clustering_experiment \
    --vault ~/ObsidianVault \
    --ground-truth ground_truth.json \
    --sweep 0.55,0.60,0.65,0.70,0.75,0.80,0.85
```

Reports each threshold's accuracy + which threshold was best.

---

## Interpreting the report

### Headline: `pairwise_accuracy`

For every pair of cards in the sample, did clustering agree with
ground truth on whether they share a topic? **The 75% gate is
written against this number.**

### Diagnostic: `false_positives` vs `false_negatives`

These two failure modes have opposite UX consequences:

- **False positive** — predicted-same, truth-different. Causes
  spurious contradictions ("you contradicted yourself" — but
  actually it's a different topic). **Trust-killing**. Must be
  near zero to ship the daemon.
- **False negative** — predicted-different, truth-same. Causes
  missed Open Threads (you have unfinished thinking but the
  daemon didn't see it). **Annoying but not trust-killing**.

If FP is low and FN is high, the threshold is too strict —
clusters are too small. Lower the threshold.

If FP is high, the threshold is too loose — different topics
collapse into one cluster. Raise the threshold OR enable LLM
boundary judgment (not yet wired into the CLI; see "Hybrid mode"
below).

### Diagnostic: `homogeneity` vs `completeness`

Standard clustering metrics:

- **Homogeneity** — does each predicted cluster contain cards
  from only one ground-truth cluster? Low → over-merging.
- **Completeness** — are cards from the same ground-truth cluster
  in the same predicted cluster? Low → over-splitting.

V-measure is their harmonic mean. The pairwise gate is what
matters for shipping; H/C/V are diagnostic.

---

## What to do when the gate fails

### Gate failed at all swept thresholds

The pure-embedding approach isn't enough on this vault. Options:

1. **Inspect false positives** — the report doesn't currently
   list specific failing pairs (a future enhancement). Manually
   spot-check a few false-positive pairs to see what makes them
   look similar to bge-m3 but actually different.
2. **Try LLM boundary judgment** — the algorithm supports an
   `llm_judge` callable that runs only on ambiguous pairs (between
   `low_threshold` and `high_threshold`). Plumbing this through
   the CLI is the next step if pure embedding maxes out.
3. **Try richer embedding text** — the default uses title +
   first 300 chars of body. Try `--body-chars 600` or more.
4. **Tighten the topic labels** — if your ground truth is
   inconsistent (e.g. you sometimes used `pricing_strategy` and
   sometimes `pricing_decision` for the same actual topic), the
   metric punishes you for ambiguity that's in YOUR labels, not
   the algorithm.

### Gate passed at the best threshold

Document the threshold you used (commit the ground-truth file +
report). That number becomes the daemon's default. Phase 2 of
the Reflection Layer can ship.

---

## Threshold tuning intuition

| Threshold | What it means |
|---|---|
| 0.55 | Almost everything is "same topic" — homogeneity tanks |
| 0.65 | Reasonable for related-but-different topics on the same X-axis (e.g. all pricing cards merge) |
| 0.75 | Stricter; same-topic pairs need to be quite similar |
| 0.85 | Only near-duplicates merge; high homogeneity, low completeness |

bge-m3 cosine similarity scores tend to land in 0.4-0.85 for
real-vault card pairs. The interesting band is 0.65-0.80.

---

## Hybrid mode (planned, not yet in CLI)

The algorithm in `mcp_server/topic_clustering.py` already supports
an `llm_judge` callable that's called on pairs with cosine
similarity in `(low_threshold, high_threshold)`. Once the
embedding-only path's accuracy ceiling is known, the next iteration
plumbs an LLM judge through the CLI:

```bash
# Future:
python -m mcp_server.clustering_experiment \
    --vault ~/ObsidianVault \
    --ground-truth ground_truth.json \
    --threshold 0.75 \
    --llm-judge anthropic    # or openai / openrouter / ...
```

The judge would call a small Haiku-class model on each ambiguous
pair: *"Are these two cards on the same topic? Yes/no."* Cost
estimate: ~$0.0001 per pair. With ~5% ambiguous-band pairs in a
200-card sample (~10K pairs total → ~500 ambiguous), one full
run costs ~$0.05.

---

## Cross-session continuity

If you stop the experiment and come back:

- Ground-truth file is the durable artifact. Save it under
  `private/clustering_experiment/ground_truth_v1.json` (gitignored
  so vault content doesn't leak).
- Report files: same place, named with the threshold that
  produced them.
- The Phase 2 daemon's clustering threshold is whatever passed
  the gate; that decision lives in code (`config/taxonomy.py` or
  `daemon/reflection.py` once shipped).

---

## See also

- [`REFLECTION_LAYER_DESIGN.md`](REFLECTION_LAYER_DESIGN.md) —
  what the clustering enables
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — how clustering plugs
  into the existing pipeline
- [`mcp_server/topic_clustering.py`](../mcp_server/topic_clustering.py) —
  algorithm
- [`mcp_server/clustering_accuracy.py`](../mcp_server/clustering_accuracy.py) —
  metrics
- [`mcp_server/clustering_experiment.py`](../mcp_server/clustering_experiment.py) —
  CLI driver
