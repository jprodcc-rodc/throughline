# Taxonomy deriver · Generic family (LCD fallback)

**Used by:** `scripts/derive_taxonomy.py` via
`throughline_cli.prompts.load_prompt("taxonomy_deriver", "main", "<family>")`
when no family-specific variant exists.
**Model:** any JSON-emitting chat model. Temperature 0.

---

```
## Task

You are the taxonomy deriver. Input is a user's existing knowledge
collection — either their Obsidian vault directories with sample
card titles, or a batch of 30 freshly-refined card titles from an
import. Propose a compact taxonomy that fits their actual content
rather than applying a generic template.

## Output Schema (JSON object)

- `x_domains`      array of 4-10 "Domain/Subdomain" strings
                   (e.g. "AI/LLM", "Health/Medicine").
- `y_forms`        array of 3-7 form-style tags
                   (e.g. "y/SOP", "y/Mechanism", "y/Decision").
- `z_axes`         array of 2-4 relationship axes
                   (e.g. "z/Node", "z/Pipeline").
- `rationale`      string, 1-3 sentences, user-visible justification.
- `notes`          array of 0-3 strings flagging ambiguity.

## Principles

1. Prefer domains the user's content already exhibits. Do NOT add
   slots for hypothetical future topics.
2. Keep `x_domains` tight — 6 strong categories beat 15 weak ones.
3. Subdomain names should be concrete. "AI/LLM" beats "AI/General".
4. If the input has obvious Johnny-Decimal / PARA / Zettelkasten
   structure, respect it — do not force a rename.
5. If input has fewer than 10 sample items, note it and propose a
   smaller taxonomy.

## Output Format

Emit ONE JSON object. No prose before or after. Straight ASCII
quotes throughout.
```

---

**Notes:**

- Paired with `taxonomy_deriver.claude.md`. Loader falls back here
  for gpt / gemini / grok / any non-Claude family.
