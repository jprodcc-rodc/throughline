# Reflection Layer — user guide

This is the **user-facing companion** to
[`docs/REFLECTION_LAYER_DESIGN.md`](REFLECTION_LAYER_DESIGN.md)
(rationale + architecture) and
[`docs/POSITION_METADATA_SCHEMA.md`](POSITION_METADATA_SCHEMA.md)
(implementation reference).

It answers:
- What does the Reflection Layer let me ASK my LLM?
- What does it return that's interesting?
- How do I get it running on my vault?
- Cost and trust expectations.

---

## TL;DR

Three new MCP tools turn your throughline vault into a
**thinking-state tracker**:

| Ask | Tool that fires | What you get |
|-----|----------------|--------------|
| "Where did I leave off on X?" | `find_open_threads` | Cards with unfinished questions |
| "I'm going with X." | `check_consistency` | Past positions on the topic + their reasoning |
| "How has my view on X evolved?" | `get_position_drift` | Chronological trajectory with stance per phase |

Run **once**:

```bash
python -m daemon.reflection_pass \
  --vault ~/ObsidianVault \
  --enable-llm-naming \
  --enable-llm-backfill \
  --enable-llm-contradictions \
  --enable-llm-drift
```

**Cost:** about $0.01-0.02 per pass on a ~70-card reflectable
vault (gemini-2.5-flash via OpenRouter). Cache files dedupe so
re-runs are essentially free.

**Vault writes:** zero, until you also add `--commit-writeback`.
Without it, the daemon writes only state files under
`~/throughline_runtime/state/`.

---

## What the three tools do

### `find_open_threads` — surfaces unfinished thinking

> User: "Let's revisit pricing again."
>
> Claude (calls `find_open_threads(topic="pricing")`):
> *"Before we dive in — you have two open threads on pricing:*
> *- Two months ago you stopped at 'how to handle freemium
>   conversion?'. You'd analyzed to the LTV model but didn't
>   conclude.*
> *- Five weeks ago you wanted to research competitor data — that
>   research never appeared in any later card."*

**Trigger phrases that work well:**
- "Let's revisit X again"
- "Where did I leave off on Y?"
- "What was I thinking about Z?"
- "I need to think through X"

**Mechanism:** structural detection. After stage 4 back-fill
extracts open questions per card, stage 5 scans the cluster for
later cards that mention enough of the question's key terms. If
no later card addresses it, the question stays "open". Conservative
threshold — better to surface a stale thread you can dismiss than
silently swallow real unfinished thinking.

---

### `check_consistency` — surfaces historical positions

> User: "I'm going with usage-based pricing."
>
> Claude (calls `check_consistency`):
> *"Before I help with implementation — three months ago you held
> the opposite position. The reasoning then was:*
> *- LTV math is unpredictable*
> *- Churn risk is severe pre-PMF*
> *- Runway can't tolerate revenue volatility*
>
> *Has something changed that makes those reasons no longer apply,
> or is this a direction worth re-examining?"*

**Trigger phrases:**
- "I'm going with X"
- "I've decided X"
- "My view is X"
- "We should X"

**Mechanism:** the tool finds the cluster best matching your
statement, returns historical cards with their stance + reasoning.
**Soft mode (default)** wraps each prior position in a question
("does the earlier reasoning still apply?"); **hard mode**
states it as a contradiction. Stage 6 (LLM contradiction
judgment) filters to actually-contradicting positions when run;
without stage 6, all cluster positions surface and the host LLM
judges contradiction in conversation.

---

### `get_position_drift` — surfaces evolution

> User: "What's my current framework for evaluating product ideas?"
>
> Claude (calls `get_position_drift(topic="product evaluation")`):
> *"Your framework has gone through three phases:*
>
> *- 12 months ago: technical feasibility first*
>   *("no technical moat = no product")*
> *- 6 months ago: market size first*
>   *("a small market however deep can't sustain a team")*
> *- 3 months ago: founder-market-fit first*
>   *("only people who actually care can survive pre-PMF")*
>
> *Each shift had reasoning behind it. Most recent: heavy weight
> on founder-market-fit. Use that, or revisit the trajectory?"*

**Trigger phrases:**
- "What's my current framework for X?"
- "How has my thinking on X evolved?"
- "I think I used to feel differently about Y"
- "Walk me through the arc on Z"

