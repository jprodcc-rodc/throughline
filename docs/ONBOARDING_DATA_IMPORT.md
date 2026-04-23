# Onboarding & Data Import

> Planning doc for v0.2.0. Captures how a new user (empty vault OR
> existing-chat-history user) gets from `git clone` to a working
> flywheel. Nothing below is implemented yet — this is the design
> spec before any code lands.
>
> **v0.2.0 scope principle (2026-04-23):** every onboarding decision
> happens inside a single `python -m throughline install` wizard
> (13 steps, 1 default per step, all Enter for sensible defaults).
> No separate `import`, `configure`, `setup` commands for v0.2.0 —
> one entry point. The wizard is the deliverable.

---

## `python -m throughline install` — the single entry point

The v0.2.0 onboarding is one wizard that collects every user decision
in ordered steps. Each step has a recommended default. A fully
hands-off user on the default path presses Enter 16 times and lands
on a working config. Two early branches (step 2 Mission and
step 5 Privacy) can drop the effective step count to 9-10 for
specialised missions. Re-running (`python -m throughline reconfigure`)
lets the user revisit any step; state persists to
`~/.throughline/config.toml`.

```
[1/16]  Python + venv + dependencies check
[2/16]  Mission — Full flywheel / RAG-only / Notes-only    ← early branch
[3/16]  Vector DB — Qdrant / Chroma / LanceDB / DuckDB-VSS
        [skipped if Notes-only]
[4/16]  LLM provider API key (entered here, never persisted to a
        git-tracked path)
[5/16]  LLM provider matrix — Anthropic / OpenAI / Google / xAI /
        DeepSeek / Qwen. Default: anthropic/claude-sonnet-4.6.
[6/16]  Privacy level — Local-only / Hybrid / Cloud-max. Default:
        Hybrid.
[7/16]  Retrieval backend — embedder + reranker paired
        (bge-m3 + bge-reranker-v2-m3 / nomic / MiniLM / OpenAI API /
        Voyage / Cohere / skip-reranker). [skipped if Notes-only]
[8/16]  Prompt family — auto-derived from step 5 (Claude → XML,
        GPT → Markdown+JSON, Gemini → structured output, else
        generic). Shown for confirm only.
[9/16]  Import source — ChatGPT / Claude / Gemini / multiple / none.
        If none: cold-start warning + explicit confirm.
[10/16] Import scan — count conversations, estimate token volume.
[11/16] Refine tier — Skim ~$0.005/conv, Normal ~$0.04/conv,
        Deep ~$0.20/conv. Wizard auto-suggests based on corpus size
        and daily budget.
[12/16] Card structure — Full/Notes-only: Compact / Standard /
        Detailed. RAG-only: fixed RAG-optimized format, step
        auto-skipped.
[13/16] First-card preview — refine one real conversation at chosen
        tier+structure, show result, optionally tune via 5 dials
        (Tone / Length / Sections / Register / Keep-verbatim).
        Repeat until user approves.
[14/16] Taxonomy source — derive from existing vault / derive from
        first 30 imported conversations / fallback template
        (JD / PARA / Zettelkasten).
[15/16] Daily budget cap — THROUGHLINE_MAX_DAILY_USD. Default $20.
[16/16] Summary + y/N. Writes config, kicks off bulk refine if
        imports were selected.
```

**Mission branch effects.** Step 2 branches the rest of the wizard:

- **Full flywheel** (default, recommended): all 16 steps apply.
- **RAG-only**: skip step 12 (card format fixed to RAG-optimized);
  step 11 defaults to Skim. Effective ~12 steps.
- **Notes-only**: skip steps 3 (vector DB), 7 (retrieval backend).
  No RAG infrastructure installed. Effective ~9 steps.

The rest of this doc goes deeper on each non-trivial step.

---

## Step 2: Mission — what is throughline for YOU?

This step is the single most important branch in the wizard. It
decouples two concerns that the v0.1 architecture accidentally
welded together:

- **"Cards as notes you read in Obsidian"** (human consumption)
- **"Cards as embeddings for RAG recall"** (machine consumption)

Those aren't the same product. Forcing every user through the same
6-section refined Markdown makes RAG-only users pay for prose they
never read, and makes the prose less optimal for retrieval (dense
fact claims retrieve better than beautifully paragraphed essays).

