# Rodix Wave 3 Observability Spec

> **Status:** Strategic-design depth (not implementer-ready). Wave 3 dossier. Author: observability-architect (Tier 3 Task 13). 2026-05-03.
>
> **Composes with:** `wave3/spec-b-deploy.md` (Railway → Hetzner) · `business/pricing-strategy.md` ($10/mo + Wave 2 caching dependency) · `business/llm-cost-real.md` ($1/$5 per M tokens Haiku 4.5) · `brand/brand-book-v1.md` §6 / §7 Decision 1, 6, 7 (privacy stance + thinking-not-engagement + anti-spin) · `tonight/escalations.md` #10 (heavy-user loss-leader).
>
> **Sister files:** `cost-cap-design.md` (per-user caps) · `alerting-rules.md` (alert detail) · `privacy-aware-logging.md` (logging discipline + audit).

## 1. Goal

Production observability for Phase 1 alpha (≤1,000 users / 30 days) and beyond. Three layers: error tracking (Sentry) + metrics dashboard (PostHog) + structured logs (Loki via Railway addons or Cloudwatch on Hetzner migration). All three honor brand-book §7 Decision 1 (white-box / no shadow profile) and Decision 6 (anti-spin honest disclosure). Privacy-first: never log user message content / AI reply content / vault card content.

## 2. Error tracking — Sentry

**Tier:** Sentry free Developer plan — 5k errors + 5M spans + 50 replays / month. Sufficient for Phase 1 alpha ≤1,000 users / 30 days at expected error rate <1% (i.e. ~0.5k-2k errors/month). Migration trigger: Sentry Team tier ($26/mo) when sustained >3k errors/month for 2 consecutive months OR when team size grows beyond solo-founder.

**Privacy-aware configuration.** The Sentry SDK runs a `before_send` hook that strips PII before transmission. Specifically scrubbed fields:

- `request.data` (raw POST body containing user message text)
- `extra.message_content` (any explicit user-message attachment)
- `extra.ai_reply` (assistant response body)
- `extra.card_content` (vault card field text — topic / concern / hope / question)
- `extra.recall_callout_content` (active-recall surface text)
- `request.headers.cookie` + `request.headers.authorization` (default Sentry scrub)

User identifiers are sent as `user.id_hash` (SHA-256 of `user_id`, never raw email or session ID). See `privacy-aware-logging.md` §1 for the Python `before_send` hook source.

**Alert rules (configured in Sentry):**

- Error rate spike: >2% errors / total transactions over rolling 5-min window → email + Sentry app notification
- New error type (issue first seen): immediate notification on first occurrence
- Slow query: p95 transaction latency >2s over 5 min → email
- Performance regression: p95 latency 50% above 7-day baseline → email

## 3. Logging strategy

**Format:** Structured JSON logs to stdout (Railway captures; Loki ingests at Hetzner migration). One JSON object per line; required fields: `timestamp` (ISO-8601 UTC), `level`, `correlation_id`, `user_id_hash`, `op`, `latency_ms`, `success`, `model`, `tokens_input`, `tokens_output`, `error_class` (if `level=ERROR`).

**Correlation IDs:** UUIDv7 (time-orderable) generated per session start. Propagated through chat → extraction → recall scoring → vault write so a single user-facing turn can be traced end-to-end. Per-user correlation across sessions uses `user_id_hash` (NOT raw `user_id`). UUIDv7's time-ordering allows efficient log queries by time window without secondary indexes.

**Log levels:** `ERROR` (failures requiring investigation) · `WARN` (recoverable degradation, e.g. recall scoring fallback) · `INFO` (business events, e.g. extraction success / cost crossing) · `DEBUG` (off in production, on during dogfood).

