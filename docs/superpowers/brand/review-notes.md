# Brand Book v2 — Skeptic Review

**Reviewer:** brand-book-skeptic v2 (Phase 4 v2 adversarial pass)
**Date:** 2026-05-03
**Subject:** `docs/superpowers/brand/brand-book-v1.md` (v2 contents, friends-intro-canonical)
**Verdict at a glance:** 6 passes · 1 partial · 0 fails. v2 is a substantive upgrade over v1. It clears all four v1 ship-blockers (0.75 hallucination · ⚡ aspirational claim · crisis-protocol gap · generic ICP) by either deleting the offense (0.75 → real Wave 1b values), or honestly fenced it into §7b (recall placeholder · crisis protocol). The remaining soft spots are length, two-layer-archetype rule clarity, and one residual generic phrase in §3 ¶3. No Type-A escalations remain in v1's category — the v1 set was cleared. One new lower-severity escalation surfaces: defensibility-frame leadership (architectural-commitment vs founder-narrative) — flagged in book itself by reconciliation log §6 awaiting Rodc.

---

## Question 1 — "Cover the name. Is it Rodix?"

**Verdict: PASSES.** The fingerprints v1 lacked are now plural and structural, not just rescued by §4-7.

Strong evidence the book is unmistakably Rodix from §1 onward:
- §1 hero: *"ChatGPT remembers your name. Rodix remembers your thinking."* — the contrast is the brand. Mem.ai never wrote this; it reads as a churn-reason from inside the category.
- §2 ¶2: the Gemini-corporate-secretary passage names a *specific* failure mode of a *named* competitor. Generic competitor brand books do not name "weeks" of "as a corporate secretary, you should..." — they say "personalization can drift." The specificity is the tell.
- §3 anti-target: *"If you ask AI 'what's a good restaurant in Lisbon' twice a week and that's it, you don't need this. ChatGPT's fine."* No competitor brand book sends users away. This sentence is the brand.
- §4: *"The Explorer's signature wound: 'There's no way to debug that' is not 'they were wrong about me' — it is 'I cannot get out of the wrong they made about me.'"* This level of psychological-frame analysis on a competitor failure is single-author voice, not committee.
- §5: parenthetical-as-honesty (Principle 2) and the 7-do/7-don't structure with *anti-examples* are uncopyable in kind. Mem.ai's brand book would not include "Don't dramatize founder status" with a violating example, because that move requires a founder voice mature enough to mock the LinkedIn-founder register.

**One residual soft spot — §3 ¶3:** *"Whatever their job title, they evaluate AI products on whether the product respects their thinking — not on feature lists. They prefer 'I don't know' plainly to confident-sounding filler."* The first sentence is generic — "respects their thinking" could be Reflect's tagline. The second sentence rescues it ("'I don't know' plainly" is Rodix-specific). Tighten: cut sentence 1, lead with "They prefer 'I don't know' plainly." But this is a polish-edit, not a v1-style failure.

---

## Question 2 — "Does the §5 voice in samples sound like Rodc, or LLM-imitating-Rodc?"

**Verdict: PASSES** for all 3 samples. Substantial improvement over v1.

**Sample 1 — chat error message.** *"Extraction didn't run on your last message. The reply itself went through fine — only the card-saving step failed. If what you said was worth keeping, retry below. If it was passing chat, skip it; nothing's lost either way."* Weakest line: *"nothing's lost either way."* It is fine — short qualifier, undoes anxiety without retreating. Not LLM-shaped. The "If X, retry. If Y, skip" two-option structure mirrors the friends-intro's *"If you want early access, ping me. If you want to wait for public launch, also fine"* — same shape.

**Sample 2 — marketing tagline + supporting subhead.** *"ChatGPT remembers your name. Rodix remembers your thinking."* + *"Every meaningful exchange becomes a card you can read, edit, and take with you — topic, concern, hope, open question. Same memory across every model you use; one click, markdown export, your hard drive."* Tagline is verbatim from friends-intro. Subhead's weakest line: *"Every meaningful exchange becomes a card you can read, edit, and take with you"* — "meaningful exchange" and "you can read, edit, and take with you" both have a slight feature-spec register. But the subhead recovers immediately with "topic, concern, hope, open question" (the actual schema, named) and *"your hard drive"* (the friends-intro anti-abstract closer). v1's Sample 2 named three vendor brands and used "都还在你这边" therapy-speak; v2 names mechanism and ends concrete. Net: passes.

