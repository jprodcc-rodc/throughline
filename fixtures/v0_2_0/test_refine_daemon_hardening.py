"""Hardening tests against bugs surfaced by the 2026-04-26
edge-case audit:

1. `_normalize_for_prefix_check` — defense-in-depth against path
   tricks that could let a card slip past the forbidden-prefix
   denylist into Qdrant. `..`, `./`, mixed slashes, and case
   variants on case-insensitive filesystems are all covered.
2. `_record_cost` — clamps negative / None token counts so a
   flaky provider's bad usage payload can't underflow the
   daily-budget check.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# _normalize_for_prefix_check
# ============================================================

class TestNormalizeForPrefixCheck:
    def test_passthrough_simple(self):
        from daemon.refine_daemon import _normalize_for_prefix_check
        assert _normalize_for_prefix_check("00_Buffer/foo.md") in (
            "00_buffer/foo.md", "00_Buffer/foo.md")  # case-dep on OS

    def test_collapses_dot_dot(self):
        """`..` traversal must NOT slip past a forbidden prefix."""
        from daemon.refine_daemon import _normalize_for_prefix_check
        cleaned = _normalize_for_prefix_check(
            "harmless/../00_Buffer/Private/secret.md")
        # After normpath, the `..` collapses with `harmless`.
        assert "00_buffer" in cleaned.lower()
        assert ".." not in cleaned

    def test_collapses_leading_dot_slash(self):
        """`./` prefix must not break the startswith check."""
        from daemon.refine_daemon import _normalize_for_prefix_check
        cleaned = _normalize_for_prefix_check("./00_Buffer/Private/x.md")
        assert "00_buffer" in cleaned.lower()
        assert not cleaned.startswith("./")

    def test_swaps_backslashes(self):
        from daemon.refine_daemon import _normalize_for_prefix_check
        cleaned = _normalize_for_prefix_check("00_Buffer\\Private\\x.md")
        assert "/" in cleaned
        assert "\\" not in cleaned

    def test_lowercases_on_windows(self):
        """On Windows + macOS, the test path must be lower-cased so
        a `00_buffer/private/x.md` doesn't slip past a `00_Buffer/Private`
        prefix on a case-insensitive filesystem."""
        if not (os.name == "nt" or sys.platform == "darwin"):
            pytest.skip("case-insensitivity check is OS-specific")
        from daemon.refine_daemon import _normalize_for_prefix_check
        cleaned = _normalize_for_prefix_check("00_BUFFER/PRIVATE/x.md")
        assert cleaned == "00_buffer/private/x.md"

    def test_strips_leading_slash(self):
        from daemon.refine_daemon import _normalize_for_prefix_check
        cleaned = _normalize_for_prefix_check("/00_Buffer/x.md")
        assert not cleaned.startswith("/")


class TestForbiddenPrefixIntegration:
    """End-to-end: a path that LOOKS like it should slip past the
    denylist (via `..`, mixed case, or `./`) is still blocked."""

    def test_dot_dot_path_blocked(self, monkeypatch, tmp_path):
        # Set up a forbidden-prefixes file with `00_Buffer/Private`.
        prefixes_json = tmp_path / "forbidden.json"
        prefixes_json.write_text(
            json.dumps(["00_Buffer/Private"]),
            encoding="utf-8",
        )
        monkeypatch.setenv("THROUGHLINE_FORBIDDEN_PREFIXES_JSON",
                            str(prefixes_json))
        # Reload daemon so it picks up the new env var at module load.
        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        # Force the upsert path on (env-controlled).
        monkeypatch.setattr(rd, "QDRANT_UPSERT_ENABLED", True)
        # Capture log lines so we can assert the FORBIDDEN block fired.
        captured = []
        monkeypatch.setattr(rd, "log", lambda m: captured.append(m))

        # Try `..` traversal.
        result = rd._upsert_note_to_qdrant(
            rel_path="harmless/../00_Buffer/Private/leak.md",
            title="X", body_full="b",
            knowledge_identity="universal",
            tags=[], source_conversation_id="c1",
        )
        assert result is False
        assert any("FORBIDDEN" in m for m in captured)

    def test_leading_dot_slash_blocked(self, monkeypatch, tmp_path):
        prefixes_json = tmp_path / "forbidden.json"
        prefixes_json.write_text(
            json.dumps(["00_Buffer/Private"]),
            encoding="utf-8",
        )
        monkeypatch.setenv("THROUGHLINE_FORBIDDEN_PREFIXES_JSON",
                            str(prefixes_json))
        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd
        monkeypatch.setattr(rd, "QDRANT_UPSERT_ENABLED", True)
        captured = []
        monkeypatch.setattr(rd, "log", lambda m: captured.append(m))

        result = rd._upsert_note_to_qdrant(
            rel_path="./00_Buffer/Private/leak.md",
            title="X", body_full="b",
            knowledge_identity="universal",
            tags=[], source_conversation_id="c1",
        )
        assert result is False

    def test_unrelated_path_proceeds(self, monkeypatch, tmp_path):
        """Sanity: a clean public path is NOT skipped."""
        prefixes_json = tmp_path / "forbidden.json"
        prefixes_json.write_text(
            json.dumps(["00_Buffer/Private"]), encoding="utf-8")
        monkeypatch.setenv("THROUGHLINE_FORBIDDEN_PREFIXES_JSON",
                            str(prefixes_json))
        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd
        monkeypatch.setattr(rd, "QDRANT_UPSERT_ENABLED", True)
        # Stub the real HTTP path so the test doesn't network out.
        monkeypatch.setattr(rd, "_embed_text", lambda _: None)

        captured = []
        monkeypatch.setattr(rd, "log", lambda m: captured.append(m))

        # A path NOT under the forbidden prefix.
        rd._upsert_note_to_qdrant(
            rel_path="70_AI/70.01_LLM_Brain/safe.md",
            title="X", body_full="b",
            knowledge_identity="universal",
            tags=[], source_conversation_id="c1",
        )
        # Should NOT have logged FORBIDDEN — the embed_text returning
        # None is the early-exit instead.
        assert not any("FORBIDDEN" in m for m in captured)


# ============================================================
# _record_cost — token clamp
# ============================================================

class TestRecordCostTokenClamp:
    def test_negative_tokens_clamped_to_zero(self, tmp_path, monkeypatch):
        """A provider returning negative usage numbers must NOT
        produce negative cost entries — that would underflow the
        daily-budget check and silently disable the cap."""
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        rd._record_cost("Slicer", "anthropic/claude-sonnet-4.6",
                         input_tokens=-100, output_tokens=-50)
        cost_file = Path(rd.COST_STATS_FILE)
        assert cost_file.exists()
        data = json.loads(cost_file.read_text(encoding="utf-8"))
        # Cost must be exactly 0 (not negative, not unrecorded).
        days = list(data.get("by_date", {}).values())
        assert len(days) == 1
        slicer = days[0]["Slicer"]
        assert slicer["input_tokens"] == 0
        assert slicer["output_tokens"] == 0
        assert slicer["cost"] == 0.0

    def test_none_tokens_clamped(self, tmp_path, monkeypatch):
        """A provider that returns None for tokens (instead of 0)
        must not crash — it gets coerced to 0."""
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        # `None` would crash an arithmetic op; the clamp must
        # absorb it.
        rd._record_cost("Refiner", "anthropic/claude-sonnet-4.6",
                         input_tokens=None, output_tokens=None)
        cost_file = Path(rd.COST_STATS_FILE)
        data = json.loads(cost_file.read_text(encoding="utf-8"))
        refiner = next(iter(data["by_date"].values()))["Refiner"]
        assert refiner["cost"] == 0.0

    def test_normal_tokens_unaffected(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        rd._record_cost("Refiner", "anthropic/claude-sonnet-4.6",
                         input_tokens=1000, output_tokens=500)
        data = json.loads(rd.COST_STATS_FILE.read_text(encoding="utf-8"))
        refiner = next(iter(data["by_date"].values()))["Refiner"]
        assert refiner["input_tokens"] == 1000
        assert refiner["output_tokens"] == 500
        assert refiner["cost"] > 0


# ============================================================
# call_llm_json — empty `choices` array no longer silently succeeds
# ============================================================

class TestCallLlmJsonEmptyChoices:
    """Pre-fix: `obj.get("choices", [{}])[0].get("message", {}).get(
    "content", "")` masked an empty-choices response (rate limit /
    safety filter / quota) as a successful empty refine. Now it
    raises so retry / log fires."""

    def _setup(self, monkeypatch, tmp_path, body_dict):
        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        import daemon.refine_daemon as rd
        # Force the LLM URL + key to non-empty for the test.
        monkeypatch.setattr(rd, "_LLM_URL",
                              "https://example.invalid/v1/chat/completions")
        monkeypatch.setattr(rd, "_LLM_KEY", "test-key")
        monkeypatch.setattr(rd, "_LLM_EXTRA_HEADERS", {})

        class _FakeResp:
            def __init__(self, b): self._b = b
            def read(self): return self._b
            def __enter__(self): return self
            def __exit__(self, *a): pass

        body_bytes = json.dumps(body_dict).encode("utf-8")
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=None: _FakeResp(body_bytes))
        return rd

    def test_empty_choices_raises_after_retries(self, tmp_path, monkeypatch):
        rd = self._setup(monkeypatch, tmp_path, {"choices": []})
        with pytest.raises(Exception) as ei:
            rd.call_llm_json(
                model="x/y", system_prompt="s", user_prompt="u",
                temperature=0.0, max_tokens=100, retries=0)
        assert "empty choices" in str(ei.value).lower()

    def test_concurrent_record_cost_no_lost_updates(self, tmp_path,
                                                          monkeypatch):
        """20 threads each call _record_cost once. Pre-fix:
        read-modify-write race lost updates because there was no
        lock. Post-fix: lock + atomic write → all 20 calls land."""
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        from threading import Thread
        N = 20

        def worker():
            rd._record_cost("Refiner", "anthropic/claude-sonnet-4.6",
                             input_tokens=100, output_tokens=50)

        threads = [Thread(target=worker) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        data = json.loads(rd.COST_STATS_FILE.read_text(encoding="utf-8"))
        days = list(data["by_date"].values())
        assert len(days) == 1
        refiner = days[0]["Refiner"]
        # All N calls accounted for: race condition would have lost
        # some updates, so this is a strict assertion.
        assert refiner["calls"] == N, (
            f"expected {N} calls, got {refiner['calls']} — "
            f"concurrent race likely lost updates")
        assert refiner["input_tokens"] == 100 * N
        assert refiner["output_tokens"] == 50 * N

    def test_atomic_write_no_partial_reads(self, tmp_path, monkeypatch):
        """During the write window, no reader should ever observe
        a half-written cost_stats.json. This is hard to test exactly
        without instrumenting the write itself, so we instead assert
        the write goes through `_atomic_write_json` (temp + rename)
        and never touches the real path with a partial payload.

        Approach: monkey-patch Path.write_text to assert it's only
        ever called on .tmp files (i.e., the atomic-rename pattern
        is in use)."""
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        for mod in list(sys.modules):
            if mod.startswith("daemon.refine_daemon"):
                del sys.modules[mod]
        import daemon.refine_daemon as rd

        from pathlib import Path as _P
        real_write = _P.write_text
        observed_paths: list = []

        def watching(self, *a, **kw):
            observed_paths.append(str(self))
            return real_write(self, *a, **kw)

        monkeypatch.setattr(_P, "write_text", watching)

        rd._record_cost("Refiner", "anthropic/claude-sonnet-4.6",
                         input_tokens=10, output_tokens=5)
        # Every direct write to disk must have hit a `.tmp` path,
        # never the real cost_stats.json. (The .replace() rename
        # then atomically swaps it in.)
        cost_file_writes = [p for p in observed_paths
                              if p.endswith("cost_stats.json")]
        assert cost_file_writes == [], (
            f"non-atomic write to cost_stats.json: {cost_file_writes}")

    def test_truncation_warning_logged(self, tmp_path, monkeypatch):
        """`finish_reason: length` (or Anthropic's `stop_reason:
        max_tokens`) means the response was truncated mid-emit. A WARN
        line tells the user WHY downstream JSON parsing fails."""
        rd = self._setup(monkeypatch, tmp_path, {
            "choices": [{
                "message": {"content": '{"unterminated": "json'},
                "finish_reason": "length",
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 4000},
        })
        captured: list = []
        monkeypatch.setattr(rd, "log", lambda m: captured.append(m))
        # Parse may raise on the unterminated JSON, but the WARN line
        # should fire BEFORE that. Catch and inspect.
        try:
            rd.call_llm_json(
                model="x/y", system_prompt="s", user_prompt="u",
                temperature=0.0, max_tokens=100,
                step_name="Refiner", retries=0)
        except Exception:
            pass
        assert any("truncated" in m.lower() for m in captured), (
            f"expected truncation warning, got logs: {captured}")
