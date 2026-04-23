# Onboarding & Data Import

> Planning doc for v0.2.0. Captures how a new user (empty vault OR
> existing-chat-history user) gets from `git clone` to a working
> flywheel. Adapters listed here are **not yet implemented** — this
> file is the design spec before any code lands.

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

## Hero gif strategy (v0.2.0 parallel track)

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