**DO NOT log (forbidden field list):**
- User message content (raw text from `/api/chat` POST body)
- AI reply content (assistant turn text, full or partial)
- Vault card field content (`topic` / `concern` / `hope` / `question` text)
- Recall callout content (the `⚡ I brought this back` quoted text)
- Email addresses (only `user_id_hash` — Clerk's user_id post-signup)
- Raw IPs (Cloudflare-edge IP for legitimate request logging is fine; never user IP in app logs)

**DO log (allowed structural metrics):**
- Operation type (`chat_turn` / `extraction` / `recall_score` / `vault_write` / `markdown_export`)
- Latency (ms, per stage)
- Success / failure (boolean)
- `user_id_hash` (SHA-256 of user_id, deterministic for cross-day correlation without identifying)
- Model used (`claude-haiku-4-5-20251001` / etc.)
- Token counts (`tokens_input`, `tokens_output`, integers)
- Intent classification result (`thoughtful` / `chitchat` / `confused` / `closed` — labels only, no message text)
- Recall trigger type (`topic` / `stance_drift` / `loose_end` / `decision_precedent`) + score (number)
- Error class name (`AnthropicAPIError` / `ExtractionParseError` / `RecallScoreFailure` — never error message body if it might quote user content)

**Retention:** 30 days production logs, automatic purge enforced via Loki retention config (`retention_period: 720h`) on Hetzner migration; Cloudwatch retention policy on Railway-resident logs (`retention_in_days: 30`). Annual privacy audit (see `privacy-aware-logging.md` §3) confirms purge is operating.

## 4. Metrics dashboard — PostHog

**Tier:** PostHog free tier (1M events / month, 1-year data retention, no credit card). 1,000 users × ~50 events/user/day = ~1.5M events/month at heavy mix — close to the cap; events should be filtered to *meaningful* events only (turn-level summary, not per-token). Migration trigger: PostHog Pay-as-you-go ($0.00005/event after 1M) at sustained >1.2M events/month.

**Per-day metrics (PostHog dashboards):**

- **Extraction success rate** — target ≥95% (Wave 1b production-tier eval gate). Drop below 90% = engineering investigation.
- **Hallucination rate** — sampled 5% of extractions, LLM-judge runs nightly batch. Calibration trigger if >5% sustained over 3 days (per `claim_extractor.md` v1.8 ship gate).
- **Latency p50 / p95 / p99** — chat turn / extraction / recall scoring (three separate panels).
- **Cost per user (today)** — input tokens × $1/M + output tokens × $5/M, per user_id_hash.
- **Active recall precision** — sampled 10% with LLM-judge, gate ≥80% per Wave 2 plan; <70% over 24h = `alerting-rules.md` Rule R4.
- **Active users (24h)** — DAU. NOT a brand-aligned engagement metric (Decision 7 forecloses), but is a load metric for capacity planning.

**Per-week metrics:**

- **Retention cohort** — Day 1 / Day 7 / Day 14 / Day 30 retention per signup cohort. Drives understanding of whether the wedge is sticking; cohort comparison across product changes.
- **Conversion to paid** — signup → 14-day-trial-end → paid. Phase 1 paid launch metric (per pricing-strategy.md §1 — only meaningful after `#b-paddle` ships).
- **Churn signals** — paid users canceling within 30 days; cohort by signup month. Triggers Phase 2 Power-tier evaluation per pricing-strategy.md §3.

**PostHog vs Sentry:** Sentry is for error/perf signals. PostHog is for product/business signals. They are complementary, not redundant. Recommendation rationale: PostHog's funnel + cohort views are out-of-the-box; recreating these in a SQLite dashboard would be 1-2 weeks of bespoke work. PostHog free tier is sufficient at Phase 1; Sentry free tier is sufficient at Phase 1; combined cost: $0/mo until either crosses scale threshold.

## 5. Alerting summary

See `alerting-rules.md` for full detail. Top-level summary: 6 rules covering extraction failure spike (CRITICAL), daily cost ceiling (CRITICAL), per-user cost cap (WARNING + auto-pause), recall precision drop (HIGH), suspicious-pattern abuse (WARNING + auto-pause), and crisis-content surface (INFO log-only — Wave 1c protocol handles user-facing).

## 6. Implementation outline (Wave 3a alpha)

1. Sign up Sentry free tier → install `sentry-sdk[fastapi]` in `app/web/server.py` startup with `before_send` hook (see `privacy-aware-logging.md`).
2. Sign up PostHog free tier → install `posthog-python` SDK; emit events from chat / extraction / recall stages with `user_id_hash` only.
3. Add structured-logging middleware to `app/web/server.py` — replaces any current `print()` / `logging.info()` calls with JSON structured emitter; enforce forbidden-field list in logger wrapper.
4. Configure Sentry alert rules (web UI; export to JSON for re-creation if vendor switched).
5. Create PostHog dashboards: 4 daily panels + 3 weekly panels.
6. Cost-cap enforcement table → see `cost-cap-design.md`.
7. Quarterly privacy audit cron job → see `privacy-aware-logging.md` §3.

## 7. Cost estimate

Phase 1 alpha: **$0/mo** (Sentry + PostHog free tiers). Hetzner migration adds Loki self-hosted (~$0 marginal on existing Hetzner box). Annual privacy-audit Rodc-time: ~2h/quarter. Negligible ops fatigue at Phase 1 scale.

At $10k MRR (~5k users): Sentry Team $26/mo + PostHog Pay-as-you-go ~$50-100/mo (5k users × ~50 events/day × 30 days = 7.5M events/mo × $0.00005 = $375/mo — likely **too expensive at scale**, recommend self-hosted PostHog or sampled events at 25%).

## 8. Risk register

1. **Sentry SDK leaking user content via stack-trace local variables** — moderate. Mitigation: `before_send` hook + quarterly grep audit (see `privacy-aware-logging.md` §3).
2. **PostHog event schema drift breaking dashboards** — low. Mitigation: typed event-emitter wrapper, schema tests.
3. **Loki retention misconfiguration** — moderate. Mitigation: explicit retention test (write known-old log line, verify purge after 31 days).
4. **Cost-tracking off by Anthropic-vs-OpenRouter pricing delta** — low. Mitigation: pricing constants in single file (`app/shared/cost/pricing.py`); see `cost-cap-design.md` §4.

---

*End observability-spec.md. Phase 1 alpha → Wave 3a dispatch ready.*
