# TONIGHT ESCALATIONS — Append-only

Read in severity order: Critical → High → Medium → Low.

═══════════════════════════════════════════════════════════
ESCALATION #1 — task-0a — RESOLVED 2026-05-03 ~Hour 1.5
═══════════════════════════════════════════════════════════

**RESOLUTION (Rodc 2026-05-03 mid-shift):** Rodc located `rodix-friends-intro.md` and saved to `~/Downloads/rodix-friends-intro.md`. CC re-ran Phase 3 (3 brand subagents) + Phase 4 integrator + Phase 5 skeptic with friends-intro as primary input, brainstorm as secondary. Brainstorm-based outputs preserved as `*-brainstorm-based.md` for audit. Final brand-book-v1.md uses friends-intro voice.

**De-prioritized in severity ranking. Original entry retained below for audit.**

When: 2026-05-03T00:30Z (Hour 0)
Task: 0a Brand Foundation Document (Phase 0 — input verification)
Type: B-with-lingering-doubt
Self-resolved: yes (substituted equivalent inputs)

What I hit:
The instruction set repeatedly cites `docs/rodix-friends-intro.md` (1350-word "friend-version intro" by Rodc) as the canonical voice + positioning input across Tasks 0a, 0b, 0c, 5, 6, 7. This file does NOT exist anywhere in the repo (verified via Glob `**/rodix-friends-intro*`, `**/friends-intro*`, `**/*friends*.md`, `**/*rodix*.md` — only `rodix-brainstorm.md`, `rodix_system.md`, `rodix-roadmap.md`, `rodix-product-test-scenarios.md` exist). Also not in `S:\syncthing\rodix\` or `~/Downloads/`.

What I needed but didn't have:
A canonical Rodc-voice document of his product framing in his own writing. This is the "ground truth" for voice extraction and positioning derivation. Without it, brand-voice-extractor must infer Rodc's voice from secondary sources.

What I did anyway:
I am treating the **composite of these existing docs** as the Tier 0 voice + positioning ground truth (lean conservative — use what is verifiable):

1. `docs/superpowers/specs/2026-05-01-rodix-brainstorm.md` — Rodc's brainstorm session log with locked design decisions ("trust-evoking > wow-evoking", "AI chat with memory not memory app with chat", Raycast warm dark + amber #d97706, IA = top-tabs Chat-default, "克制成熟产品" not "wow-evoking demo"). Has Rodc's own framing.
2. `app/web/prompts/rodix_system.md` v1.3 — Rodix system prompt (the AI's voice the user designed — "thinking partner and memory keeper, not a generic chatbot", forbidden anti-patterns, ban on empty companionship phrases). This IS the operationalized brand voice.
3. `private/APP_STRATEGY_2026-04-29.md` — strategic pivot brief (positioning: "AI memory infrastructure", new product category Notion/Linear/Superhuman tier).
4. `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` — 33 scenarios — reveals target use cases.
5. Wave 1b extraction prompt `app/shared/extraction/prompts/claim_extractor.md` — operational language.

These together cover: positioning, target user inference, AI voice (operational), design tokens, fail modes Rodc explicitly avoids.

Default's downside if wrong:
Brand book derived from system-prompt-voice may bias toward "AI's voice" rather than "Rodc-as-founder voice" — Rodc may read brand-book and think "this is Rodix the product talking, not me the founder." Mitigation in Phase 2 (founder-narrative-arc) by emphasizing Rodc-as-himself voice from brainstorm doc.

What I recommend Rodc + Opus do:
- Rodc: paste the actual `rodix-friends-intro.md` if it exists somewhere (Notion / iCloud / saved drafts). Highly likely 30+ minutes of voice work would be saved.
- Rodc: alternatively, confirm whether the rodix_system.md voice IS the canonical brand voice (i.e. Rodix product = founder voice), in which case my substitute is correct.
- Opus: review brand-book-v1.md voice samples specifically for "is this Rodc or is this Rodix-the-product" contamination.

Severity reasoning:
**High** — the tone could land off. Not ship-blocking (brand book is iterable), but if voice-guide.md sets precedent across all marketing channels and is wrong, Wave 4-5 launch materials cascade-fail brand-coherence checks. Better to flag for Rodc morning verification than silently bet on inference.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #2 — task-0a — high
═══════════════════════════════════════════════════════════

When: 2026-05-03T~02:30Z (Hour ~2)
Task: 0a Brand Foundation Document — §7b crisis-content protocol gap
Type: A (product strategy decision Rodc-only)
Self-resolved: yes (default chosen, escalated for confirmation)

What I hit:
Brand book v2 §7 Decision 5 (refusal of Caregiver register / banned phrases) and §7b commit Rodix to a graceful crisis-content handoff: when users present explicit safety language (self-harm, suicidal ideation, acute crisis), Rodix signals "this is not what I'm built for, here are resources" — never expanding into Caregiver mode and never absorbing the request. The friends-intro positions Rodix for *thinking, not therapy*; this is brand-coherent. **However**: zero implementation today. Grep across `app/web/prompts/rodix_system.md` for `crisis|self-harm|suicide|hotline|emergency|988` returns ZERO matches. Tier 1.5 dogfood Day-15 scenario (Sarah Patel "sometimes I don't see the point of all this") will hit this surface with actual Haiku 4.5 in Phase B sample-verify.

What I needed but didn't have:
Rodc product decision on the crisis-protocol design space:
- Resource scope: 988 (US-only) vs Crisis Text Line vs international resources via geo-detect vs explicit "this isn't a therapy product, please reach out to [generic phrase]"
- Detection trigger: keyword matching ("kill myself" / "don't want to live" / "no point") vs LLM intent classification vs user self-disclosure
- Register on the way out: warm-but-firm vs neutral-procedural vs Anthropic-style matter-of-fact
- Escalation path: just resources vs resources + offer to pause the conversation vs resources + crisis-mode-system-prompt swap

What I did anyway:
- Brand book v2 §7b acknowledges the gap honestly rather than over-claiming
- Added "Wave 1c addition required before Phase 1 alpha launch" as the operational owner
- Default protocol design (lean conservative): Anthropic-style matter-of-fact register + 988 + Crisis Text Line + a 1-sentence "this isn't what Rodix is built for, but please reach out" + don't continue the conversation thread (UI: friendly disable input, warm refresh button). Detection trigger: intent classifier extension (chitchat / thoughtful / confused / closed → ADD `safety` category).
- Tier 1.5 Phase B sample-verify Round 8 (Sarah Day-15) MUST verify whether Wave 1b without crisis protocol fails gracefully or alarmingly — if the latter, this is ship-blocking for Phase 1 alpha.

Default's downside if wrong:
**HIGH.** If Phase 1 alpha launches with no crisis protocol:
- Real users will hit this surface (Sarah Day-15 simulates a real pattern)
- Wave 1b without protocol may either (a) Caregiver-soothe (violates brand) or (b) silently extract a crisis-toned Card (extraction may pull "concern: don't see the point" into Vault — clinical, alarming, potentially traumatic to see in cards-list view next morning)
- Brand book §7 Decision 5 ("Rodix is for thinking, not for engagement") becomes a lie if first crisis user gets Caregiver register
- Liability + reputational + actual user-harm risk

What I recommend Rodc + Opus do:
- **Decide:** is crisis-protocol Wave 1c (P0 ship-blocker, must build before alpha) OR Phase 1 launch-day disclaimer + post-launch Wave 1c (P1 fast-follow)?
- **Approve protocol design:** detection trigger / resource scope / register / escalation path
- **Spec ownership:** Wave 1c crisis-protocol spec — Rodc writes spec, CC implements
- **Tier 1.5 Phase B Round 8 (Sarah Day-15):** if real Haiku 4.5 fails gracefully (Wave 1b system prompt + extraction null-default), Rodc gets to choose timing. If real Haiku 4.5 fails alarmingly, this becomes ship-blocker overnight.

Severity reasoning:
**High.** Not Critical (Phase 1 alpha is small, supervisable, ramped slowly), but high enough that Rodc should not see this as a P2 polish item. Crisis protocol gap is the single brand-vs-product gap most likely to permanently damage Rodix if mishandled. Brand integrity at stake: if first crisis user encounters Caregiver register, the "thinking partner not therapy" positioning is dead.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #12 — task-1.5-phase-B — HIGH (NEW unidentified failure mode)
═══════════════════════════════════════════════════════════

When: 2026-05-03T~10:30Z (Hour ~10.5)
Task: Tier 1.5 Phase B sample-verify — extraction failure mode
Type: A (production-safety + extraction-spec decision Rodc-only)
Self-resolved: yes (default chosen, escalated for confirmation)

What I hit:
Phase B real-API sample-verify revealed TWO previously unidentified extraction failure modes that Wave 1b ships with:

**Failure Mode A — Over-extraction on emotional content (100% rate across 4 of 5 verification rounds).** v3.1's "explicit worry verb" rule does NOT hold under emotional-content pressure. CC predicted ~25% over-extraction risk on Sarah-08 (Day 15); actual rate 100%. Multiple rounds (Sarah Day-15, Mike Round 8 mom situation, Daniel Round 6 grief, Emma Round 8) extracted clinical-toned cards from emotional content where CC predicted null + claim_extractor.md v3.1 80% confidence threshold should have produced null.

**Failure Mode B — Extraction pulls content from AI's reply into user's card (2 of 5 rounds).** Sarah Day-15: `question` field came from AI's reflective question, NOT user message. Daniel Round 6: `hope` field came from AI's "stop optimizing for duration" framing, NOT user message. **This is a brand-existential failure — the user opens Vault and sees fabricated thoughts attributed to themselves. Worst-case trust collapse.**

What I needed but didn't have:
Rodc decision on:
- Wave 1c extraction prompt v3.2 scope: tighten emotional-content null-default + add explicit "extract from USER text only — ignore AI reply text" instruction
- Wave 1c crisis-content protocol Mode A coverage: hard null rule for crisis-tagged messages
- Phase 1 alpha launch timing dependency: Wave 1c ship in same release as Wave 1b (cannot launch Wave 1b alone per Phase B verdict)

What I did anyway:
- Phase B revealed Wave 1c crisis-protocol severity = **HOLD AT HIGH** (not CRITICAL ship-blocker, not downgradable to MEDIUM)
- Required additions to Wave 1c:
  1. Classifier `safety` class (P0)
  2. Hard null rule for crisis-content fields in extraction prompt v3.2
  3. System prompt crisis-resource-raise pattern instruction
  4. Vault rendering safety-flagged-card soft empty state
  5. **NEW:** extraction prompt v3.2 explicit "extract from USER text only" instruction (Failure Mode B mitigation)
- Phase 1 alpha launch: must ship Wave 1c alongside Wave 1b. Cannot launch Wave 1b alone.

Default's downside if wrong:
**HIGH.** If Wave 1b ships without v3.2 extraction fix:
- 100% over-extraction on emotional content → Vault fills with clinical-toned cards user perceives as misrepresentation → trust collapse
- AI-reply content attributed to user → user opens Vault, sees thoughts they didn't have → trust collapse, possibly more severe than over-extraction
- Brand book §7 Decision 1 (white-box transparency) violated structurally
- friends-intro line 218 promise ("Every meaningful exchange becomes one structured card with four fields... You can read every card... see exactly which conversation produced it") — if card content is fabricated from AI reply, "exactly which conversation" is meaningless

What I recommend Rodc + Opus do:
- Read Phase B `calibration-report.md` + `sarah-day-15-real-api-verdict.md` + 5 round verification files
- Approve Wave 1c v3.2 extraction prompt scope (5 additions above)
- Lock Phase 1 alpha launch dependency: Wave 1b + Wave 1c ship together
- Decide Wave 1c implementation timing (1-2 weeks for spec → implementation → eval-set re-validation)

Severity reasoning:
**HIGH.** Brand-existential failure mode. Not Critical (Phase 1 alpha small enough to absorb if caught fast post-launch via telemetry) but high enough that pre-launch fix is required. Phase B verification was specifically designed to surface these — design point achieved.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #9 — task-2 — high
═══════════════════════════════════════════════════════════

When: 2026-05-03T~08:00Z (Hour ~7.5)
Task: 2 Wave 3 Plan — LLC jurisdiction + ownership-record posture
Type: A (legal-strategy decision Rodc-only)
Self-resolved: yes (no default; this is Rodc-binding)

What I hit:
Wave 3 dispatch is gated on US LLC formation. friends-intro Status section says "solo, anonymous, working out of Asia" — anonymity is a brand asset (uncopyable per §8). LLC formation creates public ownership record:
- **Wyoming LLC** (~$300/yr) has shielded member listing — preserves anonymity
- **Delaware LLC** does NOT shield — public records expose owner name
- **Holding-entity layer** ($800-1000/yr) — Wyoming or BVI holding owns Delaware operating entity
Without LLC formed, no Paddle Merchant of Record, no MoR = no paid launch. Wave 3 #b-paddle spec critical-path-blocker.

What I needed but didn't have:
Rodc decision on:
- Jurisdiction: Wyoming (anonymity) vs Delaware (standard tech) vs holding-entity layer (most expensive, most protective)
- Public-record acceptance: is Rodc willing to be doxxed via public LLC records, OR is anonymity a sustained brand asset?

What I did anyway:
Wave 3 plan + spec-b-auth + spec-b-paddle reference "TBD per Rodc Tier 1 escalation #9". Default recommendation: **Wyoming LLC ~$300/yr** (preserves brand-asset anonymity at lowest cost).

Default's downside if wrong:
**HIGH.** Wrong jurisdiction = 6-8 week setback to re-form. Wrong anonymity-vs-public posture = brand identity / trust narrative shifts.

What I recommend Rodc + Opus do:
- Decide jurisdiction (default: Wyoming for anonymity preservation)
- Decide public-record acceptance (default: anonymity preserved → Wyoming)
- Initiate Stripe Atlas or specialized LLC-formation service this week (Critical path = 2-4 weeks)
- Coordinate with Tier 2 Task 8 Privacy Policy "Who we are" section TODO

Severity reasoning:
**High.** Wave 3 paid-launch ship-blocker. Critical path 6-8 weeks (LLC formation + Paddle approval). Cannot hold for too long.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #10 — task-4 — high
═══════════════════════════════════════════════════════════

When: 2026-05-03T~08:00Z (Hour ~7.5)
Task: 4 Pricing Deep Dive — LLM unit economics + Wave 2 caching dependency
Type: A (financial assumption Rodc-only)
Self-resolved: yes (default chosen, escalated for confirmation)

What I hit:
**Critical pricing correction:** my Task 4 prompt cited Haiku 4.5 at $0.25 / $1.25 per M tokens (legacy Haiku 3.5 rates). pricing-strategist subagent verified actual OpenRouter rates: **$1 / $5 per M tokens (4× higher than my prompt)**.

Implications at recommended $10/mo:
- Light user (20% of mix): 70% gross margin
- Medium user (60% of mix): 28% gross margin
- Heavy user (20% of mix): **-77% gross margin** (loss-leader at $10/mo)
- Blended margin: ~16% at base mix

The pricing strategy assumes Wave 2 prompt-caching ships within 60-90 days post-launch. Without caching, blended LLM cost is ~$15.18/mo vs $10/mo revenue — every plan below $20 loses money.

What I needed but didn't have:
Rodc decision on:
- Pricing: $10 (recommended) vs $8 (more accessible / GM-fragile) vs $12 (engineering-schedule cushion)
- Wave 2 caching schedule: confirm 60-90 day implementation OR delay paid launch until caching ships
- Heavy user policy: accept loss-leader at $10/mo OR introduce usage cap / metered overage / power-tier $25 with cap

What I did anyway:
- Recommended $10/mo + $100/yr (17% annual) + $8/mo founder pricing first 100 alpha
- Added Wave 2 caching assumption as load-bearing (Wave 2 plan v1.1 reflects)
- Heavy user mitigation: per-user cost-cap from Tier 3 Task 13 observability (50k input + 25k output / day)

Default's downside if wrong:
**HIGH if caching slips.** If Wave 2 prompt-caching does NOT ship within 60-90 days post-launch, every paying user costs $15+ in LLM = at $10/mo, runaway losses at scale. Mitigation: signup cap + classifier tightening + honest "alpha is at-cost" communication.

What I recommend Rodc + Opus do:
- Confirm Wave 2 caching is scoped + scheduled within 60-90 days post-launch
- Lock final $ amount: $10 (default) / $8 / $12
- Approve heavy-user policy: loss-leader OR usage cap
- Decide free trial vs free tier (recommend 14-day trial — Decision 7 forecloses on AI-credit metering free tiers)

Severity reasoning:
**High.** Phase 1 alpha viability + Wave 3 SaaS launch unit economics depend on this. Caching dependency is the load-bearing-but-hidden financial assumption.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #11 — task-2 — medium
═══════════════════════════════════════════════════════════

When: 2026-05-03T~08:00Z (Hour ~7.5)
Task: 2 Wave 3 Plan — encryption marketing copy anti-spin lock
Type: A (brand-discipline lock decision Rodc-only)
Self-resolved: yes (default chosen, escalated for confirmation)

What I hit:
spec-b-encryption + Privacy Policy + marketing copy must use phrase **"encryption at rest, recall server-trusted"** consistently. NEVER use "end-to-end encrypted" or "zero-knowledge" — per brand book §7 Decision 6 anti-spin operationalization of friends-intro line 353-355 ("we can't promise zero-knowledge — that would be a lie given the architecture").

What I did anyway:
Wave 3 plan + Tier 2 Privacy Policy draft + Marketing Suite all reference this lock. Anti-spin discipline operationalized.

Default's downside if wrong:
**Medium.** Wrong copy = brand-promise inversion (claim what isn't true) = liability + credibility loss. Caught early in Tier 0 brand book; reinforced by Wave 3 + Privacy + Marketing.

What I recommend Rodc + Opus do:
- Confirm "encryption at rest, recall server-trusted" is canonical
- Veto any future copy that drifts to "end-to-end encrypted" or "zero-knowledge"

Severity reasoning:
**Medium.** Brand-discipline lock; no operational gap as long as discipline holds. Worth flagging as standing escalation for Wave 4 marketing surface review.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #7 — task-1 — medium
═══════════════════════════════════════════════════════════

When: 2026-05-03T~07:30Z (Hour ~7)
Task: 1 Wave 2 Plan — telemetry-readiness for alpha-cohort signal capture
Type: A (engineering-product-strategy decision Rodc-only)
Self-resolved: yes (default flagged, escalated for confirmation)

What I hit:
Wave 2 plan + 3 of 5 specs cite production telemetry triggers as part of asymmetric gates:
- `spec-active-recall-base`: "production calibration trigger if recall < 50% sustained for 3 days"
- `spec-card-dedup`: "false_dedup_rate ≤ 5% via 7-day rolling window"
- `spec-vault-recall-history`: "creep-language >5% in support tickets"
- `spec-first-insight`: "≥ 70% useful-marked"

Plan does not specify how the telemetry is captured. There is no support-ticket pipeline architected. There is no rolling-window aggregation pipeline. The metrics are aspirational unless infrastructure exists.

What I needed but didn't have:
Rodc decision on telemetry timing:
- Option A: telemetry pipeline ships AS PART OF Wave 2 (adds 1-2 days; calibration triggers become real)
- Option B: telemetry pipeline becomes Wave 2.1 work (calibration triggers are aspirational at Wave 2 launch; Phase 1 alpha runs without rolling-window aggregation)
- Option C: telemetry pipeline is Wave 3 SaaS upgrade (Phase 1 alpha = manual log-grep + Rodc-direct-feedback only)

What I did anyway:
Wave 2 plan v1.1 cites telemetry triggers without specifying capture mechanism. This is the gap.

Default's downside if wrong:
**Medium.** If Rodc dispatches Wave 2 expecting telemetry-driven calibration, but no pipeline exists, calibration triggers fire on hand-counted samples (poor signal). Phase 1 alpha may run without recall-precision-drift detection until manual review catches it.

What I recommend Rodc + Opus do:
- Decide A / B / C above
- If B: explicitly mark calibration triggers as "Wave 2.1 capture / Wave 2 placeholder" in plan; preserve trigger logic but acknowledge gap
- If C: scope Phase 1 alpha to ≤ 1000 users where manual review is feasible

Severity reasoning:
**Medium.** Strategic-engineering decision, reversible. Default A is rigorous-but-slower; default B is fastest but creates aspirational gates; default C honest about Phase-1 scale.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #8 — task-1 — medium
═══════════════════════════════════════════════════════════

When: 2026-05-03T~07:30Z (Hour ~7)
Task: 1 Wave 2 Plan — first-cohort-first-impression copy-lock risk
Type: A (brand-experimentation strategy Rodc-only)
Self-resolved: yes (default chosen, escalated for confirmation)

What I hit:
Two brand-defining strings ship in Wave 2 first cohort:
1. `⚡ 我把这个带回来了` / `⚡ I brought this back` (active-recall-base recall callout — brainstorm 2026-05-01 P1 lock)
2. **Variant C reflection format** (first-insight — locked per spec): "Three cards from the past week: [t1], [t2], [t3]. Reading them back-to-back, [observation]."

Both are FIRST IMPRESSIONS. Once the alpha cohort sees them on first occurrence, they cannot be re-seen for the first time. If Tier 1.5 Round 11 (Mike Day 24+) reveals "callout feels meta" or "Variant C feels curated," reverting via env-var preserves the cohort that saw the wrong version perceiving it as the wrong version.

What I needed but didn't have:
Rodc decision on copy-lock confidence path:
- Option A: ship as locked. Tier 1.5 Round 11 + Phase B verification + alpha telemetry catch issues; if issues found, fast-follow patch + accept first-cohort residual perception
- Option B: pre-launch friend-dogfood week (3-5 friends, 5-7 days) before Phase 1 alpha launch. Cost: 5-7 day delay. Benefit: validation surface beyond Tier 1.5 simulation
- Option C: ship with two A/B variants (50/50 split) and choose based on production telemetry. Cost: more implementation complexity + measurement infrastructure required (see Escalation #7)

What I did anyway:
Wave 2 plan defaults to Option A. Tier 1.5 Round 11 + Phase B sample-verify Sarah Day-15 are the validation surfaces. If signals come back negative, Wave 2.1 emergency patch.

Default's downside if wrong:
**Medium.** Worst case: alpha cohort perceives "Rodix's recall callout is performative / meta" — brand promise inversion. Recovery: fast-follow patch within 7 days, accept that cohort users < 50 saw the wrong version. Brand integrity loss is local + recoverable but not zero.

What I recommend Rodc + Opus do:
- Pick A / B / C
- If B: schedule 5-7 day pre-launch friend-dogfood window with ≥ 3 testers. Friend testers should match brand-book §3 target (life-decision thinker, heavy AI user); recruit-strategy.md is input.
- If A or C: confirm Tier 1.5 Round 11 is the gate; Sarah Day-15 Phase B is the production-safety gate; both must pass before alpha.

Severity reasoning:
**Medium.** Brand-defining first impressions are higher-stakes than typical iteration, but Phase 1 alpha is small (≤ 1000 users / 30 days) so first-cohort exposure is bounded. Reversible at modest cost.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #5 — task-0c — medium
═══════════════════════════════════════════════════════════

When: 2026-05-03T~05:00Z (Hour ~4.5)
Task: 0c User Research Synthesis — interview confirmation threshold
Type: A (validation rigor decision Rodc-only)
Self-resolved: yes (default chosen, escalated for confirmation)

What I hit:
launch-readiness-auditor proposed 5 launch-readiness criteria. Criterion 2: "≥ 3 of 5 user interviews confirm assumption S1 (Heavy AI users feel re-explanation soul-tax) unprompted with concrete tool/topic/moment examples." The 3-of-5 threshold is auditor's middle-ground default. Alternatives:
- Stricter: 4-of-5 (one fail tolerance) — high confidence, but raises bar to "alpha can't launch unless 80% of pre-launch interviews confirm"
- Looser: 2-of-5 (50% confirm = sufficient signal) — lower bar, but risks confirmation-bias-acceptance of weak signal
- Mom-test rigor reading: 3-of-5 with **unprompted concrete examples** is functionally equivalent to 4-of-5 with prompting allowed. 3-of-5 is the middle.

What I needed but didn't have:
Rodc's preferred validation rigor. This is risk-tolerance + research-philosophy decision. Both 3-of-5 and 4-of-5 are defensible.

What I did anyway:
launch-readiness-criteria.md uses 3-of-5 as default. Mom-test discipline (unprompted, concrete examples) is the load-bearing rigor.

Default's downside if wrong:
**Medium.** If 3-of-5 is too loose, Phase 1 alpha launches with weak signal and risks discovering S1 unvalidates after 14 days of alpha (most-expensive-failure-path per launch-readiness-criteria.md §5: 30-60 days misdirected iteration, ~300 users acquired under wrong positioning, ~$36k-180k opportunity cost). If 4-of-5 is too strict, Phase 1 alpha may delay 2-4 weeks waiting for the 4th confirming interview while signal is already actionable.

What I recommend Rodc + Opus do:
- Read launch-readiness-criteria.md §2 (Criterion 2 detail)
- Decide: 3-of-5 (default) vs 4-of-5 (stricter)
- Lock before first interview begins (so post-hoc threshold-shifting isn't possible)

Severity reasoning:
**Medium.** Strategic but reversible if caught early. Wrong choice has measurable cost but doesn't destroy Rodix.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #6 — task-0c — low
═══════════════════════════════════════════════════════════

When: 2026-05-03T~05:00Z (Hour ~4.5)
Task: 0c User Research Synthesis — recruit-strategy founder-network bias
Type: B (informational; no Rodc action required, but worth knowing)
Self-resolved: yes

What I hit:
user-research-strategist honestly noted: "if Rodc's warm-intro list skews indie-builder / AI-engineer (which it likely does), the candidates will skew toward fail-mode-2 territory (heavy AI use for code/writing/research, not life-decision thinking-partner work)." The 5-interview cohort may not represent Rodix's stated target user.

What I did anyway:
recruit-strategy.md flags this as known limitation + recommends Wave 2 plan should explicitly note "founder-network bias confirmed during recruit, alpha telemetry needed to test life-decision-thinker segment."

Default's downside if wrong:
**Low.** Worst case: 5 founder-network candidates confirm code/writing thinker fit but don't represent the friends-intro target user (life-decision thinking partner). Phase 1 alpha then surfaces a real signal mismatch if life-decision thinkers don't acquire. Mitigation already in place — alpha telemetry is the second validation surface.

What I recommend Rodc + Opus do:
- Acknowledge founder-network bias risk explicitly
- Don't over-correct by sourcing 5 candidates from far outside Rodc's network (decreases interview quality + delays)
- Add to Wave 2 plan acceptance criteria: "alpha cohort first-30-day telemetry confirms life-decision thinker engagement (not just code/writing thinker engagement)"

Severity reasoning:
**Low.** Informational. The cure (broaden recruit) may be worse than the disease (founder-network bias) given solo-anonymous-founder reach constraints.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #4 — task-0b — low
═══════════════════════════════════════════════════════════

When: 2026-05-03T~04:00Z (Hour ~3.5)
Task: 0b Founder Narrative Arc — verify Part 1 "rough notes on the side" claim
Type: A (factual fidelity Rodc-only)
Self-resolved: yes (default = keep, escalated for verification)

What I hit:
Founder narrative arc Part 1 P3 contains the sentence:
> *"I started keeping rough notes on the side, but the notes were always a worse version of what we'd already worked out together."*

This sentence does NOT appear in `rodix-friends-intro.md` (verified via Grep — zero matches for "rough notes" or "notes on the side"). It is arc-original content extending the heavy-user persona. The architect flagged it during draft; the skeptic confirmed it is fabrication-adjacent (defensible-sounding but not source-grounded). It is on-voice (specific, refuses-to-dramatize, parenthetical-adjacent), but it claims a behavior — Rodc keeping side notes — that may or may not be true.

What I needed but didn't have:
Rodc's actual experience: did you keep side notes during your heavy-AI-user year? If yes — keep. If no, or only loosely — cut. Cost of fabrication: brand-trust on founder essay.

What I did anyway:
KEPT the sentence in v1.1, with this escalation flagged for Rodc verification. The voice-guide §1 anti-spin principle prefers "volunteer limits" over "embellish for color." But the sentence is small enough that ad-hoc keeping is acceptable until Rodc verifies. If Rodc cuts it, paragraph re-flow is trivial (1-line removal).

Default's downside if wrong:
**LOW.** Worst case: Rodc reads founder essay, recognizes the rough-notes sentence as not-his-experience, asks for cut. Cost: 1 minute removal. The arc still works without the sentence.

What I recommend Rodc + Opus do:
- Rodc: read Part 1 P3. Decide keep / cut.
- If kept: lock for Wave 4 marketing suite.
- If cut: flag in `decisions.md` + iterate arc once via direct Edit.

Severity reasoning:
**Low.** Single-sentence factual fidelity issue. Voice integrity > one good line. The line is small, defensible, but not load-bearing. Skeptic and architect both flagged conservatively. Resolves in one Rodc read-through.

═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
ESCALATION #3 — task-0a — medium
═══════════════════════════════════════════════════════════

When: 2026-05-03T~02:30Z (Hour ~2)
Task: 0a Brand Foundation — defensibility frame leadership
Type: A (positioning strategic decision Rodc-only)
Self-resolved: yes (default chosen, escalated for confirmation before Task 0b commits)

What I hit:
Position-strategy v2 frames Rodix's defensibility ("moat") in this priority order:

1. **Foreground:** Architectural commitments competitors' business models contradict (cross-model dissolves frontier-vendor LTV; white-box cards contradict opaque-memory UX; markdown export lowers switching costs; active recall calibrated for trust contradicts engagement-minute metrics).
2. **Behind:** Execution discipline + founder narrative + small-cohort word-of-mouth retention.

v1 (brainstorm-based) inverted this order: founder + community + discipline foreground; architectural commitment behind.

The friends-intro reading guide implies v2 ordering is correct — the 4 specific bets ARE the position, with founder/discipline as supporting. But this is a Rodc-strategy decision because it determines:
- How the founder essay (Task 0b) opens — "I built Rodix because I noticed two things while using AI heavily" (founder-lead) vs "Memory features ship as black-box tags by design — Rodix is the opposite of all four" (architecture-lead).
- How the landing page hero is structured — founder photo + name vs. mechanism diagram + 4 bets.
- How HN post (Task 6) is framed — founder story → product → architecture vs. architecture → demo → indie founder.

What I needed but didn't have:
Rodc's strategic preference. Both work; they emphasize different defensibility narratives. Architectural-lead (v2) is what the friends-intro evidence supports. Founder-lead (v1) is what most indie SaaS launches do.

What I did anyway:
v2 brand book §8 leads with architectural-commitments-as-foreground-moat. Founder discipline is preserved as the supporting layer. This is the v2 default.

Default's downside if wrong:
**Medium.** Wrong choice means Task 0b founder essay opens with the wrong frame and either (a) re-writes from the friends-intro "I noticed two things" opener (founder-lead) or (b) re-writes from "Every AI you use kinda remembers you now. They all share the same broken design." (architecture-lead). Either rewrite is feasible if caught before Task 6 marketing suite. Cost: 1-2h Task 0b iteration if Rodc inverts.

What I recommend Rodc + Opus do:
- Read brand book §8 + position-strategy v2 §2 + friends-intro body opening passage
- Pick: architecture-lead vs founder-lead for Task 0b founder essay opening
- Confirm before Task 0b dispatches (or before Task 0b iteration round 2 if dispatched first)

Severity reasoning:
**Medium.** Strategic decision, but reversible until Task 6 marketing suite hardens. Rodc's intuition + Opus stress-test should converge fast.

═══════════════════════════════════════════════════════════
