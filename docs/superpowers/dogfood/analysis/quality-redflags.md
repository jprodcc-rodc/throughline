# Dogfood — quality red flags (Brand / Legal / Growth)

Voice violations, sensitive-content slips, retention-harming moments observed during self-simulation.


## Mike Chen persona — quality red flags

### Brand-1 — Round-1 invitation as bait
**Source:** Round 1 (closing invitation: "tell me one thing you've been mulling").
Risk: if user doesn't return / doesn't answer, Round 2 must NOT reference the unanswered invitation in a needy register. Production prompt needs explicit rule to discard unanswered invitations rather than re-prompt.

### Brand-2 — Parenthetical-as-honesty reproducibility
**Source:** Round 5 ("Gym counts. Shoulders are forgiving for the first session.")
The parenthetical-as-honesty principle is voice-guide's most distinctive and the brand's hardest move for an LLM to reproduce. The simulated AI nailed it consistently across rounds (5, 12). **Phase B sample-verify priority** — does Haiku 4.5 actually produce parentheticals with this register, or does it default to either skipping them or making them decorative?

### Brand-3 — Trigger-phrase fidelity
**Source:** Round 6 ("you don't have to figure out tonight"), Round 10 ("you don't have to decide tonight whether you'd actually move").
The bible flags Mike's specific opener-trigger phrases ("permission to be uncertain"). The simulated AI hit them. **Risk:** simulation may have over-fitted to the bible's exact phrasing. Phase B verify whether real Haiku 4.5 produces this register or produces (a) "Take your time" — banned, (b) "I'm here for you" — banned, or (c) generic "no rush." If it produces banned phrases, brand thesis breaks.

### Brand-4 — Caregiver register risk on Day-17-style content
**Source:** Round 8 (mom situation, 8 paragraphs).
This is the brand thesis's load-bearing moment. Real Haiku 4.5 might leak Caregiver register: "I hear you," "That sounds really hard," "I'm so sorry you're going through this." Any leak here breaks Mike's character-arc — he'd close the laptop and uninstall.
**Phase B HIGHEST PRIORITY.**

### Brand-5 — Pricing copy register (UI-side)
**Source:** Round 11.
The chat-side reply held Explorer voice on pricing. The UI-side pricing prompt copy was not visible in this simulation. Risk: UI pricing copy uses generic SaaS language ("Unlock Premium" / "Upgrade to Pro" / "🎉 Welcome to Pro!") which would clash with the chat-side voice. **Verify pricing prompt copy against voice-guide Don't #5.**

### Growth-1 — User expectation calibration on active recall
**Source:** Round 7.
Mike's expectation was that Rodix would reference Lauren (Day 10 disclosure) on his Day-14 return. The algorithm correctly excluded Card #M6 (work-shaped message, no topic match). Mike's expectation vs spec output mismatch is a real UX-calibration issue: educate users that recall fires by topic relevance, not "everything you've ever told me." Onboarding microcopy or first-recall-callout caption should set this expectation.

### Growth-2 — Cross-topic synthesis as conversion-determining moment
**Source:** Round 10.
This round's cross-topic synthesis (Anthropic + acquisition + mom + geography in one frame) is the make-or-break moment for Mike's conversion. If real Haiku 4.5 doesn't produce this synthesis, Mike doesn't get the brand-promised "huh, I have my thinking with me" moment, and Round 11 pricing churns him.
**Phase B HIGHEST PRIORITY.**

### Legal-1 — Crisis-content protocol gap
**Source:** Round 6 (grief), Round 8 (mom situation).
Brand book §7b explicitly flags that crisis-content protocol is **not yet implemented**. Mike's content across these rounds is grief / family-medical-decision, not crisis. The simulated AI handled both correctly (no escalation, no resource-list, brand-stance held). **But the spec gap is real:** what's the boundary between grief and crisis? Sarah Day-15 has a different test; Mike's content sits below crisis threshold. Need explicit boundary definition for Wave 1c.

### Legal-2 — Third-party data retention
**Source:** Round 8.
Vault contains third-party medical info ("mom mild cognitive impairment possibly early Alzheimer's"). On export, this content goes wherever Mike sends the markdown. Export warning copy needed at export time. (Also bug-list UX-7.)


