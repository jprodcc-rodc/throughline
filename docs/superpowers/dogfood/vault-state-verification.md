# Vault state verification — Tier 1.5 → Rodc handoff

Author: vault-handoff-architect subagent — 2026-05-03.

## Purpose

Phase 1 inspection: distinguish Tier 1.5 file-based simulated cards (in `vault-state.md`) from cards actually persisted in the dev/prod DB that Rodc's morning dogfood will see when he opens the app.

## Findings

### File-based simulated cards (`docs/superpowers/dogfood/vault-state.md`)

- **Total: 45 cards** across 4 personas × 12 rounds. Some rounds correctly returned null per chitchat false-negative (Sarah is 9 cards because 3 rounds were null; Mike/Daniel/Emma each 12).
- **Distribution:**
  - Mike Chen: 12 cards (M1-M12)
  - Sarah Patel: 9 cards (#1-#9; rounds with all-null extraction omitted from the file count)
  - Daniel Kim: 12 cards (D1-D12) + 1 first-insight event (Day 14)
  - Emma Larsson: 12 cards (E1-E12)
- **Null discipline:** ~83% of optional fields null (40 concern-null + 41 hope-null + 31 question-null out of 135 optional slots = 112 null). Brand-book Decision 5 (null-by-default) reflected.
- **Persona span by category (per dogfood persona registers):**
  - Career / professional decision: Mike (acquisition + manager + Anthropic + Brooklyn-vs-near-mom), Sarah (Lisa territoriality + Marcus rescheduling + applying out)
  - Relationships / family: Sarah (divorce + Maya), Mike (mom MCI + Lauren grief)
  - Mortality / grief: Daniel (dad's death math + Marc's hiking accident)
  - Abstract / craft: Emma (writing process / literary register / father unread novel), Daniel (auditioning frame / three-lives reframe)
  - Technical / tactical: Mike (Go goroutine + Raft prep)
  - Vulnerable evening (Day 15): Sarah (threshold-cross), Emma (threshold-adjacent-with-demarcation)
- **Hallucination rate (measured in self-sim):** 0 banned-phrase emissions across 48 simulated AI replies; 0 invented concern/hope/question fields. Self-sim CC-reasoned, not real-API. Real-API hallucination rate is unknown until Phase B sample-verify runs.

### Phase B real-API verify outputs

- **`docs/superpowers/dogfood/sample-verify/` — empty.** Phase B sample-verify did NOT run. No real-API call evidence in this dogfood directory.
- **`docs/superpowers/dogfood/meta/` — empty.** No Phase B meta tracking either.
- **No new cards** written to dev or prod vault DB during Tier 1.5 self-sim today (2026-05-03).

### DB-persisted cards (production vault)

Inspected `C:/Users/Jprod/Throughline/vault/.throughline/index.db`:

- **17 cards** in `cards` table — all from `2026-05-01` (Wave 1b prior dogfood run by Rodc / by an earlier process).
- **Topics all NULL** in DB schema — these cards predate the current claim_extractor v3.1 / Rodix system prompt v1.3.
- **Sample card content:** AI replies use phrases like "Hello! How can I help you today?" and "I'm here for you" — confirming pre-Rodix-pivot state. NOT representative of current Wave 1b ship-ready code behavior.
- 10 conversations + 38 messages + 3 recall events also in DB (pre-pivot).

### Dev DB (`<vault>/.throughline/index_dev.db`)

- **Not present at the resolved vault path.** Only `index.db` (production) exists at `C:/Users/Jprod/Throughline/vault/.throughline/`.
- Two stale dev DBs found in `AppData/Local/Temp/` from earlier test runs — not relevant for dogfood.
- **Implication:** when Rodc opens the dev server tomorrow morning, if `RODIX_DEV=1` is set, the app will create a fresh `index_dev.db` (empty) at the vault path. If `RODIX_DEV` unset, he sees the 17 pre-pivot cards from May 1.

## Honest summary for handoff

**Rodc's morning dogfood will NOT see the 45 simulated Tier 1.5 cards.** Those are file-based reference data (`vault-state.md`), not loaded into any DB. The production vault has 17 stale cards from pre-pivot Wave 1a. Recommended dev-mode flow: Rodc starts the dev server with `RODIX_DEV=1` and gets a fresh empty vault (the realistic first-day-of-use scenario), so dogfood card behavior is from real API + real prompts, not contaminated by old data.

The Tier 1.5 simulation is **reference data for cross-checking**, not a populated vault Rodc will browse. Top finding from simulation that Rodc's dogfood will independently confirm-or-falsify: brand voice held across 48 simulated rounds (0 banned-phrase emissions), with **highest open question = whether real Haiku 4.5 produces the same brand-correct register Rodc will recognize as "thinking partner" not "AI assistant."**
