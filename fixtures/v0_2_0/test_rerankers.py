"""Tests for U20 — reranker backend abstraction."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from rag_server import rerankers as rr


# ------- factory + registry -------

class TestCreateReranker:
    def test_default_is_bge(self, monkeypatch):
        monkeypatch.delenv("RERANKER", raising=False)
        r = rr.create_reranker()
        assert isinstance(r, rr.BgeRerankerV2M3)

    def test_explicit_skip(self):
        r = rr.create_reranker("skip")
        assert isinstance(r, rr.SkipReranker)

    def test_explicit_cohere(self):
        r = rr.create_reranker("cohere")
        assert isinstance(r, rr.CohereReranker)

    def test_env_var(self, monkeypatch):
        monkeypatch.setenv("RERANKER", "cohere")
        assert rr.create_reranker().name == "cohere"

    def test_alias_none_means_skip(self):
        r = rr.create_reranker("none")
        assert isinstance(r, rr.SkipReranker)

    def test_voyage_and_jina_route_to_cohere(self):
        """Documented v0.3 expansion points: Voyage and Jina both
        share the Cohere rerank schema, so they route to the Cohere
        impl for now."""
        for alias in ("voyage", "jina"):
            assert rr.create_reranker(alias).name == "cohere"

    def test_bge_gemma_alias_routes_to_m3(self):
        r = rr.create_reranker("bge-reranker-v2-gemma")
        assert r.name == "bge-reranker-v2-m3"

    def test_unknown_raises(self):
        with pytest.raises(ValueError) as ei:
            rr.create_reranker("magic-rerank-9000")
        msg = str(ei.value)
        assert "magic-rerank" in msg
        assert "skip" in msg
        assert "cohere" in msg

    def test_register_plugin(self):
        class Fake(rr.BaseReranker):
            name = "fake"

            def rerank(self, q, docs):
                return [1.0] * len(docs)

        rr.register_reranker("fake", Fake)
        try:
            r = rr.create_reranker("fake")
            assert r.rerank("q", ["a", "b", "c"]) == [1.0, 1.0, 1.0]
        finally:
            rr._REGISTRY.pop("fake", None)


# ------- SkipReranker -------

class TestSkipReranker:
    def test_empty_input(self):
        assert rr.SkipReranker().rerank("q", []) == []

    def test_monotonic_descending(self):
        """Output scores must sort the documents back to original
        order when descending-sorted (= no reranking)."""
        docs = ["a", "b", "c", "d"]
        scores = rr.SkipReranker().rerank("q", docs)
        pairs = sorted(zip(scores, docs), reverse=True)
        assert [d for _, d in pairs] == docs

    def test_length_matches_input(self):
        assert len(rr.SkipReranker().rerank("q", ["x"] * 7)) == 7


# ------- CohereReranker HTTP path -------

class TestCohereReranker:
    def test_empty_input_skips_http(self, monkeypatch):
        def guard(*a, **k):
            raise AssertionError("must not call HTTP on empty input")
        monkeypatch.setattr("urllib.request.urlopen", guard)
        assert rr.CohereReranker(api_key="k").rerank("q", []) == []

    def test_no_api_key_falls_back_to_skip(self, monkeypatch):
        monkeypatch.delenv("COHERE_API_KEY", raising=False)

        def guard(*a, **k):
            raise AssertionError("must not call HTTP without key")
        monkeypatch.setattr("urllib.request.urlopen", guard)
        out = rr.CohereReranker().rerank("q", ["a", "b", "c"])
        # SkipReranker output: descending monotonic.
        assert len(out) == 3
        assert out[0] > out[1] > out[2]

    def test_realigns_to_input_order(self, monkeypatch):
        """Cohere returns results potentially reordered; our reranker
        must place scores back into the INPUT positions so downstream
        code can zip(docs, scores) without surprises."""
        captured = {}

        class FakeResp:
            def __init__(self, body):
                self._b = body

            def read(self):
                return self._b

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["payload"] = json.loads(req.data.decode("utf-8"))
            # Cohere returns re-ordered by relevance. Docs were
            # [a, b, c, d]; pretend c is best, then a, then d, then b.
            return FakeResp(json.dumps({"results": [
                {"index": 2, "relevance_score": 0.95},
                {"index": 0, "relevance_score": 0.80},
                {"index": 3, "relevance_score": 0.40},
                {"index": 1, "relevance_score": 0.10},
            ]}).encode("utf-8"))

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        r = rr.CohereReranker(api_key="sk-test")
        scores = r.rerank("q", ["a", "b", "c", "d"])
        assert scores == [0.80, 0.10, 0.95, 0.40]
        # Payload shape sanity.
        assert captured["payload"]["model"].startswith("rerank-")
        assert captured["payload"]["query"] == "q"
        assert captured["payload"]["documents"] == ["a", "b", "c", "d"]

    def test_partial_results_preserved_zeroes(self, monkeypatch):
        """If Cohere returns fewer results than docs (shouldn't happen,
        but API contracts can drift), missing indices default to 0.0 so
        the output is still well-formed."""

        class FakeResp:
            def __init__(self, body):
                self._b = body

            def read(self):
                return self._b

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=None: FakeResp(json.dumps({
                "results": [{"index": 1, "relevance_score": 0.7}],
            }).encode("utf-8")),
        )
        r = rr.CohereReranker(api_key="k")
        scores = r.rerank("q", ["a", "b", "c"])
        assert scores == [0.0, 0.7, 0.0]


# ------- lazy torch import -------

class TestLazyImport:
    def test_skip_no_torch(self, monkeypatch):
        """SkipReranker is instantiated + used even when torch is
        missing. Users on minimal CPU deployments need this path."""
        import builtins
        real = builtins.__import__

        def guard(name, *a, **kw):
            if name == "torch" or name.startswith("torch."):
                raise ImportError("torch blocked for this test")
            return real(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        r = rr.create_reranker("skip")
        assert r.rerank("q", ["a"]) == [1.0]

    def test_cohere_no_torch(self, monkeypatch):
        import builtins
        real = builtins.__import__

        def guard(name, *a, **kw):
            if name == "torch" or name.startswith("torch."):
                raise ImportError("torch blocked for this test")
            return real(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", guard)
        r = rr.CohereReranker(api_key="")  # no key → skip fallback
        assert r.rerank("q", ["a", "b"])  # doesn't raise


# ------- available_rerankers -------

class TestAvailableList:
    def test_lists_primaries_and_aliases(self):
        names = set(rr.available_rerankers())
        # Primary registry.
        assert {"bge-reranker-v2-m3", "cohere", "skip"}.issubset(names)
        # Aliases.
        assert {"bge", "bge-reranker", "voyage", "jina", "none",
                 "bge-reranker-v2-gemma"}.issubset(names)
