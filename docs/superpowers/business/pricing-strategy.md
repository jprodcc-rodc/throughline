# Rodix Phase 1 Pricing Recommendation

**Author:** pricing-strategist subagent (Tier 1 Task 4 final)
**Date:** 2026-05-03
**Status:** Draft for Rodc decision
**Inputs:** `llm-cost-real.md` · `competitor-pricing.md` · `pricing-model.md` · `pricing-brand-aligned.md`
**Brand-book references:** `brand-book-v1.md` §4 archetype Explorer + Everyman / §7 Decision 7 (thinking-not-engagement)

---

## TL;DR

- **Recommended: $10 / month, $100 / year** (17% annual discount, ~$8.33/mo effective)
- **Free trial:** 14 days, no credit card
- **Phase 1 alpha founder pricing:** $8 / month for first 100 users, locked for 12 months
- **No usage tiers, no team plan, no AI-credit metering** — flat rate, brand statement
- **Pause / cancel:** first-class options, no dark patterns, markdown export on the way out

---

## Reasoning

**Brand-aligned at $10.** Rodix sits in the Explorer + Everyman blend: sovereignty + accessible. The $8-12 indie cluster (Reflect $10, Capacities Pro $10, Heptabase Pro $9, Mem Pro $10-12) is Rodix's natural neighborhood. The $20 frontier-AI cluster (ChatGPT Plus, Claude Pro) is off-brand — Decision 1 of the brand book *"Not 'better AI'. The AI underneath is whatever you choose"* explicitly rejects competing on chat quality, and a $20 price would imply that competition.

**Financially viable at $10 — conditional on Wave 2 caching shipping.** Phase 1 (no caching) blended LLM cost is ~$15.18 / month / user — every plan below $20/mo loses money on average until prompt caching ships. Wave 2+ blended cost target is ~$7.50 / month, putting $10 at 16% blended GM. The pricing decision presumes Wave 2 ships within 60-90 days post-launch. **This is a load-bearing engineering dependency.**

**Competitor-positioned.** $10 sits cleanly in the indie-tool cluster (sub-frontier, sub-luxury). Reflect $10 is the closest direct comparable on price + brand register (single-tier, indie, anti-AI-credit-metering). Rodix's positioning vs. Reflect: Rodix is AI-chat-with-memory-on-top vs Reflect is networked-notes-with-AI-bonus.

**Founder pricing $8 / 100 users / 12-month lock** echoes Capacities Believer ($12.49 patron tier) but functions as time-bounded acquisition incentive rather than indefinite tier. Cohort-based ("first 100"), duration-named (12 months), graduates to standard ($10) — honest, refuses scarcity manipulation, fits Explorer voice.

**The trade-off Rodix accepts.** Heavy users at $10/mo are loss-leaders even at Wave 2+ caching ($16.85 cost vs $10 revenue). Decision 7 ("no engagement metrics") forecloses on AI-credit metering as the conventional fix. Rodix accepts heavy-user loss-leader status for Phase 1 alpha and constrains heavy-mix to <25% of cohort. If post-launch telemetry shows heavy mix >30%, Phase 2 introduces a usage-banded "Power" tier at $18/mo (honest framing: *"if you're using Rodix as primary thinking surface for hours daily, this covers the unbounded compute"*).

---

## Sensitivity

**If light/medium/heavy mix skews lighter (e.g., 30/60/10):** Blended cost drops to ~$5.81 (Wave 2+). $10/mo GM rises to ~33%. **Best-case retention math.**

**If mix skews heavier (10/50/40):** Blended cost rises to ~$10.55. $10/mo GM is -15% — pricing fails. **Trigger Phase 2 Power tier.**

**If churn is 8% / month (high):** LTV at $10/mo collapses to ~$20 — comparable to a $50 CAC / 31-month-payback at lower churn. **Below break-even on paid acquisition; only organic CAC works at $10.** Phase 1 is organic anyway.

**If conversion is half assumed (25% trial → paid instead of 50%):** $10k MRR target halves to $5k. Survivable at Phase 1 alpha (Rodc has no runway clock); not survivable at Phase 2 paid scale-up. Mitigation: graduate to $15/mo standard if Phase 2 paid acquisition becomes priority.