Three mission options:

| Mission | Cards are… | Card format | Per-conv cost | Wizard length |
|---|---|---|---|---|
| **Full flywheel** (default) | Both read and retrieved | Standard 6-section | ~$0.04 | 16 steps |
| **RAG-only** | Machine-only — never rendered for humans | Title + entities + 3-8 dense claims | ~$0.001 | ~12 steps |
| **Notes-only** | Read only — no retrieval | Standard 6-section | ~$0.04 | ~9 steps |

**RAG-only card example:**

```yaml
---
title: "Setting up PyTorch on M2 Mac with MPS backend"
entities: [PyTorch, M2 Mac, MPS, Apple Silicon, GPU]
---
- PyTorch 2.0+ supports MPS backend natively
- Use `torch.device("mps")` instead of `cuda`
- Fallback: `PYTORCH_ENABLE_MPS_FALLBACK=1` for unsupported ops
- Install: `conda install pytorch torchvision -c pytorch-nightly`
- Verify: `torch.backends.mps.is_available()`
```

No narrative prose, no six-section envelope. Pure retrieval food.
The title is specific (not "about PyTorch") because the reranker
weights it high. Entities help BM25-hybrid retrieval. Claims are
atomic so the embedder has dense semantic units.

This is a separate refiner-prompt variant
(`prompts/en/refiner.rag_only.<family>.md`) and a separate
card-structure enum value — not a degraded Standard. Choosing
RAG-only means committing to never browsing cards as prose.

**Notes-only** skips step 3 (vector DB), step 7 (retrieval
backend), and every RAG-path in the running services. The daemon
refines, Obsidian shows the results, and there is no Qdrant /
Chroma / embedder / reranker deployed at all. For users who want a
smart summariser but not a memory system.

Default is **Full flywheel** — assumes the user wants everything.

---

## Step 3: Vector DB backends (Notes-only skips)

Default is Qdrant via Docker (production-ready, scales to millions
of cards). Lightweight alternatives for users who want to avoid
Docker / avoid a dedicated service:

| Backend | Needs service? | Embeddable? | Typical scale |
|---|---|---|---|
| **Qdrant** (default for Full) | Docker | No | Millions |
| **Chroma** (default for Local-only privacy tier) | Either | Yes | 10K+ |
| **LanceDB** | No (Rust-embedded) | Yes | 100K |
| **DuckDB-VSS** | No (DuckDB extension) | Yes | 100K |
| **SQLite-vec** | No (SQLite extension) | Yes | 10K |
| **pgvector** | Postgres | No | Millions |

The choice here affects `ingest_qdrant.py` naming (will become
`ingest_vectors.py` with a `BaseVectorStore` implementation
dispatching by `$VECTOR_DB`), `rag_server.py`'s retrieval layer,
and the daemon's upsert path. Non-trivial code change — this is the
largest engineering item in v0.2.0.

**Compatibility constraint:** not every vector DB supports every
payload schema. The wizard ships a compatibility matrix and disables
options that can't service the full payload (title / body_full /
tags / knowledge_identity / path). In practice this drops
SQLite-vec to "metadata-lean mode" (title + body_preview only).

---

## Step 5: LLM provider matrix

Default goes through OpenRouter, so any of these work without extra
code. The matrix helps users pick by context/cost rather than loyalty:

| Provider | Representative models | Typical use |
|---|---|---|
| Anthropic | Sonnet 4.6, Haiku 4.5, Opus 4.7 | Refine main (balanced / cheap / deep) |
| OpenAI | GPT-5, GPT-4o-mini | Backup / cheap |
| Google | Gemini 3 Flash | Judgement tasks (cheap, fast) |
| xAI | Grok 3 / Grok Code | Time-sensitive content, coding |
| DeepSeek | v3.2 | Low-cost Sonnet alternative |
| Qwen | 3.5 72B | Local alt via Ollama |

Grok requires no code change — it's an OpenRouter model ID. This
step is documentation, not engineering.

---

## Step 6: Privacy level (orthogonal to refine tier)

Three levels, chosen separately from the refine tier. A
health-conscious user can pick "Local-only" with the "Deep" tier —
the two decisions are independent.

