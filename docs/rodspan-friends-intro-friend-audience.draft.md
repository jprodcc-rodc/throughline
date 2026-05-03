# Rodspan — Friends Intro (friend cohort audience draft)

> **Voice authenticity disclaimer (per spec §4.2):** This draft was authored by CC inheriting CC's interpretation of Rodc voice from prior brand artifacts (which were also CC-authored). Voice oracle authenticity is a standing question. Rodc may rewrite from raw Rodc voice samples (Twitter / journal / personal writing) for true voice reference before §A.3 marketing rewrites depend on this oracle.

> **Audience:** Friend cohort already invited to alpha (people who know me personally, have heard about the project from me directly, may not know what Cherry Studio is or care). Founder-note register, more personal, less competitor-positioning. NOT for cold-launch. NOT for HN.

---

# Rodspan

**Memory layer for AI chat. Cross-model. White-box. Yours.**

## What this is

You've heard me talk about this for a while. Quick refresher in case the last conversation was a month ago.

Every AI you use kinda remembers you now. ChatGPT memory, Gemini "personalization," Claude projects.

They all share the same broken design:

- **Black-box tags.** You can't see what they "remember" about you.
- **Wrong, and you can't fix it.** Once it decides you're a "vegan crypto investor," good luck unsticking that label.
- **Locked to one vendor.** Your ChatGPT memory means nothing in Claude. You change tools, you start over.
- **Not actually yours.** No real export. No portability. Their data, gated by their UI.

Rodspan is the opposite of all four:

- **White-box thinking cards.** Four fields per card: topic, concern, hope, open question. You see every one. Edit, delete, export.
- **Cross-model.** Same memory works whether you're chatting with GPT-5, Claude, Gemini, or whatever wins next year.
- **Active recall.** When you start a new conversation, Rodspan surfaces relevant past thinking before the AI answers, so the AI has your real context — not a vendor's compressed guess.
- **Real export.** One click, markdown files. Your hard drive. Your call.

If you've heard the older pitch and the name was *Rodix*, that was the working name through April. Renamed to Rodspan in early May per a brand audit — same product, the new name actually carries the brand bet (rod + span = the load-bearing span of your conversations across time and models). The audit memo is in the repo if you're curious. I won't make you read it.

## Why this exists

I'm a heavy AI user. ~2-3 hours a day, across ChatGPT, Claude, Gemini, plus a few more. After a year of this, I noticed two things.

**Thing 1.** I kept losing my own thinking. I'd work through some hard decision with Claude over a week — career move, product call, relationship thing — and three weeks later I'd come back wanting to continue, except the conversation was buried, the threads were tangled, and I couldn't reconstruct what I had concluded without re-reading 80kb of chat. So I'd just start over. Re-explain everything. Get a slightly different answer. The thinking didn't compound — it reset every time.

**Thing 2.** The "memory" features that were supposed to fix this made it worse. Gemini decided I was a corporate secretary because I asked one factual question about the role. Then it kept opening replies with "as a corporate secretary, you should..." for weeks. There's no way to debug that. No source attribution. No real edit. ChatGPT's memory is the same — a few items it deigns to show you, plus an iceberg of inferred labels you'll never see.

The fundamental problem: vendors don't actually want you to own your AI memory. If your Claude memory worked in GPT, you'd switch tools whenever a better model came out. So they keep memory locked, opaque, and uneditable — by design.

Rodspan is built on the opposite assumption: **the memory belongs to the user, the model is interchangeable.**

## What it actually does

Three things. That's it.

### 1. Cards, not tags

Every meaningful exchange becomes one structured card with four fields:

- **Topic:** What you're thinking about
- **Concern:** What worries you / what's hard
- **Hope:** What you want / what you're aiming for
- **Question:** What's still unresolved

You can read every card. Edit it. Delete it. See exactly which conversation produced it. This is the entire memory model. There are no hidden tags, no inferred personas, no shadow profile.

### 2. Active recall

