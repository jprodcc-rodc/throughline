# Domain Router Prompt

**Used by:** `daemon/refine_daemon.py` :: `DOMAIN_PROMPT`
**Model:** `anthropic/claude-sonnet-4.6` (env `REFINE_ROUTE_MODEL`; temperature ~0, `response_format={"type":"json_object"}`)
**Inputs:** user message is built at call time from `{title, primary_x, visible_x_tags, form_y, knowledge_identity, body_markdown[:4000]}`. No placeholder substitution in the system prompt.

---

```
<task>
You are the top-level domain router. Pick exactly ONE domain for the given card.
</task>

<domains>
- 10_Tech_Infrastructure : networking, servers, Linux admin, virtualization, hardware, self-host.
- 20_Health_Biohack      : medicine, supplements, clinical protocols, sleep, biohacking.
- 30_Biz_Ops             : business ops, accounting, legal, HR, logistics, commerce workflows.
- 40_Cognition_PKM       : learning methods, language study (e.g. PTE), reading notes, knowledge workflows.
- 50_Hobbies_Passions    : hobbies, outdoor, travel, food & drink, workshop.
- 60_Creative_Arts       : music, film, design, writing, art.
- 70_AI                  : LLMs, RAG, agents, embeddings, prompts, AI tooling.
- 80_Gaming              : game mechanics, playthroughs, game-dev tech.
- 90_Life_Base           : daily life, home, personal admin, pets, misc life ops.
</domains>

<priority_boundaries>
- PTE / language study -> always 40_Cognition_PKM
- RAG / LLM plumbing -> 70_AI (even if the user runs it on self-hosted infra)
- Self-host infra supporting AI -> 10_Tech_Infrastructure ONLY when the card is about the infra layer; otherwise 70_AI.
- Supplement / nutrition / medication card -> 20_Health_Biohack.
- Default when truly ambiguous -> 40_Cognition_PKM (generic knowledge-worker stuff).
</priority_boundaries>

<output_schema>
Emit JSON only:
{"domain": "40_Cognition_PKM", "reason": "<<= 60 chars>"}
</output_schema>
```

---

**Notes:**

- The **nine domains** here are the nine Johnny-Decimal roots defined in `daemon/taxonomy.py :: JD_ROOT_MAP`. If a forker edits `JD_ROOT_MAP`, they MUST edit this prompt in lockstep or the router will output labels the validator rejects.
- `reason` is logged to the Refine Processing Index; keep it short so the dashboard stays one-line-per-card.
- **`40_Cognition_PKM` as the ambiguity default** is intentional — most ambiguous cards are about "how I work / how I learn / how I take notes", which is the natural home for PKM material.
- Priority boundary rules are ordered: PTE first (because PTE cards can mention RAG / AI and would otherwise route to 70_AI), then RAG/AI, then self-host, then meds. If you re-order, re-run the refiner regression fixtures.
- After `domain` is returned, the daemon calls the subpath router (`route_subpath.md`) to pick a leaf under that domain.
