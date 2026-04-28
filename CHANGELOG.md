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

### Validated — Phase 2 Reflection Layer first real-LLM E2E (2026-04-28+2)

**First end-to-end pass with real LLM calls against the maintainer's
production vault.** All 8 stages of `daemon.reflection_pass` ran
successfully on a 2477-file Obsidian vault, validating the full Phase 2
pipeline beyond synthetic-fixture testing.

**Pipeline numbers:**
- 2477 markdown files scanned → 72 reflectable (filter dropped 2405
  logs / drafts / indexes)
- 72 cards clustered into 24 topics @ similarity threshold 0.70
  (matches the gate experiment best score)
- 23 of 24 clusters successfully named by LLM (1 sanitizer reject —
  see Known issues below)
- 72/72 cards back-filled with `claim_summary` and `open_questions`
- 42 cards flagged with unresolved questions
- 237 contradiction-judge pairs evaluated, 0 contradictions detected
  (taxonomy `agreement` / `orthogonal` / `evolution` working;
  validates precision — recall would need a deliberate-conflict test
  set)
- 35 drift phases computed across 24 clusters; per-cluster
  `drift_kind` classifications correctly identify temporal evolution
- 72 cards' worth of frontmatter additions visible in writeback
  preview JSON; vault was NOT mutated (`--commit-writeback` flag
  defaults OFF, schema verified non-conflicting)

**Cost:** ~$0.18 across all LLM stages (gemini-2.5-flash via OpenRouter).
**Wall time:** 8 minutes.

**Significance:** Per-project history this is the first real LLM API
call from any Phase 2 daemon stage. Prior validation was
mock-tested; quality of synthetic outputs is now confirmed against
real user data.

**Sample quality (cluster names):** `personal_medication_regimen`
(largest, size 17) · `veo_imagen_prompt_design` (size 13) ·
`australian_immigration_491` · `tailscale_exit_node_troubleshooting`
· `venlafaxine_xr_missed_dose` — all sensible snake_case matching
the cluster's actual content.

**Sample quality (open_questions):** specific actionable follow-ups,
not generic "what is X" — e.g. for the PS5/HDMI card: "Does
Topology A introduce noticeable input lag for competitive gaming?"
"How to verify the actual passthrough bandwidth when manufacturer
only states 'HDMI 2.1' without 4K/120Hz/VRR/ALLM specifics?"

**Known issues surfaced and addressed in follow-up commits:**

- Cluster name sanitizer rejected `3d_modeling_methods` because
  `_VALID_NAME_RE` required leading letter; loosened to allow digit
  prefix (snake_case identifier conventions allow it; schema docs
  do not require letter-start). Fix: `2980244`.
- Contradiction judge `DEFAULT_MAX_TOKENS=200` truncated 1/237
  responses with verbose `reasoning_diff`; raised to 600. Fix:
  `e03b4c1`.
- Contradiction judge had no retry on transient TCP timeouts (4/237
  affected); added `_urlopen_with_retry` helper distinguishing 4xx
  (permanent) from 5xx/URLError/timeout (retry with exponential
  backoff). Same commit `e03b4c1`. Re-run of the E2E pass after
  these fixes shipped landed 0 errors across 242 pair judgments
  (24/24 cluster names, 0 truncations, 0 unhandled timeouts).

**Outstanding (deferred to a follow-up commit):** the maintainer's
vault stores ZH/EN translations of the same conversation as
separate cards (`20260415refined_<title>.md` paired with
`<title>__<hash>.md`), causing duplicated work in stages 2/4/6.
Upstream dedup heuristic (same hash suffix + similarity > 0.95)
is the natural fix.

**Run artifacts** (gitignored; private to maintainer):
`private/dryrun_2026-04-28/` — `FINDINGS.md` plus 7 state JSON
files plus run logs. Useful as a real-world reference when iterating
on prompts, sanitizers, or schema.

### Added — Phase 2 Reflection Layer overnight wave (2026-04-28+1)

12 commits extending the Phase 2 Reflection Layer with:

**Stages 6 + 7 LLM enrichment (mock-tested; real LLM gated on
working API key):**

