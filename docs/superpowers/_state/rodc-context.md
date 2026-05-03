> **Note 2026-05-04:** Brand renamed Rodix → Rodspan; Open Core locked (Rodspan SaaS in private rodspan-app repo + throughline OSS as algorithm canon, sibling-repo PYTHONPATH dependency). This file is a historical record from prior to the rename. See `docs/superpowers/tasks/rodix-to-rodspan-rename.md` for context. Original "Rodix" references below retained as written at the time.

# Rodc Context — Persistent State File

> **Purpose:** Cross-session context for any AI session (CC / External Opus /
> future agents) to onboard in 5 minutes without relying on chat memory or
> compaction.
>
> **Owner:** Rodc (founder)
> **Author of this dump:** External Opus, 2026-05-03 morning, post-Tier 0
> autonomous shift.
> **Last reviewed by Rodc:** [DATE TBD when Rodc reviews]
> **Update cadence:** Whenever a fact below changes. This is append-update,
> not append-only — superseded items get replaced, not stacked.
>
> **Verification tags:**
> - `[VERIFY]` = External Opus 80%+ confident but not certain. Rodc must confirm.
> - `[GAP]` = External Opus knows there's something here but cannot recall.
>   Rodc must fill in.
> - No tag = External Opus high confidence, multiply confirmed across chat.

---

## 1. Identity

### Founder (Rodc)

- **Pseudonym:** Rodc — used for project work, not legal name
- **Public identity for Rodix:** Anonymous solo founder
- **Nationality / Language:** Chinese, native Mandarin speaker. Communicates
  with External Opus primarily in Chinese (mixed with English technical terms).
  Communicates with CC primarily in Chinese.
- **Location:** Asia (per Rodix friends-intro: "working out of Asia"). `[VERIFY]`
  exact country/city — External Opus does not have explicit confirmation.
- **Working hours:** Heavy evening / late-night work pattern observed across
  multiple sessions. Sessions often run from afternoon through 1-2am local
  time.
