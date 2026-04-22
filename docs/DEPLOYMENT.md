# Deployment

> End-to-end install guide for a fresh host. Assumes familiarity with
> shell, Python virtual environments, and Docker. For the reasoning
> behind each component see `ARCHITECTURE.md`; for badge semantics once
> the system is running see `FILTER_BADGE_REFERENCE.md`.

---

## Contents

- [Prerequisites](#prerequisites)
- [Step 1 — Clone and configure](#step-1--clone-and-configure)
- [Step 2 — Qdrant](#step-2--qdrant)
- [Step 3 — RAG server](#step-3--rag-server)
- [Step 4 — Refine daemon](#step-4--refine-daemon)
- [Step 5 — OpenWebUI Filter](#step-5--openwebui-filter)
- [Step 6 — Ingest an existing vault](#step-6--ingest-an-existing-vault)
- [Step 7 — Smoke test](#step-7--smoke-test)
- [Troubleshooting](#troubleshooting)
- [Platform notes](#platform-notes)

---

## Prerequisites

| Component | Minimum | Notes |
|---|---|---|
| OpenWebUI | 0.8.12 | Earlier versions lack full Valves support for Filter Functions. |
| Python | 3.11 | 3.12 / 3.13 also fine. The RAG server uses `asyncio` TaskGroups. |
| Docker | any recent | Only used for Qdrant. Podman works too. |
| Qdrant | 1.8+ | Any REST-compatible build. |
| OpenRouter account | free tier OK | Used for Haiku RecallJudge + Sonnet-class refiner. Add ~$5 credit to start. |
| Markdown vault | any layout | Johnny-Decimal (`10_`, `20_`, …) is the default; any prefix pattern works via `INGEST_INCLUDE`. |

Disk footprint, reference system:

- Qdrant storage: ~1 KB per card × 1024-dim vector ≈ <100 MB for a few thousand cards.
- bge-m3 model weights: ~2.3 GB (downloaded on first RAG server start).
- bge-reranker-v2-m3 weights: ~2.3 GB.
- Raw conversation export: roughly equal to your chat volume.

GPU is optional. The RAG server picks MPS (Apple Silicon) > CUDA > CPU
automatically. CPU-only works for small collections; large reranker
batches can be slow.

---

## Step 1 — Clone and configure

```bash
git clone https://github.com/jprodcc-rodc/throughline
cd throughline

# Create a throwaway virtualenv for scripts and services.
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt          # top-level aggregate
```

Copy the env template and fill it in:

```bash
cp config/.env.example .env
${EDITOR:-vi} .env
```

Minimum variables to set:

| Variable | What |
|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter key (also used by the daemon). |
| `VAULT_PATH` | Absolute path to your Markdown vault root. |
| `THROUGHLINE_VAULT_ROOT` | Same value; used by the daemon. |
| `THROUGHLINE_RAW_ROOT` | Directory where OpenWebUI raw conversations land. |
| `QDRANT_URL` | Default `http://localhost:6333` is fine for a local install. |
| `RAG_EMBED_URL` | Default `http://localhost:8000` is the RAG server started in Step 3. |

Optional but recommended:

```bash
cp config/taxonomy.example.py config/taxonomy.py     # edit domains
cp config/forbidden_prefixes.example.json config/forbidden_prefixes.json
cp config/contexts_topics.example.json config/contexts_topics.json
```

- `taxonomy.py` defines the directory layout the router writes cards to.
  The example is pared down to ~6-10 leaves per domain. Edit to match
  your vault.
- `forbidden_prefixes.json` is the allowlist-negation for Qdrant. Any
  card whose vault-relative path starts with one of these prefixes will
  never be upserted to the default collection, even if the router routes
  it there.
- `contexts_topics.json` drives the Personal Context auto-builder. See
  `config/README.md` for the four-strategy schema.

---

## Step 2 — Qdrant

One-liner (Docker):

```bash
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v "$HOME/qdrant_storage:/qdrant/storage" \
  qdrant/qdrant:latest
```

Verify it is up:

```bash
curl -s http://localhost:6333/healthz
# expected: "healthz check passed"
```

The collection will be created on first ingest (Step 6). No manual
`PUT /collections/<name>` call is needed — `scripts/ingest_qdrant.py`
does it with the correct vector size (1024) and Cosine distance.

---

## Step 3 — RAG server

The RAG server embeds queries, runs the reranker, and serves
`POST /rag`, `POST /v1/embeddings`, `GET /health`, and
`GET /refine_status`.

Foreground run (for smoke testing):

```bash
cd rag_server/
python rag_server.py
# defaults: host 0.0.0.0, port 8000
```

First start downloads bge-m3 and bge-reranker-v2-m3 model weights
(~5 GB total) into `~/.cache/huggingface/`. Expect 2-10 minutes
depending on bandwidth. Subsequent starts are instant.

Smoke:

```bash
curl -s http://localhost:8000/health
# {"status":"ok","device":"mps","qdrant":"up"}
```

### Service templates

| OS | Template | Notes |
|---|---|---|
| macOS | `config/launchd/com.example.throughline.rag-server.plist` | Uses `KeepAlive` + `RunAtLoad`. Install with `launchctl bootstrap gui/$(id -u) <file>`. |
| Linux | `config/systemd/throughline-rag-server.service` | Uses `Restart=on-failure`. Install to `/etc/systemd/system/` and `systemctl enable --now`. |

Both templates use placeholders (`{{USER}}`, `{{THROUGHLINE_HOME}}`,
`{{PYTHON}}`, `{{OPENROUTER_API_KEY}}`, …). Substitute before
installing; see `config/README.md` for a full list.

---

## Step 4 — Refine daemon

The daemon watches the raw-conversation directory, slices completed
conversations, refines each slice through an LLM, dual-writes (formal
note + buffer stub), and upserts embeddings to Qdrant.

Foreground run:

```bash
cd daemon/
python refine_daemon.py
```

On startup the daemon calls `queue_existing_raw()` to catch up on
anything in `THROUGHLINE_RAW_ROOT` that has not yet been processed (per
`state/refine_state.json`). This can take a while on first boot if your
raw tree is large — each new conversation costs roughly one Slicer
call + one Refiner call + two Router calls. Cost tracking is written
incrementally to `state/cost_stats.json`.

### Service templates

| OS | Template |
|---|---|
| macOS | `config/launchd/com.example.throughline.refine-daemon.plist` |
| Linux | `config/systemd/throughline-refine-daemon.service` |

Both run the daemon under `KeepAlive` / `Restart=on-failure` so a crash
does not require manual restart. The daemon is deliberately
non-retrying on LLM failures — errors are appended to the Issue Log at
`00_Buffer/00.02_Data_Ingest/00.02.07_Daemon_Issues.md` for human
triage rather than burned through retries.

### Optional: conversation sync

If OpenWebUI runs on a separate host and the daemon runs on another,
use the sync template:

- `config/launchd/com.example.throughline.sync.plist` — rsync pull on a
  5-minute interval. Placeholders `{{SYNC_SOURCE}}` and
  `{{THROUGHLINE_RAW_ROOT}}` define the hop.
- On Linux, roll the same rsync invocation into a systemd timer; no
  bundled template ships for this variant.

---

## Step 5 — OpenWebUI Filter

1. Open the OpenWebUI web UI as an admin user.
2. Go to **Admin Panel → Functions → Create new Function**.
3. Paste the entire contents of `filter/openwebui_filter.py`.
4. Name it `throughline_filter` (or anything — `class Filter` is what
   OpenWebUI binds to).
5. Click **Save**. OpenWebUI parses the module and registers the Valves.
6. Open the new function's **Valves** pane and set at minimum:
   - `OPENROUTER_API_KEY`
   - `RAG_SERVER_URL` — default `http://localhost:8000` is fine for a
     same-host install.
7. Enable the function globally, or attach it to the models you want it
   to moderate.

Updating the Filter later can be done the same way (repaste + Save) or
scripted via the REST API — see `filter/README.md § 3`.

Minimum valve set to get a turn through end-to-end:

| Valve | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | Haiku RecallJudge call. |
| `RAG_SERVER_URL` | Backing RAG server from Step 3. |
| `DAEMON_REFINE_URL` | (Optional) daemon refine-status endpoint for the outlet badge. |

Full valve reference: `filter/README.md § 4`.

---

## Step 6 — Ingest an existing vault

If you already have refined cards on disk (e.g. migrated from another
system, or produced by a previous daemon run), seed Qdrant:

```bash
export VAULT_PATH=/absolute/path/to/vault
python scripts/ingest_qdrant.py
```

`ingest_qdrant.py` reads from `VAULT_PATH`, applies the
`INGEST_INCLUDE` glob pattern (default `[1-9]0_*`, i.e. Johnny-Decimal),
computes a stable point ID from the forward-slash-normalised path, and
upserts to `obsidian_notes`. Re-running is idempotent — changed cards
are re-upserted with the same ID.

Extra whitelisted directories outside the JD tree:

```bash
export INGEST_EXTRA_WHITELIST='00_Buffer/00.00_Overview'
python scripts/ingest_qdrant.py
```

This is the mechanism that lets master cards under `00_Buffer/` reach
the RAG index while keeping the rest of `00_Buffer/` out (see
`ARCHITECTURE.md § 6`).

---

## Step 7 — Smoke test

With all four services running, send a chat turn through OpenWebUI:

1. Open a new conversation against any model.
2. Type a question that overlaps existing cards (e.g. something you've
   refined before).
3. Expect to see:
   - A status line above the reply, e.g. `⚡ anchor pass: qdrant`
     or `auto recall: mode=general · conf=0.82 · 10 cards`.
   - A reply that cites or paraphrases your own notes.
   - A footer line with token counts and USD cost.
   - (If the daemon is running) a refine-status badge:
     `🛰️ daemon · 🟡 PENDING` after new conversations, later flipping
     to `🟢 DONE` once refinement completes.

Manual verification:

```bash
curl -s http://localhost:8000/health
curl -s "http://localhost:8000/refine_status?conversation_id=<uuid>"
```

The second endpoint is what the Filter outlet polls. A response of
`{"state":"DONE", ...}` means the daemon has finished refining that
conversation; `{"state":"PENDING", ...}` means the daemon has queued
but not yet finished; `{"state":"COLD", ...}` means the daemon is not
reachable.

---

## Troubleshooting

For Filter-specific failure modes, see
`filter/README.md § 6 — Troubleshooting`. Highlights:

- **`no_api_key`** — set `OPENROUTER_API_KEY` valve (or `OPENAI_API_KEY`
  environment variable on the OpenWebUI host).
- **`⚠️ HAIKU_DOWN × 3+`** — three consecutive judge failures. Check
  OpenRouter status and quota. The Filter falls back to cosine
  thresholding automatically; you lose brainstorm detection and query
  reformulation until the judge recovers.
- **Empty RAG results** — verify `RAG_SERVER_URL` from inside the
  OpenWebUI container, not from the host. Docker networking can put
  `localhost` on the wrong side.

For the other components:

- **RAG server won't start** — model download failure. Check HuggingFace
  connectivity; set `HF_HOME` if you need a custom cache location. On
  CPU-only hosts, set `RAG_DEVICE=cpu` to skip the MPS/CUDA probe.
- **Daemon Issue Log grows** — the daemon never silently retries on LLM
  failures. Open
  `00_Buffer/00.02_Data_Ingest/00.02.07_Daemon_Issues.md`, triage the
  `status: pending` entries, fix the upstream cause (prompt issue / bad
  raw input / rate limit), then delete the entry or mark it `acked`.
- **Qdrant double-counted points** — if `collection.points_count` is
  roughly 2× your card count, a path-normalisation regression has
  snuck in. Check that every path passed to `make_point_id()` goes
  through `_norm_path()` first. See `ARCHITECTURE.md § 11`.
- **OpenWebUI can't find the Filter file after edit** — OpenWebUI
  Functions do not hot-reload from disk. Edit either in the Admin UI or
  push via the REST API (`POST /api/v1/functions/id/<id>/update`).

---

## Platform notes

- **macOS** — first-class. All service templates ship as `launchd`
  plists. The RAG server auto-detects MPS. Obsidian Sync (if used)
  needs the Obsidian app running for file changes to propagate; an
  unattended Mac must have Obsidian open.
- **Linux** — supported. systemd service templates cover the RAG
  server and the refine daemon; roll your own unit for any sync
  pipeline you need. CUDA is picked up automatically; CPU-only works
  but reranker batch size (default 100) may need tuning for small
  hosts.
- **Windows** — supported for *development* and *ingest* only.
  `scripts/ingest_qdrant.py` runs cleanly on Windows (the forward-slash
  normalisation makes this safe). The daemon and RAG server are
  expected to run on macOS or Linux in production; Windows runtime
  support is not tested and not on the roadmap.
