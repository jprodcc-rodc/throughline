# Rodix → Rodspan Rename Execution Spec (v3)

> **Status:** LOCKED 2026-05-03 by Rodc post-brand-name-strategic-audit + post-Path-A product-strategy-lock.
> **Owner:** Rodc (Type-A) + Fresh Opus (strategy/coordinator) + CC (autonomous executor).
> **Wave 1c constraint:** Wave 1c shipped 2026-05-02 and is locked. This rename does NOT modify Wave 1c specs verbatim; it adds rename footers only. See §4.
> **Critical-path constraint:** Phase 1 alpha launch ETA 21–30 days. Wyoming LLC 6–8 week paperwork starting now. Rename must complete WITHOUT extending launch ETA.
> **Spec versioning:** v1 (initial draft) had fabricated quantitative claims and outdated TM database URLs (TESS retired Nov 2023). v2 fixed those. v3 adds product-category Path A lock + launch-blocking out-of-scope items + open strategic questions + sequencing dependency graph.

---

## §0 Decision lock + product category framing

### §0.1 Decided

Brand renames from Rodix → **Rodspan**.

### §0.2 Product strategy: Path A locked (CRITICAL — read before any rename action)

Two product paths existed at decision time. Rodc Type-A locked **Path A** 2026-05-03:

- **Path A (LOCKED):** User brings own API key; Rodspan provides chat client + memory layer; LLM cost = $0 to Rodspan. Pricing TBD ($5-10/month for memory feature, or buy-out, or OSS+donate). Direct competitor: **Cherry Studio**.
- ~~Path B (REJECTED):~~ Free trial + paid subscription with Rodspan covering API cost. Direct competitor would have been ChatGPT Plus / Claude Pro / Pi.

**Why this matters for rename:** Audit's +25% Rodspan-vs-Rodix margin holds under Path A category framing. Under Path B, the margin would have collapsed (Path B competes in LLM-provider category where empty-coined is base rate). Path A locks in Rodspan as correct rename target.

**Path B remains a possible Phase 2+ strategy pivot.** If pivoted to later, brand may need re-evaluation. Document in §13.

### §0.3 Product category framing

Rodix/Rodspan's product category is **LLM chat client** (alongside Cherry Studio / LobeChat / TypingMind / ChatBox / BoltAI / LibreChat / AnythingLLM / Chatwise / Pal Chat / Open WebUI / Msty / Faraday / Jan).

It is NOT:
- An LLM provider (ChatGPT / Claude / Gemini / Mistral / Llama / Pi / Grok / Perplexity category) — Rodspan does not serve a foundation model
- A memory infrastructure tool (throughline / mem0 / Letta / SuperMemory category) — Rodspan does not wrap other people's chat tools; it IS the chat tool

**Direct competitor benchmark: Cherry Studio.** Differentiator wedge: built-in memory layer (Cherry Studio has none) + user-facing app polish.

**Brand register implication:** "tool" engineering aesthetic per category convention (Cherry Studio / LobeChat / TypingMind compound names + minimal-to-functional UI), NOT "platform" abstraction (which LLM provider category uses with empty-coined names like Stripe / Notion / Linear). Rodspan's compound structure (Rod- + -span) fits the LLM-client category convention; Rodix's empty-coined structure was unconventional for this category.

This framing was clarified mid-audit (post-STOP-3.5) and is NOT fully reflected in `docs/superpowers/branding/name-audit/` artifacts, which were written under an earlier "memory layer" framing inherited from throughline (the predecessor self-hosted project at `https://github.com/jprodcc-rodc/throughline`). When fresh Opus or CC encounters language framing Rodspan as "memory layer" or "memory wedge into thinking" in audit artifacts, treat that as historical framing — the corrected framing is "LLM chat client with memory differentiator." All marketing rewrites in §2 must reflect the corrected framing.

### §0.4 Decision rationale (compressed for fresh-Opus pickup)

The brand-name-strategic-audit (`docs/superpowers/branding/name-audit/00-RECOMMENDATION-MEMO.md`) ran 76 candidates × 14 dimensions × 5 sensitivity weighting schemes. After Rodc-directed STOP-3.5 stress-test correction (rubric-overfit on `.com` weighting was challenged; empty-coined optionality was credited; rename cost honestly itemized; RØDE X penalty applied uniformly), Rodspan held rank 1 across all 5 schemes with +25% weighted margin over Rodix incumbent.

That +25% margin was computed under audit's "memory layer" framing. After product-category correction (§0.3) and Path A lock (§0.2), the margin moves favorably: in the LLM-client category Path A targets, compound-feature naming is base rate (Cherry Studio / LobeChat / TypingMind), so Rodspan's compound structure is MORE category-fit than Rodix's empty-coined structure. Audit's data conclusion holds; the framing reasoning underneath strengthened.

Material outperformance dimensions (≥1 point gap, post-stress-test): pronunciation transparency / spellability / cross-cultural EN-ICP / sound symbolism / voice fit / category positioning. The `.com` availability eliminates 5-year ops cost. RØDE X phonetic adjacency to rod-EX (which Rodix has) is severed.

Beyond data: Rodc surfaced `-dix` ending as *settled-for* outcome (preferred Rodex was named-out for direct RØDE X collision), and first-encounter reaction to Rodspan was "惊艳" (struck/impressed). Founder-conviction signal toward Rodspan, away from Rodix.

**Both "rename to Rodspan" and "Rodix retains" were defensible reads of the data per memo §7.** Rodc Type-A picked rename + Path A. This spec executes that decision.

**Additional architectural decision locked 2026-05-04 (post-F2 surfacing):** Rodspan SaaS + throughline OSS adopt the **Open Core model**. Throughline OSS (public, MIT) is the algorithm canon (mcp_server, throughline_cli, MCP server interface, single-user CLI). Rodspan SaaS (private rodspan-app repo) is the commercial product layer (UI, auth, billing, multi-user, cloud sync, premium memory features, polished UX). Rodspan SaaS imports throughline OSS as algorithm canon via sibling-repo PYTHONPATH (conftest.py mechanism). Three commitments accepted (see §15). This is the permanent architecture, not an interim arrangement.

### §0.5 Out of scope for this spec

- Re-debating the name (locked)
- Validating whether Rodspan beats other top-5 (locked — Rodspan over Rodkeep/Rodweave/Rodroot per Rodc Type-A)
- Re-running the audit under corrected category framing (the +25% conclusion holds; redoing the rubric is busy-work)
- Re-debating Path A vs B (locked Path A)
- Modifying Wave 1c specs verbatim (constraint)
- Modifying historical artifacts that document past state (audit reports, handoffs, dogfood rounds — see §2.3)
- **Launch-blocking work that this spec does NOT cover** — see §12

---

## §1 Validation gates

Two gates. **Gate 1 (TM) MUST pass before any rename action.** Gate 2 (pron test) is OPTIONAL per Rodc preference.

### §1.0 Pre-rename backup tags (DONE 2026-05-03 + 2026-05-04)

Two backup tags exist on origin remotes for rollback per §6 Risk 1/2/6/8.

**Tag 1 — throughline (public OSS):** `pre-rename-backup-2026-05-03` at commit `40c51af`. Captures docs/, audit artifacts, Wave 1c handoffs, dogfood verify, this spec, all OSS code (mcp_server/, throughline_cli/, fixtures/, etc.). Excludes app/ tree (gitignored at the time, since migrated to rodspan-app). Pushed to github.com/jprodcc-rodc/throughline.

**Tag 2 — rodspan-app (private SaaS):** `pre-rename-backup-2026-05-04-rodspan-app` at commit `4fbda2f`. Captures app/ tree before conftest.py was added. Pushed to github.com/jprodcc-rodc/rodspan-app.

Both tags are authoritative restore points. §A.1-A.5 + A.7-A.9 + Tier B + Tier C rollback uses Tag 1 (throughline). §A.6 rollback uses Tag 2 (rodspan-app post conftest.py commit 573a7ff).

### §1.1 Gate 1 — TM clearance (DIY without lawyer)

**Honest framing of what this sweep is and is NOT:**

This is a founder-level due-diligence sweep using public search tools that cover major jurisdictions where Rodspan would operate (US / EU / UK / Madrid international system, ~75 offices via TMview). It catches identical and obvious-similar marks in software-relevant classes.

It does NOT do:
- Phonetic-equivalent fuzzy search across all jurisdictions (paid attorney-grade fuzzy clearance costs €700–900 per EU sweep alone)
- Common-law unregistered TM searches in non-internet sources
- TTAB pending opposition / cancellation checks against pending applications
- Likelihood-of-confusion examination (the legal standard a USPTO examiner applies)
- Non-Latin transliteration sweeps (e.g., Cyrillic / CJK variants)

A bona fide cease-and-desist or USPTO refusal could still arise from marks this sweep misses. **Without a lawyer, residual risk is unquantified — we do not claim a percentage of lawyer-grade coverage because we have no data to support such a claim.** Rodc proceeds with this knowledge per §6 Risk 1.

**Databases to query (verified URLs as of 2026-05-03; CC verifies each loads before sweep begins):**

| # | Database | URL | Coverage | Query semantics |
|---|---|---|---|---|
| 1 | **TMview (EUIPN-hosted, multi-jurisdiction aggregator)** | `https://www.tmdn.org/tmview/` | ~75 offices including EUIPO + all EU national IPOs + USPTO + UK IPO + Madrid/WIPO international + non-EU partners (~60M marks) | Exact-match "Rodspan" + variants: "Rod Span", "Rod-Span", "RodSpan". Single sweep replaces individual national queries. |
| 2 | **USPTO Trademark Search (replaced TESS Nov 2023)** | `https://tmsearch.uspto.gov/` | US federal — primary jurisdiction for Rodc (Wyoming LLC) | Use "Basic search" or "Advanced search". Note: search syntax changed from old TESS — uses RegEx field tags now. Query `Rodspan` exact and `ROD*` wildcard in Class 42 + Class 9. |
| 3 | **WIPO Global Brand Database** | `https://branddb.wipo.int/` | Madrid international (overlaps with TMview but more current for very recent filings) + national collections | **Note: WIPO TOS explicitly disallows automatic/bulk querying.** Rodc or CC must do manual browser-style queries, no scripts. |
| 4 | **Wyoming Secretary of State Business Filing Search** | `https://wyobiz.wyo.gov/business/filingsearch.aspx` | Wyoming state business name registry — NOT a TM check, but blocks LLC name registration | Search "Contains: Rodspan" (per Wyoming guide: use "Contains" not "Starts With" to catch filler-word variants). |
| 5 | **Common-law sweep — search engines** | Google direct — `"Rodspan"` site searches across `.com .app .io .co` and quoted bare-name results | Catches active commercial use of the literal name in software/SaaS | Free-form. Active commercial use = STOP. Inactive personal use = FLAG. |
| 6 | **Common-law — developer registries** | `https://www.npmjs.com/search?q=rodspan` + `https://github.com/search?q=rodspan&type=repositories` + `https://pypi.org/search/?q=rodspan` | Catches active package/repo with same name in software space | Active package > 1k weekly downloads or repo > 1k stars in same space = soft STOP for Rodc evaluation. |
| 7 | **Domain WHOIS (already verified in audit 2026-05-03)** | `https://porkbun.com/checkout/search?q=rodspan` (or whois CLI) | `rodspan.app` `rodspan.com` `rodspan.dev` | Already CLEAR. Rodc must complete checkout immediately (§3 step 1) before further sweep activity. |

