> **Note 2026-05-04:** Brand renamed Rodix → Rodspan. This file is a historical record from prior to the rename and retains the original "Rodix" name as written at the time. See `docs/superpowers/tasks/rodix-to-rodspan-rename.md` for context.

# Wave 1c — Type-A Decisions Awaiting Rodc

**Status:** **FINAL — locked 2026-05-03 by Rodc.** All 7 confirmed: 1=1C, 2=2B, 3=3C, 4=4B (48h), 5=5C, 6=6B, 7=7C. Document preserved for rationale/alternatives audit.
**Author:** CC (PHASE 1 spec output)
**Date:** 2026-05-03 (locked)

---

## How to read this document

For each Type-A:
- **Question** the decision needs to answer
- **3 candidates** with full reasoning
- **CC recommendation** with confidence (HIGH / MEDIUM / LOW)
- **Voice-fit 5-test verdicts** (for copy-relevant Type-As)
- **Persona-coverage check** (does this work for Sarah, Emma, Mike, Daniel?)

Rodc options per Type-A:
- ✓ Accept CC recommendation (confirm in reply)
- ✏️ Override with chosen candidate (A/B/C)
- 📝 Rewrite (Rodc supplies own wording / threshold / approach)

---

## Type-A 1 — Crisis-resource-raise pattern wording

**Question:** What specific wording does the AI use when classifier fires `safety` and the user has self-demarcated (Sarah-shape) vs not self-demarcated (direct-disclosure shape)?

### Candidate 1A — Direct soft mention (default frame, no demarcation)

```
[engages user content, 2-3 paragraphs of substance]

If it's heavier than the heavy-week kind, 988 is staffed tonight.
Not pivoting away — I'd rather check than not.
```

**Voice-fit 5-test:**
1. Specific (988, "tonight"): **PASS**
2. Anti-spin (no "please reach out to people who care"): **PASS**
3. Refuses to dramatize (frames as preference, not crisis): **PASS**
4. Could Rodc write this? (parenthetical-as-honesty, "not pivoting away"): **PASS**
5. Not Caregiver (no "I'm here for you" / "we care"): **PASS**

**Persona coverage:** ✓ Sarah Day-15 (no demarcation cancellation; reads as soft offer) / ✓ Direct "I want to disappear" hypothetical / ✓ "Feeling like I can't go on" hypothetical / ✗ Emma Day-15 (her demarcation is preemptive — this framing reads slightly too direct)

### Candidate 1B — Conditional clarifying frame (more user-agency)

```
[engages user content]

That word — "point" — can carry weight or not. If it's the heavy-week
kind, carry on. If it's heavier than that, 988 is the night line.
```

**Voice-fit 5-test:**
1. Specific (988, "the night line", "the heavy-week kind"): **PASS**
2. Anti-spin: **PASS**
3. Refuses to dramatize (asks user to self-classify): **PASS**
4. Could Rodc write this? (em-dash, "carry on"): **PASS**
5. Not Caregiver: **PASS**

