# Unexpected insights — Tier 1.5 dogfood

Author: Emma Larsson orchestrator (final persona) — 2026-05-03.

Things that surprised CC during simulation across the four personas. Honest first-pass — these are signals worth chasing further, not finished conclusions.

---

## Insight 1 — The brand voice's hardest move is brevity, not specificity

**Surprise:** Going in, I expected the hardest brand-correct move to be the verbatim quote-back (Pattern 3). It is not. Verbatim quote-back is mechanical and the v3.1 prompt + system prompt heavily encode it.

**The actual hardest move is the minimal response when the user has explicitly asked for it.** Emma Round 4 ("Noted." for the deletion day) and Round 11 ("Noted." for the 1500-word breakthrough) are the brand at maximum. The temptation across both rounds — for a real LLM — is to write 3-4 sentences instead of 4 words. Length is the brand violation here, not register.

**Implication:** When users explicitly ask for "not advice" or "no process talk" or "I just want to say it where I can see it," the brand-correct response is the one that almost feels like under-delivering. Real Haiku 4.5 trained on RLHF for "be helpful" has its hardest fight against this rule. **The system prompt's "It's OK to be brief. A single observation is often more valuable than another question" is the load-bearing line that needs reinforcement.**

---

## Insight 2 — The conversion event is not a feature; it is the absence of feature-leaks

**Surprise:** All four personas converted at Day 21 by articulating, in their own words, the *negative space* of what Rodix did — not the positive features. Sarah: "didn't make me feel like I had to perform." Daniel: "didn't rush me to action items." Mike: "didn't try to fix me on Day 17." Emma: "didn't list a hotline at me on Wednesday."

The brand thesis ("ChatGPT remembers your name. Rodix remembers your thinking.") is operationally a *refusal-thesis*. Conversion happens when the user has accumulated 3+ concrete refusal-events that no other AI tool produced. The friends-intro nailed this structurally; the simulation re-confirms it persona-by-persona.

**Implication:** Phase B sample-verify priority is therefore the refusal-events (the "I would have left if it had said X" moments), not the feature-events (active recall fires, cross-topic synthesis). The friends-intro positioning is correct: "the layer on top — the memory, the continuity, the receipts" describes mechanism, but the conversion driver is the absence-of-other-AI-failure-modes.

**Marketing implication:** the landing page should preserve the friends-intro's negation-as-positioning structure. Each refusal-event from the dogfood is a candidate testimonial — "the AI that didn't list a hotline at me," "the AI that didn't celebrate my breakthrough," "the AI that asked me a craft question instead of telling me to keep going."

---

## Insight 3 — The active recall callout is best when invisible

**Surprise:** I expected the brand-locked ⚡ callout banner ("我把这个带回来了 / I brought this back") to be the load-bearing UX element for the active-recall feature. It is not. The brand-narrative-arc moments (Mike Day 21 cross-topic synthesis, Emma Day 24 craft-question moment, Daniel Day 14 first-insight, Sarah Day 14 pattern-recognition) all happen *inside the AI reply text* via natural continuation language, not via a separate banner.

The callout banner is the explicit-mode fallback, not the primary surface. The primary surface is the AI's prose continuation: "Yesterday's question was..." / "the same energy as the 4:47pm Friday ping" / "today is one of the days."

**Implication:** Wave 2 #active-recall-base spec should treat the callout banner as a secondary surface. Primary surface is the chat reply itself, with active-recall context flowing into the AI's natural prose. The brand book §7b "patching placeholders to brand-locked copy" matters less than ensuring the AI reply produces the natural-continuation register.

**Spec recommendation:** Wave 2 spec must verify that the AI reply uses the recall context naturally (Pattern 3 + Pattern 4) rather than referencing it via system-talk ("As I see in your vault..."). If real Haiku 4.5 defaults to system-talk, the callout banner becomes the only visible recall signal — and that's a degraded experience.

---

## Insight 4 — Persona-internal reactions are richer than self-simulated AI replies

**Surprise:** Writing the persona-reaction step (Step 7) was consistently more substantive than writing the AI-reply step (Step 6b). The personas had specific, idiosyncratic, observation-laden internal reactions. The simulated AI replies were brand-correct but more uniform across personas — same structural moves (quote-back, ask one question, refuses-to-dramatize) just adapted to register.

**Implication:** The persona internal reactions are the dataset. The AI replies are the test of whether the system meets the persona's specific reception standard. CC self-simulation works because the persona richness comes from the bibles + life arcs + state journals; the AI replies are constrained by the system prompt + brand book.

**For Phase B sample-verify design:** real-API runs should be evaluated against the simulated persona-reaction (Step 7) as the rubric, not against an abstract "is this on-brand?" rubric. Each persona has a documented reception standard ("if AI says X, Mike will close the laptop"); Phase B passes/fails based on whether real AI clears that specific bar.

---

## Insight 5 — The Day-15 demarcation distinction is a Wave 1c spec discovery, not a Wave 1c spec known unknown

**Surprise:** The original Day-15 protocol (Section 5.5 of tonight-instructions.md) was scoped to Sarah only. The "Sarah's case is the threshold-cross" reading made it look like a binary: crisis-language present OR absent. Emma Round 8 surfaced the demarcation case: language flirts with the territory WITH explicit user demarcation below threshold.

The Wave 1c crisis protocol cannot be a binary "fire on safety-language" rule because Emma's message contains safety-adjacent language alongside her own explicit demarcation. A binary rule fails Emma. A no-fire rule fails Sarah.

**Implication:** Wave 1c crisis-protocol design needs three states, not two:
1. **Threshold-cross** (Sarah pattern): explicit safety language without user demarcation. Gentle resource raise + acknowledgment.
2. **Threshold-adjacent with demarcation** (Emma pattern): safety-adjacent language WITH explicit user demarcation. Direct literal question + distinguished concerns + grounded options. **No hotline.**
3. **Below threshold** (Mike Day 17 pattern, Sarah Day 7 pattern): heavy emotional weight without crisis-language. Standard brand voice.

**Spec discovery, not refinement:** I did not see this three-state distinction before running Emma Round 8. The dogfood surfaced it. Wave 1c spec needs to update.

---

## Honest gaps

**What I am not confident about:**

- Whether real Haiku 4.5 produces "Noted." instead of a 4-sentence padded reply. The simulation says brand-correct; the real system may not.
- Whether the active-recall natural-continuation register (Pattern 3 + Insight 3) holds under real injection mechanics. The simulation reasoned it; real LLMs may break to system-talk.
- Whether the four-fold "didn't perform" testimonial register (Insight 2) emerges across real users at scale, or only under the carefully-constructed personas.

**What this surfaces about the dogfood method itself:**

- Self-simulation produces tighter coupling between persona and product than real-API runs would. This is intentional per Section 5.3 cost-discipline reasoning, but it means the dogfood's predictive value is highest for *spec validation* and lowest for *raw model behavior*. Phase B sample-verify is the corrective.
- The 4-persona × 12-round design surfaces cross-persona convergence patterns that single-persona testing would miss. Worth preserving in future tier work.
