# Tier 0 Handoff — 2026-05-03

**Tier 0 status:** COMPLETE (Hour ~5 of 30-hour shift)
**Tasks completed:** 0a (Brand Foundation Document) / 0b (Founder Narrative Arc) / 0c (User Research Synthesis)
**Author:** CC (autonomous shift)
**Audience:** Rodc + External Opus, morning review

---

## 1. Completion summary

| Task | Status | Self-grade | Hours actual / spec | Files |
|---|---|---|---|---|
| 0a Brand Foundation | DONE (v1 + v2 re-run after Rodc located rodix-friends-intro.md) | A- | 2.5 / 1.5-2 | research-notes / archetype-analysis / voice-guide / position-strategy / brand-book-v1 / review-notes / decisions / 5 brainstorm-based archives |
| 0b Founder Narrative Arc | DONE | A- | 1 / 0.75-1 | narrative-research / founder-narrative-arc-draft / narrative-skeptic-notes / founder-narrative-arc (master v1.1) |
| 0c User Research Synthesis | DONE | A- | 1 / 0.75-1 | assumption-list (47 assumptions) / user-interview-script / recruit-strategy / mom-test-checklist / launch-readiness-criteria |

Tier 0 budget was 3-4h. Actual: ~4.5h, slightly over due to v1+v2 re-run on Task 0a after Rodc located the canonical voice doc mid-shift. The re-run was correct (v1 had concluded Sage primary on partial inputs; v2 reaches Explorer primary on canonical inputs) — but cost ~1h over budget. Acceptable.

Tier 0 deliverables are the foundation for all subsequent tiers. No subsequent task should re-derive brand voice, target user, or positioning — read Tier 0 outputs.

---

## 2. Type-B engineering decisions (with reasoning chains, not just conclusions)

These are decisions made within established product direction. Rodc may revisit any.

### Decision T0-1 — Archive-then-rebuild on primary-input correction

**Decision:** When `rodix-friends-intro.md` was located mid-shift (after Phase 1-5 v1 complete), CC archived v1 outputs as `*-brainstorm-based.md` and re-ran Phase 3-5 with friends-intro as canonical primary input.

**Reasoning chain:**
1. v1 outputs were grounded in (brainstorm + system-prompt + APP_STRATEGY_2026-04-29) — partial input set.
2. v1 reached different verdicts than v2 would: v1 archetype = Sage primary (read in-product AI mechanics as if they were brand archetype); v1 voice = "Specific. Restrained. Capable-treating." (inferred from enforcement layer); v1 pitch = "thinking not engagement" (CC inference).
3. Hand-merging v1 + v2 outputs would paper over contradictions rather than resolve them.
4. v2 re-run with friends-intro produces verdicts that survive the friends-intro reading-guide test (which explicitly rejects Sage as "too clean").
5. Archive ensures audit trail without diff-merge friction.
6. Cost: ~1h re-run; benefit: brand book grounded in canonical voice, subsequent tasks (founder essay / marketing) inherit correct voice.

**Confidence:** HIGH that re-run was correct path. MEDIUM-HIGH that v2 outputs are durable — Rodc voice verification is the next test.

### Decision T0-2 — Two-layer archetype model (brand-Explorer + AI-Sage-flavored)

**Decision:** Brand book §4 documents two archetypes simultaneously: brand-archetype = Explorer (primary) + Everyman (color); in-product AI character = Sage-flavored Socratic (per `rodix_system.md` v1.3 Round 1/2/3+ phasing). Routing rule for transitional surfaces: default Explorer unless surface speaks *as the AI character*.

**Reasoning chain:**
1. v1 collapse: read in-product mechanics (claim_extractor null-default, system prompt Round 3+ stop-asking) as if those were the *brand* archetype. They are the AI *character's* archetype within the product — different layer.
2. The brand archetype operates at "Rodc presenting Rodix to the world" layer. friends-intro voice (sovereignty / mis-categorization / decisions-as-paths) is unmistakably Explorer.
3. The in-product AI voice is correctly Sage-flavored (Socratic, restraint, reflection). Forcing AI to behave Explorer-y in chat (anti-Socratic, broke Round-3 stop-asking) would break the product.
4. Rather than pick one and erase the other, document two layers explicitly + provide routing rule for transitional surfaces (onboarding / error states / recall callouts).
5. Skeptic Q6 partial-pass on v1 of the routing rule → CC added explicit routing-rule paragraph in §4 (transitional surfaces default Explorer; AI character speaks Sage).

