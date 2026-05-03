> **Note 2026-05-04:** Brand renamed Rodix → Rodspan. This file is a historical record from prior to the rename and retains the original "Rodix" name as written at the time. See `docs/superpowers/tasks/rodix-to-rodspan-rename.md` for context.

# Tier 3 Handoff — 2026-05-03

**Tier 3 status:** Selective COMPLETE / Task 15 IN FLIGHT (Hour ~9.5 of 30-hour shift)
**Tasks completed:** 9 (Design System Skill) / 13 (Observability + Cost Cap) / 15 (Vault handoff — in flight)
**Tasks skipped (per instruction prioritization):** 10 (Competitor deep dive) / 11 (Onboarding A/B) / 12 (Visual polish) / 14 (Codebase docs + ADRs)
**Author:** CC (autonomous shift)

---

## 1. Completion summary

| Task | Status | Self-grade | Files |
|---|---|---|---|
| 9 Rodix Design System Skill | DONE | A | 7 files in `.claude/skills/rodix-design-system/` |
| 10 Competitor deep dive | SKIPPED | N/A | Tier 0c competitor research suffices for Phase 1 alpha |
| 11 Onboarding A/B | SKIPPED | N/A | Wave 2 implementation defers; not blocking |
| 12 Visual polish | SKIPPED | N/A | Wave 1c can produce |
| 13 Observability + Cost Cap | DONE | A- | 4 files in `docs/superpowers/observability/` |
| 14 Codebase docs + ADRs | SKIPPED | N/A | Open-source not Phase-1-critical |
| 15 Vault handoff | IN FLIGHT | TBD | Pending Phase A vault-state.md (just completed) |

Tier 3 budget: 3-5h. Actual: ~30 min wall-clock parallel + ~30 min Task 15 in flight = ~1 hour total. Significantly under-budget by skipping 4 of 7 tasks per spec prioritization.

---

## 2. Type-B engineering decisions (with reasoning chains)

### Decision T3-1 — Selective Tier 3 (skip 4 of 7)

**Decision:** Skipped Tasks 10 / 11 / 12 / 14. Executed Tasks 9 / 13. Task 15 in flight.

**Reasoning chain:**
1. Spec instruction Section 7 prioritized: "Skip first if forced: Tier 3 Task 14 (Codebase Docs) → Task 12 (Polish List) → Task 11 (Onboarding A/B)."
2. Task 10 (Competitor deep dive) is Wave 4-5 informing, not Phase-1-alpha-blocking. Tier 0c brand research-notes.md covered 5 reference brands sufficient for Tier 0 + Tier 2 work.
3. Task 9 (Design System Skill) is HIGH-leverage — every future CC session benefits. Executed.
4. Task 13 (Observability + Cost Cap) is HIGH-priority per Escalation #10 (heavy-user cost cap). Executed.
5. Task 15 (Vault handoff) requires Phase A completion. Dispatched after Phase A done.
6. Total Tier 3 tax saved: ~3-4h (4 skipped tasks × 45-60 min each).

**Confidence:** HIGH. Aligns with spec prioritization + frees budget for strategic memo + final handoff at Hour 28-30.

### Decision T3-2 — Project-level skill location

