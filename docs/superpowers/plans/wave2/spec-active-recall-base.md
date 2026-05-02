# `#active-recall-base` v0 — Implementation Plan

> **Status (2026-05-03 morning, draft v1):** First Wave 2 spec drafted at the same depth as `#claim-extraction` v1.8. Pending Rodc + external Opus review per `feedback_plan_review_protocol.md`. Implementer dispatch is blocked until v1.X "approved for dispatch." Dependencies: `#claim-extraction` Phase 1 ship-ready (v1.8 — landed 2026-05-02 EOD), recall orchestrator infra (`app/shared/recall/orchestrator.py` already shipped Wave 1a), `chat_claims` adapter (`app/shared/storage_py/chat_claim_adapter.py` already shipped Wave 1b).
>
> **For agentic workers:** Use `superpowers:test-driven-development` per task. Then `superpowers:subagent-driven-development` extended with `docs/superpowers/skills/scenario-verification.md`.
> **App/ gitignored** — `app/web/server.py` + `app/web/static/app.js` + new modules under `app/shared/recall_inject/` do NOT go to git. Skip the per-task `Commit ...` lines for those files. `fixtures/` artifacts (eval set + runner) DO commit.

**Goal:** When the user sends a new message, retrieve up to 3 most-relevant past `chat_claims` cards from the vault and inject them as compact context into the AI's system prompt BEFORE the chat LLM generates its reply. AI references past thinking naturally without the user re-explaining. **Done 标准:Active recall callout (⚡ "我把这个带回来了" / ⚡ "I brought this back") fires correctly on relevant past cards in alpha dogfood, with precision ≥ 80% on a 60-case eval set + monitored production hallucination cap.**

**Architecture:**

