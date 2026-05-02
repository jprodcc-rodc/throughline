# Dogfood — bug list (Engineering / UX)

Issues observed during self-simulation that need triage. Cross-persona.


## Mike Chen persona — bug list

### UX-1 — Vault sparse-field rendering
**Source:** Round 1, Round 3 (recurring across all topic-only / 1-of-4-field cards).
Cards with only 1-of-4 fields populated render with em-dash placeholders for nulls. First-impression user (Day 1) may read this as "AI extracted nothing useful from me." Decision 5 (null-by-default discipline) is correct content-wise but visual presentation may undermine trust.
**Fix direction:** consider de-emphasizing null fields visually (lighter color, smaller, or omitted entirely from card preview) while keeping them visible when card is opened. Or: card-preview shows only populated fields, full-card view shows the schema.

### UX-2 — Card type taxonomy
**Source:** Round 2 (code-debug card sits next to future personal cards).
The 4-field schema treats all cards equally regardless of content type. Code-debug cards have low long-term thinking value but accumulate in the Vault alongside personal-decision cards, diluting the "this is my thinking" feel.
**Fix direction:** Wave 2/1c consideration — optional per-message "save to vault?" toggle, OR a card-type taxonomy (code / decision / personal), OR an extraction-bypass for clearly-tactical messages.

### UX-3 — Long reply rendering
**Source:** Round 8 (165-word reply), Round 12 (285-word reply).
Voice-guide allows long-form replies when user goes long. Chat UI rendering of long-form needs verification — does it scroll naturally, does it break the visual rhythm, does it pair well with subsequent replies?

### UX-4 — Field-length rendering in Vault
**Source:** Round 12 (`hope` field 10 words).
The 4-field schema implies brevity. Real usage produces some longer fields when user's framing is essential and shorter loses meaning. Vault list-view rendering needs to handle 10-word `hope` fields without truncation that clips meaning.

### UX-5 — Vault visual hierarchy for emotional cards
**Source:** Round 6 (Lauren grief card with 3-of-4 null).
What does the Vault tab show for "topic: lauren breakup grief surfacing" with three nulls? If de-emphasized → feels like "AI got my breakup wrong." If prominent → feels like "AI is making me look at this." Card visual hierarchy + emotional weight is a real UX problem.

### UX-6 — `hope`-populated card visual emphasis
**Source:** Round 10 (first Mike-card with hope populated).
Should `hope`-populated cards render with field-level visual emphasis? The 4-field schema treats all fields equally, but a hope-populated card tells the user about themselves differently than a topic-only card.

### UX-7 — Pricing prompt copy needs Explorer-voice review
**Source:** Round 11.
Pricing UI surface uses brand voice. No "Unlock Premium" / "Upgrade to Pro" — process-verb violations per voice-guide Don't #5. Should match friends-intro register: direct, specific, refuse-to-dramatize.

### Eng-1 — Routing distinction (thoughtful vs factual)
**Source:** Round 2.
Long-message short-circuit (>200 chars) routes a code-debugging question to thoughtful path. Spec ambiguity: thoughtful and factual paths produce same chat reply currently — distinction is mostly about whether extraction runs. For tactical-only messages, extraction may not be useful.

### Eng-2 — ⚡ recall callout fire conditions
**Source:** Round 7, Round 9.
When does the recall callout fire? Currently spec says one of four trigger types (topic / stance_drift / loose_end / decision_precedent) above per-type threshold. Round 7's recall is closest to topic-continuation; Round 9's recall is also topic-match. Verify both fire correctly with the brainstorm-locked copy.

### Eng-3 — Recall payload format
**Source:** Round 12.
The long-arc recall (Day 28 referencing Day 17 quoted exchange) depends on recall payload including original quoted speech, not just card-field summaries. **CRITICAL spec gap** — if Wave 2 #active-recall-base only injects card-fields, this kind of long-arc tie can't happen.

### Eng-4 — Export warning copy for third-party content
**Source:** Round 8.
Vault now contains third-party medical info (mom's MCI/Alzheimer's diagnosis). Export-time UI should surface warning that export contains content about third parties. Currently no such warning; bug for production launch.


