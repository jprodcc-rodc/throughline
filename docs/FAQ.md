# FAQ

Questions that come up repeatedly on HN / Reddit / X / email.
If your question isn't here,
[open a Discussion](https://github.com/jprodcc-rodc/throughline/discussions).

## Table of contents

- [How is this different from ChatGPT's built-in memory?](#how-is-this-different-from-chatgpts-built-in-memory)
- [How is this different from Claude Projects?](#how-is-this-different-from-claude-projects)
- [How is this different from `mem0`?](#how-is-this-different-from-mem0)
- [Can I use this alongside `mem0` / Letta / SuperMemory?](#can-i-use-this-alongside-mem0--letta--supermemory)
- [Do I need Obsidian?](#do-i-need-obsidian)
- [Do I need OpenWebUI?](#do-i-need-openwebui)
- [Does this work with Claude.ai / ChatGPT.com / Gemini directly?](#does-this-work-with-claudeai--chatgptcom--gemini-directly)
- [How much does it cost to run?](#how-much-does-it-cost-to-run)
- [Does it work fully offline?](#does-it-work-fully-offline)
- [What happens to my data?](#what-happens-to-my-data)
- [Can I self-host all of it?](#can-i-self-host-all-of-it)
- [Why 16 LLM providers? Feature creep?](#why-16-llm-providers-feature-creep)
- [Does it support Chinese / Japanese / other languages?](#does-it-support-chinese--japanese--other-languages)
- [What's the roadmap?](#whats-the-roadmap)
- [I hit a bug. What do you want from me?](#i-hit-a-bug-what-do-you-want-from-me)

---

## How is this different from ChatGPT's built-in memory?

ChatGPT memory stores short facts ("user prefers metric units",
"user is vegetarian") in OpenAI's database. Three differences:

- **You can't read them in a text editor.** throughline writes
  plain Markdown files in your vault. You can grep, back up,
  version-control, or open them in any editor — ChatGPT memory is
  a SaaS row you can't see.
- **It captures thinking, not just labels.** ChatGPT memory
  remembers WHAT you like; a throughline card captures the
  six-section reasoning that led you to a conclusion (pain point,
  mechanism, execution, pitfalls, insights, summary).
- **It survives tool changes.** When you move off ChatGPT in two
  years, the memory disappears. A vault of refined Markdown cards
  keeps working with whatever comes next.

## How is this different from Claude Projects?

Claude Projects is a system prompt + file-attachment scope.
Throughline produces the same kind of content Projects consume —
refined cards you'd want the LLM to see — but:

- **The refining is automatic.** You don't paste cards into a
  Project; they're generated from chat conversations as you have
  them.
- **It works across LLMs.** A Claude Project only runs inside
  Claude.ai. Throughline's cards feed OpenWebUI, which can talk
  to any of 16 LLM providers; the cards themselves are
  model-agnostic.
- **Cards are Markdown in your filesystem**, not a container-
  attached asset you can't export cleanly.

## How is this different from `mem0`?

[mem0](https://github.com/mem0ai/mem0) is a Python library that
stores vectors in a service-managed store. Great for application
developers who want a drop-in memory API.

Throughline is different in **audience**: throughline targets a
vault-keeping individual, not an app builder. The Markdown-first
design is the feature, not a workaround. If your end goal is "give
my app a memory backend", mem0 is a better fit; if your end goal is
"never re-explain myself to a new chat + have a searchable journal
I actually read", throughline is.

See the [comparison table in the README](../README.md#how-is-this-different-from-mem0--letta--supermemory--openwebui-built-in-memory).

## Can I use this alongside `mem0` / Letta / SuperMemory?

Yes, but the value-add diminishes. Throughline's cards already cover
the recall dimension those tools specialise in. Running both doubles
storage + cost + LLM token spend without obvious upside.

The one stackable case: use Letta for an agent's *stateful
execution memory* (its to-do list, its current call graph) and
throughline for the user's *learned knowledge store*. Different
slots.

## Do I need Obsidian?

**No.** The refine daemon writes plain Markdown files with YAML
frontmatter — same format VS Code, nvim, iA Writer, Typora,
Sublime, or Notepad can read. Obsidian is recommended because
its graph/linking UI matches the six-section card shape, but
it's not required. Nothing downstream depends on Obsidian's
`.obsidian/` folder, canvas files, or plugin format.

## Do I need OpenWebUI?

The full flywheel assumes OpenWebUI as the chat frontend (the
Filter is an OpenWebUI Function). But two of the three missions
are lighter:

- **RAG-only**: skip the Filter; you just want cards in Qdrant and
  a FastAPI endpoint (`/v1/rag`) your own code can hit. No OpenWebUI
  needed.
- **Notes-only**: skip the vector store and the Filter. You just
  want the refine daemon writing Markdown from some conversation
  source (e.g. a chat export you drop into the raw directory).

See the wizard's step 2 (Mission) for the choice.

## Does this work with Claude.ai / ChatGPT.com / Gemini directly?

Not live — those web apps don't expose a Filter-style hook point.
But the **import adapters** let you bulk-convert an exported
history: `python -m throughline_cli import claude <zip>`,
`import chatgpt`, or `import gemini` turn any official data
export into raw Markdown the daemon refines the same way.

Once imported, future conversations on those platforms go through
**an OpenWebUI frontend** that proxies Claude / OpenAI / Gemini /
etc. APIs. Same keys, different UI.

## How much does it cost to run?

Two cost axes:

**Upfront (one time):**
- ~4.6 GB download for `bge-m3` embedder + `bge-reranker-v2-m3`
  (if using the default local setup). Cloud embedders skip this.
- Docker install for Qdrant (~150 MB image).

**Recurring:**
- LLM API calls for refine. Rough numbers:
  - Skim tier: ~$0.005/conversation (Haiku-class, single call).
  - Normal tier: ~$0.015-0.05/conversation (Sonnet-class, slicer +
    refiner + router).
  - Deep tier: ~$0.20/conversation (Opus-class + critique pass).
- Qdrant + bge-m3 + daemon + rag_server all run locally after
  the initial model download. Zero recurring infra cost.

A heavy user (20 conversations/day on Normal tier) spends ~$10-30/
month. The wizard's step 15 sets a daily USD cap the daemon
enforces (pauses queue when reached, resets at local midnight).

Use `python -m throughline_cli cost` for the live dashboard.

## Does it work fully offline?

Almost. The only mandatory cloud call is the LLM refine (and even
that can be a local Ollama via the `ollama` provider preset).
Every other component — embedder, reranker, vector store, vault
writer — runs locally by default.

For fully-offline mode: pick `Ollama` at wizard step 4, local
`bge-m3` at step 7, local `qdrant` at step 3. No internet needed
beyond the first model downloads.

## What happens to my data?

- **Your conversations** get written to a raw directory the daemon
  watches. Sent to the LLM provider you chose (one of 16) when
  refine fires. Never sent anywhere else.
- **Refined cards** land in your vault as plain Markdown.
  `de_individualization` rules in the refiner prompt replace
  private IPs, home paths, and personal emails with placeholders
  (`192.0.2.10`, `/path/to/...`, `user@example.com`) before the
  card is written.
- **The `import_source` tag** in every card's frontmatter lets you
  bulk-purge any batch. `import sample-2026-04-25` tagged cards
  can be removed with one `rg -l + rm` or `throughline_cli uninstall`
  on a wider sweep.
- **No telemetry.** throughline makes zero outbound requests to
  any throughline-operated server. There isn't a throughline-
  operated server.

See [`SECURITY.md`](../SECURITY.md) for the disclosure channel +
[`THREAT_MODEL.md`](THREAT_MODEL.md) for the full attack-surface
enumeration.

## Can I self-host all of it?

Yes:

- **Qdrant** — Docker container.
- **RAG server** — local FastAPI process.
- **Daemon** — local systemd / launchd service.
- **Filter** — pasted into your own OpenWebUI install.
- **LLM** — Ollama on localhost, or any OpenAI-compatible server
  reachable on your LAN (LM Studio, vLLM, text-generation-webui,
  TEI).

No throughline-owned infrastructure in the loop.

## Why 16 LLM providers? Feature creep?

Because locking to one (historically OpenRouter) made the tool
unusable for users who already pay for Anthropic / OpenAI / a
Chinese-market provider, or who want to run entirely on Ollama. The
abstraction is 200 lines of code; the value is "works with whatever
you already pay for". The wizard auto-detects the env var you have
set — most users only think about this once.

## Does it support Chinese / Japanese / other languages?

**Prompts ship in English only** (`prompts/en/`). The codebase was
originally Chinese-first and de-localised for the open-source
release; see [`docs/CHINESE_STRIP_LOG.md`](CHINESE_STRIP_LOG.md)
for what was stripped and what's re-introducible.

User-content handling is locale-neutral:
- Non-ASCII card titles, tags, and body text round-trip correctly.
- The taxonomy observer (U27) normalises AI/代理 and AI/Agent as
  string-distinct tags; v0.3 adds semantic clustering.
- Frontmatter dates use ISO format, locale-independent.

To contribute translated prompts, see
[`prompts/README.md` § Adding a new language](../prompts/README.md#adding-a-new-language).

## What's the roadmap?

- **v0.2.x** (now): bug fixes against v0.2.0.
- **v0.3**: native implementations of the 4 aliased vector stores
  (LanceDB / DuckDB-VSS / SQLite-vec / pgvector), native rerankers
  (Voyage / Jina), U27.5/.6/.7 taxonomy growth extensions, PyPI
  publish, Docker compose (done in v0.2.x), hero screencast.
- **v1.0**: stability commitment on config.toml / CLI / ABI; shipped
  when someone OTHER than the author has been running it in
  production for meaningful hours.

Full list: [`ROADMAP.md`](../ROADMAP.md).

## I hit a bug. What do you want from me?

[Open a bug report](https://github.com/jprodcc-rodc/throughline/issues/new?template=bug_report.yml).
The template asks for:

- `python -m throughline_cli doctor` output (redact absolute paths).
- OS + Python version.
- Which component (wizard / daemon / rag_server / Filter / …).
- Which LLM provider + model you picked.
- Logs from `~/throughline_runtime/logs/refine_daemon.log` or
  rag_server stderr — redact paths and API keys before pasting.

That's usually enough for me to tell you what to try next.
