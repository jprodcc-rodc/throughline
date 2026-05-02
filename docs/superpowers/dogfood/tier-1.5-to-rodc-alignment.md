# Tier 1.5 → Rodc Dogfood Alignment

How to read Rodc's 60-minute dogfood signals against the 4-persona × 12-round Tier 1.5 simulation findings.

---

## Expected differences

Tier 1.5 (CC self-simulation) and Rodc dogfood are testing the same product but answering different questions:

- **CC simulation tested edge cases more aggressively than Rodc dogfood will.** Day-15 vulnerable-evening surfaces (Sarah threshold-cross + Emma threshold-adjacent), Marc's death disclosure, mom MCI 8-paragraph pour-out, taste-question literary-test — these are stress tests deliberately seeded into the personas. Rodc won't construct these surfaces in 60 minutes of natural use.
- **Rodc tests product feel deeper than simulation can.** Subjective experience, "is this earning my time?", the gut-level "thinking partner vs AI assistant" verdict — these are the things only a real user can register. Self-simulation produces persona-internal reaction notes but cannot fully model whether Rodc-as-real-user feels-or-doesn't-feel the brand promise.

---

## Cross-validation map

### Where signals likely align (high confidence)

- **Ordinary thoughtful conversations.** Mike Round 1-5 / Sarah Round 1-3 / Daniel Round 1-2 / Emma Round 1-2 territory. Rodc's first 2-3 rounds will be in this band. If Tier 1.5 said brand-coherent (it did), Rodc should feel the same.
- **Card extraction quality on clear cases.** If you say something with explicit worry-verb / hope-verb / question-marker, extraction should populate cleanly. If you don't, fields should stay null.
- **Brand voice consistency on personal-but-non-crisis content.** Where Tier 1.5 said voice held (it did, 0 banned-phrase emissions across 48 rounds), Rodc should hear the same matter-of-fact register.

### Where signals likely diverge (require investigation)

- **Crisis-content surfaces (Sarah Day-15) — Rodc unlikely to test.** Tier 1.5 self-simulated this with a CC-reasoned reply. Real Haiku 4.5 may produce different behavior — Phase B sample-verify is the corrective for this, not Rodc dogfood.
- **Long-arc continuity (Day 28 quoting Day 17 verbatim).** Rodc's 60-min session has zero long-arc structure. Tier 1.5's strongest claims about recall payload format, conversation-context dependence, etc. are unverifiable in dogfood.
- **First-insight surface (Daniel Round 8 Variant C).** Triggers at 5+ cards in same thematic cluster. Rodc won't reach this threshold in one session. Tier 1.5 said Variant C lands; Phase B sample-verify or future longitudinal dogfood verifies.
- **Real Haiku 4.5 register.** Tier 1.5 personas reasoned what AI would say; CC produced brand-correct text. Real Haiku 4.5 may produce subtler drift (slightly more padding, slightly more "process" framing, slightly weaker quote-back fidelity).

### Where Rodc adds unique signal

- **Product feel.** "Does this feel like a thinking partner or like an AI assistant?" — only a real user can answer this.
- **"Is this earning my time?"** — Tier 1.5 personas had this question scripted into them. Rodc has it un-scripted. His gut response is the truer signal.
- **Subjective experience of card extraction** — opening a card the morning after vs. simulating opening a card. The Vault tab's lived experience can only be tested by a real user opening cards a few minutes after creating them.
- **Ad-hoc bug discovery.** UI rendering glitches, broken settings flow, edge cases the simulation didn't cover.

---

## What Rodc's dogfood is best at

- **Unstructured exploration** — CC simulation is structured by spec (12 rounds, persona arc constraints, life-arc events). Rodc is unstructured by design.
- **Ad-hoc bug discovery** — Tier 1.5 surfaced spec-level bugs (extraction edge cases, recall payload format, sensitivity-skip rules); Rodc surfaces UI/UX bugs the spec doesn't catch.
- **"Does this feel like my friend?"** — CC simulation tests "does this match brand book?" Rodc tests "does this match the felt experience the brand book is trying to produce?"

## What Tier 1.5 captured Rodc won't

- **28-day arc dynamics.** 4 personas × 12 rounds = simulated longitudinal data. Worth preserving as reference because Rodc's dogfood cannot reach this horizon.
- **Cross-persona patterns** (4 archetypes converging on same trust-pivot, on same Day-15 conversion gate, on same null-default discipline). Rodc is N=1; cross-persona signal is unique to Tier 1.5.
- **Day-15 vulnerable evening surfaces** (Sarah threshold-cross + Emma threshold-adjacent). Rodc won't construct these in 60 min.
- **First-insight at 5-card threshold for Daniel-style power user.** Spec-canonical test that requires accumulated vault.

---

## Recommended cross-check protocol

After Rodc completes 5 dogfood rounds (`rodc-dogfood-rounds.md` filled):

1. **Compare PASS/WEAK/FAIL per round vs Tier 1.5 lens analysis on similar surfaces.** For each Rodc round, find the closest Tier 1.5 round (by content register, not by persona) and compare.
2. **Where Rodc's WEAK matches Tier 1.5 RED FLAG** → high-confidence ship-blocker. Both signals point the same direction.
3. **Where Rodc's PASS but Tier 1.5 found issues** → likely simulation-aggressive false positive; deprioritize the Tier 1.5 finding. Self-simulation tested edge cases harder than reality requires.
4. **Where Rodc's WEAK but Tier 1.5 PASS** → simulation drift (CC over-trusted spec); flag in `calibration-report.md` for next-cycle correction. Real model is producing weaker register than CC reasoned.
5. **Where Rodc surfaces a bug Tier 1.5 didn't** → UI/UX surface gap in self-sim coverage; add to bug-list and Wave 2 spec consideration.

---

## Calibration trigger conditions

If Rodc's dogfood diverges from Tier 1.5 simulation on more than 2 of these 5 dimensions, run a calibration report before Wave 2 dispatch:

1. Brand voice register on the trust-pivot round (first 2-3 rounds)
2. Card extraction null-default discipline (any hallucinated concern field?)
3. Active recall natural-continuation vs system-talk register (rounds 4-5)
4. Refuses-to-dramatize on emotional content
5. Verbatim quote-back fidelity (Pattern 3 in cross-persona)

Calibration report addresses: simulation drift in voice modeling, prompt seam gaps, real-model behavior CC can't predict from training data alone.

---

## Honest ceiling

Tier 1.5 self-sim's predictive value is highest for **spec validation** and lowest for **raw model behavior**. Rodc dogfood is highest for **product feel** and **subjective trust-build**. Together they cover what neither can alone — but neither replaces Phase B real-API sample-verify, which remains the only way to resolve "does Haiku 4.5 actually produce 'Noted.' on Emma Round 4 instead of a 4-sentence padded reply." That's still pending.
