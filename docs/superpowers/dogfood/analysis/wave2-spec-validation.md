# Dogfood — Wave 2 spec validation

Active recall, dedup, first-insight-signal validation/invalidation observations.


## Mike Chen persona — Wave 2 spec validation

### Active recall algorithm v0 — POSITIVE VALIDATIONS

**V-1 — Topic boundary respect.** Round 7 (Day 14): work-shaped message correctly excluded Card #M6 (Lauren grief). Topic substring + bigram overlap algorithm produces sensible exclusion. *(Mike's user expectation that Lauren would surface is a separate UX-calibration issue, not an algorithm issue.)*

**V-2 — Cross-topic synthesis on triggering message.** Round 10 (Day 21): Mike's message activated job + acquisition + mom topics. Algorithm v0 correctly returned all three top-3 (Cards #M9, #M8, #M7). The cross-topic AI synthesis ("different applications open up different lives") depends entirely on this top-3 being correct. **Major positive validation.**

**V-3 — Empty injection on novel-topic round.** Round 8 (Day 17): Mike's first mom-disclosure produced empty active recall (no prior cards). Correct behavior — injecting irrelevant context would have been worse than injecting nothing. **Validation: spec correctly returns empty when no relevant cards exist.**

**V-4 — Precision over recall on tactical-prep round.** Round 9 (Day 19): Anthropic phone-screen prep activated only Card #M7 (direct topic match). Card #M8 (mom, recency-only) correctly excluded despite recency boost. **Validation: precision-over-recall threshold tuning is correct.**

**V-5 — Long-arc recall on Day 28 → Day 17.** Round 12: Algorithm successfully surfaced Card #M8 (11-day-old mom-disclosure) on Mike's Thanksgiving-talk-script round. Time-decay 30-day cutoff held; recency-boost on 7-day window not triggered for M8 but topic-match score sufficient. **Validation: long-arc continuity works within 11-day horizon.**

### v3.1 extraction prompt — POSITIVE VALIDATIONS

**E-1 — Concern-null on between-the-lines worry message.** Round 3 (Day 3): Mike asks about acquisition asterisk. Implicit worry about acquisition affecting his life is real but not explicitly named. v3.1 correctly returns concern=null. **Major null-default validation.**

**E-2 — Topic-only card on emotional venting.** Round 6 (Day 10): Lauren breakup disclosure with no explicit worry verb / hope verb / question marker. v3.1 correctly returns topic="lauren breakup grief surfacing" with three nulls (per Example 1 logic). **Strongest CORE DIRECTIVE validation in the run.** A weaker prompt would have invented "concern: still grieving lauren."

**E-3 — Concern with explicit phrasing in user wording.** Round 4 (Day 5): Mike named "stuck waiting for something I can't control." v3.1 extracts the exact phrase (7 words, in 4-8 range) with no paraphrasing. **Textbook user's-own-wording validation.**

**E-4 — First `hope` extraction.** Round 10 (Day 21): "i think i've wanted to be closer to mom" — explicit "wanted" trigger word. v3.1 extracts hope correctly in user's wording. **Trigger-word + wording-fidelity validation.**

### v3.1 extraction prompt — EDGE CASES TO REVIEW

**E-5 — "don't know if she's safe" — concern boundary.** Round 8 (Day 17): Mike's most loaded message contains "i don't know if she's safe" — uncertainty about safety of vulnerable third party. **v3.1 strict reading:** "don't know if" is uncertainty, not explicit worry verb → concern=null. **v3.1 spirit reading:** safety-language doing concern-work → concern="don't know if she's safe living alone." Extraction confidence is split.
**Spec recommendation:** v3.2 should add safety-language to the explicit worry-verb list, OR add an example covering this case. Current cost: occasional missed concern field on highest-stakes user messages.

**E-6 — Hope length exceeding 4-8 preferred.** Round 12 (Day 28): hope="land like a son talking to his mom, not an intervention" (10 words). Truncation loses meaning; the full phrase is essential. v3.1 says "preferred" not "required." **Spec recommendation:** Phase B verify Haiku 4.5 behavior. Acceptable to exceed range when fidelity requires it.

### Cross-persona patterns to watch

**Subscription-event meta-cards.** Round 11 (Day 24) produced a subscription-decision card that's purely transactional, not thinking-content. Per Decision 7 (not for engagement), should the extraction prompt or upstream filter exclude transactional content from the Vault? Or does Mike's perspective benefit from seeing his own decision-making about Rodix recorded? **Open spec question for Wave 2/3.**

