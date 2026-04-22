# RAG Server

FastAPI service hosting the retrieval half of Throughline:

- Dense embeddings via `BAAI/bge-m3` (1024-dim, L2-normalised).
- Cross-encoder reranking via `BAAI/bge-reranker-v2-m3`.
- A thin proxy over Qdrant for vector search.
- A `/refine_status` endpoint the OpenWebUI Filter polls to render the
  per-conversation daemon status badge.

The file was originally named `macos_rag_server_BAAI.py`; it is cross-platform
(MPS on Apple Silicon, CUDA on Nvidia, CPU fallback elsewhere) and is simply
`rag_server.py` here.

---

## Endpoints

### `POST /v1/embeddings`

OpenAI-compatible. Accepts either a single string or a list.

```json
{ "input": "some text", "model": "bge-m3" }
```

Response mirrors OpenAI's embedding response shape:

```json
{
  "object": "list",
  "data": [{"object": "embedding", "embedding": [...], "index": 0}],
  "model": "bge-m3",
  "usage": {"prompt_tokens": 5, "total_tokens": 5}
}
```

### `POST /v1/rerank`

Cross-encoder score for every `(query, document)` pair. Returns results
sorted by `relevance_score` descending.

```json
{ "query": "...", "documents": ["doc1", "doc2", ...], "model": "bge-reranker" }
```

### `POST /v1/rag`

The one-shot retrieval endpoint the Filter uses.

Request body:

| Field | Type | Default | Meaning |
|---|---|---|---|
| `query` | string | required | User turn or reformulated query |
| `top_k` | int | 10 | Final result count after rerank+boosts |
| `candidate_k` | int | 30 | Qdrant search limit before rerank |
| `knowledge_identity` | string? | null | Optional Qdrant pre-filter |
| `freshness_weight` | float | 1.0 | 0 disables; 1.0 = default half-life bonus |
| `collection` | string? | null | Must appear in `RAG_ALLOWED_COLLECTIONS` |
| `pp_boost` | float? | env default | Add-on for `knowledge_identity=personal_persistent` |
| `group_boost` | float? | env default | Add-on when `payload.group == group_key` |
| `group_key` | string? | null | Key for `group_boost` matching |

Response:

```json
{
  "results": [
    {
      "title": "...", "knowledge_identity": "...", "tags": [...],
      "date": "...", "path": "...",
      "body_preview": "first 500 chars",
      "body_full": "up to ~20k chars",
      "vector_score": 0.81, "rerank_score": 5.3,
      "freshness_bonus": 0.42, "payload_boost": 0.0,
      "final_score": 5.72
    }
  ],
  "total_candidates": 30
}
```

Ranking pipeline:

1. Embed query with bge-m3 (max_length 512).
2. Qdrant cosine search (`candidate_k` candidates, optional
   `knowledge_identity` filter).
3. Rerank candidate `body_preview` fields with bge-reranker-v2-m3
   (max_length 512, batch 100).
4. Add `freshness_bonus` + `payload_boost` to the rerank score.
5. Sort by final score, keep top_k.

### `GET /v1/rag/health`

Returns `{ "status": "ok", "qdrant": "ok", "points_count": <int> }` when the
configured collection is reachable.

### `GET /refine_status?conv_id=<uuid or >=8-char prefix>`

Reads the daemon's `refine_state.json`, maps the daemon's internal
`last_status` to one of seven badge archetypes consumed by the Filter, and
returns the slice list + trigger hint + echo-guard metadata.

Badge archetypes:

| Archetype | Daemon statuses that map to it | Filter meaning |
|---|---|---|
| `REFINED` | `refined`, `over_compressed` | All slices succeeded |
| `PARTIAL` | `partial_refined` | Some slices succeeded |
| `SUGGESTED` | `extension_skipped` | Worth-refining but auto-refine off |
| `SKIPPED_NOISE` | `extension_noise_*`, `skipped`, `skip_no_valuable_slice` | Judge said noise |
| `SKIPPED_EPHEMERAL` | `skip_ephemeral` | One-shot content |
| `SKIPPED_NATIVE` | `skip_native_llm` | LLM already handles it |
| `ECHO_SKIP` | `skip_rag_echo` | Echo-guard intercepted it |
| `FAILED` | `slice_failed`, `refine_failed`, `*_route_failed`, `retry_gaveup`, `force_one_failed` | Red; see daemon log |
| `PENDING` | (no entry yet) | Daemon hasn't processed this conv |
| `UNKNOWN` | (unmapped status) | Shouldn't happen in steady state |

State file mtime is cached, so the endpoint is cheap to poll.

---

## Running it

```bash
pip install fastapi uvicorn pydantic torch transformers qdrant-client sentence-transformers
export QDRANT_URL=http://localhost:6333
export VAULT_PATH=/path/to/your/vault   # only needed by ingest, not the server
uvicorn rag_server:app --host 0.0.0.0 --port 8000
```

The module also has a `__main__` block that prints bind details and starts
uvicorn directly:

```bash
python rag_server.py
```

---

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `QDRANT_URL` | `http://localhost:6333` | Qdrant HTTP endpoint |
| `RAG_COLLECTION` | `obsidian_notes` | Primary collection name |
| `RAG_ALLOWED_COLLECTIONS` | `obsidian_notes` | Comma-separated whitelist for `collection` field |
| `EMBED_MODEL` | `BAAI/bge-m3` | HuggingFace model id for embeddings |
| `RERANK_MODEL` | `BAAI/bge-reranker-v2-m3` | HuggingFace model id for reranker |
| `RAG_DEVICE` | auto | Force `mps` / `cuda` / `cpu` |
| `RAG_FRESHNESS_HALF_LIFE` | `365` | Days for freshness decay |
| `RAG_PP_BOOST` | `0.0` | Default add-on for `personal_persistent` payloads |
| `RAG_GROUP_BOOST` | `0.0` | Default add-on when `payload.group == group_key` |
| `REFINE_STATE_FILE` | `~/.local/share/throughline/state/refine_state.json` | Daemon state path |
| `RAG_HOST` | `0.0.0.0` | uvicorn bind host |
| `RAG_PORT` | `8000` | uvicorn bind port |

---

## Dependencies

- Python 3.10+
- `torch` (with MPS or CUDA if available)
- `transformers` (pulls the two BAAI models on first load)
- `fastapi`, `uvicorn`, `pydantic`
- A running Qdrant instance (tested against 1.9.x)

First run downloads the models (~2 GB) into the HuggingFace cache. Keep the
server process alive; weights stay resident in GPU/MPS memory.

---

## How reranker and boosts compose

The Filter sends a single query to `/v1/rag` with the per-turn boost knobs.
The server returns up to `top_k` results already sorted by

```
final_score = rerank_score + freshness_bonus + payload_boost
```

`freshness_bonus` is a linear decay from `weight * 1.0` (today) to `0.0`
(>= one half-life old), clamped at zero.

`payload_boost` stacks `pp_boost` (rewards notes the user marked as
long-term identity / configuration / architectural) and `group_boost`
(rewards notes sharing an explicit `group` tag with the caller's
`group_key`).

If you want rerank-only ranking, set all three knobs to 0.
