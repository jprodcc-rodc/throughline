# Phase 6 Session State

**Purpose:** Cross-session continuity anchor. If the conversation is summarized or a new session opens, read this file FIRST to pick up exactly where the last session left off. This is the single source of truth for Phase 6 progress.

**Last updated:** 2026-04-23 (overnight batch)

---

## Where we are

Phase 6 = **English-only regression** for the open-source `throughline` repo (rewrite of the private Chinese-speaking RODC flywheel). Every Chinese artifact either stripped or rewritten; now validating the English rewrites don't regress behavior.

| Harness | Scope | Status | File(s) |
|---|---|---|---|
| **H1** | RecallJudge EN classification drift (48 cases × real Haiku 4.5) | ✅ **45/48 PASS (93.8%)** · 3 brainstorm drift accepted | `run_h1.py` · `recall_judge_en.jsonl` · `h1_results.json` · `H1_ANALYSIS.md` |
| **H2** | Cheap-gate short-turn behavior (20 cases offline) | ✅ **10/20 MATCH** · 10 gaps = intentional bare-pronoun regex strip (accepted as v0.1.0 cost) | `run_h2.py` · `pronouns_en.jsonl` · `h2_results.json` |
| **H3 code** | Card-injection wrapper + truncation (9 CD/LN cases offline) | ✅ **9/9 PASS** | `run_h3_code.py` · `h3_code_results.json` |
| **H3 Haiku** | Injection/PII/roleplay resistance (31 cases × real Haiku 4.5) | ✅ **31/31 PASS (100%)** after retry of 2 network timeouts · $0.17 | `run_h3_haiku.py` · `retry_h3_errors.py` · `h3_haiku_results.json` · `H3_ANALYSIS.md` |
| **H4** | 4 refiner prompts on EN raws (8 sampled cases × real Sonnet 4.6) | ✅ **15/16 PASS (93.8%)** · 1 WARN on personal/universal boundary, zero structural failures | `refiner_en.jsonl` · `h4_results.md` |

## Commits on this branch

- `bac196a` — Phase 6 H1 fixture + runner + results + analysis (pushed)
- pending: H2 + H3 code + thanks fix + SESSION_STATE (staged)

## Key paths

| What | Where |
|---|---|
| Public repo (throughline) | `C:\Users\Jprod\code\throughline` |
| Private mirror (obsidian_python) | `S:\syncthing\obsidian_python` |
| Phase 6 fixtures + runners | `throughline/fixtures/phase6/` |
| Shipped Filter | `throughline/filter/openwebui_filter.py` |
| Shipped 8 EN prompts | `throughline/prompts/en/` |
| Chinese-strip log (HIGH-risk roll-up) | `throughline/docs/CHINESE_STRIP_LOG.md` |
| Phase 6 checklist (public) | `throughline/docs/PHASE_6_CHECKLIST.md` |
| Phase 6 risk mirror (private) | `S:\syncthing\obsidian_python\docs\THROUGHLINE_PHASE6_RISKS.md` |

## Credentials handling

- OpenRouter key rotated once in previous session. Current key visible in my context from a Read tool call on `C:\Users\Jprod\.tl_key` (file deleted after use). User's preference: use it for remaining Phase 6 runs without another rotation; user can re-rotate post-phase if desired.
- **Rule for next session:** if the key in Filter code history differs from the one in valves, user has rotated. Do NOT inline keys in user-visible commands; prefer `$env:OPENAI_API_KEY` via launchd/shell profile or pure-file-flow via `C:\Users\Jprod\.tl_key` with immediate `rm` after.

## Fixture calibration history (important — do not re-debug)

H1 went through two fixture versions because the initial fixture confused display-label `general` with JSON-value `auto`. Root-cause resolved. Calibrations per filter.py few-shot:

- **Line 1088-89:** no-anchor generic definition → `native`
- **Line 1091:** should-I/what-if (no anchor) → `brainstorm`
- **Line 1092:** explicit "decided …" → `decision`
- **Line 1094:** proxy-person ("my friend …") → `native`
- **Line 1095:** meta-self ("what's your …") → `native`

## Known English-only behavior gaps (accepted for v0.1.0)

1. **Brainstorm drift** — English "should we / what if / give me N ideas" classified as `native` instead of `brainstorm` by Haiku. Users must use `/recall` for explicit RAG. Ship as known limitation. (H1 B01/B02/B03)
2. **Bare-pronoun cheap-gate absent** — "it" / "that one" / "what about it" as first-turn inputs hit Haiku instead of being cheap-gated. Cost ~$0.003/turn. (H2 FT01-FT10)
3. **Thanks fix applied** — added "thanks / thank you / thx / ty / cheers" to `_NOISE_RE`. (filter/openwebui_filter.py:740-741)

## Pending work (overnight batch)

1. ✅ H3 Haiku-side batch (31/31 PASS · $0.17)
2. ✅ H4 Sonnet subagent (15/16 PASS, 1 WARN)
3. ✅ Pytest wrappers (`test_phase6.py`, 21 passed + 10 xfailed)
4. EN fuzz probe pass (translate `bug_probes/fuzz_filter_inlet.py` from private repo)
5. README Phase 6 public results section
6. Private mirror `[mech]`-prefix commits back to obsidian_python
7. Update `docs/CHINESE_STRIP_LOG.md` with H2/H3/H4 results
8. Final `PHASE6_OVERNIGHT_REPORT.md`

## Next session quick-start

```bash
# 1. Read this file first
# 2. Check background jobs
cd C:\Users\Jprod\code\throughline
ls fixtures/phase6/h3_haiku_output.log fixtures/phase6/h4_results.md
git log --oneline -10

# 3. Pending tasks — read `docs/PHASE_6_CHECKLIST.md` for remaining gates
```

## Phase roadmap ahead

- **Phase 6 (now):** Regression harnesses + results documented
- **Phase 7:** Private collaborator dogfooding (invite 1-2 alpha users)
- **Phase 8:** Public release v0.1.0 + HN Show post

---

_If reading this is the first thing you do in a new session: don't redo the fixture calibration — it's already correct. Start by checking background job outputs (H3 Haiku + H4 Sonnet) and continuing the overnight batch checklist above._
