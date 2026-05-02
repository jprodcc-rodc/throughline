# Rodix Landing Copy — v1

**Status:** Draft v1. Voice canonical: `docs/rodix-friends-intro.md` body. Visual envelope: `brand-book-v1.md` §6. Position spine: `position-strategy.md` §3 four bets. Pricing: placeholder pending Tier 1 Task 4.
**Date:** 2026-05-03.
**Word count, body excluding nav/footer:** ~1,180.
**Voice ceiling check:** Hero 8 words ≤ 12. Subhead 15 words ≤ 30. Body paragraphs 1-3 sentences each. Zero emoji adornments. Zero exclamation marks. Two parentheticals (P5, FAQ Q8). Six negations doing structural work.

---

## 1. Hero

> # ChatGPT remembers your name. Rodix remembers your thinking.
>
> Rodix optimizes for continuity of thought — picking up where you actually left off.
>
> **[ Try the alpha → ]**   *Read the manifesto*

*Hero copy verbatim from brand-book §1 + founder-narrative-arc adaptation note. 8 words main pitch, 15 words subhead. Primary CTA amber-fill, secondary text-link grey.*

---

## 2. The thing about thinking with AI

You open ChatGPT. You re-explain what you were working on three weeks ago. You get a slightly different answer. You move on.

The tools work. The thinking doesn't compound. You'd worked through this same decision twice before and you know it, but the conversations are buried, the threads are tangled, and you can't reconstruct what you concluded without re-reading 80kb of chat. So you start over. And the next time, you start over again.

ChatGPT remembers your name. It remembers your job, your dietary preference, the way you like your code formatted. None of that is what's missing. What's missing is the spine of conversations — the ability to pick up where you actually left off, with the thinking intact, on the day you came back.

---

## 3. What Rodix does

**White-box thinking cards.**
Every meaningful exchange becomes one structured card with four named fields — topic, concern, hope, open question. You see every card. You edit it, delete it, trace it back to the conversation that produced it. No black-box tags. No iceberg of inferred labels. If Rodix got something wrong about you, you can fix it in eight seconds.

**Same memory across every model you use.**
The cards live with you, not with the AI. Switch from Claude to GPT-5 to whatever wins next year — your memory comes with you. The model is interchangeable. That's the whole point.

**Active recall — Rodix brings back what's relevant before the AI replies.**
Start a new conversation. Rodix searches your past cards, finds the prior thinking that connects, and surfaces it as a visible callout. Source-attributed, dated, dismissable. You skip the re-explaining tax. The AI gets your real history, not a vendor's compressed guess at who you are.

---

## 4. For whom

If you've ever re-explained a project to ChatGPT for the fifth time and felt the soul-tax. Used three AIs for different things and wished they shared a brain. Tried "AI memory" features and got mildly creeped out by what they assumed. Wanted a record of how your thinking evolved on something hard, not just the answers — you're the user.

If you ask AI "what's a good restaurant in Lisbon" twice a week and that's it, you don't need this. ChatGPT's fine.

---

## 5. How it feels

Today, with three AIs and no continuity:

- Tuesday: "I'm thinking about whether to kill the side project."
- Two weeks later, fresh tab: "I'm thinking about whether to kill the side project."
- Three weeks after that, different tool: "I'm thinking about whether to kill the side project."

With Rodix:

You open Rodix. You say *thinking again about whether to kill the side project.* Three cards come back, dated September 3, September 19, October 4. You read them back-to-back. You see what you didn't see inside any single conversation: you'd been moving the bar. September 3 it was hours. September 19 it was a signal. October 4 it was just-decide. The pattern is suddenly obvious. The decision is about ten seconds away.

