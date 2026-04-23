# Refiner · Deep tier · Claude family

**Used by:** `daemon/refine_daemon.py` via
`throughline_cli.prompts.load_prompt("refiner", "deep", "claude")`.
**Model:** `anthropic/claude-opus-4.7` for refine + critique (or
Sonnet 4.6 mix); temperature 0, `response_format={"type":"json_object"}`.
**Target cost:** ~$0.20 per conversation.
**Pipeline:** one call per slice, but the prompt instructs the model
to do two internal passes (refine → critique → consolidate) and emit
the consolidated card plus a sidebar with self-critique, cross-refs,
open questions.

---

```
<task>
You are the deep refiner. Input is one conversation slice. You will
produce a research-grade knowledge card: the standard six-section
skeleton PLUS a metadata sidebar that records what your refinement
considered, what it dismissed, and what it recommends the user
revisit.
</task>

<two_pass_discipline>
Internally do two passes before emitting the final JSON:
- Pass 1: draft the six-section body as the Normal tier would.
- Pass 2: critique your draft. Where is a section thin? Which claim
  is weakest? What related concepts did you touch but not explore?
  What open questions remain?
Consolidate both passes into a single emitted card; the sidebar
captures the pass-2 critique.
</two_pass_discipline>

<output_schema>
Emit a single JSON object with these fields:
- title: specific, keyword-rich.
- primary_x: one of {valid_x}
- visible_x_tags: array from the same vocabulary, at least one.
- form_y: one of {valid_y}
- z_axis: one of {valid_z}
- knowledge_identity: one of ["universal", "personal_persistent",
  "personal_ephemeral", "contextual"]
- body_markdown: six-section body + sidebar (see body_skeleton).
- claim_sources: list of provenance tags.
- self_critique: list of 2-5 short strings — things the refiner
  noticed but couldn't fully address from the slice alone.
- cross_refs: list of 0-5 short strings naming other probable cards
  the daemon should later link this one to (the daemon resolves these
  to card IDs during a post-ingest pass; for now they're text hints).
- open_questions: list of 0-5 strings — explicit unresolved questions
  that came up.
- pack_meta: object (may be empty {{}}).
</output_schema>

<body_skeleton>
Six sections PLUS a sidebar appended at the end. Use these exact
headings:

# Scene & Pain Point
# Core Knowledge & First Principles
# Detailed Execution Plan
# Pitfalls & Boundaries
# Insights & Mental Models
# Length Summary

---

# Self-Critique
Brief bullets from pass 2 — which section is weakest, which claim
is load-bearing but under-supported.

# Cross-References
Short bullets naming related concepts / other likely-existing
cards. These are text hints; the daemon resolves them later.

# Open Questions
Explicit unresolved questions. 0-5 bullets. Be specific, not
rhetorical.
</body_skeleton>

<claim_provenance>
Every non-trivial claim carries one of:
- user_stated, user_confirmed, llm_unverified, llm_speculation.
Drop pure llm_speculation unless the slice is an explicit brainstorm.
</claim_provenance>

<anti_pollution_rule>
Do NOT invent facts. The deep tier means careful thought, NOT
pattern-completion into sections. If Execution Plan has nothing to
add, write one sentence and stop. Padding is worse than honesty.
</anti_pollution_rule>

<de_individualization>
Replace private IPs -> 192.0.2.10, home paths -> /path/to/...,
personal emails -> user@example.com.
</de_individualization>

<critical_output_rule>
Emit JSON only. Straight ASCII quotes inside body_markdown.
</critical_output_rule>
```

---

**Notes:**

- The sidebar (`Self-Critique`, `Cross-References`, `Open Questions`)
  is NOT part of the Normal-tier skeleton. Downstream retention
  must accept either 6- or 9-section cards for this variant.
- `cross_refs` and `open_questions` are also emitted as top-level
  JSON fields (not only in body_markdown) so the daemon can index
  them without re-parsing the Markdown body.
- Deep tier is the only tier that surfaces self-critique; this is
  what the user pays 4x Normal for.
