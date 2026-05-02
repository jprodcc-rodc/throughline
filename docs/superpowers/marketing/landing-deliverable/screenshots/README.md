# Landing Page Screenshot Specs — for Rodc to capture

**Status:** Pre-launch. Landing currently uses no real screenshots; the 4-field card stack in section 5 is rendered in pure CSS as a working facsimile (close enough to ship, replaceable later with real Vault screenshots if desired).

This file lists the screenshots the landing *could* benefit from. None are blocking. Capture in the order below.

---

## 1. `og-card.png` — OpenGraph share card (1200 x 630)

Used by social platforms when the URL is shared (HN, Twitter, LinkedIn).

**Composition:**
- Background `#18181b`
- Centered: `Rodix` wordmark in Inter 700, ~80px, color `#fafafa`
- Below wordmark: tagline "ChatGPT remembers your name. Rodix remembers your thinking." in Inter 400, ~32px, color `#a1a1aa`, max width 900px
- Bottom-right subtle: `rodix.app` in Inter 500, ~16px, color `#71717a`
- No icons. No emoji. No gradient. No avatar.

**Why this composition:** Friends-intro voice is "the pitch is the thesis." OG card is the pitch, surface only. Anything more dramatizes.

**Tool suggestion:** Figma 1200x630 frame, export as PNG. Or Canva text-only template.

---

## 2. `vault-screenshot-desktop.png` — Vault tab with a few cards (recommended, optional)

Used as evidence in the "How it feels" section if/when desired (currently the section uses a CSS-rendered card stack and does not need a screenshot).

**Composition:**
- 1440 x 900 viewport
- Capture the live `app/web/static/index.html` Vault tab with 3-5 real cards already extracted
- 35/65 master-detail layout
- Cards visible in the left pane, one card detailed in the right pane
- Show the four fields (topic / concern / hope / question) rendered in the right pane
- Browser chrome OPTIONAL but if included, use Safari mac frame for warmth

**Capture steps:**
1. Run the local app, sign in, talk to Rodix for 3-4 thoughtful exchanges
2. Switch to Vault tab
3. Click on the most-meaningful card to open it in the detail pane
4. Capture the full viewport at 1440x900 (DevTools Device Mode = `Responsive 1440 x 900`)
5. Save as `vault-screenshot-desktop.png`

**Privacy:** Use real cards but check there's nothing personal that shouldn't ship publicly. If in doubt, generate a fresh test conversation that's clean.

---

## 3. `recall-callout.png` — Active recall in chat (optional, Phase 2 nice-to-have)

When Wave 2 #active-recall-base ships the locked `⚡ 我把这个带回来了` / `⚡ I brought this back` UI, this becomes the *single* most product-specific screenshot to surface in marketing.

**Composition:**
- Chat tab mid-conversation
- A recall callout visible — header `⚡ I brought this back`, source card link, dismiss/feedback buttons
- The user message above and AI reply below should be visible to show the in-conversation context
- 1200 x 800 capture, browser chrome optional

**Status:** Wave 2 deliverable. Don't capture yet — the current Wave 1b implementation has placeholder header `记忆提醒 · 话题相关` and placeholder buttons (per `brand-book-v1.md` §7b first item). Wait until the locked copy ships.

---

## 4. `mobile-vault.png` — Mobile responsive view (optional)

**Composition:**
- 390 x 844 viewport (iPhone 14 Pro size)
- Vault tab single-column collapsed
- A card visible in master view
- Tap-to-detail interaction visible if possible

**Why optional:** Phase 1 device priority is desktop primary; mobile is "responsive does just enough to not visibly break." Mobile screenshots aren't load-bearing for launch ammunition. Capture if natural.

---

## 5. `chat-thoughtful.png` — Multi-round thoughtful conversation (optional)

**Composition:**
- 1440 x 900 viewport
- Chat tab showing 3-4 turns of a Round 1 → Round 2 → Round 3 conversation per `rodix_system.md` v1.3 phasing
- The Round 3+ AI reply demonstrating the "stops asking, reflects" register

**Why optional:** Demonstrates the AI character (Sage-flavor) but landing is brand-introducing (Explorer voice) per the two-layer model in brand-book §4. The chat screenshot is more useful in product test scenarios documentation than on the landing page itself.

---

## What NOT to capture

- Onboarding screens. Onboarding is a private product surface; surfacing it in marketing creates expectation mismatch when alpha users don't get the landing-page version first.
- Empty states. They're correct product behavior but read as a "thin product" image to first-time visitors.
- Settings panel. Internal mechanism, low signal for landing visitor.
- Banner / error / loading states. Same reason.
- Animated GIFs or videos. Phase 1 is static-image-only landing per Linear/Anthropic restraint pattern.

---

## File naming + location

All screenshots live in `app/web/static/landing/screenshots/`. Use kebab-case lowercase. PNG for static, no JPG, no WebP for now (broadest tool compatibility for capture/edit cycle).

If a screenshot is sensitive (real card content, real conversation), consider scrubbing the email/name/specifics before commit. The `app/` directory is gitignored (per memory `feedback_commit_push.md` and `.gitignore`), but the safekeeping copy in `docs/superpowers/marketing/landing-deliverable/` will be tracked in git.

---

*End screenshots/README.md. Capture priority: 1 (og-card) > 2 (vault-desktop) > the rest. None blocking.*
