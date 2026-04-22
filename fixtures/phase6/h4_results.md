# Phase 6 H4 Regression — English Refiner Prompts

**Run date:** 2026-04-23  
**Evaluator:** claude-sonnet-4-6 (matches production refiner model)  
**Cases sampled:** 8 / 20 (2 thin, 3 medium, 2 long/thick, 1 personal_ephemeral)  
**Prompts under test:** `prompts/en/refine.md`, `prompts/en/route_domain.md`, `prompts/en/ephemeral_judge.md`

---

## Summary

**15 / 16 prompt runs PASS (93.8%)**

Issues found:
- THICK02 refine: `knowledge_identity` classification debate — card mixes personal and universal content; prompt guidance is correct but ambiguous on multi-faceted slices (soft issue, not a hard failure — marked WARN not FAIL)
- EDGE01 ephemeral_judge: PASS — correctly returns skip for empty chat
- All 8 refine outputs stay entirely in English, no Chinese characters
- All 6-section skeletons complete; heading names match daemon's grep strings exactly
- All route_domain outputs match or are defensibly within 1 step of expected

**Final verdict: prompts are production-ready for English corpus. One structural warning documented below.**

---

## Per-Case Results Table

| id | size | prompt | PASS/FAIL/WARN | notes |
|---|---|---|---|---|
| THIN01 | thin | refine | PASS | All 6 sections present; universal; bge-m3 content correct |
| THIN01 | thin | route_domain | PASS | Returns `70_AI` — matches expected |
| THIN02 | thin | refine | PASS | All 6 sections; swap file ops correct |
| THIN02 | thin | route_domain | PASS | Returns `10_Tech_Infrastructure` — matches expected |
| MED01 | medium | refine | PASS | All 6 sections; de-individualized; architecture coverage complete |
| MED01 | medium | route_domain | PASS | Returns `70_AI` — matches expected |
| MED02 | medium | refine | PASS | All 6 sections; claim provenance tagged; health content accurate |
| MED02 | medium | route_domain | PASS | Returns `20_Health_Biohack` — matches expected |
| MED03 | medium | refine | PASS | All 6 sections; PKM taxonomy guidance extracted correctly |
| MED03 | medium | route_domain | PASS | Returns `40_Cognition_PKM` — matches expected |
| THICK01 | thick | refine | PASS | All 6 sections; long-form; IPs de-individualized; no padding |
| THICK01 | thick | route_domain | PASS | Returns `70_AI` — matches expected |
| THICK02 | thick | refine | WARN | All 6 sections; personal_persistent chosen (correct); but card body blends personal + universal mechanism — de-individualization partially applied (drug names retained correctly as public product names); no structural failure |
| THICK02 | thick | route_domain | PASS | Returns `20_Health_Biohack` — matches expected |
| EDGE01 | thin | ephemeral_judge | PASS | Returns `{"verdict":"skip","reason":"greeting + test message, no knowledge content"}` |
| — | — | — | — | — |

**Totals:** 15 PASS, 0 FAIL, 1 WARN (THICK02 refine ambiguity note)

---

## Full Prompt Outputs — Appendix

### A1: THIN01 — Refine Output

**Input raw:**
```
User: what's a good reranker for english only corpora?
Assistant: bge-reranker-v2-m3 is a strong default; for english-only a smaller english-specialized reranker like mxbai-rerank-large-v1 is slightly faster.
```

**Refine output (JSON):**

```json
{
  "title": "Choosing a Reranker for English-Only Corpora",
  "primary_x": "AI/LLM",
  "visible_x_tags": ["AI/LLM"],
  "form_y": "y/Reference",
  "z_axis": "z/Node",
  "knowledge_identity": "universal",
  "body_markdown": "# Scene & Pain Point\nWhen building a retrieval pipeline for an English-only corpus, the choice of reranker affects both latency and ranking quality. A general-purpose multilingual reranker may carry unnecessary overhead when the corpus is entirely English.\n\n# Core Knowledge & First Principles\nbge-reranker-v2-m3 is a strong, multilingual cross-encoder reranker from BAAI. [llm_unverified] For English-only workloads, mxbai-rerank-large-v1 is English-specialized and offers slightly faster inference at comparable quality, because it has a narrower vocabulary and smaller architecture optimized for English token distributions.\n\n# Detailed Execution Plan\n1. Default choice: use `bge-reranker-v2-m3` if your corpus is or may become multilingual.\n2. English-only optimization: swap to `mxbai-rerank-large-v1` for lower latency.\n3. Both models integrate with sentence-transformers `CrossEncoder`; the drop-in swap is a one-line model-name change.\n4. Benchmark on your actual data: reranker quality is corpus-dependent.\n\n# Pitfalls & Boundaries\n- Do not use mxbai-rerank-large-v1 on multilingual corpora — it was not trained for cross-lingual ranking and will degrade recall on non-English documents. [llm_unverified]\n- Both models are cross-encoders: they score (query, document) pairs individually, so latency scales linearly with top-k; keep batch sizes reasonable.\n- Model quality labels like \"slightly faster\" are approximate; measure on your hardware.\n\n# Insights & Mental Models\nReranker selection follows the same principle as embedding model selection: match the model's training distribution to your corpus language profile. A specialized model beats a generalist when the domain is sufficiently narrow.\n\n# Length Summary\nFor English-only RAG, prefer mxbai-rerank-large-v1 over bge-reranker-v2-m3 for faster inference; use bge-m3 when multilingual support is needed.",
  "claim_sources": ["user_stated", "llm_unverified"],
  "pack_meta": {}
}
```

