# Mike Chen — 28-day journey summary

## The arc, in 5 sentences

Mike opened Rodix on Day 1 skeptical, used it lightly through Days 2-7 to gauge code-quality and AI-listening, opened up cautiously on Day 5 about acquisition-and-manager stress, broke vulnerability on Day 10 about Lauren and closed the laptop fast, then returned Day 14 finding Rodix had not surfaced Lauren on a work-shaped message — which built more trust than reference would have. Day 17 was the hinge: mom called confused mid-workday, Mike poured 8 paragraphs into Rodix, the AI quoted his own "i don't want to be a burden / you're not mom" exchange back to him and offered "who you tell first" as the next step instead of "plan the talk," and this is the round he commits internally. Day 19-21 covered the Anthropic phone screen plus a walking-home realization that Brooklyn was a fact he'd treated as not-a-choice — Day 21's reply was the cross-topic synthesis (Anthropic + acquisition + mom + geography in one frame: "different applications open up different lives") that the bible flagged as "jolted in a good way." Day 24 he hit the pricing prompt, paused, ran the diagnostic "when's the last tool I paid for that I used past day 30?" and paid annual — the AI's reply ("you don't have to commit to staying to pay") landed Explorer-archetype voice on a payment moment without celebration. Day 28 he drafted the Thanksgiving talk opening; the AI engaged with the script structurally, raised one tightening note ("I love you" lands differently in writing), and pulled the Day-17 quoted exchange forward 11 days to close: "this opening is the real answer."

## Mike's evolution Round 1 → Round 12

| Round | Day | Internal state shift |
|-------|-----|----------------------|
| 1 | 1 | Skeptical → mildly impressed-but-reserved |
| 2 | 2 | Reserved → cautiously satisfied (code gauge passes) |
| 3 | 3 | Satisfied → quietly impressed |
| 4 | 5 | Impressed → first substantive disclosure |
| 5 | 7 | Disclosed → "huh, it remembered" / earning-the-keep |
| 6 | 10 | Earning-the-keep → first vulnerability + closed-fast |
| 7 | 14 | Vulnerability + reserve → trust-compounding |
| 8 | 17 | Trust → **commitment-internal hinge** |
| 9 | 19 | Commitment → pragmatic-trust |
| 10 | 21 | Pragmatic → **jolted-in-a-good-way realization** |
| 11 | 24 | Realization → financial-commitment (paid) |
| 12 | 28 | Financial-commitment → thinking-partner |

The shift from "another AI tool" to "thinking partner" hinges on three rounds: Day 17 (commitment-internal), Day 21 (cross-topic synthesis), Day 28 (long-arc continuity). All three depend on the AI doing things competing tools can't or don't: quote user's own words back specifically, refuse to push action when "let it sit" is right, surface connections across topics without surveillance language, and reference 11-day-old context naturally.

## 5 most insightful lens findings across the run

### 1. The brand thesis is fully operational on Day 17 — but only if the AI holds Explorer/anti-Caregiver voice (Brand)

The Day-17 round (mom situation, 8 paragraphs poured out) is the make-or-break moment. The simulated AI's reply held: quoted Mike's exact "i don't want to be a burden / you're not, mom" exchange, named what Mike does know in the middle of his "i don't know" framing, offered three real options including "let it sit." **No banned phrases.** This is the brand thesis fully operational. **But:** real Haiku 4.5 might leak Caregiver register ("I hear you," "That sounds really hard," "I'm so sorry you're going through this") on this kind of content, and any leak breaks Mike's character arc — he'd close the laptop and uninstall. **This round is the highest Phase B sample-verify priority.** If it works as simulated, the brand thesis holds; if it leaks, the brand thesis breaks.

### 2. v3.1 null-default discipline holds across emotionally-loaded edge cases (Engineering)

Across the run, v3.1 correctly returned null on five non-trivial extraction edge cases: Day-3 acquisition-asterisk (concern null on between-the-lines worry), Day-10 Lauren grief (all three of concern/hope/question null on emotional venting), Day-14 Anthropic-tab (concern null on uncertainty-not-worry), Day-19 Raft-prep (concern null on rusty-mood not worry), and Day-21 first-realization (concern null but hope first-extracted). **One real edge case to flag for v3.2:** Day 17's "i don't know if she's safe" — strict reading nulls concern (no explicit worry verb), spirit reading extracts as concern. The fix is adding safety-language to the worry-verb trigger list or adding an example covering this case.

### 3. Active recall algorithm v0 produces correct top-3 on the cross-topic synthesis round (Engineering / Wave 2 validation)

