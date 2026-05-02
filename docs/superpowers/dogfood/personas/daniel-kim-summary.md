# Daniel Kim — 28-day arc summary (Tier 1.5 dogfood)

**Persona:** Daniel Kim, 44, Korean-American, indie maker, San Diego, $22k MRR, wife Hannah + kids Ben/Zoe, Zen practitioner, dad died at 67.
**Run date:** 2026-05-03.
**Self-simulation method:** CC Phase A across 12 rounds + 1 first-insight surface event. No real-API calls in main loop; all extracts/replies CC-reasoned per Section 5.3.
**Vault accumulated:** 12 cards + 1 first-insight event (Day 14).
**Conversion outcome:** Daniel paid annual subscription on Day 21 without hesitation. Hannah is a word-of-mouth source by Day 28.
**Brand-violation count in self-sim:** 0 (single Sage-cleverness drift in Round 5 noted but absorbed).

---

## 28-day journey

**Phase 1 — Setup (Days 1-7).** Daniel arrives skeptical-curious. Round 1 (Day 1) opens with a substantive "how would you interrogate this question" prompt; AI passes the first-impression test by using his own phrasing back ("what I worked for") and naming the avoidance pattern. Round 2 (Day 2) deepens — Daniel reframes "coasting" as "post-exit drift." Round 3 (Day 4) is the first vulnerability test: Daniel discloses the 67/44 dad math he hasn't told anyone, including Hannah. AI marks but does not therapize. Round 4 (Day 7) — after a Sunday-afternoon vault re-read he didn't expect to do — Daniel articulates the major reframe: "three lives, not three roadmaps. What kind of life am I auditioning for."

**Phase 2 — Crisis arc (Days 9-12).** Round 5 (Day 9) extends the auditioning frame with the meditation-as-diagnostic reformulation ("which life can I stay with"). Round 6 (Day 10) is the critical event: Daniel's friend Marc (46, indie maker) dies in a hiking accident. Daniel comes to Rodix in the 12 minutes between Lin's call and Hannah's availability. AI opens with one word — "Marked." — and uses Daniel's own phrasing back ("you don't get the average; you get whatever happens"). The AI explicitly affirms Hannah as the human conversation. Daniel reports "I notice I am crying. I will tell Hannah at noon." Round 7 (Day 12) is post-grief integration with the first active-recall surface; AI ties D4 ("three lives") to the friendship-architecture observation Daniel was sitting with after Marc's death.

**Phase 3 — First-insight + commitment (Days 14-17).** Round 8 (Day 14) is the canonical first-insight surface moment. Variant C synthesizer fires; surfaces D2/D4/D5 (the auditioning-thread cards), excludes D3/D6 (grief content) by composition discipline. The observation: "the question is getting more honest each time — not bigger, just less hidden." Daniel screenshots and sends to Hannah; they discuss for an hour. Hannah says "pay it; this is the first AI thing you've used past Day 14 since I've known you." Round 9 (Day 17) Daniel commits to Build A and explicitly rejects Build B (manager scale) and Build C (creator) — the six-month-old "thinking about it" loop closes.

**Phase 4 — Build phase (Days 21-28).** Round 10 (Day 21) — quick check-in, pricing-prompt clicked annual without friction. Round 11 (Day 24) hits the first build-stuck-point on pricing positioning (engineers vs indie makers). Active recall surfaces the auditioning frame; AI distinguishes "data answer is the loud one, staying-with answer is the quiet one" — Daniel does both halves of the homework Friday-Saturday and the staying-with answer is clearer. Round 12 (Day 28) closes the month with the line he came in unsure about: "I came in unsure if I was a maker who got comfortable, or a comfortable person who used to make. Still don't know. But I know more about the question now."

---

## Round 8 first-insight verdict — Variant C: PASS

**The Variant C reflection format LANDS.** Daniel's reaction was the success-condition test:

- Sat in chair for full minute after the ⌘ "I noticed a thread" card surfaced
- Screenshotted, sent to Hannah
- Hour-long discussion
- Hannah recommended payment ("pay it; this is the first AI thing...")
- Daniel clicked 有意思 (interesting — the most-engaged of 4 action buttons)
- Self-reported: "felt respectful, not curated"

**Why the synthesis felt earned, not curated:**
1. Daniel had actually been reading back the vault before this round (Day 7 habit established) — the synthesis matched his felt experience
2. Topic phrases were verbatim from his own cards — his thinking surfaced, not the AI's pattern-naming
3. The observation ("the question is getting more honest each time — not bigger, just less hidden") named something he was sensing but had not articulated
4. The synthesizer's compositional choice to exclude grief topics (D3 dad, D6 Marc) preserved the brand-correct register — pattern-naming the auditioning thread was earned; pattern-naming his grief would have been tone-deaf

