# Rodix Microcopy Patterns

The 3 microcopy surfaces (errors / empty states / tooltips) ship today in `app/web/static/copy/{errors,empty-states,tooltips}.json`. This guide documents the pattern so future copy stays consistent — and so the JSON files themselves remain the audit trail.

---

## The Rodix microcopy formula

Every Rodix microcopy string should pass three filters:

1. **Terse.** Error messages: 2 short paragraphs max — what failed + what user can do next + recovery affordance. Empty state titles: ≤ 8 words. Toasts: ≤ 60 characters. Tooltips: name the thing in one fragment.
2. **Anti-spin.** Don't over-claim. Don't soft-hedge. Volunteer the limit when it's structurally honest. ("The reply went through; nothing's lost.")
3. **Don't blame the user.** Mechanism named without softening, but never *"You typed something invalid."* Closer to *"Couldn't extract a card from that message."*

Anti-pattern check: would Rodc write *"We're sorry, something went wrong"*? No. Read the friends-intro: anti-spin lives in volunteering the actual situation, not in performative apology.

---

## 1. Error messages (`errors.json`)

### Pattern

`{ what failed concretely } + { what didn't fail / what's preserved } + { recovery affordance or next step }`

### Examples (sourced from shipped `errors.json`)

**1. Extraction failure during chat:**
> *"Couldn't extract a card from that message. The reply went through; nothing's lost."*

Anti-spin: surfaces what failed AND what didn't. The user's chat continues — no need to dramatize.

**2. API timeout:**
> *"Took longer than expected. Try again — this happens occasionally."*

The em-dash carries an honest qualifier. *"This happens occasionally"* is anti-dramatic specificity — not "we're investigating" / "rare issue" / "we apologize."

**3. Vault sync failure:**
> *"Sync hit a snag. Your changes are on this device — they'll catch up next time."*

"Hit a snag" refuses to dramatize. The em-dash insertion names what's preserved — local changes are safe. Recovery affordance is implicit (user does nothing; sync auto-retries).

**4. Magic link expired:**
> *"That link expired. Send a new one — they're good for 15 minutes."*

Specific time qualifier (*"15 minutes"*, not "for a limited time"). Recovery affordance is inline.

**5. Quota exceeded:**
> *"Hit the daily limit. Resets at midnight UTC. Premium tiers come post-launch."*

Three short fragments. Names the boundary, names when it lifts, names the future state honestly. *"Premium tiers come post-launch"* is anti-spin — doesn't promise / doesn't tease / doesn't apologize.

### Anti-patterns (don't ship)

- *"Oops! Something went wrong. Please try again."* — Generic, sycophantic, no specificity.
- *"We're experiencing technical difficulties. Our team has been notified."* — Theater, no recovery affordance, hides mechanism.
- *"Error: 500 Internal Server Error"* — Anti-honest in the other direction; raw stack trace exposed to user.
- *"Sorry, this is on us. We're working hard to fix it!"* — Apology theater + LinkedIn founder-coach drift.

---

## 2. Empty states (`empty-states.json`)

### Pattern

`{ name what's missing } + { name why it's correct or what causes it } + { what the user can do, never coaxing }`

Empty states are a high-leverage Rodix surface. Most products fill empty states with encouragement walls (*"Get started! Create your first project!"*). Rodix uses them to teach mechanism — null is correct (Decision 5), and the empty state is honest about that.

### Examples (sourced from shipped `empty-states.json`)

**1. Vault empty (most-photographed empty state):**
> *"Your cards will appear here as you talk to Rodix. We don't write them — your thinking does."*

The negation does positioning work. *"We don't write them — your thinking does."* This is the 4-fold-bet brand stance compressed to two sentences. Inline em-dash carries the honesty.

**2. First chat empty:**
> *"Type something you've actually been thinking about. Not a test — a real one. Cards will appear as you talk."*

*"Not a test — a real one"* is the friends-intro register applied to onboarding. Sends unfit users away by implication: if you wanted a demo, this isn't that.

**3. Vault search no results:**
> *"Nothing matches that search yet. Try a different phrase, or a topic you've thought about recently."*

*"Yet"* is an honest qualifier — short, definite. *"A topic you've thought about recently"* is brand-coherent: Rodix indexes thinking, not entities.

