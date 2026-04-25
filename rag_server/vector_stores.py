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

v0.2.x ships SIX real backend implementations:

- `qdrant`     — raw HTTP against Qdrant's REST API. No client SDK
                  dependency; stdlib urllib only. Preserves the exact
                  behaviour the daemon / rag_server already depend on.
- `chroma`     — via chromadb's Python client. Optional dep; if
                  chromadb is not importable, instantiating returns a
                  stub that reports the install hint on every call
                  rather than crashing at import time.
- `lancedb`    — embedded, file-backed (Arrow / Lance format), zero-
                  server. `pip install lancedb` opt-in. Closes #6.
- `sqlite_vec` — fully embedded, sqlite3-stdlib + sqlite_vec extension.
                  Lightest credible footprint. Closes #11.
- `duckdb_vss` — embedded analytical DB + the VSS extension for vector
                  search. Picks for users already on a DuckDB stack.
                  Closes #10.
- `pgvector`   — server-based Postgres + pgvector extension. Picks for
                  users on an existing Postgres ops stack. Closes #9.

The four backends originally aliased to `qdrant` (lancedb /
duckdb_vss / sqlite_vec / pgvector) all shipped as first-class real
implementations during v0.2.x. Only spelling aliases remain (e.g.
`sqlite-vec` → `sqlite_vec`).

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
# LanceDB — optional dep, stub on missing install
# =========================================================

class _LanceDBUnavailable(BaseVectorStore):
    """Stub returned at instantiation when lancedb isn't importable.

    Matches the Chroma stub pattern so the wizard can list LanceDB
    as a choice and nothing crashes at import time. Real calls hit a
    readable RuntimeError with the install hint."""

    name = "lancedb"
    _HINT = (
        "LanceDB backend selected but `lancedb` is not installed. "
        "Run `pip install lancedb pyarrow` and restart the server. "
        "Alternatively, `pip install throughline[lancedb]` once the "
        "extra is published."
    )

    def ensure_collection(self, *a, **kw): raise RuntimeError(self._HINT)
    def upsert(self, *a, **kw):             raise RuntimeError(self._HINT)
    def search(self, *a, **kw):             raise RuntimeError(self._HINT)
    def delete(self, *a, **kw):             raise RuntimeError(self._HINT)
    def count(self, *a, **kw):              raise RuntimeError(self._HINT)