**If Wave 2 caching slips:** Every month past 90 days post-launch with $10/mo flat-rate and $15/mo blended cost = ~$5/user/month burn. At 1,000 users = $5k/mo burn. Sustainable for 6-12 months; not indefinitely. **This is the hard constraint that ties pricing to engineering schedule.**

---

## Open decisions for Rodc (Type-A)

### Decision 1 — Final $ amount

**Recommend: $10 / month standard.**

Alternatives:
- **$8 / month** — Everyman-leans-harder, fits friends-intro accessibility register strongly. Risk: GM negative on medium stratum until caching; constrains Phase 2 paid acquisition further. **If Rodc weights "accessibility above all" > "GM above all," choose $8.**
- **$12 / month** — Explorer-leans-harder, $2 cushion above LLM cost at Wave 2+, more room for engineering schedule slip. Risk: pushes against indie cluster ceiling; reads slightly premium vs Reflect $10. **If Rodc weights "engineering schedule risk" > "competitor anchor cluster," choose $12.**

### Decision 2 — Free trial vs free tier

**Recommend: 14-day free trial, no permanent free tier.**

Alternative: **Permanent free tier with conversation-cap** (e.g., 1 thoughtful conversation/day free, unlimited paid). Rejected primary because Decision 7 forecloses on engagement-metric framing. **If Rodc reads conversation-cap as "sample size" not "engagement metric," free-tier path is viable** — would expand top-of-funnel and viral acquisition at the cost of cohort-quality dilution.

### Decision 3 — Annual discount %

**Recommend: 17% (= 10× monthly = $100 / year).** Cluster-middle, round-number, reads honest.

Alternatives:
- **20% ($96 / year)** — slightly more competitive vs Heptabase 25%, but $96 is awkward
- **25% ($90 / year)** — matches Heptabase, reads "we really want you to commit" (mildly off-brand)

---

## Most-vulnerable financial assumption

**Wave 2 prompt-caching ships within 60-90 days post-launch.** This is the load-bearing assumption. Without it, blended LLM cost stays at $15.18/mo and every plan below $20/mo loses money. The pricing strategy assumes the engineering schedule.

**Mitigation if caching slips:**
1. Lengthen alpha cohort runway by capping new-user signup (Phase 1 was capped at ≤1,000 anyway — natural fit)
2. Tighten intent-classifier threshold to lower extraction rate from ~40% to ~25-30% (engineering quick-win, partial relief)
3. Communicate honestly to alpha cohort if caching ship slips: *"alpha is at-cost, full pricing model lands at public launch"* — Anti-spin voice volunteers the constraint

---

## Phase 2 (Chinese launch) pricing

**Deferred to Phase 2 plan. Likely lower — country-adjusted.**

Notes for that plan:
- Chinese market price norms ~30-50% lower than Western SaaS for similar prosumer products (e.g., Notion equivalents in CN at ¥30-50/月 ≈ $4-7/mo)
- Brand-book §3 commits Phase 1 = English-speaking international, no China launch — Phase 2 pricing is a separate strategic exercise once English-launch retention data is in hand
- Pricing power vs Chinese AI tools (Doubao, Kimi, Yuanbao) is constrained by local AI free tiers; Rodix's wedge there is portability + transparency, not raw chat quality
- Cross-model + markdown export are stronger differentiators in CN where vendor lock-in is even more pronounced (WeChat ecosystem, etc.)
- Local LLM cost economics differ — DeepSeek / Qwen route pricing more attractive than Anthropic OpenRouter route

**Recommendation for Phase 2 plan author:** assume target Phase 2 price ~¥35/月 ($5-6/mo USD) with annual ¥350 (~$50/year), founder pricing ¥25 first 100 CN users.

---

## Risk surfacing — task brief had wrong LLM pricing

The task brief specified `$0.25 / M input + $1.25 / M output` for Haiku 4.5. **Verified actual OpenRouter pricing is $1 / M input + $5 / M output — 4× higher.** All numbers in this strategy use the verified rates. The brief's old numbers would have suggested a sub-$5/mo plan was viable; with actual rates, $10/mo is the floor for Wave 2+ economics. Rodc — flagging in case the brief sourced from a stale internal note.

---

*End pricing-strategy.md. Awaiting Rodc decision on the three Type-A escalations + cohort-launch ammunition needs.*
