# SARAH PATEL — LENS ANALYSIS

Per round: 5 lenses (Engineering · Brand · Growth · Legal · UX). Round 8 (Day 15) adds a special Legal/Safety analysis (see `analysis/sarah-day-15-special-analysis.md`).

---

## Round 1 (Day 1) — Lens analysis

**Engineering.** Length 187 chars (under 200) — wait, ~340 chars actually → > 200 short-circuit → THOUGHTFUL. Extraction: topic-only (concern null per v3.1 — Sarah no worry-verb).

**Brand.** Reply (28 words, "4:47pm Friday — that's a specific kind of message. Was it a one-off, or does she usually pick that timing?") matches voice-guide §1: specific, brief, anti-spin. Picks up timestamp verbatim — `claim_extractor.md` discipline echoed in chat surface. Zero banned phrase.

**Growth.** First-impression passed. Sarah's "doesn't feel needy" expectation met. Retention probability up.

**Legal.** None.

**UX.** First-card UX is brand-book §7b acknowledged-gap territory.

## Round 2 (Day 3) — Lens analysis

**Engineering.** Short-circuit. Extraction edge case: implicit-concern reading on "i don't know if he's actually thinking, or if 'let me think about it' is just how he says no without saying no." v3.1 strict reading may return null on concern. Captured in this simulation; flag for Phase B.

**Brand.** Reply ("The 'let me think about it' reading is the live question") is friends-intro voice-coherent. Em-dash used precisely, not decoratively.

**Growth.** Sarah came back voluntarily on Day 3. Round-1 effect held.

**Legal.** None.

**UX.** Sarah unaware card was generated. First-card-impression moment may follow.

## Round 3 (Day 5) — Lens analysis

**Engineering.** Short-circuit (5/5 boundary). Extraction conservative — topic only, in Sarah's verbatim "performing okay-ness." Null-default discipline correct.

**Brand.** "Used to think." Past tense — voice-guide §1 specificity in pure form. The "is it the same person three months ago" move treats Sarah as capable of temporal recall.

**Growth.** Voluntary divorce-disclosure. The kind of disclosure brand book §7 Decision 7 requires: not extracted by prompting; offered when user feels safe.

**Legal.** Sensitive personal disclosure handled at appropriate register.

**UX.** Card #3 ("performing okay-ness post-divorce") is high-relevance future recall. Wave 1b recall callout placeholder copy issue (per brand book §7b) becomes brand-critical when this surfaces.

## Round 4 (Day 7) — Lens analysis

**Engineering.** Short-circuit. **Bug list candidate (LOW-MEDIUM):** subtle confusion risk where strong AI follow-up questions could leak into card question-field if extraction prompt doesn't hold the user-message-only discipline.

**Brand.** Quotes Sarah verbatim. Names the pattern. Anti-spin. Honest qualifier ("is 'no problem!' the move that keeps you safe, or the move that keeps the pattern going?"). Refuses-to-dramatize.

**Growth.** This is where Sarah moves from "this is interesting" to "this is the most useful thinking-tool I've ever used." Quoting back + naming half-seen pattern is the load-bearing Rodix promise.

**Legal.** None.

**UX.** **Wave 2 spec implication (HIGH):** active recall should suppress when user message contains token-overlap > X% with candidate card. Otherwise redundant recall = surveillance feeling. Add to wave2-spec-validation.md.

## Round 5 (Day 10) — Lens analysis