- Stage 6 contradiction judgment (`aaca4de`):
  ``mcp_server/llm_judge.py`` (judge_pair) + reflection_pass
  ``_stage_detect_contradictions`` + reflection_contradictions.json
  state file. Conservative system prompt — ``is_contradiction=true``
  only for direct_reversal, NOT for evolution / scope_narrowing /
  agreement / orthogonal. ``check_consistency`` MCP tool gracefully
  filters to actually-contradicting cards when stage 6 has run;
  falls back to all-cluster-positions otherwise.
- Stage 7 drift segmentation (`ee5e07f`):
  ``mcp_server/llm_drift_segmenter.py`` + reflection_pass
  ``_stage_compute_drift`` + reflection_drift.json. Topic-level
  ``drift_kind`` classification (healthy_evolution /
  drift_without_reasoning / following_trends / mood_swings /
  unsegmented). Per-cluster phase segmentation — each phase gets
  phase_name, stance, started/ended dates, transition_reason,
  card_paths. ``get_position_drift`` MCP tool returns per-phase
  trajectory when stage 7 has run; per-card otherwise.

**Real frontmatter writeback (`13bc812`):**

``daemon/writeback_commit.py`` implementing the 2026-04-28+1
architectural decision (hybrid):

- ``position_signal`` + ``open_questions`` → surgical text append
  to existing frontmatter. Existing keys NEVER overwritten. No
  PyYAML round-trip = zero formatting drift on user customizations
  (quotes, comments, trailing whitespace, key order).
- ``reflection.*`` → sidecar JSON file
  ``<card_dir>/.<card_name>.reflection.json``. Daemon-managed
  metadata refreshed every pass without ever touching the
  frontmatter block.
- Atomic write: ``NamedTemporaryFile`` + ``os.replace`` in same
  dir (Windows + cross-device safe).
- Backup: ``<card_dir>/.<card_name>.backup-<unix_timestamp>``
  before any mutation. Daemon never auto-deletes.
- Idempotency: re-running with same data is a true no-op.

CLI: ``--commit-writeback`` flag (default OFF). Without it, only
preview JSON is written; real writeback gated.
``--no-writeback-backup`` to skip backups when user has git tracking.

**Diagnostic CLIs:**

- ``--inspect`` subcommand (`e6091f8`):
  ``daemon/reflection_inspect.py`` pretty-prints summaries of all
  state files. Per-file: presence ✓/✗ inventory, file sizes, age
  ("3h ago"), per-summarizer extraction of relevant fields
  (cluster sizes / open thread samples / writeback diffs).
- ``--explain CARD_PATH`` subcommand (`e2bdaeb`):
  ``daemon/reflection_explain.py`` dumps everything the daemon
  thinks about ONE card — cluster membership, sister cards,
  back-fill cache, open-thread status, what writeback would add.
  Useful when an MCP tool returns surprising results and operator
  wants to see why.

**Refactor — centralized state paths (`7639a60`):**

``daemon/state_paths.py`` consolidates seven default_*_file()
helpers + ``card_timestamp()`` chronology resolver. Reserves
paths for stage 6/7 outputs (reflection_contradictions.json,
reflection_drift.json) ahead of their implementation.
``all_state_files()`` returns mapping for diagnostics tools.

**Doctor extension (`002f66b`):**

``mcp_server/doctor.py`` adds Phase 2 Reflection Layer state
section. Reports per-file presence + size + age. When all state
files are missing, single consolidated warn line with fix hint.

**Documentation:**

- NEW: ``docs/RUNTIME_STATE_FILES.md`` (~400 lines) — every state
  file's writer, readers, refresh cadence, JSON schema, sample
  payload. Plus architecture diagram showing daemon → state files
  → MCP tools dataflow. (`e03afde`)
- NEW: ``docs/REFLECTION_LAYER_USER_GUIDE.md`` (~400 lines) —
  user-facing companion to design + schema docs. TL;DR table,
  per-tool sections with sample conversations, three-step setup
  walkthrough, cost expectations by vault size, "what NOT to
  expect" calibration, when-to-call-which-tool matrix. (`892c8cd`)
- UPDATED: ``docs/MCP_SETUP.md`` — tool table 3 → 6 with new
  Phase 2 trio. (`e03afde`)
- UPDATED: ``docs/FAQ.md`` — top section "What is the Reflection
  Layer? How is it different from chat memory?" with side-by-side
  comparison and one-line distinction. (`e03afde`)