**4. Recall no history:**
> *"No past cards to bring back yet. They'll surface as topics return across conversations."*

The verb is "bring back" — Decision 3 locked. Mechanism named (topics return across conversations).

**5. Settings telemetry empty:**
> *"No recent activity. Telemetry is intentionally light here — we don't track engagement metrics."*

Volunteers a brand commitment (Decision 7 — no engagement metrics). Anti-spin in operation: most products would hide this; Rodix names it.

### Anti-patterns (don't ship)

- *"Oops! Looks like there's nothing here yet. Create your first card to get started!"* — Sycophancy + coaxing + exclamation marks.
- *"Empty state — no data."* — Too sparse, no mechanism named, no user affordance.
- *"You haven't created any cards yet."* — Blame-the-user framing.
- *"Get inspired! Try our example prompts ↓"* — Coaxing with marketing layer.

---

## 3. Tooltips (`tooltips.json`)

### Pattern

`{ name the thing in one fragment, no verb required }`

Tooltips are the simplest Rodix surface and the easiest to over-explain. Rule: name what the control does, not why the user should care. Voice register is descriptive, not promotional.

### Examples (sourced from shipped `tooltips.json`)

**1. Card field labels:**
- *"What you're thinking about"* (topic)
- *"What worries you / what's hard"* (concern)
- *"What you want / where you're going"* (hope)
- *"What's still unresolved"* (question)

Plain-language definitions of the 4 fields. The card is the most-photographed Rodix object; these labels are what new users learn the schema by.

**2. Recall callout actions:**
- *"Mark as relevant"* (recall_relevant)
- *"Mark as not relevant"* (recall_not_relevant)
- *"Skip — don't bring back"* (recall_skip)

Imperative form, short. *"Skip — don't bring back"* uses the locked verb "bring back" (Decision 3).

**3. Settings controls:**
- *"One click → markdown files"* (settings_export) — names the affordance, names the output format. Per Decision 4, real export = markdown.
- *"30-day deletion SLA"* (settings_delete_account) — anti-spin specificity. Most products say "Delete account"; Rodix says when it actually completes.
- *"Pause card extraction"* (settings_extraction_toggle) — names what the toggle does, not why ("Take control!").

**4. Chat actions:**
- *"Send (Enter)"* (chat_send) — names the keyboard shortcut. Power-user-friendly.
- *"Start fresh — new context"* (chat_new_conversation) — names what changes (context resets).

### Anti-patterns (don't ship)

- *"Click here to send your message!"* — Verbose, exclamation, no mechanism.
- *"This will permanently delete your account. This action cannot be undone."* — Theatrical, panic-inducing. Rodix says: *"30-day deletion SLA"* (concrete, anti-dramatic).
- *"Save your beautiful insights to markdown!"* — Adjective-stack ("beautiful"), exclamation, generic SaaS register.

---

## 4. The 3 microcopy surfaces — when in doubt

Walk this decision tree before writing new microcopy:

```
Is the surface speaking AS the AI character mid-conversation?
├─ Yes → Sage layer. Use rodix_system.md voice. (Only the recall callout falls here.)
└─ No → Explorer layer. All other microcopy. Continue:

Does it explain a system state that failed or is empty?
├─ Yes → errors.json or empty-states.json pattern. Walk the formula:
│         { what failed/missing } + { what's preserved/why correct } + { recovery/next step }
└─ No → tooltips.json pattern. Name the thing in one fragment.
```

---

## 5. Pre-ship checklist for new microcopy

Before adding to `errors.json` / `empty-states.json` / `tooltips.json`:

1. Could this string be search-and-replaced into another product without changing meaning? If yes, fail. (Specificity test.)
2. Does it use any of: *transform, leverage, unlock, supercharge, harness, surface, facilitate*? If yes, rewrite.
3. Does it have an exclamation mark? Friends-intro uses zero. Rewrite.
4. Does it open with *"Oops!"* / *"Sorry,"* / *"Great!"* / *"Of course!"*? Strip.
5. Does it apologize? Errors should name what failed and what didn't, not perform contrition. Rewrite as anti-spin.
6. Does it coax the user (*"Get started!"* / *"Try our..."* / *"Discover..."*)? Strip — Rodix sends unfit users away, doesn't pull fit users in with marketing.

If any check fails, return to `voice-guide.md` §6 and apply the 5-question checklist.