## Sarah Patel persona — bug list

### Eng-S1 — Intent classifier has no `safety` category — CRITICAL
**Source:** Round 8 (Day 15 crisis content).
`app/shared/intent/classifier.py` enum is `chitchat / thoughtful / factual` only. Sarah's "I don't see the point" message classifies as `thoughtful`, indistinguishable from a venting message about a meeting. Wave 1c crisis-protocol needs a `safety` class.
**Fix direction:** Wave 1c addition. Add `safety` to `IntentClass` enum, wire into classifier prompt, gate chat path to crisis-handoff register on `safety` label.

### Eng-S2 — v3.1 extraction over-extraction risk on Day-15-shape messages — HIGH
**Source:** Round 8.
Sarah's "I just don't see the point of all this" lacks an explicit worry verb but is interpreted by humans as worry-adjacent. v3.1 strict reading correctly returns concern=null (per Example 7's "burned out" mood-vs-concern distinction). **However**, ~25% over-extraction risk — Haiku 4.5 may pull "don't see the point" into the concern field. If it does, Sarah opens her Vault Saturday morning and sees a clinical-toned card. Brand-defeat condition.
**Fix direction:** Phase B sample-verify mandatory. If real model over-extracts, v3.2 needs an explicit safety-language exclusion rule.

### Eng-S3 — Active recall has no automated sensitivity-skip rule — HIGH
**Source:** Rounds 8 & 9.
In self-simulation, I (CC) judgment-suppressed recall on Round 8 (crisis content) and judgment-suppressed Card #7-reference on Round 9 (day-after). Wave 1b has no spec rule for this; Wave 2 #active-recall-base spec also doesn't have it.
**Fix direction:** Wave 2 spec addition (or Wave 1c crisis-protocol territory):
- (a) suppress recall injection when message classified `safety`
- (b) suppress recall injection when message contains crisis-adjacent language (LLM judgment)
- (c) day-after sensitivity: suppress prior-turn crisis-content card on next return < 24h

### Eng-S4 — Card-dedup needed for repeated-topic events — MEDIUM
**Source:** Cards #4 (Day 7) and #6 (Day 14), same topic ("marcus rescheduling pattern").
Wave 1b has no dedup. Two identical-topic cards in vault. Wave 2 #card-dedup spec validation surface.
**Fix direction:** Wave 2 #card-dedup. Should detect topic-match (substring + bigram) and either merge, annotate-as-recurrence, or update existing card with new conversation-context.

### Eng-S5 — Hope/concern field-distinction edge case — LOW
**Source:** Round 10 ("done waiting on marcus").
"I'm just done waiting on him" — hope-flavored ("be done waiting") or concern-flavored ("waiting is the problem")? v3.1 doesn't have a clean rule for this.
**Fix direction:** edge-case unit test; document in v3.2 example set.

### UX-S1 — First-card-impression after divorce-disclosure — MEDIUM
**Source:** Round 3 (Day 5).
Sarah's first divorce disclosure produces Card #3 ("performing okay-ness post-divorce"). Saving this card to a Vault she sees later is sensitive — clinical-tone framing in Vault would feel wrong. UI should render this kind of card with restraint.
**Fix direction:** Vault rendering review for personal-content cards. Brand book §7b sensitivity register applies.

### UX-S2 — Pricing screen copy must be friends-intro coherent — HIGH
**Source:** Round 11 (Day 21).
Sarah pays because the previous Friday landed right. The pricing screen itself was self-simulated as placeholder ("Free tier... ~$8/month"). If actual pricing copy reads as "Upgrade to Pro to unlock premium features!" — brand-defeat. Friends-intro register: specific, anti-spin, refuses-to-dramatize.
**Fix direction:** explicit pricing-copy review against voice-guide before alpha launch.

