# Phase 6 Session State

**Purpose:** Cross-session continuity anchor. If the conversation is summarized or a new session opens, read this file FIRST to pick up exactly where the last session left off. This is the single source of truth for Phase 6 progress.

**Last updated:** 2026-04-23 (v0.1.0 shipped + v0.2.0 usability scoped)

## v0.1.0 shipped 🎉

- Tag: `v0.1.0` → commit `cbbb92f`
- GitHub Release: https://github.com/jprodcc-rodc/throughline/releases/tag/v0.1.0
- Phase 6 ship-blockers all green (see next section)
- Post-v0.1.0 work rolled directly into v0.2.0 planning (below).

## v0.2.0 scope (rev 3, decided 2026-04-23 late evening)

After a third round of user additions, the wizard grows to 16 steps
but Mission branching (step 2) can shrink effective step count to
9-10 for specialised users. Six new U items landed; key architectural
observation: **card consumption mode (for reading vs for retrieval)
is an independent dimension the v0.1 architecture accidentally
welded to structure + tier**. Mission branch decouples them.

See the non-rev2 section below for the full list. Additions in rev3:

- **U20** Reranker swappable (paired with U12 in wizard step 7):
  bge-reranker-v2-m3 / v2-gemma local, Cohere / Voyage / Jina API,
  or skip.
- **U21** Vector DB swappable (wizard step 3): Qdrant (default Full),
  Chroma (default Local-only privacy), LanceDB, DuckDB-VSS,
  SQLite-vec, pgvector. `BaseVectorStore` abstraction spanning
  rag_server + daemon + ingest — largest engineering item.
- **U22** Prompt family per LLM (wizard step 8, auto-derived):
  Claude XML / GPT Markdown+JSON / Gemini structured / generic.
  ~48 prompt files (tier × mode × family), code-light but docs-heavy.
- **U23** Preview 5-dial constrained edit (wizard step 13): Tone,
  Length, Sections toggle, Language register, Keep-verbatim.
  No free-form prompt editing to preserve daemon schema.
- **U24** Mission branching (wizard step 2): Full flywheel /
  RAG-only / Notes-only. Decides which later steps apply.
- **U25** RAG-optimized card format (triggered by U24 RAG-only):
  title + entities + 3-8 atomic claims, no prose envelope.
  ~$0.001/conv. `prompts/en/refiner.rag_only.*.md`.

### The wizard's 16 steps (rev 3)

```
[1]  Python + venv + deps
[2]  Mission (U24) — Full / RAG-only / Notes-only    ← early branch
[3]  Vector DB (U21)  [skipped if Notes-only]
[4]  API key
[5]  LLM provider (U11)
[6]  Privacy level (U18)
[7]  Retrieval backend (U12 + U20)   [skipped if Notes-only]
[8]  Prompt family (U22) — auto-derived, confirm only
[9]  Import source (U2) + cold-start warning if fresh
[10] Import scan
[11] Refine tier (U15) + smart suggestion (U19)
[12] Card structure (U16)   [skipped if RAG-only, U25 format fixed]
[13] First-card preview (U17) + 5-dial constrained edit (U23)
[14] Taxonomy (U13)
[15] Daily budget cap (U3)
[16] Summary + confirm
```

## v0.2.0 scope (rev 2, decided 2026-04-23 evening)

**One sentence:** `python -m throughline install` is a 13-step wizard
that collects every onboarding decision with a sensible default per
step. All Enter = working config. Re-run any time to reconfigure.

**Everything in v0.2.0 orbits this one command.** The 13 steps
summon the underlying mechanisms (U1, U2, U3, U11-U19) — each step
surfaces a user decision that some code path has to honour.

### The wizard's 13 steps

```
[1]  Python + venv + deps
[2]  Docker / Qdrant
[3]  API key
[4]  LLM provider matrix (U11 — Anthropic / OpenAI / xAI / etc.)
[5]  Privacy level (U18 — Local-only / Hybrid / Cloud-max)
[6]  Embedder backend (U12 — bge-m3 / nomic / MiniLM / OpenAI)
[7]  Import source (U2 — ChatGPT / Claude / Gemini / fresh) + cold-
     start warning if fresh
[8]  Import scan (count + token estimate)
[9]  Refine tier (U15 — Skim / Normal / Deep, 40x cost spread)
     + smart suggestion (U19)
[10] Card structure (U16 — Compact / Standard / Detailed) via
     first-card preview (U17)
[11] Taxonomy (U13 — derive from vault / derive from imports /
     templates fallback)
[12] Daily budget cap (U3 — THROUGHLINE_MAX_DAILY_USD)
[13] Summary + confirm
```

### P0 work that underlies the wizard

- **U14** — the wizard itself (Rich-based CLI, config persistence
  to `~/.throughline/config.toml`).
