# Task 0a Summary — Brand Foundation Document

**Completed:** 2026-05-03 ~Hour 2.5 (started Hour 0)
**Time spent:** ~2.5 hours actual (1.5h v1 + 1h v2 re-run after Rodc located rodix-friends-intro.md mid-shift)
**Self-grade:** A-

Self-grade reasoning: A- because v2 grounded in canonical voice doc, voice samples sound recognizably Rodc per skeptic verdict (6/1/0 pass/partial/fail on 7 review questions), Wave 1b reality gaps acknowledged honestly in §7b, two-layer archetype reconciliation is load-bearing intellectual work, and decisions log + escalations are clean. Knocked off full A because: (a) length 7233 words is over the 4000-5500 spec band — Rodc may want trim; (b) the architecture-lead-vs-founder-lead defensibility frame is escalated rather than resolved; (c) v1 work was wasted (4 hours of CC time + 5 subagents on partial inputs). Latter is forgivable — the v1 work surfaced issues (fabricated threshold, recall callout aspirational claim, crisis protocol gap) that v2 then resolved cleanly.

## Outputs

Files produced (`docs/superpowers/brand/`):
- `research-notes.md` — Phase 1 brand research across 5 reference brands (Linear, Anthropic, Notion, Granola, Cal.com). 1555 words. Recommended primary borrowing target: Anthropic + Linear for brand stance + restraint; specifically rejected Granola playfulness, Notion automation framing, Cal.com transactional tone.
- `archetype-analysis.md` — v2 friends-intro-based. Primary = Explorer; Secondary = Everyman (color). 2777 words. Decisive evidence: "Gemini decided I was a corporate secretary" passage = Explorer's signature wound (mis-categorization with no escape path). Sage explicitly rejected per reading guide. Two-layer model documented: brand-Explorer + AI-Sage-flavored.
- `voice-guide.md` — v2 friends-intro-based. Voice in 3 adjectives: **Specific. Anti-spin. Refuses-to-dramatize.** 3499 words. Most distinctive principle: parenthetical-as-honesty. 5 voice principles + 7 dos + 7 donts + 3 sample passages (chat error / marketing tagline+support / support email reply) + voice consistency checklist + Rodix-vs-neighbors distinguishing.
- `position-strategy.md` — v2 friends-intro-based. Canonical pitch: **"ChatGPT remembers your name. Rodix remembers your thinking."** 5294 words. 4-bets-as-architectural-commitments-moat framing + 3 fail modes (incumbents fix one / users want quick answers / one model wins decisively) + reconciliation with v1 framing.
- `brand-book-v1.md` — MASTER. v2 friends-intro-based. 7233 words + reconciliation log appendix + v1 → v2 changelog. 8 sections + §7b "brand commitments pending Wave 2 / 1c implementation".
- `review-notes.md` — v2 skeptic review. 6 passes / 1 partial / 0 fails on 7 questions. 1 high-priority edit (§7b button-label completion) + 1 medium edit (§4 routing rule for transitional surfaces). Both applied directly via CC Edit tool.
- `decisions.md` — Type-B engineering decisions log (7 decisions).

Archived (preserved for audit, brainstorm-based v1 work):
- `archetype-analysis-brainstorm-based.md` (Sage primary)
- `voice-guide-brainstorm-based.md` (Specific. Restrained. Capable-treating.)
- `position-strategy-brainstorm-based.md` ("thinking not engagement" pitch)
- `brand-book-v1-brainstorm-based.md` (v1 master)
- `review-notes-brainstorm-based.md` (v1 skeptic review with 4 ship-blocker findings)

## Key decisions made

1. **Two-layer archetype model.** Brand = Explorer (primary) + Everyman (color); in-product AI character = Sage-flavored Socratic. Both preserved. Routing rule for transitional surfaces (default Explorer unless surface speaks as AI character).
2. **Pitch precedence:** friends-intro short pitch as canonical ("ChatGPT remembers your name. Rodix remembers your thinking."). v1's longer pitch preserved for sub-headings.
3. **Defensibility frame ordering:** v2 leads with architectural-commitments-competitors-can't-adopt (per friends-intro). v1 led with execution-discipline-plus-founder-narrative. Escalated to Rodc as #3 (medium severity).
4. **§7b honest gap acknowledgment:** Brand book makes 3 explicit "brand commitments pending implementation" claims (recall callout copy, crisis protocol, per-user encryption) — naming the gap rather than over-claiming. This honors §5's anti-spin principle structurally.
5. **Did NOT patch `rodix_system.md`.** Wave 1b ship-ready code is frozen until dogfood verifies. Brand book's extended English banned-phrase list documented for Wave 1c or Wave 2 system-prompt iteration.

## Type-B engineering decisions log

