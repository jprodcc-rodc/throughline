"""FastAPI RAG server: bge-m3 embeddings + bge-reranker-v2-m3 rerank + Qdrant retrieval.

Endpoints:
    POST /v1/embeddings       OpenAI-compatible embedding endpoint (bge-m3 by default)
    POST /v1/rerank           OpenAI-style rerank endpoint (bge-reranker-v2-m3 by default)
    POST /v1/rag              One-shot retrieval: embed -> Qdrant search -> rerank -> freshness
    GET  /v1/rag/health       Qdrant reachability + collection point count
    GET  /refine_status       Daemon state poll for OpenWebUI Filter badge (7-state archetype)

Device selection (in order of preference): MPS (Apple Silicon) -> CUDA -> CPU.
Override via env var RAG_DEVICE = mps | cuda | cpu.

Boost logic (per-request overrides supported):
    freshness_weight          Linear decay with a configurable half-life in days
    pp_boost  / group_boost   Optional reranker add-ons (request body only; defaults 0.0)

Configuration (env vars):
    QDRANT_URL                Default http://localhost:6333
    RAG_COLLECTION            Default obsidian_notes
    RAG_ALLOWED_COLLECTIONS   Comma-separated whitelist (default: obsidian_notes)
    EMBED_MODEL               Default BAAI/bge-m3
    RERANK_MODEL              Default BAAI/bge-reranker-v2-m3
    RAG_DEVICE                mps | cuda | cpu (default: auto)
    RAG_FRESHNESS_HALF_LIFE   Days, default 365
    RAG_PP_BOOST              Default 0.0 (no boost)
    RAG_GROUP_BOOST           Default 0.0 (no boost)
    REFINE_STATE_FILE         Path to daemon's refine_state.json
    RAG_HOST                  Default 0.0.0.0
    RAG_PORT                  Default 8000
"""

import asyncio
import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rag_server.embedders import create_embedder
from rag_server.rerankers import create_reranker
from rag_server.vector_stores import create_vector_store


# ==========================================
# 1. Pluggable embedder (U12) + reranker (U20)
# ==========================================
# Backend chosen via EMBEDDER / RERANKER env vars; default is the
# v0.1 behaviour (bge-m3 + bge-reranker-v2-m3). Swapping to openai /
# cohere / skip flips the backend without editing code.
#
# Instantiation is free — ensure_loaded() runs on the first real
# embed/rerank call so `import rag_server.rag_server` stays fast
# for tests and for a cold deploy that might want to fail closed
# on a bad config before it downloads a multi-GB model.
EMBEDDER = create_embedder()
RERANKER = create_reranker()
VECTOR_STORE = create_vector_store()
print(f"[rag_server] Embedder: {EMBEDDER.name} ({EMBEDDER.vector_size}-dim)")
print(f"[rag_server] Reranker: {RERANKER.name}")
print(f"[rag_server] Vector store: {VECTOR_STORE.name}")
print("[rag_server] Models will load on first /v1/embeddings or /v1/rerank call.")

# ==========================================
# 4. Qdrant configuration
# ==========================================
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("RAG_COLLECTION", "obsidian_notes")

# Whitelist of collection names accepted from the request body. Any other
# name supplied by a caller is silently ignored (defence against payload
# injection routing reads to an attacker-controlled collection).
_allowed_raw = os.getenv("RAG_ALLOWED_COLLECTIONS", COLLECTION)
ALLOWED_COLLECTIONS = {c.strip() for c in _allowed_raw.split(",") if c.strip()}
if COLLECTION not in ALLOWED_COLLECTIONS:
    ALLOWED_COLLECTIONS.add(COLLECTION)

# Default boost knobs — can be overridden per-request.
DEFAULT_FRESHNESS_HALF_LIFE_DAYS = float(os.getenv("RAG_FRESHNESS_HALF_LIFE", "365"))
DEFAULT_PP_BOOST = float(os.getenv("RAG_PP_BOOST", "0.0"))
DEFAULT_GROUP_BOOST = float(os.getenv("RAG_GROUP_BOOST", "0.0"))