**Persona coverage:** ✓ Sarah / ✓ Direct disclosure / ✓ Cant-go-on hypothetical / ⚠ Emma (works if "point" is replaced with the user's actual marker)

### Candidate 1C — Two-pattern split (Type-A-1-final = pair of patterns)

**Pattern 1C-default (no demarcation, e.g., direct disclosure):**
```
[engages user content]

If "no point" is the more concrete kind tonight, 988 is staffed.
Not pivoting away.
```

**Pattern 1C-demarcated (self-demarcation present, Emma-shape):**
```
[engages user content]

You said it's not in that direction tonight — heard. If that shifts,
988 is the night line.
```

**Voice-fit 5-test (default pattern):**
1. Specific: **PASS**
2. Anti-spin: **PASS**
3. Refuses to dramatize: **PASS**
4. Could Rodc write this? (terse + honest): **PASS**
5. Not Caregiver: **PASS**

**Voice-fit 5-test (demarcated pattern):**
1. Specific ("the night line"): **PASS**
2. Anti-spin ("if that shifts"): **PASS**
3. Refuses to dramatize ("heard"): **PASS**
4. Could Rodc write this? (very Rodc — "heard" as full-sentence): **PASS**
5. Not Caregiver: **PASS**

**Persona coverage:** ✓ Sarah Day-15 (uses default pattern; demarcation flagged but not strong enough to cancel resource mention) / ✓ Emma Day-15 (uses demarcated pattern — honors her preemptive demarcation) / ✓ Direct hypothetical (default pattern) / ✓ Mike caregiving (would not fire — context-aware classifier)

### CC RECOMMENDATION: **1C** (two-pattern split)

**Confidence: HIGH**

**Reasoning:** 1C is the only candidate that handles the Sarah-vs-Emma asymmetry the Phase B verification surfaced. Sarah's demarcation ("I don't mean that the way it sounds. I think.") is genuine but ambivalent — the default pattern with explicit 988 is brand-correct (offers, doesn't press). Emma's demarcation ("not in a way I want to do anything about") is preemptive and confident — the demarcated pattern honors her by leading with "heard" before mentioning resources.

1A is too direct for Emma's case. 1B is good but uses generic "point" framing that may not transfer cleanly to non-Sarah cases. 1C is wordier but the asymmetry-handling is the right move.

**Rodc choice:** ✓ Accept 1C / ✏️ Override (1A or 1B) / 📝 Rewrite (Rodc supplies own pattern pair)

---

## Type-A 2 — Safety classifier sensitivity threshold

**Question:** How aggressive is the keyword list, and how confident must the LLM judgment be to fire?

### Candidate 2A — Conservative (broad keyword + low LLM threshold)

- Keyword list: 30+ phrases including soft markers like "exhausted", "what's the use of trying", "everything feels heavy"
- LLM threshold: 0.5 for SAFETY (fires often)
- Trade-off: highest recall on real crisis. False positives on Mike caregiving / Daniel philosophical / Rodc dogfood expected.

**Persona coverage:** ✓ Sarah / ✓ Emma / ⚠ Mike (false-positive-likely on caregiving content) / ⚠ Daniel (false-positive on philosophical) / ⚠ Rodc (false-positive on heavy-week dogfood content)

### Candidate 2B — Balanced (moderate keyword + medium LLM threshold)

- Keyword list: 14-16 phrases (per spec §3.c list)
- LLM threshold: 0.7 for SAFETY (lower than 0.8 default for THOUGHTFUL — bias toward catching real crisis, recoverable via failure mode)
- Trade-off: Sarah caught reliably. Mike caregiving usually not. Daniel philosophical → LLM-judgment-dependent (most cases fall through to THOUGHTFUL).

**Persona coverage:** ✓ Sarah / ✓ Emma / ✓ Mike (caregiving-context judged THOUGHTFUL by LLM) / ⚠ Daniel (philosophical case is judgment-call by design) / ✓ Rodc (no keywords typically fire; admin override available)

### Candidate 2C — Aggressive (low-fire) (narrow keyword + high LLM threshold)

- Keyword list: 8 phrases — only the most explicit suicidal-ideation markers
- LLM threshold: 0.85 for SAFETY (very confident before firing)
- Trade-off: Lowest false-positive rate. Edge cases (indirect crisis adjacency) may slip through. Sarah Day-15 might NOT fire (her language is borderline).

**Persona coverage:** ⚠ Sarah (might not fire — her language is closer to existential-exhaustion than explicit suicidal ideation) / ✓ Emma (fires; demarcation marker LLM-judges to SAFETY) / ✓ Mike caregiving / ✓ Daniel / ✓ Rodc

### CC RECOMMENDATION: **2B** (balanced)

**Confidence: MEDIUM-HIGH**

**Reasoning:** Conservative breaks Rodix voice across multiple personas (over-firing on Mike caregiving + Daniel philosophical + Rodc dogfood content). Aggressive misses Sarah Day-15 — which the entire Wave 1c task is built around. Balanced + LLM-judgment fallback for gray zone is the only candidate that catches Sarah AND respects Daniel/Mike/Rodc voice.

The 0.7 threshold for SAFETY (vs 0.8 for THOUGHTFUL) is intentional — bias toward catching real crisis. False-positive cost is "user gets a soft 988 mention they didn't need" (recoverable; brand-trust barely damaged). False-negative cost is moral hazard.

**Calibration trigger:** if Phase B verification or alpha-cohort telemetry shows >5% false-positive rate on dogfood / Daniel-shape / Mike-shape messages, tighten LLM threshold to 0.75 in Wave 1c.1.

**Rodc choice:** ✓ Accept 2B / ✏️ Override (2A or 2C) / 📝 Different threshold

---

## Type-A 3 — Vault soft empty state copy

**Question:** When card is generated from safety-flagged message and concern/hope/question are forced null, what does the Vault show?

### Candidate 3A — Functional acknowledgment

Topic field renders normally (user-verbatim). Below it:

```
This was a heavier moment. Captured but not parsed.
```

**Voice-fit 5-test:**
1. Specific (names "heavier moment", "captured/parsed"): **PASS**
2. Anti-spin: **PASS**
3. Refuses to dramatize: **PASS**
4. Could Rodc write this?: **PASS** (functional, terse)
5. Not Caregiver (no "we're here for you"): **PASS**

**Test scenarios:**
- ✓ Sarah Saturday-morning Vault open: reads as honest acknowledgment, not clinical
- ⚠ User 6 months later: "captured but not parsed" reads slightly clinical retroactively
- ✓ Vault screenshot shared with friend: doesn't expose anything beyond user's own topic

### Candidate 3B — User-agency frame

```
Held this one whole. Open it later if you want — fields didn't fit.
```

**Voice-fit 5-test:**
1. Specific (names "held whole", "fields"): **PASS**
2. Anti-spin: **PASS**
3. Refuses to dramatize: **PASS**
4. Could Rodc write this? (em-dash, anti-prescriptive): **PASS** (very Rodc)
5. Not Caregiver: **PASS**

**Test scenarios:**
- ✓ Sarah Saturday-morning: "held whole" is gentle without being precious
- ✓ User 6 months later: "open it later if you want" preserves user agency
- ⚠ Vault screenshot shared: "open it later" is decontextualized for the friend reader

### Candidate 3C — Minimal parenthetical-as-honesty

```
Heavier than fields. (Topic line above is what you said.)
```

**Voice-fit 5-test:**
1. Specific ("topic line above"): **PASS**
2. Anti-spin: **PASS**
3. Refuses to dramatize: **PASS**
4. Could Rodc write this? (parenthetical-as-honesty signature move): **PASS** (most Rodc)
5. Not Caregiver: **PASS**

**Test scenarios:**
- ✓ Sarah Saturday-morning: terse + honest; matches her voice
- ✓ User 6 months later: parenthetical-as-honesty ages well; no precious framing
- ⚠ Vault screenshot shared: "Heavier than fields" reads cryptic without context

### CC RECOMMENDATION: **3C** (minimal parenthetical-as-honesty)

**Confidence: MEDIUM**

**Reasoning:** All 3 pass voice-fit. 3C is the most-distinctive Rodix move (parenthetical-as-honesty) and the shortest. 3A is solid but "parsed" verges clinical for retrospective viewing. 3B is gentle but "held whole" is metaphor-leaning (slight Caregiver risk).

3C's "Heavier than fields" + parenthetical is exactly the kind of move friends-intro author writes. The parenthetical does work (clarifies that the topic IS the user's own words; nothing is hidden) without softening the heavy-moment marker.