When you start a new conversation, Rodspan searches your past cards before the AI answers. If something's relevant, it surfaces — here's what you were wrestling with three weeks ago about this exact thing, here's the question you left open. The AI gets your real context. You skip the re-explaining tax.

This is the part current "memory" features structurally can't do. They optimize for "personalization" (knowing your name, your job). Rodspan optimizes for **continuity of thought** — picking up where you actually left off.

### 3. Cross-model. Real export.

Same memory works across providers. The cards are yours, stored on your side. Switch models tomorrow, the memory comes with you.

Export is one click → markdown files. Not a JSON dump nobody can read. Markdown. Open it in Obsidian, paste it into Notion, throw it on a USB stick. Your data, your file.

## Who's it for

If you've ever:

- Re-explained a project to ChatGPT for the fifth time and felt the soul-tax
- Used three AIs for different things and wished they shared a brain
- Tried "AI memory" features and got mildly creeped out by what they assumed
- Wanted a record of how your thinking evolved on something hard, not just the answers

…you're the user.

If you ask AI "what's a good restaurant in Lisbon" twice a week and that's it, you don't need this. ChatGPT's fine.

## A real example

Here's me, last Tuesday.

I'm thinking about whether to keep building a side project or shut it down. I've been turning this over for two months. I've talked to AI about it maybe 12 times across two providers, plus my wife, plus a friend on a walk.

I open Rodspan. I say: *"Thinking again about whether to kill the side project."*

Rodspan surfaces three cards from the past 8 weeks:

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

Reading those three cards back-to-back, the pattern is suddenly obvious in a way it never was inside any single conversation: I keep moving the bar. September 3 it was hours, September 19 it was a signal, October 4 it was just-decide. I'm not actually torn. I'm avoiding the decision.

That's the kind of insight you can't get from any one conversation. You can only see it from the spine of conversations, which is what cards give you and what no current AI tool surfaces.

I killed the project that night.

(I might restart it next year. That's fine. Different decision.)

## What it's not

- **Not a journaling app.** You don't write into it. It writes itself from your AI conversations.
- **Not a knowledge base.** It's not for storing notes you've already organized. It's for capturing thinking as it happens, while it's still messy.
- **Not "better AI."** The AI underneath is whatever you choose. Rodspan is the layer on top — the memory, the continuity, the receipts.
- **Not a vendor lock-in.** You can leave any time, take everything with you, in markdown.

## How it actually works (technical, brief)

For people who'd ask:

- **Frontend:** Web app. PWA. Desktop and mobile. Native desktop app (Tauri) coming after public launch. Mobile native after that.
- **AI providers:** You bring your own API key (OpenAI / Anthropic / OpenRouter). Multiple keys at once is fine. The chat layer is provider-agnostic; memory layer is too. LLM cost is on your card (Rodspan doesn't bill for inference, only for the memory + UI layer).
- **Memory pipeline:** Every conversation runs through (a) an intent classifier — chitchat / thoughtful / factual / safety; only thoughtful exchanges generate cards; (b) a claim extractor — pulls topic / concern / hope / question. Both with explicit accuracy gates and human-evaluated test sets, not vibes.
- **Active recall:** When you send a message, Rodspan searches your cards via embeddings + entity match. If anything relevant scores above threshold, it surfaces before the AI generates. The AI sees your real history.
- **Storage:** Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture). Encryption hardening on the post-launch roadmap. Export is plaintext markdown — that's the actual ownership story.
- **License:** Subscription for the memory + UI layer. Pricing settles before public launch. The OSS algorithm canon (`mcp_server`, `throughline_cli`) is MIT-licensed and lives at github.com/jprodcc-rodc/throughline — you can self-host the memory layer if you'd rather.

## Status (honest)

- Core engine: working
- Web app: alpha
- Public launch: weeks, not months
- Founder: solo, anonymous, working out of Asia, second half of a multi-year build

If you want early access, ping me. If you want to wait for public launch, also fine — I'll post when it's open.

## The shorter pitch

**ChatGPT remembers your name. Rodspan remembers your thinking.**

That's the whole thing.

---

*Built by Rodc · rodspan.app · @rodspan*
