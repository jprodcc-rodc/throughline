# Task 0b Summary — Founder Narrative Arc

**Completed:** 2026-05-03 ~Hour 3.5 (started Hour 2.5)
**Time spent:** ~1 hour actual (research + architect + skeptic + 4 surgical edits + final)
**Self-grade:** A-

Self-grade reasoning: A- because friends-intro voice grounded throughout (skeptic Q3 mostly-passes), Part 1 origin / Part 2 tension / Part 3 resolution / Closing hold the arc structure cleanly, the canonical pitch is preserved verbatim, the volunteered-limit triplet (Escalation #4 mitigation) restores the anti-spin posture skeptic flagged. Knocked off full A because: (a) the "rough notes on the side" sentence is unverified-with-Rodc (Escalation #4); (b) length (1942 words) is over the 1500-2500 sweet spot if Rodc wants tight; (c) skeptic flagged 5 partials before iteration — 4 surgical edits address them but voice-fidelity verification across the whole arc requires Rodc read-through.

## Outputs

Files produced (`docs/superpowers/brand/`):
- `narrative-research.md` — Phase 1 research across 5 founder narratives (Anthropic / Granola / Linear / Notion / Stripe). 1730 words. Recommended primary borrowing target: Patrick Collison (heavy-user opening) + Granola (analogical mid-section, but McLuhan anchor avoided) + Linear ("never fully believed" cadence).
- `founder-narrative-arc-draft.md` — v1 draft from architect subagent. Preserved for diff.
- `narrative-skeptic-notes.md` — skeptic review. 0 full-pass / 5 partial / 2 fail-with-edit on Q1-Q7. Top edit: insert volunteered-limit sentence (HIGH) — most distinctive single move in friends-intro per voice-guide §1.
- `founder-narrative-arc.md` — MASTER (v1.1, iterated). 1942 words. Title: "ChatGPT remembers your name. Rodix remembers your thinking." Subtitle: "Why I'm building a memory layer for AI chat — and why the people who already make AI can't." Part 1 (3 paragraphs) / Part 2 (2 paragraphs) / Part 3 (2 paragraphs) / Closing (1 paragraph) + adaptation notes for 6 channels.

## Key decisions made

1. **Architecture-lead opening framing for Parts 2-3, founder-lead for Part 1.** Honors Escalation #3 (carried from Task 0a) by leading the structural-incentive argument architecturally (Part 2 paragraph 2 = LTV-lock-in framing) while Part 1 stays founder-personal. This is what friends-intro itself does.

2. **Avoid McLuhan anchor.** Both Granola and Notion saturate "we shape our tools, and thereafter our tools shape us." Rodix's anchor is friends-intro's own canonical pitch ("ChatGPT remembers your name. Rodix remembers your thinking.").

3. **Volunteered-limit triplet inserted in Part 3 P1** (Escalation #4 mitigation). Skeptic flagged Q4 fail: arc had zero zero-knowledge admission, missing the most distinctive single move from friends-intro. Restoration: "Server-side recall, by the way — so this is not zero-knowledge, and won't pretend to be. Encryption hardening lives on the post-launch roadmap. The actual ownership story is markdown export." (Adapted from friends-intro lines 352-355.)

4. **Combination-of-bets framing inserted in Part 2 P2** (Escalation #2 mitigation; defends against fail mode 1 — incumbents copying one bet). Replaces redundant moral-failing parenthetical with: "The bet is not that any single one of these commitments is uncopyable — Anthropic could ship cards tomorrow if it wanted; OpenAI could ship export. The bet is that the *whole shape* — memory the user owns, model interchangeable, transparency by default, real export — is structurally unavailable to anyone whose business model depends on you not leaving."

5. **Cut "most user-respectful of the three attempts" qualifier on Claude projects.** Architect-flagged + skeptic-confirmed; the ranking is internal-strategy (position-strategy.md) and does not appear in friends-intro. Cutting four words preserves the unified critique.

6. **Skipped iterator subagent dispatch.** 4-5 edits batch was small enough for direct CC Edit tool application (per Decision 5 in Task 0a decisions.md — skip iterator subagent if edit batch ≤ 3-5 small edits).

## Type-B engineering decisions log

(Recorded inline above + carrying forward Task 0a Decision 5 about iterator subagent threshold.)

## Cross-task implications

- **Task 0c (User Research Synthesis):** The arc's Closing 4-condition "If you've ever..." passage feeds the user interview script (Mom-test "moments-of-frustration probe" pattern).
- **Task 5 (Marketing Landing):** Hero subhead = arc Resolution P2 sentence 1 compressed to 15 words: *"Rodix optimizes for continuity of thought — picking up where you actually left off."* Arc adaptation notes specify this.
- **Task 6 (Marketing Suite):** All 5 channel deliverables (founder essay / HN post / PH post / Twitter thread / launch video script) derive from this arc per the adaptation notes. Founder essay = full arc. HN = compressed. Twitter = 8 tweets. Video = 60-90 sec script.
- **Task 7 (Documentation Pack):** welcome.md + how-it-works.md + getting-started.md should reference the arc's "spine of conversations" framing (Part 3 P1 side-project example) as the canonical "what does Rodix unlock" demonstration.

## TODO for Rodc

1. **Resolve Escalation #4 (rough notes on the side, LOW).** Did you actually keep side notes during your heavy-AI-user year? Keep / cut.
2. **Confirm Escalation #2 mitigation in Part 2 P2** (combination-of-bets framing). The arc now defends against fail mode 1 — does the framing land for you, or do you want a softer / sharper version?
3. **Read full arc + skeptic notes.** Verify voice fidelity. If any sentence sounds LinkedIn-y, founder-coach-y, or LLM-imitating-Rodc, flag for cut.
4. **Confirm length.** 1942 words is essay-length but on the high end. If you want tighter, candidate cuts: Part 2 P1 final sentence ("Three different companies. Three different teams. The same architectural choice, made the same way, for the same reason.") + Part 3 P1 fourth sentence ("None of that is a feature list; it is a posture.") — both restate-the-claim sentences.
5. **Adaptation notes section** — review the 6 channel adaptations (essay / HN / Twitter / video / email-sig / hero subhead). These will be implementer-input for Task 6 Marketing Suite. Veto / approve.

## Lessons / patterns noticed

Logged in `docs/superpowers/tonight/reusable-patterns.md`:
- Pattern in use (carried from Task 0a): Skeptic → CC-direct-Edit pair (when edit batch ≤ 3-5)
- New pattern noticed (will append to reusable-patterns.md): "Architect's flagged-for-Rodc verification places" — the architect subagent should be required to flag any sentence that goes beyond source canonical input. Skeptic then verifies via Grep. This caught both the "rough notes" line (Type-A escalation) and the "most user-respectful" qualifier (cut). Without architect's flag-list, both would have shipped uninspected.

## Cost log

- 4 web_fetch (Phase 1 research; 1 success Anthropic, others 404 → fallback to WebSearch synthesis)
- 4 WebSearch (correction passes for failed fetches; 3 succeeded)
- 2 productive subagent dispatches (architect + skeptic)
- 4 CC Edit operations (surgical iteration)
- ~150k subagent tokens (lower than 0a because fewer subagents)
- 0 LLM API calls outside subagents

## Next task

Task 0c — User Research Synthesis. Will use rodix-friends-intro.md (target user "If you've ever..." passage) + arc Closing + brand book §3 + position-strategy fail modes (especially fail mode 2 "users want quick answers not continuity") as primary inputs.
