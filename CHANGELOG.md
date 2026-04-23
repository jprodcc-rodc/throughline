# Changelog

All notable changes land here. Dates are UTC. For the full commit
list behind any entry, `git log vX..vY`.

This project follows [Semantic Versioning](https://semver.org/);
pre-1.0 minor bumps can include breaking config shape changes.

---

## [v0.2.0] — 2026-04-23

The v0.1.0 → v0.2.0 jump turns throughline from "clone-and-configure"
into a `python install.py` onboarding flow and widens the backend +
corpus envelope along the way.

### Added — wizard + import (the user-facing spine)
- **U14** · 16-step install wizard (rich-based TUI, mission-branched).
- **U2** · Three import adapters: Claude export, ChatGPT export,
  Gemini Takeout. Dogfooded against live exports; 7 real bugs caught.
- **U17** · First-card preview gate that calls the LLM live.
- **U23** · 5-dial constrained preview edit (tone / length / sections /
  register / keep-verbatim). Persists to `config.toml` so every
  daemon refine inherits it.
- **U4** · Privacy-consent dry-run panel at step 10 tail — explicit
  yes/no before data leaves the machine.
- **U24** · Mission branching: Full flywheel / RAG-only / Notes-only.
- **U26** · Wizard banner + between-step progress ticker.

### Added — refine pipeline
- **U15** · Tier matrix: skim / normal / deep (40× cost spread).
- **U16** · Card structure options: compact / standard / detailed.
- **U22** · Prompt family loader (Claude XML / generic Markdown).
- **U25** · RAG-optimized card format (title + entities + 3–8 atomic
  claims).
- **U1** · Cold-start 🌱/🌿 status line in the OpenWebUI Filter.
- **U3** · Daily USD budget cap enforced by the daemon
  (`THROUGHLINE_MAX_DAILY_USD` > `daily_budget_usd` in config.toml;
  zero = kill switch; day rollover resets naturally).

### Added — taxonomy (U13 + U27 MVP loop)
- **U13** · `scripts/derive_taxonomy.py` — one-shot LLM derivation for
  users with 100+ cards.
- **U27.1** · Skeletal 5-domain starter (`config/taxonomy.minimal.py`)
  for <100-card users.
- **U27.2** · All 8 refiner prompts emit `proposed_x_ideal` alongside
  the constrained `primary_x`.
- **U27.3** · `daemon/taxonomy_observer.py` appends every refine to
  `state/taxonomy_observations.jsonl`.
- **U27.4** · `python -m throughline_cli taxonomy [review | reject]`
  closes the growth cycle.

### Added — swappable backends
- **U12** · `rag_server/embedders.py` — `BgeM3Embedder` (local torch,
  lazy-load) + `OpenAIEmbedder` (stdlib urllib). Registry + alias map.
- **U20** · `rag_server/rerankers.py` — `BgeRerankerV2M3` +
  `CohereReranker` + `SkipReranker`. Cohere realigns rel-sorted
  results to input order.
- **U21** · `rag_server/vector_stores.py` — `QdrantStore` (stdlib
  urllib) + `ChromaStore` (optional dep, stub on missing install).
  Alias routing for lancedb / duckdb_vss / sqlite_vec / pgvector until
  v0.3+ ships the real drivers.
- `rag_server.py` wires through the three factories so
  `EMBEDDER` / `RERANKER` / `VECTOR_STORE` env vars actually flip
  the backend end-to-end.

### Added — packaging + ergonomics
- **U5** · "Obsidian is optional" callout in README + DEPLOYMENT.
- **U6** · `bge-m3` preflight section for the ~4.6 GB model download.
- **U8** · Uninstall scripts for mac/linux + windows.

### Fixed
- Daemon import surface — `JD_ROOT_MAP`, `JD_LEAF_WHITELIST`,
  `normalize_route_path`, `is_valid_leaf_route` are now exported
  as documented aliases. A fresh `git clone` can start the daemon
  without requiring a local `config/taxonomy.py` override.

### Tests
- 551 passed, 10 xfailed — up from 38 + 10 at v0.1.0.

### Not shipped (deferred to v0.3+)
- U27.5 — Filter outlet "N candidates pending" hint.
- U27.6 — `taxonomy retag` batch re-refine.
- U27.7 — Deprecation of zero-usage leaves + merge proposal.
- Real implementations of lancedb / duckdb_vss / sqlite_vec / pgvector
  (abstraction + alias routing is in place).
- Voyage / Jina / bge-reranker-v2-gemma dedicated reranker impls
  (currently alias to Cohere / bge-m3).

---

## [v0.1.0] — 2026-04-23

First public release. Working flywheel: OpenWebUI → daemon refines
conversations → Obsidian-style Markdown vault → Qdrant indexing →
RAG server → OpenWebUI Filter.

- `daemon/refine_daemon.py` — watchdog-driven refine pipeline with
  6-section knowledge cards, XYZ taxonomy, dedup, dual-write.
- `rag_server/` — FastAPI with bge-m3 embeddings + bge-reranker-v2-m3
  cross-encoder + Qdrant retrieval + freshness / payload boosts.
- `scripts/ingest_qdrant.py` — one-shot vault → Qdrant ingest.
- `packs/` — pack-aware routing + policy override system.
- `Filter/` — OpenWebUI Filter function with status badge and
  forbidden-prefix guards.

Full release notes:
<https://github.com/jprodcc-rodc/throughline/releases/tag/v0.1.0>

[v0.2.0]: https://github.com/jprodcc-rodc/throughline/releases/tag/v0.2.0
[v0.1.0]: https://github.com/jprodcc-rodc/throughline/releases/tag/v0.1.0
