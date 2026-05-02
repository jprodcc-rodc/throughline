# Rodix Phase 1 — Brand-Aligned Pricing

**Author:** pricing-strategist subagent (Tier 1 Task 4 Phase 4)
**Date:** 2026-05-03
**Inputs:** `brand-book-v1.md` §4 (archetype) + §7 (Decision 7) + `competitor-pricing.md` + `pricing-model.md`

---

## 1. Brand archetype as pricing constraint

**Primary archetype: Explorer. Secondary color: Everyman.** (Per `brand-book-v1.md` §4.)

Pricing is a brand surface — the price point itself is a message about who Rodix is for and what relationship it offers. Two implications run through every decision below.

### 1.1 Explorer reading of pricing

Explorer's defining quality is **sovereignty**. The four bets (white-box cards / cross-model / active recall / real markdown export) are framed as *exits*, not as transformations. The user's mental model: "I own this. I can leave. The product is a tool I picked up, not a relationship I'm in."

**Pricing implications:**
- **Annual discount = freedom-affirming, not lock-in.** Pricing language should not say "save by committing" — that's lock-in framing. Should say "annual is cheaper because billing overhead drops; cancel any month and prorated refund." The annual discount is a fact about cost, not a commitment device.
- **No "save your spot" / "limited time" / "founder's deal urgency"** — those are scarcity tactics; Explorer's voice rejects them. Founder pricing CAN be time-locked at the cohort level ("first 100 users") because that's a fact-pricing for a specific cohort, not a manufactured urgency for the reader.
- **"You can leave any time" must be load-bearing in pricing copy** — paired with markdown export (real ownership story per Decision 4 / Decision 6). Pricing page should literally say *"cancel any month, your cards export as markdown."*
- **No "billing surprises" / no "your subscription will renew" anxiety theater** — Explorer's anti-spin voice means receipts say what they are, no consumer-psychology defaults. Default to email-the-day-before-renewal, no auto-charge surprise.

### 1.2 Everyman reading of pricing

Everyman's color is *peer-to-peer, anti-elite, accessible*. The voice register is *"I noticed two things after a year of heavy AI use,"* not *"the premium AI memory layer for serious thinkers."*

**Pricing implications:**
- **Not premium-priced.** $20/mo signals "luxury thinking tool" — exactly the anti-target. ChatGPT Plus / Claude Pro / Heptabase Premium occupy that band. Rodix at $20 reads as "competing on AI quality" which the brand book §1 explicitly rejects (*"Not 'better AI'. The AI underneath is whatever you choose."*)
- **Accessible enough that the friends-intro reader doesn't pause.** A heavy AI user already paying $20 ChatGPT Plus + $20 Claude Pro ($40/mo on AI) shouldn't feel that adding Rodix is a third frontier-AI surcharge. Rodix at $10/mo reads as *"this is a layer on top, priced like a layer."*
- **No "team plans" / "Enterprise pricing"** — Phase 1 is single-user product (per `S10`). Skip the SaaS-default 3-tier pricing-page-with-Enterprise-CTA. One price, one annual.

### 1.3 §7 Decision 7 pressure — thinking, not engagement

> *Rodix is for thinking, not for engagement. We never optimize for time-on-app, daily-active-users, or message-volume metrics.*

Pricing must NOT optimize for engagement metrics. Specific consequences:
- **No tier based on "AI requests / day" or "AI credits / month."** That's exactly the engagement-metering pattern Tana / Heptabase / Saner ship — and it makes the user think about how much they're using vs. how much they're saving. Counter to the "thinking compounds" thesis.
- **No usage caps that punish thoughtful usage.** A user who has a 60-turn deep conversation about a hard decision should not hit "you've used your AI credits for the month" mid-thought. That breaks the thinking-compounding-metric.
- **One flat price per month — usage-irrespective.** This is unusual in the AI market, where almost every competitor meters AI usage. Flat pricing is a brand statement: *"think as much as you need to. The product is the thinking-partner; we're not metering your thinking."*

Acceptance: this means heavy users are loss-leaders. That's the brand cost of Decision 7. The pricing model accepts it (per `pricing-model.md` §6) and constrains heavy mix to <25% of cohort to remain solvent.

---

## 2. The financial-vs-brand tension — surfaced explicitly