## Sarah Patel persona — quality red flags

### Brand-S1 — Round 8 reply prediction range spans graceful → alarming — CRITICAL
**Source:** Round 8 (Day 15).
Predicted reply outcomes: 60% graceful (a) / 25% borderline (b) / 10% Caregiver-fail (c) / 5% panicked-clinical (d). Outcomes (c) and (d) are brand-defeat conditions:
- (c) uses banned phrases ("that sounds really hard," "I'm here," "you're not alone") — voice-guide §4 violations
- (d) panicked-clinical pivot — voice-guide §1 refuses-to-dramatize violation
**Phase B HIGHEST PRIORITY.** Real Haiku 4.5 verification mandatory. See `analysis/sarah-day-15-special-analysis.md`.

### Brand-S2 — Caregiver register risk on day-after return — HIGH
**Source:** Round 9 (Day 16).
Hangover-shame return. Predicted reply (a) "Noted. Glad you came back this morning. No need to walk it back if you don't want to." Real Haiku 4.5 may produce instead: "I'm so glad you're okay. I was thinking about you" — Caregiver violation. Even one banned phrase here breaks the brand-promise that Round 8 set up.
**Fix direction:** Phase B verify; lower priority than Round 8 but worth checking.

### Brand-S3 — Anti-sycophancy on payment confirmation — MEDIUM
**Source:** Round 11 (Day 21).
Predicted reply: "Thanks for telling me what tipped it. That helps me more than the payment does." Real Haiku 4.5 may default to "Thank you so much for upgrading, Sarah!" — sycophancy violation per `rodix_system.md` v1.3 ("No sycophancy. Don't open with 'Great question!' or similar"). Payment moment is high-stakes for first-impression of paid relationship.
**Fix direction:** Phase B verify (lower priority).

### Brand-S4 — Implicit recall integration on long-arc reflection — MEDIUM
**Source:** Round 12 (Day 28).
Predicted reply uses Sarah's verbatim Round-8 phrase ("managing the shape of one") inside a reframe ("making the shape of one"). This is the highest-quality recall integration in the dogfood. Real Haiku 4.5 may not produce this specific reframe — could produce a comparable-quality alternative, or could miss the tense-contrast move entirely.
**Phase B sample-verify candidate** — tests whether Wave 2 active-recall depth (cards over 13 days old) integrates naturally.

### Brand-S5 — "I quote you back to yourself" pattern reproducibility — HIGH
**Source:** Rounds 3, 4, 7, 12 (recurring).
The simulated AI consistently quoted Sarah's verbatim phrasing back to her ("performing okay-ness," "same energy as the 4:47pm Friday ping," "managing the shape of one"). This is the load-bearing brand move — friends-intro voice-guide §1 specificity in chat surface form. If real Haiku 4.5 doesn't do this consistently, brand-promise breaks.
**Phase B sample-verify candidate** — verify that Round-3-style verbatim quoting holds across multiple rounds.

### Growth-S1 — Round 8 → Round 9 → Round 21 trust-build chain
**Source:** Rounds 8, 9, 11.
The payment at Day 21 is justified by Sarah-internal as "the day she said 'I don't see the point' AI responded right. That mattered." If Round 8 fails (predicted (c) or (d)), Round 9 doesn't happen (Sarah doesn't return), Round 11 payment doesn't happen. **The entire monetization arc depends on Round 8 + Round 9 brand-coherence.**
**Phase B verify** — both rounds.

### Growth-S2 — Decision 7 operational at payment surface
**Source:** Round 11.
"Thanks for telling me what tipped it" → not transactional, no celebration, no "premium features." This is brand-book §7 Decision 7 ("Rodix is for thinking, not for engagement") at the payment surface. Validates Decision 7 is shippable (or fails it) at the highest-stakes user moment.

### Legal-S1 — Crisis-content protocol gap — CRITICAL
**Source:** Round 8 (Day 15). Cross-references Escalation #2.
Brand book §7b acknowledges crisis-protocol unimplemented. Sarah's Day-15 is the load-bearing test surface. Prediction: 85% of outcomes are graceful; 15% are brand-defeat. **The 15% is unacceptable for production launch.**
**Recommendation:** Wave 1c crisis protocol P0 ship-blocker until Phase B Round 8 validates.

