# Why a 16-step wizard exists

A note on the engineering behind `python install.py`. throughline's
install wizard is the most-touched piece of user-facing code in the
project. This doc explains why it has the shape it has — for
contributors thinking about extending it, and for reviewers
wondering whether the complexity earns its keep.

---

## The shape, in one sentence

> 16 steps when you want full control · `--express` (1 command,
> auto-detect) when you don't · `--reconfigure` to change a few
> things after install without restarting · `--dry-run` to preview
> any of these paths · back navigation throughout · pairwise +
> property-based test coverage so the choices we expose actually
> work in combination.

Each piece earns its place. None was added speculatively.

---

## Why 16 steps (and not fewer)

The wizard collects 16 *real* decisions, not 16 dialogs over the
same setting. They're the irreducible config-space of a
self-hosted PKM pipeline:

| Step | Decision | Default | Why exposed |
|---|---|---|---|
| 1 | Python version + venv check | (auto) | Many install failures resolve to "wrong Python" — better to fail-fast with a fix hint than mid-import |
| 2 | Mission (Full / RAG-only / Notes-only) | Full | Branches the rest of the wizard; RAG-only saves 30s/refine on machines that don't need readable cards |
| 3 | Vector DB (qdrant / chroma / lancedb / sqlite_vec / duckdb_vss / pgvector) | qdrant | Six real backends; users on existing Postgres or DuckDB stacks pick differently |
| 4 | LLM provider (16 presets) | auto-detect from env | The user already exported some `*_API_KEY`; we shouldn't ask them to type another |
| 5 | Specific model | preset's first | Cost / speed / capability vary 10× across models from the same provider |
| 6 | Privacy tier (local_only / hybrid / cloud_max) | hybrid | Pre-selects backends in steps 7+ to match — no manual cross-checking |
| 7 | Embedder + reranker | bge-m3 + bge-reranker-v2-m3 | Privacy tier in step 6 narrows; users pick from the legal subset |
| 8 | Prompt family (claude / gpt / generic) | inferred from step 4 | Prompt phrasing matters more than people think; matching the model family wins 5-10% on refine quality |
| 9 | Import source (chatgpt / claude / gemini / openwebui-sqlite / sample / none) | none | Users with existing chat exports save weeks of manual catch-up |
| 10 | Import scan + cost estimate + privacy consent | (display) | We refuse to backfill 1000 conversations through someone's API without them seeing the dollar number first |
| 11 | Refine tier (skim / normal / deep) | normal | 40× cost spread; deep is for re-refining important conversations later |
| 12 | Card structure (standard / RAG-only / minimal) | standard | RAG-only mission shifts here automatically; standalone tweak available |
| 13 | Live LLM preview + 5-dial tuning | (interactive) | Users see one real card refined from a real conversation BEFORE committing to backfill — the most-skipped step in similar tools, and the one that catches the most "wait, this doesn't fit my style" cases |
| 14 | Taxonomy strategy (minimal / inherit / derive / template) | minimal | Users with <100 cards need a skeletal start; users with 2000+ benefit from a one-shot LLM derivation of their existing content |
| 15 | Daily USD cap | $20 | Hard kill-switch — no LLM-backed tool should be uncapped by default |
| 16 | Summary + run import | (display + y/N) | Last chance to review every choice; one keypress to commit |

A 5-step wizard would have to lump these into "everything else"
buckets — and lose every reviewer who picks `chroma` for the vector
store but then can't change which prompt family their refiner uses.

---

## Why also `--express`

90% of evaluating users don't have opinions yet. They want a
working install in three seconds so they can decide if the tool
matters. For them, `--express`:

- Reads `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `OPENROUTER_API_KEY`
  / etc. from env, picks the first one set, picks that provider's
  recommended model
- Picks every other default the wizard would pick on
  Enter-Enter-Enter (`bge-m3` + `bge-reranker-v2-m3` + `qdrant` +
  `hybrid` privacy + `normal` refine tier + `$20` daily cap)
- Writes config in ~3s, prints the per-conversation cost + daily
  cap, exits

A user who runs `--express`, evaluates throughline for an hour,
and decides to commit can then run `--reconfigure` to override any
of the 16 choices.

`--express` doesn't replace the wizard. It's the wizard's *fast
path* for users who don't need the wizard yet.

---

## Why also `--reconfigure`

Re-running the full 16-step wizard to change one decision is
hostile. `--reconfigure` lets the user pick a subset of steps to
re-run, preserves all other answers, and validates the result
before writing. Common cases:

- Switched providers? `--reconfigure --steps 4,5,8`
- Want to try `chroma` instead of `qdrant`? `--reconfigure --steps 3,7`
- Changed your mind on privacy tier? `--reconfigure --steps 6,7`

Behind the scenes: the wizard reads the current
`~/.throughline/config.toml`, masks the steps not in `--steps`,
runs only the requested ones, validates the merged config, writes.
No data loss; no zero state.

---

## Why also `--dry-run`

A wizard that writes config you can't preview is a wizard that
forces you to commit-then-undo. `--dry-run` walks the full
wizard (or `--express`, or `--reconfigure`), prints what would be
written, and exits. Zero side effects. Useful for:

- Sharing a config recipe with someone else (run with their env
  vars, screenshot the summary, paste-into-chat)
- Validating a config-as-code pipeline (CI runs `--dry-run` on a
  PR; if a step's prompt changes shape, CI fails before merge)
- Curiosity ("what does throughline default to on this machine?")

---

## UX engineering: T1 + T2 + T3 wave

The wizard pre-T1 was a numbered-input prompt loop. Functional;
not pleasant. The T1+T2+T3 wave (April 2026) layered three
modern-CLI affordances on top:

- **T1 — `questionary` arrow-key picker** for any step with a
  fixed option set. Highlight + descriptions + cyan accent. Falls
  back to legacy numbered input on non-TTY (CI / pytest / piped
  stdin) so headless installs still work, and an opt-out env var
  (`THROUGHLINE_LEGACY_UI=1`) for terminals where prompt_toolkit
  fights the parent shell (Windows mintty / some git-bash setups).
- **T2 — `rich.spinner`** during long operations (model load,
  cost scan, live refine preview). Spinner + live progress text +
  ETA. Hides the seconds where the wizard would otherwise look
  frozen.
- **T3 — Hierarchical summary tree at step 16.** The pre-T3
  summary was a 16-line key-value cascade; T3 groups it into 6
  sections (Provider · Backends · Privacy · Refine · Taxonomy ·
  Budget) with proper indentation. A user reviewing 16 choices in
  one screen can now scan in 5 seconds, not 30.

All three are auto-fallback-friendly. Pytest collection sees a
non-TTY, picks the legacy paths, runs deterministically.

---

## Validation: provider/key hard-block

Step 4 asks "which LLM provider?" Step 5 asks "which model?". A
naive wizard would write whatever the user picked and let the
daemon discover the first 401 at runtime.

The hard-block at step 4 + step 13 entry checks:

- Did the user pick a provider whose env var (e.g.
  `ANTHROPIC_API_KEY`) is set? If not, warn and require explicit
  `Continue anyway?` (defaults to NO).
- At step 13 (live preview), re-check before issuing the LLM call.
  Catch the case where the user changed providers in step 4 but
  hadn't actually exported the key.

Cost of catching it at step 4: 0.5s. Cost of catching it at first
real refine (after a 1000-conversation backfill): an hour of
"why didn't anything happen?" debugging + a daily-cap hit on the
wrong provider.

---

## Escape hatches

The wizard has explicit out-of-the-box paths so users with
unusual setups don't get cornered:

- **"Other" model option at every preset** — every provider's
  model list ends with `__OTHER__` which prompts a free-form
  string. Users can type whatever's in that provider's docs at
  the time of install (model lists drift faster than wizards
  update).
- **Generic OpenAI-compatible endpoint** as a 17th provider —
  `THROUGHLINE_LLM_URL` + `THROUGHLINE_LLM_API_KEY` covers any
  provider not in the preset table (LocalAI, vLLM, custom proxies,
  enterprise gateways).
- **Manual install path** in `docs/DEPLOYMENT.md` — every wizard
  step has its corresponding env var documented, so users who
  prefer hand-edited `.env` files (scripted ops, air-gapped, …)
  skip the wizard entirely.
- **`--reconfigure` + `--dry-run`** as recovery paths — any wrong
  decision is a `--reconfigure --steps N` away from being fixed,
  with `--dry-run` to preview the fix.

---

## Testing the choice space

A 16-step wizard with 5 average options per step has 5^16 =
~150 billion possible install combinations. We can't test all of
them. We can do better than testing one default path:

- **1-wise per provider** (`test_wizard_pairwise.py` + per-provider
  fixtures): every provider preset gets exercised at every step
  it can reach. Catches presets whose model lists don't match
  step 5's expected schema.
- **Pairwise (2-wise) covering array** (~185 tests): for every
  pair of decisions across the wizard, every value-combination is
  exercised at least once. Covers ~95% of the bug surface that
  would otherwise need exhaustive testing. Generated via a
  pairwise-coverage tool, then committed as fixed test cases for
  determinism.
- **Property-based wizard testing**: hypothesis-style tests that
  generate random valid wizard inputs, run the wizard end-to-end
  in `--dry-run`, and assert post-conditions (config validates,
  no missing required fields, no contradictions). Runs in the
  same suite as the unit tests.
- **`fixtures/v0_2_0/test_wizard_validation_warnings.py`** —
  invariants on the warnings system: no warning fires when its
  trigger condition is absent, every documented warning has a
  fix-line, etc.

The result: 800+ wizard-related tests in the regression suite,
all running in under 3 seconds (no real LLM calls; every call
mocked at the boundary).

---

## What this doc is not

- Not a user manual — for "how to use the wizard", see
  [`docs/DEPLOYMENT.md`](DEPLOYMENT.md) and the wizard's own
  printed help (`python install.py --help`).
- Not a defense of complexity — every choice point above can be
  argued. If a future reviewer reads this and disagrees, the
  decision *they* should make is documented in
  [`docs/DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md) (the wizard
  doesn't have its own entry there yet — adding one is a
  reasonable PR).
- Not a roadmap — what the wizard will look like in v0.3 + beyond
  is in [`ROADMAP.md`](../ROADMAP.md).

---

## See also

- [`docs/DEPLOYMENT.md`](DEPLOYMENT.md) — install walkthrough
- [`docs/ONBOARDING_DATA_IMPORT.md`](ONBOARDING_DATA_IMPORT.md) —
  step-by-step coverage of step 9 (the import flow), the deepest
  branch in the wizard
- [`throughline_cli/wizard.py`](../throughline_cli/wizard.py) —
  the actual implementation (~2,000 LOC)
- [`fixtures/v0_2_0/test_wizard_pairwise.py`](../fixtures/v0_2_0/test_wizard_pairwise.py)
  — the covering-array test
