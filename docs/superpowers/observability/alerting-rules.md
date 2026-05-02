# Rodix Wave 3 — Alerting Rules

> **Status:** Strategic-design depth. Wave 3 dossier. Author: observability-architect. 2026-05-03.
>
> **Anchors:** `observability-spec.md` §5 · `cost-cap-design.md` §3 (per-user cap) · `brand/brand-book-v1.md` §7b (crisis-content protocol Wave 1c).

## Rule R1 — Extraction failure spike (CRITICAL)

- **Trigger:** Extraction failure rate >10% over rolling 1-hour window. Failure = parse error OR Anthropic API error OR LLM-judge flagged hallucination on sampled batch.
- **Severity:** CRITICAL.
- **Recipient:** Rodc (PagerDuty / SMS via Sentry → Twilio webhook). Phase 1 alpha may simplify to email + push (PagerDuty $19/mo defers to ~$10k MRR).
- **Auto-action:** None at first occurrence. If sustained >2h, auto-flag `EXTRACTION_DEGRADED` flag in Redis (or SQLite `system_state` table) — chat continues, extraction quietly skipped until Rodc reviews.
- **Manual investigation path:** Sentry → recent errors filtered by `op:extraction` + `level:error`. Cross-reference with PostHog dashboard "extraction success rate" panel. Likely root causes: Anthropic API outage / model deprecation / prompt token-budget regression / OpenRouter rate-limit.
- **Escalation if Rodc unavailable >12h:** auto-flag holds; chat-only mode is acceptable degradation per brand-book §7 Decision 5 (null-default — empty card better than wrong card). User sees no UI change; vault stops growing for the duration.

## Rule R2 — Total daily cost ceiling (CRITICAL)

- **Trigger:** Aggregate `cost_usd_total` across all users for current UTC day exceeds **2× expected**. Expected = 1,000 users × $0.30 worst-case = $300/day. Trigger at $600/day.
- **Severity:** CRITICAL.
- **Recipient:** Rodc (SMS).
- **Auto-action:** Soft-throttle — system-wide flag `DAILY_COST_THROTTLE` enables aggressive intent-classifier gating (only `thoughtful` intent reaches Anthropic; `chitchat` returns canned response). Continues until midnight UTC reset.
- **Manual investigation path:** PostHog dashboard "cost per user (today)" — sort descending. Identify outlier users; cross-reference R3 alerts. Likely root causes: traffic spike (good — investigate growth) / abuse pattern (bad — investigate R5) / extraction loop bug (worst — fix immediately).
- **Escalation if Rodc unavailable >24h:** throttle holds; alpha cohort experiences degraded chat for the day. Acceptable failure mode at Phase 1 scale.

## Rule R3 — Per-user cost cap exceeded (WARNING)

- **Trigger:** Single user's `daily_user_cost` exceeds 50k input OR 25k output tokens (per `cost-cap-design.md` §2). Triggers at the moment cap-check middleware blocks the user.
- **Severity:** WARNING.
- **Recipient:** Rodc (email digest, hourly batch — not paged immediately to avoid noise).
- **Auto-action:** **Cap enforced — user receives soft block per `cost-cap-design.md` §3.** No account suspension; no payment language. User account flagged `cap_review_pending` for Rodc to investigate within 48h.
- **Manual investigation path:** PostHog → user_id_hash filter → 7-day session pattern. Distinguish: (a) genuine heavy user — flag for Power-tier outreach if Wave 3b paid launched; (b) accidental loop / front-end bug — apologize + comp via override env var; (c) abuse — manual ban via `RODIX_USER_BANNED_USERIDS` env var (Wave 3 schema).
- **Escalation if Rodc unavailable >48h:** Cap holds (user locked out for the day); auto-resets at midnight UTC. No escalation needed at Phase 1 — the cap *is* the safety mechanism.

## Rule R4 — Recall precision drop (HIGH)

