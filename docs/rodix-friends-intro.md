# Rodix — Friends Intro

> **Note for CC:** This document has two layers. The header below is an
> expert reading guide for Tier 0 Task 0a subagents. The body (starting
> at "Memory layer for AI chat") is Rodc's canonical friend-version
> intro — the voice this document encodes is the voice Rodix's brand
> book must match. Read the body as voice sample, read the header as
> task instruction.

---

## How to Read This Document — Expert Reading Guide for CC

This document is the canonical Rodix Phase 1 brand voice + position
artifact. It is Rodc's friend-version intro (~1,350 words), written
for peers — not for marketing, not for funders, not for HN. The voice
in the body below is the voice Rodix's brand book must encode.

### For Brand Archetype Analyst (Task 0a Subagent A)

Read for archetype signals in:

- **The 4-fold critique of incumbents** (white-box / cross-model /
  active recall / real export) is not a feature list — it is a
  values statement. Surface what archetype values: transparency,
  user sovereignty, intellectual continuity, anti-lock-in.
- **The "Gemini decided I was a corporate secretary" passage.**
  What archetype reacts to mis-categorization with this specific
  frustration? Not anger. Not contempt. A particular kind of
  "this was avoidable."
- **The "killed the project that night" closing example.** What
  archetype tells a decision story this way — matter-of-fact, not
  triumphant, with the qualifier "(I might restart it next year.
  That's fine. Different decision.)"? Note the parenthetical. Note
  the refusal to dramatize.
- **The honest status section.** "Solo, anonymous, working out of
  Asia, second half of a multi-year build." What archetype writes
  status this way?

Do not read as: Sage (too clean), Magician (too transformative),
Hero (too triumphant). The reasoning of your archetype choice
matters more than the verdict — show your work.

### For Brand Voice Extractor (Task 0a Subagent B)

The voice IS this document. Do not paraphrase it. Extract patterns:

- **Short paragraphs.** Most are 1–3 sentences.
- **Parenthetical asides.** "(I might restart it next year. That's
  fine. Different decision.)" — these carry weight, do not flatten
  them.
- **Em-dashes for emphasis**, used precisely, not decoratively.
- **Numbered or bulleted lists** when listing, but never to fake
  rigor — only when the list actually maps to discrete items.
- **Refusal of marketing language.** "Not 'better AI'", "not vendor
  lock-in", "Not a journaling app." The negation pattern is core
  voice.
- **Specific over abstract.** "I open Rodix. I say: 'Thinking again
  about whether to kill the side project.'" Not "users open the
  app and engage in reflective conversation."
- **Honest qualifications.** "weeks, not months" — not "launching
  soon!" The honesty is the brand.

Specifically attend to:

- How Rodc handles bad news: explicit, no spin.
- How Rodc handles competitor critique: specific, not snarky. Names
  ChatGPT memory, Gemini personalization, Claude projects, then
  shows what's broken about each. No mockery.
- How Rodc qualifies uncertainty: parentheticals, "might", "fine",
  "I'd just start over."
- How Rodc handles the technical section: brief, honest about
  architectural compromises ("we can't promise zero-knowledge —
  that would be a lie given the architecture").

The 3 sample passages your output must produce must come from this
document or be near-indistinguishable from it. If your samples sound
LinkedIn-y, founder-coach-y, or like ChatGPT trying to sound like a
founder, restart.

### For Brand Position Strategist (Task 0a Subagent C)

Three positioning frames already articulated in the body:

**Why now (specific, datable market moment):**
Vendor AI memory shipped recently — ChatGPT memory, Gemini
personalization, Claude projects. All broken in the same way:
opaque, uneditable, vendor-locked. The market created the problem
Rodix solves; Rodix did not invent a problem to sell into.

**Why me (evidence-not-credentials framing):**
Heavy AI user, ~2–3 hours/day, across multiple providers, for
about a year. Not framed as expertise. Framed as time-on-keyboard
that surfaces patterns a casual user wouldn't see. The two
"things I noticed" are the why-me.

**Why this (4 specific bets against incumbent design):**
1. White-box thinking cards (vs. black-box tags)
2. Cross-model (vs. vendor lock-in)
3. Active recall (vs. "personalization")
4. Real export — markdown, not JSON dump (vs. fake portability)

Each is a specific architectural commitment that competitors cannot
casually adopt because it contradicts their business model.

**Three fail modes are embedded but not stated.** Read between lines:
- Incumbents fix one of the four (but probably not — see "by design")
- Users don't actually want continuity of thought (they want quick
  answers) — possible
- Cross-model never matters because one model wins decisively —
  possible but not 2026 reality