1. **Trigger** — runs at `/api/chat` AFTER intent classification but BEFORE the chat LLM call. Always runs (even on chitchat — fast path returns no recall when topic-match is weak). Latency budget: ≤ 200ms p95 (FTS5 + lightweight scoring; no LLM call in v0).
2. **Retrieval** — wraps existing `app/shared/recall/orchestrator.py::Orchestrator` with the `TopicEvaluator` only (the other 3 evaluators are out of scope for v0 per spec scoping). Calls `chat_claim_adapter.get_recent_chat_claims_in_conversation` for in-conversation candidates and runs an FTS5 cards-table query for cross-conversation candidates (existing `app/shared/storage_py/fts.py`).
3. **Ranking v0** — `(topic_substring + topic_bigram + recency + decay)` blended score, capped at top 3 with a per-result minimum threshold of 0.65 (mirrors `ThresholdConfig.topic` from `orchestrator.py`).
4. **Injection** — appends a structured block to `_RODIX_SYSTEM_PROMPT` (loaded once at module import; dynamic block is appended per-request inside `/api/chat` after the static prompt). Block lives in a stable position so the LLM's anchoring is consistent across turns.
5. **AI integration instruction** — system prompt gets a 3-sentence addendum instructing the AI to reference past cards conversationally without saying "I see in your vault…" / "looking at your records…" (banned phrases per `voice-guide.md` §4 don't #4 + brand-book Decision 3 verb = "bring back," not "surface").
6. **Recall callout** — when the AI's reply naturally references a recalled card (detected via overlap heuristic + LLM-judge fallback at Wave 2.1), frontend renders ⚡ "我把这个带回来了" (Chinese) / ⚡ "I brought this back" (English) banner with the source-card link. Per brand-book §7b first item + brainstorm `#8` micro-adj 2.
7. **Recall logging** — every injection is logged via existing `recall_event_adapter.log_event()` so threshold-learning + alpha telemetry can aggregate. Frequency caps DEFERRED to Wave 2.1 (existing orchestrator caps are evaluator-output-side; v0 always-runs at chat time so caps would suppress injection-side, a different semantic — needs explicit design pass).

**Hard dependency:** `#claim-extraction` v1.8 must be live in production. Reason: recall reads from `chat_claims` table; if the table is empty or polluted with hallucinated 4-field cards, recall either starves (empty vault) or flips polarity (irrelevant card injected → AI awkwardly references it → trust collapses per assumption W17). Phase 1 ship-readiness is met (79.3% overall accuracy, 2.3% hallucination rate, hard ship blocker GREEN per claim-extraction plan v1.8 §"Hallucination as trust killer").

**Tech Stack:** Python · existing `app/shared/recall/orchestrator.py` · existing `app/shared/recall/evaluators/topic.py` · existing `app/shared/storage_py/chat_claim_adapter.py` · existing `app/shared/storage_py/fts.py` · existing `app/shared/storage_py/recall_event_adapter.py` · NEW thin module `app/shared/recall_inject/` for the chat-time injection pipeline · `_RODIX_SYSTEM_PROMPT` dynamic suffix in `app/web/server.py`

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | Backend mostly-invisible feature. Visible signal: ⚡ "我把这个带回来了" / "I brought this back" callout in the chat surface when AI references an injected card; AI replies start incorporating user's prior thinking without re-prompting. |
| 产品策略假设 | Active recall = "remembers your thinking" canonical pitch operationalized. Per brand-book §1 + §7 Decision 3, this is the load-bearing Wave 2 feature: WITHOUT it the eight-word pitch ("ChatGPT remembers your name. Rodix remembers your thinking.") is unbacked by product behavior. Position-strategy §3.3 names this as one of 4 architectural bets. |
| 适合 / 不适合 | **适合**: All Phase 1 alpha users (≤1,000 in 30 days). **不适合**: Users who explicitly prefer fresh-context single-shot AI use (these self-select OUT per brand-book §3 anti-target — *"ChatGPT's fine for restaurant questions"*). v0 does NOT yet detect "let's start fresh" user signal — Wave 3+ adds explicit forget-mechanic. |
| Trade-off | + AI behaves as continuity-of-thought partner (the wedge) / + Vault becomes load-bearing (cards revisited > write-only) / + asymmetric trust signal: irrelevant injection awkward but bounded (max 3 cards × ~150 tokens = ~450 token overhead) / − latency floor +100-200ms per chat call / − precision-failure mode (wrong card injected) directly damages brand register: AI awkwardly references something user didn't say / − vault-empty users get nothing (no harm, but no aha either — covered by `#3a` 4-tier cold-start) |
| 最大风险 | **Wrong-card injection (low precision) → AI awkwardly references something the user did not actually say or recently say → trust collapse (S16+W17 — "surveillance-fail-mode polarity flip" per brand-book §appendix item 4).** Mitigation: asymmetric gate precision ≥ 80% (better silent than wrong); minimum threshold 0.65 (matches orchestrator default); top-3 cap; null-by-default discipline (return ZERO injections rather than risk one wrong); brand-book Decision 5 null-default applied to recall, not just extraction. |

## Ambiguity flag

✓ **Mostly resolved** — most decisions are pinned by existing code surface. 3 open items flagged for Rodc + external Opus review:

**Locked decisions:**
- **Reuse orchestrator infrastructure** — NEW thin module `app/shared/recall_inject/` wraps `Orchestrator` + `TopicEvaluator` (NOT a parallel scoring system). Per memory rule "verify-first; reuse existing functions; do not propose parallel infrastructure."
- **Storage source** — read from `chat_claims` table via `chat_claim_adapter.py::get_recent_chat_claims_in_conversation` for in-conv candidates AND `cards` table via FTS5 (`fts.py::search_cards_fts`) for cross-conversation candidates. Two sources because chat_claims (Wave 1b feature) is the production-extraction output, while `cards` is the MCP-ingestion + history-import target — alpha vault could have either or both.
- **Search scope** — across ALL conversations by default (per spec). User-explicit "scoped to current conversation only" deferred to Wave 3+.
- **v0 algorithm** — substring + bigram + recency + decay, not embeddings or MMR. Wave 2.1 calibration may add embeddings if precision falls below 80%.
- **Injection point** — after the locked `_RODIX_SYSTEM_PROMPT` static body, before the user message. Same `messages[]` array passed to LLM provider, same role="system" — appended into a single system message string with a clear visual delimiter so a future "remove recall context" flag can strip it surgically.
- **Trigger** — every `/api/chat` call. NOT gated by intent classifier output — even chitchat can recall (`你好,前天的项目还没决定` is chitchat-classed but recall-relevant). Filtering happens by SCORE, not by INTENT.
- **Recall callout copy** — `⚡ 我把这个带回来了` (Chinese) / `⚡ I brought this back` (English) per brand-book §7b first item + brainstorm `#8` micro-adj 2. Action buttons `用上了 / 不相关 / 已经想过 / 跳过` per same brainstorm lock. NOT `记下了 / 看了 / 不相关 / 忽略` (current Wave 1b placeholder per brand-book §7b acknowledgment).

**Open items for Rodc + Opus review:**
- **OPEN-1**: Should v0 inject recall cards even when intent classifier returns CHITCHAT? Pro: a chitchat-classed `你好,我又想到那个工作的事` IS a recall trigger. Con: extra latency on every chitchat round. **Recommendation**: yes, always run recall — cost is bounded (FTS5 query ≤ 50ms; lightweight bigram scoring; no LLM call). If telemetry shows >70% of chitchat calls inject zero cards, gate at Wave 2.1.
- **OPEN-2**: Should the recall callout fire for EVERY injection, or only when the AI's reply ACTUALLY references the card? Pro (every): simple, no detection logic. Con: AI may receive 3 cards but reference 0 — callout would lie about what just happened. **Recommendation**: fire only when reply detectably references the card (substring match on topic OR LLM-judge fallback). Fall back to silent injection (no callout) when AI didn't reference. Asymmetric: better silent than wrong.
- **OPEN-3**: Frequency caps. The existing `FrequencyCaps(per_conversation=1, per_day=3)` in `orchestrator.py` is for the EVALUATOR-output-side (when does orchestrator emit a candidate). For chat-time injection, "1 per conversation" would mean only ONE turn in a conversation gets injected — wrong semantic. Injection-side caps should be: max 3 cards per single chat turn (already specified) + soft per-day cap for callout-rendered events, not for silent injections. **Recommendation**: defer to Wave 2.1 calibration; v0 has the hard 3-per-turn cap and no per-day cap at injection (only at callout-render time the existing orchestrator caps apply through `recall_events`). Document the difference clearly so Wave 2.1 doesn't conflate them.

## Dev mode + asymmetric precision gate (load-bearing per brand-book §appendix item 4)

**Dev mode** (`RODIX_DEV=1`):
- v0 algorithm runs against the dev SQLite vault
- Latency budget logged per call; threshold values reload-on-edit when `app/shared/recall_inject/scorer.py` changes (so iterative tuning is fast)

**Production mode**:
- Same code path; production telemetry (Wave 2.1) drives threshold calibration

**Asymmetric precision gate** (load-bearing — per brand-book §appendix reconciliation item 4 + assumption W17):

| Metric | v0 target | Reasoning |
|---|---|---|
| **Recall precision** (TP / (TP+FP) on 60-case eval) | **≥ 80%** | Wrong-card injection is the trust killer. Better silent than wrong. Aligns with `claim-extraction` precision discipline + brand-book Decision 5 null-by-default applied to recall. |
| **Recall recall** (TP / (TP+FN)) | ≥ 60% (soft floor) + production calibration trigger if recall < 50% sustained for 3 days | Promoted from monitor-only after v1.1 reviewer push back: under-recall is the wedge-failure mode for the W11/W13 retention thesis ("brings it back when it matters" is a recall claim). 50% recall monitor would silently break half of valid retention loops; 60% soft floor with a calibration trigger preserves precision-asymmetric framing without losing the canonical-pitch teeth. |
| **Top-1 precision** when 1+ card injected | ≥ 85% | The TOP card is what the AI reads first; if top-1 is wrong, AI likely references the wrong thing. Stricter than overall precision. |
| **Empty-vault behavior** | 0 injections, 0 errors, 0 latency-spike | Per spec edge case; verified by separate test bucket. |
| **Hallucination invariance** | AI does not invent details about injected cards | Verified via dogfood: AI can only reference fields that exist in the injected block. Subjective judgment per Rodc Round (similar to claim-extraction Task 15). |

**Why precision >> recall here**: a recall-only target (high recall, low precision) would inject 5 cards every turn, most irrelevant. AI references one of them awkwardly ("you mentioned earlier worrying about X" — except user didn't say X this conversation). User reads "this product is making things up about me" → trust collapse + brand polarity flip from "trusty" to "creepy" (W17). The precision gate enforces null-by-default extension into recall.

**Eval set** — NEW: `fixtures/v0_2_0/eval/recall_injection_cases.json` (60 cases):

- **20 in-conversation continuation** cases — vault has card from earlier turn this conversation; user message references the topic. Expected: top-1 = that card. Tests obvious-match path.
- **20 cross-conversation recall** cases — vault has card from a different conversation 3-30 days old; user message references the topic. Expected: top-1 = that card. Tests cross-conversation-default scope.
- **10 "no recall" cases** — vault has cards but none topic-relevant to user message; OR vault is empty. Expected: 0 injections. Tests anti-hallucination behavior (the precision-asymmetry case).
- **10 distractor cases** — vault has 3+ cards on similar-but-distinct topics; user message clearly references ONE. Expected: top-1 = the right one. Tests fine-grained discrimination (career-change-A vs career-change-B vs career-change-C).

Manual annotation: ~2.5h one-time. Each case: `{id, category, vault_state: list[ChatClaimRow], user_message: str, expected_card_ids: list[str] | "none"}`.

**Failure handling**: same 4 options as `#claim-extraction`:
- (a) tighter threshold (raise from 0.65 → 0.70+)
- (b) revise scoring formula (e.g., reweight bigram vs substring, change decay constant)
- (c) accept temporary lower threshold + telemetry calibration in Wave 2.1
- (d) add embedding fallback (Wave 3+ scope per spec; would re-open spec scope)

**Production calibration trigger (Wave 2.1)**:
- If callout-rendered events show `user_action='not_relevant'` rate > 25% sustained → emergency v1 algorithm iteration
- Below 25% → v0 calibration is acceptable for Phase 1

---

## Files

**Modify** (gitignored — no commit):
- `app/web/server.py`:
  - In `/api/chat` handler, after intent classification, BEFORE calling LLM provider: run `recall_inject.run(conversation_id, user_msg, conn)` → returns `RecallInjection` (cards + score for each + injection-block string). Append injection block as suffix to `_RODIX_SYSTEM_PROMPT` for THIS request only (do NOT mutate the module-level constant).
  - Carry `injected_card_ids` and `injection_block_text` in chat response metadata so the frontend knows which cards may surface as recall callouts.
  - Add follow-up logic: after LLM reply received, run lightweight reply-references-card detection (substring overlap on topic field) → if positive, log a `recall_event` via `recall_event_adapter.log_event()` AND surface the callout to frontend. If no detected reference, log a "silent_injection" recall_event (new event subtype) so telemetry can compare injected vs referenced rates.
  - Add `GET /api/recall/by_message/{message_id}` (parallel shape to `/api/claim/by_message/{id}`) returning `{ready, callout: Optional[CalloutDict]}` for the frontend to fetch the callout content.
- `app/web/prompts/rodix_system.md`:
  - Append a NEW §"Past thinking integration" section (~120 words) instructing the AI to reference past cards conversationally without using banned introductory phrases ("I see in your vault…", "looking at your records…", "based on what I remember…"). Per brand-book Decision 3 verb = "bring back" not "surface" — guidance to AI uses verb-of-natural-reference ("you mentioned" / "the [topic] you were working through" / "earlier you wondered if…") rather than meta-commentary about the recall mechanism.
- `app/web/static/app.js`:
  - After AI reply renders, poll `GET /api/recall/by_message/{id}` (1s interval, 5s timeout — same shape as `claim-extraction` polling — flagged as Wave 3+ SSE/WebSocket upgrade in same code-comment as `#realtime-claim-delivery` debt).
  - On callout response, render ⚡ "我把这个带回来了" / ⚡ "I brought this back" banner inline above the AI message bubble with: source-card title (link to Vault tab card), 4 action buttons (`用上了` / `不相关` / `已经想过` / `跳过` — Chinese; `Useful` / `Not relevant` / `Already thought about it` / `Skip` — English).
  - PATCH the existing Wave 1b placeholder header `记忆提醒 · 话题相关` (`app/web/static/app.js:580` per brand-book §7b first item) to the locked copy `⚡ 我把这个带回来了`. PATCH the placeholder action buttons `记下了 / 看了 / 不相关 / 忽略` to the brainstorm-locked `用上了 / 不相关 / 已经想过 / 跳过`.

**Create** (gitignored — no commit):
- `app/shared/recall_inject/__init__.py` — public exports: `run`, `RecallInjection`, `score_chat_claim`, `format_injection_block`
- `app/shared/recall_inject/pipeline.py` — `run(conn, conversation_id, user_msg) -> RecallInjection` orchestrates: gather candidates → score → top-3 + threshold → format block
- `app/shared/recall_inject/scorer.py` — `score_chat_claim(claim: ChatClaimRow, user_msg: str, now: datetime) -> float` v0 algorithm (substring + bigram + recency + decay)
- `app/shared/recall_inject/formatter.py` — `format_injection_block(claims: list[ChatClaimRow]) -> str` produces the brand-aligned snippet per the format-variant decision (see §"Injection format" below)
- `app/shared/recall_inject/test_pipeline.py` — unit tests (uses tmp SQLite + fixture rows)
- `app/shared/recall_inject/test_scorer.py` — unit tests for the scoring formula (deterministic; no LLM)
- `app/shared/recall_inject/test_formatter.py` — golden-file tests for the injection-block format

**Create** (tracked — commit normally):
- `app/web/test_chat_recall_inject.py` — integration test for `/api/chat` → recall injection → AI receives modified system prompt → verified via mock LLM
- `app/shared/recall_inject/test_recall_inject_integration.py` — opt-in eval gate test (`@pytest.mark.integration`)
- `fixtures/v0_2_0/eval/recall_injection_cases.json` — 60-case eval set
- `fixtures/v0_2_0/eval/run_recall_injection_eval.py` — runner; computes precision / recall / top-1 precision / per-category breakdown

## Prerequisite gate

**Do not start Task 1 until `#claim-extraction` v1.8 production hallucination rate stays ≤ 5% sustained for 3+ days post-launch** (or Rodc-signed-off temporary threshold). Reason: recall reads `chat_claims`. If extraction is hallucinating (false-positive 4-field cards), recall amplifies the hallucination — injecting fake-content cards into the AI's context. Trust collapses faster than via extraction-only path because the recall callout EXPLICITLY surfaces "this is from your vault" — a hallucinated card surfaced via callout tells the user "we made this up about you" with brand affirmation. **Verify upstream telemetry first; only then dispatch this plan.**

## Bite-sized TDD tasks

- [ ] **Task 1: Scorer — substring + bigram match**
  - Write failing test `test_scorer.py::test_substring_match_scores_high` — `score_chat_claim(claim, user_msg)` where claim.topic="换工作" and user_msg="我又在想换工作的事" → score ≥ 0.7
  - Write `test_substring_match_case_insensitive` — claim.topic="Career Change" and user_msg="thinking about career change" → score ≥ 0.7
  - Implement v0 scoring:
    - **Substring score (3.0)**: claim.topic appears as case-insensitive substring inside user_msg (or vice-versa)
    - **Bigram score (2.0)**: bigram overlap > 0.4 between claim.topic tokens and user_msg tokens (use char-bigrams for CJK; word-bigrams for Latin; hybrid for mixed — ENUM by detecting CJK char fraction in claim.topic)
    - Score is the MAX of the two (not sum) so a substring win doesn't double-count
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 2: Scorer — recency + decay**
  - Write failing test `test_scorer.py::test_recent_card_in_same_conversation_gets_bonus` — claim from same conversation, created < 7 days ago → +1.0 to score
  - Write `test_old_card_decays` — claim created 60 days ago (cross-conversation) → score × 0.5
  - Write `test_recent_cross_conversation_no_bonus` — claim from different conversation, < 7 days ago → no recency bonus (recency bonus is only for SAME conversation; cross-conv recall is on topic-strength alone — design choice: prevents recent-but-irrelevant cards from out-ranking older-strongly-relevant ones)
  - Implement: `recency_bonus(claim, conversation_id, now) -> float` returns +1.0 iff same conv AND created within 7 days. `decay_factor(claim, now) -> float` returns 1.0 for ≤30 days, 0.5 for >30 days (cliff, not gradient — gradient is Wave 2.1 calibration)
  - Final score: `(base_score + recency_bonus) * decay_factor`
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 3: Scorer — threshold and edge cases**
  - Write failing test `test_scorer.py::test_below_threshold_returns_zero` — claim with no topic match → score 0.0
  - Write `test_null_topic_in_claim_handled` — `claim.topic = None` (the null-default extraction case) → score 0.0 (no error)
  - Write `test_empty_user_msg_returns_zero` — user_msg="" → score 0.0
  - Verify the existing `ThresholdConfig.topic = 0.65` from `app/shared/recall/orchestrator.py` is the comparison constant (import + reference, do NOT redefine) — Task 5 uses this for top-3 filtering
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 4: Pipeline — gather candidates from chat_claims + cards**
  - Write failing test `test_pipeline.py::test_gather_in_conversation_then_cross_conversation` — vault has 3 chat_claims in current conv + 5 chat_claims in other convs + 10 MCP `cards` from history-import → `_gather_candidates(conn, conversation_id)` returns all 18 candidates with `source` tag (`'chat_claim_in_conv' | 'chat_claim_other_conv' | 'mcp_card'`)
  - Implement: call `chat_claim_adapter.get_recent_chat_claims_in_conversation(conn, conversation_id, limit=20)` for in-conv candidates; SELECT all chat_claims NOT in this conv (limit 100, ordered by created_at DESC) for cross-conv; call `fts.search_cards_fts(conn, user_msg, limit=10)` for MCP cards (FTS5 already does the heavy filtering for cards table)
  - **Adapter ChatClaimRow → unified Candidate** — wrap each row as `Candidate(id, topic, body_summary, conversation_id, created_at, source)` so downstream scoring is source-agnostic. body_summary builds `topic / concern / hope / question` 1-line concat with null-skip
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 5: Pipeline — top-3 by combined score, with threshold**
  - Write failing test `test_pipeline.py::test_top_3_above_threshold` — vault has 5 candidates: 3 with score ≥ 0.65 (1.2 / 0.8 / 0.7), 2 with score < 0.65 (0.4 / 0.2). Top-3 result is the 3 above threshold, ordered by score desc
  - Write `test_top_3_caps_at_3_when_more_above_threshold` — vault has 5 candidates all ≥ 0.65 → returns 3 highest
  - Write `test_returns_empty_when_all_below_threshold` — vault has 5 candidates all < 0.65 → returns []
  - Write `test_returns_empty_on_empty_vault` — vault has 0 candidates → returns [] (no error)
  - Implement: score each candidate via `score_chat_claim()`, filter by threshold (0.65 from `ThresholdConfig.topic`), sort score desc, take top 3
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 6: Formatter — injection block format**
  - Write failing test `test_formatter.py::test_format_injection_block_3_cards` — input list of 3 chat_claims → output string matches a brand-aligned format (see §"Injection format" below — use the locked variant)
  - Write `test_format_injection_block_empty_list` — input `[]` → output empty string `""` (no header for zero cards — silent injection per anti-hallucination discipline)
  - Implement formatter using locked variant from §"Injection format" decision below
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 7: Pipeline — public `run()` entrypoint**
  - Write failing test `test_pipeline.py::test_run_returns_RecallInjection_with_block_text` — calls `run(conn, conv_id, user_msg)` → returns `RecallInjection(cards=[...3 ChatClaimRow], block_text="...", scores=[...])` for a vault with 5 candidates above threshold
  - Write `test_run_returns_empty_RecallInjection_on_no_match` — returns `RecallInjection(cards=[], block_text="", scores=[])` when no candidate above threshold
  - Implement: `run(conn, conversation_id, user_msg, *, now=None) -> RecallInjection` wires Tasks 4-6; `now` is injected for deterministic testing
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 8: Server integration — append injection to system prompt**
  - Write failing test `test_chat_recall_inject.py::test_thoughtful_chat_with_relevant_vault_injects_block` — POST chat with vault containing matching card → mock LLM is called with system message that contains the injection block string
  - Write `test_chitchat_chat_still_runs_recall` — vault has matching card; user message classifies CHITCHAT → injection still happens (recall is intent-orthogonal per OPEN-1 recommendation)
  - Write `test_empty_vault_no_injection` — vault is empty → mock LLM is called with the static `_RODIX_SYSTEM_PROMPT` only, no suffix
  - Modify `/api/chat` handler in `server.py`: after intent classification, build `injection = recall_inject.run(conn, conv_id, last_user_msg)`. Then `messages_for_llm[0]['content'] = _RODIX_SYSTEM_PROMPT + injection.block_text` (only if non-empty). Carry `injection.cards[i].id for i in range(...)` in response metadata as `_recall_card_ids`.
  - PASS
  - (No commit — `app/web/server.py` and `test_chat_recall_inject.py` both gitignored — wait, test file is tracked per Files §; commit `eval(active-recall-base): add chat-recall-inject integration test`)

- [ ] **Task 9: Server integration — `GET /api/recall/by_message/{id}` polling endpoint**
  - Write failing test `test_get_recall_by_message_returns_404_when_not_ready` — call before AI reply finished → returns `{ready: False, callout: None}`
  - Write `test_get_recall_by_message_returns_callout_when_referenced` — AI reply contains substring of injected card.topic → returns `{ready: True, callout: {source_card_id, source_card_title, copy_zh, copy_en}}`
  - Write `test_get_recall_by_message_returns_silent_when_not_referenced` — AI reply does NOT reference any injected card → returns `{ready: True, callout: None}` (silent injection logged but no callout shown)
  - Implement: `GET /api/recall/by_message/{message_id}` queries a NEW lightweight in-memory cache `_recall_callout_by_message_id: dict[str, Optional[CalloutDict]]` populated when the chat handler post-processes the LLM reply (Task 10). Cache TTL 60s (mirrors polling timeout window 5s × 12 retries safety margin).
  - **Architectural debt**: in-memory dict survives the process lifetime only — same Wave 1b temp mechanism as `#claim-extraction`. Wave 3+ migrates to SSE/WebSocket per `#realtime-claim-delivery` debt comment.
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 10: Reply-references-card detection + recall_event log** (HARDENED v1.1 per reviewer Edit 3)
  - Write failing test `test_chat_recall_inject.py::test_reply_with_topic_substring_logs_referenced_event` — AI reply contains injected card.topic as substring (≥4 char EN / ≥3 char CJK threshold met) → `recall_events` row inserted with `user_action=NULL` (action arrives via Task 12 follow-up endpoint), `selected_card_id` matches, AND callout cache populated
  - Write `test_reply_without_topic_substring_logs_silent_event` — AI reply does NOT reference any injected card → recall_events row inserted with subtype `silent_injection`, no callout cache entry
  - Write `test_reply_with_short_cjk_topic_does_NOT_false_positive` — injected card has 2-char CJK topic ("副业") and reply mentions "副业" generically → detector returns None (substring length floor rejects), recall_event logged as `silent_injection`. THIS TEST IS CRITICAL: catches the reviewer-flagged 2-char CJK false-positive failure mode.
  - Write `test_reply_with_trivial_substring_overlap_does_NOT_false_positive` — injected card topic is one character of a longer reply → detector returns None (length-normalized check rejects: substring must be ≥ 5% of reply length OR appear in user-emphasized context like a pronoun referent)
  - Implement detection function `_detect_reply_references_card(reply: str, injected_cards: list[ChatClaimRow]) -> Optional[ChatClaimRow]`:
    - **Length floor**: skip cards where `len(card.topic_normalized) < 4` for ASCII-dominant or `< 3` for CJK-dominant. (Detection: simple ratio of CJK chars in topic > 0.5 → CJK path.)
    - For each injected card meeting length floor: if card.topic_normalized appears as case-insensitive substring in reply → continue to length-normalized check.
    - **Length-normalized check**: substring must be ≥ 5% of `len(reply)` OR be the first significant noun in the reply (heuristic: substring start position < `len(reply) * 0.4`). Rejects 0.5% noise overlap on long replies.
    - Tie-break: first card in `injected_cards` order (which is score-desc, so highest-scoring wins).
    - Return None if no match.
  - **Wave 2.1 LLM-judge fallback path** (scaffolded as `NotImplementedError` for v0 honesty): add stub function `_llm_judge_reply_references_card(reply: str, injected_cards: list[ChatClaimRow]) -> Optional[ChatClaimRow]` with body `raise NotImplementedError("Wave 2.1 — calibrate against substring detector telemetry first")`. v0 ships with substring detector only; Wave 2.1 wires LLM-judge for hard cases (short topics + ambiguous replies). The stub-with-explicit-NotImplementedError makes the gap legible to next implementer instead of silent.
  - Wire: in `/api/chat` handler after LLM reply received, call substring detector → if returns a card, populate callout cache. Always log a `recall_event` (referenced or silent) so telemetry can compute "injected vs actually referenced" rate.
  - **Wave 2.1 calibration**: if "silent injection" rate is high (>50% of injected cards never referenced), the AI integration prompt addition (Task 11) needs revision OR threshold needs raising OR LLM-judge fallback gets wired (the NotImplementedError above).
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 11: System prompt — past-thinking integration instruction**
  - Modify `app/web/prompts/rodix_system.md`: APPEND a new section `## Past thinking integration` after the existing `## Voice` section. Content (~120 words):
    ```
    ## Past thinking integration

    A separate system step may add a "Past thinking from your vault" block below your main instructions. When such a block is present, treat those cards as honest context — things the user actually said earlier and that may bear on what they're saying now.

    Reference them naturally when they're useful: "the [topic] you were working through last week", "you mentioned wondering whether X — has that shifted?". Quote their actual phrasing where it sharpens the reflection.

    DO NOT use meta-commentary about the recall mechanism: never say "I see in your vault…", "looking at your records…", "based on what I remember…", "my memory shows…", or any phrasing that sounds like reading from a database. The user knows their thinking is saved; treat it the way a friend who actually paid attention would.

    When the block is absent, ignore this section.
    ```
  - Write failing test `test_chat_recall_inject.py::test_system_prompt_contains_integration_section` — load the prompt file, assert it contains "Past thinking integration" header AND the banned-phrase list ("I see in your vault…", "looking at your records…")
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 12: Frontend — render recall callout + 4 action buttons**
  - Modify `app/web/static/app.js`:
    - After AI reply renders, IF `body._recall_card_ids` is non-empty, start polling `GET /api/recall/by_message/{id}` (1s interval, 5s timeout — clone of `#claim-extraction` polling shape; same SSE/WebSocket upgrade flag in code comment)
    - On polling success with `callout != null`: render `⚡ 我把这个带回来了` (Chinese surface) / `⚡ I brought this back` (English surface — language-detect from current chat messages or from `lang` attribute) banner ABOVE the AI message bubble with:
      - Source-card title clickable link → opens Vault tab + selects that card
      - 4 action buttons inline: `用上了` (positive — applied) / `不相关` (correction — wrong injection) / `已经想过` (positive — already considered) / `跳过` (neutral skip)
    - On 5s timeout OR `callout=null`: silent (no callout banner — was either silent injection or polling missed)
    - On action-button click: POST `/api/recall/{event_id}/action` with chosen action (uses existing endpoint at `server.py:2668`)
  - **PATCH the existing Wave 1b placeholder header** at `app/web/static/app.js:580` from `header.textContent = '记忆提醒 · ' + recallTypeLabel(recallType);` to the locked copy `⚡ 我把这个带回来了` (or English equivalent based on lang detect)
  - **PATCH the placeholder action buttons** from `记下了 / 看了 / 不相关 / 忽略` to the brainstorm-locked `用上了 / 不相关 / 已经想过 / 跳过`
  - Code-level verification — frontend smoke test
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 13: Eval harness — 60-case recall_injection_cases.json + asymmetric runner**
  - Create `fixtures/v0_2_0/eval/recall_injection_cases.json` with 60 cases per §"Eval set" breakdown above (20 in-conv / 20 cross-conv / 10 no-recall / 10 distractor)
  - Each case: `{id, category, vault_state: list[ChatClaimRow], current_conversation_id: str, user_message: str, expected_card_ids: list[str] | "none"}`
  - Manual annotation: ~2.5h one-time. Source vault states from real Rodc dogfood traffic (post-Phase-1-launch, anonymized) where available; else hand-craft.
  - Create `fixtures/v0_2_0/eval/run_recall_injection_eval.py`:
    - Loads cases, builds in-memory SQLite per case (avoids cross-case state bleed)
    - Calls `recall_inject.run(conn, conv_id, user_msg)` for each case
    - Computes:
      - **Per-case verdict**: TP (top-1 ID is in expected_card_ids) / FP (any injected card is NOT in expected_card_ids) / FN (no injection BUT expected_card_ids non-empty) / TN (no injection AND expected="none")
      - **Aggregate**: precision = TP / (TP+FP), recall = TP / (TP+FN), top-1 precision = TP / total cases with any injection
      - **Per-category breakdown** (in-conv / cross-conv / no-recall / distractor) so failure is debuggable
      - **Confusion-by-source grid**: for each FP, log which source bucket (chat_claim_in_conv / chat_claim_other_conv / mcp_card) supplied the wrong winner
  - Commit `eval(active-recall-base): add 60-case recall injection eval set + asymmetric runner` (fixtures IS tracked)

- [ ] **Task 14: Asymmetric precision gate enforcement**
  - Write failing test `app/shared/recall_inject/test_recall_inject_integration.py::test_eval_meets_asymmetric_gate` — `@pytest.mark.integration` (opt-in via `RUN_INTEGRATION=1` env)
  - Loads 60 cases via the runner from Task 13
  - Asserts (4 conditions):
    - `precision >= 0.80` (the load-bearing gate)
    - `top_1_precision >= 0.85`
    - `empty_vault_cases_inject_zero == True` (the per-category check)
    - `recall >= 0.50` (monitor-only — asserted but failure is non-blocking with printed warning)
  - On any FAIL: print full per-category confusion + per-source confusion + score histogram so failure is debuggable
  - **Do not silently lower the gate** — on failure raise to Rodc with the 4 risk-register options
  - PASS once all 4 assertions hold OR Rodc-signed-off temporary threshold
  - (No commit — `test_recall_inject_integration.py` lives in app/, gitignored.)

- [ ] **Task 15: Alpha observability — recall injection log**
  - Add logging in `recall_inject.run()`: every call → log `INFO recall_injected conversation_id={x} user_msg_len={n} candidates_examined={m} injected={k} top_score={s}`
  - On callout fired: log `INFO recall_callout_fired event_id={e} card_id={c} action_pending=true` (action arrives later)
  - On silent injection: log `INFO recall_silent_injection card_id={c} reason='reply_no_substring_match'`
  - These logs are the alpha-test signal — Rodc can grep server stderr for `recall_injected count=` patterns to verify recall fires at appropriate cadence
  - PASS by inspection
  - (No commit — app/ gitignored.)

- [ ] **Task 16: End-to-end code-level verification**
  - Verify the full pipeline against mocked LLM:
    - Vault with matching card → injection in system prompt → mocked LLM reply contains topic substring → callout fires → action button click logs to recall_events (verified via test)
    - Vault with matching card → injection in system prompt → mocked LLM reply does NOT reference (different topic) → silent injection logged → no callout (verified via test)
    - Empty vault → no injection → no callout → no error (verified via test)
    - Vault with 5 matching cards → top-3 injected → 4th and 5th not in system prompt (verified via prompt-content assertion)
  - Run full app test suite — all green
  - Run integration eval (Task 14) — all 4 gate assertions hold OR Rodc sign-off recorded
  - Document the eval result file path in the final report
  - **Flag for Rodc subjective-feel gate** (Task 17 below)

- [ ] **Task 17: Rodc 5-round subjective dogfood gate** (parallel to `#claim-extraction` Task 15)
  - **Why a separate gate**: even a passing 80% precision gate (statistical) can hide a product-feel failure where injected cards are technically-correct but feel intrusive ("how does it know that's relevant" — surveillance-fail-mode polarity flip per W17 + brand-book §appendix). Statistical PASS + dogfood-FAIL is the most insidious failure mode for a memory product.
  - **Process**:
    1. Implementer signals Wave 2 release ready (Tasks 1-16 done, eval gate GREEN)
    2. Rodc runs 5 real conversations on real topics over a 3-day window — career / life / technical / a deliberately fresh-topic / a continuation-of-prior-thread (so all categories surface)
    3. After each, Rodc reads:
       - Did the injection block contain RELEVANT cards? (precision feel)
       - Did the AI reference them naturally without sounding meta? (integration prompt feel)
       - Did the ⚡ callout fire correctly when reference happened? (callout discipline)
       - Was there ANY moment where the AI awkwardly referenced something user did not say? (the trust-killer signal)
    4. Rodc records subjective verdict per round: PASS / WEAK / FAIL with one-line note
  - **Outcome resolution**:
    - 4-5 PASS / 0-1 WEAK / 0 FAIL → ship Wave 2
    - ≥ 2 WEAK or ≥ 1 FAIL → raise Rodc for one of: revise threshold, revise integration prompt, revise scoring formula, accept calibration debt + monitor production
  - This gate is human-judgment; implementer marks Task 16 done with `awaiting_subjective_dogfood`; Rodc closes Task 17 manually after dogfood completes.
  - (No code change.)

---

## Injection format (locked variant — proposed 3, recommend Variant 2)

The format the user never sees but the AI does. Three variants explored; Variant 2 recommended.

### Variant 1 — Bullet-list, neutral header (REJECTED)

```
Past thinking from this user's vault, possibly relevant to current message:
- 换工作 — 担心业务收缩 / 期望:更好机会 / 开放问题:如何在不完美中选择
- 副业 (Sept 3, 2 weeks ago) — 担心:200 hours sunk / 期望:reclaim 6h/week
- 哲学兴趣 — topic only, no concern/hope/question
```

**Rejected because**: "Past thinking from this user's vault" is meta-commentary — the AI may echo similar phrasing back to the user (banned per voice-guide §4 don't #4 + §3 sample passage 2). Header risks AI saying "looking at your past thinking…" which is the failure mode we're avoiding.

### Variant 2 — Tagged context, no meta header (RECOMMENDED — LOCKED)

```
[Context: things the user has worked through before, that may bear on what they say now. Use only if naturally relevant; do not mention this list directly.]

Topic: 换工作 (5 days ago, this conversation)
  Concern: 业务收缩
  Hope: 更好机会
  Question: 如何在不完美中选择

Topic: 副业 (Sept 3, different conversation)
  Concern: 200 hours sunk
  Hope: reclaim 6h/week

Topic: 哲学兴趣 (2 weeks ago, different conversation)
  (no other fields)

[End context]
```

**Recommended because**:
- Square-bracket meta tag clearly separates SYSTEM-LEVEL context from the AI's voice — model is less likely to echo the wrapper as user-facing prose
- "Use only if naturally relevant; do not mention this list directly" is the explicit instruction echoed in `rodix_system.md` Past thinking integration section (Task 11) — belt-and-suspenders
- 4-field structure mirrors the user-facing card view exactly (topic / concern / hope / question per brand-book Decision 1) — model is already trained-by-prompt to think in those four fields after `claim_extractor.md`
- Date + scope ("5 days ago, this conversation" / "different conversation") gives AI temporal anchoring without saying meta things to the user
- Null-skip (the third card has only topic) reflects null-by-default discipline (brand-book Decision 5) — a 1-field card is the product working correctly, not a degraded state
- Token budget: ~70-100 tokens per card × 3 cards + wrapper = ~250-350 tokens (under the 450 token budget; leaves headroom for variation)

### Variant 3 — Inline narrative, conversational (REJECTED)

```
The user has been thinking about: 换工作 (this week — worried about 业务收缩, hoping for 更好机会, asking how to choose in imperfect options); 副业 (early Sept — sunk 200 hours, hoped to reclaim 6h/week); 哲学兴趣 (2 weeks ago — open).
```

**Rejected because**: too narrative — the AI may copy the structure verbatim into its reply ("I see you've been thinking about…"). Risks the same meta-commentary banned phrase. Variant 2's tagged structure is harder to echo accidentally.

**LOCKED**: Variant 2. Validate against Haiku 4.5 context window (200K tokens) — easily within budget. Validate against nvidia free model (32K tokens) — 350 tokens is 1% of context, no concern.

---

## Done criteria

- [ ] `#claim-extraction` v1.8 production hallucination ≤ 5% sustained for 3+ days BEFORE this plan dispatches ✓
- [ ] Reuse `app/shared/recall/orchestrator.py::Orchestrator` infrastructure (no parallel system) ✓
- [ ] Read from `chat_claims` (`chat_claim_adapter.get_recent_chat_claims_in_conversation` + cross-conv SELECT) AND `cards` (FTS5) ✓
- [ ] v0 algorithm: substring + bigram + recency + decay; threshold = 0.65 (`ThresholdConfig.topic`) ✓
- [ ] Top-3 cap, with min-threshold per card; null-by-default (return 0 cards rather than wrong cards) ✓
- [ ] Injection format Variant 2 (locked) appended to `_RODIX_SYSTEM_PROMPT` per request ✓
- [ ] `rodix_system.md` extended with `## Past thinking integration` section (banned-phrase list for AI: "I see in your vault…", "looking at your records…", "based on what I remember…") ✓
- [ ] `GET /api/recall/by_message/{id}` polling endpoint (Wave 2 temp; SSE/WebSocket upgrade flagged for Wave 3+) ✓
- [ ] Frontend renders ⚡ "我把这个带回来了" / ⚡ "I brought this back" callout + 4 action buttons (`用上了 / 不相关 / 已经想过 / 跳过`) — both copy AND buttons match brainstorm 2026-05-01 `#8` micro-adj 2 lock + brand-book §7b first item ✓
- [ ] Existing Wave 1b placeholder header AND placeholder buttons PATCHED to locked copy (closes brand-book §7b first-item gap) ✓
- [ ] Reply-references-card detection + dual recall_event logging (referenced + silent_injection) so Wave 2.1 can compute "injected vs referenced" rate ✓
- [ ] Recall injection log line per call (`recall_injected conversation_id=…`) — alpha-observable per IA-C cascade caveat ✓
- [ ] **60-case eval set committed** (fixtures/) — incl. 4 categories ✓
- [ ] **Asymmetric precision gate — all 4 assertions hold** (precision ≥ 80% LOAD-BEARING / top-1 precision ≥ 85% / empty-vault zero injections / recall ≥ 50% MONITOR) OR Rodc-signed-off temporary threshold ✓
- [ ] Tests green: full app suite + new unit + integration eval ✓
- [ ] **Rodc 5-round subjective dogfood gate** (Task 17) — 4-5 PASS / 0-1 WEAK / 0 FAIL on real conversations OR Rodc-recorded mitigation ✓
- [ ] **Scenario verification**: S-CARD-3 (Active Recall trigger — the canonical scenario for this feature, currently flagged as Wave 1b dependency-marker; this plan substantiates it), S-CHAT-1 / S-CHAT-5 / S-CHAT-6 (multi-round depth — recall must not interfere with C-2.2 phase rules), S-CROSS-3 (delete vault card → recall does not surface deleted card), and NEW scenario S-CARD-5 to be added during Task 12 covering empty-vault no-injection + no-callout silent path PASS ✓

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位:plan 中 N/A(use "Rodix" verbatim per `project_rodix_name.md`)
2. ✓ Desktop-first:N/A(invisible feature; callout UI verified at desktop only Phase 1 per `project_device_priority.md`)
3. ✓ §7.4 5 项 articulated
4. ✓ Pre-mortem 4 modes:like-me ✓ / metric vs goal ✓ (precision asymmetric over engagement / recall) / reactive vs strategic ✓ (the wedge feature, not reactive) / edge vs main(empty vault is a main-path, not edge — covered by `#3a` 4-tier cold start AND by Task 5 explicit empty-vault test)
5. ✓ 桌面横向利用率:N/A
6. ✓ Mobile responsive:N/A(backend; callout banner is responsive — leverages existing message-bubble styling per `#3a`)
7. ✓ Empty state:由 `#3a` 4-tier cold start cover (vault empty path) + Task 5 verify

## Post-launch follow-ups (P2)

- **Wave 2.1: threshold calibration from production telemetry**. Once 30 days of real recall_event data exists, run threshold sensitivity analysis: at what threshold does `user_action='not_relevant'` rate drop below 25% sustained? Below 15%? Adjust the 0.65 default if data supports.
- **Wave 2.1: alpha-observability log-grep verification** (parallel to claim-extraction Task 14): Rodc grep server stderr for `recall_injected` lines + `recall_callout_fired` lines + `recall_silent_injection` lines and confirm cadence matches expectation (3-7 callouts per 100 thoughtful messages, ballpark — adjust based on alpha cohort behavior).
- **Wave 2.1: silent-injection vs referenced rate metric**. If silent injections > 50% of total injections, the AI integration prompt addition (Task 11) needs revision. Possible failures: AI ignores the recall block; AI integrates but doesn't reference topics overtly enough for substring detection; topic field too short for substring match (try also matching against concern/hope/question?). All require Wave 2.1 product-data analysis.
- **Wave 3+: embedding-based scoring fallback** if v0 substring+bigram precision fails the 80% gate. Out of scope here; the door is left open by the source-agnostic Candidate dataclass (Task 4).
- **Wave 3+: explicit "let's start fresh" / "forget that" intent detection**. v0 deliberately does not gate on user-explicit-forget signal — this requires either a 5th intent class or a dedicated forget-detector. Risk if missing: when user explicitly says "let's pretend we never talked about that," recall still surfaces the prior card → trust collapse. Mitigation interim: callout `不相关` button gives user explicit suppress affordance per-recall.
- **Wave 3+: SSE/WebSocket upgrade for `/api/recall/by_message/{id}`** (parallel to `#realtime-claim-delivery` debt — share the same future spec).
- **Wave 3+: per-conversation scope toggle**. Today: cross-conversation always. Future: user-explicit "scope to this conversation only" mode (settings toggle). The Candidate `source` tag (chat_claim_in_conv / chat_claim_other_conv / mcp_card) makes this filter trivial to add later.

## Rollback plan (NEW v1.1 per reviewer Edit 1)

**Env-var seam:** `THROUGHLINE_RECALL_INJECTION_ENABLED` (default ON in production, OFF in tests). Gate the `recall_inject.run()` call site in `/api/chat` handler around:

```python
if not _env_bool("THROUGHLINE_RECALL_INJECTION_ENABLED", default=True):
    injection = RecallInjection(cards=[], block_text="", scores=[])
else:
    injection = recall_inject.run(...)
```

**Rollback path (production):**
1. Operator sets `THROUGHLINE_RECALL_INJECTION_ENABLED=0` in environment.
2. Process picks up env on next config reload (or restart — assume restart cadence < 5 min in alpha).
3. Chat handler reverts to pre-Wave-2 behavior: no system-prompt suffix, no recall events logged for injection, no callout cache writes.
4. Existing `recall_events` rows preserved (no destructive mutation); telemetry can compare pre-disable vs post-disable behavior.
5. **Total time-to-recover: < 5 minutes** (config flip + reload). Compare to no-rollback path: 24-50 hours including code deploy + test gates. The env-var seam matches the load-bearing brand-existential signal.

**Rollback path (test):**
- All test fixtures default `THROUGHLINE_RECALL_INJECTION_ENABLED=0` to preserve Wave 1b chat behavior in unaffected tests.
- Tests that exercise recall explicitly set `monkeypatch.setenv("THROUGHLINE_RECALL_INJECTION_ENABLED", "1")`. (Per Wave 1b test-env-var-leak fix pattern in `feedback_test_state_leak_pattern.md`: every fixture calling `server.build_app()` must scope its own env vars.)

**Schema rollback:** N/A. This spec adds NO schema migration; only `recall_events` writes (existing v4 schema supports). Rollback leaves DB intact.

**Failure-mode rollback:** if `THROUGHLINE_RECALL_INJECTION_ENABLED=0` is set but a deployed code path still attempts to read recall data (e.g., frontend polls `/api/recall/by_message/{id}`), the polling endpoint returns `{ready: True, callout: None}` (silent path). No client-side error.

**What rollback does NOT solve:** if alpha cohort already saw the ⚡ "我把这个带回来了" callout on a wrong card and trust collapsed for that user, env-var disable does not retroactively fix the perception. Rollback prevents NEW wrong calls; doesn't undo prior ones. This is the cost of brand-existential signals — they're hard to un-see.

---

## Risk register

| Risk | Likelihood | Impact | Mitigation | Source assumption |
|---|---|---|---|---|
| Wrong card injected (low precision) → AI awkwardly references → trust collapse | MEDIUM (W17 + S16 not yet validated) | CRITICAL (brand polarity flip) | 80% precision gate + null-by-default + threshold 0.65 + top-1 ≥ 85% | W17, S16 |
| Silent injection rate >50% (cards reach AI but AI never references) | MEDIUM (untested) | MEDIUM (telemetry waste, no user-visible harm) | Wave 2.1 calibration trigger; revise integration prompt / threshold | OPEN-2 |
| Empty vault for new user → no recall ever fires → no aha → user perception "this is just ChatGPT" | HIGH (cold start guaranteed) | MEDIUM (mitigated by `#3a`) | Covered by `#3a` 4-tier cold start; v0 task 5 verifies zero-error empty-vault path | W11, W13 |
| `chat_claims` and `cards` table conflict — duplicate / contradictory entries (chat-time extraction + history-import on overlapping topic) | LOW (Wave 1b ships chat_claims; Wave 2 history-import lands separately) | LOW | Source tagging in Candidate; if duplicates, score takes max — no extra dedup logic for v0; Wave 2.1 if observed | n/a |
| User explicitly says "forget that" but recall still surfaces | MEDIUM (no v0 detection) | MEDIUM (trust hit, but recoverable via `不相关` button) | Wave 3+ explicit forget-mechanic; v0 mitigation = `不相关` callout button | edge case 4 |
| Latency budget exceeded (>200ms per chat call) | LOW (FTS5 + lightweight scoring, no LLM) | MEDIUM (chat feels slow) | p95 latency assertion in Task 8; FTS5 already proven sub-second at 10k cards (per `app/shared/storage_py/perf/bench_fts.py`) | n/a |
| Recall fires too often → callout-fatigue → "noise" | MEDIUM (no production data) | MEDIUM (long-term retention loss) | Frequency caps Wave 2.1 (deferred per OPEN-3); v0 hard cap = 3 cards per turn but no per-day cap on injection-side | W17 |
| Concurrent retrieval (user types fast / racing chat turns) | LOW | LOW | SQLite is serialized at server level; FTS5 read-only; no race | edge case |

## References

- Scenarios: S-CARD-3 (Active Recall — the canonical for this feature), S-CHAT-1, S-CHAT-5, S-CHAT-6, S-CROSS-3, NEW S-CARD-5 (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`)
- Hard dependency: `#claim-extraction` v1.8 — recall reads `chat_claims`. Production hallucination must stay ≤ 5% sustained ≥ 3 days before this plan dispatches.
- Brand: `docs/superpowers/brand/brand-book-v1.md` §1 (canonical pitch — recall makes "remembers your thinking" load-bearing) + §7 Decision 3 (verb = "bring back" not "surface" — locked) + §7b first item (recall callout placeholder gap CLOSED by this spec) + §appendix item 4 (surveillance-fail-mode polarity flip = the trust-killer signal).
- Voice: `docs/superpowers/brand/voice-guide.md` §3 don't #4 (banned phrases AI must not use when referencing past cards) + §3 sample passage 2 (founder essay register applies to AI integration prompt) + §A locale notes (Chinese needs more discipline than English).
- Position: `docs/superpowers/brand/position-strategy.md` §3.3 Bet 3 (active recall is one of 4 architectural commitments — Wave 2 unlocks the position).
- Assumptions: `docs/superpowers/research/assumption-list.md` S16 (recall callout perceived as helpful not surveillance — UNVALIDATED, this spec validates) + W11 (vault retention) + W13 (multi-week return pattern) + W17 (recall density risk — surveillance polarity flip).
- Prior art:
  - `app/shared/recall/orchestrator.py` — `Orchestrator` + `ThresholdConfig.topic = 0.65` reused, NOT cloned
  - `app/shared/recall/evaluators/topic.py` — FTS5 pattern + `_normalize_score` exponential CDF reference for Wave 2.1 if needed
  - `app/shared/storage_py/chat_claim_adapter.py::get_recent_chat_claims_in_conversation` — primary chat_claims accessor
  - `app/shared/storage_py/fts.py::search_cards_fts` — MCP cards FTS5 path
  - `app/shared/storage_py/recall_event_adapter.py::log_event` — telemetry path (existing `RecallEvent` schema accepts `selected_card_id` + `candidate_card_ids` + `selection_reason` — fields are spec-compatible)
  - `app/web/server.py:1286` `/api/chat` handler — modify in-place per Task 8
  - `app/web/prompts/rodix_system.md` — extend with `## Past thinking integration` section per Task 11
  - `app/web/static/app.js:580` — placeholder header patched per Task 12
  - `app/shared/extraction/extractor.py` — split-route env-var seam pattern (`THROUGHLINE_EXTRACTION_PROVIDER`) is the model for any v0.1 model-pinning of recall (not needed v0)
- Roadmap: Wave 2 P0 (the load-bearing Wave 2 deliverable per brand-book §7 Decision 3 + position-strategy §3.3). Unblocks: real Bet 3 marketing claim ("active recall"), brand-book §7b first item recall-callout-copy gap, position-strategy §3.3 active-recall architectural commitment substantiation. Blocks: future `#vault-recall-history` spec (the recall_count field needed for Wave 2.1 dedup tracking), `#realtime-claim-delivery` spec (Wave 3+ SSE/WebSocket — same migration target as `#claim-extraction` polling).
- 协议 §5.1: `#active-recall-base` is P0 Wave 2; downstream Wave 2.1 calibration items are P1; Wave 3+ items are P2.

---

*End spec-active-recall-base.md v1 — pending Rodc + external Opus review per `feedback_plan_review_protocol.md`. Implementer dispatch blocked until v1.X "approved for dispatch."*