**Mechanism:** stage 7 (LLM drift segmentation) groups cluster
cards into stance phases. Each phase has a name, reasoning, start
+ end dates. The tool returns this trajectory. Without stage 7,
each card is its own trajectory entry — host LLM synthesizes
phases by grouping consecutive similar-stance cards.

---

## Three-step setup

### Step 1: install + run daemons (Phase 1 setup)

If you don't already have throughline running, follow
[`docs/MCP_SETUP.md`](MCP_SETUP.md). You need `daemon` +
`rag_server` + `throughline-mcp`. Verify with:

```bash
python -m mcp_server --doctor
```

### Step 2: run the Reflection Pass

The first time, you run with all four LLM stages enabled:

```bash
python -m daemon.reflection_pass \
  --vault "$THROUGHLINE_VAULT_ROOT" \
  --enable-llm-naming \
  --enable-llm-backfill \
  --enable-llm-contradictions \
  --enable-llm-drift
```

What this does:

1. Walks your vault, filters down to the **reflectable subset**
   (cards with `slice_id` from refiner output OR non-empty
   `managed_by` for hand-curated profiles).
2. Clusters them via embedding similarity (uses the local
   `rag_server`).
3. Stage 3: LLM-names each cluster (cluster_42 → "pricing_strategy").
4. Stage 4: LLM-extracts `claim_summary` + `open_questions` per
   card. **Cached by mtime.**
5. Stage 5: token-overlap detects which questions are still
   unresolved. Pure structural; no LLM.
6. Stage 6: LLM-judges stance pairs in same cluster. Are they
   contradicting or evolving?
7. Stage 7: LLM-segments each cluster into stance phases.
8. Stage 8: writes a **preview JSON** of what frontmatter
   additions would land in each card.

State files end up under `$THROUGHLINE_STATE_DIR/`. The MCP tools
read these files in real-time when Claude / Cursor / Continue.dev
fires them. **No LLM cost on the MCP hot path.**

Inspect what got computed:

```bash
python -m daemon.reflection_pass --inspect
```

Drill into one specific card:

```bash
python -m daemon.reflection_pass --explain "/path/to/card.md"
```

### Step 3 (optional): commit to vault frontmatter

Without `--commit-writeback`, all the daemon-computed metadata
lives only in `$THROUGHLINE_STATE_DIR/*.json`. The MCP tools
work fine reading from there.

If you want the metadata IN your vault frontmatter (portable,
greppable, survives state file deletion):

```bash
python -m daemon.reflection_pass --commit-writeback
```

What this does:

- For each card with diffs in the writeback preview:
  - Writes a timestamped backup
    `<card_dir>/.<card>.backup-<unix>`
  - **Surgically appends** `position_signal` and `open_questions`
    to frontmatter. Existing keys NEVER overwritten. No PyYAML
    round-trip = no formatting drift on your existing fields.
  - Writes a sidecar `<card_dir>/.<card>.reflection.json` with
    daemon-refreshable fields (`status`, `last_pass`).

Skip the backup (only if you have git tracking the vault):

```bash
python -m daemon.reflection_pass --commit-writeback --no-writeback-backup
```

### Periodic re-run

After the initial pass, just run periodically:

```bash
python -m daemon.reflection_pass \
  --enable-llm-naming \
  --enable-llm-backfill \
  --enable-llm-contradictions \
  --enable-llm-drift
```

Cache files dedupe — only NEW or EDITED cards trigger LLM calls.
For a stable vault that hasn't changed since last pass, total
cost is near $0.

### Auto-schedule (recommended for daily use)

Manual re-runs work but most users will forget. Two service
templates ship for a weekly auto-pass:

- **macOS**: `config/launchd/com.example.throughline.reflection-pass.plist`
  — fires Sunday 3 AM via `StartCalendarInterval`.
- **Linux**: `config/systemd/throughline-reflection-pass.service` +
  `.timer` — same cadence via `OnCalendar=Sun *-*-* 03:00:00`,
  `Persistent=true` so a missed run catches up on next boot.

Both templates run the same command as the manual re-run above
(all 4 LLM stages enabled, NO `--commit-writeback` — preview only).
Edit the template if you want a different cadence, fewer stages, or
to commit writebacks automatically.

