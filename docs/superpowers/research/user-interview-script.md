# Rodix User Interview Script — Phase 1 Validation

**Author:** user-research-strategist (Tier 0 Task 0c)
**Date:** 2026-05-03
**Purpose:** 45-60 minute 1v1 interview Rodc can run with 5 candidate users to empirically test the Top 5 most foundational assumptions (S1, V2+S9, S17, S15, D1) and the Top 2 contradictions (D5, D2) extracted in `assumption-list.md`.
**Discipline:** Mom Test (Rob Fitzpatrick). All questions probe past behavior, not future intent. No leading framing. No pitching before probing the problem (first 30 minutes).
**Companion docs:** `mom-test-checklist.md` (self-check) · `recruit-strategy.md` (where to find 5 candidates).

---

## Pre-interview prep (5 min, before candidate joins)

- Open the **Mom Test Checklist** and re-read items 1-5.
- Have a notes doc open. Plan to type, not summarize from memory afterward — memory degrades inside 90 minutes.
- Record audio if candidate consents (ask at start). If no consent, type aggressively.
- Have the friends-intro pulled up but **closed in a separate tab**. Section D is the only place to introduce Rodix; Sections A-C must run with zero product exposure.
- Decide before this candidate: am I showing live alpha, describing in friends-intro voice, or both? Default for first 5 candidates: **describe** (less variable than alpha-state which may distract from problem-probe).

---

## Section A — Rapport + life context (5 min)

**Goal:** relax the candidate, signal "this is a conversation, not a sales call." Establish the candidate is talking, not me. NO mention of Rodix. NO mention of AI memory. NO leading framing.

Open with thanks-for-time + a one-sentence honest framing:

> "Thanks for the time. I'm doing some early user research — I'd rather hear about what you're actually doing than pitch you on anything, so I'm going to mostly ask questions about your week. Recording audio is fine? You can stop me any time."

### Questions (pick 3, in order)

**A1.** "What does a typical work week look like for you right now? Walk me through, say, last Tuesday or Wednesday."
*(Anchor in a specific recent day. "Typical" alone invites generality.)*

**A2.** "What's the biggest decision or open question you've been chewing on lately — work, life, side project, anything?"
*(Surfaces a real thinking workload candidate has, which Section B can then re-anchor against. Probes S8 — does target user actually have hard-thing thinking workload?)*

**A3.** "When was the last time you felt like you got real thinking done — actually moved forward on something, not just answered email? What were you doing?"
*(Past behavior. Probes S1 indirectly — does candidate frame "thinking" as a felt activity at all?)*

### Avoid in Section A

- "Are you the kind of person who...?" (invites self-flattery)
- "Do you think a lot about hard problems?" (leading and abstract)
- Anything mentioning AI, ChatGPT, memory, productivity tools

---

## Section B — Current "thinking" workflow probe (15 min)

**Goal:** validate the wedge empirically. Does this candidate think for a living, or are they a quick-answer user (probes contradiction D5 from `assumption-list.md`)? What surfaces do they use today for complex thinking — notebooks, friends, AI, therapist, nothing?

**Discipline:** Each question must anchor in a specific past moment. If the candidate slips into general/abstract ("I usually..."), follow up with "tell me about the last time."

### Questions (use all 5)

