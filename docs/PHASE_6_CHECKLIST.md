# Phase 6 Regression Checklist

> Scope: English-only smoke and regression testing before flipping the
> repository public. Derived from `docs/CHINESE_STRIP_LOG.md` — every
> `HIGH` / `MEDIUM` entry maps to at least one check here.

**How to use:** work top-down. Each section is a gate — do not proceed
to the next until the previous passes. Log each PASS/FAIL in
`fixtures/phase6/RESULTS.md` (create as you go).

---

## 0. Clean-environment setup

The point of Phase 6 is to catch drift from a fresh clone, not to
re-run tests against the live developer tree.

- [ ] Fresh OS user or clean VM (Mac or Linux).
- [ ] `git clone git@github.com:jprodcc-rodc/throughline.git` into a
      path that has **never seen the private tree**.
- [ ] Copy `config/.env.example` → `.env`; fill required fields; do
      **not** reuse values from the private deployment.
- [ ] Follow `docs/DEPLOYMENT.md` end-to-end with no outside help.
      Note every doc ambiguity in `RESULTS.md` — doc-fix PRs here are
      the cheapest Phase 6 output.

**Exit criterion:** `curl $RAG_SERVER_URL/health` returns 200 and the
daemon launchd/systemd unit reaches `ACTIVE` on first boot.

---

## 1. HIGH-risk regressions (must pass)

Each of these represents a code path that was rewritten end-to-end
during migration and has never been A/B-compared against the original.

### 1.1 RecallJudge English classification (`filter/openwebui_filter.py:_RECALL_JUDGE_SYSTEM_PROMPT`)

- [ ] Create `fixtures/phase6/recall_judge_en.jsonl` with ≥ 50 turns
      covering every branch: `native`, `general` (auto recall),
      `brainstorm`, `decision`, `aggregate=true`, `topic_shift=true`,
      pronoun anaphora, meta-self, proxy-person, casual expression,
      fail-safe timeout.
- [ ] Run each turn through the real Haiku judge (`JUDGE_MODEL`
      default). Log verdict JSON + latency.
- [ ] Target: ≥ 90% match the intended label.
- [ ] Any `< 0.60` confidence verdict on a clear-cut turn is a doc or
      prompt bug — file an issue with the full prompt dump.

### 1.2 Bare pronoun gate (`_BARE_PRONOUN_RE` replacement)

- [ ] Create `fixtures/phase6/pronouns_en.jsonl` with 20 first-turn
      English pronoun-only queries (`it`, `that one`, `what about it`,
      `how's it going`, `that thing`, …).
- [ ] Verify: first-turn bare-pronoun queries do **not** trigger the
      judge (should land in the cheap gate as `noise` / `short`).
      Pronoun-only turns with history **should** trigger the judge.
- [ ] If the English cheap gate over-fires or under-fires, tune
      `_BARE_PRONOUN_RE` / cheap-gate thresholds rather than the
      judge prompt.

### 1.3 Injection-guard adversarial suite

- [ ] Port the adversarial fixture from the private tree
      (`tests/adversarial/injection_stress_v2.3.9_r2.jsonl` — 40
      targeted + 80 random non-author-persona cases).
- [ ] Land as `fixtures/phase6/injection_en.jsonl`.
- [ ] Run each payload through a live Filter + RAG round trip.
      Assert: (a) no injected instruction is executed by the
      downstream model, (b) card bodies are always wrapped in the
      `DATA not INSTRUCTIONS` envelope, (c) `CARD_CONTENT_MAX_CHARS`
      truncation fires on > 2000 char payloads.
- [ ] Any execution-of-injected-instruction is a ship-blocker.

### 1.4 Daemon four-prompt card shape (`daemon/refine_daemon.py` SLICE/REFINE/DOMAIN/SUBPATH)

- [ ] Create `fixtures/phase6/refiner_en.jsonl` with 20 slices — thin
      (< 400 tokens), medium (~2k), thick (> 5k), mixed code+prose,
      list-heavy, dialogue.
- [ ] Drive them through `daemon.refine` and assert each output
      (a) contains all six skeleton sections, (b) passes
      `_count_sections_complete >= 6`, (c) emits a
      `knowledge_identity` value from the allowed set, (d) routes to a
      real path on the shipped `daemon/taxonomy.py`.