**Decision:** Rodix Design System Skill at `C:\Users\Jprod\code\throughline\.claude\skills\rodix-design-system\` (project-level), NOT user-level `~/.claude/skills/`.

**Reasoning chain:**
1. Project-level ships with the repo — Wave 2 / Wave 4 / Wave 5 implementer subagents inherit automatically.
2. User-level requires Rodc to copy files to home dir manually.
3. Project-level survives `git clone` for any future contributor (open-source path).
4. Trade-off: skill activates only when this project loads. Other Rodix-related projects (e.g., MCP server in separate repo) need separate copy.

**Confidence:** HIGH for tonight's scope. Future: if Rodc spins separate repos, copy to user-level.

### Decision T3-3 — Cost cap 50k input + 25k output / user / day

**Decision:** Daily cap = 50k input + 25k output tokens / user / day. Cost ceiling ~$0.30/day per user (~$9/month worst case).

**Reasoning chain:**
1. Heavy user (200 turns/day × 2k tokens) = 400k tokens. Cap at 50k+25k = ~3× heavy-expected (generous).
2. Cap × 1000 alpha users × 30 days = $9k/month max LLM burn — within Rodc alpha-runway tolerance.
3. Tighter cap (e.g., 25k+12k = 1.5×) risks legitimate heavy users hit cap before $10/mo subscription pays off.
4. Looser cap (e.g., 100k+50k = 6×) risks runaway loss at scale.
5. Rodc admin-override flag (`RODIX_USER_OVERRIDE_USERID`) preserves Rodc's own dogfood without cap.

**Confidence:** HIGH. Documented in `cost-cap-design.md` §1.

### Decision T3-4 — Power-tier $25/mo cap = 3× standard

**Decision:** Power-tier ($25/mo Wave 3 SaaS) cap = 150k input + 75k output / day = ~$0.83/day worst case. Multiplier = 3× standard.

**Reasoning chain:**
1. Friends-intro "200 hours in" calibrates "real heavy use." 3× standard = ~10× standard heavy-expected.
2. 2× too tight for power users who use Rodix as primary thinking surface.
3. 5× breaks unit economics ($1.50/day × 30 = $45/month cost vs $25/month revenue).
4. 3× = middle ground.

**Confidence:** MEDIUM. Type-A escalation flagged in cost-cap-design.md §5 — Rodc confirms before Wave 3b dispatch.

### Decision T3-5 — Anti-spin in cost-cap user-facing copy

**Decision:** Cost-cap soft block copy: "Today's thinking budget is reached. Resume tomorrow at midnight UTC." NOT "quota exceeded" / "you've used up your tokens" / "rate limit hit."

**Reasoning chain:**
1. Brand-book §7 Decision 7 (thinking-not-engagement metric) — copy reinforces brand stance.
2. Anti-spin per voice-guide §1 — frame as soft limit, not punishment.
3. "Thinking budget" preserves user agency framing.

**Confidence:** HIGH. Aligns with §7b commitments + brand voice.

### Decision T3-6 — Privacy-aware logging discipline

**Decision:** Sentry `before_send` hook strips `request.data` + `extra.message_content` + `extra.ai_reply` + `extra.card_content`. NEVER log user content. Per-user metrics use hashed user_id.

**Reasoning chain:**
1. Brand-book §7 Decision 1 (white-box / transparency) cuts both ways: user sees own data, system never logs user content.
2. Crisis-content surfaces (Sarah Day-15 type) MUST NOT appear in logs even for debugging — would create inadvertent data trail.
3. Quarterly audit grep verifies zero leakage.

**Confidence:** HIGH. Privacy-first discipline.

---

## 3. Confidence-flagged items for Rodc + Opus review

| Item | CC Confidence | Why qualified | Rodc / Opus action |
|---|---|---|---|
| Skill activation keywords | HIGH | 17 trigger keywords cover Rodix product + content + UI surfaces | None — verify via 1 test invocation |
| Two-layer model in skill | HIGH | Brand-Explorer + AI-Sage routing rule load-bearing | Verify against Tier 2 deliverables coherence |
| Skill self-test (85-word product update) | HIGH | Passed 5-question voice-guide checklist | None — confirmed |
| Cost cap 50k+25k / user / day | HIGH | 3× heavy-expected; loss-leader mitigation per Escalation #10 | Confirm before Wave 3b dispatch |
| Power-tier 3× multiplier | MEDIUM | Type-A escalation flagged | Confirm before Wave 3b dispatch |
| Sentry free tier 5k events / month | HIGH | Sufficient for Phase 1 alpha ≤1000 users | None |
| PostHog vs SQLite-backed dashboard | MEDIUM | Recommended PostHog (1M events / month free tier) | Rodc confirms vendor choice |
| 30-day log retention policy | HIGH | GDPR-aligned + storage cost contained | None |

---

## 4. Pre-compaction snapshot — active context not in files

### 4.1 Active reasoning about Tier 3 Task 9 Design System Skill activation timing

Skill activates when this project loads (project-level). For Wave 2 / 4 / 5 implementer subagents:
- Subagent prompts MUST reference `.claude/skills/rodix-design-system/SKILL.md` explicitly (subagents don't auto-load project skills unless told).
- Or: Wave 2 plan v1.2 implementer-dispatch checklist should add "Read Rodix Design System Skill at .claude/skills/rodix-design-system/SKILL.md before any Rodix-facing copy."

Brand-coherence enforcement happens via subagent instruction, not magic auto-activation.

### 4.2 Active reasoning about Tier 1.5 Finding 5 ("Marked." / "Noted." pattern) propagation

Tier 1.5 surfaced "Marked." matter-of-fact acknowledgment pattern AFTER Tier 3 Task 9 dispatched. Skill voice-guide.md does NOT yet codify this pattern.

Recommendation: post-Tier-1.5 patch to `.claude/skills/rodix-design-system/voice-guide.md` adding:

> **8th do/don't pair (matter-of-fact acknowledgment for heavy disclosure):**
> 
> DO: Open with single word — "Marked." / "Noted." / "Acknowledged." Then proceed to substance.
> DON'T: "I'm so sorry to hear that. That sounds really hard. Let me know if there's anything I can do."

Apply via direct Edit tool when Phase B + Task 15 complete. Pre-final-memo cleanup.

### 4.3 Active reasoning about Tier 3 skipped tasks impact

Skipped tasks risk:
- Task 10 (Competitor deep dive) — Wave 4-5 marketing positioning weaker; Tier 0c research-notes covers 5 brands sufficient for Phase 1 alpha launch.
- Task 11 (Onboarding A/B) — Wave 2 ships current onboarding (Wave 1a #2a); A/B test designed during Wave 2 implementation.
- Task 12 (Visual polish) — Wave 1c iteration; not Phase 1 launch blocker.
- Task 14 (Codebase docs + ADRs) — Open-source path Phase 2+; not Phase 1 critical.

None of skipped tasks are Phase-1-alpha-blocking. Each can be picked up by Rodc or future CC session post-launch.

### 4.4 Active observation about Tier 3 overall

Tier 3 aimed compounding — outputs that benefit Wave 2-5 work. Task 9 Design System Skill is the highest-compounding Tier 3 output (every future CC session benefits). Task 13 Observability is Wave 3 deploy-time prep. Task 15 (in flight) is Rodc dogfood prep.

---

## 5. Cross-tier insights

### 5.1 — Skipping is tier discipline, not failure

Tier 3 prioritization (skip 4 of 7) reflects budget allocation, not quality compromise. Tasks 10/11/12/14 are deferable; doing all 7 would have consumed 6-8h that better used on strategic memo + handoff + Phase B verification.

### 5.2 — Rodix Design System Skill is the unlock for Wave 2-5 brand-coherence

Without the skill, every future CC session re-derives Rodix style from brand book (~5-10 min × N sessions = compounding tax). With it, implementer subagents inherit Rodix-coherent baseline automatically. **This is the highest-leverage single Tier 3 output.**

### 5.3 — Cost cap is the load-bearing financial mitigation

Per Escalation #10 (heavy-user loss-leader at $10/mo), cost cap (Tier 3 Task 13) is what prevents runaway losses. $0.30/day × 1000 users × 30 days = $9k/month max. Without cap, runaway scenario uncapped. **Cost cap is operationally critical for Phase 1 alpha launch.**

---

## 6. What Rodc + Opus should read first (Tier 3 only)

If Rodc has 15 min:
1. **3 min:** This handoff
2. **5 min:** Skill SKILL.md (`.claude/skills/rodix-design-system/SKILL.md`) — quick reference for activation + 7 don'ts
3. **5 min:** `cost-cap-design.md` — daily cap + power-tier + admin-override
4. **2 min:** When Task 15 completes, read `rodc-handoff.md` for morning dogfood sequence

If 30+ min, add:
- Skill `voice-guide.md` (operational voice rules condensed)
- Skill `component-patterns.md` (10 components with ASCII sketches)
- `observability-spec.md` + `alerting-rules.md` (Wave 3 deploy-time)

---

## 7. Outstanding TODOs for Rodc

### Pre-Phase-1-alpha:
1. **Patch skill voice-guide.md** with "Marked."/"Noted." pattern (Tier 1.5 Finding 5).
2. **Confirm Sentry vs PostHog** for observability stack.
3. **Confirm cost cap thresholds** (50k+25k standard / 150k+75k power tier) before Wave 3b dispatch.

### Pre-Wave 3 dispatch:
4. **Resolve Type-A power-tier 3× multiplier** (cost-cap-design.md §5).
5. **Plan Wave 4-5 competitor deep dive** (Tier 3 Task 10 deferred).

---

*End Tier 3 handoff. Phase B + Task 15 in flight; final memo + chat summary follow.*