Surface these three explicitly in your position-strategy.md output.

**Important constraints (avoid these in your strategy):**

- Do not assume BYOK is part of Phase 1 strategy. Phase 1 keeps
  provider strategy simple and unstated to user. BYOK is a possible
  later option, not a launch story.
- Do not commit to specific pricing in position. Pricing is Task 4's
  job; position should leave room for the pricing recommendation.
- Encryption: Phase 1 has at-rest plaintext; encryption-per-user is
  Wave 3 (post-launch). The body of this document mentions per-user
  keys aspirationally; do not extract that as current fact.

### What this document is NOT

- Not a complete brand book — that's your Task 0a output.
- Not the marketing landing copy — that's Task 5.
- Not the founder narrative arc — Task 0b extends this into a
  publishable narrative; this document is the source.
- Not a complete position-strategy — Subagent C produces the full
  version using this as foundation.

### Phase 1 launch context (already decided by Rodc + Opus)

- Phase 1 = English-speaking international launch (no Chinese
  market, no EU)
- Geo-block EU (GDPR + sensitive personal data exposure)
- Pricing band TBD (Task 4 will recommend)
- LLM provider: OpenRouter primary, Anthropic-direct fallback
  (split-route via env-var seam, default "anthropic")
- Solo founder, anonymous, working from Asia
- Target: ≤1,000 alpha users in first 30 days
- Wave 1b shipped (commit 53b56f0): claim extraction with Haiku 4.5
  via OpenRouter, eval gate passed (hallucination 2.3% / overall
  79.3% PASS / 11/14 strict gates)
- Wave 2 in planning tonight (your Task 1)
- Wave 3 SaaS upgrade in planning tonight (your Task 2)

---

# BODY — Rodc's Friend-Version Intro (canonical)

# Rodix

**Memory layer for AI chat. Cross-model. White-box. Yours.**

## The pitch in 30 seconds

Every AI you use kinda remembers you now. ChatGPT memory, Gemini
"personalization," Claude projects.

They all share the same broken design:

- **Black-box tags.** You can't see what they "remember" about you.
- **Wrong, and you can't fix it.** Once it decides you're a "vegan
  crypto investor," good luck unsticking that label.
- **Locked to one vendor.** Your ChatGPT memory means nothing in
  Claude. You change tools, you start over.
- **Not actually yours.** No real export. No portability. Their
  data, gated by their UI.

Rodix is the opposite of all four:

- **White-box thinking cards.** Four fields per card: topic,
  concern, hope, open question. You see every one. Edit, delete,
  export.
- **Cross-model.** Same memory works whether you're chatting with
  GPT-5, Claude, Gemini, or whatever wins next year.
- **Active recall.** When you start a new conversation, Rodix
  surfaces relevant past thinking before the AI answers, so the AI
  has your real context — not a vendor's compressed guess.
- **Real export.** One click, markdown files. Your hard drive.
  Your call.

## Why this exists

I'm a heavy AI user. ~2–3 hours a day, across ChatGPT, Claude,
Gemini, plus a few more. After a year of this, I noticed two things:

**Thing 1.** I kept losing my own thinking. I'd work through some
hard decision with Claude over a week — career move, product call,
relationship thing — and three weeks later I'd come back wanting to
continue, except the conversation was buried, the threads were
tangled, and I couldn't reconstruct what I had concluded without
re-reading 80kb of chat. So I'd just start over. Re-explain
everything. Get a slightly different answer. The thinking didn't
compound — it reset every time.

**Thing 2.** The "memory" features that were supposed to fix this
made it worse. Gemini decided I was a corporate secretary because I
asked one factual question about the role. Then it kept opening
replies with "as a corporate secretary, you should..." for weeks.
There's no way to debug that. No source attribution. No real edit.
ChatGPT's memory is the same — a few items it deigns to show you,
plus an iceberg of inferred labels you'll never see.

The fundamental problem: vendors don't actually want you to own
your AI memory. If your Claude memory worked in GPT, you'd switch
tools whenever a better model came out. So they keep memory locked,
opaque, and uneditable — by design.

Rodix is built on the opposite assumption: **the memory belongs to
the user, the model is interchangeable.**

## What it actually does

Three things. That's it.

### 1. Cards, not tags

Every meaningful exchange becomes one structured card with four
fields:

- **Topic:** What you're thinking about
- **Concern:** What worries you / what's hard
- **Hope:** What you want / what you're aiming for
- **Question:** What's still unresolved

You can read every card. Edit it. Delete it. See exactly which
conversation produced it. This is the entire memory model. There
are no hidden tags, no inferred personas, no shadow profile.