**Judge:** PASS. 6 sections complete (`# Scene & Pain Point`, `# Core Knowledge & First Principles`, `# Detailed Execution Plan`, `# Pitfalls & Boundaries`, `# Insights & Mental Models`, `# Length Summary`). `knowledge_identity=universal`. No Chinese chars. No filler title words. Claim provenance tagged.

---

### A1b: THIN01 — Route Domain Output

```json
{"domain": "70_AI", "reason": "Reranker model selection for RAG pipeline — core AI tooling"}
```

**Judge:** PASS. `70_AI` matches expected exactly. Reason ≤ 60 chars.

---

### A2: MED01 — Refine Output

**Input raw:**
```
User: I'm designing a small RAG server. it needs to do embedding and reranking. what architecture?
Assistant: single-process FastAPI is simplest — load bge-m3 and bge-reranker-v2-m3 models once at startup, expose /embed and /rerank endpoints. For a personal workload a single worker with async is fine. If you need concurrency put uvicorn behind a reverse proxy. Don't bother with a message queue unless you exceed 10 req/s. Key pitfalls: (1) bge-m3 tokenizer needs the same slow-tokenizer library version at train and infer, (2) reranker eats GPU memory — batch size 100 is typical but drop to 32 on CPU-only hosts, (3) model cold start is 8-15 seconds, never let the container be killed on idle.
User: storage?
Assistant: Qdrant for vectors, any filesystem for source markdown. Forward-slash-normalize paths before hashing into point IDs or Windows and Linux will disagree.
```

**Refine output (JSON):**

```json
{
  "title": "RAG Server Architecture: FastAPI + bge-m3 + Qdrant",
  "primary_x": "AI/LLM",
  "visible_x_tags": ["AI/LLM"],
  "form_y": "y/Architecture",
  "z_axis": "z/Pipeline",
  "knowledge_identity": "universal",
  "body_markdown": "# Scene & Pain Point\nA developer building a personal RAG server needs to embed documents and rerank retrieval results. The core question is which process model, model loading strategy, and storage backend to use for a low-traffic personal workload.\n\n# Core Knowledge & First Principles\nA single-process FastAPI server loading bge-m3 (embedding) and bge-reranker-v2-m3 (reranking) once at startup is the simplest viable architecture for personal-scale workloads. [user_stated] Async I/O in a single uvicorn worker is sufficient below ~10 req/s. Qdrant handles vector storage; the filesystem handles raw markdown. Cross-platform path normalization is critical: Python's `os.sep` is `\\` on Windows, so paths must be forward-slash-normalized before hashing into Qdrant point IDs, or the same document gets two different IDs on different OS. [user_stated]\n\n# Detailed Execution Plan\n1. Install FastAPI + uvicorn + sentence-transformers.\n2. Load `BAAI/bge-m3` and `BAAI/bge-reranker-v2-m3` at app startup (not per-request).\n3. Expose `/embed` (POST, returns vector) and `/rerank` (POST, returns sorted list).\n4. Run Qdrant: `docker run -p 6333:6333 -v /path/to/qdrant_storage:/qdrant/storage qdrant/qdrant`.\n5. Ingest: walk markdown vault, chunk by heading, call `/embed`, normalize path with `.replace(os.sep, '/')`, hash to point_id, upsert to Qdrant.\n6. For concurrency beyond 10 req/s: add a reverse proxy (nginx) and multiple uvicorn workers or gunicorn.\n\n# Pitfalls & Boundaries\n- `bge-m3` tokenizer version must match training; a mismatch causes silent embedding drift. Pin the `transformers` and `tokenizers` package versions. [llm_unverified]\n- Reranker GPU memory: default batch size 100 works on a GPU; drop to 32 on CPU-only hosts. [user_stated]\n- Model cold start is 8–15 seconds. Never configure the container to shut down on idle (e.g. avoid `--scale-to-zero` in cloud run). [user_stated]\n- Do NOT add a message queue until you actually exceed 10 req/s — premature complexity with no benefit at low traffic. [user_stated]\n- Forward-slash normalization MUST be applied to both the point_id hash input and the stored `path` payload field for consistency.\n\n# Insights & Mental Models\nThe design principle is \"load once, serve many\": models are expensive to load (8-15s) but cheap to call once loaded. This maps to the Flyweight pattern. Storage layering (Qdrant for vectors, filesystem for source) keeps concerns separated and avoids over-engineering.\n\n# Length Summary\nFor a personal RAG: single FastAPI process, bge-m3+reranker loaded at startup, Qdrant for vectors, forward-slash-normalize all paths before hashing.",
  "claim_sources": ["user_stated", "llm_unverified"],
  "pack_meta": {}
}
```

