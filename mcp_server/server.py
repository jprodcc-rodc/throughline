"""FastMCP application factory.

Phase 1 scaffolding stub — registers the 3 tools as fastmcp
decorators but each tool currently returns a placeholder shape.
Real implementations land in subsequent commits (save_conversation
in Week 1 commit 2, recall + list in Week 2).

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


def build_app() -> FastMCP:
    """Construct + return the FastMCP application with all 3 tools
    registered. Factored out of module load so tests can build a
    fresh app per test if needed.
    """
    app = FastMCP(
        name="throughline",
        version=__version__,
    )

    app.tool()(save_conversation)
    app.tool()(recall_memory)
    app.tool()(list_topics)

    return app
