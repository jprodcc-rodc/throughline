"""FastMCP application factory.

Phase 1 (v0.2.x, shipped) registered 3 real tools:
- save_conversation, recall_memory, list_topics

Phase 2 (v0.3, in progress) adds 3 more for the Reflection Layer:
- find_open_threads, check_consistency, get_position_drift

The Phase 2 trio currently registers as stubs (returning
`_status: "stub"`) so MCP clients can wire up and test the surface
end-to-end before the Reflection Pass daemon lands the underlying
metadata. Engineering gate (≥75% topic-clustering pairwise accuracy
on author's vault): cleared 2026-04-28 at 0.975.

Per locked decision Q4 (`private/MCP_SCAFFOLDING_PLAN.md` § 12.A):
tool names are NOT namespaced (`save_conversation`, not
`throughline_save_conversation`). If collision with another MCP
server in the same client surfaces, namespace in a minor bump.

Per locked decision Q3: tool descriptions are verbose with explicit
"Call this when:" / "Do NOT call:" guidance — descriptions live in
each tool module's docstring and propagate via `fastmcp`'s automatic
docstring → tool description mapping.
"""
from __future__ import annotations

from fastmcp import FastMCP

from mcp_server import __version__
from mcp_server.tools.save_conversation import save_conversation
from mcp_server.tools.recall_memory import recall_memory
from mcp_server.tools.list_topics import list_topics
from mcp_server.tools.find_open_threads import find_open_threads
from mcp_server.tools.check_consistency import check_consistency
from mcp_server.tools.get_position_drift import get_position_drift
from mcp_server.tools.throughline_status import throughline_status


def build_app() -> FastMCP:
    """Construct + return the FastMCP application with all tools
    registered. Factored out of module load so tests can build a
    fresh app per test if needed.
    """
    app = FastMCP(
        name="throughline",
        version=__version__,
    )

    # Phase 1: foundational tools.
    app.tool()(save_conversation)
    app.tool()(recall_memory)
    app.tool()(list_topics)

    # Phase 2: Reflection Layer (currently stub-tier; real impl
    # in subsequent commits once daemon + position_signal land).
    app.tool()(find_open_threads)
    app.tool()(check_consistency)
    app.tool()(get_position_drift)

    # Discovery / onboarding entry point — closes the cold-start gap
    # where a fresh-install user with 0 cards has no natural trigger
    # for any of the other 6 tools.
    app.tool()(throughline_status)

    return app
