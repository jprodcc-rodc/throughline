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

## Next (`v0.3` — frontend decoupling + engineering hardening)

v0.2.x already drove the embedder / reranker / vector-store
abstractions to ground (six real vector backends + native voyage /
jina rerankers — see "Shipped in v0.2.x" below). v0.3 turns to the
remaining two areas reviewers consistently flag: frontend coupling
to OpenWebUI, and engineering hygiene around long-running install
hygiene.

### v0.3 in progress

- **Reflection Layer (the throughline differentiator)** — three
  MCP tools that turn the existing card store into a thinking-state
  tracker, not just a memory tracker:
  - `find_open_threads` ✅ shipped — surfaces unfinished reasoning
    when the user starts a related conversation. Reads daemon
    state file populated by structural detection (token-overlap
    on cluster chronology, no LLM on hot path).
  - `check_consistency` ✅ shipped — when the user states a position,
    surfaces historical positions in the matching topic cluster
    AND the original reasoning, so the user can reaffirm, recognize
    drift, or update the current take. Not "you're wrong" — *"here's
    your past reasoning, please engage with it."*
  - `get_position_drift` ✅ shipped — returns the chronological
    trajectory of cards on a topic, with stance + reasoning per
    entry. Metacognitive infrastructure.

  **Engineering gate:** clustering accuracy ≥75% pairwise on the
  maintainer's vault (≥2,300 cards) — **cleared 2026-04-28 at
  0.975** (best threshold 0.70). Phase 2 implementation unblocked
  and shipped through 11 incremental commits.

  **Built on:** topic clustering (`mcp_server/topic_clustering.py`)
  + a Reflection Pass daemon (`daemon/reflection_pass.py`) that
  runs through 8 stages on every pass (load → reflectable filter →
  cluster → name canonicalization → back-fill → open-thread
  detection → contradiction detection (stub) → drift segmentation
  (stub) → writeback preview). State files mediate between the
  daemon's offline computation and the MCP tools' real-time reads;
  no LLM on the MCP hot path.

  **What's gated on user opt-in:** stage 3 cluster naming +
  stage 4 back-fill require `--enable-llm-naming` /
  `--enable-llm-backfill` flags + an OpenRouter / OpenAI-compatible
  API key. Total cost on the maintainer's 72-card reflectable
  subset: ~$0.01 per full pass (gemini-2.5-flash). Cache files
  dedupe so re-runs are essentially free until cards change.

  **Why this is the headline:** April 2026 Anthropic shipped
  past-chat referencing in Claude Desktop. Basic AI memory is
  commodity. Throughline's empty niche is *thinking-state
  tracking*: proactive surfacing of unfinished thinking,
  contradictions, drift — across all AI tools, on the user's own
  vault. Full design rationale + side-by-side with Anthropic's
  feature in
  [`docs/REFLECTION_LAYER_DESIGN.md`](docs/REFLECTION_LAYER_DESIGN.md).
  Position-metadata schema in
  [`docs/POSITION_METADATA_SCHEMA.md`](docs/POSITION_METADATA_SCHEMA.md).

  **Remaining for v0.3 final:** atomic vault frontmatter writeback
  (currently preview-only; high-blast-radius commit gated on its
  own smoke-test cycle), stage 6 LLM contradiction judgment
  (enriches `check_consistency` output), stage 7 LLM drift
  segmentation (refines `get_position_drift` from per-card to
  per-phase trajectory).

- **OpenAI-compatible proxy adapter** — a small FastAPI proxy that
  exposes `/v1/chat/completions` and injects throughline RAG before
  forwarding to the user's actual LLM provider. Lets any OpenAI-SDK
  client (LibreChat, custom apps, etc.) use throughline transparently.
- **`bge-reranker-v2-gemma`** — separate registry entry rather than
  aliasing to `bge-reranker-v2-m3`. The Gemma cross-encoder has a
  different size / accuracy trade-off worth surfacing.
- **`nomic-embed` + `MiniLM`** — distinct native embedder impls.
  Currently aliased to `bge-m3`; v0.3 ships the real models with
  their own vector-size + tokenizer wiring.
- **U27.6** — `python -m throughline_cli taxonomy retag --since DATE
  --domain X` for batch re-refining historical cards under a newly-
  added taxonomy leaf. Cost-bearing operation; gated behind the
  daily budget cap and an explicit `--confirm-cost`.
- **Stale-triage auto-archive** — `00_Buffer/` stubs older than
  N days (configurable, default 90) get auto-archived to
  `00_Buffer/_stale/` with a one-line manifest. Closes the "dual-
  write design has no expiry" feedback. Surfaced via doctor + a
  one-shot `throughline_cli triage prune --dry-run`.
- **`_norm_path` invariant lint rule** — pre-commit hook (or ruff
  custom check) that flags any `qdrant_client.upsert(point_id=...)`
  / equivalent call where `point_id` is not provably routed through
  `_norm_path()`. Forward-slash normalisation on Windows currently
  rests on convention + docstring; this turns it into a build
  failure when violated.
- **Recall accuracy regression suite** — the Haiku-judge
  `RecallJudge` 93.8% number was a one-shot eval. v0.3 ships an
  ongoing regression set (~50 ground-truth queries × ground-truth
  cards) re-run on every model upgrade (Haiku 4.6 → 5 → …) with
  results history surfaced in a new `docs/RECALL_HISTORY.md` and
  linked from README. Turns a "single point of failure" into a
  monitored dependency.