Install instructions are in [`docs/DEPLOYMENT.md`](DEPLOYMENT.md).
Verify the timer is active with:

```bash
# macOS
launchctl list | grep throughline.reflection-pass
# Linux
systemctl --user list-timers throughline-reflection-pass.timer
```

To run the pass on demand (skip the schedule wait):

```bash
# macOS
launchctl kickstart -k gui/$(id -u)/com.example.throughline.reflection-pass
# Linux
systemctl --user start throughline-reflection-pass.service
```

---

## Cost expectations

Reference: maintainer's vault (~70 reflectable cards, 24
clusters, gemini-2.5-flash via OpenRouter).

| Stage | Calls | Token cost | USD |
|-------|-------|-----------|-----|
| 3 (cluster naming) | 24 (one per cluster) | ~250 in / 8 out per call | $0.0004 |
| 4 (back-fill) | 72 (one per card) | ~1000 in / 200 out per call | $0.0097 |
| 6 (contradictions) | ~50 pairs | ~400 in / 50 out per call | $0.002 |
| 7 (drift segmentation) | ~6 multi-card clusters | ~600 in / 400 out per call | $0.005 |
| **Total per FULL pass** | ~150 calls | | **~$0.017 / ¥0.12** |

Cache makes re-runs essentially free — only NEW/EDITED cards
trigger calls.

Rough breakdown for vaults of different sizes:

- **30 reflectable cards / 12 clusters**: ~$0.007 first pass
- **70 reflectable cards / 24 clusters**: ~$0.017 first pass
- **200 reflectable cards / 50 clusters**: ~$0.045 first pass
- **500 reflectable cards / 100 clusters**: ~$0.10 first pass

---

## What you should NOT expect

- **The Reflection Layer doesn't replace careful thinking.** It
  surfaces past thinking; you still do the new thinking.
- **Cluster names will sometimes be off.** First pass with
  `--enable-llm-naming` may produce a name like "miscellaneous"
  for a cluster that's actually about a coherent topic. Edit
  manually in `reflection_cluster_names.json` (cache file) and
  the daemon respects user edits on subsequent passes.
- **Contradictions will sometimes false-positive.** Stage 6 is
  conservative but not perfect. Soft-mode default (questions, not
  assertions) is the failsafe — Claude asks rather than tells.
- **Drift segmentation requires real cluster size.** A cluster
  with only 1-2 cards stays "unsegmented" — no phase structure
  is meaningful for so few data points.

---

## When to call which tool

| If the user is... | Tool that fires |
|---|---|
| Re-starting a familiar topic | `find_open_threads` |
| Stating a position / decision | `check_consistency` |
| Asking about evolution / "current view" | `get_position_drift` |
| Asking a discrete factual question | `recall_memory` (Phase 1) |
| Asking what they've worked on | `list_topics` (Phase 1) |
| Saving a conversation as a card | `save_conversation` (Phase 1) |

Each tool has explicit "Call this when:" / "Do NOT call:" rules
in its docstring; the host LLM uses these to decide. You don't
need to prompt-engineer.

---

## Trust + privacy expectations

- All state files live under `~/throughline_runtime/state/`. None
  of the Reflection Pass output leaves your machine.
- LLM calls (when stages 3/4/6/7 are enabled) hit your configured
  provider (OpenRouter / OpenAI-compat). The card content + your
  reasoning leave your machine for those calls.
- Cache files include card paths but not card contents (just the
  extracted summaries + judgments).
- Backup files live next to your cards. Daemon never auto-deletes
  — you manage cleanup with `rm .*.backup-*`.

---

## Cross-references

- [`docs/REFLECTION_LAYER_DESIGN.md`](REFLECTION_LAYER_DESIGN.md) —
  why this exists; comparison with chat memory products
- [`docs/POSITION_METADATA_SCHEMA.md`](POSITION_METADATA_SCHEMA.md) —
  full schema reference; what's in frontmatter vs sidecar
- [`docs/RUNTIME_STATE_FILES.md`](RUNTIME_STATE_FILES.md) —
  every state file's schema and lifecycle
- [`docs/MCP_SETUP.md`](MCP_SETUP.md) — Phase 1 + Phase 2 tool
  installation walkthrough
