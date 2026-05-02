# `#claim-extraction` — Implementation Plan

> **Status (2026-05-02 evening, post-v3.1):** v1.7 — Ship gate REDEFINED per Rodc + External Opus directive after v3.1 result. v3.1 (concern ADDITIONAL RULES + Examples 7+8 + LLM-judge fallback) hit overall 78.5% PASS / hallucinations 6/256 fields (effectively solved) but per-field recall/precision still under v1.3 strict gates because **the eval ground truth itself is over-specific** — concern field uses single-string canonical answers ("family financial stability if I quit") that miss equally-correct paraphrases ("losing income"). Path forward (path "iv"): re-label 64 EN cases concern field as `list[str]` of acceptable variants + new ship gate (recall ≥60% / precision ≥70% / hallucination rate ≤8% per field, plus chitchat FP ≤5% + overall ≥75% = 14 conditions). NOT lower-the-gate dishonesty; NOT v4 prompt diminishing returns; the real fix is honest ground truth. Runner now supports `expected: str | list[str]` (multi-variant; first match wins). v1.7 status preserved across deliveries.
> **v1.6 (2026-05-02 evening, post-rebalance):** Eval rebalance applied (64 EN / 16 ZH / 0 mixed); few-shot 4 EN / 2 ZH; runner per-language metrics; parse_4field fix.
>
> **v1.5 (2026-05-02 evening, pre-rebalance):** Eval gate decision suspended pending eval rebalance. v2 prompt eval (Haiku 4.5, 80 cases) FAIL targets (overall 64.1% vs 70% target; hope/topic/sparse regressions). Rodc surfaced critical context: **Rodix launches English**; the 80-case eval was 65% 中文 / 25% English (Chinese-primary per `_meta.language_mix`) and v2 few-shot was 6/6 Chinese. Eval metrics calibrated on 中文 did NOT reflect English production.
> v1.4 (2026-05-02 afternoon): Tasks 1-14 implementer DONE; eval gate FAIL on nvidia free (33.8% overall, hope recall 22%, API fail 25%) → Rodc directive (a)+(d): Step 1 isolation eval on Haiku 4.5, Step 2 split-route ship / prompt rewrite. Step 1 result: API fails 25%→1.25% (provider was unstable) but overall 33.8%→61.3% with hope recall 22%→65% — directionally improved but still gate-FAIL. Step 2 path picked = (b) prompt rewrite (per directive: hope <70% = schema/prompt issue). Added P2 follow-up for Task 14 log-grep verification at Rodc dogfood.
> v1.3 (2026-05-01): Rodc + 外部 Opus reviewed, 4 push backs incorporated, approved for dispatch. Implementer prerequisite: #intent-classifier eval gate GREEN (landed 2026-05-02 92% / 97.5% / 100% / 88%).
> **For agentic workers:** Use `superpowers:test-driven-development` per task. Then `superpowers:subagent-driven-development` extended with `docs/superpowers/skills/scenario-verification.md`.
> **App/ gitignored** — `app/shared/extraction/` + `app/web/server.py` + `app/web/static/app.js` modifications do NOT go to git. Skip the per-task `Commit ...` lines for those files. `fixtures/` artifacts (eval set + runner) DO commit.

**Goal:** Implement post-chat hook that triggers LLM-based 4-field claim extraction (主题 / 忧虑 / 希望 / 问题) on user+AI message pair, **gated by `#intent-classifier` returning THOUGHTFUL**. Persist to claims table. Replace `#8` placeholder stub with real LLM output. **Done 标准:Vault badge 增长在 alpha 测试中可观察 (per IA-C cascade caveat) + asymmetric accuracy gate met.**

**Architecture:**

1. **Trigger gate** — `#intent-classifier` (already wired into `/api/chat` post Wave 1b) returns `IntentClass`. Extraction enqueues ONLY when `intent == THOUGHTFUL` (covers low-confidence fallback automatically since fallback overrides class to thoughtful). chitchat / factual classifications skip extraction entirely.
2. **Background queue** — clone of existing `EmbedQueue` shape from `app/shared/embeddings/cache.py`. Bounded thread + work queue + dropped-task counter. Doesn't block the chat response.
3. **LLM extractor** — wrapper that builds a 4-field prompt, calls `_resolve_llm_config()` provider, parses JSON defensively (same nvidia-model lessons as classifier: `max_tokens >= 3000`, no `response_format: json_object`).
4. **Persistence** — existing `app/shared/storage_py/claim_adapter.py`; verify 4-field schema is supported (extend if needed via additive migration).
5. **Frontend** — `app.js` polls `GET /api/claim/by_message/{message_id}` (1s interval, 5s timeout) after AI reply renders; on success swaps placeholder card with real fields.