**Sample 3 — support email.** *"Fair flag. The card was saved by Rodix's extraction step, which runs after every message that names something specific (a worry, a goal, a question). The AI itself didn't decide to save it — extraction is a separate, fixed pass. … The switch should have been more visible from the start — that's on me, and the next release moves it. … If anything else feels like Rodix did something behind your back, send it. I'd rather hear it. — Rodc"* Strongest sample. Weakest line: *"that's on me, and the next release moves it."* — that is the strongest line, actually. Whole sample sounds like Rodc. No "Thank you for your feedback." Concedes user frame ("Fair flag"), names mechanism (extraction-as-separate-pass), owns gap ("that's on me"), invites more ("I'd rather hear it"). Founder signature. Cannot be cribbed.

The pattern v1 had — marketing voice drifts toward LLM-imitation while in-product voice stays Rodc-shaped — is largely fixed because the §1 hero is now a friends-intro verbatim quote rather than a CC-paraphrase.

---

## Question 3 — Single weakest sentence in the entire book

**Verdict: §6 ¶3 sentence on Inter font.**

*"Inter font is neutral, unspecific, global — matches the cross-model bet (no vendor flavor, no vertical signal). Sans-serif resists the 4-field-card sentimentality drift Granola's handwritten warmth would invite."*

Weak because: *"neutral, unspecific, global"* is boilerplate font-spec writing — every dark-mode dev-tool product description uses this register for Inter ("clean, modern, neutral"). The justification (*"matches the cross-model bet"*) is an after-the-fact narrative graft; Inter does not actually signal cross-model neutrality to any user — they just see a sans-serif. The real reason for Inter (Linear / Vercel / GitHub / 80% of dev-tool brands use it; it is the safe default) is unstated, so the book invents a brand reason that does not survive scrutiny.

This sentence could appear unmodified in Linear's brand book, Vercel's, Resend's, Cal.com's. It is the most generic phrasing in the document.

Suggested replacement: *"Inter is Phase 1's font because it is the dark-mode-dev-tool default — chosen for being unremarkable rather than for signaling anything specific. The visual-system signal lives in the amber accent and the absence of decoration, not in the typeface."* That sentence cannot appear in a Linear brand book because it admits the typeface is a default rather than a brand asset — which is exactly Rodix's anti-spin posture.

---

## Question 4 — What does the book ask Rodix to be that Wave 1b is not?

**Verdict: PASSES.** §7b honestly fences three known gaps. Verified each via Grep.

**Verified gap 1 — Recall callout copy.** §7b first bullet acknowledges the placeholder. I confirmed: `app/web/static/app.js` line 580 still renders *"记忆提醒 · " + recallTypeLabel(recallType)* with `topic: '话题相关'` (line 627). No ⚡ glyph anywhere in `app/` (Grep on `^.{0,5}⚡` returned zero matches). The action buttons are still `记下了 / 看了 / 不相关 / 忽略` (app.js 615-618), not the brainstorm-locked `用上了 / 不相关 / 已经想过 / 跳过`. The book's acknowledgment is honest as far as it goes — but it names only the *header* string gap. The action-button-label gap is also locked-but-unshipped and the §7b bullet does not name it. **Recommend §7b first bullet add:** *"Action button labels in `app.js` 615-618 also remain `记下了 / 看了 / 不相关 / 忽略` rather than the brainstorm-locked `用上了 / 不相关 / 已经想过 / 跳过`. Both string-level patches are scoped together as a Wave 2 deliverable on `#active-recall-base`."* This is a 30-second edit that takes the §7b acknowledgment from 75% honest to 100% honest.

**Verified gap 2 — Crisis protocol.** §7b second bullet acknowledges zero coverage. I confirmed: Grep on `crisis|self-harm|suicide|hotline|emergency|988` across `app/` returns one match in `app/shared/extraction/test_extractor.py` (a test fixture mentioning the words — not protocol code). `rodix_system.md` has zero matches. The brand book's escalation flag — *"Brand stance is fixed; the protocol design (resource scope, detection trigger, register on the way out) is the open Type-A escalation question for Rodc"* — is correct framing. This is appropriately honest.

**Verified gap 3 — Encryption claims.** Decision 6 in §7 quotes the friends-intro's anti-spin verbatim: *"Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture). Encryption hardening on the post-launch roadmap. Export is plaintext markdown — that's the actual ownership story."* §7b third bullet adds *"Per-user encryption is Wave 3 SaaS upgrade, not Phase 1."* The book never claims zero-knowledge or per-user keys as current state. Passes cleanly. This is the strongest move in §7b — it builds anti-spin into the highest-stakes claim category.

