# Copy Review Notes — Tier 2 Task 7 Self-Review

**Date:** 2026-05-03
**Author:** documentation-pack-writer subagent
**Scope:** 5 markdown docs (`welcome.md` · `how-it-works.md` · `privacy-summary.md` · `faq.md` · `getting-started.md`) + 3 JSON microcopy assets (`errors.json` · `empty-states.json` · `tooltips.json`)
**Total surface area:** ~3,100 words across markdown; 50 JSON entries (20 + 10 + 20).

---

## Lens 5 — UX/Design emphasis

This pack lives almost entirely on Lens 5: every word is consumed by a real user inside a flow, not by a stakeholder reading a doc. That means the ranking criterion is "would a heavy-AI-user, three weeks in, recognize this as Rodix?" — not "is this technically accurate." Both must be true; the second is necessary but not sufficient. The friends-intro register is the load-bearing test. Specifically:

- **Microcopy is brand at the surface where attention is shortest.** A first-time user spends more cognitive cycles on the empty Vault state than on the founder essay. If `vault_empty` reads like ChatGPT's default voice, the entire brand-as-Explorer claim collapses on first impression. This is why empty-states are written long (≤ 150 chars vs errors' ≤ 100): they're high-leverage brand moments.
- **Tooltips are where the voice stretches thinnest.** ≤ 30 chars per entry leaves no room for parentheticals, em-dashes, negation patterns. The voice has to survive on word choice alone (e.g., "What worries you / what's hard" preserves the disjunction-as-honesty move; "What concerns you" alone would be more efficient but blander).
- **Errors are the inverse — the voice is stress-tested under negative emotion.** The user is annoyed; if the copy is also annoying (apology theater, exclamation marks, "Oops!"), the brand register breaks. Anti-spin is the test: name what failed + what user can do, no excessive apology, no blaming the user.

The four challenges below are this pack's specific Lens-5 risks.

---

## Challenge 1 — Does microcopy feel hand-written or auto-generated?

**Verdict:** Mostly hand-written; one notable risk zone.

**Strong signals (hand-written):**
- `errors.json::extraction_failed` — *"Couldn't extract a card from that message. The reply went through; nothing's lost."* Uses the friends-intro "nothing's lost either way" honest-qualifier pattern from voice-guide §5 Sample 1. A generic copywriter would write "We couldn't extract a card. Please try again." The "the reply went through" is the friends-intro move of naming what *didn't* fail.
- `empty-states.json::vault_empty` — *"Your cards will appear here as you talk to Rodix. We don't write them — your thinking does."* The em-dash + negation-as-positioning is signature Rodix. A generic empty-state would say "No cards yet. Start a conversation!"
- `errors.json::quota_exceeded` — *"Hit the daily limit. Resets at midnight UTC. Premium tiers come post-launch."* Three short fragments, no apology, volunteers a future state honestly. Friends-intro cadence.

**Weak signals (risk of auto-generated):**
- `tooltips.json` is the thin zone. At ≤ 30 chars, several entries (`card_edit: "Edit this field"`, `chat_send: "Send (Enter)"`, `vault_search: "Search across all fields"`) are functional rather than voiced. They're not *wrong*, but they could be in any product. The defense: tooltips at this length ceiling are functional by genre — over-voicing them would look forced. The voiced ones (`card_concern_field`, `recall_skip: "Skip — don't bring back"`, `recall_callout: "A past card relevant to this"`) do the brand work; the functional ones get out of the way.

**Verdict:** Acceptable. The tooltip layer is functional-leaning by necessity; the markdown docs and longer JSON entries carry the voice weight.

---

## Challenge 2 — Is welcome.md condescending or empowering?

**Verdict:** Empowering, with one calibration check needed.

The condescension trap for onboarding copy is the "let me hold your hand through this exciting journey" register. `welcome.md` rejects it explicitly:

- Opens with *"You signed up. Here's what the next five minutes look like."* — declarative, peer-to-peer, no congratulations.
- Treats the user as capable: *"Talk like you would to ChatGPT."* (assumes ChatGPT competence) and *"a decision you've been turning over"* (assumes the user has thinking to bring; doesn't manufacture an excuse to sample-prompt them).
- The "What Rodix is not" paragraph is the load-bearing empowerment move: it sends unfit users away (*"If you ask AI 'what's a good restaurant in Lisbon' twice a week and that's it, you don't need this. ChatGPT's fine."*) — which is the friends-intro signature of treating the reader as someone who can decide whether the product is for them.

**Calibration risk:** The third paragraph mentions *"someone who's already three AI-tools deep, has tried 'memory' features and quietly turned them off"*. This is accurate to the friends-intro ICP (S2 + S3 from assumption-list), but it could read as gatekeeping to a user who *hasn't* tried memory features — which is a meaningful slice of the alpha cohort. The honest call: keep it. The friends-intro positions narrowly on purpose; broadening to "anyone who uses AI" would be the broadening drift named as fail mode in brand-book §6.

**Verdict:** Pass. Empowering rather than condescending. The ICP-narrowing is intentional and matches §3 anti-target framing.

---

## Challenge 3 — FAQ — is each question one a real user would ask, or imagined?

**Verdict:** Mixed — 13/15 are real, 2/15 are CC-imagined-but-defensible.

**Real (13/15):** Questions 1–8, 11–15. These are the questions a discerning HN/IndieHackers reader would surface when evaluating a memory-layer product:
- Q1 (just ChatGPT?), Q2 (vs Mem.ai/Reflect?), Q3 (why won't ChatGPT ship this?) — competitive positioning, exactly what an evaluator asks.
- Q4 (zero-knowledge?), Q11 (EU?), Q15 (mental health crisis?) — privacy/safety questions a careful user surfaces.
- Q5 (switch from Claude to GPT-5?), Q6 (export and leave?), Q7 (export format?) — portability questions native to the cross-model bet.
- Q8 (vs journaling), Q12 (anonymous founder), Q13 (cost), Q14 (delete a card) — operational questions every alpha user has.

**CC-imagined-but-defensible (2/15):** Q9 ("Why is this English-only?") and Q10 ("When will Chinese launch?") are speculative for an English-speaking alpha cohort — most won't ask these. *But:* the friends-intro reading-guide explicitly names Phase 1 = English-speaking international, and the alpha-cohort surface is HN/Twitter where Chinese-speaking heavy-AI-users exist. Including them is hedge against the question being asked but missing from the FAQ. Acceptable, but they could be cut to 13 questions if length is a concern.

**Missing question worth flagging:** *"What does Rodix do when I'm not actively asking it to remember something?"* — this is the recall-vs-personalization confusion (S17 contradiction in assumption-list). The how-it-works.md covers it, but the FAQ doesn't have a direct entry. Worth adding in v2.

**Verdict:** Pass with note. 15 questions is the upper bound; could trim to 13 if Q9/Q10 don't appear in early support tickets.

---

## Challenge 4 — Brand voice — pick 3 random microcopy entries; are they distinctively Rodix?

Random selection from 50-entry JSON pool (rolled 8, 23, 47):

**Entry 8 (errors.json::card_delete_failed):** *"Delete didn't go through. The card is still here. Try again."*
- **Distinctively Rodix?** Yes. Three short fragments, declarative, no apology, no "Oops!". The "The card is still here" is the friends-intro move of naming what didn't change to ground the user. A generic copywriter writes "Sorry, we couldn't delete that card. Please try again." The brevity + the explicit reassurance about state is the Rodix signature.
- **Anti-test:** Could ChatGPT-default voice produce this? No — ChatGPT-default would have apologized.

**Entry 23 (empty-states.json::settings_no_recent_activity):** *"No recent activity. Telemetry is intentionally light here — we don't track engagement metrics."*
- **Distinctively Rodix?** Strongly yes. This volunteers a brand commitment (Decision 7 — anti-engagement metrics) inside an empty state, which is the friends-intro pattern of using transitional surfaces to reinforce the brand stance. Most products' "no recent activity" would say "Check back later for updates!" — Rodix uses the moment to remind the user *why* there's nothing here, by design.
- **Anti-test:** Could Linear/Notion/Anthropic produce this? Anthropic could; Linear/Notion couldn't (their products optimize for engagement metrics).

**Entry 47 (tooltips.json::settings_extraction_toggle):** *"Pause card extraction"*
- **Distinctively Rodix?** Mildly. At 24 chars, it's mostly functional. "Pause" rather than "Disable" is a softer verb that suggests reversibility, matching the friends-intro "different decision" cadence (a decision is a state, not an oath). But this is subtle and could be hard to defend as distinctively Rodix in a blind test.
- **Anti-test:** Could appear in any product. The distinctiveness is in the system context (the existence of an extraction toggle is itself a brand commitment), not in this six-word string.

**Verdict:** 2/3 strongly distinctive, 1/3 functional-leaning. Tooltip layer is the predicted weak zone (matches Challenge 1 finding).

---

## Top 1 weakest microcopy entry

**`tooltips.json::vault_search` — "Search across all fields"**

This is the thinnest entry in the pack. It's not wrong — it accurately describes what the search field does — but it's voice-neutral. A more Rodix-distinctive version: *"Search your wording, not paraphrased"* (echoes the white-box claim from how-it-works.md §2). At ≤ 30 chars, the budget is tight: that alternative is exactly 30 chars and would deepen the brand surface. Recommend swap in v2.

## Top 1 strongest (most distinctively Rodix)

**`empty-states.json::vault_empty` — "Your cards will appear here as you talk to Rodix. We don't write them — your thinking does."**

This is the canonical surface where the product's white-box claim, the friends-intro register, and the negation-as-positioning move all converge. The em-dash sets up the contrast; the second clause does what the friends-intro tagline does ("ChatGPT remembers your name. Rodix remembers your thinking") at empty-state scale. A user who reads this on Day 1 has been told what the product is, who writes the cards, and what the role of the user is — in 23 words. The brand-book brand-routing rule (transitional surfaces default to Explorer voice) is exactly executed here.

---

## Open items for review

- **Sync with `app.js` extraction error strings:** `errors.json::extraction_failed` and `extraction_returned_empty` should match the existing string IDs used by the chat surface. CC has not verified the IDs in this round; implementer should reconcile before wiring.
- **Wave 1c crisis protocol coordination:** `faq.md::Q15` and `privacy-summary.md::Crisis content` reference Wave 1c protocol that has not yet shipped (per brand-book §7b). Copy is forward-looking; if Wave 1c lands with different resource-list scope or different detection-trigger phrasing, both files need patch.
- **Tooltip layer voice pass:** `vault_search`, `card_edit`, `chat_send`, and ~3 other purely-functional entries could be re-voiced for v2 if 30-char budget is loosened to 35 chars. Not a Phase 1 launch blocker.
- **FAQ Q9 / Q10 retention decision:** 15 vs 13 questions. Trim if early support tickets don't surface the language/EU questions in the first 30 days.

---

*End copy-review-notes.md. Self-review complete. Pack ready for Rodc + external review per `feedback_plan_review_protocol.md`.*
