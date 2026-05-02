# `#vault-recall-history` — Implementation Spec (Wave 2)

> **Status (2026-05-03):** v1.0 — implementer-ready spec. Asymmetric gate: **assumption-validation-critical** per `assumption-list.md` S16 vs W17 polarity tension. Tier 1.5 dogfood Round 11 (Mike at Day 24+) is the validation surface; production telemetry confirms ship-or-rollback at Wave 2 mid-cycle.
>
> **For agentic workers:** Use `superpowers:test-driven-development` per task. Then `superpowers:subagent-driven-development` extended with `docs/superpowers/skills/scenario-verification.md`.
>
> **App/ gitignored** — `app/web/server.py` + `app/web/static/vault.js` modifications do NOT go to git. Skip per-task `Commit ...` lines for those files. Schema file (`app/shared/schema/chat_claims_v5.sql`) + `app/shared/storage_py/chat_claim_adapter.py` ARE tracked and DO commit.

**Goal:** Surface a per-card "this thinking is being used" signal in Vault Detail. When a card is included in an Active Recall injection, atomically increment its `recall_count` and stamp `last_recalled_at`. The Vault Detail panel renders a single subdued row — `Recalled 3 times · last 2 days ago` — making the recall mechanism legible to the user. **Done 标准: see→trust→verify aha closure observable in Tier 1.5 Round 11 dogfood + ≥70% positive-or-neutral reception by alpha telemetry, OR roll back the row.**

**Architecture:**