- **Trigger:** Active recall precision (LLM-judge sampled 10%) <70% over rolling 24h window. Wave 2 ship gate is ≥80%; <70% = degraded.
- **Severity:** HIGH.
- **Recipient:** Rodc (email).
- **Auto-action:** None automatic. Wave 2 plan calibration trigger: if sustained 3 days, flag `recall_calibration_due` for Rodc to tune `ThresholdConfig` in `app/shared/recall/orchestrator.py`.
- **Manual investigation path:** PostHog → recall events filtered by `recall_judge_score < 0.7`. Cross-reference with recall trigger type breakdown — is one type (e.g. `stance_drift`) causing the drop? Likely root causes: vault-size growth changing recall-payload distribution / model behavior shift / threshold drift.
- **Escalation if Rodc unavailable >72h:** Recall continues at degraded precision. Per brand-book §7 Decision 3, "active recall" verb commitment holds even at degraded precision — but the 4-fold critique inverts (recall stops feeling "trusty / thoughtful" and starts feeling "creepy / intrusive"). Wave 2 plan flags this as P0 brand risk (Reconciliation log item 4 in brand-book) — if 72h sustained, manually disable recall via flag until Rodc returns.

## Rule R5 — Suspicious-pattern abuse (WARNING)

- **Trigger:** Single user posts >100 messages in a rolling 1-hour window OR >500 messages in a rolling 24h window. (Heavy expected baseline = 200/day; >500/day flags as outlier even before cost cap.)
- **Severity:** WARNING.
- **Recipient:** Rodc (email).
- **Auto-action:** Auto-pause user account for 1 hour (return HTTP 429 Too Many Requests on `/api/chat`); flag `pattern_review_pending`. Phase 1 alpha — pattern detection is rate-limit + hand review, not ML classifier.
- **Manual investigation path:** PostHog → user_id_hash → 24h session pattern. Distinguish: (a) genuine power user crossing into heavy-mix — investigate per R3; (b) automated test / scripted abuse — confirm via timing pattern (e.g. <500ms inter-message gap is bot-like); (c) compromised account — verify via Clerk session log.
- **Escalation if Rodc unavailable >24h:** Auto-pause expires (1h); cost cap (R3) catches over-spend; cumulative count keeps incrementing. Acceptable graceful degradation.

## Rule R6 — Crisis-content surface detected (INFO log-only)

- **Trigger:** Any extraction matches crisis keyword list (`assumption-list.md` D1 + Wave 1c protocol). Keyword list locked at Wave 1c dispatch; placeholder list per brand-book §7b: self-harm / suicide / hotline / "no point" / "can't go on" / etc.
- **Severity:** INFO.
- **Recipient:** **Logged only.** Do NOT page Rodc. Wave 1c crisis protocol handles user-facing surface (resource banner + chat-thread pause).
- **Auto-action:** Wave 1c protocol: (a) bypass extraction (no `topic: suicide` cards ever written — ship-blocking discipline per brand-book §7b); (b) surface resource banner ("This isn't what Rodix is built for. If you're in crisis, please reach out: 988 / Crisis Text Line / international resources"); (c) optional: chat-thread pause UI (warm refresh button).
- **Manual investigation path:** Wave 1c retrospective — quarterly review of crisis-content trigger rate. NOT individual investigation (privacy boundary — Rodc does not read individual crisis-content messages, by design and by brand commitment).
- **Escalation if Rodc unavailable:** Wave 1c protocol is autonomous — does not require Rodc real-time intervention. Quarterly review is async.

**Why INFO not WARNING/HIGH:** Brand-book §7b commits to Rodix being a *thinking* product, not a *therapy* product. Paging Rodc on crisis content would create Caregiver-flavored ops panic and could push Rodc toward inappropriate intervention. The discipline is: protocol handles user, log records frequency for cohort-level safety review, individual crisis-content is private to user.

---

## Recipient summary table

| Rule | Severity | Channel | Auto-action |
|---|---|---|---|
| R1 Extraction spike | CRITICAL | SMS + email | Auto-flag DEGRADED after 2h |
| R2 Total cost ceiling | CRITICAL | SMS | Auto-throttle |
| R3 Per-user cap | WARNING | Email digest hourly | Cap-enforced soft-block |
| R4 Recall precision | HIGH | Email | None — manual calibration |
| R5 Pattern abuse | WARNING | Email | Auto-pause 1h |
| R6 Crisis content | INFO | Log only | Wave 1c protocol |

## Phase 1 simplification

Phase 1 alpha (≤1,000 users / 30 days): SMS via Sentry-Twilio integration is overkill — email + push notifications via Sentry app suffice. PagerDuty deferred to Wave 4 / $10k MRR. Migration trigger: when Rodc is sleeping through the alarm OR when alpha cohort grows large enough that R1/R2 fire >1×/week.

---

*End alerting-rules.md.*