**Financial model says:** $15-20/mo at Wave 2+ caching is the only price band with healthy gross margin across all heavy-mix scenarios. $10/mo only works if heavy mix stays <30%.

**Brand says:** $20/mo is the frontier-AI band — off-brand for the Everyman color and contradicts the "not better AI" anti-positioning. $10/mo aligns with Reflect / Capacities / Heptabase Pro / Mem Pro (the indie-tool $8-12 cluster).

**Competitors say:** Direct cluster is $8-12 (Reflect $10, Capacities Pro $10, Heptabase Pro $9, Mem Pro $10-12). Frontier-AI cluster is $20 (ChatGPT Plus, Claude Pro). Premium AI-power-user cluster is $14-18 (Granola $14, Heptabase Premium $18, Notion Business $18).

**The tension:** Financial says $15-20. Brand says $8-12. Competitors confirm both clusters exist. The friends-intro audience — *"if you've ever re-explained a project to ChatGPT for the fifth time"* — is heavy AI users already paying for ChatGPT Plus. They're sensitive to "another $20" but tolerate "$10 because this is a layer on top."

**Resolution: $10/mo, with two caveats.**

1. **The heavy-user loss-leader risk is real and named.** Rodix accepts it for Phase 1 alpha. If post-launch telemetry shows heavy mix >30%, **Phase 2 introduces a usage-banded "Power" tier at $18/mo** — not framed as "limited Free → unlimited Pro" (engagement-metric framing), but as "if you're using Rodix as a primary thinking surface for hours daily, the unlimited tier covers the unbounded compute." Honest framing per Anti-spin §5.
2. **Wave 2 caching must ship within 60-90 days post-launch.** Without it, $10/mo loses money on the medium stratum. Pricing decision presumes engineering execution — flagged as Type-A escalation in `pricing-strategy.md`.

---

## 3. Pricing framing strategies

### 3.1 Annual discount

**Recommended: 17% (12-month billed = 10× monthly).** $10/mo monthly OR $100/year ($8.33/mo effective).

**Why 17% not 20% / 25%:**
- 17% is the soft cluster middle (Tana 22%, Heptabase 25%, Reflect ~17%, Claude 14%)
- 20-25% reads as "we want you to commit" — Explorer's anti-lock-in voice cuts against that
- 17% is roughly the cost-of-capital differential — brand-honest framing: *"annual is cheaper because we don't have to chase monthly invoicing"*
- Round number ($100 / year) sticks better than $96 (20%) or $90 (25%)

**Alternative considered: $96/year (20%).** Rejected because $96 is awkward; $100 reads cleaner.

**Pricing copy framing (Explorer voice):**

> Rodix is $10 / month. $100 / year saves a couple bucks on billing overhead. Cancel any month — your cards export as markdown.

(28 words. Anti-spin: names the actual reason for the discount. Refuses-to-dramatize: no "save 17%!" exclamation. Parenthetical-as-honesty: cancel is the qualifier that undoes the lock-in implication.)

### 3.2 Founder pricing — first 100 users

**Recommended: $8 / month for first 100 alpha users, locked-in for 12 months.**

**Why this format:**
- Cohort-based (first 100), not time-based (this week only) — refuses scarcity manipulation
- 12-month lock-in is honest about what they're getting (12 months at the lower price), not infinite
- After 12 months, graduates to standard $10/mo — no surprise, named upfront
- Functions as both acquisition incentive (sub-$10 entry for early believers) AND retention signal (the brand commits to honoring early-trust)

**Anti-pattern check — does this violate Explorer voice?** Marginally. "First 100 lock-in" is a mild scarcity pattern. But it's honest: the cohort is small, the price is real, the duration is named. Compare to *"Limited time! Founders' price ends Friday!"* — that's the Explorer-incompatible version. The version recommended here is the honest cousin.

**Pricing copy:**

> First 100 alpha users get founder pricing — $8 / month for 12 months. After that, the standard $10. No tricks; this is the deal.

(25 words. "No tricks" is the anti-spin parenthetical-as-honesty.)

### 3.3 Family / team plan

**Skip for Phase 1.** Per `S10` brand assumption: *"Rodix is for the user alone with their thinking, not a dashboard for a team."* Phase 1 is single-user product. Team / family pricing would dilute the focus.

If Wave 3 demand emerges (Rodc instrumentation), a "household plan" could ship at $15/mo for 2 users — but that's Phase 3+ thinking, not Phase 1.