- **U11** — LLM provider matrix (Grok via OpenRouter; doc-only, no
  code change).
- **U12** — embedder abstraction in `rag_server/rag_server.py`;
  `ingest_qdrant.py` derives VECTOR_SIZE from active embedder;
  Qdrant-rebuild flag on embedder change.
- **U13** — `scripts/derive_taxonomy.py` (LLM-derived from vault or
  imports); JD/PARA/Zettel templates demoted to fallback.
- **U15** — three refiner prompt variants (`refiner.skim.md`,
  `refiner.normal.md`, `refiner.deep.md`); pipeline
  parameterisation for stage count (Skim skips slicer, Deep adds
  critique).
- **U16** — same three-structure variant + first-card preview gate.
- **U17** — preview gate between step 10 and bulk refine.
- **U18** — privacy level as separate config axis; filters which
  models/endpoints the pipeline can use.
- **U19** — smart tier suggestion from corpus size + budget.
- **U2** — three adapters (see import section below).
- **U1** — cold-start Filter status line (🌱/🌿/full by card count).
- **U3** — daily budget cap enforced by daemon queue.
- **U4** — privacy-consent dry-run + `import_source` tag (now lives
  inside the wizard as step 7b).

### P1 shipped 2026-04-24

- **U5** — "Obsidian is optional" callout added to README.md top +
  DEPLOYMENT.md prerequisites. Plain Markdown files work in any
  editor; Obsidian is recommended, not required.
- **U6** — bge-m3 preflight section in DEPLOYMENT.md prerequisites.
  Suggests `pip install "huggingface_hub[cli]"` + two
  `huggingface-cli download` commands so the ~4.6 GB download happens
  once up front instead of blocking the first rag_server start.
- **U8** — scripts/uninstall.sh (macOS + Linux) + scripts/uninstall.ps1
  (Windows). Both prompt before each destructive step, default-keep
  the refined vault (user content), default-keep the Qdrant
  collection (--drop-collection to opt in), handle launchd / systemd
  / Docker container stops, clean ~/.throughline + runtime dir, hand
  off the OpenWebUI Filter removal as a manual step with a pointer.
- **~~U7~~** — taxonomy static templates **subsumed by U13**;
  JD/PARA/Zettel live on as wizard fallback only.

### v0.2.0 P0 shipped 2026-04-23 / 04-24

- **U14** wizard skeleton + TUI polish + step-10 adapter integration
- **U22** prompt family loader + normal/rag_optimized variants
- **U25** RAG-optimized card format (claude + generic)
- **U2** 3 import adapters (claude / chatgpt / gemini) — claude
  dogfooded 5 real bugs, gemini 0 bugs
- **U17** first-card preview (wizard step 13 calls real LLM via new
  throughline_cli/llm.py)
- **U15** tier matrix complete: skim / normal / deep × claude /
  generic = 8 prompt files
- **U1** cold-start status line in Filter (🌱 0-49 / 🌿 50-199 /
  silent 200+) with 5-min Qdrant count cache
- **U26** wizard banner + between-step progress ticker
- **U24** mission branching (baked into U14)
- **U3** daily USD cap scaffolded in wizard config; daemon
  enforcement still pending

### Still outstanding

- **U23** 5-dial constrained edit (preview iteration)
- **U13** taxonomy LLM derivation (wizard step 14 is currently
  template-only)
- **U3** daemon enforcement of THROUGHLINE_MAX_DAILY_USD
- **U4** import privacy-consent dry-run panel (tag exists; the
  interactive confirm pass needs stitching)
- **U12** embedder backend swappable (rag_server refactor)
- **U20** reranker swappable
- **U21** vector DB abstraction (biggest engineering item)

### Test counts (latest)

289 passed + 10 xfailed (was 38 + 10 at v0.1.0 tag). New sub-suites
across v0.2.0:
  - test_wizard.py          35
  - test_prompts.py         57
  - test_adapters_claude.py 55
  - test_adapters_chatgpt.py 41
  - test_adapters_gemini.py 38
  - test_preview.py         18
  - test_cold_start.py      15
Plus the 38 v0.1.0 Phase-6 cases still green.

**Deferred from v0.2.0 to v0.2.x marketing phase:**
- U9 — hero gif automation toolchain (Charm VHS + Remotion + OBS)
- U10 — dual-gif strategy (30s README loop + 60s import walkthrough)
- Design spec preserved in `docs/ONBOARDING_DATA_IMPORT.md` for later
  pickup; just not a v0.2.0 blocker.

**Deferred to v0.3.0:**
- B2 Merge & Synthesis (L3 cross-source aggregation; the correct home
  for "full aggregation" questions that adapters deliberately avoid).

**Private-repo ROADMAP** (`S:\syncthing\obsidian_python\docs\ROADMAP.md`,
commits `3f33621` / `428a73b`) has the same scope with the author's
personal notes attached. Public repo carries only the mechanism-level
plan.

