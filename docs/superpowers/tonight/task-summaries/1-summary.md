# Task 1 Summary — Wave 2 Plan

**Completed:** 2026-05-03 ~Hour 7.5 (started Hour 5)
**Time spent:** ~2.5 hours (Phase 1 ingestion + 5 parallel spec writers + integrator + reviewer + 3 HIGH edits + 2 new escalations)
**Self-grade:** A-

Self-grade reasoning: A- because all 5 specs implementer-ready (4/5 PASS or PARTIAL on junior-engineer test per reviewer; 1 weakest spec hardened with 3 HIGH edits applied), Wave 2 plan composes 5 specs with explicit task DAG + 5-criterion launch gate + risk register. Knocked off full A because: (a) reviewer found growth-operator-value PARTIAL (zero validated WTP signal across 5 specs); (b) 4 MEDIUM/LOW edits pending Rodc review; (c) 2 new Type-A escalations (#7 telemetry-readiness + #8 copy-lock confidence) surfaced; (d) `card-dedup` brand check ceremonial (Edit 6 Medium pending); (e) `card-real` Task 4 has unresolved precondition `openDetailById` (Edit 5 Medium).

## Outputs

Files produced (`docs/superpowers/plans/wave2/` + `docs/superpowers/plans/`):
- `wave2/spec-card-real.md` — 432 lines. Real Card UI replacing Wave 1a placeholder.
- `wave2/spec-active-recall-base.md` — 445 + 3 HIGH-edit additions = ~520 lines now. Load-bearing Wave 2 P0. Variant 2 injection format locked. Recall recall floor: 60% soft + calibration trigger. Env-var rollback seam added. Task 10 hardened (length floor + length-normalized check + Wave 2.1 LLM-judge NotImplementedError scaffolding).
- `wave2/spec-first-insight.md` — 410 lines. Threshold 5 default (Type-A). Variant C reflection format locked. Option D UI placement (chat-stream card variant).
- `wave2/spec-card-dedup.md` — 359 lines. Threshold 3 default (Type-A). 4 MEDIUM edits pending.
- `wave2/spec-vault-recall-history.md` — 398 lines. Strongest rollback discipline. S16-vs-W17 polarity flip risk surfaced. Schema v4→v5 additive.
- `2026-05-03-wave2.md` — Wave 2 master plan v1.1 (~290 lines + v1 → v1.1 changelog + v1.2 implementer-dispatch checklist). 5-criterion launch gate. Cross-spec risk register. Schema migration coordination.
- `wave2-review-notes.md` — reviewer findings, 3300 words. Q1-Q5 verdicts. 7 specific edits ranked by severity. 2 new Type-A escalations.

## Key decisions made

1. **3 HIGH edits applied directly via CC Edit tool (per pattern: ≤ 5 small edits → CC direct).** spec-active-recall-base now has env-var seam, recall floor 60% soft, hardened Task 10. Time saved vs iterator subagent: ~5 min.

2. **4 MEDIUM/LOW edits documented but NOT applied.** Rodc reviews + applies (or asks CC to). Reasoning: Rodc may have view on whether vault.js openDetailById exists; Rodc may rebut streak-counter analogy differently than CC. Avoid pre-emptive over-commit.

3. **5-criterion composite launch gate** (per Tier 0c launch-readiness-criteria.md):
   1. Rodc dogfood ≥ 4/5 PASS
   2. ≥ 3/5 user interviews confirm S1 unprompted
   3. ≥ 2/5 candidates surface ≥ 2 of friends-intro 4-conditions
   4. Sarah Day-15 simulation passes Phase B real-API verification
   5. Active recall precision ≥ 80% on dogfood vault

4. **Task DAG** — card-real + active-recall-base parallel from Day 1 → card-dedup + first-insight + vault-recall-history Day 3-7. 5-9 day estimate at Wave 1b velocity; 7-12 with risk buffer + Wave 1c crisis protocol blocker.

5. **Per-spec asymmetric gates aligned with brand-existential signals.** Following Wave 1b v1.8 trust-killer-vs-completeness split-route precedent: precision-as-HARD-ship-blocker, recall/dedup-as-monitor-only with calibration triggers. Edit 2 (recall recall 60% soft floor) corrected the only place this pattern was too lax.

6. **Cross-spec schema migration coordination** — both card-dedup and vault-recall-history target chat_claims_v5. Plan §"Schema migration coordination" flags that single combined PR is required (or rename one to v6 to make order explicit).

## Type-B engineering decisions

- **3 HIGH edits applied direct, 4 MEDIUM/LOW deferred to Rodc** — see Decision 1-2 above.
- **Wave 2 telemetry pipeline scope decision deferred** — Escalation #7. Plan v1.1 cites telemetry triggers without specifying capture mechanism.
- **Reuse `app/shared/recall/orchestrator.py`** verified existing infrastructure — `spec-active-recall-base` reuses `Orchestrator + ThresholdConfig.topic = 0.65 + TopicEvaluator + FTS5 path`. Not parallel infrastructure.

## Cross-task implications

- **Tier 1 Tasks 2-4 (Wave 3 / Acquisition / Pricing):** Will reference Wave 2 specs + 5-criterion launch gate.
- **Tier 1.5 Phase A (dogfood):** Validates active-recall on simulated rounds; Round 11 (Mike Day 24+) is recall-counter validation surface.
- **Tier 1.5 Phase B (sample-verify):** Sarah Day-15 verifies crisis protocol gap (D1 / Escalation #2) — feeds launch-readiness Criterion 4.
- **Tier 2 Task 5 (Marketing Landing):** Wave 2 spec features inform "what Rodix does" landing copy. ⚡ recall callout is brand promise visible in marketing.
- **Tier 2 Task 7 (Documentation Pack):** how-it-works.md describes the 5 Wave 2 features. faq.md addresses recall-precision-creep concern proactively.
- **Tier 2 Task 8 (Privacy Policy + ToS):** vault-recall-history's recall_count metadata is privacy-disclosable per S20.
- **Tier 3 Task 9 (Rodix Design System Skill):** Encodes Wave 2 spec UI patterns for future implementer subagents.
- **Future Wave 1c crisis-content protocol:** Required before Phase 1 alpha launch (Escalation #2). Affects active-recall + first-insight skip-conditions.

## TODO for Rodc

1. **Resolve TYPE-A 1-5** (first-insight threshold / card-dedup threshold / active-recall injection format / crisis protocol timing / defensibility frame leadership)
2. **Resolve NEW Escalation #7** (Wave 2 telemetry-readiness — A/B/C decision)
3. **Resolve NEW Escalation #8** (first-cohort copy-lock confidence — A/B/C decision)
4. **Apply MEDIUM Edits 4, 5, 6 OR accept as v1.1 push back:**
   - Edit 4: spec-card-dedup Task 5 vault_id parameter + LIMIT 100
   - Edit 5: spec-card-real Task 4 openDetailById precondition
   - Edit 6: spec-card-dedup §9 streak-counter rebuttal
5. **Apply LOW Edit 7** (plan §Schema migration coordination wording bump)
6. **Read wave2-review-notes.md** for the full reviewer findings + defenses of strong moves
7. **Decide Wave 2 dispatch timing** — after Wave 1b dogfood + Tier 1.5 verification + interview cohort

## Lessons / patterns noticed

Will append to reusable-patterns.md:
- **Reviewer-found edits as ship-blocker filter:** the 3-HIGH/4-MEDIUM/LOW ranking from reviewer subagent enabled clean batching of "must apply now" vs "Rodc reviews tomorrow" decisions. Severity ranking saved iteration time.
- **Plan v1 → v1.1 + v1.2 implementer-dispatch checklist:** Rather than producing a final plan, leave clear "what's resolved / what's pending / what Rodc decides" markers. Reduces ambiguity at next-session dispatch.

## Cost log

- 5 parallel spec-writer subagents (~750k tokens total)
- 1 plan integrator subagent (~200k)
- 1 plan reviewer subagent (~180k)
- 4 CC Edit operations (3 HIGH spec-active-recall-base + 1 plan changelog)
- ~1.13M total subagent tokens for Task 1
- 0 LLM API calls outside subagents
