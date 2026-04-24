# Prompts

This directory contains the **canonical prompts** used by the
Throughline pipeline. v0.2.x split prompts between two loader
styles:

1. **Loader-based prompts** (refiner + taxonomy deriver) live under
   `en/refiner.<tier>.<family>.md` and
   `en/taxonomy_deriver.<variant>.<family>.md`. Loaded at runtime
   via `throughline_cli.prompts.load_prompt()` with a
   family-fallback chain.
2. **Hardcoded-mirror prompts** (the legacy Filter + daemon
   prompts) live under `en/<name>.md`. The markdown is a
   documentation + review surface; the authoritative string is in
   the matching `.py` file's `**Used by:**` pointer.

---

## Contents

- [Loader-based prompts (refiner + taxonomy deriver)](#loader-based-prompts-refiner--taxonomy-deriver)
- [Hardcoded-mirror prompts (Filter + daemon legacy)](#hardcoded-mirror-prompts-filter--daemon-legacy)
- [Adding a new language](#adding-a-new-language)
- [Adding a new tier / family variant](#adding-a-new-tier--family-variant)
- [Fallback chain](#fallback-chain)
- [Testing conventions](#testing-conventions)

---

## Loader-based prompts (refiner + taxonomy deriver)

Eight refiner variants ship: **tier × family**.

| Tier | Claude family (XML tags) | Generic family (Markdown) |
|---|---|---|
| `skim` | `en/refiner.skim.claude.md` | `en/refiner.skim.generic.md` |
| `normal` | `en/refiner.normal.claude.md` | `en/refiner.normal.generic.md` |
| `deep` | `en/refiner.deep.claude.md` | `en/refiner.deep.generic.md` |
| `rag_optimized` | `en/refiner.rag_optimized.claude.md` | `en/refiner.rag_optimized.generic.md` |

Called as:

```python
from throughline_cli.prompts import load_prompt
body = load_prompt("refiner", variant="normal", family="claude")
```

The loader extracts the fenced-body block (the literal string
between the first ```…``` fence pair) and returns it. Files follow
a `# Title / front-matter / ---\n```\nBODY\n```\n--- / notes` shape
so the fenced block is the call-time string.

**Contract fields every refiner variant must expose:**
- `{valid_x}`, `{valid_y}`, `{valid_z}` format placeholders
- `primary_x` schema field (ROUTING INVARIANT, must match
  `{valid_x}`)
- `proposed_x_ideal` schema field (U27 observer consumes this;
  fall back to `primary_x` if the model can't produce it)
- The six-section body skeleton: `# Scene & Pain Point`,
  `# Core Knowledge & First Principles`,
  `# Detailed Execution Plan`, `# Pitfalls & Boundaries`,
  `# Insights & Mental Models`, `# Length Summary`
  (Skim + RAG-optimized variants are exempt from six sections;
  document your chosen shape in the variant's Notes.)
- Provenance tags: `user_stated`, `user_confirmed`,
  `llm_unverified`, `llm_speculation`
- Anti-pollution rule (don't invent facts)
- De-individualization rule (IPs → 192.0.2.10, home paths →
  /path/to/..., emails → user@example.com)

See `fixtures/v0_2_0/test_prompts.py` for the 97-test suite
enforcing these contracts across every variant.

**Taxonomy deriver** variants (`en/taxonomy_deriver.main.<family>.md`)
follow the same shape; see the existing `claude` + `generic` files.

---

## Hardcoded-mirror prompts (Filter + daemon legacy)

These pre-date the loader. The markdown is the review surface; the
`.py` file is authoritative. If they drift, the Python wins — file
an issue so the markdown catches up.

| File | Role | Called from |
|---|---|---|
| `en/recall_judge.md` | Decide `needs_rag` / `mode` / `aggregate` / `topic_shift` / `reformulated_query` per user turn | Filter inlet |
| `en/slice.md` | Carve a raw conversation into coherent knowledge slices | Daemon SLICE stage |
| `en/refine.md` | Turn one slice into a six-section knowledge card (JSON) | Daemon REFINE stage (pre-loader) |
| `en/route_domain.md` | Pick one top-level JD domain (10–90) for a refined card | Daemon DOMAIN stage |
| `en/route_subpath.md` | Pick a leaf subpath under a chosen domain; fallback-aware | Daemon SUBPATH stage |
| `en/ephemeral_judge.md` | Decide whether a short message is worth refining at all | Daemon pre-SLICE gate |
| `en/extension_judge.md` | Decide whether newly-appended messages are worth a re-refine | Daemon ExtensionGuard |
| `en/echo_judge.md` | Decide whether a slice is substantively new vs. an echo of top-1 | Daemon EchoGuard (grey zone) |

Each file carries a header like:

```
# <Prompt name>

**Used by:** `<path/to/file.py>` :: `<symbol>`
**Model:** `<default model>`
**Inputs:** `<placeholder1>`, `<placeholder2>`

---

<prompt body verbatim>

---

**Notes:**
- <any non-obvious behavior>
```

---

## Adding a new language

v0.2.x is English-only by design; `zh/` and friends are opt-in
community PRs. To ship a new language `xx`:

1. Create `prompts/xx/` mirroring the `en/` filename layout.
2. Translate each file's body, preserving:
   - **Every `{placeholder}`** exactly as-is (they're Python
     format-string slots).
   - **Section heading** forms used by downstream validators. For
     the six-section refiner skeleton, `daemon/refine_daemon.py ::
     _count_sections_complete()` grep-counts the English headings
     literally; a non-English translation must either keep them in
     English OR upstream a PR that makes `_count_sections_complete`
     accept localised headings.
   - **Schema fields** (`primary_x`, `form_y`, `z_axis`, etc.)
     stay English strings; only the *instructions* translate.
3. Add translation-specific tests under `fixtures/v0_2_0/` using the
   same shape as `test_prompts.py :: TestFamilyConsistency`.
4. Flip the wizard's language selector (step 4 adjacent — a future
   step that doesn't exist yet; discuss in
   [ROADMAP.md](../ROADMAP.md) before landing wizard surface area).

See `docs/CHINESE_STRIP_LOG.md` for what the original Chinese-first
codebase looked like and which constructs were hardest to
de-locale. It's the reference checklist for anyone doing the work
in reverse.

---

## Adding a new tier / family variant

Families are "prompt style buckets": Claude responds best to XML
tags; GPT + generic open-weights respond best to Markdown
headers; Gemini structured-output mode has its own quirks. Tiers
are quality/cost points: skim ($0.005/conv) → normal → deep
($0.20/conv) → rag_optimized (dense machine-only).

### To add a new **family** (e.g. `gemini` as a distinct variant
rather than alias to generic):

1. For each tier that should have a native Gemini variant, add
   `en/refiner.<tier>.gemini.md`. Minimum:
   `en/refiner.normal.gemini.md` (the default tier).
2. The loader's `FAMILY_FALLBACK` chain in `throughline_cli/prompts.py`
   already documents where the chain ends (always `generic`). Only
   touch it if you need a new non-terminal fallback.
3. Add the variant to `fixtures/v0_2_0/test_prompts.py ::
   TestFullTierFallbackBehaviour.test_every_family_x_variant_resolves`
   so it's covered by the parametrised matrix.
4. Wire the wizard's step 8 (`prompt_family`) to offer the new
   family if the user's step 5 provider uses it. `prompt_family`
   auto-derivation lives in `throughline_cli/wizard.py ::
   step_05_llm_provider`.

### To add a new **tier** (e.g. `ultra_skim` for batch-
flashcard generation):

1. Add `en/refiner.<tier>.claude.md` + `en/refiner.<tier>.generic.md`.
2. Add the tier to `throughline_cli/prompts.py ::
   available_variants()` coverage — the `test_full_tier_matrix_complete`
   test will flag any family that doesn't cover the new tier.
3. Wire `daemon/refine_daemon.py` to know how to pick / price the
   new tier. Update `throughline_cli/config.py :: WizardConfig.refine_tier`
   type annotation.
4. Add a dollar-cost estimate to `scripts/ingest_qdrant.py` if the
   wizard's step 11 "smart tier suggestion" should ever recommend
   it.

---

## Fallback chain

`throughline_cli/prompts.py :: FAMILY_FALLBACK` encodes how an
unknown or missing family routes:

```
claude  -> claude -> generic
gpt     -> gpt    -> generic
gemini  -> gemini -> generic
generic -> generic
<any other family name> -> generic
```

So `load_prompt("refiner", "normal", "mistral")` returns the
generic Markdown variant, not an error. Missing (name, variant)
combinations DO raise `FileNotFoundError` with the tried chain
listed — silent fallback would let a typo pick the wrong prompt.

---

## Testing conventions

All prompt-file contracts are enforced by
`fixtures/v0_2_0/test_prompts.py`:

- **Structural** — every variant loads, every variant has the
  `{valid_x}`/`{valid_y}`/`{valid_z}` placeholders, every variant
  has `primary_x` + `proposed_x_ideal` adjacent in the schema, the
  anti-pollution rule is present.
- **Family consistency** — Claude and generic variants of the same
  tier must preserve the same section headings, the same
  provenance tags, the same knowledge-identity values, and the
  same JSON schema fields. Only the wrapper differs.
- **Fallback** — every (family × tier) cell in the matrix must
  return a non-empty string (falling back to generic if needed).

Run `pytest fixtures/v0_2_0/test_prompts.py -q` before landing a
prompt change. If a new variant breaks one of the existing
contracts, the test message points at which invariant failed.

---

## Customising prompts without forking

Still the recommended path for major edits:

1. Fork the repo.
2. Edit the matching file under `prompts/en/`.
3. For hardcoded-mirror prompts, also edit the authoritative Python
   string (the `**Used by:**` pointer tells you where).
4. Run `pytest fixtures/v0_2_0/test_prompts.py` + the full Phase 6
   regression (`fixtures/phase6/`) to confirm schema parity.

Do **not** silently tweak tone while preserving the schema — many
downstream validators (card retention gate, cost gate, confidence
tier badges) assume specific fields and confidence ranges. See each
prompt's `**Notes:**` for the non-negotiable fields.