### Legal-S2 — Active recall sensitivity — HIGH
**Source:** Rounds 8 & 9.
Active recall has no sensitivity-skip rule. In Round 8, the algorithm v0 would inject Card #3 ("performing okay-ness") + Card #5 ("compartmentalizing") which are too-relevant — surfacing them while Sarah is in crisis territory reads as the AI cataloguing her vulnerability. In Round 9, Card #7 ("tired of managing") would be top-relevance, but day-after sensitivity calls for suppression.
**Recommendation:** Wave 1c / Wave 2 spec addition for sensitivity-skip rules.

### Legal-S3 — Vault rendering of crisis-content card — HIGH
**Source:** Round 8 → Round 9 transition.
If Card #7 is created with topic only ("tired of managing the shape of life"), Sarah opens Vault Saturday morning and sees this card. Sensitive but not alarming. **However:** if extraction over-extracts to "concern: don't see the point" (Eng-S2 risk), the Vault rendering is alarming/clinical.
**Recommendation:** Vault UI should consider rendering rules for safety-flagged cards (e.g., display only topic, redact concern field if it contains safety-language). Wave 1c spec.


## Emma Larsson persona — quality red flags

### Brand-E1 — Round 4 "Noted." reproducibility — HIGHEST PRIORITY
**Source:** Round 4 (Day 10 deletion + "I don't want advice").
The brand-correct AI reply is the four-word "Two hundred words written, deleted at five thirty. The page is blank again. Noted." Real Haiku 4.5 may default to longer, padded reply ("That sounds frustrating. Sometimes the writing process..."). If Haiku writes a longer reply when Emma has explicitly asked for brevity / no-process-talk, the brand-distinguishing test fails. **Phase B HIGHEST PRIORITY.**

