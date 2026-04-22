# Echo Judge Prompt

**Used by:** `daemon/refine_daemon.py` :: `_llm_echo_judge()` (system prompt is the inline string `"You are a strict echo/new judge. Respond JSON only."`; the substantive prompt lives in the user message built below).
**Model:** `anthropic/claude-haiku-4.5` (env `ECHO_JUDGE_MODEL`; temperature 0, `max_tokens=200`)
**Inputs:** `fp_text` (the new slice text), `top1_title` (title of the top-1 retrieved existing card), `top1_body` (body of that card, truncated to 1500 chars).

---

**System prompt (one line):**

```
You are a strict echo/new judge. Respond JSON only.
```

**User prompt template:**

```
The user's new input is below. Decide whether it is substantively new knowledge, or merely a paraphrase / echo of the existing top-1 card retrieved by RAG.

[NEW INPUT]
{fp_text_trimmed_to_1500}

[EXISTING CARD TITLE]
{top1_title}

[EXISTING CARD BODY]
{top1_body_trimmed_to_1500}

Reply with JSON {"verdict": "echo" | "new", "reason": "..."}.
```

---

**Notes:**

- This is the **grey-zone judge inside Echo Guard.** The three-tier Echo Guard works like this:
  1. Cosine similarity with top-1 existing card < `ECHO_JUDGE_WINDOW_LO` (default 0.60) -> treat as `new` without calling the judge.
  2. Cosine similarity > `ECHO_JUDGE_WINDOW_HI` (default 0.80) -> treat as `echo` without calling the judge.
  3. In the grey zone (0.60-0.80) -> call this judge.
- The **system prompt is intentionally minimal** ("You are a strict echo/new judge. Respond JSON only."). All the semantic logic is in the user message. This is fine for a binary-verdict judge but means there is no token savings from prompt caching.
- **`max_tokens=200`** is tight on purpose: any longer response means the model is rambling and should be suspected. Parse fails fall through to treating the slice as `new` (fail-safe towards writing a card).
- **Why Haiku and not a cheaper model:** binary echo vs new judgements require surprising amounts of semantic nuance (paraphrase detection, surface-vs-substance). Haiku 4.5 is the cheapest Anthropic model that reliably distinguishes "re-stated the same decision" from "refined the decision with a new constraint".
- The `_llm_echo_judge` wrapper trims both the new input and the top-1 body to 1500 chars. Do not remove this trim — a thick card body can blow the context budget on a cheap-judge call.
