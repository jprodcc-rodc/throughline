"""U21 · Vector store backend abstraction — `BaseVectorStore`.

Every backend implements the same five operations:

    ensure_collection(name, vector_size, distance)    -> None
    upsert(collection, points)                         -> int (count)
    search(collection, vector, limit, filter_=None)    -> List[SearchHit]
    delete(collection, point_ids)                      -> int (count)
    count(collection, filter_=None)                    -> int

The `rag_server`, `daemon/refine_daemon`, and `scripts/ingest_qdrant`
all talk to exactly one vector DB today (Qdrant). v0.2.0 ships this
abstraction so:

- Wizard step 3 can collect the user's choice and the daemon reads
  it from config without hard-coding a DB.
- Users who want a fully local / zero-setup path can pick Chroma or
  any of the alias backends without editing code.
- Downstream users can register their own backend with
  `register_vector_store()` and everything else keeps working.

v0.2.0 ships TWO reference implementations:

- `qdrant`   — raw HTTP against Qdrant's REST API. No client SDK
                dependency; stdlib urllib only. Preserves the exact
                behaviour the daemon / rag_server already depend on.
- `chroma`   — via chromadb's Python client. Optional dep; if
                chromadb is not importable, instantiating returns a
                stub that reports the install hint on every call
                rather than crashing at import time.

Other backends (`lancedb`, `duckdb_vss`, `sqlite_vec`, `pgvector`)
are registered as aliases routing to `qdrant` for now so the wizard
can list them without implying full support. v0.3 adds the real
impls.

Design notes:
- `SearchHit` is a plain dict shape, not a dataclass, so callers
  can round-trip payloads without serialisation ceremony.
- `filter_` is backend-specific payload — each backend documents
  its own schema. Callers targeting multiple backends must pass
  `None` and filter client-side.
- All backends MUST be idempotent on `ensure_collection` — repeated
  calls with the same parameters are no-ops.
"""
from __future__ import annotations

import abc
import json
import os
import urllib.request
import urllib.error
from typing import Any, Callable, Dict, List, Optional


# Shape of one search result. Kept as a dict alias rather than a
# dataclass because Qdrant / Chroma / etc. will stuff different extras
# into the payload; a dict is the path of least friction.
SearchHit = Dict[str, Any]


class BaseVectorStore(abc.ABC):
    name: str = ""

    @abc.abstractmethod
    def ensure_collection(self, name: str, vector_size: int,
                            distance: str = "cosine") -> None: ...

    @abc.abstractmethod
    def upsert(self, collection: str,
                points: List[Dict[str, Any]]) -> int:
        """Points are `{id, vector, payload}`. Return count upserted."""

    @abc.abstractmethod
    def search(self, collection: str, vector: List[float],
                limit: int = 10,
                filter_: Optional[Dict[str, Any]] = None
                ) -> List[SearchHit]:
        """Return hits ordered by descending similarity; each hit has
        at least `{id, score, payload}`."""

    @abc.abstractmethod
    def delete(self, collection: str, point_ids: List[Any]) -> int: ...

    @abc.abstractmethod
    def count(self, collection: str,
                filter_: Optional[Dict[str, Any]] = None) -> int: ...


# =========================================================
# Qdrant — stdlib urllib, matches the existing daemon wire calls
# =========================================================

class QdrantStore(BaseVectorStore):
    name = "qdrant"

    def __init__(self, url: Optional[str] = None,
                  timeout: float = 30.0,
                  api_key: Optional[str] = None) -> None:
        self.url = (url or os.getenv("QDRANT_URL")
                     or "http://localhost:6333").rstrip("/")
        self.timeout = timeout
        self.api_key = api_key or os.getenv("QDRANT_API_KEY", "")

    def _request(self, method: str, path: str,
                  data: Optional[Dict[str, Any]] = None
                  ) -> Optional[Dict[str, Any]]:
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(self.url + path, data=body,
                                        method=method)
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("api-key", self.api_key)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            # 404 on a collection GET is legitimate "not created yet".
            if e.code == 404:
                return None
            raise

    def ensure_collection(self, name: str, vector_size: int,
                            distance: str = "cosine") -> None:
        existing = self._request("GET", f"/collections/{name}")
        if existing is not None:
            return
        self._request("PUT", f"/collections/{name}", data={
            "vectors": {
                "size": int(vector_size),
                "distance": distance.capitalize(),  # Qdrant wants "Cosine"
            }
        })

    def upsert(self, collection: str,
                points: List[Dict[str, Any]]) -> int:
        if not points:
            return 0
        payload = {"points": [
            {
                "id": p["id"],
                "vector": p["vector"],
                "payload": p.get("payload") or {},
            }
            for p in points
        ]}
        self._request("PUT",
                       f"/collections/{collection}/points?wait=true",
                       data=payload)
        return len(points)

    def search(self, collection: str, vector: List[float],
                limit: int = 10,
                filter_: Optional[Dict[str, Any]] = None
                ) -> List[SearchHit]:
        body: Dict[str, Any] = {
            "vector": vector,
            "limit": int(limit),
            "with_payload": True,
        }
        if filter_ is not None:
            body["filter"] = filter_
        resp = self._request("POST",
                              f"/collections/{collection}/points/search",
                              data=body)
        hits = (resp or {}).get("result") or []
        return [
            {
                "id": h.get("id"),
                "score": h.get("score"),
                "payload": h.get("payload") or {},
            }
            for h in hits
        ]

    def delete(self, collection: str, point_ids: List[Any]) -> int:
        if not point_ids:
            return 0
        self._request("POST",
                       f"/collections/{collection}/points/delete?wait=true",
                       data={"points": list(point_ids)})
        return len(point_ids)

    def count(self, collection: str,
                filter_: Optional[Dict[str, Any]] = None) -> int:
        body: Dict[str, Any] = {"exact": True}
        if filter_ is not None:
            body["filter"] = filter_
        resp = self._request("POST",
                              f"/collections/{collection}/points/count",
                              data=body)
        return int(((resp or {}).get("result") or {}).get("count") or 0)


