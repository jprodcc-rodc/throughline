# `#card-dedup` — Implementation Plan

> **Status (2026-05-03 morning, Wave 2 Tier 1 spec dispatch):** v1.0 — first dispatch, awaiting Rodc + external Opus review per per-feature plan-review protocol. **TYPE-A ESCALATION OPEN on threshold (default 3 / alts 2 / 4 / 5)** — Rodc must lock before dispatch.
>
> **Hard dependency:** `#card-real` (Wave 2 spec 1) — Card UI patterns this spec extends. The simplified card is a *new render path* of the same card primitive `#card-real` ships. `#card-real` lock-in for the 4-field card shape, the inline-expand affordance, and the click-through-to-vault contract must precede this spec's frontend tasks.
>
> **For agentic workers:** Use `superpowers:test-driven-development` per task. Then `superpowers:subagent-driven-development` extended with `docs/superpowers/skills/scenario-verification.md`.
> **App/ gitignored** — `app/shared/dedup/` + `app/web/server.py` + `app/web/static/app.js` + `app/web/static/vault.js` modifications do NOT go to git. Skip the per-task `Commit ...` lines for those files. `fixtures/` artifacts (eval set + runner) DO commit. Schema migration `chat_claims_v5.sql` DOES commit.

**Goal:** Reduce Card noise on revisited topics. When a user has already accumulated **N=3** Cards on the same topic within a **14-day rolling window**, the 4th and subsequent same-topic Cards render in a *simplified* form ("Recorded · #4 — related to earlier ↗") with a counter and a click-through to a topic-filtered Vault view. Backend still extracts and persists all 4 fields — only the *render* simplifies. **Done 标准:Recorded the user's thinking compounding (per brand-book §7 Decision 7), didn't dramatize each turn.**

**Architecture:**