class LanceDBStore(BaseVectorStore):
    """Embedded, file-based vector store — zero-server alternative to
    Qdrant. Persists under `LANCEDB_PATH` (default
    `~/throughline_runtime/lancedb`).

    Collections are LanceDB tables. Payload is stored as a JSON-
    serialized string column so a single schema fits every pack
    without per-collection gymnastics.

    Distance is set via table options; we use cosine to match
    QdrantStore's default contract. IDs are string-typed so the
    daemon's md5-derived slice_ids round-trip unchanged.
    """

    name = "lancedb"

    def __new__(cls, *a, **kw):
        try:
            import lancedb  # noqa: F401
            import pyarrow  # noqa: F401
        except Exception:
            return _LanceDBUnavailable()
        return super().__new__(cls)

    def __init__(self, path: Optional[str] = None) -> None:
        import lancedb
        self.path = path or os.getenv(
            "LANCEDB_PATH",
            os.path.expanduser("~/throughline_runtime/lancedb"),
        )
        os.makedirs(self.path, exist_ok=True)
        self._db = lancedb.connect(self.path)
        # Cache vector_size per collection so search knows the shape
        # even when the table is created empty and populated later.
        self._vector_size: Dict[str, int] = {}

    def _schema(self, vector_size: int):
        import pyarrow as pa
        return pa.schema([
            pa.field("id", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), vector_size)),
            # Payload as JSON string — simplest path to schema-free
            # per-pack payloads without repeatedly rewriting the
            # Arrow schema.
            pa.field("payload", pa.string()),
        ])

    def ensure_collection(self, name: str, vector_size: int,
                            distance: str = "cosine") -> None:
        self._vector_size[name] = int(vector_size)
        existing = set(self._db.table_names())
        if name in existing:
            return
        # Create an empty table with the schema. LanceDB supports
        # creating from schema directly without a sample row.
        self._db.create_table(name, schema=self._schema(int(vector_size)))

    def _table(self, collection: str):
        if collection in self._db.table_names():
            return self._db.open_table(collection)
        # Auto-create with a best-guess vector size; the daemon
        # normally calls ensure_collection first, but fall back for
        # direct upserts by tools that skipped the explicit create.
        vs = self._vector_size.get(collection, 1024)
        return self._db.create_table(
            collection, schema=self._schema(vs))

    def upsert(self, collection: str,
                points: List[Dict[str, Any]]) -> int:
        if not points:
            return 0
        import json as _json
        table = self._table(collection)
        rows = [
            {
                "id": str(p["id"]),
                "vector": p["vector"],
                "payload": _json.dumps(p.get("payload") or {},
                                        ensure_ascii=False),
            }
            for p in points
        ]
        # LanceDB `merge_insert` upserts by primary key. Older
        # versions lack merge_insert; add-then-dedup is the
        # portable fallback.
        ids = [r["id"] for r in rows]
        try:
            table.delete(f"id IN ({','.join(repr(i) for i in ids)})")
        except Exception:
            pass
        table.add(rows)
        return len(rows)

    def search(self, collection: str, vector: List[float],
                limit: int = 10,
                filter_: Optional[Dict[str, Any]] = None
                ) -> List[SearchHit]:
        import json as _json
        table = self._table(collection)
        query = table.search(vector, vector_column_name="vector") \
                      .limit(int(limit))
        # LanceDB filters use SQL-WHERE syntax on the payload column.
        # We don't index payload internals (it's a JSON string), so
        # server-side filtering would require column-per-field
        # flattening. For parity with Qdrant's knowledge_identity
        # filter we pull rows client-side and filter in Python —
        # OK for the RAG query volume (~10s of candidates).
        rows = query.to_list()
        hits: List[SearchHit] = []
        for row in rows:
            payload_raw = row.get("payload") or "{}"
            try:
                payload = _json.loads(payload_raw)
            except _json.JSONDecodeError:
                payload = {}
            if filter_:
                # Qdrant-shape `filter_` like
                # {"must": [{"key": "knowledge_identity", "match":
                #   {"value": "universal"}}]}.
                # Simple interpretation: every `must` clause must
                # match exact payload value.
                want = {}
                for clause in (filter_.get("must") or []):
                    k = clause.get("key")
                    v = clause.get("match", {}).get("value")
                    if k is not None:
                        want[k] = v
                skip = False
                for k, v in want.items():
                    if payload.get(k) != v:
                        skip = True
                        break
                if skip:
                    continue
            # LanceDB returns `_distance` (L2-adjacent). Convert to
            # a higher-is-better score so downstream code can sort
            # descending like it does for Qdrant / Chroma.
            dist = row.get("_distance", 1.0)
            score = 1.0 - float(dist)
            hits.append({
                "id": row.get("id"),
                "score": score,
                "payload": payload,
            })
        return hits

    def delete(self, collection: str, point_ids: List[Any]) -> int:
        if not point_ids:
            return 0
        table = self._table(collection)
        ids_sql = ",".join(repr(str(pid)) for pid in point_ids)
        table.delete(f"id IN ({ids_sql})")
        return len(point_ids)

    def count(self, collection: str,
                filter_: Optional[Dict[str, Any]] = None) -> int:
        table = self._table(collection)
        if filter_ is None:
            return int(table.count_rows())
        # Filtered count: same client-side pattern as search().
        # LanceDB search without a vector argument isn't supported;
        # we pull all rows and count matches. Cheap for small tables,
        # slow at 1M+ — acceptable tradeoff for v0.2.x.
        import json as _json
        matched = 0
        for row in table.to_pandas().to_dict("records"):
            payload_raw = row.get("payload") or "{}"
            try:
                payload = _json.loads(payload_raw)
            except _json.JSONDecodeError:
                continue
            ok = True
            for clause in (filter_.get("must") or []):
                k = clause.get("key")
                v = clause.get("match", {}).get("value")
                if k is not None and payload.get(k) != v:
                    ok = False
                    break
            if ok:
                matched += 1
        return matched


