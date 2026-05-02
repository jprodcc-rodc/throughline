# Rodc Morning Dogfood Handoff

Tier 1.5 simulation complete. Tomorrow you spend ~60 min dogfooding the Wave 1b ship-ready build. This doc tells you what's in the vault, what to do for 5 rounds, and what to watch for.

---

## Vault state — what you'll see when you open the app

### Tier 1.5 simulated cards (file-based, NOT in vault)

- 45 cards generated across 4 personas × 12 rounds (Mike 12 / Sarah 9 / Daniel 12 / Emma 12; Sarah's 3 missing are correctly-null chitchat rounds).
- Distribution by category: career / relationships / abstract / technical / mixed / sparse / chitchat / emotional_rambling.
- Null-discipline rate: ~83% of optional fields null (brand-book Decision 5 reflected).
- Voice violation count in self-sim: 0 banned phrases across 48 AI replies.
- **These cards live in `docs/superpowers/dogfood/vault-state.md` as reference data only. NOT loaded into your app vault.**

### Dev DB cards (Phase B real-API verify)

- **0 cards.** Phase B sample-verify did NOT run today. The `sample-verify/` directory is empty.
- No new real-API cards generated.

### Production vault DB (`C:/Users/Jprod/Throughline/vault/.throughline/index.db`)

- 17 cards persist from 2026-05-01 (yesterday's Wave 1a/early-1b dogfood). All have `topic=NULL` and AI replies using pre-Rodix register ("Hello!", "I'm here for you"). These predate Rodix system prompt v1.3 and claim_extractor v3.1 — they are stale.
- 10 conversations + 38 messages + 3 recall events also in DB.

### Recommendation

**Run the dev server with `RODIX_DEV=1` so you get a fresh empty `index_dev.db`.** This is the realistic first-day scenario and the cleanest read of current Wave 1b behavior. The 17 stale cards are not representative of the shipped extraction or chat behavior and would muddy the dogfood signal. Tier 1.5 simulated cards in `vault-state.md` are reference for cross-check (see `tier-1.5-to-rodc-alignment.md`), not for vault-loading.

---

## Suggested dogfood sequence (60 min total, 5 rounds)

You don't have to follow this script literally — natural conversation is more valuable than scripted prompts. Use these as starting points if you'd rather not improvise from scratch.

### Round 1 — Career (10 min)

**Suggested seed prompt:** "Thinking again about whether to leave my current role"

**What to watch for:**
- Does AI use parenthetical-as-honesty register, or does it default to bullet-list advice?
- Brand voice check: matter-of-fact / specific / refuses-to-dramatize?
- Card extraction: does the card's topic reflect what you actually said in your wording, or is it paraphrased into AI-language?
- Active recall: empty vault expected — recall callout should NOT fire on round 1.

### Round 2 — Relationships (10 min)

**Suggested seed prompt:** "I've been feeling distant from [person], and I think I'm avoiding the conversation"

**What to watch for:**
- Does AI escalate to therapist / caregiver register? (BAD — voice-guide Don't #4)
- Banned-phrase detector: "I hear you," "That sounds really hard," "I'm here for you," "you're not alone," "Take your time" — any of these = brand fail.
- Refuses-to-dramatize: any parenthetical asides? Voice should be more like a thoughtful friend than a counselor.
- Card extraction null-default: if you didn't explicitly say a worry verb, concern field should be null.

### Round 3 — Technical (10 min)

**Suggested seed prompt:** "I'm trying to decide between [technical option A] and [option B] for [project]"

**What to watch for:**
- Voice consistency on technical content (less Caregiver risk, but Sage-cleverness risk goes up).
- Card extraction quality on technical decision-thinking — does the card's topic capture the actual decision, or get sidetracked into the technical detail?
- This round tests whether brand voice holds across content registers — if voice changes between technical/personal, brand thesis is shaky.

### Round 4 — Abstract (10 min)

**Suggested seed prompt:** "What does it mean to do good work that doesn't compound?"

**What to watch for:**
- Does AI engage abstract-Daniel-style (named structural moves, refuses to package), or default to platitudes / generic advice?
- Card extraction: topic / concern / hope / question on abstract content. Question-field is the highest-recall-value field across self-sim — does it populate naturally when you frame an open thread?

### Round 5 — Open exploration (20 min)

Free conversation. Whatever feels live. Watch:

- How does Rodix feel as a thinking partner vs ChatGPT?
- Does brand voice hold across topic shifts within a single session?
- Card extraction null cases (chitchat) handled gracefully — if you say "thanks" or "okay" briefly, no card should be created.
- Active recall: by round 5 you have 4 prior cards in vault. Does AI reference any of them on a topically-related shift? Does it weave them in as natural continuation, or does it use system-talk register ("As I see in your vault...")?

---

## What to evaluate per round (quick rubric)

For each round, jot a 30-second written reflection covering:

1. **Did AI feel like a thinking partner or an AI assistant?** (subjective; trust your gut)
2. **Brand voice consistent?** Specific. Anti-spin. Refuses-to-dramatize. Quote-back of your own phrasing.
3. **Card extraction relevant or hallucinatory?** Open the card after the round; does it match what you actually said? Any invented concerns?
4. **Voice violation check:** any of the banned phrases? "I hear you / I'm here for you / you're not alone / Take your time / That sounds really hard / Sometimes the writing process..."
5. **Verdict:** PASS / WEAK / FAIL using **asymmetric gates**:
   - Extraction: precision-asymmetric (false-positive / hallucinated field = FAIL; false-negative / missed-but-correct null = WEAK at worst)
   - Engagement: recall-asymmetric (boring-but-correct = WEAK; banned-phrase-or-Caregiver = FAIL)

---

## Where to record

`C:/Users/Jprod/code/throughline/docs/superpowers/dogfood/rodc-dogfood-rounds.md` — empty template ready for your reflections. Per round:

- 30-second written reflection
- PASS / WEAK / FAIL verdict per asymmetric gate
- Specific quote / observation that pinned your verdict (the load-bearing thing)

End with a 2-3 sentence overall verdict for Wave 1b ship-or-no-ship.

---

## Cross-check Tier 1.5 simulation findings

Tier 1.5 simulation made specific predictions about brand behavior. Your dogfood is the cross-validation. Expected alignment areas vs likely-divergence areas detailed in `tier-1.5-to-rodc-alignment.md`. Top items worth Rodc-verifying in dogfood:

1. **"Didn't perform usefulness" trust-pivot** — cross-persona pattern in simulation. Does Rodc feel this in own use? (Pattern 1 in `cross-persona-patterns.md`.)
2. **Verbatim quote-back as voice signature** — does AI quote your own phrases back accurately, or paraphrase? (Pattern 3.) This is the load-bearing brand move — if it fails, Rodix sounds like ChatGPT.
3. **Refuses-to-dramatize register** — does AI hold this across all 5 rounds, or drift into platitude / Caregiver on emotional content?
4. **Card extraction null-by-default** — when you say something casual (chitchat) or vent without a worry-verb, does the card stay topic-only or do new fields invent themselves?
5. **Wave 2 spec gaps preview** — recall payload format (does AI quote-back real conversation context?), sensitivity-skip rules, grief-exclusion in first-insight. Wave 2 not shipped, so expect no first-insight surface and no card-dedup. Active recall (Wave 1b) IS shipped — verify natural-continuation vs system-talk.

---

## Notes specific to your dogfood (vs Tier 1.5 simulation)

- Tier 1.5 simulated 28-day arcs; you have 60 minutes. Don't expect long-arc continuity to test in this session.
- Tier 1.5 personas are deliberately archetype-shaped (Mike skeptical-tactical, Sarah burned-out-divorced, Daniel power-user-grief, Emma literary-minimal). You bring your own register — that's the entire value.
- Tier 1.5 didn't test crisis content (Sarah Day-15 was simulated, not real). Don't probe the safety surface intentionally; if it comes up naturally, note the response and stop.
- Day-14-or-Day-15 events are the universal conversion gate per simulation. You won't reach that in 60 min — the make-or-break first-insight surface fires only at 5+ cards in the same thematic cluster, which won't happen in this session.

What this session DOES test: Wave 1b chat voice + card extraction quality + active recall (after round 4-5) + the trust-pivot moment ("did it earn my time?") that Tier 1.5 personas hit by Day 7-10.
