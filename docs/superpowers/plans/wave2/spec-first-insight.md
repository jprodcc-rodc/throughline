# `#2b` first-insight 钩子 — Implementation Plan

> **Status (Wave 2 spec, draft v1.0, 2026-05-03):** Spec-only; not yet dispatched. Awaiting Rodc review (per `feedback_plan_review_protocol`) → external Opus review → push backs → v1.X "approved for dispatch" → implementer subagent.
>
> **Type-A escalation flagged at top:** the *threshold value* (3 / 5 / 7 / 10 cards) is the load-bearing product-strategy decision, not a tunable. Default 5 documented; 3 / 7 alternatives reasoned below; Rodc must lock before dispatch. See "Type-A escalation" addendum at bottom.
>
> **For agentic workers:** Use `superpowers:test-driven-development` per task. Then `superpowers:subagent-driven-development` extended with `docs/superpowers/skills/scenario-verification.md`.
>
> **App/ gitignored** — `app/shared/insight/` + `app/web/server.py` + `app/web/static/app.js` modifications do NOT go to git. Skip the per-task `Commit ...` lines for those files. `fixtures/` artifacts (eval set + golden tests) DO commit.

**Goal:** When a user reaches a vault-accumulation milestone, surface a single reflection that connects the *thread* across their recent thinking — the canonical pattern from `founder-narrative-arc.md` Part 3 P1: *"Three cards came back, dated September 3, September 19, October 4. Reading them back-to-back, the pattern was suddenly obvious in a way it never was inside any single conversation."* This is the brand's load-bearing aha moment that ChatGPT memory and Gemini personalization structurally cannot ship — continuity-of-thought made visible. **Done 标准: ≥1 first-insight surface per persona by Day 7-10 in Tier 1.5 dogfood; Sarah Day-15 emotional_rambling cluster does NOT trigger insight; production "useful" rate ≥ 70%.**

**Architecture:**

1. **Trigger evaluator** — runs after every successful claim persist (i.e., after `extraction_queue` task handler calls `insert_chat_claim`). Reads `count_chat_claims` and the most-recent N claims via `get_recent_chat_claims_in_conversation` *across* conversations (extend adapter if needed). If conditions are met, enqueue an insight-generation task.
2. **Skip-conditions gate** — same-topic cluster check + single-conversation cluster check + sensitive-content check + frequency-cap check. **Precision >> recall.** Better silent than tone-deaf.
3. **LLM insight synthesizer** — wrapper that builds a *Variant C* prompt (canonical voice; see "Reflection format" below) over the recent N cards and asks for one short reflection. Same `_resolve_llm_config` provider stack as `#claim-extraction` (split-route: free model in chat, Haiku 4.5 for synthesis).
4. **Insight event log** — new SQLite table `insight_events` (FK message_id of triggering claim, FK conversation_id, surfaced_at, dismissed_at, user_action, fingerprint of cards-set). Used to (a) frequency-cap, (b) avoid surfacing the same pattern twice, (c) telemetry for "useful rate" gate.
5. **UI surface** — new card variant ⌘ in chat stream (Option D below) — distinct icon, amber border to stay within brand-book §6 visual envelope, with 4 user-action buttons matching ⚡ recall callout shape.

**Tech Stack:** Python · `_resolve_llm_config` (same as classifier + extractor) · existing `chat_claim_adapter.py` (extended with cross-conversation accessor) · NEW `insight_events` adapter + table · background trigger after extractor persist · render hook in `app.js`.

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | New chat-stream card variant ⌘ "I noticed a thread" — amber border (per §6 visual lock), distinct icon (Lucide `git-branch` or `route`, line stroke 1.5px, NOT ⚡), 1-2 sentences body + 4 action buttons. |
| 产品策略假设 | First-insight is **the** brand-defining moment per `founder-narrative-arc` Part 3 P1. ChatGPT memory cannot ship this; Gemini cannot; Claude projects cannot. Rodix can because the four bets (white-box cards / cross-model / active recall / real export) compose into "your thinking compounded across cards" — and that composition is what the user feels when 5 cards become one observed pattern. |
| 适合 / 不适合 | **适合**: heavy AI users who reached vault threshold; specifically the friends-intro 4-condition self-selection list. **不适合**: chitchat users (will never hit threshold; if they did via long single-topic clusters, skip-conditions silence it); users in crisis (see "Sensitive content" edge case + Wave 1c crisis protocol dependency). |
| Trade-off | + delivers the canonical aha demonstrated in founder-narrative-arc / + closes the brand-promise loop ("Rodix remembers your thinking" becomes felt, not asserted) / − one wrong-feeling insight breaks brand worse than a missed one (precision >> recall) / − extra LLM call cost / − new event table + UI surface + skip-conditions all interact (cascade-failure surface area) |
| 最大风险 | **Tone-deaf insight on sensitive cluster** — vault dominated by `emotional_rambling` recent activity (Sarah Day-15 wine-moment scenario per Tier 1.5 spec) → insight surfaces "you've been thinking about feeling lost" → user reads as cold pattern-naming on real distress. **缓解**: skip-conditions §5.3 + crisis-content protocol dependency (Wave 1c gate) + production "useful" rate ≥ 70% gate + dogfood Sarah Day-15 scenario MUST verify silence. |

## Ambiguity flag

✓ **TYPE-A ESCALATION on threshold value (3 / 5 / 7 / 10).** Default 5 chosen below with reasoning. Locked decisions for everything else; Rodc decides threshold before dispatch.

