# Design Decisions

> Each entry records: the alternatives considered, the call made, and
> the reason. "What" belongs in `ARCHITECTURE.md`; this document
> answers "why". Entries are in no particular order — each is
> self-contained.

---

## Contents

- [1. Haiku RecallJudge over regex or a larger model](#1-haiku-recalljudge-over-regex-or-a-larger-model)
- [2. Four-layer personal context instead of system-prompt stuffing](#2-four-layer-personal-context-instead-of-system-prompt-stuffing)
- [3. Dual-write (buffer stub + formal note)](#3-dual-write-buffer-stub--formal-note)
- [4. Forward-slash path normalisation as a load-bearing contract](#4-forward-slash-path-normalisation-as-a-load-bearing-contract)
- [5. Four-value `knowledge_identity` instead of two](#5-four-value-knowledge_identity-instead-of-two)
- [6. Opt-in Pack system with 4-tier detection](#6-opt-in-pack-system-with-4-tier-detection)
- [7. Separate Qdrant collections for sensitive packs](#7-separate-qdrant-collections-for-sensitive-packs)
- [8. Prompts stay hardcoded in Python](#8-prompts-stay-hardcoded-in-python)
- [9. English-only open-source build](#9-english-only-open-source-build)

---

## 1. Haiku RecallJudge over regex or a larger model

### Alternatives considered

- **Pure regex / heuristics** — classify turns via hand-written rules.
  No per-turn LLM cost, zero latency.
- **Large model judge** — use Sonnet or GPT-class to classify. High
  quality but slow and expensive per turn.
- **Multiple small judges in parallel** — one for mode, one for
  aggregate, one for topic shift, one for query rewrite. Each can be
  cheap individually.
- **Small-model single-call judge** (chosen).

### Call

A single Haiku-class call that returns a structured JSON verdict with
five fields (`needs_rag`, `mode`, `aggregate`, `topic_shift`,
`reformulated_query`, `confidence`).

### Reason

- **Regex drift.** Every new user idiom ("those?", "what about it?",
  language-switches, topic anchors) requires a new pattern. Maintenance
  cost rises; judgement remains brittle on anything not pre-listed.
- **Big-model latency.** Sonnet-class latency on short turns (~2-4 s)
  is noticeable in an interactive chat.
- **Parallel-judge coupling.** When one judge says "this is
  brainstorming" and another says "aggregate over all your notes", the
  calling Filter has to arbitrate. That arbitration logic drifts from
  the judges themselves.
- **Single-call shape.** Haiku is fast enough (~400-800 ms) to hide in
  the first-token-latency slot. One round trip, one coherent verdict,
  no arbitration. Cost is tiny (fractions of a cent per turn). When
  the judge fails, the Filter falls back to a cosine threshold — a
  coarser but correct safety net.

A `_judge_fail_streak` counter surfaces sustained failures in the
outlet badge (`⚠️ HAIKU_DOWN × 3+`). The fallback is intentionally
visible: users should notice when degraded classification is active.

---

## 2. Four-layer personal context instead of system-prompt stuffing

### Alternatives considered

- **Single static system prompt** with everything about the user
  pasted in.
- **RAG-over-personal-profile** — store profile notes in the same
  Qdrant collection as general knowledge and let retrieval surface
  them.
- **Dedicated personal-context service** — one HTTP endpoint that
  returns "what the model needs to know about this user for this
  query".
- **Layered stack** (chosen) — static prefix + retrieval boost +
  auto-generated cards + optional service.

### Call

Ship four independent layers, each of which is individually useful:

- **L1: `CONTEXT_CARDS` valve** — static system-prompt prefix, always
  on, wrapped in a DATA-not-INSTRUCTIONS guard.
- **L2: reranker boost** — `knowledge_identity=personal_persistent`
  gets a score boost; shared `group:` tags bundle related cards.
- **L3: auto-generated context cards** — `contexts_auto_builder.py`
  scans vault profile files and writes one context card per topic.
- **L4: optional personal-agent HTTP service** — user-supplied
  synthesiser, called from the Filter inlet.

### Reason

- **Stuffing breaks at scale.** A fully expanded user context (current
  medications, hardware, projects, relationships) is thousands of
  tokens even when compressed. Paying that on every turn is wasteful,
  and LLMs lose recency-weighted attention on the middle of long
  prompts.
- **RAG-over-profile leaks content into the shared index.** Personal
  facts stored in the same collection as general knowledge can be
  surfaced by a query that doesn't intend to reach them. Worse, if the
  index is ever exported or shared for debugging, private facts go
  with it.
- **Single-service coupling is fragile.** If the personal agent is
  down, the entire personal-context pathway breaks. An escape hatch
  that sits in front of a static layer is more robust.
- **Mechanism vs content.** The open-source build ships the mechanism
  — scanner, sync, reranker hooks, agent scaffolding — without any of
  the content. Any user's L1 valves / L3 cards / L4 service content
  live entirely in their own fork. That separation is what makes this
  layer safe to open-source at all.

---

## 3. Dual-write (buffer stub + formal note)

### Alternatives considered

- **Write-approve-upsert** — daemon writes a pending stub, user
  approves, only then does the formal card land and the Qdrant point
  get upserted.
- **Write-formal-only** — skip the stub; rely on post-hoc triage by
  searching the vault for recent additions.
- **Dual-write** (chosen) — formal card and Qdrant point land
  immediately; a buffer stub is written alongside with a back-pointer
  to the formal card, awaiting triage.

### Reason

- **Write-approve coupling kills RAG.** In practice, users fall behind
  on triage. If approval gates indexing, RAG silently degrades while
  the queue grows. The queue then becomes intimidating, and users
  abandon triage entirely.
- **Formal-only loses reversibility.** Without a stub, there is no
  triage surface — no list of "things the daemon recently decided to
  add to durable memory". Bad cards slip into the index unnoticed.
- **Dual-write decouples the two concerns.** The formal card is
  immediately useful (RAG can recall it within minutes). The stub is a
  cleanup-afterwards surface — the user can reject something days
  later, and the reject path cleanly removes all three artefacts
  (stub, formal, Qdrant point). Neither piece blocks the other.

The cost is one extra small file per refinement. That is cheap.

---

## 4. Forward-slash path normalisation as a load-bearing contract

### Alternatives considered

- **Store the raw platform path as the Qdrant point ID** — whatever
  `os.path.join` produces on the ingest host becomes the ID.
- **Hash the card body** — IDs derived from content, not path.
- **UUIDs** — non-deterministic IDs stored in the card's frontmatter.
- **Forward-slash-normalised path hash** (chosen).

### Reason

- **Raw platform paths diverge.** A card at
  `10_Tech/10.01_Network/foo.md` ingested from Windows yields
  `10_Tech\10.01_Network\foo.md`; the same card ingested from macOS
  yields the forward-slash variant. MD5 hashes of those two strings
  differ. Qdrant ends up with two points for one card, and the
  collection size silently doubles.
- **Body hashing** makes IDs unstable: any edit to the card body
  produces a new ID, orphaning the old Qdrant point and leaving the
  collection to leak over time.
- **UUIDs in frontmatter** require migrating every existing card to
  add the field, and break on clone/copy (both cards now carry the
  same UUID).
- **Normalised-path hashing** gives deterministic, stable, platform-
  independent IDs with no frontmatter dependency. The cost is a single
  `_norm_path()` helper that every path must flow through before
  `make_point_id()`. It is called out in the module docstring, in the
  `make_point_id()` comment, and in `scripts/README.md`. Future
  refactors must preserve it.

This is the one behaviour of the ingest script that a future
contributor can accidentally break catastrophically. Hence the
redundant documentation.

---

## 5. Four-value `knowledge_identity` instead of two

### Alternatives considered

- **Binary** — `personal` vs `not_personal`. Simplest classifier; easy
  for a refiner LLM to emit.
- **Three-value** — add `contextual` for facts tied to a specific
  scenario.
- **Four-value** (chosen) — `universal`, `personal_persistent`,
  `personal_ephemeral`, `contextual`.
- **Many-valued / free-form tags** — let the refiner emit arbitrary
  category strings.

### Reason

- **Binary conflates time and generality.** "User's current
  medication" and "user's flight tomorrow" are both `personal`, but
  they have very different half-lives. Using one label for both forces
  the RAG layer to treat them identically — either always surface both
  (noise on old travel plans) or decay both (losing durable
  medications).
- **Three-value misses the freshness axis.** Adding `contextual`
  catches scenario-bound facts but leaves `personal` ambiguous on
  durability.
- **Four-value separates two orthogonal axes:** durability
  (`personal_persistent` vs `personal_ephemeral`) and scope
  (`universal` vs `personal` vs `contextual`). Each combination maps
  to a distinct RAG behaviour — reranker boost, freshness half-life,
  and filter eligibility all depend on the value.
- **Free-form tags** lose the ability to express defaults in code.
  Downstream consumers (RAG server, Filter, auto-refine) all need
  predictable enum values to switch on.

Default-to-`universal` when ambiguous. The guidance in the refiner
prompt is explicit: it is safer to miss a `personal_persistent`
(harmless over-generic answer) than to tag a generic fact as personal
(clutters the user's personal index).

---

## 6. Opt-in Pack system with 4-tier detection

### Alternatives considered

- **No packs** — one monolithic refiner prompt for every domain.
- **Always-on packs** — the daemon hot-swaps its prompts by topic on
  every conversation.
- **Explicit-only packs** — packs only trigger on a literal `@marker`
  in the user's message.
- **4-tier detection** (chosen) — `@marker` → topic pin → source model
  → route hint.

### Reason

- **Monolithic prompts fail at the extremes.** A refiner prompt that
  tries to handle exam preparation *and* casual conversation *and*
  technical architecture ends up too vague for any of them. A study
  pack wants to preserve the verbatim original prompt for drill
  purposes; a general-knowledge pack wants aggressive
  de-individualisation. These are directly contradictory rules.
- **Always-on detection is expensive.** Running a pack-detection LLM
  call on every conversation adds tokens and latency without adding
  quality for the 80% of turns that are general chat.
- **Explicit-only is too high-friction.** Users forget to type
  `@pack`. The pack's value is lost on every unmarked turn.
- **4-tier detection** layers the cheap tests first: literal marker
  hit (cheapest), then a configured topic pin (still local string
  work), then the `source_model` field (available in the exporter
  output), then a route hint (which default path would this card land
  in). First hit wins. No LLM call is introduced by pack detection
  itself.

Packs are opt-in: if none match, the default pipeline runs unchanged.
Pack authors get a narrow surface to override (slicer, refiner,
routing, a small set of policies) without touching the daemon core.

---

## 7. Separate Qdrant collections for sensitive packs

### Alternatives considered

- **Single collection + `ki_filter` at query time** — all packs write
  to `obsidian_notes`; sensitive content is filtered out of retrieval
  by filter logic in the RAG server.
- **Single collection + path-prefix blocklist** — sensitive cards
  never reach the index at all, enforced by
  `_QDRANT_DEFAULT_FORBIDDEN_PREFIXES` at write time.
- **Separate collection per sensitive pack** (chosen, preserved as a
  mechanism).

### Reason

- **Query-time filtering is fragile.** Any pathway into retrieval
  that forgets to apply the filter leaks content. Cross-collection
  queries, new endpoints, debug exports, client-side caches — each is
  a new place the filter must be remembered.
- **Blocklist at ingest is correct but insufficient.** It keeps
  sensitive cards out of the default collection, but provides no way
  to run *domain-specific* retrieval (e.g. during a session where the
  sensitive content is supposed to be active). Blocklist implies
  "never retrieve"; sometimes the need is "retrieve only when asked".
- **Separate collection** gives hard isolation plus an opt-in
  retrieval surface. A pack's `pack.yaml` sets
  `qdrant_collection: <name>` and `qdrant_skip_default: true`; cards
  from that pack land only in the named collection. The RAG server's
  `RAG_ALLOWED_COLLECTIONS` env var controls which collections are
  reachable at query time. Callers targeting the alternate collection
  must explicitly name it.

The open-source build ships this *mechanism* (per-pack collection,
default-write forbidden-prefixes, allowlist in the RAG server) without
shipping any sensitive-domain pack itself. Users who need a clinical
or otherwise sensitive pack build one on their own fork with their own
safeguards. See `CHINESE_STRIP_LOG.md` for what was stripped.

---

## 8. Prompts stay hardcoded in Python

### Alternatives considered

- **Runtime-loaded prompts** — Filter and daemon read `.md` files on
  each LLM call.
- **Config-driven template** — prompts are Jinja / f-string templates
  that load at startup from config.
- **Hardcoded strings in Python** (chosen) — prompt text is a module-
  level constant.

### Reason

- **Self-contained packaging.** The Filter is a single file pasted
  into OpenWebUI's Functions UI. A runtime loader would require either
  bundling prompt files inside the Python source (defeating the
  "edit the prompt externally" goal) or reading from a filesystem
  path that the OpenWebUI container may not mount.
- **No silent-outage failure mode.** A missing prompt file at startup
  would be a crash; a typoed prompt path would be a same-day
  not-reproducible failure. Hardcoding makes the prompt as durable as
  the code itself.
- **Performance.** Loading a multi-kilobyte prompt on every turn
  costs a small amount of I/O. Not dramatic, but meaningful on
  first-token latency.
- **Review surface exists anyway.** `prompts/en/*.md` contains a
  verbatim mirror of the runtime strings. It is the review /
  translation / PR surface. If the project ever grows a
  `PROMPT_LANG` valve, the runtime loader slots in front of the
  hardcoded constant as a fallback, and the markdown files become the
  source of truth. That upgrade is not scheduled.

---

## 9. English-only open-source build

### Alternatives considered

- **Ship the upstream bilingual codebase** — keep the original CJK
  comments, prompts, and regex alongside English translations.
- **Add a `LANG` valve** that loads a localised prompt at runtime from
  `prompts/<lang>/*.md`.
- **English-only** (chosen).

### Reason

- **The bilingual upstream carried identity.** The original codebase
  mixed Chinese comments with identity-bearing examples (user names,
  private IPs, medication names, specific dates). Sanitising a
  bilingual file leaves plenty of places for an identity phrase to
  survive a `grep`. An English-only build is grep-auditable end-to-
  end: `[\u4e00-\u9fff]` matches zero, always.
- **Runtime `LANG` valve without translations is a tease.** The
  `prompts/zh/` directory ships empty (`.gitkeep` only) precisely
  because the project has no maintainer capacity to keep a Chinese
  prompt in sync with the English one. Shipping an incomplete
  localisation layer creates false expectations.
- **Community re-i18n path is preserved.** Forkers who want a
  localised build can drop their translations into `prompts/<lang>/`,
  wire the runtime loader described in §8, and publish a fork-specific
  release. The scaffolding (prompts extracted to mirror files, clear
  documentation in `prompts/README.md`) keeps that path open.
- **Stripping is documented.** `docs/CHINESE_STRIP_LOG.md` records
  every Chinese-specific construct that was removed, translated, or
  rewritten, and the Phase 6 risk level of each removal. A
  hypothetical future maintainer re-introducing Chinese has a
  regression scope to aim at.

Open-source safety matters more than user reach. The upstream user's
identity is thoroughly removable from an English-only build in a way
it cannot be from a bilingual one.