**Hard dependency:** `#intent-classifier` MUST have its asymmetric accuracy gate met (or Rodc-signed-off temporary threshold) before this plan dispatches. Reason: extraction is gated by classifier output; if classifier is unreliable, extraction either floods (if classifier over-routes thoughtful) or starves (if it under-routes). Eval gate the upstream first.

**Tech Stack:** Python · `_resolve_llm_config` (same as classifier) · existing `claim_adapter.py` · background thread queue (clone of `EmbedQueue`) · async polling endpoint

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | Backend feature — invisible. Visible signal:Vault tab badge increments + `#8` Card with Promise renders real fields. |
| 产品策略假设 | Vault 增长 = brand 信任建立的核心机制. Claim extraction 不工作 = IA-C "Top Tabs" 退化为装饰 = 产品定位空喊. P0 优先级反映这个判断. |
| 适合 / 不适合 | **适合**: 全部用户 — 这是 P0 必做,无 user segment 选择. **不适合**: 极简洁癖用户(他们不会用 [PRODUCT_NAME])— 不在产品 target. |
| Trade-off | + enable see→trust→verify 完整 aha + Vault badge 实可观察 / − extra LLM call per message($cost+latency)/ extraction 失败 cascade 下游`#8`/`#3a`/`#9b`全废 |
| 最大风险 | LLM extraction 准确率低 → 4 字段抽错 → 用户看到 `#8` 显示无意义内容 → 信任崩.**缓解**:eval harness(reuse existing fixtures/v0_2_0/eval pipeline)在 launch 前跑;`#recall-quality` P1 接续校准. |

## Ambiguity flag

✓ **无 ambiguity** — Rodc + Opus review pre-baked all decision points into v1.2:

Locked decisions:
- **Extractor implementation**: NEW wrapper in `app/shared/extraction/` (NOT reuse `mcp_server.llm_extractor` — per memory rule "work in app/, don't modify root throughline core"). Same `_resolve_llm_config()` provider plumbing as classifier.
- **Background queue**: clone of existing `EmbedQueue` shape (battle-tested with shutdown drain semantics on Windows).
- **Dev model**: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (matches classifier + chat — single LLM provider stack at LAN dev).
- **Production model**: **TBD Wave 3** (consistent with `#intent-classifier` v1.3 — defer pick until dogfood telemetry exists). NOT a blocker.
- **Trigger gate**: `intent == THOUGHTFUL` from `#intent-classifier` (single check; fallback bias already routes ambiguous cases to thoughtful).
- **Sync vs async**: **async polling** — extraction does NOT block `/api/chat` response. Frontend polls `GET /api/claim/by_message/{id}` 1s interval, 5s timeout. Reason: extraction LLM call is ~2s; doubling chat round-trip is unacceptable.

## Dev mode + asymmetric accuracy gate (v1.2 — mirrors `#intent-classifier` rigor)

**Dev mode**(`RODIX_DEV=1`):
- Extractor uses dev model (nvidia free)
- No env-var seam yet (Wave 3 introduces if needed)

**Production mode**: TBD Wave 3.

**Asymmetric accuracy gate** (v1.3 recalibrated per Opus push back 1 — error cost asymmetry runs BOTH ways: missing fields = product feels dumb / **hallucinated fields = trust collapses**):

| Field | Recall | Precision | Reasoning |
|---|---|---|---|
| `topic` | **≥ 90%** | **≥ 80%** | Most user-noticeable miss; can be slightly over-eager since topic is the anchoring frame |
| `concern` | **≥ 80%** | **≥ 85%** | Hallucinating a "worry the user didn't express" is the trust killer — precision matters more than recall here |
| `hope` | **≥ 80%** | **≥ 85%** | Hopes have explicit verbal markers (`我想` / `希望` / `期望` / `I want` / `aspire`) — if extractor can't catch them, it's a prompt failure; over-extraction (false hopes) feels patronizing |
| `question` | **≥ 75%** | **≥ 80%** | Often implicit but is the **active-recall trigger primitive** — a missed question = recall hook bleed; over-extracted question = noise |
| `chitchat` (false positive) | rate **≤ 5%** | — | Any non-null field on chitchat input = false positive (user gets a junk Card) |
| Overall field accuracy | **≥ 75%** | — | Per-field exact match across all 4 × all 80 cases (320 grades) |