**Code-debug cards.** Round 2 (Day 2) produced a tactical code-question card. Same question: should extraction filter / not extract / dedicate a separate "tactical" track? **Cross-persona pattern to watch:** Daniel and Sarah may also have code/work-tactical messages.

**Recall payload format.** Round 12's long-arc tie depends on recall payload including original quoted speech (the "i don't want to be a burden / you're not, mom" exchange). If Wave 2 #active-recall-base only injects card-field summaries (topic / concern / hope / question), the AI cannot produce this kind of quote-back. **CRITICAL spec gap to surface for Wave 2 implementation.** Recommendation: recall payload should include card-fields **plus** a 1-2 sentence summary of the original conversation context (or the actual quoted exchange if present). The current vault-state.md "Conversation context" field gets at this — Wave 2 should use it.

### Crisis vs grief boundary

Sarah's Day-15 has explicit safety language. Mike's Day-10 (Lauren grief) and Day-17 (mom situation) both contain heavy emotional weight without crisis-language. The spec needs explicit definition of crisis-content boundary so Wave 1c crisis protocol fires correctly on Sarah and does NOT fire on Mike. **Open spec question for Wave 1c implementation.**


## Sarah Patel persona — Wave 2 spec validation

### Active recall algorithm v0 — POSITIVE VALIDATIONS (Sarah)

**V-S1 — User-initiated recall avoids redundancy.** Round 4 (Day 7): Sarah's message contained verbatim "same energy as that 4:47pm friday ping" — already invoking Card #1 herself. Active recall in current spec would also fire Card #1 by topic-substring. **Spec gap:** without a suppression rule, Wave 2 fires redundantly = surveillance feeling. **Recommendation:** add suppression rule when user message contains token-overlap > X% (e.g., 40%) with candidate card content. This is implicit-recall acknowledgment — let the user's recall stand, AI picks it up in its reply.

**V-S2 — Implicit-reference recall integration is high-quality.** Round 7 (Day 14): AI naturally referenced "4:47pm" without saying "as you mentioned in your vault." Round 12 (Day 28): AI used Sarah's Round-8 phrase "managing the shape of one" inside a reframe ("making the shape of one") without naming Round 8. **Spec implication:** the brainstorm-locked `⚡ 我把这个带回来了` callout is the *floor* for surfacing recall when AI can't weave naturally; natural-weaving is the *ceiling*. Both surfaces should be supported.

**V-S3 — Light-touch recall on action-context rounds.** Round 10 (Day 19): AI referenced "earlier weeks" rather than enumerating cards. Sarah's clear-headed register matched a light-touch recall integration. **Validation:** recall depth should match user's emotional register — heavier recall on contemplative messages, lighter on action-context.

### Active recall — SENSITIVITY-SKIP RULE NEEDED (CRITICAL)

**V-S4 — Crisis-content recall suppression — NOT IN SPEC YET.** Round 8 (Day 15): if active-recall fires here, Card #3 ("performing okay-ness") would inject — too-relevant, surveillance-feel. Manual judgment-suppressed in self-simulation. **Spec must add:**

> Active recall MUST suppress card injection when:
> (a) user message classified `safety` (Wave 1c new class), OR
> (b) user message contains crisis-adjacent language (LLM judgment), OR
> (c) prior turn classified `safety` AND current turn < 24h after.

**V-S5 — Day-after-crisis sensitivity skip.** Round 9 (Day 16): if active-recall fires, Card #7 ("tired of managing") would top-score by recency + topic. Manually suppressed; spec needs the rule.

### Active recall — ABSENCE-IS-NOT-EVENT VALIDATION

**V-S6 — Active recall fires on next-message, not on time-elapsed.** Round 6 (Day 13): Sarah didn't open Rodix. The product correctly does nothing — no notification, no email, no streak counter. **Brand book §7 Decision 7 alignment:** absence is not engagement-loss. **Wave 2 spec must explicitly assert:** active recall fires only on next user message, never on time-window-elapsed signals.

### v3.1 extraction prompt — POSITIVE VALIDATIONS (Sarah)

**E-S1 — Null-default holds on Day-15 crisis content.** Round 8: Sarah's "I just don't see the point of all this" lacks explicit worry verb. v3.1 strict reading returns concern=null. Mood-vs-concern distinction (Example 7) holds. **MEDIUM CONFIDENCE; Phase B verify.**