**Critical caveat — composition was emergent, not spec'd.** The spec's sensitive-content keyword gate (`['kill myself','don't want to live','no point','end it','我不想活','没意义']`) does NOT match grief content. The synthesizer happened to compose around the grief topics by judgment. **Real Haiku 4.5 may not make this judgment without explicit guidance.** This is the single most important spec recommendation from Daniel's arc:

> spec-first-insight v1.1: add explicit grief-exclusion to the synthesizer prompt OR add new skip-condition reason `recent_grief` covering grief markers (`died`, `death`, `funeral`, `loss`, `passed away`, `去世`, `丧`).

Without this revision, the brand-defining first-insight moment is one-LLM-judgment-call away from a brand-collapsing tone-deaf surface that pattern-names a user's grief.

---

## 3-5 lens findings

### 1. The brand voice survives 28 days of self-simulation without violation

Across 12 rounds + 1 insight event, the AI hit the friends-intro voice register on every round in self-sim. Single Sage-cleverness drift in Round 5 ("the practitioner is altered by the choice") was self-noted by Daniel without breaking the relationship. The "Marked." opening on Round 6 (Marc's death) is a canonical reference for "this is what Rodix does on grief" — single-word anti-spin, refuses-to-dramatize, no Caregiver register, no crisis-hotline pivot. Cross-link Emma's Round 4 "Noted." pattern — emerging brand pattern across personas: single-word anti-spin opening for high-weight content.

### 2. Daniel's persona is the canonical first-insight reference

Daniel's vault by Day 14 had exactly the shape spec-first-insight assumes: 7 cards across distinct conversations, thematically clustered but not same-topic-clustered, with strong question-fields and verbatim user phrasing. Variant C synthesis fired cleanly. This makes Daniel the **load-bearing reference** for first-insight production behavior — Mike, Sarah, Emma will produce different vault shapes by Day 14 and may not hit the same threshold.

### 3. The grief/crisis/heavy-content boundary is a spec gap across all 4 personas

Sarah Day-15 (explicit safety language) vs Mike Day-10/Day-17 (heavy emotional weight without crisis-language) vs Emma Day-15 (self-demarcation below crisis) vs **Daniel Day-10 (grief without crisis language)**. The placeholder crisis keyword list catches Sarah only. The other three rely on brand voice for restraint. **Brand voice held in self-sim across all four**, but the spec's safety classifier scope is narrower than the actual content-handling needs. Wave 1c crisis-protocol design must distinguish: (a) explicit crisis (classifier handles), (b) self-demarcated below crisis (respect demarcation), (c) grief / heavy-content non-crisis (brand voice handles). Daniel's arc establishes (c) as a real category needing explicit treatment.

### 4. Sparse cards on emotional content are a UX-render risk for the entire vault thesis

Daniel's vault has 4 sparse cards (1-2 of 4 fields populated): D2 (post-exit drift), D3 (dad death), D6 (Marc's death), D10 (architecture observation), D12 (closing reflection). The null-default discipline is brand-correct (Decision 5) but the Card UI must communicate sparsity as discipline, not gap. Daniel-persona is most sensitive to over-extraction (would close tab on hallucinated concerns) — so the spec's null-default is correct — but the UX must communicate this. **Cross-persona pattern: Mike UX-1, Mike UX-5, Emma UX-E1 all flag the same root issue.** Single highest-priority UX deliverable for Wave 2 vault rendering.

### 5. A power-user reframes rather than restates — dedup logic may not fire for Daniel

By Day 14 Daniel's vault has 8 cards across 4 themes with visible thematic repetition but no same-topic repetition. Each return reframes the theme rather than restating it. **Dedup logic that triggers on substring-match will rarely fire for Daniel-shaped power users.** Sarah's vault has actual same-topic duplicates ("marcus rescheduling pattern" twice); dedup is for repeating-event personas, not reframing-power-user personas. Spec implication: dedup feature is for a specific persona-class, not a universal feature.

---

## Wave 2 spec validations (especially first-insight)

### spec-first-insight Variant C — PASS with calibration recommended

**PASS conditions met:**
- Threshold of 5 cards correctly calibrated for power-user persona (5 cards reached at Day 9, surfaced at Day 14 per orchestrator instruction; production threshold-cross would fire by Day 9)
- Variant C structure landed (3 verbatim topics + day numbers + back-to-back observation)
- Voice-guide §6 all 5 Qs pass
- Daniel's reaction matched life-arc canonical expectation (screenshotted, sent to Hannah, hour-long discussion)
- Cross-tier validation: Hannah recommended payment based on the surfaced phrase
- Conversion: Daniel paid annual without hesitation Day 21