**Why precision gates were added**: a recall-only gate lets the extractor "play it safe" by hallucinating fields whenever the LLM is unsure — high recall, low quality. Users seeing "concerns I never expressed" or "hopes I never voiced" in their Vault is the fastest path to trust collapse for a memory product. Precision gates force the extractor to **leave fields null when in doubt** (matching spec §5.5 edge case 1: 缺字段不硬塞).

**Eval set** (v1.3 push back 2 — bumped 60 → **80 cases** to cover production-realistic boundary distribution):

Existing `fixtures/v0_2_0/eval/claim_extraction_cases.json` has 14 cases across 5 categories (career / relationships / technical / abstract / chitchat). Extend to **80 total**:

- **60 core cases** (Task 11 base) across the 5 existing categories — extension of the existing 14 by ~46
- **+20 boundary cases** (Task 11 addendum, the 20-30% production-realistic distribution Opus flagged):
  - **7 `mixed`**: one user message touches 2-3 topics simultaneously (e.g., "我在想换工作,而且家里催婚,搞不清哪个先解决"). Tests whether extractor cleanly picks the dominant topic OR returns multi-topic cleanly.
  - **7 `sparse`**: only `topic` is present; concern/hope/question all null (e.g., "我对哲学有点兴趣"). Tests whether extractor returns null fields cleanly vs hallucinating concern/hope to "fill the form".
  - **6 `emotional_rambling`**: long emotional venting with low information density (e.g., "今天真的太烦了,什么都不顺,感觉整个世界都在和我作对……"). Tests graceful degradation — extractor should either pull a coarse topic or return all null, NOT manufacture a fake structured claim.

Manual annotation: ~30-60 min additional for the 20 boundary cases (1.5h - 2h total counting the original 46 extension).

**Failure handling**: same 4 options as `#intent-classifier`:
- (a) switch dev to paid model (Haiku 4.5 / Gemini 2.5 Flash)
- (b) revise extraction prompt + re-run
- (c) accept temporary lower threshold + telemetry-driven calibration in Wave 2
- (d) split-route: chat keeps free / extraction uses paid (needs env-var seam — would re-open the deferral)

**Free model risk mitigation**:
- Detect free-model unavailable (rate limit / deprecation / quota): graceful fallback → placeholder card with subtle "extraction unavailable" hint + log warning + raise to Rodc
- JSON parse failure: defensive scan for `{...}` block (no `response_format: json_object`); on validation fail retry once; second fail → silent skip per spec edge case 2

**Eval set + few-shot language bias (v1.5 added; v1.6 marks MITIGATED 2026-05-02 evening)**: Rodix launches English. Dev / Rodc dogfood uses 中文 for UI convenience only — that's a *test-time* preference, not a *ship-time* truth. ~~The 80-case eval set was 65% 中文 / 25% English / 10% mixed; v2 few-shot was 6/6 中文.~~ **Status v1.6: MITIGATED.** Rebalance applied 2026-05-02 evening: eval set is now 64 EN / 16 ZH / 0 mixed (mixed-language deferred to Phase 2); few-shot is 4 EN / 2 ZH (covers 6 boundary categories with 中英 mix); runner emits `metrics_by_language.en` (ship gate, blocking) + `metrics_by_language.zh` (monitor only, non-blocking); each case carries an explicit `language` tag. Phase 2 (Chinese launch) reactivates the ZH-bucket gate when product-level Chinese support spec is written.

**Concern eval ground truth over-specific (v1.7 added 2026-05-02 evening)**: After v3.1 prompt iteration brought concern recall from 30% → 48% but the strict v1.3 gate (≥80%) remained out of reach, root-cause analysis showed the failure was eval-side, not model-side: concern ground truth was a single canonical string ("family financial stability if I quit") that human annotators would judge equivalent to paraphrases the model produces ("losing income"). LLM-judge fallback couldn't bridge this gap because the strings are lexically distant even with semantic-equivalence judging on long phrases. **Status v1.7: MITIGATED.** Two-part fix: (1) re-labeled 64 EN cases concern ground truth as `list[str]` of acceptable variants — first variant matching = TP. (2) Ship gate v1.7: per-field recall ≥60% / precision ≥70% / hallucination rate ≤8% + chitchat FP ≤5% + overall ≥75% = **14 conditions**. The hallucination cap is the real anti-trust-collapse signal (the v1.3 gate was indirect: precision encoded both hallucination and mismatch under one ratio). **Trade-off documented**: looser per-field gates accept more wording variance; stricter hallucination cap maintains trust integrity.

