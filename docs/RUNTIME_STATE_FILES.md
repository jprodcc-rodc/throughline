# Throughline runtime state files

The Reflection Pass daemon (`daemon/reflection_pass.py`) and the
MCP tools (`mcp_server/tools/`) communicate via JSON state files
under `$THROUGHLINE_STATE_DIR/` (default
`~/throughline_runtime/state/`). The daemon is the only writer;
MCP tools and the `--inspect` / `--explain` diagnostics are pure
readers.

This doc lists every file, its schema, when it's written, who
reads it, and how to inspect it.

---

## TL;DR — file inventory

| File | Writer | Readers | Refresh cadence |
|------|--------|---------|-----------------|
| `reflection_pass_state.json` | daemon | `--inspect`, doctor | every pass (non-dry-run) |
| `reflection_cluster_names.json` | daemon stage 3 | daemon (cache), `--inspect` | when new clusters formed |
| `reflection_backfill_state.json` | daemon stage 4 | daemon (cache), `--inspect` | when card mtime changes |
| `reflection_open_threads.json` | daemon stage 5 | `find_open_threads` MCP tool | every pass |
| `reflection_positions.json` | daemon | `check_consistency`, `get_position_drift` MCP tools | every pass |
| `reflection_writeback_preview.json` | daemon stage 8 | `--diff-preview`, future `--commit-writeback` | every pass |
| `reflection_contradictions.json` | daemon stage 6 (NOT YET) | future `check_consistency` enrichment | every pass once stage 6 ships |
| `reflection_drift.json` | daemon stage 7 (NOT YET) | future `get_position_drift` enrichment | every pass once stage 7 ships |

Run `python -m daemon.reflection_pass --inspect` to see a live
summary of what's present and how stale.

---

## `reflection_pass_state.json` — per-pass watermark

**Writer:** `daemon/reflection_pass.py:run_pass` at end of each
non-dry-run pass.

**Shape:** serialized `PassResult` dataclass.

```json
{
  "started_at": "2026-04-28T12:00:00+00:00",
  "finished_at": "2026-04-28T12:00:30+00:00",
  "cards_scanned": 2477,
  "cards_reflectable": 72,
  "cards_excluded": 2405,
  "cards_with_position_signal": 0,
  "cards_clustered": 72,
  "clusters_count": 24,
  "cluster_names_resolved": 24,
  "backfill_completed": 72,
  "open_threads_detected": 8,
  "contradictions_detected": 0,
  "drift_phases_computed": 0,
  "cards_updated": 0,
  "dry_run": false,
  "stages_completed": [...],
  "stages_skipped": [...],
  "errors": []
}
```

**Use cases:** doctor checks that a pass ran in the last N hours;
`--inspect` shows last-run age and per-stage counters; future
incremental mode uses `started_at` as a watermark for "what
changed since last pass".

---

## `reflection_cluster_names.json` — stage 3 cache

**Writer:** stage 3 (`_stage_resolve_cluster_names`) when
`--enable-llm-naming` is set. Mutated in-place during the pass;
written at end if the pass is non-dry-run.

**Shape:** `cluster_signature -> snake_case_name`.

```json
{
  "0|10_Tech/foo.md,10_Tech/bar.md": "pricing_strategy",
  "1|20_Health/a.md,20_Health/b.md,20_Health/c.md": "b1_thiamine_therapy"
}
```

The signature combines `cluster_id` with sorted member paths so
re-clustering with shifted membership invalidates the cache
naturally. When the pass re-runs and a cluster's membership
hasn't changed, the cache hit avoids the LLM call entirely.

---

## `reflection_backfill_state.json` — stage 4 cache

**Writer:** stage 4 (`_stage_backfill_position_signal`) when
`--enable-llm-backfill` is set.

**Shape:** `<card_path>|<mtime_int> -> {claim_summary, open_questions}`.

