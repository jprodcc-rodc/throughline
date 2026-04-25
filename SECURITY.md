# Security policy

For the deep threat-model breakdown — what the system defends against,
what it doesn't, where the sharp edges are — see
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md). This file is the
shorter "what data moves where, and how to report" reference; it
should be self-contained enough to read on its own before installing.

---

## Data flow

throughline runs entirely on your local machine. There is no
throughline-operated server. No data leaves your machine **except** to
the LLM / embedder / reranker endpoints **you yourself configure**.

What that means in practice:

- **Local-only path** (default with `EMBEDDER=bge-m3` + local
  reranker + Qdrant + Ollama LLM): conversation content stays on
  your machine entirely.
- **Remote embedder / reranker** (OpenAI / Cohere / Voyage / Jina):
  conversation content is sent to those providers for vectorisation
  and re-ranking. Read their privacy policies; we don't proxy.
- **LLM API calls** (OpenAI / Anthropic / DeepSeek / Gemini /
  OpenRouter / SiliconFlow / …): every refine sends the conversation
  slice as the prompt. This is true of any LLM tool, not specific to
  throughline. Whichever provider the wizard's step 4 resolves to
  sees every refine call.

The wizard's step 6 (Privacy) makes this choice explicit and
pre-selects backends per the tier you pick (`local_only` /
`hybrid` / `cloud_max`).

---

## What throughline reads from your system

- **Your import source** (read-only):
  - OpenWebUI sqlite database, OR
  - ChatGPT export `conversations.json`, OR
  - Claude export, OR
  - any folder of Markdown files you point it at.
- **Your designated Obsidian vault** — to read existing cards for
  RAG retrieval (and to detect dedup hashes before re-refining).
- **Environment variables** (typically populated by `.env`) — for
  API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, …).
- **`~/.throughline/config.toml`** — wizard-written user prefs.

## What throughline writes

- **New Markdown files to your vault** under designated folders
  (`00_Buffer/` for triage stubs; routed leaf paths for refined
  cards). All under `$THROUGHLINE_VAULT_ROOT`.
- **State files** under `state/` — `cost_stats.json`,
  `dedup_hashes.json`, `taxonomy_observations.jsonl`, etc.
- **Logs** under `logs/` — daemon refine activity, refine errors,
  doctor reports.
- **Vector embeddings** to your configured vector store (default:
  Qdrant on localhost:6333).

## What throughline does NOT do

- Does not phone home. There is no telemetry endpoint, no usage
  beacon, no auto-update check.
- Does not collect telemetry. Local logs and state files are local
  only; nothing is uploaded.
- Does not transmit data outside the LLM / embedder / reranker
  providers you configure in step 4 / step 5 / step 6 of the
  wizard.
- Does not modify files outside the project directory and your
  designated vault.
- Does not bundle a remote-update mechanism for prompts or code;
  upgrades are git-pull or pip-install, your call when.

---

## Threat model awareness

A few honest caveats most install guides skip:

- **Vault sensitivity = chat sensitivity.** Cards captured by
  throughline are exactly as sensitive as what you typed at your
  LLM. throughline doesn't reduce or amplify that sensitivity — it
  just makes it persistent and searchable. If you wouldn't paste it
  into ChatGPT, don't expect throughline to scrub it.
- **Your vault is now a long-term record of your thinking.** Treat
  it accordingly: full-disk encryption (FileVault / LUKS /
  BitLocker), regular backups, encrypted backup destination.
- **API keys are stored in plaintext in `.env`.** This is industry
  standard for development tools. If your threat model requires
  secret rotation or vault-encrypted secrets, throughline does not
  currently bundle that — pair it with `keyring`, 1Password CLI, or
  similar.
- **Refined cards inherit prompt-injection risk.** The refiner
  prompts include anti-pollution rules, claim-provenance tagging,
  and de-individualisation, but a sufficiently sophisticated
  injection in your conversation body could still steer card tone.
  See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for residual
  risk discussion and the H3 gate that catches the common cases.

The full asset inventory, threat actor list, defended-against
attacks, and explicit-out-of-scope cuts are documented in
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md). Read that before
running anything sensitive through the daemon.

---

## Reporting a vulnerability

**Don't open a public issue.** For anything that could affect users'
data safety — credential leakage, path traversal, prompt injection
that escalates beyond a single card, SSRF against Qdrant / the RAG
server, etc. — please report privately.

Preferred channel: **GitHub's private security advisory** at
<https://github.com/jprodcc-rodc/throughline/security/advisories/new>.
That opens a confidential thread only the maintainer can see.

Include:
- a minimal reproduction (fixture / command / network trace);
- the impact you've confirmed (data disclosure, RCE, DoS, …);
- whether the issue is already public anywhere.

## Scope

In scope:
- `daemon/` — the refine pipeline and its state files
- `rag_server/` — the FastAPI endpoints (`/v1/embeddings`,
  `/v1/rerank`, `/v1/rag`, `/refine_status`)
- `throughline_cli/` — install wizard + import adapters
- `packs/` — pack runtime loading arbitrary YAML + prompts
- anything that writes under `~/.throughline/` or the user's vault

Out of scope (report upstream instead):
- vulnerabilities in Qdrant, OpenWebUI, PyTorch, Transformers,
  FastAPI, or any other pinned dependency — those live with their
  respective projects.
- misuse of a user's own API keys that the user placed in their
  shell environment.

## Response

This is a solo-maintained alpha project. A first acknowledgement
should land within 5 working days. Fix timelines depend on severity
and my day job — critical issues (active exploitation, credential
exposure) get prioritised over cosmetic ones.

## Disclosure

Unless you ask otherwise, a published fix will credit the reporter
in the release notes.
