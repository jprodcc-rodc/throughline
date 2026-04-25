"""U20 · Reranker backend abstraction.

Every reranker implements `rerank(query, documents) -> list[float]`
returning one relevance score per document in input order. The
`rag_server` FastAPI app picks up a concrete reranker via
`create_reranker()`.

v0.2.0 ships three references:

- `bge-reranker-v2-m3` — local cross-encoder via transformers.
  Default for Full-privacy / Local-only missions.
- `cohere`             — Cohere rerank API (v3.5 rerank-english-v3.0).
  Reference cloud alternate.
- `skip`               — no-op; preserves the pre-rerank score order.
  Valid pick for users who want pure vector search or who run on
  CPU-only boxes where cross-encoder inference is too slow.

Other providers (Voyage, Jina, bge-reranker-v2-gemma, etc.) are
NOT implemented in this commit. Register them via
`register_reranker()`.

Design notes:
- Torch + transformers imported LAZILY inside `BgeRerankerV2M3.ensure_loaded()`
  so `create_reranker("cohere")` / `create_reranker("skip")` don't
  pay the model-load tax.
- Cohere HTTP is stdlib urllib — no additional deps, no SDK pinning.
- Scores from different backends are NOT cross-comparable; the
  rag_server uses rerank scores only to sort within a single result
  set, never as absolute relevance signals.
"""
from __future__ import annotations

import abc
import json
import os
import urllib.request
from typing import Callable, Dict, List, Optional


class BaseReranker(abc.ABC):
    """Minimal reranker contract."""

    name: str = ""

    @abc.abstractmethod
    def rerank(self, query: str, documents: List[str]) -> List[float]:
        """Return one score per document. Higher = more relevant.

        Empty documents list → empty scores list. Must never raise
        on empty input.
        """

    def ensure_loaded(self) -> None:
        """Optional eager-init hook for heavy startups."""


# =========================================================
# SkipReranker — identity pass-through
# =========================================================

class SkipReranker(BaseReranker):
    """No-op reranker.

    Returns a monotonically-decreasing score so the original input
    ordering is preserved. Picking this is the right call when:
    - you're CPU-bound and can't afford the cross-encoder,
    - your embeddings are already good enough for your corpus size,
    - you're iterating on retrieval and want to A/B with and without
      a reranker in the loop.
    """

    name = "skip"

    def rerank(self, query: str, documents: List[str]) -> List[float]:
        n = len(documents)
        # Descending floats so the original order survives a sort.
        return [float(n - i) for i in range(n)]


# =========================================================
# BgeRerankerV2M3 — local cross-encoder (the v0.1 default)
# =========================================================

class BgeRerankerV2M3(BaseReranker):
    """Wraps the existing rag_server cross-encoder path."""

    name = "bge-reranker-v2-m3"

    def __init__(self, model_path: Optional[str] = None,
                  device: Optional[str] = None,
                  max_length: int = 512,
                  batch_size: int = 8) -> None:
        self.model_path = model_path or os.getenv(
            "RERANK_MODEL", "BAAI/bge-reranker-v2-m3")
        # RAG_DEVICE is the legacy rag_server env var; honour it so
        # existing deployments keep pinning cpu / mps / cuda.
        self.device_override = device or os.getenv("RAG_DEVICE") or None
        self.max_length = max_length
        self.batch_size = batch_size
        self._tokenizer = None
        self._model = None
        self._torch_device = None

    def ensure_loaded(self) -> None:
        if self._model is not None:
            return
        import torch
        from transformers import (
            AutoModelForSequenceClassification, AutoTokenizer,
        )

        def _pick_device():
            if self.device_override:
                return torch.device(self.device_override)
            if torch.backends.mps.is_available():
                return torch.device("mps")
            if torch.cuda.is_available():
                return torch.device("cuda")
            return torch.device("cpu")

        self._torch_device = _pick_device()
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        m = AutoModelForSequenceClassification.from_pretrained(
            self.model_path, torch_dtype=__import__("torch").float16,
        )
        self._model = m.to(self._torch_device).eval()

    def rerank(self, query: str, documents: List[str]) -> List[float]:
        if not documents:
            return []
        self.ensure_loaded()
        import torch
        scores: List[float] = []
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            pairs = [[query, d] for d in batch]
            inputs = self._tokenizer(
                pairs, padding=True, truncation=True,
                max_length=self.max_length, return_tensors="pt",
            ).to(self._torch_device)
            with torch.no_grad():
                logits = self._model(**inputs, return_dict=True).logits.view(-1)
            scores.extend(logits.cpu().tolist())
        return scores


