# Product Hunt Launch Package

**Status:** Draft for Phase 1 alpha launch. Friends-intro register, calibrated slightly more conversational for PH maker-community warmth without losing the anti-spin discipline.

---

## Title (60-char ceiling)

> **Rodix — Memory layer for AI chat that's actually yours**

*(53 chars. PH titles are name + dash + clause.)*

---

## Tagline (60-char ceiling)

> **Cross-model AI memory. White-box cards. Real export.**

*(54 chars. Three short claims, no marketing verbs. Each claim corresponds to one of the four bets — Bet 2 / Bet 1 / Bet 4. Bet 3 (active recall) lives in the description below.)*

---

## Description (260-char ceiling)

> **ChatGPT remembers your name. Rodix remembers your thinking. Every conversation becomes a structured card you can read, edit, and export. Same memory works in any AI you use.**

*(178 chars. Friends-intro 8-word pitch verbatim as the lede. Mechanism named. No adjectives. Negation positioning preserved.)*

---

## First comment (founder note, signed)

*Posted by Rodc within 60 seconds of going live, pinned to top of comment thread.*

---

> Hi PH —
>
> I'm a heavy AI user. ~2-3 hours a day, across ChatGPT, Claude, Gemini, plus a few more. After a year of this, I noticed two things. First: my thinking didn't compound across conversations — every time I came back to a hard decision I'd been working out, I had to re-explain. Second: the "memory" features that were supposed to fix that made it worse. Gemini decided I was a corporate secretary because I asked one factual question about the role, then opened replies with "as a corporate secretary, you should…" for weeks. There was no way out of the wrong it had made.
>
> Rodix is the opposite. Every meaningful exchange becomes a card with four named fields — topic, concern, hope, open question. You read it, you edit it, you delete it, and you can see exactly which conversation produced it. Same memory works across whatever model you use. When you start a new conversation, Rodix searches your past cards before the AI generates, and surfaces relevant prior thinking as a visible recall callout. Export is one click, plaintext markdown — open it in Obsidian, paste it into Notion, throw it on a USB stick.
>
> Honest about what's not there yet: server-side recall (so this is not zero-knowledge, and won't pretend to be), encryption hardening on the post-launch roadmap, English-only at Phase 1, EU geo-blocked, single-user, desktop-primary. The actual ownership story today is markdown export. If you want what isn't built yet, fair — I'd rather you know.
>
> If you've ever re-explained a project to ChatGPT for the fifth time and felt the soul-tax — you're the user. If you ask AI "what's a good restaurant in Lisbon" twice a week and that's it, you don't need this. ChatGPT's fine.
>
> Solo, anonymous, working out of Asia, second half of a multi-year build. I'll be in this thread today — happy to walk through anything, get yelled at about whatever I missed.
>
> Founder essay if you want the long version: [link to founder-essay-draft.md publish target]
>
> — Rodc

*(389 words. Friends-intro register full-strength. Three paragraphs of substance, fourth is anti-target, fifth is status. No emoji. No exclamation. "Hi PH" replaces "Hi HN" — slightly warmer opener appropriate for the platform without drift.)*

---

## 5 prepared maker comments (responses to common questions)

### 1. Privacy / "is this end-to-end encrypted?"

> Fair to ask up front. Today: server-side recall with at-rest plaintext. So this is not zero-knowledge, and I'd rather say that out loud than ship "encrypted" copy that means something narrower than people think it means. Encryption hardening is on the post-launch roadmap; per-user keys are Wave 3, not Phase 1.
>
> The actual ownership story today is markdown export — one click, plaintext, your hard drive. That's the part that lets you leave with everything if I screw something up.
>
> If end-to-end is a hard requirement for you, totally reasonable — Rodix isn't there yet.

### 2. Pricing / "what's it cost?"

> TBD honestly, and I'd rather see how alpha goes before committing. Direction is likely a free tier (with caps on chat volume + active-recall fires) plus a paid tier for heavy use. Not committing to numbers yet — I'd rather price after I know what alpha users actually use, not what I guessed they'd use.
>
> If pricing surprises you negatively when it lands, complain loudly. Easier to fix while there are fewer of us.

### 3. Availability / "when can I actually use it?"

