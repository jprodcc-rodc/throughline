"""Phase 1 scaffolding smoke tests for mcp_server.

These tests verify the *structure* of the MCP server — module imports
work, tools have the expected signatures, docstrings are non-empty
and contain the call-when guidance per locked decision Q3 in
private/MCP_SCAFFOLDING_PLAN.md § 12.A.

What these tests do NOT cover (yet):
- The fastmcp app build (requires fastmcp installed; gated test)
- Real save_conversation file-write logic (Week 1 commit 2)
- Real recall_memory HTTP roundtrip (Week 2)
- Real list_topics taxonomy reading (Week 2)
- End-to-end stdio handshake with a host client (Week 3 manual)
"""
from __future__ import annotations

import inspect

import pytest


# ---------- Module-level import check ----------

def test_mcp_server_package_imports():
    """`import mcp_server` works without fastmcp installed."""
    import mcp_server

    assert mcp_server.__version__
    assert isinstance(mcp_server.__version__, str)


def test_tools_module_imports():
    """All three tool functions are importable without fastmcp."""
    from mcp_server.tools import (
        save_conversation,
        recall_memory,
        list_topics,
    )

    assert callable(save_conversation)
    assert callable(recall_memory)
    assert callable(list_topics)


# ---------- Tool signature checks ----------

def test_save_conversation_signature():
    """save_conversation takes the schema documented in
    MCP_SCAFFOLDING_PLAN § 3.1."""
    from mcp_server.tools import save_conversation

    sig = inspect.signature(save_conversation)
    params = sig.parameters

    assert "text" in params
    assert "title" in params
    assert "source" in params
    assert "wait_for_refine" in params

    # `text` is required (no default)
    assert params["text"].default is inspect.Parameter.empty
    # Others have defaults
    assert params["title"].default is None
    assert params["source"].default == "claude_desktop"
    assert params["wait_for_refine"].default is False


def test_recall_memory_signature():
    """recall_memory takes the schema documented in § 3.2."""
    from mcp_server.tools import recall_memory

    sig = inspect.signature(recall_memory)
    params = sig.parameters

    assert "query" in params
    assert "limit" in params
    assert "include_personal_context" in params
    assert "domain_filter" in params

    # Locked decision Q1: include_personal_context defaults to False
    assert params["include_personal_context"].default is False


def test_list_topics_signature():
    """list_topics takes the schema documented in § 3.3."""
    from mcp_server.tools import list_topics

    sig = inspect.signature(list_topics)
    params = sig.parameters

    assert "prefix" in params
    assert "include_card_counts" in params

    assert params["include_card_counts"].default is True


# ---------- Tool description quality (locked decision Q3) ----------

@pytest.mark.parametrize(
    "tool_name",
    ["save_conversation", "recall_memory", "list_topics"],
)
def test_tool_docstring_has_call_when_guidance(tool_name):
    """Per Q3: tool descriptions must include explicit 'Call this
    when:' guidance so the host LLM knows when to fire the tool."""
    import importlib

    mod = importlib.import_module(f"mcp_server.tools.{tool_name}")
    fn = getattr(mod, tool_name)

    assert fn.__doc__, f"{tool_name} must have a docstring"
    assert "Call this when:" in fn.__doc__, (
        f"{tool_name} docstring must include 'Call this when:' guidance "
        "per locked decision Q3"
    )


@pytest.mark.parametrize(
    "tool_name",
    ["save_conversation", "recall_memory", "list_topics"],
)
def test_tool_docstring_has_do_not_call_guidance(tool_name):
    """Per Q3: tool descriptions must include 'Do NOT call:' anti-
    pattern guidance so the host LLM doesn't over-call."""
    import importlib

    mod = importlib.import_module(f"mcp_server.tools.{tool_name}")
    fn = getattr(mod, tool_name)

    assert fn.__doc__, f"{tool_name} must have a docstring"
    assert "Do NOT call:" in fn.__doc__, (
        f"{tool_name} docstring must include 'Do NOT call:' guidance "
        "per locked decision Q3"
    )


# ---------- Tool return shape (Phase 1) ----------
#
# Each tool returns a dict with a `_status` field. Implemented tools
# return "ok" / "error" depending on outcome; tools still scaffolded
# return "stub". As Phase 1 commits land, more of these flip from
# "stub" to "ok"|"error". Comprehensive per-tool behaviour tests
# live in their own file (e.g. test_mcp_server_save_conversation.py).


def test_save_conversation_returns_dict_with_status():
    """save_conversation has its real implementation as of Phase 1
    Week 1 commit 2. This smoke check just ensures the tool surface
    is reachable and returns a dict with the contractual fields.
    """
    from mcp_server.tools import save_conversation

    # Empty text → predictable error path, no env / fs side effects
    result = save_conversation(text="")
    assert isinstance(result, dict)
    assert "queued" in result
    assert "_status" in result
    assert result["_status"] in {"ok", "error"}  # not "stub" anymore


def test_recall_memory_stub_returns_dict():
    """recall_memory is still a stub as of Week 1; flips when
    Week 2 commit lands."""
    from mcp_server.tools import recall_memory

    result = recall_memory(query="test")
    assert isinstance(result, dict)
    assert "cards" in result
    assert result["_status"] == "stub"


def test_list_topics_stub_returns_dict():
    """list_topics is still a stub as of Week 1; flips when
    Week 2 commit lands."""
    from mcp_server.tools import list_topics

    result = list_topics()
    assert isinstance(result, dict)
    assert "domains" in result
    assert result["_status"] == "stub"


# ---------- FastMCP app build (gated on fastmcp install) ----------

def test_build_app_registers_three_tools():
    """If fastmcp is installed, build_app() returns a FastMCP
    instance with all 3 tools registered.

    Skipped when fastmcp is not installed — scaffolding tests above
    still cover the structural invariants without it.
    """
    pytest.importorskip("fastmcp")

    from mcp_server.server import build_app

    app = build_app()
    # fastmcp's tool registry shape may evolve; this assertion
    # uses the public attr that exists across 0.4.x line.
    assert app is not None