Locked decisions:
- **Reflection format**: **Variant C** (founder-narrative-arc-style: dated-card retrospective). Reasoning below in "Reflection format" section.
- **UI placement**: **Option D** (distinct chat-stream card variant ⌘ "I noticed a thread" — amber border per §6, distinct line-icon, 4 action buttons). Reasoning below in "UI placement" section.
- **Trigger gate model**: same provider as extractor (split-route via `THROUGHLINE_INSIGHT_PROVIDER` env-var seam, default `anthropic` → Haiku 4.5; reuses `_resolve_llm_config` lessons from `#claim-extraction` v1.8 — defensive JSON parsing, `max_tokens >= 3000`, no `response_format: json_object`).
- **Frequency cap**: max 1 surface per 7 calendar days (rolling, per-user), regardless of vault growth velocity. Hard rule, NOT tunable in Wave 2.
- **Single-conversation cluster handling**: if 5 most-recent cards share a `conversation_id`, skip — they are not 5 thinking moments. (Per critical edge case.)
- **Same-topic cluster handling**: if 5 most-recent cards have substring or bigram-overlapping `topic` fields, skip — boring, not insight. (Per critical edge case.)
- **Sensitive content gate**: if any of the 5 most-recent cards has `concern` field matching crisis-content keywords (per Wave 1c crisis protocol), skip insight entirely. (Per brand-book §7 Decision 7 + §7b crisis-content handoff.)
- **Asymmetric gate**: precision >> recall. Better silent than tone-deaf. Production "useful" rate ≥ 70% (Variant D action: "thanks" / "saved" / "interesting") OR raise to Rodc.

## TYPE-A escalation: threshold value

**Default 5; alternatives 3 and 7 documented for Rodc review.**

| Threshold | Pros | Cons | When to pick |
|---|---|---|---|
| **3** | Earlier first-aha; tight loop on cold-start magic | Premature — user hasn't built up enough thinking; 3 cards is often "noise plus one real thing"; risks tone-deaf because 3 cards rarely contain a *thread*; same-topic clusters more likely to dominate at low N | Pick if dogfood signal: users churning before Day 7 because nothing felt magical |
| **5 (default)** | ≈ 1 week of moderate use; large enough to actually contain a pattern; small enough that user hasn't faded; founder-narrative-arc canonical example uses 3 cards but those cards are *across 4 weeks* — at Phase 1 weekly cadence, 5 cards ≈ 1 week of thinking moments | Some users will reach 5 in single conversation (skip-conditions handle this); some users may want it sooner | **Phase 1 default** per "5 ≈ 1 week of moderate use" + precision>>recall posture |
| **7** | Strongest signal-density; almost certain to contain a real pattern; aligns with weekly-cadence aha cycle | Many users fade before 7 → first-insight surface never fires → brand promise undelivered → "Rodix is just ChatGPT but slower" | Pick if Wave 1b dogfood signal: users complain "why is Rodix surfacing trivial connections so early" |
| **10** | Maximum signal-density; only fires for committed users | Vast majority of alpha users never see it; brand magic moment becomes vapor; defeats purpose | Don't pick at Phase 1 |

**Reasoning for default 5**:
- Per `assumption-list.md` S1: heavy AI users (~2-3 hours/day across multiple providers) accumulate cards faster than casual users — but Rodc's friends-intro side-project example is *one user across 4 weeks*. The cadence calibration should reflect that thinking-partner use is dense, not constant.
- 5 cards ≈ 1 typical week assuming 1-2 thoughtful conversations per day with claim extraction firing on ~50% (not all thoughtful → 4-field card; many sparse). Tier 1.5 personas reach 5 cards at Day 7-10.
- Precision-asymmetric: a wrong-feeling 3-card insight ("your thinking has touched Python and oranges and your mom") breaks brand more than 5-card insight ("this past week you've worked through three angles on the side-project decision: cost, signal, just-decide"). Higher N = more material = denser thread = lower hallucination risk.

**Calibration trigger (Wave 3)**: if Phase 1 alpha telemetry shows <40% of weekly-active users hit threshold by Day 14, Rodc revisits to consider lowering to 3. If >30% of triggered insights get "not now" / dismiss action, Rodc revisits to raise to 7.

## Reflection format

Three variants explored; Variant C recommended.

**Variant A — neutral pattern-naming**:
> "Looking at your last 5 cards, there's a thread: you've been thinking about [topic A], [topic B], and [topic C]."

Verdict: **fail voice-guide §6 Q4** — "looking at your last 5 cards" is meta-reportage register; would not pass Rodc-recognizes-as-his-own-writing. The phrase "there's a thread" is acceptable but the lead-in is generic SaaS-product voice ("Here's what we noticed about you!"). Reads like a weekly-summary feature.

**Variant B — poetic synthesis**:
> "A pattern in your recent thinking: [synthesis]"

Verdict: **fail voice-guide §1 Refuses-to-dramatize** — "A pattern in your recent thinking" is exactly the kind of phrasing that drifts toward LinkedIn founder-coach voice ("Here's a profound observation about *you*..."). Too curated, too declarative-without-evidence.

**Variant C (recommended) — founder-narrative-arc retrospective**:
> "Three cards from the past week: [topic 1], [topic 2], [topic 3]. Reading them back-to-back, [observation about the pattern]."