1. **Topic-similarity computation** — for each new persisted chat_claim, compute a `topic_normalized` string (lowercased + whitespace-collapsed) at insert time. Reuse the bigram + substring similarity primitives from `app/shared/recall/` if compatible (the topic FTS evaluator's tokenization patterns are the closest existing kin).
2. **Dedup decision** — at the moment of `insert_chat_claim`, query the count of prior chat_claims within the conversation's user vault that match the new topic via the similarity rule **AND** were created in the last 14 days **AND** have `source = 'live'`. If count ≥ 3 → set `simplified_reference = 1` and store `simplified_count = count + 1` (the user-facing #N).
3. **Frontend render** — `app.js` and `vault.js` (per `#card-real`) check `claim.simplified_reference`. When true, render the simplified card "Recorded #N · related to earlier ↗" with an *inline expand* affordance (one-click; default collapsed). Click on the simplified card body → navigate to `Vault?topic={topic_canonical}`.
4. **Vault topic-filter view** — new `?topic=X` query param on the vault URL. List filters to all cards whose `topic_normalized` matches the filter via the same similarity rule. URL-bar deep-linking + back-button-restorable.
5. **Asymmetric gate** — recall-leaning. Better to NOT dedup (user sees full Card again) than incorrectly dedup (user feels their thinking was summarized away). Production target: **false-dedup rate ≤ 5%** measured by user-explicit "expand" clicks + dedup-marked-wrong feedback.

**Tech Stack:** Python · `app/shared/dedup/` (NEW module) · existing `chat_claim_adapter.py` (EXTEND with `source` + `topic_normalized` + `simplified_count` columns via additive migration `v4 → v5`) · existing `app/web/server.py` polling + new `/api/vault/by_topic` endpoint · `app.js` / `vault.js` frontend simplified-render + expand affordance + topic-filter view

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | Visible feature — simplified Card replaces the full 4-field expansion on the 4th+ same-topic turn. Counter "#N" is visible. Inline-expand chevron is visible. Click-through arrow `↗` is visible. |
| 产品策略假设 | Per brand-book §7 Decision 7: Rodix optimizes for thinking compounding, NOT message volume. A user revisiting the same topic for the 4th time means *"this is what I'm working on"* — the product's response should *count and link*, not *re-summarize*. Repeating the full 4-field expansion every turn is engagement-coded behavior; counting the revisit is thinking-compounding-coded behavior. The dedup IS the brand stance operationalized. |
| 适合 / 不适合 | **适合**: thoughtful users who revisit hard topics over weeks (per friends-intro side-project example: 6 weeks on the same fence, 3 cards). **不适合**: never-revisit users (their cards never trigger dedup → no behavior change for them). The "summarized away" failure mode (D5 contradiction) hits users whose framing genuinely shifts mid-cluster — the asymmetric gate covers that. |
| Trade-off | + reduces card-noise on revisited topics + visible counter rewards thinking-compounding (per brand voice §B "the example carries the argument — name a count") + click-through-to-cluster gives the user a continuity surface they didn't have / − asymmetric false-dedup risk: user feels their thinking was summarized away when topic actually evolved (per D5 mitigation 2) − threshold tuning is permanent debate territory − adds a code path that must stay in sync with `#card-real`'s 4-field expansion |
| 最大风险 | **False-dedup feels like surveillance / summarization-away** (per assumption D5 + brand-book §appendix item 4 surveillance-fail-mode polarity flip).**缓解**: (a) recall-leaning threshold (3 not 2; 14-day window not 30-day); (b) inline-expand always available (no information actually hidden, just collapsed); (c) `false_dedup_rate` telemetry surfaced via `/api/dedup/feedback` for post-launch tuning; (d) D5 calibration trigger: if alpha users mark > 5% of dedups as wrong → emergency raise threshold to 4 + post-mortem before continuing. |

## Ambiguity flag

⚠ **TYPE-A ESCALATION OPEN — threshold lock pending Rodc decision.**

Default = **3** (this spec's recommendation). Alternatives:
- **N=2** — more aggressive dedup; risks D5 false-positive on users whose 2nd card legitimately shifted framing.
- **N=4** — more conservative; keeps user seeing full Card 3 times before simplification. Costs: more visible noise on heavy revisitors.
- **N=5** — very conservative; effectively only fires for genuine compulsive revisitors. Risks: feature too rare to be observable / valuable in alpha.

Reasoning for default **N=3**:

1. The friends-intro side-project example used 3 cards (Sept 3 / Sept 19 / Oct 4) before the user noticed *"the bar kept moving"* — Rodc's own n=1 mental model is 3-cards-is-when-the-pattern-becomes-visible. Aligning the simplified card with the 3rd-revisit threshold makes the simplified-card timing *match* when the user themselves notices the pattern.
2. Wave 1b `#claim-extraction` Task 10 used a within-conversation 5-message window with the same N=3. Reusing 3 across the cross-conversation 14-day variant preserves user mental-model consistency.
3. N=2 fails D5 too often — a user saying "换工作" then "换工作但要考虑娃上学" should see two full cards, not see the 2nd dedupped.
4. N=4/5 leaves too many visible-but-redundant cards in the alpha cohort's small surface.

**Other locked decisions** (no escalation):
- **Window: 14 days rolling.** Reuses the friends-intro "weeks not months" cadence. Matches alpha cohort's expected revisit horizon.
- **Scope: across vault, not within conversation.** More useful for "you've been thinking about X for a week" pattern; within-conversation is a degenerate case (already covered by Wave 1b's 5-message window which stays for backward compat).
- **Imported cards excluded.** `chat_claims.source = 'imported'` (from Wave 1b `#9a` history-import) cards do NOT count toward the threshold AND are NOT eligible for dedup themselves. Reason: a user importing 200 ChatGPT exports should not see Day 1 simplified cards — that's a cold-start anti-pattern.
- **Null topic excluded.** chitchat-adjacent extractions where `topic IS NULL` are never dedup-eligible.
- **Counter logic: "currently in vault" not "ever generated".** If user deletes a same-topic card before threshold hits, the count drops. Threshold is "3 currently in vault matching topic, in last 14 days". Avoids the user-confusion mode where deleted cards still count.
- **Single global threshold v0.** Per-persona thresholds deferred to Wave 3+.
- **Topic-similarity algorithm: same as active-recall.** Substring case-insensitive **OR** bigram > 0.5 over `topic_normalized`. Reuses `app/shared/recall/` infrastructure; if the existing tokenizers don't expose a clean public API, expose them at task implementation time (do NOT silently re-implement).

## Asymmetric gate (production target)

| Signal | Target | Direction | Reason |
|---|---|---|---|
| `false_dedup_rate` | **≤ 5%** | HARD ship blocker | False dedup = user feels summarized away → trust collapse on a thinking-compounding product (D5 contradiction). The trust-killer signal here is "Rodix decided I was repeating myself when I wasn't" — symmetric in failure mode to the Gemini "corporate secretary" pattern from friends-intro. |
| `correctly_dedupped_rate` | **monitor only** | NOT blocking | Recall (catching every legitimate revisit) is fine to under-deliver in v0; user just sees a few extra full cards. Cost is recoverable. |
| `inline_expand_click_rate` | **monitor only** | NOT blocking | High expand rate would suggest dedup is being *triggered correctly* but *user-unwanted* — a softer signal than `false_dedup_rate`. Wave 3 calibration input. |
| `topic_filter_view_engagement` | **monitor only** | NOT blocking | Click-through to `Vault?topic=X` is a positive signal for the cluster pattern; absence is not failure (user may simplified-recognize the pattern without clicking). |

**Why precision-asymmetric (not recall-symmetric)**: Per brand-book §7 Decision 7 (thinking compounding metric, NOT engagement metric), the cost of false-dedup is *not recoverable* (user trust collapses on "summarized away"). The cost of false-non-dedup is *recoverable* (user sees one extra full card). Aligns with claim-extraction v1.8's trust-killer-vs-completeness gate split.

**False-dedup measurement** (concrete operationalization):

A dedup is "false" when within 24h of seeing the simplified card the user either:
1. Clicks the inline-expand chevron → expand event logged with `simplified_card_id`
2. Marks the dedup as wrong via a small "this isn't what I was thinking about earlier" feedback affordance (visible only on simplified cards; ghost-button style; per brand voice §B "ghost button" recovery affordance)

Both events feed `false_dedup_rate = (expand_clicks + wrong_marks) / total_simplified_cards_shown` over a 7-day rolling window. Monitor surfaced via `/api/dedup/feedback` (admin-only) at alpha.

## Files

**Modify** (gitignored — no commit):
- `app/web/server.py` — extend `insert_chat_claim` callsite to compute dedup decision before persistence; add `GET /api/vault/by_topic?topic=X` endpoint; add `POST /api/dedup/feedback` for false-dedup signals
- `app/shared/storage_py/chat_claim_adapter.py` — add `count_recent_same_topic_chat_claims(conn, vault_id, topic_normalized, *, since_days=14)` accessor; extend `ChatClaimRow` with `source: str`, `topic_normalized: Optional[str]`, `simplified_count: Optional[int]` fields; update insert/get to handle new columns
- `app/web/static/app.js` — when polling endpoint returns claim with `simplified_reference: true`, render the simplified card variant; wire inline-expand chevron + "this isn't related" feedback; wire click-through to `?topic=`
- `app/web/static/vault.js` — handle `?topic=X` query param on load → filter list view to topic cluster; show topic-cluster header with count; back-button-restorable
- `app/shared/storage_py/test_chat_claim_adapter.py` — extend with new column tests

**Create** (gitignored — no commit):
- `app/shared/dedup/__init__.py` — public exports
- `app/shared/dedup/topic_normalizer.py` — `normalize_topic(s: str) -> str` (lowercase + whitespace-collapse + light Unicode normalization). Pure function, no LLM.
- `app/shared/dedup/similarity.py` — `bigram_similarity(a: str, b: str) -> float` and `is_similar(a: str, b: str, *, bigram_threshold=0.5) -> bool` (substring OR bigram > 0.5). Reuses recall/ tokenizer if exposed; else inline a self-contained implementation that the recall/ module can later adopt.
- `app/shared/dedup/dedup_decision.py` — `should_dedup(conn, vault_id, new_topic, *, threshold=3, window_days=14) -> DedupDecision` (returns `{should_dedup: bool, count: int, matched_card_ids: list[str]}`). Pure function over the adapter's count call.
- `app/shared/dedup/test_topic_normalizer.py` — unit tests
- `app/shared/dedup/test_similarity.py` — unit tests covering CJK + EN + mixed
- `app/shared/dedup/test_dedup_decision.py` — unit tests covering threshold / window / source filter / null-topic / deletion-decrements-count

**Create** (tracked — commit normally):
- `app/shared/schema/chat_claims_v5.sql` — additive migration: add `source TEXT NOT NULL DEFAULT 'live' CHECK (source IN ('live', 'imported'))`, `topic_normalized TEXT`, `simplified_count INTEGER`. Backfill `topic_normalized` from existing `topic` rows. Add index `idx_chat_claims_topic_norm_recent ON chat_claims (topic_normalized, created_at DESC) WHERE topic_normalized IS NOT NULL`.
- `app/shared/storage_py/sqlite_adapter.py` — bump `SCHEMA_VERSION = 5`; add v4→v5 migration entry
- `fixtures/v0_2_0/eval/dedup_cases.json` — eval set for dedup correctness (see Task 10)
- `fixtures/v0_2_0/eval/run_dedup_eval.py` — runner (see Task 10)

## Prerequisite gates

1. **`#card-real` (Wave 2 spec 1) lock confirmed.** This spec's frontend tasks (8, 9) extend `#card-real`'s render contract. If `#card-real`'s 4-field render path is still in flux when this spec dispatches, frontend tasks will repeatedly merge-conflict.
2. **Threshold escalation resolved.** Per ambiguity flag above. Implementer must NOT begin Task 5 (dedup_decision module) without Rodc's signed-off N value.
3. **Wave 1b `#claim-extraction` shipped + 5-round dogfood PASS** (gate already met as of v1.8 status — confirms `chat_claims` table is production-realistic before this spec extends it).

## Bite-sized TDD tasks

- [ ] **Task 1: Topic normalizer**
  - Write failing test `test_topic_normalizer.py::test_normalize_lowercase_whitespace_unicode` — `normalize_topic("  Career Change  ") == "career change"`; `normalize_topic("换工作 ") == "换工作"`; mixed CJK+EN handled.
  - Implement `normalize_topic` in `app/shared/dedup/topic_normalizer.py`. Pure function. NFC Unicode normalize → lowercase → collapse whitespace (`re.sub(r"\s+", " ", s).strip()`).
  - Edge: `normalize_topic(None) → None` (passthrough so callers can compose without null-guarding).
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 2: Bigram similarity**
  - Write failing test `test_similarity.py::test_bigram_similarity_basic` covering: identical strings → 1.0; disjoint strings → 0.0; "换工作" vs "考虑换工作" → > 0.5; "career change" vs "thinking about career" → > 0.3 (won't pass dedup threshold); CJK 2-char + EN-3-char both handled.
  - Implement: bigram set Jaccard similarity. For CJK: bigrams of consecutive characters (no whitespace). For EN: lowercase + 3-char shingles preferred (matches FTS5 trigram tokenizer in `app/shared/recall/evaluators/topic.py`). Return Jaccard `|A∩B| / |A∪B|`.
  - **Reuse path**: inspect `app/shared/recall/evaluators/topic.py::_is_cjk_only` and `_EN_STOPWORDS`; if a tokenizer there is reusable, import it. Otherwise duplicate-with-comment "TODO: factor into shared/text_utils after Wave 2".
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 3: is_similar combinator**
  - Write failing test `test_similarity.py::test_is_similar_substring_or_bigram` — substring case-insensitive ("Career" in "career change") OR bigram > 0.5. Either path triggers True.
  - Implement: `def is_similar(a, b, *, bigram_threshold=0.5) -> bool: return _substring_check(a, b) or bigram_similarity(a, b) > bigram_threshold`.
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 4: Schema migration v4 → v5 (`source` + `topic_normalized` + `simplified_count`)**
  - Write failing test `test_chat_claim_adapter.py::test_v5_columns_exist` — `SELECT source, topic_normalized, simplified_count FROM chat_claims LIMIT 1` succeeds.
  - Create `app/shared/schema/chat_claims_v5.sql`:
    ```sql
    ALTER TABLE chat_claims ADD COLUMN source TEXT NOT NULL DEFAULT 'live'
      CHECK (source IN ('live', 'imported'));
    ALTER TABLE chat_claims ADD COLUMN topic_normalized TEXT;
    ALTER TABLE chat_claims ADD COLUMN simplified_count INTEGER;
    UPDATE chat_claims SET topic_normalized = LOWER(TRIM(topic))
      WHERE topic IS NOT NULL AND topic_normalized IS NULL;
    CREATE INDEX IF NOT EXISTS idx_chat_claims_topic_norm_recent
      ON chat_claims (topic_normalized, created_at DESC)
      WHERE topic_normalized IS NOT NULL;
    ```
  - Bump `SCHEMA_VERSION = 5` in `sqlite_adapter.py`. Add v4→v5 migration entry.
  - Update `chat_claim_adapter.py::ChatClaimRow` with new fields. Update `insert_chat_claim` / `get_*` helpers to pass through. Default `source='live'` and `topic_normalized=normalize_topic(claim.topic)` at insert time when caller hasn't set them.
  - **Backfill behavior**: existing rows pre-migration have `source='live'` (default), `topic_normalized` populated by SQL `LOWER(TRIM(topic))`, `simplified_count = NULL`. The Python normalizer is more sophisticated (NFC + collapse-whitespace) than `LOWER(TRIM)`; document the slight asymmetry in the migration comment. Acceptable because (a) backfilled rows are pre-Wave-2 and won't dedup against Wave 2 traffic; (b) any new same-topic card after migration computes `topic_normalized` via the Python normalizer.
  - Test schema migration test passes
  - PASS
  - (Commit `feat(schema): chat_claims v4→v5 — source / topic_normalized / simplified_count for dedup` for tracked SQL + adapter changes.)

- [ ] **Task 5: dedup_decision module — threshold + window + source filter**
  - Write failing test `test_dedup_decision.py::test_should_dedup_at_threshold` — given 3 prior chat_claims with similar topic in last 14 days, all `source='live'`, in same vault → `should_dedup() == True` and `count == 3`.
  - `test_should_dedup_below_threshold` — 2 prior → False.
  - `test_should_dedup_filters_imported` — 3 prior with `source='imported'` → False (imported never counts).
  - `test_should_dedup_window_excludes_old` — 3 prior but oldest > 14 days → False.
  - `test_should_dedup_null_topic_skipped` — new claim has `topic IS NULL` → False (returns early without DB query).
  - `test_should_dedup_uses_normalized_match` — prior topic "Career Change" + new topic "career change" → matches.
  - Implement `app/shared/dedup/dedup_decision.py`:
    - `def should_dedup(conn, vault_id_or_user_id, new_topic_normalized, *, threshold=3, window_days=14, similarity_check: Callable = is_similar) -> DedupDecision`
    - Strategy: (1) early-exit on null topic. (2) Query candidate rows from `chat_claims` filtered by `source='live'` AND `created_at >= now - 14 days` AND `topic_normalized IS NOT NULL`. (3) In Python, filter candidates with `is_similar(candidate.topic_normalized, new_topic_normalized)` — substring fast path + bigram fallback. (4) If matched count ≥ threshold → return DedupDecision(should_dedup=True, count=matched, matched_card_ids=...).
  - **Performance note**: in v0 the post-DB Python similarity filter is acceptable for alpha cohort (≤1000 users, ≤50 cards/user). Wave 3 may need an FTS-indexed candidate query if cards/user grows past ~500 per topic-cluster. Document as P2 follow-up.
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 6: chat_claim_adapter `count_recent_same_topic_chat_claims` accessor + `get_by_topic` accessor**
  - Write failing test `test_chat_claim_adapter.py::test_count_recent_same_topic` — given fixture rows, accessor returns correct count.
  - `test_get_by_topic_filters_correctly` — given fixture, returns all live chat_claims matching topic in vault, ordered by created_at DESC.
  - Implement (in `chat_claim_adapter.py`):
    - `count_recent_same_topic_chat_claims(conn, *, topic_normalized, since_iso, source='live') -> int` — direct SQL count using the `idx_chat_claims_topic_norm_recent` index.
    - `get_chat_claims_by_topic(conn, *, topic_normalized, since_iso=None, source='live', limit=50) -> list[ChatClaimRow]` — fuel for the topic-filter view.
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 7: Server integration — apply dedup at insert + extend polling response**
  - Write failing test `app/web/test_chat_dedup.py::test_4th_same_topic_persists_simplified` — POST 3 thoughtful messages with similar topic via TestClient; 4th message → polling returns `{ready: true, claim: {simplified_reference: true, simplified_count: 4, topic: "...", concern: null, hope: null, question: null}}`. (Note: simplified card hides 4 fields from render, but we still PERSIST them to chat_claims — this test asserts the polling response shape.)
  - **Decision: persist 4 fields OR persist nulls on simplified rows?** Persist 4 fields. Reason: per spec §C-4 (still extracts 4 fields, data preserved), navigating to the topic-filter view must show all 4 fields per card. The `simplified_reference=1` flag is *render-only*, not data-loss.
  - **Frontend response shape**: extend polling response to include `simplified_count` when `simplified_reference=true`. Clients use it to render "#N".
  - Implement: in the extraction queue's persist callback, before `insert_chat_claim`, run `should_dedup(...)`; if True → set `claim.simplified_reference = True` and `claim.simplified_count = decision.count + 1`. Else → defaults.
  - PASS
  - (No commit for `server.py` — gitignored.)

- [ ] **Task 8: Frontend — simplified card render + inline expand + click-through (extends `#card-real`)**
  - **Pre-condition**: `#card-real` shipped its full Card render path. This task adds a *branch* for `claim.simplified_reference === true`.
  - Modify `app/web/static/app.js::renderClaimCard`:
    - When `claim.simplified_reference === true`:
      - Render compact horizontal card: `[icon] Recorded #{simplified_count} · related to earlier ↗ [chevron-expand]`
      - Voice (per brand voice-guide §1 specific + anti-dramatize): English "Recorded #4 · related to earlier ↗", Chinese "已记下 #4 · 与之前相关 ↗" — locked phrasing per S-CARD-4 spec.
      - Click on body or `↗` arrow → `window.location.assign('/vault?topic=' + encodeURIComponent(claim.topic_normalized || claim.topic))`
      - Click on `[chevron-expand]` → toggle inline expansion. Expanded state shows full 4 fields below the simplified header (NOT a separate card, in-place expand). Logs `dedup_expand_click` telemetry event with `claim_id`.
    - When `claim.simplified_reference === false` → unchanged (full Card from `#card-real`).
  - Add a small "this isn't related to earlier" ghost button below expanded fields → POST to `/api/dedup/feedback` with `{claim_id, kind: 'wrong_dedup'}`. Ghost button per brand voice §B (3-tier button system; ghost = recovery).
  - **Voice review checklist** (per voice-guide §6):
    - ✓ specific: "#4" carries a count, not abstract
    - ✓ anti-spin: doesn't say "great, you're thinking about this!" — just records
    - ✓ refuses-to-dramatize: "Recorded" is a verb, not "Insightful repeat thinking captured!"
    - ✓ negation-as-positioning: "related to earlier" not "you're repeating yourself"
    - ✓ chevron is procedural, not celebratory (per brand-book §6 visual)
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 9: Frontend — Vault `?topic=X` filter view (extends `#card-real`'s Vault tab)**
  - Modify `app/web/static/vault.js`:
    - On URL load: parse `?topic=` query param. If present → fetch `GET /api/vault/by_topic?topic=X` → render filtered list with topic-cluster header `[← back] Topic: "{topic}" · {N} cards`.
    - Render full 4 fields per card (the topic-filter view is the "always-show-everything" surface; simplified rendering is chat-only).
    - Browser back button → restore unfiltered vault state. Use `history.pushState` so URL updates but the SPA tab transition is smooth.
    - Filtering reuses the same similarity algorithm (server-side `get_chat_claims_by_topic` with normalized topic).
  - Add `GET /api/vault/by_topic?topic=X` endpoint in `server.py`:
    - Validate query param (≤200 chars, not null).
    - Normalize topic via `normalize_topic`.
    - Return `{topic_filter: <normalized>, cards: [<full ChatClaimRow as JSON>...], count: N}`.
    - Filter to current user's vault (Wave 1b auth context — Wave 2 carries it through).
  - **Empty-state**: filter that returns 0 cards → show empty state per `#card-real`'s vault empty-state pattern + inline link "← back to all cards".
  - PASS
  - (No commit — app/ gitignored.)

- [ ] **Task 10: Eval — dedup correctness on synthetic + Rodc-curated cases**
  - Create `fixtures/v0_2_0/eval/dedup_cases.json`. Schema per case: `{id, category, prior_cards: [{topic, created_days_ago, source}], new_topic, expected: {should_dedup: bool, count: int, reason: str}}`.
  - Categories (n target):
    - **clear_dedup** (12) — same topic exact match, 3+ prior in window, all live → expect dedup.
    - **clear_no_dedup_below_threshold** (8) — 2 prior in window → expect no dedup.
    - **clear_no_dedup_outside_window** (6) — 3 prior but oldest >14 days → expect no dedup.
    - **clear_no_dedup_imported** (4) — 3 prior all `source='imported'` → expect no dedup.
    - **bigram_match** (10) — substring/bigram match cases ("换工作" vs "考虑换工作", "Career change" vs "career thinking") → expect dedup at threshold.
    - **D5 framing-shift** (12) — topic field changes mid-cluster (e.g., "换工作" → "换工作但要考虑娃上学" → "孩子教育") — the trickiest cases. Annotator marks per-case "should this dedup or not". Asymmetric: the annotator should prefer NOT to dedup on framing shifts (recall-leaning).
    - **EN_only** (6) — English-language cases, including 3-char shingles
    - **ZH_only** (6) — Chinese-language cases, including 2-char CJK bigrams
    - **mixed_lang** (4) — same topic expressed in EN and ZH within one user's vault
    - **null_topic** (4) — `topic IS NULL` rows mixed in (ensures null-skip works)
    - **deletion_decrements** (3) — 4 prior cards but 2 deleted → "currently in vault" count is 2 → no dedup
    - **boundary** (5) — exactly at threshold (count == 3) and exactly at window boundary (14 days 0 hours)
  - **Total: 80 cases.** Manual annotation: ~2 hours one-time (D5 framing-shift cases need careful judgment).
  - Create `fixtures/v0_2_0/eval/run_dedup_eval.py`:
    - For each case: build a tmp SQLite DB with prior cards, call `should_dedup(...)` on the new_topic, compare to expected.
    - Compute:
      - `correct_dedup_rate = TP / (TP + FN)` — caught real dedups
      - `false_dedup_rate = FP / (FP + TN)` — incorrectly dedupped (the trust-killer signal)
      - per-category accuracy (D5 framing-shift category should be tracked separately as it's the asymmetric-gate edge case)
    - **Asymmetric ship gate**:
      - `false_dedup_rate ≤ 5%` HARD ship blocker
      - `correct_dedup_rate ≥ 70%` monitor only (recall is recoverable in production)
      - D5 framing-shift category: `should_dedup` count ≤ 1 of 12 (i.e., extractor recognizes framing shifts as NOT dedup-eligible at least 11 of 12 times)
  - Commit `eval(card-dedup): 80-case eval set + asymmetric gate runner` (fixtures IS tracked).

- [ ] **Task 11: Asymmetric gate enforcement (integration test)**
  - Write failing test `app/shared/dedup/test_dedup_integration.py::test_eval_meets_asymmetric_gate` — `@pytest.mark.integration`, opt-in via `RUN_INTEGRATION=1`.
  - Loads 80 cases from `fixtures/v0_2_0/eval/dedup_cases.json`.
  - Asserts:
    - `false_dedup_rate <= 0.05`
    - D5 framing-shift category: `false_dedup_count_in_category <= 1` (out of 12)
    - `correct_dedup_rate >= 0.70` (monitor only — assert as warning not blocker)
  - On any FAIL: print full per-category confusion + the false-positive case IDs (so failure is debuggable per Rodc convention)
  - **Do not silently lower the gate** — on `false_dedup_rate > 5%`, raise to Rodc with options: (a) tighten similarity threshold (bigram > 0.6), (b) raise N to 4 globally, (c) add a per-category exclusion rule, (d) accept temporary + telemetry calibration.
  - PASS
  - (No commit — `test_dedup_integration.py` lives in app/, gitignored.)

- [ ] **Task 12: `/api/dedup/feedback` endpoint + telemetry**
  - Write failing test `app/web/test_dedup_feedback.py::test_feedback_records_wrong_dedup` — POST `{claim_id, kind: 'wrong_dedup'}` → returns 200; subsequent GET to admin metric endpoint shows count.
  - Implement endpoint in `server.py`. Persist to a small `dedup_feedback` table (or stderr log first; full table is Wave 3 work).
  - **For alpha**: log line `INFO dedup_feedback claim_id={x} kind={wrong_dedup|expand_click}` is sufficient; Rodc greps logs to compute `false_dedup_rate` manually during 5-round dogfood.
  - PASS
  - (No commit — app/ gitignored. The log-grep convention matches `#claim-extraction` Task 13's `claim_persisted` pattern.)

- [ ] **Task 13: End-to-end code-level verification**
  - Verify the full pipeline:
    - 3 prior same-topic live cards in vault → 4th thoughtful chat → polling returns simplified_reference=true with simplified_count=4
    - Frontend renders simplified card with #4 + chevron + click-through
    - Click `↗` → `Vault?topic=X` loads filtered list
    - Inline-expand chevron toggles 4-field display
    - "this isn't related" feedback POSTs to `/api/dedup/feedback`
    - Imported card path: 3 prior `source='imported'` + 4th live thoughtful → simplified_reference=false (imported didn't count)
    - Null-topic path: thoughtful with topic IS NULL → no dedup attempt
  - Run full app test suite — all green
  - Run integration eval (Task 11) — gate assertions hold OR Rodc sign-off
  - **Flag for Rodc subjective dogfood gate** (Task 14) — implementer flags Wave 2 release as "code-complete + eval gate met, awaiting 5-round dogfood"
  - (No commit — app/ gitignored.)

- [ ] **Task 14: Rodc 5-round subjective dogfood gate** (mirror of `#claim-extraction` Task 15)
  - **Why this is a separate gate**: Statistical pass on synthetic eval cases can hide a product-feel failure where users feel "summarized away" even when the eval marks the dedup correct. This gate catches it before alpha.
  - **Process**:
    1. Implementer signals Wave 2 release ready (Tasks 1-13 done, eval gate GREEN)
    2. Rodc runs 5 real revisit-pattern conversations (e.g., 4 turns over 7 days on the same topic)
    3. After the 4th turn each, Rodc asks: "did the simplified card feel right? would I want the full card here, or does this show the pattern better?"
    4. Rodc records subjective verdict per round: PASS / WEAK / FAIL with one-line note
  - **Outcome resolution**:
    - 4-5 PASS / 0-1 WEAK / 0 FAIL → ship
    - ≥ 2 WEAK or ≥ 1 FAIL → 4 options (raise threshold to 4 / refine similarity / add per-card "dedup off" toggle / pivot to manual-only dedup with user-trigger)
  - This gate is human-judgment, NOT automatable. Implementer marks Task 13 done with `awaiting_subjective_dogfood`; Rodc closes Task 14 manually after dogfood completes.
  - (No code change.)

## Done criteria

- [ ] `#card-real` (Wave 2 spec 1) shipped + Card UI patterns locked ✓
- [ ] Threshold escalation resolved by Rodc (default 3 unless Rodc lock differs) ✓
- [ ] `topic_normalizer.normalize_topic` (NFC + lowercase + collapse) ✓
- [ ] `similarity.is_similar` (substring OR bigram > 0.5) reuses recall/ infrastructure where compatible ✓
- [ ] Schema v4 → v5 migration committed (additive: source / topic_normalized / simplified_count + index) ✓
- [ ] `dedup_decision.should_dedup` (threshold + 14-day window + source='live' filter + null-topic skip) ✓
- [ ] `chat_claim_adapter` extended with `count_recent_same_topic_chat_claims` + `get_chat_claims_by_topic` accessors ✓
- [ ] Server insert hook applies dedup decision before persist; polling response carries `simplified_reference + simplified_count` ✓
- [ ] `GET /api/vault/by_topic` endpoint live ✓
- [ ] `POST /api/dedup/feedback` endpoint live (alpha-grade log line is sufficient) ✓
- [ ] Frontend simplified-card render + inline-expand + click-through (extends `#card-real`) ✓
- [ ] Frontend `?topic=X` Vault filter view (back-button-restorable) ✓
- [ ] **80-case eval set committed** (fixtures/), incl. 12 D5 framing-shift cases ✓
- [ ] **Asymmetric gate**: `false_dedup_rate ≤ 5%` HARD; D5 framing-shift category ≤ 1 false-positive of 12 HARD; `correct_dedup_rate ≥ 70%` monitor ✓
- [ ] Tests green: full app suite + new unit + integration eval ✓
- [ ] **Rodc 5-round subjective dogfood gate** — 4-5 PASS / 0-1 WEAK / 0 FAIL on real revisit-pattern conversations ✓
- [ ] **Scenario verification**: S-CARD-4 (same-topic 4th simplified) PASS as the core scenario; S-CARD-1 (Vault badge animation — verify badge does NOT increment on simplified cards if `#card-real` decided not-counted; OR DOES if it counts the underlying chat_claim — defer to `#card-real` decision); S-VAULT-3 (vault list with topic-cluster filter view); S-CHAT-5 (multi-turn → 4th turn dedup); S-CARD-3 (Active Recall — confirm dedup doesn't break recall trigger; recall fires on the *original* full cards in the cluster, simplified card itself is not recall-source-eligible) PASS ✓

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位:N/A — feature affects card render, not naming
2. ✓ Desktop-first: yes — simplified card is a horizontal compact pattern that benefits from desktop horizontal real estate; mobile responsive degrades to stacked
3. ✓ §7.4 5 项 articulated above
4. ✓ Pre-mortem 4 modes:
   - **like-me user**: D5 framing-shift handled — Rodc himself shifts framing across revisits, this gate explicitly tests against false-dedup on his pattern
   - **metric vs goal**: explicit — `false_dedup_rate` is the goal (trust); `correct_dedup_rate` is the proxy metric (monitor only). Gate split prevents optimizing against the wrong signal.
   - **reactive vs strategic**: spec is strategic (operationalizes brand-book §7 Decision 7); the asymmetric gate is the strategic anti-reactive choice (we don't optimize for "user always sees latest card" engagement)
   - **edge case vs main path**: D5 framing-shift is the main risk path (12 of 80 eval cases reflect this proportion); imported / null-topic / window-boundary are edges (smaller eval allocation)
5. ✓ 桌面横向利用率: simplified card uses horizontal compact layout (icon + text + chevron + arrow on one line), desktop horizontal real estate utilized
6. ✓ Mobile responsive: simplified card stacks to single column on < 768px; chevron-expand affordance still works (full-width touch target, ≥ 44x44px)
7. ✓ Empty state: `Vault?topic=X` returning 0 cards is handled per `#card-real`'s vault empty-state pattern + back-link

## Risk register

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | False-dedup feels like surveillance / "summarized away" → trust collapse | Medium | High (trust killer) | Asymmetric gate ≤5%; D5 framing-shift category in eval; recall-leaning threshold; inline-expand always available; `wrong_dedup` feedback affordance; calibration trigger if alpha >5% |
| R2 | Topic-similarity algorithm misfires on language boundaries (mixed CJK+EN, transliteration) | Medium | Medium | 4 mixed-lang cases in eval; reuse recall/ tokenizers; tune bigram threshold from 0.5 → higher if mixed-lang false-positive observed |
| R3 | Wave 1b cards persisted before v5 migration have `topic_normalized` populated by SQL `LOWER(TRIM)` not Python normalizer → minor algorithmic mismatch | Low | Low | Documented; backfilled rows are pre-Wave-2 traffic, won't dedup against new traffic; Wave 3 can re-run Python normalizer in a backfill job if needed |
| R4 | Performance on cards/user > 500 — post-DB Python similarity filter becomes O(n) per insert | Low (alpha cohort) | Medium (Wave 3) | P2 follow-up: FTS-indexed candidate query; not a Wave 2 blocker |
| R5 | `#card-real` doesn't actually ship the inline-expand affordance and this spec assumed it | Medium | High (frontend rework) | Hard prereq gate (this spec doesn't dispatch until `#card-real` lock confirmed); Task 8 verifies the contract before render-extend |
| R6 | User deletes prior card mid-cluster → count drops below threshold → next card renders full → confusing inconsistency ("why didn't this dedup like last time?") | Medium | Low | "Currently in vault" semantics are actually user-intuitive (user knows they deleted); zero spec change required, but flag for documentation in user-facing help |
| R7 | Imported cards never count → user with 200 imported cards on "career change" sees Day 1 first live card render full, even though they "feel like" they've discussed it many times | Low | Low | Intended behavior. Per spec §C-4: imported = pre-product, dedup is a *live-product* feature. Counter-intuitive only on first read; aligns with brand-book §7 Decision 1 (white-box: only product-generated state shapes product-rendering). |

## Post-launch follow-ups (P2)

- **FTS-indexed candidate query** when cards/user exceeds 500 in any topic cluster (per R4). Wave 3.
- **Per-persona threshold tuning** — Wave 3 may want different N for different user types (e.g., "writer" persona uses N=2, "power-user" persona uses N=4). v0 = single global threshold.
- **Backfill `topic_normalized` with Python normalizer** — current SQL `LOWER(TRIM)` backfill is a near-equivalent; Python normalizer adds NFC + collapse-whitespace which the SQL version misses for legacy rows. Wave 3 backfill job, low priority.
- **`dedup_feedback` table proper** — current implementation uses log-line + admin-grep; promote to first-class table when `false_dedup_rate` calibration becomes data-driven (post-alpha).
- **Cross-conversation dedup applied within-conversation too?** — current spec applies cross-vault. Within-conversation 5-message dedup from Wave 1b stays for backward compat; should it be subsumed under this 14-day rule? Defer to dogfood signal.

## References

- Scenarios: S-CARD-4 (same-topic 4th simplified — primary), S-CARD-1 (Vault badge animation — confirm interaction), S-VAULT-3 (vault list with topic-cluster filter view), S-CHAT-5 (multi-turn 4th turn dedup), S-CARD-3 (Active Recall doesn't break) — `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`
- Hard dependency: `#card-real` (Wave 2 spec 1) — Card UI patterns this extends. Lock the 4-field render path + inline-expand pattern before this spec dispatches frontend tasks.
- Brand: `docs/superpowers/brand/brand-book-v1.md` §7 Decision 7 (thinking compounding metric, NOT engagement metric); §appendix item 4 (surveillance-fail-mode polarity flip risk); §7b commitment-vs-shipped honesty
- Voice: `docs/superpowers/brand/voice-guide.md` §1 specific + anti-spin + refuses-to-dramatize; §B word-count ceilings; §6 voice consistency checklist for simplified-card copy
- Assumptions: `docs/superpowers/brand/research/assumption-list.md` D5 (broadening-vs-narrowing fail mode 2 mitigation — false-dedup feels like Rodix is "summarizing them" rather than tracking thinking); S16 (recall callout polarity flip risk applies analogously here)
- Spec: `docs/superpowers/plans/2026-05-01-claim-extraction.md` v1.8 — TEMPLATE for spec depth; Task 10 (within-conversation dedup) is the Wave 1b precursor this spec generalizes
- Prior art:
  - `app/shared/storage_py/chat_claim_adapter.py` — table contract + `get_recent_chat_claims_in_conversation` accessor pattern
  - `app/shared/schema/chat_claims_v4.sql` — schema baseline; v5 migration is additive
  - `app/shared/recall/evaluators/topic.py` — tokenization patterns for substring + CJK + EN bigram (reuse where compatible)
  - `app/shared/recall/orchestrator.py::ThresholdConfig` — pattern for per-trigger-type threshold config; same shape may emerge in Wave 3 when per-persona thresholds land
  - `app/shared/embeddings/cache.py::EmbedQueue` — shape for any future async dedup-recompute (not needed in v0)
- Roadmap: Wave 2, depends on `#card-real`. Unblocks `#decision-journal-lite` (Wave 2 spec 3) cluster view; enables thinking-compounding telemetry.
- 协议 §5.1: `#card-dedup` is P1 in Wave 2 — primary signal that thinking-compounding metric is operational at the product surface.