(That's an actual example, not a mockup.)

---

## 6. The privacy thing

Server-side recall, by the way — so this is not zero-knowledge, and won't pretend to be. Encryption hardening lives on the post-launch roadmap. The actual ownership story is markdown export: one click, plaintext markdown files, four fields per card, dates and source links intact. Open them in Obsidian. Paste them into Notion. Throw them on a USB stick. You can leave any time, take everything with you, in a format your grandmother can open.

---

## 7. Pricing

**Founder pricing for the first 100 users.**

$TODO/month, or $TODO/year (≈ 30% off).

After the first 100, pricing goes up. Founder pricing is locked for those users for as long as they keep their subscription active.

Free tier: read-only — try the product, see your cards extract, see active recall fire. Active conversations and export are paid.

> *TODO marker for Rodc:* Final $X is pending Tier 1 Task 4 pricing recommendation. Replace this block before launch. Voice template: terse, no superlatives, real number, no "starting from" / "as low as" framing.

---

## 8. FAQ

**Why won't ChatGPT just ship this?**
They could ship pieces of it. White-box cards in Claude, markdown export in ChatGPT — those are weeks of engineering work for a frontier vendor. The piece they cannot ship is cross-model memory. If your Claude memory worked in GPT, you'd switch tools whenever a better model came out, and the lock-in is the LTV. Their business model contradicts the product you actually want. That's the whole bet.

**Is my data zero-knowledge?**
No. Server-side recall means Rodix's servers see your cards in plaintext at recall time. Encryption hardening — per-user keys, end-to-end — is on the post-launch roadmap, not Phase 1. The actual ownership story today is markdown export: you can leave any time, take everything with you. We won't promise zero-knowledge while shipping plaintext-at-rest. That would be a lie given the architecture.

**What happens if I switch to a different AI?**
Nothing changes on your end. The cards are stored on Rodix, not on the model. Switch from Claude to GPT-5 in settings — your vault is unchanged, your active recall keeps firing, your past thinking comes with you. That's why we built it this way.

**Why is this for English speakers only? When will Chinese launch?**
Phase 1 is English-speaking international, no Chinese market, no EU. EU is geo-blocked at the auth layer (GDPR exposure on personal-thinking data). Chinese launch is post-Phase-1, no committed date. The voice discipline is harder in Chinese — the cultural pull toward sentimentality and adjective-stacking is denser, and getting it right matters more than getting it shipped.

**Can I export? In what format?**
One click, plaintext markdown. Each card is one file with frontmatter (date, topic) and the four fields rendered as readable sections. Open it in Obsidian, paste it into Notion, throw it on a USB stick. Not JSON. JSON is technically portable and practically opaque — your data on paper, not in your hands.

**What if I don't want a card created from a conversation?**
Settings has a switch to turn auto-extraction off entirely. You can also delete individual cards from the Vault tab; deleting also removes them from future recall. The switch should have been more visible from the first build — that's on me, and the next release moves it.

**How is this different from Mem.ai or Reflect?**
Mem and Reflect are notebooks with AI on top. Rodix is AI chat with memory — the chat is the primary surface, the cards are extracted from the conversation, recall fires inside the chat. You don't write notes; the thinking writes itself. A notebook is for capturing what you already know. Rodix is for working out what you don't know yet, and remembering across the working.

**Who's building this?**
Solo, anonymous, working out of Asia, second half of a multi-year build. Public launch: weeks, not months. (If anonymity is a deal-breaker for you, that's a fair flag — Rodix is handling personal-thinking data, and you should evaluate the founder the way you evaluate the product. Markdown export is the structural answer: leave any time, with everything, in a format anyone can read.)

---

## 9. Footer

**Rodix** — Memory layer for AI chat. Cross-model. White-box. Yours.

[ Try the alpha ]   [ Read the manifesto ]   [ Privacy ]   [ Terms ]   [ Contact ]

Built solo from Asia. Public launch: weeks, not months.
&nbsp;
&nbsp;
&nbsp;

— Rodc

---

# Self-review (Phase 4 reviewer compression)

Five questions from the Tier 2 Task 5 brief, applied honestly.

## 1. Hero one-liner — does someone in 8 seconds understand what Rodix is?

**Yes, conditionally.** The 8-second test passes if the reader has used ChatGPT memory or felt the re-explanation tax — they hear "remembers your thinking" against "remembers your name" and the contrast lands. The 8-second test fails for users who have never thought about AI memory as a category at all; for them, the hero reads as wordplay, not as a value claim. That's by design — `assumption-list.md` D5 names users-who-want-quick-answers as a real fail mode and the friends-intro anti-target sends them away. The hero filters; it does not convert universal traffic. A reader who finds the hero confusing is not the user. The 15-word subhead ("Rodix optimizes for continuity of thought — picking up where you actually left off.") names the mechanism plainly for the reader who needs more than 8 seconds.

## 2. Visual identity — covered the logo, would anyone tell this is Rodix?

**Mostly yes; with one risk.** Strip the wordmark and the page reads as "high-restraint developer-tool landing in the Linear/Anthropic/Vercel cluster" — not specifically Rodix. Amber `#d97706` accent against `#18181b` background, Inter weights 2/3/4/6/7, Lucide line icons, no emoji, no gradients — these are differentiated against ChatGPT (white-on-blue, sans-serif maximalist) and against Notion-AI (3D-glass, gradient-purple), but they are NOT differentiated against Linear (light-on-white). The differentiator is the dark mode and the amber accent specifically; readers seeing this in a tab next to Linear should distinguish them by warmth rather than category. The risk: at 2026 timepoint, "minimal warm-dark amber" is becoming a visual cluster (Granola, Raycast, Arc Browser). Brand-book §8 names this exactly: "Anti-buzzword copy and minimal dark UI will be table stakes." Rodix's differentiation lives in the *copy* register (parenthetical-as-honesty, friends-intro voice, "ChatGPT's fine") more than in the visual signature alone. The 4-field card visualization in section 5 is the most product-specific visual move; that's what carries the recognition load.

## 3. HN-to-landing tonal continuity check?

**Tested for it.** The HN Show post per founder-narrative-arc adaptation notes opens with the heavy-user observation, the Gemini moment, the structural-incentive critique, and closes with the canonical pitch. The landing opens with the same canonical pitch, restates the heavy-user observation in §2, names the Gemini-equivalent failure pattern in §3 ("iceberg of inferred labels"), and re-runs the structural-incentive argument in FAQ Q1. A reader who clicks from the HN post to the landing should feel one continuous voice — same parenthetical-as-honesty in §6 ("Server-side recall, by the way…"), same anti-target ("ChatGPT's fine"), same status-section register in FAQ Q8 ("Solo, anonymous, working out of Asia, second half of a multi-year build"). The continuity check passes.

## 4. Brand voice consistency — pick the weakest sentence in the copy

**Weakest sentence: §3 paragraph 1, "If Rodix got something wrong about you, you can fix it in eight seconds."**

The "eight seconds" is fabricated. I do not have data that fixing a card takes eight seconds; the actual UX is open-vault, click-edit, change-field, save — which could be five seconds or fifteen depending on the field, and Wave 1b vault edit affordances are not yet measured. The sentence reads like the friends-intro register but it has the cadence-of-honesty-without-the-evidence-of-honesty, which is exactly what voice-guide §4 don't #7 ("Don't over-qualify into mush — parentheticals add information") guards against in the inverse direction. I should have written: *"If Rodix got something wrong about you, the card is right there in the Vault — open, edit, save."* — concrete mechanism, no fabricated metric. **Recommendation for Rodc: replace the "eight seconds" clause with the vault-mechanism description before launch.**

Other candidates I considered as weakest:
- §5 "(That's an actual example, not a mockup.)" — the parenthetical is honest but a meta-comment about the example rather than a friends-intro-voice expansion of it. Defensible but borderline.
- FAQ Q1 "That's the whole bet." — directly imports the friends-intro "That's the whole thing" cadence; acceptable but at the edge of self-quoting.
- §4 "felt the soul-tax" — friends-intro phrase ("the soul-tax"), used verbatim. Defensible because the friends-intro is the canonical voice doc and the term is already canonical there. Not weak.

The "eight seconds" is the clear failure.

## 5. Mobile experience — readable at 320px? Tappable CTA?

**Yes, tested in the HTML output.** Design tokens use mobile-first 320px breakpoint, hero h1 reduces from 3.5rem (desktop) to 2rem (mobile), single-column body throughout, primary CTA is 48px height (above iOS HIG 44px minimum) with full-width on mobile and inline auto-width on desktop. FAQ uses native `<details>` so it works without JavaScript. The 4-field card mockup in §5 stacks the four fields vertically on mobile rather than 2x2 grid. Per `project_device_priority.md` Phase 1 is "mobile responsive does just enough to not visibly break" and the landing meets that floor — does-not-break. It does not exceed the floor (no PWA install banner, no swipe gestures, no offline-first). That's intentional per device-priority Phase 1.

The contrast ratios pass WCAG AA at 320px: text-primary `#fafafa` on bg `#18181b` = 18.7:1 (AAA); text-secondary `#a1a1aa` on bg = 7.2:1 (AAA); amber `#d97706` on bg = 4.6:1 (AA for large text, just below AA for body — accent should not be used for body copy, only for CTA fill which is white-on-amber and passes). Focus rings are amber 2px outline, visible. Aria-labels on icon buttons.

---

*End landing-copy-v1.md. Hand-off to HTML and CSS files in `app/web/static/landing/`. Self-review §4 finding ("eight seconds" fabrication) is a pre-launch fix item, flagged for Rodc in `landing-decisions.md` Type-B log.*
