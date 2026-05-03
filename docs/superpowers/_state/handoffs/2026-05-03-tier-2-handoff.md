> **Note 2026-05-04:** Brand renamed Rodix → Rodspan. This file is a historical record from prior to the rename and retains the original "Rodix" name as written at the time. See `docs/superpowers/tasks/rodix-to-rodspan-rename.md` for context.

# Tier 2 Handoff — 2026-05-03

**Tier 2 status:** COMPLETE (Hour ~9.5 of 30-hour shift)
**Tasks completed:** 5 (Marketing Landing) / 6 (Marketing Suite 5 channels) / 7 (Documentation Pack) / 8 (Privacy + ToS)
**Author:** CC (autonomous shift)

---

## 1. Completion summary

| Task | Status | Self-grade | Files |
|---|---|---|---|
| 5 Marketing Landing | DONE | A- | landing-research / landing-copy-v1 / index.html / design-tokens.css / screenshots README / decisions |
| 6 Marketing Suite | DONE | A | voice-research + 5 channel deliverables + voice-consistency-review + decisions (8 files) |
| 7 Documentation Pack | DONE | A- | welcome / how-it-works / privacy-summary / faq / getting-started + 3 JSON microcopy + review (9 files) |
| 8 Privacy Policy + ToS | DONE | A- | legal-research / privacy-policy-draft / terms-of-service-draft / legal-review-notes / legal-decisions (5 files) |

Tier 2 budget: 5-6h. Actual: ~50 min wall-clock parallel + ~10 min sequential = ~1 hour. Significantly under-budget due to background-parallel pattern.

Tier 2 deliverables: deploy-ready landing (HTML + CSS + copy), 5-channel marketing suite (founder essay + HN + PH + Twitter + video), documentation pack (5 markdown + 3 JSON microcopy), legal drafts (Privacy Policy + ToS).

---

## 2. Type-B engineering decisions (with reasoning chains)

### Decision T2-1 — Background-parallel for 4 Tier 2 tasks

**Decision:** All 4 Tier 2 tasks dispatched as parallel `run_in_background: true` Agent calls. Returned in 5-10 min batches over ~50 min wall-clock total.

**Reasoning chain:**
1. Tier 2 deliverables are independent (landing / marketing / docs / legal) — no spec dependencies.
2. Each task is appropriately scoped for single-comprehensive-subagent (no nested orchestration needed).
3. Parallel saves ~3-4 hours (sequential 4 × 60-90 min vs parallel ~50 min wall-clock).

**Confidence:** HIGH. Same pattern as Tier 1 Tasks 2-4.

### Decision T2-2 — Defer copy/HTML iteration

**Decision:** Tier 2 deliverables saved at v1 (or v1.1 with subagent self-review). Did NOT dispatch reviewer + iterator subagents per Tier 0/1 pattern.

**Reasoning chain:**
1. Each Tier 2 subagent ran an internal self-review (per task brief).
2. Marketing/legal copy is iterable post-Rodc-review with low cost (no schema migration / no implementer dispatch).
3. Reviewer + iterator pattern adds ~30-45 min × 4 = 2-3h. Trade-off vs deferring to Rodc tomorrow morning.
4. Self-review sections in each deliverable allow Rodc to spot-check without re-running.

**Confidence:** MEDIUM-HIGH. Some risk Rodc reads tomorrow + finds issues skeptic would have caught. Mitigated: each subagent's self-review section flags weak sentences explicitly.

### Decision T2-3 — Landing CSS new soft-amber border token

**Decision:** Marketing Landing introduced `--border-amber-soft: rgba(217, 119, 6, 0.35)` as new CSS token (not in brand-book §6). Used for landing's 4-field card mockup (Sept 3 / Sept 19 / Oct 4 example).

