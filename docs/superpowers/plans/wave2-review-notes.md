# Wave 2 Plan v1 — Reviewer Notes (wave2-plan-reviewer)

**Author:** wave2-plan-reviewer subagent
**Date:** 2026-05-03
**Inputs:** `2026-05-03-wave2.md` (master, 290 lines) + 5 wave2/spec-*.md files (2,044 lines combined) + `brand-book-v1.md` v2 + `2026-05-01-claim-extraction.md` v1.8.
**Lens:** junior-engineer + growth-operator + brand-coherence + rollback-discipline + most-fragile-assumption.

---

## Q1 — Junior engineer test

**Verdicts per spec:**

- **`#card-real`** — **PARTIAL**. Mostly buildable, but Task 4 explicitly says "Pre-condition: `#3a` Cards mgmt UI's detail panel exists and supports an `openDetailById(claimId)` shape (verify by reading existing vault.js — if not present, implement the seek-and-open via existing list iteration)." That's an "or do something else" instruction that a junior will read four ways. The Ambiguity flag at line 401 also concedes this is unresolved: *"if not present, raise to Rodc as Plan v1.1 push back: either add the accessor (extends `#3a`) or accept degraded UX."* Junior will guess; spec ships ambiguous.
- **`#active-recall-base`** — **PARTIAL**. The injection-format Variant 2 is locked, threshold reuse is named, the 60-case eval has clear category breakdown. **However, Task 10 reply-references-card detection is hand-wavy**: substring on topic field only ("if card.topic appears as case-insensitive substring in reply"). For Chinese topics like "副业" (2 chars), almost any AI reply mentioning side-projects will substring-match. A junior will implement-as-spec'd and ship a callout that fires on coincidental substring overlap, then telemetry will show silent_injection rate near 0% (everything matches by accident). The spec acknowledges this in Wave 2.1 calibration but doesn't gate v0 against it. **Also**: Task 8 says "carry `injection_block_text` in chat response metadata" but the response shape is never specified — junior has to invent the field name. Same for `_recall_card_ids` carrier shape.
- **`#2b first-insight`** — **PASS**. Most concrete spec of the 5. Variant C locked verbatim with regex shape (`r"(\d+|Three|Four|Five) cards?.*: .*\. .*back-to-back.*"`); 5 skip-conditions each have failing tests; Type-A escalation explicit at top with 4 alternatives + reasoning; insight_events table SQL inline. A junior reads this and implements without asking. Only quibble: the LLM `confidence < 0.6` gate is asserted but the prompt doesn't explain what makes the LLM emit < 0.6 vs ≥ 0.6 — so the gate may end up bimodal (everything either 0.0 or 0.9).
- **`#card-dedup`** — **PARTIAL**. Schema migration has good SQL inline, similarity rule named (substring OR bigram > 0.5), 80-case eval distribution is detailed. **Weakest paragraph (most likely to generate clarifying questions):** Task 5, the `should_dedup` API surface. *"Strategy: (1) early-exit on null topic. (2) Query candidate rows from `chat_claims` filtered by `source='live'` AND `created_at >= now - 14 days` AND `topic_normalized IS NOT NULL`. (3) In Python, filter candidates with `is_similar(candidate.topic_normalized, new_topic_normalized)` — substring fast path + bigram fallback. (4) If matched count ≥ threshold → return DedupDecision(should_dedup=True, count=matched, matched_card_ids=...)."* Two ambiguities: (a) **what's the candidate set size cap?** The spec quietly imports a "limit 100" elsewhere but Task 5 has no LIMIT clause — a vault with 5,000 live cards in 14 days runs O(5000) Python similarity scans per insert; junior either adds LIMIT and breaks correctness or doesn't and creates a perf cliff Wave 3 has to fix. (b) **What's `vault_id_or_user_id`?** Phase 1 is single-user-per-server; the parameter name is genuinely confusing — there's no `vault_id` column today. Junior pulls the wrong identifier.
- **`#vault-recall-history`** — **PASS**. Tightest spec of the 5. Schema migration is two ALTER TABLE statements; increment API has full Python source inline; edge cases 1-7 each have explicit decision + rationale; copy is locked verbatim ("Recalled N times · last X ago"); env-var rollback path explicit (`THROUGHLINE_RECALL_COUNTER_ENABLED`). The S16-vs-W17 polarity tension is articulated as the asymmetric gate. Junior implements this in 2 days and ships.

