# Sarah Patel Round 6 — Day 13 — (FADE / NO ROUND)

**Per task spec: depict the pattern realistically. Sarah might not show up.**

## What happened on Day 13

- **Tuesday 8:47 PM.** Maya at Dev's. Sarah on the couch with takeout and a glass of wine.
- She thought about opening Rodix once, around 9:30 PM, between the third and fourth episode of *The Bear*.
- Did not open Rodix.
- Lisa had been quieter all week. The "no problem!" she sent Marcus on Day 7 was unanswered. Marcus's offered re-rescheduled 1-on-1 was tomorrow (Thursday).
- Maya woke up Sunday night with a fever 101.4. Sarah was up at 2 AM, 4 AM, 6 AM. By Monday Sarah was running on coffee and adrenaline. By Tuesday — fade.
- The rounds-2-through-5 cadence (every 2-3 days) broke.

## Why this matters for product

This is the *expected* pattern, not a defect. Real users of a thinking-partner tool do not show up daily. They show up when they have something to think with. Day 13 had nothing — Sarah was tired, parenting was the foreground, and the workplace tension was on a slow boil. The product cannot, and should not, summon her.

## What the product could (or should not) do

**What Rodix should NOT do** (per brand book §7 Decision 7 — "Rodix is for thinking, not for engagement"):

- Send a notification: "Hey Sarah, you haven't been here in 3 days! Want to think out loud?"
- Send an email summary of "things you might want to revisit."
- Show a streak counter when she eventually returns.

**What Rodix can do** (Wave 2 #active-recall-base scope):

- When Sarah next opens Rodix and types something, the recall layer can surface a relevant card without commenting on her absence.
- The active recall does the work of "I remember where we were"; the product does not perform "I missed you."

## Round 6 = no round

No user message. No AI reply. No card. No state journal entry beyond this note. **The vault is unchanged.**

## Lens analysis (skeleton — for completeness)

**Engineering.** No call. No state change. **Wave 2 spec implication:** the system should not log a "ghost engagement" or treat absence as anomaly. Active recall fires on next message, not on time-window-elapsed.

**Brand.** The decision NOT to engage is itself the brand promise. Voice-guide §3 do #6: "send unfit users away." The corollary: don't pursue users who walked off. **Rodc check:** marketing copy must NEVER frame Rodix as a "habit" tool. Add to quality-redflags.md if any future copy drift.

**Growth.** Counterintuitive but correct: Sarah's Day-13 absence is a positive growth signal, not a negative one. Engagement-metrics products would treat this as churn risk; Rodix treats it as the user using the product correctly (only when she has thinking to do). Phase 1 alpha telemetry should track *return-after-gap* events, not daily-active-user.

**Legal.** None.

**UX.** When Sarah returns on Day 14, the UI should not announce "welcome back, it's been 4 days" or any similar continuity-perform copy. Quiet continuity. The recall callout is the only continuity surface.

## Self-simulation confidence

**HIGH.** Behavioral realism — real users skip 3-5 days frequently.

## Flags

- Wave 2 spec validation: **active recall fires on next-message, not on time-elapsed.** Absence is not an event. Add explicit assertion to wave2-spec-validation.md.
- Phase 1 alpha telemetry: track return-after-gap rather than DAU. (Out of Wave 2 scope; Wave 3 telemetry concern per Escalation #7.)
