"""Phase 1 Week 2 commit 3 — recall_memory real-logic tests.

Covers:
- rag_client.search: payload construction, response parsing, error
  paths (unreachable / non-200 / malformed JSON / server-side error)
- recall_memory tool: success path + error paths, response mapping,
  domain_filter, personal_context surfacing, include_personal_context
- helper functions: domain extraction + axis-tag exclusion + filter
  matching

All tests mock urllib at the boundary so they're fast + offline.
"""
from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError

import pytest


# ---------- helpers ----------

class TestDomainHelpers:
    """The X/Y/Z axis tag scheme: domain tags vs y/* (form) and z/*
    (relation) axis tags."""

    def test_extract_domain_first_non_axis(self):
        from mcp_server.tools.recall_memory import _extract_domain

        assert (
            _extract_domain(["Health/Biohack", "y/Mechanism", "z/Node"])
            == "Health/Biohack"
        )

    def test_extract_domain_empty_when_only_axis(self):
        from mcp_server.tools.recall_memory import _extract_domain

        assert _extract_domain(["y/SOP", "z/Boundary"]) == ""

    def test_extract_domain_empty_when_no_tags(self):
        from mcp_server.tools.recall_memory import _extract_domain

        assert _extract_domain([]) == ""

    def test_matches_domain_exact(self):
        from mcp_server.tools.recall_memory import _matches_domain

        assert _matches_domain(["Health/Biohack", "y/Mechanism"], "Health/Biohack")

    def test_matches_domain_prefix(self):
        from mcp_server.tools.recall_memory import _matches_domain

        # 'Health' matches 'Health/Biohack' via prefix
        assert _matches_domain(["Health/Biohack"], "Health")

    def test_matches_domain_no_match(self):
        from mcp_server.tools.recall_memory import _matches_domain

        assert not _matches_domain(["Tech/AI"], "Health")

    def test_matches_domain_partial_no_false_positive(self):
        """'Health' should NOT match 'HealthNot/X' (prefix needs / boundary)."""
        from mcp_server.tools.recall_memory import _matches_domain

        # Domain 'HealthNot' starts with 'Health' as a string but
        # isn't 'Health' or 'Health/X' — match should fail.
        assert not _matches_domain(["HealthNot/X"], "Health")


# ---------- rag_client (boundary tests via urllib mock) ----------

