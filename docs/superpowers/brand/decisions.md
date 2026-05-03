# Task 0a Brand Foundation — Decisions Log (Type-B engineering decisions)

This file records the engineering decisions CC made during Task 0a that don't need escalation but Rodc may want to revisit. For Type-A decisions (strategic, Rodc-only), see `docs/superpowers/tonight/escalations.md`.

## Decision 1 — File-archival convention on input correction

**Decision:** When primary input changes mid-task (Rodc located `rodix-friends-intro.md` mid-shift), rename existing outputs to `*-{old-source}-based.md` (e.g. `archetype-analysis-brainstorm-based.md`) and re-run Phase 3 with new primary input. The new outputs replace the canonical filename (`archetype-analysis.md`).

**Alternative considered:** Hand-merge old + new outputs to preserve the work. Rejected because brainstorm-based outputs concluded fundamentally different verdicts (Sage primary vs Explorer primary; "thinking not engagement" vs "ChatGPT remembers your name. Rodspan remembers your thinking."). Hand-merge would have papered over the contradictions rather than resolved them.

**Why:** Audit trail preserved without forcing manual diff. v2 outputs are clean reads grounded in canonical input. Logged in `reusable-patterns.md` as "Archive-then-rebuild on primary-input correction" pattern.

## Decision 2 — Scope boundary on `rodspan_system.md` patch suggestion

**Decision:** Brand book v2 §5 added an extended English-language banned-phrase list ("I hear you", "I get it", "That sounds really hard", "Let's unpack this together", "I'm listening", "You're not alone") that exceeds the current `rodspan_system.md` v1.3 ban list. CC did NOT patch `rodspan_system.md` — that's Wave 1b shipped code (commit 53b56f0 frozen until dogfood verifies).

**Alternative considered:** Auto-patch `rodspan_system.md` with the extended list. Rejected because the instruction set explicitly says "Touch Wave 1b ship-ready code (commit 53b56f0 frozen until dogfood verifies)" is NOT licensed.

**Why:** Brand book documents the *brand stance* on banned English phrases; rodspan_system.md operationalizes it. The two layers can be temporarily out of sync. Wave 1c (or Wave 2 system-prompt iteration) is the correct vehicle for the patch. Logged in v1 → v2 changelog for Rodc visibility.

## Decision 3 — Two-layer archetype model documentation

**Decision:** §4 documents an explicit two-layer model: brand archetype = Explorer (primary) + Everyman (color); in-product AI character = Sage-flavored Socratic. Both preserved. Routing rule added for transitional surfaces (onboarding / error states / recall callouts) — default to brand-Explorer unless surface speaks *as the AI character*.

**Alternative considered:** Pick one archetype, force the other to align. Rejected because v1 conflated layers (Sage-as-brand-archetype was wrong; v1 read in-product mechanics as if they were the brand) and a single-layer choice would either reduce brand specificity (Explorer → erases AI character's Sage flavor that's clearly correct) or force the AI to behave Explorer-y in chat (anti-Socratic, breaks Round 3+ stop-asking discipline).

**Why:** Friends-intro voice IS Explorer; rodspan_system.md voice IS Sage-flavored. Both inputs are canonical. A two-layer model is more honest than picking one. Routing rule prevents "schizoid" deliveries (e.g., a launch-video script that flips registers mid-clip).

## Decision 4 — Pitch precedence: friends-intro short pitch as canonical

**Decision:** Brand book §1 uses the friends-intro short pitch verbatim: **"ChatGPT remembers your name. Rodspan remembers your thinking."** v1's longer pitch ("AI chat that visibly remembers what you said and brings it back when it matters — built for thinking, not for engagement") is preserved as a longer-form articulation suitable for landing-page subhead or founder-essay-pull-quote, not hero copy.

**Alternative considered:** Use v1's longer pitch. Rejected because friends-intro author wrote the short pitch and tagged it "That's the whole thing" — that is a canonical signal. Eight words beats 22 for hero use.

**Why:** v1's "built for thinking, not for engagement" sub-claim survives in §3 anti-target framing and §7 Decision 7 — useful when the contrast needs unpacking, but not for hero. Short pitch is brand-on-voice.

## Decision 5 — Skeptic-iterator subagent pair vs single review-and-revise