- [ ] Any section-count shortfall or route to `System_Inbox` on a
      thick slice indicates the English heading translation diverged
      from the Python parser. File with the exact heading string.

---

## 2. MEDIUM-risk checks (should pass, document if not)

### 2.1 Concept-anchor fallback behaviour

- [ ] With `ANCHOR_TOKENS` valve empty, confirm the fallback list
      (generic tech terms) does not fire on everyday English chitchat.
- [ ] Document the expected cost: every borderline turn pays one
      Haiku judge call.

### 2.2 Ephemeral judge English calibration

- [ ] 10 English pleasantries + 10 one-liner decisions. Expected:
      pleasantries skipped, decisions refined. If skew is > 20%,
      tighten `_EPHEMERAL_PATTERNS` not the prompt.

### 2.3 RAG server cross-platform device fallback (`_pick_device`)

- [ ] Boot `rag_server/rag_server.py` on a pure-CPU host. Verify
      reranker loads without crash and responds within 5 s on a
      100-card rerank with default `max_length=512`. If slow, cut
      batch size to 32 and note the required tuning knob in
      `rag_server/README.md`.
- [ ] Boot on a CUDA host if available. Confirm CUDA path is picked
      automatically.

### 2.4 Ingest cross-platform path determinism

- [ ] Build a three-note fixture vault with ASCII-only filenames.
      Run `scripts/ingest_qdrant.py --dry-run` from (a) a Windows
      checkout, (b) a Linux checkout. Assert the three `point_id`
      values match across platforms (MD5 is stable only if
      `_norm_path` forwards-slashes correctly).

### 2.5 Taxonomy customisation

- [ ] Swap `daemon/taxonomy.py` for `config/taxonomy.example.py`
      with two or three custom leaves. Re-run a refine pass. Confirm
      router hits the custom leaves and falls back to `System_Inbox`
      on unmatched domains.

### 2.6 Contexts-topics sample sanity

- [ ] Copy `config/contexts_topics.example.json` verbatim. Populate
      `vault/00_Buffer/00.05_Profile/<topic>.md` files matching the
      example topic names. Run the contexts auto-builder. Confirm:
      (a) `<topic>__profile.md` cards are produced, (b) they show up
      in Filter valve `CONTEXT_CARDS` after one sync tick. An English
      user who took the example literally should get a working demo.

---

## 3. LOW-risk spot checks (grep-only; quick)

All scripts in this section are one-liners; no fixtures required.

- [ ] **Badge CJK snapshot** — run the Filter against three English
      turns, capture rendered outlet text, grep `[\u4e00-\u9fff]`.
      Expected: 0 matches. Any hit means a CJK string survived Phase
      2 sanitization.
- [ ] **Forbidden-prefix enforcement** — enable
      `config/forbidden_prefixes.example.json`. Create a vault note
      under the forbidden prefix. Run ingest. Confirm note is skipped
      and log line identifies it.
- [ ] **Refine-status badge** — hit `/refine_status?conversation_id=...`
      for a conversation with no refinement in flight. Confirm a
      valid one-of-seven state comes back and the Filter outlet
      renders the emoji.

---

## 4. Documentation fit-and-finish

- [ ] README top-level quickstart is reproducible by a reader who
      skips every other doc. If not, expand.
- [ ] `docs/DEPLOYMENT.md` is followed top-to-bottom without Googling
      any step. If you had to Google, patch the doc.
- [ ] `docs/FILTER_BADGE_REFERENCE.md` every badge listed was
      actually observed at least once during Phase 6. Any unobserved
      badge is either documented-but-dead (remove) or
      documented-but-rare (mark as such).
- [ ] `docs/CHINESE_STRIP_LOG.md` every `TBD — Phase 6 must create …`
      line is either resolved with a fixture path or re-scoped with
      a written rationale.

---

## 5. Results log format

Create `fixtures/phase6/RESULTS.md` with one entry per check:

```markdown
## <Section>.<Number> <Title>

- **Run date:**
- **Status:** PASS | FAIL | SKIP
- **Fixture:** path
- **Findings:** 1-3 lines
- **Follow-up issue:** #N (if FAIL)
```

When all sections PASS or have a filed follow-up issue, Phase 6 is
complete — bump README status banner from `Alpha` to `Beta` and
proceed to Phase 7 (private collaborator testing).
