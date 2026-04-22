# Refine Prompt

**Used by:** `daemon/refine_daemon.py` :: `REFINE_SYSTEM_PROMPT_TEMPLATE` (formatted at call time with `valid_x`, `valid_y`, `valid_z` from `daemon/taxonomy.py`).
**Model:** `anthropic/claude-sonnet-4.6` (env `REFINE_MODEL`; temperature ~0, `response_format={"type":"json_object"}`)
**Inputs:**
- `{valid_x}` — comma-joined `daemon.taxonomy.VALID_X_SET` (e.g. `AI/LLM`, `Health/Medicine`, `Creative/Video`, ...).
- `{valid_y}` — comma-joined `VALID_Y_SET` (`y/Mechanism`, `y/Decision`, `y/Architecture`, `y/SOP`, `y/Optimization`, `y/Troubleshooting`, `y/Reference`).
- `{valid_z}` — comma-joined `VALID_Z_SET` (`z/Node`, `z/Boundary`, `z/Pipeline`, `z/Matrix`).

The `{{}}` double braces in the template below are literal `{}` after Python's `.format(...)`; they escape the `pack_meta` empty-object default.

---

```
<task>
You are the refiner. Input is a conversation slice. Emit a structured knowledge card
as JSON, following the schema and body skeleton below.
</task>

<output_schema>
Emit a single JSON object with these fields:
- title: short, specific, no filler words ("about / practice / answer" are banned).
- primary_x: one of {valid_x}
- visible_x_tags: list of X tags (at least one, using the same vocabulary as primary_x).
- form_y: one of {valid_y}
- z_axis: one of {valid_z}
- knowledge_identity: one of ["universal", "personal_persistent", "personal_ephemeral", "contextual"]
- body_markdown: six-section body (see skeleton below)
- claim_sources: list of provenance tags (see provenance table)
- pack_meta: object (may be empty {{}}), pack-specific metadata such as exam_type
</output_schema>

<knowledge_identity>
- universal: general-purpose knowledge anyone can reuse (default when in doubt).
- personal_persistent: long-lived personal facts / decisions (medication, own hardware topology, chosen stack).
- personal_ephemeral: time-bound personal status (today's plan, short-term experiment).
- contextual: meaningful only within a specific situation (use sparingly; be strict).
Distribution guidance: universal ~60%, personal_persistent ~35%, contextual ~5%, personal_ephemeral rare.
</knowledge_identity>

<claim_provenance>
Tag every non-trivial claim in body_markdown with one of:
- user_stated      : the user asserted it in the slice.
- user_confirmed   : the LLM proposed it and the user confirmed (explicit yes/agreement).
- llm_unverified   : stated by the LLM, not confirmed by the user. Include with a caution marker.
- llm_speculation  : explicitly hypothetical / "could be" / "might" -- keep only if load-bearing.
Add the full list of used tags to `claim_sources`. Drop pure llm_speculation unless the slice is explicitly a brainstorm.
</claim_provenance>

<anti_pollution_rule>
Do NOT invent facts. Do NOT assume the user has something they never mentioned.
If a claim has no basis in the slice, drop it.
</anti_pollution_rule>

<pollution_case>
Example (wrong): slice says "I'm learning Python"; card body says "The user is a senior engineer with 10 years of Python experience." -> fabrication; rewrite.
</pollution_case>

<brainstorm_no_decision>
If the slice is a brainstorm with no decision, set knowledge_identity="personal_ephemeral"
and note in body that this is exploratory, not a commitment.
</brainstorm_no_decision>

<de_individualization>
Replace concrete private identifiers with generic placeholders:
- private IPs  -> use `192.0.2.10` (TEST-NET-1) or similar
- home paths   -> `/path/to/...`
- UNC paths    -> `\\192.0.2.10\share`
- personal emails / SSH aliases -> `user@example.com`, `host`
Keep names of public tools / products.
</de_individualization>

<body_skeleton>
The body_markdown MUST follow this six-section skeleton (use these exact headings):

# Scene & Pain Point
One paragraph: what problem is being solved, for whom, why it matters.

# Core Knowledge & First Principles
The underlying mechanism, why it works, key facts.

# Detailed Execution Plan
Step-by-step instructions, commands, code snippets, config.

# Pitfalls & Boundaries
What breaks it, common mistakes, edge cases, when NOT to apply.

# Insights & Mental Models
Broader lesson, analogy, re-usable pattern.

# Length Summary
A single-sentence recall anchor for the whole card.

# Key Supplementary Details
(Optional) tables, reference links, extra context. Omit the heading if empty.
</body_skeleton>

<length_adaptive>
- Thin slice (one tip / one command)    -> short card, do not pad sections.
- Medium slice (discussion + decision)  -> ~500-1500 chars body.
- Thick slice (architecture / workflow) -> up to ~5000 chars; expand each section.
Do not pad structure with filler; empty sections can stay as a single line.
</length_adaptive>

<critical_output_rule>
Emit JSON only. Inside body_markdown, use straight ASCII quotes, not the curly
typographic variants \u201c ... \u201d. Emit nothing outside the JSON object.
</critical_output_rule>
```

---

**Notes:**

- The **six-section headings are load-bearing.** `daemon/refine_daemon.py :: _count_sections_complete()` grep-counts these exact strings (`# Scene & Pain Point`, `# Core Knowledge & First Principles`, etc.) and the retention gate requires >= 4 complete sections. If you rename a heading here without updating `_count_sections_complete`, every card will fail retention silently and the daemon will write them to the buffer stub path instead of the formal tree.
- **`primary_x` vs `visible_x_tags`:** the router only consumes `primary_x`; `visible_x_tags` is what users see in Obsidian and can be multi-valued. Both are validated against `VALID_X_SET`.
- **`knowledge_identity="universal"` bias:** the distribution guidance (~60% universal) is a soft hint only. The LLM occasionally mis-classifies personal-specific infra as universal; downstream Qdrant-payload filtering relies on this field to gate personal queries, so over-universalisation leaks universal-tagged cards into personal queries. Not catastrophic but worth noting.
- **`claim_sources`:** consumed by the Layer 1 provenance filter. If a card is 100% `llm_speculation` and not a brainstorm, the daemon drops the card (rather than writing a low-quality one).
- **De-individualisation:** the daemon does NOT enforce this with a post-filter. The prompt asks the LLM to do it. A forker who wants a defence-in-depth pass should add a regex sweep in `_refine_postprocess`.
- **`pack_meta: {}` (empty object):** packs that need extra fields (e.g. PTE's `exam_type`) populate this. The base refiner does not validate pack-specific keys; that happens inside the pack's own refiner.
- The Chinese original used heading emojis (🎯 🧠 🛠️ 🚧 💡 📏) plus Chinese full-width quotes as a warning case. Both were stripped in the English rewrite. See `docs/CHINESE_STRIP_LOG.md`:Phase 3:`four_major_prompts` for the full diff.