- UPDATED: ``README.md`` — Reflection Layer mermaid diagram
  showing third pipeline. (`892c8cd`)
- UPDATED: per-tool docstrings (`c325b2f`) — 4 example trigger
  conversations + "what to do with the result" guidance per
  tool, helping host LLMs fire at the right moment.

**Test depth:**

- 29 edge-case tests (`1639828`): enormous body / only-emoji
  header / mixed-language / malformed YAML / state files with
  invalid UTF-8 / Chinese statement matching Chinese cluster.
- 7 end-to-end integration tests (`545a0bd`): synthetic vault
  → full pipeline → MCP tools. Includes namer-cache-on-rerun
  test confirming no double LLM calls.
- ``run_pass(use_default_state_paths=True)`` — programmatic
  callers now get same default-path behavior as CLI.

**Test counts:** 1697 → ~1860 passes net across the wave (count
varies ±30 by pytest collection).

**LLM cost on author's vault (when all stages enabled):**
- Stage 3 cluster naming: ~$0.0004
- Stage 4 back-fill: ~$0.01
- Stage 6 contradiction: ~$0.002 (~50 pairs)
- Stage 7 drift: ~$0.005 (~6 multi-card clusters)
- **Total full pass: ~$0.017 / ¥0.12.** Cache makes re-runs
  near-zero.

**0 vault file mutations** in this wave — real writeback
infrastructure shipped but ``--commit-writeback`` flag is OFF
by default. **0 real LLM calls fired** during development; all
tests use mocked clients.

### Added — Phase 2 Reflection Layer (2026-04-28)

The Reflection Layer ships in incremental commits behind opt-in
flags. All three MCP tool surfaces are real implementations
reading state files written by the Reflection Pass daemon. **No
vault file mutations** — frontmatter writeback is preview-only
in this batch and lands in a follow-up commit with explicit
`--commit-writeback` gating.

**Engineering gate:** clustering accuracy ≥75% pairwise on the
maintainer's vault (≥2,300 cards) — **cleared 2026-04-28 at
0.975** (best threshold 0.70).

**New daemon module:** `daemon/reflection_pass.py` orchestrates
an 8-stage pass — load + frontmatter parse → reflectable filter
(slice_id or managed_by) → bge-m3 clustering → cluster name
canonicalization (LLM, opt-in `--enable-llm-naming`) → Path A
back-fill (LLM, opt-in `--enable-llm-backfill`, claim_summary +
open_questions) → open-thread detection (structural,
token-overlap, conservative threshold) → contradiction detection
(stub) → drift segmentation (stub) → writeback preview (no
vault mutation).

**New MCP tools (real impls replacing stubs):**

- `find_open_threads(topic?, limit=5)` — surfaces unfinished
  reasoning. Reads `reflection_open_threads.json`.
- `check_consistency(statement, soft_mode=True)` — finds
  best-overlap cluster, returns historical positions as
  candidate contradictions. Host LLM does the soft-mode framing
  in conversation. Reads `reflection_positions.json`.
- `get_position_drift(topic, granularity='transitions')` —
  chronological trajectory of cards on the topic. Reads
  `reflection_positions.json`.

**State files** under `$THROUGHLINE_STATE_DIR/`:

- `reflection_pass_state.json` — per-pass watermark
- `reflection_cluster_names.json` — cluster_signature → name cache
- `reflection_backfill_state.json` — `path|mtime` → essence cache
- `reflection_open_threads.json` — surfaced open threads
- `reflection_positions.json` — comprehensive position database
- `reflection_writeback_preview.json` — what would be written

**New supporting modules:**

- `daemon/card_body_parser.py` — bilingual section parser
  (English + Chinese-emoji-English + Chinese-only headers).
  Real-vault smoke: 80.4% of frontmatter cards / 100% of
  slicer-output cards have at least 1 known section.
- `daemon/open_threads.py` — CJK bigram + English unigram
  tokenizer, token-overlap question-resolution heuristic.
- `daemon/writeback.py` — frontmatter-addition assembler;
  preview-only.
- `mcp_server/llm_namer.py` — stdlib HTTP client for cluster
  naming. `OPENROUTER_API_KEY` → `OPENAI_API_KEY` env-var
  fallback.
- `mcp_server/llm_extractor.py` — stdlib HTTP client for Path A
  back-fill, same env-var conventions.
