"""Tests for U21 — vector store backend abstraction.

Covers `rag_server.vector_stores`: BaseVectorStore contract,
QdrantStore (HTTP mocked), ChromaStore (chromadb mocked or stub),
registry + factory + aliases.

No live Qdrant / Chroma required.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from rag_server import vector_stores as vs


# ------- factory + registry -------

class TestCreateVectorStore:
    def test_default_is_qdrant(self, monkeypatch):
        monkeypatch.delenv("VECTOR_STORE", raising=False)
        s = vs.create_vector_store()
        assert s.name == "qdrant"

    def test_explicit_qdrant(self):
        s = vs.create_vector_store("qdrant")
        assert isinstance(s, vs.QdrantStore)

    def test_env_var(self, monkeypatch):
        monkeypatch.setenv("VECTOR_STORE", "qdrant")
        assert vs.create_vector_store().name == "qdrant"

    def test_alias_routing_to_qdrant(self):
        """All four originally-aliased v0.3 backends shipped as real
        impls in v0.2.x. Only `none` (the Notes-only mission stub)
        still routes to qdrant."""
        for alias in ("none",):
            s = vs.create_vector_store(alias)
            assert s.name == "qdrant", f"{alias} failed to resolve"

    def test_sqlite_vec_hyphen_alias_routes_to_underscore(self):
        """`sqlite-vec` (hyphen, the spelling on the project's site)
        is an alias to the underscore-spelled primary."""
        s = vs.create_vector_store("sqlite-vec")
        # Stub or real, the name field is the underscore form.
        assert s.name == "sqlite_vec"

    def test_duckdb_vss_hyphen_alias_routes_to_underscore(self):
        """`duckdb-vss` is an alias to `duckdb_vss`."""
        s = vs.create_vector_store("duckdb-vss")
        assert s.name == "duckdb_vss"

    def test_unknown_raises(self):
        with pytest.raises(ValueError) as ei:
            vs.create_vector_store("milvus-cluster-9000")
        msg = str(ei.value)
        assert "milvus" in msg
        assert "qdrant" in msg
        assert "chroma" in msg

    def test_register_plugin(self):
        class Fake(vs.BaseVectorStore):
            name = "fake"

            def ensure_collection(self, *a, **k): pass
            def upsert(self, *a, **k): return 0
            def search(self, *a, **k): return []
            def delete(self, *a, **k): return 0
            def count(self, *a, **k): return 0

        vs.register_vector_store("fake", Fake)
        try:
            assert vs.create_vector_store("fake").name == "fake"
        finally:
            vs._REGISTRY.pop("fake", None)

    def test_available_lists_primaries_and_aliases(self):
        names = set(vs.available_vector_stores())
        # All five non-Qdrant primaries are available in v0.2.x.
        assert {"qdrant", "chroma", "lancedb",
                 "sqlite_vec", "duckdb_vss", "pgvector"}.issubset(names)
        assert {"sqlite-vec", "duckdb-vss", "none"}.issubset(names)


# ------- QdrantStore wire-level tests -------

def _fake_http_factory(script):
    """Build a urlopen replacement driven by a sequenced script.

    Each script entry is (method, path_suffix_contains, response_dict).
    The fake asserts the expected method + path and returns the
    canned JSON response."""
    call_log: List[Dict[str, Any]] = []
    remaining = list(script)

    class _Resp:
        def __init__(self, body_dict):
            self._body = json.dumps(body_dict).encode("utf-8")

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

    def fake(req, timeout=None):
        body = None
        if req.data:
            body = json.loads(req.data.decode("utf-8"))
        call_log.append({
            "method": req.get_method(),
            "url": req.full_url,
            "body": body,
        })
        if not remaining:
            return _Resp({})
        expect_method, expect_contains, response = remaining.pop(0)
        assert req.get_method() == expect_method, (
            f"expected {expect_method}, got {req.get_method()}")
        assert expect_contains in req.full_url, (
            f"{expect_contains!r} not in {req.full_url!r}")
        if callable(response):
            return _Resp(response(body))
        return _Resp(response)

    return fake, call_log


class TestQdrantStore:
    def test_ensure_collection_idempotent(self, monkeypatch):
        fake, log = _fake_http_factory([
            ("GET", "/collections/obs", {"result": {"status": "green"}}),
        ])
        monkeypatch.setattr("urllib.request.urlopen", fake)
        s = vs.QdrantStore(url="http://fake")
        s.ensure_collection("obs", vector_size=1024)
        # Only the GET; no PUT because the collection already exists.
        assert [c["method"] for c in log] == ["GET"]

    def test_ensure_collection_creates_when_missing(self, monkeypatch):
        # First GET returns 404 (simulated via our fake raising).
        import urllib.error

        put_log: List[Dict[str, Any]] = []

        class _Resp:
            def __init__(self, body):
                self._body = body

            def read(self):
                return self._body

            def __enter__(self): return self

            def __exit__(self, *a): pass

        def fake(req, timeout=None):
            if req.get_method() == "GET":
                raise urllib.error.HTTPError(
                    req.full_url, 404, "Not found", {}, io.BytesIO(b""))
            put_log.append({
                "method": req.get_method(),
                "body": json.loads(req.data.decode("utf-8")),
            })
            return _Resp(b'{}')

        monkeypatch.setattr("urllib.request.urlopen", fake)
        s = vs.QdrantStore(url="http://fake")
        s.ensure_collection("obs", vector_size=1536, distance="cosine")
        assert len(put_log) == 1
        assert put_log[0]["method"] == "PUT"
        assert put_log[0]["body"]["vectors"]["size"] == 1536
        assert put_log[0]["body"]["vectors"]["distance"] == "Cosine"

    def test_upsert_empty_short_circuits(self, monkeypatch):
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("must not call HTTP on empty points")),
        )
        s = vs.QdrantStore(url="http://fake")
        assert s.upsert("obs", []) == 0

    def test_upsert_posts_normalized_payload(self, monkeypatch):
        fake, log = _fake_http_factory([
            ("PUT", "/collections/obs/points", {"result": {"status": "ok"}}),
        ])
        monkeypatch.setattr("urllib.request.urlopen", fake)
        s = vs.QdrantStore(url="http://fake")
        n = s.upsert("obs", [
            {"id": 1, "vector": [0.1, 0.2], "payload": {"title": "a"}},
            {"id": 2, "vector": [0.3, 0.4]},  # no payload → {}
        ])
        assert n == 2
        pts = log[0]["body"]["points"]
        assert pts[0]["payload"] == {"title": "a"}
        assert pts[1]["payload"] == {}

    def test_search_returns_normalized_hits(self, monkeypatch):
        fake, _ = _fake_http_factory([
            ("POST", "/points/search", {
                "result": [
                    {"id": 1, "score": 0.9, "payload": {"t": "a"}},
                    {"id": 2, "score": 0.7, "payload": {"t": "b"}},
                ],
            }),
        ])
        monkeypatch.setattr("urllib.request.urlopen", fake)
        s = vs.QdrantStore(url="http://fake")
        hits = s.search("obs", [0.1, 0.2], limit=5)
        assert len(hits) == 2
        assert hits[0] == {"id": 1, "score": 0.9, "payload": {"t": "a"}}

    def test_delete_empty_short_circuits(self, monkeypatch):
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("must not call HTTP on empty delete")),
        )
        assert vs.QdrantStore(url="http://fake").delete("obs", []) == 0

    def test_delete_posts_ids(self, monkeypatch):
        fake, log = _fake_http_factory([
            ("POST", "/points/delete", {"result": "ok"}),
        ])
        monkeypatch.setattr("urllib.request.urlopen", fake)
        n = vs.QdrantStore(url="http://fake").delete("obs", [1, 2, 3])
        assert n == 3
        assert log[0]["body"]["points"] == [1, 2, 3]

    def test_count(self, monkeypatch):
        fake, _ = _fake_http_factory([
            ("POST", "/points/count", {"result": {"count": 42}}),
        ])
        monkeypatch.setattr("urllib.request.urlopen", fake)
        assert vs.QdrantStore(url="http://fake").count("obs") == 42

    def test_count_missing_defaults_to_zero(self, monkeypatch):
        fake, _ = _fake_http_factory([
            ("POST", "/points/count", {}),
        ])
        monkeypatch.setattr("urllib.request.urlopen", fake)
        assert vs.QdrantStore(url="http://fake").count("obs") == 0

    def test_api_key_header(self, monkeypatch):
        captured = {}

        class _Resp:
            def read(self): return b'{"result": {"count": 0}}'
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake(req, timeout=None):
            captured["headers"] = {k.lower(): v for k, v in req.header_items()}
            return _Resp()

        monkeypatch.setattr("urllib.request.urlopen", fake)
        vs.QdrantStore(url="http://fake", api_key="secret").count("obs")
        assert captured["headers"].get("api-key") == "secret"


# ------- ChromaStore behaviour — stub path when unavailable -------

class TestChromaStoreWithoutChromadb:
    def test_stub_when_chromadb_missing(self, monkeypatch):
        """If chromadb is not importable, instantiation succeeds and
        returns a stub; real calls raise RuntimeError with install
        hint, not ImportError at class-definition time."""
        # Force the import to fail.
        import builtins
        real_import = builtins.__import__

        def guard(name, *a, **kw):
            if name == "chromadb" or name.startswith("chromadb."):
                raise ImportError("chromadb not installed (simulated)")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        s = vs.ChromaStore()
        assert s.name == "chroma"
        with pytest.raises(RuntimeError) as ei:
            s.ensure_collection("x", 1024)
        assert "chromadb" in str(ei.value).lower()


class TestChromaStoreWithFakeChromadb:
    """Simulate chromadb via an in-memory fake so the ChromaStore's
    own glue is covered without installing the dep."""

    def _inject_fake_chromadb(self, monkeypatch):
        import types
        fake = types.ModuleType("chromadb")

        class FakeCollection:
            def __init__(self, name):
                self.name = name
                self._docs = {}  # id -> (vector, meta)

            def upsert(self, ids, embeddings, metadatas):
                for i, e, m in zip(ids, embeddings, metadatas or [{}] * len(ids)):
                    self._docs[i] = (e, m or {})

            def query(self, query_embeddings, n_results, where=None):
                # Naive: return first n_results ids in insertion order
                # with canned distances.
                ids = list(self._docs.keys())[:n_results]
                return {
                    "ids":       [ids],
                    "distances": [[0.1 * (i + 1) for i in range(len(ids))]],
                    "metadatas": [[self._docs[i][1] for i in ids]],
                }

            def delete(self, ids):
                for i in ids:
                    self._docs.pop(i, None)

            def count(self):
                return len(self._docs)

            def get(self, where=None, limit=None):
                ids = list(self._docs.keys())
                if limit is not None:
                    ids = ids[:limit]
                return {"ids": ids}

        class FakeClient:
            def __init__(self, path=None):
                self.path = path
                self._cols = {}

            def get_or_create_collection(self, name, metadata=None):
                col = self._cols.get(name)
                if col is None:
                    col = FakeCollection(name)
                    self._cols[name] = col
                return col

        fake.PersistentClient = FakeClient
        monkeypatch.setitem(sys.modules, "chromadb", fake)

    def test_upsert_and_search_roundtrip(self, tmp_path, monkeypatch):
        self._inject_fake_chromadb(monkeypatch)
        s = vs.ChromaStore(path=str(tmp_path))
        s.ensure_collection("obs", vector_size=3, distance="cosine")
        n = s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"t": "one"}},
            {"id": "b", "vector": [0.4, 0.5, 0.6], "payload": {"t": "two"}},
        ])
        assert n == 2
        hits = s.search("obs", [0.1, 0.2, 0.3], limit=2)
        assert len(hits) == 2
        assert {h["id"] for h in hits} == {"a", "b"}
        # Score is 1 - distance so descending-sort still works.
        assert hits[0]["score"] > hits[1]["score"]

    def test_delete(self, tmp_path, monkeypatch):
        self._inject_fake_chromadb(monkeypatch)
        s = vs.ChromaStore(path=str(tmp_path))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3]},
            {"id": "b", "vector": [0.4, 0.5, 0.6]},
        ])
        assert s.count("obs") == 2
        assert s.delete("obs", ["a"]) == 1
        assert s.count("obs") == 1

    def test_count_empty(self, tmp_path, monkeypatch):
        self._inject_fake_chromadb(monkeypatch)
        s = vs.ChromaStore(path=str(tmp_path))
        s.ensure_collection("obs", 3)
        assert s.count("obs") == 0


# ------- LanceDBStore behaviour — stub path when unavailable -------

class TestLanceDBStoreWithoutLancedb:
    def test_stub_when_lancedb_missing(self, monkeypatch):
        """If lancedb (or pyarrow) isn't importable, instantiation
        succeeds and returns a stub; real calls raise RuntimeError
        with the install hint, not ImportError at class-definition."""
        import builtins
        real_import = builtins.__import__

        def guard(name, *a, **kw):
            if name == "lancedb" or name.startswith("lancedb."):
                raise ImportError("lancedb not installed (simulated)")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        s = vs.LanceDBStore()
        assert s.name == "lancedb"
        with pytest.raises(RuntimeError) as ei:
            s.ensure_collection("x", 1024)
        assert "lancedb" in str(ei.value).lower()


class TestLanceDBStoreWithFakeLancedb:
    """Simulate lancedb + pyarrow via in-memory fakes so the
    LanceDBStore's own glue is covered without installing the dep."""

    def _inject_fake_lancedb(self, monkeypatch):
        import types

        # --- fake pyarrow just enough that _schema doesn't explode.
        fake_pa = types.ModuleType("pyarrow")

        class FakeField:
            def __init__(self, name, typ):
                self.name = name
                self.type = typ

        class FakeSchema:
            def __init__(self, fields):
                self.fields = fields

        fake_pa.field = lambda name, typ: FakeField(name, typ)
        fake_pa.schema = lambda fields: FakeSchema(fields)
        fake_pa.string = lambda: "string"
        fake_pa.float32 = lambda: "float32"
        fake_pa.list_ = lambda inner, size=None: ("list", inner, size)
        monkeypatch.setitem(sys.modules, "pyarrow", fake_pa)

        # --- fake lancedb module with a minimal connect/Table API.
        fake = types.ModuleType("lancedb")

        class FakeTable:
            def __init__(self, name, schema):
                self.name = name
                self.schema = schema
                self._rows = []  # list of dicts

            class _Query:
                def __init__(self, table, vector):
                    self._table = table
                    self._vector = vector
                    self._limit = 10

                def limit(self, n):
                    self._limit = n
                    return self

                def to_list(self):
                    import math as _math

                    def _dist(a, b):
                        # Simple L2 distance.
                        if not a or not b:
                            return 1.0
                        return _math.sqrt(sum(
                            (float(x) - float(y)) ** 2
                            for x, y in zip(a, b)))

                    scored = []
                    for row in self._table._rows:
                        d = _dist(row["vector"], self._vector)
                        out = dict(row)
                        out["_distance"] = d
                        scored.append(out)
                    scored.sort(key=lambda r: r["_distance"])
                    return scored[:self._limit]

            def search(self, vector, vector_column_name="vector"):
                return FakeTable._Query(self, vector)

            def add(self, rows):
                for r in rows:
                    self._rows.append(dict(r))

            def delete(self, where_clause):
                # Parse `id IN ('a','b',...)`. Good enough for tests.
                import re as _re
                m = _re.match(
                    r"id\s+IN\s*\(([^)]*)\)", where_clause, _re.IGNORECASE)
                if not m:
                    return
                ids_raw = m.group(1)
                ids = {
                    x.strip().strip("'").strip('"')
                    for x in ids_raw.split(",") if x.strip()
                }
                self._rows = [r for r in self._rows
                              if str(r.get("id")) not in ids]

            def count_rows(self):
                return len(self._rows)

            class _Frame:
                def __init__(self, rows):
                    self._rows = rows

                def to_dict(self, orient):
                    assert orient == "records"
                    return [dict(r) for r in self._rows]

            def to_pandas(self):
                return FakeTable._Frame(self._rows)

        class FakeDB:
            def __init__(self, path):
                self.path = path
                self._tables = {}

            def table_names(self):
                return list(self._tables.keys())

            def create_table(self, name, schema):
                t = FakeTable(name, schema)
                self._tables[name] = t
                return t

            def open_table(self, name):
                return self._tables[name]

        fake.connect = lambda path: FakeDB(path)
        monkeypatch.setitem(sys.modules, "lancedb", fake)

    def test_upsert_and_search_roundtrip(self, tmp_path, monkeypatch):
        self._inject_fake_lancedb(monkeypatch)
        s = vs.LanceDBStore(path=str(tmp_path))
        s.ensure_collection("obs", vector_size=3, distance="cosine")
        n = s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"t": "one"}},
            {"id": "b", "vector": [0.4, 0.5, 0.6], "payload": {"t": "two"}},
        ])
        assert n == 2
        hits = s.search("obs", [0.1, 0.2, 0.3], limit=2)
        assert len(hits) == 2
        assert {h["id"] for h in hits} == {"a", "b"}
        # Closer vector comes first (score is 1 - distance).
        assert hits[0]["id"] == "a"
        assert hits[0]["score"] > hits[1]["score"]
        # Payload JSON round-tripped correctly.
        assert hits[0]["payload"] == {"t": "one"}

    def test_upsert_updates_in_place(self, tmp_path, monkeypatch):
        self._inject_fake_lancedb(monkeypatch)
        s = vs.LanceDBStore(path=str(tmp_path))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"v": 1}},
        ])
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"v": 2}},
        ])
        assert s.count("obs") == 1  # not 2 — delete-then-add upsert.
        hits = s.search("obs", [0.1, 0.2, 0.3], limit=5)
        assert hits[0]["payload"] == {"v": 2}

    def test_delete(self, tmp_path, monkeypatch):
        self._inject_fake_lancedb(monkeypatch)
        s = vs.LanceDBStore(path=str(tmp_path))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3]},
            {"id": "b", "vector": [0.4, 0.5, 0.6]},
        ])
        assert s.count("obs") == 2
        assert s.delete("obs", ["a"]) == 1
        assert s.count("obs") == 1

    def test_search_filter_must_clause(self, tmp_path, monkeypatch):
        """Qdrant-shape `filter_` with a `must` clause applies
        client-side after the vector search."""
        self._inject_fake_lancedb(monkeypatch)
        s = vs.LanceDBStore(path=str(tmp_path))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3],
             "payload": {"knowledge_identity": "universal"}},
            {"id": "b", "vector": [0.2, 0.3, 0.4],
             "payload": {"knowledge_identity": "personal"}},
        ])
        hits = s.search(
            "obs", [0.1, 0.2, 0.3], limit=5,
            filter_={"must": [{"key": "knowledge_identity",
                                "match": {"value": "universal"}}]})
        assert len(hits) == 1
        assert hits[0]["id"] == "a"

    def test_count_with_filter(self, tmp_path, monkeypatch):
        self._inject_fake_lancedb(monkeypatch)
        s = vs.LanceDBStore(path=str(tmp_path))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p1"}},
            {"id": "b", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p2"}},
            {"id": "c", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p1"}},
        ])
        assert s.count("obs") == 3
        n = s.count("obs", filter_={
            "must": [{"key": "pack", "match": {"value": "p1"}}]})
        assert n == 2

    def test_empty_upsert_and_delete_shortcircuit(self, tmp_path, monkeypatch):
        self._inject_fake_lancedb(monkeypatch)
        s = vs.LanceDBStore(path=str(tmp_path))
        s.ensure_collection("obs", 3)
        assert s.upsert("obs", []) == 0
        assert s.delete("obs", []) == 0