def _fake_urlopen_response(body: dict, status: int = 200):
    """Build a mock urlopen response context manager."""
    payload = json.dumps(body).encode("utf-8")
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = payload
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestRAGClientSearch:
    def test_success_returns_response_dict(self):
        from mcp_server.rag_client import search

        fake = _fake_urlopen_response({
            "results": [
                {"title": "Card A", "tags": ["Health/Biohack"], "final_score": 0.9},
            ],
            "total_candidates": 1,
        })
        with patch("urllib.request.urlopen", return_value=fake):
            result = search(query="test query", limit=5)
        assert "results" in result
        assert result["total_candidates"] == 1
        assert result["results"][0]["title"] == "Card A"

    def test_payload_includes_query_and_top_k(self):
        from mcp_server.rag_client import search

        fake = _fake_urlopen_response({"results": []})
        with patch("urllib.request.urlopen", return_value=fake) as mocked:
            search(query="hello", limit=7)
        # urlopen was called with a Request — check its data
        call_args = mocked.call_args
        req = call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        assert body["query"] == "hello"
        assert body["top_k"] == 7

    def test_pp_boost_passed_through(self):
        from mcp_server.rag_client import search

        fake = _fake_urlopen_response({"results": []})
        with patch("urllib.request.urlopen", return_value=fake) as mocked:
            search(query="hi", pp_boost=1.0)
        body = json.loads(mocked.call_args[0][0].data.decode("utf-8"))
        assert body["pp_boost"] == 1.0

    def test_pp_boost_omitted_when_none(self):
        from mcp_server.rag_client import search

        fake = _fake_urlopen_response({"results": []})
        with patch("urllib.request.urlopen", return_value=fake) as mocked:
            search(query="hi", pp_boost=None)
        body = json.loads(mocked.call_args[0][0].data.decode("utf-8"))
        assert "pp_boost" not in body

    def test_empty_query_raises(self):
        from mcp_server.rag_client import search

        with pytest.raises(ValueError):
            search(query="")

    def test_unreachable_server_raises_typed(self):
        from mcp_server.rag_client import RAGServerUnreachable, search

        with patch(
            "urllib.request.urlopen",
            side_effect=URLError("Connection refused"),
        ):
            with pytest.raises(RAGServerUnreachable) as exc_info:
                search(query="hi")
        assert "rag_server unreachable" in str(exc_info.value).lower()

    def test_malformed_json_raises_typed(self):
        from mcp_server.rag_client import RAGResponseMalformed, search

        bad_resp = MagicMock()
        bad_resp.status = 200
        bad_resp.read.return_value = b"not json {{"
        bad_resp.__enter__ = MagicMock(return_value=bad_resp)
        bad_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=bad_resp):
            with pytest.raises(RAGResponseMalformed):
                search(query="hi")

    def test_missing_results_field_raises_typed(self):
        from mcp_server.rag_client import RAGResponseMalformed, search

        fake = _fake_urlopen_response({"foo": "bar"})  # no 'results'
        with patch("urllib.request.urlopen", return_value=fake):
            with pytest.raises(RAGResponseMalformed):
                search(query="hi")

    def test_server_side_error_field_raises_typed(self):
        from mcp_server.rag_client import RAGServerError, search

        fake = _fake_urlopen_response({
            "results": [],
            "error": "vector search failed: connection lost",
        })
        with patch("urllib.request.urlopen", return_value=fake):
            with pytest.raises(RAGServerError) as exc_info:
                search(query="hi")
        assert "vector search failed" in str(exc_info.value)


# ---------- recall_memory tool ----------