---

## Where we are

Phase 6 = **English-only regression** for the open-source `throughline` repo (rewrite of a private upstream flywheel whose original natural language was not English). Every non-English artifact either stripped or rewritten; now validating the English rewrites don't regress behavior.

| Harness | Scope | Status | File(s) |
|---|---|---|---|
| **H1** | RecallJudge EN classification drift (48 cases × real Haiku 4.5) | ✅ **45/48 PASS (93.8%)** · 3 brainstorm drift accepted | `run_h1.py` · `recall_judge_en.jsonl` · `h1_results.json` · `H1_ANALYSIS.md` |
| **H2** | Cheap-gate short-turn behavior (20 cases offline) | ✅ **10/20 MATCH** · 10 gaps = intentional bare-pronoun regex strip (accepted as v0.1.0 cost) | `run_h2.py` · `pronouns_en.jsonl` · `h2_results.json` |
| **H3 code** | Card-injection wrapper + truncation (9 CD/LN cases offline) | ✅ **9/9 PASS** | `run_h3_code.py` · `h3_code_results.json` |
| **H3 Haiku** | Injection/PII/roleplay resistance (31 cases × real Haiku 4.5) | ✅ **31/31 PASS (100%)** after retry of 2 network timeouts · $0.17 | `run_h3_haiku.py` · `retry_h3_errors.py` · `h3_haiku_results.json` · `H3_ANALYSIS.md` |
| **H4** | 4 refiner prompts on EN raws (8 sampled cases × real Sonnet 4.6) | ✅ **15/16 PASS (93.8%)** · 1 WARN on personal/universal boundary, zero structural failures | `refiner_en.jsonl` · `h4_results.md` |

## Commits on this branch (public throughline, all pushed)

- `bac196a` — Phase 6 H1 fixture + runner + results + analysis
- `7a0f936` — Phase 6 H2 + H3 code + cheap-gate `thanks` fix + SESSION_STATE
- `8ab61dd` — Phase 6 H3 Haiku + H4 Sonnet-subagent + dual-layer injection guard doc
- `b0d8503` — CHINESE_STRIP_LOG backfill + README Phase 6 section + shape fuzz + overnight report

## Private-repo sync (done 2026-04-23)

Three files in `S:\syncthing\obsidian_python` updated to reflect Phase 6 completion:

- `docs/THROUGHLINE_PHASE6_RISKS.md` — §0 execution row flipped ✅, §1 regression results filled, §4 ship-blocker 4/7 checked, §5 overnight summary added
- `CLAUDE.md` — timeline header row for 2026-04-23 Phase 6 overnight added
- `docs/.internal/BUSINESS_ANALYSIS_ONEPAGER.md` — new §4.13 Phase 6 section, test-point count 317→420+, open-source-readiness table refreshed (prompt-language row + test-coverage row)

No `[mech]` commits on the private side this session — sync was docs-only.

## Key paths

| What | Where |
|---|---|
| Public repo (throughline) | `C:\Users\Jprod\code\throughline` |
| Private mirror (obsidian_python) | `S:\syncthing\obsidian_python` |
| Phase 6 fixtures + runners | `throughline/fixtures/phase6/` |
| Shipped Filter | `throughline/filter/openwebui_filter.py` |
| Shipped 8 EN prompts | `throughline/prompts/en/` |
| Chinese-strip log (HIGH-risk roll-up) | `throughline/docs/CHINESE_STRIP_LOG.md` |
| Phase 6 checklist (public) | `throughline/docs/PHASE_6_CHECKLIST.md` |
| Phase 6 risk mirror (private) | `S:\syncthing\obsidian_python\docs\THROUGHLINE_PHASE6_RISKS.md` |

## Credentials handling

- OpenRouter key rotated once in previous session. Current key visible in my context from a Read tool call on `C:\Users\Jprod\.tl_key` (file deleted after use). User's preference: use it for remaining Phase 6 runs without another rotation; user can re-rotate post-phase if desired.
- **Rule for next session:** if the key in Filter code history differs from the one in valves, user has rotated. Do NOT inline keys in user-visible commands; prefer `$env:OPENAI_API_KEY` via launchd/shell profile or pure-file-flow via `C:\Users\Jprod\.tl_key` with immediate `rm` after.

## Fixture calibration history (important — do not re-debug)

H1 went through two fixture versions because the initial fixture confused display-label `general` with JSON-value `auto`. Root-cause resolved. Calibrations per filter.py few-shot:

- **Line 1088-89:** no-anchor generic definition → `native`
- **Line 1091:** should-I/what-if (no anchor) → `brainstorm`
- **Line 1092:** explicit "decided …" → `decision`
- **Line 1094:** proxy-person ("my friend …") → `native`
- **Line 1095:** meta-self ("what's your …") → `native`