def qdrant_request(method: str, path: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    url = QDRANT_URL + path
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[rag_server] Qdrant error: {e}")
        return None


# ==========================================
# 5. FastAPI app
# ==========================================
app = FastAPI(
    title=f"Throughline RAG server ({EMBEDDER.name} + {RERANKER.name})")


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "bge-m3"


@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    texts = request.input if isinstance(request.input, list) else [request.input]
    embeddings_list = await asyncio.to_thread(EMBEDDER.embed, texts)
    # We no longer have direct access to the tokenizer's exact count
    # (cloud embedders don't expose it at all); approximate at ~4
    # chars/token so the usage field stays a rough cost proxy.
    total_tokens = sum(len(t) for t in texts) // 4
    data = [
        {"object": "embedding", "embedding": emb, "index": i}
        for i, emb in enumerate(embeddings_list)
    ]

    return {
        "object": "list",
        "data": data,
        "model": request.model,
        "usage": {"prompt_tokens": total_tokens, "total_tokens": total_tokens},
    }


class RerankRequest(BaseModel):
    query: str
    documents: List[str]
    model: str = "bge-reranker"


@app.post("/v1/rerank")
async def create_reranking(request: RerankRequest):
    all_scores = await asyncio.to_thread(
        RERANKER.rerank, request.query, request.documents,
    )

    results = []
    for index in range(len(request.documents)):
        if index >= len(all_scores):
            break
        results.append({
            "index": index,
            "document": {"text": request.documents[index]},
            "relevance_score": all_scores[index],
        })

    results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
    return {"results": results}


class RAGRequest(BaseModel):
    query: str
    # Optional pre-filter on payload field: universal / personal_persistent / personal_ephemeral / contextual
    knowledge_identity: Optional[str] = None
    top_k: int = 10
    candidate_k: int = 30
    # Time-decay weight: 0 disables, 1.0 is the default (365-day half-life, max +1.0 bonus).
    freshness_weight: float = 1.0
    # Optional collection override. Must be in ALLOWED_COLLECTIONS; otherwise ignored.
    collection: Optional[str] = None
    # Optional rerank-side boosts (floats added to the rerank score before ranking).
    # pp_boost applies to payload.knowledge_identity == "personal_persistent".
    # group_boost applies to payload.group == request.group_key (if both set).
    pp_boost: Optional[float] = None
    group_boost: Optional[float] = None
    group_key: Optional[str] = None


@app.post("/v1/rag")
async def rag_query(request: RAGRequest):
    # Step 1: embed the query via the active embedder backend.
    embeddings = await asyncio.to_thread(EMBEDDER.embed, [request.query])
    if not embeddings:
        return {"results": [], "error": "empty embedding"}
    query_vector = embeddings[0]

    # Step 2: decide which collection to query. Whitelist-enforced.
    target_collection = COLLECTION
    if request.collection and request.collection in ALLOWED_COLLECTIONS:
        target_collection = request.collection

    # Vector search via the active backend (U21). The legacy
    # qdrant_request helper is kept for the health endpoint below so
    # the response shape stays Qdrant-specific, but the hot path is
    # abstracted — VECTOR_STORE=chroma flips without code edits.
    filter_: Optional[Dict[str, Any]] = None
    if request.knowledge_identity:
        # Qdrant filter schema. Chroma's `where` uses a different
        # shape; we pass None there and filter client-side below.
        if VECTOR_STORE.name == "qdrant":
            filter_ = {
                "must": [
                    {
                        "key": "knowledge_identity",
                        "match": {"value": request.knowledge_identity},
                    }
                ]
            }

    try:
        hits = await asyncio.to_thread(
            VECTOR_STORE.search, target_collection, query_vector,
            int(request.candidate_k), filter_,
        )
    except Exception as e:
        return {"results": [], "error": f"vector search failed: {e}"}

    # Normalize to the legacy `{id, score, payload}` shape the rest of
    # this handler expects.
    candidates = [
        {
            "id": h.get("id"),
            "score": h.get("score"),
            "payload": h.get("payload") or {},
        }
        for h in hits
    ]
    # Client-side knowledge_identity filter for non-Qdrant backends
    # that can't express the filter server-side.
    if request.knowledge_identity and VECTOR_STORE.name != "qdrant":
        candidates = [
            c for c in candidates
            if (c["payload"].get("knowledge_identity")
                == request.knowledge_identity)
        ]
    if not candidates:
        return {"results": []}

    # Step 3: rerank candidates via the active reranker backend.
    docs = [c["payload"].get("body_preview", "") for c in candidates]
    scores = await asyncio.to_thread(RERANKER.rerank, request.query, docs)

    # Step 4: freshness bonus + optional boosts + top_k cut.
    half_life = DEFAULT_FRESHNESS_HALF_LIFE_DAYS
    pp_boost = request.pp_boost if request.pp_boost is not None else DEFAULT_PP_BOOST
    group_boost = request.group_boost if request.group_boost is not None else DEFAULT_GROUP_BOOST
    now = datetime.now()

    def _parse_date(date_str: str):
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except (ValueError, AttributeError):
                continue
        return None

    def _freshness_bonus(date_str: str, weight: float) -> float:
        if weight <= 0:
            return 0.0
        dt = _parse_date(date_str)
        if dt is None:
            return 0.0
        days_ago = max(0, (now - dt).days)
        return weight * max(0.0, 1.0 - days_ago / half_life)

    def _payload_boost(payload: Dict[str, Any]) -> float:
        extra = 0.0
        if pp_boost and payload.get("knowledge_identity") == "personal_persistent":
            extra += pp_boost
        if group_boost and request.group_key and payload.get("group") == request.group_key:
            extra += group_boost
        return extra

    scored = []
    for candidate, rerank_score in zip(candidates, scores):
        payload = candidate.get("payload", {}) or {}
        date_str = payload.get("date", "")
        fresh = _freshness_bonus(date_str, request.freshness_weight)
        boost = _payload_boost(payload)
        final = rerank_score + fresh + boost
        scored.append((candidate, rerank_score, fresh, boost, final))

    ranked = sorted(scored, key=lambda x: x[4], reverse=True)[:request.top_k]

    results = []
    for candidate, rerank_score, fresh, boost, final_score in ranked:
        payload = candidate.get("payload", {}) or {}
        results.append({
            "title": payload.get("title", ""),
            "knowledge_identity": payload.get("knowledge_identity", ""),
            "tags": payload.get("tags", []),
            "date": payload.get("date", ""),
            "path": payload.get("path", ""),
            "body_preview": payload.get("body_preview", ""),
            "body_full": payload.get("body_full", payload.get("body_preview", "")),
            "vector_score": candidate.get("score", 0),
            "rerank_score": rerank_score,
            "freshness_bonus": round(fresh, 4),
            "payload_boost": round(boost, 4),
            "final_score": round(final_score, 4),
        })

    return {"results": results, "total_candidates": len(candidates)}


@app.get("/v1/rag/health")
async def rag_health():
    result = qdrant_request("GET", f"/collections/{COLLECTION}")
    if result and result.get("status") == "ok":
        points_count = result.get("result", {}).get("points_count", 0)
        return {"status": "ok", "qdrant": "ok", "points_count": points_count}
    return {"status": "ok", "qdrant": "unreachable"}


# ==========================================
# 6. /refine_status — OpenWebUI Filter badge endpoint
# Reads the daemon's refine_state.json and returns the 7-state archetype.
# ==========================================

_default_state_path = Path.home() / ".local" / "share" / "throughline" / "state" / "refine_state.json"
REFINE_STATE_FILE = Path(os.getenv("REFINE_STATE_FILE", str(_default_state_path)))

# Cache — re-read only if the file's mtime changes.
_state_cache: Dict[str, Any] = {"mtime": 0, "data": {}}


def _load_state_cached() -> Dict[str, Any]:
    """Cached state loader. Re-read only if file mtime changed."""
    try:
        mtime = REFINE_STATE_FILE.stat().st_mtime
    except FileNotFoundError:
        return {}
    if mtime == _state_cache["mtime"]:
        return _state_cache["data"]
    try:
        data = json.loads(REFINE_STATE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[rag_server] WARN: failed to read refine_state.json: {e}")
        return _state_cache["data"]
    _state_cache["mtime"] = mtime
    _state_cache["data"] = data
    return data


# 7-archetype badge mapping. Daemon last_status -> Filter badge state.
BADGE_MAP = {
    "refined":                      "REFINED",           # green — all slices succeeded
    "over_compressed":              "REFINED",           # green — succeeded but body is short
    "partial_refined":              "PARTIAL",           # yellow — some slices succeeded
    "extension_skipped":            "SUGGESTED",         # orange — judge said worth, auto-refine off
    "extension_noise_prefilter":    "SKIPPED_NOISE",     # grey — short delta, pre-filtered
    "extension_noise_judge":        "SKIPPED_NOISE",     # grey — judge said noise
    "skip_ephemeral":               "SKIPPED_EPHEMERAL", # grey — slicer flagged as one-off
    "skip_native_llm":              "SKIPPED_NATIVE",    # grey — LLM already knows this
    "skip_no_valuable_slice":       "SKIPPED_NOISE",     # grey
    "skipped":                      "SKIPPED_NOISE",     # grey
    "skip_rag_echo":                "ECHO_SKIP",         # light blue — pre-flight RAG echo intercept
    "slice_failed":                 "FAILED",            # red
    "refine_failed":                "FAILED",            # red
    "domain_route_failed":          "FAILED",            # red
    "subpath_route_failed":         "FAILED",            # red
    "force_one_failed":             "FAILED",            # red
    "retry_gaveup":                 "FAILED",            # red
}


def _map_badge_state(raw_status: str) -> str:
    """Map daemon last_status to one of the 7 badge archetypes."""
    if not raw_status:
        return "PENDING"
    return BADGE_MAP.get(raw_status, "UNKNOWN")


def _trigger_hint(conv_data: Dict[str, Any]) -> str:
    """Infer trigger mode from conv_data:

    - force_refine: user appended an explicit @refine marker
    - ext_worth:   judge said worth -> auto-refine
    - ext_noise:   judge said noise -> filtered out
    - normal:      first automatic refine
    """
    raw_status = conv_data.get("last_status", "")
    refine_count = int(conv_data.get("force_refine_count", 0))
    if raw_status == "skip_rag_echo":
        return "echo_guard"
    if "extension_noise" in raw_status:
        return "ext_noise"
    if raw_status == "extension_skipped":
        return "ext_suggested"
    if refine_count > 0:
        return f"force_refine(x{refine_count})"
    return "auto"


def _find_conv(state: Dict[str, Any], conv_id: str) -> Optional[Dict[str, Any]]:
    """Find conv by full ID or short prefix (min 8 chars).

    Exact match first, then prefix match iff exactly 1 candidate.
    """
    convs = state.get("conversations", {})
    if conv_id in convs:
        return convs[conv_id]
    if len(conv_id) < 8:
        return None
    matches = [cid for cid in convs if cid.startswith(conv_id)]
    if len(matches) == 1:
        return convs[matches[0]]
    return None


@app.get("/refine_status")
async def refine_status(conv_id: str):
    """Return daemon refine status for a conv_id.

    Input: conv_id (full UUID or short prefix, >= 8 chars)
    Output: 7-archetype badge state + slice details + trigger hint
    """
    if not conv_id or len(conv_id.strip()) < 6:
        return JSONResponse(
            {"error": "conv_id required (>=6 chars)"}, status_code=400,
        )

    state = _load_state_cached()
    if not state:
        return {
            "conv_id": conv_id,
            "badge_state": "UNKNOWN",
            "error": "refine_state.json not readable",
        }

    conv = _find_conv(state, conv_id.strip())
    if conv is None:
        # daemon hasn't processed this conv yet
        return {
            "conv_id": conv_id,
            "badge_state": "PENDING",
            "raw_status": "",
            "short_id": conv_id[:8],
            "title": "",
            "updated_at": "",
            "slices": [],
            "skipped": [],
            "trigger_hint": "",
            "refine_markers": 0,
        }

    # Resolve the full conv_id when the caller supplied only a prefix.
    full_conv_id = conv_id.strip()
    for cid in state.get("conversations", {}):
        if state["conversations"][cid] is conv:
            full_conv_id = cid
            break

    raw_status = conv.get("last_status", "")
    badge = _map_badge_state(raw_status)

    slices = []
    for sid, sl in (conv.get("slices") or {}).items():
        if not isinstance(sl, dict):
            continue
        slices.append({
            "slice_id": sid[:8],
            "title": sl.get("title", ""),
            "target": sl.get("target_leaf_path", ""),
            "triage": sl.get("triage_status", ""),
            "slice_status": sl.get("status", ""),
        })

    skipped = []
    for sk in conv.get("skipped", []):
        if isinstance(sk, dict):
            skipped.append({
                "title_hint": sk.get("title_hint", ""),
                "reason": sk.get("reason", ""),
            })

    return {
        "conv_id": full_conv_id,
        "short_id": full_conv_id[:8],
        "badge_state": badge,
        "raw_status": raw_status,
        "title": conv.get("source_chat_title", ""),
        "updated_at": conv.get("last_processed_at", ""),
        "slices": slices,
        "skipped": skipped,
        "trigger_hint": _trigger_hint(conv),
        "refine_markers": int(conv.get("force_refine_count", 0)),
        # echo-guard auxiliary fields (only populated when raw_status == skip_rag_echo).
        "echo_hint": conv.get("echo_hint", ""),
        "echo_top1_title": conv.get("echo_top1_title", ""),
        "echo_top1_score": conv.get("echo_top1_score"),
        "echo_top1_days_ago": conv.get("echo_top1_days_ago"),
    }


# ==========================================
# 7. Entry point
# ==========================================
if __name__ == "__main__":
    import socket

    import uvicorn

    host = os.getenv("RAG_HOST", "0.0.0.0")
    port = int(os.getenv("RAG_PORT", "8000"))

    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except (socket.gaierror, OSError):
        local_ip = "127.0.0.1"

    print("\n" + "=" * 55)
    print("  Throughline RAG server")
    print(f"  EMB    : http://{local_ip}:{port}/v1/embeddings")
    print(f"  RERANK : http://{local_ip}:{port}/v1/rerank")
    print(f"  RAG    : http://{local_ip}:{port}/v1/rag")
    print(f"  HEALTH : http://{local_ip}:{port}/v1/rag/health")
    print(f"  STATUS : http://{local_ip}:{port}/refine_status?conv_id=...")
    print("=" * 55 + "\n")

    uvicorn.run(app, host=host, port=port)