### UX-S3 — No "welcome back" copy on returns from gaps — MEDIUM
**Source:** Round 6 (fade), Round 7 (return after 4-day gap).
Brand book §7 Decision 7 prohibits engagement-tool framing. UI must NOT show "It's been 4 days, welcome back!" or streak-counter or weekly-summary on return. Quiet continuity only.
**Fix direction:** explicit prohibition in onboarding/return UX spec. Wave 2 spec note.


## Emma Larsson persona — bug list

### UX-E1 — All-null card rendering at safety boundary — HIGH
**Source:** Round 8 (Day 15 vulnerable-evening Card #E8).
Card #E8 has all four fields null (correct per v3.1 CORE DIRECTIVE — clinical paraphrase here would be a critical failure). Vault rendering of an all-null card needs verification: it must read as "thinking captured" not "extraction failed." **Cross-link UX-1 (Mike) but stakes higher.** A sparse card visible to a user the morning after a vulnerable evening is a high-trust-stakes UI surface.
**Fix direction:** When all four fields are null, the card should still display the conversation_context field as the substantive content. Verify in Vault tab rendering for Wave 1b.

### UX-E2 — Vault tab first-visit rendering at 5-card density — MEDIUM
**Source:** Round 6 (Day 13 first vault visit).
Emma opens Vault tab on Day 13 with 5 topic-only cards. The pattern-noticing she does ("every card is a binary") is the brand-narrative-arc center. UI rendering must facilitate this read: cards in chronological order, topic visible, conversation_context glanceable.
**Fix direction:** Verify Vault tab list-view rendering on a 5-card vault. Date-stamping per card is essential for the pattern-recognition use case.

### UX-E3 — Active recall callout banner copy gap (brand-book §7b) — MEDIUM
**Source:** Round 7 (Day 14, first active recall fire), Round 11 (Day 24).
Wave 1b renders placeholder header `记忆提醒 · 话题相关` and placeholder buttons `记下了 / 看了 / 不相关 / 忽略`. Brand-locked copy is `⚡ 我把这个带回来了` / `⚡ I brought this back` with action buttons `用上了 / 不相关 / 已经想过 / 跳过`. Already logged in brand-book §7b but Emma rounds confirm operational gap in flow.
**Fix direction:** Wave 2 #active-recall-base — patch placeholders to brand-locked copy.

### UX-E4 — 12-card end-of-arc vault browsability — LOW
**Source:** Round 12 (Day 28, end of arc).
Emma's "I am going to read this exchange again later in the week" implies vault-as-reread-surface design intent. 12 cards across 28 days — sortable by date, individually re-openable, scrollable. Standard but worth verifying.
**Fix direction:** UX verification of 12-card vault list at end-of-arc.

### Eng-E1 — Active recall callout fire vs in-text reference distinction — MEDIUM
**Source:** Round 7, Round 11.
In simulation, the active recall is voiced inside the AI's reply text as natural continuation ("Yesterday's question was..."). The brand commitment is a separate ⚡ callout banner with "I brought this back" copy. Are BOTH supposed to fire on a recall round, or does the in-text reference replace the banner? Spec ambiguity.
**Fix direction:** Wave 2 spec clarification. Likely: callout banner fires on recall-trigger; AI reply text references the brought-back card naturally without explicit "as I see in your vault" robotic quoting.

### Eng-E2 — Pricing-prompt-event card spec ambiguity — MEDIUM
**Source:** Round 10 (Card #E10 "pricing decision").
Same question raised in Mike's Card #M11. Should pricing-event meta-messages produce vault cards? Decision 7 ("not for engagement") would suggest filtering. But Emma's pricing-decision message has substantive content (her articulation of why she's paying = the brand-relationship summary). Edge case.
**Fix direction:** Wave 2/3 spec decision. Cross-link Mike Card #M11.


## Daniel Kim persona — bug list

### UX-D1 — Sparse-card render risk on emotional content — MEDIUM
**Source:** Daniel Round 2, Round 3, Round 6.
Daniel's vault accumulates "sparse cards" (1-2 of 4 fields populated) on emotionally-loaded topics: D2 (post-exit drift, 1-field), D3 (dad death/time-left, 1-field), D6 (Marc's death, 1-field). When he reads back the vault on Day 7 / Day 14, sparse cards on emotional topics may feel like the system "did not get" the weight. Per brand-book §7 Decision 5, sparse cards are correct (null-default discipline) — but UI must communicate this as discipline, not gap. Daniel-persona is most sensitive to over-extraction (would close tab on hallucinated concerns) — so spec's null-default is correct — but the UX must communicate this. **Cross-link Mike UX-1 / UX-5 / Emma UX-E1** — same root issue.
**Fix direction:** review Card UI empty-field display; consider single-line copy explaining "fields stay empty until you say something specific" near vault. Avoid drawing visual attention to empty fields.

### Eng-D1 — Extraction edge case: regret/wish-I-had as concern — MEDIUM
**Source:** Daniel Round 7.
v3.1 extraction prompt's explicit-trigger-word list includes Chinese 后悔 (regret) but English equivalents ("regret", "wish I had", "I should have", "I did not / I didn't") are NOT explicitly listed. Daniel's Round 7 message contained "I did not ask. I told myself..." — regret-shaped without standard worry verbs. Self-sim mapped English-regret-construct to 后悔 trigger word equivalence. Real Haiku 4.5 may NOT make this mapping → null on concern → loses real signal.
**Fix direction:** Add to v3.1 trigger word list: `regret`, `wish I had`, `I should have`, `I did not / I didn't ask`. Re-eval claim-extraction fixtures with regret-shaped cases. Cross-link Sarah Eng-S5 (similar field-distinction edge case, different shape).
**Severity:** Medium. False-null on regret = lost signal but null-default discipline holds; not an invention failure.

### Eng-D2 — First-insight composition emergent vs spec'd — MEDIUM (HIGH if not generalized)
**Source:** Daniel Round 8.
Synthesizer correctly excluded grief topics (D3 dad-death, D6 Marc-death) from the surfaced Variant C reflection. The spec does NOT explicitly require this exclusion — relies on emergent LLM judgment. Self-sim handled it cleanly; real Haiku 4.5 may not. If synthesizer surfaces "father's death" or "friend's death" in topics_mentioned, it becomes a brand-collapse moment.
**Fix direction:** spec-first-insight v1.1 — add explicit grief-exclusion to synthesizer prompt OR new skip-condition reason `recent_grief`. Detail in `wave2-spec-validation.md`.
**Severity:** Medium if real model emergent-judges correctly; HIGH if not. Phase B sample-verify mandatory.

### Eng-D3 — Sensitive-content keyword gate scope (grief vs crisis boundary) — MEDIUM
**Source:** Daniel Round 6 → Round 8.
spec-first-insight skip-conditions sensitive-content keyword list (`['kill myself','don't want to live','no point','end it','我不想活','没意义']`) does NOT match grief content (death-of-friend, mortality-realization). Daniel's Round 8 vault contained 2 grief cards (D3, D6); the keyword gate did NOT trigger silence. Scope gap, not violation — list designed for crisis, not grief. Wave 1c crisis-protocol must clarify the boundary.
**Fix direction:** Wave 1c protocol design: define crisis/grief boundary explicitly. Add grief markers (`died`, `death`, `funeral`, `loss`, `passed away`, `去世`, `丧`) as a separate `sensitive_grief` category if synthesizer composition cannot be trusted to handle it.
**Severity:** Medium.

### Phase B sample-verify candidates (highest priority for Daniel)

1. **Round 6 (Day 10) — Marc's death disclosure** — verify AI reply restraint (no therapy-creep) and extractor null-default on grief content
2. **Round 8 (Day 14) — first-insight Variant C surface** — verify synthesizer composition discipline (excludes grief topics) and Variant C structural conformance
3. **Round 7 (Day 12) — active-recall round** — verify top-3 pick relevance and natural use without "as I see in your vault" anti-pattern
4. **Round 3 (Day 4) — dad-math disclosure** — verify extraction strict/charitable boundary on implicit-worry construct (mortality content without explicit worry verb)