**Weakest spec: `#active-recall-base`.** The reply-references-card detection (Task 10) is the spec's pivot point — it controls whether the ⚡ callout fires correctly — and it's specified as a one-line substring match without acknowledging that 2-character CJK topics will produce 80%+ false-positive substring matches against any related reply. A junior cannot implement this safely without significant clarifying conversation OR will ship a callout that lies about what just happened (the very failure mode the spec's OPEN-2 says it's avoiding).

---

## Q2 — Growth operator value test

**Question: Does Wave 2 produce value users will pay for, or just ship?**

The plan's master gate sentence (line 132): *"≥ 3 alpha users confirm 'Rodix feels like thinking partner' qualitatively."* Three alpha users. That's interview-level signal, not paying-cohort signal. The plan does not specify any conversion / retention / upgrade-intent metric anywhere across 290 lines. Wave 2 success criteria are:

1. precision ≥ 80% (engineering quality)
2. hallucination rate ≤ 5% (engineering quality)
3. false_dedup_rate ≤ 5% (engineering quality)
4. ≥ 70% useful-marked (product feel)
5. ≥ 4/5 dogfood PASS (founder feel)

**A Sequoia-level growth operator would say:** *"Where's the activation metric? Where's the willingness-to-pay signal? Where's the comparison against the WTP baseline of ChatGPT Plus ($20/mo) for someone who is currently paying for ChatGPT Plus? You shipped 5 specs and you can't tell me whether any one of them moves WTP. You're shipping engineering health, not product-market-fit signal."*

**Per-spec implementer-shaped vs user-value-shaped audit:**

- **`#card-real`** — **user-value shaped.** Click-through closes the see→trust→verify loop. The user does something they couldn't do before. Defensible.
- **`#active-recall-base`** — **user-value shaped (load-bearing).** This IS the brand promise operationalized. The spec is correct that without it the eight-word pitch is unbacked. PASS.
- **`#2b first-insight`** — **user-value shaped, but speculative.** Founder-narrative-arc Part 3 P1 says this is "the canonical aha." There is zero validated evidence that 5 cards × 1 retrospective insight produces a paying-customer feeling. The spec says (line 30): *"This is **the** brand-defining moment per founder-narrative-arc Part 3 P1."* That's a brand assertion, not a user-research finding. If the threshold is wrong (Type-A 1) AND the format is wrong (Variant C may feel curated despite voice-lint), this spec ships a gimmicky "we noticed a thread!" surface that retention-studies show users dismiss within 3 weeks (cf. LinkedIn's "Connections you may know" which had to be redesigned 4 times).
- **`#card-dedup`** — **implementer-shaped, dressed as user-value.** The spec rationalizes dedup as "respects user time when revisiting compounds" but the actual UX outcome is the user sees a smaller card with a counter. There's no user research cited that says alpha users want this. The brand-book §7 Decision 7 ("thinking compounding metric, NOT engagement metric") is invoked as moral cover but the linkage is weak: a counter on a simplified card is **a different kind of engagement metric**, not an absence of one. **A growth operator's gut: ship dedup post-Phase-1 once you've measured how often users actually revisit topics. Doing it before measurement is engineering taste imposed as product.**
- **`#vault-recall-history`** — **implementer-shaped.** The spec's own §7 explicitly says the hypothesis is unvalidated and that Tier 1.5 Round 11 + production telemetry will determine ship-or-rollback. **It's shipping a brand experiment with a feature flag.** The growth-operator read: this is a brand-experimentalist surface, not a paid-cohort feature. It's defensible to ship behind a flag (and the spec does this correctly), but the plan's master document does NOT acknowledge that this spec is essentially a paid A/B test rolled into Wave 2 ship.

