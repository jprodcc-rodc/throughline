# Rodspan Brand Book — v1 (friends-intro-canonical)

**Status:** Master document. Reference for all subsequent brand, product, marketing, and copy work.
**Author:** brand-book-integrator (Phase 4 v2 re-run, integrating archetype-analysis v2 · voice-guide v2 · position-strategy v2).
**Date:** 2026-05-03.
**Primary canonical input:** `~/Downloads/rodix-friends-intro.md` body — Rodc's 1,350-word friend-version intro. The voice the body encodes is the voice this book must encode.
**Secondary inputs:** `archetype-analysis.md` v2 · `voice-guide.md` v2 · `position-strategy.md` v2 · `2026-05-01-rodspan-brainstorm.md` · `app/web/prompts/rodspan_system.md` v1.3 · `app/shared/extraction/prompts/claim_extractor.md` · `app/shared/recall/orchestrator.py` · `research-notes.md`.
**Supersedes:** `brand-book-v1-brainstorm-based.md` (preserved for audit; do not consume as input).

This document is the single source of truth for what Rodspan is, who it is for, how it sounds, and what it refuses to become. Where this book conflicts with a downstream artifact (mockup, marketing draft, founder essay), this book wins until explicitly amended. Where it conflicts with an upstream operational source (`rodspan_system.md`, `claim_extractor.md`, brainstorm sign-offs, the friends-intro), the operational source wins and this book updates to match. The friends-intro is the voice oracle; when in doubt about register, re-read it.

---

## 1. Rodspan in one sentence

> **ChatGPT remembers your name. Rodspan remembers your thinking.**

Eight words. From the friends-intro closing — *"That's the whole thing."* Adopt verbatim. This sentence does two specific jobs no longer formulation does as well. First, it inoculates against confusion with "personalization" features by establishing a different value-claim entirely: the contrast is not *amount* of memory but *type* of memory. ChatGPT-style personalization remembers a profile-of-user (name, job, dietary preference); Rodspan remembers continuity-of-thought (what you were working out, what you concluded, what you left open). A reader does not need to learn a new category — they position Rodspan relative to the thing they already know, and the difference is sharper in eight words than in twenty-two. Second, the sentence implicitly carries all four architectural bets (white-box cards, cross-model, active recall, real export) without listing them; downstream copy unpacks them, this hero does not.

The pitch is the thesis. Marketing copy will compress and unpack; every form must remain consistent with this contrast. No fabricated thresholds, no invented metrics — the thresholds and mechanism live in §3.3 and the architecture, not in the headline.

**Note on the name.** *Rodspan* is a coined compound: **rod** (founder pseudonym Rodc; phonetically a load-bearing structural element, the spine of a thing held together) + **span** (Old English *spann* — bridge across, extent of time, distance held between two points). The compound carries the brand bet directly: *the load-bearing span of your conversations with LLMs across time, models, and sessions*. The name does the work the pitch does — the contrast with ChatGPT-style profile-memory is not just stated, it is etymologically located. Empty-coined alternatives (the predecessor name *Rodix* among them) deferred this work to copy and visual identity; *Rodspan* lets the name itself encode the architectural commitment. Compound naming also fits LLM-client category convention (Cherry Studio / LobeChat / TypingMind / ChatBox all use compound names) — an underlying signal of what kind of product Rodspan is in the wider ecosystem.

---

## 2. Why Rodspan exists

> **The market created the problem Rodspan solves; Rodspan did not invent a problem to sell into.**

That sentence — distilled from the friends-intro reading guide — is the spine of why-now. The full argument runs through three datable signals from frontier vendors and one structural conclusion.

**ChatGPT memory shipped through 2024-2025 and revealed the negative space Rodspan occupies.** It was the largest possible distribution test of the AI-memory category, and it failed in a way OpenAI cannot fix without re-architecting ChatGPT itself. As the friends-intro frames the user experience: *"a few items it deigns to show you, plus an iceberg of inferred labels you'll never see."* The visible layer is a placation; the hidden layer is what actually shapes the model's behavior; the user has no surface for either auditing or correcting either layer. The result on Reddit and HN is a low-trust working relationship — turn it off, or leave it on while quietly distrusting it. ChatGPT's single-text-box UX has nowhere to put a vault primitive.

**Gemini personalization shipped and produced the "corporate secretary" failure mode.** From the friends-intro: *"Gemini decided I was a corporate secretary because I asked one factual question about the role. Then it kept opening replies with 'as a corporate secretary, you should...' for weeks. There's no way to debug that. No source attribution. No real edit."* This is not a bug. It is the predictable output of a personalization system designed around inferred-persona labels rather than user-controlled cards. The architecture made escape impossible by design.

**Claude projects shipped and proved the same pattern across all three frontier vendors.** Projects are the most user-respectful of the three incumbent attempts — named, scoped, somewhat editable — but share the structural defect: memory is locked to one vendor. *"Your ChatGPT memory means nothing in Claude. You change tools, you start over."*

The structural conclusion: all three vendors made the same fundamental architectural choice — memory belongs to the model, not to the user — because that choice is aligned with their business model (lock-in extends LTV) and incompatible with the user's interest (continuity across tools). Vendors do not actually want users to own AI memory. *"If your Claude memory worked in GPT, you'd switch tools whenever a better model came out. So they keep memory locked, opaque, and uneditable — by design."* Rodspan's bet is not that AI memory is an interesting category — every vendor has now confirmed it is. The bet is that the user-aligned implementation is structurally available only to a builder whose business model does not depend on lock-in.

---

## 3. Who Rodspan is for

The friends-intro's "Who's it for" section is the canonical answer; this book preserves its shape and quotes verbatim where it matters.

> **If you've ever re-explained a project to ChatGPT for the fifth time and felt the soul-tax. Used three AIs for different things and wished they shared a brain. Tried "AI memory" features and got mildly creeped out by what they assumed. Wanted a record of how your thinking evolved on something hard, not just the answers — you're the user.**