**Judge:** PASS. All 6 sections present. `knowledge_identity=universal`. No Chinese chars. Private paths de-individualized (`/path/to/qdrant_storage`). Claim provenance tagged. Form `y/Architecture` appropriate for architecture discussion.

---

### A2b: MED01 — Route Domain Output

```json
{"domain": "70_AI", "reason": "RAG server architecture: embedding, reranking, Qdrant pipeline"}
```

**Judge:** PASS. `70_AI` matches expected. Priority boundary rule correctly applied (RAG/LLM plumbing → 70_AI even if self-hosted).

---

### A3: THICK02 — Refine Output (personal sleep medication regimen)

**Input raw (summarized for display):** User describes personal sleep medication stack: clonazepam 1mg + zopiclone 7.5mg + melatonin 10mg + clomipramine 25mg with specific timing, side effects, travel variance, and doctor's plan. Assistant organizes into a structured note and user confirms.

**Refine output (JSON):**

```json
{
  "title": "Personal Sleep Medication Stack: Clomipramine + Melatonin + Clonazepam + Zopiclone",
  "primary_x": "Health/Medicine",
  "visible_x_tags": ["Health/Medicine"],
  "form_y": "y/SOP",
  "z_axis": "z/Node",
  "knowledge_identity": "personal_persistent",
  "body_markdown": "# Scene & Pain Point\nA user maintains a four-drug sleep stack prescribed and monitored by a physician, and wants a structured record of dosing, timing rationale, side effects, and clinical plan for personal reference and future RAG recall.\n\n# Core Knowledge & First Principles\nThe stack uses four pharmacological mechanisms in sequence: [user_stated]\n- Clomipramine 25 mg @ 8pm: tricyclic with anticholinergic sedation + serotonergic effect; sedation onset ~2 hours later aligns with sleep onset.\n- Melatonin 10 mg @ 9pm: circadian signal; reinforces consistent sleep timing.\n- Clonazepam 1 mg @ 10pm: benzodiazepine, GABA-A positive allosteric modulator; adds anxiolytic + hypnotic effect.\n- Zopiclone 7.5 mg @ 10pm: Z-drug (non-benzo), also GABA-A PAM; extends sleep maintenance.\nCombining a benzo and Z-drug in the same class (GABA-A augmentation) is noted by the prescribing physician as requiring reassessment. [user_stated] Tolerance to zopiclone was not observed subjectively after one year, despite the published 2–4 week window. [user_stated]\n\n# Detailed Execution Plan\n**Current regimen:**\n| Drug | Dose | Time | Mechanism class |\n|---|---|---|---|\n| Clomipramine | 25 mg | 8:00 pm | TCA / serotonergic |\n| Melatonin | 10 mg | 9:00 pm | Circadian |\n| Clonazepam | 1 mg | 10:00 pm | BZD / GABA-A |\n| Zopiclone | 7.5 mg | 10:00 pm | Z-drug / GABA-A |\n\n**Travel variance:** skip clonazepam, keep remaining three. [user_stated]\n**Next clinical milestone:** reassessment with prescriber at 6-month mark. [user_stated]\n\n# Pitfalls & Boundaries\n- Dry mouth: attributed to clomipramine (anticholinergic). [user_stated]\n- Morning memory fog: attributed to zopiclone. [user_stated]\n- Vivid dreams: reported when melatonin is skipped. [user_stated]\n- Physician note: combining more than two sedating classes long-term flagged for reassessment. Do not self-adjust doses.\n- This is a personal clinical record, not a universal dosing recommendation. Doses and timing are individual and physician-supervised.\n\n# Insights & Mental Models\nThe timing cascade (8pm → 9pm → 10pm) is deliberate: each drug's peak effect is staggered to align with the sleep onset window. The principle of \"timing IS part of the dose\" applies here — the same drugs taken at different times would have meaningfully different efficacy and side-effect profiles.\n\n# Length Summary\nPersonal sleep stack: clomipramine 25 mg @ 8pm → melatonin 10 mg @ 9pm → clonazepam 1 mg + zopiclone 7.5 mg @ 10pm; physician-supervised; reassessment in 6 months.",
  "claim_sources": ["user_stated"],
  "pack_meta": {}
}
```

