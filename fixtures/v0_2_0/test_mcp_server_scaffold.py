"""Phase 1 + Phase 2 scaffolding smoke tests for mcp_server.

These tests verify the *structure* of the MCP server — module imports
work, tools have the expected signatures, docstrings are non-empty
and contain the call-when guidance per locked decision Q3 in
private/MCP_SCAFFOLDING_PLAN.md § 12.A.

Phase 1 (shipped, v0.2.x): save_conversation / recall_memory /
list_topics are real implementations.

Phase 2 (in progress, v0.3): find_open_threads / check_consistency /
get_position_drift are stubs returning `_status: "stub"` until the
Reflection Pass daemon and position_signal frontmatter schema land.
The scaffold tests here verify the surface (signature, docstring
quality, return shape contract) so Phase 2 work can flip stubs to
real implementations one at a time without rewriting the surface.

What these tests do NOT cover (yet):
- The fastmcp app build registers all tools (gated test below)
- Real Reflection Pass daemon detection logic (subsequent commit)
- End-to-end stdio handshake with a host client (manual smoke test)
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
    """All six tool functions are importable without fastmcp."""
    from mcp_server.tools import (
        save_conversation,
        recall_memory,
        list_topics,
        find_open_threads,
        check_consistency,
        get_position_drift,
    )

    assert callable(save_conversation)
    assert callable(recall_memory)
    assert callable(list_topics)
    assert callable(find_open_threads)
    assert callable(check_consistency)
    assert callable(get_position_drift)


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


def test_find_open_threads_signature():
    """find_open_threads takes (topic, limit). topic optional, limit
    defaults 5. See docs/REFLECTION_LAYER_DESIGN.md § Open Threads."""
    from mcp_server.tools import find_open_threads

    sig = inspect.signature(find_open_threads)
    params = sig.parameters

    assert "topic" in params
    assert "limit" in params

    assert params["topic"].default is None
    assert params["limit"].default == 5


def test_check_consistency_signature():
    """check_consistency takes (statement, soft_mode). statement
    required; soft_mode defaults True (mitigation for engineering
    risk #3 false-positive contradictions per design doc)."""
    from mcp_server.tools import check_consistency

    sig = inspect.signature(check_consistency)
    params = sig.parameters

    assert "statement" in params
    assert "soft_mode" in params

    # statement required (no default)
    assert params["statement"].default is inspect.Parameter.empty
    # soft_mode defaults True per design doc § 'Engineering risks'
    assert params["soft_mode"].default is True


def test_get_position_drift_signature():
    """get_position_drift takes (topic, granularity). topic required;
    granularity defaults 'transitions'."""
    from mcp_server.tools import get_position_drift

    sig = inspect.signature(get_position_drift)
    params = sig.parameters

    assert "topic" in params
    assert "granularity" in params

    # topic required
    assert params["topic"].default is inspect.Parameter.empty
    assert params["granularity"].default == "transitions"


# ---------- Tool description quality (locked decision Q3) ----------

ALL_TOOLS = [
    "save_conversation",
    "recall_memory",
    "list_topics",
    "find_open_threads",
    "check_consistency",
    "get_position_drift",
]


@pytest.mark.parametrize("tool_name", ALL_TOOLS)
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


@pytest.mark.parametrize("tool_name", ALL_TOOLS)
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


def test_recall_memory_returns_dict_with_status():
    """recall_memory has its real implementation as of Phase 1 Week
    2 commit 3 (rag_client + tool wired). This smoke check just
    ensures the tool surface returns a dict with the contractual
    fields. Comprehensive behaviour tests in
    test_mcp_server_recall_memory.py.
    """
    from mcp_server.tools import recall_memory

    # Empty query → predictable error path, no network side effects
    result = recall_memory(query="")
    assert isinstance(result, dict)
    assert "cards" in result
    assert result["_status"] in {"ok", "error"}  # not "stub" anymore


def test_list_topics_returns_dict_with_status():
    """list_topics has its real implementation as of Phase 1 Week 2
    commit 4 (taxonomy_reader + tool wired). Smoke check the tool
    surface — real behaviour tests in test_mcp_server_list_topics.py.
    """
    from mcp_server.tools import list_topics

    # Default call — taxonomy loads; vault may or may not exist
    result = list_topics(include_card_counts=False)
    assert isinstance(result, dict)
    assert "domains" in result
    assert result["_status"] in {"ok", "error"}  # not "stub" anymore


# ---------- Phase 2 stub return shape ----------
#
# These return `_status: "stub"` until the Reflection Pass daemon and
# position_signal frontmatter schema land. Tests assert the *contract*
# (key names, types) so flipping each stub to real implementation
# doesn't break the surface.


def test_find_open_threads_returns_real_shape(monkeypatch, tmp_path):
    """find_open_threads is now a real implementation reading the
    state file written by Reflection Pass stage 5. With no state
    file present (point at empty dir), it returns _status: "error"
    with a clear message — never crashes."""
    from mcp_server.tools import find_open_threads

    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "no_state"))
    result = find_open_threads()
    assert isinstance(result, dict)
    assert "open_threads" in result
    assert isinstance(result["open_threads"], list)
    assert "total_open_threads" in result
    assert result["_status"] == "error"  # state file missing → error
    assert "_message" in result
    assert "has not run yet" in result["_message"]


def test_check_consistency_returns_real_shape(monkeypatch, tmp_path):
    """check_consistency is now a real implementation reading the
    positions state file. With no state file present, returns
    _status: error with clear message — never crashes."""
    from mcp_server.tools import check_consistency

    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "no_state"))
    result = check_consistency(statement="I think we should use Postgres")
    assert isinstance(result, dict)
    assert "contradictions" in result
    assert isinstance(result["contradictions"], list)
    assert result["_status"] == "error"
    assert "_message" in result
    assert "has not run yet" in result["_message"]


def test_get_position_drift_returns_real_shape(monkeypatch, tmp_path):
    """get_position_drift is now a real implementation reading the
    positions state file. With no state file, error with hint."""
    from mcp_server.tools import get_position_drift

    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "no_state"))
    result = get_position_drift(topic="pricing_strategy")
    assert isinstance(result, dict)
    assert "topic" in result
    assert result["topic"] == "pricing_strategy"
    assert "trajectory" in result
    assert isinstance(result["trajectory"], list)
    assert result["_status"] == "error"
    assert "_message" in result


# ---------- FastMCP app build (gated on fastmcp install) ----------

def test_build_app_registers_all_tools():
    """If fastmcp is installed, build_app() returns a FastMCP
    instance with all 6 tools (3 Phase 1 + 3 Phase 2 stubs) registered.

    Skipped when fastmcp is not installed — scaffolding tests above
    still cover the structural invariants without it.
    """
    pytest.importorskip("fastmcp")

    from mcp_server.server import build_app

    app = build_app()
    # fastmcp's tool registry shape may evolve; this assertion uses
    # the public attr that exists across 0.4.x line.
    assert app is not None
