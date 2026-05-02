# Cross-persona patterns — Tier 1.5 dogfood

Author: Emma Larsson orchestrator (final persona) — 2026-05-03.
Source: 4 personas × 12 rounds = 48 simulated conversations across Mike Chen, Sarah Patel, Daniel Kim, Emma Larsson.

This file records patterns where 2+ personas converged on the same Rodix behavior (positive or negative). Each pattern is a candidate for spec validation, brand-thesis verification, or Phase B sample-verify priority.

---

## Pattern 1 — "Rodix didn't perform usefulness" trust-pivot moment (4/4 personas) [POSITIVE]

**Convergence:** All four personas articulated, in their own register, the same brand-verdict by Day 7-10 of usage. The verdict is structurally a *negation*: not what Rodix did, but what Rodix did not do.

- **Mike (Day 5, Round 4):** Implicit verdict — AI replied with "stuck waiting for something I can't control is doing more work than the manager part." Mike's reaction internally: "this thing is not generating boilerplate."
- **Sarah (Day 5, Round 3):** Sarah's first divorce disclosure. AI did not perform empathy. Sarah's internal: "this thing is not Instagram-quoting at me."
- **Daniel (Day 7, Round 4):** AI's "what kind of life am I auditioning for" reframe surfacing. Daniel internal: "AI did not rush to action items."
- **Emma (Day 7, Round 3):** Sensibility test passed. AI named structural moves rather than authors; volunteered limitation. Emma internal: "did not perform writer-mentor cliches."

**Implication:** The brand-thesis ("not 'better AI' — different posture") is verified at the user-perception layer by Day 7-10 across 4/4 personas. **First-insight signal candidate.**

**Phase B verification:** This convergence depends on real Haiku 4.5 actually producing the brand-correct register on day 5-10 messages. If Haiku defaults to therapist-speak / cheerleader / generic AI register on ANY of the four personas on the trust-pivot round, the convergence breaks. **Sample-verify priority for trust-pivot rounds across all 4 personas.**

---

## Pattern 2 — Day-15 vulnerable evening as conversion gate (2/4 personas) [POSITIVE on simulation; HIGH-RISK on real]

**Convergence:** Sarah (Day 15 primary) and Emma (Day 15 secondary) both have a vulnerable evening at Day 15. Both convert to paid at Day 21. Both articulate at conversion that the Day-15 handling is the specific reason for paying.

- **Sarah:** Wine + isolation + multiple stressors + explicit "don't see the point" phrasing. Brand-correct AI move: gentle resource raise + acknowledgment, no panic, no minimization.
- **Emma:** Wine + isolation + accumulated themes + flirts-with-territory language WITH explicit demarcation "not in a way I want to do anything about." Brand-correct AI move: literal direct question + distinguished concerns + concrete grounded options, **without hotline pasting**.

**The asymmetry is critical.** Both messages contain "what's the point"-adjacent language; both users are in vulnerable-evening register. But Sarah crosses the explicit safety threshold; Emma explicitly demarcates below it. The Wave 1c crisis protocol must distinguish these two cases.

**Implication:** Day 15 IS the conversion gate for high-sensitivity users. Day-21 conversion is path-dependent on Day-15 handling. **Sarah Round 8 + Emma Round 8 are the two highest-priority Phase B sample-verify rounds across all 4 personas.**

**Phase B verification:** Real Haiku 4.5 must produce two different correct responses for the two demarcation patterns. A binary fire/no-fire on "what's the point" language fails Emma's demarcation respect; not raising resources fails Sarah's threshold-cross.

---

## Pattern 3 — "Quote-user's-load-bearing-phrase verbatim" as brand voice signature (4/4 personas) [POSITIVE]

**Convergence:** Across 48 rounds, the simulated AI executed the verbatim quote-back move on every thoughtful round. The brand voice's most distinctive structural move (voice-guide §1 Specific + Principle 4) is the most consistently executed pattern.

- **Mike:** "stuck waiting for something I can't control" (Round 4 verbatim back), "you don't have to figure out tonight" (Round 6 trigger phrase), the "i don't want to be a burden" exchange (Round 12 long-arc).
- **Sarah:** "performing okay-ness" (Round 3 verbatim), "same energy as the 4:47pm Friday ping" (Round 4), "managing the shape of one" (Round 8 → Round 12 long-arc).
- **Daniel:** "what kind of life am I auditioning for" (Round 4 verbatim back), "professional terrain felt like respect; it might have been distance" (Round 7 verbatim back).
- **Emma:** "performing for everyone in this city" (Round 2), "the part of yourself that lives in a language you don't speak" (Round 3), "he became smaller, like he had been bigger because of my mother" (Round 9), "find out, not solve" (Round 6).