**Unit economics implication:** Wave 2 adds 4 LLM-calling code paths (extraction → recall scoring → first-insight synthesis → recall callout reply detection). Currently chat = 1 LLM call. Post-Wave-2 a thoughtful turn fires up to 4 LLM calls (1 chat + extraction + recall scoring is local but recall callout LLM-judge fallback Wave 2.1 + insight synthesis on threshold cross). At Haiku 4.5 prices ($0.25/$1.25 per M tokens) on a heavy AI user (~50 thoughtful turns/day) that's roughly $0.30-0.80/day per active user just in extraction+insight+judge calls. Phase 1 alpha (≤1,000 users in 30 days) is fine; Wave 3 SaaS at scale needs careful unit-economics modeling that this plan does not surface. **The plan should call this out and Wave 3 should plan against it. Currently it doesn't.**

**Summary verdict:** Wave 2 ships engineering-quality and brand-promise instantiation. It does NOT ship validated value. Two of five specs (`#card-dedup`, `#vault-recall-history`) are implementer-shaped or experiment-shaped and would be deferable post-Phase-1. **The plan would be stronger if it explicitly framed Wave 2 as "ship 2 P0 + 1 brand-defining + 2 telemetry-informed-by-alpha" rather than "5 specs, all P0/P1 same priority."** First-insight, card-dedup, and vault-recall-history all have telemetry calibration triggers — they're shipping experiments dressed as features. Acknowledge it.

---

## Q3 — Brand consistency check (operational vs ceremonial)

**Per spec: is the brand-coherence section doing real work, or is it a checklist?**

- **`#card-real` §9 — REAL work.** Quote: *"Header label: `已记下` — UNCHANGED from Wave 1a. Anchor microcopy, Rodc-locked. Per brand-book §5: 'Negation is not snark — it is position.' `已记下` (already-saved, past tense) signals 'the receipt is done, not the relationship.' Resists 'Saved! ✓' sycophancy."* This constrains. The spec **rejects** the ⚡ recall-callout strings even though the user spec request had them — *"Per brand-book §7b first item, these strings belong to `#active-recall-base`"* (line 185). That's the brand check actively scoping the spec, not just listing decisions. Strong signal of operational use.

- **`#active-recall-base` §"Injection format" — REAL work.** Variant 1 and Variant 3 are explicitly rejected with brand-rooted reasoning: *"'Past thinking from this user's vault' is meta-commentary — the AI may echo similar phrasing back to the user (banned per voice-guide §4 don't #4 + §3 sample passage 2)."* Three formats explored; brand book killed two. Real constraint.

- **`#2b first-insight` §"Reflection format" — REAL work.** Same pattern: Variant A and B rejected on voice-guide §1 + §6 Q4 grounds; only Variant C survives because it matches founder-narrative-arc Part 3 P1 cadence verbatim. Quote (line 87): *"Q4 Rodc-recognizes-as-his-own ✓ — this is *literally* the friends-intro Part 3 P1 cadence ('Three cards came back, dated September 3, September 19, October 4. Reading them back-to-back, the pattern was suddenly obvious...')."* Real check.

- **`#card-dedup` §"Voice review checklist" — CEREMONIAL.** Quote: *"✓ specific: '#4' carries a count, not abstract / ✓ anti-spin: doesn't say 'great, you're thinking about this!' — just records / ✓ refuses-to-dramatize: 'Recorded' is a verb, not 'Insightful repeat thinking captured!' / ✓ negation-as-positioning: 'related to earlier' not 'you're repeating yourself' / ✓ chevron is procedural, not celebratory."* Five checkmarks against five voice principles. Each "anti-pattern" cited is a strawman the spec was never going to ship. The actual brand-coherence stress test for this spec — *does the existence of a counter on a simplified card violate Decision 7's "we never ship... a streak counter, or a project-tagging system"?* — is NOT addressed. The spec invokes Decision 7 as moral cover but doesn't ask the harder question: when does "Recorded #4" cross from anti-engagement counting into engagement-coded gamification? The brand book §7 Decision 7 line 225 explicitly bans streak counters; the spec should rebut that this is not a streak counter, not just assert it isn't.