Verdict: **passes voice-guide §6 all five Qs**:
- Q1 parenthetical/em-dash precise ✓ (em-dash for the second sentence's pivot)
- Q2 negation positioning ✓ (implicit — the "single conversation" the user could have had any single time is what's being negated by *back-to-back*)
- Q3 specific quotes/dates ✓ — three card topic phrases, the canonical "back-to-back" phrasing from the friends-intro
- Q4 Rodc-recognizes-as-his-own ✓ — this is *literally* the friends-intro Part 3 P1 cadence ("Three cards came back, dated September 3, September 19, October 4. Reading them back-to-back, the pattern was suddenly obvious...")
- Q5 unfit user sent away ✓ — N/A here (insight only fires for already-fit users who reached threshold), but the surface respects user agency: 4 buttons including "not now"

**Voice ceilings** (per voice-guide §B):
- Body 2-3 sentences (Variant C is 2)
- ≤ 50 words total
- No "leverage" / "harness" / "unlock" / "supercharge" / "transform" / "surface" / "I'm here for you"
- Em-dash precise; parenthetical only if it carries honesty (e.g., "(your thinking went somewhere — three weeks of cards confirm it.)" — though usually no parenthetical needed)
- Date qualifiers: use card timestamps verbatim (`9月3日 / 9月19日 / 10月4日` or `Sept 3 / Sept 19 / Oct 4`) per voice-guide Q3 specific-over-abstract

**LLM prompt template** (frozen at `app/shared/insight/prompts/insight_synthesizer.md`):
- Input: 5 most-recent ChatClaimRow shapes (topic / concern / hope / question / created_at)
- Output JSON: `{cards_referenced: list[claim_id], topics_mentioned: list[str, max 3], observation: str (1 sentence, 6-25 words), confidence: 0.0-1.0}`
- Instruction: emit Variant C structure; quote topic verbatim from card.topic field; do NOT paraphrase; if observation feels generic ("you've been thinking a lot"), set confidence < 0.5 and surface NOTHING (server-side gate); if 3 cards' topics are all the same word, return `{confidence: 0.0, reason: 'same_topic_cluster'}` (boring, not insight).
- Same defensive JSON parsing as `#claim-extraction` v1.8; max_tokens 3000.

---

## Files

**Modify** (gitignored — no commit):
- `app/web/server.py` — extraction-queue post-persist hook: after `insert_chat_claim`, call `_maybe_trigger_insight(message_id)`. Add `GET /api/insight/by_event/{insight_event_id}` for frontend rendering. Add `POST /api/insight/{insight_event_id}/action` for the 4 user-action buttons.
- `app/web/static/app.js` — render `⌘ I noticed a thread` chat-stream card on insight event delivery; wire 4 action buttons (`thanks` / `saved` / `not now` / `interesting`); poll `/api/insight/by_event/{id}` similar to existing claim polling.
- `app/web/test_chat_insight.py` — integration test for chat → extraction → trigger → insight surface (gitignored, lives in `app/web/`).

**Create** (gitignored — no commit):
- `app/shared/insight/__init__.py` — public exports
- `app/shared/insight/trigger.py` — `should_surface_insight(conn, message_id) -> InsightDecision` (encapsulates: count threshold, frequency cap, single-conversation cluster check, same-topic cluster check, sensitive-content check)
- `app/shared/insight/synthesizer.py` — `Synthesizer.synthesize(cards: list[ChatClaimRow]) -> InsightSynth` (Haiku 4.5 prompt + JSON parse + confidence gate)
- `app/shared/insight/insight_event_adapter.py` — SQLite adapter for new `insight_events` table (mirror shape of `chat_claim_adapter.py`)
- `app/shared/insight/prompts/insight_synthesizer.md` — frozen prompt
- `app/shared/insight/test_trigger.py` — unit tests for skip-conditions
- `app/shared/insight/test_synthesizer.py` — unit tests with mock LLM
- `app/shared/insight/test_insight_event_adapter.py` — adapter CRUD tests

**Create** (tracked — commit normally):
- `fixtures/v0_2_0/eval/insight_skip_cases.json` — 30 cases × {`category`, `cards: list[ChatClaimRow-shape]`, `expected_decision`, `notes`} for skip-condition eval. Categories: `should_trigger`, `same_topic_cluster`, `single_conversation`, `sensitive_content`, `recent_cap`, `low_density`.
- `fixtures/v0_2_0/eval/insight_synthesis_cases.json` — 20 cases of 5-card windows + golden Variant C output ranges for golden-style synthesis eval.
- `fixtures/v0_2_0/eval/run_insight_eval.py` — runner mirrors `run_claim_extraction_eval.py` shape; emits `metrics_by_category.{should_trigger,sensitive_content,...}` + overall.
- `fixtures/v0_2_0/eval/insight_synthesizer_prompt.txt` — frozen prompt copy.

**Schema migration** (DDL, additive):
- New table `insight_events`:
  ```sql
  CREATE TABLE IF NOT EXISTS insight_events (
    id TEXT PRIMARY KEY,                        -- ie-...
    triggered_by_message_id TEXT NOT NULL,      -- the chat claim that caused threshold cross
    conversation_id TEXT,                       -- FK conversations.id; nullable (cross-conversation insights)
    cards_referenced TEXT NOT NULL,             -- JSON list of cc-... ids
    observation TEXT NOT NULL,                  -- the rendered Variant C body
    confidence REAL NOT NULL,                   -- 0.0-1.0
    surfaced_at TEXT NOT NULL,                  -- ISO 8601
    dismissed_at TEXT,                          -- ISO 8601, nullable
    user_action TEXT,                           -- thanks|saved|not_now|interesting|null
    fingerprint TEXT NOT NULL,                  -- hash of sorted cards_referenced for dedup
    UNIQUE(fingerprint)                         -- prevents same-pattern resurface
  );
  ```
  Apply via additive migration; do NOT touch `chat_claims`. `chat_claim_adapter.get_recent_chat_claims_across_conversations` accessor will also be added (extends existing module).

## Prerequisite gate

**Do not start Task 1 until**:
1. `#claim-extraction` Phase 1 ship gate is GREEN (already met per v1.8 split-route evidence — 79.3% overall, 2.3% hallucination on 256 EN field decisions).
2. **Type-A threshold escalation resolved by Rodc** (see top of spec + addendum below).
3. **Wave 1c crisis-content protocol decision recorded** — even if implementation is post-launch, the *detection trigger* (keyword list / classifier extension) must be defined so first-insight skip-conditions §5.3 can reference it. If Rodc decides Wave 1c is post-launch, then first-insight Wave 2 ships with a *placeholder keyword list* (US 988 / "kill myself" / "don't want to live" / "no point" / "我不想活" — covering the explicit-language failure mode) and a TODO marker pointing to Wave 1c spec.

## Bite-sized TDD tasks

- [ ] **Task 1: Trigger evaluator — happy-path threshold cross**
  - Write failing test `test_trigger.py::test_threshold_5_triggers_when_5_cards_across_conversations` — given 5 cards, all distinct conversation_ids, all distinct topics, no recent insight in 7 days → returns `InsightDecision(should_surface=True, cards=[...5 ChatClaimRow])`.
  - Implement `trigger.should_surface_insight(conn, message_id) -> InsightDecision`. The decision dataclass: `{should_surface: bool, reason: str ('triggered'|'below_threshold'|'recent_cap'|'same_topic_cluster'|'single_conversation'|'sensitive_content'|'low_density'), cards: list[ChatClaimRow]}`.
  - Reads `count_chat_claims(conn) >= THRESHOLD` (default 5; pluggable via env `THROUGHLINE_INSIGHT_THRESHOLD`, integer, clamp [3, 10]). Reads recent N via new `get_recent_chat_claims_across_conversations(conn, limit=THRESHOLD)`.
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 2: Skip — same-topic cluster**
  - Write failing test `test_trigger.py::test_same_topic_cluster_skips` — given 5 cards all with topic substring containing "换工作" (or shared bigram on English topic) → returns `InsightDecision(should_surface=False, reason='same_topic_cluster')`.
  - Implement substring-overlap heuristic v1: lowercase both topics, strip punctuation, check if any pair has min(len(a), len(b)) >= 3 substring-shared. Or compute bigram set overlap > 0.5.
  - Document the heuristic in code comment + flag for Wave 3 LLM-judged-equivalence upgrade if precision-eval shows misclassification.
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 3: Skip — single-conversation cluster**
  - Write failing test `test_trigger.py::test_single_conversation_cluster_skips` — given 5 cards all sharing one `conversation_id` → returns `InsightDecision(should_surface=False, reason='single_conversation')`. (Distinct topics within one chat session = one thinking moment, not 5.)
  - Implement: if `len(set(c.conversation_id for c in cards)) == 1`, skip.
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 4: Skip — recent-insight frequency cap**
  - Write failing test `test_trigger.py::test_recent_insight_within_7_days_skips` — given threshold met but `insight_events` has a row with `surfaced_at` within 7 days → returns `InsightDecision(should_surface=False, reason='recent_cap')`.
  - Implement: query `insight_events` for any row WHERE `surfaced_at >= now - 7 days`; if exists → skip.
  - Add edge case: `dismissed_at IS NOT NULL AND user_action IN ('not_now','thanks')` should NOT extend the cap — that's normal user feedback, not "back off more"; the 7-day cap is rolling regardless of action. Document this; DO NOT implement frequency-back-off in Wave 2 (potential Wave 3 calibration if telemetry shows users tap "not now" repeatedly).
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 5: Skip — sensitive content gate**
  - Write failing test `test_trigger.py::test_sensitive_concern_skips` — given 5 cards where any has `concern` containing crisis keywords (placeholder list: `['kill myself', 'don\'t want to live', 'no point', 'end it', '我不想活', '没意义']`) → returns `InsightDecision(should_surface=False, reason='sensitive_content')`.
  - Implement keyword scan; case-insensitive; substring match. Reuse the Wave 1c keyword list constant (when Wave 1c lands, refactor to import; until then, define locally with TODO marker).
  - Per `assumption-list.md` D1 + brand-book §7b: this is the highest-stakes user-experience surface in the codebase. Sarah Day-15 dogfood scenario MUST verify silence here.
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 6: Skip — same-pattern fingerprint dedup (vault delete-then-readd edge case)**
  - Write failing test `test_trigger.py::test_same_fingerprint_skips` — given 5 cards whose sorted-id-set hashes to a fingerprint already in `insight_events` (user deleted one card, added two more, threshold re-crossed but the same 4 prior cards still dominate) → returns `InsightDecision(should_surface=False, reason='low_density')` (or new reason `repeated_pattern`).
  - Implement fingerprint = `hashlib.sha256(','.join(sorted([c.id for c in cards])).encode()).hexdigest()[:16]`.
  - Edge case rationale: per critical edge case "user has 4 cards, deletes 1, adds 2 more (5 again)" — 80% of cards overlap with prior fingerprint cohort; re-surfacing the same pattern would feel buggy.
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 7: Synthesizer — happy-path Variant C output**
  - Write failing test `test_synthesizer.py::test_synthesize_returns_variant_c_shape` — given 5 distinct-topic distinct-conversation ChatClaimRow → mock LLM returns Variant C JSON → synthesizer returns `InsightSynth(observation="Three cards from the past week: A, B, C. Reading them back-to-back, ...", topics=[A,B,C], confidence=0.8)`.
  - Implement Synthesizer using `_resolve_llm_config('insight')` (falls through to extractor provider via env-var seam; Phase 1 default `anthropic` → Haiku 4.5).
  - Same defensive JSON parsing as `#claim-extraction` v1.8.
  - Locked prompt at `app/shared/insight/prompts/insight_synthesizer.md`, loaded module-level.
  - Confidence gate: if `confidence < 0.6`, return `InsightSynth(should_surface=False, reason='low_confidence')` server-side (LLM saying "I don't see a real pattern here" is the null-default discipline in action).
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 8: Synthesizer — voice-guide §6 Q4 lint at output**
  - Write failing test `test_synthesizer.py::test_voice_lint_rejects_banned_phrases` — given LLM output containing any of: `'I'm here for you'` / `'我在这里'` / `'leverage'` / `'unlock'` / `'transform your thinking'` / `'a profound'` / etc. (full list mirrors `rodix_system.md` banned-phrase list extended for English from voice-guide v2 §4 Don'ts) → synthesizer returns `InsightSynth(should_surface=False, reason='voice_violation')`.
  - Implement post-LLM lint pass; case-insensitive substring match. List lives in `app/shared/insight/voice_lint.py` (new file, exports `BANNED_PHRASES` constant); identical list deduplicated from rodix_system.md banned phrases (factor out in Wave 3 if list grows).
  - Why server-side gate: even with the locked prompt, LLM occasionally drifts; voice-violation = silent skip is better than rendering tone-deaf insight.
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 9: insight_events adapter (DB schema + CRUD)**
  - Write failing test `test_insight_event_adapter.py::test_insert_then_fetch_roundtrips` — insert an InsightEventRow, fetch by id, fields match.
  - Implement `app/shared/insight/insight_event_adapter.py` mirror of `chat_claim_adapter.py` shape. Functions: `insert_insight_event`, `get_insight_event`, `get_recent_insight_events(conn, *, since_iso) -> list`, `update_insight_event_action(conn, id, action) -> bool`.
  - Apply additive migration: detect missing table → create. Run on app start (mirrors existing schema bootstrap pattern).
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 10: Cross-conversation accessor in chat_claim_adapter**
  - Write failing test `test_chat_claim_adapter.py::test_get_recent_chat_claims_across_conversations_returns_newest_first` — insert 8 chat_claims across 3 conversations → call `get_recent_chat_claims_across_conversations(conn, limit=5)` → returns 5 newest sorted by `created_at DESC, rowid DESC`.
  - Implement in `app/shared/storage_py/chat_claim_adapter.py` (extends existing module — does NOT belong to insight module since it's a generic accessor). Mirror style of existing `get_recent_chat_claims_in_conversation`.
  - PASS
  - (No commit — app/ gitignored. The adapter file is also gitignored per `app/shared/storage_py/`.)

- [ ] **Task 11: server.py post-extraction hook**
  - Write failing test `test_chat_insight.py::test_thoughtful_chat_5th_card_triggers_insight_event` — 5 chat turns each producing extracted claim → 5th claim persist triggers `_maybe_trigger_insight(message_id)` → `insight_events` row written → `GET /api/insight/by_event/{id}` returns `{ready: true, observation: ..., topics: [...]}`.
  - Implement `_maybe_trigger_insight` in server.py, called inside the extraction queue's persist callback (after `insert_chat_claim` returns successfully):
    1. `decision = trigger.should_surface_insight(conn, claim_id)`
    2. If `decision.should_surface`: call `synth = Synthesizer.synthesize(decision.cards)`
    3. If `synth.should_surface`: `insert_insight_event(...)`
    4. Else log structured reason and skip.
  - Add `GET /api/insight/by_event/{id}` returning `{ready: bool, event: Optional[InsightEventDict]}`.
  - Add `POST /api/insight/{id}/action` accepting `{action: 'thanks'|'saved'|'not_now'|'interesting'}`; updates `user_action` + `dismissed_at`.
  - Failure mode: synthesizer LLM fail → log + skip; do NOT block chat. (Mirrors `#claim-extraction` v1.8 graceful-degradation posture.)
  - PASS
  - (No commit — `app/web/server.py` gitignored.)

- [ ] **Task 12: Frontend ⌘ "I noticed a thread" card**
  - Write failing browser-shape pseudo-test (manual + scenarios verify): after AI reply renders + claim card swap completes, IF response carried `_insight_event_id: ie-...`, poll `/api/insight/by_event/{id}` (1s interval, 8s timeout — synthesizer is slower than extractor).
  - On poll success: render new chat-stream card variant. Visual:
    - Icon: Lucide `git-branch` (line stroke 1.5px, 16px) — distinct from ⚡ recall
    - Title: "我注意到一条线索" (zh) / "I noticed a thread" (en)
    - Body: Variant C observation rendered verbatim
    - 4 action buttons: `谢谢` / `存下了` / `下次再说` / `有意思` (mapping: `thanks` / `saved` / `not_now` / `interesting`)
    - Border: `--accent-amber` (1px solid; same visual register as ⚡ recall + Card with Promise)
    - Background: same surface as Card with Promise (NOT distinct color — staying within brand-book §6 lock)
  - On 4-button click: `POST /api/insight/{id}/action` with payload, then visually mark card as "✓ 谢谢" (or equivalent per action) and disable buttons.
  - On 8s poll timeout: silent fail; do NOT render error to user. (Insight is bonus; missing it should never feel like a failure.)
  - Add code comment in `app.js` referencing this debt: "Insight surface uses polling — same Wave 3 SSE/WebSocket upgrade applies." (Mirrors `#claim-extraction` Task 8 architectural debt label.)
  - (No commit — app/ gitignored.)

- [ ] **Task 13: Eval harness — skip-conditions correctness**
  - Create `fixtures/v0_2_0/eval/insight_skip_cases.json` with 30 cases distributed:
    - 10 `should_trigger` (5 distinct topics × distinct conversations × no recent cap × no sensitive content)
    - 6 `same_topic_cluster` (5 cards with overlapping topic phrases)
    - 5 `single_conversation` (5 cards sharing conversation_id)
    - 5 `sensitive_content` (any card has crisis-keyword in concern)
    - 2 `recent_cap` (insight_events seeded with within-7-days row)
    - 2 `low_density` (5 cards with confidence-collapse-shaped data — e.g., all topic = single word, or 4 of 5 topics share noun)
  - Each case: `{id, category, cards: list[partial ChatClaimRow], insight_events_seed: list, now_iso, expected_decision: InsightDecision-shape, notes?: str}`.
  - Manual annotation effort: ~1.5h.
  - Extend `fixtures/v0_2_0/eval/run_insight_eval.py` to compute:
    - per-category accuracy (decision matches expected)
    - precision (of 30 cases, what fraction of `should_trigger=True` decisions were correct)
    - recall (of 10 should_trigger cases, what fraction got `should_trigger=True`)
    - **asymmetric gate**: precision >= 95% (skip-conditions must NOT hallucinate triggers); recall >= 70% (acceptable to miss some real triggers in favor of precision)
  - Commit `eval(first-insight): 30 skip-condition cases + asymmetric gate runner` (fixtures IS tracked).

- [ ] **Task 14: Eval harness — synthesizer voice + tone (golden tests)**
  - Create `fixtures/v0_2_0/eval/insight_synthesis_cases.json` with 20 cases × {`cards: list[ChatClaimRow]`, `golden_observation_pattern: str (regex or substring set)`, `must_not_contain: list[str]` (banned phrases per voice-guide §4)}.
  - Each case represents a 5-card window that *should* surface — eval asks "did the synthesizer produce a Variant C-shaped output that quotes topic verbatim, contains an observation, and avoids banned phrases?"
  - Golden checks:
    - `output.observation` matches Variant C structure regex: `r"(\d+|Three|Four|Five) cards?.*: .*\. .*back-to-back.*"` (or its zh equivalent)
    - All 3 topics in `output.topics_mentioned` appear verbatim in `output.observation`
    - No banned-phrase from `BANNED_PHRASES` constant
    - `output.confidence >= 0.6` for the 16 cases that should fire; `confidence < 0.6` for the 4 confidence-collapse cases
  - Asymmetric gate: voice-violation rate ≤ 5% (1 banned-phrase miss per 20 cases acceptable; 2+ FAIL → prompt revision); structural-conformance ≥ 90% (Variant C shape match).
  - Commit `eval(first-insight): 20 synthesis golden cases + voice lint runner`.

- [ ] **Task 15: End-to-end code-level verification**
  - Verify the full pipeline works against mocked LLM:
    - Thoughtful chat × 5 → claim extracted × 5 → 5th persist triggers insight → synthesizer mocked to Variant C → `insight_events` row written → polling endpoint returns observation → frontend renders ⌘ card with 4 buttons (verified via test stub).
    - Same-topic-cluster scenario: 5 cards on "换工作" → trigger evaluator returns `same_topic_cluster` → no synthesizer call → no insight surface (verified).
    - Sensitive-content scenario: card with `concern: 我不想活` in window → trigger evaluator returns `sensitive_content` → no synthesizer call → no insight surface (verified). **This is the Sarah Day-15 dogfood gate.**
    - Frequency-cap scenario: insight surfaced at T-3-days → 6th claim triggers re-eval → returns `recent_cap` → no second insight (verified).
  - Run full app test suite — all green
  - Run eval harness Tasks 13 + 14 — asymmetric gates met OR Rodc sign-off recorded
  - Document the eval result file path in the final report
  - **Flag for Rodc subjective-feel gate** (Task 16 below) — implementer flags Wave 2 release as "code-complete + eval gate met, awaiting Rodc 5-round dogfood + Tier 1.5 Phase B Sarah Day-15 verification"
  - (No commit — app/ gitignored.)

- [ ] **Task 16: Tier 1.5 dogfood validation gate** (independent product-feel check)
  - **Why this is a separate gate**: same logic as `#claim-extraction` Task 15 — statistical PASS + dogfood FAIL is the most insidious failure mode for a brand-defining feature. First-insight is the brand's *load-bearing aha moment*; if it doesn't *feel* like the friends-intro Sept 3 / Sept 19 / Oct 4 example, the brand promise is unfulfilled regardless of eval-pass.
  - **Process**:
    1. Implementer signals Wave 2 first-insight ready (Tasks 1-15 done, eval gates met)
    2. Tier 1.5 dogfood Phase A: each persona (Daniel / Sarah / Mike / Emma) runs through their canonical Day 1-10 sequence; CC verifies first-insight surfaces by Day 7-10 for each.
    3. Tier 1.5 dogfood Phase B sample-verify Round 8 (Sarah Day-15): real Haiku 4.5 + emotional_rambling cluster → MUST silent-skip per skip-conditions §5.3. If insight fires, Wave 2 ship blocker.
    4. Rodc reads the surfaced insight per persona. Verdict per persona: PASS / WEAK / FAIL with one-line note.
  - **Outcome resolution**:
    - 4 PASS / 0-1 WEAK / 0 FAIL → ship Wave 2
    - ≥ 1 FAIL → block; raise Rodc with 4 options:
      - (a) revise prompt (Variant C wording calibration)
      - (b) raise threshold (5 → 7) so insights only fire on richer windows
      - (c) tighten skip-conditions (e.g., require ≥ 4 distinct conversation_ids not just ≥ 2)
      - (d) accept misalignment + telemetry-driven Wave 3 calibration
  - This gate is human-judgment, NOT automatable. Implementer marks Task 15 done with `awaiting_subjective_dogfood`; Rodc closes Task 16 manually.
  - (No code change.)

## Done criteria

- [ ] `#claim-extraction` Phase 1 ship gate GREEN ✓ (already met per v1.8)
- [ ] **Type-A threshold escalation resolved by Rodc** (default 5 / alternatives 3 / 7 / 10) ✓
- [ ] Wave 1c crisis-protocol detection trigger DEFINED (placeholder keyword list acceptable for Wave 2 ship; full spec is Wave 1c) ✓
- [ ] Trigger evaluator: 5 skip-conditions implemented (same-topic / single-conversation / recent-cap / sensitive-content / fingerprint-dedup) ✓
- [ ] Synthesizer: Variant C prompt locked + defensive JSON + confidence gate + voice-violation lint ✓
- [ ] `insight_events` table additive migration ✓
- [ ] Cross-conversation accessor in `chat_claim_adapter` ✓
- [ ] `/api/insight/by_event/{id}` polling endpoint + `/api/insight/{id}/action` ✓
- [ ] Frontend ⌘ "I noticed a thread" card with 4 action buttons + 8s poll timeout silent fail ✓
- [ ] **30-case skip-conditions eval committed** (fixtures/) — 10 trigger / 6 same-topic / 5 single-conversation / 5 sensitive / 2 recent-cap / 2 low-density ✓
- [ ] **20-case synthesis eval committed** (fixtures/) — Variant C structural conformance + voice-lint ✓
- [ ] **Skip-conditions asymmetric gate**: precision ≥ 95% / recall ≥ 70% OR Rodc sign-off ✓
- [ ] **Synthesis asymmetric gate**: voice-violation rate ≤ 5% / structural conformance ≥ 90% OR Rodc sign-off ✓
- [ ] Tests green: full app suite + new unit + eval harness ✓
- [ ] **Tier 1.5 dogfood gate** (Task 16) — 4 personas reach first-insight by Day 7-10 + Sarah Day-15 silent-skip + Rodc 4 PASS / 0-1 WEAK / 0 FAIL ✓
- [ ] **Scenario verification**: S-INSIGHT-1 (5th card crosses threshold → ⌘ card surfaces in chat with Variant C body + 4 buttons), S-INSIGHT-2 (single-conversation cluster → no surface), S-INSIGHT-3 (same-topic cluster → no surface), S-INSIGHT-4 (sensitive concern in window → no surface, Sarah Day-15), S-INSIGHT-5 (frequency cap — second threshold within 7 days → no second surface), S-INSIGHT-6 (action button click registers + button-disable + chat continues), S-INSIGHT-7 (vault delete-then-readd same-fingerprint → no resurface), S-INSIGHT-8 (synthesizer LLM timeout → silent skip, chat unaffected) PASS ✓

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位:N/A (insight surface uses Rodix's chat character voice; per brand-book §4 two-layer model, this is the AI-as-Sage-flavor speaking inside chat)
2. ✓ Desktop-first:phase 1 desktop-primary (per memory note `project_device_priority`); ⌘ card responsive at mobile baseline ("doesn't visibly break")
3. ✓ §7.4 5 项 articulated
4. ✓ Pre-mortem 4 modes:
   - **like-me**: Rodc would feel insight at Day 7-10 with 5 distinct-topic distinct-conversation cards. Personas calibrated to match.
   - **metric vs goal**: NOT optimizing for insight-surface-count. Optimizing for "useful rate ≥ 70%" (precision) + Tier 1.5 4-persona pass.
   - **reactive vs strategic**: insight is brand's load-bearing aha moment; Wave 2 ship is strategic.
   - **edge case vs main path**: precision >> recall; skip-conditions are first-class, NOT post-hoc patches.
5. ✓ 桌面横向利用率:⌘ card lives in chat stream column, no special wide-screen requirement
6. ✓ Mobile responsive:single-column ⌘ card collapses 4 buttons to vertical stack at 375px
7. ✓ Empty state:N/A (insight only fires post-threshold; no "no insights yet" surface — silence is the empty state, per Decision 7 anti-engagement posture)

## Post-launch follow-ups (P2)

- **Wave 3 telemetry-driven threshold calibration** — if <40% weekly-active hit threshold by Day 14, lower to 3; if >30% trigger "not now"/dismiss, raise to 7. Cron-like batch job over `insight_events` × user-active-days table.
- **Wave 3 SSE/WebSocket upgrade** — same architectural debt as `#claim-extraction` Task 8; insight polling becomes real-time push.
- **Wave 3 LLM-judged-equivalence for same-topic cluster** — substring/bigram heuristic v1 will misfire on synonyms ("换工作" / "辞职" / "换跑道"); LLM-judge upgrade flagged.
- **Wave 3 multi-pattern surface** — current Wave 2 surfaces ONE pattern across last 5 cards; Wave 3 may surface "this week's top 3 themes" if telemetry signals demand it. Currently rejected per Decision 7 (anti-engagement / anti-summary-as-product) but data may invalidate.
- **Wave 3 source-card jump-to** — clicking a topic in the ⌘ card body takes user to that card in Vault tab. Currently text-only (Wave 2 simplicity); flagged.

## References

- Scenarios: S-INSIGHT-1 through S-INSIGHT-8 (NEW for Wave 2 — to be added to `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` v1.4 by implementer at Task 12)
- Hard dependencies:
  - `#claim-extraction` v1.8 — first-insight reads chat_claims; extraction must be GREEN (already met)
  - Wave 1c crisis-protocol *detection trigger* defined (full implementation can be post-launch; trigger keyword list MUST exist for skip-conditions §5.3)
- Brand sources:
  - `docs/superpowers/brand/founder-narrative-arc.md` Part 3 P1 — canonical user-experience demonstration (Sept 3 / Sept 19 / Oct 4 cards). The spec aligns to this verbatim.
  - `docs/superpowers/brand/brand-book-v1.md` §1 (canonical pitch unpacks here) + §7 Decision 7 (Rodix is for thinking not engagement) + §7b (crisis-content handoff dependency) + §6 visual identity (amber border lock)
  - `docs/superpowers/brand/voice-guide.md` §1 + §6 (consistency checklist applied to Variant C output) + §B (word-count ceiling for body)
- Assumption sources:
  - `docs/superpowers/research/assumption-list.md` S15 (continuity-of-thought distinction — the load-bearing distinction this feature delivers) + S17 (users will distinguish continuity-of-thought from personalization) + D1 (Sarah Day-15 sensitive-content failure mode)
- Code sources:
  - `app/shared/storage_py/chat_claim_adapter.py` — `count_chat_claims`, `get_recent_chat_claims_in_conversation`, will be extended with `get_recent_chat_claims_across_conversations`
  - `app/shared/extraction/extractor.py` + `extraction_queue.py` — pattern to clone for Synthesizer + post-persist hook
  - `app/shared/intent/classifier.py` — `_resolve_llm_config` + defensive JSON parsing pattern
- Roadmap: Wave 2, depends on `#claim-extraction` (GREEN) + Wave 1c crisis-protocol detection trigger (DEFINED)
- 协议 §5.1: `#2b` is P2 in roadmap, but **Phase 1 brand-defining** per founder-narrative-arc canonical example — first-insight is the unique brand-promise delivery surface. Recommended re-classification to P1 for Wave 2 dispatch (Rodc decision).

---

## Type-A escalation addendum (for `escalations.md`)

═══════════════════════════════════════════════════════════
ESCALATION #N — task-tier1-spec-first-insight — high
═══════════════════════════════════════════════════════════

When: 2026-05-03 (Tier 1 Wave 2 spec drafting)
Task: spec-first-insight (#2b)
Type: A (product strategy threshold lock — Rodc-only)
Self-resolved: yes (default chosen, escalated for confirmation before Task 1 dispatches)

What I hit:
The first-insight feature triggers when user accumulates N chat_claims (vault threshold). N drives the entire user-experience curve: too low (3) and the first-insight feels premature/empty/tone-deaf; too high (10) and most alpha users never see the brand's load-bearing aha moment before they fade. The threshold is product-strategy, not engineering — calibrating it after launch costs trust because users who hit it early form the cohort whose first impression of the brand magic is set.

What I needed but didn't have:
Rodc decision on N ∈ {3, 5, 7, 10}. Defaulted 5 with reasoning documented in spec ("≈ 1 week of moderate use" + precision-asymmetric posture).

What I did anyway:
- Default 5 locked in spec
- Alternatives 3 / 7 / 10 documented with pros/cons
- Calibration trigger flagged for Wave 3 (telemetry-driven adjustment if Phase 1 alpha shows <40% hit-rate by Day 14 or >30% dismiss-rate)
- Env-var seam `THROUGHLINE_INSIGHT_THRESHOLD` (clamp [3, 10]) so Rodc can override without code change

Default's downside if wrong:
**Medium-high.** Wrong threshold + Phase 1 launch:
- Too low (3): users see insight before vault has real material → first impression = "Rodix is just like ChatGPT memory making things up about me" → brand collapse
- Too high (10): alpha cohort fades before insight fires → brand magic moment never delivers → "Rodix is just ChatGPT but the cards table" → wedge fails per assumption-list D5

What I recommend Rodc + Opus do:
- Read spec "TYPE-A escalation: threshold value" section (4-row comparison table)
- Pick: 3 / 5 / 7 / 10
- If 5 (default): no further action; spec dispatches as-is
- If other: edit spec line ("default 5") + note in `decisions.md`

Severity reasoning:
**High.** Phase 1 launch-blocking strategic decision. Reversible post-launch via env-var OR data migration, but the *first cohort's first impression* is set by this number and can't be redone. Better to lock with Rodc judgment than ship default.

═══════════════════════════════════════════════════════════
