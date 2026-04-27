# throughline-mcp

MCP server form of [throughline](https://github.com/jprodcc-rodc/throughline)
— exposes save / recall / list-topics tools to any
[Model Context Protocol](https://spec.modelcontextprotocol.io)-aware
client (Claude Desktop, Claude Code, Cursor, Continue.dev, …) so
you can use throughline's vault + refine pipeline without migrating
to OpenWebUI.

## Install

```bash
pip install throughline-mcp
```

This pulls in `throughline` (the shared core: daemon, RAG server,
embedder, reranker, vector stores, taxonomy) plus `fastmcp` (the
MCP stdio transport) automatically.

## Quick setup

1. Run the wizard once to set up `~/.throughline/config.toml`:

   ```bash
   export ANTHROPIC_API_KEY=sk-...
   python install.py --express
   ```

2. Start the daemon + RAG server (separate terminals or as
   `launchd` / `systemd` services):

   ```bash
   python rag_server/rag_server.py
   python daemon/refine_daemon.py
   ```

3. Configure your MCP client. For Claude Desktop, edit
   `~/Library/Application Support/Claude/claude_desktop_config.json`
   (Mac) / `%APPDATA%\Claude\claude_desktop_config.json` (Windows) /
   `~/.config/Claude/claude_desktop_config.json` (Linux):

   ```json
   {
     "mcpServers": {
       "throughline": {
         "command": "throughline-mcp"
       }
     }
   }
   ```

4. Restart Claude Desktop. Three tools become available:

   - `save_conversation(text, title?, source, wait_for_refine?)`
   - `recall_memory(query, limit?, include_personal_context?, domain_filter?)`
   - `list_topics(prefix?, include_card_counts?)`

The host LLM decides when to call them based on each tool's
`Call this when:` / `Do NOT call:` docstring guidance.

Full per-client setup + troubleshooting at
[`docs/MCP_SETUP.md`](https://github.com/jprodcc-rodc/throughline/blob/main/docs/MCP_SETUP.md).

## License

MIT — same as the parent `throughline` package.
