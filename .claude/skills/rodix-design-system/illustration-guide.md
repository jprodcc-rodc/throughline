# Rodix Illustration Guide

Rodix is anti-decoration. Most "design systems" need a long illustration guide because their products lean on visual flourish to carry warmth. Rodix doesn't. The Card with Promise carries the warmth; the type carries the hierarchy; the amber accent carries the verification register. Illustration is a distraction from the architectural commitments.

This guide is short because the answer is mostly *don't*.

---

## The rule

**Use images only for product UI screenshots.** Marketing illustration / 3D-glass effects / character-icons / abstract-shapes / aspirational-photography are off-brand.

The Card with Promise IS the visual identity. When Rodix needs an image, the image is a Card with Promise rendered in the actual product. That's it.

---

## What's allowed

- **Product screenshots** of the Card with Promise, Vault list, recall callout, settings — rendered in actual amber `#d97706` on warm-dark `#18181b` / surface `#27272a`. Inter font. Lucide line icons. Real example data, not "Lorem ipsum" / "User Name 1."
- **Card-as-specimen** photography. The card is the most-photographed Rodix object. Treat it like a museum specimen — centered, well-lit (in dark mode), no decoration around it.
- **Sticky date headers** in marketing layouts — borrowed from the Vault, used as section dividers in long-form (founder essay, HN post). The amber sticky-date register carries Rodix visual identity into long-form text.
- **The `⚡` glyph** in active-recall callouts. The single permitted emoji. Never decorative — only when speaking AS the AI character at recall trigger.

---

## What's not allowed

- **Marketing illustration.** No abstract gradient blobs, no "AI brain" iconography, no neural-network mesh visuals, no clouds-with-arrows.
- **3D-glass effects.** Notion-AI uses these; Rodix rejects them. Considered density, not maximalist UI.
- **Character icons / mascot art.** Rodix has no mascot. The product is the founder's voice, not a brand character.
- **Map / compass / journey iconography.** Explorer is a posture toward freedom, not a visual genre. No "your journey" visuals.
- **Granola handwritten warmth.** Sentimentality drift. Inter sans-serif resists this.
- **Stock photography.** No "diverse-team-around-laptop" / "person-thinking-by-window" / "city-skyline-at-night" filler.
- **Emoji decorations.** Single exception is `⚡` in recall callouts. No 🚀 / 🎉 / 🔥 / 🎯 / ✨ / 🧠 / 💡 / 📌 anywhere else.
- **Celebration animation.** No confetti, no springy save-success bounces, no rotating sparkles. Animations are functional (state transitions), not festive.
- **Author / founder portrait.** The friends-intro status section says *"anonymous, working out of Asia"* — operationalize that. Rodc does not appear in marketing assets.

---

## Whitespace

Whitespace is the Rodix illustration. Considered density at the level of Linear / Anthropic — restraint, not maximalism. Empty states should be real empty states with one-line hints, never encouragement walls.

When in doubt, remove the visual element. The word counts in `voice-guide.md` §9 apply: hero ≤ 12 words, paragraph 1-3 sentences. The same discipline applies to visual surface — if the image isn't load-bearing, cut it.

---

## Color application

The amber `#d97706` accent is the verification color. Apply it consistently:

- Card with Promise border (1px)
- Recall callout border (1px) + faint amber tint background (`rgba(217,119,6,0.05)`)
- Sticky date headers (small caps, weight 600)
- Source-card markers (`↗` link colors)
- Primary button background

Never decorative. Never as a gradient. Never on logo / brand mark. The amber consistency is what makes the Card with Promise legible across surfaces — once a user sees an amber 1px border, they know "this is a Rodix-verified object."

---

## Type hierarchy as visual hierarchy

Per `visual-tokens.json`:
- Hero text uses Inter weight 200, `clamp(2rem, 5vw, 3.5rem)`. The thin weight at large size is the Rodix visual signature.
- Body text uses Inter weight 400, 16px, line-height 1.6.
- Headings use Inter weight 600.

Type weight contrast carries hierarchy. Not box shadows. Not background gradients. Not decorative borders.

---

## Cross-references

- `visual-tokens.json` — colors / typography / spacing / component metrics.
- `component-patterns.md` — how each component renders these visual tokens.
- `docs/superpowers/brand/brand-book-v1.md` §6 — the locked tokens + brand reading of the choices (why amber over Raycast orange, why Inter, why no emoji).

---

## A note on the founder essay / long-form

When writing long-form Rodix content (founder essay, HN post, Twitter thread), the visual is type itself. Use the sticky-date-header pattern from the Vault to break sections — small-caps amber dates as visual rhythm. Body text in Inter weight 400. No pull quotes in decorative boxes; if a sentence deserves emphasis, the friends-intro pattern is to put it on its own line, blockquoted.

Friends-intro example:
> *"That's the whole thing."*

One sentence. Own line. No decoration. The sentence carries itself.

---

*The shortest possible summary of this guide: amber 1px border, Inter, no emoji, no marketing illustration. The Card with Promise is the visual identity.*