# =========================================================
# SqliteVecStore — embedded, single-file, near-zero deps
# =========================================================

class _SqliteVecUnavailable(BaseVectorStore):
    """Stub returned when the `sqlite_vec` extension package isn't
    installed. Same pattern as Chroma / LanceDB stubs: instantiation
    succeeds, real calls hit a readable RuntimeError."""

    name = "sqlite_vec"
    _HINT = (
        "sqlite-vec backend selected but `sqlite_vec` is not installed. "
        "Run `pip install sqlite-vec` and restart the server. "
        "Alternatively, `pip install throughline[sqlite-vec]` once the "
        "extra is published."
    )

    def ensure_collection(self, *a, **kw): raise RuntimeError(self._HINT)
    def upsert(self, *a, **kw):             raise RuntimeError(self._HINT)
    def search(self, *a, **kw):             raise RuntimeError(self._HINT)
    def delete(self, *a, **kw):             raise RuntimeError(self._HINT)
    def count(self, *a, **kw):              raise RuntimeError(self._HINT)


class SqliteVecStore(BaseVectorStore):
    """Lightest-weight credible vector backend — a single SQLite file
    + the `sqlite-vec` loadable extension. Zero-server, zero Python-
    level deps beyond `sqlite_vec` itself (sqlite3 is stdlib).

    Schema per collection: TWO tables.
      - `<name>_vec`  : vec0 virtual table, holds the embeddings.
      - `<name>_meta` : (id TEXT PK, payload TEXT JSON, rowid INTEGER)
                         maps vec0's integer rowid back to the
                         daemon's string ids + JSON payload.

    The two-table split is forced by vec0's API: it tracks vectors
    by integer rowid only, and it doesn't store ancillary columns.
    Any caller that wants to retrieve by string id or apply payload
    filters has to maintain a parallel mapping. We do.
    """

    name = "sqlite_vec"

    def __new__(cls, *a, **kw):
        try:
            import sqlite_vec  # noqa: F401
        except Exception:
            return _SqliteVecUnavailable()
        return super().__new__(cls)

    def __init__(self, path: Optional[str] = None) -> None:
        import sqlite3
        import sqlite_vec
        self.path = path or os.getenv(
            "SQLITE_VEC_PATH",
            os.path.expanduser("~/throughline_runtime/sqlite-vec.db"),
        )
        # Make sure the parent dir exists (sqlite3 won't create it).
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.enable_load_extension(True)
        sqlite_vec.load(self._conn)
        self._conn.enable_load_extension(False)
        self._vector_size: Dict[str, int] = {}

    # --- helpers ---------------------------------------------------
    def _vec_table(self, collection: str) -> str:
        return f"{collection}_vec"

    def _meta_table(self, collection: str) -> str:
        return f"{collection}_meta"

    def _vec_blob(self, vector: List[float]) -> bytes:
        """Pack a Python list of floats into the byte format vec0
        expects (little-endian float32). Stdlib `struct` keeps us
        dep-free."""
        import struct as _struct
        return _struct.pack(f"{len(vector)}f", *(float(x) for x in vector))

    # --- ABC methods -----------------------------------------------
    def ensure_collection(self, name: str, vector_size: int,
                            distance: str = "cosine") -> None:
        # vec0's CREATE-VIRTUAL-TABLE syntax: vector column declared
        # as `vec_type[N]` where vec_type is float / int8 / bit. We
        # use float for fidelity-first; quantization is a v0.3
        # optimisation.
        self._vector_size[name] = int(vector_size)
        self._conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS {self._vec_table(name)} "
            f"USING vec0(vector float[{int(vector_size)}])"
        )
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS {self._meta_table(name)} ("
            f"  id TEXT PRIMARY KEY, payload TEXT, rowid INTEGER)"
        )
        self._conn.commit()

    def upsert(self, collection: str,
                points: List[Dict[str, Any]]) -> int:
        if not points:
            return 0
        import json as _json
        vec_table = self._vec_table(collection)
        meta_table = self._meta_table(collection)
        cur = self._conn.cursor()
        n = 0
        for p in points:
            pid = str(p["id"])
            payload = _json.dumps(p.get("payload") or {},
                                    ensure_ascii=False)
            blob = self._vec_blob(p["vector"])
            # Look up existing rowid for this string id (if any).
            existing = cur.execute(
                f"SELECT rowid FROM {meta_table} WHERE id = ?", (pid,)
            ).fetchone()
            if existing is not None:
                rowid = existing[0]
                cur.execute(
                    f"UPDATE {vec_table} SET vector = ? WHERE rowid = ?",
                    (blob, rowid))
                cur.execute(
                    f"UPDATE {meta_table} SET payload = ? WHERE id = ?",
                    (payload, pid))
            else:
                cur.execute(
                    f"INSERT INTO {vec_table}(vector) VALUES (?)", (blob,))
                rowid = cur.lastrowid
                cur.execute(
                    f"INSERT INTO {meta_table}(id, payload, rowid) "
                    f"VALUES (?, ?, ?)", (pid, payload, rowid))
            n += 1
        self._conn.commit()
        return n

    def search(self, collection: str, vector: List[float],
                limit: int = 10,
                filter_: Optional[Dict[str, Any]] = None
                ) -> List[SearchHit]:
        import json as _json
        vec_table = self._vec_table(collection)
        meta_table = self._meta_table(collection)
        # vec0 MATCH syntax: `WHERE vector MATCH ? AND k = ?`.
        # `distance` is automatically populated for the result.
        # We use `LIMIT ?` instead of vec0's `k = ?` parameter for
        # broader vec0 version compat.
        blob = self._vec_blob(vector)
        rows = self._conn.execute(
            f"SELECT v.rowid, v.distance, m.id, m.payload "
            f"FROM {vec_table} v JOIN {meta_table} m ON m.rowid = v.rowid "
            f"WHERE v.vector MATCH ? "
            f"ORDER BY v.distance LIMIT ?",
            (blob, int(limit)),
        ).fetchall()
        hits: List[SearchHit] = []
        for _rowid, dist, sid, payload_raw in rows:
            try:
                payload = _json.loads(payload_raw or "{}")
            except _json.JSONDecodeError:
                payload = {}
            if filter_:
                # Same Qdrant-shape `must` clause translation as
                # LanceDBStore — applied client-side.
                want = {}
                for clause in (filter_.get("must") or []):
                    k = clause.get("key")
                    v = clause.get("match", {}).get("value")
                    if k is not None:
                        want[k] = v
                skip = False
                for k, v in want.items():
                    if payload.get(k) != v:
                        skip = True
                        break
                if skip:
                    continue
            # Convert distance → score (higher-is-better) so callers
            # can sort descending uniformly across backends.
            score = 1.0 - float(dist)
            hits.append({"id": sid, "score": score, "payload": payload})
        return hits

    def delete(self, collection: str, point_ids: List[Any]) -> int:
        if not point_ids:
            return 0
        vec_table = self._vec_table(collection)
        meta_table = self._meta_table(collection)
        cur = self._conn.cursor()
        deleted = 0
        for pid in point_ids:
            sid = str(pid)
            row = cur.execute(
                f"SELECT rowid FROM {meta_table} WHERE id = ?", (sid,)
            ).fetchone()
            if row is None:
                continue
            rowid = row[0]
            cur.execute(
                f"DELETE FROM {vec_table} WHERE rowid = ?", (rowid,))
            cur.execute(
                f"DELETE FROM {meta_table} WHERE id = ?", (sid,))
            deleted += 1
        self._conn.commit()
        return deleted

    def count(self, collection: str,
                filter_: Optional[Dict[str, Any]] = None) -> int:
        meta_table = self._meta_table(collection)
        if filter_ is None:
            row = self._conn.execute(
                f"SELECT COUNT(*) FROM {meta_table}").fetchone()
            return int(row[0] if row else 0)
        # Filtered count: pull payloads + count matches client-side.
        # Same tradeoff as LanceDB — fine at RAG cardinality, not
        # for analytical scans.
        import json as _json
        matched = 0
        for (payload_raw,) in self._conn.execute(
                f"SELECT payload FROM {meta_table}"):
            try:
                payload = _json.loads(payload_raw or "{}")
            except _json.JSONDecodeError:
                continue
            ok = True
            for clause in (filter_.get("must") or []):
                k = clause.get("key")
                v = clause.get("match", {}).get("value")
                if k is not None and payload.get(k) != v:
                    ok = False
                    break
            if ok:
                matched += 1
        return matched


