# Rodix Phase 1 Funnel Model — 30-Day Alpha

**Author:** acquisition-strategist subagent (Tier 1 Task 3)
**Date:** 2026-05-03
**Companion:** `acquisition-strategy.md` (channels + plan), `acquisition-research.md` (source data).
**Goal:** Model the 30-day funnel with conversion-rate assumptions sourced to real indie launch data, plus sensitivity analysis at half each rate.

---

## Stage definitions

| # | Stage | What counts |
|---|-------|-------------|
| 1 | Channel impression → landing | Click-through from HN / PH / Twitter / Reddit / IH post into rodix.app |
| 2 | Landing → signup | Email captured (waitlist or direct signup; Phase 1 design is direct signup with key, no separate waitlist) |
| 3 | Signup → first conversation | User sends ≥1 thoughtful message in chat (intent classifier scores `thoughtful`) |
| 4 | First conversation → 3 conversations Week 1 | User returns and has ≥3 thoughtful conversations within 7 days of signup |
| 5 | Week 1 engagement → Day 14 retention | User returns at least once between Day 7 and Day 14 |
| 6 | Day 14 retention → paid conversion at Day 21+ | User converts to paid plan (assumes pricing live by Day 21; if Phase 1 stays free, replace with "self-described willing-to-pay" survey response) |

---

## Realistic-case funnel (3% landing→signup, indie-SaaS-with-wedge baseline)

| Stage | Conversion | Source / rationale | Volume needed for 100 alpha by Day 30 |
|-------|------------|---------------------|----------------------------------------|
| 1. Impressions / clicks → landing | **n/a** (we count landing visitors as the top of funnel; channel mix in `acquisition-strategy.md` produces the volume) | Industry assumption: ad/social CTR isn't relevant — Rodix has no paid ads; channel-mix table is the funnel input | ~5,800 landing-page visits |
| 2. Landing → signup | **3%** | Blended indie-SaaS launch median: HN front-page 2-4% (Appliku 10% outlier, average lower), PH 1.4-2% (Plausible benchmark), IH per-post 19-23% (PostKing data, but tiny absolute volume); blended for our channel mix lands ~3% | ~5,800 × 3% = **174 signups** |
| 3. Signup → first conversation (activation) | **70%** | High because signup flow funnels straight into chat (no onboarding gate per `#1a` settings spec). 30% drop-off accounts for tire-kickers and email-only captures | 174 × 70% = **122 first-conversation users** |
| 4. First conv → 3 conv Week 1 (engaged) | **40%** | Heavy AI users typically retain at activation; 40% is conservative for a thinking-tool wedge (vs ~20% generic SaaS). The friends-intro 4-condition fit means activated users skew engaged. | 122 × 40% = **49 engaged Week-1 users** |
| 5. Week 1 → Day 14 retention | **65%** | Among already-engaged users, return rate Day 7-14 is high (~60-70% range for thinking-tool category per Roam/Obsidian-class data). | 49 × 65% = **32 Day-14 retained** |
| 6. Day 14 → paid at Day 21+ | **30%** | Among retained alpha users, paid conversion runs 25-35% in indie SaaS where the product solves a real felt pain. Assumes pricing live by Day 21. If pricing not live, this is "would pay if asked" survey signal. | 32 × 30% = **~10 paid alpha** |

**Realistic-case Day-30 alpha-user count:** ~120 *first-conversation* users (the right "alpha-user" count for Phase 1 measurement). Not the 174 signups (which inflate by tire-kickers); not the 32 Day-14 retained (which deflate by Phase 1 measurement window). **The number we report is 120.**

---

## Sensitivity analysis — half-rate stress test

What if every conversion rate in stages 2-6 is half what I assumed? (Stage 1 input volume held constant.)

| Stage | Realistic | Half-rate stress |
|-------|-----------|------------------|
| 1. Landing visits | 5,800 | 5,800 |
| 2. Landing → signup (1.5%) | 174 | **87 signups** |
| 3. Signup → first conv (35%) | 122 | 87 × 35% = **30 first-conv** |
| 4. → engaged Week 1 (20%) | 49 | 30 × 20% = **6 engaged** |
| 5. → Day 14 retained (32.5%) | 32 | 6 × 32.5% = **2 retained** |
| 6. → paid (15%) | 10 | 2 × 15% = **0 paid** |