**B1.** "Tell me about the last time you had to think through something complex or ambiguous — not a fact you could look up, but something with no clear right answer. What was it, and what did you actually do?"
*(Probes S1 — does heavy thinking happen at all in this candidate's life? Probes S8 — what kind of hard-thing? Listen for: career / relationship / project / parent-decline / divorce vs. work-task / writing / coding.)*

**B2.** "Walk me through what you reached for first when you were trying to think through that. A notebook? A walk? A friend? An AI? Nothing?"
*(Past behavior, no leading. Probes contradiction D5 — is candidate's "thinking-with-AI" a real workflow or hypothetical?)*

**B3.** "How often do you use AI tools in a typical week — and what kind of stuff do you bring to them? Try to think about the last 5-10 times specifically."
*(Anchors in count, not feeling. Probes S1's heavy-user assumption — is this candidate actually 2-3 hours/day across multiple providers, or 5x/week for restaurant questions? The anti-target test from §3 brand book.)*

**B4.** "When you use AI for something complex — versus 'what's the capital of Belarus' — does the conversation go differently? Tell me about the last specific time you used AI to actually think through something, not just look something up."
*(Probes contradiction D5 directly — is "thinking aloud with AI" a real behavior or rare? Listen for: does the candidate even distinguish thinking-use from answer-use?)*

**B5.** "What's something hard you've been thinking about for more than two weeks — work, life, project, anything? How does the thinking compound for you between sessions, if at all?"
*(Probes S17 — "continuity of thought." Does the candidate experience compounding/non-compounding as a felt phenomenon? Listen for the language candidate uses; "continuity" is Rodix vocabulary, candidate may say "I lose the thread" / "I forget what I figured out" / nothing.)*

### Probes when candidate goes vague

- "Walk me through the last time."
- "What was the actual question / situation?"
- "What did you do right after?"
- "How long did that last?"

### Listen for

- **Strong wedge signal:** Candidate reaches for AI for hard thinking AND reports re-explaining / losing thread / going in circles between sessions. (S1 confirmed for this candidate.)
- **Wedge-narrows signal:** Candidate uses AI heavily but only for research / coding / writing tasks — never for life-decision thinking. (Fail mode 2 / contradiction D5 for this candidate.)
- **Wedge-misses signal:** Candidate doesn't use AI for thinking at all and has no felt continuity-loss. (Anti-target.)

---

## Section C — Past failure / friction probe (15 min)

**Goal:** surface the soul-tax pattern empirically (S1) and the inferred-persona failure pattern (S9, V2). Test the friends-intro 4-condition list against actual past behavior, not endorsement.

**Discipline:** Each question targets a specific moment. NO "Do you find AI memory annoying?" / "Have you been frustrated by AI tools?" — these invite politeness lies. Anchor the question in a thing the candidate actually did.

### Questions (use all 5)

**C1.** "When was the last time you re-asked an AI a question you'd asked before — same topic, different conversation? Tell me about that moment. What did you do, what did you feel?"
*(Probes friends-intro condition 1: "re-explained for the fifth time and felt the soul-tax." Probes assumption S1. Past-behavior anchored. The lie-test: candidate cannot fabricate a specific recent moment.)*

**C2.** "Have you used 'memory' features in any AI tool — ChatGPT memory, Gemini personalization, Claude projects? If yes, walk me through what happened the last time you noticed it doing something. If no, did you ever turn one on and then turn it off?"
*(Probes V1 + V2 + S9. Past behavior. The "did you turn it off" question is critical — surfaces the broad pattern of users disabling memory after distrust.)*

**C3.** "Has an AI ever assumed something about you that was wrong — and you couldn't seem to fix it? Tell me about that specific moment."
*(Probes S9 — Gemini "corporate secretary" pattern as user behavior, not as Rodc's analysis. The lie-test: candidate cannot describe the specific wrong-categorization moment if it never happened. Anchor: "you couldn't seem to fix it" is concrete.)*

**C4.** "Tell me about a complex topic — work, life, a project — that you've been turning over for two or more weeks. When you come back to it after a few days, how do you pick up where you left off? Do you?"
*(Probes S17 — the continuity-of-thought distinction. Does candidate currently *do* continuity-of-thought maintenance? With what surface? Listen for: notebook, prior conversation re-read, mental model, nothing.)*

**C5.** "Are you using more than one AI tool — say, ChatGPT and Claude, or with Gemini? If yes, has there been a moment when you wished they shared context — that the second one knew what you'd told the first? Or — honestly — have you never noticed?"
*(Probes friends-intro condition 2: "used three AIs and wished they shared a brain." The "or never noticed" is the Mom-test escape hatch — gives candidate a real out, surfaces honest negative if the felt-pain isn't there. Probes contradiction D4 — is multi-provider use real for this candidate?)*

### Probes when candidate deflects

- "What did you do right after?"
- "Did you go back and try again, or just give up?"
- "What were you actually trying to do?"
- "Walk me through the last time."

### Listen for

- **Soul-tax confirmed:** candidate describes specific re-explaining moments with felt frustration (S1 holds for this candidate). Even better: candidate volunteers a workaround they invented.
- **Creeped-out confirmed:** candidate volunteers a "I don't trust what it remembers" moment unprompted.
- **Multi-tool confirmed:** candidate uses 3+ AI tools, can name a specific cross-tool wish moment.
- **Contradicted:** candidate uses 1 tool, has never noticed memory misfires, can't recall a re-explaining moment. (Anti-target signal — record this even if it's unwelcome.)

---

## Section D — Show or describe Rodix briefly (10 min)

**Goal:** observe reaction without leading. The first 30 minutes built up problem-context; this section introduces the product *briefly* and watches what the candidate does with it.

**Discipline:** describe in friends-intro voice. Do NOT pitch. Do NOT use "imagine" / "what if" / "would you." Show the artifact, then probe past-behavior-shaped reactions.

### Default opener (describe mode)

> "Okay — let me describe what I'm building, briefly. Then I want to hear what you'd actually do with it.
>
> It's called Rodix. It's a memory layer for AI chat — works across ChatGPT, Claude, Gemini, others. When you have a conversation with any of them, Rodix pulls out the meaningful parts as structured cards: topic, concern, hope, open question. You see every card. Edit, delete, export. Next time you start a conversation, Rodix surfaces relevant cards before the AI answers — so the AI sees your actual prior thinking, not a vendor's compressed guess.
>
> Markdown export, one click, your hard drive. That's the whole thing."

*(45 seconds. Voice from friends-intro §"The pitch in 30 seconds" + §"What it actually does." NO claims about benefits. NO future-tense promises. Mechanism-first.)*

### Questions (use 3 of these 4)

**D1.** "What did you expect would happen next when I said 'Rodix surfaces relevant cards'? What does that picture look like in your head?"
*(Probes S15 — does "topic / concern / hope / question" 4-field schema make sense without explanation? Probes S17 — does "continuity of thought" register as different from "personalization"? Listen for what mental model candidate actually constructs from the description.)*

**D2.** "What confused you or seemed weird?"
*(Anti-leading. The candidate is licensed to be negative. If they say "nothing was confusing," push: "What's the part you'd want to see before you'd believe it works?")*

**D3.** "If you sat down with this tomorrow morning, what's the first thing you'd actually do? Walk me through."
*(Probes behavior intent through specific imagined past-shaped action — "walk me through" forces concreteness. Listen for: would the candidate actually use it as a thinking surface, or would they use it for tasks? Tests fail mode 2 / contradiction D5.)*

**D4.** "What questions does the description leave open for you that I haven't answered?"
*(Surfaces what's missing without leading. Often the most useful question — candidate's question reveals their mental model.)*

### Avoid in Section D

- "Would you use this?" *(future intent, Mom-test fail)*
- "Do you think you'd pay for this?" *(Compliments / politeness territory.)*
- "What features would you want to see?" *(Invites feature-list speculation; not behavior.)*
- "Does this resonate?" *(Compliment-bait.)*
- Pitching benefits *("the great thing about this is...")*. The friends-intro is anti-pitch; the interview should be too.

### Listen for

- **Pull signal:** candidate describes a specific recent moment where they would have wanted Rodix. Unprompted.
- **Confusion signal:** candidate's mental model of "cards" / "recall" / "cross-model" diverges from what's in the description. (S15 / S17 weak for this candidate.)
- **Fit-test signal:** candidate's "first thing I'd do" is task-shaped (write a doc / look something up) rather than thinking-shaped (work through the parent-decline thing / kill-the-side-project thing). Fail mode 2 indicator.

---

## Section E — Open exploration (10 min)

**Goal:** surface anything the script didn't probe. The candidate has now been talking for 45 minutes; they have context. Cheap to ask what I missed.

### Questions (use 2 of these 3)

**E1.** "What questions did you expect me to ask that I didn't?"
*(Surfaces the candidate's mental model of what would matter. Often reveals the candidate's own concerns / objections that politeness suppressed in Section D.)*

**E2.** "What's something I haven't asked about that would matter to how you'd think about a tool like this — for yourself?"
*(Anchors in candidate's real frame. The "for yourself" is the mom-test discipline — invites past-shaped contemplation, not market-research speculation.)*

**E3.** "If you imagine yourself trying this for a week and then quitting — what would the reason most likely be?"
*(Pre-mortem framing. Surfaces the most likely churn vector from this candidate's perspective. Behavior-anchored: imagine yourself, not "imagine users.")*

### Listen for

- **Surprising objection:** something Rodc didn't anticipate. This is the highest-information moment of the interview.
- **Repeat themes from earlier:** if candidate circles back to the same friction / hope / fear from Section B-C, that's a real signal.
- **Crisis-signal:** if candidate volunteers anything in the territory of "what if I'm in a hard place when I use it" → **Note carefully.** Probes contradiction D1 (emotional content vs. no Caregiver register / no crisis protocol).

---

## Closing (3-5 min)

**Step 1 — Thank, no compliments fishing.**

> "This was really useful. Thank you for the time."

*(NOT: "Was this helpful for you too?" — invites compliment.)*

**Step 2 — Referral ask.**

> "One last thing — who else should I talk to who'd have a different perspective on this? Someone who thinks differently from you, or uses AI differently."
*(The "different from you" framing is critical — invites diverse referrals rather than copies of the same candidate.)*

**Step 3 — Honest expectation set.**

> "I'll reach back out in a few weeks when there's something to actually show. No newsletter, no waitlist spam — just a note when there's a thing."
*(Friends-intro voice: "I'll post when it's open.")*

### Avoid in closing

- "Would you want to be a beta user?" *(Future intent.)*
- "Mind if I add you to a waitlist?" *(Treat as separate decision after interview, not embedded in it. Compliment territory if asked here.)*
- "Any final thoughts?" *(Already covered in Section E. Asking again invites politeness wrap-up.)*

---

## Post-interview (10-15 min, immediately after)

**Done within 30 minutes of interview ending. Memory degrades fast.**

1. Re-listen to the most surprising 30 seconds of audio (or re-read the typed equivalent).
2. Run the **Mom Test Checklist** against your interview. Honestly. The checklist is for you, not for show.
3. Write a 5-line summary in a single notes file:
   - Wedge fit: yes / partial / no.
   - Strongest signal heard (specific moment).
   - Most surprising thing candidate said.
   - Friends-intro 4-conditions: which conditions did this candidate hit empirically?
   - Anti-target risk: does this candidate look more like the "ChatGPT's fine for restaurant questions" user than the target?
4. Note the referral the candidate gave you. Schedule outreach within 24 hours while warmth holds.
5. Resist the urge to treat one positive candidate as validation. n=1 is a data point, not a pattern.

---

## Calibration after interviews 1-2

After the first two interviews, take 30 minutes to:

- **Re-read the script.** Are there questions that consistently produce vague answers? Replace them with sharper past-behavior questions.
- **Check if a question keeps falling flat.** If C2 (memory features) is producing "I haven't tried any" three times in a row, your recruit channel is wrong — you're talking to people outside the heavy-AI-user segment.
- **Audit yourself.** Are you talking too much? Re-listen to a 5-minute stretch of audio. Target asymmetry: 80% candidate, 20% you. If you're at 50/50, you're pitching, not probing.

---

## Per-interview assumption coverage map

For each candidate, after the interview, record on a one-page rubric:

| Assumption | Probed by | Result for this candidate |
|---|---|---|
| S1 (soul-tax) | B1, B5, C1, C4 | confirmed / partial / contradicted / N/A |
| S17 (continuity ≠ personalization) | B5, C4, D1 | confirmed / partial / contradicted / N/A |
| S15 (4-field schema understandable) | D1 | confirmed / partial / contradicted / N/A |
| V2 + S9 (vendor lock-in / inferred persona) | C2, C3 | confirmed / partial / contradicted / N/A |
| D1 (emotional content / crisis) | A2, B1, E2, E3 | candidate volunteered: yes / no |
| D5 (continuity vs. quick answers) | B3, B4, D3 | thinking-user / quick-answer-user / mixed |
| D2 (cross-model) | B3, C5 | multi-tool / single-tool / N/A |
| Friends-intro condition 1 (re-explaining tax) | C1 | hit empirically: yes / no |
| Friends-intro condition 2 (3 AIs / shared brain) | C5 | hit empirically: yes / no |
| Friends-intro condition 3 (creeped out by memory) | C2, C3 | hit empirically: yes / no |
| Friends-intro condition 4 (record of evolved thinking) | B5, C4 | hit empirically: yes / no |

**Pattern across 5 candidates is the actual data.** A single candidate's results are noise. If 4 of 5 candidates hit conditions 1+4 but only 1 of 5 hits condition 2, the 4-condition list needs revision (condition 2 is not foundational for the wedge).

---

*End user-interview-script.md. Companion: `mom-test-checklist.md`, `recruit-strategy.md`.*
