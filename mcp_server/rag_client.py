"""HTTP client to localhost rag_server's /v1/rag endpoint.

stdlib urllib only — matches throughline's "no extra deps" policy
(daemon and rag_server itself use urllib too, see e.g.
`daemon/refine_daemon.py`'s embedder/reranker calls).

The rag_server contract is:

POST /v1/rag
  Request:  { query: str,
              top_k: int = 10,
              candidate_k: int = 30,
              knowledge_identity: str | None,
              freshness_weight: float = 1.0,
              pp_boost: float | None,
              ...others (collection, group_boost, group_key) }
  Response: { results: [ { title, knowledge_identity, tags, date,
                           path, body_preview, body_full,
                           vector_score, rerank_score,
                           freshness_bonus, payload_boost,
                           final_score } ],
              total_candidates: int }
  On error: { results: [], error: str }

This module raises typed exceptions on transport / decode errors;
the tool function catches them and returns the documented MCP
error shape to the host LLM. Keeps tool code clean.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Optional


DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 10


class RAGClientError(Exception):
    """Base exception for rag_client failures. Subclasses describe
    *where* the failure happened (transport / decode / server-side)
    so the caller can build an appropriate user-facing message.
    """


class RAGServerUnreachable(RAGClientError):
    """Connection refused / timeout / DNS error — rag_server is
    likely not running on localhost:8000. Hint user to start it."""


class RAGServerError(RAGClientError):
    """rag_server returned non-200 OR a 200 with `error` field set."""


class RAGResponseMalformed(RAGClientError):
    """Body wasn't valid JSON, or didn't have the expected shape."""


def get_base_url() -> str:
    """Resolve the rag_server URL. Override via env var so users
    running on non-default ports / hosts can point MCP at theirs."""
    return os.environ.get("THROUGHLINE_RAG_URL", DEFAULT_BASE_URL).rstrip("/")


def embed_batch(
    texts: list[str],
    base_url: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> list[list[float]]:
    """Call rag_server `/v1/embeddings` for a batch of strings.
    Returns one embedding vector per input string in the same order.

    Used by the topic-clustering experiment harness — not on the
    MCP request hot path (recall_memory delegates the embed step
    server-side via /v1/rag).

    Raises:
        RAGServerUnreachable: rag_server isn't running.
        RAGServerError: rag_server returned a non-200.
        RAGResponseMalformed: response shape unexpected.
    """
    if not texts:
        return []

    url = (base_url or get_base_url()) + "/v1/embeddings"
    payload = {"input": texts, "model": "bge-m3"}
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw = resp.read()
    except urllib.error.URLError as exc:
        raise RAGServerUnreachable(
            f"rag_server unreachable at {url}: {exc.reason}"
        ) from exc
    except (TimeoutError, OSError) as exc:
        raise RAGServerUnreachable(
            f"rag_server timeout at {url}: {exc}"
        ) from exc
    if status != 200:
        raise RAGServerError(f"rag_server returned HTTP {status}")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RAGResponseMalformed(
            f"embeddings response not JSON: {exc}"
        ) from exc
    # OpenAI-compatible shape: {"data": [{"embedding": [...]}, ...]}
    items = data.get("data") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise RAGResponseMalformed(
            "embeddings response missing `data` list"
        )
    out: list[list[float]] = []
    for item in items:
        vec = item.get("embedding") if isinstance(item, dict) else None
        if not isinstance(vec, list):
            raise RAGResponseMalformed(
                "embeddings response missing `embedding` per item"
            )
        out.append([float(x) for x in vec])
    if len(out) != len(texts):
        raise RAGResponseMalformed(
            f"embeddings response length mismatch: "
            f"got {len(out)}, expected {len(texts)}"
        )
    return out


def search(
    query: str,
    limit: int = 5,
    knowledge_identity: Optional[str] = None,
    pp_boost: Optional[float] = None,
    base_url: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Call rag_server `/v1/rag`. Returns the parsed response dict
    on success.

    Raises:
        RAGServerUnreachable: rag_server isn't running / unreachable.
        RAGServerError: rag_server returned a non-200 OR a 200 with
            `error` field. Message includes server-side detail.
        RAGResponseMalformed: response body isn't a JSON object with
            the expected `results` field.
    """
    if not query or not query.strip():
        raise ValueError("query must be non-empty")

    payload: dict[str, Any] = {
        "query": query,
        "top_k": int(limit),
    }
    if knowledge_identity is not None:
        payload["knowledge_identity"] = knowledge_identity
    if pp_boost is not None:
        payload["pp_boost"] = float(pp_boost)

    url = (base_url or get_base_url()) + "/v1/rag"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw = resp.read()
    except urllib.error.URLError as exc:
        raise RAGServerUnreachable(
            f"rag_server unreachable at {url}: {exc.reason}. "
            f"Is `python rag_server/rag_server.py` running?"
        ) from exc
    except (TimeoutError, OSError) as exc:
        raise RAGServerUnreachable(
            f"rag_server timeout / OS error at {url}: {exc}"
        ) from exc

    if status != 200:
        raise RAGServerError(f"rag_server returned HTTP {status}")

    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RAGResponseMalformed(
            f"rag_server response was not JSON: {exc}"
        ) from exc

    if not isinstance(data, dict) or "results" not in data:
        raise RAGResponseMalformed(
            "rag_server response missing `results` field"
        )

    if data.get("error"):
        raise RAGServerError(f"rag_server error: {data['error']}")

    return data