# =========================================================
# DuckDBVSSStore — embedded analytical SQL + vector search
# =========================================================

class _DuckDBVSSUnavailable(BaseVectorStore):
    """Stub returned when `duckdb` isn't installed."""

    name = "duckdb_vss"
    _HINT = (
        "DuckDB-VSS backend selected but `duckdb` is not installed. "
        "Run `pip install duckdb` (the VSS extension is auto-loaded "
        "from duckdb's extension repo on first use). Alternatively, "
        "`pip install throughline[duckdb-vss]` once published."
    )

    def ensure_collection(self, *a, **kw): raise RuntimeError(self._HINT)
    def upsert(self, *a, **kw):             raise RuntimeError(self._HINT)
    def search(self, *a, **kw):             raise RuntimeError(self._HINT)
    def delete(self, *a, **kw):             raise RuntimeError(self._HINT)
    def count(self, *a, **kw):              raise RuntimeError(self._HINT)


class DuckDBVSSStore(BaseVectorStore):
    """Embedded analytical SQL + vector search — single .duckdb file,
    zero-server. Best fit when the user already runs DuckDB for
    analytics and wants vectors in the same database.

    Schema per collection: a single table.
        id      VARCHAR PRIMARY KEY
        vector  FLOAT[<dim>]
        payload JSON

    The VSS extension is loaded on connect via `INSTALL vss; LOAD vss;`
    Distance computed via `array_distance()` (L2). Upsert uses
    `INSERT ... ON CONFLICT (id) DO UPDATE` for proper update
    semantics (DuckDB supports this since v0.10).
    """

    name = "duckdb_vss"

    def __new__(cls, *a, **kw):
        try:
            import duckdb  # noqa: F401
        except Exception:
            return _DuckDBVSSUnavailable()
        return super().__new__(cls)

    def __init__(self, path: Optional[str] = None) -> None:
        import duckdb
        self.path = path or os.getenv(
            "DUCKDB_VSS_PATH",
            os.path.expanduser("~/throughline_runtime/throughline.duckdb"),
        )
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self._conn = duckdb.connect(self.path)
        # VSS extension is community-maintained; INSTALL fetches if
        # needed, LOAD activates it. Failures here are surfaced
        # immediately rather than on first MATCH.
        try:
            self._conn.execute("INSTALL vss")
        except Exception:
            # Some sandboxed environments forbid network fetches;
            # the user can pre-install the extension manually.
            pass
        self._conn.execute("LOAD vss")
        self._vector_size: Dict[str, int] = {}

    # --- ABC methods -----------------------------------------------
    def ensure_collection(self, name: str, vector_size: int,
                            distance: str = "cosine") -> None:
        self._vector_size[name] = int(vector_size)
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS {name} ("
            f"  id      VARCHAR PRIMARY KEY,"
            f"  vector  FLOAT[{int(vector_size)}],"
            f"  payload JSON"
            f")"
        )

    def upsert(self, collection: str,
                points: List[Dict[str, Any]]) -> int:
        if not points:
            return 0
        import json as _json
        n = 0
        for p in points:
            pid = str(p["id"])
            vec = list(p["vector"])
            payload = _json.dumps(p.get("payload") or {},
                                    ensure_ascii=False)
            # ON CONFLICT works on PRIMARY KEY columns in DuckDB.
            self._conn.execute(
                f"INSERT INTO {collection}(id, vector, payload) "
                f"VALUES (?, ?, ?) "
                f"ON CONFLICT (id) DO UPDATE SET "
                f"  vector = excluded.vector, "
                f"  payload = excluded.payload",
                [pid, vec, payload],
            )
            n += 1
        return n

    def search(self, collection: str, vector: List[float],
                limit: int = 10,
                filter_: Optional[Dict[str, Any]] = None
                ) -> List[SearchHit]:
        import json as _json
        rows = self._conn.execute(
            f"SELECT id, array_distance(vector, ?::FLOAT[]) AS dist, payload "
            f"FROM {collection} "
            f"ORDER BY dist LIMIT ?",
            [list(vector), int(limit)],
        ).fetchall()
        hits: List[SearchHit] = []
        for sid, dist, payload_raw in rows:
            try:
                payload = _json.loads(payload_raw or "{}")
            except (_json.JSONDecodeError, TypeError):
                payload = payload_raw if isinstance(payload_raw, dict) else {}
            if filter_:
                want = {}
                for clause in (filter_.get("must") or []):
                    k = clause.get("key")
                    v = clause.get("match", {}).get("value")
                    if k is not None:
                        want[k] = v
                skip = False
                for k, v in want.items():
                    if payload.get(k) != v:
                        skip = True
                        break
                if skip:
                    continue
            score = 1.0 - float(dist)
            hits.append({"id": sid, "score": score, "payload": payload})
        return hits

    def delete(self, collection: str, point_ids: List[Any]) -> int:
        if not point_ids:
            return 0
        ids = [str(p) for p in point_ids]
        # Use parameter list — DuckDB supports `id IN (?, ?, ...)`
        # with positional params via UNNEST or the list shorthand.
        placeholders = ",".join(["?"] * len(ids))
        self._conn.execute(
            f"DELETE FROM {collection} WHERE id IN ({placeholders})", ids)
        return len(ids)

    def count(self, collection: str,
                filter_: Optional[Dict[str, Any]] = None) -> int:
        if filter_ is None:
            row = self._conn.execute(
                f"SELECT COUNT(*) FROM {collection}").fetchone()
            return int(row[0] if row else 0)
        # Filtered count: client-side payload walk (same trade-off
        # as LanceDB / sqlite-vec).
        import json as _json
        matched = 0
        for (payload_raw,) in self._conn.execute(
                f"SELECT payload FROM {collection}").fetchall():
            try:
                payload = _json.loads(payload_raw or "{}")
            except (_json.JSONDecodeError, TypeError):
                payload = payload_raw if isinstance(payload_raw, dict) else {}
            ok = True
            for clause in (filter_.get("must") or []):
                k = clause.get("key")
                v = clause.get("match", {}).get("value")
                if k is not None and payload.get(k) != v:
                    ok = False
                    break
            if ok:
                matched += 1
        return matched