| Level | Slice / refine / route | Embed / rerank | Typical user |
|---|---|---|---|
| Local-only | Ollama Qwen 72B | bge-m3 local | High-sensitivity content (health, therapy, legal) |
| Hybrid (default) | OpenRouter API | bge-m3 local | Most users |
| Cloud-max | OpenRouter API | OpenAI / Voyage API | Fastest; least private |

---

## Step 7: Retrieval backend — embedder + reranker (paired)

The default is bge-m3 embedder + bge-reranker-v2-m3 reranker. Both
must be chosen together because they have compatibility
implications (e.g. API-only reranker forces the embedder to be
dimension-compatible with its input encoder; some rerankers only
work on English, etc.).

**Embedder options:**

| Backend | Dim | Cost | Quality | Use when |
|---|---|---|---|---|
| bge-m3 (local) | 1024 | $0 | 9/10 | Default; you have ~8 GB RAM |
| OpenAI text-embedding-3-large (API) | 3072 | API | 9/10 | No local GPU / no heavy RAM |
| nomic-embed-text-v1.5 (local) | 768 | $0 | 8/10 | Limited RAM but decent quality |
| all-MiniLM-L6-v2 (local) | 384 | $0 | 6/10 | CPU-only / absolute minimum |
| Voyage voyage-3 (API) | 1024 | API | 9/10 | Long-document retrieval |

**Reranker options:**

| Backend | Cost | Quality | Notes |
|---|---|---|---|
| bge-reranker-v2-m3 (local) | $0 | 9/10 | Default; 2.3 GB |
| bge-reranker-v2-gemma (local) | $0 | 9/10 | Newer, larger |
| Cohere rerank-v3 (API) | $$ | 9/10 | No local RAM |
| Voyage rerank-2 (API) | $$ | 9/10 | Long-text friendly |
| Jina reranker-v2 (API) | $ | 8/10 | Cheapest API option |
| **Skip reranker** | $0 | 7/10 | Embedding-only; fastest, least RAM |

The wizard pairs them: choosing an API reranker offers only
API-compatible embedders for that provider; choosing Skip reranker
is allowed for any embedder.

**Binding constraint:** the vector DB collection's vector size must
match the embedder's dimension. Switching embedders post-install
requires rebuilding the collection. The wizard pins this at step 7,
and `python -m throughline reconfigure` for this step requires an
explicit `--rebuild-vector-db` flag.

**Code impact:** `rag_server/rag_server.py` needs `BaseEmbedder` +
`BaseReranker` abstractions; `scripts/ingest_qdrant.py` becomes
`scripts/ingest_vectors.py` with a backend dispatcher; `VECTOR_SIZE`
is derived from the active embedder, not hardcoded 1024.

---

## Step 8: Prompt family (auto-picked, confirm only)

Different LLM families produce different quality depending on how
the prompt is shaped:

- **Anthropic Claude** prefers XML tagging (`<recent_history>`,
  `<current_query>`, `<fail_safe>`). The shipped v0.1 prompts are
  already this shape.
- **OpenAI GPT** prefers Markdown + explicit JSON schema for
  structured output. Tool-use is a first-class path.
- **Google Gemini** supports structured output directly, with
  function-declarations-like schemas.
- **Other / generic** — plain Markdown with explicit output
  headers, the lowest-common-denominator form.

The wizard auto-derives the prompt family from step 5's provider
choice (Anthropic → claude, OpenAI → gpt, Gemini → gemini, else
generic). Step 8 shows the derived choice for confirm; users can
override but usually shouldn't.

Every shipped prompt exists in the corresponding family variant:

```
prompts/en/refiner.normal.claude.md
prompts/en/refiner.normal.gpt.md
prompts/en/refiner.normal.gemini.md
prompts/en/refiner.normal.generic.md
```

Cross product with tier (Skim / Normal / Deep) and mode (Full /
RAG-only) means up to ~48 prompt files. This is doc-heavy but
code-light — the pipeline just loads
`refiner.{tier}.{mode}.{family}.md` at call time.

---

## Step 11: Refine tier (3 tiers, 40× cost spread)

User picks upfront; can override per-import with `--tier`.