**Confidence:** HIGH on the two-layer model itself (intellectually correct). MEDIUM on the routing rule for unusual surface combinations (e.g., chat error message that quotes the AI character — does that surface inherit Explorer or Sage?). Rodc can refine.

### Decision T0-3 — Skeptic-then-iterator subagent pair (for v1 Task 0a) vs CC-direct-Edit (for v2 Task 0a + Task 0b)

**Decision:** v1 Task 0a used skeptic + iterator subagent pair. v2 Task 0a + Task 0b used skeptic + CC-direct-Edit (skipped iterator subagent because edit batch was ≤ 5 small surgical edits).

**Reasoning chain:**
1. Subagent dispatch overhead: ~300 token prompt setup + ~3-5 min latency.
2. Subagent benefit: fresh-context judgment, useful when edits require re-think (not mechanical replace).
3. Threshold (preliminary, refined during shift): if edit batch ≤ 5 small surgical edits with clear verbatim-replace instructions → CC direct (faster, no divergence). If > 5 edits OR any edit requires re-think → iterator subagent.
4. Task 0a v1 had 4 reality-gap issues found by skeptic; iterator subagent was overkill in retrospect.
5. Task 0a v2 had 2-3 small edits (button labels, routing rule) → CC direct.
6. Task 0b had 4-5 small edits → CC direct.

**Confidence:** MEDIUM on the threshold (≤ 5 edits). Will refine across Tier 1+ data.

### Decision T0-4 — Verbatim-quote-or-Grep mandate as standard subagent guardrail

**Decision:** All Tier 0 v2 subagent prompts mandated "cite friends-intro VERBATIM" + "use Bash/Grep to verify factual claims about Wave 1b code."

**Reasoning chain:**
1. v1 Task 0a had a fabricated 0.75 threshold that survived 5 levels of subagent review (3 brand subagents + integrator + skeptic) before final iterator caught it via Grep.
2. The structural failure: each subagent inferred from prior subagent's output. Inference compounds.
3. Verbatim-quote-or-Grep mandate forces ground-truth-or-explicit-quote at every subagent boundary.
4. v2 outputs verified clean: real recall thresholds (0.50 / 0.60 / 0.65 / 0.70) cited from `app/shared/recall/orchestrator.py`, recall callout placeholder verified in `app/web/static/app.js` line 580+627, crisis-protocol absence verified via Grep returning zero matches.
5. Skeptic Q4 specifically tests Wave-1b-reality-vs-aspirational claims; v2 passed (vs v1 fail).

**Confidence:** HIGH. Should become standard subagent guardrail across all tiers. Logged in `reusable-patterns.md`.

### Decision T0-5 — Forced ranking in extraction-style subagent outputs

**Decision:** assumption-extractor (Task 0c) was required to produce 35-55 items AND Top 5 foundational + Top 2 contradictions (forced K-rank subset).

**Reasoning chain:**
1. Flat list of 47 assumptions is hard for downstream subagents to act on.
2. Forced ranking creates a stable "where to focus" subset.
3. Wave 2 plan / Pricing / Marketing each pull from Top 5 + Top 2, not full list.
4. Cost: 5% more tokens to produce ranking; benefit: dramatic downstream usability.
5. Pattern generalizes — any "extract N items" subagent should be required to produce Top-K subset.

**Confidence:** HIGH. Logged in `reusable-patterns.md`.

### Decision T0-6 — Substitute composite docs as "rodix-friends-intro" before Rodc located the actual file

**Decision:** v1 Phase 3 ran with composite of (brainstorm + system-prompt + APP_STRATEGY + product-test-scenarios + claim-extractor) as substitute for the missing rodix-friends-intro.md.

**Reasoning chain:**
1. Instructions cited `docs/rodix-friends-intro.md` as primary input but file did not exist (Glob verified).
2. Two options: (a) escalate as critical and wait, (b) substitute composite docs and continue with high-severity escalation flagged.
3. Chose (b) — Rodc was asleep (per instructions, no mid-shift consult). Holding 5 hours of work pending file location was higher cost than re-running on canonical input later.
4. Escalation #1 logged + downgraded to "resolved" once Rodc located file.
5. v1 outputs preserved as audit trail for the substitute-was-wrong-vs-right comparison.

**Confidence:** HIGH that substitute decision was correct. The re-run preserved value of v1 work as comparison data + de-risk for the "what if Rodc never finds friends-intro" branch.