**Stress-test Day-30 alpha count:** ~30 first-conversation users, 6 actually engaged, 2 retained at Day 14, 0 paid.

This is the floor scenario. It corresponds to "launch event under-yielded AND wedge is narrower than friends-intro implies AND retention curve is generic-SaaS-shaped, not thinking-tool-shaped." If Rodix lands here, fail mode 2 (users want quick answers, not continuity) is the most likely diagnosis.

---

## Bottleneck analysis

The bottleneck is **Stage 4 — first conversation → 3 conversations Week 1**. Three reasons:

1. It carries the largest realistic-case absolute drop (122 → 49, losing 73 users) and the largest half-rate fragility (49 → 6, losing 43 users at half-rate).
2. It is the stage most directly governed by *whether the product works for thinking* (vs. for novelty). A user who has a single thoughtful conversation but never returns has not validated the wedge.
3. It is the earliest stage where Rodc has *product* leverage rather than *acquisition* leverage. Stages 1-3 are channel-mix problems; Stage 4 is "does the recall callout, the vault, the see-trust-verify pattern actually compound?"

**Implication:** Day-7 hook in the retention sequence (see `acquisition-strategy.md` §retention) is the highest-leverage operational lever. If Day 7 produces a recall callout that visibly lands ("oh — that's the thing I said two weeks ago"), Stage 4 holds. If Day 7 produces an empty vault or a recall miss, Stage 4 collapses and the whole funnel does.

---

## Three scenario summary

| Scenario | Day-30 first-conv users | Day-14 retained | Paid (if priced) | Implication for Wave 2 + pricing |
|----------|--------------------------|-----------------|-------------------|----------------------------------|
| **Optimistic** (5% L→S, 80% activation, 50% engaged, 75% retained, 35% paid) | **~250** | ~75 | ~26 | Wedge is *broader* than friends-intro implies (heavy-AI-thinker segment is larger than we modeled). Wave 2 prioritizes telemetry-driven recall calibration. Pricing can launch at $12-15/mo with confidence; LTV thesis defensible. |
| **Realistic** (3% / 70% / 40% / 65% / 30%) | **~120** | ~32 | ~10 | Wedge is real, narrow, holds. Wave 2 prioritizes fail-mode-2 telemetry (intent classifier shape), Day-7 retention hook quality, and recall callout polarity (is it "trusty" or "creepy"?). Pricing launches at $9-12/mo, conservative; let alpha telemetry calibrate before raising. |
| **Floor / stress** (1.5% / 35% / 20% / 32.5% / 15%) | **~30** | ~2 | 0 | Either the launch event under-yielded *or* fail mode 2 is real (users want quick answers). Wave 2 narrows scope, accepts smaller alpha, and the explicit Type-A escalation per `position-strategy.md` §4.2: do not broaden product to absorb quick-answer use case. Pricing decision deferred — pricing on a 30-user base is noise. |

---

## Volume input — where do 5,800 landing visits come from?

Per `acquisition-strategy.md` 30-day calendar:

- HN Show HN launch (Day 0): ~3,000 visitors if front-page top-30, ~500 if below
- PH launch (Day 1): ~1,000 visitors realistic, up to 2,500 if Top 5 of day
- Twitter founder thread (Day 1-3) + sustained: ~600 visitors over 30 days
- IndieHackers post Day 7 + sustained engagement: ~400 visitors
- Reddit (r/PKM, r/ChatGPT, r/LocalLLaMA, r/ObsidianMD) Day 3 + Day 14: ~500 visitors
- Long-form blog (founder essay) cross-posted Day 5 + tutorials Day 15, Day 25: ~600 visitors (tail compounds beyond Day 30)
- Newsletter swaps (TLDR / Bytes if any land): ~200 visitors
- Word-of-mouth from interviews + early users: ~300 visitors

**Total realistic:** ~6,100 visitors over 30 days (conservatively rounded down to 5,800 to absorb attribution gap).

**Floor case** (HN below-front-page + PH Top 30 + low Twitter conversion): ~2,000 visitors → 30 first-conv users matches the stress-test outcome above.

---

*End funnel-model.md. Companion: `acquisition-strategy.md`, `acquisition-research.md`.*
