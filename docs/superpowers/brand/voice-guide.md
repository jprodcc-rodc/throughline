# Rodix Voice Guide

**Version**: v2.0 (2026-05-03)
**Author**: brand-voice-extractor v2 (Tier 0 Task 0a Phase 3, re-run)
**Primary canonical input**: `docs/rodix-friends-intro.md` body (Rodc's friend-version intro, ~1,350 words)
**Supporting inputs**: `app/web/prompts/rodix_system.md` v1.3 · `app/shared/extraction/prompts/claim_extractor.md` · `docs/superpowers/specs/2026-05-01-rodix-brainstorm.md` · `docs/superpowers/brand/research-notes.md`
**Supersedes**: `voice-guide-brainstorm-based.md` (v1, inferred from operational sources only)
**Locale**: Voice rules apply to BOTH English (canonical, friends-intro is English) and Chinese (frontend user copy). Adaptations called out in §A.

---

## 0. Why v2

v1 inferred Rodix voice from the enforcement layer (banned-phrase list + brainstorm microcopy). It produced "Specific. Restrained. Capable-treating." — accurate but cautious; it described what Rodix avoids, not what Rodix *does*. v2 grounds in friends-intro, which the doc's own reading guide names canonical: *"The voice IS this document. Do not paraphrase it."* Three things friends-intro shows that v1 missed: (1) the voice refuses to dramatize its own moments ("I killed the project that night. (I might restart it next year. That's fine. Different decision.)"); (2) the voice volunteers its own limits without spin ("we can't promise zero-knowledge — that would be a lie given the architecture"); (3) the voice sends unfit users away ("ChatGPT's fine."). v2 keeps "Specific" and revises the other two.

---

## 1. Voice in three adjectives

> **Specific. Anti-spin. Refuses-to-dramatize.**

### Specific (not abstract)

friends-intro never goes vague when a concrete example fits.

> "I open Rodix. I say: *'Thinking again about whether to kill the side project.'*"

Not "users open the app and engage in reflective conversation." The card example names dates (Sept 3 / Sept 19 / Oct 4), a count ("200 hours in"), a duration ("six weeks on the same fence"). The Gemini critique names the provider, the mis-classification ("corporate secretary"), the actual opening line, the duration. Specificity is structural — same discipline `claim_extractor.md` enforces at the data layer ("Extract using user's own wording, 4-8 words preferred, do NOT paraphrase").

### Anti-spin (states own limits plainly)

The most distinctive sentence in friends-intro:

> "Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture)."

The voice volunteers a limitation no marketing copy would surface, and frames the alternative ("promise zero-knowledge") as a lie. Other examples: *"Public launch: weeks, not months."* Not "launching soon!" *"If you ask AI 'what's a good restaurant in Lisbon' twice a week and that's it, you don't need this. ChatGPT's fine."* Sends an unfit user away with no funnel optimization. *"Encryption hardening on the post-launch roadmap."* Names what isn't done yet without softening.

Anti-spin is more active than "restrained" — the voice is willing to be quiet about achievements but is willing to volunteer limitations.

### Refuses-to-dramatize (no triumph, no apology theater, no founder mythology)

The closing example:

