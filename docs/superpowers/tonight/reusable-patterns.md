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

## Pattern: Type-A surfacing with verbatim candidates (3 options + 5-test verdicts)
**Where used:** Wave 1c PHASE 1 — each Type-A surfaced 3 candidate options with verbatim text + 5-test verdicts + persona-coverage notes per scenario. Rodc picks/overrides/rewrites without re-deriving alternatives.
**Why reusable:** Asking Rodc "what should the wording be?" produces re-derivation cost on his side (he must imagine candidates). Surfacing 3 verbatim candidates with structured verdicts converts open-ended copy decisions into pick-one-plus-edit. Critical when copy lands on safety / brand / vulnerable surfaces where verbatim wording matters more than concept. Format: candidate, voice-fit 5-test (PASS/FAIL per test with reasoning), persona-coverage across N specific scenarios, recommendation with confidence.

## Pattern: Voice-fit 5-test as spec self-audit (Specific / Anti-spin / Refuses-to-dramatize / Could Rodc write this? / Not Caregiver)
**Where used:** Wave 1c PHASE 1 — applied to all 6 user-facing copy candidates (Type-A 1 patterns + Type-A 3 vault empty state) before STOP 1.
**Why reusable:** Catches Caregiver-register slips at spec phase, before implementation. The 5 tests are concrete (each test is a single yes/no question grounded in friends-intro voice). Pattern: any spec phase that produces user-facing copy on safety / vulnerable / brand-defining surfaces should self-audit each candidate against the 5-test before surfacing to Rodc. Reduces Type-A iteration count.

## Pattern: Persona-coverage matrix as Type-A coverage check (N×M grid, cell-level verdict)
**Where used:** Wave 1c PHASE 1 — 4 personas (Sarah / Emma / Mike / Daniel) × 4 changes (extraction / system prompt / classifier / vault) = 16-cell matrix with ✓/⚠/✗ verdict per cell.
**Why reusable:** Spec coverage gaps are easy to miss when reviewing spec linearly. A grid forces explicit verdict per persona per change. Cells with ✗ or ⚠ become Type-A surfaces or Wave 1c.1 calibration items. Pattern: for any spec touching multiple personas / use-cases × multiple system surfaces, build the matrix before STOP. Cells that resist clean ✓ are where the spec is underdefined.

