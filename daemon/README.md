# Throughline Refine Daemon

A long-running process that watches a directory of raw conversation MD files
(exported from OpenWebUI or any compatible source), turns each conversation
into structured knowledge cards, routes them into a Johnson-Decimal vault
layout, and upserts them into a Qdrant collection for RAG retrieval.

## What the daemon does, at a glance

```
raw MD (watchdog) -> Extension Value Judge (cheap, skip noise)
                  -> Echo Guard (cosine + Haiku judge, block RAG echoes)
                  -> Slicer (Sonnet one-shot, or Opus 1M for big convs)
                  -> Refiner (six-section body + knowledge_identity + XYZ tags)
                  -> Domain + subpath router (falls back to System_Inbox)
                  -> Dedup against Qdrant top-k
                  -> Dual-write: formal note (JD path) + buffer stub
                  -> Qdrant upsert (forward-slash path key, payload w/ body_full)
```

## Files in this directory

| File | Purpose |
|---|---|
| `refine_daemon.py` | Main entry. `python -m daemon.refine_daemon`. |
| `taxonomy.py` | XYZ tag sets, JD root map, leaf whitelist, path normalisation. |
| `notify.py` | Cross-platform desktop notifications (macOS local, Linux/Win via SSH). |
| `pack_source_model_guard.py` | Opt-out guard that blocks specific `source_model` values from writing to the default Qdrant collection, with an optional `pack_hint` redirect. |

## Running

```bash
# One-time:
cp config/.env.example config/.env      # edit paths + API key
pip install watchdog pyyaml

# Run:
export $(grep -v '^#' config/.env | xargs)
python -m daemon.refine_daemon
```

On macOS use `launchd` with `KeepAlive=true`. On Linux use `systemd` with
`Restart=always`. The daemon is safe to restart: it re-scans `RAW_ROOT`,
hashes each file, and skips anything already processed.

## Environment variables

All of these have defaults; override with `.env` or shell exports.

| Var | Default | Notes |
|---|---|---|
| `THROUGHLINE_VAULT_ROOT` | `~/ObsidianVault` | Where refined notes land. |
| `THROUGHLINE_RAW_ROOT` | `~/throughline_runtime/sources/openwebui_raw` | Watched directory. |
| `THROUGHLINE_STATE_DIR` | `~/throughline_runtime/state` | `refine_state.json`, `cost_stats.json`. |
| `THROUGHLINE_LOG_DIR` | `~/throughline_runtime/logs` | `refine_daemon.log`. |
| `THROUGHLINE_PACKS_DIR` | `<repo>/packs` | Pack definitions. |
| `THROUGHLINE_FORBIDDEN_PREFIXES_JSON` | *(empty)* | JSON list of vault path prefixes that must never go into the default Qdrant collection. See `config/forbidden_prefixes.example.json`. |
| `OPENROUTER_API_KEY` | *(required)* | LLM calls fail without this. |
| `QDRANT_URL`, `QDRANT_COLLECTION` | `http://127.0.0.1:6333`, `knowledge_notes` | Qdrant endpoint. |
| `EMBEDDING_URL` | `http://127.0.0.1:8000/embed` | Local embedding FastAPI (bge-m3 or similar). |
| `REFINE_SLICE_MODEL`, `REFINE_MODEL`, `REFINE_ROUTE_MODEL` | Sonnet 4.6 | Per-step model overrides. |
| `ECHO_JUDGE_MODEL`, `EXT_JUDGE_MODEL` | Haiku 4.5 / Gemini 3 Flash | Cheap judge models. |

See `config/.env.example` for the full list.

## Four LLM prompts

All four system prompts live at the top of `refine_daemon.py`:

- `SLICE_SYSTEM_PROMPT` — slicer. Emits `{"slices": [...]}` with `keep` flags.
- `REFINE_SYSTEM_PROMPT_TEMPLATE` — refiner. Formatted with `VALID_X_SET`,
  `VALID_Y_SET`, `VALID_Z_SET`. Preserves the six-section body skeleton and
  `knowledge_identity` 4-value taxonomy.
