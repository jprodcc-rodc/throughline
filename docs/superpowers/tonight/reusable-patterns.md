# Reusable Working Patterns — Tonight Shift

**Use:** Input for next-session Working Mode Internalization task. Append-only, 1-2 sentence flags. Don't extract to skill yet.

---

## Pattern: Archive-then-rebuild on primary-input correction
**Where used:** Task 0a Phase 3 re-run (Rodc located missing rodix-friends-intro.md mid-shift).
**Why reusable:** When canonical input changes mid-task, renaming current outputs to `*-{old-source}-based.md` and re-running cleanly preserves the audit trail without forcing manual diff. Faster than partial-update + safer than overwrite.

## Pattern: Reading-Guide-as-task-instruction header
**Where used:** Task 0a v2 — `rodix-friends-intro.md` carries a header section explicitly addressing brand subagents (archetype/voice/position) with task-specific signal callouts.
**Why reusable:** Any canonical doc can carry an "Expert Reading Guide for [agents X/Y/Z]" header. Subagent prompts then forward this header verbatim — dramatically tighter grounding vs. orchestrator paraphrasing. Cuts hallucination risk + frees orchestrator from re-explaining the doc each dispatch.

## Pattern: Skeptic → Iterator subagent pair (review-as-edit-list)
**Where used:** Task 0a Phase 5 — skeptic produced numbered edits with verbatim quotes; iterator applied surgical Edit-tool changes.
**Why reusable:** When a skeptic format requires "Section affected + verbatim quote + replacement sentence + reason," the iterator's job becomes mechanical (high-quality, low-divergence). Skeptic+iterator pair beats single "review-and-revise" subagent because the format forces specificity + traceability. Applicable to any deliverable review (specs, marketing copy, plans).

## Pattern: Verbatim-quote-or-Grep ground truth requirement
**Where used:** Task 0a Phase 3 v2 — subagent prompts mandated "cite friends-intro VERBATIM" + "use Bash/Grep to verify factual claims."
**Why reusable:** v1 subagents inferred from partial inputs and produced fabricated thresholds (0.75) that didn't exist in code. v2 with verbatim-quote-or-Grep mandate produced markedly more grounded output. Pattern: any subagent making product/spec claims should be required to either quote the source verbatim or Grep to confirm — never paraphrase + assert. Should be standard subagent guardrail.

## Pattern: Architect's flagged-for-Rodc places (subagent self-flagging)
**Where used:** Task 0b — founder-narrative-architect subagent was required to flag sentences that go beyond source canonical input (e.g., "I started keeping rough notes" not in friends-intro). Skeptic then verified via Grep.
**Why reusable:** Without architect's flag-list, both flagged sentences (Escalation #4 + cut "most user-respectful" qualifier) would have shipped uninspected. The flag-list creates a built-in audit checkpoint between architect (creative) and skeptic (verification). Pattern: any architect-style subagent producing prose should be required to surface "places I almost invented content / Rodc to verify" as a structured output section. Skeptic's verification then becomes mechanical Grep work rather than guess-the-fabrication.

## Pattern: Sequential vs parallel subagent dispatch
**Where used:** Task 0c — assumption-extractor first (other 2 read its output) → user-research-strategist + launch-readiness-auditor in parallel.
**Why reusable:** When subagent B + C inputs depend on subagent A's output, dispatch A sequentially first. Then B+C parallel. Cost: ~3 min extra latency for A's run. Benefit: B+C don't race-read empty / stale files. Heuristic: if subagents share input files, parallel safe; if subagent N+1 needs to *read* subagent N's *output*, sequential.

## Pattern: Forced ranking in extraction-style subagent outputs
**Where used:** Task 0c assumption-extractor required to produce 35-55 items + Top 5 foundational + Top 2 contradictions (forced K-rank subset).
**Why reusable:** Flat list of 47 items is hard to act on downstream. Forced Top-K ranking makes the output actionable: subsequent subagents (Wave 2 plan / pricing / marketing) each pull the K highest-priority items. Pattern: any "extract N items" subagent prompt should add "rank top K and explain why each made the cut." Cost: 5% more tokens, dramatic downstream usability gain.

## Pattern: CC-direct-Edit beats iterator-subagent for ≤ 5 small edits
**Where used:** Task 0a + 0b — Phase 5 skeptic produced numbered edits with verbatim quotes; CC applied surgical edits via Edit tool directly instead of dispatching iterator subagent.
**Why reusable:** Subagent dispatch overhead (300+ tokens prompt setup + ~3-5 min latency) is amortized only over multi-edit batches (>5 edits) or when edits require fresh-context judgment. For 3-5 small surgical edits with clear verbatim-replace instructions, CC Edit tool is faster + lower-divergence. Threshold (preliminary): ≤ 5 small edits → CC direct; > 5 or any edit requiring re-think → iterator subagent. Refine threshold based on Tier 1+ data.