| Tier | Output | Pipeline | Cost per conv | Use case |
|---|---|---|---|---|
| **Skim** | 1-paragraph summary + 1 tag, single card | Haiku 4.5 one call (skip slicer, skip reranker) | ~$0.005 | Index old chat history for searchable retrieval |
| **Normal** | Standard 6-section card | Sonnet 4.6 slice → Sonnet 4.6 refine → Haiku 4.5 route | ~$0.04 | Daily use; default |
| **Deep** | Multi-pass: slice → refine → self-critique → cross-ref | Opus 4.7 + Sonnet 4.6 three-pass | ~$0.20 | Research grade, decisions, long-term memory |

Implementation is not three separate refiner scripts; it's the same
pipeline parameterised along (model × prompt × stage count). Skim
skips slicer and reranker; Deep adds a critique stage. The three
refiner prompt variants live at `prompts/en/refiner.skim.md`,
`refiner.normal.md` (current default), `refiner.deep.md`.

Cost examples for a typical 1247-conversation ChatGPT import:

- Skim: ~$6
- Normal: ~$48
- Deep: ~$240

---

## Step 12: Card structure (only for Full and Notes-only missions)

**If Mission = RAG-only this step is skipped** — the card format is
fixed to the RAG-optimized variant documented in Step 2.

The wizard doesn't ask "which structure do you want" in the abstract.
It refines one real conversation ($0.04 at Normal tier) and shows
the rendered card, then asks "does this fit?". If not, the user
swaps structure and re-previews. Cycles until the user agrees.

| Structure | Shape | Suits |
|---|---|---|
| Compact | Title + one paragraph + tags | Zettelkasten / single-claim style |
| Standard (default) | 6-section skeleton (scenario / core / execution / avoid / insight / summary) | Balanced, most users |
| Detailed | 6-section + sidebar (related cards, contradictions, open questions) | Power users, research-grade |

Implementation: three refiner prompt variants, same pipeline.
User's choice persisted to `~/.throughline/config.toml`.

---

## Step 14: Taxonomy derivation (not template selection)

The wizard prefers to **derive the user's taxonomy from their
content** rather than ship a generic template.

- **Path A — user already has an Obsidian vault.** The wizard scans
  top-level directory names plus 3-5 sampled notes per directory,
  then runs a single Claude pass (~$0.02) that emits a suggested
  `taxonomy.py`. The user reviews it in a diff view and edits. This
  is the recommended path — users see "this was built from my
  existing vault" and immediately trust it.
- **Path B — user has imports but no prior vault.** The wizard
  refines the first 30 imported conversations with the Normal-tier
  pipeline, clusters the resulting cards, then derives a taxonomy
  from those clusters. Subsequent re-refine of the full import uses
  the derived taxonomy.
- **Fallback templates.** Johnny Decimal, PARA, Zettelkasten
  templates remain available for users who prefer a known shape or
  want to skip the LLM-derivation step. These are the "I'll figure
  it out later" escape hatch, not the default path.

Tool: `scripts/derive_taxonomy.py`, one-shot, writes to
`config/taxonomy.py`.

---

## Step 13: First-card preview + 5-dial constrained edit

After import scan + tier + structure choice, before kicking off bulk
refine, the wizard refines **one** randomly selected conversation at
the chosen (tier × structure × mode × prompt family) and shows the
rendered card. The user sees actual quality, actual structure,
actual token/cost footprint.

Five tuning dials are exposed (bounded mutation — no free-form
prompt editing, which would break the refiner schema):

1. **Tone** — formal / neutral / casual
2. **Length** — short / medium / long
3. **Sections** (Full / Notes-only only) — toggle any of the six
   sections off
4. **Language register** — technical / plain / ELI5
5. **Keep-verbatim quotes** — on / off (retain literal original-
   conversation phrasing inside cards)

Each dial change re-runs refine on the same conversation and shows
the updated card. The preview loop costs about $0.04 per cycle at
Normal tier (~$0.001 per cycle at Skim / RAG-only); users typically
converge in 2-5 cycles ($0.10-$0.20 total).

Once the user approves, the tuned-dial settings are baked into
`~/.throughline/config.toml` as refiner parameters. The bulk refine
then applies them across the entire import.

**What is NOT exposed** at this gate:

- Free-form editing of prompt text — the daemon's downstream
  consumers (router, dedup, Qdrant payload) depend on a stable
  schema; arbitrary prompts break it.
- Adding new sections — sections are fixed per structure template.
- Changing the YAML frontmatter schema.

