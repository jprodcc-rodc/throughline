"""Tests for mcp_server.tools.save_refined_card.

The cost-free save path: host LLM does the refining itself, this
tool just files the structured result. Tests cover input validation,
path routing under vault, atomic write, frontmatter shape, and
filename collision handling.
"""
from __future__ import annotations

from pathlib import Path

import pytest


class TestInputValidation:
    def test_empty_title_returns_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card
        result = save_refined_card(
            title="", body="x", domain="Health/Biohack"
        )
        assert result["_status"] == "error"
        assert "title" in result["_message"].lower()
        assert result["card_path"] is None

    def test_whitespace_title_returns_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card
        result = save_refined_card(
            title="   \n\t", body="x", domain="Health/Biohack"
        )
        assert result["_status"] == "error"

    def test_empty_body_returns_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card
        result = save_refined_card(
            title="T", body="", domain="Health/Biohack"
        )
        assert result["_status"] == "error"
        assert "body" in result["_message"].lower()

    def test_empty_domain_returns_error(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card
        result = save_refined_card(title="T", body="x", domain="")
        assert result["_status"] == "error"
        assert "domain" in result["_message"].lower()
        # Hint should point at list_topics
        assert "list_topics" in result["_message"]

    def test_invalid_knowledge_identity_returns_error(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card
        result = save_refined_card(
            title="T", body="x", domain="Health/Biohack",
            knowledge_identity="bogus_value",
        )
        assert result["_status"] == "error"
        assert "knowledge_identity" in result["_message"]

    def test_missing_vault_root_returns_error(
        self, tmp_path, monkeypatch
    ):
        # Point at a directory that doesn't exist
        missing = tmp_path / "no_such_vault"
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(missing))
        from mcp_server.tools.save_refined_card import save_refined_card
        result = save_refined_card(
            title="T", body="x", domain="Health/Biohack"
        )
        assert result["_status"] == "error"
        assert "vault" in result["_message"].lower()


class TestHappyPath:
    def test_writes_card_under_domain_dir(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card

        result = save_refined_card(
            title="Tailscale exit node troubleshooting",
            body="# Scene\n\nMulti-hop NAT issues.\n",
            domain="Tech/Network",
        )

        assert result["_status"] == "ok"
        assert result["host_refined"] is True
        assert result["domain"] == "Tech/Network"
        path = Path(result["card_path"])
        assert path.exists()
        assert path.parent == tmp_path / "Tech" / "Network"
        assert path.name.endswith(".md")

    def test_frontmatter_managed_by_host_llm_refined(
        self, tmp_path, monkeypatch
    ):
        """Cards from this tool must be tagged so daemon-side
        tooling can distinguish host-refined vs daemon-refined."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card

        result = save_refined_card(
            title="X", body="body content", domain="AI/LLM"
        )
        path = Path(result["card_path"])
        text = path.read_text(encoding="utf-8")
        assert 'managed_by: "host_llm_refined"' in text
        assert 'knowledge_identity: "universal"' in text
        assert "AI/LLM" in text  # domain in tags

    def test_extra_tags_rendered(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card

        result = save_refined_card(
            title="X", body="b", domain="AI/LLM",
            extra_tags=["y/SOP", "z/Pipeline"],
        )
        text = Path(result["card_path"]).read_text(encoding="utf-8")
        assert "  - AI/LLM" in text
        assert "  - y/SOP" in text
        assert "  - z/Pipeline" in text

    def test_personal_persistent_knowledge_identity(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card

        result = save_refined_card(
            title="My current meds", body="b",
            domain="Health/Biohack",
            knowledge_identity="personal_persistent",
        )
        text = Path(result["card_path"]).read_text(encoding="utf-8")
        assert 'knowledge_identity: "personal_persistent"' in text

    def test_filename_collision_appends_suffix(
        self, tmp_path, monkeypatch
    ):
        """Two cards with identical title shouldn't overwrite each
        other — second gets -2 suffix, third gets -3, etc."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card

        r1 = save_refined_card(
            title="DupName", body="first", domain="AI/LLM"
        )
        r2 = save_refined_card(
            title="DupName", body="second", domain="AI/LLM"
        )
        r3 = save_refined_card(
            title="DupName", body="third", domain="AI/LLM"
        )

        p1, p2, p3 = (Path(r["card_path"]) for r in (r1, r2, r3))
        assert p1 != p2 != p3
        assert p1.exists() and p2.exists() and p3.exists()
        assert "first" in p1.read_text(encoding="utf-8")
        assert "second" in p2.read_text(encoding="utf-8")
        assert "third" in p3.read_text(encoding="utf-8")

    def test_chinese_title_round_trips(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        from mcp_server.tools.save_refined_card import save_refined_card

        result = save_refined_card(
            title="个人完整用药清单全景",
            body="# 场景\n\n药物记录。",
            domain="Health/Biohack",
            knowledge_identity="personal_persistent",
        )
        assert result["_status"] == "ok"
        path = Path(result["card_path"])
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "个人完整用药清单全景" in text
        assert "药物记录" in text


class TestFilenameSanitization:
    def test_unsafe_chars_replaced(self):
        from mcp_server.tools.save_refined_card import _sanitize_filename
        s = _sanitize_filename("hello/world: bad?chars*")
        assert "/" not in s
        assert "?" not in s
        assert ":" not in s
        assert "*" not in s

    def test_chinese_preserved(self):
        from mcp_server.tools.save_refined_card import _sanitize_filename
        s = _sanitize_filename("个人完整用药清单")
        assert "个人完整用药清单" == s

    def test_empty_returns_untitled(self):
        from mcp_server.tools.save_refined_card import _sanitize_filename
        assert _sanitize_filename("") == "untitled"
        assert _sanitize_filename("   ") == "untitled"
        assert _sanitize_filename("///") == "untitled"

    def test_long_title_truncated(self):
        from mcp_server.tools.save_refined_card import _sanitize_filename
        s = _sanitize_filename("a" * 200, max_len=50)
        assert len(s) <= 50


class TestServerWiring:
    """save_refined_card must register on FastMCP app alongside
    save_conversation — verifies tools/__init__ + server.py wiring."""

    def test_registered_on_app(self):
        try:
            from fastmcp import FastMCP  # noqa: F401
        except ImportError:
            pytest.skip("fastmcp not installed")

        from mcp_server.server import build_app
        app = build_app()
        # FastMCP 3.x: list_tools is async, but the tools attr varies
        import asyncio
        try:
            tools = asyncio.run(app.list_tools())
            names = {t.name for t in tools}
        except Exception:
            names = set()
        assert "save_refined_card" in names, (
            f"save_refined_card must be registered as MCP tool; "
            f"got: {sorted(names)}"
        )