Each of those four conditions selects a heavy AI user who has already noticed something specific that Rodspan is built to fix. Not a general curiosity-seeker. Not an early adopter who tries every tool. Someone who has accumulated enough hours-on-keyboard that the cumulative tax of tool-switching, label-trapping, and re-explaining has become visible.

Concretely: an engineer thinking through a parent's cognitive decline at midnight; a designer mid-divorce trying to keep their working brain intact; a researcher who needs to think out loud about a paper without performing for a co-author; a heavy AI user (~2-3 hours/day across multiple providers) who has tried the incumbent memory features, found them mis-categorizing or opaque, and quietly turned them off. Whatever their job title, they evaluate AI products on whether the product respects their thinking — not on feature lists. They prefer "I don't know" plainly to confident-sounding filler.

**Anti-target — and the anti-target is brand-defining.** From the friends-intro:

> **If you ask AI "what's a good restaurant in Lisbon" twice a week and that's it, you don't need this. ChatGPT's fine.**

This sentence is not a funnel-optimization decision. It is the negation that defines the brand. Rodspan's voice will read as cold to users seeking comfort, sparse to users seeking automation, unimpressive to users seeking demo-grade wow. The fail mode of broadening into those segments is well-named in §6 (constraints): each accommodation is reasonable in isolation; eighteen months of saying yes produces a worse Notion with an AI sidebar. The user we want already opts out of generic AI products on instinct.

**Phase 1 launch geography.** English-speaking international, no Chinese market, no EU. EU is geo-blocked at the auth and routing layer (GDPR exposure on personal-thinking data). Phase 1 device priority is desktop Web primary; mobile responsive does just enough to not visibly break. PWA install and Tauri desktop are Phase 2 (launch+30); native iOS/Android are Phase 3 (launch+90). Target: ≤ 1,000 alpha users in the first 30 days. The brand book applies to every locale, but Chinese frontend strings need *more* discipline than English by default — the cultural pull toward sentimentality and adjective-stacking is denser.

