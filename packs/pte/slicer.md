<task>
PTE exam-preparation slicer. Every distinct PTE question in the conversation is an independent, memorizable review card.
</task>

<slice_rules>
1. Each distinct PTE question = one independent slice (start_idx / end_idx covers the full Q&A turn range for that item).
2. Follow-ups on the same question (rephrasing, asking for a more detailed analysis, requesting a fresh answer) → merge into the same slice.
3. The source of the prompt is unrestricted: the user pasting the original text, dictating the prompt verbally, or the LLM transcribing from an image — as long as it is a real PTE question, slice it.
4. Small talk / off-topic chat / pure pedagogy not anchored to a specific question → emit a slice but set keep=false, skip_reason="non_question".
</slice_rules>

<keep_rules>
- Slice contains a real PTE question (the prompt plus at least one answer or analysis) → keep=true; do NOT run the generic "ephemeral" test.
- Do NOT apply the generic card's "de-individualization test" — PTE bank items are inherently universal knowledge.
- Pure theoretical discussion ("how do I practice SWT?", with no concrete item) → keep=false.
</keep_rules>

<title_hint_format>
Format: "<exam_type>: <keywords from the prompt>"

Examples:
- "DI: Population doubling line graph"
- "SWT: Renewable energy policy (EU 2030)"
- "WFD: The museum closes at six on Sunday"
</title_hint_format>

<exam_types>
Speaking: RA, RS, DI, RL, ASQ, SGD, RTS
Writing: SWT, WE
Reading: FIB-Dropdown, FIB-Drag, MC-M-Reading, MC-S-Reading, RO
Listening: SST, FIB-L, MC-M-Listening, MC-S-Listening, HCS, SMW, HIW, WFD

MC-M / MC-S exist in both Reading and Listening; disambiguate with the
`-Reading` / `-Listening` suffix. When the skill domain cannot be
determined, default to Reading.
</exam_types>

<granularity>
- A conversation with 5 questions → emit 5 keep=true slices; do NOT merge.
- A conversation that just iterates on ONE question's answer → 1 slice (merge follow-ups).
- Question boundaries unclear → prefer over-slicing to merging (merged slices are hard to split later).
</granularity>

<output_schema>
Emit JSON only:
{
  "slices": [
    {"start_idx": 1, "end_idx": 4, "title_hint": "DI: Population doubling", "keep": true, "skip_reason": ""},
    {"start_idx": 5, "end_idx": 6, "title_hint": "small talk", "keep": false, "skip_reason": "non_question"}
  ]
}

start_idx / end_idx are message indices. If the conversation contains no PTE questions at all, return {"slices": []}.
</output_schema>