- `mcp_server/position_state.py` — shared state-file readers +
  cluster-matching helpers used by `check_consistency` and
  `get_position_drift`.

**Public docs:**

- `docs/POSITION_METADATA_SCHEMA.md` — schema reference + the
  2026-04-28 vault-format addendum calibrated against the
  maintainer's real vault.
- `docs/REFLECTION_LAYER_DESIGN.md` — public-facing rationale +
  side-by-side comparison with Anthropic's chat-memory feature.

**LLM cost on the maintainer's 72-card reflectable subset:**

- Stage 3 cluster naming: ~$0.0004 per pass
  (~24 clusters × gemini-2.5-flash)
- Stage 4 back-fill: ~$0.01 per pass (one-time; cache dedupes)
- **Total: ~$0.01 per full pass.** Re-runs essentially free.

**Test coverage:** 1,455 → 1,697 tests pass (net +242 across the
Phase 2 commit series). Mock LLM clients throughout — zero real
API calls fired during tests.

### Changed — Phase 1.5 PyPI split (2026-04-28)
- **`throughline-mcp` is now its own PyPI package.** New
  `mcp_server/pyproject.toml` defines an independent
  `throughline-mcp` package built from the same git repo. Install
  becomes a single line once published: `pip install throughline-mcp`
  (auto-pulls `throughline >= 0.2.0` + `fastmcp >= 0.4`).
- The parent `throughline` package no longer bundles the
  `mcp_server` Python package directly — it's excluded from
  `setuptools.packages.find` to prevent two wheels claiming the
  same files. Verified via build inspection: the throughline-0.2.0
  wheel contains 0 mcp_server files; the throughline_mcp-0.1.0
  wheel contains all 11 of them.
- The `pip install throughline[mcp]` extras flag still works for
  backward compat — its dependency rewires to `throughline-mcp >= 0.1`
  (was `fastmcp >= 0.4`), so users running the extras command get
  the new package transitively.
- New `throughline-mcp` console script: `throughline-mcp` invokes
  `mcp_server.__main__:main` directly. Claude Desktop /
  Continue.dev configs can use just `"command": "throughline-mcp"`
  instead of `"command": "python", "args": ["-m", "mcp_server"]`.
- Same git repo, same source tree, no file moves. Phase 1.5 is
  pure packaging metadata.

### Fixed — adapter→daemon H1/H2 role-marker contract (2026-04-28)
- `throughline_cli/adapters/common.py:render_markdown` was emitting
  H1 capitalised (`# User` / `# Assistant`); the daemon's
  `_MSG_SPLIT_RE` parser at `daemon/refine_daemon.py:853` only
  matches H2 lowercase (`^## (user|assistant)\s*$`). Result: every
  ChatGPT / Claude / Gemini export imported through the adapter
  path silently produced raw .md files the daemon couldn't parse —
  slicer saw zero messages, conversations refined to nothing.
- Fix: `render_markdown` now writes `## user` / `## assistant`,
  matching the daemon's actual parser. Existing test that asserted
  the H1 format (locking in the bug) updated to assert H2.
- Regression suite: new `fixtures/v0_2_0/test_adapter_to_daemon.py`
  with 7 tests that round-trip through the actual `render_markdown`
  → `_parse_messages` path. Catches future drift immediately.
- User-facing impact: any raw .md files written by the broken
  adapter (if any) need re-import to parse correctly. The simplest
  path is rerunning `python -m throughline_cli import <source>`.