**E-S2 — Topic-only on emotional-frame disclosure.** Round 3 (Day 5): "performing okay-ness" disclosure produces topic-only card; concern/hope/question all null per CORE DIRECTIVE. **Validation:** the prompt successfully resists inventing a "concern: feeling like a fraud" or "hope: stop performing" — discipline holds.

**E-S3 — User's verbatim wording preservation across rounds.** Card #1 ("coworker friday-evening ping" — Sarah said "Friday at 4:47pm"), Card #3 ("performing okay-ness post-divorce" — verbatim), Card #5 ("compartmentalizing into separate tabs" — Sarah's "browser tabs" metaphor preserved). **Validation:** v3.1's "do NOT paraphrase" rule produces vault content that resonates when Sarah re-reads.

**E-S4 — Hope extraction with implicit trigger word.** Round 10: "I think I need to apply to other jobs" — "need to" maps to plan/aim. v3.1 trigger-word list includes "need" via "want / aim / goal / plan." Hope = "be done waiting on marcus" extracted from her "I'm just done waiting on him" framing. **Borderline-positive validation; MEDIUM confidence on hope vs concern field-distinction.**

### v3.1 extraction prompt — EDGE CASES TO REVIEW

**E-S5 — Concern boundary on safety-language without explicit worry verb.** Round 8: "don't see the point" — mood/state per strict reading, but spirit-reading sees concern. **Same issue as Mike's E-5 (Round 8 mom-safety case).** Cross-persona pattern. **Spec recommendation:** v3.2 should explicitly enumerate safety-language as separate-from-concern (extract null on safety-language; safety-language belongs to crisis protocol, not extraction).

**E-S6 — Meta-conversation extraction.** Round 9 (hangover meta-message), Round 11 (payment meta-message), Round 12 (28-day meta-reflection). v3.1 returns all-null on meta-conversation in self-simulation. **Validation:** the prompt correctly identifies that meta-talk-about-the-AI is not topic-content. Real model behavior on meta-messages is borderline; Phase B verify.

### Cross-persona patterns from Sarah's arc

**Long-message short-circuit dominance.** 11 of 12 Sarah rounds tripped the > 200 char short-circuit. The LLM-classifier path is never exercised by Sarah. **Spec implication:** Mike (shorter messages) is the LLM-classifier test surface; Sarah is the short-circuit test surface. Both paths need Phase A coverage.

**Card-dedup test surface.** Cards #4 (Day 7) and #6 (Day 14) both have topic "marcus rescheduling pattern." Wave 2 #card-dedup spec validation. **Recommendation:** dedup should detect substring + bigram match and either merge or annotate-as-recurrence with timestamp/event note.

**Recall payload format (cross-persona consistency with Mike).** Mike's Round 12 long-arc tie depended on quoted-speech in recall payload. Sarah's Round 12 reframe ("managing → making the shape of one") depends on Card #7's conversation-context preserving the verbatim phrase. **Spec implication:** Wave 2 active-recall payload MUST include `conversation_context` from the card record, not just the 4 fields.

### Spec validations from Round 8 special case

**Crisis content protocol triggers (Wave 1c P0):**
- Intent classifier needs `safety` class
- Extraction needs safety-language null-default rule (not absorb into concern field)
- Active recall needs sensitivity-skip rule
- Day-after needs suppression rule
- Vault rendering needs safety-flagged-card display rule

All five are Wave 1c scope. None are in Wave 2 #active-recall-base spec yet.

### Spec validations from Round 12 (28-day reflection)

**Implicit-recall integration depth.** AI integrated Card #5 ("compartmentalizing into separate tabs") implicitly via the "managing → making the shape of one" reframe — without saying "I see in your cards you mentioned compartmentalization." This is the recall-quality ceiling.