- **PyPI release.** `pip install throughline` instead of `git clone +
  venv + pip install -r requirements.txt`. Console-script entry
  points (`throughline-install`, `throughline-import`,
  `throughline-taxonomy`).
- **5-minute screencast / GIF in the README.** Removes the "what
  does it actually look like" friction. (User recording in
  parallel with v0.3 dev work — anchor commented in README is
  ready.)

### v0.3 may deliver (depends on user signal)

- **Cross-language taxonomy clustering** — bge-m3 embedding similarity
  to cluster `AI/Agent` ≡ `AI/代理` for multilingual users.
- **Per-pack Qdrant collection auto-routing** — `packs/pack_runtime.py`
  already supports collection override; auto-routing (e.g. `pack:
  medical/*` → its own collection) is the next step. Limits blast
  radius of a per-pack data leak.
- **Encrypted-at-rest vault option** — write cards through `age` or
  `gpg` so a stolen disk doesn't leak the vault. Offered as opt-in;
  default stays plaintext to keep `rg` searchability the headline
  feature.

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

- the v0.3 backends + frontend adapters have been used in anger by
  someone other than the author (production hours, not just CI),
- `v0.2.x → v0.3 → v1.0` migration is documented end-to-end with no
  manual fixups,
- the recall-accuracy regression suite has at least 3 model-version
  data points showing stability,
- the test suite covers all five user paths (Full / RAG-only /
  Notes-only × cold-start / warm-import).

---

## Shipped in v0.2.x (since v0.2.0)

Things this roadmap previously listed under v0.3 that landed early.
Tracking here so reviewers cross-checking ROADMAP vs CHANGELOG see
the deltas:

- **Vector-store backends**: `lancedb` (#6), `sqlite_vec` (#11),
  `duckdb_vss` (#10), `pgvector` (#9) — all shipped as real impls.
  Only spelling aliases remain in the registry (`sqlite-vec` →
  `sqlite_vec` etc.).
- **Reranker backends**: `voyage` + `jina` shipped as native HTTP
  clients (separate from the Cohere alias they used to share).
- **U27.5** — Filter outlet `🌱 N taxonomy candidates` hint via
  doctor + `__event_emitter__`.
- **U27.7** — zero-usage taxonomy leaf detection in doctor with a
  deprecation hint.
- **Docker compose for "try it out"** — single-command spin-up of
  Qdrant + daemon + an empty vault, with a sample import. README
  Quickstart leads with it.
- **`--express` install** — auto-detect provider from env var, sane
  defaults, ~3s config write. The 16-step wizard is now demoted to
  "when you want full control".
- **Wizard UX wave** — questionary arrow-key picker, rich spinner,
  hierarchical step-16 summary tree, back navigation, provider/key
  hard-block, universal "Other" model escape hatch.
- **MCP server (Phase 1)** — `mcp_server/` package exposing three
  tools (`save_conversation` / `recall_memory` / `list_topics`) over
  stdio so any MCP-aware client (Claude Desktop / Claude Code /
  Cursor / Continue.dev) can reach the throughline vault without
  migrating to OpenWebUI. `pip install -e .[mcp]`; setup at
  [`docs/MCP_SETUP.md`](docs/MCP_SETUP.md). Shipped in:
  - `5776f3d` — scaffolding + 3 tool stubs + 14 tests
  - `ea62907` — `save_conversation` real impl (writes raw .md
    into daemon queue with defensive turn-shape coercion)
  - `b306312` — `recall_memory` real impl (HTTP client to localhost
    rag_server `/v1/rag` with typed errors + domain filter +
    personal context surfacing)
  - `2bd9051` — `list_topics` real impl (taxonomy + vault scanner
    with 60s cache)

  Phase 2 reflection-layer tools (Open Threads / Contradiction
  Surfacing / Drift Detection) remain dogfood-gated; design sketch
  in `private/` strategy docs, NOT in the public ROADMAP yet.

---

## Explicitly out of scope

These have come up; they're not on any roadmap:

- **Hosted SaaS.** throughline is local-first. No cloud-hosted variant
  is planned.
- **Mobile app.** The reading surface is OpenWebUI / Obsidian; both
  have their own mobile stories.
- **Replacing OpenWebUI.** v0.3's MCP + OpenAI-compatible adapters
  decouple the engine, but a from-scratch chat UI is not a goal.
- **Replacing Obsidian.** Cards land as plain Markdown with YAML
  frontmatter. Obsidian is recommended but not required.
- **Built-in LLM provider proxy.** The wizard collects an
  OpenRouter / OpenAI / Anthropic / etc. key and uses the provider
  directly. We don't add a proxy hop. (The v0.3 OpenAI-compatible
  adapter is the *opposite* direction — letting other clients call
  through throughline, not throughline routing through a hop.)
- **Multi-device sync layer.** "your data, your machine" stays the
  core philosophy. If you need cross-device, layer your own sync
  (Syncthing, Resilio, iCloud Drive on the vault folder, …).
- **Team collaboration / multi-user mode.** Single-user, local-first,
  by design.

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