**Decision:** v2 used skeptic subagent (review-notes.md with verbatim quotes + numbered edits) followed by direct CC Edit tool application (3 edits), instead of dispatching an iterator subagent. v1 used skeptic + iterator subagent pair.

**Alternative considered:** Dispatch v2 iterator subagent (parallel to v1 pattern). Rejected because v2 only had 2 specific edits (§7b button-label completion + §4 routing rule for transitional surfaces) — small enough to apply directly via Edit tool without losing fidelity. Iterator pattern is high-leverage when 5+ edits are needed.

**Why:** Subagent dispatch overhead (300+ tokens prompt setup + agent latency) only worth it for medium-or-larger edit batches. Logged in `reusable-patterns.md` as candidate refinement: "Skeptic → Iterator subagent pair" pattern, with note: skip iterator if edit batch ≤ 3 edits.

## Decision 6 — Length over-target for brand book

**Decision:** Brand book v2 final length 7233 words; spec target was 4000-5500. CC kept the over-target length.

**Alternative considered:** Trim by 25-30% to hit target band. Rejected because length is partly inflated by required verbatim friends-intro quoting (per spec: "cite friends-intro VERBATIM") + reconciliation log (required by spec) + v1 → v2 changelog (required by spec). Trimming would have lost load-bearing canonical quotes.

**Why:** This is the canonical brand reference. Subsequent tasks (founder essay, marketing landing, marketing suite, design system skill) read this book. Better to err long with verifiable quotes than short with summaries. If Rodc disagrees, trimming a 30% pass is straightforward post-review.

## Decision 8 — Rename + Open Core architecture lock (2026-05-04)

**Decision:** Renamed Rodix → Rodspan per audit memo (`docs/superpowers/branding/name-audit/00-RECOMMENDATION-MEMO.md`). Product category clarified to LLM chat client wedge (not memory layer). Path A locked (user-BYO-API + Cherry Studio competitor). Open Core architecture locked: Rodspan SaaS in private `rodspan-app` repo + throughline OSS as algorithm canon, sibling-repo PYTHONPATH dependency via conftest.py. Three commitments accepted (sunset clause on commitment 1: throughline OSS maintained while Rodspan is active commercial product). See spec `docs/superpowers/tasks/rodix-to-rodspan-rename.md` §15.

**Alternative considered:** (a) Rodix retains — Rodc Type-A picked rename per audit memo §7 (both options were defensible reads of the data). (b) Path B (Rodspan covers LLM cost, free-trial + paid subscription) — rejected; would have collapsed the audit's +25% Rodspan-vs-Rodix margin under LLM-provider category framing. (c) Decouple Rodspan from throughline OSS roots (rewrite `mcp_server` / `throughline_cli` imports to local copies) — rejected; cancelled per §13.4. Open Core treats sibling-repo dependency as permanent architecture, not technical debt.

**Why:** Compound-feature naming (rod + span) fits the LLM-client category convention (Cherry Studio / LobeChat / TypingMind compound names) where Rodix's empty-coined pattern was unconventional. Open Core preserves throughline OSS as algorithm canon — improvements flow back to OSS user base — while Rodspan SaaS captures commercial layer (UI / auth / billing / multi-user / cloud sync / premium memory). Layer rules locked at write-time per code change (no "I'll put it in SaaS for now"). Logged as Type-A escalation closure for #1=D (OSS / SaaS relationship) — RESOLVED.

## Decision 7 — Wave 1b code verification before brand claims

**Decision:** All brand-book claims about shipped product behavior were Bash/Grep verified before inclusion. Specifically: recall thresholds (real values from `app/shared/recall/orchestrator.py`), recall callout placeholder copy (from `app/web/static/app.js` lines 580 + 627), crisis-protocol absence (zero Grep matches in `app/web/prompts/rodspan_system.md`).

**Alternative considered:** Trust subagent verbal claims without verification. Rejected because v1 had a fabricated 0.75 threshold that survived 5 levels of subagent review (Phase 3 archetype/voice/position + Phase 4 integrator + Phase 5 skeptic) before the final iterator caught it via Grep. Verifying before claiming was the structural fix.

**Why:** Brand book that fabricates numbers violates its own §5 anti-spin principle. Logged in `reusable-patterns.md` as "Verbatim-quote-or-Grep ground truth requirement" pattern. Should be standard subagent guardrail going forward.

---

End decisions.md.