# ------- SqliteVecStore behaviour — stub path when unavailable -------

class TestSqliteVecStoreWithoutSqliteVec:
    def test_stub_when_sqlite_vec_missing(self, monkeypatch):
        """If sqlite_vec isn't importable, instantiation succeeds and
        returns a stub; real calls raise RuntimeError with the
        install hint."""
        import builtins
        real_import = builtins.__import__

        def guard(name, *a, **kw):
            if name == "sqlite_vec" or name.startswith("sqlite_vec."):
                raise ImportError("sqlite_vec not installed (simulated)")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        s = vs.SqliteVecStore()
        assert s.name == "sqlite_vec"
        with pytest.raises(RuntimeError) as ei:
            s.ensure_collection("x", 1024)
        assert "sqlite-vec" in str(ei.value).lower() or \
               "sqlite_vec" in str(ei.value).lower()


class TestSqliteVecStoreWithFakeSqliteVec:
    """Use real stdlib sqlite3 (in-memory) but fake the `sqlite_vec`
    extension. The fake replaces vec0 virtual tables with regular
    tables that keep the bytes blob; MATCH queries are emulated via
    a Python UDF that ranks by L2 distance.

    The trick: monkey-patch `sqlite3.Connection.execute` to rewrite
    `CREATE VIRTUAL TABLE ... USING vec0(...)` into a regular CREATE
    TABLE. The store's other SQL is portable as-is; only the MATCH
    operator needs an emulation hook."""

    def _inject_fake_sqlite_vec(self, monkeypatch):
        """Replaces `sqlite_vec` + wraps `sqlite3.connect` to return a
        proxy that simulates vec0 (CREATE VIRTUAL TABLE ... USING
        vec0 → regular table; vector MATCH → Python-side L2 ranking).

        This is a pragmatic test rig — it doesn't validate the SQL
        we'd actually send to a real sqlite-vec install, but it does
        validate every code path in SqliteVecStore that doesn't
        involve the extension's actual implementation."""
        import types
        import math as _math
        import struct as _struct
        import re as _re
        import sqlite3 as _sqlite3

        fake_sv = types.ModuleType("sqlite_vec")
        fake_sv.load = lambda _conn: None  # the proxy below handles it
        monkeypatch.setitem(sys.modules, "sqlite_vec", fake_sv)

        real_connect = _sqlite3.connect

        class _ProxyCursor:
            def __init__(self, rows):
                self._rows = list(rows)

            def fetchall(self):
                return self._rows

            def fetchone(self):
                return self._rows[0] if self._rows else None

        class _ProxyConn:
            def __init__(self, real):
                self._real = real
                # Track autoincrement rowid per table for inserts that
                # land in our rewritten vec0 tables (which have an
                # explicit AUTOINCREMENT rowid column).
                self._next_rowid = {}

            def enable_load_extension(self, _flag):
                pass

            def execute(self, sql, params=()):
                # Rewrite vec0 CREATE → regular table.
                if "USING vec0" in sql or "using vec0" in sql:
                    m = _re.search(
                        r"CREATE\s+VIRTUAL\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
                        r"(\w+)\s+USING\s+vec0\(",
                        sql, _re.IGNORECASE)
                    if m:
                        table = m.group(1)
                        return self._real.execute(
                            f"CREATE TABLE IF NOT EXISTS {table} ("
                            f" rowid INTEGER PRIMARY KEY AUTOINCREMENT,"
                            f" vector BLOB)")
                # Handle MATCH queries: parse + Python-side ranking.
                if "MATCH" in sql.upper() and params:
                    return self._exec_match_query(sql, params)
                return self._real.execute(sql, params)

            def cursor(self):
                # Wrap a real cursor with the same execute logic.
                real_cur = self._real.cursor()
                proxy = self  # noqa

                class _CurProxy:
                    def __init__(self):
                        self.lastrowid = None

                    def execute(self, sql, params=()):
                        if "USING vec0" in sql or "using vec0" in sql:
                            return proxy.execute(sql, params)
                        if "MATCH" in sql.upper() and params:
                            return proxy._exec_match_query(sql, params)
                        real_cur.execute(sql, params)
                        self.lastrowid = real_cur.lastrowid
                        return real_cur

                    def fetchone(self):
                        return real_cur.fetchone()

                    def fetchall(self):
                        return real_cur.fetchall()

                return _CurProxy()

            def commit(self):
                self._real.commit()

            def _exec_match_query(self, sql, params):
                # Expected shape (matches SqliteVecStore.search()):
                #   SELECT v.rowid, v.distance, m.id, m.payload
                #   FROM <vec> v JOIN <meta> m ON m.rowid = v.rowid
                #   WHERE v.vector MATCH ? ORDER BY v.distance LIMIT ?
                m = _re.search(
                    r"FROM\s+(\w+)\s+v\s+JOIN\s+(\w+)\s+m\b",
                    sql, _re.IGNORECASE)
                assert m, f"unrecognized MATCH query: {sql}"
                vec_table = m.group(1)
                meta_table = m.group(2)
                blob = params[0]
                limit = int(params[1]) if len(params) > 1 else 10
                size = len(blob) // 4
                qvec = _struct.unpack(f"{size}f", blob)
                vecs = self._real.execute(
                    f"SELECT rowid, vector FROM {vec_table}").fetchall()
                scored = []
                for rowid, vblob in vecs:
                    if vblob is None:
                        continue
                    rsize = len(vblob) // 4
                    rvec = _struct.unpack(f"{rsize}f", vblob)
                    d = _math.sqrt(sum(
                        (float(a) - float(b)) ** 2
                        for a, b in zip(qvec, rvec)))
                    scored.append((rowid, d))
                scored.sort(key=lambda r: r[1])
                scored = scored[:limit]
                results = []
                for rowid, dist in scored:
                    row = self._real.execute(
                        f"SELECT id, payload FROM {meta_table} "
                        f"WHERE rowid = ?", (rowid,)).fetchone()
                    if row is None:
                        continue
                    results.append((rowid, dist, row[0], row[1]))
                return _ProxyCursor(results)

        def _proxy_connect(path, *args, **kwargs):
            return _ProxyConn(real_connect(path, *args, **kwargs))

        monkeypatch.setattr(_sqlite3, "connect", _proxy_connect)

    def test_upsert_and_search_roundtrip(self, tmp_path, monkeypatch):
        self._inject_fake_sqlite_vec(monkeypatch)
        s = vs.SqliteVecStore(path=str(tmp_path / "vec.db"))
        s.ensure_collection("obs", vector_size=3, distance="cosine")
        n = s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"t": "one"}},
            {"id": "b", "vector": [0.4, 0.5, 0.6], "payload": {"t": "two"}},
        ])
        assert n == 2
        hits = s.search("obs", [0.1, 0.2, 0.3], limit=5)
        assert len(hits) == 2
        assert {h["id"] for h in hits} == {"a", "b"}
        # Nearest result returns highest score.
        assert hits[0]["id"] == "a"
        assert hits[0]["score"] > hits[1]["score"]
        assert hits[0]["payload"] == {"t": "one"}

    def test_upsert_updates_in_place(self, tmp_path, monkeypatch):
        self._inject_fake_sqlite_vec(monkeypatch)
        s = vs.SqliteVecStore(path=str(tmp_path / "vec.db"))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"v": 1}},
        ])
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"v": 2}},
        ])
        assert s.count("obs") == 1  # update, not duplicate insert.
        hits = s.search("obs", [0.1, 0.2, 0.3], limit=5)
        assert hits[0]["payload"] == {"v": 2}

    def test_delete(self, tmp_path, monkeypatch):
        self._inject_fake_sqlite_vec(monkeypatch)
        s = vs.SqliteVecStore(path=str(tmp_path / "vec.db"))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3]},
            {"id": "b", "vector": [0.4, 0.5, 0.6]},
        ])
        assert s.count("obs") == 2
        assert s.delete("obs", ["a"]) == 1
        assert s.count("obs") == 1
        # Deleting a non-existent id is a no-op (returns 0).
        assert s.delete("obs", ["nope"]) == 0

    def test_search_filter_must_clause(self, tmp_path, monkeypatch):
        self._inject_fake_sqlite_vec(monkeypatch)
        s = vs.SqliteVecStore(path=str(tmp_path / "vec.db"))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3],
             "payload": {"knowledge_identity": "universal"}},
            {"id": "b", "vector": [0.2, 0.3, 0.4],
             "payload": {"knowledge_identity": "personal"}},
        ])
        hits = s.search(
            "obs", [0.1, 0.2, 0.3], limit=5,
            filter_={"must": [{"key": "knowledge_identity",
                                "match": {"value": "universal"}}]})
        assert len(hits) == 1
        assert hits[0]["id"] == "a"

    def test_count_with_filter(self, tmp_path, monkeypatch):
        self._inject_fake_sqlite_vec(monkeypatch)
        s = vs.SqliteVecStore(path=str(tmp_path / "vec.db"))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p1"}},
            {"id": "b", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p2"}},
            {"id": "c", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p1"}},
        ])
        assert s.count("obs") == 3
        n = s.count("obs", filter_={
            "must": [{"key": "pack", "match": {"value": "p1"}}]})
        assert n == 2

    def test_empty_upsert_and_delete_shortcircuit(self, tmp_path, monkeypatch):
        self._inject_fake_sqlite_vec(monkeypatch)
        s = vs.SqliteVecStore(path=str(tmp_path / "vec.db"))
        s.ensure_collection("obs", 3)
        assert s.upsert("obs", []) == 0
        assert s.delete("obs", []) == 0