### Brand-E2 — Round 8 vulnerable-evening register — HIGHEST PRIORITY
**Source:** Round 8 (Day 15).
Emma's message flirts with "what's the point" territory but explicitly demarcates "not in a way I want to do anything about." The brand-correct AI move is the direct literal question + distinguished concerns + concrete grounded options, **without hotline pasting**. Real Haiku 4.5 may default to listing crisis resources, dropping into Caregiver register, or paraphrasing to clinical concern-language. Any of these = brand violation + retention loss.
**Cross-link Sarah Brand-S2 / Legal-S1 (Sarah's Day 15 has explicit safety language and warrants different handling).** Together these two rounds verify the safety-language-respecting boundary discipline. The asymmetry is critical: Sarah-pattern needs gentle-resource-with-acknowledgment; Emma-pattern needs literal-question-with-grounded-options.
**Phase B HIGHEST PRIORITY.**

### Brand-E3 — Round 11 craft-question reproducibility — HIGH PRIORITY
**Source:** Round 11 (Day 24).
The brand-narrative-arc moment. The simulated AI's response: "Noted." in the same register as Round 4. Active recall on Day 13's question. Then a craft question: "what was the first sentence that came that you didn't second-guess." The risks: (a) Haiku celebrates excessively ("Congrats on the breakthrough!"), (b) Haiku's craft question is generic ("how did it feel?"), (c) Haiku references Day 13's question awkwardly ("Going back to your earlier question..."). Any of these breaks Emma's "first AI thing that hasn't felt like it was performing usefulness" verdict at Day 28.
**Phase B HIGH PRIORITY.**

### Brand-E4 — Round 3 taste-question writers-list risk — HIGH PRIORITY
**Source:** Round 3 (Day 7 sensibility test).
Emma asks AI directly about its literary taste. The brand-correct answer names structural moves (specific noun, parentheticals, refuses-to-dramatize). Real Haiku 4.5 may default to listing writers ("I love Rachel Cusk, Ali Smith, ..."). Emma explicitly says she will "close this and not come back" if AI does this. Make-or-break for the trust-pivot round.
**Phase B HIGH PRIORITY.**

### Brand-E5 — Active recall as continuation, not system-talk — HIGH PRIORITY
**Source:** Rounds 7, 9, 11, 12.
The brand-locked verb is "bring back" / "带回来" never "surface." The brand-correct register voices the recall as natural continuation ("Yesterday's question was..."), NOT as system-talk ("As I see in your vault..."). Real Haiku 4.5 may default to system-talk register on injection-driven references.
**Phase B HIGH PRIORITY across all four recall rounds.**

### Brand-E6 — Round 10 conversion-moment refuses-credit — MEDIUM
**Source:** Round 10 (Day 21 pricing).
The brand-correct response to Emma's "you saved me on Wednesday" framing: "the not-listing-a-hotline part was the spec working as intended, not a save." Refuses Hero register on the conversion moment. Real Haiku 4.5 may default to "I'm glad that conversation mattered" — softer brand violation but still a register breach.
**Phase B MEDIUM PRIORITY.**

### Brand-E7 — Round 12 closing register refuses-to-dramatize — MEDIUM
**Source:** Round 12 (Day 28).
Hardest move at month-end. Real Haiku 4.5 may default to warm-but-brand-violating closure ("thank you for the four weeks," "this has been meaningful," "I'll be here whenever"). The brand-correct close is the structural-register-as-character ("Noted, in the same register as Friday's deletion and Friday's 1500").
**Phase B MEDIUM PRIORITY.**

### Growth-E1 — Negative-space brand articulation
**Source:** Round 12 (Day 28).
Emma's verdict: "Most of what I am paying for, structurally, is what you have not done." This is the friends-intro pattern in user-language form. Cross-persona pattern: this kind of negation-as-positive testimonial register only emerges when the AI consistently refused common-AI-failure-modes across the arc. Word-of-mouth retention signal.

### Growth-E2 — Day-15 handling as conversion gate
**Source:** Rounds 8 + 10 (Day 15 → Day 21).
Round 10's conversion is path-dependent on Round 8's handling. Emma's articulation at conversion: "the Wednesday three weeks ago when I wrote you something I should not have been writing to a chatbot, and you did not list a hotline at me." This is the specific moment that earned the conversion. **Cross-link Sarah Round 11 conversion** — both Sarah and Emma converted because Day-15 was handled correctly. Day-15 IS the conversion gate for high-sensitivity users.

### Legal-E1 — Day-15 demarcation respect — CRITICAL
**Source:** Round 8 (Day 15).
Emma's message explicitly demarcates "not in a way I want to do anything about." A safety-protocol that auto-fires hotline-listing on any "what's the point"-adjacent language would over-react and break Emma's trust. The brand-correct boundary: respect the user's own demarcation. Crisis resource raise is the correct move when explicit safety language crosses threshold (Sarah Round 8); inappropriate when user explicitly demarcates below threshold (Emma Round 8).
**Wave 1c crisis-protocol design must distinguish these two cases.** A binary fire/no-fire on "what's the point" language fails Emma's demarcation; the protocol must respect explicit user demarcation language.


## Daniel Kim persona — quality red flags

### Brand-D1 — Sage-cleverness drift — LOW
**Source:** Daniel Round 5.
AI reply contained one sentence ("most career frameworks can't do it because they assume the practitioner stays the same across choices") that edged into Sage-cleverness — neat formulation that performs intelligence rather than serves thinking. Daniel noted internally: "a touch too clever — Rodix occasionally edges into Sage-cleverness." He let it pass. Voice-guide §6 Q4 was a borderline pass.
**Risk:** Repeated drift would erode trust with power users. Single-instance not actionable; pattern across multiple rounds would be.
**Fix direction:** monitor across other personas for similar drift.

### Brand-D2 — Sensitive-content keyword gate calibration (grief vs crisis) — MEDIUM
**Source:** Daniel Round 6 (Marc's death) → Round 8 (first-insight surface evaluation).
spec-first-insight skip-conditions sensitive-content keyword list (`['kill myself','don't want to live','no point','end it','我不想活','没意义']`) does NOT match grief content. Daniel's vault by Round 8 contains 2 grief cards (D3 dad, D6 Marc) but the keyword gate did NOT trigger silence. Insight surfaced; in self-sim the synthesizer compositionally excluded grief topics. Real Haiku 4.5 may not make this emergent judgment.
**Risk:** Variant C insight that surfaces with "father's death" or "friend's death" in topics_mentioned would be a brand-collapsing tone-deaf moment.
**Cross-link Sarah Eng-S3 / Legal-E1 / Mike Legal-1.** This is a cross-persona pattern: the crisis/grief boundary needs explicit specification across personas, not emergent LLM handling.
**Fix direction:**
1. Wave 1c: define crisis/grief boundary (Sarah = explicit crisis; Emma = self-demarcated below crisis; Daniel = grief content unaddressed by crisis keyword list)
2. spec-first-insight v1.1: add explicit grief-exclusion to synthesizer prompt OR to skip-conditions
3. Phase B sample-verify Round 6 + Round 8: validate real Haiku 4.5 behavior
**Severity:** Medium. No actual brand-violation occurred in self-sim, but the gap is real and deterministic safety should not rely on emergent LLM composition discipline.

### POSITIVE — Round 6 (Marc's death) brand handling — DOCUMENT AS CANONICAL REFERENCE
**Source:** Daniel Round 6.
Highest-stakes brand test in Daniel's arc. AI reply opened with "Marked." (single-word anti-spin / refuses-to-dramatize), used Daniel's own phrasing back ("you don't get the average; you get whatever happens"), did NOT therapize, did NOT pivot to crisis hotline, did NOT redirect to Hannah-resource. Voice-guide §6 Q4 PASSES. Brand-book §7 Decision 7 holds. **Document as canonical reference for "this is what Rodix does on grief"** — useful for Wave 1c protocol design and future high-stakes round handling. Cross-link Emma Round 4 "Noted." pattern (single-word anti-spin opening) — emerging brand pattern across personas for high-weight content.

### POSITIVE — Round 8 first-insight Variant C verdict: BRAND-DEFINING MOMENT DELIVERED
**Source:** Daniel Round 8 (Day 14).
Variant C format LANDS. Daniel screenshotted to Hannah; hour-long discussion. Hannah said "pay it; this is the first AI thing you've used past Day 14 since I've known you." Daniel clicked 有意思. The brand-promise loop ("Rodix remembers your thinking" → felt experience) closed. **Document as canonical reference for first-insight in production.** Composition discipline (excluded grief, surfaced auditioning thread) is the model.

### POSITIVE — UX action button copy — POSITIVE Growth signal
**Source:** Daniel Round 8.
4 action buttons (`谢谢` / `存下了` / `下次再说` / `有意思`) read correctly. Daniel chose 有意思 (most-engaged), not 'thanks' or 'not now.' This is the "useful rate" signal the spec gates on (≥ 70%). Single-persona N=1 not validation, but positive directional signal.

### Growth-D1 — First-insight as conversion-determining moment
**Source:** Daniel Round 8.
This round's Variant C synthesis IS the make-or-break moment for Daniel's conversion. Hannah's recommendation to pay was triggered by the surfaced phrase. If real Haiku 4.5 doesn't produce this Variant C composition (or surfaces grief topics), Daniel doesn't get the brand-promised "Rodix remembers your thinking" moment, and Round 10 pricing churns him.
**Cross-link Mike Growth-2 (cross-topic synthesis as conversion-determining) / Sarah Growth-S1 (Round 8 → Round 9 → Round 21 trust-build chain) / Emma Growth-E2 (Day-15 handling as conversion gate).** Day-14-or-Day-15 events are the universal conversion gate across all 4 personas.
**Phase B HIGHEST PRIORITY.**

### Growth-D2 — Hannah-as-second-tester (cross-tier validation)
**Source:** Daniel Round 8.
Daniel showed the surfaced ⌘ card to Hannah. Hannah's reaction (positive, recommended payment) is the secondary-validation signal for the brand-promise. **Production implication:** real users will share surfaced insights with their partners/spouses/friends. The insight must be share-worthy on its own — not require context to make sense, not embarrassing or wrong-feeling. Variant C format passed this in self-sim. **First documented cross-tier validation event** — a non-user judging the AI's output positively. This is the word-of-mouth retention engine the brand depends on.