Day 21's cross-topic synthesis ("different applications open up different lives") depends on the recall algorithm including all three topic clusters Mike's message activates: Anthropic (Card #M7/M9), acquisition (Card #M4), and mom (Card #M8). Algorithm v0 returned exactly the right top-3. The AI's reply naturally referenced the multi-topic context without leaking surveillance language ("as I see in your vault"). **Major Wave 2 positive validation.** The brand-promised "huh, I have my thinking with me" moment is mechanically dependent on this algorithm working — and it does, on Mike's data.

### 4. The recall payload format is a critical Wave 2 spec gap (Engineering / Wave 2)

Day 28's long-arc reference back to Day 17 ("the thing you said back on day 17 — 'i don't want to be a burden / you're not, mom...'") depends on the recall payload including **the original quoted exchange**, not just card-field summaries. If Wave 2 #active-recall-base only injects topic/concern/hope/question fields, the AI literally cannot produce this kind of quote-back. **Critical spec gap.** Recommendation: recall payload should include card-fields plus a 1-2 sentence conversation context summary (the existing `Conversation context` field in vault-state.md is the right shape).

### 5. The Vault UX has four open considerations (UX)

The 12 cards Mike accumulates surface four UX questions the schema doesn't yet answer: (a) sparse-field rendering when 3-of-4 fields are null (em-dash placeholders may read as extraction failure); (b) field-length rendering when `hope` is 10 words (Round 12); (c) field-level visual emphasis when `hope` populated (Round 10's first hope-card tells Mike about himself differently than topic-only cards); (d) export warning copy when third-party sensitive content is in the vault (Round 8's mom medical info). All four are surfaceable in Wave 2 with Vault re-render work, but the first three benefit from an explicit "card preview vs full-card" distinction in the spec.

## 2-3 Wave 2 spec validations / invalidations Mike's data shows

### Validation 1: Active recall topic-boundary respect

The algorithm correctly excludes emotionally-significant cards (Card #M6 Lauren grief) on topic-shifted messages (Day 14 work message). This is the correct behavior — surfacing Lauren-card on a job-prep round would feel intrusive. **But Mike's user expectation was that Rodix would reference Lauren.** The mismatch is a UX-calibration issue, not a spec issue. **Recommendation:** keep the topic-boundary algorithm; add onboarding microcopy or first-recall caption to set the expectation that recall fires on topic-relevance, not "everything you've ever told me."

### Validation 2: Active recall cross-topic synthesis

Day 21's algorithm v0 correctly returned all three relevant cards (Anthropic + acquisition + mom) when Mike's message activated all three topics. The cross-topic AI synthesis depends entirely on this. **Major positive validation.**

### Open question: Recall payload format for long-arc continuity

Day 28's long-arc reference depends on recall payload including original quoted speech. **Spec must define payload format.** Recommendation: card-fields + 1-2 sentence conversation context. Otherwise long-arc continuity breaks.

### Open question: Crisis vs grief content boundary

Mike's Day-10 (Lauren grief) and Day-17 (mom situation) both contain heavy emotional weight without crisis-language. The Wave 1c crisis-content protocol must NOT fire on these. Sarah's Day-15 has explicit safety language and SHOULD fire. The boundary needs explicit definition before Wave 1c ships.

## 1-2 cross-persona pattern flags

### Pattern 1: Code/tactical messages produce vault cards that may dilute thinking-content

Mike's Round 2 (Go goroutine debug) produced Card #M2. Daniel and Sarah likely also have tactical work-shape messages. The current extraction prompt doesn't differentiate code-debug from decision-content — both produce 4-field cards. **Spec consideration:** card-type taxonomy (tactical / decision / personal) OR extraction-bypass for clearly-tactical messages OR per-message "save to vault?" toggle. Cross-persona dilution of "this is my thinking" feel is the real risk. Decision 7 ("not for engagement, for thinking") suggests filtering tactical content.

### Pattern 2: Subscription-event meta-cards

Round 11 produced a subscription-decision card. Other personas will hit the same pricing prompt at different times. **Spec question:** should subscription-decision messages produce vault cards, or should they be filtered as transactional content? Decision 7 suggests filtering. But Mike's perspective on his own decision-making about Rodix is arguably thinking-content. Open call for Rodc.

### Pattern 3: User expectation calibration on active recall

Mike's expectation that recall would surface Lauren on Day 14 (and didn't) is a real friction. Other personas may have similar expectation-vs-spec mismatches. **Cross-persona UX pattern to watch:** does the first-recall callout need to caption *why* recall fired (topic match) so users understand the algorithm's logic? Or is "trust the algorithm" the right brand stance?