## Files

**Modify** (gitignored — no commit):
- `app/web/server.py` — `/api/chat` post-classifier hook: when classifier returned THOUGHTFUL, enqueue extraction task; add `GET /api/claim/by_message/{message_id}` polling endpoint
- `app/shared/storage_py/claim_adapter.py` — verify 4-field schema (extend additively if missing); add `get_claim_by_message_id` accessor for the polling endpoint
- `app/web/static/app.js` — after AI reply renders, start polling `/api/claim/by_message/{id}`; on hit swap placeholder card with real fields; on 5s timeout keep placeholder with subtle "extraction taking longer" hint
- `app/web/test_chat_placeholder.py` — add tests for the post-classifier extraction path (placeholder swap behavior)

**Create** (gitignored — no commit):
- `app/shared/extraction/__init__.py` — public exports
- `app/shared/extraction/extractor.py` — `Extractor.extract(user_msg, ai_reply) -> ClaimDict` (4 fields, possibly null) + structured failure return
- `app/shared/extraction/prompts/claim_extractor.md` — locked extraction prompt (loaded at module import; mirrors `app/web/prompts/rodix_system.md` pattern)
- `app/shared/extraction/extraction_queue.py` — background queue clone of `EmbedQueue` with shutdown-drain
- `app/shared/extraction/test_extractor.py` — unit tests (mock LLM)
- `app/shared/extraction/test_extraction_queue.py` — queue lifecycle tests

**Create** (tracked — commit normally):
- `app/web/test_chat_extraction.py` — integration test for chat → extraction → polling endpoint (uses TestClient + queue stub)
- `app/shared/extraction/test_extractor_integration.py` — opt-in eval gate test (`@pytest.mark.integration`)
- `fixtures/v0_2_0/eval/claim_extraction_cases.json` — bump 14 → 60 cases (extends existing file)
- `fixtures/v0_2_0/eval/claim_extractor_prompt.txt` — frozen prompt copy (for reproducibility)
- (`fixtures/v0_2_0/eval/run_claim_extraction_eval.py` already exists — extend to compute asymmetric per-field metrics)

## Prerequisite gate

**Do not start Task 1 until `#intent-classifier` asymmetric accuracy gate is GREEN** (or Rodc has signed off a temporary threshold). If extraction ships against a faulty classifier, every wrong THOUGHTFUL routing pollutes the Vault. Confirm classifier eval first; only then dispatch this plan.

## Bite-sized TDD tasks

