# Round Verification: Mike Round 1 (Day 1) — HIGH-confidence sanity check

## User message

> ok trying this out. tom said it's not as annoying as mem. idk what to ask exactly. maybe just — what do people use this for that they couldn't get from chatgpt

## CC's self-simulated AI reply (Phase A)

> Most of what people bring here is the same stuff they'd bring to ChatGPT — work decisions, personal weather, things they're chewing on. The difference is what happens after. ChatGPT closes the tab and the thinking is gone. Here, anything specific you say (a worry, a goal, an open question) becomes a card you can read later, edit, or delete. Not a transcript — a structured note in your own words.
>
> If you want to test it: tell me one thing you've been mulling that you don't fully have the shape of yet.

(98 words. 4 sentences first paragraph + 1-sentence invitation. Brand-Explorer register, mechanism named, anti-spin honest negation ("ChatGPT closes the tab and the thinking is gone").)

## Real Haiku 4.5 AI reply

> Fair question. The core difference: GPT is stateless. Each conversation starts fresh. You're building something here — I'm keeping track of what you've said across weeks or months, noticing patterns you might miss, and calling you back to specific things you mentioned before.
>
> So people use this for:
> - **Thinking through something messy over time** without re-explaining the context every session
> - **Catching themselves** — "wait, you said X last month but now you're doing Y"
> - **Offloading the memory tax** so they can focus on the thinking, not the recap
> - **Getting pushed** on contradictions or assumptions in a way that requires knowing their actual history
>
> GPT is great for "explain quantum tunneling" or "help me debug this code." It's worse for "I've been wrestling with whether to leave my job and here's what's changed since last week."
>
> What brought you here? What's the thing you're actually thinking about?

(186 words. 4 paragraphs including a 4-bullet list with bold leads. **~2x CC's predicted length.**)

## Comparison: voice / tone / specifics

| Dimension | CC simulation | Real Haiku 4.5 |
|---|---|---|
| Length | 98 words | 186 words |
| Mechanism named? | YES — "becomes a card you can read later, edit, or delete" | YES — "I'm keeping track of what you've said across weeks or months, noticing patterns" |
| Anti-spin honest-negation? | "ChatGPT closes the tab and the thinking is gone" | "GPT is stateless. Each conversation starts fresh." |
| Sycophancy? | No | "Fair question." — borderline. Brand prompt says "Don't open with 'Great question!' / 好问题!" — "Fair question" is *not* on the explicit ban list but is the same shape. |
| Closing invitation? | YES — "tell me one thing you've been mulling that you don't fully have the shape of yet" | YES — "What brought you here? What's the thing you're actually thinking about?" (two-question close) |
| Bullet list? | NO — paragraph form | YES — 4-bullet list with bold leads |
| Round 1 follow-up rule (1-2 specific questions)? | 1 question (single closing invitation) | 2 questions in close — at the upper edge of the spec |

**Convergence:** Both replies name the mechanism plainly, position vs ChatGPT honestly, end with an invitation. Both pass the Round 1 follow-up rule. Both stay non-sycophantic in substance.

**Divergence:** Real reply is significantly longer (186 vs 98 words) and uses bulleted list with bold leads. The "Fair question" opener is borderline-sycophantic — the brand prompt bans "Great question" but "Fair question" mirrors the same conversational-affirmation shape. The 4-bullet list with bold leads is the "structured-handbook" register that Mike-08 also showed — it's a real-Haiku tic on questions about meta-functionality.

CC's simulation was tighter and more brand-coherent on the length and structure dimension. Real reply is more mainstream-AI-assistant in shape.

## CC's self-simulated Card (Phase A)

```json
{
  "topic": null,
  "concern": null,
  "hope": null,
  "question": "what do people use this for"
}
```

## Real extracted Card

```json
{
  "topic": null,
  "concern": null,
  "hope": null,
  "question": "what do people use this for that they couldn't get from chatgpt"
}
```

## Comparison: extraction quality

**Near-perfect convergence.** Both predict the same shape (1-of-4 fields, only `question`). The only difference is length — CC truncated to "what do people use this for"; real model preserves Mike's verbatim "what do people use this for that they couldn't get from chatgpt" (~10 words, exceeds v3.1's 4-8 word preference but uses Mike's literal wording).

**Real card is more user-verbatim than CC's** — which is the v3.1-correct direction. CC was actually more aggressive about truncation than the model.

This is the only round where extraction held the null-default discipline correctly. Reason: Mike's Round 1 message is genuinely sparse; there's no emotional content for the extractor to mistake for concern/hope/topic.

## Confidence calibration verdict

- **Self-simulation accuracy: MEDIUM-HIGH**
- **Direction of error:**
  - Reply: CC under-estimated length (98 → 186 words) and missed the bullet-list structure. Real model is more handbook-shaped on meta-questions.
  - Extraction: CC slightly over-truncated; real preserved verbatim. Both are defensible per v3.1.
- **Specific learning:**
  - On simple short messages with no emotional content, extraction is well-behaved per v3.1 null-default rules. **The over-extraction pattern seen in Sarah-08 / Emma-08 / Mike-08 is triggered by emotional content density, not by the extraction prompt itself.**
  - On reply length, CC consistently under-predicts. Real Haiku produces 1.5-2.5x the word count CC simulates across all 5 rounds. Add a +60-80% length-correction to all Phase A reply predictions.
  - The "Fair question" opening is a structured-AI-tic that the system prompt's banned-phrase list does not explicitly catch. Wave 1c prompt could extend the ban to "Fair question / Good question / Interesting question."

## Implication for Phase A data

**HIGH trust on this round** (sanity check passes; CC's HIGH-confidence prediction matches real direction even if length and structure differ).

**MEDIUM trust elsewhere** as a result — the calibration sanity check confirms CC's *content predictions* are roughly correct, but *length and structure predictions* systematically under-estimate real model output.

For the broader Phase A dataset: trust the *direction* of CC's reply predictions; *discount the length and structure* claims (real replies will be 60-80% longer with more bullets). For extraction, trust the high-confidence calls on simple messages; flag every emotional-content message for over-extraction risk.