Users who want those things fork the repo, edit the prompt files,
and run the wizard with `--use-custom-prompts` to bypass the
managed defaults.

---

## The two new-user starting points

### Cold start — empty vault

- User has never used Obsidian or has an Obsidian vault with zero
  refined cards.
- They install throughline, configure OpenRouter, point it at an empty
  vault, and start chatting.
- **Expected behaviour v0.2.0:** the Filter emits a status line
  (`🌱 cold start: 0 cards · flywheel warming up`) so the user
  understands RAG will not fire until they accumulate a baseline of
  cards. The cold-start line remains until ~50 cards; a
  `🌿 ramping: N cards · partial recall` line appears in the 50-199
  range; normal recall status lines resume at 200+.
- No extra configuration is required — the daemon refines every
  conversation as it happens, and card count grows organically.

### Warm start — bulk-import existing chat history

- User has years of conversation history in ChatGPT, Claude, or
  Gemini and wants that history refined into cards before they start
  the flywheel.
- For v0.2.0 we ship three adapters that turn source exports into
  raw Markdown matching the OpenWebUI exporter's on-disk shape. The
  existing daemon then consumes those raw files without any change.

---

## Adapter specs (v0.2.0 planning)

All three adapters share the same output contract:

```
$THROUGHLINE_RAW_ROOT/
  YYYY-MM/
    YYYY-MM-DD_<conv_uuid>.md
```

…which is exactly the shape the OpenWebUI exporter produces. The
daemon's `queue_existing_raw()` catch-up picks up everything on the
next start.

Shared CLI (unified entry point, not loose `scripts/adapters/*.py`):

```bash
python -m throughline import chatgpt <zip_path> --dry-run
python -m throughline import claude  <zip_path> --out $THROUGHLINE_RAW_ROOT
python -m throughline import gemini  <zip_path>    # --out defaults to $THROUGHLINE_RAW_ROOT
```

### Design principle — aggregation happens at three distinct layers

Before diving into the adapters, a clarification that drives the whole
shape of this subsystem:

| Layer | What it aggregates | Who does it |
|---|---|---|
| **L1** | Raw source events into multi-turn conversations | **adapter** (source-specific) |
| **L2** | Conversations into individual cards (slice → refine → route) | **daemon** (already implemented) |
| **L3** | Multiple same-topic cards into master cards; cross-source synthesis | **daemon's future B2 "Merge & Synthesis" pass** (v0.3.0) |

The adapters only do L1. They deliberately do NOT do L3-style
"make the whole import come out as one well-organised knowledge base"
because:

- An adapter only sees one source. Cross-source dedupe / merge must
  compare ChatGPT + Gemini + OpenWebUI cards together.
- The right moment for L3 aggregation is "once cards reach some
  density", not "at bulk-import time" — by then the user's cards
  from the existing daemon flow are also in play.
- Doing L3 at import couples bulk import to the same machinery that
  handles steady-state synthesis. Keep the layers independent.

So: adapters produce raw MD that mirrors the shape of existing
OpenWebUI raw exports. Daemon handles the rest. B2 in v0.3.0 will
provide the "merge + master-card" story.

`--dry-run` prints a summary (number of conversations, approximate
token volume, estimated OpenRouter cost at current model prices) and
exits **without** writing anything.

All adapters must tag the emitted raw files with a frontmatter
`import_source` field (e.g. `import_source: chatgpt-2026-04-23`)
so the user can later purge a whole batch if they regret the import.

### ChatGPT export

- **How to obtain:** OpenAI → Settings → Data Controls → Export. An
  email arrives within a few minutes with a ZIP link.
- **ZIP contents:** `conversations.json` + `chat.html` +
  `message_feedback.json` + `model_comparisons.json` + `user.json`.
- **Key file:** `conversations.json`.
- **Structure:** array of conversation objects. Each conversation
  contains a `mapping` field that is a flat dict of message nodes,
  keyed by node UUID. Each node has `message`, `parent`,
  `children`. The linear conversation has to be reconstructed by
  walking from the root along `children[0]`.
- **Adapter responsibilities:**
  - Expand the `mapping` tree into a linear user/assistant
    alternation. ChatGPT branches (edits, regenerations) are
    collapsed — take the last surviving branch by `children[-1]` at
    each node.
  - Skip system-message noise and tool-call artefacts unless the
    user opts in.
  - Preserve `create_time` timestamps for `date:` frontmatter.

