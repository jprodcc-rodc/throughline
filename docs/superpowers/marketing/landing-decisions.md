# Landing Page Decisions Log — Tier 2 Task 5

**Status:** Type-B decision log (subagent-internal decisions made within brand-book §6 envelope, not requiring Rodc escalation). Each item is a closed door. Type-A escalations (require Rodc input) are flagged separately at the bottom.

**Date:** 2026-05-03.
**Author:** marketing-landing-architect subagent.

---

## Type-B decisions (closed within envelope)

### D-LP-1. Single-page architecture, not multi-page.

**Decision:** One `index.html` carries hero, problem, what, who, how-it-feels, privacy, pricing, FAQ, footer. No separate `/about`, `/pricing`, `/privacy` pages on launch.

**Why:** Friends-intro is a single 1,350-word document. A reader who lands and starts reading should be able to read the whole story without losing flow to a navigation choice. Linear and Vercel use the same pattern for solo-product launch pages. Multi-page architecture is appropriate when there are multiple products; Rodix has one.

**Trade-off:** SEO loses some long-tail page surface area. Acceptable for Phase 1 (HN/Reddit launch is direct-traffic, not SEO).

**Reversibility:** Easy. Splitting later is mechanical.

---

### D-LP-2. Dark mode default, no light mode toggle.

**Decision:** Hardcoded dark theme via `color-scheme: dark` and `theme-color: #18181b`. No `prefers-color-scheme` media query, no toggle button.

**Why:** Brand-book §6 explicitly says dark-mode-default is Phase 1; light mode is Phase 2. The intimate / private / late-night-thinking register is what dark conveys. Adding a toggle now creates a maintenance surface (two themes to keep aligned) for a feature that doesn't move the needle Phase 1.

**Trade-off:** Some readers in bright daylight will find dark uncomfortable. Acceptable — they can use OS-level inversion as a fallback. The brand-book reading is that this user is reading at midnight anyway.

**Reversibility:** Add light tokens + media query in Phase 2. Token names are already abstract (`--bg`, `--text-primary`) so swap is one CSS file.

---

### D-LP-3. Vanilla CSS + minimal vanilla JS, not Tailwind, not a framework.

**Decision:** `design-tokens.css` is hand-written CSS with custom properties. The HTML is one `index.html` with one inline `<script>` block (~30 lines, IntersectionObserver fade-in). Zero build pipeline, zero npm dependencies.

**Why:** Per task brief — "no build pipeline; landing/index.html is standalone." Tailwind via CDN was offered as an option but Tailwind CDN is 3.4MB+ uncached for a single page that uses ~40 utilities total. Hand-written CSS sized to the page is faster, lighter, and matches the Wave 1a `tokens.css` pattern that already lives in `app/web/static/`. Keeping the same architectural register across app and landing is the point.

**Trade-off:** Adding a new component requires hand-writing CSS rather than dropping in `class="bg-zinc-900 text-zinc-50"`. Acceptable — the page is small, the conventions are established.

**Reversibility:** Tailwind could be added later if the marketing surface grows beyond a single page. Migration would be mechanical.

---

### D-LP-4. Card-mockup is CSS-rendered, not a screenshot.

**Decision:** The 4-field card stack in section 5 (Sept 3 / Sept 19 / Oct 4) is built with HTML+CSS, not a PNG export of the actual Vault.

**Why:** (a) Phase 1 ships fast, the live Vault has placeholder copy that's still being polished, and friends-intro screenshots would risk surfacing pre-final UI. (b) CSS-rendered cards are responsive — the same card stacks vertically on mobile and lays out as 2x2 grid per card on desktop, where a screenshot would either be cropped or pixel-distorted at small widths. (c) The CSS card uses the locked design tokens (`--accent`, `--surface`, `--border-amber-soft`) so the visual identity stays canonical. (d) The card content is the friends-intro side-project example (Sept 3 / Sept 19 / Oct 4) verbatim — using real friends-intro copy in the visualization is more brand-on-voice than a fresh-test-data screenshot.