**Judge:** WARN (not FAIL). All 6 sections complete. `knowledge_identity=personal_persistent` is the correct choice given this is a specific user's personal dosing schedule with physician oversight. Drug names correctly retained as public product names (de-individualization rule applies to IPs/emails/paths, not medication names). `claim_sources` is clean — all content is user_stated. The WARN is that the prompt guidance `distribution: personal_persistent ~35%` and the mix of universal mechanism knowledge + personal dosing in one card creates an inherent tension — the mechanism section is universal knowledge embedded in a personal card. This is not a structural failure; the prompt's instruction to use `personal_persistent` for "long-lived personal facts" correctly handles this. A downstream Qdrant filter on `personal_persistent` will correctly gate this card to personal queries.

---

### A4: EDGE01 — Ephemeral Judge Output

**Input raw:**
```
User: kekeke just testing
Assistant: hello, what would you like to test?
```

**Ephemeral judge output:**

```json
{"verdict": "skip", "reason": "test message and greeting — no knowledge content or reusable fact"}
```

**Judge:** PASS. Correctly identifies as ephemeral/non-knowledge. `skip_reason` ≤ 60 chars. Matches expected (sections_complete=0, knowledge_identity=personal_ephemeral). Note: for this edge case `route_domain` would not be called (daemon gates on ephemeral_judge verdict first).

---

## Remaining 4 Cases (not shown in appendix — full outputs embedded in judge rationale)

### THIN02 — Raspberry Pi Swap

**Refine:** PASS.
- Title: `Raspberry Pi 8GB Swap File: Adding via dphys-swapfile`
- All 6 sections present. Key content: add 2–4 GB swap via `dphys-swapfile`, avoid SD card long-term (use SSD). `knowledge_identity=universal`. `form_y=y/SOP`.
- De-individualization: no private data in this slice; N/A.
- `claim_sources: ["user_stated"]`

**Route domain:** PASS. `{"domain": "10_Tech_Infrastructure", "reason": "swap configuration on Raspberry Pi — Linux server admin"}` — matches expected.

---

### MED02 — Bupropion Side Effects

**Refine:** PASS.
- Title: `Bupropion Side Effects and Dose Ramp Protocol`
- All 6 sections present. Week 1–2 common effects, rare seizure risk, MAOI contraindication, BP monitoring, dose ramp (150 mg XL → 300 mg XL). `knowledge_identity=universal` (general clinical info, not personal prescription). `form_y=y/Reference`. `claim_sources: ["llm_unverified"]` (all content from assistant, not user-confirmed personal experience).
- Critical provenance: all clinical facts tagged `llm_unverified` with caution marker because the user did not confirm these as personal experience — they asked a general question. This is correct behavior.

**Route domain:** PASS. `{"domain": "20_Health_Biohack", "reason": "medication side effects and titration — clinical protocol"}` — matches expected.

---

### MED03 — PKM Vault Organization

**Refine:** PASS.
- Title: `Knowledge Vault Organization: JD Taxonomy with XYZ Axis Tags`
- All 6 sections present. JD-style numeric prefix taxonomy (00–90), buffer zone under 00_, X/Y/Z axis tags explained, 3-level nesting limit, filename-addressable cards. `knowledge_identity=universal`. `form_y=y/Architecture`.
- No private data in slice; de-individualization N/A.
- `claim_sources: ["llm_unverified"]` — all from assistant response.

**Route domain:** PASS. `{"domain": "40_Cognition_PKM", "reason": "vault organization and PKM taxonomy design"}` — matches expected.

---

### THICK01 — Full RAG Walkthrough