See `docs/superpowers/brand/decisions.md` for the complete decision-by-decision log. 7 decisions recorded.

## Cross-task implications

- **Task 0b (Founder Narrative Arc):** Must use friends-intro voice (specifically the 3 adjectives + 5 principles + sample passages). Founder essay opening framing depends on Escalation #3 resolution (architecture-lead vs founder-lead).
- **Task 0c (User Research Synthesis):** Brand book §3 ("Who Rodix is for") + §1 anti-target ("If you ask AI 'what's a good restaurant in Lisbon' twice a week and that's it, you don't need this") feed assumption-extraction.
- **Task 1 (Wave 2 Plan):** §7 Decision 5 (refusal of Caregiver register) + §7b commitments feed Wave 2 spec validation. Wave 2 #active-recall-base spec must ship the locked recall callout copy ("⚡ 我把这个带回来了") + locked action buttons ("用上了 / 不相关 / 已经想过 / 跳过").
- **Task 5 (Marketing Landing) + Task 6 (Marketing Suite) + Task 7 (Documentation Pack):** All copy must use friends-intro voice via Task 9 Rodix Design System Skill (Tier 3). Until Task 9 ships, copy-writers reference brand-book-v1.md §5 directly.
- **Task 8 (Privacy Policy + ToS):** §7 Decision 6 (anti-spin discipline on encryption claims) is operational. Privacy Policy must NOT claim zero-knowledge or per-user encryption — friends-intro language *"Encryption hardening on the post-launch roadmap"* is the honest framing. Crisis protocol gap is escalated.
- **Tier 1.5 Phase B Sample Verify Round 8 (Sarah Day-15):** Will reveal whether Wave 1b without crisis protocol fails gracefully or alarmingly. Outcome decides whether Escalation #2 (crisis protocol) is ship-blocking.
- **Task 9 (Rodix Design System Skill, Tier 3):** Brand book becomes the input for skill creation. The skill encodes voice + visual + component patterns so Wave 2/4/5 work auto-applies Rodix coherence.
- **Task 14 (Codebase Docs + ADRs, Tier 3):** ADR-006 "Brand archetype selection" should reference brand-book v2 (Explorer primary + Everyman secondary) and the two-layer model decision.

## TODO for Rodc

1. **Read `rodix-friends-intro.md` body again, then read brand-book-v1.md §1 + §5 sample passages.** Confirm voice matches your friend-version intro author voice. If a sample passage sounds LinkedIn-y or LLM-y, flag it before Task 6 marketing suite.
2. **Resolve Escalation #2 (crisis protocol gap, HIGH).** Decide: Wave 1c P0 ship-blocker OR Phase 1 launch-day disclaimer + post-launch Wave 1c (P1 fast-follow). Approve protocol design space (resource scope / detection trigger / register / escalation path).
3. **Resolve Escalation #3 (defensibility frame leadership, MEDIUM).** Architecture-lead (v2) vs founder-lead (v1). Determines Task 0b founder essay opening.
4. **Confirm two-layer archetype model.** Brand = Explorer; AI = Sage-flavored. Read §4 → review the routing rule for transitional surfaces. Veto / approve.
5. **Confirm Decision 6 (anti-spin on encryption / per-user keys).** Brand book commits Rodix to never marketing what isn't built. Verify this matches your intent.
6. **Optional: trim brand book §8 + reconciliation log if 7233 words feels long.** §1-7 are load-bearing. §8 can be cut by 30% without losing core. Reconciliation log can be cut to 1-paragraph note.

## Lessons / patterns noticed

Logged in `docs/superpowers/tonight/reusable-patterns.md`:
1. Archive-then-rebuild on primary-input correction
2. Reading-Guide-as-task-instruction header (the friends-intro pattern Rodc designed)
3. Skeptic → Iterator subagent pair (review-as-edit-list)
4. Verbatim-quote-or-Grep ground truth requirement (subagent guardrail)

## Cost log

- 5 web_fetch (Phase 1 research)
- 8 subagent dispatches (3 v1 brand subagents + 1 v1 integrator + 1 v1 skeptic + 1 v1 iterator + 3 v2 brand subagents + 1 v2 integrator + 1 v2 skeptic = 11 actually; 8 productive)
- ~600k total subagent tokens spent (reasonable for ~7000-word canonical doc grounded in 1300-word source)
- 0 LLM API calls outside subagents (no Phase B sample-verify yet — that's Tier 1.5)

## Next task

Task 0b — Founder Narrative Arc. Will use brand-book-v1.md + friends-intro as primary inputs. Founder essay opening framing depends on Escalation #3 resolution (default: architecture-lead per brand book §8). If Rodc resolves Escalation #3 before Task 0b dispatches, use Rodc's choice. Otherwise dispatch with default + flag for iteration if Rodc inverts.
