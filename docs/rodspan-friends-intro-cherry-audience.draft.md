# Rodspan — Friends Intro (Cherry Studio audience draft)

> **Voice authenticity disclaimer (per spec §4.2):** This draft was authored by CC inheriting CC's interpretation of Rodc voice from prior brand artifacts (which were also CC-authored). Voice oracle authenticity is a standing question. Rodc may rewrite from raw Rodc voice samples (Twitter / journal / personal writing) for true voice reference before §A.3 marketing rewrites depend on this oracle.

> **Audience:** This draft targets the Cherry-Studio-adjacent power user — someone who already runs a BYO-API LLM chat client (Cherry Studio, LobeChat, TypingMind, ChatBox, AnythingLLM, Open WebUI, Msty, Faraday, Jan), brings their own OpenAI / Anthropic / OpenRouter key, and uses AI heavily enough that the gap in memory has become visible. NOT for friend cohort already invited to alpha. NOT for HN cold-launch.

---

# Rodspan

**LLM chat client with a memory layer. BYO-API. Cross-model. White-box. Yours.**

## The pitch in 30 seconds

If you're already running Cherry Studio, LobeChat, TypingMind, ChatBox, or any other BYO-API client, you've made the right structural choice. You pay LLM costs at-cost, your conversations don't train someone else's model, you keep model choice in your own hands. The current crop of clients does this well.

What they don't do is remember your thinking.

Cherry Studio gives you tabs and providers and a polished chat surface — and after three weeks of conversations across two providers about the same hard decision, you have ten threads, no through-line, and no way to surface what you concluded last month when you start the next conversation. The chat client is great. The memory is missing.

Rodspan is the BYO-API client with the memory layer built in.