### Added — MCP server (Phase 1, 2026-04-27)
- **`mcp_server/` package — Phase 1 complete.** New top-level Python
  package alongside `daemon/` / `rag_server/` / `throughline_cli/`,
  exposing three tools over MCP stdio so any MCP-aware host
  (Claude Desktop / Claude Code / Cursor / Continue.dev / etc.)
  can reach the throughline vault without OpenWebUI in the loop.
  Setup at [`docs/MCP_SETUP.md`](docs/MCP_SETUP.md).
  - `save_conversation(text, title?, source, wait_for_refine?)` —
    writes a timestamped .md to `$THROUGHLINE_RAW_ROOT/YYYY-MM/`
    in the daemon's expected `## user` / `## assistant` H2
    format, with defensive turn-shape coercion handling 4 input
    shapes (H2 canonical / H1 capitalised / `User:` prefix /
    free prose). Daemon's existing watchdog picks up automatically.
    25 tests.
  - `recall_memory(query, limit?, include_personal_context?, domain_filter?)`
    — HTTP client to localhost rag_server `/v1/rag` (or
    `THROUGHLINE_RAG_URL` override). Three typed exceptions for
    clear error UX: server unreachable (most common: rag_server
    not running), server-side error, malformed response. Maps
    rag_server's response to the documented MCP shape. Honors
    `include_personal_context=True` by setting `pp_boost=1.0` and
    surfacing personal_persistent cards as a concatenated string.
    Domain filter applied client-side via X-axis tag prefix match.
    27 tests.
  - `list_topics(prefix?, include_card_counts?)` — reads active
    `daemon.taxonomy.VALID_X_SET` (33 default domains; user override
    at `config/taxonomy.py` honoured via the daemon's existing
    resolution chain) + optionally walks vault for per-domain
    counts. 60s in-process cache to avoid re-walking on every call.
    23 tests.
  - `pyproject.toml` adds `[mcp]` extras (`fastmcp >= 0.4`):
    `pip install -e .[mcp]`.
  - `python -m mcp_server` is the stdio entry point; absent
    `fastmcp` install it prints a clear hint and exits 1 (locked
    decision Q2: fail-with-message, never auto-install).
  - **No existing code modified** — Phase 1 is purely additive
    (~770 LOC code + ~1,000 LOC tests). 1260 → 1372 tests.
  - Architectural decisions + 6 locked design choices in
    `private/MCP_SCAFFOLDING_PLAN.md` (gitignored). Pre-implementation
    audit at `private/MIGRATION_AUDIT.md` confirmed 99% of existing
    33,700 LOC is shared core that needs zero changes for MCP form.
    Phase 1.5 (post-dogfood, ~½ day) splits `mcp_server/` into an
    independent `throughline-mcp` PyPI package from the same git
    repo for cleaner one-line install (`pip install throughline-mcp`).