# =========================================================
# PgVectorStore — Postgres + pgvector extension
# =========================================================

class _PgVectorUnavailable(BaseVectorStore):
    """Stub returned when `psycopg` (v3) isn't installed."""

    name = "pgvector"
    _HINT = (
        "pgvector backend selected but `psycopg` (v3) is not installed. "
        "Run `pip install psycopg[binary]` and restart the server. "
        "Make sure your Postgres instance has the pgvector extension "
        "(`CREATE EXTENSION IF NOT EXISTS vector` once per database). "
        "Alternatively, `pip install throughline[pgvector]` once published."
    )

    def ensure_collection(self, *a, **kw): raise RuntimeError(self._HINT)
    def upsert(self, *a, **kw):             raise RuntimeError(self._HINT)
    def search(self, *a, **kw):             raise RuntimeError(self._HINT)
    def delete(self, *a, **kw):             raise RuntimeError(self._HINT)
    def count(self, *a, **kw):              raise RuntimeError(self._HINT)


class PgVectorStore(BaseVectorStore):
    """Postgres + pgvector extension. The only server-based backend
    in the embedded-alternates set; useful when the team already
    operates Postgres and wants to keep vectors in the same database
    as the rest of the application data.

    Connection: DSN string from `PGVECTOR_DSN` env, falling back to
    `DATABASE_URL`. Format: `postgresql://user:pass@host:port/db`.

    Schema per collection: a single table.
        id      TEXT PRIMARY KEY
        vector  vector(<dim>)
        payload JSONB

    Distance: cosine (`<=>` operator). Caller can pre-convert to
    L2 (`<->`) by passing `distance="l2"` to ensure_collection but
    the search query stays cosine — pgvector picks the operator
    based on the index, not the per-query call.

    Upsert via `INSERT ... ON CONFLICT (id) DO UPDATE SET ...` —
    proper update semantics across Postgres ≥ 9.5.
    """

    name = "pgvector"

    def __new__(cls, *a, **kw):
        try:
            import psycopg  # noqa: F401  -- psycopg v3
        except Exception:
            return _PgVectorUnavailable()
        return super().__new__(cls)

    def __init__(self, dsn: Optional[str] = None) -> None:
        import psycopg
        self.dsn = (
            dsn
            or os.getenv("PGVECTOR_DSN")
            or os.getenv("DATABASE_URL")
            or "postgresql://localhost/throughline"
        )
        # autocommit: simpler caller contract; each call commits.
        # Tunable via subclass if pipeline batching is wanted.
        self._conn = psycopg.connect(self.dsn, autocommit=True)
        # Ensure the pgvector extension is loaded (idempotent).
        # Skipped silently if the connecting role lacks CREATE EXTENSION
        # privilege — a DBA typically does this once per database.
        try:
            self._conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        except Exception:
            pass
        self._vector_size: Dict[str, int] = {}

    # --- ABC methods -----------------------------------------------
    def ensure_collection(self, name: str, vector_size: int,
                            distance: str = "cosine") -> None:
        self._vector_size[name] = int(vector_size)
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS {name} ("
            f"  id      TEXT PRIMARY KEY,"
            f"  vector  vector({int(vector_size)}),"
            f"  payload JSONB"
            f")"
        )
        # HNSW index for cosine distance. `IF NOT EXISTS` keeps this
        # idempotent. Index builds can be slow on large tables; users
        # with > 1M rows may prefer to bulk-load first then create
        # the index manually with their own ops parameters.
        op_class = "vector_cosine_ops" if distance == "cosine" \
            else "vector_l2_ops"
        try:
            self._conn.execute(
                f"CREATE INDEX IF NOT EXISTS {name}_vector_hnsw "
                f"ON {name} USING hnsw (vector {op_class})"
            )
        except Exception:
            # Older pgvector versions (< 0.5) lack HNSW; fall back
            # to IVFFlat.
            try:
                self._conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {name}_vector_ivf "
                    f"ON {name} USING ivfflat (vector {op_class}) "
                    f"WITH (lists = 100)"
                )
            except Exception:
                pass  # leave as a sequential scan; correctness > speed.

    def upsert(self, collection: str,
                points: List[Dict[str, Any]]) -> int:
        if not points:
            return 0
        import json as _json
        n = 0
        for p in points:
            pid = str(p["id"])
            vec_literal = self._vec_literal(p["vector"])
            payload = _json.dumps(p.get("payload") or {},
                                    ensure_ascii=False)
            self._conn.execute(
                f"INSERT INTO {collection}(id, vector, payload) "
                f"VALUES (%s, %s::vector, %s::jsonb) "
                f"ON CONFLICT (id) DO UPDATE SET "
                f"  vector = excluded.vector, "
                f"  payload = excluded.payload",
                [pid, vec_literal, payload],
            )
            n += 1
        return n

    def search(self, collection: str, vector: List[float],
                limit: int = 10,
                filter_: Optional[Dict[str, Any]] = None
                ) -> List[SearchHit]:
        import json as _json
        vec_literal = self._vec_literal(vector)
        # Cosine distance: 0 = identical, 2 = opposite. Score = 1 - d
        # gives the standard "higher = better" ordering that callers
        # expect across all backends.
        cur = self._conn.execute(
            f"SELECT id, vector <=> %s::vector AS dist, payload "
            f"FROM {collection} "
            f"ORDER BY dist LIMIT %s",
            [vec_literal, int(limit)],
        )
        rows = cur.fetchall()
        hits: List[SearchHit] = []
        for sid, dist, payload_raw in rows:
            if isinstance(payload_raw, dict):
                payload = payload_raw  # psycopg returns dict for JSONB
            else:
                try:
                    payload = _json.loads(payload_raw or "{}")
                except (_json.JSONDecodeError, TypeError):
                    payload = {}
            if filter_:
                want = {}
                for clause in (filter_.get("must") or []):
                    k = clause.get("key")
                    v = clause.get("match", {}).get("value")
                    if k is not None:
                        want[k] = v
                skip = False
                for k, v in want.items():
                    if payload.get(k) != v:
                        skip = True
                        break
                if skip:
                    continue
            score = 1.0 - float(dist)
            hits.append({"id": sid, "score": score, "payload": payload})
        return hits

    def delete(self, collection: str, point_ids: List[Any]) -> int:
        if not point_ids:
            return 0
        ids = [str(p) for p in point_ids]
        # ANY(%s::text[]) is the idiomatic pgvector / Postgres pattern
        # for an IN-style filter with a list parameter.
        self._conn.execute(
            f"DELETE FROM {collection} WHERE id = ANY(%s::text[])", [ids])
        return len(ids)

    def count(self, collection: str,
                filter_: Optional[Dict[str, Any]] = None) -> int:
        if filter_ is None:
            row = self._conn.execute(
                f"SELECT COUNT(*) FROM {collection}").fetchone()
            return int(row[0] if row else 0)
        # Filtered count: pull payloads + count matches client-side.
        # Same trade-off as the other embedded backends; fine at RAG
        # cardinality. A v0.3 candidate is to translate `must` clauses
        # into `payload @> jsonb_build_object(k, v)` for server-side
        # filter — defer until usage warrants the complexity.
        import json as _json
        matched = 0
        for (payload_raw,) in self._conn.execute(
                f"SELECT payload FROM {collection}").fetchall():
            if isinstance(payload_raw, dict):
                payload = payload_raw
            else:
                try:
                    payload = _json.loads(payload_raw or "{}")
                except (_json.JSONDecodeError, TypeError):
                    continue
            ok = True
            for clause in (filter_.get("must") or []):
                k = clause.get("key")
                v = clause.get("match", {}).get("value")
                if k is not None and payload.get(k) != v:
                    ok = False
                    break
            if ok:
                matched += 1
        return matched

    # --- helpers ---------------------------------------------------
    def _vec_literal(self, vector: List[float]) -> str:
        """pgvector's text representation of a vector: `[1.0,2.0,...]`.
        Sent as a string + cast to ::vector inside the SQL — works
        across psycopg versions without needing a custom type adapter."""
        inside = ",".join(repr(float(x)) for x in vector)
        return "[" + inside + "]"


# =========================================================
# Registry + factory
# =========================================================

_REGISTRY: Dict[str, Callable[[], BaseVectorStore]] = {
    "qdrant":     QdrantStore,
    "chroma":     ChromaStore,
    "lancedb":    LanceDBStore,
    "sqlite_vec": SqliteVecStore,
    "duckdb_vss": DuckDBVSSStore,
    "pgvector":   PgVectorStore,
}

_ALIASES: Dict[str, str] = {
    # All four originally-aliased v0.3 backends shipped as real impls
    # in v0.2.x: lancedb / sqlite_vec / duckdb_vss / pgvector. The
    # hyphen-spelling aliases for the underscore primaries are kept.
    "sqlite-vec":  "sqlite_vec",
    "duckdb-vss":  "duckdb_vss",
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