- **`#vault-recall-history` §4 + §11 R6 — REAL work.** Quote: *"Counter becomes a vanity metric / gamification — §4 explicitly rejects celebratory framing; copy ceiling enforces flat statement; no streak / badge / emoji."* And §4 anti-pattern list cites specific strings to NOT ship (`🔁 Recalled 3 times`; `Rodix brought this back 3 times!`). Constrains the implementer. **And** the spec's W17 polarity-flip risk explicitly defends amber-reservation (the counter is `--text-secondary`, NOT amber, because amber is for active surfaces). That's the brand-book §6 visual identity cited as a constraint. Solid.

**Summary:** 4 of 5 specs are using the brand book operationally; `#card-dedup`'s brand check is the one ceremonial section, and it's specifically silent on the hardest brand question for that feature (whether a visible card counter is brand-incompatible engagement-coded UI by the standard of Decision 7 line 225). **Edit needed in §"Voice review checklist": add a paragraph rebutting the streak-counter analogy directly, not just listing 5 ✓.**

---

## Q4 — Most fragile assumption

**The most fragile assumption across all 5 specs: precision >> recall is the right asymmetric framing for active-recall.**

Both `#active-recall-base` (line 67-73) and `#vault-recall-history` (line 197-216) treat the recall-precision asymmetry as load-bearing. The reasoning is well-argued for the trust-killer scenario: wrong card injected → AI awkwardly references something user did not say → trust collapse. **But this framing has a blind spot: it does not consider scenarios where recall is load-bearing.**

**Concrete failure case the spec ignores:** A user opens a brand-new conversation 8 days after the friends-intro side-project conversation. They start with *"OK so I've been thinking about this side project thing again."* The user EXPECTS Rodix to bring back the prior card. With precision-asymmetric tuning at threshold 0.65, the topic-similarity score on "side project thing" against "副业" (assuming Chinese) or against "side project" (English) may NOT clear 0.65 because the user used "this side project thing" — pronominal, less topic-specific. Rodix returns 0 cards. AI replies as if it's a fresh topic. **This is the failure mode that destroys retention thesis W11/W13** — user thinks "Rodix doesn't actually remember." User churns with the conclusion "this is just ChatGPT but I have to type my own context."

The plan's risk register R11 names this risk (*"Empty-vault new user → no recall ever fires → no aha → 'Rodix is just ChatGPT' perception"*) but assigns it to *new users* with empty vaults. The same failure happens with **populated vaults under-recalling**, and the plan does not flag it. The 80% precision gate × 50% recall monitor floor means up to half of valid recall opportunities are silenced. For a memory product, "Rodix forgot what we discussed" is a more brand-existential failure than "Rodix mis-recalled" — at least mis-recall is interpretable as "the system is trying."

**Asymmetric-but-symmetric reframe:** Wave 2 should ship with precision ≥ 80% AND recall ≥ 60% (both as soft gates with telemetry calibration). The current spec defines recall as monitor-only at 50% — that's too lax. A user whose vault contains the "side project" card and who explicitly references it in conversation 9 is the canonical retention loop; if recall misses 50% of these, the product is permanently broken in ways no precision optimization fixes.

**Other fragile assumptions worth naming:**

- **Threshold = 5 for first-insight.** The Type-A escalation acknowledges this. But the spec assumes "5 cards = 1 week of moderate use" — for the alpha cohort (heavy AI users, 2-3hrs/day), 5 cards may land in 36 hours, well before vault density justifies a "thread observation." If insight fires at Day 2 with 5 cards from 3 different topics in 36 hours, it'll feel premature. Spec calibration trigger correctly catches this Wave 3, but Phase 1 first-cohort first-impression cannot be redone.

- **`recall_count` metadata is a trust signal.** Spec-vault-recall-history asserts this and gates ship behind Tier 1.5 Round 11 + 70% positive/neutral. But the spec's own §11 R1 names this as brand-existential P0 risk. The validation surface (Round 11 = 1 persona × 1 dogfood walk) is statistically thin. **A single persona's reaction is not ship-validation for a brand-existential signal.** The spec implicitly accepts this by gating with env-var rollback, but the decision to ship-with-flag-on vs ship-with-flag-off is not made — `THROUGHLINE_RECALL_COUNTER_ENABLED` defaults to OFF in Task 6 but the §13 references suggest "ship with row visible at Phase 1 alpha launch (env var default ON)." Inconsistency.