```json
{
  "/path/to/card.md|1714512345": {
    "claim_summary": "Use B1 daily for nerve repair",
    "open_questions": ["What's the right dose escalation?"]
  }
}
```

Cache invalidates when `mtime` shifts (user edited the card),
ensuring re-runs only fire LLM calls for new or changed content.

---

## `reflection_open_threads.json` — stage 5 output

**Writer:** every pass (after stage 5), regardless of dry-run.
Stage 5 is pure structural — no LLM, no I/O risk.

**Reader:** `mcp_server/tools/find_open_threads.py`.

**Shape:**

```json
{
  "generated_at": "2026-04-28T12:00:00+00:00",
  "vault_root": "/Users/.../ObsidianVault",
  "dry_run": false,
  "open_threads": [
    {
      "card_path": "/path/to/card.md",
      "topic_cluster": "pricing_strategy",
      "open_questions": [
        "How to handle freemium conversion?",
        "What happens to LTV at scale?"
      ],
      "last_touched": "2026-01-15",
      "context_summary": "Discussing freemium pricing for early-stage SaaS"
    }
  ]
}
```

Sorted by `last_touched` DESC. The `find_open_threads` tool
applies optional topic filter and limit; total count comes from
the entries length.

---

## `reflection_positions.json` — comprehensive position database

**Writer:** every pass. The widest state file — every reflectable
card's stance/reasoning/date/cluster keyed by cluster.

**Readers:** `mcp_server/tools/check_consistency.py`,
`mcp_server/tools/get_position_drift.py`.

**Shape:**

```json
{
  "generated_at": "2026-04-28T12:00:00+00:00",
  "vault_root": "/.../ObsidianVault",
  "dry_run": false,
  "clusters": [
    {
      "cluster_id": "0",
      "topic_cluster": "pricing_strategy",
      "size": 3,
      "cards": [
        {
          "card_path": "/path/to/early.md",
          "title": "Early discussion",
          "stance": "Against usage-based for early-stage SaaS",
          "reasoning": ["LTV math is unpredictable", "Churn risk severe pre-PMF"],
          "open_questions": ["What changes once past PMF?"],
          "date": "2025-12-01",
          "is_open_thread": false,
          "is_backfilled": true
        }
      ]
    }
  ]
}
```

Cards within each cluster are sorted chronologically by
`date` (using `card_timestamp()` priority: frontmatter.date >
.updated > file mtime > "0").

When stage 4 (back-fill) hasn't run, `stance`/`reasoning`/
`open_questions` are null/empty and `is_backfilled: false`.
Tools degrade gracefully with explicit "no back-fill yet"
messages rather than crashing or returning empty.

---

## `reflection_writeback_preview.json` — stage 8 preview

**Writer:** every pass (stage 8). **Stage 8 in current release
NEVER mutates vault files** — this preview is the only output.
The actual atomic frontmatter rewrite is gated to a future
commit with `--commit-writeback` flag.

**Shape:**

```json
{
  "generated_at": "2026-04-28T12:00:00+00:00",
  "dry_run": false,
  "cards_would_be_modified": 72,
  "diffs": [
    {
      "card_path": "/path/to/card.md",
      "additions": {
        "position_signal": {
          "topic_cluster": "pricing_strategy",
          "stance": "...",
          "reasoning": [...],
          "conditions": null,
          "confidence": "asserted",
          "emit_source": "refiner_inferred",
          "topic_assignment": "daemon_canonicalized"
        },
        "open_questions": [...],
        "reflection": {
          "status": "open_thread",
          "last_pass": "2026-04-28T12:00:00+00:00"
        }
      },
      "skipped_fields": ["position_signal"]
    }
  ]
}
```

`additions` lists fields that would be ADDED to frontmatter.
`skipped_fields` lists fields already present in current
frontmatter (would not be overwritten).

`reflection` is treated specially: it's daemon-managed metadata
and is always added even if a prior `reflection` block exists
(daemon refreshes `last_pass` on every run).

---

