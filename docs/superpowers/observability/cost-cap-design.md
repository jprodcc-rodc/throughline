# Rodix Wave 3 — Per-User Cost Cap Design

> **Status:** Strategic-design depth. Wave 3 dossier. Author: observability-architect. 2026-05-03.
>
> **Anchors:** Escalation #10 (heavy-user loss-leader at $10/mo + Wave 2 caching dependency) · `business/pricing-strategy.md` (heavy mix <25% target / Phase 2 Power-tier $18-25 if >30%) · `business/llm-cost-real.md` (Haiku 4.5 $1/$5 per M tokens / 200 turns/day heavy user expected at ~400k tokens/day) · `brand/brand-book-v1.md` §5 voice (anti-spin / refuses-to-dramatize / banned phrases) · `brand/brand-book-v1.md` §7 Decision 7 (thinking-not-engagement — caps cannot read as engagement metering).

## 1. The problem

Heavy users at $10/mo cost Rodix ~$33/month in LLM spend (per `llm-cost-real.md` §3.3). Without caps, a worst-case "200-message night" user could burn $5+ in a single day. The mitigation must be: (a) generous enough that real heavy users feel respected, not metered (Decision 7 — anti-engagement-counter); (b) firm enough that runaway abuse / accidental loops don't bankrupt the alpha; (c) voiced anti-spin (no "you've used up your tokens" / no "quota exceeded").

## 2. Per-user daily token cap

**Cap = 50,000 input tokens + 25,000 output tokens / user / day.**

Sizing rationale:
- Light user expected: 25 turns × ~2,150 input + ~280 output = ~54k input / ~7k output / day
- Heavy user expected: 200 turns × ~2,150 input + ~280 output = ~430k input / ~56k output / day
- Cap of 50k input / 25k output is roughly **1.2× light user / 0.12× heavy user** — initially looks aggressive, but...

**Correction:** The cap as designed in the task brief is **1.2× light expected, not 3× heavy expected**. To honor "3× heavy-expected" framing while keeping cost bounded, the cap should scale with the expected heavy stratum, not the light stratum. **Revised recommended cap: 600k input + 100k output tokens / day** (3× heavy expected at ~200k input / ~30k output baseline reduced via Wave 2 caching). This translates to:

- Cost ceiling per user per day: 600k × $1/M + 100k × $5/M = $0.60 + $0.50 = **~$1.10/day, ~$33/month** (matches heavy stratum at-cost — no worse than current loss-leader)

For Phase 1 alpha (no caching, ≤1,000 users), the **stricter daily cap of 50k input / 25k output** ($0.18-0.30/day baseline) is preferred for runway protection. Heavy users will hit the cap occasionally (~5% of cohort per `pricing-strategy.md` heavy-mix calibration); they receive a soft block and a Rodc-review-flag (see §3 below). Wave 3b paid launch revisits cap to align with $10/mo or $25/mo Power-tier (see §5).

**Recommended Phase 1 alpha cap:** **50k input + 25k output tokens / user / day.** Cost ceiling per user per day: $0.18 baseline + ~$0.12 extraction overhead = **~$0.30/day, ~$9/month/user worst case**. At 1,000 users × ~$0.30 worst-case = $300/day = $9k/month max LLM burn — within Rodc's stated alpha-runway tolerance per `pricing-strategy.md` §5.

## 3. Hit-cap behavior

When user crosses 50k input OR 25k output cumulative for the UTC day:

**Soft block on input:** chat input field disabled. Banner appears above input:

> **Today's thinking budget is reached. Resume tomorrow at midnight UTC.**

**UI affordance:**
- Disabled chat input + countdown timer ("Resets in 7h 23m")
- Vault tab + Markdown export remain fully functional (offline thinking is unaffected — honors brand-book §7 Decision 4 real-export commitment)
- "Why am I seeing this?" link → support page explaining the cap honestly (anti-spin: "Phase 1 alpha is at-cost; we're holding daily compute steady to keep the alpha sustainable while we ship Wave 2 caching that will lift this cap.")

**Voice discipline (anti-spin per brand book §5):**
- DO say: "Today's thinking budget is reached." / "Resume tomorrow at midnight UTC."
- DO NOT say: "You've used up your tokens." / "Quota exceeded." / "You've hit your limit." / "Pay more to continue."
- DO NOT use process verbs: "leverage / unlock / supercharge / utilize."
- DO NOT dramatize or apologize: "We're sorry, but..." / "Unfortunately..."

**Cap reset:** Midnight UTC if user timezone unknown (Phase 1 alpha — no profile timezone yet). Phase 2 (Clerk profile lands timezone) shifts to user-local midnight.

## 4. Cost tracking implementation

**Schema (Wave 3 SQLite migration):**

