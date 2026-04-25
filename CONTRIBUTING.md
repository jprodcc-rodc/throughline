# Contributing

Thanks for the interest. This is a personal project first, open-source
second — the reference implementation runs 24/7 against the maintainer's
real vault, and changes need to not break that. Friendly PRs always
welcome; please follow the rough flow below so we can land them quickly.

---

## Quick reference

| You want to | Do this |
|---|---|
| Report a bug | Open an [issue](https://github.com/jprodcc-rodc/throughline/issues/new?template=bug_report.md) |
| Suggest a feature | Open a [feature request](https://github.com/jprodcc-rodc/throughline/issues/new?template=feature_request.md) |
| Ask a design question | Start a [Discussion](https://github.com/jprodcc-rodc/throughline/discussions) |
| Find a starter PR | Filter for [`good first issue`](https://github.com/jprodcc-rodc/throughline/labels/good%20first%20issue) |
| Privately disclose a security issue | See [`SECURITY.md`](SECURITY.md) |
| See where the project is headed | Read [`ROADMAP.md`](ROADMAP.md) |

---

## Dev setup

```bash
git clone https://github.com/jprodcc-rodc/throughline.git
cd throughline
python -m venv .venv
source .venv/bin/activate                     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install pytest ruff                       # test + lint extras
```

Verify it works:

```bash
pytest fixtures/ -q                           # full suite, ~15-30s
ruff check --select F,E9 .                    # linter (CI runs the same)
python -m throughline_cli doctor              # health check
```

The full suite has ~590 tests and stays under a minute on a modern
laptop. CI runs the same pytest invocation on Python 3.11 and 3.12.

### Optional: pre-commit hooks

Install once and every `git commit` runs the same checks CI runs,
catching lint failures before you push:

```bash
pip install pre-commit
pre-commit install
```

Skip with `git commit --no-verify` when you genuinely need to bypass
(CI still runs). See `.pre-commit-config.yaml` for the hook list.

### Without the heavy optional deps

You can skip `torch`, `transformers`, `chromadb`, and `openai` if
you're only working on the wizard / daemon / taxonomy pieces.
Their imports are lazy; the test suite mocks every call site that
would touch them.

```bash
# Minimal install — what CI uses
pip install fastapi pydantic pyyaml watchdog rich markdownify pytest ruff
```

---

## Claiming an issue

1. Comment on the issue saying you'd like to take it.
2. The maintainer will assign it to you (usually within a day).
3. Open a draft PR early — even with a stub commit. Easier to course-
   correct early than to rewrite later.

If a `good first issue` ticket has been open >2 weeks unassigned,
just claim it.

---

## Commit / PR conventions

### Commit messages

Conventional-Commits-ish, but with a U-item prefix for in-roadmap work:

```
<type>(<scope>): <imperative subject ≤ 70 chars>

<wrapped body explaining WHY and any trade-offs.
 reference issue numbers as 'closes #42'.>
```

Common types: `fix`, `feat`, `chore`, `docs`, `test`, `ux`, `wire`.
Special: a new U-item ships as `U<N>: <subject>` (see `git log` for
historical examples — `U27.4: throughline_cli taxonomy`, `U21:
BaseVectorStore abstraction`).

### Pull requests

Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md). Keep:

- **summary** — one or two sentences
- **test plan** — copy-paste of what you ran (not just intent)
- **related** — `closes #N` if applicable

CI must be green before merge. The required checks are
`pytest (3.11)`, `pytest (3.12)`, and `lint (ruff)` — branch protection
enforces this.

---

## Scope guidance

**What belongs here:**

- Filter / daemon / RAG-server improvements
- New RecallJudge prompt variants with test fixtures
- New backends for the U12 / U20 / U21 abstractions
  (embedder / reranker / vector store)
- Adapters for other chat frontends or export formats
- Localized prompt files under `prompts/<lang>/`
- UX polish in the wizard or `throughline_cli` subcommands
- Tests pinning behaviour the suite missed

**What doesn't:**

- Personal vault content (keep that in your own repo)
- Hardcoded personas or identities in prompts (must be swappable
  via config)
- Hosted SaaS hooks (throughline is local-first; see `ROADMAP.md`
  §"Out of scope")

---

## House style

- **Code formatting** is enforced by `ruff check --select F,E9` only.
  No black / isort / autoformat-on-save required. We may widen the
  rule set in v0.3 if the codebase warrants it.
- **Type hints** encouraged but not required outside public function
  signatures. mypy is not run in CI yet.
- **Comments** explain *why*, not *what*. Prefer one short line over
  a multi-paragraph docstring. Don't restate code.
- **Tests** live under `fixtures/v0_2_0/` (current release line).
  Phase-6-era tests under `fixtures/phase6/` are frozen audit fixtures;
  don't extend them.
- **Path strings** use forward slashes throughout — Windows is a tier-1
  target and the daemon's `_norm_path` collapses backslashes already.

---

## Combinatorial-config testing strategy

The wizard exposes ~9 axes (mission, vector_db, llm_provider,
embedder, reranker, privacy, refine_tier, card_structure,
taxonomy) with a full Cartesian of ~5.6 million combinations
across the user-pickable values, more if you count the 80+
provider-scoped models. Running all of them is impossible —
running ad-hoc samples leaves interaction bugs (provider X +
reranker Y) uncaught. The repo uses a four-layer strategy:

**Layer 1 — 1-wise (each-choice) coverage.** Every value of
every axis runs through the wizard at least once.
Lives in `fixtures/v0_2_0/test_wizard_combinations.py`. ~105 tests.
Catches "this enum value isn't wired to anything" bugs (we
recently fixed step 7 silently writing 4 broken embedder/reranker
keys this way).

**Layer 2 — 2-wise (pairwise) covering array.** A greedy
covering-array generator builds ~96 cases such that every
(axis_i_value, axis_j_value) pair fires at least once across
all axis pairs. Empirically catches 70-90% of real-world
combinatorial bugs (Kuhn et al., NIST 2004).
Lives in `fixtures/v0_2_0/test_wizard_pairwise.py`. ~175 tests
including a meta-check that the array is actually a valid covering
array (so a bug in the generator can't silently shrink coverage).

**Layer 3 — Property-based / randomized.** Each CI run picks 30
random configs from the full Cartesian and walks the wizard. Seed
is fixed per session; failing CI prints `PROPERTY_TEST_SEED=N` so
the contributor can reproduce locally. Set
`PROPERTY_TEST_ITERATIONS=1000` for a long-form fuzz session.
Lives in `fixtures/v0_2_0/test_wizard_property.py`.

**Layer 4 — Schema/contract enforcement.** Every wizard pick key
that lands in `config.toml` MUST resolve through its registry
(`create_vector_store / create_embedder / create_reranker /
get_preset`). The contract test in
`fixtures/v0_2_0/test_wizard_keys_resolve.py` enumerates the keys
and pins them to the registries — adding a new option that
isn't wired up fails CI.

**If you add a new wizard option:** update the matching axis in
`_AXES` (pairwise) and the `_BASE_ANSWERS` dict
(combinations) and verify the contract test still passes. The
test infrastructure walks the whole 4-layer pyramid for free
once the axis is declared.

**If you change a registry:** the dynamic schema validator (added
to `config.validate()`, exercised by `test_doc_drift.py`) verifies
that every registered provider/backend round-trips through the
schema. README/DEPLOYMENT prose claims (e.g. "13 doctor checks")
are pinned to the actual code by the same drift test.

---

## Code of conduct

See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Short version: be
decent, critique code not people, and stop when asked. Reports go
through a private security advisory ([`SECURITY.md`](SECURITY.md)).