### Decision T0-7 — Defensibility frame defaults to architecture-lead (Escalation #3)

**Decision:** Brand book §8 + position-strategy v2 §6-8 + founder narrative arc v1.1 Part 2 lead with "architectural commitments competitors' business models contradict" as the foreground moat. Founder narrative + execution discipline + community as supporting layer.

**Reasoning chain:**
1. v1 inverted this ordering (founder + community + discipline foreground; architecture behind).
2. friends-intro reading guide implies architecture-lead: "Each is a specific architectural commitment that competitors cannot casually adopt because it contradicts their business model."
3. Architecture-lead survives 2031 commodity-AI scenario better — vendor incentives don't change just because LLMs commoditize.
4. Founder-lead is what most indie SaaS launches do, but Rodc's anonymity makes founder-lead a weaker brand asset (vs. funded competitors with named-founder brands).
5. Both work; v2 default is architecture-lead per Rodc-evidence (friends-intro framing).
6. Escalated to Rodc as #3 (medium severity) — Rodc may invert.

**Confidence:** MEDIUM-HIGH. Rodc may have stronger founder-narrative instincts than friends-intro suggests.

### Decision T0-8 — §7b "Brand commitments pending Wave 2 / 1c implementation" subsection (honor reality gap)

**Decision:** Brand book §7b explicitly names 3 brand commitments NOT yet operational: ⚡ recall callout copy (Wave 2 deliverable), crisis-content protocol (Wave 1c P0), per-user encryption (Wave 3 SaaS upgrade).

**Reasoning chain:**
1. v1 brand book §7 conflated brand commitments with operational reality. Skeptic Q4 fail: brand book over-claimed shipped behavior.
2. Anti-spin voice principle (per voice-guide §1) requires the brand to volunteer limitations. The brand book itself must follow this principle.
3. Splitting §7 (operational today) + §7b (commitments pending) makes the gap honest.
4. §7b frames pending items as "Wave X deliverable / commitment stands" — preserves brand intent without over-claiming reality.
5. Preempts the failure mode where Phase 1 marketing copy claims behaviors Phase 1 alpha doesn't ship.

**Confidence:** HIGH. The split is structurally correct; marginal risk Rodc thinks §7b should be even more aggressive about reality-gap (e.g., bullet on "Phase 1 server-side recall is not zero-knowledge" repeated in main §7 not just §7b).

---

## 3. Confidence-flagged items for Rodc + Opus review

These are NOT escalations (those are in `escalations.md`) but items where CC's confidence is qualified.

| Item | CC Confidence | Why qualified | Recommended Rodc / Opus action |
|---|---|---|---|
| Brand archetype Explorer + Everyman secondary | HIGH on Explorer, MEDIUM on Everyman | Everyman color is supported by friends-intro's "solo, anonymous, working out of Asia" indie posture, but could also read as anti-elite-Rebel-shading. Subtle. | Read brand-book §4. Confirm color, or veto Everyman → propose alternative. |
| Voice 3 adjectives "Specific. Anti-spin. Refuses-to-dramatize." | HIGH | Friends-intro evidence converges hard. v2 skeptic 6/1/0 verdict supports. | Read voice-guide §1 + §4. Validate the 3 adjectives. Veto if any feels off. |
| Pitch precedence (8-word friends-intro pitch over 22-word v1 pitch) | HIGH | Friends-intro author wrote and tagged as canonical ("That's the whole thing"). | None — confirmed correct unless Rodc disagrees. |
| Two-layer archetype model | HIGH on intellectual correctness, MEDIUM on operational clarity | Routing rule for transitional surfaces is novel; untested across Tier 2 deliverables. May need refinement when Wave 4 marketing video script is written. | Read brand-book §4. Test mentally: would the routing rule hold for "vault empty state hint" / "extraction failure error message" / "support email reply quoting AI dialog"? |
| Defensibility frame architecture-lead default | MEDIUM-HIGH | Per friends-intro evidence, but Rodc may have stronger founder-narrative instincts. | Resolve Escalation #3 before Task 6 marketing suite hardens. |
| Founder narrative arc Part 1 P3 "rough notes on the side" sentence | LOW | Not in friends-intro. Architect inferred. Skeptic confirmed fabrication-adjacent. | Resolve Escalation #4 — verify with Rodc's actual experience. |
| Crisis-content protocol gap | HIGH on the gap exists, MEDIUM-HIGH on it being P0 ship-blocker | §7b acknowledges but does not implement. Tier 1.5 Phase B Sarah Day-15 will reveal severity (graceful-fail vs alarming-fail). | Resolve Escalation #2 before Phase 1 alpha. |
| Interview confirmation threshold (3-of-5 default) | MEDIUM | Reasonable middle, but rigor-vs-speed is a judgment call. | Resolve Escalation #5 before first interview. |
| Founder-network bias in recruit | MEDIUM (acknowledged) | Rodc's reach skews indie-builder; may not surface life-decision-thinker segment. | See Escalation #6 — informational, no immediate action. |
| 47 assumption distribution (4 Validated / 18 Strong / 19 Weak / 6 Contradicted) | HIGH on category-line strictness, MEDIUM on completeness | Some assumptions may have been missed; 47 is exhaustive within the 6-doc scope but not exhaustive of Phase 1 launch knowledge. | None — re-run if Rodc thinks specific category undercounted. |
| Brand book v2 length (7233 words vs target 4000-5500) | MEDIUM (aware over-target) | Length partly inflated by required verbatim friends-intro quoting + reconciliation log + changelog. Trimmable post-hoc by 25-30%. | Optional post-Tier-0 trim if Rodc prefers tight master doc. |