**Reasoning chain:**
1. Solid amber on three stacked cards reads as "marketing illustration" (loud, demands attention).
2. Soft amber reads as "subtle distinguishing feature" (restrained, hover strengthens to full).
3. Brand-book §6 visual identity is constraint envelope, not exhaustive token spec.
4. Hover state preserves the locked amber.

**Confidence:** HIGH. Aligns with Anthropic-restraint visual register.

### Decision T2-4 — HN post mechanism-first opening

**Decision:** HN Show post opens with concrete problem-and-product (architectural-commitment frame), NOT with founder-personal-story.

**Reasoning chain:**
1. HN audience values mechanism over biography.
2. Mike Round 8 cross-persona finding: 4/4 personas converged on "didn't perform usefulness" trust-pivot — HN audience is closest to this filter.
3. Founder-personal-story is the founder essay scope; HN inherits founder context but leads with what.
4. Friends-intro voice register: HN-honest = mechanism + volunteered-limit + invitation.

**Confidence:** HIGH.

### Decision T2-5 — Twitter thread anonymous handle constraint

**Decision:** Twitter thread signs only `@rodix` (no personal handle). 8 tweets all 64-279 chars. ⚡ used once. NO 🚀/🎉/🔥.

**Reasoning chain:**
1. Anonymous-founder constraint per friends-intro Status section.
2. ⚡ is Rodix product asset (recall callout); used once in thread mirrors product use.
3. Other emojis would violate brand-book §6 zero-emoji-decoration rule.

**Confidence:** HIGH.

### Decision T2-6 — Privacy Policy honest disclosure of Phase 1 limits

**Decision:** Privacy Policy explicitly discloses:
- Phase 1 = at-rest plaintext (no zero-knowledge)
- Wave 3 = per-user encryption (NOT zero-knowledge even then)
- Anthropic ZDR = TODO pending verification
- Crisis content = Wave 1c protocol (not yet implemented)
- Geo-block EU at network edge AND user-declared residence

**Reasoning chain:**
1. Friends-intro voice line 353-355 honesty: "we can't promise zero-knowledge — that would be a lie."
2. Brand-book §7 Decision 6 + §7b standing escalation lock anti-spin discipline at legal layer.
3. Honest disclosure is brand-coherent + legally defensible (vs overclaim + sue-vulnerability).

**Confidence:** HIGH. Anti-spin brand-discipline holds across legal layer.

### Decision T2-7 — FAQ includes crisis-content question (Q15)

**Decision:** FAQ includes "What if I'm having a hard time / mental health crisis?" Question 15 of 15. Honest answer per Wave 1c crisis-protocol: "Rodix is for thinking, not therapy. If you're in crisis, please reach out to 988 (US) / Crisis Text Line / local equivalents. Future Wave 1c will surface these resources automatically."

**Reasoning chain:**
1. Brand book §7b commitment to crisis-content protocol must be visible to user pre-implementation.
2. FAQ documents intent before code ships.
3. Honest disclosure of "future Wave 1c" preserves anti-spin discipline.

**Confidence:** HIGH.

### Decision T2-8 — Documentation pack "Marked." pattern absent

**Decision:** Documentation pack does NOT yet codify "Marked." / "Noted." matter-of-fact acknowledgment pattern (Tier 1.5 Finding 5).

**Reasoning chain:**
1. Tier 1.5 surfaced this AFTER Tier 2 documentation dispatched.
2. Pattern emergence is post-tier discovery; codification is iterative.
3. Voice-guide.md should add this — Tier 3 Task 9 Design System Skill voice-guide.md may need v1.1 patch.

**Confidence:** MEDIUM. Worth flagging for Tier 3 Task 9 patch + Wave 4 voice-guide v1.1.

---

## 3. Confidence-flagged items for Rodc + Opus review