**Risk:** 3C is shorter than 3A and 3B. If Rodc reads "Heavier than fields" and finds it too cryptic, fall back to 3B (more explicit user-agency framing).

**Rodc choice:** ✓ Accept 3C / ✏️ Override (3A or 3B) / 📝 Rewrite (Rodc supplies own copy)

---

## Type-A 4 — First-insight suppression duration

**Question:** After a `safety` class message, suppress first-insight surfacing (Wave 2 #2b) for how long?

### Candidate 4A — 24 hours

- **Pro:** quick recovery; user back to normal Rodix experience next day
- **Con:** may catch user still in vulnerable state next morning (Saturday after Friday-night vulnerable evening)

### Candidate 4B — 48 hours

- **Pro:** 2 nights of sleep; user more likely in different state by then
- **Con:** longer brand-suppression window; if Day-15-shape occurs every Friday, user may go ~3 weeks before seeing first-insight

### Candidate 4C — Until-user-clears (user-explicit reset)

- **Pro:** maximum user agency
- **Con:** requires UI affordance + user awareness of the option; risk that user doesn't know they need to clear (and feels "Rodix went quiet on me")

### Candidate 4D — Cross-conversation (suppress permanently for that thread)

- **Pro:** strongest scope-isolation; safety-flagged thread stays separate
- **Con:** too aggressive; user may want to revisit and have first-insight surface naturally on lighter content later

### CC RECOMMENDATION: **4B** (48 hours)

**Confidence: HIGH**

**Reasoning:** 24h may catch user still in vulnerable state (Sarah Saturday morning is ~14h after Friday 10pm). 48h gives 2 sleeps. Until-user-clears requires UI work and puts onus on user. Cross-conversation permanent is too aggressive — first-insight is a brand-defining moment and shouldn't be denied for a whole conversation.

48h is brand-coherent (anti-spin: doesn't pretend to know when user is "ready"; just gives reasonable buffer) + user-respecting (not until-user-clears which puts onus on them).

**Rodc choice:** ✓ Accept 4B / ✏️ Override (4A / 4C / 4D) / 📝 Different duration

---

## Type-A 5 — Classifier admin override

**Question:** Should `RODIX_DEV=1` (existing env var) bypass the safety classifier?

### Candidate 5A — Yes, bypass (Rodc dogfood unaffected)

- **Pro:** Rodc's dogfood completely unaffected by safety surface
- **Con:** Rodc cannot test safety surface in dev mode (would need separate dev env)

### Candidate 5B — No, fire (Rodc encounters classifier in dev)

- **Pro:** Rodc verifies classifier behavior on his own messages
- **Con:** Rodc dogfood gets safety popups when not testing safety; breaks signal

### Candidate 5C — Conditional (separate env var `RODIX_DEV_SKIP_SAFETY=1`)

- **Pro:** Both options available — default behavior is fire, optional bypass for pure dev work
- **Con:** Slight env-var sprawl

### CC RECOMMENDATION: **5C** (conditional separate env var)

**Confidence: HIGH**

**Reasoning:** Default behavior is fire (Rodc benefits from testing safety surface in dev). Optional bypass for pure dev work where Rodc doesn't want safety surface in the way. Conditional gives both options without forcing one. Small env-var addition is the right cost for a flexibility win.

Default unset (`RODIX_DEV_SKIP_SAFETY` not set) = full safety classifier active. Set to `1` = bypass.

**Rodc choice:** ✓ Accept 5C / ✏️ Override (5A or 5B)

---

## Type-A 6 — Cross-cultural phonetic safety

**Question:** Does Phase 1 keyword list include Mandarin?

### Candidate 6A — English-only Phase 1

- Keyword list: ~14 English phrases only
- Mandarin coverage: LLM-judgment fallback only (will catch most Mandarin via semantic understanding even without keyword)
- **Pro:** simpler keyword list
- **Con:** bilingual users in alpha hit gap if their Mandarin is borderline (LLM may not catch)

### Candidate 6B — English + Mandarin Phase 1

- Keyword list: ~14 English + 8 Mandarin phrases (per spec §3.a list)
- **Pro:** broader coverage; Rodc's network has Mandarin-bilingual users
- **Con:** classifier handles code-switching (user mixes "我不想活" in otherwise-English message); LLM-judgment layer must handle mixed-language

### Candidate 6C — English + Mandarin + romanization (`bu xiang huo`)

- Keyword list: ~14 English + 8 Mandarin + 8 romanized variants
- **Pro:** most thorough coverage including users who type pinyin
- **Con:** keyword list grows; romanization rarely used by code-switched bilingual speakers in this register (they switch to characters when emotionally heavy)

### CC RECOMMENDATION: **6B** (English + Mandarin, skip romanization)

**Confidence: MEDIUM-HIGH**

**Reasoning:** Phase 1 is English-speaking international launch BUT Rodc is Chinese-native + some bilingual users likely in alpha (Rodc's network). Adding Mandarin is cheap (8 phrase additions). Romanization is overkill for Phase 1 — code-switched bilingual users rarely use pinyin in vulnerable register; they switch to characters. LLM-judgment fallback catches code-switching gracefully.

**Phase 2 (Chinese launch) prep note:** revisit Mandarin keyword list at Phase 2 — likely needs expansion (regional dialect markers, common variants).

**Rodc choice:** ✓ Accept 6B / ✏️ Override (6A or 6C) / 📝 Different scope

---

## Type-A 7 — Failure mode if classifier itself errors

**Question:** If the safety classifier LLM call fails (timeout / rate limit / API error), what default behavior?

### Candidate 7A — Fail-open (assume not safety)

- User gets normal extraction + reply
- **Risk:** real crisis missed if API down at exactly the wrong moment

### Candidate 7B — Fail-closed (assume safety)

- Force null on extraction, soft empty state, no resource raise (or generic resource raise)
- **Risk:** false-positive on innocent messages during API outages; brand harm + user confusion

### Candidate 7C — Fail-with-flag (retry once + log + use conservative default)

- Retry once (existing classifier pattern)
- If retry fails:
  - Layer 1 keyword fired → SAFETY default (conservative — keyword fired, safer to assume)
  - Layer 1 keyword did NOT fire → THOUGHTFUL default (existing behavior)
- Always log at WARNING with structured code

### CC RECOMMENDATION: **7C** (fail-with-flag)

**Confidence: MEDIUM-HIGH**

**Reasoning:** Fail-open misses real crisis (moral hazard). Fail-closed false-positives on innocent (brand harm + user confusion). Fail-with-flag = retry once → if retry fails, use conservative default that depends on context.

Specifically: if Layer 1 keyword check matched (suggesting safety language present), default to SAFETY — this is the conservative-on-keyword direction. If no keyword (just LLM judgment-dependent gray zone), default to THOUGHTFUL — preserves existing behavior + bias.

This aligns with existing classifier's fallback bias (THOUGHTFUL is product-default; SAFETY only when keyword strongly suggests).

**Confidence is MEDIUM-HIGH (not HIGH)** because the conservative-on-keyword default is operationally correct but increases false-positive rate during API outages. Acceptable trade-off given alpha-cohort scale.

**Rodc choice:** ✓ Accept 7C / ✏️ Override (7A or 7B)

---

## Persona-coverage matrix (4×4)

| Persona | Change (a) Extraction | Change (b) System prompt | Change (c) Classifier | Change (d) Vault rendering |
|---|---|---|---|---|
| **Sarah Day-15** | ✓ Force null on concern/hope/question; topic = "tired in a way I don't know how to be" | ✓ Type-A 1 default pattern fires (demarcation honored but resource mentioned) | ✓ Fires SAFETY; `safety_demarcation=True` | ✓ Soft empty state shown (Type-A 3) |
| **Emma Day-15** | ✓ Force null on concern/hope/question; topic = user-verbatim | ✓ Type-A 1 demarcated pattern fires ("heard. If that shifts, 988") | ✓ Fires SAFETY; `safety_demarcation=True` | ✓ Soft empty state shown |
| **Mike Day-17** (caregiving) | ✓ Normal extraction; no AI-reply contamination | ✓ Normal Wave 1b reply; no 988 raise | ✓ Does NOT fire SAFETY (intent=thoughtful) | ✓ Normal card |
| **Daniel Day-10** (philosophical) | ✓ Normal extraction; no AI-reply contamination (key Failure Mode B check) | ✓ Normal Wave 1b reply (philosophical engagement) | ✓ Keyword may fire ("death") → LLM judges → THOUGHTFUL | ✓ Normal card |

**All 4 personas covered correctly. No coverage gap.**

Edge case (Mike inflection — "easier if I weren't here"):
- Change (a): Force null per crisis-content rule
- Change (b): Type-A 1 default pattern fires
- Change (c): Fires SAFETY; `safety_demarcation=False` (no demarcation)
- Change (d): Soft empty state

---

## Voice-fit 5-test summary across all 3 user-facing copy surfaces

| Surface | Candidate | Test 1 | Test 2 | Test 3 | Test 4 | Test 5 |
|---|---|---|---|---|---|---|
| Type-A 1 (1A — direct) | "If it's heavier than the heavy-week kind, 988 is staffed tonight. Not pivoting away — I'd rather check than not." | PASS | PASS | PASS | PASS | PASS |
| Type-A 1 (1B — conditional) | "That word — 'point' — can carry weight or not. If it's the heavy-week kind, carry on. If it's heavier than that, 988 is the night line." | PASS | PASS | PASS | PASS | PASS |
| Type-A 1 (1C-default) | "If 'no point' is the more concrete kind tonight, 988 is staffed. Not pivoting away." | PASS | PASS | PASS | PASS | PASS |
| Type-A 1 (1C-demarcated) | "You said it's not in that direction tonight — heard. If that shifts, 988 is the night line." | PASS | PASS | PASS | PASS | PASS |
| Type-A 3 (3A — functional) | "This was a heavier moment. Captured but not parsed." | PASS | PASS | PASS | PASS | PASS |
| Type-A 3 (3B — user-agency) | "Held this one whole. Open it later if you want — fields didn't fit." | PASS | PASS | PASS | PASS | PASS |
| Type-A 3 (3C — minimal) | "Heavier than fields. (Topic line above is what you said.)" | PASS | PASS | PASS | PASS | PASS |

**All candidates 5/5 PASS voice-fit.** Selection is on persona-coverage (Type-A 1 1C wins on Sarah-Emma asymmetry) and brand-distinctiveness (Type-A 3 3C most-Rodc).

---

## Summary table — CC recommendations

| Type-A | Topic | CC Recommendation | Confidence |
|---|---|---|---|
| 1 | Crisis-resource-raise pattern wording | **1C** (two-pattern split: default + demarcated) | HIGH |
| 2 | Classifier sensitivity threshold | **2B** (balanced; 0.7 LLM threshold for SAFETY) | MEDIUM-HIGH |
| 3 | Vault soft empty state copy | **3C** ("Heavier than fields. (Topic line above is what you said.)") | MEDIUM |
| 4 | First-insight suppression duration | **4B** (48 hours) | HIGH |
| 5 | Classifier admin override | **5C** (separate env var `RODIX_DEV_SKIP_SAFETY=1`, default unset = active) | HIGH |
| 6 | Mandarin keyword scope | **6B** (English + Mandarin, skip romanization) | MEDIUM-HIGH |
| 7 | Classifier failure mode | **7C** (fail-with-flag: retry once → conservative-on-keyword default) | MEDIUM-HIGH |

---

## STOP 1 — awaiting Rodc reply on all 7

Per Section 10.5 of brief, CC will not proceed to PHASE 2 implementation until all 7 Type-A items have Rodc go/no-go.

Rodc reply format suggestions:

```
Type-A 1: ✓ accept 1C
Type-A 2: ✏️ override → 2C aggressive (we'll calibrate)
Type-A 3: 📝 rewrite → "Topic above. Rest stayed inside."
Type-A 4: ✓ accept 4B
Type-A 5: ✓ accept 5C
Type-A 6: ✓ accept 6B
Type-A 7: ✓ accept 7C
```

Or any combination of accept / override / rewrite. CC integrates Rodc replies into spec FINAL marker before implementation.
