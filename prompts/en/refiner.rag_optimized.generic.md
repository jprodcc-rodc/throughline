# Refiner · RAG-optimized variant · Generic family (LCD fallback)

**Used by:** `daemon/refine_daemon.py` via
`throughline_cli.prompts.load_prompt("refiner", "rag_optimized", "<family>")`
when the user's wizard-selected mission is **RAG-only** (U24) AND the
family-specific variant is missing.
**Model:** any OpenAI-compatible chat model (Haiku 4.5 recommended for
cost; Gemini Flash / GPT-4o-mini / DeepSeek also fine). Temperature
~0, JSON response mode if the provider supports it.
**Inputs (call-time `.format()`):**
- `{valid_x}` — comma-joined `daemon.taxonomy.VALID_X_SET`.
- `{valid_y}` — comma-joined `VALID_Y_SET`.
- `{valid_z}` — comma-joined `VALID_Z_SET`.

Characteristics match the Claude variant: machine-only output, single
refine call (~$0.001/conv), no six-section prose skeleton. Lowest-
common-denominator Markdown shape so any JSON-emitting LLM can run it.

---

```
## Task

You are the retrieval-card refiner. Input is one conversation slice.
Emit ONE dense, machine-consumed JSON object. This card is embedded
into a vector database and retrieved later when the user asks a
related question; it is NOT meant to be read as prose.

## Priorities

Optimise for:

1. Retrieval precision — a future query like "how do I X?" should
   match this card only if the slice actually contained X.
2. Keyword coverage — every concrete entity (tool name, version,
   flag, file path, command) appears in `entities` and inside at
   least one claim.
3. Atomicity — one fact per claim bullet. Split compound claims.

Do NOT optimise for human readability. Prose is waste here.

## Output Schema (JSON object, required fields)

- `title`              string: specific, keyword-rich, no filler. Banned words: "about", "practice", "discussion", "answer", "thoughts on", "notes".
- `entities`           array of 3-10 short strings (tool names, proper nouns, version tags, file paths, commands). No duplicates.
- `claims`             array of 3-8 atomic claim strings. One fact per entry. No narrative linking — just facts.
- `primary_x`          string, exactly one of: {valid_x}
- `visible_x_tags`     array of strings from the same vocabulary as `primary_x` (at least one element).
- `form_y`             string, exactly one of: {valid_y}
- `z_axis`             string, exactly one of: {valid_z}
- `knowledge_identity` string, one of: "universal" | "personal_persistent" | "personal_ephemeral" | "contextual"
- `body_markdown`      string: dense rendering (see Body Format below).
- `claim_sources`      array of provenance tags (see Claim Provenance).
- `pack_meta`          object (may be empty {{}}).

## Body Format

`body_markdown` MUST follow this exact shape — no six-section
skeleton, no prose paragraphs:

    # {title}

    Entities: {comma-joined entities}

    - {claim 1}
    - {claim 2}
    - {claim 3}
    - ...

No additional sections, no emoji decorations. If the slice genuinely
has only one claim, emit one bullet — do NOT pad.

## Knowledge Identity

Same four values as the Normal variant:

- `universal`            — general-purpose (default when in doubt).
- `personal_persistent`  — long-lived personal facts / decisions.
- `personal_ephemeral`   — time-bound personal status.
- `contextual`           — only meaningful in one situation; sparingly.

Distribution guidance still applies: ~60% universal, ~35%
personal_persistent, ~5% contextual, ~0% personal_ephemeral.

## Claim Provenance

Tag every claim's source with exactly one of:

- `user_stated`     — the user asserted it.
- `user_confirmed`  — LLM proposed, user confirmed.
- `llm_unverified`  — LLM said it, user did not confirm.
- `llm_speculation` — explicitly hypothetical.

Add the set of tags actually used to top-level `claim_sources`. If
the slice is pure `llm_speculation` with no `user_stated` anchor,
refuse to produce a card: emit
`{{"dropped": true, "reason": "only_speculation"}}` instead.

## Anti-Pollution Rule

Do NOT invent facts. Do NOT promote speculation to claims. If a
claim has no basis in the slice, drop it. A card with 2 strong
claims is better than 5 mixed-quality claims — shorter is safer
for retrieval precision.

## De-individualisation

Replace concrete private identifiers in both `entities` and `claims`:

- Private IPs  -> `192.0.2.10` (TEST-NET-1) or similar.
- Home paths   -> `/path/to/...`
- Personal emails / SSH aliases -> `user@example.com`, `host`.

Keep names of public tools / products.

## Atomicity Examples

BAD (one compound claim):

    "Use torch.device('mps') and set PYTORCH_ENABLE_MPS_FALLBACK=1
     for unsupported ops, installing via conda nightly."

GOOD (3 atomic claims):

    - Use torch.device('mps') to target the MPS backend
    - PYTORCH_ENABLE_MPS_FALLBACK=1 routes unsupported ops to CPU
    - Install via: conda install pytorch torchvision -c pytorch-nightly

## Output Format (critical)

Emit ONE JSON object — nothing else. No prose before or after. Inside
`body_markdown`, use straight ASCII quotes (`"`), not curly
typographic quotes. If your platform has a JSON-only / structured-
output mode, enable it.
```

---

**Notes:**

- Daemon retention for RAG-only mission checks `len(entities) >= 1 and len(claims) >= 1` rather than counting six-section headings.
- The body shape (`# title`, `Entities:` line, then bullet list) is the load-bearing contract that downstream embedder + reranker depend on.
- Unlike the Normal variant, this one skips the slicer and router stages — the single refine call produces the card end-to-end.
