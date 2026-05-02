# Rodix Phase 1 — Pricing Model (5 Scenarios)

**Author:** pricing-strategist subagent (Tier 1 Task 4 Phase 3)
**Date:** 2026-05-03
**Inputs:** `llm-cost-real.md` (cost) + `competitor-pricing.md` (anchors)

---

## 1. Inputs and assumptions

**Per-user blended LLM cost (Phase 1, no caching):** $15.18 / month
- Light (20%): $4.22
- Medium (60%): $12.65
- Heavy (20%): $33.72

**Per-user blended LLM cost (Wave 2+, with prompt caching + intent-classifier tightening):** ~$7.50 / month — used as "Wave 2 target" column.

**Phase 1 alpha context:** ≤1,000 users target, $10k MRR target, no growth team, founder-direct support cost ≈$0 / month per user (absorbed in Rodc's labor).

**Stripe fees:** ~3% of revenue (assume $0.30 fixed + 2.9% on $10 sub ≈ $0.59 / sub / month).

**Infra cost (Postgres / object storage / observability):** ~$0.30 / user / month at alpha scale (amortized fixed costs over 1k users).

**Total non-LLM variable cost per user:** ~$0.90 / month.

---

## 2. Five pricing scenarios

### 2.1 Gross margin per user (after LLM + Stripe + infra)

**Phase 1 (Wave 1b, no caching) — blended cost $15.18 / month:**

| Price | Revenue | LLM cost | Other | **GM $** | **GM %** |
|---|---|---|---|---|---|
| $5 / mo | $5.00 | $15.18 | $0.90 | -$11.08 | -222% |
| $8 / mo | $8.00 | $15.18 | $0.90 | -$8.08 | -101% |
| $10 / mo | $10.00 | $15.18 | $0.90 | -$6.08 | -61% |
| $15 / mo | $15.00 | $15.18 | $0.90 | -$1.08 | -7% |
| $20 / mo | $20.00 | $15.18 | $0.90 | $3.92 | 20% |

**Wave 2+ (with caching) — blended cost $7.50 / month:**

| Price | Revenue | LLM cost | Other | **GM $** | **GM %** |
|---|---|---|---|---|---|
| $5 / mo | $5.00 | $7.50 | $0.90 | -$3.40 | -68% |
| $8 / mo | $8.00 | $7.50 | $0.90 | -$0.40 | -5% |
| $10 / mo | $10.00 | $7.50 | $0.90 | $1.60 | 16% |
| $15 / mo | $15.00 | $7.50 | $0.90 | $6.60 | 44% |
| $20 / mo | $20.00 | $7.50 | $0.90 | $11.60 | 58% |

### 2.2 Per-stratum margin at recommended Wave 2+ economics

**$10 / mo (recommended):**

| Stratum | LLM cost | GM $ | GM % |
|---|---|---|---|
| Light | $2.10 (caching) | $7.00 | 70% |
| Medium | $6.30 (caching) | $2.80 | 28% |
| Heavy | $16.85 (caching) | -$7.75 | -77% |

**$8 / mo (alternative — Everyman lean):**

| Stratum | LLM cost | GM $ | GM % |
|---|---|---|---|
| Light | $2.10 | $5.00 | 63% |
| Medium | $6.30 | $0.80 | 10% |
| Heavy | $16.85 | -$9.75 | -122% |

**$12 / mo (alternative — Explorer lean):**

| Stratum | LLM cost | GM $ | GM % |
|---|---|---|---|
| Light | $2.10 | $9.00 | 75% |
| Medium | $6.30 | $4.80 | 40% |
| Heavy | $16.85 | -$5.75 | -48% |

**Critical observation:** At any price under $25/mo, the heavy stratum is unprofitable even at Wave 2+ caching costs. **Rodix needs either (a) usage-cap tier for heavy users, (b) explicit acceptance that heavy users are loss-leaders subsidized by light/medium, or (c) tiered "Pro Heavy" upsell.** The model below assumes (b) — heavy is loss-leader for word-of-mouth but capped at <25% of cohort.

---

## 3. Break-even users (acquisition cost recovery)

**At $50 CAC (organic / HN / founder-essay channel):**

| Price | Wave 2+ GM $ | Months to recoup CAC |
|---|---|---|
| $5 | -$3.40 | never |
| $8 | -$0.40 | never |
| $10 | $1.60 | 31.3 months |
| $15 | $6.60 | 7.6 months |
| $20 | $11.60 | 4.3 months |

**At $150 CAC (paid acquisition / sponsored content):**

| Price | Wave 2+ GM $ | Months to recoup CAC |
|---|---|---|
| $10 | $1.60 | 93.8 months (impossible — exceeds expected lifetime) |
| $15 | $6.60 | 22.7 months |
| $20 | $11.60 | 12.9 months |

**Implication:** $10/mo only works at organic CAC. **Rodix cannot run paid acquisition at sub-$15 pricing** — the unit economics fundamentally do not support it. Phase 1 is HN / founder essay / Twitter — purely organic — so $10 is acceptable for Phase 1, but Phase 2 paid scale-up requires either higher pricing OR aggressive caching wins.

---

## 4. LTV at retention scenarios

**LTV formula:** `LTV = ARPU × gross margin % × average lifetime (months)`

**Wave 2+ economics, 12-month average lifetime (modest churn ~5%/mo):**

| Price | GM % blended | LTV |
|---|---|---|
| $5 | -68% | -$40.80 |
| $8 | -5% | -$4.80 |
| $10 | 16% | $19.20 |
| $15 | 44% | $79.20 |
| $20 | 58% | $139.20 |

**Wave 2+ economics, 24-month average lifetime (sticky, ~3%/mo churn):**

| Price | LTV |
|---|---|
| $10 | $38.40 |
| $15 | $158.40 |
| $20 | $278.40 |

---

## 5. Churn sensitivity

**At 3% monthly churn (sticky thinking-partner case):** Average lifetime ≈ 33 months
**At 5% monthly churn (medium):** Average lifetime ≈ 20 months
**At 8% monthly churn (early SaaS norm for prosumer):** Average lifetime ≈ 12.5 months

**LTV at $10/mo, Wave 2+ economics ($1.60 GM):**

| Churn | Lifetime | LTV |
|---|---|---|
| 3% | 33 mo | $52.80 |
| 5% | 20 mo | $32.00 |
| 8% | 12.5 mo | $20.00 |

**LTV at $15/mo:**

| Churn | Lifetime | LTV |
|---|---|---|
| 3% | 33 mo | $217.80 |
| 5% | 20 mo | $132.00 |
| 8% | 12.5 mo | $82.50 |

**Implication:** The retention assumption matters more than the price point in the $10-15 range. A $10 product with 3% churn and an $18 product with 8% churn have similar LTV. **Rodix's retention is the variable to optimize** — the friends-intro thesis (continuity-of-thought wedge → multi-month decision tracking → low churn) is the financial bet.

---

## 6. Heavy-user mix sensitivity (the dominant variable)

At $10/mo (Wave 2+ caching costs), blended GM as heavy-mix changes:

| Heavy mix | Blended cost | GM $ at $10 | GM % |
|---|---|---|---|
| 5% | $5.81 | $3.29 | 33% |
| 15% | $7.06 | $2.04 | 20% |
| 20% (base) | $7.50 | $1.60 | 16% |
| 30% | $8.62 | $0.48 | 5% |
| 40% | $10.55 | -$1.45 | -15% |

**Implication:** Heavy-user mix above 30% kills the $10 plan even with caching. **Critical Phase 1 metric to instrument: heavy-user-share-of-cohort.** If alpha tracks toward 30%+ heavy mix (the friends-intro 200-hours-in pattern is heavy), pricing must reset upward OR a usage-cap "Free / Pro / Power" tier must ship in Phase 2.

---

## 7. Sensitivity summary

**Dominant variables (in order of impact):**

1. **Heavy-user mix** — moves blended cost ±60% across 5-40% range
2. **Caching ship date** — Wave 2 prompt-caching is a ~50% cost cut; until it ships, every plan below $20/mo loses money on average
3. **Retention** — 3% vs 8% churn is a 2.6× LTV swing
4. **Conversion rate at the price point** — see §8 below
5. **CAC channel** — paid is impossible below $15/mo

**Subordinate variables (smaller impact):**

6. Annual discount % — 17-25% range moves average ARPU by single digits
7. Stripe fees — fixed at ~3% of revenue
8. Infra costs — fixed at ~$0.30 / user / month at alpha scale

---

## 8. Conversion-rate hard challenge (Lens 3)

**What if conversion is half assumed?** The friends-intro target is ≤1,000 alpha in 30 days. If trial→paid conversion is half assumed (e.g., 25% instead of expected 50%):

- 1,000 trials × 25% = 250 paid
- $10 × 250 = $2,500 MRR (not $5,000)
- LLM burn at heavy mix: 250 × $15.18 = $3,795 — **net negative ~$1,300 / month**
- Annual: $30k MRR target collapses to $15k MRR

**Mitigation paths:**
1. **Higher price compensates lower conversion:** $20 × 250 = $5,000 MRR (matches target) — but higher price probably reduces conversion further (price elasticity)
2. **Free tier with paid upsell:** higher top-of-funnel (more "users"), lower conversion (more freeloaders), but viral acquisition compensates
3. **Founder pricing first 100:** $8/mo locked-in for 12 months → if 100 paid + 150 trial-converters at $10 → $800 + $1,500 = $2,300 (modest but predictable)
4. **Accept lower revenue, focus on retention learning** — Phase 1 alpha value is the *learning*, not MRR

**Rodc's Phase 1 financial cushion:** No board, no growth team, no paid acquisition. $10k MRR target is a coordination point, not a runway requirement. **Conversion-rate downside is survivable at the $10-15 band; not at $5-8 band where every additional user is a net loss.**

---

## 9. Summary table — recommended price by scenario

| Goal | Recommended price | Reasoning |
|---|---|---|
| Maximize MRR, healthy GM | $15 / mo | Best margin/conversion tradeoff at Wave 2+ economics |
| Match Everyman positioning | $10 / mo | Aligned with $8-12 indie cluster (Reflect / Mem / Capacities) |
| Aggressive accessibility | $8 / mo | Below GM at heavy mix; only works if heavy <15% |
| Premium / luxury | $20 / mo | Fights ChatGPT Plus directly; off-brand per anti-target |
| Phase 1 alpha founder pricing | $8 / mo first 100 | 12-month locked, then graduate to standard tier |

**Recommended: $10 / month standard; $96 / year ($8 / month effective, 20% annual discount); founder pricing $8 / month for first 100 alpha users locked-in 12 months.**

Detailed reasoning + brand alignment in `pricing-brand-aligned.md`. TL;DR + Type-A escalations in `pricing-strategy.md`.

---

*End pricing-model.md.*
