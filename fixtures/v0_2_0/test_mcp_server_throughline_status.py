"""Tests for mcp_server.tools.throughline_status — discovery /
onboarding tool that surfaces install state for the host LLM.

Coverage:
- cold-start (empty vault) → status='cold_start' + save_conversation hint
- populated but no Reflection Pass → status='warning' + reflection_pass hint
- populated + fresh Reflection Pass → status='ok'
- populated + stale Reflection Pass (>14d) → status='warning' + re-run hint
- malformed pass-state file → defensive: ok status, no crash
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest


def _write_card(vault: Path, filename: str, tags: list[str], title: str = "T"):
    fm_tags = "[" + ", ".join(tags) + "]"
    body = (
        "---\n"
        f"title: \"{title}\"\n"
        "date: 2026-04-01\n"
        f"tags: {fm_tags}\n"
        "---\n\n"
        "# Body\n\nLorem ipsum.\n"
    )
    path = vault / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _write_pass_state(state_dir: Path, *, finished_at: str, age_days: float = 0):
    """Write a reflection_pass_state.json with controllable mtime
    (mtime drives the staleness check, finished_at drives the
    age_days return field — they should be consistent)."""
    state_dir.mkdir(parents=True, exist_ok=True)
    f = state_dir / "reflection_pass_state.json"
    f.write_text(json.dumps({
        "started_at": finished_at,
        "finished_at": finished_at,
        "cards_scanned": 100,
        "cards_reflectable": 30,
    }), encoding="utf-8")
    if age_days > 0:
        old = time.time() - (age_days * 86400)
        os.utime(f, (old, old))


class TestThroughlineStatus:
    def setup_method(self):
        from mcp_server.taxonomy_reader import clear_cache
        clear_cache()

    def test_cold_start_empty_vault(self, tmp_path, monkeypatch):
        """0 cards → status='cold_start' + actionable save_conversation
        hint that names the user-facing trigger phrases."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))

        from mcp_server.tools.throughline_status import throughline_status
        result = throughline_status()

        assert result["tagged_card_count"] == 0
        assert result["domain_count"] == 0
        assert result["_status"] == "cold_start"
        assert "_message" in result
        msg = result["_message"].lower()
        # Hint must reference save_conversation + a trigger phrase
        assert "save_conversation" in msg
        assert "remember" in msg or "保存" in msg

    def test_populated_vault_no_reflection_pass_warns(
        self, tmp_path, monkeypatch
    ):
        """Cards exist but reflection_pass_state.json missing →
        status='warning' + hint pointing at python -m daemon.reflection_pass."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        _write_card(tmp_path, "c1.md", ["Health/Biohack"])
        _write_card(tmp_path, "c2.md", ["AI/LLM"])

        from mcp_server.tools.throughline_status import throughline_status
        result = throughline_status()

        assert result["tagged_card_count"] >= 2
        assert result["reflection_pass"]["last_run"] is None
        assert result["_status"] == "warning"
        msg = result["_message"].lower()
        assert "reflection pass" in msg or "reflection_pass" in msg

    def test_populated_vault_fresh_pass_ok(self, tmp_path, monkeypatch):
        """Cards + recent (today) reflection state → status='ok'
        and no _message (don't pollute the response with stale-state
        hints when nothing's wrong)."""
        from datetime import datetime, timezone
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        sd = tmp_path / "state"
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(sd))
        _write_card(tmp_path, "c.md", ["Health/Biohack"])
        _write_pass_state(
            sd, finished_at=datetime.now(timezone.utc).isoformat()
        )

        from mcp_server.tools.throughline_status import throughline_status
        result = throughline_status()

        assert result["tagged_card_count"] >= 1
        assert result["reflection_pass"]["last_run"] is not None
        assert result["reflection_pass"]["is_stale"] is False
        assert result["_status"] == "ok"
        assert "_message" not in result

    def test_populated_vault_stale_pass_warns(self, tmp_path, monkeypatch):
        """Cards + reflection state from 21 days ago (past 14d
        threshold) → status='warning' + re-run hint."""
        from datetime import datetime, timezone, timedelta
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        sd = tmp_path / "state"
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(sd))
        _write_card(tmp_path, "c.md", ["Health/Biohack"])
        old_iso = (datetime.now(timezone.utc) - timedelta(days=21)).isoformat()
        _write_pass_state(sd, finished_at=old_iso, age_days=21)

        from mcp_server.tools.throughline_status import throughline_status
        result = throughline_status()

        assert result["reflection_pass"]["is_stale"] is True
        assert result["reflection_pass"]["age_days"] is not None
        assert result["reflection_pass"]["age_days"] > 14
        assert result["_status"] == "warning"
        msg = result["_message"].lower()
        assert "stale" in msg or "old" in msg
        assert "reflection_pass" in msg or "reflection pass" in msg

    def test_malformed_pass_state_treated_as_missing(
        self, tmp_path, monkeypatch
    ):
        """A corrupt JSON in reflection_pass_state.json must NOT
        crash status — it should degrade to 'no pass run' shape."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        sd = tmp_path / "state"
        sd.mkdir()
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(sd))
        (sd / "reflection_pass_state.json").write_text(
            "{ this is not valid json", encoding="utf-8"
        )
        _write_card(tmp_path, "c.md", ["Health/Biohack"])

        from mcp_server.tools.throughline_status import throughline_status
        # Should not raise
        result = throughline_status()
        # Treated as if no pass ran
        assert result["reflection_pass"]["last_run"] is None
        assert result["_status"] == "warning"

    def test_vault_root_unset_returns_none(self, tmp_path, monkeypatch):
        """When THROUGHLINE_VAULT_ROOT is unset, vault_root field is
        None — caller can detect install hasn't been initialized."""
        monkeypatch.delenv("THROUGHLINE_VAULT_ROOT", raising=False)
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))

        from mcp_server.tools.throughline_status import throughline_status
        result = throughline_status()

        assert result["vault_root"] is None

    def test_returned_shape_contract(self, tmp_path, monkeypatch):
        """Lock the return shape so host LLMs that key off specific
        fields don't break on minor refactors."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))

        from mcp_server.tools.throughline_status import throughline_status
        result = throughline_status()

        # Top-level keys
        for key in ["tagged_card_count", "total_md_files", "domain_count", "vault_root",
                    "reflection_pass", "_status"]:
            assert key in result, f"missing top-level key: {key}"

        # reflection_pass nested keys
        for key in ["last_run", "age_days", "is_stale"]:
            assert key in result["reflection_pass"], (
                f"missing reflection_pass.{key}"
            )

        # Types
        assert isinstance(result["tagged_card_count"], int)
        assert isinstance(result["domain_count"], int)
        assert result["vault_root"] is None or isinstance(
            result["vault_root"], str
        )
        assert isinstance(result["_status"], str)


class TestServerWiring:
    """Make sure the new tool actually gets registered on the
    FastMCP app, not just defined in isolation."""

    def test_throughline_status_registered(self):
        try:
            from fastmcp import FastMCP  # noqa: F401
        except ImportError:
            pytest.skip("fastmcp not installed")

        from mcp_server.server import build_app
        app = build_app()
        # FastMCP exposes registered tools via list_tools (async). Probe
        # via the internal _tool_manager registry which is sync.
        tool_names = set()
        if hasattr(app, "_tool_manager") and hasattr(app._tool_manager, "_tools"):
            tool_names = set(app._tool_manager._tools.keys())
        elif hasattr(app, "tools"):
            tool_names = {t.name for t in app.tools}

        assert "throughline_status" in tool_names, (
            f"throughline_status must be registered; got: {tool_names}"
        )