### Claude.ai export

- **How to obtain:** Claude.ai → Settings → Account → Privacy →
  Export data. Email arrives with a ZIP.
- **ZIP contents:** **`conversations.jsonl`** (JSON Lines — one
  conversation per line, not a single JSON array) plus some metadata
  files.
- **Structure:** each line is a full conversation object with a
  linear `messages` array. Much simpler than ChatGPT — no tree
  reconstruction.
- **Adapter responsibilities:**
  - Line-by-line parse with `json.loads(line)` in a loop.
  - One raw MD per conversation.
  - Claude Projects are embedded in the same file; optionally filter
    by project name via `--project-name`.

### Gemini (Google Takeout)

- **How to obtain:** `https://takeout.google.com/` → My Activity →
  check only **Gemini Apps** → export.
- **ZIP contents:** `Gemini Apps/MyActivity.json` at either the root
  or nested under `Takeout/`.
- **Structure:** `MyActivity.json` is Google's generic My Activity
  schema — an **event log**, one query+response per record, with no
  native conversation boundaries. Google explicitly documents this
  format as *unstable and undocumented; may change without notice*.

#### Reconstruction strategy (daily grouping + cross-day semantic stitch)

The adapter cannot just emit "1 event = 1 MD". The daemon's slicer is
designed for multi-turn input; feeding it 2-sentence events produces
thin, fragmented cards at 6× the cost. But the naive "30-minute time
gap" cluster (the upstream author's original approach) is too rigid —
it either over-fragments (a topic revisited nightly becomes 7 separate
sessions) or over-merges (a single evening's multi-topic burst
collapses to one noisy session).

The adapter reconstructs conversations in two passes:

1. **Day buckets.** Group every event into the calendar day of its
   timestamp.
2. **Cross-day continuation stitch.** For each day boundary
   (last event of day N-1 vs first event of day N), embed both via
   the local bge-m3 rag_server and compute cosine similarity. If
   `cosine > 0.5`, merge day N's events into day N-1's bucket — the
   user left a topic open overnight and resumed it. Otherwise keep
   the boundary.

Each resulting bucket becomes one raw MD file with reconstructed
user/assistant alternation. The daemon's slicer then subdivides each
bucket by topic as usual.

- **Why not finer-grained event-pair semantic clustering (e.g.
  Haiku per adjacent pair)?** Costs ~$1 / 1000 events, and the
  daemon slicer does a second pass anyway — redundant work. Daily
  grouping + stitch is the 80/20 tradeoff: ~85% accuracy, zero
  extra API cost (bge-m3 runs locally), explainable to users
  ("split on day, merge if topic continues").

- **HTML → Markdown:** use the `markdownify` library
  (BeautifulSoup-based). Do **not** use regex — Gemini's
  `safeHtmlItem` field contains nested code blocks, lists, and
  anchor tags that trip naive regex every time.

- **Defensive parsing.** Unrecognised record shapes are dumped to
  stderr and skipped, not crashed. Archive build-date is logged so a
  format change can be correlated with a dated export.

---

## Privacy / cost guardrails for bulk import

Importing 1000+ chats triggers a large refine backlog. Both privacy
and cost risk surface at that moment:

- **Cost:** every conversation goes through Slicer + Refiner + 2×
  Router calls. At Sonnet 4.6 prices, a 5-year ChatGPT archive can
  be $50-$200 of API spend depending on volume. v0.2.0 must ship a
  `THROUGHLINE_MAX_DAILY_USD` env var that pauses the daemon queue
  once hit.
- **Privacy:** imported conversations may contain personally
  identifiable information the user did not intend to persist as
  cards. The adapter `--dry-run` output must show this explicit
  confirmation prompt:

  ```
  About to ingest 1247 conversations (~3.2M tokens).
  - LLM refiner will run on each → approx $42 at current Sonnet rates
  - Cards will be written to $VAULT_PATH
  - Qdrant vectors will be upserted to collection obsidian_notes
  - All cards will carry frontmatter `import_source: chatgpt-2026-04-23`
    so you can later remove this batch with
    `python scripts/bulk_purge.py --import-source chatgpt-2026-04-23`
  Continue? (y/N)
  ```

  Only after the user types `y` does actual writing begin. Adapter
  writes a manifest `state/imports/<import_source>.json` with
  per-conversation UUIDs so purge can undo cleanly.