- `DOMAIN_PROMPT` — top-level router (9 JD domains).
- `SUBPATH_PROMPT_TEMPLATE` — second-level router. Falls back to
  `JD_FALLBACK_PATH` (Bug #2 fix) instead of raising when the LLM returns a
  path outside `JD_LEAF_WHITELIST`.

## knowledge_identity taxonomy

| Value | Meaning | Typical share |
|---|---|---|
| `universal` | General-purpose knowledge anyone can reuse. | ~60% |
| `personal_persistent` | Long-lived personal facts / decisions. | ~35% |
| `personal_ephemeral` | Time-bound personal status. | <1% |
| `contextual` | Meaningful only in a narrow context. | ~5% |

Intent markers in the user's messages can override:
- `@refine` bypasses Extension Judge + Echo Guard (force trigger).
- `/brainstorm` forces `personal_ephemeral`.
- `/decision` forces `personal_persistent`.

## XYZ tag taxonomy

- **X = domain** (32 tags, e.g. `Tech/Network`, `AI/LLM`, `Health/Medicine`).
- **Y = form** (`y/SOP`, `y/Architecture`, `y/Decision`, `y/Mechanism`, `y/Optimization`, `y/Troubleshooting`, `y/Reference`).
- **Z = relation** (`z/Node`, `z/Boundary`, `z/Pipeline`, `z/Matrix`).

Definitions live in `daemon/taxonomy.py`. Users who want a different axis
scheme can edit those sets; the refiner prompt interpolates them at runtime.

## claim_sources provenance

Every non-trivial claim in the body is tagged with one of:

- `user_stated` — the user asserted it.
- `user_confirmed` — LLM proposed, user agreed.
- `llm_unverified` — LLM-stated, not confirmed. Kept with caution.
- `llm_speculation` — explicitly hypothetical. Usually dropped.

The full used-tag set is written to `claim_sources` in the card frontmatter.

## Method H retention gates

After the refiner returns a body, three gates guard against silent two-round
wastage (the "2x burn" pattern where a bad refiner output triggers a
high-fidelity retry):

1. **Size-aware ratio gate** — `body_chars / slice_chars` must meet a
   slice-length-dependent minimum (lower bar for tiny slices).
2. **Body absolute length** — `body_chars >= RETENTION_MIN_BODY_CHARS`.
3. **Structural completeness** — at least
   `RETENTION_MIN_SECTIONS_COMPLETE` of the six body sections must be
   non-trivially filled.

Failing any gate drops the card silently (no retry); the conversation stays
in state as `no_cards_written` until the raw MD changes.

## Echo Guard (anti-RAG-recursion)

When the user asks a question, the Filter retrieves related cards from
Qdrant and injects them. The LLM often paraphrases the retrieved content in
its reply. Without protection the daemon would then refine the paraphrase
as "new" knowledge — a recursive pollution loop.

The guard uses three tiers:

- cosine `< ECHO_PASS_BELOW` (0.60) -> proceed.
- cosine in `[0.60, 0.80)` -> ask Haiku whether it is substantively new
  content or an echo of the top-1 existing card.
- cosine `>= ECHO_BLOCK_ABOVE` (0.80) -> block without calling Haiku.

Bypasses: `@refine` marker, fingerprint shorter than
`ECHO_FP_MIN_CHARS`, top-1 card older than `ECHO_AGE_BYPASS_DAYS`.

## Packs

Conversations can be routed through a specialised pack that overrides the
slicer / refiner prompts, routing base path, and `knowledge_identity`
policy. See `packs/README.md`. The default `pte` pack demonstrates the
shape.

Detection precedence: `prefix` > `source_model` > `topic_pin` >
`route_prefix`. The first match wins; mtime hot-reload means edits to a
pack's YAML / MD take effect on the next tick without a daemon restart.

## Dashboards

The daemon writes three Obsidian dashboards for human triage:

- `00.02.04_Refine_Processing_Index.md` — one row per processed conv.
- `00.02.07_Daemon_Issues.md` — failure log the user bulk-triages later.
- `00.02.08_Auto_Refine_Log.md` — Extension Judge outcomes.

None of these contain secrets; they are safe to commit if you version your
vault publicly.

## Safe-to-commit vault paths

`_load_forbidden_prefixes()` reads a JSON list of vault path prefixes that
should never be embedded into the default Qdrant collection. Use this to
keep a private Profile / Journal subtree out of semantic search. An empty
list (the default) means everything goes in.

Packs can additionally set `qdrant_collection:` to an alternate collection
name, isolating pack-specific content. The main Qdrant server should
whitelist which collections are queryable from the Filter.

## Known caveats

- On Windows, the Qdrant point-ID for a note is derived from its
  forward-slash path. Always normalise with `.replace(os.sep, "/")` before
  computing the hash, or you'll end up with two points per note.
- `source_model` comes from the raw MD's frontmatter. Exporters must
  preserve it; otherwise the source-model guard and pack routing are
  no-ops.
- The daemon assumes files under `RAW_ROOT` are append-only. Editing an
  already-processed raw file changes its hash and triggers a re-refine;
  this is intentional (`@refine` workflow relies on it).
