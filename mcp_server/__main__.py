"""`python -m mcp_server` stdio entry point.

Configured into Claude Desktop / Claude Code / Cursor / Continue.dev
via the host's `mcpServers` config — see `docs/MCP_SETUP.md`.

Subcommands:
- (default, no args)  Start the MCP server over stdio.
- `--doctor`          Run prerequisite checks + exit (no server start).
- `--version` / `-V`  Print version + exit.
- `--help` / `-h`     Print help + exit.

Failure mode: if `fastmcp` is not installed, prints a clear install
hint and exits 1 (matches the locked design decision Q2 in
`private/MCP_SCAFFOLDING_PLAN.md` § 12.A — fail-with-message, never
auto-install).
"""
from __future__ import annotations

import sys


_HELP = """\
throughline-mcp — MCP server for the throughline vault.

Usage:
  python -m mcp_server                Run server over stdio.
  python -m mcp_server --doctor       Verify runtime prerequisites.
  python -m mcp_server --version      Print version.
  python -m mcp_server --help         This help.

Configure your MCP client (Claude Desktop / Code / Cursor /
Continue.dev) to invoke `python -m mcp_server` (or the
`throughline-mcp` console script if installed via PyPI). See
docs/MCP_SETUP.md for per-client config.
"""


def main(argv: list[str] | None = None) -> int:
    """Dispatch on argv. Returns process exit code."""
    args = list(argv) if argv is not None else sys.argv[1:]

    # Help / version handled before any imports that need fastmcp,
    # so users without fastmcp can still read help.
    if args and args[0] in ("--help", "-h"):
        print(_HELP)
        return 0
    if args and args[0] in ("--version", "-V"):
        from mcp_server import __version__
        print(__version__)
        return 0
    if args and args[0] == "--doctor":
        # Doctor doesn't need fastmcp itself; it CHECKS for fastmcp
        # as one of its required prerequisites.
        from mcp_server.doctor import run_doctor
        return run_doctor()
    if args:
        # Unknown flag — show help on stderr + nonzero exit
        print(f"unknown argument: {args[0]}\n", file=sys.stderr)
        print(_HELP, file=sys.stderr)
        return 2

    # Default: start the stdio MCP server.
    try:
        from mcp_server.server import build_app
    except ImportError as exc:
        if "fastmcp" in str(exc).lower():
            print(
                "throughline MCP server requires `fastmcp`.\n\n"
                "Install with: pip install throughline-mcp\n"
                "(or for development: pip install -e mcp_server)\n",
                file=sys.stderr,
            )
            return 1
        raise

    app = build_app()
    app.run()  # fastmcp default: stdio transport
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