# ------- DuckDBVSSStore behaviour — stub path when unavailable -------

class TestDuckDBVSSStoreWithoutDuckDB:
    def test_stub_when_duckdb_missing(self, monkeypatch):
        """If duckdb isn't importable, instantiation succeeds and
        returns a stub; real calls raise RuntimeError with the
        install hint."""
        import builtins
        real_import = builtins.__import__

        def guard(name, *a, **kw):
            if name == "duckdb" or name.startswith("duckdb."):
                raise ImportError("duckdb not installed (simulated)")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        s = vs.DuckDBVSSStore()
        assert s.name == "duckdb_vss"
        with pytest.raises(RuntimeError) as ei:
            s.ensure_collection("x", 1024)
        assert "duckdb" in str(ei.value).lower()


class TestDuckDBVSSStoreWithFakeDuckDB:
    """Simulate `duckdb` via an in-memory fake — minimal SQL parser
    plus a Python-side store of (id, vector, payload) tuples per
    table. Just enough to exercise every code path in DuckDBVSSStore."""

    def _inject_fake_duckdb(self, monkeypatch):
        import types
        import re as _re
        import math as _math

        fake = types.ModuleType("duckdb")

        class _FakeCursor:
            def __init__(self, rows):
                self._rows = list(rows)

            def fetchall(self):
                return self._rows

            def fetchone(self):
                return self._rows[0] if self._rows else None

        class _FakeConn:
            def __init__(self, path):
                self.path = path
                self._tables = {}  # name -> {id: (vector, payload)}

            def execute(self, sql, params=()):
                stripped = sql.strip()
                up = stripped.upper()
                # No-ops we don't care about.
                if up.startswith("INSTALL ") or up.startswith("LOAD "):
                    return _FakeCursor([])
                # CREATE TABLE IF NOT EXISTS <name>(...)
                m = _re.match(
                    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(",
                    stripped, _re.IGNORECASE)
                if m:
                    name = m.group(1)
                    self._tables.setdefault(name, {})
                    return _FakeCursor([])
                # INSERT ... ON CONFLICT — params: [pid, vec, payload]
                m = _re.match(
                    r"INSERT\s+INTO\s+(\w+)\s*\(", stripped, _re.IGNORECASE)
                if m and "ON CONFLICT" in up:
                    name = m.group(1)
                    pid, vec, payload = params
                    self._tables.setdefault(name, {})
                    self._tables[name][pid] = (list(vec), payload)
                    return _FakeCursor([])
                # SELECT id, array_distance(vector, ?::FLOAT[]) ...
                m = _re.match(
                    r"SELECT\s+id,\s+array_distance\(vector,\s+\?::FLOAT\[\]\)\s+AS\s+dist,\s+payload\s+FROM\s+(\w+)\s+ORDER\s+BY\s+dist\s+LIMIT\s+\?",
                    stripped, _re.IGNORECASE)
                if m:
                    name = m.group(1)
                    qvec, limit = params
                    rows = []
                    for pid, (vec, payload) in self._tables.get(name, {}).items():
                        if not vec:
                            d = 1.0
                        else:
                            d = _math.sqrt(sum(
                                (float(a) - float(b)) ** 2
                                for a, b in zip(qvec, vec)))
                        rows.append((pid, d, payload))
                    rows.sort(key=lambda r: r[1])
                    return _FakeCursor(rows[:int(limit)])
                # DELETE FROM <name> WHERE id IN (?, ?, ...)
                m = _re.match(
                    r"DELETE\s+FROM\s+(\w+)\s+WHERE\s+id\s+IN\s+\(",
                    stripped, _re.IGNORECASE)
                if m:
                    name = m.group(1)
                    for pid in params:
                        self._tables.get(name, {}).pop(pid, None)
                    return _FakeCursor([])
                # SELECT COUNT(*) FROM <name>
                m = _re.match(
                    r"SELECT\s+COUNT\(\*\)\s+FROM\s+(\w+)$",
                    stripped, _re.IGNORECASE)
                if m:
                    name = m.group(1)
                    return _FakeCursor([(len(self._tables.get(name, {})),)])
                # SELECT payload FROM <name>
                m = _re.match(
                    r"SELECT\s+payload\s+FROM\s+(\w+)$",
                    stripped, _re.IGNORECASE)
                if m:
                    name = m.group(1)
                    return _FakeCursor(
                        [(payload,) for (_, payload)
                         in self._tables.get(name, {}).values()])
                raise AssertionError(
                    f"unrecognized SQL in fake duckdb: {sql!r}")

        fake.connect = lambda path: _FakeConn(path)
        monkeypatch.setitem(sys.modules, "duckdb", fake)

    def test_upsert_and_search_roundtrip(self, tmp_path, monkeypatch):
        self._inject_fake_duckdb(monkeypatch)
        s = vs.DuckDBVSSStore(path=str(tmp_path / "x.duckdb"))
        s.ensure_collection("obs", vector_size=3, distance="cosine")
        n = s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"t": "one"}},
            {"id": "b", "vector": [0.4, 0.5, 0.6], "payload": {"t": "two"}},
        ])
        assert n == 2
        hits = s.search("obs", [0.1, 0.2, 0.3], limit=2)
        assert len(hits) == 2
        assert {h["id"] for h in hits} == {"a", "b"}
        assert hits[0]["id"] == "a"
        assert hits[0]["score"] > hits[1]["score"]
        assert hits[0]["payload"] == {"t": "one"}

    def test_upsert_updates_in_place(self, tmp_path, monkeypatch):
        self._inject_fake_duckdb(monkeypatch)
        s = vs.DuckDBVSSStore(path=str(tmp_path / "x.duckdb"))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"v": 1}},
        ])
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"v": 2}},
        ])
        assert s.count("obs") == 1
        hits = s.search("obs", [0.1, 0.2, 0.3], limit=5)
        assert hits[0]["payload"] == {"v": 2}

    def test_delete(self, tmp_path, monkeypatch):
        self._inject_fake_duckdb(monkeypatch)
        s = vs.DuckDBVSSStore(path=str(tmp_path / "x.duckdb"))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3]},
            {"id": "b", "vector": [0.4, 0.5, 0.6]},
        ])
        assert s.count("obs") == 2
        assert s.delete("obs", ["a"]) == 1
        assert s.count("obs") == 1

    def test_search_filter_must_clause(self, tmp_path, monkeypatch):
        self._inject_fake_duckdb(monkeypatch)
        s = vs.DuckDBVSSStore(path=str(tmp_path / "x.duckdb"))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3],
             "payload": {"knowledge_identity": "universal"}},
            {"id": "b", "vector": [0.2, 0.3, 0.4],
             "payload": {"knowledge_identity": "personal"}},
        ])
        hits = s.search(
            "obs", [0.1, 0.2, 0.3], limit=5,
            filter_={"must": [{"key": "knowledge_identity",
                                "match": {"value": "universal"}}]})
        assert len(hits) == 1
        assert hits[0]["id"] == "a"

    def test_count_with_filter(self, tmp_path, monkeypatch):
        self._inject_fake_duckdb(monkeypatch)
        s = vs.DuckDBVSSStore(path=str(tmp_path / "x.duckdb"))
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p1"}},
            {"id": "b", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p2"}},
            {"id": "c", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p1"}},
        ])
        assert s.count("obs") == 3
        assert s.count("obs", filter_={
            "must": [{"key": "pack", "match": {"value": "p1"}}]}) == 2

    def test_empty_upsert_and_delete_shortcircuit(self, tmp_path, monkeypatch):
        self._inject_fake_duckdb(monkeypatch)
        s = vs.DuckDBVSSStore(path=str(tmp_path / "x.duckdb"))
        s.ensure_collection("obs", 3)
        assert s.upsert("obs", []) == 0
        assert s.delete("obs", []) == 0