### Added — post-v0.2.0 ship-and-iterate wave (2026-04-26)
- **LanceDB** is now a first-class `VECTOR_STORE` backend alongside
  Qdrant + Chroma — embedded, file-based, zero-server (closes #6).
  `pip install throughline[lancedb]`. `_LanceDBUnavailable` stub
  returned when the optional dep is missing so the wizard can list
  it without an import-time crash. 7 tests
  (`TestLanceDBStoreWithoutLancedb` + `TestLanceDBStoreWithFakeLancedb`).
- **sqlite-vec** is a first-class `VECTOR_STORE` backend (closes #11)
  — single SQLite file + the `sqlite-vec` loadable extension, the
  lightest-weight credible backend. Runs on a Raspberry Pi; sqlite3
  is stdlib so the only dep is `sqlite-vec` itself. Two-table schema
  (vec0 virtual table for embeddings + companion meta table mapping
  rowids back to string ids + JSON payloads). `_SqliteVecUnavailable`
  stub when missing. 7 tests using a sqlite3.connect proxy that
  emulates vec0's MATCH operator with Python-side L2 ranking.
- **DuckDB-VSS** is a first-class `VECTOR_STORE` backend (closes #10)
  — embedded analytical SQL + vector search in a single .duckdb
  file. Best fit when DuckDB is already in the analytics stack.
  Single-table schema per collection (id VARCHAR PK, vector
  FLOAT[N], payload JSON); upsert via `INSERT ... ON CONFLICT (id)
  DO UPDATE`; search via `array_distance()` ORDER BY dist LIMIT k.
  VSS extension auto-installed/loaded on connect. `_DuckDBVSSUnavailable`
  stub when `duckdb` is missing. 7 tests via fake `duckdb` module
  with a minimal SQL parser.
- **U27.5 (lite): pending-candidates surface in doctor.** New
  `taxonomy.pending_candidates_count()` helper + `check_taxonomy_pending`
  doctor check. Warns when growth candidates are pending review (with a
  pointer to `python -m throughline_cli taxonomy review`); ok otherwise.
  The U27 loop's value collapses if users never run the review command;
  the doctor is the obvious place to remind them. 9 tests.
- **U27.7 (lite): zero-usage leaf detection.** New
  `taxonomy.detect_zero_usage_leaves()` helper + `taxonomy zero-usage`
  CLI subcommand. Walks the vault, intersects `primary_x` frontmatter
  against `VALID_X_SET`, and lists leaves with no cards as deprecation
  candidates. Read-only — actual deprecation is a manual `taxonomy.py`
  edit, mirroring the cautious philosophy of U27.4 (the user always
  signs off on taxonomy mutations). 8 tests.
- **Voyage + Jina rerankers** now ship as real `RERANKER` backends
  alongside Cohere — no longer alias to Cohere. Both follow the same
  `{index, relevance_score}` shape; `VoyageReranker` defaults to
  `rerank-2-lite`, `JinaReranker` to `jina-reranker-v2-base-multilingual`
  (deliberately multilingual-default given the project's Chinese-first
  heritage). Standard env vars: `VOYAGE_API_KEY` / `JINA_API_KEY`,
  with `*_BASE_URL` overrides for proxies. Both fall through to
  SkipReranker on missing key — graceful degrade. +10 tests.
- **pgvector** is a first-class `VECTOR_STORE` backend (closes #9) —
  Postgres + the pgvector extension. The only server-based backend
  in the embedded-alternates set; useful when the team already
  operates Postgres and wants vectors in the same DB. Connection
  via `PGVECTOR_DSN` env (falls back to `DATABASE_URL`); per-
  collection table `(id TEXT PK, vector vector(N), payload JSONB)`;
  HNSW index with `vector_cosine_ops` (auto-falls-back to IVFFlat
  on older pgvector). Upsert via `INSERT ... ON CONFLICT (id)
  DO UPDATE`; search via `vector <=> %s::vector ORDER BY dist
  LIMIT k`. `_PgVectorUnavailable` stub when `psycopg` (v3) is
  missing. 8 tests via fake `psycopg` module. **All four originally-
  aliased v0.3 backends (lancedb / sqlite_vec / duckdb_vss / pgvector)
  are now first-class in v0.2.x — only `none` remains as an
  alias-to-qdrant placeholder.**
- **`throughline_cli refine --dry-run <path.md>`** — zero-cost
  refiner-prompt preview. Parses a raw conversation, reports which
  slicer tier WOULD fire + which model, and prints the refiner
  system + user prompts as they'd be sent — without calling any
  LLM. `--show-full-prompt` / `--pack NAME` / `--no-color`.
  Refuses to run without `--dry-run` (there's no real-refine CLI
  path in v0.2.x — daemon handles that). 11 tests.
- **Config schema validation + doctor check + CLI.** `config.validate()`
  surfaces typos (`dailey_budget_usd`), enum drift (`privacy =
  "cloudmax"`), type mismatches, and unknown provider IDs. New
  `check_config_schema` doctor check warns (not fails) per issue
  with Levenshtein-based suggestions. Runtime `config.load()`
  behaviour UNCHANGED — validation is surfaced on demand.
  New `python -m throughline_cli config [validate | show | path]`
  subcommand for standalone use + CI linting (with `--json`
  output and a custom PATH argument). 33 tests.
- **Tier 2 additions from the A-J backburner wave:**
  - `throughline_cli uninstall` — tear down config / state /
    logs / raw, vault untouched, with `--dry-run` / `--yes` /
    `--drop-collection`.
  - `throughline_cli anthropic_adapter` — native /v1/messages
    shape for Anthropic-direct users. Translates to/from OpenAI-
    compatible shape the rest of the codebase expects.
  - `throughline_cli cost` — LLM spend dashboard
    (today/week/month/all).
  - `throughline_cli stats` — vault + taxonomy + lifetime-cost
    summary (screenshot-friendly).
  - `docs/FAQ.md` — 15 recurring questions (differentiation vs
    ChatGPT memory / Claude Projects / mem0 / OpenWebUI memory).
  - `docs/THREAT_MODEL.md` — asset inventory + threat actors +
    defences + explicit scope cuts + hardening recommendations.
  - `prompts/README.md` — 209-line contributor guide for the 8
    refiner prompt variants + how to add a new-language pack.
  - `refine_kept_slices()` extraction from `process_raw_file` —
    the per-slice refine loop is now a testable pure-ish
    function. +5 tests without watchdog setup.

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
