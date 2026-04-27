"""MCP server for throughline.

Exposes the same vault + refine pipeline as the OpenWebUI Filter
form, but reachable from any MCP-aware client (Claude Desktop,
Claude Code, Cursor, Continue.dev) — no OpenWebUI migration
required.

Phase 1 ships three tools:

- `save_conversation` — write a conversation segment into the
  daemon's refine queue
- `recall_memory` — retrieve cards relevant to a query
- `list_topics` — list taxonomy domains

The server itself runs as a stdio process; the host LLM client
spawns it per `~/.claude_desktop_config.json` (or the equivalent
for Cursor / Continue.dev).

Architecture: this package is a thin CLIENT of throughline's
existing core (daemon watchdog + rag_server HTTP). It does NOT
duplicate any pipeline logic. See `private/MIGRATION_AUDIT.md`
for the integration-point map and `private/MCP_SCAFFOLDING_PLAN.md`
for the deliverables list.
"""
from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
