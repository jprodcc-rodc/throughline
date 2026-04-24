"""Tests that rag_server.py actually uses the U12 / U20 abstractions.

Before this wiring, rag_server had bge-m3 + bge-reranker-v2-m3
hard-coded; EMBEDDER / RERANKER env vars from the wizard were
ignored. This test proves the env vars flip the backend end-to-end
(module import → EMBEDDER / RERANKER globals → endpoint handlers).

No live transformers / Cohere / OpenAI calls — the abstractions
(tested in test_embedders.py / test_rerankers.py) guarantee
call-through; here we only verify the wiring.
"""
from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


def _fresh_import_rag_server():
    """Re-import rag_server.rag_server so a preceding test's env
    vars don't leak into module-level state."""
    for key in list(sys.modules.keys()):
        if key.startswith("rag_server"):
            del sys.modules[key]
    import rag_server.rag_server as r
    return r


class TestEmbedderWiring:
    def test_default_is_bge_m3(self, monkeypatch):
        monkeypatch.delenv("EMBEDDER", raising=False)
        monkeypatch.delenv("RERANKER", raising=False)
        r = _fresh_import_rag_server()
        assert r.EMBEDDER.name == "bge-m3"
        assert r.EMBEDDER.vector_size == 1024

    def test_embedder_env_var_flips_backend(self, monkeypatch):
        monkeypatch.setenv("EMBEDDER", "openai")
        monkeypatch.setenv("RERANKER", "skip")
        r = _fresh_import_rag_server()
        assert r.EMBEDDER.name == "openai"
        assert r.EMBEDDER.vector_size == 1536

    def test_reranker_env_var_flips_backend(self, monkeypatch):
        monkeypatch.setenv("EMBEDDER", "openai")  # avoid torch load
        monkeypatch.setenv("RERANKER", "cohere")
        r = _fresh_import_rag_server()
        assert r.RERANKER.name == "cohere"

    def test_skip_reranker_flips(self, monkeypatch):
        monkeypatch.setenv("EMBEDDER", "openai")
        monkeypatch.setenv("RERANKER", "skip")
        r = _fresh_import_rag_server()
        assert r.RERANKER.name == "skip"

    def test_import_is_cheap(self, monkeypatch):
        """Instantiation must not trigger a model load. Otherwise a
        misconfigured server crashes at import before we can surface
        a helpful error, and CI spends 30s per test."""
        monkeypatch.setenv("EMBEDDER", "bge-m3")  # heaviest option
        monkeypatch.setenv("RERANKER", "bge-reranker-v2-m3")
        r = _fresh_import_rag_server()
        # The embedder/reranker instances exist but should NOT have
        # loaded the actual torch models yet.
        assert r.EMBEDDER._model is None
        assert r.RERANKER._model is None


class TestVectorStoreWiring:
    def test_default_is_qdrant(self, monkeypatch):
        monkeypatch.delenv("VECTOR_STORE", raising=False)
        monkeypatch.setenv("EMBEDDER", "openai")  # skip torch
        r = _fresh_import_rag_server()
        assert r.VECTOR_STORE.name == "qdrant"

    def test_env_var_flips_backend(self, monkeypatch):
        monkeypatch.setenv("EMBEDDER", "openai")
        monkeypatch.setenv("VECTOR_STORE", "chroma")
        r = _fresh_import_rag_server()
        assert r.VECTOR_STORE.name == "chroma"

    def test_alias_routes_through(self, monkeypatch):
        """pgvector / duckdb_vss / sqlite_vec should not crash the
        import — they alias to qdrant until v0.3 ships the real impls.
        (lancedb shipped as a real impl in v0.2.x.)"""
        monkeypatch.setenv("EMBEDDER", "openai")
        monkeypatch.setenv("VECTOR_STORE", "pgvector")
        r = _fresh_import_rag_server()
        assert r.VECTOR_STORE.name == "qdrant"


class TestRagDeviceRespected:
    """The legacy RAG_DEVICE env var must still route through to both
    the bge embedder and bge reranker so existing deployments don't
    silently lose device pinning after this refactor."""

    def test_device_passed_through_embedder(self, monkeypatch):
        monkeypatch.setenv("EMBEDDER", "bge-m3")
        monkeypatch.setenv("RAG_DEVICE", "cpu")
        from rag_server.embedders import BgeM3Embedder
        e = BgeM3Embedder()
        assert e.device_override == "cpu"

    def test_device_passed_through_reranker(self, monkeypatch):
        monkeypatch.setenv("RERANKER", "bge-reranker-v2-m3")
        monkeypatch.setenv("RAG_DEVICE", "cuda")
        from rag_server.rerankers import BgeRerankerV2M3
        r = BgeRerankerV2M3()
        assert r.device_override == "cuda"
