# Brand Book v1 — Skeptic Review

**Reviewer:** brand-book-skeptic (Phase 4b adversarial pass)
**Date:** 2026-05-03
**Subject:** `docs/superpowers/brand/brand-book-v1.md` v1
**Verdict at a glance:** 2 passes · 2 partial holds · 1 fail. The book is structurally serious and operationally sharp, but the voice samples and the §1 thesis sentence both leak generic-AI-thinking-partner language, and §1 contains at least one verifiable factual error against shipping code. The ship-blocker is not the prose; it is the gap between what §7 Decision 2 promises and what Wave 1b's recall card actually renders.

---

## Question 1 — "If you covered the product name, could you tell it's Rodix?"

**Verdict: PARTIALLY HOLDS.** Sections 4, 5, and 7 are unmistakably Rodix. Sections 1, 2, and 3 paragraph 1 are generic.

The §1 thesis sentence — *"Rodix is an AI chat that visibly remembers what you said and brings it back when it matters — built for thinking, not for engagement"* — could appear verbatim on Mem.ai's relaunch page or Reflect's about page. "Built for thinking, not for engagement" is the exact framing that Mem.ai used in 2022 ("for the way you think"), and "visibly remembers" is the same value-prop ChatGPT Memory's marketing cribs in reverse ("remembers what matters"). The clause that *would* differentiate — "null-by-default" or "stops asking by Round 3" or "no celebration UI" — is absent from the thesis. The 22-word sentence the book claims is "the thesis" is actually a pleasant-sounding category placeholder.

§2 paragraph 1 — *"The per-token cost of frontier-grade reasoning has fallen below the cost of a database query"* — is a 2026 talking point every AI company uses. The cost-of-tokens framing is in Anthropic posts, OpenAI dev posts, and every YC founder's thread. Cover the name and this paragraph reads as "any AI startup explaining why the moat moved." It does not name what Rodix uniquely refuses to do.

§3 paragraph 1 — *"People who think for a living — broadly construed: knowledge workers, founders, researchers, writers, designers, engineers, consultants, anyone whose work product is decisions, frames, or arguments rather than tickets closed or tasks completed"* — is the Notion / Roam / Reflect / Mem.ai / Tana ICP statement. The 12-noun list is the tell: when a brand book lists every flavor of knowledge worker, it has not picked. Mem.ai's 2022 deck literally said "knowledge workers, founders, researchers, writers."

What rescues the book: §4 *"the explicitly banned voice in `rodix_system.md` is Caregiver voice, not Sage voice"* and the operational specifics (Round 3 stop-asking, the four banned phrases, the ⚡ amber callout, "bring back" replacing "surface") are unmistakably Rodix. Cover the name on §7 and you can still tell — Mem.ai never said "we never ship a today view" and Reflect never said "treat the user as capable, capable of being pushed gently if their thinking has a gap." Those are Rodix-specific. But a brand book whose first 3 sections require sections 4-7 to rescue them has buried the lede.

---

## Question 2 — "Do the §5 samples sound like Rodc, or like an LLM imitating a founder?"

**Verdict: PARTIALLY HOLDS.** Sample 1 (chat error) sounds genuinely like the product. Sample 3 (support email) sounds like Rodc. Sample 2 (marketing tagline + subhead) is the weakest — it sounds like ChatGPT writing what a founder would write.

