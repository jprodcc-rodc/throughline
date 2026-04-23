"""Tests for U12 — embedder backend abstraction.

Covers `rag_server.embedders` (BaseEmbedder, BgeM3Embedder,
OpenAIEmbedder, create_embedder factory + registry).

All tests avoid the real torch / transformers / HTTP stacks — the
contract is what matters, not that we've reinvented bge-m3 in a
fixture. Live model calls are covered by the rag_server smoke tests
(out of scope here).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from rag_server import embedders as emb


# ------- factory + registry -------

class TestCreateEmbedder:
    def test_default_is_bge_m3(self, monkeypatch):
        monkeypatch.delenv("EMBEDDER", raising=False)
        e = emb.create_embedder()
        assert isinstance(e, emb.BgeM3Embedder)
        assert e.name == "bge-m3"
        assert e.vector_size == 1024

    def test_explicit_openai(self):
        e = emb.create_embedder("openai")
        assert isinstance(e, emb.OpenAIEmbedder)
        assert e.name == "openai"

    def test_env_var_respected(self, monkeypatch):
        monkeypatch.setenv("EMBEDDER", "openai")
        e = emb.create_embedder()
        assert e.name == "openai"

    def test_alias_resolves(self):
        """Aliases (jina / voyage / cohere / nomic / minilm) all route
        to a real backend rather than erroring out. The aliases are
        documented as v0.3+ expansion points."""
        for alias in ("jina", "voyage", "cohere"):
            e = emb.create_embedder(alias)
            assert e.name == "openai"  # documented route
        for alias in ("nomic", "minilm"):
            e = emb.create_embedder(alias)
            assert e.name == "bge-m3"

    def test_unknown_raises_with_known_list(self):
        with pytest.raises(ValueError) as ei:
            emb.create_embedder("quantum-magic-embed-9000")
        msg = str(ei.value)
        assert "quantum-magic" in msg
        assert "bge-m3" in msg  # known list included
        assert "openai" in msg

    def test_register_embedder_plugin(self):
        class FakeEmbedder(emb.BaseEmbedder):
            name = "fake"
            vector_size = 32

            def embed(self, texts):
                return [[0.0] * 32 for _ in texts]

        emb.register_embedder("fake", FakeEmbedder)
        try:
            e = emb.create_embedder("fake")
            assert e.name == "fake"
            assert e.vector_size == 32
            assert e.embed(["x", "y"]) == [[0.0] * 32, [0.0] * 32]
        finally:
            # Keep the global registry tidy between tests.
            emb._REGISTRY.pop("fake", None)

    def test_available_lists_everything(self):
        names = set(emb.available_embedders())
        assert {"bge-m3", "openai", "jina", "nomic",
                 "minilm", "voyage", "cohere"}.issubset(names)


# ------- BaseEmbedder contract -------

class TestBaseEmbedderContract:
    def test_bge_m3_has_vector_size(self):
        e = emb.BgeM3Embedder()
        assert e.vector_size == 1024

    def test_openai_default_vector_size(self, monkeypatch):
        monkeypatch.delenv("OPENAI_EMBED_DIM", raising=False)
        e = emb.OpenAIEmbedder()
        assert e.vector_size == 1536  # text-embedding-3-small default

    def test_openai_env_override_vector_size(self, monkeypatch):
        monkeypatch.setenv("OPENAI_EMBED_DIM", "768")
        e = emb.OpenAIEmbedder()
        assert e.vector_size == 768

    def test_empty_input_empty_output_bge(self):
        """Empty-in / empty-out is part of the contract — callers chunk
        in batches and an empty last chunk must not crash."""
        e = emb.BgeM3Embedder()
        # ensure_loaded() would pull torch; but with zero inputs we
        # short-circuit before touching the model.
        assert e.embed([]) == []

    def test_empty_input_empty_output_openai(self):
        e = emb.OpenAIEmbedder()
        assert e.embed([]) == []


# ------- lazy torch import -------

class TestLazyImport:
    def test_create_openai_does_not_load_torch(self, monkeypatch):
        """Instantiating the openai embedder must NOT trigger a
        torch import — users on Cloud-max should not pay the torch
        import tax."""
        # Simulate a torchless environment by blocking the import.
        import builtins
        real_import = builtins.__import__

        def guard(name, *a, **kw):
            if name == "torch" or name.startswith("torch."):
                raise ImportError("torch intentionally blocked in this test")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        # Creating + embedding should work (empty-in shortcut).
        e = emb.OpenAIEmbedder()
        assert e.embed([]) == []


# ------- OpenAIEmbedder HTTP mocking -------

class TestOpenAIEmbedderHTTP:
    def test_posts_to_embeddings_endpoint(self, monkeypatch):
        captured = {}

        class FakeResponse:
            def __init__(self, body):
                self._body = body

            def read(self):
                return self._body

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["headers"] = dict(req.header_items())
            body = req.data
            import json as _j
            captured["payload"] = _j.loads(body.decode("utf-8"))
            return FakeResponse(_j.dumps({
                "data": [
                    {"embedding": [0.1, 0.2, 0.3] + [0.0] * 1533},
                    {"embedding": [0.4, 0.5, 0.6] + [0.0] * 1533},
                ],
            }).encode("utf-8"))

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        e = emb.OpenAIEmbedder(model="text-embedding-3-small",
                                base_url="https://example.test/v1",
                                api_key="sk-test")
        out = e.embed(["hello", "world"])
        assert len(out) == 2
        assert len(out[0]) == 1536
        assert captured["url"].endswith("/embeddings")
        assert captured["method"] == "POST"
        # Authorization header carries the bearer token.
        auth = dict((k.lower(), v) for k, v in captured["headers"].items())
        assert auth.get("authorization") == "Bearer sk-test"
        assert captured["payload"]["model"] == "text-embedding-3-small"
        assert captured["payload"]["input"] == ["hello", "world"]


# ------- ingest_qdrant VECTOR_SIZE integration -------

class TestIngestVectorSize:
    def test_env_override_wins(self, monkeypatch, tmp_path):
        """INGEST_VECTOR_SIZE is still honoured so users stuck on
        non-standard models can force a size."""
        # _resolve_vector_size is module-private; exec it via import.
        monkeypatch.setenv("INGEST_VECTOR_SIZE", "768")
        # Stub VAULT_PATH so the ingest module doesn't sys.exit on
        # import; we just need the resolver function, not the main
        # entrypoint.
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        # Re-import a fresh instance of the helper. To avoid running
        # the whole module, we pull out the function directly via a
        # subprocess-like boundary — easier: reload then read.
        if "scripts.ingest_qdrant" in sys.modules:
            del sys.modules["scripts.ingest_qdrant"]
        mod = __import__("scripts.ingest_qdrant",
                         fromlist=["_resolve_vector_size"])
        assert mod._resolve_vector_size() == 768

    def test_falls_back_to_embedder_vector_size(self, monkeypatch, tmp_path):
        monkeypatch.delenv("INGEST_VECTOR_SIZE", raising=False)
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        monkeypatch.setenv("EMBEDDER", "openai")
        monkeypatch.setenv("OPENAI_EMBED_DIM", "2048")
        if "scripts.ingest_qdrant" in sys.modules:
            del sys.modules["scripts.ingest_qdrant"]
        mod = __import__("scripts.ingest_qdrant",
                         fromlist=["_resolve_vector_size"])
        assert mod._resolve_vector_size() == 2048
