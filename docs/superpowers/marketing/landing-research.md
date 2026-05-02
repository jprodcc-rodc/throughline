# Landing Research Synthesis — Tier 2 Task 5

**Status:** 1-page synthesis. Tier 0 research-notes encodes Anthropic + Linear as primary borrowing targets; this doc names the specific moves we adopt.

---

## What carries over from Tier 0

`brand-book-v1.md` §6 already locks the visual constraint envelope: `#18181b` warm dark, `#27272a` surface, `#fafafa` text-primary, `#a1a1aa` text-secondary, `rgba(255,255,255,0.05)` border, `#d97706` amber accent (deliberately not Raycast `#ff5e1a`), Inter weights 2/3/4/6/7, Lucide line icons 1.5px stroke, zero emoji adornments. Wave 1a `tokens.css` already implements this exactly — landing-page CSS borrows the token names verbatim so the design system stays single-source.

Anthropic + Linear were named primary borrowing targets in `research-notes.md`. The traits we keep: monochromatic base, generous whitespace, no auto-playing video, no gradient backdrops, no exclamation points, no ALL CAPS, dramatic typographic hierarchy carrying the structural work, body text held to 2-3 sentence blocks, static product screenshots framed inside cards rather than parallax-floated. The trait we don't borrow: Linear's headline-repetition gimmick — friends-intro voice doesn't restate, and repeating "ChatGPT remembers your name. Rodix remembers your thinking." three times would dramatize. One occurrence, given full breathing room.

---

## Reference fetched 2026-05-03

`linear.app` returned: monochromatic-on-light, sans-serif three-tier hierarchy, single-column, screenshots full-width, no motion in static HTML, no superlatives. Notes for adoption:
- **Adopt:** typographic hierarchy doing structural work (no decoration), single-column body, ample vertical gaps, screenshots as bounded product evidence.
- **Adopt:** absence of micro-animation. Friends-intro voice cadence is static; copy carries the work, motion adds nothing.
- **Don't adopt:** Linear runs on a light background. Rodix is dark-mode-default per brand-book §6 — Phase 1 is dark only, light mode toggle is Phase 2.
- **Don't adopt:** headline repetition gimmick. Once is the friends-intro discipline.

Anthropic-equivalent moves (from research-notes recall): institutional restraint without the "we" register. We keep the tonal restraint, swap the institutional voice for personal "I" per friends-intro Sample 3 ("— Rodc").

---

## Skill activation note

`frontend-design:frontend-design` skill is registered but the brand-book §6 + Wave 1a UI patterns already encode every constraint the skill would impose (color, type, spacing, density, motion, decoration). The landing visual envelope is already canonical. I work inside that envelope rather than invoking the skill, since the skill's output would have to defer to brand-book §6 anyway. Documented here for audit.

---

## Top assumptions the landing must address (from `assumption-list.md`)

The landing page is the surface where the friends-intro 4-condition self-selection list does its filtering work. Specifically:

- **S1 — re-explanation soul-tax** (foundational): hero subhead must name the felt problem, not the feature.
- **S17 — continuity vs personalization distinction** (foundational): the 8-word pitch carries this; FAQ unpacks "what's the difference between this and ChatGPT memory?"
- **D1 — emotional content vs no Caregiver register** (Type-A unresolved): the "For whom" anti-target sentence handles the brand-honest filter. Crisis copy is Wave 1c — landing should not promise what isn't shipped.
- **D5 — continuity wedge vs quick-answer fail-mode** (foundational): "ChatGPT's fine" anti-target on the landing is the on-page filter that the position strategy §4.2 calls for.
- **W14 — anonymous-founder trust deficit**: the founder section names the constraint structure honestly per friends-intro status section, four facts, no mythology.

The two most contradiction-heavy spots are (a) emotional-content register on the landing and (b) cross-model marketing claim. For (a) the landing must not mention crisis support since `rodix_system.md` doesn't yet handle it (per §7b second item); the anti-target line "ChatGPT's fine" is the brand-honest filter. For (b) per D2 resolution: cross-model is architectural promise on the landing, not a Phase 1 functional claim — landing copy says "same memory across every model you use" because the architecture supports it; founder essay can unpack the Phase 1 implementation specifics.

---

*End landing-research.md. Brand-book §6 is the visual envelope; voice-guide §1-5 is the copy envelope; assumption-list Top 5 + 3 contradictions are the addressed-or-defended targets.*