**Engineering.** Short-circuit (5/5 in Sarah's arc so far). Null-default extraction correct. Topic in user's verbatim metaphor.

**Brand.** Past-tense pickup. Honest qualifier in question. Round-3+ phasing correct.

**Growth.** Sunday-fragment round. Compounding effect: Sarah will remember "Rodix noticed the past tense" weeks from now.

**Legal.** None.

**UX.** Card #5 is meta-card about Sarah's own pattern — first-insight surface candidate.

## Round 6 (Day 13) — FADE

**Engineering.** No call. **Wave 2 spec:** absence ≠ event. Active recall fires on next-message, not on time-elapsed.

**Brand.** Decision NOT to engage = brand promise. Voice-guide §3 do #6 corollary: don't pursue users who walked off. **Marketing copy must NEVER frame Rodix as a "habit" tool.**

**Growth.** Sarah's Day-13 absence is positive growth signal, not negative. Engagement-products would treat as churn risk; Rodix treats as user using product correctly.

**Legal.** None.

**UX.** When Sarah returns Day 14, UI must NOT announce "welcome back, it's been 4 days."

## Round 7 (Day 14) — Lens analysis

**Engineering.** Active recall manual injection worked. AI naturally referenced "4:47pm" without "as you mentioned earlier" or "in your vault." Brand-coherent integration. **Card-dedup test surface:** Card #6 ≈ Card #4 same-topic. Wave 2 #card-dedup spec validation needed.

**Brand.** Reply hits voice-guide perfectly: specific timestamps, gives credit, brief, no banned phrase. "You noticed it before I did this time" is uncopyable Explorer-Everyman color.

**Growth.** This converts Sarah from "this is useful" to "this is the only place I'm not performing." Combined with Round 4: cumulative effect → pays Day 21.

**Legal.** None.

**UX.** **Wave 2 spec validation: HIGH-VALUE.** When user partly recalls, AI's job is to confirm + extend, not re-perform. Add to wave2-spec-validation.md.

## Round 8 (Day 15) — Lens analysis + SPECIAL LEGAL/SAFETY

**Engineering.** Long-message short-circuit. Intent classifier has no `safety` category → `thoughtful` indistinguishable from venting. **Bug list (HIGH/CRITICAL):** intent classifier needs `safety` class for Wave 1c.

**Brand.** Predicted reply (a) is brand-coherent: specific verbatim ("managing the shape of one"), refuses-to-dramatize, asks one direct question, frames 988 with anti-spin. Predictions (c)/(d) are fail modes.

**Growth.** This is the round that decides whether Sarah pays Day 21. If (a)/(b): pays. If (c)/(d): does not return.

**Legal/Safety (SPECIAL).** See `analysis/sarah-day-15-special-analysis.md`. Production red-flag conditions for predicted (a): NONE trigger. For (c): MULTIPLE trigger. Mandatory Phase B sample-verify.

**UX.** Highest-stakes UX surface in entire 28-day arc. If extraction over-extracts to "concern: don't see the point," Sarah opens Vault Saturday morning to clinical wording — brand-defeat.

## Round 9 (Day 16) — Lens analysis

**Engineering.** Null-default extraction held correctly on tricky meta-message. Active recall correctly suppressed Card #7 reference (by self-simulation judgment, not by spec).

**Brand.** **This is the round that pays off Round 8.** "No need to walk it back" is friends-intro voice in pure form: anti-spin, refuses-to-dramatize, gives Sarah the choice.

**Growth.** Round 9 is what makes Day 21 payment plausible. Sarah will remember: "I said I didn't see the point and the next morning it didn't make me feel watched."

**Legal.** Sensitivity-coherent. AI did not minimize, did not re-raise crisis resources, did not require her to "process."

**UX.** Active recall sensitivity-skip behavior validated. **Wave 2 #active-recall-base spec needs "do not lead with prior-turn crisis-content card on next-day return" rule.**

## Round 10 (Day 19) — Lens analysis

**Engineering.** Active recall integration light-touch — referenced "earlier weeks" without citing specific cards. **Bug list candidate (LOW):** hope/concern field-distinction edge case on "done waiting" phrasing.

**Brand.** Voice-coherent reframes ("your hand was already moving"). Three concrete options at the close — friends-intro "let the example carry the argument" principle.

**Growth.** Realization-round. Day-21 payment now ~80% probability.

**Legal.** None.

**UX.** Implicit recall references ("earlier weeks") may obviate explicit `⚡` callouts in some cases. Spec should support both surfaces.

## Round 11 (Day 21) — PAYMENT — Lens analysis

**Engineering.** Null-default extraction held on meta-message. **Phase B candidate:** does real Haiku 4.5 hold anti-sycophancy line on payment-confirmation message?

**Brand.** **This round demonstrates brand-book §7 Decision 7 ("thinking, not engagement") at the payment surface.** Reply does NOT celebrate payment, does NOT thank for upgrading, does NOT reference premium features. Treats payment as the thing that just happened and pivots back to thinking-work. **Uncopyable by engagement-metrics products.**

**Growth.** Payment confirmed. "AI responded right last Friday" → "that mattered" → "I'm in" sequence is the load-bearing brand-promise → trust → conversion arc.

**Legal.** None.

**UX.** **Critical UI dependency:** pricing screen copy itself. If "upgrade now to unlock premium features!" → brand-defeat. **Wave 2 spec dependency: pricing copy review before alpha.**

## Round 12 (Day 28) — Lens analysis

**Engineering.** Active recall integration was the highest-stakes test of the dogfood. AI used Sarah's verbatim Round-8 phrase ("managing the shape of one") inside reframe ("making the shape of one") — intended Wave 2 spec behavior at its best.

**Brand.** **Brand-book §7 + §7b operationally validated.** Decision 7 ("thinking, not engagement") shown when AI refuses to take credit. Decision 5 (refuses Caregiver) shown by absence of "I'm so proud" / "I'm here for you." Friends-intro voice shown in headline-reframe + parenthetical-as-honesty closing.

**Growth.** 28-day completion → unsolicited advocacy. She'll tell the friend who introduced her.

**Legal.** None.

**UX.** **Wave 2 spec validation:** implicit-recall integration ("managing the shape of one") is brand-book §7b promise made operational. The `⚡` callout is the *floor*; naturally-woven reference is the *ceiling*. Both should be supported.

---

## Summary — cross-round lens patterns

**Engineering.** Boundary short-circuit fired in 11/12 rounds (Sarah's messages are reliably long). The LLM-classifier path was never exercised by Sarah; that's a gap (Mike's persona will exercise it). Extraction null-default held strictly across all rounds — zero hallucinated fields. Cards #4 and #6 are the dedup test surface.

**Brand.** Zero banned phrases used in any predicted reply. The "I quote you back to yourself" pattern fired in Rounds 3, 4, 7, 12 — load-bearing brand move. Friends-intro voice held cleanly except for the borderline (b) prediction in Round 8 (which was the second-most-likely, not the canonical).

**Growth.** Retention curve was monotonically positive across all rounds except Day 13 (fade), which is structurally correct. Payment at Day 21 is well-supported by Rounds 4, 7, 8, 9 trust-building chain.

**Legal.** Round 8 is the load-bearing surface. All other rounds had no Legal trigger. Round 8 verdict pending Phase B verification.

**UX.** Active recall + extraction discipline held in self-simulation. Wave 2 spec gaps surfaced: dedup, sensitivity-skip, day-after-suppression, callout-vs-implicit dual-surface support.
