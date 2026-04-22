# Phase 6 Overnight Regression Report

**Run date:** 2026-04-23 · **Total live-API cost:** ~$0.44 · **Sessions:** 1 (spanning user's sleep)

## TL;DR

All 5 Phase 6 harnesses completed successfully. No critical bugs, 1 fix committed (cheap-gate `thanks` ack missing), 2 accepted English-tone limitations documented for v0.1.0.

| Harness | Scope | Result | Cost |
|---|---|---|---|
| **H1** RecallJudge classification | 48 EN turns × real Haiku 4.5 | **45/48 PASS (93.8%)** | $0.26 |
| **H2** Cheap-gate short-turn | 20 EN turns offline | **10/20 MATCH + 10 xfail** | $0 |
| **H3 code** Injection wrapper | 9 offline assertions | **9/9 PASS** | $0 |
| **H3 Haiku** Injection resistance | 31 EN turns × real Haiku 4.5 | **31/31 PASS (100%)** | $0.17 |
| **H4** Refiner prompt regression | 8 EN fixtures × real Sonnet 4.6 (Claude Code subagent) | **15/16 PASS (93.8%)** | $0 |
| **Bonus:** inlet-shape fuzz | 17 malformed-body cases | **0 bugs** | $0 |

## What shipped this session

**6 commits on the `throughline` repo `main` branch** (public, `jprodcc-rodc/throughline`):

- `bac196a` — Phase 6 H1 fixture + runner + results + analysis
- `7a0f936` — Phase 6 H2 + H3 code + cheap-gate `thanks` fix + session state
- `8ab61dd` — Phase 6 H3 + H4 complete, dual-layer injection guard + refiner regression
- (pending) — CHINESE_STRIP_LOG + README + fuzz probe + overnight report

**Test artifacts:**
- `fixtures/phase6/*.jsonl` — 4 fixture files (136 total cases)
- `fixtures/phase6/run_h*.py` + `retry_h3_errors.py` — 4 runners + 1 retry tool
- `fixtures/phase6/test_phase6.py` — pytest wrapper, 21 passed + 10 xfailed
- `fixtures/phase6/h*_results.json` / `h4_results.md` — per-harness raw results
- `fixtures/phase6/H*_ANALYSIS.md` — 3 narrative deep-dives
- `fixtures/phase6/SESSION_STATE.md` — cross-session continuity anchor
- `fixtures/phase6/fuzz_inlet.py` — ported shape-fuzz probe

**Code changes:**
- `filter/openwebui_filter.py:_NOISE_RE` — added `thanks | thank you | thx | ty | cheers` (ack-noise gap found by H2)

**Docs updates:**
- `docs/CHINESE_STRIP_LOG.md` — populated H1/H2/H3/H4 Phase 6 results into the corresponding risk rows
- `README.md` — added Phase 6 regression section with live result table

## Known English-only limitations (accepted for v0.1.0)

1. **Brainstorm mode drift** — Haiku 4.5 classifies English "should we X?" / "what if Y?" / "give me N ideas" as `mode=native` instead of `mode=brainstorm`. Users must use `/recall` slash for explicit RAG on brainstormy inputs. No data corruption, no privacy issue — just missed auto-recall. Fix options deferred to Phase 7: add English few-shot examples, or add `PROMPT_LANG` valve per user choice. (H1 FAILs B01/B02/B03)

2. **Bare-pronoun cheap-gate absent** — English build deliberately strips the Chinese `_BARE_PRONOUN_RE` (documented in `openwebui_filter.py:760-764`). First-turn "it" / "that one" / "what about it" inputs fall through to the Haiku judge instead of being cheap-skipped. Cost: ~$0.003/turn on short pronoun-only inputs. Context-backed pronouns (second-turn+) route correctly because the judge sees the history. (H2 FTs 01-10 marked xfail in pytest)

## Fix landed this session

- **Cheap-gate `thanks` ack missing** — the English `_NOISE_RE` rewrite dropped `thanks` and its variants. Clearly ack-noise, no ambiguity. Added `thanks | thank you | thx | ty | cheers` back. (Committed in `7a0f936`.)

## What wasn't tested (acceptable gaps)

- Slice pre-stage (cuts long raw conversations into topic slices — covered only implicitly by H4 refiner test)
- Subpath router second stage (route_domain → subpath inside the chosen domain)
- Full daemon end-to-end loop (requires real Obsidian vault + Qdrant + bge-m3 models)
- Ephemeral judge on volume — only 1 borderline EDGE01 sample in H4
- `--real` variant of the inlet fuzz (adversarial content appended to live queries) — overlaps with H3 Haiku-side; skipped to avoid double-coverage
- `bug_probes/invariant_sweep.py` + `replay_haiku_judge_variance.py` — private-repo probes, not ported this session (Phase 7)

## Credential handling

- One OpenRouter key rotation performed mid-session (Phase -1 precaution, unrelated to Phase 6 work)
- Key used via pure-file-flow (Read from `C:\Users\Jprod\.tl_key`, inlined into single bash invocation, `rm -f` on same command)
- Key remains in assistant context from the Read tool output but was never typed in chat
- User may re-rotate post-phase at their discretion

## Next session pickup

1. **Read `fixtures/phase6/SESSION_STATE.md` FIRST** — the continuity anchor has current state, key paths, fixture-calibration history (do not re-debug).
2. Remaining P0 items before `v0.1.0` tag:
   - Private-mirror sync: cherry-pick `[mech]`-class commits from this session back into `S:\syncthing\obsidian_python` per the workflow in `docs/THROUGHLINE_PHASE6_RISKS.md`
   - Phase 7 dogfooding: invite 1-2 alpha users to try clean-env install
3. Phase 8: `v0.1.0` tag + Show HN post + npm-style release notes

## Phase 6 verdict

**🟢 Ship-clean for v0.1.0.** All HIGH-risk entries in `docs/CHINESE_STRIP_LOG.md` now have concrete regression results populated. Two accepted English-tone limitations are documented in README + CHINESE_STRIP_LOG so users can find them. One obvious bug was found and fixed in the same session.

Cost to reach this state: **~$0.44 live API + 1 Sonnet-subagent subscription invocation**. Cheaper than a single CI run on most commercial test harnesses.
