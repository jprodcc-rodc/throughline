# Rodix Phase 1 — Real LLM Cost per User

**Author:** pricing-strategist subagent (Tier 1 Task 4 Phase 1)
**Date:** 2026-05-03
**Status:** Draft input to `pricing-strategy.md`

---

## 1. Pricing source of truth

**Haiku 4.5 via OpenRouter Anthropic proxy** — Wave 1b production model per `docs/superpowers/plans/2026-05-01-claim-extraction.md` v1.8.

Verified pricing on `openrouter.ai/anthropic/claude-haiku-4.5` (fetched 2026-05-03):

- **Input:** $1.00 / million tokens
- **Output:** $5.00 / million tokens
- Prompt caching: not exposed for this model on OpenRouter

> **Correction to task brief.** The task brief specified `$0.25 / M input + $1.25 / M output` as "Haiku 4.5 reference." Those are **legacy Haiku 3.5** rates. Actual Haiku 4.5 OpenRouter rates are **4× higher**. All numbers below use the verified $1 / $5 rates. This 4× delta materially changes unit economics — flagged for Rodc.

**Why Haiku 4.5 (not a cheaper model):** Wave 1b ship gate locked Haiku 4.5 specifically because it's the only model that hit the trust-killer hallucination threshold (≤2.3% in EN production-tier eval). nvidia-nemotron-3-nano free tier failed the trust-killer gate. The $1 / $5 cost is the price of `claim_extractor.md` null-by-default discipline working.

---

## 2. Token estimates per turn — calibrated against Wave 1b

**Input tokens per chat turn** (passes to model for chat reply, NOT extraction):
- System prompt (`rodix_system.md` v1.3): ~1,200 tokens
- Conversation history (rolling window, ~6 turns): ~800 tokens
- Active recall injection (Wave 2 ships): ~450 tokens additional system context
- Current user message: ~120 tokens
- **Total input per turn (Phase 1, Wave 1b, no recall yet):** ~2,150 tokens
- **Total input per turn (Wave 2+, with recall):** ~2,600 tokens

**Output tokens per chat turn:**
- Default 2-4 sentence response per voice ceiling §5: ~200 tokens
- Round 2 synthesis turns: ~400 tokens
- Round 3+ reflection turns: ~300 tokens
- **Weighted average across rounds:** ~280 tokens

**Extraction pass per "thoughtful" message** (separate model call):
- Extractor system prompt (`claim_extractor.md`): ~2,100 tokens
- Few-shot examples: ~600 tokens
- User message + assistant context: ~250 tokens
- **Extraction input total:** ~2,950 tokens
- **Extraction output (4-field card JSON):** ~120 tokens

**Extraction trigger rate:** Per Wave 1b intent-classifier eval — only "thoughtful" intents extract. Approximate 60% of turns trigger extraction in heavy-thinking-partner usage, 25% in mixed usage, 10% in chitchat-heavy usage. Use **~40% extraction rate** as the medium-user blended assumption.

---

## 3. Three usage strata — cost per user per month

### 3.1 Light user — 5 conversations/day × 5 turns = 25 turns/day, 750 turns/month

| Component | Tokens/month | $ Cost (Phase 1) |
|---|---|---|
| Chat input (750 turns × 2,150) | 1.61M | $1.61 |
| Chat output (750 × 280) | 0.21M | $1.05 |
| Extraction input (750 × 0.4 × 2,950) | 0.89M | $0.89 |
| Extraction output (750 × 0.4 × 120) | 0.04M | $0.18 |
| **Phase 1 subtotal** | **2.75M tokens** | **$3.73** |
| Active recall delta (Wave 2: +450 input/turn) | +0.34M | +$0.34 |
| LLM-judge eval (10% sampling, ~$0.02/judgment) | — | +$0.15 |
| **Total cost / Light user / month** | | **~$4.22** |

### 3.2 Medium user — 15 conversations/day × 5 turns = 75 turns/day, 2,250 turns/month

Mid-stratum reflects friends-intro "heavy AI user 2-3 hours/day" pattern, calibrated against Wave 1b dogfood Round 11 cadence (~12 cards/day in active sessions).

| Component | Tokens/month | $ Cost (Phase 1) |
|---|---|---|
| Chat input (2,250 × 2,150) | 4.84M | $4.84 |
| Chat output (2,250 × 280) | 0.63M | $3.15 |
| Extraction input (2,250 × 0.4 × 2,950) | 2.66M | $2.66 |
| Extraction output (2,250 × 0.4 × 120) | 0.11M | $0.54 |
| **Phase 1 subtotal** | **8.24M tokens** | **$11.19** |
| Active recall delta (Wave 2) | +1.01M | +$1.01 |
| LLM-judge eval (10% sampling) | — | +$0.45 |
| **Total cost / Medium user / month** | | **~$12.65** |

### 3.3 Heavy user — 40 conversations/day × 5 turns = 200 turns/day, 6,000 turns/month

Heavy user is the friends-intro "200 hours in" power user — multi-hour sessions, side-project decision-thinking, Vault grows ~30+ cards/day.