- **Wave 1b extraction quality holds at production scale.** Plan §"Wave 2 success criteria" line 127 sets this gate at ≤ 5% sustained hallucination. Current eval-set measurement is 2.3% on 256 EN field decisions. **Eval set is curated; production traffic distribution is not.** If users genuinely talk about "kill the project" / "I want to die at this work" (non-crisis colloquial usage) the chitchat false-positive rate may climb past 5% because the v3.1 prompt and the placeholder crisis-keyword list were not trained on traffic distributions yet. This is the most empirically uncertain gate of Wave 2.

**Highest-priority fragile assumption:** **Recall recall** (50% floor is too lax; the wedge fails if Rodix forgets). Quote ship-blocker edit recommendation in §2 below.

---

## Q5 — Rollback discipline

**Per spec rollback audit:**

- **`#card-real` §13 — DOCUMENTED, partially TESTED.** Feature flag `_CARD_REAL_ENABLED` named; rollback is a static-asset re-deploy. **However**: Task 1 (polling response exposes `claim_id`) and Task 2 (`GET /api/claim/{claim_id}`) are backend changes that don't have rollback paths. If Task 2's accessor route 5xx-throws en masse, the spec says (§13): *"frontend's click handler catches fetch failure → renders inline hint."* That's degradation, not rollback. The spec's own EC9 (deleted card 404) is the only actual tested failure path. **No rollback testing for the new accessor itself.**

- **`#active-recall-base` — UNDOCUMENTED.** Spec has no §"Rollback plan" section. The OPEN-3 frequency cap is deferred to Wave 2.1, which IS a calibration not a rollback. If recall starts misfiring at production scale (precision drops below 80%), there's no kill-switch path. The closest equivalent is the existing orchestrator's threshold knob; raising threshold is a code change requiring re-deploy, not a runtime flag. **High risk: this is the load-bearing brand spec and it has no rollback path. Add `THROUGHLINE_RECALL_INJECTION_ENABLED` env-var gate around Task 8's prompt suffix.**

- **`#2b first-insight` — DOCUMENTED but ENV-VAR ONLY.** `THROUGHLINE_INSIGHT_THRESHOLD` clamp [3, 10] (Task 1) gives Rodc a runtime knob to disable triggers at threshold=10 (effectively never fires). **However**: spec doesn't articulate "rollback path" explicitly. Setting threshold=10 doesn't delete the insight_events that already fired — historical insights stay visible to users. If Wave 2 ships and Mike's day 7 insight surfaced as tone-deaf, that insight stays in his Vault history forever (insight_events have no TTL or delete affordance for users). **Add task: user-facing dismiss + delete affordance OR explicit "insights surfaced before threshold was raised remain visible with admin-only soft-delete."**

- **`#card-dedup` §"Asymmetric gate" — DOCUMENTED with explicit calibration trigger.** Quote: *"`false_dedup_rate > 5%` → emergency raise threshold to 4 + post-mortem."* That's a calibration, not a rollback. The schema migration v4→v5 is additive; reverting requires column drops which SQLite handles awkwardly. **Schema rollback safety**: ALTER TABLE DROP COLUMN was added to SQLite in 3.35 (March 2021) — should be safe but spec doesn't verify. **Edit: add a sentence confirming SQLite version target ≥ 3.35 OR document that migration is one-way (forward-only).**

- **`#vault-recall-history` §6 + §"Rollback path" — DOCUMENTED, with env-var gate explicit.** `THROUGHLINE_RECALL_COUNTER_ENABLED=0` disables increment and render. Schema stays. Quote (§5 EC6): *"Failure mode that breaks rollback: if any code path was already writing to v5 columns when migration is rolled back, those writes silently fail."* Acknowledges the constraint and provides operator escape. **Strongest rollback discipline of the 5 specs.**

**Cross-spec schema-migration coordination — SAFE BUT FRAGILE.** Plan §"Schema migration coordination" line 109-112 correctly identifies that `#card-dedup` and `#vault-recall-history` both target v5 and must merge into a single `chat_claims_v5.sql`. **However**: if implementer ships dedup migration first and recall-history migration follows, there's a window where SCHEMA_VERSION=5 means different columns depending on which spec landed first. The plan acknowledges this needs implementer-side audit during Day 2 dispatch. **A cleaner solution:** explicit pre-flight check in plan — both migrations must land in a single PR with all 5 columns OR the plan should rename one to v6 to make order explicit. Current state allows non-deterministic schema state.