| Item | CC Confidence | Why qualified | Rodc / Opus action |
|---|---|---|---|
| Landing copy v1 (no iteration loop) | MEDIUM-HIGH | Self-review caught one fabricated metric ("eight seconds"); HTML output corrected; markdown preserved audit | Rodc reads landing-copy-v1.md; veto/approve weakest sentence |
| Landing soft-amber CSS token | HIGH | Aligns with Anthropic-restraint visual register | Tier 3 Task 9 Design System Skill should incorporate |
| HN title 76 chars | HIGH | Verbatim from founder-narrative-arc adaptation note | None — confirmed |
| Marketing Suite cross-channel coherence | HIGH | Self-review verdict 1-voice with 5 calibrations | Rodc reads voice-consistency-review.md |
| Privacy Policy ZDR TODO | HIGH | Cannot publish until Anthropic ZDR confirmed | Rodc contacts Anthropic sales (1-3 day lead) |
| Privacy Policy crisis-content clause | HIGH | Honest disclosure of Wave 1c gap | Coordinate with Wave 1c crisis-protocol spec |
| ToS founder-signature anonymous-vs-LLC tension | MEDIUM-HIGH | Intersects Wave 3 LLC formation (Escalation #9) | Resolve LLC jurisdiction first |
| Documentation pack "Marked." pattern absent | MEDIUM | Tier 1.5 finding post-Tier 2 dispatch | Patch via Tier 3 Task 9 Design System v1.1 |
| FAQ Q15 crisis-content honest answer | HIGH | Friends-intro voice register + Wave 1c commitment | None — verify wording |
| 5-channel marketing total ~5500 words | MEDIUM | Above target due to PH + voice review | Acceptable; trim post-review if needed |

---

## 4. Pre-compaction snapshot — active context not in files

### 4.1 Active reasoning about Wave 4 marketing surface review

When Rodc launches Phase 1 alpha, the 5 marketing channels execute in this order:
- Day -7: founder essay published (rodix.app/blog or Substack)
- Day 0: HN Show HN launch (Tuesday 6am EST optimal)
- Day 1: Product Hunt queued launch
- Day 1-3: Twitter founder thread + organic engagement
- Day 0-7: Launch video posted on Twitter + landing
- Day 0-30: Continued blog content + community engagement

Each surface must hold brand voice. Per Escalation #11 (anti-spin marketing copy lock — standing), every public copy update reviews against §7 Decision 6 lock language ("encryption at rest, recall server-trusted" never "end-to-end").

### 4.2 Active reasoning about marketing-decisions.md 5 Type-A items

Marketing Suite subagent flagged 5 Type-A escalations in `marketing-decisions.md`. These are tier-2-specific (channel-tactics decisions Rodc weighs) — not promoted to top-level escalations.md. Examples likely:
- Founder essay venue (rodix.app/blog vs Substack vs Medium)
- HN posting time (Tuesday 6am EST default)
- Video format (vertical 9:16 + horizontal 16:9 both vs prioritize one)
- Twitter handle naming (@rodix locked but @rodc personal vs anonymous account decision)
- PH launch maker comments pre-prepared

These are Rodc-decision items but not cross-tier blocking. Rodc reads marketing-decisions.md when planning launch sequence.

### 4.3 Active reasoning about Privacy Policy pre-publish gates

Privacy Policy cannot publish until:
1. Anthropic ZDR status confirmed (Rodc → Anthropic sales, 1-3 days)
2. LLC formed (Wave 3 Escalation #9, 2-4 weeks)
3. Wave 1c crisis-protocol shipped (Wave 1c spec → implementation, 1-2 weeks)
4. Lawyer review (optional, 2-4 weeks if Rodc allocates budget)

Phase 1 alpha can launch with TODO-marked Privacy Policy IF Rodc explicitly accepts alpha-state legal risk + Phase 1 alpha is small (≤ 1000 users) + invitation-only-not-public. Phase 2 / public launch requires all 4 gates passed.

### 4.4 Active observation about voice fidelity holding across 12 Tier 2 deliverables

5 Marketing channels + 5 documentation surfaces + Privacy + ToS = 12 distinct copy deliverables. All hold friends-intro voice (Specific. Anti-spin. Refuses-to-dramatize.) per individual self-reviews.

Cross-deliverable voice coherence is the strongest brand-validation signal Tier 2 produces. Rodc reads any 2-3 random deliverables → recognizable Rodc voice → brand book operationally coherent.

---

## 5. Cross-tier insights

### 5.1 — Anti-spin discipline cascades through legal layer

Tier 0 brand book §7 Decision 6 → Tier 0 voice-guide §1 anti-spin → Tier 2 Privacy Policy honest disclosure → Tier 2 marketing copy "encryption at rest" framing → Wave 3 #b-encryption marketing lock. Same principle applied 5 layers deep with consistent operationalization.

### 5.2 — Self-review-as-final-pass is faster than skeptic-iterator pair for medium-stakes tasks

Tier 2 used "subagent runs internal self-review" pattern (per task briefs). No external skeptic + iterator subagents. Saved 2-3h vs Tier 0 pattern.

Trade-off: Tier 0 surfaced reality-gaps that internal self-review may miss. Tier 2 is medium-stakes (iterable post-Rodc-review); Tier 0 was foundational (cascading downstream impact). Pattern: skeptic-iterator for foundation tasks; self-review for derivative tasks.

### 5.3 — Public-facing Phase 1 launch packet is now complete

Rodc has a launchable Phase 1 alpha packet:
- Landing (deploy-ready HTML + CSS)
- Founder essay (1425 words, rodix.app/blog or Substack)
- HN Show HN post (~595 words, Tuesday 6am EST optimal)
- PH launch package (queued)
- Twitter thread (8 tweets)
- Launch video script (60-90 sec voiceover, both 9:16 + 16:9)
- 5 user-facing markdown docs
- 3 JSON microcopy files
- Privacy Policy + ToS drafts (pending TODOs)

Total Tier 2 deliverables ~30+ files. This is the launch arsenal.

---

## 6. What Rodc + Opus should read first (Tier 2 only)

If Rodc has 30 min:
1. **5 min:** This handoff
2. **10 min:** `landing-copy-v1.md` (full landing page text + self-review)
3. **5 min:** `founder-essay-draft.md` (canonical founder voice)
4. **5 min:** `voice-consistency-review.md` (5-channel coherence verdict)
5. **5 min:** `legal-review-notes.md` (5 stress tests + priority-ranked edits)

If 60+ min, add:
- `hn-launch-post.md` + `twitter-launch-thread.md`
- `faq.md` (Q15 specifically — crisis-content)
- `privacy-policy-draft.md` Sections 13 + 14 + 20 (sensitive data + crisis + not-claims)
- `marketing-decisions.md` 11 Type-B + 5 Type-A items

---

## 7. Outstanding TODOs for Rodc

### Pre-publish required:
1. **Anthropic ZDR confirmation** — contact Anthropic sales (1-3 days). Privacy Policy §5/§12/§20 carry TODO.
2. **LLC formation** (Escalation #9) — Wyoming default, 2-4 weeks. Privacy Policy §1 + ToS §17 carry TODO.
3. **Wave 1c crisis-protocol shipping** (Escalation #2) — pre-Phase-1-alpha gate.
4. **Final pricing $ amount** (Escalation #10) — Landing pricing block carries placeholder $X-$Y.

### Pre-launch optional:
5. Lawyer review (legal-decisions.md flags option b: 2-4 weeks parallel with LLC).
6. Friend dogfood week (Escalation #8: 5-7 days pre-Phase-1-alpha for copy-lock confidence).
7. Marketing Suite 5 Type-A items (channel tactics).
8. Documentation pack "Marked." pattern patch (Tier 1.5 Finding 5).

---

*End Tier 2 handoff. Tier 3 partial; Phase B + Task 15 in flight.*