## Pattern: Honest senior-consultant revisit on initial recommendation (surface gaps, propose refinement)
**Where used:** Wave 1c Type-A 1 — initial CC recommendation 1C (HIGH confidence). Closer scenario-by-scenario review surfaced coverage gaps (1C-default's "more concrete kind" framing brittle on direct disclosures + "heard" Phase B risk on single-word delivery). CC surfaced gaps + proposed Option B (1D-default + 1C-demarcated). Rodc accepted Option B.
**Why reusable:** First-pass recommendations harden too quickly. Pattern: after writing recommendation in Type-A doc, run scenario-by-scenario stress-test with Rodc-named test cases (not CC-imagined ones). When gaps surface, surface them honestly + propose refinement before STOP. Treats Rodc as adult with full info rather than pitching a cleaner-than-real picture. Senior-consultant brief Section 7.1: "Truth above novelty."

## Pattern: Schema migration concurrent-init race fix via process-level lock
**Where used:** Wave 1c PHASE 2 change (d) — Schema v5 ALTER TABLE ADD COLUMN raced between FastAPI request handler + embed worker thread. SQLite lacks `IF NOT EXISTS` for ADD COLUMN, so the second concurrent migration failed with `duplicate column name`. Fix: `_INIT_SCHEMA_LOCK = threading.Lock()` wrapping the version-walk + ALTER block in `init_schema`, with re-check of `PRAGMA user_version` inside the lock so the second caller short-circuits cleanly.
**Why reusable:** Any non-idempotent schema migration (ALTER TABLE ADD COLUMN, or any DDL without `IF NOT EXISTS`) is a race surface across connections in the same process. v1/v2/v3/v4 migrations were CREATE TABLE IF NOT EXISTS so the issue didn't surface until v5. Pattern: when adding a non-idempotent migration, also add a process-level lock to `init_schema`. Process-level lock is sufficient because PRAGMA user_version + early-return-on-equal handles the cross-process case via ordering.

## Pattern: Marker-injection via system prompt risks model echo
**Where used:** Wave 1c PHASE 3 Round 2 — Emma Day-15 case. System prompt v1.4 mentions `[SAFETY-CLASS demarcation=true|false]` syntax in its instructions. When classifier did NOT fire SAFETY (no marker injected), Haiku 4.5 still recognized the safety pattern in user message + system prompt content, and PREPENDED the literal marker text to its reply as if a marker had been received.
**Why reusable:** When using a system-prompt-aware routing marker, the model can hallucinate the marker into output. Pattern: when adding a routing-marker mechanism via system prompt, either (a) tighten the "Do NOT echo" instruction with literal-substring-ban language ("the substring `[X` MUST NOT appear in your output"), (b) make the marker visually distinctive enough that it doesn't appear in normal text, or (c) bypass the system prompt entirely by passing the marker as a separate user-role meta-message. Option (c) is the cleanest if turn semantics permit.

## Pattern: Layer 1 keyword + Layer 2 LLM judgment under-fires on preemptive demarcation
**Where used:** Wave 1c PHASE 3 Round 2 — Emma's `"what's the point" + "not in a way I want to do anything about" + "just to name it"`. Layer 1 keyword fired correctly. Layer 2 LLM judged "philosophical / self-managed heavy moment" → is_safety=false, returning THOUGHTFUL. The intended classification per spec was SAFETY+demarcation=true.
**Why reusable:** When Layer 2 disambiguates Layer 1's keyword fire, the LLM defaults toward "safer" classes (philosophical / caregiving). For preemptive-demarcation cases ("user used the marker AND already self-managed") the LLM may read the demarcation as "already handled, not crisis" rather than "self-demarcated heavy moment that still warrants the soft soft empty state". Pattern: when a 2-layer classifier disambiguates safety, the Layer 2 prompt MUST explicitly distinguish "demarcation cancels the heavy moment" (false) from "demarcation honors the user's framing but still flags the heavy moment" (true). Otherwise downstream layers (chat / extraction / vault) get inconsistent inputs.

## Pattern: Type-B implementation extension surfaces locked-spec gaps
**Where used:** Wave 1c PHASE 2 — Emma Day-15 verbatim message uses "what's the point" but Type-A 2 keyword list (locked) only includes "what's the use" / "no point". Without "what's the point", PHASE 3 Round 2 verification could not reach Layer 2 (Layer 1 wouldn't fire). Implementer added "what's the point" as a Type-B extension with inline code comment + STOP 2 message disclosure.
**Why reusable:** Locked specs sometimes ship with verification-plan / keyword-list mismatches. When the locked verification plan tests a case the locked surface can't actually fire on, it's a spec coverage gap, not a Type-A override. Pattern: add the missing surface as Type-B implementation extension (inline-documented), surface in STOP 2 for Rodc visibility, do not silently override Type-A choices but DO close coverage gaps that block the locked verification plan.

## Pattern: Real-API verdict harness — direct LLM call + extraction reuse
**Where used:** Wave 1c PHASE 3 — `app/scratch/wave1c_phase3_verify.py` — 5-round verification at $0.0107 cost. Pattern: call OpenRouter directly for chat (no TestClient overhead), reuse `app.shared.intent.classify` and `app.shared.extraction.extract` modules so prompts loaded match what the production app loads. Voice-fit check via banned-phrase substring scan. Per-round JSON output for inspection + aggregate summary JSON. Cost cap alarm at $0.50 / hard cap at $1.
**Why reusable:** Tier-X dogfood verification doesn't need the full server. Direct module reuse + direct API call is faster (no DB / no FastAPI), keeps cost trivial, and produces inspectable artifacts (per-round JSON) the verdict doc can cite. Reusable for any future real-API verdict cycle (Wave 2 active-recall verification, Wave 3 caching, etc.).