- **White-box thinking cards.** Every meaningful exchange becomes one card with four named fields: topic, concern, hope, open question. Visible, editable, deletable, traceable to the conversation that produced it. No black-box tags, no inferred personas you can't see.
- **Active recall.** When you start a new conversation, Rodspan searches your past cards before the AI generates, and surfaces relevant prior thinking. The AI gets your real history, not a vendor's compressed guess. You skip the re-explaining tax.
- **Cross-model.** Switch from Claude to GPT-5 to Gemini at any time — the memory comes with you. Same cards, same recall, no vendor lock-in. (Same property Cherry Studio gives you on chat — extended to memory.)
- **Real export — markdown.** One click, plaintext markdown. Open it in Obsidian, paste it into Notion, throw it on a USB stick. Your data, your file. (TypingMind's export is JSON; we picked markdown because a JSON dump is portable on paper, not in practice.)

## Why this exists

I'm a heavy AI user. ~2-3 hours a day, across ChatGPT, Claude, Gemini, plus a few more. After a year of this, I noticed two things.

**Thing 1.** I kept losing my own thinking. I'd work through some hard decision with Claude over a week — career move, product call, relationship thing — and three weeks later I'd come back wanting to continue, except the conversation was buried, the threads were tangled, and I couldn't reconstruct what I had concluded without re-reading 80kb of chat. So I'd just start over. Re-explain everything. Get a slightly different answer. The thinking didn't compound — it reset every time.

**Thing 2.** The "memory" features that were supposed to fix this made it worse. Gemini decided I was a corporate secretary because I asked one factual question about the role. Then it kept opening replies with "as a corporate secretary, you should..." for weeks. There's no way to debug that. No source attribution. No real edit. ChatGPT's memory is the same — a few items it deigns to show you, plus an iceberg of inferred labels you'll never see.

The fundamental problem: vendors don't actually want you to own your AI memory. If your Claude memory worked in GPT, you'd switch tools whenever a better model came out. So they keep memory locked, opaque, and uneditable — by design.

The Cherry Studio crowd already saw the first half of this — that's why you switched away from native ChatGPT in the first place. BYO-API gives you back model choice, cost transparency, conversation ownership. But none of the BYO-API clients shipped a memory layer, so the tax of re-explaining stayed.

Rodspan is built on the assumption Cherry Studio implicitly makes about chat — **the data belongs to the user, the model is interchangeable** — and applies it to memory.

## What it actually does

Three things. That's it.

### 1. Cards, not tags

Every meaningful exchange becomes one structured card with four fields:

- **Topic:** What you're thinking about
- **Concern:** What worries you / what's hard
- **Hope:** What you want / what you're aiming for
- **Question:** What's still unresolved

You can read every card. Edit it. Delete it. See exactly which conversation produced it. This is the entire memory model. There are no hidden tags, no inferred personas, no shadow profile.

The four-field structure is enforced at extraction time, not added as post-hoc visualization. The extractor's core directive: *null is the default, not the failure case. Filling a field with invention is a critical failure.* A card with two fields populated is the product working correctly, not a degraded state. Rodspan's vault will look sparser than competitors who hallucinate plausible-looking content. That's a feature.

### 2. Active recall

When you start a new conversation, Rodspan searches your past cards before the AI answers. If something's relevant, it surfaces — here's what you were wrestling with three weeks ago about this exact thing, here's the question you left open. The AI gets your real context. You skip the re-explaining tax.

This is the part current "memory" features structurally can't do. They optimize for "personalization" (knowing your name, your job). Rodspan optimizes for **continuity of thought** — picking up where you actually left off. Recall thresholds are conservative on purpose; we'd rather miss a borderline recall than fire a wrong one.

### 3. Cross-model. Real export.

Same memory works across providers. The cards are yours, stored on your side. Switch models tomorrow, the memory comes with you.

Export is one click → markdown files. Not a JSON dump nobody can read. Markdown. Open it in Obsidian, paste it into Notion, throw it on a USB stick. Your data, your file.

## How Rodspan compares to what you're already running

Honest framing — Cherry Studio / LobeChat / TypingMind / ChatBox / AnythingLLM are all good products. They got the BYO-API economics right. Rodspan is in the same product category, with one specific addition.

| Feature | Cherry Studio | LobeChat | TypingMind | Rodspan |
|---|---|---|---|---|
| BYO-API (you bring the key) | yes | yes | yes | yes |
| Multi-provider (Anthropic / OpenAI / OpenRouter) | yes | yes | yes | yes |
| Cross-model conversations | yes | yes | yes | yes |
| **Built-in memory layer (white-box, structured cards)** | **no** | **no** | **no** | **yes** |
| **Active recall (surfaces prior thinking before AI generates)** | **no** | **no** | **no** | **yes** |
| Markdown export | partial | partial | JSON | yes (plaintext markdown is canonical) |

The difference is one row, but it's the row that matters when you're using AI as a thinking surface rather than a query box.

## Who's it for

If you've ever:

- Re-explained a project to ChatGPT (or Cherry Studio, or Claude) for the fifth time and felt the soul-tax
- Used three AIs for different things and wished they shared a brain
- Tried "AI memory" features and got mildly creeped out by what they assumed
- Wanted a record of how your thinking evolved on something hard, not just the answers

…you're the user. Bonus points if you've already configured Cherry Studio (or similar) with three providers and know what BYO-API saves you per month.

If you ask AI "what's a good restaurant in Lisbon" twice a week and that's it, you don't need this. ChatGPT's fine.

## What it's not

- **Not a journaling app.** You don't write into it. It writes itself from your AI conversations.
- **Not a knowledge base.** It's not for storing notes you've already organized. It's for capturing thinking as it happens, while it's still messy.
- **Not "better AI."** The AI underneath is whatever you choose. Rodspan is the layer on top — the memory, the continuity, the receipts.
- **Not a vendor lock-in.** You can leave any time, take everything with you, in markdown.
- **Not a Cherry Studio replacement for everyone.** If you're using Cherry Studio purely for chat-with-API-keys and don't have the memory tax, Cherry Studio is fine. Rodspan is for the slice of the BYO-API population who use AI as a thinking surface.

## How it actually works (technical, brief)

For people who'd ask:

- **Frontend:** Web app first. PWA. Desktop and mobile. Native desktop app (Tauri) coming after public launch. Mobile native after that.
- **API providers:** Bring your own key. Default config supports OpenAI, Anthropic, OpenRouter; can be extended. The chat layer is provider-agnostic; memory layer is too.
- **Memory pipeline:** Every conversation runs through (a) an intent classifier — chitchat / thoughtful / factual / safety; only thoughtful exchanges generate cards; (b) a claim extractor — pulls topic / concern / hope / question. Both with explicit accuracy gates and human-evaluated test sets, not vibes.
- **Active recall:** When you send a message, Rodspan searches your cards via embeddings + entity match. If anything relevant scores above per-type threshold (topic 0.65, stance_drift 0.70, loose_end 0.50, decision_precedent 0.60), it surfaces before the AI generates. Frequency capped at 1 per conversation, 3 per day at the free tier.
- **Storage:** Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture). Encryption hardening on the post-launch roadmap. Export is plaintext markdown — that's the actual ownership story.
- **Pricing:** Memory + UI layer subscription. Pricing band settling before public launch. LLM cost is on you (your key, your bill, our $0). This is the structural choice that lets us compete with Cherry Studio's free price point on the things you'd compare us on.

## A note on architecture (Open Core)

Rodspan SaaS is the commercial sibling of [throughline](https://github.com/jprodcc-rodc/throughline), the open-source memory layer for LLMs. Throughline is the algorithm canon — claim schema, drift detector, MCP server interface, single-user CLI — under MIT license. Rodspan SaaS imports throughline as a dependency, adds the multi-user UI layer, billing, cloud sync, and the polished chat client. Algorithm improvements default to OSS throughline so they flow back to OSS users; SaaS-specific features (UI, billing, sync) live in the private SaaS repo.

Why this matters to you: improvements to memory algorithm, claim schema, recall scoring, provider routing all live in OSS — verifiable, forkable, persistent. The commitment is that throughline OSS receives 5-10 hours/month maintenance while Rodspan SaaS is an active commercial product. If Rodspan ever ends, throughline doesn't disappear — it has a published sunset path (archive / transfer / fork).

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

*Built by Rodc · rodspan.app · @rodspan · sibling of [throughline](https://github.com/jprodcc-rodc/throughline)*