---

## New-user rough edges (v0.2.0 P1 scope)

Not ship-blockers for v0.2.0, but each one is a known friction point
for a fresh install. Priority order by observed friction:

1. **Obsidian is not required.** The daemon writes plain Markdown;
   any editor works. `README.md` + `DEPLOYMENT.md` should say this in
   the opening paragraph — currently they implicitly assume Obsidian
   is installed.
2. **bge-m3 / bge-reranker first download is ~5 GB.** A `preflight`
   step in `DEPLOYMENT.md` should suggest `huggingface-cli download
   BAAI/bge-m3 BAAI/bge-reranker-v2-m3` before starting the
   RAG server, so a slow-connection user sees hf progress instead of
   a silent stuck server.
3. **Taxonomy fork friction.** The shipped `taxonomy.example.py` is
   Johnny-Decimal 10-90 with RODC-style leaves. Users on PARA or
   Zettelkasten hesitate to fork. v0.2.0 ships 2-3 taxonomy templates
   (`taxonomy.jd.py`, `taxonomy.para.py`, `taxonomy.zettel.py`) and
   a five-line "how to pick one" section in the deployment guide.
4. **Uninstall / nuke path.** A user who tries throughline and
   decides it isn't for them needs a one-command uninstall.
   `scripts/uninstall.sh` shuts services, drops the Qdrant
   collection, deletes `state/` and `logs/`, and optionally keeps
   the refined vault cards. Document the side-effects clearly.

---

## Hero gif strategy (deferred — do after usability is green)

**Status:** deferred from v0.2.0. The author chose to spend v0.2.0 on
"can a new user actually USE the tool end to end with minimum
friction" (U1-U8 above) before any marketing/polish work. Gif
authoring lands in a later v0.2.x phase once the adapters ship and at
least one external alpha confirms the install path.

The design below stays in the doc so future-you doesn't have to
redesign from scratch when the time comes.

Two gifs, different audiences:

1. **README top hero (30 s, silent, loops).** Six beats telling the
   whole flywheel story: user chats → cards grow → bulk import →
   richer recall. No CLI details — focus on the closed loop. Text
   overlays only, no voice.
2. **Import walkthrough (60 s, no loop).** Embedded in this doc
   below the adapter specs. Shows one complete adapter run end to
   end (`python -m throughline import gemini ...` recommended,
   since Gemini is the trickiest — confidence by example).

### Toolchain (chosen for reproducibility)

| Segment | Tool | Why |
|---|---|---|
| Terminal CLI (all progress bars, prompts) | [Charm VHS](https://github.com/charmbracelet/vhs) | `.tape` source checked into repo; anyone can `vhs render` to regenerate after a UI tweak. |
| Obsidian / OpenWebUI UI capture | OBS Studio (or Loom) | True UI, no automation substitute. |
| Titles, transitions, brand colours | [Remotion](https://www.remotion.dev/) | React/TS as source. Deterministic render. |
| Final composition | ffmpeg | Simple overlay + concat. |

Each gif has a `docs/assets/hero/` directory (tape files, source
`.mp4`, rendered `.gif`). The tape files are the source of truth —
pixel-equivalent renders can be reproduced without re-recording UI.

Claude Design (SVG / brand / banners) is a separate deliverable from
the gifs — it covers the static visual identity (logo, README
`<img>` above the gif, architecture diagram polish). Not a substitute
for the UI-capture segments.

---

## Out of scope (deferred)

- **Running without OpenRouter.** Some alpha users may want Ollama
  local models for privacy. Cost pattern is different; taxonomy
  prompts tuned against Sonnet 4.6 may degrade. v0.3.0 candidate,
  not v0.2.0.
- **Mobile OpenWebUI compatibility.** Filter Functions UI on mobile
  is not tested. Assume desktop-first for v0.2.0.
- **Multi-tenant / team vault.** Current design is single-user.
  Changing that touches collection naming, ingest path
  normalisation, and personal-context leakage. Not v0.2.0.

---

## Status

**Design spec only.** None of the adapters or the cold-start status
line are implemented yet. Tracking issues will land in the v0.2.0
GitHub milestone once it is opened.
