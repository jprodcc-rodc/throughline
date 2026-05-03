---
name: rodspan-design-system
description: Use when writing any Rodspan-facing copy or building Rodspan UI components — covers voice (Specific. Anti-spin. Refuses-to-dramatize.), visual identity (amber #d97706 + Inter + dark-mode-default), component patterns, and microcopy. Triggered by mentions of "Rodspan", "brand voice", "marketing copy", "landing page", "UI component", "design tokens", "microcopy", "Rodspan product", "founder essay", "support email", "empty state", "error message", "tooltip", "vault", "card", "recall callout", "onboarding".
---

# Rodspan Design System

## When to use

- Writing user-facing Rodspan copy: marketing, docs, microcopy, error states, empty states, tooltips, button labels.
- Building Rodspan UI components: Card with Promise, Vault list, recall callout, settings modal, onboarding screens.
- Creating Rodspan marketing assets: founder essay, HN post, Twitter thread, landing page hero.
- Reviewing whether a deliverable is Rodspan-coherent (voice, visual, layer routing).
- Designing onboarding / chat / vault / decisions surfaces.

## Quick reference

- **Brand archetype:** Explorer (primary) + Everyman (secondary, color only).
- **In-product AI character:** Sage-flavored Socratic (per `app/web/prompts/rodspan_system.md` v1.3 — Round 1 ask, Round 2 maybe, Round 3+ stop asking and reflect).
- **Voice in 3 adjectives:** Specific. Anti-spin. Refuses-to-dramatize.
- **Most distinctive principle:** Parenthetical-as-honesty. The parenthetical undoes the strongest part of a claim without retreating from it. *"(I might restart it next year. That's fine. Different decision.)"*
- **Visual signature:** Considered density (Linear / Anthropic restraint, NOT Notion-3D-glass). Amber `#d97706` accent on warm-dark `#18181b` / surface `#27272a`. Inter font. Lucide line icons. Zero emoji decorations.
- **Canonical pitch:** "ChatGPT remembers your name. Rodspan remembers your thinking." (8 words, friends-intro verbatim, hero-locked.)
- **Ship gate:** Apply the 5-question consistency checklist (`voice-guide.md` §6) before any user-facing copy ships.

## The 7 don'ts (operational; never ship)

1. **NO McLuhan "we shape our tools" anchor.** Saturated by Granola + Notion. Rodspan doesn't borrow it.
2. **NO LinkedIn-y verbs:** *empower, leverage, supercharge, harness, unlock, transform, surface, facilitate, utilize, enable, 10x.* "surface" was specifically rejected in brainstorm `#8` micro-adj 2 in favor of relational "bring back" / "带回来".
3. **NO Caregiver register:** *I'm here for you, I hear you, take your time, 慢慢说, 我陪你, that sounds really hard, whatever it is, 无论是什么.* Banned in `rodspan_system.md` and extended by spirit, not just literal translation.
4. **NO ChatGPT-default opener:** *Of course!, Great question!, 好问题!, I understand,, 当然,*. Filler clauses go before substance — kill them.
5. **NO emoji decorations.** The single exception is `⚡` for the active-recall callout. No 🚀 / 🎉 / 🔥 / 🎯 / ✨.
6. **NO over-claiming security:** never *"zero-knowledge encrypted"* or *"end-to-end encrypted"* in Phase 1 — server-side recall is the truth. Per Decision 6: *"Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture)."* Encryption hardening is post-launch roadmap.
7. **NO streak counters / engagement metrics / today view / weekly summary.** Decision 7 — Rodspan is for *thinking compounding*, not engagement. We never optimize for time-on-app, DAU, or message volume.

## Files in this skill

- `voice-guide.md` — 5 voice principles + 7 do's + 7 don'ts + 3 sample passages + 5-question checklist + neighbor distinctions.
- `visual-tokens.json` — colors / typography / spacing / component metrics (programmatic).
- `component-patterns.md` — Chat bubble · Card with Promise · Vault list · Vault detail · Recall callout · Settings modal · Onboarding 3-step.
- `microcopy-patterns.md` — Error / empty / tooltip patterns + 3-5 examples each, sourced from `app/web/static/copy/*.json`.
- `sample-passages.md` — 3 voice samples (chat error · marketing tagline · support email reply).
- `illustration-guide.md` — Minimal visual style. Rodspan is anti-decoration; image use is for product UI screenshots, not marketing-illustration.

## Two-layer model — load-bearing

Rodspan has two voice layers; routing the wrong one to the wrong surface is the most common failure mode.

- **Brand-as-Explorer** (sovereignty / anti-lock-in / matter-of-fact / parenthetical-as-honesty) — governs *landing pages · founder essay · HN post · Twitter thread · support emails · marketing copy · docs · onboarding · empty states · error states · tooltips · button labels*. Anywhere Rodspan introduces itself or explains a system state.
- **AI-as-Sage-flavored** (Socratic / Round 1 ask / Round 2 maybe / Round 3+ stop asking and reflect) — governs *in-product chat replies* per `app/web/prompts/rodspan_system.md` v1.3. Anywhere Rodspan speaks AS the AI character mid-conversation.

**Routing test:** "Is this Rodspan-introducing-itself, or Rodspan-thinking-with-the-user?" If it explains a system state ("we couldn't extract a card"), it's Explorer. If it speaks first-person mid-conversation ("Let me ask one more thing"), it's Sage. The recall callout `⚡ 我把这个带回来了` is the AI character speaking inside chat → Sage. The vault-empty-state hint *"Your cards will appear here as you talk to Rodspan. We don't write them — your thinking does."* is brand-introducing → Explorer.

When in doubt, write Explorer; the AI character has its system prompt as enforcement.

## Related skills

- `frontend-design` — for HTML / CSS implementation patterns and high-quality production frontends.
- `claude-api` — when integrating the Anthropic SDK for chat / extraction / recall calls.

## Verification before shipping

Before any Rodspan-facing copy ships, walk the 5-question checklist (`voice-guide.md` §6):

1. **Parenthetical or em-dash test.** Does this paragraph contain a parenthetical aside or em-dash, used precisely (not decoratively)? If a long paragraph has neither, ask whether the strong claim should be honestly qualified.
2. **Negation-as-positioning test.** Does any negation appear, and is it positioning a specific neighbor the reader already knows (ChatGPT memory / Gemini personalization / journaling apps)? Copy that defines itself only by positives is missing the friends-intro structural move.
3. **Specificity test.** Does the copy quote, name, or count a specific thing — the user's word, an actual number, a sentence-quote, a date, a duration? If it could be search-and-replaced into another product without changing meaning, it fails.
4. **Founder-recognition test.** Would Rodc recognize this as his own writing? Read aloud. Wrong-answer tells: triple-clause padding, "Let's unpack this," self-explaining metaphors, exclamation marks, *transform / amazing / delightful / journey*.
5. **Anti-target test.** Would the unfit user be sent away clearly, or coaxed? If the copy reads like "anyone can benefit," it's not Rodspan. Rodspan says: *"ChatGPT's fine."*

If any of the five fail, return to `voice-guide.md` and re-shape. If you're stuck, re-read the friends-intro passages quoted in `sample-passages.md`.

## Decisions log (the doors that are closed)

These are the lines Rodspan holds. Any deliverable that violates one of these is not Rodspan-coherent — even if it sounds nice.

- **Decision 1 — White-box thinking cards.** Never opaque memory. Every card has 4 named fields (topic / concern / hope / question), every card is editable / deletable / exportable. The Vault is a top-tab equal to Chat, not a settings page.
- **Decision 2 — Cross-model.** Memory works whether the user is on GPT, Claude, Gemini, or whatever wins next. Never partner-exclusive on memory portability.
- **Decision 3 — Active recall verb is "bring back" / "带回来"**, never "surface" / "personalize". Per brainstorm `#8` micro-adj 2.
- **Decision 4 — Real export = markdown.** Never JSON-only. *"Open it in Obsidian, paste it into Notion, throw it on a USB stick."*
- **Decision 5 — Null-by-default extraction.** Empty fields are correct. *"Filling a field with invention is a CRITICAL FAILURE."*
- **Decision 6 — Honest about architectural compromises.** Server-side recall today, encryption hardening on roadmap. Never market what isn't yet built.
- **Decision 7 — For thinking, not engagement.** No today view, no weekly summary, no streak counter, no project-tagging system.

## Cross-references for full depth

When the skill's operational shortcuts aren't enough, return to the source:

- **Brand book** — `docs/superpowers/brand/brand-book-v1.md` (master document, friends-intro-canonical).
- **Voice guide v2** — `docs/superpowers/brand/voice-guide.md` (full 5-principle treatment).
- **Friends-intro** — primary canonical voice doc. When in doubt about register, re-read it.
- **System prompt** — `app/web/prompts/rodspan_system.md` v1.3 (in-product AI character).
- **Extraction prompt** — `app/shared/extraction/prompts/claim_extractor.md` (null-default + verbatim 4-8 word extraction).
- **Microcopy source** — `app/web/static/copy/{errors,empty-states,tooltips}.json`.