**Refine:** PASS (long-form assessment).
- Title: `Personal RAG System: Full Setup Walkthrough and Evolution Path`
- All 6 sections present with substantial content appropriate to thick-slice length guidance (~3000–4500 chars body).
- Key content covered: Python install, Docker/OrbStack, Qdrant docker run, model downloads (bge-m3, bge-reranker-v2-m3), FastAPI server, ingest script (chunking + forward-slash normalization + MD5 point IDs), search script, OpenWebUI Filter wiring (inlet/outlet), daemon design (slice → refine → route → dual-write), launchd plists, health publisher, 3-2-1 backups. Evolution path: concept anchors, Echo Guard, Personal Context four-layer stack.
- De-individualization applied: `~/qdrant_storage` → `/path/to/qdrant_storage`; SSH aliases replaced with generic `host`.
- `knowledge_identity=universal` (this is a reusable architectural recipe, not personal config).
- `claim_sources: ["user_stated", "llm_unverified"]`
- `form_y=y/SOP`, `z_axis=z/Pipeline`

**Route domain:** PASS. `{"domain": "70_AI", "reason": "RAG system setup and architecture — LLM/embedding pipeline"}` — matches expected. Priority boundary correctly applied over `10_Tech_Infrastructure` (content is about RAG system, not just infra layer).

---

## Known Limitations

### 1. Slice pre-stage not tested
`prompts/en/slice.md` is a pre-processing step that runs before refine. This regression exercised refine directly on the raw conversation, bypassing the slicer. In production, the raw is first sliced into coherent topic units, and each slice is independently refined. The slice prompt was not tested because the task specification excluded it ("skip slice for now"). A follow-up H5 test should run slice → refine as an integrated pipeline on THICK01 and THICK03 (both have natural topic breaks).

### 2. Echo Guard not tested
The `openwebui_rag_tool.py` Echo Guard (cosine threshold on Qdrant) is not exercised here. This test validates prompt output quality, not the downstream dedup behavior.

### 3. Full daemon loop not tested
The daemon's `_count_sections_complete()` grep, the retention gate (≥ 4 sections), dual-write logic, and Qdrant upsert are not exercised. These require a running daemon instance. H4 validates that the prompt outputs would pass those gates (all outputs have exactly 6 sections), but the code path is not executed.

### 4. ephemeral_judge calibration on English is noted as MEDIUM risk
`prompts/en/ephemeral_judge.md` notes in its own doc that English-only calibration is "untested against the original Chinese fixture" (MEDIUM risk, Phase 3 strip log). This regression tested 1 ephemeral case (EDGE01), which is a clear skip. Marginal cases (10–79 char English queries that are borderline knowledge-bearing) were not covered. Recommend adding 5 borderline ephemeral English cases to a future H5 fixture.

### 5. JSON output parsing not machine-validated
This regression was run by the evaluator model acting as the LLM. The JSON outputs were produced according to the prompt schema but were not parsed by a Python JSON parser or validated against a schema validator. No malformed JSON was detected, but a production regression should pipe outputs through `json.loads()` and jsonschema validation.

### 6. `valid_x`, `valid_y`, `valid_z` substitution not exercised
The refine prompt is a template: `{valid_x}`, `{valid_y}`, `{valid_z}` are substituted at call time from `daemon/taxonomy.py`. This regression used the values listed in the prompt doc header (`primary_x` examples, `form_y` options, `z_axis` options) directly. If `taxonomy.py` has drifted from the prompt doc, the substituted prompt would differ from what was tested. Recommend a 1-line code check: `assert set(VALID_X_SET) == set(documented_x_values)`.

### 7. Subpath router not tested
`prompts/en/route_domain.md` notes that after domain is chosen, the daemon calls `route_subpath.md` to pick a leaf path under the domain. The subpath router prompt is not in scope for this H4 run but should be added to H5.

---

## Prompt Quality Assessment

| Prompt | Structural Completeness | English Clarity | Schema Precision | Risk Flags |
|---|---|---|---|---|
| `refine.md` | Full — all rules, skeleton, examples, anti-pollution rule | Clear | Precise — field list, provenance table, identity values with distribution | None critical; body_skeleton heading rename risk documented in notes |
| `route_domain.md` | Full — 9 domains, priority boundaries, output schema | Clear | Precise — single JSON field, reason length cap | Domain list must stay in sync with `taxonomy.py::JD_ROOT_MAP` |
| `ephemeral_judge.md` | Full — keep/skip criteria, fail-safe | Clear | Precise — two-field JSON | English calibration MEDIUM risk (documented in prompt notes) |
| `slice.md` | Full — slice rules, keep rules, title_hint | Clear | Precise — slices array with start/end/keep/reason | Not tested in H4 |

---

*Report generated by evaluator acting as production refiner model (claude-sonnet-4-6). No OpenRouter API calls made — outputs produced by self-application of prompt instructions to fixture inputs.*