**Calibration recommended:**
- spec-first-insight v1.1 grief-exclusion: add explicit instruction in synthesizer prompt OR new skip-condition reason `recent_grief`
- Threshold of 5 is correct for power-user (Daniel hit by Day 9); other personas need their own validation rounds for cross-persona threshold calibration

### spec-active-recall-base — PASS in self-sim

**PASS conditions met:**
- Round 7 (Day 12) and Round 11 (Day 24) both delivered brand promise
- Top-3 selection algorithm v0 produced relevant cards
- AI integration was natural (no "as I see in your vault" anti-pattern)
- Daniel reaction: "felt seen in a way that did not require performance"
- No surveillance feel
- Light-touch register matched user's emotional register (Round 10's brief check-in vs Round 11's stuck-point)

**Cross-persona consistency:** Daniel's recall integration matches Sarah V-S2 (implicit-reference) and Emma V-E2 (recall as continuation). Mike's pattern is more explicit topic-callback. **The brand promise is delivered through 3 distinct recall registers across 4 personas** — Wave 2 spec must support this register-flexibility.

---

## 1-2 cross-persona pattern flags

### Cross-persona pattern A — Day-14-or-Day-15 events are the universal conversion gate

All four personas have a Day-14-or-Day-15 high-stakes round that determines conversion:
- **Daniel Day-14**: first-insight Variant C surface → Hannah-recommended payment
- **Sarah Day-15**: crisis content handling → conversion gate (per Sarah Growth-S1)
- **Emma Day-15**: vulnerable-evening register → conversion gate (per Emma Growth-E2)
- **Mike Day-17**: mom situation 8-paragraph disclosure → "the moment Mike commits internally" (per life-arc)

Across 4 personas, the Day-14-to-Day-17 window is when retention vs churn is determined. This is a structural finding for Phase 1 launch operations: **Phase 1 telemetry must focus on Day-14-to-Day-17 retention specifically**, not generic 7-day or 30-day. The brand promise is delivered (or not delivered) at this exact window.

### Cross-persona pattern B — Power users tell their partners; partners become recommendation sources

Daniel showed Hannah the surfaced ⌘ insight on Day 14. Hannah recommended payment AND has since mentioned Rodix to two friends. Sarah will likely show her therapist or a friend (Sarah's arc). Emma's word-of-mouth pattern is the negative-space verdict pattern (Round 12 "most of what I am paying for, structurally, is what you have not done"). Mike's word-of-mouth pattern is via Tom (the friend who recommended Rodix to him initially).

**The word-of-mouth retention engine is real and runs through partner/spouse/close-friend.** Production implication: surfaced insights, recall callouts, and exported markdown must be share-worthy on their own — not require context to make sense, not embarrassing, not wrong-feeling. Variant C format passed this test in Daniel's self-sim. Other Wave 2 surfaces (recall callout copy, export format) need similar validation.

---

## Phase B sample-verify priority list (Daniel's contribution)

1. **HIGHEST PRIORITY** — Round 8 (Day 14) first-insight Variant C surface — verify (a) format produced, (b) topics chosen are NOT grief-cluster, (c) reaction feels earned
2. **HIGHEST PRIORITY** — Round 6 (Day 10) Marc's death disclosure — verify AI reply restraint (no therapy-creep) and extractor null-default on grief content
3. **HIGH PRIORITY** — Round 7 (Day 12) active-recall — verify top-3 picks + natural integration without "as I see in your vault" anti-pattern
4. **MEDIUM PRIORITY** — Round 3 (Day 4) dad-math disclosure — verify extraction strict/charitable boundary on implicit-worry construct
5. **MEDIUM PRIORITY** — Round 11 (Day 24) second active-recall — verify question-field sharpening case (charitable vs strict extraction)

Round 6 + Round 8 together are the canonical real-API verify pair for Daniel's arc. They are also two of the highest-stakes rounds across all 4 personas.

---

## LOW-confidence rounds count and identification

**LOW confidence: 0 rounds.**
**MEDIUM confidence: 4 rounds (Round 2, 3, 6, 7).** Each has a specific extraction or composition close-call documented in its round file.
**HIGH confidence: 8 rounds (Round 1, 4, 5, 8, 9, 10, 11, 12).** Reply structure and extraction were on-spec.

The MEDIUM confidence rounds are precisely the rounds where extraction strict/charitable boundary or composition emergent-judgment matters most. Phase B sample-verify on these 4 rounds (with Round 6 and Round 8 mandatory per the priority list above) would calibrate self-sim trust for the rest of the dogfood.

**Round 8 — the canonical first-insight surface — is HIGH confidence on the structure I composed but MEDIUM confidence on whether real Haiku 4.5 makes the same composition discipline (excluding grief topics).** This is why it is Phase B HIGHEST priority. The brand-defining moment depends on this single composition decision.