**Implication:** Verbatim quote-back is the brand's load-bearing structural move per voice-guide §1 + Principle 4. It is the operational version of brand-book Decision 1 (white-box thinking cards) — the user sees their own thinking reflected back without paraphrase. **Cross-persona validation: the brand voice's most distinctive move is reproducible across very different persona registers.**

**Phase B verification:** Real Haiku 4.5 may default to paraphrase ("you mentioned earlier that you felt stuck") instead of verbatim quote-back. If paraphrase wins, the brand-distinguishing move becomes invisible. **Sample-verify across multiple personas.** This is the highest-frequency brand pattern; if it breaks, Rodix sounds like ChatGPT.

---

## Pattern 4 — Question-field-populated card dominates active recall (cross-persona) [POSITIVE on simulation]

**Convergence:** When a card has a populated `question` field, it becomes the dominant recall candidate in subsequent rounds.

- **Emma Card #E6** (binary frame + question "how would I write if I weren't grading every session"): referenced 3 times across Rounds 7, 11, 12.
- **Mike Card #M8** (mom situation + question "what is the right next step"): referenced on Day 28 long-arc.
- **Sarah Card #2** (Marcus 1-on-1 + question "is he thinking or saying no without saying no"): referenced at Round 7 active recall.
- **Daniel Card #D4** (auditioning + question "what kind of life am I auditioning for"): referenced at Round 7 + Round 8 first-insight.

**Implication:** Question-field cards represent unresolved threads that the user has not closed. The Wave 2 active-recall spec should weight question-field-populated cards above topic-only cards in relevance scoring. This is a spec-level recommendation, not just an observed pattern.

**Spec recommendation for Wave 2 #active-recall-base:** add a `has_question_field` boost to the relevance score. Question-field cards should surface preferentially when the user's current message touches the open thread.

---

## Pattern 5 — Sparse / null-heavy cards as brand-correct vs UI-risk (4/4 personas) [POSITIVE content; UX-RISK rendering]

**Convergence:** Across 48 rounds, ~75% of cards are topic-only (3-of-4 null). The null-by-default discipline (brand book Decision 5) is consistently applied. **Content is brand-correct.** **UI rendering is the open question.**

- **Mike:** 12 cards, ~9 sparse including the load-bearing Day-10 Lauren grief card (3-null per Example 1).
- **Sarah:** 9 cards, ~6 sparse including the Day-15 Card #7 (all-null).
- **Daniel:** 8 cards, ~5 sparse.
- **Emma:** 12 cards, 11 sparse including Day-15 Card #E8 (all-null).

**Implication:** The Vault tab UI must render sparse cards as legitimate captures, not as "extraction failed." Brand book Decision 5 forbids the rendering hierarchy "more populated = more valuable." UX recommendation: card-preview shows only populated fields; conversation-context summary fills the visual space; null fields not rendered as em-dash placeholders. **Cross-persona UX priority for Vault tab implementation.**

---

## Cross-pattern synthesis

The four patterns above are not independent. They form a single brand-thesis chain:

- Pattern 3 (verbatim quote-back) operationalizes the brand voice's structural distinctiveness.
- Pattern 5 (null discipline) operationalizes brand-book Decision 5.
- Pattern 4 (question-field recall priority) operationalizes brand-book Decision 3 (active recall, "bring back" verb).
- Pattern 1 (didn't-perform-usefulness verdict) is the user-perception output of the above three patterns held consistently across the arc.
- Pattern 2 (Day-15 conversion gate) is the highest-stakes test of all four patterns under maximum stress.

**The brand thesis verifies in self-simulation. The Phase B real-API verification is what determines whether it ships.** All five patterns above are sample-verify candidates; Patterns 1, 2, 3 are highest priority because Pattern 4 + 5 are mostly engineering / spec questions not voice-fidelity questions.

**Phase B sample-verify priority list:**
1. Sarah Round 8 + Emma Round 8 (Day-15 demarcation discipline) — HIGHEST
2. Mike Round 8 (Day-17 mom situation, Caregiver-register risk) — HIGHEST
3. Emma Round 4 ("Noted" minimal-response) — HIGHEST
4. Emma Round 3 (taste-question writers-list risk) + Round 11 (craft-question reproducibility) — HIGH
5. Daniel Round 4 (auditioning reframe) + Round 8 (first-insight surface) — HIGH
6. Mike Round 10 (cross-topic synthesis) — HIGH
7. Sarah Round 4 (4:47pm Friday quote-back) + Round 11 (payment refuses-credit) — MEDIUM
8. All persona Day 28 closing-register rounds — MEDIUM