- **AI usage:** Heavy AI user, ~2-3 hours/day across multiple providers
  (per Rodc's own friends-intro). 1+ year of intensive AI usage built the
  pattern recognition that produced Rodix.

### Project (Rodix)

- **Name:** Rodix
- **Tagline:** "Memory layer for AI chat. Cross-model. White-box. Yours."
- **Shorter tagline:** "ChatGPT remembers your name. Rodix remembers your thinking."
- **Domain:** rodix.app (primary), rodix.dev, rodix.chat (defensive)
- **Twitter:** @rodix `[VERIFY — pending registration]`
- **GitHub:** rodix-app (org) `[VERIFY — pending registration]`
- **Internal repo name:** throughline (legacy, predates Rodix branding)
- **Local repo path:** `C:\Users\Jprod\code\throughline\` (Windows)
- **Sync:** Some files in `S:\syncthing\rodix\` (separate from repo)

---

## 2. Project State (as of 2026-05-03 morning)

### Wave 1b — SHIPPED

- **Commit:** `53b56f0`
- **Status:** Ship-ready, frozen until dogfood verification
- **What it is:** Claim extraction pipeline (4-field cards: topic / concern /
  hope / question) using Haiku 4.5 via OpenRouter
- **Eval gates passed:**
  - Hallucination: 2.3% / 256 fields (trust-killer GREEN, cap was 5%)
  - Overall PASS: 79.3%
  - Strict gates: 11/14 passed
- **Plan version:** v1.8 at `docs/superpowers/plans/2026-05-01-claim-extraction.md`
- **Scenarios:** v1.3 at `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`
- **Extraction prompt:** v3.1 at `app/shared/extraction/prompts/claim_extractor.md`

### Wave 2 — IN PLANNING (tonight's CC autonomous shift)

5 specs being planned by CC right now in `docs/superpowers/plans/wave2/`:
- `#card-real` — replace placeholder card UI with real 4-field card
- `#active-recall-base` v0 — surface relevant past cards on new conversation
- `#2b first-insight` — pattern-spotting moment after vault accumulates
- `#card-dedup` — simplify card UI when same topic appears 3+ times
- `#vault-recall-history` — show recall count on each card

### Wave 3 — IN PLANNING (tonight's CC autonomous shift)

7 specs being planned by CC for SaaS upgrade:
- `#b-auth` (passwordless magic link recommended)
- `#b-encryption` (SQLCipher at-rest)
- `#b-multitenant` (row-level isolation initially)
- `#b-paddle` (primary) + `#b-polar` (fallback)
- `#b-deploy` (Hetzner / Railway TBD)
- `#b-security-review`
- `#b-privacy-policy`

### Tier 0 — COMPLETED (tonight's CC autonomous shift)

- Brand Foundation Document (re-run with friends-intro after escalation #1)
- Founder Narrative Arc
- User Research Synthesis

### Tier 1.5 Dogfood — IN PROGRESS or COMPLETE `[VERIFY]`

- Hybrid mode: Phase A self-simulate 48 rounds + Phase B 5-round real-API verify
- 4 personas: Mike Chen / Sarah Patel / Daniel Kim / Emma Larsson
- Critical test: Sarah Day-15 crisis content protocol
- Vault target: 30+ cards generated for Rodc's morning dogfood

---

## 3. Phase 1 Launch Strategy

### Decisions made (do not relitigate without strong reason)

- **Phase 1 = English-speaking international launch.** No Chinese market, no EU.
- **Phase 2 = Chinese market** (post-launch, no firm date).
- **EU geo-block.** Dual-layer: IP filter + user-declared residence at signup.
  Reason: GDPR sensitive personal data exposure (mental health disclosed
  conversationally). No legal budget to handle GDPR properly.
- **LLM provider:** OpenRouter primary, Anthropic-direct fallback. Split-route
  via env-var seam `THROUGHLINE_EXTRACTION_PROVIDER` (default "anthropic").
- **Extraction model:** Haiku 4.5 via OpenRouter Anthropic proxy.
- **Pricing band:** TBD. Task 4 produces recommendation. Rodc final call.
- **Real launch ETA:** 14-21 days post Wave 1b ship-ready. Includes:
  - Paddle approval lead time: 5-7 days
  - Privacy Policy lawyer-spot-consult: 3-10 days
  - DNS propagation: 1-3 days
  - Buffer for unknowns

### Brand decisions (provisional, awaiting CC Tier 0 final + Rodc review)

- **Archetype:** [GAP — CC Tier 0 produced final after re-run with friends-intro;
  Rodc to verify in `docs/superpowers/brand/brand-book-v1.md`]
- **Voice principles:** Per friends-intro voice — short paragraphs,
  parenthetical asides, em-dashes, refusal of marketing language, specific
  over abstract, honest qualifications
- **Visual direction:** TBD via Tier 3 Task 9 (Rodix Design System Skill)

---

## 4. Constraints (hard, do not propose violations)

### Financial

- **No lawyer budget for Phase 1 launch.** Privacy Policy path:
  Termly free + reference Anthropic/Notion PP structure + friend review.
  Lawyer-spot-consult only for high-risk clauses (sensitive data / crisis
  content liability).
- **No marketing budget.** Acquisition is HN + PH + Twitter + content +
  IndieHackers + newsletter swaps. No paid ads.
- **OpenRouter credits:** Topped up tonight (~$20+). Burn rate during
  development is the cost concern; production cost capped per-user (Wave 3 spec).
- **No funding round planned.** Bootstrapped. `[VERIFY]`

### Legal / Identity

- **US LLC registration in progress** via third-party agent. Lead time 1-4 weeks.
  Rodc not handling personally. `[VERIFY]` agent name / status.
- **Rodix name TM situation:**
  - US: clear
  - Switzerland: TM #677580 in software class. Risk acknowledged. Mitigation
    = geo-block EU (Switzerland not in EU but in EFTA — `[VERIFY]` whether
    geo-block covers Switzerland too)
- **DBA / business entity for Phase 1 alpha:** [GAP — Rodc clarify]
- **DPO appointed:** No (Phase 1 not GDPR-compliant by design)

### Technical

- **Wave 1b code is frozen** until dogfood verification. CC and any other
  agent must not modify ship-ready code.
- **`app/` directory is gitignored** in current setup. Code changes there
  are not commit-able. (Inherited from earlier setup decisions.) `[VERIFY]`
- **SQLite for Phase 1**, not Postgres. Decision documented in ADR-001.
- **English-only UI for Phase 1.** Chinese support deferred.

### Capacity / Time

- **Solo founder.** No team. No co-founder. No employees.
- **Heavy reliance on Claude (CC) for execution.** External Opus for strategy.
- **Real working capacity:** 6-10h/day intensive work. Weekend rhythm differs
  from weekday `[VERIFY]`.

---

## 5. Pending Operational TODOs

These are blocking Phase 1 launch in some way. None are urgent today
but all need resolution within 14-21 days.

- [ ] **Domain checkout** at Porkbun — rodix.app, .dev, .chat (~$28/yr).
  Currently stuck at HSTS preload notice page in checkout. Needs Rodc
  finishing the flow.
- [ ] **Twitter @rodix** registration
- [ ] **GitHub rodix-app organization** registration
- [ ] **Email forwarding** hi@rodix.app → Gmail (configure in Porkbun after
  domain checkout)
- [ ] **Revoke leaked OpenRouter key** (key prefix 0110, leaked at some
  point — `[VERIFY]` exact circumstance)
- [ ] **Paddle merchant application** — apply after domain + LLC ready.
  5-7 day approval window.
- [ ] **Polar.sh fallback merchant** — register as backup if Paddle rejects
- [ ] **Termly Privacy Policy** — generate using Tier 2 Task 8 draft as base
- [ ] **Friend review of Privacy Policy** — Rodc to identify reviewer
- [ ] **Lawyer spot-consult** — high-risk clauses only, when budget allows
- [ ] **Confirm Anthropic ZDR status** — Tier 2 Task 8 should produce
  research result; Rodc must verify before publishing PP

---

## 6. Working Style — How Rodc Operates

### Communication patterns (observed across many sessions)

- **Push back style:** Direct. Rodc rejects framings without softening.
  When External Opus drifts toward generic AI / SaaS framings, Rodc says
  "no, this is wrong" and pushes for specifics.
- **Depth-over-speed preference:** Rodc consistently asks for more depth,
  more detail, more rigor. Tonight's instruction set went through 6 push-back
  rounds, each time Rodc demanded deeper. Default to more depth than to
  match a time budget.
- **Rejection of stereotypes:** "AI fatigue user persona" gets rejected.
  "Stressed software engineer" gets rejected. Rodc wants real specific
  people (Mike Chen with mom dementia + Brooklyn fintech + Anthropic interview),
  not archetypes.
- **Quality bar:** Linear / Notion / Anthropic-tier. Generic SaaS feel is
  immediate reject.

### Decision-making patterns

- **Ambivalence is OK.** Rodc tolerates "I'm not sure yet, let's hold."
  Will not be rushed to false certainty.
- **Uses External Opus as thinking partner**, not as oracle. Rodc has own
  judgment and frequently overrides Opus suggestions.
- **Will cancel a path if framing is wrong** — even after significant work
  invested. "Sunk cost should not anchor next decision."
- **Prefers explicit over implicit.** Decisions get documented (plan, spec,
  ADR). Verbal-only decisions are flagged as risk.

### Chinese / English language pattern

- **Chinese for strategy + operational discussion** with External Opus
- **English for technical artifacts** (code, plans, specs, brand book, prompts)
- **Mixed in casual chat** — technical terms in English embedded in Chinese sentences

### What Rodc rejects (in writing / outputs)

- Hype-y SaaS marketing voice
- "Founder coach" or LinkedIn-influencer tone
- Pattern-matched advice without specifics
- Generic "you've got this" cheerleading
- Excessive flattery or sycophancy
- Short / surface answers when depth was requested

### What Rodc values (in collaborators / outputs)

- Specific examples > abstract principles
- Honest failure flags > hidden uncertainty
- Push-back on Rodc when Rodc is wrong
- Naming uncomfortable truths (especially in strategic memos)
- Self-grading (A/B/C/D) with honest reasoning

---

## 7. The 3-Actor Working Mode

### External Opus (this session, web/mobile chat)

- **Role:** Long-context strategy partner. Pair-thinks with Rodc on
  framing, decisions, protocol design.
- **Cannot:** Execute code, run API calls, access local files (except
  upload/paste), wake during autonomous CC shifts
- **Strengths:** Long conversation context (until compaction), strategic
  synthesis, push-back, framework design
- **Weaknesses:** Detail amnesia after compaction, no production code
  ability, cannot verify file system state

### CC (Claude Code, terminal/IDE)

- **Role:** Autonomous worker. Builds, edits, runs subagents, manages
  files locally
- **Can:** Read/write all repo files, run bash, dispatch subagents in
  parallel, autonomous shifts of 30-40h
- **Cannot:** Decide product strategy (Type-A territory), modify ship-ready
  code without explicit approval, wake Rodc
- **Strengths:** Local file system, parallel subagent orchestration, long
  autonomous work, codebase awareness
- **Weaknesses:** Same Claude model as Opus — also subject to compaction;
  no internet-wide context unless explicitly fetched

### Rodc

- **Role:** Product owner. Final decision authority on all Type-A items.
- **Decides:** Product direction, brand identity, target user, pricing,
  Phase 1 launch timing, what to ship and what to defer
- **Reviews:** All Tier 0+1+1.5+2 outputs before public launch
- **Cannot delegate:** Strategic ambivalence resolution, brand voice "is
  this me or not" judgment, pricing $ amount

### Decision tree (always applies)

- **Type A (Rodc-only):** Product strategy, brand identity, target user,
  pricing, launch timing
  - Action: AI picks conservative default + writes escalation
  - File: `docs/superpowers/tonight/escalations.md` (or session-specific)
- **Type B (AI judgment):** Engineering decisions within established product
  direction
  - Action: AI decides + documents in task decisions log
- **Type C (cross-task insight):** AI realizes earlier task was wrong while
  doing later task
  - Action: AI updates earlier task + writes to cross-task-insights.md
- **Type D (quality red flag):** AI doesn't trust its own output
  - Action: AI iterates 1-2 rounds; if still bad, escalates as Type-A

### 5 Expert Lenses (always applied to important deliverables)

1. **Senior Product Engineer** (15 years SaaS, shipped 5 products)
2. **Brand Architect** (built 2 8-figure ARR brands)
3. **SaaS Growth Operator** (0→100K MRR experience)
4. **Legal Compliance Expert** (GDPR / SaaS / sensitive data)
5. **Senior UX/Design Director** (Linear / Notion-tier polish)

These lenses serve as final review before any deliverable is marked
complete. Self-grade A-D against each lens.

---

## 8. Open Type-A Decisions Awaiting Rodc

These are pending Rodc judgment. AI sessions should not relitigate; just
flag if surfacing in current work.

- **Final brand archetype** (CC produced recommendation in Tier 0; Rodc to
  confirm or override)
- **Active recall threshold** for #2b first-insight (default 5 cards, alts
  3 / 7)
- **Card-dedup threshold** (default 3 cards same topic, alts 2 / 4 / 5)
- **Phase 1 pricing** (Task 4 produces recommendation; Rodc final $ call)
- **Free tier vs free trial** (14-day trial recommended in instruction;
  Rodc to confirm)
- **Phase 2 (Chinese launch) pricing strategy** (likely lower; not urgent now)
- **Rodix Sage vs Caregiver vs Magician archetype** — depending on Tier 0
  output, Rodc may want to override
- **Whether to publish founder essay before Rodix launch or after**
  (HN post-launch double-strategy proposed)

---

## 9. Things External Opus Might Hallucinate (Self-Flagged)

I (External Opus, dump author) explicitly note these as low-confidence:

- **Specific dates of past discussions** — I remember "Wave 1b shipped May 1ish"
  but exact dates within hours/days are blurry post-compaction
- **Exact quotes from Rodc's past push-backs** — I remember the patterns,
  not verbatim words
- **Rodc's family situation** — anything I might infer beyond "solo founder
  in Asia" is speculation
- **Specific ChatGPT/Claude/Gemini examples Rodc tried** — partial memory
- **Detailed Wave 1a history** — I joined as strategy partner mostly during
  Wave 1b. Pre-Wave-1a history limited
- **Rodc's exact technical comfort zones** — I know Rodc is technical and
  uses Claude Code, but specific stack expertise levels less clear

If asked about anything in this category, I will hedge or flag uncertainty
rather than answer with false confidence.

---

## 10. Update Protocol

When this file should change:

- **Always:** Pending TODO completion (move to "completed" or remove)
- **Always:** Phase status changes (Wave 1b shipped → Wave 2 shipping → etc.)
- **Always:** New Type-A decisions resolved (move from open to decided)
- **Often:** New constraints surfaced (legal / financial / capacity)
- **Rarely:** Identity / working style sections — these are stable

When updating:

- Replace superseded items, don't stack append-only
- Bump "Last reviewed by Rodc" date
- Note significant changes in commit message: `update rodc-context.md: X`

When NOT to update:

- Daily progress (that goes in session handoffs, not here)
- Speculative future plans (those go in plan files)
- Specific deliverables (those are their own files)

---

## 11. Onboarding instructions for fresh AI session

Whether you are CC, External Opus, or another agent encountering Rodc for
the first time in a fresh session:

1. Read this file completely (5 min)
2. Read `docs/superpowers/_state/project-status.md` (current sprint state)
3. Read latest `docs/superpowers/_state/handoffs/` file (last session
   summary)
4. Report back to Rodc in 3-5 bullet points:
   - What you understand about the project
   - What you understand about Rodc's working style
   - What you'd do first if asked to work
   - Any contradictions or gaps you spotted
5. Wait for Rodc confirm or correct before proceeding

Never start work in a fresh session without explicit Rodc confirmation
of your understanding.