- [ ] **Task 1: Extractor wrapper interface**
  - Write failing test `test_extractor.py::test_extract_returns_4_fields` — `Extractor().extract(user_msg, ai_reply)` → returns `{topic, concern, hope, question}` with sensible values (mock LLM call via `unittest.mock.patch` on `requests.post`)
  - Implement `Extractor` in `app/shared/extraction/extractor.py` using `_resolve_llm_config()` for provider/url/key (NOT `mcp_server.llm_extractor` — keeps app/ self-contained). Same defensive JSON parsing as classifier (scan for first `{...}` block; no `response_format: json_object`; `max_tokens=3000`).
  - 4-field schema: topic = nominal phrase / concern = fear/risk / hope = aspiration/goal / question = open question. Prompt instructs: "Output JSON with exactly these 4 keys. If a field is not present, set to null. Don't synthesize."
  - Locked prompt at `app/shared/extraction/prompts/claim_extractor.md`, loaded module-level (mirrors `_load_rodix_system_prompt()` pattern with inline fallback)
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 2: Extractor edge case — sparse fields**
  - Write failing test `test_extractor.py::test_extract_handles_pure_chitchat` — input "天气怎么样" → expects all 4 fields null (per spec edge case 1)
  - Verify implementation handles null + doesn't synthesize
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 3: Extractor edge case — LLM failure**
  - Write failing test `test_extract_handles_llm_timeout` — mock LLM raises `requests.Timeout` → extractor returns `{ok: false, reason: 'timeout', fields: None}` (not throw)
  - Reason taxonomy: `timeout` / `network` / `auth` (401/403) / `rate_limit` (429) / `parse` (invalid JSON) / `schema` (4 keys missing)
  - On parse / schema fail: retry once before giving up (per Risk register mitigation)
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 4: Extraction queue clone**
  - Write failing test `test_extraction_queue.py::test_queue_processes_in_background` — enqueue task, wait 100ms, verify processed
  - Clone `EmbedQueue` shape from existing `app/shared/embeddings/cache.py` (same: thread + queue + bounded + dropped stat + shutdown-drain)
  - Capacity: bounded at 100 (alpha cohort sizing)
  - Shutdown-drain semantics required (per existing `EmbedQueue` precedent — Windows file-locking on test teardown)
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 5: Queue integration with extractor**
  - Write failing test `test_queue_calls_extractor_and_persists` — enqueue task with `(message_id, conversation_id, user_msg, ai_reply)` → task runs extractor → persists 4-field claim → returns `claim_id`
  - Implement task handler
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 6: Persistence — claim_adapter 4-field schema**
  - Inspect existing `app/shared/storage_py/claim_adapter.py` — does the table have columns for `topic` / `concern` / `hope` / `question` + `message_id` foreign key?
  - If yes: pass-through, just add a `get_claim_by_message_id(conn, message_id)` accessor.
  - If no: extend schema additively (new schema version + migration). Write 4 nullable TEXT columns.
  - Write test `test_claim_adapter_persists_4_fields` and `test_get_claim_by_message_id`
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 7: /api/chat post-classifier hook + polling endpoint**
  - **Pre-condition**: classifier already runs in `/api/chat` (Wave 1b `#intent-classifier` Task 11). Hook into the SAME branch where `result.intent == THOUGHTFUL` would set `claim_placeholder`. Replace the placeholder logic at that branch:
    - Old: `claim_placeholder = _stub_claim_placeholder() if intent == THOUGHTFUL else None`
    - New: enqueue extraction task → response carries `claim_placeholder = None` (frontend polls for the real result)
  - Add `GET /api/claim/by_message/{message_id}` returning `{ready: bool, claim: Optional[ClaimDict]}` shape
  - Write failing integration test `test_chat_extraction.py::test_thoughtful_chat_enqueues_extraction` — POST chat with thoughtful msg + classifier mocked to THOUGHTFUL → queue receives task with correct args
  - Write `test_chitchat_chat_does_not_enqueue` — classifier returns CHITCHAT → queue NOT called
  - Write `test_get_claim_by_message_returns_404_when_not_ready` and `test_get_claim_by_message_returns_claim_when_ready`
  - PASS
  - (No commit for `app/web/server.py` — gitignored. `app/web/test_chat_extraction.py` is also gitignored.)

- [ ] **Task 8: Frontend swap placeholder for real claim** (polling — **Wave 1b temporary** per v1.3 clarification)
  - Modify `app.js` `#8` rendering: after AI reply renders, IF the response was for a thoughtful intent (signaled by `body._claim_pending: true` or absence of `_claim_placeholder`), start polling `/api/claim/by_message/{id}` at 1s interval, 5s timeout
  - On polling success → replace placeholder card with real fields (use existing `renderClaimCard` shape with real values)
  - On 5s timeout: keep placeholder card with subtle "(extraction taking longer than usual)" hint inline
  - On extraction failure (`{ok: false, reason: ...}`): hide card silently (per spec edge case 2)
  - Verify: chitchat / factual responses don't trigger any polling (classifier already gated them out server-side)
  - **Architectural debt label** (per v1.3 Opus clarification): polling is the **Wave 1b temporary mechanism**. Production-grade real-time delivery upgrades to **SSE or WebSocket in Wave 3 / launch+** as part of `#realtime-claim-delivery` (placeholder code; not yet a planned item). Add a code comment in `app.js` AND `server.py::get_claim_by_message` referencing this debt so future readers find it. If we ship to production still polling, we have a smell.
  - (No commit — app/ gitignored.)

