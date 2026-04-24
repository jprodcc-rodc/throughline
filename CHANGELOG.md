# Changelog

All notable changes land here. Dates are UTC. For the full commit
list behind any entry, `git log vX..vY`.

This project follows [Semantic Versioning](https://semver.org/);
pre-1.0 minor bumps can include breaking config shape changes.

> **Contributors:** add new entries under `[Unreleased]` below.
> When the next version is cut, the maintainer renames that section
> to the new version number, dates it, and starts a fresh
> `[Unreleased]` block on top.

---

## [Unreleased]

### Milestone
- **Repo flipped PUBLIC** — <https://github.com/jprodcc-rodc/throughline>.
  First time the project is visible to anyone on the internet.
- **Docs site live** — <https://jprodcc-rodc.github.io/throughline/>.
  mkdocs-material, auto-deploys on push via
  `.github/workflows/docs.yml`.

### Changed — README polish (2026-04-25)
- New tagline: *"Stop re-explaining yourself to every new chat."*
- Status block rewritten to drop "for the author" signal that
  implied nobody else could use it.
- Front-page mermaid replaced with a before/after text pair;
  mermaid retained for the later Architecture section.
- Quickstart moved up to section #2 (after "What it does").
- Comparison table trimmed from 8 dimensions to 5 (mobile-friendly).
- Card example swapped from PyTorch MPS → keto-rebound for a more
  emotional, personal-context-capturing demo (still real data from
  the bundled sample export).
- Badges trimmed from 5 to 3 (test + license + python).
- Phase 6 regression section moved from README to `docs/TESTING.md`;
  README now carries a one-line pointer instead.

### Added
- `docs/TESTING.md` — regression suite overview, Phase 6 gate
  historical record, contributor test conventions.

### Added
- **U28 · multi-provider LLM support** — new
  `throughline_cli/providers.py` registry with 16 OpenAI-compatible
  presets: Global (OpenAI, Anthropic via OpenAI-compat shim,
  DeepSeek, Together, Fireworks, Groq, xAI, OpenRouter),
  China-market (SiliconFlow 硅基流动, Moonshot/Kimi, DashScope
  Alibaba Qwen, Zhipu GLM, Doubao 字节豆包), Local (Ollama,
  LM Studio), plus a generic OpenAI-compatible escape hatch.
  Each preset is a `(base_url, env_var, signup_url, model_list,
  extra_headers, region)` tuple. Data-driven; new providers = one
  dict entry.
  - `llm.py` gains `provider_id=` kwarg; endpoint + key + extra
    headers resolved from the preset. Unknown provider_id falls
    through to legacy chain (no crash). Error messages cite the
    provider's specific env var + signup URL.
  - Wizard steps 4 + 5 split: step 4 picks provider backend (auto-
    defaults to whichever env var is set, ● marker next to
    configured providers); step 5 picks a model SCOPED to that
    provider's list.
  - New `throughline_cli/active_provider.py` resolves the active
    provider for NON-wizard callers (daemon, scripts) with
    precedence `THROUGHLINE_LLM_PROVIDER` env > `llm_provider` in
    config.toml > autodetect > "openrouter". Never raises.
  - Daemon `call_llm_json()` reads resolved endpoint + key at
    module load; provider-specific extra headers merged without
    clobbering daemon's X-Title. Legacy `OPENROUTER_URL` still
    honoured. Startup log now shows `LLM PROV = <id> -> <url>`.
  - `doctor` gains `check_llm_provider_key`: verifies the resolved
    provider's env var is set; warns (not fails) when missing so
    fresh installs stay green.
  - 57 new tests: `test_providers.py` (32), `test_llm_providers.py`
    (13), `test_active_provider.py` (12).

- Open-source-project hardening: GitHub Actions CI (pytest 3.11 +
  3.12, ruff lint), CodeQL weekly scan, Dependabot for pip +
  github-actions, branch protection ruleset, repo metadata + 16
  topics, 3 seeded `good first issue` tickets, YAML-form issue
  templates, PR template, `SECURITY.md`, `CODE_OF_CONDUCT.md`,
  `ROADMAP.md`, `pyproject.toml` package skeleton with
  optional-dep extras (`local` / `openai` / `chroma` / `all` /
  `dev`) + console-script entry points
  (`throughline-{install, import, taxonomy, doctor}`).
- UX wave (post-v0.2.0):
  - **`python -m throughline_cli doctor`** — 10-check health probe
    (Python / imports / config / state / services / caches) with
    remediation hints, `--quiet` and `--json` modes.
  - **`python -m throughline_cli import sample`** — bundled
    10-conversation synthetic export at `samples/claude_sample.jsonl`
    so users can see the loop without their own export.
  - **`python -m throughline_cli --version`** / **`-V`** /
    **`version`** — print package version. `__version__` resolved
    from `importlib.metadata`, falling back to a literal for source
    checkouts.
  - **Wizard end-of-flow next-steps panel** — mission-tailored
    copy-paste commands for rag_server, daemon, and Filter install.
  - **Wizard step 13 cost preflight** — explicit `ask_yes_no("Run
    the preview?")` gate before the ~$0.01 LLM call.
  - **README polish** — comparison table vs mem0 / Letta /
    SuperMemory / OpenWebUI memory; before/after card example;
    Mermaid architecture diagram replacing the ASCII flow.
- Documentation:
  - `CONTRIBUTING.md` expanded — dev setup, claim-issue flow,
    commit conventions, house style.
  - `docs/DEPLOYMENT.md` — new "Quick install (via wizard)",
    "Pluggable backends", "Diagnostics" sections; Windows note
    upgraded to tier 1 for dev + wizard + tests.
  - `docs/ARCHITECTURE.md` — new §13 covers v0.2.0 additions
    (U12/U20/U21 abstractions, U23 dials, U27 growth loop, U3
    budget, doctor surface) without rewriting §1-12.
  - `docs/DESIGN_DECISIONS.md` — entries 10-13 capture v0.2.0
    design calls (aliased backends, `proposed_x_ideal` as separate
    field, dial defaults render to empty string, three-state
    doctor reporting).
  - `docs/ALPHA_USER_NOTES.md` — v0.2.0 update section: which
    deferrable rough edges got fixed + 5 new UX edges surfaced.

### Changed
- **Provider-agnostic front door.** README + `docs/DEPLOYMENT.md`
  rewritten so OpenRouter is listed alongside 15 other providers
  rather than the default. README's provider table regrouped by
  use case (Direct / Hosted open-weights / China / Multi-vendor
  proxy / Local / Escape hatch). Prose now says "no preferred
  vendor — wizard auto-detects whichever env var you already
  have set." Existing `OPENROUTER_API_KEY` users keep working
  with zero friction; no behaviour change.
- **Repo description + topics refreshed** — reflects the 16-
  provider story. Topics now: 16 entries including `anthropic`,
  `openai`, `deepseek`, `siliconflow`, `ollama`, `local-first`.

### Fixed
- **Daemon LLM calls ignored the wizard's provider choice.**
  Before `9536ba0`, `daemon/refine_daemon.call_llm_json()` hard-
  coded OpenRouter. A user who picked SiliconFlow in the wizard
  would see the preview hit SiliconFlow, then watch the real
  refine daemon keep hitting OpenRouter. Now module-load reads
  through `throughline_cli.active_provider.resolve_endpoint_and_key()`.
- **Fresh-clone pip install silently failed on Chinese-locale
  Windows.** `requirements.txt` had UTF-8 em-dashes in comment
  banners; pip on GBK/cp936 locales couldn't decode them and
  returned exit 0 anyway. Fixed: pure ASCII + inline note about
  `PYTHONUTF8=1` for anyone hitting similar drift elsewhere.
  Regression test in `TestRequirementsFileAscii`.
- **`python install.py --help` started the wizard.** The wizard
  main() ignored unknown args, so `--help` silently began a
  16-step prompt flow. Added explicit help handling + unknown-
  flag rejection (exit 2 with usage panel).
- **Stale `v0.2.0-dev` labels** in wizard banner + step 4 text.
  Banner now reads dynamically from
  `throughline_cli.__version__`.
- **Daemon import on a fresh clone.** `daemon/refine_daemon.py`
  imported four names from `daemon/taxonomy.py` (`JD_ROOT_MAP`,
  `JD_LEAF_WHITELIST`, `normalize_route_path`, `is_valid_leaf_route`)
  that the module never exported. A `git clone` + `python -m
  daemon.refine_daemon` ImportError'd at module load. Aliases
  added; regression test in `test_daemon_import_surface.py`.
- **rag_server actually uses the U12/U20/U21 abstractions.** Before
  the wiring commit (`3568b22`), `EMBEDDER` / `RERANKER` /
  `VECTOR_STORE` env vars set in the wizard were ignored — the
  server hard-coded bge-m3 + bge-reranker-v2-m3 + Qdrant. Now the
  env vars flip the backend end-to-end.
- **Error messages without remediation.** Audit pass added "what to
  do next" hints to user-facing failures in `scripts/ingest_qdrant.py`
  (`VAULT_PATH` missing, openai missing), `daemon/pack_source_model_guard.py`
  CLI handler, `throughline_cli/llm.py` no-API-key.
- **`scripts/ingest_qdrant.py` openai import deferred.** Was a
  module-load `sys.exit(1)` if openai was missing; now lazy via
  `_get_embed_client()` so the module imports cleanly without the
  optional dep.
- **Ruff F + E9 dead-code sweep.** 22 unused imports + 4 unused
  local-variable bindings cleaned up across daemon / ui / adapters
  / tests.

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