### 2. Active recall

When you start a new conversation, Rodix searches your past cards
before the AI answers. If something's relevant, it surfaces — here's
what you were wrestling with three weeks ago about this exact thing,
here's the question you left open. The AI gets your real context.
You skip the re-explaining tax.

This is the part current "memory" features structurally can't do.
They optimize for "personalization" (knowing your name, your job).
Rodix optimizes for **continuity of thought** — picking up where
you actually left off.

### 3. Cross-model. Real export.

Same memory works across providers. The cards are yours, stored on
your side. Switch models tomorrow, the memory comes with you.

Export is one click → markdown files. Not a JSON dump nobody can
read. Markdown. Open it in Obsidian, paste it into Notion, throw it
on a USB stick. Your data, your file.

## Who's it for

If you've ever:

- Re-explained a project to ChatGPT for the fifth time and felt the
  soul-tax
- Used three AIs for different things and wished they shared a brain
- Tried "AI memory" features and got mildly creeped out by what
  they assumed
- Wanted a record of how your thinking evolved on something hard,
  not just the answers

…you're the user.

If you ask AI "what's a good restaurant in Lisbon" twice a week and
that's it, you don't need this. ChatGPT's fine.

## A real example

Here's me, last Tuesday.

I'm thinking about whether to keep building a side project or shut
it down. I've been turning this over for two months. I've talked to
AI about it maybe 12 times across two providers, plus my wife, plus
a friend on a walk.

I open Rodix. I say: *"Thinking again about whether to kill the
side project."*

Rodix surfaces three cards from the past 8 weeks:

```
[Sept 3]
Topic:    Side project shutdown
Concern:  Sunk cost — 200 hours in
Hope:     Reclaim 6 hours/week
Open:     Is the metric "hours" or "joy"?

[Sept 19]
Topic:    Side project shutdown
Concern:  I'd miss the craft of it
Hope:     A clearer signal that it's worth continuing
Open:     What signal would change my mind?

[Oct 4]
Topic:    Side project shutdown
Concern:  I've been stuck on the same fence for 6 weeks
Hope:     Just decide
Open:     What does "stuck" tell me?
```

Reading those three cards back-to-back, the pattern is suddenly
obvious in a way it never was inside any single conversation: I
keep moving the bar. September 3 it was hours, September 19 it was
a signal, October 4 it was just-decide. I'm not actually torn. I'm
avoiding the decision.

That's the kind of insight you can't get from any one conversation.
You can only see it from the spine of conversations, which is what
cards give you and what no current AI tool surfaces.

I killed the project that night.

(I might restart it next year. That's fine. Different decision.)

## What it's not

- **Not a journaling app.** You don't write into it. It writes
  itself from your AI conversations.
- **Not a knowledge base.** It's not for storing notes you've
  already organized. It's for capturing thinking as it happens,
  while it's still messy.
- **Not "better AI."** The AI underneath is whatever you choose.
  Rodix is the layer on top — the memory, the continuity, the
  receipts.
- **Not a vendor lock-in.** You can leave any time, take everything
  with you, in markdown.

## How it actually works (technical, brief)

For people who'd ask:

- **Frontend:** Web app. PWA. Desktop and mobile. Native desktop
  app (Tauri) coming after public launch. Mobile native after that.
- **AI providers:** Cross-model from day one. Provider strategy
  details settle as we go.
- **Memory pipeline:** Every conversation runs through (a) an
  intent classifier — chitchat / thoughtful / factual; only
  thoughtful exchanges generate cards; (b) a claim extractor —
  pulls topic / concern / hope / question. Both with explicit
  accuracy gates and human-evaluated test sets, not vibes.
- **Active recall:** When you send a message, Rodix searches your
  cards via embeddings + entity match. If anything relevant scores
  above threshold, it surfaces before the AI generates. The AI sees
  your real history.
- **Storage:** Server-side recall (so we can't promise
  zero-knowledge — that would be a lie given the architecture).
  Encryption hardening on the post-launch roadmap. Export is
  plaintext markdown — that's the actual ownership story.
- **License:** Subscription. Pricing settles before public launch.

## Status (honest)

- Core engine: working
- Web app: alpha
- Public launch: weeks, not months
- Founder: solo, anonymous, working out of Asia, second half of a
  multi-year build

If you want early access, ping me. If you want to wait for public
launch, also fine — I'll post when it's open.

## The shorter pitch

**ChatGPT remembers your name. Rodix remembers your thinking.**

That's the whole thing.

---

*Built by Rodc · rodix.app · @rodix*
