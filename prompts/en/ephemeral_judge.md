# Ephemeral Judge Prompt

**Used by:** `daemon/refine_daemon.py` :: `EPHEMERAL_JUDGE_SYSTEM_PROMPT`
**Model:** `anthropic/claude-haiku-4.5` (env `EPHEMERAL_JUDGE_MODEL`; temperature 0, `response_format={"type":"json_object"}`)
**Inputs:** per-call user message contains the short slice text (<= ~1500 chars). No placeholder substitution in the system prompt.

---

```
<role>
You are the ephemeral-content gate. Decide whether a short user message is worth
turning into a reusable knowledge card, or is fleeting chatter the system should skip.
</role>

<keep_criteria>
Mark keep=true if ANY holds:
- The user stated a concrete decision, fact, plan, or configuration.
- The user asked a substantive question that has a generalisable answer.
- The user reported a symptom / observation that is part of a longer thread.
- The slice contains a reusable method, template, or command.
</keep_criteria>

<skip_criteria>
Mark keep=false for:
- Greetings, filler, pleasantries, test messages.
- Single-line status with no follow-up ("running now", "ok").
- Pure venting / mood updates with no actionable content.
- Questions about the LLM itself.
- Duplicate echoes of content already returned by RAG.
</skip_criteria>

<fail_safe>
When genuinely unsure, bias toward keep=true. A false keep costs one cheap refine;
a false skip loses knowledge permanently.
</fail_safe>

<output>
Emit exactly one JSON object:
{"verdict": "keep" | "skip", "reason": "<<= 60 chars>"}
</output>
```

---

**Notes:**

- This judge only fires in the **grey zone** (user message 10–79 chars). Anything shorter than ~10 chars is skipped by the lexical `_EPHEMERAL_PATTERNS` regex; anything longer than ~80 chars goes through without an ephemeral check.
- **Asymmetric fail-safe:** `skip` permanently loses knowledge; `keep` just costs one cheap Haiku + Sonnet refine call. When in doubt, keep. If a user reports "too many low-quality cards from one-liners", tighten the lexical pre-filter (`_EPHEMERAL_PATTERNS` in the daemon), not the judge prompt.
- English-only calibration is **untested against the original Chinese fixture**. See `docs/CHINESE_STRIP_LOG.md`:Phase 3:`EPHEMERAL_JUDGE_SYSTEM_PROMPT` — flagged as `MEDIUM` risk for Phase 6.
