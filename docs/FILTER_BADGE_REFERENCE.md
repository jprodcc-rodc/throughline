# Filter Badge Reference

> Every chat turn through Throughline can emit up to three status
> lines, one recall-summary block, and one outlet badge line. This
> document is the full legend. For a quick-reference subset see
> `filter/README.md § 5`.

---

## Contents

- [1. Where badges appear](#1-where-badges-appear)
- [2. Status line 1 — pre-judge interceptions](#2-status-line-1--pre-judge-interceptions)
- [3. Status line 2 — RecallJudge verdict](#3-status-line-2--recalljudge-verdict)
- [4. Status line 3 — final recall summary](#4-status-line-3--final-recall-summary)
- [5. Recall-list entry legend](#5-recall-list-entry-legend)
- [6. `route_path` taxonomy](#6-route_path-taxonomy)
- [7. `HAIKU_DOWN` warning ladder](#7-haiku_down-warning-ladder)
- [8. Confidence tier colours](#8-confidence-tier-colours)
- [9. Outlet badge — daemon refinement status](#9-outlet-badge--daemon-refinement-status)
- [10. Cost footer](#10-cost-footer)
- [11. Suppression rules](#11-suppression-rules)

---

## 1. Where badges appear

A single user turn produces, at most:

```
[status 1]   pre-judge short-circuit notice         (optional)
[status 2]   RecallJudge verdict / fallback notice  (optional)
[status 3]   final recall summary                   (always on recall turns)
[recall list]  markdown block of cards              (when cards were injected)
[outlet badge] daemon refine status + cost footer   (always when enabled)
```

Status lines 1-3 are emitted via OpenWebUI's `type: status` events.
The recall list is a markdown message inserted into the conversation
stream (visible and scrollable). The outlet badge is appended to the
assistant's reply.

---

## 2. Status line 1 — pre-judge interceptions

Shown when the cheap gate or an explicit override decides the turn
before the Haiku RecallJudge is consulted.

| Badge | Meaning | Typical trigger |
|---|---|---|
| `⚡ anchor pass: <token> · zero-cost auto recall` | Concept-anchor hit | User mentions a known vault token (see `ANCHOR_TOKENS` valve) |
| `🔇 RAG skipped · /native` | Explicit slash | User typed `/native …` |
| `🔇 RAG skipped · gate=noise_only` | Cheap noise gate | Acknowledgement-only turn (`ok`, `sure`, punctuation-only) |
| `🔇 RAG skipped · short-query no-anchor` | Cheap short gate | Very short turn with no personal anchor or capitalised token |
| `🔇 RAG skipped · gate=first_msg_ack` | First-message ack | Opening turn is a pleasantry |

When this line fires the RecallJudge is not called and Status 2 is
absent.

---

## 3. Status line 2 — RecallJudge verdict

Shown when the judge was invoked and returned a usable verdict.

```
⚡ auto recall: mode=general · 🟢 conf=0.92 · agg · shift · reform→venlafaxine side effects · literal match treated as known entity
```

Field layout:

| Field | Meaning | When present |
|---|---|---|
| `mode=general` | Default recall mode | Always |
| `mode=decision` | User-flagged durable decision (via `/decision` or strong judge signal) | When judge sets it |
| `mode=brainstorm` | Judge classified as brainstorming; recall suppressed | Prefix becomes `🧪 RAG skipped` |
| `mode=native` | Judge says generic question, no vault context needed | Prefix becomes `🔇 RAG skipped` |
| `🟢 conf=0.XX` | Confidence ≥ 0.85 | Always (when judge returned conf) |
| `🟡 conf=0.XX` | Confidence 0.60-0.85 | |
| `🔴 conf=0.XX` | Confidence < 0.60 (weak verdict — review) | |
| `agg` | `aggregate=true`; `top_k` bumped to `TOP_K_AGGREGATE` | Non-default only |
| `shift` | `topic_shift=true`; freshness decay baseline reset | Non-default only |
| `reform→<rewritten query>` | Reformulated query sent to the embedder instead of the raw user turn | Non-default only |
| `· <reason>` | Judge's short human-readable justification (≤ ~60 chars) | Always |

### 3b. Judge failure fallback

When the judge times out or returns unparsable JSON, status 2 is
replaced with a fallback notice:

```
⚠️ HAIKU_DOWN × 3  consecutive failures  ·  last: url:timeout  ·  RAG falling back to cosine threshold
```

See §7 below for the ladder.

---

## 4. Status line 3 — final recall summary

```
> 📚 recall: 10 cards · top=0.68 · ⚙️ judge+reform · 💭 mode=general · 🟢 conf=0.92 · reform→venlafaxine side effects · literal match treated as known entity
> 👤 venlafaxine-XR-missed-dose 2026-04-12 🟠 0.78
> 🌐 SSRI-general-mechanism 2026-04-09 🟡 0.54
> ...
```

Field layout (header line):

| Field | Meaning |
|---|---|
| `📚 recall: N cards` | Final N after threshold filtering |
| `· /recall` | Explicit `/recall` slash used |
| `· ✍️ /decision` | `/decision` slash used; card will be tagged `personal_persistent` at refine time |
| `· ⚡ aggregate` | `aggregate=true` turn; `top_k=TOP_K_AGGREGATE` (default 20) |
| `top=0.XX` | Top-1 reranker score |
| `⚙️ <route_path>` | Who made the routing decision; see §6 |
| `⚙️ <route_path>+reform` | `+reform` suffix indicates a reformulated query was used |
| `💭 <judge verdict>` | Same fields as Status line 2, minus the leading emoji, so the audit trail is preserved when Status 2 was suppressed |

---

## 5. Recall-list entry legend

Each card in the recall block:

```
> 👤 venlafaxine-XR-missed-dose  2026-04-12  🟠 0.78
```

Knowledge-identity icon:

| Icon | `knowledge_identity` |
|---|---|
| 👤 | `personal_persistent` — durable user fact (medications, hardware, decisions) |
| 🌐 | `universal` — generic reference knowledge |
| ⏳ | `personal_ephemeral` — time-bound (an upcoming flight, a one-off appointment) |
| 🔗 | `contextual` — only meaningful inside a named scenario |
| 📄 | fallback — card has no `knowledge_identity` frontmatter |

Freshness dot (appended to the reranker score):

| Dot | Bonus range | Typical age |
|---|---|---|
| 🔴 | ≥ 0.90 | < 1 week |
| 🟠 | ≥ 0.70 | < 1 month |
| 🟡 | ≥ 0.50 | < 3 months |
| 🟢 | ≥ 0.30 | < 6 months |
| ⚪ | > 0.01 | older but non-zero bonus |
| (none) | 0 | freshness weighting disabled or date missing |

---

## 6. `route_path` taxonomy

The `⚙️ <route_path>` field identifies which tier made the decision.

| Value | Meaning |
|---|---|
| `cheap:short` | Cheap-gate skipped the turn as too short |
| `cheap:long` | Cheap-gate passed the turn as long enough to warrant recall without a judge |
| `cheap:first_msg` | Cheap-gate passed because it is the first message in the conversation |
| `cheap:noise` | Cheap-gate skipped the turn as noise (ack-only) |
| `cheap:anchor` | Concept-anchor match forced recall |
| `judge:rag=X \| mode=X \| agg=X \| shift=X` | Haiku RecallJudge returned a verdict; the individual flags are shown |
| `judge:fail→fallback` | Judge failed; cosine threshold routed the decision |
| `slash:native` | `/native` override |
| `slash:recall` | `/recall` override |
| `slash:decision` | `/decision` override |

A `+reform` suffix on any `judge:*` entry indicates that the judge
supplied a reformulated query which was used for embedding instead of
the raw user turn.

---

## 7. `HAIKU_DOWN` warning ladder

The Filter maintains `_judge_fail_streak`, reset to 0 on every
successful judge verdict.

| Streak | Behaviour |
|---|---|
| 1 | Silent single-turn fallback to cosine. No visible badge. |
| 2 | Silent fallback continues. No visible badge. |
| ≥ 3 | Inline badge: `⚠️ HAIKU_DOWN × N  consecutive failures  ·  last: <err_tag>` |

`<err_tag>` is one of `url:timeout`, `url:5xx`, `parse:json`,
`parse:schema`, or `key:missing`. A single successful verdict clears
the counter and the warning disappears on the next turn.

The threshold is three failures because transient OpenRouter blips
commonly produce one or two failures per hour; three in a row is
strong evidence of a sustained outage (key expiry, quota exhaustion,
or upstream incident).

---

## 8. Confidence tier colours

| Dot | Range | Interpretation |
|---|---|---|
| 🟢 | ≥ 0.85 | Judge is confident. Usually a clean pronoun reference, a well-known entity, or a clear mode signal. |
| 🟡 | 0.60 - 0.85 | Default working range. Majority of turns land here. Not a quality flag. |
| 🔴 | < 0.60 | Judge is uncertain. Verdict is worth reviewing. A consistent run of 🔴 suggests either degraded context (first message in a new topic) or a prompt that could use anchor tokens. |

Confidence colours are rendered on Status line 2 and in the `💭`
field of Status line 3.

---

## 9. Outlet badge — daemon refinement status

Appended to the assistant's reply when `DAEMON_REFINE_URL` is
configured. The Filter polls
`GET /refine_status?conversation_id=<id>` and renders:

```
🛰️ daemon · 🟡 PENDING · i: 1.2k · o: 480 · $0.003
```

States reported by the `/refine_status` endpoint:

| State | Emoji | Meaning |
|---|---|---|
| `SKIP` | ⏸️ | Echo Guard or ephemeral judge skipped this conversation; no cards written. |
| `PENDING` | 🟡 | Daemon has queued the conversation; not yet refined. |
| `DONE` | 🟢 | Cards written and upserted to Qdrant. |
| `BLOCKED` | 🔴 | Echo Guard HIGH tier rejected; duplicate of an existing card. |
| `ERROR` | ⚠️ | Daemon hit an error; entry appended to the Issue Log. |
| `COLD` | 🧊 | Endpoint unreachable — the daemon service is probably not running. |
| (no badge) | — | `REFINE_STATUS_ENABLED=false` or `DAEMON_REFINE_URL` unset. |

The badge is a snapshot taken at outlet time. If the daemon finishes
refining after the outlet returns, the badge does not update until the
next turn. Out-of-band notifiers (desktop notifications, tray indicator)
cover the "completed after the fact" case.

---

## 10. Cost footer

The tail of the outlet line reports per-turn cost:

```
i: 1.2k · o: 480 · $0.003
```

- `i:` — total input tokens across every LLM call initiated by the
  Filter during this turn (RecallJudge + any L4 agent call).
- `o:` — total output tokens (same scope).
- `$X.XXX` — priced via a small model-pricing table in the Filter. Not
  authoritative (it is not driven by OpenRouter's billing API); a fast
  estimate.

Turns that made no LLM calls (e.g. slash overrides, cheap-gate skips)
render `i: 0 · o: 0 · $0.000`.

---

## 11. Suppression rules

Not every turn emits every line. Common exclusions:

- **Slash override turns** — Status 1 fires; Status 2 is absent (no
  judge call); Status 3 is present when recall happened.
- **Concept-anchor hits** — Status 1 shows `⚡ anchor pass`; Status 2
  is absent.
- **Cheap-gate skips** — Status 1 shows `🔇 RAG skipped`; Status 2 and
  Status 3 are absent (no recall happened).
- **`MODE_JUDGE_ENABLED=false`** — the RecallJudge is disabled
  entirely; all turns go through cosine thresholding. Status 2 never
  appears; Status 3's `⚙️` field reads `judge:off`.
- **Judge returns `needs_rag=false`** — Status 2 fires with the judge
  verdict; Status 3 is absent (no recall).

### Common questions

**Q: "Why did `⚙️ judge` appear but `💭 mode=general` did not?"**
A: `⚙️` identifies the decision-maker (judge / slash / cheap gate);
`💭` shows the resulting verdict. Both appear on `judge:*` routes; on
non-judge routes the `💭` field is suppressed because there is no
verdict to report.

**Q: "I keep getting 🔴 conf on my queries. Bad?"**
A: Not necessarily — a few 🔴 in a row means the judge is consistently
uncertain on your content. Common causes: vault vocabulary is specific
enough that the judge has no training prior (add tokens to
`ANCHOR_TOKENS` to force-route them as `cheap:anchor`), or the
conversation opened mid-topic with no grounding.

**Q: "Can I disable the outlet badge entirely?"**
A: Yes — set `REFINE_STATUS_ENABLED=false` and leave
`DAEMON_REFINE_URL` empty. The badge disappears; the cost footer also
disappears.
