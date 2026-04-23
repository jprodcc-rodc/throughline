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
        """v0.3 expansion points route to Qdrant for now. The wizard
        can list them; the user can pick them without crashing."""
        for alias in ("lancedb", "duckdb_vss", "duckdb-vss",
                       "sqlite_vec", "sqlite-vec", "pgvector", "none"):
            s = vs.create_vector_store(alias)
            assert s.name == "qdrant", f"{alias} failed to resolve"

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
        assert {"qdrant", "chroma"}.issubset(names)
        assert {"lancedb", "duckdb_vss", "sqlite_vec",
                 "pgvector", "none"}.issubset(names)


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
