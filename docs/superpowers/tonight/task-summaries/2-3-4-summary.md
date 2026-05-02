# Tier 1 Tasks 2-4 Summary — Wave 3 Plan + Acquisition + Pricing

**Completed:** 2026-05-03 ~Hour 8 (started Hour 7.5; 3 parallel background subagents)
**Time spent:** ~25 min wall-clock (truly parallel) / ~22 min sum-of-subagent-time
**Self-grade:** A- (combined)

Self-grade reasoning: 3 parallel subagents produced strong outputs. Critical surface: pricing-strategist caught a pricing error in my prompt (Haiku 4.5 actual $1/$5 vs my prompt's stale $0.25/$1.25), reframing economics from comfortable margins to 60-90-day-caching-dependent unit economics. This is the kind of catch that justifies parallel-with-verification dispatch.

## Outputs

### Task 2 — Wave 3 Plan
- `docs/superpowers/plans/wave3/spec-b-auth.md` (Clerk magic link + Google OAuth recommended)
- `docs/superpowers/plans/wave3/spec-b-encryption.md` (SQLCipher + per-user key from Argon2id KDF; explicit anti-spin lock on "encryption at rest, recall server-trusted")
- `docs/superpowers/plans/wave3/spec-b-multitenant.md` (row-level → per-user file at scale)
- `docs/superpowers/plans/wave3/spec-b-paddle.md` (Paddle MoR primary + Polar.sh fallback; 2-4 week approval critical path)
- `docs/superpowers/plans/wave3/spec-b-deploy.md` (Railway → Hetzner at $50/mo + Cloudflare EU geo-block)
- `docs/superpowers/plans/wave3/spec-b-security-review.md` (self-audit checklist)
- `docs/superpowers/plans/wave3/spec-b-privacy-policy.md` (coordinates with Task 8)
- `docs/superpowers/plans/2026-05-XX-wave3.md` (master plan, 242 lines)

### Task 3 — Acquisition Strategy
- `docs/superpowers/business/acquisition-research.md` (5 reference launches, 5 sources cited)
- `docs/superpowers/business/acquisition-strategy.md` (10 channels ranked; top 3 = HN / long-form blog / Twitter founder)
- `docs/superpowers/business/funnel-model.md` (per-stage conversion + sensitivity analysis)

### Task 4 — Pricing Deep Dive
- `docs/superpowers/business/llm-cost-real.md` (real Haiku 4.5 pricing $1/$5; 3 user strata; mix-weighted at $10k MRR)
- `docs/superpowers/business/competitor-pricing.md` (11 competitors current pricing)
- `docs/superpowers/business/pricing-model.md` (5 scenarios $5/$8/$10/$15/$20; sensitivity)
- `docs/superpowers/business/pricing-brand-aligned.md` (Explorer + Everyman archetype mapping)
- `docs/superpowers/business/pricing-strategy.md` (TL;DR: $10/mo + $100/yr + $8 founder pricing first 100)

## Key decisions made

### Task 2 — Wave 3 Plan
1. **Clerk over Auth0** — free tier 10k MAU, fastest setup for solo-anonymous founder. Lock-in: medium.
2. **SQLCipher over field-level encryption** — battle-tested, Python bindings, ~5% perf overhead. Per-user key derived from auth via Argon2id.
3. **Paddle over Stripe direct** — Merchant of Record handles VAT/sales-tax across 200+ countries, critical for solo-anonymous-founder-from-Asia.
4. **Railway over Hetzner for Phase 1** — $5-20/mo, auto-deploys; migrate at $50/mo Railway costs.
5. **Phase 1 = at-rest plaintext (no encryption)** — explicit anti-spin per friends-intro. Per-user encryption is Wave 3 SaaS work.
6. **Wyoming LLC default** for anonymity preservation (Escalation #9).
7. **Anti-spin marketing-copy lock:** "encryption at rest, recall server-trusted" — never "end-to-end encrypted" or "zero-knowledge" (Escalation #11).

### Task 3 — Acquisition Strategy
1. **Top 3 channels (priority order):**
   - HN Show HN (Day 0) — friends-intro voice native to HN; architectural-commitment frame is HN-native
   - Long-form blog (founder essay Day 5 + tutorials Day 15/25) — only channel that compounds beyond Day 30
   - Twitter founder thread + organic — @simonw / @karpathy / @swyx / @nat reply circles; anonymous handle constraint OK
2. **Funnel bottleneck = Stage 4** (first conv → 3 conv Week 1, 122→49 realistic case)
3. **Viral mechanic = Option C: Founder-direct invitation** — Rodc personally onboards each invite (15-30 min, capped 30/month). Trust-asymmetric retention + anti-target filter at door.
4. **Realistic Day-30 scenario:** ~120 first-conv users / ~32 Day-14 retained / ~10 paid (if priced).

### Task 4 — Pricing
1. **Recommended price: $10/mo, $100/yr (17% annual discount).**
2. **Founder pricing $8/mo for first 100 alpha users locked-in 12 months.**
3. **CRITICAL CORRECTION:** Haiku 4.5 actual pricing is $1/$5 per M tokens (4× higher than my prompt's stale $0.25/$1.25). Reframes unit economics.
4. **Wave 2 prompt-caching dependency:** without caching, blended LLM cost ~$15.18/mo vs $10/mo revenue. Caching is load-bearing-but-hidden financial assumption — must ship within 60-90 days post-launch (Escalation #10).
5. **Heavy user policy:** accept -77% GM as loss-leader at $10/mo (mitigated by Tier 3 Task 13 cost cap 50k input + 25k output / day).
6. **Free trial 14-day, NOT free tier** — Decision 7 forecloses on AI-credit metering.

## Type-A escalations surfaced

- **Escalation #9 (HIGH):** LLC jurisdiction + ownership-record posture (Wave 3 paid-launch blocker; Wyoming default)
- **Escalation #10 (HIGH):** LLM unit economics + Wave 2 caching 60-90 day dependency
- **Escalation #11 (MEDIUM):** Encryption marketing copy anti-spin lock (standing brand-discipline)

## Cross-task implications

- **Task 8 Privacy Policy + ToS:** "Who we are" section TODO — pending LLC formation (Escalation #9). Anti-spin language locked across Privacy Policy + ToS.
- **Tier 1.5 Phase A (in flight):** unaffected.
- **Tier 1.5 Phase B sample-verify:** unaffected.
- **Tier 2 Task 5 Marketing Landing:** pricing copy = "$10/mo / $100/yr / $8/mo founder pricing first 100" with TODO for Rodc final $ confirmation per Escalation #10.
- **Tier 2 Task 6 Marketing Suite:** pricing TBD until Rodc resolves Escalation #10. Marketing Suite agent likely uses placeholder.
- **Tier 3 Task 13 Observability + Cost Cap:** specifically enables heavy-user loss-leader mitigation (50k input + 25k output daily cap).

## TODO for Rodc

1. **Resolve Escalation #9** (LLC jurisdiction — Wyoming default).
2. **Resolve Escalation #10** (final pricing $10 default; confirm Wave 2 caching schedule).
3. **Acknowledge Escalation #11** (anti-spin marketing copy lock — standing).
4. **Read Wave 3 master plan** (`2026-05-XX-wave3.md`) — 242 lines, 6-8 week paid-launch critical path.
5. **Read pricing-strategy.md TL;DR** + sensitivity analysis (Phase 1 alpha viability + Wave 3 unit economics).
6. **Read acquisition-strategy.md** top-3 channels + 30-day calendar.
7. **Read funnel-model.md** Stage 4 bottleneck (Day-7 retention hook quality is highest-leverage operational lever).
8. **Initiate Stripe Atlas / specialized LLC formation** this week.

## Lessons / patterns noticed

Will append to reusable-patterns.md:
- **Subagent prompt-data-correctness verification:** Task 4 pricing-strategist caught my prompt's stale Haiku pricing ($0.25/$1.25 → actual $1/$5). When dispatching with quantitative claims, prompt should explicitly invite the subagent to "verify pricing/numerical claims against current source" rather than treat my numbers as authoritative.
- **Parallel-but-with-cross-task-implication-tracking:** 3 truly parallel agents on 3 independent tasks; their outputs converge (pricing affects marketing copy; LLC affects privacy policy; acquisition channel choice affects retention metrics). Post-merge integration is non-trivial — surfaced 2 new high-severity escalations.

## Cost log

- 3 parallel background subagents (~345k tokens total: 116k + 122k + 105k)
- 2 web_fetch failures (recoverable via WebSearch)
- 1 critical pricing correction caught by subagent verification

## Next: Tier 1.5 + Tier 2 in flight (8 background agents); Tier 3 Task 9 dispatch next.
