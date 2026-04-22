# Phase 6 H1: RecallJudge English Classification Drift — Analysis

**Run:** 2026-04-23 · real Haiku 4.5 · 48 cases · **45/48 PASS (93.8%)** · 0 errors · $0.2642

System prompt: 18048 chars (shipped `_RECALL_JUDGE_SYSTEM_PROMPT` extracted from `filter/openwebui_filter.py`).

## Result by category

| Category | Pass rate | Notes |
|---|---|---|
| Noise / meta / self (N/M) | 11/11 | All correctly `native`, no RAG. |
| Generic (G) | 10/10 | Incl. 3 no-anchor cases (G01/G04/G07) correctly judged `native`. |
| Brainstorm (B) | 1/4 | **Drift** — see below. |
| Decision (D) | 3/3 | Explicit decisions, slash, and goal all land correctly. |
| Aggregate (A) | 6/6 | Incl. negative (A06) — specific query not flagged aggregate. |
| Topic shift (T) | 3/3 | Anchor shift, out-of-scope shift, and continuation all correct. |
| Pronoun (P) | 3/3 | All recognized as referring to prior context. |
| Proxy person (PX) | 2/2 | "my friend" / "a colleague" correctly downgrade to native. |
| Casual (C) | 3/3 | |
| Fail-safe (F) | 3/3 | Injection attempts and empty input handled safely. |

## 3 FAILs — all brainstorm mode drift

| ID | Query | Got | Expected | Notes |
|---|---|---|---|---|
| B01 | should we A/B test two landing page copies or three | native (no RAG) | brainstorm (RAG) | Should-I tone per filter.py:1091 few-shot. |
| B02 | what if we renamed the product to something more memorable | native | brainstorm | What-if tone per same few-shot. |
| B03 | give me 10 tagline ideas for throughline | native | brainstorm | Creative-generation. |

**Root cause (hypothesis):** Haiku 4.5 in English reads "should we" / "what if" / "give me N ideas" as conversational/native rather than as RAG-backed brainstorm. The Chinese few-shot examples (`"应该不应该..."`, `"如果...呢"`) may not transfer symmetrically to English tone markers.

**Impact:** Low for v0.1.0 open source.
- User falls through to `mode=native` → no RAG injection, model answers directly from own reasoning.
- No wrong injection, no privacy leak, no crash.
- The cost is *missed* RAG on brainstorm-flavored questions — user would need to explicitly use `/recall` if they want past notes pulled in.

**Mitigation options (not for v0.1.0):**
1. Add English few-shot examples to `_RECALL_JUDGE_SYSTEM_PROMPT` covering "should we / what if / give me N ideas" → `brainstorm`.
2. Document in README that brainstorm auto-detection is Chinese-tuned; English users should use `/recall` for explicit RAG.
3. Post-v0.1.0 feedback loop: collect real English brainstorm turns, measure drift, tune prompt.

**Decision:** Accept as known limitation for Phase 6 ship. Log in `docs/CHINESE_STRIP_LOG.md` HIGH-risk row H1.

## Calibration history

- **v1 fixture (51 cases):** 16/51 PASS (31.4%). Root cause: fixture confused JSON `mode` field with display label — wrote `"general"` where JSON expects `"auto"`; several cases mis-specified decision/proxy-person/no-anchor semantics against filter.py:1083-1095 few-shot.
- **v2 fixture (48 cases):** 45/48 (93.8%). Removed 2 pronoun cases (P03/P04) — cheap gate pre-empts the judge for those, they belong in H2 bare-pronoun harness. Calibrated all mode labels to JSON values. Strengthened B01/B02 to explicit should-I/what-if tone, A04 to stronger aggregate signal.

## Fixture files

- `recall_judge_en.jsonl` — 48 calibrated cases
- `run_h1.py` — OpenRouter runner, temp=0, max_tokens=500, 15s timeout
- `h1_results.json` — per-case verdict + usage + latency
- `h1_v2_output.log` — live console output
