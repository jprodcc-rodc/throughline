# throughline

> Stop re-explaining yourself to every new chat.

[![test](https://github.com/jprodcc-rodc/throughline/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/jprodcc-rodc/throughline/actions/workflows/test.yml)
[![license](https://img.shields.io/github/license/jprodcc-rodc/throughline)](LICENSE)
[![python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)

<!--
  ╭─────────────────────────────────────────────────────────────╮
  │  HERO GIF GOES HERE — 10-15 seconds, three scenes:           │
  │    1) Plain ChatGPT forgetting context (frustrated face)     │
  │    2) Same ask in OpenWebUI + throughline (RAG injects card) │
  │    3) Cut to Obsidian, new card appears in graph             │
  │  Tools: Arcade.software / Screen Studio / ScreenToGif        │
  │  Drop the .gif in docs/assets/hero.gif and uncomment ↓        │
  ╰─────────────────────────────────────────────────────────────╯

![throughline hero demo](docs/assets/hero.gif)
-->

**v0.2.0 alpha** — running 24/7 in production. [Issues welcome](https://github.com/jprodcc-rodc/throughline/issues).
Docs: <https://jprodcc-rodc.github.io/throughline/>

---

## 👋 Who this is for

throughline is built for people whose context is complex enough that
re-explaining it costs real time, energy, or accuracy:

- People with multiple chronic conditions, polypharmacy, or layered
  medical history that no single chat ever fully captures.
- Long-term solo builders who keep losing the *reasoning* behind
  decisions they made months ago — not the decision itself, the why.
- Neurodivergent thinkers (ADHD, autism, AuDHD, …) whose working
  memory is already at capacity before the AI loop even starts.

If your use case is "occasional ChatGPT chats and I'd like them
remembered," ChatGPT's built-in memory is probably enough. throughline
is designed for the cases where built-in memory is **not** enough,
and where carrying that context across model + provider switches
matters more than zero-friction onboarding.

---

## ✨ What it does

**Before throughline:** Every new chat starts from zero. Your AI
forgets your medical history, your project, your preferences, the
conclusions you reached last month. You re-explain yourself every
time. Past conversations pile up somewhere you never look again.

**After throughline:** Every conversation gets refined into a durable
six-section Markdown card in your Obsidian vault. The next chat that
overlaps automatically pulls the card back in. Your AI already knows
you.

- **Cards are plain Markdown** — grep them, edit them, read them in
  five years no matter what tool you use then.
- **Taxonomy grows as you write** — 5 broad domains seed; system
  observes drift, proposes new ones for your approval.
- **Zero lock-in** — 16 OpenAI-compatible LLM providers, 5 swappable
  vector stores, 5 swappable rerankers.

---

## 💡 Why this exists

Most personal-knowledge tools either:
- **Record** but don't **synthesize** (raw transcripts pile up)
- **Synthesize** but lose **personal context** (generic answers about
  your own meds / projects / history)
- **Inject personal context** but leak it into the **public index**
  (your RAG now has your address in it)

throughline separates *mechanism* (system provides) from *content*
(you provide) at every layer, so you can safely share the engine
without sharing yourself.

---

## 🚀 Quickstart

### Docker compose (evaluate in 5 minutes, no Python install)

```bash
git clone https://github.com/jprodcc-rodc/throughline.git
cd throughline
cp .env.example.compose .env          # set ONE provider API key
docker compose up -d
docker compose run --rm daemon \
    python -m throughline_cli import sample   # 10 sample conversations
docker compose logs -f daemon
```

Default `EMBEDDER=openai` + `RERANKER=skip` keeps the image to
~400 MB. Add `--build-arg INSTALL_LOCAL=1` for the full local
(`bge-m3` + reranker) path. Full walkthrough in
[`docs/DEPLOYMENT.md` § Docker compose](docs/DEPLOYMENT.md#docker-compose-try-it-in-5-minutes).

### Install wizard (16 steps, all-Enter defaults — or 1-command express)

```bash
git clone https://github.com/jprodcc-rodc/throughline.git
cd throughline
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python install.py --express                          # ← already exported an API key? skip the 16-step interview
# OR
python install.py                                    # ← the full 16-step wizard
```

`--express` auto-detects whichever LLM provider env var you have
exported (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`,
…), fills sane defaults for everything else, prints the
per-conversation cost + daily cap, and writes config in ~3 seconds.
Run `--express --dry-run` to preview without committing.

What the full wizard covers, in order: Python check → mission (Full /
RAG-only / Notes-only) → vector DB → LLM provider → privacy level →
embedder + reranker → prompt family → import source + path → import
scan + cost estimate + **explicit privacy consent** → refine tier
(Skim / Normal / Deep) → card structure → live-LLM preview of your
first card with optional 5-dial tuning → taxonomy strategy → daily
USD cap → summary + run import.

After the wizard:

```bash
python rag_server/rag_server.py        # FastAPI on :8000 — embed + rerank + retrieval
python daemon/refine_daemon.py         # watchdog → refine → vault writer
```

Drop `filter/openwebui_filter.py` into OpenWebUI's Admin → Functions
panel; set its `RAG_SERVER_URL` valve to your local server. Now your
chats refine into cards, the cards get indexed, and the next chat
that overlaps gets the relevant cards injected.

### Re-run, health-check, sample

```bash
python install.py --reconfigure              # change a few settings
python -m throughline_cli doctor              # 13 checks with remediation
python -m throughline_cli import sample       # 10 synthetic conversations
python -m throughline_cli taxonomy review     # approve self-growth signals
python -m throughline_cli refine --dry-run <raw.md>   # preview refiner prompt, no LLM call
python -m throughline_cli stats               # screenshot-friendly summary
python -m throughline_cli cost                # LLM spend dashboard
python -m throughline_cli config validate     # lint config.toml for typos / enum drift
```

> **Obsidian is optional.** The daemon writes plain Markdown +
> frontmatter; any editor reads it. Obsidian is recommended for the
> graph + linking UI, but nothing downstream requires it.

### Manual install (no wizard)

If the wizard is too opinionated for your setup, the long-form guide
in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) walks the same flow by
hand: configure `.env`, start Qdrant via Docker, launch the RAG
server + daemon, install the Filter.

### Pluggable backends

| Component | Default | Alternates (today) | Coming in v0.3 |
|---|---|---|---|
| Embedder (`EMBEDDER`) | `bge-m3` (local) | `openai` (real impl); `jina` / `voyage` / `cohere` (alias → OpenAI-compatible endpoint with custom `EMBEDDING_API_BASE`) | `nomic` / `minilm` as distinct native impls |
| Reranker (`RERANKER`) | `bge-reranker-v2-m3` (local) | `cohere`, `voyage`, `jina`, `skip` (all real impls — separate HTTP clients, not aliases) | — |
| Vector store (`VECTOR_STORE`) | `qdrant` | `chroma`, `lancedb`, `sqlite_vec`, `duckdb_vss` (all embedded, zero-server), `pgvector` (Postgres + pgvector extension) — all real impls, all six closed against tracking issues | — |

### LLM providers

**16 preset routes** — wizard auto-detects whichever env var you've
exported. Direct (OpenAI / Anthropic / DeepSeek / xAI), hosted
open-weights (Together / Fireworks / Groq), 5 China-market routes,
OpenRouter proxy, Ollama / LM Studio for fully local, plus a
generic OpenAI-compatible escape hatch.

<details>
<summary><b>Click for the full provider grid + env vars</b></summary>

| Region | Providers |
|---|---|
| **Direct (anywhere)** | OpenAI · Anthropic · DeepSeek · xAI |
| **Hosted open-weights** | Together.ai · Fireworks.ai · Groq |
| **China (大陆 access)** | SiliconFlow (硅基流动) · Moonshot (Kimi) · DashScope (Alibaba Qwen) · Zhipu (智谱 GLM) · Doubao (字节豆包) |
| **Multi-vendor proxy** | OpenRouter (one key → 300+ models) |
| **Local / self-hosted** | Ollama · LM Studio |
| **Escape hatch** | Generic OpenAI-compatible endpoint (`THROUGHLINE_LLM_URL` + `THROUGHLINE_LLM_API_KEY`) |

Each provider reads its own env var (`OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `SILICONFLOW_API_KEY`, …). Existing users with
`OPENROUTER_API_KEY` already set keep working with zero config
change.

</details>

**Smoke-test the install** (after step 16): ask something in
OpenWebUI that overlaps your existing notes. You should see
`⚡ anchor pass` or `auto recall: mode=general · conf=0.82 · N cards`
above the reply.

<!-- TODO: drop screenshot of the OpenWebUI status badge here -->
<!-- ![OpenWebUI status badge](docs/assets/screenshot-recall-badge.png) -->


---

## 🃏 What a refined card looks like

You ask in chat six months ago: *"I lost 12kg on strict keto but my
weight's creeping back even at <30g carbs/day. What's going on?"*

Six months later you hit it again. Without throughline, the AI starts
from scratch. With throughline, the daemon already refined that
conversation into a card — `Keto rebound after 6 months — three
mechanisms, not willpower` — and the next chat pulls it back in.

<details>
<summary><b>Click to see the full card</b> (Markdown, ~50 lines, lives in your Obsidian vault)</summary>

```markdown
---
title: "Keto weight rebound after 6 months — three mechanisms, not willpower"
date: 2026-04-02 20:42:00
knowledge_identity: personal_persistent
tags: [Health/Biohack, y/Mechanism, z/Node]
source_conversation_id: "sample-002-keto-rebound"
---

# Scene & Pain Point
After ~6 months of strict keto (<30g carbs/day) with 12kg lost, weight
is creeping back despite holding the same macro rules. Easy to read as
willpower failure; usually not.

# Core Knowledge & First Principles
Three compounding mechanisms, in order of likely magnitude:
1. Adaptive thermogenesis — BMR drops 10-15% during weight loss.
2. Calorie creep — fat-fueled meals are calorie-dense; satiety adapts.
3. Insulin-sensitivity recovery — small glucose loads stored more efficiently.

# Detailed Execution Plan
- Track 7 days of intake honestly vs TDEE minus 15% adaptation deficit.
- Re-introduce measured portions; eyeballing stops working at 4-6 months.
- If the gap is real, the intervention is calories, not carbs.

# Pitfalls & Boundaries
- "Still under 30g carbs" ≠ "still hypocaloric". Protocol-adherence
  doesn't equal caloric deficit.

# Insights & Mental Models
6-month rebound is a data story, not a discipline story. Recovering
biology doing exactly what it's designed to do.

# Length Summary
Keto rebound at month 6 = adaptive thermogenesis + portion drift +
insulin recovery. Fix is a measurement week, not more willpower.
```

</details>

This is the file you grep with `ripgrep`, embed for RAG, and re-read
in five years. The conversation it came from is one line in a daemon log.

---

## How is this different from `mem0` / `Letta` / `SuperMemory` / OpenWebUI built-in memory?

Short answer: **throughline produces durable, human-readable Markdown
that lives in your file system.** The others produce vectors that live
in their store. Different point on the privacy / portability axis,
and a different target user — not a "better than" claim.

| | throughline | mem0 | Letta | SuperMemory | OpenWebUI memory |
|---|---|---|---|---|---|
| **Local-only mode** | yes (default) | yes (with self-host config) | yes (open-source server) | no (cloud service) | yes (built into OpenWebUI) |
| **Source of truth** | Markdown files in your vault | own DB | own DB | cloud DB | sqlite next to OpenWebUI |
| **Taxonomy mechanism** | LLM proposals + manual approval into 9-domain hierarchy | similarity-based recall (no taxonomy) | similarity-based recall | similarity-based recall | flat note list |
| **If you migrate away** | vault is plain Markdown, grep-able with `rg` | DB export to JSON | DB export | depends on cloud export | sqlite dump |
| **Designed for** | individuals with complex personal context | app developers integrating memory APIs | agent / multi-step builders | consumers wanting smart memory | casual OpenWebUI users |

throughline is heavier to install (it's a daemon + RAG server + Filter,
not a SaaS subscription or a `pip install + one line`) — and that's a
real cost. The trade-off you're paying it for: cards live in plain
Markdown you can grep, edit, or read in five years independent of any
tool decision you make today.

---

## 🏗️ Architecture

**Two independent pipelines, one shared substrate.** They meet only
on append-only storage (Markdown vault + vector store).

### Pipeline 1 — per-turn, in-band (every chat message)

```text
   ┌──────────────┐    query    ┌──────────────┐   vec    ┌──────────┐
   │  OpenWebUI   │ ───────────► │  RAG server  │ ───────► │  Vector  │
   │   Filter     │              │ embed+rerank │ ◄─────── │  store   │
   │  (auto-      │ ◄─────────── │              │   cards  └──────────┘
   │   recall)    │   context    └──────────────┘
   └──────┬───────┘
          │
          │ injected system prompt
          ▼
   ┌──────────────┐  reply +
   │     LLM      │  status     ┌──────────────┐
   │              │ ──────────► │   You see    │
   └──────────────┘  badge      └──────────────┘
```

Reads from the vector store. **Never writes to the vault.**

### Pipeline 2 — per-conversation, out-of-band (after each chat)

```text
                                        ┌────────────────────┐
                                        │  Markdown vault    │
                                ┌─────► │  (formal card)     │
                                │       └────────────────────┘
   ┌──────────┐    ┌──────────┐ │       ┌────────────────────┐
   │  raw     │ ── │  Refine  │ ├─────► │  Buffer stub       │
   │  .md     │ ──►│  daemon  │ │       │  (00_Buffer/, needs│
   │ (export) │    │          │ │       │   human triage)    │
   └──────────┘    └──────────┘ │       └────────────────────┘
                                │       ┌────────────────────┐
                                └─────► │  Vector store      │
                                        │  (embeddings)      │
                                        └────────────────────┘
```

Writes to the vault + buffer + vector store. **Never reads live chat.**

---

Filter bugs **cannot corrupt the vault**. Daemon bugs **cannot
pollute a live reply**. Full breakdown:
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 📁 Repository layout

```
throughline/
  filter/           OpenWebUI Filter Function (single-file paste into Admin → Functions)
  daemon/           Refine daemon (watches raw conversations, writes cards)
  rag_server/       FastAPI service: embedding, reranking, RAG endpoint, refine-status
  throughline_cli/  Install wizard, import adapters, taxonomy CLI, doctor
  packs/            Pluggable domain packs (slicer/refiner/routing overrides)
  scripts/          One-off tooling: vault ingest, context sync, uninstall
  samples/          Bundled demo data + recording recipe
  prompts/en/       Verbatim mirror of the runtime prompt strings
  config/           .env.example, taxonomy template, service templates
  docs/             Architecture, deployment, design decisions, badge reference
```

Each top-level directory has its own `README.md` for local detail.
Regression tests: see [`docs/TESTING.md`](docs/TESTING.md).

---

## 🔗 Links

- [Docs site](https://jprodcc-rodc.github.io/throughline/) — full navigable documentation
- [Architecture](docs/ARCHITECTURE.md) — how the pieces fit
- [Deployment](docs/DEPLOYMENT.md) — end-to-end install
- [Design decisions](docs/DESIGN_DECISIONS.md) — why each call was made
- [Roadmap](ROADMAP.md) — what's shipping next
- [Changelog](CHANGELOG.md) — version history

---

## 🤝 Contributing

PRs welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md). Good first
issues filter:
<https://github.com/jprodcc-rodc/throughline/labels/good%20first%20issue>.

---

## 📜 License

[MIT](LICENSE) — do what you want, no warranty.

---

## 🙏 Acknowledgments

Built on:
- [OpenWebUI](https://github.com/open-webui/open-webui) — the chat frontend
- [Qdrant](https://github.com/qdrant/qdrant) — default vector store (others swappable)
- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) + [bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) — default local embeddings + reranking
- The LLM providers listed above — bring whichever one you already pay for