class TestRecallMemoryTool:
    def test_success_maps_response_to_mcp_shape(self):
        from mcp_server.tools import recall_memory

        fake = _fake_urlopen_response({
            "results": [
                {
                    "title": "Keto rebound",
                    "knowledge_identity": "personal_persistent",
                    "tags": ["Health/Biohack", "y/Mechanism"],
                    "date": "2026-04-02",
                    "body_preview": "short",
                    "body_full": "full body text here",
                    "final_score": 0.87,
                },
            ],
            "total_candidates": 1,
        })
        with patch("urllib.request.urlopen", return_value=fake):
            result = recall_memory(query="keto")

        assert result["_status"] == "ok"
        assert len(result["cards"]) == 1
        card = result["cards"][0]
        assert card["title"] == "Keto rebound"
        assert card["content"] == "full body text here"
        assert card["domain"] == "Health/Biohack"
        assert card["date"] == "2026-04-02"
        assert card["score"] == 0.87
        assert result["total_matched"] == 1

    def test_falls_back_to_body_preview_when_no_full(self):
        from mcp_server.tools import recall_memory

        fake = _fake_urlopen_response({
            "results": [
                {"title": "T", "tags": [], "body_preview": "preview only"},
            ],
            "total_candidates": 1,
        })
        with patch("urllib.request.urlopen", return_value=fake):
            result = recall_memory(query="q")
        assert result["cards"][0]["content"] == "preview only"

    def test_empty_query_returns_error(self):
        from mcp_server.tools import recall_memory

        result = recall_memory(query="")
        assert result["_status"] == "error"
        assert "non-empty" in result["_message"].lower()

    def test_unreachable_rag_server_returns_error_with_hint(self):
        from mcp_server.tools import recall_memory

        with patch(
            "urllib.request.urlopen",
            side_effect=URLError("Connection refused"),
        ):
            result = recall_memory(query="hi")
        assert result["_status"] == "error"
        assert "rag_server" in result["_message"].lower()

    def test_server_error_field_returns_error(self):
        from mcp_server.tools import recall_memory

        fake = _fake_urlopen_response({
            "results": [],
            "error": "embedding failed",
        })
        with patch("urllib.request.urlopen", return_value=fake):
            result = recall_memory(query="hi")
        assert result["_status"] == "error"
        assert "embedding failed" in result["_message"]

    def test_domain_filter_excludes_non_matching(self):
        from mcp_server.tools import recall_memory

        fake = _fake_urlopen_response({
            "results": [
                {"title": "Health card", "tags": ["Health/Biohack"], "body_preview": "h"},
                {"title": "Tech card", "tags": ["Tech/AI"], "body_preview": "t"},
            ],
            "total_candidates": 2,
        })
        with patch("urllib.request.urlopen", return_value=fake):
            result = recall_memory(query="hi", domain_filter="Health")
        titles = [c["title"] for c in result["cards"]]
        assert "Health card" in titles
        assert "Tech card" not in titles

    def test_include_personal_context_concatenates_pp_cards(self):
        from mcp_server.tools import recall_memory

        fake = _fake_urlopen_response({
            "results": [
                {
                    "title": "Allergies",
                    "knowledge_identity": "personal_persistent",
                    "tags": ["Health/Profile"],
                    "body_preview": "Allergic to penicillin.",
                },
                {
                    "title": "Generic fact",
                    "knowledge_identity": "universal",
                    "tags": ["Health/Biohack"],
                    "body_preview": "Generic body.",
                },
            ],
            "total_candidates": 2,
        })
        with patch("urllib.request.urlopen", return_value=fake) as mocked:
            result = recall_memory(query="hi", include_personal_context=True)

        # personal_context should contain only the PP card body
        assert result["personal_context"] is not None
        assert "Allergic to penicillin" in result["personal_context"]
        assert "Generic body" not in result["personal_context"]

        # pp_boost should have been passed to rag_server
        body = json.loads(mocked.call_args[0][0].data.decode("utf-8"))
        assert body["pp_boost"] == 1.0

    def test_include_personal_context_false_omits_pp_boost(self):
        """Locked decision Q1: default False, no pp_boost in payload."""
        from mcp_server.tools import recall_memory

        fake = _fake_urlopen_response({"results": [], "total_candidates": 0})
        with patch("urllib.request.urlopen", return_value=fake) as mocked:
            recall_memory(query="hi")  # default include_personal_context=False
        body = json.loads(mocked.call_args[0][0].data.decode("utf-8"))
        assert "pp_boost" not in body

    def test_personal_context_is_none_when_no_pp_cards(self):
        from mcp_server.tools import recall_memory

        fake = _fake_urlopen_response({
            "results": [
                {"title": "Card", "knowledge_identity": "universal",
                 "tags": [], "body_preview": "x"},
            ],
            "total_candidates": 1,
        })
        with patch("urllib.request.urlopen", return_value=fake):
            result = recall_memory(query="hi", include_personal_context=True)
        assert result["personal_context"] is None

    def test_limit_passed_through_as_top_k(self):
        from mcp_server.tools import recall_memory

        fake = _fake_urlopen_response({"results": [], "total_candidates": 0})
        with patch("urllib.request.urlopen", return_value=fake) as mocked:
            recall_memory(query="hi", limit=12)
        body = json.loads(mocked.call_args[0][0].data.decode("utf-8"))
        assert body["top_k"] == 12

    def test_default_limit_is_5(self):
        from mcp_server.tools import recall_memory

        fake = _fake_urlopen_response({"results": [], "total_candidates": 0})
        with patch("urllib.request.urlopen", return_value=fake) as mocked:
            recall_memory(query="hi")
        body = json.loads(mocked.call_args[0][0].data.decode("utf-8"))
        assert body["top_k"] == 5