> Public launch: weeks, not months. Today is the alpha-list signup. If you ping me here or on the site, I'll add you. If you'd rather wait for the public open, also fine — I'll post when it's open, no drip-marketing in between.
>
> Currently English-only, EU geo-blocked (GDPR + personal-thinking data is a problem I don't have the legal capacity to do right), desktop-primary on the Web. Mobile responsive but the Phase 1 ammunition is desktop. PWA / Tauri / native iOS / Android are Phase 2 and Phase 3 — not soon, but not never.

### 4. Cross-model / "does this actually work in [Claude / GPT / Gemini]?"

> Yes — that's the whole point. The cards are stored on Rodix's side, tied to you, not to any specific model or any specific conversation. Claim extraction runs on Haiku 4.5 (OpenRouter) as the default ship config, but the chat layer is provider-agnostic. Switch the chat model, the vault still works. Switch your favorite model in six months when something better comes out, the vault still works.
>
> The structural reason this is hard for OpenAI / Google / Anthropic to ship: cross-model memory dissolves their LTV. They literally cannot ship it without harming their core business. So this bet was structurally available to an indie and not to them.

### 5. Open source / "is the code open?"

> Partial. The recall orchestrator and the extractor prompt are in a public repo — those are the load-bearing pieces, and I want them readable and challengeable. The full app stack isn't open source today; that's a Phase 2 question I'm leaving open while I figure out what shape makes sense.
>
> If you want to read the part where Rodix decides whether to bring back a memory, that's already public. If you want the whole stack, ask me again in a few months.

---

## 3 screenshot descriptions (for Rodc to capture)

### Screenshot 1 — Card with Promise UI (4 fields visible)

**File suggestion:** `card-with-promise-001.png`
**Aspect ratio:** 4:3 desktop crop, ~1600x1200.

Frame a single Vault card mid-detail-view. The four named fields visible top-to-bottom — Topic / Concern / Hope / Open Question. Field labels in muted secondary (`#a1a1aa`); field values in primary (`#fafafa`). Source attribution row at the bottom of the card: "From conversation on Sept 19" with a clickable link icon (Lucide `arrow-right`). The Promise pattern that brainstorm `#8` locked: each field, if populated, reads in the user's own wording (4-8 words preferred per `claim_extractor.md`). At least one field shown as null/empty — illustrates the null-default discipline.

PH thumbnail copy hint (if they ask): *"Every conversation becomes a card. You can read it, edit it, export it."*

### Screenshot 2 — ⚡ Active recall callout in chat

**File suggestion:** `recall-callout-002.png`
**Aspect ratio:** 4:3 desktop crop, mid-chat.
**Honest pre-screenshot label:** *"Coming next sprint — Wave 2 recall callout."*

Frame a chat thread mid-conversation. The user's message at top: *"thinking again about whether to kill the side project."* Below it, before the AI's reply, a recall callout card with the ⚡ glyph (single allowed emoji per brand book §6) and the locked copy `⚡ 我把这个带回来了` / English-mirror `⚡ I brought this back`. Inside the callout: a compressed reference to the prior card (the Sept 3 / Sept 19 / Oct 4 thread on side-project shutdown) with a "view source card" link. Action buttons row: `用上了 / 不相关 / 已经想过 / 跳过` (per brainstorm `#8` micro-adj 2 lock; current operational placeholders are `记下了 / 看了 / 不相关 / 忽略` per brand book §7b — flag in screenshot caption that this is the locked target copy, not the Wave 1b ship state).

PH-honest framing in the thumbnail caption: *"Active recall callout — shipping in next sprint. Today's alpha shows placeholder copy; locked target shown here."*

### Screenshot 3 — Vault detail with markdown export button

**File suggestion:** `vault-export-003.png`
**Aspect ratio:** 4:3 desktop crop.

Frame the Vault tab list view. Several cards visible (4-6) with sticky date headers showing temporal grouping (e.g., a "Last week" header with three cards underneath, an "Earlier this month" header with two cards). Each card shows topic + a short Concern preview line. The Export button in the top-right action area, Lucide `download` icon, label `Export to markdown` (English) / `导出为 Markdown` (Chinese). Hover state optional but ideal — preview tooltip text: *"Plaintext markdown. Your hard drive."* If the export-progress modal can be triggered for the screenshot, capture the moment showing "Exporting 47 cards..." mid-progress — quantifies the "real export" claim.

PH thumbnail copy hint: *"Export everything in one click. Markdown. Your file."*

---

## Hashtags / categories for PH submission

- Primary category: **Productivity** (closest fit — though Rodix is anti-engagement; PH category taxonomy doesn't have "thinking-tools" yet)
- Secondary category: **Artificial Intelligence**
- Tags: `AI memory` · `cross-model` · `markdown export` · `privacy` · `indie`

*(Skip "automation" / "agents" / "GPT wrapper" — none of these describe Rodix accurately.)*

---

## Posting day notes for Rodc

- Launch day window: 12:01 AM Pacific. Most active US-PH window 9 AM-12 PM Pacific.
- Pre-launch: ping the alpha list 24h ahead with "Rodix launches on PH tomorrow at 12:01 AM PT — if you have a PH account and want to upvote, the link will be in the morning email." No begging, no "please support me." If they liked alpha, they'll show up.
- Live-thread responsiveness: target < 30 min response window for the first 8 hours. PH judges hide replies that arrive 6 hours late.
- If a hostile comment lands ("this is just ChatGPT memory with extra steps"): one of the prepared maker comments above, polite, mechanism-first. No defending. No emotional response. If the comment is technically wrong, correct it once with evidence; if it's a values disagreement, name it as a values disagreement and move on.
- End-of-day post: brief thanks, no "made #1 on PH today!!!" If you placed top 5, say "honored, will keep building" and stop. No screenshot of the leaderboard.

---

*End ph-launch-package.md. Word counts: title 53, tagline 54, description 178, first-comment 389, 5 maker comments avg 110 each, screenshot descriptions ~150 each. Total package ~2,200 words. Friends-intro register held throughout — slightly more conversational than founder essay (PH community expects warmth) but no spin, no exclamation, no adjective stacks.*