**Active recall claims verification.** The book commits to active recall as a brand bet (§7 Decision 3) but cites verified Wave 1b production thresholds (`topic 0.65, stance_drift 0.70, loose_end 0.50, decision_precedent 0.60` per `app/shared/recall/orchestrator.py` `ThresholdConfig`). I confirmed: `orchestrator.py` lines 141-144 contain those exact values. No fabrication. Passes. The §7b third bullet does not need to extend to active-recall scoping because per memory `#active-recall-base` is Wave 2 (not 1b) — but the book never claims active recall is shipped at the user-facing-callout level (§7b first bullet covers the callout gap explicitly). Net: honest.

---

## Question 5 — Five-year coherence: what survives commodity LLMs?

**Verdict: PASSES.** §8 is the strongest section in the book. v2 sharpens v1's already-strong §8 by separating foreground moat (architectural commitments) from behind moat (execution discipline + founder narrative + small-cohort retention).

Stress-test scenario 1 — **Anthropic ships white-box memory in Claude in 2027.** What holds? Answer in book: cross-model still differentiates because OpenAI and Google would not match (LTV thesis incompatible). Real markdown export still differentiates against Claude's per-vendor architecture. The white-box claim alone collapses; the four-bet *combination* survives. Book's argument is correct — but if **all three** frontier vendors ship white-box memory before Phase 1 launch (low-prob but non-zero), only cross-model survives, and the book's claim that "every funded competitor still has to answer to growth metrics" becomes the sole moat. The book acknowledges this (§8 ¶3 (a)(b)(c) "what's at risk of becoming generic"). Pass.

Stress-test scenario 2 — **GPT-5 / Gemini converge into one dominant model and cross-model becomes irrelevant.** What holds? This is one of the three fail modes named in friends-intro reading guide line 110: *"Cross-model never matters because one model wins decisively."* Book's §8 does not directly address this scenario — it assumes the multi-vendor world persists. Honest read: if Anthropic shutters mid-2027 and Claude users default to GPT, half of Rodix's bet (cross-model portability) becomes a feature for a dead use case. What survives in that world: white-box transparency + null-by-default + real markdown export. Three of four bets, not four. The book should acknowledge this scenario in §8 — **recommend adding one paragraph:** *"If by 2031 the multi-vendor landscape collapses to a single dominant model, cross-model becomes a feature for a dead use case. Three of the four bets survive (white-box, null-default, markdown export). Rodix's defensibility narrows to user-sovereignty primitives within a monopoly architecture — still distinctive, but on a smaller axis."* This is medium-severity polish; the book is currently silent on the most named-by-friends-intro fail scenario.

Strong move v2 makes that v1 did not: separating foreground moat (architectural-commitments-incompatible-with-vendor-business-models) from behind moat (execution discipline + founder narrative + small-cohort retention). The §8 closing line — *"the moat is 'we hold these lines longer than anyone with capital is willing to'"* — is the right answer for an indie single-founder, and the book is honest enough to write it.

---

## Question 6 (NEW) — "Two-layer archetype model: useful or hedge?"

**Verdict: PARTIALLY HOLDS.** The two-layer model is a hard-won real insight, but the rule for choosing which layer dominates a given surface is implicit, not explicit.

The two-layer model itself is *correct* — v1's Sage primary reading collapsed the AI-character layer into the brand layer; v2's Explorer primary + Sage-flavored AI character is the right resolution. §4 ¶7 *"Brand-as-Explorer governs landing, founder essay, HN post, Twitter thread, support emails, marketing copy. AI-as-Sage-flavor governs the in-product chat — how Rodix behaves when the user is mid-thought"* is the load-bearing rule. This is intellectually serious work and v1 got it wrong. Defend.

**The hedge concern.** When in doubt, which layer dominates? The book says §4 *"when in doubt about register on a brand surface, re-read the friends-intro; when in doubt about register on an in-product chat surface, re-read rodix_system.md v1.3."* Good — but what about *transitional* surfaces? Specifically:

- **Chat error message (Sample 1).** Is this Brand-as-Explorer (it's a UI surface introducing Rodix's failure-handling personality) or AI-as-Sage (it's in-product, mid-conversation)? Sample 1's voice — *"Extraction didn't run on your last message. … nothing's lost either way."* — reads Explorer to my ear (anti-spin, refuses-to-dramatize). But by the §4 rule it should be Sage-flavored because it is in-product chat. Mismatch.
- **Onboarding subtitle.** Per brainstorm `#2a`: `[PRODUCT_NAME] 不绑定任何 AI 公司——你的 memory 跨任何模型`. Is onboarding Brand surface (introducing Rodix to a new user) or AI surface (the AI is one click away from the user reading this)? Both. Book is silent.
- **The recall callout copy '⚡ I brought this back'.** This is in-product chat, but its register is Explorer ("brought back" = relational, anti-engineer-verb), not Sage (which would be "Here is a relevant past thought"). Friends-intro calls this register; `rodix_system.md` does not enforce it.

**The Wave 4 marketing video stress test.** Mental simulation: if Wave 4 launch video shows Rodix-the-AI speaking in chat (Sage register) embedded inside Rodc's voice-over (Explorer register), would the cuts feel coherent? Probably yes — the video has two voices because the product has two voices, and that *is* the brand differentiator (the AI is interchangeable; Rodc-the-builder is not). But the book does not explicitly say "the two-voice cut is intentional and trust-building." Recommend §4 add an **implementation rule:** *"On surfaces where the user is meeting Rodix-as-product, lead with Brand-as-Explorer voice. On surfaces where the user is mid-thinking with Rodix-the-AI, lead with Sage-flavored AI voice. Transitional surfaces (onboarding, error states, recall callouts, support email mid-incident) inherit Brand-as-Explorer because they are introducing Rodix's character on a recovery path. The AI voice gets the chat reply itself; everything wrapping the chat reply is Explorer."*

This is a medium-severity edit. Without it, the two-layer model could read as a hedge that lets both archetypes off the hook on hard cases.

---

## Question 7 (NEW) — Length & ruthlessness check

**Verdict: 2 sections could be cut by 30% without losing load-bearing content.**

Book is 7233 words; target was 4000-5500 (~35% over). Justified-overrun: §5 verbatim friends-intro quoting (~600 words) and Reconciliation Log (~900 words, audit trail). Net trimmable budget: ~1700 words.

**Cut candidate 1 — §4 (currently ~720 words). Trim to ~500.**
The four "Anti-implications — Explorer drift to avoid" bullets (lines 76, paragraph) are valuable as guardrails but redundant with §6 visual-identity *"What Explorer implies for visual moves Task 9 should make"* paragraph. Both make the same "no map iconography, no compass metaphors, no 'your journey' visual genre" point. **Cut the §6 ¶6 restatement; keep §4's anti-implications version** because §4 is the archetype-rules section and §6 should defer to Task 9 anyway. Saves ~120 words.

Also: §4 ¶3 *"The 'Gemini decided I was a corporate secretary' passage is the Explorer's signature wound"* is strong but the surrounding gloss (*"Caregiver would feel hurt; Sage intellectually offended; Rebel furious"*) is archetype-theory exposition. The point survives in 2 sentences instead of 5: *"The Gemini-corporate-secretary passage is the Explorer's signature wound: not 'they were wrong about me' but 'I cannot get out of the wrong they made about me.' Containment-without-exit is the archetype's core nightmare."* Saves ~80 words.

**Cut candidate 2 — Reconciliation Log (currently ~900 words). Trim to ~600.**
Items 4 (fail modes), 5 (0.75 threshold), and 7 (Explorer-Sage) are essential audit trail — keep verbatim. Items 1, 2, 3, 6 each occupy ~120 words explaining "v1 said X, v2 says Y, here's why Y" — but v1 is preserved as `brand-book-v1-brainstorm-based.md` for audit. The reconciliation entries can be condensed to 50-60 words each: state the shift, name the canonical input that drove it, point at the v1 doc for the full v1 reasoning. Saves ~280 words.

**Defended sections — do NOT cut:**
- §5 voice principles (1-5) verbatim quotes from friends-intro. These are the canonical voice samples. Cutting them weakens the book's enforcement teeth.
- §7 Decision 6 (honest about architectural compromises) — the longest verbatim friends-intro quote. This is the trust artifact.
- §7b — three honest gap acknowledgments. Cutting any reduces honesty surface.
- §8 — the foreground/behind moat structure is load-bearing for Phase 1 positioning.

Net: a careful editor could bring the book to ~5500 words (target ceiling) while strengthening rather than weakening voice. Severity: low — the over-length is paid in audit-trail value, not in marketing fluff.

---

## Edits the brand book needs

**Edit 1 — §7b first bullet: extend recall-callout gap acknowledgment to action button labels.** **Severity: medium.**
Current: names header-text gap only.
Add: *"Action button labels in `app/web/static/app.js` lines 615-618 also remain `记下了 / 看了 / 不相关 / 忽略` rather than the brainstorm-locked `用上了 / 不相关 / 已经想过 / 跳过`. Both string-level patches scope together as a Wave 2 deliverable on `#active-recall-base`."*
Why: §7b is the book's honesty surface. Naming only half the recall-callout gap reads as half-honest. The verification surface for "the brand book is anti-spin operationalized" depends on §7b being exhaustive about Wave 1b gaps, not partial.

**Edit 2 — §6 ¶3: rewrite the Inter sentence.** **Severity: low (polish).**
Current: *"Inter font is neutral, unspecific, global — matches the cross-model bet (no vendor flavor, no vertical signal). Sans-serif resists the 4-field-card sentimentality drift Granola's handwritten warmth would invite."*
Replace with: *"Inter is Phase 1's font because it is the dark-mode-dev-tool default — chosen for being unremarkable rather than for signaling anything specific. The visual-system signal lives in the amber accent and the absence of decoration, not in the typeface."*
Why: the current sentence is the most generic phrasing in the book — boilerplate font-spec writing that would survive a paste into Linear's brand book. The replacement admits the typeface is a default, which is the anti-spin posture the rest of the book holds.

**Edit 3 — §4: add explicit two-layer-routing rule for transitional surfaces.** **Severity: medium.**
Currently: §4 ¶7 names brand-vs-AI surfaces but is silent on transitional ones (onboarding, error states, recall callouts, support email mid-incident).
Add a new paragraph after §4 ¶7: *"On transitional surfaces (onboarding, error states, recall callouts, support email mid-incident), lead with Brand-as-Explorer voice — these are introducing Rodix's character on a recovery path. The AI voice gets the chat reply itself; everything wrapping the chat reply is Explorer-shaped. The recall callout text '⚡ I brought this back' is Explorer (relational verb, anti-engineer-tone), even though it appears in chat — the AI did not 'choose' to bring it back; Rodix-as-product brought it back."*
Why: without this, the two-layer model reads as a hedge that lets both archetypes off the hook on the hard cases. The recall-callout copy is in-product chat but Explorer-register; the rule should make this explicit so future copy work in the gray zone has a deterministic answer.

**Edit 4 — §3 ¶3: tighten the generic clause.** **Severity: low.**
Current: *"Whatever their job title, they evaluate AI products on whether the product respects their thinking — not on feature lists. They prefer 'I don't know' plainly to confident-sounding filler."*
Replace with: *"They prefer 'I don't know' plainly to confident-sounding filler. Whatever their job title, they evaluate AI products on whether the product treats them as capable — not on feature lists."*
Why: leading with "respects their thinking" is the most generic phrasing in §3 (could be Reflect's tagline). Reordering puts the specific anti-filler stance first, where the section needs Rodix-fingerprints. The "treats them as capable" replacement aligns with `rodix_system.md`'s "Treat the user as capable" voice principle (line 52), which is operational source-of-truth.

**Edit 5 — §8: add one-paragraph treatment of the "one model wins" fail scenario.** **Severity: medium.**
Currently: §8 implicitly assumes a multi-vendor 2031 landscape.
Add as new paragraph after §8 ¶3: *"What if cross-model becomes irrelevant — one frontier model wins decisively by 2028, and 'memory across providers' is a feature for a dead use case? Three of the four bets survive (white-box transparency, null-default discipline, markdown export). Rodix's defensibility narrows to user-sovereignty primitives within a monopoly architecture — still distinctive on the axes the dominant vendor cannot match without harming their lock-in, but on a smaller axis."*
Why: this is one of the three fail modes the friends-intro reading guide explicitly names (line 110-112). The brand book engages two of three (incumbents fixing one bet · users not wanting continuity) but is silent on this third. Honesty surface gain ≈ moderate; closes the gap between the friends-intro's named risks and the book's coverage.

---

## Type-A escalations to Rodc

**Escalation 1 — Defensibility framing leadership: architectural-commitments lead, or founder-narrative lead?** **Severity: medium.**
**What's at stake:** v2 §8 puts architectural-commitments as foreground moat, founder-narrative as behind moat. Reconciliation log §6 explicitly flags this as the Type-A escalation: *"is the architectural-commitment frame the right hero-frame for the founder essay and landing page, or should the founder narrative lead and architectural commitments support? The friends-intro suggests architectural commitments lead and founder narrative supports; v2 follows the friends-intro. Rodc should confirm or revise."* This is unresolved.
**What the book says:** v2 follows friends-intro and leads with architectural commitments. Founder essay ordering (Task 0b) and landing copy (Task 5) inherit this.
**What Rodc should weigh:** If architectural-commitments lead, founder essay opens with the 4-fold critique → 4 bets → "Solo, anonymous, working out of Asia, second half of a multi-year build" appears as a status-fact at the end. If founder-narrative leads, founder essay opens with "I'm a heavy AI user" framing → builds to the 4 bets → architectural commitments are evidence not thesis. v2's choice (architectural lead) is the harder sell but produces the more durable brand asset because the founder-narrative-lead version dilutes when Rodc-the-name becomes Rodix-the-company. Rodc-as-author-in-2031 may not be Rodc-as-author-in-2026.
**Recommendation:** Confirm v2's architectural-lead choice before Task 0b founder essay drafts, because Task 0b commits the ordering operationally.

(No Escalation 2 — v1's two escalations were 0.75-hallucination and crisis-protocol-gap. Both are cleared by v2: 0.75 is corrected to verified values everywhere; crisis protocol is honestly fenced into §7b with the protocol-design Type-A flagged for Rodc inside §7b itself rather than as a separate escalation. v2 cleared the v1 escalation set. The single residual escalation is a strategic hierarchy question, not a brand-vs-product reconciliation gap.)

---

## What v2 got right (defend these moves; do not weaken when applying edits)

1. **Two-layer archetype model (§4 ¶7 + Reconciliation log §1, §7).** v1 collapsed Brand-as-Explorer and AI-as-Sage into one archetype and got it wrong. v2's separation — "brand-as-Rodc-presents-Rodix" vs "AI-as-Rodix-behaving-in-chat" — is hard-won intellectual work and the reconciliation log §7 makes the rationale legible. Edit 3 (above) sharpens the rule for transitional surfaces but the model itself is correct. Defend.

2. **§7b as honesty surface.** Three explicit Wave 1b gaps (recall-callout placeholder, crisis-protocol absence, encryption-as-Wave-3) named in the brand book itself rather than papered over. *"Naming the gap rather than over-claiming is itself the discipline"* (§7b ¶2) is the load-bearing sentence. This is the strongest structural move in v2 vs v1. Anti-spin operationalized.

3. **§5 voice principles 1-5 with anti-examples.** Friends-intro grounding gives every principle a verbatim quote + anti-pattern. Principle 2 (parenthetical-as-honesty) is the most distinctive structural move in the document — most brand books would not name this as a principle; v2 makes it Principle 2. Anti-examples ("Hedge-parenthetical that drains the claim", "Note the exclamation mark — friends-intro uses zero") are uncopyable in kind because they require a founder voice mature enough to mock its own register-failure modes. Defend hard.

4. **§3 anti-target verbatim quote: *"If you ask AI 'what's a good restaurant in Lisbon' twice a week and that's it, you don't need this. ChatGPT's fine."*** Most brand books cannot send users away in their ICP section. This sentence does. v1's 12-noun ICP list is replaced by the friends-intro 4-condition "if you've ever..." passage + the anti-target quote. The contrast against generic competitor brand books is starkest here. This single quote is the load-bearing move for Question 1 (cover the name, is it Rodix?). Defend.

5. **§7 Decision 6 (honest about architectural compromises) verbatim friends-intro quote.** *"Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture)"* in the brand book is the most distinctive trust-building move in the entire document. Most brand books soften compromises; this one volunteers them and frames the alternative as a lie. This sentence alone differentiates Rodix from any competitor that markets "encrypted" / "private" / "secure" without disclosing where the architecture cannot promise that. Defend hard.

---

*End review-notes.md (v2 skeptic pass). 6 passes / 1 partial / 0 fails. v1's 4 ship-blockers cleared. Most important edit: Edit 1 (extend §7b recall-callout gap acknowledgment to action button labels — 30 seconds, brings honesty surface from 75% to 100%). Top Type-A escalation: Defensibility framing leadership (architectural-commitments lead vs founder-narrative lead) — already flagged in book's own reconciliation log §6, awaiting Rodc.*
