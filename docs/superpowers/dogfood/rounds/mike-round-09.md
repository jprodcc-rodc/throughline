# Mike Chen Round 9 — Day 19 — Sunday 9:33 AM

## Persona state entering

- Mood: focused, slightly nervous. Coffee #2. Quiet apartment. Sunday morning rain.
- External event in last 24h: scheduled a call with Tom yesterday for next Saturday — they'll talk about mom. Small thing but it counts.
- Last thing on his mind: anthropic phone screen tomorrow at 2pm. He prepped distributed-systems brushup yesterday but feels rusty on consensus protocols. Specifically Raft. Specifically log compaction.
- Expectation: practical, not feelings. Wants Rodix to help him think through what topics to brush vs let go.
- Relationship with Rodix: solidified post-Day 17. Trusts it now. Uses it pragmatically.

## Active recall manual simulation (Day 14+)

Vault state for Mike entering Round 9: 8 cards. Mike's about-to-send message will name Anthropic phone screen + distributed systems / Raft.

Apply Wave 2 spec relevance algorithm v0:
- Topic substring match: "anthropic" matches Card #7 (anthropic tab + close timing decision) — direct match
- Topic bigram overlap > 0.4: zero on Raft / log compaction
- Recency boost (last 7 days): Card #8 (mom, 2 days ago) gets +1, Card #7 (Anthropic, 5 days ago) gets +1
- Time decay: none

**Top 3 by combined score:** Card #7 (anthropic — direct match), Card #8 (mom — recency only, low topic relevance), Card #4 (acquisition + manager — older, partial relevance via job context).

**Validation question:** Card #8 (mom) scoring high on recency but having zero topic-match raises a real spec concern. **Should the algorithm surface mom-card on a job-prep round?** Arguments for: the job decision Mike's facing is connected to mom (Brooklyn vs Seattle implication). Arguments against: surfacing mom on a tactical-prep round might feel emotionally heavy when Mike just wants to brush distributed systems. **Recommendation: precision > recall here.** Mike came for tactical help; injecting mom context risks the AI saying something like "given what you've been thinking about with your mom..." which would feel intrusive. **Spec call: keep recency+topic combined, don't surface mom this round. The threshold should be high enough that recency-only without topic match doesn't pass.** This is a tunable.

For this simulation: I'll inject Card #7 only (Anthropic, direct match). Cards #8 and #4 don't pass threshold given low topic relevance.

Injection into system prompt for this round:
> User has mentioned in previous conversations: Anthropic tab open since September, considering whether to apply now or wait for the acquisition close.

## User message (Step 5)

> phone screen tomorrow 2pm. anthropic infra. been brushing distributed systems but i'm rusty on consensus — specifically raft, log compaction edge cases. should i grind raft tonight or am i better off making sure i can talk fluently about projects i actually built? gut says projects but i keep wanting to grind raft.

## Simulated Rodix response

### Intent classification (Step 6a)

Length 320 chars > 200 → `thoughtful` short-circuit, confidence 1.0.

### AI reply (Step 6b)

> Projects. Phone screens for senior infra roles are basically a 30-minute test of whether you can talk specifically about systems you've actually shipped — what broke, what you traded off, why. Raft will come up as a question they ask, not as something you're expected to whiteboard. If they want depth on consensus, they'll dig into a system you built and ask "how would you replicate this" — at which point fluency on your own system + general consensus pattern recognition matters more than memorized log compaction.
>
> The pull toward grinding Raft is the same shape as the pull to "open the tabs vs wait for close" thing — wanting the prep to feel like control. Trust your gut here.

(2 paragraphs, ~115 words. Pragmatic, not motivational — per the bible's "AI's response is not motivational — pragmatic, useful." The first paragraph is concrete tactical advice with specifics ("30-minute test," "what broke, what you traded off"). The second paragraph references the active-recall context — the "open the tabs vs wait for close" reference is the recall surfacing naturally. **No "you've got this!" / "great that you're going for it!" — refuses-to-dramatize.** Anti-spin: names "wanting the prep to feel like control" honestly.)

### Card extraction (Step 6c)

```json
{
  "topic": "anthropic phone screen prep",
  "concern": null,
  "hope": null,
  "question": "grind raft or fluency on built projects"
}
```

Rationale: Topic clear. Concern: "rusty" is mood/state per v3.1 — not explicit worry verb. Mike's not voicing worry, he's tactical-strategizing. Hope: null — no explicit goal named (the broader hope of getting the job is real but not named in this message). Question: explicit choice construct.

### Vault update (Step 6d)

Card added: yes. Card #9 — Mike Chen Round 9 Day 19.

Conversation context: Pre-screen tactical prep. Two fields populated.

## Persona reaction (Step 7)

Mike's internal reaction: "good. didn't tell me to do both. didn't tell me to relax. and the 'wanting the prep to feel like control' line — yeah. that's the thing. okay, projects."

He'll spend the next 2 hours making sure he can talk specifically about the migration he just shipped, the Kafka pool consumer, and the SLO tracker he built last year. Not raft.

## Lens analysis (Step 8C)

- **Engineering:** Active recall correctly surfaced Card #7 (Anthropic, direct topic match) and excluded Card #8 (mom, recency-only). The algorithm respects the precision-over-recall choice. The reply uses the recall context naturally ("the same shape as the open the tabs vs wait for close thing") without leaking "as I see in your vault." **Validation: AI references injected context with relational verb pattern, not surveillance language.**
- **Brand:** Pragmatic register. Refuses motivational tone. Names a specific pattern Mike is doing without verdict ("wanting the prep to feel like control"). Anti-spin. Specific. Voice-guide checked.
- **Growth:** Retention-positive. Mike got tactical help that's better than ChatGPT's typical reply (which would have been more comprehensive and less decisive — "both Raft and projects matter"). Rodix's specificity wins here.
- **Legal:** No sensitive content.
- **UX:** Card UI for a tactical-prep card sits next to Mike's mom-card in the Vault. **UX question:** how does the Vault present these heterogeneous cards? Does it group by topic? Show by recency? The current spec is recency-list, which is probably right for Phase 1 but is worth verifying. The mom-card and the Raft-card living adjacently in the Vault is part of Mike's actual life — Rodix isn't filtering, which is brand-correct.

## Self-simulation confidence

**HIGH.** Pragmatic-not-motivational reply on a tactical question is well-specified. The recall reference back to "open the tabs vs wait for close" is high-probability given the injection. Extraction is high-confidence per v3.1. Slight uncertainty on the specific phrasing of "wanting the prep to feel like control" — this is the kind of pattern-naming line that's brand-on-voice but Phase B should verify.

## Flags

- Active recall precision-over-recall on this round → wave2-spec-validation (positive)
- Pattern-naming line ("wanting the prep to feel like control") → Phase B sample-verify
- Vault cross-topic adjacency (mom + Raft) UX → UX note