1. **Storage** — additive migration `chat_claims_v4 → chat_claims_v5`. New columns: `recall_count INTEGER NOT NULL DEFAULT 0`, `last_recalled_at TEXT NULL` (ISO 8601). Backfill = `0` / `NULL` for all existing rows. **Decision-locked**: counter lives on `chat_claims` (not `cards`) because the recall surface is the 4-field claim payload, not the markdown card body. The `cards` table and `chat_claims` table are 1:1 in chat-flow content (a chat-saved card has one chat_claim via `messages.saved_card_id`); fixture-loaded cards have no chat_claim and are EXCLUDED from this counter (no row to increment).
2. **Increment hook** — `#active-recall-base` (Wave 2 spec 2) is the ONLY writer. When the orchestrator selects a card AND injects it into the AI prompt, before logging the recall_event row, the same transaction increments `chat_claims.recall_count` and sets `last_recalled_at`. **Atomic with the recall_event insert** — a partial write (event logged but counter unbumped) is the failure mode that breaks the audit invariant.
3. **Vault Detail UI** — `vault.js::renderCardDetail()` reads the existing detail-endpoint payload (which already serves recall_history). New copy row replaces the existing `已被 recall N 次` tag (line 329) with a friendlier "Recalled N times · last X ago" row in `--text-secondary` (#a1a1aa) on the standard surface, NOT amber. Hide the row entirely when `recall_count == 0`.
4. **Privacy** — `chat_claims` rows are scoped to the single-user vault (one user per server instance, by Phase 1 architecture). No `user_id` column needed today; defer to Wave 3 when multi-user lands. Document the discipline so Wave 3 doesn't accidentally leak counters cross-user.
5. **Performance** — `recall_count` and `last_recalled_at` are read ONLY in `GET /api/cards/{card_id}` (detail endpoint). The Vault list endpoint (`GET /api/cards?group=time`) does NOT join `chat_claims` — N+1 query risk avoided by design.

**Hard dependency:** `#active-recall-base` (Wave 2 spec 2) MUST be implemented and writing recall_events for this counter to ever increment above `0`. Without active-recall, this spec ships a permanently-zero counter — the Vault Detail row never renders, but the schema is in place. **This spec can land before `#active-recall-base`** (additive schema + always-zero render = harmless null state); the see→trust→verify validation, however, only fires once active-recall is live.

**Tech Stack:** SQLite additive migration · `chat_claim_adapter.py` extension · `app/web/server.py` detail endpoint passes new fields through · `vault.js` renderCardDetail copy row · 0 new LLM calls · 0 new background workers.

---

## §1 5项 framing

| | |
|---|---|
| Visual | Subdued row in Vault Detail panel: `Recalled 3 times · last 2 days ago`. Inter font, `--text-secondary` (#a1a1aa) on standard surface (#27272a). Below the 4-field section, above the recall history list. NOT amber — amber is reserved for active surfaces (badges, recall callouts), counter is passive metadata. |
| 产品策略假设 | Recall transparency = the visible mechanism behind "Rodix remembers your thinking" (brand book §1 hero pitch). User sees the counter increment over time → see→trust→verify aha closure. ChatGPT memory is opaque ("I remember some things"); Rodix shows the receipt. **This is the white-box transparency commitment (Decision 1) operationalized at the per-card level.** |
| 适合 / 不适合 | **适合**: Heavy AI users who want auditable AI behavior (per brand book §3 ICP). They evaluate AI products on whether the product respects their thinking — counter is the receipt. **不适合**: Users who experience visible counters as anxiety surface (cf. unread-badge fatigue) — but this row is opt-in-by-detail-view, NOT pushed via badge. They never see it unless they open a Card. Anti-target users who want quick answers (D5 fail mode) won't open Vault Detail anyway. |
| Trade-off | + **see→trust→verify aha closure** — user observes thinking-being-used over time / + zero LLM cost / + zero new background work / − **surveillance polarity flip risk (W17 + brand-book §appendix item 4)** — counter could read as "Rodix is watching me" if recall density too high / − schema migration risk on existing chat_claims data / − adds detail-endpoint payload size by 2 fields (negligible). |
| 最大风险 | **Surveillance flip (W17 + brand-book §appendix item 4 explicitly named).** S16 says "users will recognize a recall callout as helpful, not intrusive" — **strong, not validated**. W17 says recall density risk → polarity flip. This counter is a SECONDARY surveillance signal layered on the recall callout itself. If users react to recall callouts as creepy AND see the counter incrementing, they double down on the negative read. **Mitigation**: Tier 1.5 Round 11 (Mike at Day 24+) explicitly observes counter reaction; if creep-vs-trust polarity flips, **roll back the row** (keep the schema for future use; hide the UI). Schema is harmless when the row is hidden. |

## §2 Ambiguity flag

✓ **No ambiguity.** Decision points all locked at v1.0:

Locked decisions:
- **Counter lives on**: `chat_claims` (not `cards`). Reason: recall surface is the 4-field claim payload; `cards` is the markdown body shell. A fixture-loaded card with no chat_claim has no recall_count to track (no claim was ever extracted, so no thinking-being-used signal exists for that card).
- **Increment trigger**: when `#active-recall-base` injects the card into the AI prompt — i.e., the moment of system-level recall, NOT when the user clicks the recall callout. This is the **system-event-counter, not user-event-counter** distinction (see §5 edge case 1).
- **Display rule for `recall_count == 0`**: hide row entirely. Don't surface "Not yet recalled" — feels weird (per spec instruction).
- **Display rule for `recall_count >= 50`**: show exact number ("Recalled 87 times"). Transparency over politeness, per brand book §7 Decision 1 white-box commitment.
- **Decrement rule**: NEVER. Counter is monotonic. Deleting a recall_event row does NOT decrement chat_claims.recall_count. Reason: the counter records system attempts (what Rodix tried to do), not user-validated recall hits (what the user kept). Document this design choice in §5 explicitly so future implementers don't add a "recompute" job that "fixes" the gap.
- **Atomicity**: increment + recall_event insert wrapped in single SQLite transaction in the orchestrator's persist path. If the increment fails (e.g., row not found because chat_claim was deleted between selection and injection), the recall_event still logs (with selected_card_id pointing to a now-orphan chat_claim) and the increment is silently skipped. Reason: recall_events FK is `ON DELETE SET NULL` for `selected_card_id`; we never crash the recall pipeline because of a missing claim row.

Open question (deferred to Wave 3): when multi-user lands, `recall_count` per-user is the correct semantic. Today (single-user Phase 1), no `user_id` column needed.

## §3 Trigger

The counter increments **iff** all three conditions hold:

1. `#active-recall-base` orchestrator selected a card via `OrchestratorContext` (highest-scoring candidate above per-trigger threshold).
2. The selected card's `chat_claim` row exists (was extracted by `#claim-extraction` post-thoughtful chat).
3. The card content was actually injected into the AI prompt (not just considered-but-cap-rejected).

**Out of scope (do NOT increment):**
- User clicks the ⚡ recall callout's "用上了" button — this is a USER reaction, not a system attempt. Reactions live in `recall_events.user_action`, not in the counter.
- User views the card in Vault Detail — viewing is not recall.
- `claim_extraction` runs on a new chat turn — extraction is not recall.
- Card deleted by user → counter on the now-deleted chat_claim is GC'd via FK cascade (chat_claims FK `message_id` → messages, ON DELETE CASCADE; deleting the conversation cascades through). The increment write that may have been pending is no-op'd silently.

**Hard dependency on `#active-recall-base`:** without that spec implemented, no recall_event ever logs and no card ever gets injected, so this counter is permanently `0`. The vault detail row stays hidden. **This spec is harmless to ship before `#active-recall-base` lands** — additive migration with zero defaults + hide-on-zero render = invisible. Once `#active-recall-base` ships, the counter starts incrementing organically.

## §4 Visual & copy

**Vault Detail panel** (`vault.js::renderCardDetail()`):

- **Location**: below the 4-field section (existing line 367-368), above the recall history list. New `<section class="vault-detail-recall-summary">`.
- **Markup**:
  ```html
  <div class="vault-detail-recall-summary-row">
    Recalled <strong>3</strong> times · last <span>2 days ago</span>
  </div>
  ```
- **Style** (add to `app.css`):
  ```css
  .vault-detail-recall-summary-row {
    color: var(--text-secondary);   /* #a1a1aa */
    font-family: Inter, sans-serif;
    font-size: 13px;
    line-height: 1.6;
    padding: 8px 0;
    border-top: 1px solid var(--border-subtle);
  }
  .vault-detail-recall-summary-row strong {
    color: var(--text-primary);     /* #fafafa — slight emphasis */
    font-weight: 600;
  }
  ```
- **No amber.** Amber is for active surfaces (Vault badge pulse, recall callout, sticky date headers). This row is passive metadata.
- **Copy ceiling**: ≤ 60 characters per voice guide §B (toast-class). Verbatim: `Recalled N times · last <relative time>`.
- **Relative time formatting**: `last 2 hours ago` / `last 2 days ago` / `last 3 weeks ago` / `last 5 months ago`. Existing `formatLongTime()` in `vault.js` handles long-form; add `formatRelativeShort()` for relative deltas. Resolution buckets: hours / days / weeks / months / years. Never "just now" — too cute; use "less than an hour ago".
- **Hide-on-zero**: if `recall_count == 0` OR `last_recalled_at == null`, do NOT render the section.

**Brand-book §6 visual identity compliance:**
- ✓ Background warm dark (#18181b) preserved (no override)
- ✓ Inter font (no system fallback)
- ✓ `--text-secondary` (#a1a1aa) — within locked palette
- ✓ NO emoji in this row (per Decision 1 + §6 "no emoji adornments" — the ⚡ glyph is the in-product chat AI character, NOT vault metadata; metadata is Explorer voice = anti-decoration)
- ✓ NO amber (amber is verification color for active surfaces, not metadata)

**Brand-voice (§5 voice guide §6 Q1-Q5):**
- Q3 (specific): ✓ exact count + concrete relative time
- Q5 (don't coax): ✓ no "Awesome! Recalled 3 times!" / no "Your thinking is helping you grow!" — flat statement. Just the receipt.
- "Recalled" — passive verb, anti-spin. NOT "Rodix has helped you N times" (Caregiver register, banned).

**Anti-pattern (do NOT ship):**
- ❌ `🔁 Recalled 3 times` (decorative emoji, banned per §6 + decision 5)
- ❌ `Rodix brought this back 3 times!` (exclamation marks banned per voice guide; "brought this back" is the recall callout copy lock — reuse-collision in metadata register)
- ❌ Amber color on the count number (would imply active state when this is metadata)
- ❌ Hover tooltips explaining recall_count (over-engineering; the row is the explanation)

## §5 Edge cases & design decisions

### Edge case 1: Card recalled but user didn't click ⚡ callout

**Decision: still increments.** We're tracking system behavior (what Rodix attempted), not user-validated recall hits.

**Rationale:** the alternative ("only count when user clicks 用上了") would mean the counter underrepresents recall density by 95%+ (most micro-feedback features see <5% click engagement per assumption W5). The counter would feel "broken" — 50 recalls fire, counter shows 2. **The counter is the audit trail of recall attempts, not the success log.** User reactions (`用上了 / 不相关 / 已经想过 / 跳过`) are surfaced separately in the per-event recall history list (already rendered by `renderCardDetail`), where the granular reaction belongs.

**Document this in code comment:**
```python
# chat_claim_adapter.py::increment_recall_count
# NOTE: Counter is system-event-counter, NOT user-event-counter.
# We increment when the orchestrator INJECTS the card (system attempt),
# not when the user clicks "用上了" (reaction). The per-event reaction
# is captured separately in recall_events.user_action. Do NOT add a
# "recompute counter from clicks" cron — that would change the semantic
# from audit-trail to success-log silently.
```

### Edge case 2: Imported card from history (Wave 1b #9a `source='imported'`)

**Decision: starts at `recall_count = 0`.**

Imported cards are eligible for active recall once a user message can map to them (per `#active-recall-base` semantic-similarity matching against existing claims). The counter starts cold — same as native cards — and grows organically only when recall actually fires. This is correct: imported cards represent past thinking the user has not yet brought back; counter at 0 reflects that.

### Edge case 3: `recall_count >= 50`

**Decision: show exact number.** `Recalled 87 times · last 2 days ago`.

**Rationale:** transparency over politeness, per brand book §7 Decision 1. "Many times" is the personalization-fudge ChatGPT does ("I remember some things from our past conversations") — Rodix shows the receipt. If the user opens Vault Detail and sees 87, that IS the experience: the system has been bringing this card back consistently.

**Sanity check (alpha calibration):** if median recall_count at Day 30 is >50 in alpha telemetry, the recall thresholds in `#active-recall-base` are likely too loose. This is the surveillance-flip canary (W17). Counter at 87 reads as "watched"; counter at 7 reads as "useful". Adjust thresholds, not the display rule.

### Edge case 4: `recall_count == 0` (zero recalls)

**Decision: hide row entirely.**

**Rationale:** "Not yet recalled" surfaces an absence the user wasn't asking about, with implicit "we'll get there!" energy that violates voice principle 5 (no soft hedges). A clean card with no recall metadata is the correct empty state. The 4-field section + recall history (also empty, also hidden) + quote = sufficient. Adding a "Not yet recalled" row would clutter the panel for the dominant case (most cards in early alpha will be at 0).

**Implementation:** `if (recall_count > 0 && last_recalled_at) { render row }`. Both conditions required (defensive against schema drift).

### Edge case 5: Recall counter "decremented" (user deletes a recall event)

**Decision: NEVER decrement.** Counter is monotonic.

**Rationale:** The counter is system-event-counter, not user-event-counter. Even if the user could delete a `recall_event` row (Wave 1b currently has no such UI; Wave 2+ may add a "this recall was wrong, hide from history" affordance), deletion of the event row reflects user-side data hygiene, not "the system never tried." The audit invariant is: **`recall_count` equals total system-attempted injections of this card, ever**. Backfill from migration uses 0 default; no recompute job ever runs.

**Alternative considered and rejected:** "Sync recall_count from `SELECT COUNT(*) FROM recall_events WHERE selected_card_id = ?` on each delete." Rejected because (a) it changes counter semantic from audit-trail to live-count, (b) it adds a query on every recall_event delete, (c) it lets the user "rewrite history" by deleting events — incompatible with brand book §7 Decision 1's white-box-transparency commitment to the user (deleting an event hides it from view but the system DID try).

### Edge case 6: Migration partial failure mid-flight

**Decision: migration is purely additive (ALTER TABLE ADD COLUMN with DEFAULT). Atomic at the SQLite level — succeeds or whole DDL is rolled back.**

**Rollback path** (if migration fails): revert to `chat_claims_v4.sql`. The new columns simply do not exist; all writes targeting `chat_claims` continue to work (they use named columns; v5 columns are not in the v4 INSERT). Detail endpoint returns `recall_count = 0` / `last_recalled_at = null` defensively (server-side fallback in `_hydrate_card_claim`); UI hides row.

**Failure mode that breaks rollback:** if any code path was already writing to v5 columns when migration is rolled back, those writes silently fail. Mitigation: env-var seam `THROUGHLINE_RECALL_COUNTER_ENABLED=1` (default off until migration verified in Tier 1.5 dogfood); orchestrator increment path is gated behind this env var. **Operator can disable the counter without rolling back the schema.**

### Edge case 7: Concurrent increments (race condition)

**Decision: SQLite single-writer model + transaction wrap in orchestrator persist path = no race.** A single Python process (Phase 1 architecture) cannot have two concurrent recall pipelines for the same conversation. The increment is `UPDATE chat_claims SET recall_count = recall_count + 1, last_recalled_at = ? WHERE id = ?` — atomic at the SQL level, no read-modify-write race.

**Future-proofing for Wave 3 multi-process:** if Wave 3 introduces a multi-worker recall pipeline, this UPDATE remains race-safe (SQL atomic increment). No changes needed.

## §6 Files

**Modify** (gitignored — no commit):
- `app/web/server.py` — `_hydrate_card_claim()` extends to read `recall_count` / `last_recalled_at` from `chat_claims`; `GET /api/cards/{card_id}` detail response carries `claim.recall_count` + `claim.last_recalled_at`.
- `app/web/static/vault.js` — `renderCardDetail()` adds the recall summary row between 4-field section and recall history list. Replace the existing `已被 recall N 次` tag (line 329) with the new row (or remove the tag, leave only the new row — implementer's call, but DON'T render both).
- `app/web/static/app.css` — add `.vault-detail-recall-summary-row` styles per §4.

**Modify** (tracked — commit normally):
- `app/shared/schema/chat_claims_v4.sql` — UNCHANGED. Do not edit; v5 is a separate file.
- `app/shared/storage_py/chat_claim_adapter.py` — extend `ChatClaimRow` dataclass with `recall_count: int = 0` + `last_recalled_at: Optional[str] = None`. Add `increment_recall_count(conn, claim_id, *, now_iso)` function. Add `get_chat_claim_with_recall(conn, message_id)` if needed for the detail-endpoint hot path.
- `app/shared/storage_py/test_chat_claim_adapter.py` (or wherever existing tests live) — extend with increment tests.

**Create** (tracked — commit normally):
- `app/shared/schema/chat_claims_v5.sql` — additive migration `ALTER TABLE chat_claims ADD COLUMN recall_count INTEGER NOT NULL DEFAULT 0; ALTER TABLE chat_claims ADD COLUMN last_recalled_at TEXT NULL;` + bump `PRAGMA user_version`.
- `app/shared/storage_py/test_chat_claim_recall_count.py` — unit tests for increment, idempotency, monotonic invariant.

**Touch lightly** (gitignored — no commit; only if `#active-recall-base` already landed):
- `app/shared/recall/orchestrator.py` (or its persistence boundary) — add the `chat_claim_adapter.increment_recall_count()` call in the same transaction as the recall_event insert. **Gated behind `THROUGHLINE_RECALL_COUNTER_ENABLED=1` env var** until Tier 1.5 Round 11 dogfood validates.

## §7 Asymmetric gate (assumption-validation-critical)

**This spec validates a brand-level assumption (S16) against a brand-level risk (W17 + brand-book §appendix item 4 surveillance-fail-mode).**

**Hypothesis to validate:** showing `recall_count` makes the user feel *"Rodix is using my thinking"* (positive — see→trust→verify aha closure, the visible mechanism behind brand-book §1 hero pitch).

**Counter-hypothesis (W17):** showing `recall_count` makes the user feel *"Rodix is watching me"* (surveillance flip; brand-book §appendix item 4 named explicitly).

**Validation surface: Tier 1.5 Round 11 (Mike at Day 24+).** Persona Mike has been using Rodix for 24+ simulated days; his vault has accumulated cards; some cards have been recalled multiple times. Round 11 walks Mike opening Vault Detail on a high-recall-count card (≥3 recalls) and observing the row. **Capture verbatim Mike's reaction.**

**Production gate (post-Phase-1-launch alpha):**
- ≥ 70% of users who view Vault Detail on a card with `recall_count > 0` either (a) interact positively with the row OR (b) do NOT dismiss / express creep about the row in support feedback.
- Telemetry: log `vault_detail_view{has_recall_summary=bool}` + `vault_detail_dismiss_recall_summary` (if dismissable affordance lands in Wave 2 polish; Phase 1 scope is non-dismissable).

**Calibration trigger (rollback path):** if alpha telemetry shows
- creep-reaction language in support tickets ("creepy", "watching me", "is this surveillance?") above 5% of card-detail-view sessions
- OR support-ticket sentiment-flip on the recall feature post-counter-launch (compared to pre-counter-launch baseline from Round 11 dogfood)

→ **roll back the row** (env-var-disable the render in `vault.js`; counter continues incrementing in DB silently). Schema stays. Re-evaluate at Wave 2 mid-cycle.

**Why this is asymmetric, not symmetric, gating:** the cost of WRONG render (creep-flip) is brand-existential (per brand-book §appendix item 4 escalation: "P0 brand risk"). The cost of MISSING render (zero-recall hidden) is feature dormancy (mild; user just doesn't see the receipt yet). So the gate biases toward HIDE on ambiguity.

## §8 Bite-sized TDD tasks

- [ ] **Task 1: Schema migration `chat_claims_v4 → v5`**
  - Write failing test `test_chat_claim_recall_count.py::test_v5_migration_adds_columns_with_zero_defaults` — load schema, verify `recall_count` and `last_recalled_at` columns exist with correct types and defaults
  - Write `test_v5_migration_backfills_existing_rows_to_zero` — insert a v4-shape row before migration, run migration, verify row's recall_count = 0 / last_recalled_at = NULL
  - Implement `app/shared/schema/chat_claims_v5.sql`:
    ```sql
    ALTER TABLE chat_claims ADD COLUMN recall_count INTEGER NOT NULL DEFAULT 0;
    ALTER TABLE chat_claims ADD COLUMN last_recalled_at TEXT NULL;
    ```
  - Bump schema loader's PRAGMA user_version to 5
  - PASS
  - Commit: `feat(schema): chat_claims v5 — add recall_count + last_recalled_at`

- [ ] **Task 2: ChatClaimRow dataclass extension**
  - Write failing test `test_chat_claim_recall_count.py::test_chat_claim_row_carries_recall_fields` — insert claim, verify default recall_count=0 / last_recalled_at=None
  - Extend `ChatClaimRow` dataclass with `recall_count: int = 0` and `last_recalled_at: Optional[str] = None`
  - Update `_row_to_chat_claim()` to read the new columns
  - Update `insert_chat_claim()` to pass through recall_count / last_recalled_at on INSERT OR REPLACE (preserves counter on idempotent re-extraction; without this, re-extracting the same chat_claim resets the counter to 0 — a bug)
  - PASS
  - Commit: `feat(chat-claim): extend adapter with recall_count + last_recalled_at fields`

- [ ] **Task 3: `increment_recall_count` API**
  - Write failing test `test_increment_recall_count_increments_by_one` — insert claim with count=0, call increment, verify count=1 and last_recalled_at is now-ish
  - Write `test_increment_recall_count_is_atomic` — mock-patch UPDATE to fail, verify no partial state (transaction rolls back)
  - Write `test_increment_recall_count_on_missing_claim_returns_false` — call increment with non-existent id, verify returns False (no exception); document silent-skip semantic in code
  - Write `test_increment_recall_count_does_not_decrement` — call increment N times, verify count=N (sanity check + documents monotonic invariant)
  - Implement:
    ```python
    def increment_recall_count(
        conn: sqlite3.Connection,
        claim_id: str,
        *,
        now_iso: Optional[str] = None,
    ) -> bool:
        """Atomic increment of chat_claims.recall_count + stamp
        last_recalled_at. Returns True iff the row exists and was
        updated; False if claim_id not found (silent skip — never
        raises).

        SEMANTIC: counter is system-event-counter, not user-event-
        counter. Increment on system injection (orchestrator -> AI
        prompt), NOT on user click. Monotonic; never decrement.
        """
        if now_iso is None:
            now_iso = _now_iso()
        with conn:
            cur = conn.execute(
                """
                UPDATE chat_claims
                SET recall_count = recall_count + 1,
                    last_recalled_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (now_iso, now_iso, claim_id),
            )
            return cur.rowcount > 0
    ```
  - PASS
  - Commit: `feat(chat-claim): atomic increment_recall_count with monotonic invariant`

- [ ] **Task 4: Detail endpoint payload extension**
  - Write failing test `app/web/test_card_detail_endpoint.py::test_detail_includes_recall_count_when_claim_exists` — fixture chat_claim with recall_count=3, GET /api/cards/{id}, verify `claim.recall_count == 3` + `claim.last_recalled_at` populated
  - Write `test_detail_returns_zero_recall_count_when_no_claim` — fixture card with no chat_claim, verify response defaults claim.recall_count=0 (or claim=null, depending on existing `_hydrate_card_claim` behavior — preserve)
  - Modify `_hydrate_card_claim()` in `server.py` to extend the claim dict with `recall_count` + `last_recalled_at` when the chat_claim row is present
  - Verify `GET /api/cards?group=time` (list endpoint) does NOT join chat_claims — N+1 audit
  - PASS
  - (No commit for `app/web/server.py` — gitignored. `app/web/test_card_detail_endpoint.py` IS tracked, commit normally.)

- [ ] **Task 5: Vault Detail UI render**
  - Visual TDD: open Vault Detail on a fixture card with recall_count=3 and last_recalled_at=2-days-ago → row renders as `Recalled 3 times · last 2 days ago`
  - Open Vault Detail on a card with recall_count=0 → row does NOT render
  - Open Vault Detail on a card with recall_count=1 → row renders as `Recalled 1 time · last <relative>` (singular)
  - Open Vault Detail on a card with recall_count=87 → row renders verbatim "Recalled 87 times · last <relative>" (transparency over politeness)
  - Replace the existing `已被 recall N 次` tag (line 329) with the new row (or move the count out of the header tag and into the dedicated section — implementer's call; the new row is the canonical surface)
  - Add `formatRelativeShort(iso_timestamp, now=Date.now())` helper alongside existing `formatLongTime`
  - Verify Inter font + `--text-secondary` color + NO amber + NO emoji
  - (No commit — `vault.js` + `app.css` gitignored.)

- [ ] **Task 6: Orchestrator increment hook (gated)**
  - **Pre-condition**: `#active-recall-base` Wave 2 spec 2 has shipped or is shipping in parallel; orchestrator persist path exists.
  - Write failing test `app/shared/recall/test_orchestrator.py::test_inject_increments_chat_claim_counter` — orchestrator.persist(selected_card_with_claim) → verify chat_claims row's recall_count went from 0 to 1
  - Write `test_inject_does_not_increment_when_env_var_disabled` — set `THROUGHLINE_RECALL_COUNTER_ENABLED=0`, persist → verify counter stays at 0 (recall_event still logged)
  - Write `test_inject_skips_increment_silently_when_no_chat_claim` — orchestrator selects a fixture-loaded card (no chat_claim) → verify recall_event logs, no increment, no exception
  - Implement gated increment in orchestrator persist path. Default env-var to OFF until Tier 1.5 Round 11 validates.
  - PASS
  - (No commit for `orchestrator.py` — app/ gitignored. Gated env var default OFF.)

- [ ] **Task 7: Tier 1.5 Round 11 dogfood validation**
  - **Why this is a separate gate**: even a passing unit test bar can hide a brand-level surveillance flip. S16 vs W17 polarity tension is not statistically gateable — it's a felt-experience signal.
  - **Process**:
    1. Implementer flips `THROUGHLINE_RECALL_COUNTER_ENABLED=1` in dogfood environment.
    2. Tier 1.5 Phase A simulates Mike at Day 24+. Mike's vault has 5+ cards with `recall_count >= 1` (some with 3+).
    3. Mike opens Vault Detail on his highest-recall card. Captures verbatim subjective reaction in dogfood log.
    4. Categorize reaction: TRUST_POSITIVE / NEUTRAL / CREEP_NEGATIVE / CONFUSED (doesn't understand what counter means).
  - **Outcome resolution**:
    - TRUST_POSITIVE or NEUTRAL → ship with row visible at Phase 1 alpha launch (env var default ON).
    - CREEP_NEGATIVE → roll back row visibility (env var default OFF). Schema stays for re-evaluation at Wave 2 mid-cycle.
    - CONFUSED → micro-iterate copy ("Recalled" → "Brought back" or similar; preserve Explorer voice constraints) and re-walk.
  - Dogfood verdict updated in `private/dogfood-rounds.md` + roadmap status note.
  - (No code change.)

- [ ] **Task 8: Telemetry hooks for production calibration**
  - Add `INFO recall_count_incremented chat_claim_id={x} new_count={n} card_id={y}` log line in increment path
  - Add `INFO vault_detail_recall_summary_rendered count={n}` in `vault.js` (use existing analytics endpoint if present; else log to console for alpha — Wave 2 instrumenation upgrade tracked separately)
  - These log lines feed the calibration trigger in §7: parse for creep-language correlation + recall density distribution
  - PASS by inspection
  - (No commit — gitignored.)

- [ ] **Task 9: End-to-end code-level verification + S-VAULT-RECALL-1 scenario**
  - Verify pipeline: thoughtful chat → claim_extraction creates chat_claim → time passes → user starts new conversation on related topic → `#active-recall-base` selects the chat_claim's card → orchestrator injects + increments counter → user opens Vault Detail → row renders with new count
  - Verify edge cases all covered: zero-count hides, monotonic increment, no decrement on event delete, 87-count shows verbatim, fixture-loaded card no-op, imported card no-op until first real recall
  - Run full app test suite — all green
  - **Add new scenario to product-test-scenarios.md**: `S-VAULT-RECALL-1: Vault Detail recall summary row renders correctly across recall_count spectrum (0 / 1 / 3 / 87)`. Author CC, Rodc reviews at Wave 2 wave-end spot check.
  - **Document the scenario in §References below** for the implementer dispatch report
  - PASS

## §9 Done criteria

- [ ] `chat_claims_v5.sql` additive migration lands with bump to PRAGMA user_version ✓
- [ ] `ChatClaimRow` dataclass + adapter functions extended ✓
- [ ] `increment_recall_count()` atomic, monotonic, silent-skip on missing ✓
- [ ] Detail endpoint payload extends with recall_count + last_recalled_at; list endpoint UNCHANGED (N+1 audit) ✓
- [ ] Vault Detail UI renders summary row per §4 visual spec; hides on zero ✓
- [ ] Orchestrator increment hook gated behind `THROUGHLINE_RECALL_COUNTER_ENABLED` env var ✓
- [ ] Tests green: full app suite + new unit + new integration ✓
- [ ] **Tier 1.5 Round 11 dogfood verdict TRUST_POSITIVE or NEUTRAL** (or rollback path activated per §7) ✓
- [ ] **Scenario verification**: S-VAULT-RECALL-1 (new, document and run) ✓
- [ ] Telemetry hooks live for production calibration trigger ✓
- [ ] Brand-book §6 visual identity audit: Inter font ✓ / palette compliance ✓ / no emoji ✓ / no amber on metadata ✓

## §10 7项

1. ✓ `[PRODUCT_NAME]` 占位: N/A — copy is "Rodix" once `#r-name-final` lock applied; Phase 1 already locked (per memory `project_rodix_name.md`).
2. ✓ Desktop-first: ✓ — Vault Detail panel is desktop-primary surface; mobile responsive tier collapses to fullscreen detail (existing `vault-back-btn` pattern preserved); recall summary row scales naturally.
3. ✓ §1 5项 articulated above.
4. ✓ Pre-mortem 4 modes:
   - **like-me user**: Rodc himself — would Rodc want to see his counter? Yes. Heavy AI user wants the receipt. ✓
   - **metric vs goal**: counter is a metric (system attempts) presented as user-facing; the goal is see→trust→verify aha closure. Risk: counter becomes goal (gamification) — explicitly rejected via "no celebratory framing" §4. ✓
   - **reactive vs strategic**: this spec is STRATEGIC (transparency = brand commitment), not reactive (no user complained "I want a counter"). The pre-emptive validation gate (§7) acknowledges strategic specs need experimental discipline. ✓
   - **edge case vs main path**: surveillance-flip (W17) IS the main risk, not an edge — explicitly named in §1 5项 and §7. The `recall_count == 0` edge is well-handled (hide). ✓
5. ✓ 桌面横向利用率: ✓ — adds 1 row of vertical space, no horizontal change.
6. ✓ Mobile responsive: ✓ — row inherits existing detail panel responsive layout; no dedicated mobile work.
7. ✓ Empty state: ✓ — `recall_count == 0` is the empty state; hide row entirely. Section §5 edge case 4 documents.

## §11 Risk register

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Surveillance polarity flip (W17 + brand-book §appendix item 4)** — counter reads as "watched" not "useful" | medium | brand-existential (P0 risk per brand book) | Tier 1.5 Round 11 dogfood + production telemetry trigger + env-var rollback path (schema stays, UI hides) |
| R2 | Migration partial failure (column add fails on a corrupted DB) | low | medium | additive ALTER (no destructive ops) + test migrates fresh + populated DBs + `THROUGHLINE_RECALL_COUNTER_ENABLED=0` operator escape hatch lets users continue with new DB schema unused |
| R3 | Counter desync — recall_event logged but counter not incremented (or vice versa) | low | low | both writes in single transaction in orchestrator persist path; if atomicity assumption breaks, audit invariant fails — add periodic invariant check `chat_claims.recall_count == COUNT(recall_events.selected_card_id matching this claim's card_id)` as P2 monitoring (NOT a recompute job — read-only assertion) |
| R4 | INSERT OR REPLACE on chat_claim re-extraction wipes recall_count | medium | medium | Task 2 explicitly preserves recall_count on idempotent re-extract; test locks the behavior |
| R5 | Vault Detail UI clutter from adding a row | low | low | passive metadata register + 13px secondary color + hide-on-zero = invisible until earned; no growth in cognitive load |
| R6 | Counter becomes a vanity metric / gamification | low | brand register erosion | §4 explicitly rejects celebratory framing; copy ceiling enforces flat statement; no streak / badge / emoji |
| R7 | Tier 1.5 dogfood persona Mike confused (CONFUSED outcome) | medium | low | iterate copy 1 cycle; "Recalled" is the most semantically clean verb tested; if confused → "Used N times in conversations" as fallback, but verify still preserves Explorer voice |

## §12 Post-launch follow-ups (P2)

- **Recall summary on hover-tooltip in Vault list view**: P2 enhancement — list view rows show subtle dot-indicator if `recall_count > 0`, hover shows `Recalled 3 times · last 2 days ago`. **Reject for Phase 1** (N+1 query risk on list view + clutters list). Revisit at Wave 3 with proper aggregation query.
- **Recall summary in markdown export**: append `Recalled: 3 times (last 2026-04-30)` to per-card markdown frontmatter. **Reject for Phase 1** (export is "your data, your file" semantic — exporting system telemetry mixes data layers). Revisit when export surface settles.
- **Per-trigger-type breakdown** (`Recalled 3 times · 2 topic / 1 stance_drift`): power-user transparency — useful but premature. Defer to alpha telemetry → "do users want to see WHY each recall fired?" If yes → Wave 2 mid-cycle UI iteration.
- **Decrement on user-explicit "this recall was wrong"**: rejected per §5 edge case 5 (semantic conflict). Revisit only if surveillance-flip telemetry shows users want this lever explicitly.
- **`user_id` column when multi-user lands**: Wave 3 concern. Document the discipline: counter is per-user; cross-user reads are forbidden. Add at multi-user spec dispatch.

## §13 References

- **Spec inputs**: brand-book-v1.md §1 hero pitch (visible mechanism = trust-verify aha) + §7 Decision 1 (white-box transparency) + §appendix item 4 (surveillance-flip P0 risk preservation); voice-guide.md §6 (consistency checklist) + §B (word-count ceilings); assumption-list.md S16 vs W17 polarity tension.
- **Hard dependency**: `#active-recall-base` (Wave 2 spec 2). Counter increments require recall pipeline. This spec safe to land before; render only fires once dependency live.
- **Schema prior art**: `app/shared/schema/chat_claims_v4.sql` (current schema), `cards_v3.sql` (additive-migration pattern reference).
- **Adapter prior art**: `app/shared/storage_py/chat_claim_adapter.py` (extend the `ChatClaimRow` dataclass + add atomic UPDATE).
- **UI prior art**: `app/web/static/vault.js::renderCardDetail()` line 325-332 (existing `已被 recall N 次` tag — replace or repurpose).
- **Endpoint prior art**: `app/web/server.py::get_card_detail()` line 1948-1999 + `_hydrate_card_claim()` (extend payload).
- **Validation surface**: `private/dogfood-rounds.md` Round 11 (Mike at Day 24+); production calibration trigger via support-ticket sentiment + recall density telemetry.
- **Scenarios**: S-VAULT-RECALL-1 (NEW — author CC at Task 9, Rodc spot-check at Wave 2 wave-end).
- **Roadmap**: Wave 2 spec 5 (this spec); depends on `#active-recall-base` (Wave 2 spec 2); informs Wave 2 mid-cycle telemetry calibration; brand-book §appendix item 4 P0 escalation surface.

---

*End spec-vault-recall-history.md v1.0. Implementer-ready pending Rodc + external review approval per `feedback_plan_review_protocol.md` (Plan v1 → Rodc + external Opus review → push backs → v1.X "approved for dispatch").*