# =========================================================
# CohereReranker — reference cloud alternate
# =========================================================

class CohereReranker(BaseReranker):
    """Calls Cohere's /rerank endpoint.

    API docs: https://docs.cohere.com/reference/rerank
    Default model: `rerank-english-v3.0`. Users pick multilingual via
    `COHERE_RERANK_MODEL=rerank-multilingual-v3.0`. Requires the
    `COHERE_API_KEY` env var; without it `rerank()` returns a
    no-rerank (descending-order) fallback so the RAG server degrades
    gracefully rather than erroring.
    """

    name = "cohere"

    def __init__(self, model: Optional[str] = None,
                  base_url: Optional[str] = None,
                  api_key: Optional[str] = None) -> None:
        self.model = model or os.getenv(
            "COHERE_RERANK_MODEL", "rerank-english-v3.0")
        self.base_url = (base_url or os.getenv("COHERE_BASE_URL")
                          or "https://api.cohere.com/v2").rstrip("/")
        self.api_key = api_key or os.getenv("COHERE_API_KEY", "")

    def rerank(self, query: str, documents: List[str]) -> List[float]:
        if not documents:
            return []
        if not self.api_key:
            # Degrade gracefully: caller still gets a ranked list.
            return SkipReranker().rerank(query, documents)
        url = f"{self.base_url}/rerank"
        body = json.dumps({
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": len(documents),
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        # Cohere returns {"results": [{"index": i, "relevance_score": x}, ...]}
        # possibly re-ordered; we must re-align to input order.
        n = len(documents)
        out = [0.0] * n
        for row in payload.get("results") or []:
            idx = row.get("index")
            score = row.get("relevance_score")
            if isinstance(idx, int) and 0 <= idx < n and score is not None:
                try:
                    out[idx] = float(score)
                except (TypeError, ValueError):
                    continue
        return out


# =========================================================
# VoyageReranker — Voyage AI's /v1/rerank endpoint
# =========================================================

class VoyageReranker(BaseReranker):
    """Calls Voyage AI's /v1/rerank endpoint.

    API docs: https://docs.voyageai.com/docs/reranker
    Default model: `rerank-2-lite`. Cheaper / faster than rerank-2;
    upgrade via `VOYAGE_RERANK_MODEL=rerank-2`. Requires
    `VOYAGE_API_KEY`; without it falls through to SkipReranker so
    callers degrade gracefully.

    Response shape mirrors Cohere's: a list of `{index, relevance_score}`
    rows that we re-align to the input order.
    """

    name = "voyage"

    def __init__(self, model: Optional[str] = None,
                  base_url: Optional[str] = None,
                  api_key: Optional[str] = None) -> None:
        self.model = model or os.getenv(
            "VOYAGE_RERANK_MODEL", "rerank-2-lite")
        self.base_url = (base_url or os.getenv("VOYAGE_BASE_URL")
                          or "https://api.voyageai.com/v1").rstrip("/")
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY", "")

    def rerank(self, query: str, documents: List[str]) -> List[float]:
        if not documents:
            return []
        if not self.api_key:
            return SkipReranker().rerank(query, documents)
        url = f"{self.base_url}/rerank"
        body = json.dumps({
            "model":     self.model,
            "query":     query,
            "documents": documents,
            "top_k":     len(documents),
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        # Voyage returns {"data": [{"index": i, "relevance_score": x}, ...]}
        n = len(documents)
        out = [0.0] * n
        for row in payload.get("data") or []:
            idx = row.get("index")
            score = row.get("relevance_score")
            if isinstance(idx, int) and 0 <= idx < n and score is not None:
                try:
                    out[idx] = float(score)
                except (TypeError, ValueError):
                    continue
        return out


# =========================================================
# JinaReranker — Jina AI's /v1/rerank endpoint
# =========================================================

class JinaReranker(BaseReranker):
    """Calls Jina AI's /v1/rerank endpoint.

    API docs: https://jina.ai/reranker
    Default model: `jina-reranker-v2-base-multilingual` — handles
    100+ languages without the English-only limitation Cohere v3.0
    has by default. Override via `JINA_RERANK_MODEL=...`. Requires
    `JINA_API_KEY`; falls through to SkipReranker without one.

    Response shape: `{"results": [{"index": i, "relevance_score": x}]}`.
    `return_documents=false` because we already have the input list
    and don't need Jina to echo it back.
    """

    name = "jina"

    def __init__(self, model: Optional[str] = None,
                  base_url: Optional[str] = None,
                  api_key: Optional[str] = None) -> None:
        self.model = model or os.getenv(
            "JINA_RERANK_MODEL", "jina-reranker-v2-base-multilingual")
        self.base_url = (base_url or os.getenv("JINA_BASE_URL")
                          or "https://api.jina.ai/v1").rstrip("/")
        self.api_key = api_key or os.getenv("JINA_API_KEY", "")

    def rerank(self, query: str, documents: List[str]) -> List[float]:
        if not documents:
            return []
        if not self.api_key:
            return SkipReranker().rerank(query, documents)
        url = f"{self.base_url}/rerank"
        body = json.dumps({
            "model":            self.model,
            "query":            query,
            "documents":        documents,
            "top_n":            len(documents),
            "return_documents": False,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        # Jina returns {"results": [{"index": i, "relevance_score": x}, ...]}
        n = len(documents)
        out = [0.0] * n
        for row in payload.get("results") or []:
            idx = row.get("index")
            score = row.get("relevance_score")
            if isinstance(idx, int) and 0 <= idx < n and score is not None:
                try:
                    out[idx] = float(score)
                except (TypeError, ValueError):
                    continue
        return out


# =========================================================
# Registry + factory
# =========================================================

_REGISTRY: Dict[str, Callable[[], BaseReranker]] = {
    "bge-reranker-v2-m3": BgeRerankerV2M3,
    "cohere":             CohereReranker,
    "voyage":             VoyageReranker,
    "jina":               JinaReranker,
    "skip":               SkipReranker,
}

_ALIASES: Dict[str, str] = {
    "bge":                  "bge-reranker-v2-m3",
    "bge-reranker":         "bge-reranker-v2-m3",
    "bge-reranker-v2-gemma": "bge-reranker-v2-m3",  # TODO(v0.3): dedicated gemma impl
    "none":                 "skip",
}


def register_reranker(name: str, ctor: Callable[[], BaseReranker]) -> None:
    _REGISTRY[name] = ctor


def available_rerankers() -> List[str]:
    return sorted(set(_REGISTRY.keys()) | set(_ALIASES.keys()))


def create_reranker(name: Optional[str] = None) -> BaseReranker:
    """Resolve `name` (or env var `RERANKER`, or default
    `bge-reranker-v2-m3`) to a concrete reranker.

    Unknown names raise ValueError with the known list, same as
    `create_embedder` — silent fallback would change search quality
    in ways the user didn't opt into.
    """
    chosen = (name or os.getenv("RERANKER") or "bge-reranker-v2-m3").strip().lower()
    if chosen in _REGISTRY:
        return _REGISTRY[chosen]()
    if chosen in _ALIASES:
        return _REGISTRY[_ALIASES[chosen]]()
    known = ", ".join(available_rerankers())
    raise ValueError(
        f"Unknown reranker: {chosen!r}. Known: {known}. "
        f"Register additional backends with register_reranker()."
    )
