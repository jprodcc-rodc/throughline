# Roadmap

What's coming, what's speculative, what's deliberately not.

This file is the public outline. The day-to-day work tracker lives
in [`fixtures/phase6/SESSION_STATE.md`](fixtures/phase6/SESSION_STATE.md);
release-by-release deltas land in [`CHANGELOG.md`](CHANGELOG.md).

---

## Now (`v0.2.x` — bug-fix + polish track)

The current `main` is `v0.2.0`. Maintenance fixes will ship as
`v0.2.1`, `v0.2.2`, … without a fresh feature scope. Anything in
`v0.2.x`:

- bugs reported against the v0.2.0 release
- doc fixes / typos / install hiccups
- new tests pinning behaviour the suite missed

Triage label: [`v0.2.x`](https://github.com/jprodcc-rodc/throughline/labels/v0.2.x).

---

## Next (`v0.3` — driving the abstractions to ground)

v0.2.0 shipped clean abstractions for embedder, reranker, and vector
store, plus alias routing for half a dozen unimplemented backends. v0.3
ships the missing concrete drivers AND the next layer of taxonomy
self-healing.

### v0.3 will deliver

- **Vector-store backends.** Real implementations of the four backends
  v0.2.0 routes to Qdrant via alias:
  - `lancedb` — file-backed, zero-server, smallest install.
  - `duckdb_vss` — for users who already use DuckDB for analytics.
  - `sqlite_vec` — fully embedded, no separate process.
  - `pgvector` — for users on a Postgres ops stack.
- **Reranker backends.** Native `voyage` and `jina` clients (currently
  alias to Cohere); evaluate `bge-reranker-v2-gemma` as a separate
  registry entry rather than aliasing to `bge-reranker-v2-m3`.
- **U27.5** — Filter outlet `🌱 N taxonomy candidates` hint, surfaced
  weekly via OpenWebUI's `__event_emitter__`. Closes the manual-CLI gap
  that lets growth signals pile up unread.
- **U27.6** — `python -m throughline_cli taxonomy retag --since DATE
  --domain X` for batch re-refining historical cards under a newly-added
  taxonomy leaf. Cost-bearing operation; gated behind the daily budget
  cap (U3) and an explicit `--confirm-cost`.
- **PyPI release.** `pip install throughline` instead of `git clone +
  venv + pip install -r requirements.txt`. Console-script entry
  points (`throughline-install`, `throughline-import`,
  `throughline-taxonomy`).
- **Docker compose for "try it out".** One-command spin-up of OpenWebUI
  + Qdrant + the daemon + an empty vault, with a sample import.
- **5-minute screencast / GIF in the README.** Removes the "what
  does it actually look like" friction.

### v0.3 may deliver (depends on user signal)

- **U27.7** — Deprecation of zero-usage taxonomy leaves with a merge
  proposal flow. Risk: users get attached to folders they never write
  to; the threshold + surfacing UX needs care.
- **MCP server interface** — expose retrieval over MCP so other LLM
  apps can pull from the same vault.
- **Cross-language taxonomy clustering** — bge-m3 embedding similarity
  to cluster `AI/Agent` ≡ `AI/代理` for multilingual users.

---

## Later (`v1.0` — the stability commitment)

Reaching 1.0 means a public commitment NOT to break:

- the `~/.throughline/config.toml` schema
- the wizard step-N CLI flag (`python install.py --step N`)
- the daemon → vault frontmatter shape
- the Qdrant payload field set
- the embedder / reranker / vector-store factory ABCs
- the `BaseEmbedder.embed() / .vector_size / .ensure_loaded()` contract

Things that will get a deprecation cycle (warn for one minor, remove
in the next) before any 1.x release:

- env var renames
- prompt-file location moves
- pack runtime hooks

`v1.0` ships when:

- the four named v0.3 backends have been used in anger by someone other
  than the author (production hours, not just CI),
- `v0.2.x → v0.3 → v1.0` migration is documented end-to-end with no
  manual fixups,
- the test suite covers all five user paths (Full / RAG-only /
  Notes-only × cold-start / warm-import).

---

## Explicitly out of scope

These have come up; they're not on any roadmap:

- **Hosted SaaS.** throughline is local-first. No cloud-hosted variant
  is planned.
- **Mobile app.** The reading surface is OpenWebUI / Obsidian; both
  have their own mobile stories.
- **Replacing OpenWebUI.** throughline is a Filter + daemon + RAG
  server that OpenWebUI hosts; the chat UI itself is upstream.
- **Replacing Obsidian.** Cards land as plain Markdown with YAML
  frontmatter. Obsidian is recommended but not required (see U5).
- **Built-in LLM provider proxy.** The wizard collects an
  OpenRouter / OpenAI / Anthropic / etc. key and uses the provider
  directly. We don't add a proxy hop.

---

## How to influence this roadmap

- **A bug.** [Open an issue](https://github.com/jprodcc-rodc/throughline/issues/new?template=bug_report.md).
- **A feature.** [Open a feature request](https://github.com/jprodcc-rodc/throughline/issues/new?template=feature_request.md).
  Include the **why now** field; it's the strongest signal for
  prioritisation.
- **A discussion.** [Start a Discussion](https://github.com/jprodcc-rodc/throughline/discussions)
  rather than an issue for design questions or "is X the right
  approach?" threads.
- **A PR.** Look for the
  [`good first issue`](https://github.com/jprodcc-rodc/throughline/labels/good%20first%20issue)
  label. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first.