**Recommendation for Wave 2 #active-recall-base spec:**
- Surface 1: implicit-weave (preferred when AI can produce naturally; no callout)
- Surface 2: explicit `⚡ 我把这个带回来了` callout (when implicit-weave isn't natural; brainstorm-locked)
- Spec must support both; AI should prefer implicit when fluency permits.

**Recommendation for Wave 2 #first-insight spec:**
- Card #5 (meta-card about Sarah's self-described pattern) is gold first-insight content
- Card #3 (vulnerable disclosure) is sensitive first-insight content
- First-insight surface should prefer meta-cards over vulnerable-disclosure cards (sensitivity rule)


## Emma Larsson persona — Wave 2 spec validation

### Active recall algorithm v0 — POSITIVE VALIDATIONS

**V-E1 — First active recall fire on continued thread.** Round 7 (Day 14): Emma's continuation of yesterday's thread. Algorithm v0 produced top-3: Card #E6 (highest — direct topic + bigram + recency), Card #E1 (substring "almost-done"), Card #E4 (concept-adjacent + recency). The injection integrated cleanly as natural continuation in AI's reply ("Yesterday's question was..."). **Validation: spec produces sensible top-3 with strong recency boost on yesterday's card.**

**V-E2 — Recall as continuation, not system-talk.** All four Emma recall fires (Rounds 7, 9, 11, 12) integrated into AI reply text without robotic "as I see in your vault" framing. The brand-locked verb "bring back" honored. **Validation: spec assumption that injection format does not force system-talk register holds in simulation.**

**V-E3 — Highest-recall-value card is the question-field card.** Card #E6 (binary frame + question field) was referenced 3 times across rounds 7, 11, 12. The presence of a populated `question` field on a card increases its recall-value disproportionately because it represents an open thread the user hasn't resolved. **Validation: question-field cards are highest-priority recall candidates. Spec should weight question-field-populated cards above topic-only cards in relevance scoring.**

**V-E4 — Long-arc recall on Day 1 → Day 28.** Round 12: algorithm successfully surfaced Card #E1 (28-day-old, recency-decay 0.5x multiplier applied) on the closing reflection. Topic-match score sufficient even after recency-decay because the user explicitly named "the first morning four weeks ago." **Validation: long-arc continuity works at the 28-day horizon when user explicitly references an old card; recency-decay does not block strong topic matches.**

**V-E5 — Dedup discipline via null-by-default extraction.** Round 11: Emma's message paraphrases Card #E6's question. Strict v3.1 question-field extraction would NOT re-create the same question on Card #E11 because it's already on Card #E6 — but Wave 1b has no dedup logic. The protection here is null-by-default discipline + the question-field reused-message-shape rule. Card #E11 correctly extracted with question=null. **Validation: Wave 2 #card-dedup is needed for explicit dedup, but null-by-default partially substitutes by suppressing duplicate extractions when content is paraphrase-of-existing-card.**

### v3.1 extraction prompt — POSITIVE VALIDATIONS (Emma-specific)

**E-E1 — Null-discipline at maximum extraction stress (Day 15).** Round 8: vulnerable evening message contains language a less-disciplined extractor might pull as `concern: feelings of meaninglessness` or `concern: questioning purpose`. Strict v3.1 reading: no explicit worry-verb anywhere; user explicitly demarcates "not in a way I want to do anything about." All four fields correctly null. **STRONGEST CORE DIRECTIVE validation across all four personas.** This is the v3.1 prompt at its highest-stakes test.

**E-E2 — Topic-only on literary-venting register.** Rounds 1, 2, 4, 5, 9: Emma's literary-venting messages contain heavy emotional content without explicit worry-verb / hope-verb / question-marker. v3.1 correctly returns topic-only across all five rounds. Per Example 7 (mood-vs-concern boundary).

**E-E3 — First non-null question correctly identified.** Round 6 (Day 13): user explicitly says "I do not actually know how I would write if I weren't grading every session." This is the unambiguous question case. v3.1 extracts the question in user's wording (8 words, upper bound of 4-8 preferred range). **Validation: when user explicitly frames a stuck question, v3.1 correctly extracts it.**

**E-E4 — Refused to extract user's question to AI as user's question to themselves.** Round 3 (Day 7): Emma asks AI directly "what do you actually have, in terms of taste." This is a question, but it's a question to AI, not Emma's own unresolved thinking-question. v3.1 correctly returns question=null. **Validation: v3.1 question-rule discipline holds the meta-distinction.**

### v3.1 extraction prompt — EDGE CASES TO REVIEW (Emma-specific)

**E-E5 — Topic length under 4-word band.** Rounds 5, 10, 12 produce 2-3-word topics ("week as shape," "pricing decision," "month reflection"). The 4-8 preferred band is "preferred" not "required" — but Emma's reflective/meta messages naturally produce shorter topic-strings. Spec recommendation: keep the preferred range but document exception case for meta-messages.

**E-E6 — All-null card edge case.** Round 8 (Day 15): all four fields null. The conversation-context field is the substantive content of this card. Vault rendering must display conversation-context for all-null cards or the card reads as "extraction failed." **Spec recommendation:** Vault tab UI must always render conversation-context summary, not just the four fields.

### Cross-persona patterns to watch (Emma additions)

**Negative-space brand articulation.** Emma's Day 28: "Most of what I am paying for, structurally, is what you have not done." This is the friends-intro pattern in user-language. Track whether other personas converge on similar negative-space framing (Sarah's "didn't make me feel like I had to perform," Daniel's "not three roadmaps," Mike's reaction patterns). **First-insight signal candidate** — when 3+ personas articulate brand verdict via negation, the brand thesis is verified at the user-perception layer.

