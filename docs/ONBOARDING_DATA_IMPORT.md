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
in ordered steps. Each step has a recommended default — a fully
hands-off user presses Enter 13 times and lands on a working config.
Re-running the command (or `python -m throughline reconfigure`) lets
the user revisit any step; the state lives in `~/.throughline/config.toml`.

```
[1/13]  Python + venv + dependencies check
[2/13]  Qdrant (Docker) availability
[3/13]  LLM provider API key (entered here, never written to a file
        under git control)
[4/13]  LLM provider matrix (Anthropic / OpenAI / Google / xAI /
        DeepSeek / Qwen). Default: anthropic/claude-sonnet-4.6.
[5/13]  Privacy level (Local-only / Hybrid / Cloud-max). Default:
        Hybrid.
[6/13]  Embedder backend (bge-m3 / nomic-embed / MiniLM / OpenAI /
        Voyage). Default: bge-m3 local.
[7/13]  Import source (ChatGPT / Claude / Gemini / multiple / none).
        If none: cold-start warning + confirm.
[8/13]  Import scan (count conversations, estimate token volume).
[9/13]  Refine tier (Skim ~$0.005/conv, Normal ~$0.04/conv, Deep
        ~$0.20/conv). Wizard suggests a tier based on corpus size +
        daily budget.
[10/13] Card structure (Compact / Standard 6-section / Detailed +
        sidebar). Wizard runs a $0.04 test refine on one real
        conversation and shows the result before committing.
[11/13] Taxonomy source (derive from my existing vault / derive from
        my imports after first 30 cards / Johnny Decimal / PARA /
        Zettelkasten).
[12/13] Daily budget cap (THROUGHLINE_MAX_DAILY_USD). Default $20.
[13/13] Summary + y/N confirm. Writes config, kicks off first refine
        if imports were selected.
```

The rest of this doc goes deeper on each non-trivial step.

---

## Step 4: LLM provider matrix

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

## Step 5: Privacy level (orthogonal to refine tier)

Three levels, chosen separately from the refine tier. A
health-conscious user can pick "Local-only" with the "Deep" tier —
the two decisions are independent.

| Level | Slice / refine / route | Embed / rerank | Typical user |
|---|---|---|---|
| Local-only | Ollama Qwen 72B | bge-m3 local | High-sensitivity content (health, therapy, legal) |
| Hybrid (default) | OpenRouter API | bge-m3 local | Most users |
| Cloud-max | OpenRouter API | OpenAI / Voyage API | Fastest; least private |

---

## Step 6: Embedder backends (swappable, Qdrant vector size binds)

The default is bge-m3 (local, 1024d). Alternatives:

| Backend | Dim | Cost | Quality | Use when |
|---|---|---|---|---|
| bge-m3 (local) | 1024 | $0 | 9/10 | Default; you have ~8 GB RAM |
| OpenAI text-embedding-3-large | 3072 | API | 9/10 | No local GPU / no heavy RAM |
| nomic-embed-text-v1.5 (local) | 768 | $0 | 8/10 | Limited RAM but decent quality |
| all-MiniLM-L6-v2 (local) | 384 | $0 | 6/10 | CPU-only / absolute minimum |
| Voyage voyage-3 | 1024 | API | 9/10 | Long-document retrieval |

**Binding constraint:** the Qdrant collection's vector size must
match the embedder's dimension. Switching embedders post-install
requires rebuilding the collection. The wizard pins this as a
one-time decision at step 6, and `python -m throughline reconfigure`
for this step requires an explicit `--rebuild-qdrant` flag.

**Code impact:** `rag_server/rag_server.py` needs a `BaseEmbedder`
abstraction; `scripts/ingest_qdrant.py` derives `VECTOR_SIZE` from
the active embedder rather than hardcoding 1024.

---

## Step 9: Refine tier (3 tiers, 40× cost spread)

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

## Step 10: Card structure (pick after seeing a real preview)

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

## Step 11: Taxonomy derivation (not template selection)

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

## Step 7b: First-card preview gate (before bulk refine)

After import + configuration, before kicking off bulk refine, the
wizard refines **one** randomly selected conversation at the chosen
tier and shows the rendered card. The user sees actual quality,
actual structure, actual token/cost footprint, and approves
explicitly (y/N) before $0.04 becomes $42.

A user who changes tier or card structure at this gate goes back to
step 9/10 with the rerun cost absorbed by the preview envelope.

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