**Trade-off:** Card-mockup doesn't show real product chrome (top tabs, icons, etc.). Acceptable — the section's job is to convey "what reading three cards back-to-back feels like," not "what the Vault tab UI looks like." A `vault-screenshot-desktop.png` is in the screenshots/README backlog for future use if visual proof becomes load-bearing.

**Reversibility:** Replace `<article class="card-mock">` blocks with `<img>` whenever a real screenshot is captured. CSS classes don't need to change.

---

### D-LP-5. FAQ uses native `<details>`, not a JS accordion.

**Decision:** Each FAQ entry is a `<details><summary>...</summary>...</details>` element. Custom-styled but functional with JS disabled.

**Why:** Native `<details>` is a built-in browser-supported disclosure pattern, accessible by default, works with screen readers, focusable via keyboard, and zero JS. Custom accordion components require ~80 lines of state management for the same outcome with worse a11y.

**Trade-off:** The expand/collapse animation is browser-default (instant in some, smooth in others). Acceptable — consistent UX across browsers is less important than guaranteed accessibility.

**Reversibility:** Easy. Custom accordion can replace `<details>` in one find-replace.

---

### D-LP-6. Subtle fade-in on scroll, IntersectionObserver-driven.

**Decision:** Sections after the hero use a `.reveal` class that translates 12px and fades in over 600ms when scrolled into view. Triggered once, then no further animation.

**Why:** Brand-book §6 explicitly says "minimal motion; subtle fade-in on scroll (NOT parallax / NOT 3D)." This implementation is the minimum that conveys intentional design without dramatizing. 12px translate is below the threshold of cinematic motion; 600ms is below the threshold of "this is a thing happening at me." `prefers-reduced-motion` is respected (no animation, instant visible).

**Trade-off:** Some readers won't notice the fade-in at all, in which case the page renders identical to a static page. That's fine — animation is decorative restraint, not decorative load-bearing.

**Reversibility:** Removing the `.reveal` class on each section makes everything render statically. One-line change.

---

### D-LP-7. CSS card border uses `rgba(217, 119, 6, 0.35)` (`--border-amber-soft`), not solid amber.

**Decision:** The 4-field card mockup has a soft amber border, not a solid `#d97706` 1.5px. New token added: `--border-amber-soft: rgba(217, 119, 6, 0.35)`.

**Why:** A solid amber border on a stack of 3 cards reads as "marketing illustration" — too loud, demands attention. A soft amber border reads as "this card has a subtle distinguishing feature" — restrained. The hover state strengthens the border to full amber to confirm the affordance. This matches brand-book §6: amber is the verification color, applied to cards / badges / recall callouts, but is "never decorative" — soft amber on the card edge is structurally correct (it identifies the card as a Rodix card) without being decorative.

**Trade-off:** A reader skimming may miss the amber border entirely on first scroll. Acceptable — the brand-book §6 reading is that amber is restraint, not signal-flag.

**Reversibility:** One token change.

---

### D-LP-8. "Try the alpha" CTA is a placeholder anchor (`#try`), not a working signup link.

**Decision:** Both primary CTAs (nav and hero) link to `#try` for now. The actual signup integration is downstream of Tier 1 Task 4 (pricing) and Wave 2 alpha launch.

**Why:** Landing page is "deploy-ready" per task brief, but the launch pipeline (signup form, payment, alpha-cohort gating) is not yet finalized. Hardcoding a placeholder is honest; using a fake-marked button is dishonest.

**Trade-off:** A user who clicks the CTA sees no feedback. Acceptable for pre-launch state. Pre-launch checklist must replace `#try` with the real signup URL before any marketing distribution (HN post / Twitter / etc.).

**Reversibility:** Find-replace `#try` → real URL. ~30 seconds.

---

### D-LP-9. No analytics, no tracking, no third-party scripts.

**Decision:** Zero `<script src="...">` tags pointing to external domains. No GA, no Plausible, no Fathom, no Sentry, no anything.