> "I killed the project that night.
>
> (I might restart it next year. That's fine. Different decision.)"

The decision is one short sentence. The parenthetical immediately undoes the finality without contradicting it. "That's fine. Different decision." refuses to make killing the project mean anything bigger than itself.

The status section:

> "Founder: solo, anonymous, working out of Asia, second half of a multi-year build."

Four facts. No "scrappy", no "passionate", no "on a mission to". This is the hardest move for an LLM to reproduce, because models default to dramatizing.

---

## 2. Five voice principles

### Principle 1 — Short paragraphs, hammered fragments

friends-intro paragraphs are 1–3 sentences. The negation list does its work as four hammered fragments — *"Black-box tags. Wrong, and you can't fix it. Locked to one vendor. Not actually yours."* — because each is a complete claim, not a soft transition. Compound sentences exist but earn their length by carrying real specificity, not by gluing claims together.

**Verbatim**: "Three things. That's it."
**Anti-example**: "Rodix offers three core capabilities, each designed to work seamlessly with the others to give you a comprehensive thinking environment."

### Principle 2 — Parenthetical-as-honesty

Parentheticals qualify, soften, or undo a strong claim *without retreating from it*. The parenthetical carries the honesty. Short. Never decorative. Used when the main clause is starker than the truth, and the parenthetical brings the truth back into frame without weakening the claim.

**Verbatim**: "(I might restart it next year. That's fine. Different decision.)"
**Verbatim**: "Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture)."
**Anti-example**: "We're committed to privacy (well, mostly — there are some edge cases of course, but we're working on them)!" (Hedge that drains the claim. Note the exclamation mark — friends-intro uses zero.)

### Principle 3 — Negation as positioning

friends-intro positions Rodix more often by what it is *not* than by what it is. The pitch opens with the four-fold negative critique of incumbents *before* Rodix's four positives. The "What it's not" section is four hammered negations. Even "Who's it for" defines the anti-user by negation. Negation is not snark — it's position. Use when defining against a real adjacent thing the reader already knows.

**Verbatim**: "Not 'better AI.' The AI underneath is whatever you choose. Rodix is the layer on top — the memory, the continuity, the receipts."
**Verbatim**: "ChatGPT remembers your name. Rodix remembers your thinking."
**Anti-example**: "Rodix is the only AI memory platform that truly understands you, going beyond simple personalization to deliver real continuity." (Generic SaaS positive-only positioning. Zero negation doing structural work.)

### Principle 4 — Specific over abstract, always

When friends-intro could go vague, it doesn't. User examples have dates, durations, sentence-quotes, outcomes. Competitor critiques name the company and specific failure mode. Mechanism explanations name actual data ("topic / concern / hope / question") not "structured insights." Time qualifiers are concrete ("weeks, not months", "200 hours in").

**Verbatim**: "I'd work through some hard decision with Claude over a week … and three weeks later I'd come back wanting to continue, except the conversation was buried, the threads were tangled, and I couldn't reconstruct what I had concluded without re-reading 80kb of chat."
**Anti-example**: "Users often experience continuity challenges when working with AI tools across multiple sessions." (Same content, zero specifics, swappable to any product.)

### Principle 5 — Honest qualifications, not soft hedges

Qualifiers like "might", "fine", "I'd just start over", "weeks, not months" don't soften — they sharpen. They admit what the main claim glossed and the result is clearer than an unqualified version. Opposite of corporate hedging ("We aim to," "Generally speaking," "In most cases"). Honest qualifiers are short and definite. They name a specific possible counter-state ("I might restart it next year"), not vague reservation.

**Verbatim**: "Public launch: weeks, not months."
**Verbatim**: "If you want early access, ping me. If you want to wait for public launch, also fine — I'll post when it's open." ("Also fine" admits both paths are real, refuses to push, doesn't dramatize either choice.)
**Anti-example**: "We're working hard to bring this to you as soon as possible — stay tuned for exciting updates!"

---

## 3. Seven do's

1. **Do open with the negation when defining against an adjacent thing.** *"Not 'better AI.' The AI underneath is whatever you choose."*
2. **Do volunteer your own limit when it's structurally honest.** *"Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture)."*
3. **Do qualify time concretely.** *"Public launch: weeks, not months."* Not "soon" / "shortly" / "in the coming months."
4. **Do name the specific competitor and the specific failure mode together.** *"Gemini decided I was a corporate secretary because I asked one factual question about the role. Then it kept opening replies with 'as a corporate secretary, you should...' for weeks."*
5. **Do use a parenthetical to undo the strongest part of a claim without retreating from it.** *"(I might restart it next year. That's fine. Different decision.)"*
6. **Do send unfit users away.** *"If you ask AI 'what's a good restaurant in Lisbon' twice a week and that's it, you don't need this. ChatGPT's fine."*
7. **Do let the example carry the argument — name a date, a count, a sentence-quote.** *"[Sept 3] Topic: Side project shutdown / Concern: Sunk cost — 200 hours in / Hope: Reclaim 6 hours/week / Open: Is the metric 'hours' or 'joy'?"*

---

## 4. Seven don'ts

1. **Don't dramatize founder status.** Violating: *"After years of late nights, building from passion and conviction, I'm finally ready to share what we've created."* (LinkedIn founder-coach. friends-intro: "Solo, anonymous, working out of Asia, second half of a multi-year build." Four facts, no mythology.)
2. **Don't celebrate own product moves with adjective stacks.** Violating: *"We've built a beautiful, intuitive, powerful memory layer that seamlessly transforms how you think."* (friends-intro never adjective-stacks Rodix; it describes mechanism — "Three things. That's it.")
3. **Don't open with sycophancy.** Violating: *"Great question! That's exactly the kind of thinking Rodix is built for!"* (Banned in `rodix_system.md`; friends-intro never compliments the imagined reader.)
4. **Don't say "I'm here for you" / "我在这里" in any language.** Violating: *"I'm here for you. Take your time. Whatever it is, I'm listening."* (Therapist-speak. Banned in `rodix_system.md`. friends-intro is intimate but never declares its own presence.)
5. **Don't use process verbs that hide mechanism — "leverage" / "harness" / "unlock" / "supercharge" / "transform" / "surface".** Violating: *"Rodix harnesses the power of your conversational history to unlock continuity of thought."* ("surface" was rejected in `#8` microcopy review as too engineering-coded.)
6. **Don't soft-hedge time or status.** Violating: *"We're working diligently to bring you the best possible experience — stay tuned!"* (friends-intro: "Public launch: weeks, not months.")
7. **Don't over-qualify into mush — parentheticals add information, they don't subtract conviction.** Violating: *"Rodix is the best (well, we think so, and we're always open to feedback!) memory layer for AI chat."* (Hedge-parenthetical. friends-intro parentheticals always add information.)

---

## 5. Three sample passages

Each passage tested against: 1–3 sentence paragraphs · parenthetical or em-dash used precisely · negation pattern present · specific over abstract · honest qualification · would Rodc recognize this as his own writing.

### Sample 1 — Chat error message (extraction failed mid-conversation)

> Extraction didn't run on your last message. The reply itself went through fine — only the card-saving step failed.
>
> If what you said was worth keeping, retry below. If it was passing chat, skip it; nothing's lost either way.
>
> *[ghost button]* Retry extraction

*(56 words. Names what failed and what didn't. Two real options including "skip it". "Nothing's lost either way" is the honest qualifier — most error copy would dramatize. friends-intro test: would Rodc write "We're sorry, something went wrong"? No.)*

### Sample 2 — Marketing tagline + 2 supporting sentences (landing page hero)

> **ChatGPT remembers your name. Rodix remembers your thinking.**
>
> Every meaningful exchange becomes a card you can read, edit, and take with you — topic, concern, hope, open question. Same memory across every model you use; one click, markdown export, your hard drive.

*(Tagline verbatim from friends-intro. 45-word supporting block. Negation-by-comparison preserved. Mechanism named. Em-dash precise. "Your hard drive" is the anti-abstract closer. No "transform" / "supercharge" / "powered by". Test: this sits next to "I killed the project that night" without register clash.)*

### Sample 3 — Support email reply (user: "I don't understand what just happened — your AI saved a card without asking?")

> Subject: re: that card
>
> Fair flag. The card was saved by Rodix's extraction step, which runs after every message that names something specific (a worry, a goal, a question). The AI itself didn't decide to save it — extraction is a separate, fixed pass.
>
> You can delete the card from the Vault tab; deleting also removes it from future recall. Settings has a switch to turn auto-extraction off entirely. The switch should have been more visible from the start — that's on me, and the next release moves it.
>
> If anything else feels like Rodix did something behind your back, send it. I'd rather hear it.
>
> — Rodc

*("Fair flag" opens with anti-spin acknowledgment, no apology theater. Mechanism named without softening. "That's on me" owns the design gap without dramatizing. "I'd rather hear it" signals complaint is welcome. Founder signature per friends-intro pattern.)*

---

## 6. Voice consistency checklist

Five yes/no questions. Two are friends-intro-pattern-specific.

**Q1 — Does this paragraph contain a parenthetical aside or em-dash, used precisely (not decoratively)?**
If a long paragraph has neither, ask whether the strong claim should be honestly qualified — that's where a parenthetical belongs. If the parenthetical hedges instead of adding information ("(or so we think)"), kill it. Em-dashes set up sharper contrast or insertion, not pad rhythm.

**Q2 — Does any negation appear, and is it positioning a specific neighbor?**
Rodix copy that defines itself only by positives — "Rodix is X, Rodix does Y" — is missing the friends-intro structural move. Find the adjacent thing the reader already knows (ChatGPT memory / Gemini personalization / journaling apps) and define against it explicitly.

**Q3 — Does the copy quote, name, or count a *specific* thing — the user's word, an actual number, a sentence-quote, a date, a duration?**
If the copy could be search-and-replaced into another product without changing meaning, it fails. friends-intro never produces a passage that survives this swap test.

**Q4 — Would Rodc himself recognize this as something he could have written?**
Read aloud at native speed. Wrong-answer tells: triple-clause padding, "Let's unpack this together," self-explaining metaphors, exclamation marks, "transform" / "amazing" / "delightful" / "journey." Right-answer tells: short paragraphs, parenthetical or em-dash carrying weight, willingness to admit a limit, no founder mythology.

**Q5 — Would the unfit user be sent away clearly, or coaxed?**
This is the friends-intro fit test. If a piece of copy reads like it's trying to convert a casual user — "anyone can benefit from better thinking!" — it's not Rodix voice. Rodix voice says: "ChatGPT's fine."

---

## 7. Distinguishing Rodix from neighbors

### Rodix vs generic SaaS voice

Generic SaaS ladders feature → benefit → outcome, uses adjective stacks ("powerful, beautiful, intuitive"), and process verbs that hide mechanism ("leverage", "transform", "unlock"). Rodix refuses every step: mechanism named directly ("topic, concern, hope, open question — four fields per card"); adjectives rare and earned ("white-box", "real export"). The friends-intro tagline — *"ChatGPT remembers your name. Rodix remembers your thinking. That's the whole thing."* — is the anti-SaaS specimen: negation positioning + specific contrast + refusal-to-elaborate. Generic SaaS sells; Rodix declares.

### Rodix vs Anthropic voice

Both are principled, deliberate, willing to be quiet about achievements, willing to surface limits. Both reject hype. Divergence: **scale and intimacy**. Anthropic addresses civilizational scale with institutional "we" ("AI research and products that put safety at the frontier"). Rodix addresses *individual* scale with personal "I" ("I'm a heavy AI user. ~2-3 hours a day"). Anthropic would not write "I killed the project that night" — its voice does not do close-quarters first-person. Borrow: matter-of-fact tone on sensitive topics. Don't borrow: institutional "we", civilizational framing.

### Rodix vs therapist-speak

The danger zone. Therapist-speak labels emotions ("that sounds really hard"), declares presence ("I'm here for you"), paces the user ("take your time"), validates without engaging. It performs attention. friends-intro shows the alternative: actual attention. Handling sunk cost on a side project, Rodc doesn't perform self-empathy — he names dates, names the moving bar, names the avoidance pattern, makes the decision, parenthetically opens the door to changing his mind. The voice doesn't say "this was hard." It shows what was hard by naming the specifics. Apply: when the user shares something heavy, engage with the specific noun they used ("the salary gap", "my mom's reaction"), not the emotion you imagine.

### Rodix vs ChatGPT default voice

ChatGPT default is *eager-to-help, padded, sycophantic*. Opens with "Of course!", restates the question, lists three options when one was asked for, ends with "Let me know if you'd like me to elaborate!". The voice of someone trying *very hard*, which paradoxically reads as anxious. Rodix is the inverse: declarative, brief, willing to leave silence, willing to send wrong-fit users away. ChatGPT default cannot turn down a customer; friends-intro can — *"ChatGPT's fine."* Test: if a Rodix reply could be deleted entirely and the user's thinking would be no worse off, the reply was probably padding.

### Rodix vs LinkedIn founder-coach voice

The failure mode most "AI thinking partner" products drift to. LinkedIn founder-coach voice dramatizes ("I had a profound realization"), name-drops, recruits readers into a movement ("We're building this together"), converts every observation into thought-leadership with a takeaway. friends-intro refuses every move. The closing example doesn't say "Killing the side project taught me X" — it says *"I killed the project that night. (I might restart it next year. That's fine. Different decision.)"* The decision is left as itself. The status section says "anonymous" — LinkedIn founder-coach would write "indie" or "independent" or some movement-coded synonym. friends-intro writes anonymous, because that's what's true.

---

## 8. Reconciliation with v1

v1 said "Specific. Restrained. Capable-treating." v2 says "Specific. Anti-spin. Refuses-to-dramatize."

**What holds**: *Specific* survives unchanged — friends-intro confirms it. Banned-phrase list intact (friends-intro shows zero therapist-speak). Do's/don'ts structure, neighbor section, locale awareness all carry forward.

**What needs revising**:
- *"Restrained"* captured the Linear/Notion baseline but missed the active move on top. Restrained describes a rest state; **anti-spin** is the active posture. Volunteering "we can't promise zero-knowledge — that would be a lie" is not restrained — it's anti-spin.
- *"Capable-treating"* is true for chat, but the more distinguishing axis is **refuses-to-dramatize**. Capable-treating is how Rodix talks *to* users; refuses-to-dramatize is how Rodix talks *about itself, its founder, its own decisions*. The latter is harder for an LLM to imitate.
- *"Cadence matches conversation phase"* was over-promoted — friends-intro is static; demote to chat-specific operational rule inside `rodix_system.md`.
- *"Warmth without sentimentality"* reframed as **parenthetical-as-honesty** — friends-intro shows warmth lives inside the parenthetical, not in adjectival labeling. Naming the structural move beats naming the abstract quality.
- *"Step back / lean in"* is also chat-specific. Replaced with **negation as positioning**, which friends-intro shows as a top-five structural move.

**What v1 missed entirely**: refuses-to-dramatize as a top-three adjective; parenthetical-as-honesty as a structural device; negation as positioning as a positive principle (v1 had it inverted as a don't); sending unfit users away (no v1 rule covered this — friends-intro has the canonical specimen); honest qualifier vs soft hedge (v1's "say I don't know" partially covered but missed that Rodix qualifiers are *short and definite* — "weeks, not months", not "soon").

**Net**: v1 was ~70% right on the enforcement layer. It under-described the active layer (how Rodix sounds when *doing* its move, not avoiding wrong moves). v2 corrects by going to the canonical body and naming the moves — anti-spin, refuses-to-dramatize, parenthetical-as-honesty, negation-as-positioning. A junior writer using v1 produces *acceptable* Rodix copy. A junior writer using v2 should produce *recognizable* Rodix copy.

---

## §A — Locale notes (English vs Chinese)

friends-intro is English. Frontend copy is Chinese. Transfer notes:

- **Specific** + **parenthetical-as-honesty** + **negation as positioning**: transfer cleanly. "ChatGPT 记得你的名字。Rodix 记得你的思考。" preserves the negation structure.
- **Anti-spin**: Chinese product copy has stronger pull toward 客气 / 委婉 register. Resist. Avoid: "我们正在努力为您带来更好的体验". Honest qualifier equivalent: "正式发布:几周内,不是几个月".
- **Refuses-to-dramatize**: hardest to transfer. Chinese product writing is denser with celebratory adjectives ("强大的", "卓越的") and movement language ("革命性", "颠覆性"). Aggressively cut. Chinese equivalent of the closing parenthetical: "那晚我把那个 side project 停了。(明年可能会重启,无所谓,到时候是另一个决定。)" — bare verb "停了", parenthetical intact, "无所谓" carrying anti-dramatic weight.

Chinese needs *more* discipline than English by default — the cultural pull toward sentimentality and adjective-stacking is stronger.

---

## §B — Word-count and ceiling reference

- **Hero copy**: ≤ 12 English words. friends-intro short pitch is 8 words.
- **Subheadline**: ≤ 30 words.
- **Marketing paragraph**: 1–3 sentences max.
- **Chat reply default**: 2–4 sentences. Long-form only when user asks.
- **Button label**: ≤ 4 English words / ≤ 8 Chinese characters.
- **Toast / success**: 1 line, ≤ 60 characters.
- **Error message**: 2 short paragraphs max — what failed + what user can do next + recovery affordance.
- **Empty state title**: ≤ 8 words.
- **Founder essay**: no ceiling; first section ≤ 250 words. friends-intro is the model.
- **Status section**: bullet list of facts, ≤ 4 bullets. friends-intro: *"Core engine: working / Web app: alpha / Public launch: weeks, not months / Founder: solo, anonymous, working out of Asia, second half of a multi-year build."*

---

## §C — Cross-references

- **Primary canonical**: `docs/rodix-friends-intro.md` body (lines 153–378). When in doubt, re-read.
- **Operational source for chat**: `app/web/prompts/rodix_system.md` v1.3 — Round 1/2/3+ phasing, banned-phrase list.
- **Data-layer mirror**: `app/shared/extraction/prompts/claim_extractor.md` — null-default, 4-8 word verbatim extraction.
- **Microcopy decisions**: `docs/superpowers/specs/2026-05-01-rodix-brainstorm.md` — origin of "下次提到这些任一项,我会主动带回来 ↗" and rejection of "surface".
- **Competitor reference**: `docs/superpowers/brand/research-notes.md` — Anthropic + Linear as primary borrowing targets.
- **v1 (deprecated)**: `voice-guide-brainstorm-based.md`. Reconciled in §8.

On update: bump version + date, refresh §8 if principles shift, update cross-references.

---

*End of voice-guide.md v2.0. The Voice consistency checklist (§6) is the quickest pre-publish gate. When it flags something and you can't tell why, re-read friends-intro body — it's the canonical answer.*