---

## 4. Pre-compaction snapshot — active context not yet in files

These are reasoning chains and observations CC holds in working memory that are NOT yet captured in any output file. If context compresses before subsequent tier work begins, these may be lost.

### 4.1 Active reasoning about brand book overlap with Wave 2 specs

The brand book §7 Decision 5 ("refusal of Caregiver register") + §7b crisis-content protocol gap + claim_extractor.md null-default discipline + rodix_system.md banned-phrase list **collectively** define a system-prompt-modification scope for Wave 1c. Specifically:

1. Add a `safety` intent category to intent classifier (currently: chitchat / thoughtful / confused / closed)
2. Add crisis-detection routing in chat path: if intent = safety, replace standard system prompt with crisis-aware variant
3. Crisis-aware variant: refuses to extract a card, refuses to engage the conversation thread, signals "this is not what Rodix is built for" + 988 + Crisis Text Line
4. Banned-phrase list expansion: add the English equivalents brand-book v2 §5 surfaced ("I hear you" / "I get it" / "That sounds really hard" / "Let's unpack this together" / "I'm listening" / "You're not alone")

This Wave 1c spec is implicit across Tier 0 deliverables but not formalized. Should be Wave 2 plan input or separate Wave 1c spec ticket.

### 4.2 Active reasoning about Tier 1.5 dogfood sample-verify economics

Tier 1.5 spec says Phase B sample-verify costs $0.50-1.00 for 5 rounds. With the pivot away from the brainstorm-based brand outputs (Tier 0 v1) toward friends-intro-grounded outputs (v2), sample-verify priorities shift:

1. **Sarah Round 8 (Day 15)** — D1 verification — locked
2. **Active recall round** — cycle-validation — locked, but spec may shift if Wave 2 plan adjusts threshold
3. **LOW-confidence round** — depends on Phase A
4. **HIGH-confidence sanity check** — Mike Round 1 likely (lowest emotional risk, easiest reality-check)
5. **Persona-specific edge case** — Emma Round 7 (literary voice test) preferred over Daniel Round 8 (first-insight surface) — Emma's voice is harder for self-simulation to nail than Daniel's substantive opening

Cost projection: $0.50-1.00 holds for 5 rounds × ~2-3 messages average × Haiku 4.5 input/output. Should refresh Tier 1.5 cost-log.md once Phase A starts.

### 4.3 Active reasoning about Tier 1 Wave 2 plan dependency on Tier 0 outputs

When dispatching Tier 1 Task 1 (Wave 2 plan with 5 spec writers in parallel), each spec must reference Tier 0 outputs:

- spec-card-real → brand-book §6 visual identity (amber + Inter font + dark-mode-default) + voice-guide §5 sample passages for card-component microcopy
- spec-active-recall-base → §7b ⚡ recall callout copy (locked from brainstorm 2026-05-01) + voice-guide on recall-event AI behavior + assumption-list precision-asymmetric-gate
- spec-first-insight (#2b) → assumption-list S15 (continuity-of-thought distinction) + voice-guide §5 sample 1 (chat error message register, applicable to insight surface notification)
- spec-card-dedup → assumption-list contradiction D5 (broadening vs narrowing) + brand-book §3 anti-target framing
- spec-vault-recall-history → assumption-list S16/W17 (active recall surveillance risk) + voice-guide §1 anti-spin discipline (recall counters should be transparent, not gamified)

Each spec writer subagent prompt must include these specific Tier 0 references. Drafting the prompts requires holding all of Tier 0 in context. If context compresses, re-load Tier 0 summaries before dispatching Tier 1.

### 4.4 Active observation about Rodc's voice across tiers

The friends-intro voice (per voice-guide v2: "Specific. Anti-spin. Refuses-to-dramatize.") shows up consistently in:
- friends-intro body (1350 words, canonical)
- brainstorm doc (more code-switched / micro-comma-elided, but same anti-spin posture)
- claim_extractor.md (CORE DIRECTIVE "null is the default, not the failure case" — voice-grade discipline at code level)
- rodix_system.md banned phrase list (same "refuses-to-dramatize" structurally)

Rodc's voice is consistent across surfaces. This means Tier 1+ deliverables can confidently project the voice forward without each task re-deriving it. The Rodix Design System Skill (Tier 3 Task 9) should formalize this.

### 4.5 Active observation about the 4-bet moat fragility

The 4 bets (white-box / cross-model / active recall / real export) are individually copyable but combinatorially-locked-against-incumbents. The arc + position-strategy frame this honestly. But:

- The combinatorial-lock argument assumes incumbent business models stay engagement-LTV-locked. If Anthropic pivots to a "your data your model" stance (precedent: Apple's privacy posture), the moat dissolves.
- Probability of incumbent pivot in 12-24 months: low (Apple's privacy pivot took 5+ years and cost $X billion in foregone ad revenue; Anthropic would have to similarly disclaim ChatGPT-tier engagement metrics).
- But not zero. Worth monitoring: Anthropic's data retention announcements + OpenAI's memory feature evolution.

This active monitoring is implicit in position-strategy fail mode 1 but not operationalized. Tier 1 Wave 2 plan or Tier 3 monitoring should include "watch list: incumbent moat-pivot signals" as recurring agent task.

---

## 5. Cross-tier insights

Patterns observed across Tier 0 that affect Tier 1, 1.5, 2, 3:

### 5.1 — Two-layer model is canonical for Rodix

Brand book introduced "brand-Explorer + AI-Sage-flavored" two-layer model. Insight: this pattern likely applies elsewhere:

- **Marketing-target vs alpha-cohort:** brand book §3 target user (life-decision thinker) + Escalation #6 founder-network bias (alpha cohort likely indie-builder/AI-engineer). Two-layer: brand intent vs early-cohort reality.
- **Shipped-behavior vs aspirational-behavior:** §7 operational + §7b pending. Two-layer: today vs Wave 2/1c/3.
- **Voice surfaces:** Explorer for brand introduction + Sage for AI character + Routing for transitional. Three-layer (Decision T0-2).

Tier 1+ work should explicitly check: is this a one-layer or multi-layer concept? Multi-layer concepts need explicit routing rules.

### 5.2 — Anti-spin is the load-bearing voice principle

Per voice-guide §1, "anti-spin" is the most distinctive single move in friends-intro. v2 brand-book §7b honors it (acknowledges Wave 1b reality gaps). v2 founder narrative arc honors it (volunteered-limit triplet inserted). v2 launch-readiness criteria honors it (most-expensive-failure-path quantified).

Tier 1+ deliverables MUST honor anti-spin at every layer:
- Wave 2 specs MUST acknowledge calibration uncertainty in metrics ("precision target 80% — calibrate against alpha telemetry")
- Privacy Policy MUST disclose Phase 1 architecture compromises (server-side recall, no zero-knowledge)
- Marketing landing MUST not over-claim (per friends-intro voice)
- Founder essay MUST keep volunteered-limit triplet
- HN post MUST be honest about Phase 1 limits (English-only, no EU, indie pace)

If any Tier 1+ deliverable crosses the anti-spin line, Tier 0 voice work cascade-fails.

### 5.3 — Forced ranking + Top-K is the right shape for synthesis-style outputs

Task 0c assumption-list (47 items + Top 5 + Top 2) was actionable. Tier 1+ synthesis outputs (Wave 2 plan with 5 specs / Wave 3 plan with 7 specs / acquisition plan with channel ranking / pricing scenarios) should follow same shape — produce N items + force Top-K subset.

### 5.4 — Skeptic + CC-direct-Edit is faster than skeptic + iterator subagent for ≤ 5 edits

Task 0a v2 + Task 0b confirmed: when skeptic produces numbered edits with verbatim quotes + replacement sentences, CC Edit tool applies them faster than iterator subagent. Tier 1+ should default to this pattern.

### 5.5 — Architect's "places I almost invented content" self-flag is a critical guardrail

Task 0b architect subagent flagged 2 places for Rodc verification (rough notes / most-user-respectful). Skeptic Grep-confirmed both. Without architect's flag, both would have shipped uninspected. Tier 1+ architect-style subagents should require this self-flag section.

### 5.6 — Crisis-content protocol gap is THE single biggest brand-vs-product gap

Reinforced across Task 0a (Escalation #2), Task 0c (D1 contradiction), Tier 1.5 plan (Sarah Round 8 verification). This gap is the most likely source of Phase 1 brand integrity failure if mishandled. Tier 1 Wave 2 plan must include this as Wave 1c P0 spec or Phase 1 launch-day disclaimer.

### 5.7 — Solo-anonymous-founder-from-Asia constraint structure shapes everything

Per friends-intro Status section + Escalation #6 + recruit-strategy honest assessment:
- Acquisition channels: weighted toward warm intros + product-not-personal-brand reach
- Pricing: "founder pricing" framing for first 100 users compatible with anonymous identity
- Marketing voice: no founder photo + signed support emails (founder presence) + indie-transparent posture
- Defensibility: founder narrative is harder to clone but quieter than named-founder competitor brands

Tier 2 + Tier 3 deliverables (marketing landing / suite / docs / observability) must honor this constraint structure end-to-end.

---

## 6. What Rodc + Opus should read first (priority order, Tier 0 only)

If Rodc has 30 min of morning time:
1. **5 min:** This handoff file (`docs/superpowers/_state/handoffs/2026-05-03-tier-0-handoff.md`). You're reading it.
2. **10 min:** `docs/superpowers/brand/brand-book-v1.md` §1 + §3 + §4 + §5 sample passages + §7 Decision log + §7b commitments. Skim §2 / §6 / §8.
3. **5 min:** `docs/superpowers/tonight/escalations.md`. Read in severity order: #2 (HIGH crisis protocol) → #5 (MEDIUM interview threshold) → #3 (MEDIUM defensibility frame) → #4 (LOW rough notes) → #6 (LOW founder-network bias). #1 already resolved.
4. **5 min:** `docs/superpowers/research/launch-readiness-criteria.md` 5-criterion gate.
5. **5 min:** `docs/superpowers/brand/founder-narrative-arc.md` — full arc (1942 words; ~7-8 min read).

If Rodc has 60+ min:
- Add: `docs/superpowers/research/assumption-list.md` Top 5 + Top 2 + Contradicted section
- Add: `docs/superpowers/brand/voice-guide.md` 5 principles + 7 dos / 7 donts + 3 sample passages
- Add: `docs/superpowers/research/user-interview-script.md` Sections B + C

If Opus is brought in for stress-test:
- All of above
- Plus: `docs/superpowers/brand/position-strategy.md` (5294 words) for defensibility frame analysis
- Plus: `docs/superpowers/brand/review-notes.md` (skeptic v2 review) for the 6/1/0 + edits applied audit

---

## 7. Tier 1 dispatch checklist (to do at start of Tier 1)

Before Tier 1 work begins, CC must:
- [x] Verify Tier 0 outputs all readable + canonical (all 6 brand files exist; all 4 research files exist; all 3 task summaries exist; escalations file at 6 entries)
- [x] Verify Tier 0 reusable-patterns.md has all 7 patterns logged
- [ ] Read `docs/superpowers/plans/2026-05-01-claim-extraction.md` v1.8 final state (Tier 1 Task 1 input)
- [ ] Read `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` (33 scenarios) for Wave 2 spec mapping
- [ ] Verify (via Bash) `app/web/server.py` chat_claims schema for spec-card-real grounding
- [ ] Brief 5 Wave 2 spec-writer subagents with Tier 0 references (per Decision 4.3 above)

Tier 1 budget: 5-6h. Tier 1 success criteria: Wave 2 plan with 5 specs at "Wave 1b plan v1.8 quality bar" — implementer-ready, no spec ambiguity, no deferred decisions disguised as features.

---

*End Tier 0 handoff. Tier 1 begins next.*