**Worst-case recovery scenario "alpha cohort week 2, signal is bad":**

- Active recall precision plummets to 40% in production traffic (not measured by eval set). Users report "creepy and wrong."
- Time to detect: 24-48hrs (depends on alpha telemetry pipeline; spec is vague)
- Time to disable: needs new env-var seam (`THROUGHLINE_RECALL_INJECTION_ENABLED`) which doesn't exist — requires code deploy
- Time to deploy: assume 30 min Phase 1 deploy cadence
- **Total recovery time: 24-50 hours, dependent on detection speed.** Acceptable for non-existential failure but uncomfortable for a brand-existential signal.

**Recommendation:** Wave 2 dispatch checklist must include adding env-var seams for ALL 4 surfaces that aren't currently flag-gated (active-recall injection, first-insight surface, card-dedup decision, vault-recall-counter render). Currently only vault-recall-counter has it.

---

## Edits needed (severity ranked)

### EDIT 1 (HIGH — ship-blocker for Wave 2 dispatch)
**Section affected:** `spec-active-recall-base.md` — add §"Rollback plan" section + env-var seam.
**What to change:** Add `THROUGHLINE_RECALL_INJECTION_ENABLED` env-var (default ON in production, OFF in tests). Gate the `recall_inject.run()` call site in `/api/chat` handler around `if not _enabled: return RecallInjection(cards=[], block_text="", scores=[])`. Document rollback path: setting flag to OFF reverts to pre-Wave-2 chat behavior (no system-prompt suffix); recall_events log table stays clean (no inserts).
**Why:** This is the load-bearing Wave 2 P0 spec. It currently has no kill-switch. If precision drops in production, time-to-recover is 24-50 hours including code deploy. With the env-var seam, time-to-recover drops to < 5 minutes (config flip).
**Severity:** HIGH. The plan's R1 names recall-precision-failure as CRITICAL impact; the rollback path must match the impact level.

### EDIT 2 (HIGH — ship-blocker for Wave 2 dispatch)
**Section affected:** `spec-active-recall-base.md` §"Asymmetric precision gate" + plan §"Risk register" R1.
**What to change:** Promote recall-recall (currently 50% monitor-only) to a soft floor of 60% with a **production calibration trigger if recall < 50% sustained for 3 days**. Add the trigger sentence to spec line 67-73 table and to plan R1 mitigation column.
**Why:** Q4 — the precision-asymmetric framing has a blind spot: under-recall is the wedge-failure mode for retention. The plan's W11/W13 retention thesis depends on Rodix actually bringing things back when relevant. 50% recall monitor-only means up to half of valid retention loops are silently broken. This is a precision-asymmetric blindness, not precision-asymmetric correctness.
**Severity:** HIGH. The plan's wedge claim ("brings it back when it matters") is a recall claim; under-recall directly contradicts the canonical pitch.

### EDIT 3 (HIGH — should fix before implementer-dispatch)
**Section affected:** `spec-active-recall-base.md` Task 10 — reply-references-card detection.
**What to change:** Replace one-line topic-substring match with: (a) substring match requiring topic length ≥ 4 chars (or ≥ 3 CJK chars), AND (b) reply length-normalized check (substring must be a non-trivial fraction of the reply, not 0.5% noise overlap), AND (c) Wave 2.1 LLM-judge fallback path must be explicitly scaffolded as a NotImplementedError so v0 ship is at least honest about the gap.
**Why:** Q1 weakest paragraph. As specified, 2-char CJK topics will produce 80%+ false-positive substring matches (any reply mentioning the topic generally will substring-match). Junior implements as-spec'd and ships a callout that fires on coincidental overlap — exactly the brand-existential trust-killer the spec elsewhere defends against.
**Severity:** HIGH. The recall callout is the primary user-visible signal of the wedge feature; if it lies about what just happened (fires on coincidental match, not actual reference), the brand-promise inversion is severe.

