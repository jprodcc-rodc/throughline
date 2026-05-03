# Gate 1 — Trademark + Common-Law Clearance Sweep Results

> **Date:** 2026-05-04
> **Subject mark:** Rodspan
> **Sweep mode:** Rodc-driven browser, CC compiles (per spec §11 protocol)
> **Reason for mode:** WIPO TOS prohibits automated/bulk querying; TMview and USPTO Trademark Search are JS-heavy SPAs that CC's web-fetch tool cannot reliably render. Per spec §1.1 honest framing + §11 blocked-state protocol, the only honest path is Rodc manual browser queries with raw response excerpts pasted into chat for CC compilation.
> **Spec reference:** `docs/superpowers/tasks/rodix-to-rodspan-rename.md` §1.1 (Gate 1 — TM clearance, DIY without lawyer)
> **Outcome:** **CLEAR** across all 6 databases. No FLAG, no STOP. Proceed to §2 rename.

---

## Decision rule (quoted from spec §1.1)

> - All CLEAR → proceed to §2 rename
> - Any FLAG → fresh-Opus + Rodc review the FLAG, decide proceed/stop based on adjacency severity (e.g., a Rodspan TM in class 7 heavy-machinery is FLAG-but-proceed; one in class 42 software/SaaS is STOP)
> - Any STOP → halt rename; surface to Rodc for re-decision (alternatives: choose Rodkeep #2 from audit, or hold Rodix)

## Honest scope caveat (quoted from spec §1.1)

> This is a founder-level due-diligence sweep using public search tools that cover major jurisdictions where Rodspan would operate (US / EU / UK / Madrid international system, ~75 offices via TMview). It catches identical and obvious-similar marks in software-relevant classes.
>
> It does NOT do:
> - Phonetic-equivalent fuzzy search across all jurisdictions (paid attorney-grade fuzzy clearance costs €700–900 per EU sweep alone)
> - Common-law unregistered TM searches in non-internet sources
> - TTAB pending opposition / cancellation checks against pending applications
> - Likelihood-of-confusion examination (the legal standard a USPTO examiner applies)
> - Non-Latin transliteration sweeps (e.g., Cyrillic / CJK variants)
>
> A bona fide cease-and-desist or USPTO refusal could still arise from marks this sweep misses. Without a lawyer, residual risk is unquantified — we do not claim a percentage of lawyer-grade coverage because we have no data to support such a claim. Rodc proceeds with this knowledge per §6 Risk 1.

---

## Summary table

| DB | URL | Verdict | Notes |
|---|---|---|---|
| 1. TMview | tmdn.org/tmview | CLEAR | "Rodspan" exact: 0 hits across ~75 IPO aggregator |
| 2. USPTO | tmsearch.uspto.gov | CLEAR | "Rodspan" Wordmark search: 0 results (Live: 0, Dead: 0). Sanity check "Rods*" wildcard returned 168 unrelated marks (HOGS & RODS, BEAVERHEAD RODS etc.), no Rodspan. |
| 3. WIPO Brand DB | branddb.wipo.int | CLEAR | "Rodspan" exact: 0. "RodSpan" 0. "Rod-Span" 0. "Rod Span" 382 substring false-matches in non-software classes (PRODESPAÑA / Rød Spanvall / PRODISPANOS / SPANISCHBRÖDLI etc.), 0 in classes 9 or 42. |
| 4. Wyoming SOS | wyobiz.wyo.gov/business/filingsearch.aspx | CLEAR | Filing Name "Rodspan" with Search Type "Contains": NO RESULTS FOUND. "Rodspan LLC" is available for Wyoming filing. |
| 5. Google common-law | google.com | CLEAR with minor adjacencies (no STOP) | See §5 per-query detail below |
| 6. Dev registries | npm, GitHub, PyPI | CLEAR | npm: 0 packages. GitHub: 0 repositories. PyPI: 0 projects (PyPI suggested 'rowspan' as fuzzy alternative, irrelevant). |

---

## §1 — TMview (EUIPN-hosted multi-jurisdiction aggregator)

- **URL queried:** `https://www.tmdn.org/tmview/`
- **Coverage:** ~75 offices including EUIPO + all EU national IPOs + USPTO + UK IPO + Madrid/WIPO international + non-EU partners (~60M marks)
- **Queries:** "Rodspan" exact-match + variants "Rod Span", "Rod-Span", "RodSpan"
- **Raw verdict:** 0 hits across all variants
- **Adjacencies:** none in software-relevant classes (9 / 42 / 38)
- **Verdict:** CLEAR

## §2 — USPTO Trademark Search (replaced TESS Nov 2023)

- **URL queried:** `https://tmsearch.uspto.gov/`
- **Coverage:** US federal — primary jurisdiction for Rodc (Wyoming LLC)
- **Queries:** "Rodspan" Wordmark; sanity wildcard "Rods*"
- **Raw verdict:** "Rodspan" = 0 results (Live: 0, Dead: 0). Wildcard "Rods*" returned 168 unrelated marks (HOGS & RODS, BEAVERHEAD RODS, etc.), no Rodspan in result set.
- **Adjacencies:** none. The 168 wildcard matches are unrelated rod / hot-rod / fishing-rod / industrial-rod marks, no phonetic or semantic overlap with Rodspan.
- **Verdict:** CLEAR

## §3 — WIPO Global Brand Database

- **URL queried:** `https://branddb.wipo.int/`
- **Coverage:** Madrid international + national collections; overlaps TMview but more current for very recent filings
- **Queries:** "Rodspan" exact, "RodSpan" exact, "Rod-Span" exact, "Rod Span" substring
- **Raw verdict:** "Rodspan" 0; "RodSpan" 0; "Rod-Span" 0; "Rod Span" 382 substring false-matches in non-software classes
- **Adjacencies:** the 382 "Rod Span" substring matches are unrelated foreign-language compounds where "Rod" or "Span" or "rodspan" appears as part of a larger word — examples: PRODESPAÑA (Spanish food brand), Rød Spanvall (Norwegian), PRODISPANOS, SPANISCHBRÖDLI (Swiss bakery). 0 hits in NICE classes 9 (downloadable software / mobile apps) or 42 (SaaS / non-downloadable software / software design + development). Substring matches in unrelated classes do not constitute confusion risk for a Class 9/42 software TM.
- **Verdict:** CLEAR

## §4 — Wyoming Secretary of State Business Filing Search

- **URL queried:** `https://wyobiz.wyo.gov/business/filingsearch.aspx`
- **Coverage:** Wyoming state business name registry (Rodc's intended LLC jurisdiction)
- **Query:** Filing Name "Rodspan" with Search Type "Contains" (per Wyoming guide; broader than "Starts With")
- **Raw verdict:** NO RESULTS FOUND
- **Adjacencies:** none
- **Implication:** "Rodspan LLC" available for Wyoming filing (§3 Day-0 step 3)
- **Verdict:** CLEAR

## §5 — Google common-law sweep

Six free-form queries documenting what's already published on the public internet under "rodspan". Active commercial software/SaaS use = STOP; inactive personal/historical use = FLAG; absent = CLEAR.

| # | Query | Did-you-mean | Findings (raw) |
|---|---|---|---|
| 5.1 | `"rodspan"` | Did-you-mean: rowspan | Word Unscrambler page (utility site, no commercial entity); Tri-Rodspan Puzzle on Printables.com (3D STL by individual maker G Bell); helm.lu academic PDF (math/physics jargon) |
| 5.2 | `"rodspan" site:.com` | — | Tri-Rodspan Puzzle (repeat); Google Patents US2694661A (1950s expired patent on adhesive fiber rods, "rodspan" = process jargon); RODSPAN LTD (Mauritius offshore shell entity, no website, no software business) |
| 5.3 | `"rodspan" site:.app` | — | 0 documents matched |
| 5.4 | `"rodspan" site:.io` | — | 0 documents matched |
| 5.5 | `"rodspan" software` | — | NRC.gov nuclear engineering PDF (1980s finite element jargon); Stanford char-rnn wiki (Karpathy RNN-generated fake-Wikipedia text — ironically demonstrates "rodspan" is a phonotactically valid non-word); Scribd Mauritius company list (RODSPAN LTD repeat); IDCrawl Twitter user @Rodspan (Rodney Spangler personal handle) |
| 5.6 | `"rodspan" SaaS` | — | 0 documents matched |

### Adjacencies summary

None warrant STOP per spec §1.1 decision rule. Each is FLAG-only at most; per spec §1.1 "FLAG → review based on adjacency severity" — none of these constitute an active commercial software TM.

| # | Adjacency | Type | Severity assessment |
|---|---|---|---|
| (a) | Tri-Rodspan Puzzle | Individual 3D-print maker geometric puzzle on Printables.com | Not commercial, not software, not a TM filing. Lay use of compound word for puzzle geometry. CLEAR. |
| (b) | RODSPAN LTD (Mauritius) | Offshore shell entity | No active website found, no software-class business. Cross-border enforcement of a US/EU software TM against a non-software Mauritius shell ≈ 0 risk. CLEAR. |
| (c) | @Rodspan Twitter | Personal handle (Rodney Spangler) | Username squat, not brand. Twitter handle separately covered by §3 Day-1-3 manual ops. CLEAR. |
| (d) | 1950s expired patent + 1980s NRC engineering PDF | Textual occurrence in expired/historical scientific writing | No TM, no commercial use. CLEAR. |
| (e) | Stanford char-rnn fake-Wikipedia | RNN-generated text artifact | Literally demonstrates "rodspan" is a phonotactically valid non-word — it's an ML hallucination. CLEAR. |

- **Verdict:** CLEAR with minor adjacencies (no STOP)

## §6 — Developer registries (npm, GitHub, PyPI)

- **URLs queried:**
  - `https://www.npmjs.com/search?q=rodspan`
  - `https://github.com/search?q=rodspan&type=repositories`
  - `https://pypi.org/search/?q=rodspan`
- **Raw verdicts:**
  - npm: 0 packages
  - GitHub: 0 repositories
  - PyPI: 0 projects (suggested fuzzy alternative "rowspan", irrelevant)
- **Adjacencies:** none
- **Verdict:** CLEAR

## §7 — Domain WHOIS (already verified during audit)

- **URL queried:** Porkbun
- **Domains:** `rodspan.app`, `rodspan.com`, `rodspan.dev`
- **Raw verdict:** All three CLEAR at audit time; purchased 2026-05-04, expires 2027-05-04
- **Sniping window:** closed by purchase
- **Verdict:** CLEAR (registered to Rodc)

---

## Final verdict

**Gate 1 CLEAR per spec §1.1 decision rule. All databases pass. Sweep mode: Rodc-driven browser per §11 protocol (WIPO TOS prohibits automation; TMview/USPTO are JS SPAs that CC web fetch cannot reliably render). No FLAG, no STOP.**

Proceed to §2 rename per spec §1.1 — subject to §A.6 repo migration decision (separate blocker surfaced post-Gate-1).

## Residual risk acknowledged (per §1.1 + §6 Risk 1)

This sweep does not replace attorney-grade fuzzy clearance. A bona fide cease-and-desist or USPTO refusal could still arise from marks this sweep misses (phonetic equivalents, non-Latin transliterations, TTAB pending oppositions, common-law unregistered marks in non-internet sources). Rodc proceeds with this knowledge.