# ------- PgVectorStore behaviour — stub path when unavailable -------

class TestPgVectorStoreWithoutPsycopg:
    def test_stub_when_psycopg_missing(self, monkeypatch):
        """If psycopg isn't importable, instantiation succeeds and
        returns a stub; real calls raise RuntimeError with the
        install hint."""
        import builtins
        real_import = builtins.__import__

        def guard(name, *a, **kw):
            if name == "psycopg" or name.startswith("psycopg."):
                raise ImportError("psycopg not installed (simulated)")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        s = vs.PgVectorStore()
        assert s.name == "pgvector"
        with pytest.raises(RuntimeError) as ei:
            s.ensure_collection("x", 1024)
        assert "psycopg" in str(ei.value).lower()


class TestPgVectorStoreWithFakePsycopg:
    """Simulate `psycopg` (v3) via an in-memory fake — minimal SQL
    parser tracking per-table dicts of (id, vector, payload)."""

    def _inject_fake_psycopg(self, monkeypatch):
        import types
        import re as _re
        import math as _math

        fake = types.ModuleType("psycopg")

        def _parse_vec_literal(s):
            # `[1.0,2.0,...]` → list of floats. Tolerate whitespace.
            inside = s.strip().lstrip("[").rstrip("]")
            if not inside:
                return []
            return [float(x) for x in inside.split(",")]

        class _FakeCursor:
            def __init__(self, rows):
                self._rows = list(rows)

            def fetchall(self):
                return self._rows

            def fetchone(self):
                return self._rows[0] if self._rows else None

        class _FakeConn:
            def __init__(self, dsn):
                self.dsn = dsn
                self.autocommit = True
                self._tables = {}  # name -> {id: (vector, payload)}

            def execute(self, sql, params=()):
                stripped = sql.strip()
                up = stripped.upper()
                # No-ops we ignore.
                if up.startswith("CREATE EXTENSION") or \
                   up.startswith("CREATE INDEX"):
                    return _FakeCursor([])
                # CREATE TABLE IF NOT EXISTS <name>(...)
                m = _re.match(
                    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(",
                    stripped, _re.IGNORECASE)
                if m:
                    self._tables.setdefault(m.group(1), {})
                    return _FakeCursor([])
                # INSERT INTO <name>(...) VALUES (%s, %s::vector, %s::jsonb)
                #   ON CONFLICT (id) DO UPDATE ...
                m = _re.match(
                    r"INSERT\s+INTO\s+(\w+)\s*\(", stripped, _re.IGNORECASE)
                if m and "ON CONFLICT" in up:
                    name = m.group(1)
                    pid, vec_literal, payload_json = params
                    vec = _parse_vec_literal(vec_literal)
                    self._tables.setdefault(name, {})
                    self._tables[name][pid] = (vec, payload_json)
                    return _FakeCursor([])
                # SELECT id, vector <=> %s::vector AS dist, payload FROM ...
                m = _re.match(
                    r"SELECT\s+id,\s+vector\s+<=>\s+%s::vector\s+AS\s+dist,\s+payload\s+FROM\s+(\w+)\s+ORDER\s+BY\s+dist\s+LIMIT\s+%s",
                    stripped, _re.IGNORECASE)
                if m:
                    name = m.group(1)
                    qvec_literal, limit = params
                    qvec = _parse_vec_literal(qvec_literal)
                    rows = []
                    for pid, (vec, payload) in self._tables.get(name, {}).items():
                        if not vec:
                            d = 1.0
                        else:
                            d = _math.sqrt(sum(
                                (float(a) - float(b)) ** 2
                                for a, b in zip(qvec, vec)))
                        rows.append((pid, d, payload))
                    rows.sort(key=lambda r: r[1])
                    return _FakeCursor(rows[:int(limit)])
                # DELETE FROM <name> WHERE id = ANY(%s::text[])
                m = _re.match(
                    r"DELETE\s+FROM\s+(\w+)\s+WHERE\s+id\s+=\s+ANY",
                    stripped, _re.IGNORECASE)
                if m:
                    name = m.group(1)
                    ids = params[0]
                    for pid in ids:
                        self._tables.get(name, {}).pop(pid, None)
                    return _FakeCursor([])
                # SELECT COUNT(*) FROM <name>
                m = _re.match(
                    r"SELECT\s+COUNT\(\*\)\s+FROM\s+(\w+)$",
                    stripped, _re.IGNORECASE)
                if m:
                    name = m.group(1)
                    return _FakeCursor([(len(self._tables.get(name, {})),)])
                # SELECT payload FROM <name>
                m = _re.match(
                    r"SELECT\s+payload\s+FROM\s+(\w+)$",
                    stripped, _re.IGNORECASE)
                if m:
                    name = m.group(1)
                    return _FakeCursor(
                        [(payload,) for (_, payload)
                         in self._tables.get(name, {}).values()])
                raise AssertionError(
                    f"unrecognized SQL in fake psycopg: {sql!r}")

        fake.connect = lambda dsn, autocommit=False: _FakeConn(dsn)
        monkeypatch.setitem(sys.modules, "psycopg", fake)

    def test_upsert_and_search_roundtrip(self, monkeypatch):
        self._inject_fake_psycopg(monkeypatch)
        s = vs.PgVectorStore(dsn="postgresql://test/throughline_test")
        s.ensure_collection("obs", vector_size=3, distance="cosine")
        n = s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"t": "one"}},
            {"id": "b", "vector": [0.4, 0.5, 0.6], "payload": {"t": "two"}},
        ])
        assert n == 2
        hits = s.search("obs", [0.1, 0.2, 0.3], limit=2)
        assert len(hits) == 2
        assert {h["id"] for h in hits} == {"a", "b"}
        assert hits[0]["id"] == "a"
        assert hits[0]["score"] > hits[1]["score"]
        assert hits[0]["payload"] == {"t": "one"}

    def test_upsert_updates_in_place(self, monkeypatch):
        self._inject_fake_psycopg(monkeypatch)
        s = vs.PgVectorStore(dsn="postgresql://test/db")
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"v": 1}},
        ])
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3], "payload": {"v": 2}},
        ])
        assert s.count("obs") == 1
        hits = s.search("obs", [0.1, 0.2, 0.3], limit=5)
        assert hits[0]["payload"] == {"v": 2}

    def test_delete(self, monkeypatch):
        self._inject_fake_psycopg(monkeypatch)
        s = vs.PgVectorStore(dsn="postgresql://test/db")
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3]},
            {"id": "b", "vector": [0.4, 0.5, 0.6]},
        ])
        assert s.count("obs") == 2
        assert s.delete("obs", ["a"]) == 1
        assert s.count("obs") == 1

    def test_search_filter_must_clause(self, monkeypatch):
        self._inject_fake_psycopg(monkeypatch)
        s = vs.PgVectorStore(dsn="postgresql://test/db")
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3],
             "payload": {"knowledge_identity": "universal"}},
            {"id": "b", "vector": [0.2, 0.3, 0.4],
             "payload": {"knowledge_identity": "personal"}},
        ])
        hits = s.search(
            "obs", [0.1, 0.2, 0.3], limit=5,
            filter_={"must": [{"key": "knowledge_identity",
                                "match": {"value": "universal"}}]})
        assert len(hits) == 1
        assert hits[0]["id"] == "a"

    def test_count_with_filter(self, monkeypatch):
        self._inject_fake_psycopg(monkeypatch)
        s = vs.PgVectorStore(dsn="postgresql://test/db")
        s.ensure_collection("obs", 3)
        s.upsert("obs", [
            {"id": "a", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p1"}},
            {"id": "b", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p2"}},
            {"id": "c", "vector": [0.1, 0.2, 0.3],
             "payload": {"pack": "p1"}},
        ])
        assert s.count("obs") == 3
        assert s.count("obs", filter_={
            "must": [{"key": "pack", "match": {"value": "p1"}}]}) == 2

    def test_empty_upsert_and_delete_shortcircuit(self, monkeypatch):
        self._inject_fake_psycopg(monkeypatch)
        s = vs.PgVectorStore(dsn="postgresql://test/db")
        s.ensure_collection("obs", 3)
        assert s.upsert("obs", []) == 0
        assert s.delete("obs", []) == 0

    def test_dsn_precedence_env_then_default(self, monkeypatch):
        self._inject_fake_psycopg(monkeypatch)
        # No explicit DSN, no env var → default
        monkeypatch.delenv("PGVECTOR_DSN", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        s = vs.PgVectorStore()
        assert "throughline" in s.dsn
        # PGVECTOR_DSN takes precedence over DATABASE_URL
        monkeypatch.setenv("PGVECTOR_DSN", "postgresql://pg/specific")
        monkeypatch.setenv("DATABASE_URL", "postgresql://generic/db")
        s2 = vs.PgVectorStore()
        assert s2.dsn == "postgresql://pg/specific"