**Trademark class scope (Nice Classification, verified per USPTO ID Manual + Gerben IP guidance):**

| Class | Description | Rodspan relevance | Verdict on hit |
|---|---|---|---|
| **42** | Software-as-a-service (SaaS), non-downloadable software, design and development of computer software | **PRIMARY** — Rodspan web product is SaaS | LIVE mark in 42 with software ID = STOP |
| **9** | Downloadable software, mobile apps, electronic devices | **SECONDARY** — Phase 2+ if native iOS/Android app ships | LIVE mark in 9 with software/app ID = STOP |
| **38** | Telecommunications, internet services | **COMPANION** — sometimes covers chat services | LIVE mark in 38 = FLAG-and-evaluate |
| 35 | Advertising, business management | **NOT** a primary class for Rodspan | LIVE mark in 35 = FLAG-only (low overlap) |
| 41 | Education, entertainment, online services | **NOT** primary | LIVE mark in 41 = FLAG-only (low overlap) |

**Per Gerben IP guidance and standard practice for software TM searches:** check classes 9 + 42 jointly as a pair, plus 38 as a companion class. As a sanity check, CC should attempt to verify what Cherry Studio / TypingMind / LobeChat actually registered under (if at all) via TMview — if their actual registration is in different classes, update the STOP list before sweep.

**Output:** `docs/superpowers/branding/name-audit/06-tm-sweep-results.md` listing every query, raw response excerpt (1–2 lines), verdict (CLEAR / FLAG / STOP), and the date the database was queried.