```sql
CREATE TABLE usage_events (
    id INTEGER PRIMARY KEY,
    user_id_hash TEXT NOT NULL,           -- SHA-256(user_id), per privacy-aware-logging
    event_type TEXT NOT NULL,             -- 'chat_turn' | 'extraction' | 'recall_score' | 'vault_write'
    tokens_input INTEGER NOT NULL,
    tokens_output INTEGER NOT NULL,
    model TEXT NOT NULL,                  -- 'claude-haiku-4-5-20251001'
    cost_usd REAL NOT NULL,               -- precomputed at write time
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_usage_user_day ON usage_events(user_id_hash, DATE(created_at));

CREATE TABLE daily_user_cost (
    user_id_hash TEXT NOT NULL,
    date DATE NOT NULL,
    tokens_input_total INTEGER NOT NULL DEFAULT 0,
    tokens_output_total INTEGER NOT NULL DEFAULT 0,
    cost_usd_total REAL NOT NULL DEFAULT 0,
    capped BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id_hash, date)
);
```

**Aggregation:** SQLite materialized view rebuilt nightly via cron; on PostgreSQL migration (Wave 3b+), use `UPDATE daily_user_cost ... ON CONFLICT` per usage_events insert for real-time accuracy.

**Cost calculation (`app/shared/cost/pricing.py`):**

```python
HAIKU_45_INPUT_PRICE_PER_M = 1.0    # $/M tokens via OpenRouter
HAIKU_45_OUTPUT_PRICE_PER_M = 5.0

def compute_cost_usd(tokens_input: int, tokens_output: int, model: str = "claude-haiku-4-5") -> float:
    return tokens_input * HAIKU_45_INPUT_PRICE_PER_M / 1_000_000 \
         + tokens_output * HAIKU_45_OUTPUT_PRICE_PER_M / 1_000_000
```

Pricing constants live in this single module so re-pricing (Anthropic price drop / OpenRouter rate change) is one-file change. Audit-time grep `Grep "0\.000001"` should return zero matches outside `pricing.py`.

**Cap-check middleware (FastAPI dependency):** before each `/api/chat` call, query `daily_user_cost` for `(user_id_hash, today_utc)`. If `tokens_input_total >= 50000 OR tokens_output_total >= 25000`, return HTTP 402 Payment Required with structured body `{"capped": true, "reset_at": "<ISO-8601>"}`. Frontend renders the soft-block banner.

## 5. Override paths

**Rodc admin override:** environment variable `RODIX_USER_OVERRIDE_USERID` (comma-separated list of user_ids exempt from cap). Default value: Rodc's own user_id post-signup. Not configurable per-user in UI (Phase 1 — env var only); Phase 2 admin panel may surface this.

**Power-tier $25/mo (Wave 3b SaaS upgrade):** 3× cap (150k input + 75k output / day) — covers heavy stratum. Cost ceiling: $0.83/day = ~$25/month/user worst case — at-cost with $0 margin pre-caching. With Wave 2 caching: ~$0.10-0.15/day = ~$3-5/month/user, ~80% gross margin.

**Type-A escalation flagged:** Power-tier cap multiplier (3×) is one of three reasonable values (2× / 3× / 5×). 3× is the position-strategy.md §6 honest framing ("if you're using Rodix as primary thinking surface for hours daily, this covers the unbounded compute"). 2× is too tight for the friends-intro "200 hours in" power user; 5× is over-generous and breaks unit economics. Rodc to confirm 3× before Wave 3b dispatch.

## 6. Privacy-aware metrics

Per brand-book §7 Decision 1 (white-box, no shadow profile) + Decision 7 (thinking-not-engagement):

**OK to collect (aggregate):** total cost, total messages, retention cohorts, blended cost per stratum, hallucination rate, recall precision.

**OK to collect (per-user, hashed):** per-user cost, per-user message count, per-user retention bucket — keyed by `user_id_hash`, never by raw email or session content.

**NEVER collect (per-message content):** message text, AI reply text, card field text, recall callout text, raw user IPs in app logs.

**OK to collect (per-message structural):** token count, latency, model used, intent class, recall trigger type, recall score — labels and numbers only, never quoted text.

This discipline carries through to Sentry `before_send` (see `privacy-aware-logging.md` §1) and PostHog event schema (see `observability-spec.md` §4).

## 7. Wave 2 caching dependency (Escalation #10)

The cost cap is sized for **Phase 1 alpha pre-caching**. Wave 2 prompt-caching ships within 60-90 days post-launch (per pricing-strategy.md §1 load-bearing assumption); when it does, blended per-turn input cost drops ~80-90% via Anthropic prompt-cache discount. Cap can then **either** (a) stay at 50k/25k while heavy users now consume more turns within the budget (effective generosity rises 3-5×), **or** (b) lift to 150k/75k matching Power-tier — at Rodc's pricing-strategy decision.

Recommendation: **keep cap at 50k/25k post-caching.** The cap is now generous (~150-300 turns/day at cached rates) and the strict-cap discipline keeps Phase 1 alpha runway predictable. Rodc revisits at Wave 3b paid launch.

---

*End cost-cap-design.md. Awaiting Rodc confirmation on §5 power-tier 3× multiplier before Wave 3b.*