**Why:** Privacy posture per brand-book §6 + Decision 6 ("honest about architectural compromises"). Surveillance scripts on a landing page that markets "white-box memory, your data, your file" is brand-incoherent. Phase 1 alpha cohort can be measured via direct app telemetry once they sign up; landing page traffic estimation can be inferred from referrer logs server-side.

**Trade-off:** No conversion funnel visibility. Acceptable — Phase 1 has ~1,000 alpha cap; conversion data only matters for scale-up.

**Reversibility:** Trivial to add. Stays out by default.

---

### D-LP-10. Hero structures as 2-line `<h1>` with explicit `<br>`, not a single line.

**Decision:** "ChatGPT remembers your name." [BR] "Rodix remembers your thinking." rendered as two lines.

**Why:** Visual rhythm. The friends-intro punctuation is two sentences with a period between them, suggesting two beats. A single long line at full hero size would either (a) overflow on narrow viewports if not wrapped, or (b) auto-wrap at an arbitrary breakpoint that might split "ChatGPT remembers" / "your name. Rodix" — wrong cadence. Explicit `<br>` ensures the wrap always happens at the period, preserving the two-beat rhythm.

**Trade-off:** Slightly less responsive — at very narrow viewports both lines wrap further, but they wrap independently and never break the cadence between sentences.

**Reversibility:** Remove the `<br>`, accept the auto-wrap. Trivial.

---

### D-LP-11. Inter font via Google Fonts CDN, not self-hosted.

**Decision:** `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">`

**Why:** Wave 1a app/web uses the same Google Fonts CDN. Same approach for landing keeps the cache pattern consistent — a returning visitor who has already loaded Inter from the app will hit the same cached resource on the landing. Self-hosting Inter requires copying ~200KB of woff2 files into the static directory, which is fine technically but creates a sync surface (font version drift between app and landing).

**Trade-off:** Google Fonts is a third-party dependency. Slight tension with D-LP-9 (no third-party scripts) — Google Fonts is technically a third-party CSS URL. Acceptable because (a) the app already does this, (b) Google Fonts CSS doesn't track behaviorally, (c) self-hosting would require ongoing version sync.

**Reversibility:** Self-host Inter as a Phase 2 hardening if the third-party tension matters more later.

---

### D-LP-12. Pricing block uses `$TODO` placeholder verbatim, with explicit `<code>` TODO marker.

**Decision:** Pricing section shows literal "$TODO" inline with a clearly-marked code block: `TODO: replace with Tier 1 Task 4 final $X`.

**Why:** Per task brief — "If Task 4 not yet complete, write: 'Founder pricing for first 100 users: $X/mo, $Y/year' with TODO marker for Rodc to fill final $X." The literal `$TODO` is immediately visible and honest about pre-launch state, and the `<code>` marker block ensures the deploy pipeline cannot ship the page without surfacing the TODO. Friends-intro voice ("Public launch: weeks, not months") accepts admitting what isn't done; this is the same posture applied to pricing.

**Trade-off:** A pre-launch preview URL would show `$TODO` to anyone who lands on it. Acceptable — pre-launch is private (no distribution before pricing decided).

**Reversibility:** Find-replace `$TODO` → real number. Remove the `<code class="todo-marker">` block.

---

### D-LP-13. Self-review §4 finding ("eight seconds" fabrication) NOT auto-fixed in v1.

**Decision:** The original copy in §3 paragraph 1 says "you can fix it in eight seconds." Self-review found this fabricated. v1 file in `landing-copy-v1.md` preserves this finding visibly so Rodc can audit. The HTML file `index.html` has been updated to use the corrected language ("the card is right there in the Vault — open, edit, save").

**Why:** The voice review (self-review §4) is an honest audit per the task brief's reviewer compression instruction. Naming the weakest sentence is the point of the review; auto-fixing it without naming it would defeat the audit. Fixing it in the HTML output is correct because the HTML is the deploy surface; preserving the original in the markdown copy file is correct because the audit history is the value of the review.

