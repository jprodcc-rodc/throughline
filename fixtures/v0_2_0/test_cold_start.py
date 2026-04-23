"""Tests for U1 cold-start status line in the OpenWebUI Filter.

Covers:
- _cold_start_badge returns the right emoji + threshold language per
  count bucket (0 / 1-49 / 50-199 / 200+).
- _fetch_card_count caches across calls and honours TTL expiry.
- _fetch_card_count returns None on Qdrant errors (never raises).
- inlet emits cold-start status when appropriate and short-circuits
  retrieval at < warm threshold.
- inlet does NOT emit cold-start status for warm / full collections.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

# Load Filter module by spec (keeps us from requiring filter.py to be a
# proper package member).
FILTER_PATH = REPO_ROOT / "filter" / "openwebui_filter.py"


@pytest.fixture(scope="module")
def filter_mod():
    spec = importlib.util.spec_from_file_location("openwebui_filter", FILTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def fresh_filter(filter_mod):
    f = filter_mod.Filter()
    # Ensure a clean cache between tests.
    type(f)._CARD_COUNT_CACHE.clear()
    return f


# ========== badge mapping ==========

class TestColdStartBadge:
    def test_zero_cards_shows_cold(self, fresh_filter):
        b = fresh_filter._cold_start_badge(0)
        assert b is not None
        assert "cold start" in b
        assert "0 cards" in b
        assert "🌱" in b

    def test_below_warm_shows_cold(self, fresh_filter):
        b = fresh_filter._cold_start_badge(25)
        assert "cold start" in b
        assert "25 cards" in b

    def test_warm_range_shows_ramping(self, fresh_filter):
        b = fresh_filter._cold_start_badge(100)
        assert "ramping" in b
        assert "100 cards" in b
        assert "🌿" in b

    def test_at_full_threshold_is_none(self, fresh_filter):
        """At COLD_START_THRESHOLD_FULL (200) the flywheel is warm
        enough that the normal status line applies — cold-start returns
        None so the inlet skips the pre-flight emission."""
        assert fresh_filter._cold_start_badge(200) is None

    def test_beyond_full_is_none(self, fresh_filter):
        assert fresh_filter._cold_start_badge(5000) is None

    def test_at_warm_threshold_flips_to_ramping(self, fresh_filter):
        """Boundary: exactly COLD_START_THRESHOLD_WARM is ramping, not cold."""
        assert "ramping" in fresh_filter._cold_start_badge(50)


# ========== card-count probe ==========

class _FakeResp:
    def __init__(self, body):
        self._body = body
    def read(self):
        return self._body
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False


class TestFetchCardCount:
    def test_cache_hit_skips_http(self, fresh_filter, filter_mod):
        collection = fresh_filter.valves.QDRANT_COLLECTION
        fresh_filter._CARD_COUNT_CACHE[collection] = (42, time.monotonic())
        with patch.object(filter_mod.urllib.request, "urlopen") as opener:
            n = fresh_filter._fetch_card_count()
        assert n == 42
        opener.assert_not_called()

    def test_http_success_caches(self, fresh_filter, filter_mod):
        body = json.dumps({"result": {"count": 7}}).encode("utf-8")
        with patch.object(filter_mod.urllib.request, "urlopen",
                          return_value=_FakeResp(body)):
            n = fresh_filter._fetch_card_count()
        assert n == 7
        collection = fresh_filter.valves.QDRANT_COLLECTION
        assert fresh_filter._CARD_COUNT_CACHE[collection][0] == 7

    def test_http_error_returns_none(self, fresh_filter, filter_mod):
        def boom(*a, **kw):
            import urllib.error
            raise urllib.error.URLError("no qdrant")
        with patch.object(filter_mod.urllib.request, "urlopen", boom):
            assert fresh_filter._fetch_card_count() is None

    def test_malformed_response_returns_none(self, fresh_filter, filter_mod):
        body = json.dumps({"result": {"approximation": 10}}).encode("utf-8")
        with patch.object(filter_mod.urllib.request, "urlopen",
                          return_value=_FakeResp(body)):
            assert fresh_filter._fetch_card_count() is None

    def test_ttl_expiry_refetches(self, fresh_filter, filter_mod):
        collection = fresh_filter.valves.QDRANT_COLLECTION
        fresh_filter._CARD_COUNT_CACHE[collection] = (1, time.monotonic() - 600)
        body = json.dumps({"result": {"count": 999}}).encode("utf-8")
        with patch.object(filter_mod.urllib.request, "urlopen",
                          return_value=_FakeResp(body)):
            n = fresh_filter._fetch_card_count()
        assert n == 999


# ========== inlet integration ==========

class TestInletColdStart:
    """End-to-end: inlet emits cold-start status when card count is low
    AND short-circuits retrieval. For warm/full collections, no
    cold-start status is emitted."""

    async def _run_inlet(self, filter_obj, body, emitted):
        async def _capture(ev):
            emitted.append(ev)
        return await filter_obj.inlet(body, __event_emitter__=_capture)

    def test_cold_count_emits_and_shortcircuits(self, fresh_filter):
        import asyncio
        collection = fresh_filter.valves.QDRANT_COLLECTION
        fresh_filter._CARD_COUNT_CACHE[collection] = (0, time.monotonic())
        emitted = []
        body = {"messages": [{"role": "user", "content": "hello?"}],
                "chat_id": "x"}
        asyncio.run(self._run_inlet(fresh_filter, body, emitted))
        assert any(
            ev["type"] == "status"
            and "cold start" in ev["data"]["description"]
            for ev in emitted
        )

    def test_ramping_emits_but_does_not_shortcircuit(self, fresh_filter):
        import asyncio
        collection = fresh_filter.valves.QDRANT_COLLECTION
        fresh_filter._CARD_COUNT_CACHE[collection] = (100, time.monotonic())
        emitted = []
        body = {"messages": [{"role": "user", "content": "hello?"}],
                "chat_id": "x"}
        asyncio.run(self._run_inlet(fresh_filter, body, emitted))
        # Ramping status must fire.
        assert any(
            "ramping" in ev["data"].get("description", "")
            for ev in emitted
        )

    def test_warm_count_no_coldstart_emission(self, fresh_filter):
        import asyncio
        collection = fresh_filter.valves.QDRANT_COLLECTION
        fresh_filter._CARD_COUNT_CACHE[collection] = (500, time.monotonic())
        emitted = []
        body = {"messages": [{"role": "user", "content": "hello?"}],
                "chat_id": "x"}
        asyncio.run(self._run_inlet(fresh_filter, body, emitted))
        # Cold-start prefix must NOT appear.
        for ev in emitted:
            d = ev.get("data", {}).get("description", "")
            assert "cold start" not in d
            assert "ramping" not in d

    def test_disabled_valve_skips_probe(self, fresh_filter):
        """COLD_START_ENABLED=False must skip even when count is 0."""
        import asyncio
        fresh_filter.valves.COLD_START_ENABLED = False
        collection = fresh_filter.valves.QDRANT_COLLECTION
        fresh_filter._CARD_COUNT_CACHE[collection] = (0, time.monotonic())
        emitted = []
        body = {"messages": [{"role": "user", "content": "hello?"}],
                "chat_id": "x"}
        asyncio.run(self._run_inlet(fresh_filter, body, emitted))
        for ev in emitted:
            assert "cold start" not in ev.get("data", {}).get("description", "")
