# `#card-real` — Real 4-field Card-with-Promise (replace Wave 1a/1b placeholder)

> **Status (2026-05-03):** Wave 2 P0 spec. Implementer-ready. Depends on `#claim-extraction` v1.8 ship-ready (Haiku 4.5 split-route, 79.3% overall, 2.3% hallucination rate per `fixtures/v0_2_0/eval/results-anthropic-claude-haiku-4-5-*.json`). No backend extraction work — Wave 1b shipped that. **In-scope: frontend-only Card render upgrade + click-through to vault** + a small server-side detail accessor for the vault-detail route. Out-of-scope: extraction prompt iteration (frozen at v3.1), recall-callout strings (sibling spec `#active-recall-base`), schema migration (chat_claims_v4 already supports 4-field).
>
> **Trail:** Wave 1a `#8` shipped a 4-field stub seeded from `_stub_claim_placeholder()` in `app/web/server.py:180`. Wave 1b shipped real extraction (`#claim-extraction`) routed through Haiku 4.5 with polling endpoint `GET /api/claim/by_message/{id}` returning the real `chat_claims_v4` row. The Card-with-Promise UI in `app.js::renderClaimCard` (line 373) already swaps in real extracted data on a polling hit — but the displayed strings, click affordance, and concern-as-list handling were built for stub data and have known gaps now that real extracted variants are flowing.
>
> **For agentic workers:** Use `superpowers:test-driven-development` per task. App/ is gitignored — `app/web/static/app.js`, `app/web/static/app.css`, `app/web/server.py` modifications do NOT go to git. Tests in `app/web/test_*.py` are also gitignored. Skip the per-task `Commit ...` lines for those files. Documentation diffs (this spec, `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` if scenarios extend) DO commit.

---

## 1. What

Today the Card-with-Promise after every thoughtful AI reply is **rendered with real extracted fields** (Wave 1b polling delivers the chat_claims row), but the surface still carries Wave 1a placeholder affordances: a static `已记下` label, a static `→ Vault +1` hint, no click target, and no graceful handling of the multi-variant `concern: list[str]` shape that the v1.7 ground-truth relabel introduced. Per friends-intro: *"You see every one. Edit, delete, export."* That promise is the `#card-real` deliverable — the user can not only *see* the 4 fields, they can *click into* the source-of-truth vault entry, with the actual extracted wording in their own voice.

This spec turns the Card from a *receipt* surface into the *first interaction* with that thought's vault entry. Click-through navigates to `Vault tab → that card's detail panel` (existing `#3a` cards-management route, no new vault chrome). The label changes from "the system is pleased with itself" (`已记下`) to "this is what you said, and you can take it from here" (locked copy resolved in §9 below). Per brand-book §7 Decision 1 (white-box thinking cards): *"every card is traceable to the conversation that produced it, every card is editable and deletable."* The render must show actual user-voiced wording, not a paraphrase — `claim_extractor.md` enforces this at the data layer (*"Extract using user's own wording, 4-8 words preferred, do NOT paraphrase"*); this Card is its visible counterpart.

The Card validates 3 assumptions in `assumption-list.md`. **S15** (*"Users will understand 'topic / concern / hope / question' 4-field schema without explanation"*) is tested by whether users read the 4 fields and find them coherent, not whether the schema is annotated. **W11** (*"Users will keep cards in their vault rather than purging them"*) gets its first behavioral signal — does the user click through, or does the Card scroll out of view? **V3** (already validated at the eval-set level — *2.3% hallucination rate, 256 EN field decisions*) is exposed to real production traffic for the first time; if hallucinations creep above 5% sustained, the calibration trigger fires and Wave 1b prompt iteration re-opens (per claim-extraction plan v1.8 §"Calibration trigger").

## 2. Why

Wave 1a's `已记下` + `→ Vault +1` was a stub that worked because there was nothing to click into yet (Vault was a future tab) and nothing to display except canned strings. Wave 1b shipped real extraction + the Vault tab + cards-management UI. Wave 2 closes the loop: the Card stops being a *toast-shaped notification* and becomes the *first object the user can act on*. Without this, the user has the receipt of saving but no pull toward Vault — see→trust→verify breaks at "verify" because there's nowhere to verify *to*.

Why Wave 2, not Wave 3: Wave 3 is auth + paid + multi-tenant. The Card-as-clickable-entry gates the vault-engagement loop, which gates the *retention thesis* (`assumption-list.md` W13 — users return to old cards weeks later). Without click-through, the alpha cohort never produces the behavioral signal needed to validate W13. Wave 1b's polling endpoint already serves the data; deferring this spec wastes a quarter's worth of built-but-disconnected backend.

The trust-killer dimension: per claim-extraction plan v1.8 ship gate, hallucination rate is the HARD ship blocker. Wave 1b's eval result (2.3% / 6 hallucinations across 256 field decisions in EN) is a *ground-truth-set* measurement, not production. Until the Card surface displays real extracted strings to real users, V3 cannot transition from "validated against eval" to "validated against traffic." Brand-book Decision 5 (null-by-default) says *"Filling a field with invention is a CRITICAL FAILURE"*; the Card is the surface where that failure mode would first become user-visible.

## 3. Trigger

The Card renders when **all** of the following hold (no condition is OR-able):

1. `/api/chat` POST returns with `body._claim_pending === true` — meaning the post-classifier hook in `server.py` (line 1432: `claim_pending = bool(enqueued)`) routed to extraction-enqueue. This requires `intent == THOUGHTFUL` from the upstream `#intent-classifier` (or low-confidence fallback that classifier defaults to thoughtful).
2. `body.message_id` is a non-empty string (the assistant message id the chat_claims row will FK to).
3. Frontend polling against `GET /api/claim/by_message/{message_id}` (1s interval, 5s timeout per Wave 1b) returns `{ready: true, claim: <ClaimDict>, simplified: false}`.
4. `claim` has at least one non-null/non-empty-string field across `topic / concern / hope / question`. Zero non-null fields → silently hide (per claim-extraction spec edge case 1, preserved ADR-005 behavior).
5. The polling response represents a claim for the **currently-active conversation** (`messageId` was issued by an assistant message in the conversation the user is viewing). The Card never renders cross-conversation.