# =========================================================
# Chroma — optional dep, falls back to a stub on missing install
# =========================================================

class _ChromaUnavailable(BaseVectorStore):
    """Raised on first real call when chromadb isn't importable.

    Instantiation itself is free — we never crash at wizard time,
    only when the user actually asks the store to do work."""

    name = "chroma"
    _HINT = (
        "Chroma backend selected but `chromadb` is not installed. "
        "Run `pip install chromadb` and restart the server."
    )

    def ensure_collection(self, *a, **kw): raise RuntimeError(self._HINT)
    def upsert(self, *a, **kw):             raise RuntimeError(self._HINT)
    def search(self, *a, **kw):             raise RuntimeError(self._HINT)
    def delete(self, *a, **kw):             raise RuntimeError(self._HINT)
    def count(self, *a, **kw):              raise RuntimeError(self._HINT)


class ChromaStore(BaseVectorStore):
    """Wraps chromadb's PersistentClient. Distance metric note:
    Chroma defaults to L2; we set `hnsw:space=cosine` at collection
    creation so the contract matches Qdrant's default."""

    name = "chroma"

    def __new__(cls, *a, **kw):
        try:
            import chromadb  # noqa: F401
        except Exception:
            return _ChromaUnavailable()
        return super().__new__(cls)

    def __init__(self, path: Optional[str] = None) -> None:
        import chromadb
        self.path = path or os.getenv(
            "CHROMA_PATH",
            os.path.expanduser("~/throughline_runtime/chroma"),
        )
        os.makedirs(self.path, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self.path)

    def ensure_collection(self, name: str, vector_size: int,
                            distance: str = "cosine") -> None:
        metric = {"cosine": "cosine", "l2": "l2", "ip": "ip"}.get(
            distance.lower(), "cosine")
        self._client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": metric, "vector_size": int(vector_size)},
        )

    def _col(self, name: str):
        return self._client.get_or_create_collection(name=name)

    def upsert(self, collection: str,
                points: List[Dict[str, Any]]) -> int:
        if not points:
            return 0
        col = self._col(collection)
        col.upsert(
            ids=[str(p["id"]) for p in points],
            embeddings=[p["vector"] for p in points],
            metadatas=[p.get("payload") or {} for p in points],
        )
        return len(points)

    def search(self, collection: str, vector: List[float],
                limit: int = 10,
                filter_: Optional[Dict[str, Any]] = None
                ) -> List[SearchHit]:
        col = self._col(collection)
        result = col.query(
            query_embeddings=[vector],
            n_results=int(limit),
            where=filter_,
        )
        ids = (result.get("ids") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        hits: List[SearchHit] = []
        for i, pid in enumerate(ids):
            # Chroma returns distances (lower = closer); invert to
            # a similarity-like score so callers can always sort desc.
            d = dists[i] if i < len(dists) and dists[i] is not None else 1.0
            score = 1.0 - float(d)
            payload = metas[i] if i < len(metas) and metas[i] else {}
            hits.append({"id": pid, "score": score, "payload": payload})
        return hits

    def delete(self, collection: str, point_ids: List[Any]) -> int:
        if not point_ids:
            return 0
        col = self._col(collection)
        col.delete(ids=[str(x) for x in point_ids])
        return len(point_ids)

    def count(self, collection: str,
                filter_: Optional[Dict[str, Any]] = None) -> int:
        col = self._col(collection)
        if filter_ is None:
            return int(col.count())
        # Approximate — Chroma has no native filtered count. Query a
        # big n and len() the result.
        result = col.get(where=filter_, limit=100_000)
        return len((result.get("ids") or []))


# =========================================================
# Registry + factory
# =========================================================

_REGISTRY: Dict[str, Callable[[], BaseVectorStore]] = {
    "qdrant":  QdrantStore,
    "chroma":  ChromaStore,
}

_ALIASES: Dict[str, str] = {
    # v0.3 expansion points — currently route to Qdrant so the wizard
    # can list them, the user can pick them, and nothing crashes.
    # Real impls land in v0.3+.
    "lancedb":     "qdrant",
    "duckdb_vss":  "qdrant",
    "duckdb-vss":  "qdrant",
    "sqlite_vec":  "qdrant",
    "sqlite-vec":  "qdrant",
    "pgvector":    "qdrant",
    "none":        "qdrant",  # 'none' means "no vector store" — for
                                 # Notes-only mission. See rag_server
                                 # mission branch; stubbed here.
}


def register_vector_store(name: str,
                           ctor: Callable[[], BaseVectorStore]) -> None:
    _REGISTRY[name] = ctor


def available_vector_stores() -> List[str]:
    return sorted(set(_REGISTRY.keys()) | set(_ALIASES.keys()))


def create_vector_store(name: Optional[str] = None) -> BaseVectorStore:
    chosen = (name or os.getenv("VECTOR_STORE") or "qdrant").strip().lower()
    if chosen in _REGISTRY:
        return _REGISTRY[chosen]()
    if chosen in _ALIASES:
        return _REGISTRY[_ALIASES[chosen]]()
    known = ", ".join(available_vector_stores())
    raise ValueError(
        f"Unknown vector store: {chosen!r}. Known: {known}. "
        f"Register additional backends with register_vector_store()."
    )
