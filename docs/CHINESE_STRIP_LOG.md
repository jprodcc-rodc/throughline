# Chinese-Removal Log

> **Purpose:** this file is the authoritative record of every Chinese-language construct removed or translated during the open-source migration. Phase 6 English-only regression testing uses it as the test scope.
>
> **Why it exists:** the upstream private codebase was written for a Chinese-speaking primary user. Removing Chinese is not just a translation — it strips entire branches of regex, tokenizer logic, and judge prompts that had no English counterpart. Any "unexpected" behavior when an English user runs the open-source build is likely here.

---

## Conventions

Each entry uses this format:

```
### <source_file>:<symbol_or_lineno>

- **What it was:** brief description in English
- **Why it existed:** functional purpose
- **Removal mode:** STRIPPED | TRANSLATED | ENGLISH_ONLY_REWRITE | GUARDED
- **English replacement:** what (if anything) takes its place
- **Phase 6 risk:** LOW | MEDIUM | HIGH — likelihood an English user hits a different code path because this was removed
- **Regression fixture:** path to test that exercises this in Phase 6, if any
```

### Removal modes — definitions

| Mode | Meaning |
|---|---|
| `STRIPPED` | Deleted outright; no English equivalent exists or needed |
| `TRANSLATED` | 1:1 English translation, same semantics |
| `ENGLISH_ONLY_REWRITE` | Replaced with an English-only version that may behave differently in edge cases |
| `GUARDED` | Kept the Chinese code, but wrapped in a CJK-detection guard so it only triggers on Chinese input |

### Phase 6 risk levels

| Risk | Meaning |
|---|---|
| `LOW` | Translation-only; semantics preserved |
| `MEDIUM` | English path is different structure (e.g. English pronouns vs Chinese bare pronouns) but well-exercised in tests |
| `HIGH` | English path is untested or known to diverge; Phase 6 **must** add a fixture |

---

## Phase 2 · Filter (`openwebui_rag_tool.py` → `filter/openwebui_filter.py`)

<!-- filled during Phase 2 migration -->

_Pending — Phase 2 in progress._

---

## Phase 3 · Daemon + RAG server + Ingest

<!-- filled during Phase 3 migration -->

_Pending._

---

## Phase 4 · Prompts + config

<!-- filled during Phase 4 extraction -->

_Pending._

---

## Phase 5 · Docs

<!-- filled during Phase 5 sanitization -->

_Pending._

---

## Phase 6 · English-only Regression Scope (derived)

Once Phases 2-5 are complete, the `HIGH` risk rows above define the minimum regression matrix Phase 6 must exercise in English. This section lists the resulting test plan:

_Derived at end of Phase 5._
