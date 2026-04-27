"""`python -m mcp_server` stdio entry point.

Configured into Claude Desktop / Claude Code / Cursor / Continue.dev
via the host's `mcpServers` config — see `docs/MCP_SETUP.md` (TODO,
Phase 1 Week 3).

Failure mode: if `fastmcp` is not installed, prints a clear install
hint and exits 1 (matches the locked design decision Q2 in
`private/MCP_SCAFFOLDING_PLAN.md` § 12.A — fail-with-message, never
auto-install).
"""
from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    """Run the MCP server over stdio. Returns process exit code."""
    try:
        from mcp_server.server import build_app
    except ImportError as exc:
        if "fastmcp" in str(exc).lower():
            print(
                "throughline MCP server requires `fastmcp`.\n\n"
                "Install with: pip install -e .[mcp]\n"
                "(or: pip install fastmcp)\n",
                file=sys.stderr,
            )
            return 1
        raise

    app = build_app()
    app.run()  # fastmcp default: stdio transport
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