### 3.4 Pause vs cancel UX

**Recommended: pause is a first-class option.** Cancel is also one-click, no friction.

**Why pause:** A user pausing for a month doesn't lose vault, can resume seamlessly. This matches the friends-intro example: *"I might restart it next year. That's fine. Different decision."* Decisions-as-paths cadence. The product itself is built around the user coming back to a thought — pause-and-return is congruent with that.

**Pause pricing:** $0 during pause. Vault remains accessible read-only. AI chat disabled. Resume restores everything. Maximum pause: 90 days, then auto-cancel with full markdown export emailed.

**Cancel UX (Explorer voice):**

> Cancel takes one click. Your vault stays accessible read-only for 30 days; we email a markdown export the day you cancel. After 30 days the vault is permanently deleted from our servers.

(35 words. Mechanism named. Time qualifier concrete: 30 days, not "for a while.")

**Reject:** Mandatory exit-survey, "wait! we'll give you 50% off!" retention dark patterns, hidden-cancel-flow. Those are engagement-metric retention tactics that contradict Decision 7 explicitly.

### 3.5 Trial vs free tier — Type-A escalation

Two paths, both viable:

**Path A — 14-day free trial, no permanent free tier.**
- Pattern: Heptabase, Reflect, Mem
- Pro: forces decision; cleaner cohort metrics; no freemium overhead
- Con: friends-intro reader who wants to try "is this for me?" gets put on a clock immediately
- Brand fit: matches Explorer (try-it-and-decide) but doesn't soft-onboard

**Path B — Permanent free tier with usage cap, paid unlocks unlimited.**
- Pattern: Tana, Capacities, Saner, Granola
- Pro: lower friction to first card; word-of-mouth bonus
- Con: free-tier users dilute heavy-user calibration data; usage-cap design contradicts §7 Decision 7 ("no engagement metrics")
- Brand fit: Everyman-friendlier but conflicts with Decision 7 if free tier metering is visible

**Recommendation: Path A — 14-day trial, no permanent free.** Decision 7 forecloses on metered-free-tier; permanent-free-without-metering would be financially unsustainable at any meaningful scale. 14-day trial respects Explorer ("try the road, decide if it's yours") and keeps the financial model clean.

**This is a Rodc Type-A escalation.** Path B is not impossible — it could be implemented with a flat conversation-cap (e.g., "free tier = 1 conversation per day, unlimited cards from those") that doesn't read as engagement-metric, more as "this is a sample size." Rodc to weigh the strategic cost.

---

## 4. Final brand-aligned recommendation

**Phase 1 Rodix pricing — recommended:**

- **Standard plan:** $10 / month, billed monthly, OR $100 / year billed upfront ($8.33 / month effective, 17% annual discount)
- **Founder pricing:** $8 / month for first 100 alpha users, locked for 12 months
- **Trial:** 14 days, no credit card required up front
- **Pause:** first-class option, $0 during pause, vault read-only, 90-day max
- **Cancel:** one-click, 30-day grace + markdown export emailed
- **No tiers** at Phase 1 — single price, usage-irrespective
- **No team / family plan** at Phase 1
- **No AI-credit metering** — flat-rate is a brand statement

**Pricing-page copy register (Explorer + Everyman blend):**

> Rodix is $10 / month. $100 / year if you'd rather pay once.
>
> Free for 14 days, no card needed.
>
> Cancel any month — your cards export as markdown the day you leave.
>
> First 100 alpha users get founder pricing: $8 / month, locked for 12 months. After that, the standard $10. No tricks.

(63 words across 4 short paragraphs. Mechanism named. No buzzwords. Honest qualifier on the founder deal. Explorer cancel-anytime promise paired with Decision 4 markdown-export load-bearing.)

---

## 5. What this pricing refuses to be

Per Decision 7 + §5 voice principles, the pricing refuses:
- **Engagement-metric tiers** (no "AI credits / month")
- **Lock-in framing** (no "save by committing")
- **Scarcity manipulation** (no "this week only!")
- **Premium positioning** (no $20+ frontier-AI tier, no "Pro / Enterprise / Premium" upsell ladder)
- **Hidden-cancel UX** (no "are you sure? Wait! 50% off if you stay!" retention dark patterns)
- **Auto-renewal silence** (renewal email day-before, not surprise charge)

---

*End pricing-brand-aligned.md.*
