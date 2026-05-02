# Rodix Phase 1 Acquisition Strategy — 30-Day Alpha Plan

**Author:** acquisition-strategist subagent (Tier 1 Task 3)
**Date:** 2026-05-03
**Constraint:** Solo, anonymous, working from Asia. No personal-brand reach. No paid budget. Phase 1 = English-speaking international, no Chinese market, no EU.
**Companion docs:** `acquisition-research.md` · `funnel-model.md`.

This document does two jobs. **Part 1** ranks ten channels for Rodix specifically with a per-channel scorecard (effort / reach / quality / conversion / fit). **Part 2** is the combined 30-day acquisition plan: top-3 channels, calendar, retention sequence, and viral-mechanic pick.

---

# PART 1 — Channel ranking

Each channel scored on five axes:

- **Effort** = Rodc-hours over the 30 days
- **Reach (realistic)** = visits delivered in 30 days, not best-case
- **Quality** = how filtered the traffic is for the friends-intro 4-condition fit
- **Conversion (landing→signup)** = blended assumption per `acquisition-research.md`
- **Rodix-specific fit** = strength of match to brand-book §3 ICP + §4 archetype + anti-target

| Rank | Channel | Effort (hrs) | Reach (30d) | Quality | Conv L→S | Rodix fit |
|------|---------|--------------|-------------|---------|----------|-----------|
| **1** | **HN Show HN launch (Day 0)** | 8-12 (post + 12hr response window) | 500-3,000 | High | 3-10% | **Native fit** — HN audience is heavy thinking-tool users, AI-skeptical, technical. Architectural-commitment frame is HN-native. |
| **2** | **Long-form blog content (founder essay + tutorials)** | 20-30 (3 essays over 30 days) | 600-1,500 | Very high | 4-7% | **Strong fit** — founder essay encodes 4-condition filter directly; readers self-qualify before signup. Compounds beyond Day 30. |
| **3** | **Twitter founder thread + organic** | 15-20 (sustained engagement) | 600-1,200 | Medium-high | 2-4% | **Good fit with caveat** — anonymous handle reduces personal-brand leverage; Twitter rewards consistency over single thread. Substantive replies on @simonw / @swyx / @karpathy threads is the play. |
| 4 | IndieHackers community post + sustained engagement | 10-15 | 400-800 | Medium | 4-8% per engaged post | Mixed fit — IH skews builder-with-quick-answer-needs (fail-mode-2 risk). Best for "second wave" + post-mortem content, not primary launch surface. |
| 5 | Product Hunt launch (Day 1) | 8-10 (prep + launch day) | 800-2,500 | Low-medium | 1-2% | Mixed fit — PH audience is broad consumer-prosumer, includes large segment of "tries every tool" early-adopters who are anti-target per brand-book §3. Launch but don't lead with it. |
| 6 | Reddit (r/PKM, r/LocalLLaMA, r/ObsidianMD, r/ChatGPT) | 8-12 (substantive comments first, DMs second) | 300-600 | High in r/PKM and r/ObsidianMD, mixed in r/ChatGPT | 3-5% | Subreddit-dependent. r/PKM and r/ObsidianMD are condition-4 (record-of-evolved-thinking) gold. r/ChatGPT is condition-3 (creeped-out-memory) gold. Strict anti-pitch norms — comment-then-DM, never post product. |
| 7 | Newsletter swaps (TLDR / Bytes / Ben's Bites) | 5-8 (pitch + draft) | 0-2,000 (binary outcome) | Very high if landed | 5-10% | **Probably skip Phase 1.** Anonymous founder + no audience = no swap value to offer. Single exception: friend-of-Rodc with small AI-tools newsletter, treat as warm-intro variant. |
| 8 | Beta invite list / waitlist mechanic | 5-8 (landing + email seq) | 200-500 | Self-selected high | n/a (signup IS the action) | **Currently planned: skip waitlist, go direct.** Direct-signup-with-key matches Phase 1 plan; waitlist adds friction without a mechanic-payoff. Revisit only if launch over-yields and Wave 1c capacity is exceeded. |
| 9 | Cold outreach (DMs to potential users from interview cohort spillover) | 5-10 | 50-200 | Very high | 15-25% | High-quality but tiny absolute volume. Best as *complement* to recruit-strategy referrals, not standalone acquisition. Same DM template as `recruit-strategy.md` Channel 1. |
| 10 | **Paid ads — EXCLUDED** | n/a | n/a | n/a | n/a | **Documented exclusion.** Rodc has no budget; brand-book §4 Explorer archetype is incompatible with paid-acquisition posture (the moat is architectural-commitments-incumbents-cannot-make + small-cohort word-of-mouth, not LTV/CAC math); Phase 1 unit economics are unset (pricing TBD per Task 4) and paid acquisition without unit economics is fundraising-theater, not real channel work. **Revisit only post-Wave-3 if pricing + retention curves justify CAC.** |

## Top 3 channels — rationale

**#1 — Show HN (Day 0).** HN is the only channel where the friends-intro voice is *advantage*, not handicap. Anti-spin, naming-the-mechanism, refusing-to-dramatize are HN baseline. The architectural-commitment frame ("incumbents can't ship cross-model memory because the lock-in is the LTV thesis") is HN-native discourse. Realistic outcome: front-page top-30 = 1,500-3,000 visits, 3-5% L→S; below front page = 200-500 visits, 1-2%. Title and first comment decide which side. Recommended title: *"Show HN: Rodix — Memory layer for AI chat. Cross-model. White-box. Yours."* First comment within 30 min = the friends-intro §"How it actually works" brief. **Risk:** if the post reads "AI memory startup" not "architectural critique of incumbent designs," it dies on New.

**#2 — Long-form blog (founder essay + 2 tutorials).** Only channel that *compounds beyond Day 30.* Every other channel decays — HN 95% in 3 days, PH 80-90%, Twitter 50%/week. Founder essay (rodix.app/blog + Substack + cross-post HN-as-discussion) plus 2 tutorials becomes the SEO + organic-discovery tail. **Strategic answer to "where does user 101 come from":** the founder narrative encodes the 4-condition fit test directly — readers self-qualify in the post body, so conversion runs 4-7% (pre-filtered, not funnel-filtered). 6-month tail: 1,000-2,000 reads/month sustained. **Risk:** 3 long-form pieces in 30 days is real Rodc-time; if Wave 2 ships consume the hours, mechanism halves.

**#3 — Twitter founder thread + organic.** Only other channel besides HN where the target user actually congregates — @simonw / @karpathy / @swyx / @nat / @stevekrouse reply circles are the segment. **Anonymous founder is a real constraint:** Twitter rewards verified-name + photo plays. The compensation: post substantively, not promotionally. Reply-driven engagement, not post-driven. Realistic: 8-tweet founder thread = 300-800 reads; sustained reply engagement = 50-100 inbound profile views/week; Twitter→signup ~2-4%. Compounds slowly (~50-100 followers / 30 days). **Risk:** time-sink. 30+ min/session × 4-5x/week.

## Why paid ads are excluded

Three reasons even if budget existed: **(1)** Brand-book §4 Explorer archetype incompatibility — paid acquisition implies LTV/CAC optimization, which implies switching-cost retention, which dissolves the Explorer "user can leave any time" stance. **(2)** Unit economics are unset (pricing is Task 4); CAC budget without LTV anchor is fundraising-theater. **(3)** Anti-target risk — paid channels deliver broad-funnel traffic; Rodix's brand explicitly sends users away ("ChatGPT's fine"); paid acquisition fights the brand's own filter. Revisit only post-Wave-3 if pricing + 90-day retention + 3:1 LTV:CAC math hold.

---

# PART 2 — Combined 30-day acquisition plan

## Top 3 channels (carry-over from Part 1)

1. **HN Show HN** — Day 0 launch event
2. **Long-form blog** — founder essay Day 5, tutorials Day 15 + Day 25
3. **Twitter founder thread + organic** — Day 1-3 thread, sustained engagement Day 4-30

Supporting channels: PH Day 1 (treat as supplementary), Reddit Day 3 + Day 14 (subforum-specific), IH community post Day 7, cold outreach throughout (driven by interview-cohort referrals per `recruit-strategy.md`).

## 30-day calendar

| Day | Action | Channel | Expected outcome |
|-----|--------|---------|------------------|
| **-7 to -1** | Final landing-page polish; founder essay draft v3; HN title + first-comment draft; PH listing prep; Twitter thread draft (8 tweets); 5-candidate interview cohort completes (per recruit-strategy 72hr sprint) | All | Launch infrastructure ready |
| **Day 0** | **HN Show HN post at Tuesday 8am US Pacific** (peak HN traffic). Title: *"Show HN: Rodix — Memory layer for AI chat. Cross-model. White-box. Yours."* First comment by Rodc within 30 min. Standby for 12 hours of comment response. | HN | 500-3,000 visits, 30-90 signups |
| **Day 1** | **Product Hunt launch at 12:01am PST.** Maker comment from Rodc within first hour. Twitter thread published at PH-launch hour. Cross-link from PH to HN to rodix.app. | PH + Twitter | 800-2,500 PH visits, 300-800 thread reads, 20-60 signups |
| **Day 2** | Twitter reply engagement on 5 high-density threads from Day 0-1 (anyone who reacted to Show HN, anyone in the @simonw / @swyx / @karpathy reply trees). DM the 3-5 most substantive replies (not pitch — invite to alpha). | Twitter + cold | 100-200 visits, 5-15 signups |
| **Day 3** | **Reddit cross-posts.** r/LocalLLaMA: technical deep-dive on cross-model memory architecture (re-purpose HN technical comment). r/PKM: thread on "what does it mean to own your AI memory?" (frames the white-box card argument). Comment-driven, NOT promotional posts. | Reddit | 100-200 visits, 5-15 signups |
| **Day 5** | **Founder essay published on rodix.app/blog.** Cross-post to Substack (rodix-on-substack), Twitter thread quoting two specific paragraphs, HN as standalone (NOT Show HN — discussion post). | Blog | 400-800 visits over 7 days, 20-50 signups |
| **Day 7** | IndieHackers community post: "I shipped Rodix on HN at #X, here's the postmortem" — frames as transparent founder-build content, not pitch. | IH | 200-400 visits, 8-20 signups |
| **Day 10** | First Twitter retro: "30 days from idea-locked to launched — what worked." | Twitter | 100-300 visits, 3-10 signups |
| **Day 14** | **Reddit second wave.** r/ObsidianMD: cross-post the founder essay's "spine of conversations" example (the Sept 3 / Sept 19 / Oct 4 cards). r/ChatGPT: thread on Gemini "corporate secretary" failure mode (educational, frames problem space, links Rodix at end). | Reddit | 100-200 visits, 4-10 signups |
| **Day 15** | **Tutorial #1 published:** "How active recall actually works in Rodix." Walk through the threshold logic, the 4 trigger types, the see-trust-verify pattern. Technical, mechanism-named, links to source code if open-source-able. | Blog | 200-400 visits, 8-20 signups |
| **Day 21** | Mid-launch Twitter thread: "What 14 days of alpha taught me about AI memory" — extracted from real alpha telemetry (vault density, recall fire rate, fail mode 2 signals). Honest qualifications. | Twitter | 200-400 visits, 5-15 signups |
| **Day 25** | **Tutorial #2 published:** "Cross-model in practice — switching from Claude to GPT-5 mid-thought." Demo of memory portability. Cross-post to r/LocalLLaMA + Twitter. | Blog + Reddit | 300-500 visits, 10-25 signups |
| **Day 28-30** | Day-30 retro post on rodix.app/blog: alpha numbers, what surprised, what's next. Cross-post HN as standalone discussion. | Blog + HN | 200-500 visits, 5-15 signups |

**Calendar total:** ~6,100 visits realistic, ~120 first-conversation users (per `funnel-model.md` realistic-case math).

## Retention sequence — Day 1 / Day 7 / Day 30 hooks

The funnel-model.md analysis identifies Stage 4 (signup → 3 conversations Week 1) as the bottleneck. The retention sequence is designed around making *Stage 4 hold* through the recall mechanic, not through reminder-emails-as-engagement.

### Day 1 — first conversation hook

- **In-product:** intent classifier scores first message; if `thoughtful`, claim extractor produces 1-2 cards within 5-15 seconds of conversation end. User sees vault populate. **The product surfaces the value loop, not an email.**
- **Email:** *Subject: "your first cards"* — 80-word email from Rodc (signed). Body: "Two cards from your first conversation. Open your vault to see them. If they're wrong, edit them. If they're empty fields, that's the system being honest — null-by-default. Reply if anything's off." No marketing. No "welcome to your journey." Friends-intro voice.

### Day 7 — engagement hook (the load-bearing one)

This is where Stage 4 lives or dies. The hook is: **active recall fires for the first time on a returning conversation.**

- **In-product:** if the user returns and starts a new thoughtful conversation, the recall orchestrator surfaces the highest-scoring card (per `app/shared/recall/orchestrator.py` thresholds) with the ⚡ glyph and source attribution. *This is the Rodix moment.* Either it lands ("oh — yes, that's what I was thinking about") or it doesn't (silence, dismiss, "this isn't relevant"). The product itself is the retention mechanism; the email below is supplementary.
- **Email (Day 7 if user has had ≥1 thoughtful conversation but <3):** *Subject: "still here?"* — 60-word check-in. "You sent one thoughtful message on Day 1. You haven't been back. That's data — for me. If something pushed you away, I want to know. If you're just busy, that's fine. The vault holds whatever's there until you delete it." Anti-spin. No reactivation-bait.
- **Email (Day 7 if user has ≥3 thoughtful conversations):** no email. Don't interrupt. The product is working.

### Day 30 — sustaining hook

- **In-product:** Day-30 anniversary surface in vault: "You have N cards. Open the markdown export — see what 30 days of thinking looks like as files on your hard drive." This is the export-as-ownership-proof moment, not a celebration toast (per Decision 7 / brand-book §6).
- **Email:** *Subject: "month one"* — 100-word note from Rodc. "Here's what I learned about Rodix from your usage" (anonymized aggregate stats: avg cards/week, recall fire rate, modal topic categories). "Here's what's coming." "If you want to leave, the export button works — open it in Obsidian, paste it into Notion, throw it on a USB stick." Friends-intro closing voice. Surfaces the export-is-the-ownership-story commitment per Decision 6.

### What the retention sequence does NOT do

- No streak counter. No daily-summary email. No "you've earned a badge." No celebration toasts. No reactivation campaigns past Day 30 unless user explicitly opts-in. (Per Decision 7 — Rodix optimizes for thinking, not engagement; per brand-book §6 — UI density is Linear/Notion, not Notion-AI 3D-glass celebratory.)

## Viral mechanic — recommendation

**Recommended: Option C — Founder-direct invitation system (Rodc personally onboards each invite).**

**Why C over A and B.** Option A (invite codes for paid trial extension) is brand-clean but low-leverage — invitees arrive with no relationship to Rodc and the friends-intro brand-trust premium is lost. Option B (public thinking summaries) inverts the late-night-private-thinking privacy posture and pulls the product toward thinking-as-content (adjacent to journaling-app territory, brand-book §3 anti-target). Option C does three jobs at once:

1. **Trust-asymmetric retention.** A user with a 30-min Rodc-personal session has a structurally different product relationship — 3-5x more likely to retain, refer, tolerate Phase 1 rough edges.
2. **Anti-target filter.** Rodc screens out quick-answer-segment users before they consume product capacity. "ChatGPT's fine" enforcement at the door, not in the funnel.
3. **Brand-on-voice acquisition.** Direct founder onboarding *is* the "solo, anonymous, working out of Asia" posture. Per brand-book §8: "a funded team with no specifically-Rodc voice cannot simulate it."

**Operational form.** Existing alpha users get a "share" link in vault tab → pre-filled email to a friend (friends-intro voice, no incentive offered). Rodc personally runs onboarding sessions (15-30 min, batched 3-4 per week, capped at 8/week to protect Wave 2 build time). Session = run the 4-condition test live, walk through 1 thoughtful conversation, hand off. Cap: ~30 personal onboardings/month max — Rodc bandwidth is the ceiling.

**Risk + mitigation.** Mechanic does not scale past ~50 users/month at sustainable Rodc-burnout. **This is a feature, not a bug** — Phase 1 target is ≤1,000 alpha; the onboarding bottleneck *is* the brand-aligned filter. 30 onboardings × 80% retention × 1.5 invites each = 36 deeply-engaged users by Day 30, competitive with launch-event channels at higher quality. If mechanic under-yields by Day 30 (<10 founder-onboarded), fall back to Option A for Wave 2. Option B stays off the table until Wave 3 introduces a public surface compatible with thinking-as-content.

---

## 30-day expected outcomes — three scenarios

| Scenario | Day-30 alpha (first-conv) | Day-14 retained | Paid (if priced) | Wave 2 + pricing implication |
|----------|----------------------------|-----------------|-------------------|------------------------------|
| **Optimistic** | 200-300 | 60-90 | 18-32 | Wedge broader than friends-intro implies. Wave 2 prioritizes telemetry-driven recall calibration + exits-from-fail-mode-2. Pricing live by Day 21 at $12-15/mo, confident in LTV. Onboarding mechanic uncaps; Rodc protects Wave 2 build time by raising founder-onboarding bar (only the highest-fit-signal users). |
| **Realistic** | 80-150 | 25-45 | 8-15 | Wedge is real, narrow, holds. Wave 2 prioritizes fail-mode-2 telemetry, Day-7 retention hook quality, recall-callout polarity. Pricing launches conservative at $9-12/mo, alpha telemetry calibrates before raise. Founder-onboarding mechanic stays primary. |
| **Floor** | 30-50 | 6-12 | 0-2 | Either launch under-yielded or fail-mode-2 is real. Wave 2 narrows scope, accepts smaller alpha, Type-A escalation per `position-strategy.md` §4.2 — do NOT broaden product to absorb quick-answer segment. Pricing decision deferred — pricing on n=30 is noise. Founder-onboarding mechanic doubles down: every retained user becomes a P0 dogfood source. |

The realistic-case answer to the Lens 3 challenge "where does user 101 come from after launch fades": (a) blog tail at 6 months out delivers 1,000-2,000 reads/month sustained; (b) founder-direct invitation mechanic compounds at ~30/month sustained while Rodc has bandwidth; (c) referrals from retained alpha cohort run at ~0.5-1 referral per retained user every 60 days; (d) Twitter sustained engagement compounds slowly (~50-100 followers/month + ~100-200 inbound profile visits/week off reply engagement). Combined Day-31-to-Day-90 expected user adds: 80-200 sustained, with the blog tail being the highest-leverage non-Rodc-time-bound input.

---

*End acquisition-strategy.md. Companions: `acquisition-research.md`, `funnel-model.md`.*