## Known English-only behavior gaps (accepted for v0.1.0)

1. **Brainstorm drift** — English "should we / what if / give me N ideas" classified as `native` instead of `brainstorm` by Haiku. Users must use `/recall` for explicit RAG. Ship as known limitation. (H1 B01/B02/B03)
2. **Bare-pronoun cheap-gate absent** — "it" / "that one" / "what about it" as first-turn inputs hit Haiku instead of being cheap-gated. Cost ~$0.003/turn. (H2 FT01-FT10)
3. **Thanks fix applied** — added "thanks / thank you / thx / ty / cheers" to `_NOISE_RE`. (filter/openwebui_filter.py:740-741)

## Pending work (overnight batch — all done)

1. ✅ H3 Haiku-side batch (31/31 PASS · $0.17)
2. ✅ H4 Sonnet subagent (15/16 PASS, 1 WARN)
3. ✅ Pytest wrappers (`test_phase6.py`, 21 passed + 10 xfailed)
4. ✅ EN fuzz probe pass (`fuzz_inlet.py` ported shape-only, 17/17 no-crash)
5. ✅ README Phase 6 public results section
6. ✅ Private-repo docs sync (THROUGHLINE_PHASE6_RISKS.md + CLAUDE.md + BUSINESS_ANALYSIS_ONEPAGER.md)
7. ✅ `docs/CHINESE_STRIP_LOG.md` populated with H1-H4 results
8. ✅ `PHASE6_OVERNIGHT_REPORT.md` written

## Ship-blocker status (2026-04-23)

All four pre-tag ship-blockers are green; `v0.1.0` is clear to tag.

- ✅ CJK + identity grep sweep (commit `68df132`): 3 leaks fixed (H1_ANALYSIS CN few-shot literals, SESSION_STATE RODC prose + CN column label, PHASE_6_CHECKLIST `non-RODC-persona`). Residual `rodc` tokens are all `jprodcc-rodc/throughline` GitHub URL / Copyright handle (tolerated per CHINESE_STRIP_LOG §whitelist) or inside CHINESE_STRIP_LOG itself (expected historical record).
- ✅ M4 cross-platform `point_id` determinism (commit `514aa26`): `fixtures/phase6/test_m4_point_id.py` 7/7 PASS — unit-test substitute for the operational Win+WSL diff check, pins `_norm_path` + `make_point_id` convergence + golden md5 values. Full Win+WSL live ingest remains as a post-tag nice-to-have.
- ⏳ Fresh-clone DEPLOYMENT.md walkthrough — deferred to Phase 7 dogfooding (alpha users). Not a pre-tag gate.

## Next actions (pick one)

**A. Tag v0.1.0 (ready now)**
   - `git tag v0.1.0 <sha>` — pick the commit, optionally sign/annotate
   - `git push origin v0.1.0`
   - Draft a GitHub release with the Phase 6 result table + accepted limitations
   - Estimated 10-15 min

**B. Phase 7 dogfooding prep**
   - Walk through `docs/DEPLOYMENT.md` as a fresh user (clean env, read-and-follow), log every stumble
   - Write `docs/ALPHA_USER_NOTES.md` with the friction points
   - Then invite 1-2 alpha users

**C. `[mech]`-class back-port from private repo**
   - `git -C S:\syncthing\obsidian_python log --grep='\[mech\]'` to find mech-level commits not yet in throughline
   - Hand-port each (no rebase/cherry-pick across repos; strip identity)
   - Run CHINESE_STRIP + identity scan after each port
   - Independent of A/B; any time

Recommendation: **A → B → C**. A gives a clean baseline tag for B to test against.

## Next session quick-start

```bash
# 1. Read this file first (continuity anchor)
# 2. Confirm no drift
cd C:\Users\Jprod\code\throughline
git log --oneline -10    # should show b0d8503 at tip, Phase 6 commits behind
git status               # should be clean

# 3. Start on next action A (ship-blocker sweep) unless user redirects
#    - CJK grep:      rg '[\u4e00-\u9fff]' --glob '!fixtures/**' --glob '!docs/CHINESE_STRIP_LOG.md'
#    - identity grep: use the private-side risk checklist for the full identity token list
#    - M4 point_id:   ingest same fixture vault on Win + WSL, diff qdrant point_id sets
```

## Phase roadmap ahead

- **Phase 6 (now):** Regression harnesses + results documented
- **Phase 7:** Private collaborator dogfooding (invite 1-2 alpha users)
- **Phase 8:** Public release v0.1.0 + HN Show post

---

_If reading this is the first thing you do in a new session: don't redo the fixture calibration — it's already correct. Start by checking background job outputs (H3 Haiku + H4 Sonnet) and continuing the overnight batch checklist above._