**Product category and direct competitor.** Rodspan is an LLM chat client with a memory layer differentiator — same category as Cherry Studio, LobeChat, TypingMind, ChatBox, AnythingLLM, and the wider crop of BYO-API clients. It is *not* an LLM provider (ChatGPT / Claude / Gemini / Pi territory) and *not* a memory infrastructure tool (throughline OSS / mem0 / Letta — Rodspan is a chat tool that ships with memory built in, not a wrapper around other people's chat tools). Path A locked 2026-05-03: the user brings their own API key, Rodspan provides the chat client and memory layer, LLM cost is $0 to Rodspan. Direct competitor benchmark is Cherry Studio (free, open-source, no built-in memory). Differentiator wedge is the memory layer + interface polish on top of BYO-API economics.

---

## 4. Brand archetype

**Primary: Explorer. Secondary: Everyman (color, not core).**

The defining quality is sovereignty. Rodspan exists so the user's thinking is not captured, classified, or rented. Every value the friends-intro encodes points the same direction: portability over platform, evidence over credentials, "different decision" over commitment-as-identity. The voice is not pitching from a podium; it is comparing notes at a campfire.

**The 4-fold critique reads as a sovereignty manifesto.** Each indictment in the friends-intro names a specific way the user has been *contained* — cannot see, cannot edit, cannot leave, cannot extract — and the matching commitments (white-box cards, cross-model, active recall, real export) are framed as *exits*, not as illumination (Sage) or transformation (Magician). The pivot sentence is the giveaway: *"the memory belongs to the user, the model is interchangeable."* That is not a Sage's epistemic claim — it is an Explorer's claim about who owns the road and who is renting horses.

**The "Gemini decided I was a corporate secretary" passage is the Explorer's signature wound.** Caregiver would feel hurt; Sage intellectually offended; Rebel furious. Rodc's reaction is none of these. *"There's no way to debug that"* is not "they were wrong about me" — it is "I cannot get out of the wrong they made about me." The Explorer's defining nightmare is being classified into a box from which one cannot exit. The product Rodspan builds in response is escape infrastructure.

**"I killed the project that night. (I might restart it next year. That's fine. Different decision.)"** is Explorer cadence in pure form. No triumph (rejecting Hero), no extracted moral (rejecting Sage), no resolution (rejecting Caregiver). The Explorer treats decisions as paths, not oaths.

**Everyman as color.** Everyman shows up in register: peer-to-peer, anti-elite, evidence-not-credentials. *"I'm a heavy AI user. ~2-3 hours a day, across ChatGPT, Claude, Gemini, plus a few more. After a year of this, I noticed two things."* Solidarity, not authority. Kept secondary, Everyman keeps Explorer's authority warm rather than aloof. If Everyman were primary, Rodspan would tilt toward Mailchimp / Trello populism — wrong, since Rodspan is not democratizing a category, it is offering a narrow architectural alternative for a self-selected user.

**Operational implications.** Visual: warm dark + amber + Inter + Lucide line icons + zero emoji decoration. Voice: short paragraphs, parentheticals carrying honesty, em-dashes used precisely, anti-buzzword discipline, mechanism named directly. Messaging: hero ≤ 12 words; refusal of marketing language is the load-bearing pattern. Customer relationship: *equipped*. Not impressed (Magician). Not soothed (Caregiver). Not enlightened (Sage). Not mobilized (Rebel). The successful Rodspan moment is the user thinking "huh, I have my thinking with me now — the model is interchangeable, the memory is mine, I can leave whenever."

**Anti-implications — Explorer drift to avoid.** Explorer does NOT mean *aimless or commitment-phobic*. The export button is a guarantee, not an invitation to abandon. The brand encodes freedom-to-leave as the foundation of willingness-to-invest. Explorer does NOT mean *frontiersman cowboy / lone-wolf founder mythology*; the Everyman color prevents this drift. Explorer does NOT mean *travel as theme* — no map iconography, no compass metaphors, no "your journey" copy. Explorer is a posture toward freedom, not a visual genre. Explorer does NOT mean *anti-establishment posturing* — Rodspan critiques incumbents specifically and architecturally, never performs contempt. The frame is exit, not battle.

**The two-layer model — the load-bearing reconciliation.** Brand archetype operates at the Rodc-presents-Rodspan layer. The AI-companion-inside-Rodspan is a different character — a Sage-flavored Socratic interlocutor (per `rodspan_system.md` v1.3: Round 1 curious, Round 2 synthesizing, Round 3+ stops asking and reflects). This split is intentional and load-bearing. **Brand-as-Explorer** governs landing, founder essay, HN post, Twitter thread, support emails, marketing — every surface where Rodspan introduces itself. **AI-as-Sage-flavor** governs the in-product chat — how Rodspan behaves when the user is mid-thought. Both must be preserved. The brand archetype operates one layer up from the AI character. Voice writers and UX writers must know which layer they are working at; the operational guidance below in §5 spans both, with friends-intro voice carrying brand surfaces and `rodspan_system.md` carrying chat surfaces.

**Routing rule for transitional surfaces** — onboarding screens, error states, recall callouts, empty states, settings copy, and any other UI surface that is neither pure brand-introduction nor pure mid-thought-chat. Default to brand-Explorer voice (specific, anti-spin, refuses-to-dramatize) and let the AI-Sage-flavor only show when the surface speaks *as the AI character*. Test: ask "is this Rodspan-introducing-itself or Rodspan-thinking-with-the-user?" If the surface explains a system state ("we couldn't extract a card from this message"), it is Rodc-presenting-Rodspan → Explorer. If the surface speaks in first person mid-conversation ("Let me ask one more thing"), it is the AI-character → Sage. The recall callout `⚡ 我把这个带回来了` is the AI character speaking inside chat → Sage register. The vault-empty-state hint *"Your cards will appear here as you talk to Rodspan. We don't write them — your thinking does."* is brand-introducing → Explorer register. When in doubt, write Explorer; the AI character has the system prompt as its enforcement.

The transition into §5 — voice — is direct. Explorer's anti-lock-in posture and the friends-intro's anti-spin / refuses-to-dramatize voice are aligned: both refuse vendor narratives, both prize specificity over abstraction, both privilege user agency over system authority. Explorer is *what Rodspan is*; the friends-intro voice is *how Rodspan sounds*. They are the same value oriented two different ways.

---

## 5. Voice & tone

### Voice in three adjectives

> **Specific. Anti-spin. Refuses-to-dramatize.**

**Specific** — the rejection of generic phrasing. The friends-intro never goes vague when a concrete example fits: dates (Sept 3, Sept 19, Oct 4), counts ("200 hours in"), durations ("six weeks on the same fence"), exact quotes ("Thinking again about whether to kill the side project"). Specificity is structural — the same discipline `claim_extractor.md` enforces at the data layer ("Extract using user's own wording, 4-8 words preferred, do NOT paraphrase").

**Anti-spin** — states own limits plainly, sometimes volunteering them. The most distinctive sentence in the friends-intro: *"Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture)."* The voice volunteers a limitation no marketing copy would surface, and frames the alternative as a lie. *"Public launch: weeks, not months."* Not "launching soon!" *"Encryption hardening on the post-launch roadmap."* Names what isn't done yet without softening. Anti-spin is more active than restraint; the voice is willing to be quiet about achievements but is willing to volunteer limitations.

**Refuses-to-dramatize** — no triumph, no apology theater, no founder mythology. *"I killed the project that night. (I might restart it next year. That's fine. Different decision.)"* The decision is one short sentence. The parenthetical immediately undoes the finality without contradicting it. Status section: *"Founder: solo, anonymous, working out of Asia, second half of a multi-year build."* Four facts. No "scrappy", no "passionate", no "on a mission to". This is the hardest move for an LLM to reproduce, because models default to dramatizing.

### Five voice principles

**Principle 1 — Short paragraphs, hammered fragments.** Friends-intro paragraphs are 1-3 sentences. The negation list does its work as four hammered fragments — *"Black-box tags. Wrong, and you can't fix it. Locked to one vendor. Not actually yours."* — because each is a complete claim, not a soft transition. Compound sentences earn their length by carrying real specificity.
> *Verbatim:* "Three things. That's it."
> *Anti:* "Rodspan offers three core capabilities, each designed to work seamlessly with the others to give you a comprehensive thinking environment."

**Principle 2 — Parenthetical-as-honesty.** This is the most distinctive principle in the entire voice. Parentheticals qualify, soften, or undo a strong claim *without retreating from it*. The parenthetical carries the honesty — short, never decorative, used when the main clause is starker than the truth and the parenthetical brings the truth back into frame without weakening the claim.
> *Verbatim canonical demonstration:* "(I might restart it next year. That's fine. Different decision.)"
> *Verbatim:* "Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture)."
> *Anti:* "We're committed to privacy (well, mostly — there are some edge cases of course, but we're working on them)!" (Hedge-parenthetical that drains the claim. Note the exclamation mark — friends-intro uses zero.)

**Principle 3 — Negation as positioning.** The friends-intro positions Rodspan more often by what it is *not* than by what it is. The pitch opens with the four-fold negative critique of incumbents *before* Rodspan's four positives. The "What it's not" section is four hammered negations. Even "Who's it for" defines the anti-user by negation. Negation is not snark — it is position. Use when defining against a real adjacent thing the reader already knows.
> *Verbatim:* "Not 'better AI.' The AI underneath is whatever you choose. Rodspan is the layer on top — the memory, the continuity, the receipts."
> *Verbatim:* "ChatGPT remembers your name. Rodspan remembers your thinking."
> *Anti:* "Rodspan is the only AI memory platform that truly understands you, going beyond simple personalization to deliver real continuity." (Generic SaaS positive-only positioning.)

**Principle 4 — Specific over abstract, always.** When the friends-intro could go vague, it doesn't. User examples have dates, durations, sentence-quotes, outcomes. Competitor critiques name the company and specific failure mode. Mechanism explanations name actual data ("topic / concern / hope / question") not "structured insights." Time qualifiers are concrete ("weeks, not months", "200 hours in").
> *Verbatim:* "I'd work through some hard decision with Claude over a week … and three weeks later I'd come back wanting to continue, except the conversation was buried, the threads were tangled, and I couldn't reconstruct what I had concluded without re-reading 80kb of chat."
> *Anti:* "Users often experience continuity challenges when working with AI tools across multiple sessions." (Same content, zero specifics, swappable to any product.)

**Principle 5 — Honest qualifications, not soft hedges.** Qualifiers like "might", "fine", "I'd just start over", "weeks, not months" don't soften — they sharpen. Honest qualifiers are short and definite. They name a specific possible counter-state, not vague reservation.
> *Verbatim:* "Public launch: weeks, not months."
> *Verbatim:* "If you want early access, ping me. If you want to wait for public launch, also fine — I'll post when it's open."
> *Anti:* "We're working hard to bring this to you as soon as possible — stay tuned for exciting updates!"

### Seven do's

1. **Do open with the negation when defining against an adjacent thing.** *"Not 'better AI.' The AI underneath is whatever you choose."*
2. **Do volunteer your own limit when it's structurally honest.** *"Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture)."*
3. **Do qualify time concretely.** *"Public launch: weeks, not months."* Not "soon" / "shortly" / "in the coming months."
4. **Do name the specific competitor and the specific failure mode together.** *"Gemini decided I was a corporate secretary because I asked one factual question about the role. Then it kept opening replies with 'as a corporate secretary, you should...' for weeks."*
5. **Do use a parenthetical to undo the strongest part of a claim without retreating from it.** *"(I might restart it next year. That's fine. Different decision.)"*
6. **Do send unfit users away.** *"If you ask AI 'what's a good restaurant in Lisbon' twice a week and that's it, you don't need this. ChatGPT's fine."*
7. **Do let the example carry the argument — name a date, a count, a sentence-quote.** *"[Sept 3] Topic: Side project shutdown / Concern: Sunk cost — 200 hours in / Hope: Reclaim 6 hours/week / Open: Is the metric 'hours' or 'joy'?"*

### Seven don'ts

1. **Don't dramatize founder status.** Violating: *"After years of late nights, building from passion and conviction, I'm finally ready to share what we've created."* (LinkedIn founder-coach. Friends-intro: *"Solo, anonymous, working out of Asia, second half of a multi-year build."* Four facts, no mythology.)
2. **Don't celebrate your own product moves with adjective stacks.** Violating: *"We've built a beautiful, intuitive, powerful memory layer that seamlessly transforms how you think."* (Friends-intro never adjective-stacks Rodspan; it describes mechanism — "Three things. That's it.")
3. **Don't open with sycophancy in any language.** Violating: *"Great question! That's exactly the kind of thinking Rodspan is built for!"* / "好问题!" (Banned in `rodspan_system.md`.)
4. **Don't say "I'm here for you" / "我在这里" / "I'll keep you company" / "我陪你" / "Take your time" / "慢慢说" / "I hear you" / "I get it" / "That sounds really hard" / "无论是什么".** Therapist-speak in any language. Banned in `rodspan_system.md`. The English ban list extends the Chinese list by spirit, not just literal translation.
5. **Don't use process verbs that hide mechanism — "leverage" / "harness" / "unlock" / "supercharge" / "transform" / "surface" / "facilitate" / "utilize" / "enable".** ("surface" was specifically rejected in brainstorm `#8` micro-adj 2 in favor of the relational verb "bring back" / "带回来".)
6. **Don't soft-hedge time or status.** Violating: *"We're working diligently to bring you the best possible experience — stay tuned!"* (Friends-intro: *"Public launch: weeks, not months."*)
7. **Don't over-qualify into mush — parentheticals add information, they don't subtract conviction.** Violating: *"Rodspan is the best (well, we think so, and we're always open to feedback!) memory layer for AI chat."* Friends-intro parentheticals always *add* information.

### Three sample passages

**Sample 1 — Chat error message (extraction failed mid-conversation):**

> Extraction didn't run on your last message. The reply itself went through fine — only the card-saving step failed.
>
> If what you said was worth keeping, retry below. If it was passing chat, skip it; nothing's lost either way.
>
> *[ghost button]* Retry extraction

*(56 words. Names what failed and what didn't. Two real options including "skip it." "Nothing's lost either way" is the honest qualifier. Test: would Rodc write "We're sorry, something went wrong"? No.)*

**Sample 2 — Marketing tagline + supporting subhead (landing page hero):**

> **ChatGPT remembers your name. Rodspan remembers your thinking.**
>
> Every meaningful exchange becomes a card you can read, edit, and take with you — topic, concern, hope, open question. Same memory across every model you use; one click, markdown export, your hard drive.

*(Tagline verbatim from friends-intro. 45-word supporting block. Negation-by-comparison preserved. Mechanism named. Em-dash precise. "Your hard drive" is the anti-abstract closer. No "transform" / "supercharge" / "powered by". This sits next to "I killed the project that night" without register clash.)*

**Sample 3 — Support email reply (user: "I don't understand what just happened — your AI saved a card without asking?"):**

> Subject: re: that card
>
> Fair flag. The card was saved by Rodspan's extraction step, which runs after every message that names something specific (a worry, a goal, a question). The AI itself didn't decide to save it — extraction is a separate, fixed pass.
>
> You can delete the card from the Vault tab; deleting also removes it from future recall. Settings has a switch to turn auto-extraction off entirely. The switch should have been more visible from the start — that's on me, and the next release moves it.
>
> If anything else feels like Rodspan did something behind your back, send it. I'd rather hear it.
>
> — Rodc

*("Fair flag" opens with anti-spin acknowledgment, no apology theater. Mechanism named without softening. "That's on me" owns the design gap without dramatizing. Founder signature per friends-intro pattern.)*

### Quick voice ceilings

Hero copy ≤ 12 English words (friends-intro short pitch is 8). Subheadline ≤ 30 words. Marketing paragraph 1-3 sentences max. Chat reply default 2-4 sentences; long-form only when user asks. Button label ≤ 4 English words / ≤ 8 Chinese characters. Toast ≤ 60 characters. Error message: 2 short paragraphs max — what failed + what user can do next + recovery affordance. Empty state title ≤ 8 words. Founder essay: no ceiling; first section ≤ 250 words; friends-intro is the model.

---

## 6. Visual identity (provisional — defers to Task 9 Design System Skill)

This section sets the constraint envelope. Full visual spec is Task 9.

**Locked tokens (per brainstorm 2026-05-01):**
- Background `#18181b` (warm dark) · Surface `#27272a` · Text primary `#fafafa` · Text secondary `#a1a1aa` · Border `rgba(255,255,255,0.05)` · Accent `#d97706` (amber, deliberately NOT Raycast's `#ff5e1a` to avoid copy-cat optics) · Error `#ef4444` · Success `#22c55e`
- Font: Inter (Google Fonts, weights 2/3/4/6/7)
- Icons: Lucide line, 1.5-1.8px stroke, 16-18px (states) / 22-24px (navigation)
- Decoration rule: No emoji adornments. Lucide line icons replace emoji.

**Brand reading of these choices.**

*Dark-mode-default* implies the intimate / private / late-night-thinking register. Rodspan is for the user alone with their thinking, not a dashboard for a team. Light mode is not Phase 1 scope. The Explorer reading: a campfire-at-night gear-shop, not a daylight showroom.

*Amber `#d97706` accent* signals warm restraint, not loud premium. Amber is warmer than Linear's cool indigo (Explorer approachable, not aloof) and more grounded than Anthropic's pure greys. Amber is the verification color: applied consistently to badges, recall callouts, source-card markers, sticky date headers. It is never decorative.

*Inter font* is neutral, unspecific, global — matches the cross-model bet (no vendor flavor, no vertical signal). Sans-serif resists the 4-field-card sentimentality drift Granola's handwritten warmth would invite.

*No emoji adornments* is anti-cute, anti-decoration, trust-signaling. The single exception is the ⚡ glyph in the recall callout — an intentional, isolated flourish that reinforces the kept-promise register. Emoji elsewhere is incompatible with the brand.

**What Explorer implies for visual moves Task 9 should make.** Explorer means *considered terrain*, not *flashy frontier*. UI density at the level of Linear / Notion, not at the level of Notion-AI's 3D glass effects. Considered whitespace > maximalist UI. Resist Granola handwritten warmth and Notion 3D glass — both are emotional flourishes incompatible with Explorer's anti-spin posture. Empty states should be real empty states with one-line hints, never encouragement walls. State icons (loading / error / success) should feel procedural, not celebratory — the loading spec already specifies `通常 2-4 秒` only when load > 1.5s, with no celebration framing on success. Imagery (if used) favors terrain and tools over concept-art; no map iconography, no compass metaphors, no "your journey" visual genre.

*Visual identity full spec is Task 9. This section is the constraint envelope Task 9 must work within.*

---

## 7. Brand decisions log

These are the doors we close. Each is in the form: *Rodspan [is X / does Y / refuses Z]. This means we never [specific consequence].* Each should be sharp enough that a future product / marketing / copy team could fail an integrity check by violating it.

> **Decision 1: White-box thinking cards.** This means we never use opaque memory in the ChatGPT pattern ("I remember some things from our past conversations"). The user can see what the system has captured, edit it, delete it, export it. Every card has four named fields (topic / concern / hope / question), every card is traceable to the conversation that produced it, every card is editable and deletable. The Vault is a first-class top-tab equal-billing with Chat — not a settings page. There is no shadow profile. There is no inferred persona label the user cannot see. If any of these break, the bet breaks.

> **Decision 2: Cross-model.** This means we never lock memory to a single vendor. The same memory works whether the user is talking to GPT-5, Claude, Gemini, or whatever wins next year. We never ship a "GPT-only memory" or "Claude-only memory" feature. We never partner-exclusive on memory portability. Per the friends-intro: *"the memory belongs to the user, the model is interchangeable."*

> **Decision 3: Active recall — verb is "bring back," never "surface" or "personalization."** This means we never use "Rodspan surfaces…" or "Rodspan personalizes your experience." We never use opaque memory references like ChatGPT's *"I remember some things from our past conversations."* The relational verb "bring back" / "带回来" replaced the engineering verb "surface" in brainstorm `#8` micro-adj 2 and is locked. Active recall fires from one of four trigger types (topic / stance_drift / loose_end / decision_precedent) gated by per-type score thresholds (verified Wave 1b production: topic 0.65, stance_drift 0.70, loose_end 0.50, decision_precedent 0.60 per `app/shared/recall/orchestrator.py` `ThresholdConfig`). Thresholds tune against alpha telemetry; the verb does not.

> **Decision 4: Real export — markdown.** This means we never use JSON-only export disguised as portability. From the friends-intro: *"Not a JSON dump nobody can read. Markdown. Open it in Obsidian, paste it into Notion, throw it on a USB stick. Your data, your file."* Markdown is not technically superior; it is the only format where a non-engineer can verify their data is theirs. A JSON dump is an export-on-paper. The exporter (`app/shared/export/markdown_exporter.py`, `app/web/static/vault.js`) is shipped, not aspirational.

> **Decision 5: Null-by-default extraction.** This means we never invent fields to fill cards. Empty is correct. A 4-field card with two fields populated is the product working correctly, not a degraded state. From `claim_extractor.md` CORE DIRECTIVE: *"null is the default, not the failure case. Filling a field with invention is a CRITICAL FAILURE."* We accept that the vault will look sparser than competitors who hallucinate plausible-looking content. The economic logic: the cost of returning null when something exists is recoverable (user sees less); the cost of invention is not (user loses trust in the entire product).

> **Decision 6: Honest about architectural compromises.** This means we never claim zero-knowledge or end-to-end encryption when Wave 1b reality is server-side recall with at-rest plaintext. From the friends-intro verbatim: *"Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture). Encryption hardening on the post-launch roadmap. Export is plaintext markdown — that's the actual ownership story."* The actual ownership story is markdown export, not encryption-per-user. Per-user keys are Wave 3, not Phase 1. We never market what we have not yet built. Anti-spin is the discipline; this Decision is anti-spin operationalized at the highest-stakes claim.

> **Decision 7: Rodspan is for thinking, not for engagement.** This means we never optimize for time-on-app, daily-active-users, or message-volume metrics. We never ship a today view, a weekly summary, a streak counter, or a project-tagging system. We never recycle "what worries you?" / "what's the long-term goal?" across rounds (Round 3+ stops asking — `rodspan_system.md` v1.3 + S-CHAT-6). ChatGPT cannot ship this rule because engagement metrics reward turn count; Rodspan can ship it because retention depends on the conversation actually going somewhere. The metric we optimize for is whether the user's thinking compounded — verifiable later via card-revisit telemetry, recall engagement on the surfaced card, decision-resolution rate on loose-end cards. Until that telemetry is calibrated, the diagnostic is: if a new user's first session is task-shaped, the thesis is dead.

> **Decision 8: Open Core sibling of throughline OSS.** This means Rodspan SaaS (private commercial product layer — UI, auth, billing, multi-user, cloud sync, premium memory features) imports throughline OSS (public algorithm canon — `mcp_server`, `throughline_cli`, MCP server interface, single-user CLI) as a sibling-repo dependency, not a fork. Improvements to memory algorithm, claim schema, recall scoring, and provider routing default to OSS throughline so they flow back to the OSS user base; SaaS-specific features (UI / billing / cloud sync) live in the private rodspan-app repo. Three commitments lock this architecture: (a) throughline OSS receives 5-10h/month maintenance while Rodspan is an active commercial product (sunset clause if Rodspan ends), (b) layer boundary is decided at write-time per code change (no "I'll put it in SaaS for now"), (c) algorithm improvements default to OSS even when motivated by SaaS needs. Public communication may use the framing *"Rodspan is the commercial SaaS sibling of throughline (open-source memory layer for LLMs)"* — single sentence, OSS heritage as positive signal in HN / launch / about-page contexts. See `docs/superpowers/tasks/rodix-to-rodspan-rename.md` §15 for full commitment text.

---

## 7b. Brand commitments — implementation status

Section 7 lists the architectural-commitment bets. This section is honest about the gap (or lack thereof) between brand stance and shipped product. Each item below tracks the commitment + its current operational status.

- **⚡ Recall callout copy.** [Pending — Wave 2.] Brainstorm `#8` micro-adj 2 locked **"⚡ 我把这个带回来了"** / English **"⚡ I brought this back"** with action buttons `用上了 / 不相关 / 已经想过 / 跳过`. Wave 1b currently renders the placeholder header `记忆提醒 · 话题相关` (see `app/web/static/app.js` line 580: `header.textContent = '记忆提醒 · ' + recallTypeLabel(recallType);` with `topic: '话题相关'` at line 627) AND placeholder action buttons `记下了 / 看了 / 不相关 / 忽略` (vs the brainstorm-locked `用上了 / 不相关 / 已经想过 / 跳过`). Patching both header and buttons to the locked copy is a Wave 2 deliverable on `#active-recall-base`. The brand-level commitment stands; the operational implementation has known string-level gaps. Naming the gaps rather than over-claiming is itself the discipline.

- **Crisis-content handoff protocol.** [Shipped — Wave 1c, 2026-05-03.] The friends-intro positions Rodspan as for *thinking*, not therapy — and Decision 7 refuses Caregiver register. The brand stance holds across both shipped layers: when users present explicit safety language (existential-exhaustion or suicidal-ideation markers, English + Mandarin Phase 1 scope), Rodspan's chat reply surfaces 988 once — late in the reply, framed as offer not press, with preemptive self-demarcation honored via "if that shifts" framing — and the Vault captures the heavy moment as topic-only with concern/hope/question rows hidden via the Type-A 3 soft empty state ("Heavier than fields. (Topic line above is what you said.)"). Implementation surfaces: `app/shared/intent/classifier.py` (Layer 1 keyword + Layer 2 LLM judgment, `IntentClass.SAFETY` with `safety_demarcation` flag); `app/shared/intent/prompts/safety_classifier.md`; `app/shared/extraction/prompts/claim_extractor.md` v3.2 (Rule R1 user-text-only + Rule R2 crisis-content null rule); `app/web/prompts/rodspan_system.md` v1.4 (Crisis-content moments section, Pattern 1D-default + 1C-demarcated, extended banned-phrase list); `chat_claims.is_safety` schema column (v5 migration). See `docs/superpowers/specs/2026-05-03-wave1c.md` for the full spec.

- **Per-user encryption keys.** [Pending — Wave 3.] The actual ownership story today is markdown export, not encryption (see Decision 6). Per-user encryption is Wave 3 SaaS upgrade, not Phase 1. Marketing copy must not claim what Wave 3 will eventually ship. The friends-intro language *"Encryption hardening on the post-launch roadmap"* is the honest framing.

These items are why the brand book is honest: each commitment is tagged with [Shipped] or [Pending] and a wave reference. A reader should be able to tell the difference at a glance.

---

## 8. Five-year coherence test

What is true about Rodspan in 2031, when LLMs are commodity, every product claims AI memory, ChatGPT has shipped its 12th memory feature, and 5 well-funded competitors have launched?

**What stays true.** The four bets in §7 are architectural commitments, not features. They survive commodity AI because the failure modes they address are vendor-incentive failures, not technical failures. White-box transparent cards are still distinctive against any single dominant model's memory implementation, because every frontier vendor's metric tree continues to reward opacity. Cross-model is still distinctive because frontier-vendor unit economics still depend on switching costs. Real markdown export is still distinctive because vendor-built memory is still constrained by the LTV thesis. Active recall calibrated for trust rather than engagement minutes is still distinctive because every funded competitor still has to answer to growth metrics. The discipline survives any number of UI revisions and model swaps. The voice (anti-spin, refuses-to-dramatize, parenthetical-as-honesty) survives because it is founder-driven and structurally hard to clone.

**What evolves.** The implementation. The Inter / amber / Lucide visual system will be re-skinned. The 4-field schema (topic / concern / hope / question) may add or refactor fields based on extraction-quality data. The conversational-phase boundaries (Round 1 / 2 / 3) will tune. The recall thresholds (Wave 1b production: topic 0.65, stance_drift 0.70, loose_end 0.50, decision_precedent 0.60) will calibrate against alpha telemetry. The MCP surface, currently demoted to "second access surface for power users," may re-emerge or fade. Vault scale, model choice, UI density — all will move. None are brand-level commitments.

**What's at risk of becoming generic.** Three specific elements where competitors will catch up. (a) The 4-field card schema is not patent-defensible; a funded competitor reading this document could ship the same schema in two weeks. By 2031 multiple products will have structured memory cards. (b) Anti-buzzword copy and minimal dark UI will be table stakes. The Linear / Anthropic visual register will spread; Rodspan's restraint will look less distinctive in raw aesthetics. (c) Visible recall callouts (the ⚡ glyph + source card link) are an obvious UX move once articulated. Within 18 months at least one competitor will ship something near-identical. White-box claims specifically — every competitor will eventually claim transparency, even those whose architecture contradicts it.

**What protects Rodspan in 2031.** Per the friends-intro positioning: **architectural commitments competitors' business models contradict.** A funded competitor could in principle copy Rodspan in two weeks by reading this document, but could not actually ship the result without harming their existing product. OpenAI cannot ship cross-model memory because the lock-in is the LTV thesis. Anthropic cannot ship it for the same reason. Real markdown export is unavailable to any vendor whose retention depends on data-trap switching costs. Active recall calibrated for trust rather than engagement minutes is unavailable to any team whose corporate metric tree rewards engagement. Each of the four bets is a structural statement about whose interest the product is aligned with — and the other vendors are aligned the other way.

This is the *foreground* moat. Behind it: execution discipline + founder narrative + small-cohort word-of-mouth retention. Holding the lines in §7 is structurally hard for funded competitors. A team optimizing for the next round optimizes for wow. A team with a board cannot afford to refuse user requests for reasonable-sounding features. Rodc's constraint structure (single founder, no acquisition channel except word-of-mouth, no runway clock pushing toward demos) is what makes the discipline sustainable. The parenthetical-as-honesty voice and refuses-to-dramatize register are founder-driven and not reproducible by a marketing team. Rodc-as-visible-founder (HN posts, founder essay, signed support emails) is uncopyable in kind; a funded team with no specifically-Rodc voice cannot simulate it.

If by 2031 the discipline has eroded into accommodation — Rodspan has shipped a today view, softened the ban list, added celebration toasts, partnered exclusively with one frontier vendor for memory — the product has lost what made it distinctive and is competing in a category it cannot win against capitalized incumbents. The honest read: the moat is "we hold these lines longer than anyone with capital is willing to."

---

## Appendix — Reconciliation log

These are contradictions surfaced across inputs. Each was resolved deliberately for v2; Rodc may override any resolution in review.

**1. v1 archetype Sage primary vs v2 archetype Explorer primary.**
*Surface tension:* v1 (`brand-book-v1-brainstorm-based.md`) concluded Sage primary on the strength of `rodspan_system.md`'s Round 3+ reflection rule, `claim_extractor.md`'s null-default discipline, and the brainstorm `#8` "trust > wow" lock. v2 (this book) concludes Explorer primary on the strength of the friends-intro's 4-fold sovereignty critique, the Gemini "corporate secretary" passage, and the "different decision / fine" cadence.
*Resolution:* v1 was wrong — but specifically wrong by *layer collapse*. v1 read the in-product AI mechanics as if those were the brand archetype. They are the *AI character's* archetype within the product (Rodspan-the-AI-companion is correctly Sage-flavored when the user is mid-thinking — Socratic, restraint, round-3-stop-asking). The brand archetype operates one layer up. The brand is *Rodc presenting Rodspan*; the AI is *Rodspan behaving in chat*. v2 is the brand layer (Explorer); v1's Sage reading is preserved as the AI-character layer (correct for `rodspan_system.md` work, wrong for landing copy / founder essay / HN). §4 documents this two-layer model explicitly.

**2. v1 voice "Specific. Restrained. Capable-treating." vs v2 voice "Specific. Anti-spin. Refuses-to-dramatize."**
*Surface tension:* v1 inferred voice from the enforcement layer (banned-phrase list + brainstorm microcopy). v2 grounds voice in the friends-intro body, which the doc's reading guide names canonical: *"The voice IS this document."*
*Resolution:* The friends-intro evidence shifted three of the three adjectives. *Specific* survives. *Restrained* described a rest state; **anti-spin** is the active posture — volunteering "we can't promise zero-knowledge — that would be a lie" is not restrained, it is anti-spin. *Capable-treating* is true for chat but the more distinguishing axis is **refuses-to-dramatize**: capable-treating is how Rodspan talks *to* users; refuses-to-dramatize is how Rodspan talks about *itself, its founder, its own decisions* — and the latter is harder for an LLM to imitate. v2 also adds **parenthetical-as-honesty** as the most distinctive structural principle, which v1 had partially named ("warmth without sentimentality") but missed structurally.

**3. v1 pitch "AI chat that visibly remembers what you said and brings it back when it matters — built for thinking, not for engagement" (22 words) vs v2 pitch "ChatGPT remembers your name. Rodspan remembers your thinking." (8 words).**
*Surface tension:* v1's longer pitch is accurate in substance and earns its clauses. v2's friends-intro pitch is shorter, sharper, and more brand-on-voice.
*Resolution:* v2 is canonical because the friends-intro author used it ("That's the whole thing"). v1's longer formulation is preserved as a longer-form articulation suitable for founder essay or landing-page subhead, not for hero copy. The v1 sub-claim *"built for thinking, not for engagement"* survives in §3 anti-target framing and §7 Decision 7 — useful as the explicit articulation when the contrast needs unpacking, but not the hero.

**4. v1 fail modes (productivity-drift / therapy-drift / surveillance) vs v2 fail modes (incumbents-fix-one / users-don't-want-continuity / one-model-wins-decisively).**
*Surface tension:* v1's fail modes are CC-inferred internal-discipline risks. v2's fail modes are explicitly named in the friends-intro reading guide as the strategic threats embedded between the lines.
*Resolution:* v2 takes precedence. The three fail modes named by the reading guide (incumbents fix one of the four bets / users want quick answers not continuity / one model wins decisively) are the externally-facing strategic threats. v1's productivity-drift and therapy-drift remain real internal-discipline risks, preserved as voice / scope discipline in §3 anti-target and §7 Decision 7 — but they are not surfaced as *fail modes for position*. v1's surveillance-fail-mode (recall density flipping polarity at scale) is preserved as a Wave 2 calibration risk to be flagged in the `#active-recall-base` spec validation: *if alpha users describe Rodspan as "creepy" or "intrusive" rather than "trusty" or "thoughtful," the verification mechanism has flipped polarity — escalate to Rodc as P0 brand risk.*

**5. v1 fabricated 0.75 threshold vs v2 verified threshold values.**
*Surface tension:* v1 §1 (and a carry-over in v1 §8) referenced *"calibrated above 0.75"* for the recall threshold. This number does not exist anywhere in `app/`. The actual values in `app/shared/recall/orchestrator.py` `ThresholdConfig` are: topic 0.65, stance_drift 0.70, loose_end 0.50, decision_precedent 0.60.
*Resolution:* v2 cites the real values everywhere (§3 Decision 3, §8). The brand book commits itself to null-by-default discipline: when uncertain, see code, not invent a number. This is `claim_extractor.md`'s CORE DIRECTIVE applied to the brand book itself. v1's 0.75 was a critical-failure-mode invention; v2 corrects it.

**6. v1 moat "execution discipline + founder narrative + community" vs v2 moat "architectural commitments competitors' business models contradict."**
*Surface tension:* v1 framed the moat as how-well-Rodc-executes (real but copyable in principle by a sufficiently disciplined competitor). v2 frames the moat as what-kind-of-product-is-structurally-available-to-Rodc-that-is-not-available-to-frontier-vendors (not copyable without dismantling the competitor's product).
*Resolution:* Both true; v2 is the foreground story. The architectural-commitment frame is a structurally stronger defensibility argument because each of the four bets is incompatible with a frontier vendor's existing business model. v1's three elements (execution discipline, founder narrative, community) are *acquisition* and *behind-the-scenes* moats, not *defensibility* moats. v2 separates the layers in §8: architectural commitments are the foreground moat; execution discipline + founder narrative + small-cohort retention are behind it. **This is the Type-A escalation flagged in `position-strategy.md` v2 §8 for Rodc to confirm before launch positioning hardens.** Specifically: is the architectural-commitment frame the right hero-frame for the founder essay and landing page, or should the founder narrative lead and architectural commitments support? The friends-intro suggests architectural commitments lead and founder narrative supports; v2 follows the friends-intro. Rodc should confirm or revise.

**7. Brand archetype Explorer vs in-product AI voice Sage — both preserved.**
*Surface tension:* The brand book says Explorer is primary. The system prompt (`rodspan_system.md` v1.3) operationalizes a Sage-flavored Socratic interlocutor in chat (Round 1 curious, Round 2 synthesizing, Round 3+ stops asking and reflects). Are these contradictory?
*Resolution:* Two-layer model. **Brand-as-Explorer** governs how Rodspan introduces itself — landing, founder essay, HN post, Twitter thread, support emails, marketing copy. **AI-as-Sage-flavor** governs the in-product chat — how Rodspan behaves when the user is mid-thought. Both must be preserved. Voice writers and UX writers must know which layer they are working at. The brand archetype operates one layer up from the AI character, and the load-bearing test is: when in doubt about register on a *brand surface*, re-read the friends-intro; when in doubt about register on an *in-product chat surface*, re-read `rodspan_system.md` v1.3. §4 documents this split explicitly.

---

*End brand-book-v1.md (v2 friends-intro-canonical). Pending Rodc review. Reconciliation log items 4 (v1 surveillance-fail-mode preservation) and 6 (defensibility framing escalation) are the most underdefined and flagged for Rodc confirmation before §7 hardens.*

---

## v1 → v2 changelog (CC integration after Rodc located rodix-friends-intro.md mid-shift)

- §1 pitch: "thinking not engagement" (22 words) → "ChatGPT remembers your name. Rodspan remembers your thinking." (8 words, canonical from friends-intro)
- §1 thesis sentence: removed fabricated 0.75 threshold; cited verified Wave 1b values + null-default discipline.
- §3: replaced 12-noun "broadly construed" ICP list with friends-intro's 4-item "if you've ever..." passage + anti-target ("ChatGPT's fine.") quoted verbatim.
- §4: archetype Sage primary → Explorer primary (Sage retained as in-product AI voice flavor). Two-layer model documented explicitly. Everyman as secondary color (peer-to-peer, not populism).
- §5: voice 3 adjectives "Specific. Restrained. Capable-treating" → "Specific. Anti-spin. Refuses-to-dramatize." Parenthetical-as-honesty principle added (most distinctive structural move). Negation-as-positioning promoted from inverted don't to positive principle. Sample passages rewritten in friends-intro register.
- §7: Decision list restructured around the 4 architectural bets (white-box / cross-model / active-recall-verb / real export) + null-default + honest-about-architecture + thinking-not-engagement. Decision 5 (banned phrases) preserved operationally.
- §7b NEW: Brand commitments pending Wave 2 / 1c (recall callout placeholder, crisis protocol, per-user encryption). Honors the reality-gap finding from v1 review.
- §8: same coherence direction; updated to use 4-bets-as-architectural-commitments-moat framing. v1's "execution discipline + founder narrative + community" moved behind as second-layer moat.
- Reconciliation log: 7 entries documenting v1 → v2 shifts.

v1 author: brainstorm-based partial-input subagents (CC inferred voice from enforcement layer, archetype from in-product AI mechanics, fail modes from internal-discipline risks).
v2 trigger: Rodc located `~/Downloads/rodix-friends-intro.md` mid-shift — primary canonical voice doc that all three subagents v2 outputs are grounded in.