**Negative triggers** (Card MUST NOT render):
- `body._claim_pending === false` (chitchat / factual classifier route — extraction was never enqueued, no row exists).
- Polling 5s timeout with no `ready: true` response — the existing Wave 1b inline hint `(记录这一段需要更长时间…)` fires instead (preserved per ADR-005).
- `simplified: true` — the simplified-reference card path (`renderSimplifiedClaimCard`) renders instead. Out of scope for this spec; preserved as-is from Wave 1b.
- All 4 fields null in the returned `claim` (rare safety-net path, see §7 EC2).
- User has navigated away from chat tab to Vault during the 5s polling window — see §7 EC3 for handoff behavior.

## 4. Action

Step-by-step UI lifecycle from polling hit to click-through:

1. **Polling hit**: `pollForClaim(messageId)` (`app.js:450`) gets `ready: true, claim: {...}, simplified: false`. Logic stays at `app.js:475` — `renderClaimCard(body.claim)` is called.
2. **Render**: `renderClaimCard` (`app.js:373`) builds the DOM. **Modified scope** vs Wave 1a:
   - `claim.concern` may be `string | string[]`. If array: take first variant (`claim.concern[0]`); if non-empty string in array len ≥ 2, append a hover-only tooltip with full variant list (deferred to Wave 2.1 if simpler initial ship — see §7 EC8).
   - All 4 fields traversed via existing `FIELD_ORDER` loop (`app.js:366`); null/empty/whitespace-only values still skipped (Wave 1b behavior preserved).
   - If `rows.length === 0` after traversal, return `null` (Card silently hides, no badge bump — Wave 1b behavior preserved per spec edge case 1 / ADR-005).
3. **Header label change**: `claim-card-label` text changes from `已记下` to **`已记下`** (kept — anchor microcopy, Rodc-locked Wave 1a; no change requested in this spec). The `claim-card-vault-hint` text changes from `→ Vault +1` to **`→ 看 Vault 里这张`** (4 Chinese characters under the §B button-label ceiling) — see §9 brand check for derivation.
4. **Click affordance**: the Card's outer `<div class="claim-card">` gains:
   - `role="button"`, `tabindex="0"`, `aria-label="跳到 Vault 看这张卡 · 主题 {topic}"` (interpolates the topic field; falls back to `aria-label="跳到 Vault 看这张卡"` if topic is null).
   - Mouse cursor becomes `cursor: pointer` via `.claim-card[role="button"]` selector in `app.css`.
   - Click handler: `navigateToVaultCard(claimId)` — issues a `history.pushState({vault: {selectedClaimId}}, '', '#vault')` and fires the existing tab-switch logic (existing `selectTab('vault')` from Wave 1b; see `app.js` tab handler at the same module scope).
   - Keyboard handler: `Enter` and `Space` trigger the same handler. Disabled while a polling-in-flight; re-enabled after the render completes.