The weakest sentence in Sample 2 is the subhead: *"你跟 ChatGPT 说过的、跟 Claude 想过的、跟 Gemini 来回过的,都还在你这边。"* This is structurally suspicious for three reasons. First, the parallel triple-clause "X 跟 A、Y 跟 B、Z 跟 C" is a rhetorical pattern LLMs over-produce — it has rhythm but no specificity. Second, naming three competitor brands in a tagline is a marketing-school move ("triangulate against incumbents") that a real founder writing for themselves would not do — Rodc would name one ChatGPT failure mode, not three vendor logos. Third, "都还在你这边" is the kind of warm-but-vague reassurance that the rest of the book *explicitly bans* (§5 Don't 2 forbids "I'm here for you" / "我在这里"; "都还在你这边" is the tagline-shaped cousin of that exact register). The sample is using outside-the-frame voice that the inside-the-frame rules would reject.

In Sample 1 the weakest sentence is *"你的回复本身没丢 — 上面的对话照常."* It is fine but slightly mechanical — the em-dash + reassurance + "照常" pattern is the kind of error-state copy a senior PM would write in 5 minutes. It is not wrong; it is just not specifically Rodc. The strong sentence in that sample is *"如果你刚才说的那条值得记下来,可以再展开两句,我重新试"* — that one is Rodc-shaped because it puts the judgment back on the user ("if what you said is worth saving") instead of presuming.

Sample 3 (support email signed "— Rodc") is the strongest. *"你的 email 我看到了,这是个公平的问题 — '没问就保存'应该至少有一次明示。我会写进下版改进点。"* This sounds like a real person because it concedes the user's frame ("公平的问题"), names the specific UX gap ("没问就保存"), and commits to a specific next action ("写进下版改进点"). An LLM imitating a founder would write "thank you for the feedback, we appreciate it, and we'll consider it for future improvements." The sample avoids all three of those tells. Keep this one.

The pattern: when the book operates in *the product's voice* (chat, support email — first-person specific) it sounds like Rodix. When it operates in *marketing voice* (taglines, hero subheads) it drifts toward LLM-imitating-founder. This is the seam to watch.

---

## Question 3 — Weakest sentence in §2 or §3

**Verdict: §3 paragraph 1, the 12-noun ICP list.**

The single weakest sentence is: *"Primary user. People who think for a living — broadly construed: knowledge workers, founders, researchers, writers, designers, engineers, consultants, anyone whose work product is decisions, frames, or arguments rather than tickets closed or tasks completed."*

It is weak for three converging reasons. (1) Every "thinking tool" brand book in the last five years has written this sentence with minor variation — Roam, Mem.ai, Reflect, Tana, Logseq, Heptabase, Capacities. The 12-noun list is the genre marker. (2) "Broadly construed" is the giveaway — when a brand book uses "broadly construed" to expand a target user definition, it is admitting it has not chosen one. The corresponding strong move would be picking *one* user (e.g., "researchers who write for a living") and letting the rest see themselves in the example. The book does the opposite. (3) The sentence describes Rodix's *aspiration* (we want thoughtful users) rather than naming what Rodix *does* for them. Compare to §3 paragraph 2's anti-target list ("Things, OmniFocus, Replika, Character.ai") which is sharp because it names specific products it refuses to compete with. Paragraph 1 should have the same sharpness: name *one* user and *one* failure mode, not 12 users and a "broadly construed" hedge.

A specific replacement: *"Primary user. Someone who already uses ChatGPT or Claude every day for thinking-out-loud, has tried two AI memory tools that disappointed them, and notices when a product pads."* That sentence could not appear in Mem.ai's brand book without modification because Mem.ai's ICP was "anyone with notes," not "the user who has already churned out of two AI-memory products." Naming the disappointment cycle is Rodix-specific.

---

## Question 4 — What does the book ask Rodix to be that Wave 1b is not?

**Verdict: FAILS in three specific places.** The brand book makes claims that are either factually wrong against shipping code, or aspirational against Wave 1b scope.

**Gap 1 — recall threshold: factually wrong.** §1 paragraph 2 (the thesis exegesis) says *"Brings it back when it matters is the active-recall threshold (calibrated above 0.75) and the relational verb that replaced the engineering word 'surface.'"* This is not what the code says. `app/shared/recall/evaluators/loose_end.py` line 14 reads *"Default threshold (orchestrator side): 0.50 — loose ends are…"* and `app/shared/recall/evaluators/decision_precedent.py` line 14 reads *"Default threshold (orchestrator side): 0.60 — decisions are…"*. The brand book invented "0.75" — it does not exist anywhere in the repository. This is exactly the kind of plausible-sounding-but-fabricated detail that §5 Voice Principle 2 ("null is the default, not the failure case … filling a field with invention is a CRITICAL FAILURE") forbids. The book violates its own most important rule in its own thesis sentence. This must be fixed before Rodc reads it.

**Gap 2 — ⚡ recall callout: aspirational, not shipped.** §7 Decision 2 promises *"Rodix bets on transparent recall (visible Cards, ⚡ recall callouts, Vault audit surface)."* The brainstorm `#8` micro-adjustment 2 (lines 122-125) locks the recall card text as *"⚡ 我把这个带回来了"* / *"⚡ I brought this back"*. But `app/web/static/app.js` line 580 actually renders `header.textContent = '记忆提醒 · ' + recallTypeLabel(recallType)` — the literal string "记忆提醒 · 话题相关" (memory reminder · topic-related). There is no ⚡ glyph, no "我把这个带回来了" copy, no kept-promise language. The action buttons in code are `记下了 / 看了 / 不相关 / 忽略` (line 615-618), not the brainstorm-locked `用上了 / 不相关 / 已经想过 / 跳过`. Either the brainstorm spec slipped during Wave 1b implementation, or the brand book is describing a future state that has not shipped. Either way, the brand book reads as if the recall callout is a kept promise; the code reads as if it is a placeholder.

**Gap 3 — crisis-content handling: the system prompt has no crisis protocol.** §7 Decision 5 says *"When users want healing, the product gracefully signals 'this is not what I'm built for, here are resources' — it never expands the surface to absorb the request."* I grepped `app/web/prompts/rodix_system.md` and the entire `app/` tree for `crisis|self-harm|suicide|hotline|988|emergency`. Zero matches. The system prompt has no crisis-content protocol — no escalation language, no resource handoff, no detection rule. The brand book describes a behavior the operationalized prompt does not enforce. If a Wave 1b alpha user describes a mental-health crisis, the system will currently respond with whatever the underlying LLM defaults to plus the banned-phrase filter — which is exactly the unverified Caregiver-drift surface the book claims is locked-down.

**What does pass verification.** Null-by-default extraction is real: `app/shared/extraction/prompts/claim_extractor.md` line 17 enforces *"If you are not at least 80% confident that the user explicitly expressed a field, return null for that field"* and the prompt's closing lines codify the cost-asymmetry logic the book quotes. The Vault badge `+1` is real and shipped (app.js lines 526-545). The "带回来" promise text is in code at app.js line 428. So the book is not entirely making claims up — but the three places it does make claims up are the load-bearing ones for the trust-evoking thesis.

---

## Question 5 — Five-year coherence: what survives commodity LLMs?

**Verdict: PASSES — and the book deserves credit for being honest about it.** §8 is the strongest section in the book precisely because it does not flinch.

The book quotes *"there is no tech moat. The moat is 'we hold these lines longer than anyone with capital is willing to.'"* This is the right answer, and most brand books in this category will not write it. Mem.ai's 2022 deck claimed defensibility through "AI-native architecture" (gone in 18 months). Reflect claimed defensibility through "backlinks + AI" (Notion shipped both). Rodix's book correctly identifies that by 2031 every competitor will have structured memory cards, anti-buzzword copy, and amber accents. The 4-field schema is two weeks of work for a funded competitor.

What the book identifies as durable — *execution discipline + founder narrative + small-cohort retention* — is the right answer for an indie single-founder. The Cal.com analogy in the reconciliation log §5 (borrow the founder-visibility pattern, not the open-source-product pattern) is correctly tuned: Cal.com's defensibility is also not technical. It is "the founder's name is on the support emails."

The honest read I would push harder on: §8's *"founder narrative is a moat that scales sub-linearly but is uncopyable in kind"* is true, but the brand book does not yet describe what specifically Rodc's voice *is*. Anthropic has Dario / Daniela / the constitutional-AI lineage. Cal.com has Bailey Pumfleet's open-source posture. Rodix has Rodc's brainstorm voice (visible in `2026-05-01-rodix-brainstorm.md`'s 克制成熟 / "不是哇是信任" register), but the brand book does not yet name it as a brand asset. This is the next-layer move: turn Rodc's actual voice (brainstorm-doc voice, signed-support-email voice) into a documented brand sub-asset that founder essays / HN posts / launch video script can be measured against. §8 promises the moat; the book does not yet operationalize it.

If by 2031 the discipline has eroded — Rodix has shipped a today view, softened the ban list, added celebration toasts — then yes, the brand has lost what made it distinct. The book names this risk in §8 explicitly. That paragraph alone is worth the price of admission. Keep it.

---

## Three to five edits the brand book needs

**Edit 1 — §1 thesis sentence: fix the factual error and sharpen the differentiator.**
Current: *"Brings it back when it matters is the active-recall threshold (calibrated above 0.75)..."*
Replace with: *"Brings it back when it matters is the active-recall mechanism (loose-end threshold 0.50, decision-precedent 0.60, both calibration-pending against alpha telemetry per §8) and the relational verb 'bring back' that replaced the engineering word 'surface.'"*
**Why:** The "0.75" number is fabricated against shipping code. This is exactly what §5 Voice Principle 2 says is a CRITICAL FAILURE. The brand book cannot have a hallucinated number in its thesis sentence and simultaneously claim null-by-default discipline as a brand asset.

**Edit 2 — §1 thesis sentence: replace generic "AI chat that visibly remembers" with a Rodix-specific clause.**
Current: *"Rodix is an AI chat that visibly remembers what you said and brings it back when it matters — built for thinking, not for engagement."*
Replace with: *"Rodix is an AI chat that returns null rather than invent, stops asking by Round 3, and brings back your own words when they matter — built for thinking, not for engagement."*
**Why:** The current sentence could be Mem.ai's tagline. The replacement names three Rodix-specific operational stances (null-default, Round-3 stop, user's-own-words recall) that no competitor has shipped together. It is one syllable longer. It cannot be cribbed because no competitor wants to commit to "return null" as marketing copy.

**Edit 3 — §3 paragraph 1: cut the 12-noun ICP list.**
Current: *"People who think for a living — broadly construed: knowledge workers, founders, researchers, writers, designers, engineers, consultants, anyone whose work product is decisions, frames, or arguments rather than tickets closed or tasks completed."*
Replace with: *"Someone who already uses ChatGPT or Claude every day for thinking-out-loud, has tried at least one AI memory tool that disappointed them, and notices when copy is padded. Whatever their job title, they evaluate AI products on whether the product respects their thinking — not on feature lists."*
**Why:** The 12-noun list is the genre marker for "I have not chosen an ICP." Naming the disappointment cycle ("tried at least one AI memory tool that disappointed them") is Rodix-specific and cannot appear in Mem.ai's deck without admitting Mem.ai is the product they churned from. The "notices when copy is padded" clause is the recursive proof — the user the book describes would notice a 12-noun list as padding.

**Edit 4 — §5 Sample 2 (marketing tagline subhead): rewrite to not name three competitor brands.**
Current: *"你跟 ChatGPT 说过的、跟 Claude 想过的、跟 Gemini 来回过的,都还在你这边。"*
Replace with: *"换模型不丢记忆。Rodix 把每次值得保留的具体点存进你自己的 vault — 你下次说起相关的事,它主动带回来。"*
**Why:** Naming three vendor brands in a subhead is marketing-school triangulation, not founder voice. The triple-parallel structure ("X 跟 A、Y 跟 B、Z 跟 C") is an LLM rhetorical tic. The replacement keeps the cross-vendor message ("换模型不丢记忆") in 6 characters and uses two more sentences to describe the actual mechanism ("具体点", "主动带回来"). This is the voice §5 Voice Principle 1 prescribes.

**Edit 5 — §7 Decision 2: add a Wave-1b-vs-aspirational clarifier.**
Current: *"Rodix bets on transparent recall (visible Cards, ⚡ recall callouts, Vault audit surface)."*
Add as a paragraph below: *"Wave 1b ship state: visible Cards and Vault audit surface are operational. The ⚡ recall callout copy ('我把这个带回来了' / 'I brought this back') is locked in brainstorm `#8` micro-adj 2 but Wave 1b currently renders the placeholder header '记忆提醒 · 话题相关' — patching this string to the locked copy is on the Wave 1b ship-blocker list. The brand-level commitment stands; the operational implementation has a known gap."*
**Why:** The book currently reads as if Decision 2 is fully shipped. The code shows the recall card header and action buttons are placeholder strings, not the brainstorm-locked copy. A brand book that overstates ship state will be embarrassing the moment Rodc walks the demo. Naming the gap turns a credibility liability into evidence of execution discipline.

---

## Type-A escalations to Rodc

**Escalation 1 — Crisis-content handling has no operational implementation. (Severity: HIGH)**
**What's at stake:** §7 Decision 5 promises the product *"gracefully signals 'this is not what I'm built for, here are resources' — it never expands the surface to absorb the request."* `app/web/prompts/rodix_system.md` has no crisis protocol. Zero hits for `crisis|self-harm|suicide|hotline|988|emergency` across the entire `app/` tree. Brand-side commitment exists; product-side mechanism does not.
**What the book says:** Decision 5 lists Caregiver-banned phrases extensively but provides no operational contract for what *replaces* the Caregiver response when crisis content surfaces. The product test scenarios (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` per memory) cover career anxiety, mortality, identity — but the system prompt does not branch on crisis content.
**What Rodc should weigh:** Three options. (a) Add a crisis-detection rule + handoff resource list to `rodix_system.md` before Wave 2 (cheapest, but adds a category the brand has refused). (b) Add a brand-level rule that says "the system stays in Sage register on heavy topics, period — the user is treated as adult; no resource list" (purest brand stance, highest operational risk). (c) Add a thin protocol that *only* fires on explicit safety language and otherwise stays Sage (the responsible compromise). The book currently implies (a) or (c) is in place; the code implements neither. This is a P0 brand-vs-product reconciliation Rodc should resolve before Wave 2 dogfood, because the first alpha user who tests this surface will determine whether the product is "thoughtful" or "negligent" in the pivot review.

**Escalation 2 — The "0.75 threshold" hallucination in §1 reveals a deeper authorship-discipline question. (Severity: MEDIUM)**
**What's at stake:** The brand book's thesis sentence cites a calibration threshold that does not exist anywhere in the repository. The actual code says 0.50 (loose_end) and 0.60 (decision_precedent). This is exactly the failure mode `claim_extractor.md` was written to prevent: invented plausible-sounding numbers in place of "I don't know" or "see code."
**What the book says:** The book treats null-by-default as one of its load-bearing brand commitments — §4 cites it, §7 Decision 3 codifies it, §5 Voice Principle 2 names it. The §1 thesis sentence violates this principle in its own articulation.
**What Rodc should weigh:** Two layers. (1) The literal fix is Edit 1 above — replace 0.75 with the actual numbers. (2) The deeper question is whether the brand book itself should hold to the same null-default discipline the product holds to: when the book is uncertain about a fact, does it say "calibration-pending" / "see brainstorm `#1b`" rather than invent a number? If yes, this fixes one symptom now and prevents the same authoring failure mode in subsequent brand artifacts (founder essay, launch video script, press kit). If no — if the brand book is allowed marketing-poetic license that the product is not — the book is creating its own seam between "what we say externally" and "what we ship." Rodc should pick.

---

*End review-notes.md. Skeptic pass complete. 2 passes, 2 partial holds, 1 fail. Most important edit: Edit 1 (fix the 0.75 hallucination). Top escalation: Crisis-content protocol gap.*
