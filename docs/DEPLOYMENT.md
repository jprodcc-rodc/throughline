# Deployment

> End-to-end install guide for a fresh host. Assumes familiarity with
> shell, Python virtual environments, and Docker. For the reasoning
> behind each component see `ARCHITECTURE.md`; for badge semantics once
> the system is running see `FILTER_BADGE_REFERENCE.md`.
>
> **Two paths are documented below.** The **Quick install (via wizard)**
> section is the v0.2.0+ preferred entry — `python install.py` collects
> every decision and writes `~/.throughline/config.toml` for you. The
> **Manual install** sections after it show the same steps by hand for
> scripted / headless / air-gapped setups where you'd rather not run the
> TUI.

---

## Contents

- [Prerequisites](#prerequisites)
- [Docker compose (try it in 5 minutes)](#docker-compose-try-it-in-5-minutes)
- [Quick install (via wizard)](#quick-install-via-wizard)
- [Step 1 — Clone and configure](#step-1--clone-and-configure)
- [Step 2 — Qdrant](#step-2--qdrant)
- [Step 3 — RAG server](#step-3--rag-server)
- [Step 4 — Refine daemon](#step-4--refine-daemon)
- [Step 5 — OpenWebUI Filter](#step-5--openwebui-filter)
- [Step 6 — Ingest an existing vault](#step-6--ingest-an-existing-vault)
- [Step 7 — Smoke test](#step-7--smoke-test)
- [Pluggable backends (EMBEDDER / RERANKER / VECTOR_STORE)](#pluggable-backends)
- [Diagnostics (`throughline_cli doctor`)](#diagnostics-throughline_cli-doctor)
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
| Any LLM provider | one account's worth | Pick from 16 OpenAI-compatible presets (Anthropic / OpenAI / DeepSeek / SiliconFlow / Moonshot / OpenRouter / Ollama / …) via wizard step 4. ~$5 credit on a cloud provider covers the first weeks of refining; Ollama is free. See [§Pluggable backends](#pluggable-backends). |
| Markdown vault | any layout | Johnny-Decimal (`10_`, `20_`, …) is the default; any prefix pattern works via `INGEST_INCLUDE`. |

> **Obsidian is optional.** The daemon writes plain Markdown files.
> Any editor that reads Markdown (VS Code, nvim, iA Writer, TextEdit,
> Sublime, Typora) works. Obsidian is recommended because its graph /
> linking UI matches the knowledge-card style, but every file in the
> vault is readable in Notepad.

Disk footprint, reference system:

- Qdrant storage: ~1 KB per card × 1024-dim vector ≈ <100 MB for a few thousand cards.
- bge-m3 model weights: ~2.3 GB (downloaded on first RAG server start).
- bge-reranker-v2-m3 weights: ~2.3 GB.
- Raw conversation export: roughly equal to your chat volume.

GPU is optional. The RAG server picks MPS (Apple Silicon) > CUDA > CPU
automatically. CPU-only works for small collections; large reranker
batches can be slow.

### Pre-flight: download the embedding models before first RAG-server start

The RAG server downloads bge-m3 (~2.3 GB) and bge-reranker-v2-m3
(~2.3 GB) on its first start. On a fast connection this is 2-5
minutes; on a slow or throttled link it can take 30+ minutes during
which the server appears to hang at startup. Pre-fetch the weights
once so Step 3 (RAG server launch) is predictable:

```bash
pip install "huggingface_hub[cli]"
huggingface-cli download BAAI/bge-m3
huggingface-cli download BAAI/bge-reranker-v2-m3
# Weights cached under ~/.cache/huggingface/; rag_server finds them
# automatically on start.
```

Skippable if you trust your bandwidth and don't mind a long first-run
wait.

---

## Docker compose (try it in 5 minutes)

For evaluating throughline without committing to a full local
install, the bundled `docker-compose.yml` spins up Qdrant +
rag_server + daemon on one host. Minimum viable path:

```bash
git clone https://github.com/jprodcc-rodc/throughline.git
cd throughline

cp .env.example.compose .env
# Edit .env: set ONE of the API key variables (OPENROUTER_API_KEY,
# ANTHROPIC_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY, SILICONFLOW_API_KEY,
# MOONSHOT_API_KEY, …). The daemon auto-detects which one is set.

docker compose up -d

# First boot seeds the vault with 10 synthetic conversations so
# you can watch refines happen in real time:
docker compose run --rm daemon \
    python -m throughline_cli import sample
docker compose logs -f daemon
```

Defaults tuned for fast eval: `EMBEDDER=openai` (no local torch
download), `RERANKER=skip` (no cross-encoder). To enable the full
local-privacy path (`bge-m3` + `bge-reranker-v2-m3`):

```bash
docker compose build --build-arg INSTALL_LOCAL=1
# Then set EMBEDDER=bge-m3, RERANKER=bge-reranker-v2-m3 in .env
# and `docker compose up -d --force-recreate`.
```

Volumes are named by default (persist across `docker compose
down`); bind them to host paths for direct Obsidian editing by
editing `volumes.vault` in `docker-compose.yml`. See the comments
in that file for the exact bind syntax.

OpenWebUI is **not** bundled — users typically already have one
running, and the Filter's paste-into-Admin UI flow doesn't benefit
from containerisation. Point your existing OpenWebUI at
`http://<host>:8000` (the exposed rag_server port) and follow the
Filter install in [§ Step 5](#step-5--openwebui-filter).

---

## Quick install (via wizard)

For most users, the fastest path from zero to a working install is
`install.py --express` — one command, ~3 seconds, auto-detects
whichever LLM provider env var you have set:

```bash
git clone https://github.com/jprodcc-rodc/throughline
cd throughline

python3 -m venv .venv
source .venv/bin/activate                      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY=sk-...                # or OPENAI / OPENROUTER / etc.
python install.py --express                    # ~3s, sane defaults
```

`--express` picks `bge-m3` local embedder + local reranker + Qdrant
+ hybrid privacy + $20 daily cap, prints per-conversation cost,
writes `~/.throughline/config.toml`, and exits. Append `--dry-run`
to preview without writing.

### Full 16-step wizard (when you want full control)

If you want to override defaults — different vector DB, different
privacy tier, import an existing OpenWebUI / ChatGPT / Claude
history, or tune any of the 16 wizard decisions — run the full
wizard instead:

```bash
python install.py                              # 16 steps, all-Enter defaults work
python install.py --reconfigure                # later: change a few without restarting
python install.py --dry-run                    # preview the full wizard, no save
```

The full wizard:

1. Asks 16 short questions with sensible Enter-defaults. Pressing
   Enter on every prompt lands a working Full-mission config.
2. Scans your chat export (Claude / ChatGPT / Gemini) if you point
   it at one — no export? pick `5. none` at step 9 and use the
   **bundled sample export** at any later point:
   `python -m throughline_cli import sample` (10 synthetic
   conversations, ~$0.03 Normal-tier refine).
3. Runs a live preview call against your LLM provider at step 13
   (~$0.01, explicit consent required).
4. Writes `~/.throughline/config.toml` and prints a **Next 3 steps**
   panel tailored to your mission telling you the exact commands
   to launch the rag_server, the daemon, and (for Full mission) to
   install the Filter.
5. After anything changes, run `python -m throughline_cli doctor`
   to confirm each piece is reachable.

**If you prefer the manual route** — scripted ops, Docker-compose
contributor, air-gapped deploy, or you just want to see what each
env var does — continue with **Step 1** below. The wizard and the
manual path produce the same on-disk state.

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
| `<PROVIDER>_API_KEY` | Your LLM API key. The variable name depends on which provider you pick at wizard step 4: `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `SILICONFLOW_API_KEY`, `MOONSHOT_API_KEY`, `DASHSCOPE_API_KEY`, `ZHIPU_API_KEY`, `ARK_API_KEY` (Doubao), `TOGETHER_API_KEY`, `FIREWORKS_API_KEY`, `GROQ_API_KEY`, `XAI_API_KEY`. See [§Pluggable backends](#pluggable-backends). |
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
   - Your LLM provider API key (valve name matches the env var of the
     provider you picked at wizard step 4 — `OPENROUTER_API_KEY`,
     `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `SILICONFLOW_API_KEY`,
     etc.).
   - `RAG_SERVER_URL` — default `http://localhost:8000` is fine for a
     same-host install.
7. Enable the function globally, or attach it to the models you want it
   to moderate.

Updating the Filter later can be done the same way (repaste + Save) or
scripted via the REST API — see `filter/README.md § 3`.

Minimum valve set to get a turn through end-to-end:

| Valve | Purpose |
|---|---|
| `<PROVIDER>_API_KEY` | LLM provider key — matches whichever provider the wizard picked. Haiku RecallJudge + refiner both go through this key. |
| `RAG_SERVER_URL` | Backing RAG server from Step 3. |
| `REFINE_STATUS_URL` | (Optional) daemon refine-status endpoint for the outlet badge. Paired with `REFINE_STATUS_ENABLED` and `REFINE_STATUS_TIMEOUT`. |

Full valve reference: `filter/README.md § 4`.

---

## Step 6 — Ingest an existing vault

If you already have refined cards on disk (e.g. migrated from another
system, or produced by a previous daemon run), seed Qdrant:

```bash
export VAULT_PATH=/absolute/path/to/vault
python scripts/ingest_qdrant.py
```

`ingest_qdrant.py` reads from `VAULT_PATH`, applies the `INGEST_INCLUDE`
pattern list (default `["re:^[1-9]0_"]` — a single regex matching any
Johnny-Decimal top-level folder; override with a JSON list of exact
folder names and/or `re:` prefixes), computes a stable point ID from the
forward-slash-normalised path, and upserts to `obsidian_notes`. Re-running
is idempotent — changed cards are re-upserted with the same ID.

Extra whitelisted directories outside the JD tree (note: the env var takes
a **JSON list**, not a bare string — a bare path will fail to parse):

```bash
export INGEST_EXTRA_WHITELIST='["00_Buffer/00.00_Overview"]'
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
curl -s "http://localhost:8000/refine_status?conv_id=<uuid>"
```

The second endpoint is what the Filter outlet polls. A response of
`{"state":"DONE", ...}` means the daemon has finished refining that
conversation; `{"state":"PENDING", ...}` means the daemon has queued
but not yet finished; `{"state":"COLD", ...}` means the daemon is not
reachable.

---

## Pluggable backends

v0.2.0 introduced swappable backends for three components. Each picks
a default that matches the v0.1 behaviour; each flips by setting a
single environment variable (or the matching field in the wizard).

| Component | Env var | Default | Alternates (today) | Coming in v0.3 |
|---|---|---|---|---|
| Embedder | `EMBEDDER` | `bge-m3` (local torch) | `openai` | `nomic`, `minilm` native |
| Reranker | `RERANKER` | `bge-reranker-v2-m3` (local) | `cohere`, `voyage`, `jina`, `skip` (all real impls) | `bge-reranker-v2-gemma` native |
| Vector store | `VECTOR_STORE` | `qdrant` | `chroma`, `lancedb`, `sqlite_vec`, `duckdb_vss` (embedded, zero-server), `pgvector` (Postgres) — all real impls | — |

The local-default backends carry a ~4.6 GB one-time download each
(see the pre-flight section above). The cloud alternates (`openai`,
`cohere`) need their own env vars: `OPENAI_API_KEY` + optional
`OPENAI_BASE_URL`, `COHERE_API_KEY` + optional `COHERE_BASE_URL`.

Flipping any of these invalidates the Qdrant collection's stored
vectors — a different embedder produces a different vector space.
Re-run `scripts/ingest_qdrant.py` after changing `EMBEDDER`; the
script reads the active embedder's `vector_size` and creates a fresh
collection with the matching schema.

Install only the optional packages you need:

```bash
pip install .[local]      # torch + transformers — needed for EMBEDDER=bge-m3
pip install .[openai]     # openai client — needed for EMBEDDER=openai and ingest
pip install .[chroma]     # chromadb — needed for VECTOR_STORE=chroma
pip install .[lancedb]    # lancedb + pyarrow — needed for VECTOR_STORE=lancedb
pip install .[sqlite-vec] # sqlite-vec — needed for VECTOR_STORE=sqlite_vec
pip install .[duckdb-vss] # duckdb (loads VSS extension) — needed for VECTOR_STORE=duckdb_vss
pip install .[pgvector]   # psycopg[binary] — needed for VECTOR_STORE=pgvector
pip install .[all]        # everything (full local-only path)
```

---

## Diagnostics (`throughline_cli doctor`)

v0.2.0 ships a one-shot health check that answers the "is my install
actually working?" question without you having to grep three log files:

```bash
python -m throughline_cli doctor
```

Output (truncated, happy-path):

```
  ✓ python_version           Python 3.12 (>= 3.11 required)
  ✓ required_imports         all 6 runtime packages importable
  ✓ optional_imports         present: torch, transformers, openai
  ✓ config_file              /home/you/.throughline/config.toml (1824 bytes)
  ✓ config_schema            12 keys, all recognized
  ✓ state_dir                /home/you/throughline_runtime/state
  ✓ llm_provider             OpenAI (direct) · OPENAI_API_KEY set
  ✓ qdrant                   http://localhost:6333 responding 200
  ✓ rag_server               http://localhost:8000 health 200
  ✓ daemon_state             state file updated 3 min ago
  ✓ embedder_model_cache     BAAI/bge-m3 cached at ~/.cache/huggingface/...
  ✓ taxonomy_observations    47 observation(s) in taxonomy_observations.jsonl
  ✓ taxonomy_pending         no growth candidates pending review

  All 13 checks passed.
```

Flags:

- `--quiet` — only print warnings + failures. Useful in cron / CI.
- `--json` — machine-readable output. Exit code 0 iff all green (or
  only warnings); 1 if any check failed.

Each failed check prints a **remediation line** showing the exact
command to fix it. Run doctor after every install / upgrade / env
change; it's the fastest way to tell "it broke" from "it's fine but
I'm staring at the wrong log".

---

## Troubleshooting

Before anything else: **run `python -m throughline_cli doctor`**
(above). It enumerates the common failure surfaces with remediation
hints and usually short-circuits the rest of this section.

For Filter-specific failure modes, see
`filter/README.md § 6 — Troubleshooting`. Highlights:

- **`no_api_key`** — set the LLM provider's API key valve (matches
  whichever provider the wizard picked at step 4 — `OPENROUTER_API_KEY`,
  `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `SILICONFLOW_API_KEY`, …).
- **`⚠️ HAIKU_DOWN × 3+`** — three consecutive judge failures. Check
  your LLM provider's status page and quota. The Filter falls back to
  cosine thresholding automatically; you lose brainstorm detection and
  query reformulation until the judge recovers.
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
- **Windows** — tier 1 for dev + wizard, tier 2 for runtime.
  `python install.py`, the import adapters, `throughline_cli doctor`,
  `scripts/ingest_qdrant.py`, and the test suite (`pytest fixtures/`)
  are all supported on Windows 10/11 — developed against PowerShell +
  bash (git-bash). The daemon and rag_server run on Windows too (the
  path-normalisation fixes for the m4 point_id invariant make this
  safe), but long-lived service-style deployment is better-trodden on
  macOS + Linux; no `nssm` / Scheduled-Task template ships today. For
  a Windows service wrapper, roll one locally and consider opening a
  PR — it would land as a `config/windows/` template alongside the
  macOS + Linux ones.