5. **Vault detail open**: when Vault tab activates with `state.vault.selectedClaimId` non-null, `vault.js` (existing `#3a` Cards mgmt) seeks the matching `chat_claim` row by id and opens the detail panel for that card. **New server requirement**: a small accessor route `GET /api/claim/{claim_id}` returning the full `ChatClaimRow` (existing adapter accessor `chat_claim_adapter.get_chat_claim` at line 148 wires through). See §5 data flow.
6. **Telemetry event**: on click, emit `claim_card_clicked claim_id={cc-...} message_id={...} fields_populated={n}/4` to stderr (mirrors the existing `claim_persisted` log line in `extraction_queue.py`'s `persist` callback at `server.py:918`). Production telemetry pipeline pending Wave 3; this spec writes only to the alpha-observability log path.
7. **Idempotency**: clicking the Card multiple times in quick succession only fires `navigateToVaultCard` once per render lifecycle. Debounce via a render-scoped flag (`wrap.dataset.clicked === 'true'` after first fire). Fresh re-render of a different Card resets the flag.

## 5. Data flow

| Surface | Reads from | Writes to | Side effect |
|---|---|---|---|
| `pollForClaim` (app.js) | `GET /api/claim/by_message/{id}` (existing) | DOM (Card render) | `bumpVaultBadge()` (existing) |
| `renderClaimCard` (app.js) | `claim` arg from polling response; `claim_id` (NEW field, see below) | DOM | none |
| Click handler (NEW) | `claim_id` on Card dataset | `history.pushState({vault: {selectedClaimId}}, '', '#vault')` + `selectTab('vault')` | `console.log('claim_card_clicked ...')` (NEW telemetry) |
| Vault detail (existing `#3a`) | `state.vault.selectedClaimId` from history state | `GET /api/claim/{claim_id}` (NEW route) → renders detail panel | none |
| `GET /api/claim/{claim_id}` (NEW) | `chat_claim_adapter.get_chat_claim(conn, claim_id)` (existing accessor) | response body | none |

**Tables touched (read only):** `chat_claims` (existing `chat_claims_v4.sql`). **No schema change.** The `id TEXT PRIMARY KEY` column already exists at line 31 — the polling endpoint just needs to expose it (see §11 Task 2). If the polling response doesn't currently expose `claim.id`, that's the additive backend change.

**API endpoints touched:**
- `GET /api/claim/by_message/{message_id}` (existing, Wave 1b, `server.py:1598-1654`) — **add `claim_id` to response body** so the frontend can stash it on the Card for the click handler. Currently returns `ClaimByMessageResponse(ready, claim, simplified)`; new shape adds `claim_id: Optional[str]` (None when ready=false). One-line addition.
- `GET /api/claim/{claim_id}` (NEW, this spec) — vault-detail accessor. Returns `ChatClaimRow` shape via FastAPI response model.

**Queue events:** none. The extraction queue (`app/shared/extraction/extraction_queue.py`) is untouched. This spec is read-only over Wave 1b's queue output.

**No new tables. No schema migration.** `chat_claims_v4.sql` already has every column this spec needs — `id`, `message_id`, `topic`, `concern`, `hope`, `question`. The concern-as-list handling is **frontend-only string parse** (concern is stored as a single TEXT column; if the extractor writes a JSON-encoded array string into it for variant cases, `renderClaimCard` parses with `try { JSON.parse(val) } catch { fallthrough to plain string }`). If `concern` is always plain string in current persistence, the parse is a no-op and Wave 2.1 can introduce variant storage if telemetry warrants.

## 6. User-perceived behavior matrix

| # | Condition | User sees | User does next | Card click outcome |
|---|---|---|---|---|
| 1 | Thoughtful chat, extraction succeeds, all 4 fields populated, click within 30s of render | Card with 4 rows + amber accent + `→ 看 Vault 里这张` hint | Clicks Card OR scrolls past | Vault tab opens with detail panel showing this card's full state + recall history |
| 2 | Thoughtful chat, extraction succeeds, only 2 of 4 fields populated (e.g., topic + question, no concern/hope) | Card with 2 visible rows; null fields silently hidden (no empty rows) | Clicks Card | Vault detail opens; null fields show "—" placeholder per existing `#3a` detail layout |
| 3 | Thoughtful chat, extraction succeeds, all 4 fields null (rare safety-net) | Nothing — Card hidden, no Vault badge bump | Continues conversation as if no extraction had happened | n/a |
| 4 | Chitchat reply (`你好`) | Nothing — `claim_pending: false`, no polling | Continues conversation; Vault badge unchanged | n/a |
| 5 | Thoughtful chat, extraction in flight at 4s mark | Inline `(记录这一段需要更长时间…)` hint at render position (Wave 1b preserved) | If extraction completes by the next chat turn, Card may render late OR be lost on refresh (see EC4) | n/a |
| 6 | Thoughtful chat, extraction times out at 5s | The same `(记录这一段需要更长时间…)` hint as #5; no Card | Continues conversation; can re-trigger by re-paraphrasing the same content | n/a |
| 7 | User clicks Card, then immediately switches back to chat tab | Vault tab fully opens with detail panel populated | n/a (intent was browsing, not editing) | Detail panel state preserved; re-clicking Vault tab shows same detail until user clears |
| 8 | User opens chat in tab A, sends thoughtful message, then opens tab B and views Vault before extraction lands | Tab A's Card renders into chat history when extraction completes; tab B's Vault sees the new card via existing list-refresh on tab activation | Continues either tab without disruption | Cross-tab navigation independent of extraction lifecycle |
| 9 | Concern field is a list of 3 variants | Card displays first variant only; hover/expand defer to Wave 2.1 (see EC8) | Click goes to detail panel; detail panel may show full variant list (Wave 2.1 enhancement) | n/a |
| 10 | User refreshes page mid-polling (3s into 5s window) | Polling state lost; Card never renders for that message | If extraction completed pre-refresh, the chat_claims row exists; user can find it in Vault by date but won't see inline Card | Vault has the card; chat history doesn't show the Card line |

## 7. Edge cases

**EC1 — User sends 3 messages back-to-back before first extraction completes** (race):
- Each message gets its own `message_id` and its own polling cycle (independent fetch loops). Polling functions don't share state — `pollForClaim(m1)`, `pollForClaim(m2)`, `pollForClaim(m3)` run concurrently, each with its own 5s clock.
- Cards render in completion order, NOT message order. If extraction-2 lands before extraction-1, Card 2 renders above Card 1's eventual position. Chat scroll snaps to Card-2's position.
- Mitigation: not needed for v1 ship — user sending 3 thoughtful turns in <5s is rare; each Card is still pinned to its `message_id` in the DOM. **Documented limitation, not a bug.** Wave 2.1 may add ordering glue if dogfood surfaces it.

**EC2 — Extraction succeeds with all 4 fields null** (chitchat false-negative, rare):
- Polling returns `{ready: true, claim: {topic: null, concern: null, hope: null, question: null}, simplified: false}`.
- `renderClaimCard` returns `null` after `rows.length === 0` check (`app.js:387`, Wave 1b behavior preserved).
- Vault badge NOT bumped. ADR-005 silent-hide preserved.
- Telemetry: emit `claim_all_null message_id={...}` to stderr (NEW alpha-observability log line). Sustained >5% of extractions hitting this path = Wave 2 calibration trigger fires.

**EC3 — User on Vault page when Card generates from different conversation**:
- The polling cycle is bound to the chat-tab DOM. If the user navigated away mid-polling, `messagesEl.appendChild(cardEl)` writes into a hidden DOM subtree (chat tab is hidden, not destroyed).
- When user returns to chat tab, the Card is already in place. No re-fetch needed.
- Vault badge bumps in real time regardless of which tab is active (existing `bumpVaultBadge` writes to topbar element shared across tabs).
- Cross-conversation: if the user is in conversation A but extraction was for conversation B (impossible in current single-conversation model, but a Wave 3 concern), the Card would still render into A's chat tab. Mitigation: Wave 3 multi-conversation lands with `conversation_id` filter on the polling loop.

**EC4 — User refreshes page mid-polling**:
- Browser refresh kills the polling JavaScript loop. The chat_claims row may still be persisted by the queue (extraction is async, decoupled from frontend polling).
- On reload, `app.js` re-renders chat history from `localStorage` / server-side conversation log, but does NOT re-poll `/api/claim/by_message/{id}` for past messages (would be wasteful + ambiguous).
- **Result**: card row exists in DB, badge count correct, but inline Card does not render in chat history. User finds card by clicking Vault tab.
- **Documented limitation** — fix would require server-side enrichment of message history with claim_id. Defer to Wave 2.1 if dogfood asks for it.

**EC5 — Dark mode rendering** (already default per brand-book §6):
- All amber tokens (`--accent`, `--accent-soft-bg`, `--accent-soft-bg-active`) defined in `tokens.css` are dark-mode default. No light-mode variant exists; brand-book §6 `*Dark-mode-default* implies the intimate / private / late-night-thinking register`.
- Verify: `accent` token = `#d97706` (per brand-book §6 + `tokens.css`). Card border + label color use `var(--accent)`. Card background uses `var(--accent-soft-bg)` (amber-tinted dark surface).
- No emoji decoration anywhere in the Card. Per brand-book §6: *"No emoji adornments. Lucide line icons replace emoji."* Card uses no Lucide icon either; the amber border IS the visual signal.

**EC6 — Mobile vs desktop card sizing** (per brainstorm `#8` micro-adj 3 + brand-book device priority):
- Desktop: `max-width: 90%`, padding `var(--space-12) var(--space-14)` (existing in `app.css:638-654`).
- Mobile (<768px): `max-width: 100%`, padding `var(--space-8) var(--space-10)` (existing in `app.css:830-836`).
- 4 field rows stay vertical (already stacked via `flex-direction: column` in `.claim-card-fields`).
- **NEW for click target**: at <768px, the entire Card is the click target — minimum tap target 44x44px (per WCAG, scenarios C-2 cross-cutting). Card is taller than 44px due to 4 rows + padding; this is satisfied implicitly. Verify via `S-MOBILE-2` scenario.

**EC7 — User hits action button rapidly** (debounce vs idempotent):
- The Card itself is the click target — there are no separate action buttons on the Card-with-Promise (4-button affordances belong to the recall callout, sibling spec `#active-recall-base`).
- Click debounce: render-scoped flag (`wrap.dataset.clicked === 'true'` after first fire) + 500ms cooldown for double-tap forgiveness.
- Idempotent: `selectTab('vault') + history.pushState` are idempotent; multiple rapid fires resolve to the same final state. Defensive: still debounce so we don't emit duplicate telemetry events.

**EC8 — Concern is `list[string]` of length 1 vs >1**:
- Per claim-extraction plan v1.7 multi-variant relabel: ground-truth `concern` is `list[str]`; first matching variant = TP. Production extractor output **may** mirror this shape if the prompt instructs multi-variant emission (it currently does NOT — extractor emits single string). If/when extractor emits a list, the storage path JSON-encodes into the TEXT column.
- Frontend handling: `renderClaimCard` parses concern as JSON-decoded array if the string starts with `[`; otherwise treats as plain string. Display first variant only.
- Hover/expand to show alternatives: **DEFERRED to Wave 2.1**. Initial ship displays first variant only; alternative variants visible only via Vault detail panel (which may also defer alternative-variant rendering to Wave 2.1).
- This eliminates a Wave 2 dependency on extractor prompt iteration.

**EC9 — Click-through targets a deleted card**:
- User clicks Card, then in another tab/session deletes that card from Vault, then returns to chat and re-clicks the same Card in chat history.
- `GET /api/claim/{claim_id}` returns 404. Vault detail panel renders an inline empty-state hint *"This card is no longer in your vault — it may have been deleted."* (Per voice-guide §5 Sample 1 register: anti-spin, names what failed, no apology theater.)
- No error toast. The chat-tab Card stays visible (it's a static DOM node tied to chat history); on next click, same 404 + same inline hint.

**EC10 — Topic field contains a JSON-special string** (e.g., extractor leaks `{"topic": "..."}` as topic):
- `renderClaimCard` already does `typeof val !== 'string'` check (`app.js:380`). If extractor leaks structured output into a string field, the value renders as-is (it's still a string).
- Mitigation: extractor's `parse_4field` (per `app/shared/extraction/extractor.py`) is the gatekeeper. This spec doesn't add defense-in-depth at the render layer — preserves Wave 1b's *"trust the extractor's parse contract"* boundary.

## 8. Trust mode

The Card-with-Promise is the *first user-visible hallucination surface*. Brand-book §7 Decision 5 (null-by-default extraction) is operationalized HERE. If the extractor invents a "concern" the user never expressed, this Card is where the user notices, and the user's trust in Rodix collapses immediately and irreversibly. Per friends-intro: *"Black-box tags. Wrong, and you can't fix it. Locked to one vendor. Not actually yours."* — the Wave 1a/1b stub UI inherits the transparency promise; Wave 2 makes that promise legible.

**Failure modes that would lose user trust + how prevented:**

1. **Hallucinated content** (extractor invents fields): prevented at the data layer by `claim_extractor.md` CORE DIRECTIVE (*"null is the default, not the failure case. Filling a field with invention is a CRITICAL FAILURE."*). 2.3% measured eval rate. Wave 2 calibration trigger at >5% sustained. **This spec adds NOTHING new** — relies on Wave 1b ship gate already met.
2. **Paraphrased content** (extractor summarizes instead of quoting): prevented by `claim_extractor.md` extract-verbatim discipline. The Card displays whatever the extractor persisted; if the extractor paraphrased, the user sees the paraphrase. **This spec relies on the data layer's discipline; it does NOT re-check at render time.**
3. **Cross-conversation Card render** (Card from conversation B renders in conversation A's chat tab): prevented by §3 Trigger condition 5 (the polling response represents a claim for the currently-active conversation).
4. **Click-through 404** (Card click goes nowhere): prevented by §7 EC9 — graceful inline hint, no error toast, no apology theater.
5. **Stale Card after card deleted** (Card stays clickable in chat after vault delete): not prevented — by design, the chat-tab Card is part of conversation history (immutable). EC9's 404 path catches the navigation. **Documented limitation.**
6. **Card click feels like a notification dismissal, not a navigation** (UX failure): prevented by `cursor: pointer` + `aria-label="跳到 Vault 看这张卡 · 主题 {topic}"` + the explicit `→ 看 Vault 里这张` hint. The Card LOOKS like a clickable surface, not a passive receipt.

**White-box test (brand-book §7 Decision 1)**: open Card, read 4 fields, click through to Vault, see the same 4 fields in detail panel WITH the source conversation excerpt. If detail panel shows different text than Card (e.g., paraphrased), Decision 1 has been violated. Verification scenario: `S-CARD-1` extended (see §12).

## 9. Brand consistency check

**Voice principles (brand-book §5 / voice-guide §2):**

- **Specific** (Principle 4): Card displays user's actual extracted wording from `claim_extractor.md`'s "Extract using user's own wording, 4-8 words preferred, do NOT paraphrase". The Card surface is the visible enforcement of this principle.
- **Anti-spin** (Principle 1 of voice-guide): no celebration toasts, no "✓ Saved!" confirmation, no "Great thinking!" sycophancy. The Card just *appears* — its existence is the receipt.
- **Refuses-to-dramatize** (Principle 3 of voice-guide): no animation flourishes beyond the existing Vault badge pulse (Wave 1a, brand-locked at 600ms per `S-CARD-1`). No celebratory color burst. No "1 card saved!" toast.
- **Negation as positioning** (voice-guide §3): the Card is positioned by what it is NOT — not a paraphrase, not an inference, not a personalization profile. Users read 4 fields and recognize the contrast with ChatGPT memory's *"a few items it deigns to show you"* (per friends-intro lines 142-144).

**Locked microcopy strings:**

- Header label: `已记下` — UNCHANGED from Wave 1a. Anchor microcopy, Rodc-locked. Per brand-book §5: *"Negation is not snark — it is position."* `已记下` (already-saved, past tense) signals "the receipt is done, not the relationship." Resists "Saved! ✓" sycophancy.
- Vault hint: **CHANGE** from `→ Vault +1` to `→ 看 Vault 里这张` (English: `→ See it in Vault`). Rationale: `+1` was a Wave 1a stub anchored to badge animation; once the Card is clickable, the hint must communicate *navigation*, not *count*. 7 Chinese characters; under §B button-label ceiling of 8. The arrow is preserved per brainstorm `#8` micro-adj 1 (`↗ / →` recall-trigger language).
- Promise line: `下次提到这些任一项,我会主动带回来 ↗` — UNCHANGED from Wave 1a. Brand-book §7 Decision 3: *"the relational verb 'bring back' / '带回来' replaced the engineering verb 'surface' in brainstorm #8 micro-adj 2 and is locked."*
- Aria-label: `跳到 Vault 看这张卡 · 主题 {topic}` (or fallback `跳到 Vault 看这张卡` if topic null). Per voice-guide §A locale notes: Chinese needs more discipline; `·` separator is the brand pattern (matches existing `Step 1 of 3 · Get started` register).

**Note on cross-spec strings**: the user's spec request cited `⚡ 我把这个带回来了` and `用上了 / 不相关 / 已经想过 / 跳过` as locked copy for `#card-real`. Per brand-book §7b first item, these strings belong to **`#active-recall-base`** (the active-recall callout surface, sibling Wave 2 spec). They are NOT changes to the Card-with-Promise (`#card-real`) UI. Implementer should NOT touch `app.js::renderRecallCard` (line 570) under this spec — that surface is owned by `#active-recall-base`. If a reader of this spec is confused on cross-spec scope: open both specs side-by-side; this one owns `renderClaimCard`, the recall spec owns `renderRecallCard`.

**Visual identity (brand-book §6):**
- Amber accent `#d97706` via `var(--accent)` token (border + label color). Verify in DevTools no literal `#d97706` is hardcoded; tokens-only.
- Inter font via `var(--font-stack)`. No font override on the Card.
- Dark mode default; no light-mode variant.
- Zero emoji decoration. The arrow `→` is a Unicode char, not an emoji; per brand-book §6 the *only* emoji exception is `⚡` in the recall callout (sibling spec, not this one).
- Lucide icons: NONE on the Card. The amber border IS the visual signal. Adding a `bookmark` or `archive` icon would violate §6 *"Considered whitespace > maximalist UI"*.

## 10. Asymmetric gate

**Recall vs precision priority: precision >> recall.**

This Card is downstream of the extraction trust gate. Wave 1b ship gate (claim-extraction plan v1.8) already split trust-killer (hallucination) from completeness (per-field recall): hallucination rate is HARD ship blocker (≤8% per field), per-field recall is monitor-only (target ≥60%, current 53.8-56.5% across concern/hope/question). This spec inherits that asymmetry.

**Production targets for `#card-real`:**

| Metric | Target | Rationale |
|---|---|---|
| **0% Card-display-with-hallucinated-content** | HARD | One hallucinated card destroys trust. Per brand-book Decision 5 + V3. If hallucination rate breaches 5% sustained in production, calibration trigger fires (claim-extraction v1.8 §"Calibration trigger"); Card render is downstream. |
| **≤ 5% silent-hide-when-content-was-actually-good** | SOFT | False negative (extraction returned all-null on a real thoughtful turn) → Card silently hides. User loses a card they "should have" gotten. Brand-book §7 Decision 5: "the cost of returning null when something exists is recoverable (user sees less)" — but at high rate the Vault feels sparse and W6 (Vault badge as positive signal) breaks. |
| **≥ 60% Card-clicked-within-30s-of-render** | TARGET (telemetry-only, NOT ship-blocker) | Validates W11 (users keep cards) + W13 (users return to old cards). Below 50% sustained = the Card-as-clickable-entry hypothesis weakens; W11 needs separate validation. NOT ship-blocking — measurable post-launch. |
| **0% Card-renders-cross-conversation** | HARD | Trigger condition 5 enforcement. A Card from conversation B appearing in conversation A's chat tab is a multi-tenant correctness violation; defers Wave 3 multi-conversation. |
| **≤ 200ms Card-render p95 latency** | SOFT | Render is pure DOM; bottleneck is network polling (Wave 1b 1s interval). |

**Calibration trigger** (mirrors claim-extraction v1.8): Wave 2 alpha telemetry produces a Card-render-rate distribution. If hallucination > 5% sustained → emergency v4 prompt iteration on `claim_extractor.md` (NOT in this spec's scope; raise to Rodc). If silent-hide > 10% sustained → relabel boundary categories on the eval set (NOT in this spec's scope).

## 11. TDD task list

Each task: small (1-2h scope), testable. Tests live in `app/web/test_claim_card_real.py` (NEW, gitignored) for frontend behavior verification (using existing TestClient pattern from `app/web/test_chat_extraction.py`). Frontend rendering tests use `selenium` if already in test stack OR fall back to DOM-string assertion in jsdom-equivalent (verify what's available — `app/web/test_chat_placeholder.py` is the precedent).

- [ ] **Task 1: Polling response exposes `claim_id`**
  - Failing test (NEW `app/web/test_claim_card_real.py::test_polling_response_includes_claim_id`): POST `/api/chat` with thoughtful message → wait for extraction → GET `/api/claim/by_message/{id}` → assert response body has `claim_id` key matching the persisted `chat_claims.id` (cc-... prefix).
  - Modify `server.py::ClaimByMessageResponse` (line 350) — add `claim_id: Optional[str] = None` field.
  - Modify `get_claim_by_message` handler (line 1602) — populate `claim_id` from cached fields OR from `row.id` on DB hit.
  - PASS when test asserts the field is present and matches the cc-... id.
  - (No commit — `app/web/server.py` gitignored.)

- [ ] **Task 2: GET /api/claim/{claim_id} accessor route**
  - Failing test `test_get_claim_by_id_returns_4_fields`: insert a chat_claim row via adapter → GET `/api/claim/{cc-...}` → assert response body has `id, message_id, conversation_id, topic, concern, hope, question, simplified_reference, created_at, updated_at`.
  - Failing test `test_get_claim_by_id_returns_404_when_not_found`.
  - Implement route in `server.py` near `get_claim_by_message` (line 1598). Use `chat_claim_adapter.get_chat_claim` (existing accessor at line 148). FastAPI response_model = NEW `ClaimByIdResponse` (mirror `ClaimByMessageResponse` shape but flat, with FK fields).
  - PASS.
  - (No commit — gitignored.)

- [ ] **Task 3: Card click handler navigates to Vault**
  - Failing test (DOM-level, in `test_claim_card_real.py` using whatever frontend test pattern Wave 1b adopted): mock `/api/chat` + polling → render card via existing flow → simulate click on the Card → assert `selectTab('vault')` was called AND `history.pushState` carried `{vault: {selectedClaimId: cc-...}}`.
  - Modify `app.js::renderClaimCard` (line 373):
    - Add `wrap.setAttribute('role', 'button')`, `wrap.setAttribute('tabindex', '0')`, `wrap.setAttribute('aria-label', ...)` (interpolate topic — see §4 step 4).
    - Add `wrap.dataset.claimId = claim.id` (requires Task 1 complete — `claim.id` field exists).
    - Add `wrap.addEventListener('click', () => navigateToVaultCard(claim.id))`.
    - Add `wrap.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigateToVaultCard(claim.id); } })`.
  - Implement `navigateToVaultCard(claimId)`: `if (wrap.dataset.clicked === 'true') return; wrap.dataset.clicked = 'true'; history.pushState({vault: {selectedClaimId: claimId}}, '', '#vault'); selectTab('vault'); console.log('claim_card_clicked', claimId);` (use the existing `selectTab` from `#3a` cards-management surface).
  - Test: simulate click + assert `history.state.vault.selectedClaimId === cc-...` AND chat tab is hidden / Vault tab is visible.
  - Test: simulate Enter key + Space key + assert same outcome.
  - Test: simulate double-click + assert handler fires only once (debounce via `dataset.clicked`).
  - PASS.
  - (No commit — `app.js` gitignored.)

- [ ] **Task 4: Vault detail panel reads `state.vault.selectedClaimId` and opens detail**
  - **Pre-condition**: `#3a` Cards mgmt UI's detail panel exists and supports an `openDetailById(claimId)` shape (verify by reading existing vault.js — if not present, implement the seek-and-open via existing list iteration).
  - Failing test: navigate to `/#vault` with `history.state = {vault: {selectedClaimId: cc-...}}` → assert detail panel renders the matching card's 4 fields.
  - Modify `vault.js` (or `app.js` tab switch handler — verify which owns Vault state) — on Vault tab activation, read `history.state?.vault?.selectedClaimId`; if present, call `openDetailById(claimId)` after the cards list loads.
  - Test: assert detail panel is open AND scrolled-to-position AND 4 fields visible.
  - PASS.
  - (No commit — gitignored.)

- [ ] **Task 5: Vault hint label change**
  - Trivial. `app.js::renderClaimCard` line 403: change `hint.textContent = '→ Vault +1'` to `hint.textContent = '→ 看 Vault 里这张'`.
  - Test: render card with stub data → DOM assert `.claim-card-vault-hint` text equals `→ 看 Vault 里这张`.
  - PASS.
  - (No commit — gitignored.)

- [ ] **Task 6: Concern as `string | string[]` parsing**
  - Failing test `test_concern_as_array_takes_first_variant`: render card with `claim.concern = ["losing income", "family financial stability"]` → assert only "losing income" is in the DOM.
  - Failing test `test_concern_as_plain_string_unchanged`: render with `claim.concern = "losing income"` → assert "losing income" in DOM.
  - Failing test `test_concern_as_json_encoded_array_string`: render with `claim.concern = '["losing income"]'` → assert "losing income" in DOM after JSON parse.
  - Modify `renderClaimCard` field-loop (`app.js:378`):
    ```
    let val = claim[key];
    if (key === 'concern') {
      if (Array.isArray(val)) val = val[0] ?? null;
      else if (typeof val === 'string' && val.startsWith('[')) {
        try { const parsed = JSON.parse(val); if (Array.isArray(parsed)) val = parsed[0] ?? null; } catch {}
      }
    }
    if (typeof val !== 'string') continue;
    ```
  - PASS.
  - (No commit — gitignored.)

- [ ] **Task 7: Click cursor + focus styling**
  - Modify `app.css::.claim-card[role="button"]` (NEW selector below existing `.claim-card` block at line 638):
    ```
    .claim-card[role="button"] { cursor: pointer; transition: border-color 120ms ease; }
    .claim-card[role="button"]:hover { border-color: var(--accent); }
    .claim-card[role="button"]:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
    ```
  - Frontend smoke test: hover Card → border darkens to amber. Tab to Card → focus ring visible.
  - PASS by inspection.
  - (No commit — gitignored.)

- [ ] **Task 8: Telemetry log line for card click**
  - Failing test (server-side, since the click telemetry needs server-side logging too): simulate click → assert `claim_card_clicked` log line emitted to stderr with `claim_id`, `message_id`, `fields_populated=N/4`.
  - Frontend: `console.log('claim_card_clicked', {claim_id, message_id, fields_populated})`.
  - Server-side: NEW small endpoint `POST /api/claim/{claim_id}/clicked` — increments a counter + logs. (NOT critical for v1 ship; alpha can grep stderr-side log only. Implement endpoint as Wave 2.1 if telemetry pipeline needs it.)
  - PASS by stderr inspection during dogfood.
  - (No commit — gitignored.)

- [ ] **Task 9: Aria-label + keyboard accessibility verification**
  - Failing test `test_card_aria_label_interpolates_topic`: render card with `claim.topic = "换工作"` → assert `wrap.aria-label === "跳到 Vault 看这张卡 · 主题 换工作"`.
  - Failing test `test_card_aria_label_falls_back_when_topic_null`: render card with `claim.topic = null, claim.concern = "稳定性"` → assert `wrap.aria-label === "跳到 Vault 看这张卡"`.
  - Manual a11y check: keyboard Tab to Card → focus visible → Enter → Vault opens. Screen reader announces aria-label.
  - PASS.
  - (No commit — gitignored.)

- [ ] **Task 10: Mobile responsive verification**
  - Smoke test on iPad viewport (768-1024px) and iPhone SE (375px):
    - Card max-width clamps to 100% on mobile (existing `app.css:833`).
    - Click target ≥ 44x44px (Card height with padding satisfies this implicitly; verify in DevTools).
    - 4 field rows stack vertically (`flex-direction: column` already in place).
  - Verification scenario: `S-MOBILE-2` walk-through.
  - (No commit — gitignored.)

- [ ] **Task 11: End-to-end dogfood scenario (S-CARD-1 + S-CROSS-1 extension)**
  - Run full dispatch dogfood: 5 thoughtful turns + 2 chitchat turns + 1 factual turn → verify:
    - 5 cards render (one per thoughtful), each clickable → Vault detail opens correctly.
    - 2 chitchat → no Card.
    - 1 factual → no Card.
    - Card-click on any Card opens Vault tab + detail panel for that exact card.
    - Vault badge increments to 5 (or fewer if any all-null safety-net path fired — log inspection confirms count).
  - **Pass criteria**: 5/5 click-throughs land on correct detail. 0 hallucinated content (visual spot-check: do the 4 fields read like the user's actual words?). 0 cross-conversation renders.
  - This is the implementer's final self-verification before raising to Rodc 5-round subjective gate.
  - (No commit — manual dogfood log.)

- [ ] **Task 12: Rodc 5-round subjective dogfood gate** (mirrors claim-extraction Task 15)
  - Implementer signals `#card-real` code-complete (Tasks 1-11 done, scenarios PASS).
  - Rodc runs 5 thoughtful conversations on real topics. After each, asks: "Does the Card show 4 fields that read like my own thinking? Does click-through feel natural? Would I return to that card later?"
  - Outcome resolution:
    - 4-5 PASS / 0-1 WEAK / 0 FAIL → ship.
    - ≥ 2 WEAK or ≥ 1 FAIL → raise: 4 options (revise card UI / change click target shape / accept misalignment + telemetry / pivot to different navigation pattern).
  - Human-judgment, NOT automatable. Implementer marks Task 11 `awaiting_subjective_dogfood`; Rodc closes Task 12 manually.

## 12. Verification scenarios

Map this spec's behavior to scenarios in `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`:

- **S-CARD-1** (Card 触发后的 Vault badge 动画) — extends:
  - Existing: badge +1 + 600ms amber pulse + Card renders below AI reply.
  - **NEW for `#card-real`**: Card is clickable, click navigates to Vault detail. Add to scenario: *"Click Card → Vault tab opens with the same card's detail panel populated."*
  - **NEW**: vault hint reads `→ 看 Vault 里这张` (was `→ Vault +1`).
- **S-CHAT-1** (用户输入 thoughtful 想法) — verifies extraction happens; existing flow unchanged. New verifier: the Card that appears below AI reply is clickable.
- **S-CHAT-2** (chitchat) — no Card renders. Unchanged.
- **S-CHAT-3** (factual) — no Card renders. Unchanged.
- **S-CHAT-5** (完整对话流) — 4 fields render after multi-turn convergence. **NEW**: clicking the Card navigates to Vault detail showing same 4 fields + source conversation excerpt.
- **S-CROSS-1** (Onboarding → first chat → first card) — extends:
  - **NEW**: from the first-card render, user clicks Card → Vault opens with card detail. This validates the Vault tab as a *navigation destination*, not just a passive list (per brand-book §7 Decision 1 *"The Vault is a first-class top-tab equal-billing with Chat — not a settings page"*).
- **S-VAULT-3** (6-50 cards normal state) — when Vault is opened via Card click (with `selectedClaimId` in history state), default detail panel selection respects the click-source card, NOT the topmost card.
- **S-MOBILE-2** (手机竖屏 375px) — Card is fully clickable on mobile; tap target ≥ 44x44px.
- **S-EDGE-1** (network down) — polling silently fails, no Card. Unchanged.

**NEW scenario to add to product-test-scenarios.md**:
- `S-CARD-5: Card click navigates to Vault detail` — new entry in the Wave 2 section. Covers the click flow + history state preservation + back-button behavior. Implementer dispatches this addition as part of Task 11 dogfood close-out.

## 13. Rollback plan

**Kill switch**: feature flag in `app/web/static/app.js` near the polling site (`app.js:284`):
```
const _CARD_REAL_ENABLED = true; // Wave 2 #card-real ship flag
```
- If `false`: bypass click handler attachment in `renderClaimCard`. Card renders as Wave 1b (clickable cursor removed; no nav handler; Wave 1a hint label `→ Vault +1` preserved via fallback branch).
- If sustained user complaints / hallucination rate breach during alpha: flip to `false` via static asset re-deploy. No backend rollback needed; `/api/claim/{claim_id}` route stays live (idempotent, no other callers).
- Server-side polling endpoint (Task 1's `claim_id` exposure): no rollback needed — extra field is ignored by stale frontend.

**Server-side incident** (e.g., `/api/claim/{claim_id}` returning 5xx en masse): frontend's click handler catches fetch failure → renders inline hint *"This card couldn't load — try again or check Vault directly"* (per voice-guide §5 Sample 1 register). No error toast.

**Database incident** (e.g., chat_claims table corruption): polling endpoint returns ready=false; Wave 1b silent-hide path preserved (no Card renders). User experience degrades to "no Card at all" — same UX as mid-polling timeout. No new failure mode.

**Trust-incident triage** (hallucination spike >5% sustained per `assumption-list.md` V3 calibration trigger): Card kill switch flipped to `false` (`#card-real` rolls back to Wave 1b stub UX) AND extraction prompt iteration re-opens at `app/shared/extraction/prompts/claim_extractor.md` (NOT this spec's scope; raise to Rodc). Card without click-through is degraded but not broken; chat experience continues.

---

## References

- **Plans**: `docs/superpowers/plans/2026-05-01-claim-extraction.md` v1.8 (Wave 1b ship gate; this spec inherits the trust-killer/completeness split)
- **Plans**: `docs/superpowers/plans/2026-05-01-3a-cards-management.md` (Wave 1b Vault detail panel — depended-on UI)
- **Specs**: `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` v1.3 (S-CARD-1, S-CHAT-1/2/3/5, S-CROSS-1, S-VAULT-3, S-MOBILE-2, S-EDGE-1; new S-CARD-5 to add)
- **Specs**: `docs/superpowers/specs/2026-05-01-rodix-brainstorm.md` (`#8` micro-adj 1 + 2 — locked promise text + brand-tonality observations)
- **Specs**: `docs/superpowers/specs/web-product-design.md` §5.5 (`#8` 4-field structure + null-field rule)
- **Brand**: `docs/superpowers/brand/brand-book-v1.md` §6 (visual identity tokens) + §7 Decision 1 (white-box) + §7 Decision 3 (active-recall verb) + §7 Decision 5 (null-by-default)
- **Brand**: `docs/superpowers/brand/voice-guide.md` §2 Principle 1-5 + §5 Sample 1 (chat error register) + §A locale notes
- **Research**: `docs/superpowers/research/assumption-list.md` S15 (4-field schema comprehension), W11 (vault retention), V3 (hallucination ≤2.3%), W13 (multi-week return)
- **Code**: `app/shared/schema/chat_claims_v4.sql` (existing schema) · `app/shared/storage_py/chat_claim_adapter.py` (existing adapter API) · `app/web/server.py:1598-1654` (polling endpoint to extend) · `app/web/static/app.js:373-432` (renderClaimCard to extend) · `app/web/static/app.css:638-708` (existing Card styling)
- **Sibling Wave 2 spec**: `#active-recall-base` (separate spec) — owns `renderRecallCard` + the recall-callout strings `⚡ 我把这个带回来了` / `用上了 / 不相关 / 已经想过 / 跳过`. THIS spec does NOT modify those.
- **Roadmap position**: Wave 2 P0. Depends on Wave 1b `#claim-extraction` v1.8 ship-ready (DONE pending Task 15 dogfood). Unblocks `#decision-journal-lite` (Wave 2 P1) + retention-thesis validation (W11/W13).

## §7.4 5 项 framing

| | |
|---|---|
| Visual | Card stays the same shape; gains `cursor: pointer` + amber hover + click-target ≥ 44x44px on mobile. Vault hint string changes from `→ Vault +1` to `→ 看 Vault 里这张`. |
| 产品策略假设 | The Card-as-clickable-entry validates the Vault as first-class navigation destination (brand-book §7 Decision 1). Click-rate ≥ 60% in first 30s validates W11 + W13 retention thesis. |
| 适合 / 不适合 | **适合**: all thoughtful-route users — this is the first interaction surface beyond the chat reply. **不适合**: chitchat-only users — they never see a Card; ChatGPT's fine for them (per friends-intro line 268). |
| Trade-off | + Closes see→trust→verify aha loop with a real navigation target / + Validates 3 high-stakes assumptions (S15 / W11 / V3 in production) / − Extraction quality is now user-visible in production for first time (hallucination becomes externally observable) / − Adds a click-target on chat history that must coexist with future chat affordances |
| 最大风险 | Production hallucination > 5% sustained → Card displays invented content → trust collapses irreversibly. **Mitigation**: Wave 1b ship gate already tests this at 2.3% on EN bucket; calibration trigger fires at 5% with kill-switch flag in §13. |

## Ambiguity flag

✓ **Locked decisions** (this spec):
- Card-with-Promise UI scope (NOT recall callout — sibling spec `#active-recall-base`)
- Vault hint copy: `→ 看 Vault 里这张` (under §B Chinese ceiling 8 chars; resolves Wave 1a stub `→ Vault +1`)
- Concern multi-variant: display first variant only; hover/expand DEFERRED to Wave 2.1
- No new schema; existing `chat_claims_v4` adequate
- No new tables, no extraction prompt change

⚠ **One implementer-blocking question** (raise to Rodc OR resolve via plan v1.X push back):
- **Q**: Does `#3a` Cards mgmt detail panel currently support `openDetailById(claimId)` for Vault state restoration? Task 4 depends on this. If not, this spec implicitly extends `#3a` scope by ~1 task; OR Task 4 falls back to "list-search-then-click" UX which is not as crisp. Implementer should verify by reading `vault.js` BEFORE starting Task 4. If not present, raise to Rodc as Plan v1.1 push back: either add the accessor (extends `#3a`) or accept degraded UX.

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位: not applicable (Card surface uses no brand name string)
2. ✓ Desktop-first: yes, mobile responsive verified (Task 10 + EC6 + S-MOBILE-2)
3. ✓ §7.4 5 项 articulated above
4. ✓ Pre-mortem 4 modes: like-me (anti-target sent away by chitchat-no-Card path) / metric vs goal (click-rate is leading indicator of W11, NOT the goal — the goal is trust-validated retention) / reactive vs strategic (clickable Card is strategic — closes verify loop, doesn't react to support tickets) / edge vs main (10 edge cases enumerated in §7; main path = thoughtful → 4-field card → click → Vault detail)
5. ✓ 桌面横向利用率: Card max-width 90% on desktop preserves chat-bubble proportions; doesn't stretch edge-to-edge
6. ✓ Mobile responsive: yes, Tasks 7 + 10 + EC6
7. ✓ Empty state: by §7 EC2 (all-null silent hide) + EC4 (refresh mid-polling silent loss) — both resolve to "no Card" which falls back to `#3a` Vault tab cold-start empty state per `S-VAULT-1`

## Done criteria

- [ ] Polling endpoint `/api/claim/by_message/{id}` exposes `claim_id` field ✓
- [ ] `GET /api/claim/{claim_id}` accessor route live ✓
- [ ] `renderClaimCard` makes Card clickable with role=button + tabindex + aria-label ✓
- [ ] Click handler navigates to Vault tab + opens detail panel for that card ✓
- [ ] Keyboard Enter / Space trigger same nav as click ✓
- [ ] Vault hint string changed: `→ Vault +1` → `→ 看 Vault 里这张` ✓
- [ ] Concern field handles `string | string[] | json-encoded array string` and displays first variant ✓
- [ ] Telemetry log line `claim_card_clicked` emitted on click ✓
- [ ] Hover/focus styles use `var(--accent)` token (no hardcoded `#d97706`) ✓
- [ ] Mobile (<768px) verified: tap target ≥ 44x44px + 4 field rows stack vertically ✓
- [ ] Tests green: full app suite + new unit + frontend behavior verification (jsdom or selenium per existing pattern) ✓
- [ ] Scenario verification: S-CARD-1 (extended), S-CHAT-1/2/3/5 (Card click adds), S-CROSS-1 (extended), S-VAULT-3 (selectedClaimId respect), S-MOBILE-2, S-EDGE-1 PASS ✓
- [ ] NEW S-CARD-5 added to product-test-scenarios.md and committed ✓
- [ ] **Rodc 5-round subjective dogfood gate** (Task 12) — 4-5 PASS / 0-1 WEAK / 0 FAIL on real conversations OR Rodc-recorded mitigation ✓

---

*End spec-card-real.md (v1.0, 2026-05-03). Wave 2 P0. Awaiting Rodc + external Opus review per `feedback_plan_review_protocol.md`.*