- [ ] **Task 9: Vault badge update from real claim**
  - When polling success and claim has any non-null field → increment Vault badge (existing `bumpVaultBadge` function — re-use)
  - When all 4 fields null → badge NOT incremented (per spec edge case 1)
  - For chitchat / factual (no extraction enqueued) → badge NOT incremented (already true since no claim arrives)
  - Code-level verification — frontend smoke test
  - (No commit — app/ gitignored.)

- [ ] **Task 10: Same-topic deduplication (spec edge case 3)**
  - Write failing test `test_extractor.py::test_same_topic_simplified_after_3` — given 3 prior claims on topic "换工作" within last 5 messages → 4th extraction returns flag `simplified_reference: true` instead of full 4 fields
  - Implement check: before persisting, query last 5 claims in conversation → if any has matching topic (case-insensitive substring or LLM-judged equivalence — start with substring for v1) → set simplified flag
  - Frontend renders simplified card with `已记下 #N · 与之前相关 ↗` text only (no 4-field expansion)
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 11: Eval harness — bump 14 → 80 cases + asymmetric per-field precision/recall**
  - Existing `fixtures/v0_2_0/eval/claim_extraction_cases.json` has 14 cases (5 categories). **Extend to 80** = 60 core + 20 boundary:
    - **60 core** (extending existing 14 by 46 across the 5 categories):
      - +13 career (now 16) — including 3 boundary cases (multi-offer decisions, niche industries, mid-life career change)
      - +10 relationships (now 13)
      - +8 technical (now 11) — including ambiguous tech-vs-thoughtful (e.g., "should I migrate to X" — both technical AND a decision)
      - +8 abstract (now 10)
      - +7 chitchat (now 10) — for false-positive testing
    - **20 boundary** (new categories per v1.3 push back 2):
      - **7 `mixed`**: one user message touches 2-3 topics simultaneously. Tag in `category: mixed`. Expected: extractor picks the dominant topic OR populates topic with a comma-joined list (annotator's call per case).
      - **7 `sparse`**: only `topic` is present; concern/hope/question are null in `expected`. Tests anti-hallucination behavior.
      - **6 `emotional_rambling`**: long emotional venting, low information density. Expected: coarse topic OR all null; **never** manufactured concern/hope.
  - Each case: `{id, category, input: {user, ai}, expected: {topic, concern, hope, question}, notes?: str}`
  - Manual annotation: ~1.5-2 hours one-time
  - Extend `fixtures/v0_2_0/eval/run_claim_extraction_eval.py` to compute:
    - **per-field recall AND precision** (`topic` / `concern` / `hope` / `question`)
    - chitchat false-positive rate (any non-null field on chitchat input)
    - overall field accuracy (320 grades = 4 × 80)
    - per-category accuracy (incl. mixed / sparse / emotional_rambling for boundary visibility)
    - confusion-by-field grid (counts each "expected null but got X" → tells us which field hallucinates most)
  - Manual run on `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (after `#intent-classifier` eval gate confirmed GREEN)
  - Commit `eval(claim-extraction): bump to 80 cases + asymmetric P/R metrics` (fixtures IS tracked)

- [ ] **Task 12: Asymmetric accuracy gate enforcement (recall AND precision)**
  - Write failing test `app/shared/extraction/test_extractor_integration.py::test_eval_meets_asymmetric_gate` — `@pytest.mark.integration` (opt-in via `RUN_INTEGRATION=1` env, won't fire on default `pytest`)
  - Loads 80 cases, calls `extract()` on each (real LLM, dev model)
  - Computes metrics per the gate table in §"Asymmetric accuracy gate"
  - Asserts (10 conditions — recall + precision pair per field, plus FP rate, plus overall):
    - `recall(topic) >= 0.90` AND `precision(topic) >= 0.80`
    - `recall(concern) >= 0.80` AND `precision(concern) >= 0.85`
    - `recall(hope) >= 0.80` AND `precision(hope) >= 0.85`
    - `recall(question) >= 0.75` AND `precision(question) >= 0.80`
    - `chitchat_false_positive_rate <= 0.05`
    - `overall_field_accuracy >= 0.75`
  - **Precision computation**: TP = extracted-and-non-null AND matches expected (or substring-match heuristic for free-text fields). FP = extracted-and-non-null but expected was null (anti-hallucination check). Document the substring-vs-exact match heuristic in the runner so it's reproducible.
  - On any FAIL: print full per-field confusion + per-category breakdown (incl. boundary categories) so failure is debuggable
  - **Do not silently lower the gate** — on failure, raise to Rodc with the 4 risk-register options
  - PASS once all 10 assertions hold OR Rodc-signed-off temporary threshold
  - (No commit — `test_extractor_integration.py` lives in app/, gitignored.)

- [ ] **Task 13: Alpha observability — Vault badge growth log**
  - Add logging in queue task handler: every successful claim persist → log `INFO claim_persisted message_id={x} conversation_id={y} fields_populated={n}/4`
  - These logs are the alpha-test gate per IA-C cascade caveat: Rodc can grep server logs to verify "聊一次 → badge `+1`" pattern holds in real usage
  - No new endpoint (lives in stderr/log file)
  - PASS by inspection
  - (No commit — app/ gitignored.)

- [ ] **Task 14: End-to-end code-level verification**
  - Verify the full pipeline works against mocked LLM (no live calls):
    - Thoughtful chat → classifier mocked to THOUGHTFUL → extraction enqueued → polling endpoint returns claim → frontend swap (verified via test)
    - Chitchat chat → classifier mocked to CHITCHAT → extraction NOT enqueued → no polling → no card (verified via test)
    - Same-topic 4th message → simplified flag set → frontend renders simplified card
  - Run full app test suite — all green
  - Run integration eval (Task 12) — all 10 gate assertions hold OR Rodc sign-off recorded
  - Document the eval result file path in the final report (per implementer dispatch report shape)
  - **Flag for Rodc subjective-feel gate** (Task 15 below) — implementer flags Wave 1b release as "code-complete + eval gate met, awaiting Rodc 5-round dogfood"
  - (No commit — app/ gitignored. The integration eval result JSON in fixtures/ is untracked per existing convention.)

- [ ] **Task 15: Rodc 5-round subjective dogfood gate** (v1.3 ADD per Opus push back — independent product-feel check beyond statistical correctness)
  - **Why this is a separate gate**: even a passing eval gate (statistical correctness on 80 cases) can hide a product-feel failure where the 4 fields don't sound like the user's own thinking. Statistical PASS + dogfood FAIL is the most insidious failure mode for a memory product — Rodc must catch it before alpha rollout.
  - **Process**:
    1. Implementer signals Wave 1b release ready (Tasks 1-14 done, eval gate GREEN)
    2. Rodc runs 5 real conversations on real topics (career / life / technical / relationships — Rodc's actual current concerns, NOT canned eval cases)
    3. After each, Rodc reads the 4 extracted fields and asks: "does this sound like what I actually said? would I tell another person these 4 things if asked to summarize this conversation?"
    4. Rodc records subjective verdict per round: PASS / WEAK / FAIL with one-line note
  - **Outcome resolution**:
    - 4-5 PASS / 0-1 WEAK / 0 FAIL → ship
    - ≥ 2 WEAK or ≥ 1 FAIL → raise: 4 options (revise prompt / change schema / accept misalignment + telemetry / pivot to different extraction approach)
  - This gate is human-judgment, NOT automatable. Implementer marks Task 14 done with `awaiting_subjective_dogfood`; Rodc closes Task 15 manually after dogfood completes.
  - (No code change.)

## Done criteria

- [ ] `#intent-classifier` accuracy gate met (or Rodc-signed-off threshold) BEFORE this plan dispatches ✓
- [ ] Extractor wrapper (4-field prompt, app/-self-contained, defensive JSON parse) ✓
- [ ] Background queue clone of `EmbedQueue` with shutdown-drain ✓
- [ ] `claim_adapter` 4-field schema verified or extended additively ✓
- [ ] `/api/chat` post-classifier hook: enqueue extraction ONLY when classifier returned THOUGHTFUL ✓
- [ ] `GET /api/claim/by_message/{id}` polling endpoint live (Wave 1b temp; SSE/WebSocket upgrade flagged for Wave 3+) ✓
- [ ] Frontend polling swaps placeholder for real claim; 5s timeout / silent-fail per edge case 2; debt comment in code referencing Wave 3 upgrade ✓
- [ ] Same-topic dedup (4th in 5-window → simplified flag) ✓
- [ ] **80-case eval set committed** (fixtures/) — incl. 20 boundary cases (mixed / sparse / emotional_rambling) ✓
- [ ] **Asymmetric accuracy gate — all 10 assertions hold** (recall+precision per field × 4 fields = 8 conds, plus chitchat-FP, plus overall accuracy) OR Rodc-signed-off temporary threshold ✓
- [ ] Vault badge growth log (alpha-observable per IA-C cascade caveat) ✓
- [ ] Tests green: full app suite + new unit + integration eval ✓
- [ ] **Rodc 5-round subjective dogfood gate** (Task 15) — independent product-feel check; 4-5 PASS / 0-1 WEAK / 0 FAIL on real conversations OR Rodc-recorded mitigation ✓
- [ ] **Scenario verification**: S-CARD-1 (Vault badge animation when classifier-routed thoughtful → real fields), S-CARD-2 (system prompt failure ≠ extraction trigger — the gate is classifier intent, NOT AI reply phrase), S-CARD-3 (Active Recall — Wave 2 dependency, gate that classifier+extraction outputs are consumable), S-CARD-4 (same-topic 4th simplified), S-CHAT-1 (thoughtful → real claim card after polling), S-CHAT-2 (chitchat → no extraction, no card), S-CHAT-3 (factual → no extraction, no card), S-CHAT-4 (boundary cases, all 5 — relies on classifier correctness, gate verified upstream), S-CHAT-5 (multi-turn → 2nd-round extraction triggers correctly), S-CHAT-6 (multi-round depth pivot — extraction fires per turn but doesn't overwrite the conversation's full claim history) PASS ✓

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位:plan 中 N/A(backend feature)
2. ✓ Desktop-first:N/A(invisible feature)
3. ✓ §7.4 5 项 articulated
4. ✓ Pre-mortem 4 modes:like-me ✓ / metric vs goal ✓ / reactive vs strategic ✓ / edge vs main(extraction failure cascade 是 main risk,plan 显式 mitigate)
5. ✓ 桌面横向利用率:N/A
6. ✓ Mobile responsive:N/A(backend)
7. ✓ Empty state:由 `#3a` 4-tier cold start cover

## Post-launch follow-ups (P2)

- **Task 14 alpha-observability log-grep verification** (added 2026-05-02 per Rodc directive): Task 14 done-criterion includes "Vault badge 增长在 alpha 测试中可观察" — but the unit + integration tests cover the *mechanism* (claim_persisted log line + bumpVaultBadge frontend trigger), not the *live-log signal*. **At Task 15 Rodc 5-round dogfood**, in addition to subjective per-round PASS / WEAK / FAIL judgments, Rodc greps the server stderr / log file for `claim_persisted message_id=` lines and confirms one fires per thoughtful turn. This closes the alpha-observability done-criterion gap. **Not blocking ship** — but the done-condition isn't fully met without this manual log-grep step. If automated, becomes part of `INFRA 4` test infra investments.

## References

- Scenarios: S-CARD-1, S-CARD-2, S-CARD-3, S-CARD-4, S-CHAT-1, S-CHAT-2, S-CHAT-3, S-CHAT-4 (all 5 cases), S-CHAT-5, S-CHAT-6 (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`)
- Hard dependency: `#intent-classifier` — extraction only fires when classifier returns `THOUGHTFUL` (or low-confidence fallback). Classifier eval gate MUST be GREEN before this plan dispatches.
- Spec: `web-product-design.md` §5.5(`#8`)+ §6 dependency + spec §C-4.6 (extraction is downstream of classifier; do NOT recreate classifier-style banned-phrase gating here)
- Brainstorm: IA-C cascade `#claim-extraction` done 标准追加 "Vault badge 增长在 alpha 测试可观察"
- Prior art:
  - `fixtures/v0_2_0/eval/claim_extraction_cases.json` — existing 14-case eval set (the seed Task 11 extends to 60)
  - `fixtures/v0_2_0/eval/run_claim_extraction_eval.py` — existing runner (Task 11 extends to compute asymmetric per-field metrics)
  - `app/shared/embeddings/cache.py::EmbedQueue` — shape to clone (Task 4)
  - `app/shared/intent/classifier.py` — pattern for `_resolve_llm_config` + defensive JSON parsing (mirror in extractor)
- Roadmap: Wave 1b, depends on `#intent-classifier`. Unblocks `#8` real feature (replaces placeholder card with real LLM output) + `#3a` (real cards in Vault tab) + `#9b` (history-import first-insight).
- 协议 §5.1: `#claim-extraction` 是 P0, 3 个下游 P1/P2 项依赖