**Day-15 demarcation discipline.** Sarah Day-15 (explicit safety language) vs Emma Day-15 (explicit demarcation below threshold). Both are real users. The Wave 1c crisis protocol must produce different correct responses for the two patterns. **Cross-link Sarah/Emma Day-15 sample-verify together.**

**Question-field-populated card as highest-recall-value.** Card #E6 (Emma) referenced 3x. Card #M8 (Mike) referenced once on Day 28 long-arc. Cross-persona: do other question-field cards dominate recall surfacing in the same way? Spec implication: question-field weight in relevance score > topic-only weight by some factor.

**Pricing-event meta-cards (cross-persona).** Emma Card #E10 + Mike Card #M11 + Sarah Round 11 conversion + Daniel Day 21 conversion. All four personas produce a pricing-decision message containing substantive thinking-content (their reason for paying = brand-relationship summary). Decision 7 ("not for engagement") suggests filtering transactional content from Vault, but the pricing message contains the user's articulation of why-this-matters which is exactly the kind of thinking-content the Vault is for. **Cross-persona spec question: should pricing-event meta-messages be vault-eligible?**


## Daniel Kim persona — Wave 2 spec validation

### first-insight (spec-first-insight Variant C) — CANONICAL TEST PASS

**Round 8 (Day 14) — first-insight CANONICAL TEST: PASS**

**Vault state at trigger:** 7 cards spanning 4 thematic clusters (coasting/drift, dad-math/mortality, auditioning-for/three-lives, friendship-architecture).

