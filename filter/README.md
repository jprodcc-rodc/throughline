# Throughline OpenWebUI Filter

An OpenWebUI Filter that routes each user turn through a three-tier gate —
cheap heuristics, Haiku-based RecallJudge, and a backing RAG server — and
injects retrieved notes into the model's system prompt. It also reads a daemon
refinement-status endpoint and renders a per-turn status badge + cost footer in
the outlet.

---

## 1. What this Filter does

- **Inlet:** decides whether the current turn needs RAG recall. Short / noisy /
  marker-only turns skip the LLM call entirely. Longer turns invoke a Haiku
  RecallJudge that returns a structured JSON verdict (`mode`, `needs_rag`,
  `aggregate`, `topic_shift`, `reformulated_query`, `confidence`). On judge
  failure the Filter falls back to a cosine-similarity threshold.
- **Context injection:** pulls personal context cards from valves (L1) and
  optionally from a personal-agent HTTP service (L4), wrapped in a hardened
  "DATA not INSTRUCTIONS" guard to neutralise prompt-injection attempts.
- **Outlet:** appends a status badge (RAG decision + daemon refinement status)
  and a cost footer (tokens + USD) to the assistant's reply.

---

## 2. Prerequisites

- OpenWebUI **0.8.12 or later** (Functions → Filters with full Valves support).
- A RAG backend exposing `POST /rag` and `GET /refine_status?conversation_id=…`
  (see the sibling `rag_server/` package in this repo).
- A Qdrant instance reachable from the RAG backend (embedding + rerank happen
  server-side; the Filter only speaks HTTP to the RAG server).
- An OpenRouter API key with access to `anthropic/claude-haiku-4.5`
  (the default judge model; overridable via the `JUDGE_MODEL` valve).
- Python 3.11+ on the Filter runtime (OpenWebUI embeds its own interpreter;
  no additional packages beyond `httpx` and the OpenWebUI stdlib are needed).

---

## 3. Installation

1. Copy `filter/openwebui_filter.py` to your clipboard.
2. In OpenWebUI, go to **Admin Panel → Functions → Create new Function**.
3. Paste the file contents. Name it `throughline_filter` (or anything — the
   class name `Filter` is what OpenWebUI binds to).
4. Click **Save**. OpenWebUI will import the module and register the Valves.
5. Click the new function's **Valves** icon and set at minimum:
   - `OPENROUTER_API_KEY`
   - `RAG_SERVER_URL` (default `http://localhost:8000`)
6. Toggle the function **on** globally, or attach it to specific Models.

To update the Filter later, either repaste or use the REST endpoint
`POST /api/v1/functions/id/<id>/update` with a JWT in the `Authorization`
header.

---

## 4. Valves reference

| Name | Default | What it controls |
|---|---|---|
| `OPENROUTER_API_KEY` | `""` | OpenRouter key for the RecallJudge. Empty → falls back to env `OPENAI_API_KEY`. Neither set → judge is skipped and cosine threshold routes. |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | Override for OpenRouter-compatible proxies. |
| `JUDGE_MODEL` | `anthropic/claude-haiku-4.5` | Model used for the RecallJudge verdict call. |
| `MODE_JUDGE_TIMEOUT` | `5.0` | Hard timeout (seconds) for the judge HTTP call. On timeout the Filter falls back to cosine. |
| `RAG_SERVER_URL` | `http://localhost:8000` | Base URL of the backing RAG server. |
| `PERSONAL_AGENT_URL` | `""` | Optional L4 personal-agent HTTP endpoint. Empty → skipped. |
| `CONTEXT_CARDS` | `""` | L1 personal context cards inlined as a single string. Injected verbatim inside a prompt-injection guard. |
| `ANCHOR_TOKENS` | `""` | Newline- or comma-separated concept anchors. A match in the user turn forces auto-recall (no judge call). Empty → falls back to a short generic tech list. |
| `CARD_CONTENT_MAX_CHARS` | `2000` | Per-card truncation cap for `CONTEXT_CARDS`, preventing a single long card from monopolising the system prompt. |
| `COSINE_THRESHOLD` | `0.60` | Cutoff used by the judge-fallback path when the RecallJudge is unavailable. |
| `RECALL_LOG_PATH` | `""` | Path for the JSONL recall-decision log. Empty → uses `$THROUGHLINE_LOG_DIR` env or `~/throughline_recall_history.jsonl`. |
| `DAEMON_REFINE_URL` | `""` | Daemon refinement-status endpoint. Empty → outlet skips the refine badge. |
| `TOP_K_DEFAULT` | `10` | Number of RAG hits requested on normal turns. |
| `TOP_K_AGGREGATE` | `20` | Bumped top-k when the judge returns `aggregate=true`. |

See the top of `openwebui_filter.py` for the full `Valves` pydantic class —
every field carries an inline description string that OpenWebUI renders in the
Admin UI.

---

## 5. Badge reference

The outlet appends a single-line badge to each reply. Emoji legend:

| Badge | Meaning |
|---|---|
| `📚 auto` | RecallJudge decided this turn needs recall (default mode). |
| `✍️ decision` | User explicitly invoked `/decision` — persistent mode. |
| `🎓 PTE mode active` | PTE study pack hit (prefix or topic). |
| `🧪 brainstorm` | Judge classified the turn as brainstorming — recall suppressed. |
| `⚡ aggregate` | Judge set `aggregate=true`; `top_k` bumped to `TOP_K_AGGREGATE`. |
| `🔇 RAG skipped` | Cheap-gate decided this turn skipped RAG (noise / marker-only / explicit `/native`). |
| `📡 ECHO_SKIP` | Daemon is likely to echo-skip this turn at ingest time. |
| `🟢 / 🟡 / 🔴` | RecallJudge confidence tiers (≥ 0.85 / 0.60-0.85 / < 0.60). |
| `🛰️ daemon` | Prefix for the daemon refinement-status badge that follows. |
| `⚠️ HAIKU_DOWN × N` | `N` consecutive judge failures. Shown for `N ≥ 3`. |

Below the badge, a second line shows the token + cost footer for the turn.

---

## 6. Troubleshooting

- **`no_api_key`** — neither `OPENROUTER_API_KEY` valve nor `OPENAI_API_KEY`
  env is set on the OpenWebUI runtime. Set one and save; Filter re-reads on
  each call (no restart required).
- **`haiku_down` once** — single transient judge failure (timeout or 5xx). The
  Filter already fell back to cosine on that turn; next turn retries.
- **`⚠️ HAIKU_DOWN × 3+`** — three or more consecutive judge failures. Check
  OpenRouter status, API-key quota, and `MODE_JUDGE_TIMEOUT`. If persistent,
  the cosine fallback keeps recall usable but loses brainstorm detection and
  query reformulation.
- **Empty RAG results** — verify `RAG_SERVER_URL` is reachable from the
  OpenWebUI container (`curl $RAG_SERVER_URL/health`) and that the backing
  Qdrant collection is populated. The Filter will still render a badge but the
  injected context section will be empty.
- **Judge keeps returning `needs_rag=false`** — the RecallJudge prompt is
  conservative by design: short turns, acknowledgements, and meta-questions
  about the assistant itself are routed to `native` (no recall). Add
  disambiguating concept anchors via the `ANCHOR_TOKENS` valve to force recall
  on in-vocabulary terms.