**Decision rule:**
- All CLEAR → proceed to §2 rename
- Any FLAG → fresh-Opus + Rodc review the FLAG, decide proceed/stop based on adjacency severity (e.g., a Rodspan TM in class 7 heavy-machinery is FLAG-but-proceed; one in class 42 software/SaaS is STOP)
- Any STOP → halt rename; surface to Rodc for re-decision (alternatives: choose Rodkeep #2 from audit, or hold Rodix)

**Duration:** unknown until first sweep. CC should target a single afternoon. If any database is unreachable or query interface is JS-heavy and CC's web-fetch can't render it, see §11 blocked-state escalation. Do NOT fabricate "checked" results.

### §1.2 Gate 2 — Pronunciation test (OPTIONAL, Rodc-skipped)

Rodc skipped per session conversation: visceral first-impression "惊艳" passed internal gate; audit dim 5 = 4.5/5; a 5-person blind test would not change Rodc's Type-A.

If Rodc reverses and wants the test before committing: post 5 sample English-native speakers a single text "rodspan", ask them to record pronouncing it. Pass condition: ≥4 of 5 produce rod-SPAN with stress on the first syllable on first read.

---

## §2 CC autonomous rename scope (214-file inventory)

Categorized into three tiers. Tier A blocks launch; Tier B blocks polish; Tier C is historical record (do NOT modify, only annotate).

**Naming convention applied throughout:**
- "Rodix" → "Rodspan"
- "rodix" → "rodspan"
- "RODIX" → "RODSPAN"
- "rodix.app" → "rodspan.app"
- "rodix.com" → "rodspan.com"
- "rodix.dev" → "rodspan.dev"
- "@rodix" → "@rodspan"
- "rodix-app" (GitHub org) → "rodspan-app"
- "rodix_system.md" → "rodspan_system.md" (file rename)
- "rodix-design-system" (skill directory) → "rodspan-design-system" (directory rename)
- "rodix-friends-intro.md" → "rodspan-friends-intro.md" (file rename + content regenerate, see §4.2)

**CC commit discipline (mandatory):** one logical change per commit. File rename + find-replace inside that file = one commit. Multi-file batched commits ONLY when the files form an atomic unit (e.g., a JSON schema + its consuming code). This isolates rollback per §6 Risk 2.

**CC must NOT blind-replace in code without re-running tests after each commit affecting code paths (§A.6).**

**Effort estimate disclaimer:** CC's per-file throughput on this codebase is not measured. The ranges below are rough planning numbers, not commitments. CC measures actual throughput on the first 3 files in §A.1 and surfaces the calibrated estimate to fresh Opus before continuing.

### §2.0 Sequencing dependency graph

CC must respect this dependency graph. NOT all sub-tiers can run in parallel.

```
A.1 brand foundation ──┬──> A.2 friends-intro ──> A.3 marketing ──> A.4 user copy
                       │                                              │
                       │                                              v
                       ├──> A.5 legal                               (Tier A done if all green)
                       │
                       ├──> A.6 system + code (parallel-safe; runs independently)
                       │
                       ├──> A.7 design-system (parallel-safe)
                       │
                       ├──> A.8 memory files (parallel-safe)
                       │
                       └──> A.9 specs (parallel-safe)

NOTE: A.2 friends-intro is canonical voice oracle and BLOCKS A.3 marketing per §4.2.
NOTE: A.6 must complete + pytest pass + Wave 1c verify before §3 Day-3+ self-dogfood.
NOTE: §3 manual ops sequenced separately - see §3.
```

**CC must NOT start A.3 before A.2 is locked (Rodc-reviewed friends-intro).** Wrong order = marketing copy conflicts with new voice oracle.

**A.6 (code) can run in parallel with A.1/A.2/A.3** because code does not import brand artifact files. This parallelism is encouraged to reduce calendar.

### §2.1 Tier A — Brand-critical, must rename before launch

#### A.1 — Brand foundation (8 files)

These are the canonical brand artifacts; rename is largely find-replace BUT each file requires a semantic-coherence re-read because some sentences hinge on the word `Rodix` being meaning-empty. Those sentences need rewrite to reflect that Rodspan IS semantically loaded (span = continuity-across-time, fits LLM-client category convention).

**Critical for §0.3 framing carry-through:** when re-reading these files for semantic coherence, also check for the older "memory layer" framing (inherited from throughline). Rewrite to "LLM chat client with memory differentiator" framing under Path A. This is a semantic rewrite, not a find-replace.

| File | Action |
|---|---|
| `docs/superpowers/brand/brand-book-v1.md` (~7233 words) | Find-replace + semantic re-read of §1 (name etymology), §3 (positioning vs Cherry Studio explicit), §4 (archetype if Rodspan vs Rodix shifts read), §7b (button label fix — see §4.5) |
| `docs/superpowers/brand/voice-guide.md` (~3403 words) | Find-replace + verify §5 voice samples don't have Rodix-specific sentence constructions |
| `docs/superpowers/brand/position-strategy.md` (~5202 words) | Find-replace + verify category-positioning logic still holds; update competitor framing if it referenced wrong category (LLM-provider instead of LLM-client) |
| `docs/superpowers/brand/archetype-analysis.md` | Find-replace + verify Explorer+Everyman archetype reads still apply (they do; Rodspan slightly stronger Explorer evocation) |
| `docs/superpowers/brand/founder-narrative-arc.md` (~1942 words) | Find-replace + verify Escalation #4 "rough notes" carry-forward still pending; do NOT auto-resolve |
| `docs/superpowers/brand/decisions.md` | Find-replace + add new decision-log entry: "2026-05-03 — renamed Rodix → Rodspan per audit memo + product category corrected to LLM-client wedge + Path A locked (user-BYO-API)" |
| `docs/superpowers/brand/review-notes.md` | Find-replace |
| `docs/superpowers/brand/research-notes.md` | Find-replace |

**Brainstorm-based variants (working copies):** `archetype-analysis-brainstorm-based.md`, `brand-book-v1-brainstorm-based.md`, `position-strategy-brainstorm-based.md`, `review-notes-brainstorm-based.md`, `voice-guide-brainstorm-based.md`, `narrative-research.md`, `narrative-skeptic-notes.md`, `founder-narrative-arc-draft.md` — apply find-replace, no semantic re-read; lower priority.

#### A.2 — Voice oracle (1 file, special handling)

| File | Action |
|---|---|
| `docs/rodix-friends-intro.md` (~1350 words) → rename to `docs/rodspan-friends-intro.md` | **Regenerate from scratch using Rodspan-aware semantic anchor + corrected product category framing + Path A locked.** NOT find-replace. See §4.2 process. |

This file is `voice-guide.md` §5's reference oracle. Per voice-guide, friends-intro is canonical voice source — if it conflicts with anything else, friends-intro wins. So getting this right is prerequisite to A.3 marketing.

**Audience for friends-intro (Rodc-locked 2026-05-03):** primary = Cherry Studio / LobeChat / TypingMind users (who don't know Rodc or throughline; need Path A wedge framing); secondary = friend cohort already invited to alpha (founder-note register). Mix per Q2=E. Voice should serve Cherry-Studio-adjacent power user primarily, friend cohort secondarily. CC drafts for primary; Rodc reviews secondary register fit.

#### A.3 — Marketing & launch package (15 files)

**BLOCKED until A.2 locked.** Friends-intro is voice oracle; marketing prose must reflect that.

| File | Action |
|---|---|
| `app/web/static/landing/index.html` | Find-replace + render-test in browser (visual verification) |
| `docs/superpowers/marketing/landing-deliverable/index.html` | Find-replace |
| `docs/superpowers/marketing/landing-copy-v1.md` | Find-replace + verify hero copy semantic + check for "memory layer" framing → rewrite to "LLM chat client with memory" + Cherry Studio explicit comparison |
| `docs/superpowers/marketing/landing-decisions.md` | Find-replace |
| `docs/superpowers/marketing/landing-research.md` | Find-replace |
| `docs/superpowers/marketing/founder-essay-draft.md` (~1425 words) | Find-replace + semantic re-read of name-introduction paragraph + product framing |
| `docs/superpowers/marketing/hn-launch-post.md` (~595 words) | Find-replace + verify first-line opener (Rodspan-vs-Rodix HN reception will differ); explicit competitor framing vs Cherry Studio recommended |
| `docs/superpowers/marketing/twitter-launch-thread.md` (8 tweets) | Find-replace + verify 280-char limits hold (Rodspan is 1 char longer than Rodix) |
| `docs/superpowers/marketing/launch-video-script.md` | Find-replace + verify pronunciation cue notes |
| `docs/superpowers/marketing/ph-launch-package.md` | Find-replace |
| `docs/superpowers/marketing/marketing-decisions.md` | Find-replace |
| `docs/superpowers/marketing/voice-research.md` | Find-replace |
| `docs/superpowers/marketing/voice-consistency-review.md` | Find-replace |
| `docs/superpowers/marketing/landing-deliverable/screenshots/README.md` | Find-replace |
| `app/web/static/landing/screenshots/README.md` | Find-replace |

**Two landing directories (`app/web/static/landing/` vs `docs/superpowers/marketing/landing-deliverable/`):** CC must `diff` the two index.html files before find-replace. If content differs (beyond brand name), surface to Rodc — there's a sync gap that should be resolved before rename.

#### A.4 — User-facing copy (12 files)

| File | Action |
|---|---|
| `docs/superpowers/copy/welcome.md`, `how-it-works.md`, `faq.md`, `privacy-summary.md`, `getting-started.md`, `copy-review-notes.md` | Find-replace |
| `docs/superpowers/copy-deliverable/welcome.md`, `how-it-works.md`, `faq.md`, `privacy-summary.md`, `getting-started.md`, `copy-review-notes.md` | Find-replace |
| `docs/superpowers/copy-deliverable/empty-states.json` | Find-replace + JSON-validate |
| `docs/superpowers/copy-deliverable/errors.json` | Find-replace + JSON-validate |
| `app/web/static/copy/empty-states.json` | Find-replace + JSON-validate |
| `app/web/static/copy/errors.json` | Find-replace + JSON-validate |

#### A.5 — Legal (5 files)

| File | Action |
|---|---|
| `docs/superpowers/legal/privacy-policy-draft.md` | Find-replace + verify §5/§12/§20 ZDR placeholders unchanged (separate Anthropic ZDR question still pending). **Path A note:** since user brings own API key, "data routing through Anthropic" framing changes — user is direct Anthropic customer for their key, Rodspan is not the data processor for LLM calls. Privacy Policy must reflect this. |
| `docs/superpowers/legal/terms-of-service-draft.md` | Find-replace + add Path A clause: user retains responsibility for their own API key TOS compliance |
| `docs/superpowers/legal/legal-decisions.md` | Find-replace + log Rodspan rename + Path A as new decisions |
| `docs/superpowers/legal/legal-research.md` | Find-replace |
| `docs/superpowers/legal/legal-review-notes.md` | Find-replace |

#### A.6 — System prompt + code core (HIGHEST risk subset)

**CRITICAL: §A.6 runs in `C:/Users/Jprod/code/rodspan-app/` (private repo), NOT in `C:/Users/Jprod/code/throughline/`.** Per Open Core split (§4.4) on 2026-05-04, app/ tree migrated to private rodspan-app. Throughline/ no longer contains app/ files. CC must `cd C:/Users/Jprod/code/rodspan-app/` before any §A.6 file action.

**Pre-rename baseline (regression target): 645 passed, 2 skipped, 0 failed** (measured in rodspan-app at commit 573a7ff with conftest.py providing throughline sibling import). Run pytest after every file change in §A.6 — if pass count drops, immediately `git revert` the commit.

**Backup tag for rollback:** `pre-rename-backup-2026-05-04-rodspan-app` at commit 4fbda2f (pushed to origin private repo). This tag captures app/ tree state before conftest.py was added; the conftest.py commit 573a7ff is the actual §A.6 starting point.

Wave 1c shipped on Rodix prompt strings. Rename must NOT regress test suite.

**Mandatory baseline measurement before A.6 begins:** CC runs `pytest` and records exact pass/skip/fail count. This becomes the regression target. Do not assume the handoff's "443 + 2 skipped + 16 safety + 2 schema" number is current — measure it.

**A.6 must include audit step for non-text "rodix" references:**

Before any A.6 file find-replace, CC runs:
```bash
cd C:/Users/Jprod/code/throughline
grep -rn "rodix" --include="*.py" --include="*.json" --include="*.toml" --include="*.yaml" --include="*.yml" --include="*.cfg" --include="*.env*" --include="Dockerfile" .
```

For each hit, classify:

| Hit type | Example | Decision |
|---|---|---|
| Brand-string in docstring / comment | `# Rodix loads system prompt...` | Rename per convention |
| **Env variable name** | `RODIX_OPENROUTER_KEY` | **Surface to Rodc** — env rename is breaking change for Rodc's local dev shell + any CI |
| **Config key** | `rodix_api_url` in `.toml`/`.yaml` | **Surface to Rodc** — config rename invalidates current `~/.rodix/config.toml` if exists |
| **DB schema field** | `rodix_user_id` in migration / model | **Surface to Rodc** — DB column rename = migration script + existing data risk |
| **localStorage / cookie / sessionStorage key** | `localStorage.getItem('rodix_session')` | **Surface to Rodc** — key rename logs out current session(s); if zero existing users it's free, otherwise needs migration shim |
| **API endpoint path** | `/api/rodix/cards` | **Surface to Rodc** — path rename breaks any client bookmarks/scripts |
| **Filesystem path string** | `~/.rodix/` or `~/Documents/Rodix/` | **Surface to Rodc** — see §4.6 vault data migration |

**CC must NOT blind-rename any of the surfaced categories without explicit Rodc unblock.** These are breaking changes whose blast radius depends on existing usage CC cannot see.

| File | Action | Test verification |
|---|---|---|
| `app/web/prompts/rodix_system.md` → **rename to `rodspan_system.md`** | `git mv` + content rename + grep for any importer that hardcodes path | Run full app/ test suite |
| `app/web/server.py` | Find-replace; check for any string-literal references to filename `rodix_system.md` and update to `rodspan_system.md`; check API endpoint paths | `pytest app/web/test_server.py` |
| `app/web/test_server.py` | Find-replace | Run after server.py update |
| `app/shared/intent/classifier.py` | Find-replace; check whether classifier loads system prompt explicitly | `pytest app/shared/intent/test_classifier.py` (16 safety tests must pass) |
| `app/shared/intent/test_classifier.py` | Find-replace |  |
| `app/shared/intent/__init__.py` | Find-replace |  |
| `app/shared/extraction/extractor.py` | Find-replace; confirm Wave 1c R1/R2 rules untouched in semantic content |  |
| `app/shared/extraction/extraction_queue.py` | Find-replace |  |
| `app/shared/extraction/test_extractor_integration.py` | Find-replace |  |
| `app/shared/secrets/key_storage.py`, `test_key_storage.py`, `__init__.py` | Find-replace + check if env var name `RODIX_*` exists; surface |  |
| `app/shared/storage_py/vault_path.py`, `test_vault_path.py` | Find-replace + **CRITICAL: surface vault path string to Rodc per §4.6** | Run vault tests |
| `app/shared/storage_py/fixtures/cards/fixture_few.json`, `fixture_medium.json` | Find-replace + JSON-validate |  |
| `app/web/test_cards_api.py`, `test_chat_placeholder.py`, `test_settings.py` | Find-replace |  |
| `app/scratch/wave1c_phase3_verify.py` | Find-replace; this is the Phase 3 verification harness |  |
| `fixtures/v0_2_0/eval/intent_cases.json`, `run_intent_eval.py` | Find-replace |  |

**CC must run pytest after each file in A.6.** If pass count drops, `git revert` immediately and isolate.

After all A.6 files complete + test suite green, CC runs `app/scratch/wave1c_phase3_verify.py` (renamed) once against real OpenRouter. Expected verdict: same as 2026-05-02 baseline (4/5 PASS + 1 WEAK on Emma classifier-layer with downstream chat self-correction). Cost ~$0.01. If verdict differs, surface to fresh Opus before proceeding.

#### A.7 — `.claude/skills/rodix-design-system/` directory rename (with content audit)

**This is more than directory rename.** The skill is a design system with 7 files. CC must audit content before declaring rename complete.

| Step | Action |
|---|---|
| 1 | `git mv .claude/skills/rodix-design-system/ .claude/skills/rodspan-design-system/` |
| 2 | For each file, find-replace "rodix" → "rodspan" |
| 3 | **Content audit per file:** read each, surface to Rodc anything that's: (a) Rodix-themed visual concept that needs Rodspan re-conception, (b) color tokens picked for Rodix register that may not fit Rodspan, (c) illustration style around Rodix metaphor |
| 4 | JSON-validate `visual-tokens.json` post-rename |
| 5 | Update any `.claude/skills/index` or skill-loader if it hardcodes the path; verify CC can still load the skill post-rename |

**Files in skill (audit each):**
- `SKILL.md` — usage instructions
- `component-patterns.md` — UI component patterns
- `illustration-guide.md` — illustration style
- `microcopy-patterns.md` — UI microcopy patterns
- `sample-passages.md` — example brand prose
- `visual-tokens.json` — colors/typography/spacing tokens
- `voice-guide.md` — secondary voice reference

**Surface to Rodc as STOP if any file describes visual identity (logo / wordmark / illustration metaphor) that is Rodix-conceptual and not generic.** Visual identity for Rodspan is launch-blocking out-of-scope per §12. CC should not unilaterally decide what Rodspan's visual identity is.

#### A.8 — `.claude/projects/.../memory/` files

CC's persistent memory across sessions; outdated names will confuse future CC.

| File | Action |
|---|---|
| `MEMORY.md` | Find-replace + add new entry: "2026-05-03 brand renamed Rodix→Rodspan; product category clarified as LLM chat client (Cherry Studio competitor); Path A locked (user-BYO-API)" |
| `project_rodix_name.md` → rename to `project_rodspan_name.md` | Rename + content rewrite (this file recorded the *old* name decision; now records the rename decision history) |
| `reference_rodix_system_prompt.md` → rename to `reference_rodspan_system_prompt.md` | Rename + content rename |
| `feedback_cc_self_verify.md`, `feedback_design_judgment_failures.md`, `project_app_state_2026_05_01.md`, `project_app_state_2026_05_02.md`, `project_app_state_2026_05_03.md`, `project_device_priority.md`, `reference_product_test_scenarios.md`, `reference_test_state_leak_pattern.md`, `reference_ux_skill.md` | Find-replace; these are working memory, low-stakes |

#### A.9 — Tasks & specs not in Wave 1c lock (5 files)

| File | Action |
|---|---|
| `docs/superpowers/tasks/brand-name-strategic-audit.md` | Find-replace within prose only. Header note added: "This task spec was the input that produced the Rodspan rename. Original references to Rodix as benchmark are preserved in audit artifacts (`docs/superpowers/branding/name-audit/`)." |
| `docs/superpowers/specs/marketing-site-design.md` | Find-replace |
| `docs/superpowers/specs/web-product-design.md` | Find-replace |
| `docs/superpowers/specs/2026-05-01-rodix-brainstorm.md` → rename to `2026-05-01-rodspan-brainstorm.md` | Rename file + content |
| `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` → rename to `2026-05-01-rodspan-product-test-scenarios.md` | Rename file + content |

### §2.2 Tier B — Secondary, rename before public docs sweep

Lower stakes than Tier A; bulk find-replace with JSON-validate where applicable.

#### B.1 — Plans (15 files)

`docs/superpowers/plans/2026-05-01-1a-settings-panel.md`, `2026-05-01-2a-onboarding-skeleton.md`, `2026-05-01-3a-cards-management.md`, `2026-05-01-5-visual-polish.md`, `2026-05-01-8-placeholder-ui.md`, `2026-05-01-9a-history-import.md`, `2026-05-01-b-dev-deploy.md`, `2026-05-01-claim-extraction.md`, `2026-05-01-intent-classifier.md`, `2026-05-01-rodix-roadmap.md` → rename to `2026-05-01-rodspan-roadmap.md`, `2026-05-03-wave2.md`, `2026-05-XX-wave3.md`, `wave2-review-notes.md`

Plus wave2 specs: `wave2/spec-active-recall-base.md`, `spec-card-dedup.md`, `spec-card-real.md`, `spec-first-insight.md`, `spec-vault-recall-history.md`

Plus wave3 specs: `wave3/spec-b-auth.md`, `spec-b-deploy.md`, `spec-b-paddle.md`, `spec-b-privacy-policy.md`, `spec-b-security-review.md`

#### B.2 — Business (8 files)

`acquisition-research.md`, `acquisition-strategy.md`, `competitor-pricing.md`, `funnel-model.md`, `llm-cost-real.md`, `pricing-brand-aligned.md`, `pricing-model.md`, `pricing-strategy.md`

**Note:** `competitor-pricing.md` likely needs framing correction — Cherry Studio (free) / TypingMind ($39 buy-out) / LobeChat (free) are correct Path A competitors; ChatGPT Plus / Claude Pro are NOT direct competitors per §0.3. Also: `llm-cost-real.md` may need significant rework — under Path A, Rodspan does NOT cover LLM cost, so the cost model framing changes.

#### B.3 — Research (5 files)

`assumption-list.md`, `launch-readiness-criteria.md`, `mom-test-checklist.md`, `recruit-strategy.md`, `user-interview-script.md`

#### B.4 — Observability (4 files)

`alerting-rules.md`, `cost-cap-design.md`, `observability-spec.md`, `privacy-aware-logging.md`

**Note:** `cost-cap-design.md` may be Path-B-flavored; under Path A user pays own LLM cost so caps are user-side concern, not Rodspan ops concern. CC surfaces if framing reads wrong.

#### B.5 — Skills support (2 files)

`docs/superpowers/skills/scenario-reviewer-prompt.md`, `scenario-verification.md`

#### B.6 — Brainstorm HTML (8 files in `.superpowers/brainstorm/`)

Early UI brainstorm sketches. Find-replace + verify HTML still renders. Lower priority — not user-facing.

`02-design-language-rodix.html`, `04-info-architecture.html`, `06-settings-panel.html`, `07-what-i-just-saved-revisit.html`, `08-onboarding-shape.html`, `11-ia-redo.html`, `14-onboarding-step2-c-improved.html`, `19-visual-polish.html`

#### B.7 — Vault state (2 files)

`docs/superpowers/dogfood/vault-state.md`, `vault-state-verification.md` — state captures, not historical transcripts. Find-replace.

### §2.3 Tier C — Historical record, DO NOT MODIFY

Dated records of past state. Modifying them rewrites history. Instead, **add a single header annotation** and leave content untouched.

**Annotation template (add to top of each file as a single line under existing header):**
```
> **Note 2026-05-03:** Brand renamed Rodix → Rodspan. This file is a historical record from prior to the rename and retains the original "Rodix" name as written at the time. See `docs/superpowers/tasks/rodix-to-rodspan-rename.md` for context.
```

#### C.1 — Audit artifacts (10 files) — DO NOT MODIFY content

`docs/superpowers/branding/name-audit/00-RECOMMENDATION-MEMO.md`, `01-candidates.md`, `02-gate-results.md`, `03-strategic-evaluation.md`, `05-decision-matrix.md`, `cost-log.md`, `methodology-notes.md`, `time-log.md`, `04-finalists/00-rodix-dossier.md`, `01-rodspan-dossier.md`, `02-rodkeep-dossier.md`, `03-rodweave-dossier.md`, `04-rodroot-dossier.md`

Annotate top of `00-RECOMMENDATION-MEMO.md` with rename outcome AND with §0.3 framing-correction note + Path A lock note. Other files: leave unmodified entirely.

#### C.2 — Wave 1c specs LOCKED (2 files) — annotation only

`docs/superpowers/specs/2026-05-03-wave1c.md`, `2026-05-03-wave1c-type-a-decisions.md`

Add annotation at top: "Wave 1c shipped 2026-05-02 on the Rodix name. Brand renamed to Rodspan 2026-05-03. The shipped behavior and verdicts in this spec are unchanged; future readers should mentally substitute Rodspan for Rodix when reasoning about post-2026-05-03 product behavior."

#### C.3 — Tier handoffs (7 files) — DO NOT MODIFY

`docs/superpowers/_state/handoffs/2026-05-03-tier-0-handoff.md`, `tier-1-handoff.md`, `tier-1.5-handoff.md`, `tier-2-handoff.md`, `tier-3-handoff.md`, `wave1c-handoff.md`, `2026-05-04-wave1c-resume-handoff.md`

Annotate top; do not modify content.

#### C.4 — Tonight summaries (5 files) — DO NOT MODIFY

`docs/superpowers/tonight/escalations.md`, `final-chat-summary.md`, `reusable-patterns.md`, `strategic-memo.md`, `task-summaries/0a-summary.md`, `0b-summary.md`, `0c-summary.md`, `1-summary.md`

Annotate top; do not modify.

#### C.5 — Dogfood rounds (~80 files) — DO NOT MODIFY

`docs/superpowers/dogfood/personas/*-bible.md`, `*-conversation-history.md`, `*-life-arc.md`, `*-state-journal.md`, `*-summary.md`, `*-lens-analysis.md` (4 personas × 6 files = 24)

`docs/superpowers/dogfood/rounds/{daniel,emma,mike,sarah}-round-{01..12}.md` (4 personas × 12 rounds = 48)

`docs/superpowers/dogfood/analysis/cross-persona-patterns.md`, `quality-redflags.md`, `sarah-day-15-special-analysis.md`, `unexpected-insights.md`, `wave2-spec-validation.md`

`docs/superpowers/dogfood/sample-verify/calibration-report.md`, `round-mike-08-real-vs-simulated.md`, `sarah-day-15-real-api-verdict.md`, `wave1c-verdict.md`

`docs/superpowers/dogfood/rodc-handoff.md`

Historical evidence — modifying invalidates the evidence. Annotate the top of each persona's bible file (4 files); do not annotate every round.

#### C.6 — Other historical (3 files)

`docs/superpowers/2026-05-01-session-handoff.md` — annotate top
`docs/superpowers/_state/rodc-context.md` — annotate top + add new line "2026-05-03: brand renamed Rodix → Rodspan; product category clarified as LLM chat client; Path A locked (user-BYO-API)" but preserve historical text
`docs/superpowers/copy-deliverable/empty-states.json`, `errors.json` — already in §A.4

---

## §3 Rodc manual ops

CC cannot do these. Sequenced by what blocks what.

### Day 0 (today, 2026-05-03)

1. **URGENT — Porkbun checkout `rodspan.app` + `rodspan.com` + `rodspan.dev`** (~30 min, ~$50)
   - Audit artifacts already commit "Rodspan" name to repo. **Per Q5=A, throughline OSS repo at `https://github.com/jprodcc-rodc/throughline` is public, so domain sniping window is open.** Domain checkout BEFORE Gate 1 launch.
   - Original Rodix Porkbun cart (rodix.app + rodix.dev, ~$28, stuck on HSTS preload notice) — abandon. The $28 sunk is part of rename cost.
   - Skip `rodspan.chat` per prior decision.

2. **OpenRouter old key revoke** (5 min)
   - Per Escalation #1 in `docs/superpowers/tonight/escalations.md` (leaked-key cleanup deferred from prior wave). Revoke old key; issue new.
   - Independent of rename, but bundled here as immediate Day-0 item.

### Day 0–1 (after Gate 1 TM sweep CLEAR)

3. **Wyoming LLC paperwork — `Rodspan LLC`** (~$275 first year + ~$150 EIN service if used; ~1h Rodc + 7-14 day processing)
   - Verify `Rodspan LLC` available in `https://wyobiz.wyo.gov/business/filingsearch.aspx` (Gate 1 sweep already includes this)
   - Registered agent: `wyomingregisteredagent.com` $25/yr
   - File Articles of Organization at `https://wyobiz.wyo.gov/business/registrationtype.aspx`, $100 fee
   - EIN via Form SS-4 fax to IRS (+1-855-641-6935) for non-US founder, 4-6 weeks; or Northwest $150 service
   - Mercury bank account once EIN issued

4. **Email Anthropic re ZDR** (10 min, 1-3 day reply)
   - Independent of rename; blocks Privacy Policy §5/§12/§20.
   - **Path A note:** since user brings own API key, ZDR may apply differently — Anthropic ZDR is between user and Anthropic, not Rodspan and Anthropic. Re-frame question accordingly.

### Day 1–3 (after CC Tier A complete, code + brand + marketing verified)

5. **Twitter `@rodspan`** (15 min)
   - Anonymous account, voice per voice-guide §5 (post-A.2 regenerate)
   - Skip `@rodix` registration entirely (was in plan, never executed).
   - **Rodc-handle relationship:** `@rodc` (founder) and `@rodspan` (product) — separate accounts, different audience. `@rodc` posts founder-narrative + dev-log; `@rodspan` posts product-launch + feature + support. Cross-link.

6. **GitHub org `rodspan-app`** (per Q5=A: keep `jprodcc-rodc/throughline` repo as OSS predecessor; create separate `jprodcc-rodc/rodspan-app` PRIVATE repo for Rodspan SaaS code)
   - Per Q5: Path is "(a) keep current `jprodcc-rodc/throughline` repo as OSS, new `rodspan` private repo".
   - **Implication for §A.6 code rename:** code is currently in `~/code/throughline/` Windows path which corresponds to public `jprodcc-rodc/throughline`. After Path A locks AND domain checkout completes, Rodc must decide migration path:
     - (i) Move Rodspan code to new private repo `rodspan-app`; keep throughline repo as OSS-only with original throughline code (which may be different from Rodspan code)
     - (ii) Keep all code in throughline repo; mark Rodspan-specific files private via .gitignore + separate deployment
     - (iii) Fork throughline → rodspan-app, develop Rodspan in fork, throughline stays as upstream OSS
   - **This is launch-blocking.** Spec does not pre-decide migration path; surface to fresh Opus + Rodc as blocker for §3 step 6.

7. **Porkbun `hi@rodspan.app` email forwarding** (15 min)
   - Standard Porkbun setup post-domain-checkout.

### Day 3–5 (after CC Tier A complete + verified)

8. **Self-dogfood 5 rounds with `RODSPAN_DEV=1`** (~5h Rodc, per `docs/superpowers/dogfood/rodc-handoff.md` after rename)
   - Verifies the renamed system end-to-end before friend dogfood.
   - **Per Q4: Rodc has not personally run real dogfood yet (CC simulated all prior dogfood).** This step is the FIRST real-API run by Rodc. Vault data starts from zero. No migration concern (per §4.6 below).
   - **Dogfood objective explicit:**
     - (a) Verify rename did not break system end-to-end (chat + extract + vault + active-recall flows all work post-rename)
     - (b) Verify LLM voice fits Rodc's first-person experience (per §5 LLM self-reference manual review)
     - (c) Surface anything broken about Cherry-Studio-aware framing in chat / extraction / cards copy
     - (d) Calibrate Rodc's mental model of how Rodspan responds to actual Rodc inputs (audit was synthetic personas)

### Day 5–7 (parallel with Tier B)

9. **Friend dogfood pre-launch 5–7 days** (Escalation #8) — identify reviewer Rodc trusts.
   - **Per Q4: zero prior friend cohort exposure to Rodix, so no rename communication needed.** Friends meet "Rodspan" fresh.

10. **Termly Privacy Policy generation** (~30 min Rodc)
    - After Anthropic ZDR confirmation.
    - **Path A note:** since user brings own API key, Privacy Policy framing changes. User is direct Anthropic customer for their key; Rodspan stores card data + vault data only.

11. **Friend Privacy Policy review** (~1–2 days)

### Pre-launch (week 3, target ~21–30 days from now)

12. **Paddle merchant application — `Rodspan LLC`** (5–7 day approval)
    - After domain + LLC ready.
    - **Path A note:** Paddle merchant for Rodspan subscription only; NOT a payments processor for user's API spend. User's API spend goes direct to OpenRouter / Anthropic / OpenAI.

13. **Polar.sh backup merchant** registration

14. **Self-dogfood final 5 rounds**

### Decision points NOT yet made (Type-A still pending; carry forward)

- **#3 MEDIUM** defensibility frame architecture-lead vs founder-lead — pending
- **#4 LOW** rough notes verification — pending; affects founder-narrative-arc.md after rename
- **#5 MEDIUM** interview confirmation threshold — pending
- **#7 MEDIUM** telemetry-readiness Sentry + PostHog — pending
- **#10 HIGH** pricing — under Path A, options are: $5-10/mo memory feature, buy-out, or OSS+donate. Cherry Studio is free; competing pricing. Pending.
- **NEW** OSS throughline / Rodspan SaaS public messaging — pending; affects §3 step 6 + future positioning

These are independent of rename. Carry forward.

---

## §4 Special handling — six things needing explicit attention

### §4.1 — Wave 1c immutability

Wave 1c shipped on Rodix system prompt + classifier safety prompts + extraction R1/R2 rules + schema v5 + tests. Rename in §A.6 touches all of these.

**The constraint is:** rename must not change *behavior*, only *strings referring to the brand name*.

CC verification protocol before declaring Tier A complete:
1. Run full `pytest` suite — must show same pass count as the baseline measured at start of A.6.
2. Run `app/scratch/wave1c_phase3_verify.py` (renamed) against real OpenRouter — must produce same 4/5 PASS + 1 WEAK at the same ~$0.01 cost.
3. **Manual LLM voice review (§5 verification):** Rodc opens chat, sends 5 sample messages of varying register (work problem / emotional / philosophical / casual / crisis-adjacent), reads LLM responses, confirms voice fits Rodspan / Path A framing. Tests don't catch this.
4. If any of 1-3 differs, **rollback the change** (see §6) and surface to fresh-Opus.

Wave 1c spec files (`2026-05-03-wave1c.md`, `2026-05-03-wave1c-type-a-decisions.md`) are NOT modified content-wise; only annotation per §2.3 C.2.

### §4.2 — friends-intro regenerate vs find-replace

Per §A.2, the new `docs/rodspan-friends-intro.md` is a regenerate, not find-replace. Three reasons stack:
1. Rodspan's semantics enable better lines than Rodix's meaning-empty version (especially the "spine of conversations" metaphor in line ~311 of Rodix version)
2. The original was framed under "memory layer" framing inherited from throughline; Rodspan version positions correctly as LLM chat client with memory wedge
3. Path A locked (user-BYO-API): voice should reflect "you bring your API key, I bring memory + interface" framing

**Audience (Rodc-locked Q2=E):** primary = Cherry Studio / LobeChat / TypingMind users (don't know Rodc/throughline; need Path A wedge framing); secondary = friend cohort already in alpha (founder-note register).

**Process:**
1. CC drafts new `docs/rodspan-friends-intro.md` from scratch using `docs/rodix-friends-intro.md` as structural reference but rewriting prose where Rodspan's semantics + corrected framing + Path A enable better lines.
2. CC produces a side-by-side diff annotated: "structural anchor preserved | prose rewrite | new semantic-leveraged line | category framing correction | Path A framing".
3. Rodc Type-A reviews diff and either (a) accepts CC draft, (b) edits inline, (c) rewrites line-by-line.
4. New file becomes voice oracle for all subsequent A.3 marketing rewrites.

**Voice oracle authenticity caveat:** the original Rodix friends-intro was authored by CC, not Rodc personally. Regenerating via CC therefore inherits the same authenticity ceiling — voice oracle may not reflect Rodc's true voice but rather CC's interpretation of Rodc's voice. This is a standing question Rodc may want to address by personally writing or editing the regenerated friends-intro. Spec does not enforce this; it surfaces the caveat.

### §4.3 — `rodix_system.md` → `rodspan_system.md` file rename

The live system prompt loaded by `app/web/server.py`. Pure find-replace inside the file is insufficient — the FILENAME also changes, which means any importer hardcoding `rodix_system.md` as a path string breaks at runtime.

CC procedure:
1. `grep -rn "rodix_system" .` to find all references (likely server.py and possibly scratch/test files)
2. Rename file: `git mv app/web/prompts/rodix_system.md app/web/prompts/rodspan_system.md`
3. Find-replace `rodix_system` → `rodspan_system` in importers
4. Run full test suite immediately
5. If ANY test fails that wasn't failing pre-rename, this is regression — `git revert` and surface

### §4.4 — OSS throughline / Rodspan SaaS relationship (RESOLVED 2026-05-04)

**Per Q1=D Type-A 2026-05-04 (post-F2 architectural surfacing): Open Core model locked.** OSS throughline continues as algorithm canon, maintained as long as Rodspan SaaS is active commercial product. Rodspan SaaS imports throughline as sibling-repo PYTHONPATH dependency. See §15 for layer rules and three commitments. Spec configuration:

- throughline OSS repo at `https://github.com/jprodcc-rodc/throughline` continues to exist, public
- Rodspan SaaS uses code from this repo (currently)
- Per Q5=A: future migration to separate `rodspan-app` private repo is planned
- §A.9 includes throughline-OSS-related files where they exist in repo (`throughline_cli/` Python module, etc.)
- **Default:** find-replace "rodix" → "rodspan" but NOT "throughline" → "rodspan" or any other mass rename of throughline references
- Exception: `rodix-friends-intro.md` is a Rodspan-specific file (not throughline OSS); rename to `rodspan-friends-intro.md`
- **CC must surface to Rodc + fresh Opus when it encounters "throughline" references in any file CC is renaming, asking whether to leave throughline references intact or migrate**

This means: throughline OSS branding lives alongside Rodspan SaaS branding in the repo for now. Cleanup deferred to post-launch, post-Rodc decision on long-term relationship.

### §4.5 — brand-book §7b "button label" fix

Wave 1c shipped with a known §7b "button label" fix referenced in handoff and audit. Specific content of §7b not in scope to pre-decide here; CC reads `brand-book-v1.md` §7b before A.1 rename to understand context.

**CC instruction:** In §A.1 brand-book-v1.md rename, treat §7b as find-replace only. Do NOT semantic-rewrite §7b. The §7b content was already locked in Wave 1c; semantic rewrite would re-open a closed decision.

### §4.6 — Vault data migration policy

`app/shared/storage_py/vault_path.py` defines where user vault data lives. If path string contains "rodix" (likely `~/.rodix/` or similar), rename strategy depends on Rodc's data state:

**Per Q4: Rodc has not personally run real dogfood; CC simulated all dogfood persona runs in repo fixtures.** This means:

- No production user data exists
- Rodc's local dev environment has no `~/.rodix/` of actual personal data to preserve
- Rename `~/.rodix/` → `~/.rodspan/` is FREE — no migration script needed

**CC procedure for vault_path.py:**
1. Find-replace path string "rodix" → "rodspan"
2. Update test fixtures matching path
3. Surface to Rodc: "Vault path renamed from `~/.rodix/` to `~/.rodspan/`. If Rodc has any local `~/.rodix/` directory with personal data, migrate before next dev run."

**If §3 step 8 self-dogfood begins on Rodspan path AND Rodc later wants to test pre-rename comparisons:** spec does not preserve old path. Comparison between Rodix-path-self-dogfood (none exists) and Rodspan-path-self-dogfood (starting fresh) is moot.

---

## §5 Verification — definition of "rename complete"

Tier A complete iff:
- [ ] Full `grep -ri "rodix\|Rodix\|RODIX" .` returns ONLY:
  - Files in §2.3 Tier C historical record
  - Files explicitly retaining "throughline" references per §4.4
  - `.claude/paste-cache/` (auto-cleanup, ignore)
  - `.claude/projects/.../subagents/agent-*.meta.json` (CC working state, ignore)
  - `.claude/tasks/.../*.json` (CC task state, ignore)
- [ ] `pytest` shows same pass count as baseline measured at A.6 start
- [ ] `app/scratch/wave1c_phase3_verify.py` (renamed) produces 4/5 PASS + 1 WEAK against real OpenRouter
- [ ] Landing page (`app/web/static/landing/index.html`) renders in browser, shows "Rodspan" everywhere
- [ ] `app/web/server.py` loads, opens chat, extraction produces "Rodspan" wording in any system-message-derived strings
- [ ] All Tier C files have rename-annotation header
- [ ] **Rodc smoke test:** open chat in browser, send 3 test messages including one that should trigger card extraction, verify card appears in vault with "Rodspan" branding everywhere visible to user. ~10 min Rodc.
- [ ] **Rodc LLM voice review (§4.1.3):** 5 sample messages of varying register, read LLM responses, confirm voice fits Rodspan + Path A framing.

Tier B complete iff:
- [ ] Plans, business, research, observability, skills support, brainstorm HTML, vault state files all show Rodspan
- [ ] No regression in tests

Manual ops complete iff:
- [ ] `rodspan.app`, `rodspan.com`, `rodspan.dev` registered to Rodc
- [ ] Wyoming `Rodspan LLC` filing submitted
- [ ] Twitter `@rodspan` registered (separate from `@rodc`)
- [ ] GitHub org / repo strategy resolved per §3 step 6
- [ ] `hi@rodspan.app` email forwarding live

---

## §6 Rollback plan — failure modes & responses

### Risk 1 — TM sweep flags STOP after rename in progress
**Trigger:** Gate 1 missed something; post-rename someone surfaces a Rodspan TM in a software class.
**Response:**
1. Stop all rename work immediately.
2. `git revert` Tier A commits if not yet pushed; restore from `pre-rename-backup-2026-05-03` tag (§1.0) if pushed.
3. Re-evaluate: alternatives are Rodkeep #2 from audit (different rename), Rodix retain (revert to pre-rename), or hold launch and pursue TM coexistence (depends on adjacency severity).

**Mitigation:** Gate 1 covers major jurisdictions. Residual TM risk is unquantified per §1.1.

**Ops-layer rollback note (Gap 9 acknowledgment):** `git revert` rolls back code/docs only. If Domain checkout / LLC paperwork / Twitter handle / GitHub repo creation are already done, those are SEPARATE rollback workflows: domain refunds (probably none — Porkbun typically non-refundable), Wyoming LLC change-of-name fee + filing, Twitter handle release (may be sniped before re-registration), GitHub org rename. Real ops rollback is days of work, not 1h CC. This is the documented residual cost of no-lawyer path triggering.

### Risk 2 — Test suite regression after A.6 code rename
**Trigger:** Rename introduced a path breakage or string mismatch.
**Response:**
1. CC `git revert` the failing commit immediately.
2. Re-isolate which file caused regression; rename that file alone with full test verification.
3. If multiple files entangled, do them serially with test runs between each.

**Mitigation:** §4.1 verification protocol mandates test runs after each A.6 file. §2 commit discipline limits blast radius.

### Risk 3 — friends-intro regenerate produces inferior voice
**Trigger:** Rodc reviews CC's regenerated friends-intro draft and finds it weaker than original Rodix version.
**Response:**
1. Rodc rewrites the file by hand using Rodspan name + corrected framing + Path A + original structure as scaffold.
2. A.3 marketing rewrites cannot start until friends-intro is locked, so this gates marketing rewrites.

**Mitigation:** §4.2 process gives Rodc explicit veto. Default acceptable since CC has no time pressure on this file.

### Risk 4 — Domain rodspan.com or rodspan.app sniped during TM gate window
**Trigger:** Domain squatter sees the audit artifacts (public throughline OSS repo per Q5=A) and registers between audit completion and Porkbun checkout.
**Response:**
1. Rodc registers domains FIRST, in parallel with TM sweep, since registration is reversible (transfer if needed) but lost availability isn't.
2. If sniped: re-run audit's #2 finalist (Rodkeep) availability; if Rodkeep clear, fall back. If both sniped, hold Rodix.

**Mitigation:** §3 Day-0 step 1 instructs Rodc to checkout immediately, BEFORE Gate 1.

### Risk 5 — Wyoming `Rodspan LLC` name unavailable
**Trigger:** Wyoming filing search shows existing `Rodspan LLC` or close variant.
**Response:**
1. File LLC under fallback: `Rodspan Software LLC` or `Rodspan Labs LLC` or `Rodspan Holdings LLC`.
2. Brand and LLC do not need exact match.

**Mitigation:** Gate 1 includes Wyoming Business Search. Catches this before LLC paperwork.

### Risk 6 — Mid-rename, Rodc decides reverse course
**Trigger:** Rodc gets cold feet halfway through Tier A.
**Response:**
1. CC stops; preserves `pre-rename-backup-2026-05-03` tag.
2. Rodc decides: (a) full revert via tag, (b) finish Tier A but stop Tier B, (c) push through.

**Mitigation:** This spec exists explicitly to prevent this — decision is locked in §0. If Rodc reverses, that's a real Type-A reversal, not a process failure.

### Risk 7 — TM database query interface unreachable / JS-heavy / disallowed
**Trigger:** CC's web fetch can't render TMview SPA, or WIPO TOS blocks automated query, or USPTO new-system syntax differs from CC's understanding.
**Response:** Per §11 blocked-state escalation. Rodc may need to do some manual browser queries; CC compiles results.

**Mitigation:** Spec acknowledges this risk upfront in §1.1.

### Risk 8 — Env var / DB schema / cookie / API path rename has unanticipated breakage
**Trigger:** §A.6 grep audit (in rodspan-app/) surfaces "rodix" in env var / DB / cookie / API path; Rodc unblocks rename; some external dependency Rodc forgot about breaks.
**Response:**
1. CC `git revert` the breaking commit in rodspan-app (NOT throughline — §A.6 runs in rodspan-app per Open Core split).
2. If breakage cascades to throughline (very unlikely since throughline algorithm canon does not contain "rodix" branding), `git revert` in throughline separately.
3. Rodc identifies the dependency and either updates it or signals to keep the rodix-named identifier as legacy alias.
4. Both options (update vs alias) are valid. Spec does not pre-decide.

**Mitigation:** §A.6 explicitly surfaces these classes of rename to Rodc rather than blind-renaming. rodspan-app backup tag pre-rename-backup-2026-05-04-rodspan-app at 4fbda2f provides clean restore point.

---

## §7 Reference paths

```
Repo root: C:\Users\Jprod\code\throughline\

Audit artifacts (DO NOT MODIFY content; annotate only):
- docs/superpowers/branding/name-audit/00-RECOMMENDATION-MEMO.md
- docs/superpowers/branding/name-audit/04-finalists/01-rodspan-dossier.md
- docs/superpowers/branding/name-audit/05-decision-matrix.md (post-stress-test)

Wave 1c lock (DO NOT MODIFY content; annotate only):
- docs/superpowers/specs/2026-05-03-wave1c.md
- docs/superpowers/specs/2026-05-03-wave1c-type-a-decisions.md

Working state (READ FIRST when fresh-Opus picks up):
- docs/superpowers/_state/rodc-context.md
- docs/superpowers/tonight/reusable-patterns.md
- docs/superpowers/tonight/escalations.md

Predecessor project context (informs §0.3 framing + §4.4 OSS-relationship):
- https://github.com/jprodcc-rodc/throughline (public OSS repo)

Voice oracle (post-rename, regenerated):
- docs/rodspan-friends-intro.md (per §4.2)

This spec:
- docs/superpowers/tasks/rodix-to-rodspan-rename.md
```

---

## §8 Open Type-A escalations carry-forward

Independent of rename; carry forward unchanged from prior handoff:

- **#3 MEDIUM** defensibility frame (architecture-lead vs founder-lead) — pending
- **#4 LOW** rough notes verification — pending; affects founder-narrative-arc.md after rename
- **#5 MEDIUM** interview confirmation threshold — pending
- **#7 MEDIUM** telemetry-readiness (Sentry + PostHog Tier 3) — pending
- **#8 MEDIUM** first-cohort copy-lock confidence (5–7 day friend dogfood) — pending
- **#9 HIGH** LLC jurisdiction Wyoming default — Rodc starting Day-0 step 3 with Rodspan LLC name
- **#10 HIGH** pricing — under Path A, options are: $5-10/mo memory feature, buy-out, or OSS+donate. Pending.
- **#11 MEDIUM** anti-spin marketing copy lock — standing, applies to A.3 rewrites
- **#13 NEW LOW** rodix.chat skip — confirmed; rodspan.chat also skip
- **#14 NEW MEDIUM** Anthropic ZDR confirmation — pending; Rodc Day-0 email; framing changes under Path A

**Wave 1c.1 calibration backlog** (carry forward from `2026-05-03-wave1c-handoff.md`; not affected by rename):
- P0 Layer 2 LLM under-classify Emma-shape preemptive demarcation
- P0 marker-echo bug on Haiku 4.5
- P2 Mike Day-17 topic paraphrase ("cognitive decline" vs "she's slipping")
- P2 Type-A 3 ZH localization (deferred — but per Path A decision EN-only is sufficient)

**New escalations from this spec:**
- **NEW MEDIUM** OSS throughline / Rodspan SaaS long-term relationship (Q1=D pending)
- **NEW MEDIUM** GitHub repo migration path per §3 step 6 (Q5=A direction set, migration path TBD)
- **NEW MEDIUM** Path A vs Path B revisit trigger — if Phase 1 alpha telemetry shows ICP mismatch with Cherry Studio user base, Rodc may revisit Path B; would re-open brand-name decision
- **NEW LOW** AI co-authorship attribution in HN post / founder essay / Twitter bio (Gap 15)
- **NEW LOW** Voice oracle authenticity caveat — friends-intro is CC-authored not Rodc-authored (§4.2)

Resolved (don't re-raise):
- **#2** crisis-content protocol — RESOLVED via Wave 1c
- **#12** extraction failure mode — RESOLVED via Wave 1c
- **brand-name-final-decision** — RESOLVED via this spec (Rodspan)
- **product-strategy-Path-A-vs-B** — RESOLVED 2026-05-03 (Path A locked)

---

## §9 Fresh Opus first action after handoff

When Rodc starts a fresh Opus session and references this spec:

State machine:

| State | Description | Fresh Opus action |
|---|---|---|
| **−1** | Spec just saved, fresh Opus session just opened, hasn't read spec yet | Read this spec end-to-end + audit memo `00-RECOMMENDATION-MEMO.md`. Confirm §0.2 Path A locked + §0.3 product category framing understood. Do NOT begin tooling. |
| **0** | Decision locked, Gate 1 not started | Write paste-ready CC message to launch Gate 1 TM sweep per §1.1. |
| **1** | Gate 1 running | Wait for results. Surface to Rodc when complete. If CC hits §11 blocked state, surface immediately. |
| **2** | Gate 1 CLEAR | Write paste-ready CC message to launch §1.0 backup tag + §2.1 Tier A.1 (brand foundation), starting with brand-book-v1.md. |
| **3** | Tier A in progress | Check TodoWrite-style task state from CC. Identify next file in tier order per §2.0 dependency graph. Surface STOP for Rodc review at end of each tier sub-section (A.1, A.2, A.3, ...). |
| **4** | Tier A complete + verified | Write paste-ready CC message for Tier B. |
| **5** | Tier B complete | Guide Rodc through §3 manual ops in sequence. |

Each tier completion gets a STOP for Rodc review per Wave-1c-resume-handoff pattern.

**Do NOT auto-proceed.**
**Do NOT modify §2.3 Tier C historical files content.** Annotation only.
**Do NOT modify Wave 1c specs content.** Annotation only.
**Do NOT re-debate the Rodspan decision.** §0 is locked.
**Do NOT re-debate Path A.** Locked 2026-05-03.
**Do NOT proceed past §A.6 grep audit results without Rodc unblock on env var / DB / cookie / API path renames.**

Default first response template if Rodc says "继续 rename" with no further state context:

> "Reading rodix-to-rodspan-rename.md spec. State checks:
> 1. Pre-rename backup tag created (§1.0): [yes / no]?
> 2. Domains rodspan.{app,com,dev} purchased (§3 Day-0 step 1): [yes / no]?
> 3. Gate 1 TM sweep run (§1.1): [not yet / running / complete]?
> 4. Has CC begun any §2.1 work: [yes / no]?
> 5. Path A vs Path B: confirmed Path A still locked? (yes/no)
>
> Awaiting Rodc state confirmation. Default next action depends on state."

---

## §10 End of spec — total cost summary

**This breakdown is rename + LLC + domains only — NOT Phase 1 alpha launch total cost. Path A specifically: Rodspan does NOT cover user LLM cost, so no API budget line.**

Out-of-pocket:
- Domains (`rodspan.app` + `.com` + `.dev`): ~$50
- Wyoming LLC year 1 (filing + registered agent): ~$275
- EIN service if used (Northwest): ~$150 — optional, can self-file Form SS-4 free
- Sunk Rodix Porkbun (rodix.app + .dev abandoned cart): ~$28

**Subtotal: ~$500–$525**

CC time (per file estimates uncalibrated; CC measures throughput on first 3 A.1 files and surfaces calibrated estimate):
- Rough planning range: 18–35h CC autonomous across Tier A, similar for Tier B if needed

Rodc time:
- friends-intro Type-A review: 30 min – 4h depending on draft quality
- §A.6 surfaced env var / DB / cookie / API path decisions: 30 min – 2h
- Manual ops sequence: ~6–10h spread over 5–14 days
- Smoke test post-A.6: ~10 min
- LLM voice review post-A.6: ~30 min

Calendar (parallel paths):
- Rename CC autonomous: triggered on Gate 1 CLEAR; CC continues until A.6 verified, then surfaces
- LLC paperwork: 7–14 day Wyoming processing (parallel)
- Anthropic ZDR: 1–3 day reply (parallel)
- TM sweep: targeted same-day, but unbounded if §11 blocked
- §12 launch-blocking out-of-scope work (logo / hosting / etc.): SEPARATE timeline, NOT covered by this spec

**Phase 1 alpha launch ETA 21–30 days from 2026-05-03 should remain achievable IF (a) Gate 1 CLEAR happens within Day-0 to Day-2 window, (b) no major rollback events occur, AND (c) §12 launch-blocking out-of-scope work is started in parallel with this rename.**

---

## §11 Blocked-state escalation protocol

When CC autonomous execution hits a state where it cannot make progress and is uncertain whether to continue, retry, or escalate:

**CC's required behavior:**

1. **Do NOT fabricate progress.** Never write "checked database, all clear" if CC could not actually load the database. Never claim a test passed if CC cannot run pytest. Never declare a file renamed if `git mv` failed. Falsifying state is worse than blocking.

2. **Do NOT silently retry indefinitely.** Maximum 3 retries on any single tool call (web fetch, git op, pytest run, file edit). After 3, treat as blocked.

3. **Do NOT degrade silently.** If CC's web fetch can't render TMview SPA, do not switch to "best guess based on Google search" without surfacing — that's the path to fabricated coverage.

4. **Surface explicitly to fresh-Opus + Rodc:**

```markdown
## BLOCKED — [phase, e.g., Gate 1 / Tier A.6 / verification]

**What CC was trying to do:** [specific action, e.g., "query TMview for 'Rodspan' exact match"]

**What happened:** [specific failure, e.g., "web fetch returned empty HTML; SPA likely requires JavaScript that CC's fetch tool cannot execute"]

**What CC has tried:** [list of retries, alternative approaches]

**What CC will NOT do without Rodc instruction:**
- Fabricate the result
- Skip this database and silently mark "covered"
- Switch to a non-equivalent backup source

**Options for Rodc:**
- (a) Skip this database; document as "could not query; coverage gap" in `06-tm-sweep-results.md`
- (b) Rodc does the query manually in browser, pastes result into chat
- (c) Provide alternative endpoint or tooling
- (d) Halt rename and reconsider
```

5. **Halt and wait.** Do not proceed past a blocked state without explicit Rodc unblock.

This protocol applies to every CC tool failure across the rename: TM database queries, git operations, pytest runs, file edits, web fetches, JSON validation, real-API verification, and especially **A.6 env var / DB / cookie / API path surfaces** which are inherently Rodc-decision not CC-decision.

---

## §12 Launch-blocking work this spec does NOT cover

**These items are launch-blocking but separate workstreams from rename. They must be tracked separately and completed before Phase 1 alpha launch.** Listing them here so they don't get lost.

### §12.1 — Visual identity for Rodspan (Gap 1, P0)

**Status:** Rodix had no logo, no wordmark, no favicon, no OG image, no app icon. This was deferred (handoff Tier 3). Now Rodspan needs all of these.

**Components required:**
- Logo (SVG primary + PNG variants @1x/2x/3x; sizes: 32px favicon, 180px iOS app icon, 512px android, 1200x630 OG image)
- Wordmark (font selection + lockup decision: lowercase `rodspan` / camelCase `RodSpan` / spaced `ROD SPAN`)
- Favicon
- App icon (Phase 2 if/when native app)
- OG image / social cards
- Twitter banner / avatar (anonymous-friendly)
- Email signature graphic (optional)

**Owner:** Rodc decision on direction; CC can generate via Imagen / similar AI, or Rodc engages designer (Fiverr / Upwork / friend).

**Estimated effort:** Hard to estimate without scope decision. Range: 2-8h CC + Rodc review (AI-generated, accept-or-reject) up to 1-3 weeks if engaging designer.

**Cherry Studio visual benchmark (Gap 4):** before designing, Rodc may want to study Cherry Studio's visual register (logo, color palette, illustration style) to decide whether Rodspan should align (same category fit) or differentiate. This is strategic, not just aesthetic.

**Blocker for:** landing page, Twitter @rodspan setup (avatar/banner needed), HN launch post (OG image needed), favicon visible to alpha testers.

### §12.2 — Design system content audit (Gap 2, P0)

**Status:** §A.7 renamed `.claude/skills/rodix-design-system/` directory but the **content** of those 7 files may describe Rodix-specific visual concepts (illustration metaphors, color rationale, microcopy patterns tied to Rodix register). CC surfaces what's in those files when running A.7 audit step 3.

**Owner:** Rodc + designer (if engaged).

**Estimated effort:** depends on what's in the files. Read-and-decide ~2h Rodc.

**Blocker for:** any Rodspan UI work that references the design system.

### §12.3 — User first-impression visual touchpoints (Gap 3, P0)

**Status:** spec covers brand copy rewrite. Visual touchpoints not covered:
- Landing page hero design (typography lockup choice + visual)
- App icon / favicon
- Login screen visual
- Onboarding first screen
- Vault top header design
- Email "from" name display + signature

**Owner:** Rodc + designer.

**Estimated effort:** 1-3 weeks parallel with rename.

**Blocker for:** Phase 1 alpha launch.

### §12.4 — Hosting / deployment decision (Gap 22, per Q3)

**Status:** Per Q3, Rodc has not run dev environment or planned prod hosting. No deploy URL exists. No HTTPS cert configured. `.app` TLD is HSTS-preload-required (Google enforces HTTPS).

**Decisions needed:**
- Dev hosting (local only? remote dev box? Vercel preview?)
- Prod hosting (Vercel / Cloudflare / Railway / Fly.io / self-hosted on VPS)
- DNS provider (Porkbun for domain registration, but DNS hosting could be elsewhere)
- HTTPS cert provisioning (Let's Encrypt via host? Cloudflare?)
- Email transactional service (SendGrid / Resend / Postmark for password reset etc.)
- Database hosting (SQLite local / Postgres via Neon/Supabase / managed elsewhere)

**Owner:** Rodc Type-A on each.

**Estimated effort:** 1-2 days research + decision + initial setup.

**Blocker for:** Phase 1 alpha (need a URL users can visit).

### §12.5 — competitor-positioning.md creation (Gap 7)

**Status:** This file is referenced by audit task spec §13 but does not exist in repo. Brand foundation has a structural gap.

**Content needed:** Cherry Studio + LobeChat + TypingMind + ChatBox + BoltAI + LibreChat + AnythingLLM + Open WebUI + Msty + Faraday + Jan: each with positioning summary, pricing, distinctive feature, weakness, and how Rodspan differentiates. ~2000-3000 words.

**Owner:** CC drafts (using web search to gather competitor info), Rodc reviews and edits.

**Estimated effort:** 3-5h CC + 1-2h Rodc.

**Blocker for:** position-strategy.md polish, marketing rewrites that need explicit competitor framing.

### §12.6 — Voice oracle authenticity check (Gap 6, P1)

**Status:** Per §4.2 caveat, friends-intro and most voice-related brand artifacts are CC-authored, not Rodc-personally-written. Voice oracle therefore has unknown authenticity ceiling.

**Decision needed:** Rodc decides whether to (a) accept CC-authored voice as canonical, (b) personally write a 500-1000 word raw text in Rodc's true voice (Twitter draft / journal entry / etc.) to use as ground-truth voice sample, (c) edit existing CC-authored artifacts toward Rodc's voice.

**Owner:** Rodc.

**Estimated effort:** 1-3h Rodc for option (b).

**Blocker for:** voice-fit verification post-rename. Without authenticity check, marketing rewrites and friends-intro regenerate may compound CC's interpretation drift.

### §12.7 — Items moot per Q4 (Gap 23 / Gap 24 / Gap 5)

These were potential gaps but resolved by Rodc's responses:

- **Gap 5 (Chinese brand presentation):** moot — ICP is English per Rodc.
- **Gap 23 (vault data migration):** moot — no real data to migrate per Q4.
- **Gap 24 (existing alpha communication):** moot — no friend cohort exposed to Rodix per Q4.

Listed here as resolved-and-out-of-scope so future readers don't re-raise.

---

## §13 Open product strategic questions carry-forward

Independent of rename; not for spec to resolve. Surface here so they don't get lost during execution focus.

### §13.1 — Path A pricing (Escalation #10 carry-forward + Path A specifics)

Cherry Studio is free + open-source. Rodspan is Path A (user-BYO-API) but planned paid. Pricing options:

- $5/month memory layer subscription
- $10/month memory + cloud sync + extras
- One-time buy-out ($29-49) à la TypingMind
- OSS + donate model (no subscription)
- Freemium: free local-only / paid cloud-sync

**Decision needed before Phase 1 alpha launch.** Affects landing page CTA, pricing page, Paddle product setup.

### §13.2 — User-BYO-API onboarding UX (Path A specific)

Cherry Studio onboarding for API key entry: user pastes key in settings, goes. TypingMind same.

Rodspan must be at least as good. Decisions needed:
- Required at first chat or deferred until first message?
- Multi-provider config (let user paste OpenAI + Anthropic + OpenRouter all)?
- Key validation on entry (test API call) or lazy?
- Storage: localStorage / IndexedDB / encrypted at rest in vault?

This is product UX work. Spec acknowledges; does not resolve.

### §13.3 — OSS throughline / Rodspan SaaS public messaging (per Q1=D)

When Rodspan launches publicly on HN / Twitter / blog, the relationship to OSS throughline must be communicated (or not). Options:

- (a) Rodspan announced as "successor / hosted version of throughline" — leverages OSS legitimacy + reach
- (b) Rodspan announced standalone — no throughline mention; clean slate
- (c) Rodspan announced as "by the team behind throughline" — partial credit

Different choices have different effects on HN reception, brand authenticity, OSS community goodwill. Rodc strategic decision.

### §13.4 — (D) decouple option — CANCELLED 2026-05-04

Earlier draft of this spec (pre-Open-Core lock) included option (D) as a post-launch task: rewrite Rodspan app/ to not depend on throughline OSS root packages (mcp_server, throughline_cli). This option is now **cancelled** per Open Core architectural lock 2026-05-04.

**Reason for cancellation:** Open Core model treats sibling-repo dependency as permanent architecture, not technical debt. Throughline OSS continues as algorithm canon while Rodspan SaaS is active commercial product. Decoupling would break the model's algorithm-flow benefit (improvements in OSS automatically flow to SaaS).

**If Open Core is later abandoned** (e.g., Rodspan acquired by buyer wanting clean separation), (D) can be re-considered as part of architectural transition. Until then, do NOT execute (D).

### §13.5 — Path B revisit trigger

Path A is locked 2026-05-03. **If** Phase 1 alpha telemetry shows:
- ICP mismatch with Cherry Studio user base (e.g., users want hosted LLM, not BYO-API)
- Memory feature unable to justify paid $5-10/month vs Cherry Studio free
- TAM too small even at high conversion

Then Rodc may revisit Path B. **This would re-open brand-name decision** — Rodspan is fit for Path A category; under Path B (LLM provider category), empty-coined would be base rate and Rodix-or-similar would re-emerge.

Spec does NOT pre-resolve this. Surface as standing risk for post-launch evaluation.

### §13.6 — Rodc / Rodspan handle relationship + AI co-authorship (Gap 15 + Gap 16)

Twitter:
- `@rodc` = founder voice, narrative, dev-log
- `@rodspan` = product voice, support, feature announcements
- Cross-link between them

HN / founder essay / Twitter bio attribution:
- Anonymous founder (Rodc) built with Claude Code (CC) collaboration
- How explicit to make AI collaboration in launch communication?

Rodc strategic decision; not blocking.

### §13.7 — Brand artifacts stage-2 review (NEW 2026-05-04)

**Trigger:** §A.2 friends-intro lock + §A.3 marketing first draft complete.

**Owner:** Rodc + CC (Rodc Type-A on edge cases).

**Estimated effort:** 2-3h CC + 1-2h Rodc review.

**Scope:** Cross-reference review of 8 brand foundation files + 15 marketing files for:
- Internal consistency (no contradictions between sections of same file)
- External consistency (no contradictions across brand + marketing + user copy)
- Path A framing applied uniformly across all files
- Open Core mention placed appropriately (not over-promoted, not missing)
- Voice oracle (post-§A.2 lock) reflected accurately in voice samples and marketing copy
- Cherry Studio competitor framing consistent

**Output:** surface inconsistencies + Rodc Type-A decisions + commit fixes per file.

**Why this is needed:** Initial §A.1 + §A.3 rename pass is per-file, not cross-file. Stage-2 review catches drift between files that emerged because rewrites happened independently.

### §13.8 — Voice-guide update from real dogfood signal (NEW 2026-05-04)

**Trigger:** Rodc self-dogfood 5 rounds complete + friend dogfood feedback in.

**Owner:** Rodc + CC.

**Estimated effort:** 1-2h.

**Scope:** voice-guide.md §5 sample passages may need update if real-API responses under Rodspan rename diverge from documented voice. Particularly relevant if LLM voice shifts post-rename per spec §4.1 LLM self-reference manual review.

**Why this is needed:** Wave 1c verified system prompts under Rodix branding. After rename, LLM may self-identify differently. Real dogfood reveals if voice samples in voice-guide need update to match actual post-rename behavior.

### §13.9 — Visual identity integration (NEW 2026-05-04)

**Trigger:** §12.1 logo / visual identity decided (separate launch-blocking task).

**Owner:** Rodc + CC.

**Estimated effort:** 1-2h.

**Scope:** brand-book §4 archetype + voice-guide §5 voice samples + design-system skill files updated to reference new visual identity. Microcopy patterns may need updates reflecting visual register.

**Why this is needed:** Rodspan currently has no logo / wordmark / visual identity (Rodix didn't either per handoff). After §12.1 decides visual identity, brand artifacts must be updated to reference it consistently.

### §13.10 — Competitor positioning integration (NEW 2026-05-04)

**Trigger:** §12.5 competitor-positioning.md drafted (separate launch-blocking task).

**Owner:** Rodc + CC.

**Estimated effort:** 1h.

**Scope:** position-strategy.md updated to reference competitor-positioning.md as authoritative source. brand-book §3 positioning section verified against new competitor analysis. Marketing copy verified against competitor framing.

**Why this is needed:** Currently position-strategy.md and brand-book §3 reference Cherry Studio / LobeChat / TypingMind generically. Once competitor-positioning.md exists with detailed analysis, brand artifacts should reference that source rather than duplicate analysis.

---

## §14 End of spec

Total expected duration: ~30–50h CC autonomous + ~6–10h Rodc + 7–14 day Wyoming LLC processing (parallel) + 1–3 day TM sweep (parallel-ish) + §12 out-of-scope work parallel timeline.

Total expected calendar: ~5–7 days for rename code/docs work + LLC paperwork + ZDR + dogfood preparation. Phase 1 alpha launch ETA 21–30 days from 2026-05-03 unchanged ASSUMING §12 work also progresses.

Total cost out-of-pocket: ~$500 (rename + LLC + domain + sunk Rodix Porkbun). §12 work may add cost (designer, hosting subscriptions) — separately budgeted.

No lawyer cost (replaced by Opus + CC TM sweep, with documented residual risk in §6 Risk 1).

## §15 Open Core architectural commitments (LOCKED 2026-05-04)

Three commitments Rodc accepted as part of Open Core model lock. These are durable architectural decisions, not preferences. Future fresh Opus + CC sessions must enforce these commitments when reviewing code / spec / strategy decisions.

### §15.1 — Commitment 1: Throughline OSS maintained while Rodspan is active

Throughline OSS receives 5-10 hours/month maintenance: issue triage, critical bug fixes, dependency updates, docs readability. This commitment holds as long as Rodspan SaaS is an **active commercial product** (alpha / beta / production with paying or trial users).

**Sunset path if Rodspan ends:** If Rodspan ends due to commercial failure, burnout, acquisition, or pivot, throughline enters sunset evaluation. Four honorable exits:

(a) Archive on GitHub — most common; README updated to "no longer maintained" + recommend alternatives if any.

(b) Transfer maintainership — if active OSS contributor exists who wants to take over.

(c) Continue as personal side-project — if Rodc personally invested, low priority (1-2h/month).

(d) Fork algorithm into successor project — if Rodc continues memory-related work elsewhere.

None of (a)/(b)/(c)/(d) constitutes abandonment. All preserve user trust appropriately for the situation.

**Dormancy clarification:** If Rodspan goes dormant (low usage but technically alive — e.g., 50 users, low growth, no incident in months), throughline maintenance reduces to 1-3h/month critical-only. Dormancy lasting >6 months triggers sunset evaluation.

### §15.2 — Commitment 2: Layer boundary strict execution

Every code change requires explicit decision: OSS or SaaS layer? Ambiguous cases default to OSS (algorithm canon).

**Anti-pattern to resist:** "I'll put it in SaaS for now and figure out later." This is how Open Core models break. Rodc + CC must decide layer at write-time.

**Layer rules table:**

| Code type | Layer |
|---|---|
| Memory algorithm improvement (drift detection, recall scoring, etc.) | OSS throughline |
| Claim schema evolution | OSS throughline |
| LLM provider routing / adapter | OSS throughline |
| MCP server interface | OSS throughline |
| User-facing UI / UX components | Private rodspan-app |
| Authentication / billing / subscription | Private rodspan-app |
| Multi-user / team / collaboration features | Private rodspan-app |
| Cloud sync infrastructure | Private rodspan-app |
| Analytics / observability / SaaS metrics | Private rodspan-app |
| Premium memory features (recall+, dashboards) | Private rodspan-app |
| Cherry-Studio-aware design / brand UX | Private rodspan-app |
| Marketing / brand artifacts | Private rodspan-app |

**Rule of thumb for ambiguous cases:** "If a hypothetical other OSS user wanting throughline self-host would also benefit from this code → OSS. If only Rodspan SaaS paying customers would → SaaS."

### §15.3 — Commitment 3: Algorithm improvements default to OSS

Algorithm improvements (drift detection, Claim schema, recall scoring, provider adaptation) default to OSS throughline, even if motivated only by Rodspan SaaS needs.

**Reasoning:** Schema/algorithm is canon. Forking canon between OSS and SaaS = model collapse. The cost of giving away an improvement to OSS users (free-rider concern) is far less than the cost of forking canon (architectural debt + decoupling work + diverging behavior).

**Exception:** SaaS-specific algorithm tuning (e.g., latency optimizations only relevant to hosted multi-user setups) may stay in SaaS layer. But schema definitions, core algorithms, and provider routing → always OSS.

### §15.4 — Enforcement during this rename and onward

During §A rename execution and all subsequent Wave 2+ work:

- CC must surface to Rodc when making decisions that affect layer assignment.
- Fresh Opus must validate proposed changes against Layer rules table (§15.2).
- Rodc Type-A on edge cases; default to OSS for ambiguity.
- Quarterly review (or per-Wave): audit recent commits for layer violations; rebalance if needed.

Spec is complete. Hand off to fresh Opus.