## `reflection_contradictions.json` — stage 6 output (NOT YET)

**Status:** path reserved by `daemon/state_paths.py`, file not
yet written. Stage 6 (LLM contradiction judgment) is a stub.

**When implemented**, schema will be:

```json
{
  "generated_at": "...",
  "card_pairs": [
    {
      "card_a": "/path/to/early.md",
      "card_b": "/path/to/late.md",
      "topic_cluster": "pricing_strategy",
      "is_contradiction": true,
      "reasoning_diff": "...",
      "addressed_by": null
    }
  ]
}
```

`check_consistency` MCP tool will use this to filter from "all
historical positions in cluster" down to "specifically
contradicting positions" with explanation.

Until stage 6 ships, `check_consistency` returns full cluster
positions and lets the host LLM (Claude / Cursor) judge
contradiction in conversation — soft-mode default.

---

## `reflection_drift.json` — stage 7 output (NOT YET)

**Status:** path reserved, file not yet written. Stage 7 (LLM
drift segmentation) is a stub.

**When implemented**, schema will be:

```json
{
  "generated_at": "...",
  "topics": {
    "pricing_strategy": {
      "phases": [
        {
          "phase_name": "value-based pre-PMF",
          "stance": "...",
          "reasoning": [...],
          "started": "2025-04-15",
          "ended": "2025-10-20",
          "card_paths": [...]
        }
      ],
      "drift_kind": "healthy_evolution"
    }
  }
}
```

`get_position_drift` MCP tool will use this to upgrade from
"per-card trajectory" (current V1) to "per-phase trajectory"
where each phase represents a coherent stance period with
transition reasoning.

---

## Inspecting state files

Three CLI helpers:

```bash
# Pretty summary of everything
python -m daemon.reflection_pass --inspect

# Per-card diagnostic — dumps ALL state's view of one card
python -m daemon.reflection_pass --explain "S:/obsidian/card.md"

# State directory directly (raw JSON):
ls $THROUGHLINE_STATE_DIR/
cat $THROUGHLINE_STATE_DIR/reflection_pass_state.json
```

`--inspect` reports stale-ness via humanized timestamps ("3h ago"),
file sizes, per-stage counters, and sample entries.

`--explain CARD_PATH` is invaluable when an MCP tool returns a
result you don't expect — it shows you exactly which state file
has what about that card.

---

## Where state files come from in the architecture

```
┌─────────────────────────────────────────────────────────────┐
│  vault/                                                      │
│  └── card.md  (frontmatter + body)                           │
└────────────────────┬────────────────────────────────────────┘
                     │ daemon walks + parses
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  daemon/reflection_pass.py — 8-stage pass                    │
│    1. load                                                   │
│    1.5 reflectable filter (slice_id || managed_by)           │
│    2. cluster (bge-m3 via rag_server)                        │
│    3. cluster naming (LLM, opt-in) → cluster_names.json      │
│    4. back-fill (LLM, opt-in) → backfill_state.json          │
│    5. open-thread detection (no LLM) → open_threads.json     │
│    6. contradiction judgment (LLM, NOT YET) → contradictions.json
│    7. drift segmentation (LLM, NOT YET) → drift.json         │
│    8. writeback preview (no vault mutation) → writeback_preview.json
│       + writes positions.json (every-pass)                   │
│       + writes pass_state.json (every-pass watermark)        │
└────────────────────┬────────────────────────────────────────┘
                     │ MCP tools read state files
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  mcp_server/tools/                                           │
│    find_open_threads     ← reads open_threads.json           │
│    check_consistency     ← reads positions.json              │
│                            (contradictions.json when stage 6) │
│    get_position_drift    ← reads positions.json              │
│                            (drift.json when stage 7)         │
└─────────────────────────────────────────────────────────────┘
```

State files are throughline's contract between offline LLM
work (daemon) and realtime user-facing surfaces (MCP tools).
LLM cost happens in the daemon, never on the MCP hot path.