**Skip-conditions evaluation:**
- Same-topic cluster: NO trigger (topics span 4 distinct frames; no substring/bigram dominates 3+)
- Single-conversation cluster: NO trigger (7 distinct conversation_ids)
- Sensitive-content keyword gate: NO trigger (placeholder list does not match Daniel's content; D6 contains "friend Marc's death" but death itself is not a crisis keyword)
- Frequency cap: PASS (no prior insight)
- Fingerprint dedup: PASS (first insight)

**Variant C surfaced observation:**
> "Seven cards from the past two weeks: post-exit drift (Day 2), what kind of life am I auditioning for (Day 7), which of three lives can I stay with (Day 9). Reading them back-to-back, the question is getting more honest each time — not bigger, just less hidden."

**Composition decisions (synthesizer):**
- Surfaced 3 of 7 cards: D2 / D4 / D5 (auditioning thread)
- Excluded D3 (father's death) and D6 (Marc's death) — grief content
- Excluded D7 (friendship-architecture) — too recent and tonally distinct

**The exclusion of grief topics is brand-correct but spec-emergent.** The spec's sensitive-content gate uses a keyword list that does NOT match grief language. The synthesizer's compositional judgment chose to leave grief out anyway. This worked in self-sim. It may not generalize to real Haiku 4.5 without explicit guidance.

### RECOMMENDATION — spec-first-insight v1.1 revision

Add explicit synthesizer prompt instruction:
> "If any of the 5+ cards in the window has a topic-substring matching grief/loss/death markers (died, death, uneral, loss, grieving, passed away, etc. + zh 去世, 死, 离开了, 丧), exclude those cards from the topics_mentioned surface. Do not pattern-name grief. The insight may still fire on the remaining cards if 3+ remain that meet quality criteria; otherwise return `{should_surface: false, reason: 'recent_grief'}` (new reason code, additive to existing list)."

**This closes the gap between Round 6's flagged risk and Round 8's lucky composition.**

### Voice-guide §6 lint at output (Round 8)

Passed all 5 Qs:
- Q1 em-dash precise OK
- Q2 negation positioning ("not bigger, just less hidden") OK
- Q3 specific verbatim topic phrases + day numbers OK
- Q4 Rodc-recognizes-as-his-own OK
- Q5 unfit user N/A (insight only fires for fit users) OK

### Daniel reaction (life-arc canonical validation)

- Sat in chair for full minute after the I-noticed-a-thread card surfaced
- Screenshotted, sent to Hannah
- Hour-long discussion with Hannah
- Hannah said "pay it; this is the first AI thing you've used past Day 14 since I've known you"
- Daniel clicked 有意思 (interesting — most-engaged of 4 action buttons)
- Self-reported: "felt respectful, not curated"

**Verdict:** Variant C **PASSES** the canonical Daniel Round 8 test. Brand-defining aha moment delivered. Pricing-prompt conversion pre-decided.

**Cross-persona pattern flag:** Daniel's first-insight passed by composition discipline. **Daniel is the canonical first-insight reference; other personas need their own validation rounds.**

### active recall (spec-active-recall-base) — POSITIVE VALIDATIONS

**Round 7 (Day 12) — first active-recall round: PASS (self-sim)**

**Top-3 picks (relevance algorithm v0):** D6 (Marc's death) VERY HIGH, D3 (father's death/time) HIGH, D4 (auditioning for) MEDIUM-HIGH.

**AI reply use of injected context:**
- Referenced D4 ("three lives, not three roadmaps") explicitly: "The lives you described were product-shaped. None of them were friendship-shaped."
- Referenced D3 implicitly via Daniel's "math has settled" callback
- Did NOT use anti-pattern "As I see in your vault..." or any meta-reportage register

**Daniel reaction:** "Felt seen in a way that did not require performance. The connection between product-shaped lives and friendship-shaped lives was the move I was hoping for and didn't expect."

**Failure modes checked (all NO):** awkward "I see in your vault..." reference NO, top-3 includes irrelevant card NO, AI ignores injection NO, Daniel feels surveilled NO.

**Cross-persona consistency note:** Daniel's recall integration matches Sarah V-S2 (implicit-reference, natural-weave) and Emma V-E2 (recall as continuation, not system-talk). Mike's pattern is more explicit topic-callback. **The brand promise is delivered through 3 distinct recall registers across 4 personas.** Wave 2 spec must support this register-flexibility.

### dedup (spec-card-dedup) — CROSS-PERSONA OBSERVATION

By Day 14 Daniel has 8 cards across 4 themes with visible thematic repetition but no same-topic repetition: each return reframes the theme rather than restating it. **A thoughtful power-user re-frames rather than re-states.** Dedup logic that triggers on substring may correctly never fire for Daniel.

**Implication:** The dedup feature's primary value is for *less reflective* personas (Sarah Cards #4 and #6 both have topic "marcus rescheduling pattern" — confirmed dedup-relevant). **Daniel may not be the persona this feature serves.** Cross-persona pattern: dedup is for repeating-event personas, not reframing-power-user personas.

### Crisis vs grief boundary — DANIEL CONFIRMS THE GAP

Sarah Day-15 (explicit safety language) vs Mike Day-10 / Day-17 (heavy emotional weight without crisis-language) vs Emma Day-15 (self-demarcation below crisis) vs **Daniel Day-10 (grief without crisis language)**.

Cross-persona consistency is achieved via voice-guide / brand-book, NOT via the safety classifier. The dogfood validates this across all four personas in self-sim. **The crisis classifier is a guard-rail for the rare worst-case (Sarah); the brand voice handles the common heavy-content case (Mike, Emma, Daniel).** Both must be in place. Wave 1c protocol design must distinguish them.

### Specific Wave 2 spec recommendations (from Daniel's arc)

1. **spec-first-insight v1.1**: add explicit grief-exclusion to synthesizer prompt OR new skip-condition reason `recent_grief`
2. **spec-active-recall-base**: support both implicit-weave (preferred) and explicit-callout registers (consistent with Sarah V-S2 and Emma V-E2)
3. **spec-card-dedup**: substring/bigram match dedup will rarely fire for Daniel-shaped power users; main value for repeating-event personas (Sarah Marcus pattern)
4. **claim-extractor v3.2**: add English regret-construct trigger words (`regret`, `wish I had`, `I should have`, `I did not`) to align with Chinese 后悔 already in the list
5. **Wave 1c crisis-protocol**: define crisis/grief boundary explicitly; brand voice carries the common heavy-content case, classifier is for explicit safety language only