**Trade-off:** v1 markdown and v1 HTML differ on this one sentence. Acceptable — the markdown is the audit-and-revision artifact; the HTML is the rendered deploy. They diverge at the moment review surfaces a fix, until the next markdown revision.

**Reversibility:** Fix the markdown to match the HTML. Trivial. Flagged for the v1.1 markdown revision pass.

---

## Type-A escalations (Rodc decision required)

These are decisions the subagent could not close within brand-book §6 envelope and surfaces to Rodc explicitly.

### A-LP-1. Final pricing — Tier 1 Task 4 dependency.

**Surfaced to Rodc:** Replace `$TODO` placeholder in §7 with final founder pricing. Friends-intro voice templates available in landing-copy-v1.md.

**Decision blocker:** Tier 1 Task 4 (pricing recommendation) not yet complete.

**Recommended path:** Once Tier 1 Task 4 lands, find-replace `$TODO` in `index.html` and `landing-copy-v1.md`, remove the `<code class="todo-marker">` block, ship.

---

### A-LP-2. Anonymity disclosure on landing — keep as FAQ Q8 or surface higher?

**Surfaced to Rodc:** Currently the founder anonymity is in FAQ Q8 ("Who's building this?"). It's not on the landing above-the-fold. The friends-intro Closing has the status section ("Solo, anonymous, working out of Asia, second half of a multi-year build.") at the end of the document, not the start. The landing follows that pattern — the question is FAQ-tier, not hero-tier.

**Decision question:** Should the founder anonymity be surfaced earlier (e.g., as a footnote under the hero, or as a pinned bar above the fold) given that anonymity is a real trust deficit per `assumption-list.md` W14?

**Default per friends-intro pattern:** Don't surface higher. The friends-intro placement is the canonical answer; the landing follows. Rodc may override if alpha-launch trust signals indicate users are bouncing on "who is this person."

**Reversibility:** Easy to add a `<p class="founder-strip">` directly below the hero CTA row in `index.html`.

---

### A-LP-3. "Try the alpha" CTA destination — to be defined.

**Surfaced to Rodc:** Currently both CTAs link to `#try` (anchor placeholder). Rodc to confirm the actual signup target.

**Recommended options:**
1. Self-hosted signup form on `rodix.app/signup`
2. Tally / Typeform / similar third-party form (note: tension with D-LP-9 if a tracking cookie is involved)
3. Direct-to-app signup at `rodix.app/app` (deepest funnel, requires the in-app signup flow to be ready)

**Decision blocker:** Alpha-launch signup pipeline not yet finalized.

---

### A-LP-4. Manifesto link — points to founder essay or HN post or both?

**Surfaced to Rodc:** "Read the manifesto" secondary CTA currently links to `#manifesto` anchor in the footer. The intended destination is the founder essay per `founder-narrative-arc.md`, but no URL is set.

**Recommended path:** Once the founder essay is published (likely as a long-form post on `rodix.app/manifesto` or as the HN Show post), set the anchor to that URL. Until then, the anchor scrolls to the footer (which references the manifesto) — acceptable as graceful degradation.

---

## Open questions (lower priority, post-launch reconsideration)

- **Mobile-first specific gestures:** swipe-to-expand FAQ? Probably no — `<details>` pattern is the floor. Reconsider in Phase 2.
- **Light mode:** Phase 2 deliverable per brand-book §6.
- **Internationalization:** Phase 1 is English only per `position-strategy.md` §6. Chinese landing is post-Phase-1, no committed date.
- **Accessibility audit beyond WCAG AA:** AA met; AAA contrast for primary text. Screen reader audit via NVDA / VoiceOver pre-launch.
- **Performance Lighthouse target:** Should hit 95+ on mobile given the file sizes (~30KB CSS + ~25KB HTML, no JS framework). Capture before launch.

---

*End landing-decisions.md. 13 Type-B closed; 4 Type-A surfaced. Type-A items are pre-launch blockers; the rest of the page is deploy-ready behind a placeholder signup target.*