| Component | Tokens/month | $ Cost (Phase 1) |
|---|---|---|
| Chat input (6,000 × 2,150) | 12.90M | $12.90 |
| Chat output (6,000 × 280) | 1.68M | $8.40 |
| Extraction input (6,000 × 0.4 × 2,950) | 7.08M | $7.08 |
| Extraction output (6,000 × 0.4 × 120) | 0.29M | $1.44 |
| **Phase 1 subtotal** | **21.95M tokens** | **$29.82** |
| Active recall delta (Wave 2) | +2.70M | +$2.70 |
| LLM-judge eval (10% sampling) | — | +$1.20 |
| **Total cost / Heavy user / month** | | **~$33.72** |

---

## 4. Mix-weighted total at $10k MRR scale

Assume mix: **20% light / 60% medium / 20% heavy** (per task brief).

Per-user blended LLM cost: `0.2 × $4.22 + 0.6 × $12.65 + 0.2 × $33.72 = $0.84 + $7.59 + $6.74 = ~$15.18 per user / month`

**At $10/mo retail price:** Average revenue per user (ARPU) = $10. **LLM cost ratio = 152% of revenue** — i.e. company loses money on every user before infrastructure, payment processing, or labor.

**At $15/mo retail:** ARPU $15. LLM cost ratio = 101%. Still unprofitable.

**At $20/mo retail:** ARPU $20. LLM cost ratio = 76%. Gross margin 24% pre-Stripe-fees (~3%) and pre-infra. Net margin ≈ 20%.

### 4.1 Sensitivity: heavy-user mix sensitivity

Mix dominates. If heavy-user share rises:

| Mix (L/M/H) | Blended cost | $10/mo margin | $15/mo margin | $20/mo margin |
|---|---|---|---|---|
| 30 / 60 / 10 | $11.40 | -14% | 24% | 43% |
| 20 / 60 / 20 (base) | $15.18 | -52% | -1% | 24% |
| 10 / 60 / 30 | $18.96 | -90% | -26% | 5% |
| 20 / 50 / 30 | $19.39 | -94% | -29% | 3% |
| 10 / 50 / 40 | $23.17 | -132% | -55% | -16% |

**Critical observation:** Heavy users are catastrophically unprofitable below $20/mo. A 30-40% heavy mix with current pricing assumptions makes any flat-rate plan below $25 lose money outright. This is the central financial fact for Rodix Phase 1 pricing.

### 4.2 Conversation-length sensitivity (input balloon)

Phase 1 input cost is dominated by system prompt + conversation history + (Wave 2) recall injection. If users converse longer (more turns per conversation), conversation-history token count grows — but if rolling window is capped at ~6 turns, this is bounded. The unbounded growth comes from **vault size driving recall payload**: Wave 2 active recall injects up to ~3 cards × ~150 tokens each. If a user has 500+ cards and recall fires liberally, the per-turn input grows. Wave 2 calibration must hold the line.

### 4.3 Optimization levers (Wave 2+ engineering)

1. **Prompt caching** — Anthropic's prompt-caching API (Haiku 4.5 supports it via direct Anthropic; not exposed on OpenRouter today). System prompt + few-shots are stable across users → 90% cost cut on input. **Most impactful single optimization.**
2. **Extraction-rate downshift** — current ~40% extraction-rate assumption is calibrated against thoughtful-mix. Better intent classifier (Wave 1b shipped + ongoing tuning) can lower this to ~25-30% by skipping borderline cases more aggressively.
3. **Local extraction for small messages** — sparse cases (only `topic` extractable) could route to a 7B local model for further 90% savings on that subset. Engineering investment ~2 weeks.
4. **Tighter rolling window** — drop conversation history from 6 turns to 3 turns when no recall fires. ~30% input cut.

**Realistic Wave 2-3 cost target:** With prompt caching + tighter classifier + local sparse-case handling, blended cost can drop from $15.18 to ~$6-8 per user / month at the same usage profile. **This is the gross-margin path.**

---

## 5. Honest unit-economics framing

**Today (Wave 1b, no caching, no local fallback):** A heavy user at $10/mo costs Rodix ~$33 / month — Rodix loses **$23 per heavy user per month**. At $20/mo, Rodix loses $13 per heavy user per month. **Heavy users do not become profitable until ~$35-40/mo retail.**

**Tomorrow (Wave 2+ with caching):** Blended cost drops to ~$6-8 / month. At $10/mo retail, gross margin becomes 20-40% even at the heavy stratum. **Pricing decisions assume Wave 2 caching ships within 60-90 days post-launch.**

**Phase 1 alpha context:** Alpha cohort is ≤1,000 users targeting $10k MRR. Sensitivity calculus is small: even at $0 gross margin in alpha, $10/mo × 1,000 = $10k MRR achievable, monthly LLM burn ≤$15k (worst case), Rodc absorbs that during alpha to learn pricing behavior. The unit-economics fix is Wave 2-3 engineering, not pricing alone.

---

*End llm-cost-real.md — input to `pricing-model.md` (financial scenarios) and `pricing-strategy.md` (TL;DR).*