### EDIT 4 (MEDIUM — should fix before implementer-dispatch)
**Section affected:** `spec-card-dedup.md` Task 5 — `should_dedup` API surface.
**What to change:** (a) Resolve `vault_id_or_user_id` parameter — Phase 1 is single-user-per-server, parameter should be removed entirely OR explicitly wired to `_get_current_user_id()` accessor (which doesn't exist yet). (b) Add explicit LIMIT to candidate query (recommend LIMIT 100 with documented fallback if vault density grows past 100 same-topic cards in 14 days — Wave 3 FTS-indexed candidate query). (c) Document that Phase 1 single-user-per-server architecture means `vault_id` is implicit and the parameter exists for forward-compat with Wave 3 multi-user.
**Why:** Q1 ambiguity. Junior either invents a vault_id getter OR implements without limit and creates O(n) similarity-scan perf cliff that Wave 3 has to fix.
**Severity:** MEDIUM. Doesn't break correctness for alpha (≤1000 users, ≤50 cards/user), but a perf cliff at Day 31 is preventable now with 2 lines of edit.

### EDIT 5 (MEDIUM — should fix before implementer-dispatch)
**Section affected:** `spec-card-real.md` Task 4 + Ambiguity flag at line 401.
**What to change:** Resolve the `openDetailById` precondition before dispatch by either (a) verifying via grep on `vault.js` that the accessor exists (and updating spec verbatim), OR (b) adding Task 4a "implement openDetailById on `#3a` Cards mgmt detail panel" as an explicit cross-spec task. The current "verify-or-fall-back" instruction is a deferred decision the implementer will resolve under time pressure with worse outcome than Rodc resolving now.
**Why:** Q1 PARTIAL. Spec quality is otherwise good; this is the one open question that should not exist at v1 dispatch.
**Severity:** MEDIUM. 30-min upfront work prevents 2-hour implementer drift.

### EDIT 6 (MEDIUM — should fix before implementer-dispatch)
**Section affected:** `spec-card-dedup.md` §9 Brand check — Voice review checklist.
**What to change:** Replace the 5-checkmark ceremonial list with a paragraph that directly addresses: *"Why is 'Recorded #4' not engagement-coded gamification of the type brand-book §7 Decision 7 line 225 explicitly bans (`We never ship a today view, a weekly summary, a streak counter, or a project-tagging system`)?"* Required answer: counter rewards revisit (compounds), doesn't reward consecutive days (engagement). Distinction must be defended explicitly, not asserted.
**Why:** Q3 — only ceremonial brand check across 5 specs. The hardest brand question for this feature is sidestepped.
**Severity:** MEDIUM. Plan ships if Rodc agrees the rebuttal is sound, but currently the check is performative.

### EDIT 7 (LOW — polish)
**Section affected:** Plan `2026-05-03-wave2.md` §"Schema migration coordination" line 109-112.
**What to change:** Bump explicitly to "single combined PR for v5 migration containing all 5 columns from both specs" OR rename `#vault-recall-history` migration to v6. Currently v5 with non-deterministic column-set ordering is a footgun if specs land out-of-order.
**Why:** Q5 rollback discipline.
**Severity:** LOW. Plan acknowledges the issue; this is just hardening the language.

---

## Type-A escalations beyond existing #2-#6

**NEW Escalation #7 (proposed): Wave 2 telemetry-readiness + alpha-cohort signal targets.**

**Rationale:** Plan's Wave 2 success criteria are 100% engineering quality + brand-promise instantiation. Zero metrics tie to retention / WTP / activation. Three specs have calibration triggers that depend on production telemetry that the plan doesn't specify how to capture. `support_ticket_creep_language_rate` is named multiple times; there's no support-ticket pipeline architected. `false_dedup_rate` is a 7-day rolling window measurement; there's no rolling-window aggregation pipeline. **Rodc decision required:** is Wave 2 telemetry shipped with Wave 2, or do calibration triggers become Wave 2.1 work? If the latter, the calibration triggers are aspirational and shouldn't be cited as ship gates.

**NEW Escalation #8 (proposed): Phase-1 first-cohort-first-impression risk on first-insight + recall-callout copy lock.**

**Rationale:** Both `⚡ 我把这个带回来了` (active-recall-base) and Variant C reflection format (first-insight) are brand-defining strings the alpha cohort sees on first occurrence. Once seen, can't be re-seen for first time. Spec has no plan for what to do if Tier 1.5 Round 11 says "callout feels meta" or "Variant C feels curated" — both gates have outcome resolution paths but neither has "what if the alpha cohort feels this way" path. Should we have a rolling-week of pre-launch dogfood beyond Tier 1.5 with 2-3 friend testers (pre-alpha cohort) to validate copy lock before it becomes irreversible? Type-A: cost of pre-launch friend dogfood = 5-7 days delay. Cost of wrong copy lock at alpha = brand-promise miscalibration.

---

## What the plan got right (defenses)

1. **Reuse-not-clone discipline.** `spec-active-recall-base` line 39: *"NEW thin module `app/shared/recall_inject/` wraps `Orchestrator` + `TopicEvaluator` (NOT a parallel scoring system)."* Plan §"Dependencies" line 53 names it. This is hard-won discipline from Wave 1b — verified via my grep that `app/shared/recall/orchestrator.py` exists and the spec correctly cites `ThresholdConfig.topic = 0.65`. Real reuse, not lip-service.

2. **Asymmetric gate split (trust-killer vs completeness).** Plan §"Wave 2 success criteria" inherits the Wave 1b v1.8 split-route precedent. `spec-active-recall-base` precision ≥ 80% is HARD ship blocker; recall ≥ 50% is monitor-only. `spec-card-dedup` `false_dedup_rate ≤ 5%` is HARD; `correct_dedup_rate ≥ 70%` is monitor-only. **This is the strongest pattern in the plan.** It correctly translates the Wave 1b lesson (trust-killer is HARD, completeness is monitor) into Wave 2 ship gates.

3. **Schema-migration cross-spec integration audit.** Plan §"Schema migration coordination" line 109-112 catches that BOTH `card-dedup` and `vault-recall-history` target `chat_claims_v5`. This is a cross-spec risk invisible from either spec alone. The plan flags it explicitly with R8 and assigns implementer-side audit. **This is the kind of integration risk most plans miss.**

4. **Type-A escalation flagging at top of each spec.** `spec-first-insight` and `spec-card-dedup` both have explicit Type-A boxes at top with 4-row alternative-comparison tables. Default chosen with reasoning; alternatives documented. Rodc reads spec, picks number, dispatches. **This is the Wave 1b v1.8 pattern correctly carried forward.**

5. **Brand-check section is 4-of-5 operational.** `#card-real`, `#active-recall-base`, `#2b first-insight`, `#vault-recall-history` all have brand-coherence sections that DO real constraint work (rejecting variants on brand grounds). Not a checkbox exercise.

---

## Final verdict

**Plan-level disposition:** **PARTIAL — ship after EDIT 1, EDIT 2, EDIT 3 (the 3 HIGH-severity edits) addressed.** The remaining 4 edits (medium + low) can be addressed during implementer-dispatch checklist or in v1.1 push back, but they should be addressed.

**Strongest 3 specs:** `spec-vault-recall-history` (rollback discipline + brand-coherence-real-work), `spec-first-insight` (specificity + Type-A escalation), `spec-card-real` (brand check operational + concrete TDD tasks).

**Weakest spec:** `spec-active-recall-base` — the load-bearing P0 spec, has the most ambiguous critical task (Task 10 reply-detection) AND no rollback section. Edit 1 + Edit 3 must land before dispatch.

**Most fragile assumption:** Recall-recall floor at 50% monitor-only is too lax for a wedge product whose canonical pitch is "brings it back when it matters." Edit 2 must address this.

**Should the plan dispatch as-is?** **No.** The 3 HIGH edits each take 1-2 hours of spec re-work. After they land, dispatch.

---

*End wave2-review-notes.md (v1, 2026-05-03). Author: wave2-plan-reviewer subagent. Reviewer applied junior-engineer + growth-operator + brand-coherence + rollback-discipline + most-fragile-assumption lenses to 5 Wave 2 specs + master plan v1. Findings recommend 3 HIGH-severity edits + 4 MEDIUM/LOW edits + 2 new Type-A escalations beyond existing #2-#6.*
