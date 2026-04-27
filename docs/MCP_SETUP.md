# MCP server setup

throughline ships an MCP server alongside the OpenWebUI Filter. If
you'd rather use throughline from **Claude Desktop**, **Claude Code**,
**Cursor**, **Continue.dev**, or any other [Model Context Protocol]-
aware client without migrating to OpenWebUI, this is the entry point.

[Model Context Protocol]: https://spec.modelcontextprotocol.io/

> **MCP server form vs Filter form** — both share the same vault and
> daemon. The MCP server is a thin alternative *access surface*, not
> a different product. You can run both at once; conversations
> saved through MCP land in the same vault as conversations refined
> by the Filter.

---

## What you get

Three tools registered with your MCP-aware client:

| Tool | What it does | Calls cost? |
|---|---|---|
| `save_conversation` | Write a conversation segment into throughline's refine queue. Daemon picks it up automatically and produces a 6-section knowledge card. | ~$0.04 per refine on the Normal tier (one Sonnet call). |
| `recall_memory` | Retrieve cards from your vault relevant to a query. Embedding + reranking happens in the local rag_server. | ~$0.0003 (Haiku judge) + local compute. |
| `list_topics` | List the X-axis taxonomy domains + (optionally) per-domain card counts. No LLM call. | Free. |

The host LLM (Claude / Cursor / etc.) decides when to call these
based on the tool descriptions. All three descriptions include
explicit "Call this when:" / "Do NOT call:" guidance; you don't need
to prompt-engineer.

---

## Prerequisites

Before configuring your MCP client, throughline must be installed
and the supporting daemons running:

1. **Install throughline + the MCP extras**:

   ```bash
   git clone https://github.com/jprodcc-rodc/throughline.git
   cd throughline
   python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -e .[mcp]
   ```

2. **Run the wizard once** (sets up `~/.throughline/config.toml`,
   creates `~/throughline_runtime/sources/openwebui_raw/` and
   `~/ObsidianVault/`):

   ```bash
   export ANTHROPIC_API_KEY=sk-...                # or OpenAI / OpenRouter / etc.
   python install.py --express                    # ~3 seconds
   ```

3. **Start the daemon + RAG server** in separate terminals (or use
   the `launchd` / `systemd` service templates in `config/`):

   ```bash
   python rag_server/rag_server.py                # FastAPI on :8000
   python daemon/refine_daemon.py                 # watchdog → refine → vault
   ```

4. **Verify** with the doctor:

   ```bash
   python -m throughline_cli doctor
   ```

   13 checks; everything should be green or warning. If anything's
   red, follow the printed remediation hints first — MCP needs the
   same plumbing the Filter form uses.

---

## Configuring your MCP client

The `mcpServers` config schema is consistent across Claude Desktop,
Claude Code, Cursor, and Continue.dev. The location of the config
file differs.

### Claude Desktop

**Config file location:**

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Add this block** (or merge into existing `mcpServers`):

```json
{
  "mcpServers": {
    "throughline": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/absolute/path/to/throughline",
      "env": {
        "PYTHONPATH": "/absolute/path/to/throughline"
      }
    }
  }
}
```

Replace `/absolute/path/to/throughline` with your actual repo path
(e.g. `/Users/you/code/throughline` on macOS or
`C:\\Users\\you\\code\\throughline` on Windows — note the doubled
backslashes inside JSON).

**Restart Claude Desktop** (Cmd+Q on Mac / right-click tray + Quit
on Windows; relaunch). On next conversation start, ask "what tools
do you have?" and Claude should mention `save_conversation`,
`recall_memory`, `list_topics`.

### Claude Code

Edit `~/.claude.json` (created on first run) or whatever your Claude
Code config path is, and add the same `mcpServers` block.

### Cursor

`Settings → MCP servers → New server`, paste the JSON above. Cursor
auto-restarts the MCP process on save.

### Continue.dev

In your `~/.continue/config.json`:

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "name": "throughline",
        "transport": {
          "type": "stdio",
          "command": "python",
          "args": ["-m", "mcp_server"],
          "cwd": "/absolute/path/to/throughline"
        }
      }
    ]
  }
}
```

### Other MCP-aware clients

Any client speaking the MCP spec's stdio transport works. The
command to launch the throughline server is always:

```bash
cd /absolute/path/to/throughline
python -m mcp_server
```

stdin/stdout speaks JSON-RPC per the MCP spec; the client wraps
this transparently.

---

## What each tool sees

### `save_conversation(text, title=None, source="claude_desktop", wait_for_refine=False)`

Writes a timestamped `.md` to `$THROUGHLINE_RAW_ROOT/YYYY-MM/`
in the daemon's expected `## user` / `## assistant` H2 format.
Defensive turn-shape coercion handles 4 input shapes:
1. `## user` / `## assistant` H2 (canonical) — passthrough
2. `# User` / `# Assistant` H1 — re-headerized
3. `User:` / `Assistant:` line prefixes — promoted to H2
4. Free prose — wrapped as a single `## user` block

### `recall_memory(query, limit=5, include_personal_context=False, domain_filter=None)`

POSTs to `localhost:8000/v1/rag` (or whatever
`THROUGHLINE_RAG_URL` is set to). The rag_server embeds + reranks
+ applies freshness boost. Result mapped to
`{cards: [...], personal_context: str|None, total_matched: int}`.

`include_personal_context=True` upweights `personal_persistent`
cards (allergies, durable preferences, current projects) via the
rag_server's `pp_boost` parameter, AND surfaces any such cards in
the result set as a concatenated `personal_context` string for
the host LLM to read.

### `list_topics(prefix=None, include_card_counts=True)`

Reads the active `daemon.taxonomy.VALID_X_SET` (33 domains in the
default install; user override at `config/taxonomy.py` takes
precedence). `include_card_counts=True` walks the vault for
per-domain counts (cached for 60s).

---

## Troubleshooting

### `python -m mcp_server requires fastmcp`

You missed `pip install -e .[mcp]`. Run it; fastmcp is the only
new dep MCP form adds on top of the regular install.

### Tool calls return `{"_status": "error", "_message": "rag_server unreachable..."}`

The rag_server isn't running. Start it:

```bash
python rag_server/rag_server.py
```

If it's running on a non-default host/port, point MCP at it:

```bash
export THROUGHLINE_RAG_URL=http://192.168.1.42:8001
```

### Tool calls return `{"_status": "error", "_message": "RAW_ROOT not found..."}`

You haven't run the wizard yet, or `$THROUGHLINE_RAW_ROOT` points
somewhere that doesn't exist. Run `python -m throughline_cli doctor`
to verify the path resolution.

### Claude doesn't seem to call the tools

Two possibilities:

1. **Claude Desktop didn't pick up the MCP config**: check the dev
   tools console (Cmd+Opt+I on Mac) for MCP errors. Verify the
   `cwd` path is absolute and the directory exists.
2. **The user prompt didn't trigger Claude's tool-use heuristic**:
   the tool descriptions tell Claude *when* to fire. If you ask
   something that doesn't match a "Call this when:" pattern, Claude
   won't call. Try: "save this conversation as a card" (triggers
   save), "what did I think about X last month?" (triggers recall),
   "what topics are in my vault?" (triggers list).

### `save_conversation` succeeds but no card appears in the vault

The daemon picks up new files in `$THROUGHLINE_RAW_ROOT` via
watchdog. Check:

1. Is `python daemon/refine_daemon.py` running?
2. Look at `~/throughline_runtime/logs/refine_daemon.log` for
   errors — most commonly: LLM provider env var missing, or daily
   budget cap hit.
3. The card lands in your vault under the routed leaf path; if
   routing was uncertain, it lands in
   `00_Buffer/00.00_System_Inbox` for human triage.

### Multiple MCP servers + tool name collisions

throughline uses bare names (`save_conversation` etc.) — if you've
got another MCP server installed that also exposes a tool by the
same name, the host client may pick one or the other. Check your
client's MCP server registration order; if a collision happens,
[file an issue](https://github.com/jprodcc-rodc/throughline/issues)
and we'll consider namespacing in a minor bump.

---

## Architecture

The MCP server is a thin client of throughline's existing core. No
shared code is duplicated; the MCP form just exposes save / recall
/ list as tool surfaces.

```text
   ┌───────────────────────────────────────────┐
   │ Claude Desktop / Code / Cursor / etc.     │
   │ (MCP-aware host)                          │
   └─────────────────┬─────────────────────────┘
                     │ stdio (JSON-RPC, MCP spec)
                     ▼
   ┌───────────────────────────────────────────┐
   │ python -m mcp_server                      │
   │  ├─ tools/save_conversation.py            │
   │  ├─ tools/recall_memory.py                │
   │  └─ tools/list_topics.py                  │
   └────┬────────────────┬────────────────┬────┘
        │ filesystem     │ HTTP           │ filesystem read +
        │ write          │ POST           │ daemon.taxonomy import
        ▼                ▼                ▼
   ┌──────────┐   ┌──────────────┐   ┌──────────────┐
   │ daemon/  │   │ rag_server/  │   │ vault + tax. │
   │ (existing│   │ (existing,   │   │ (existing)   │
   │ watchdog)│   │ :8000)       │   │              │
   └──────────┘   └──────────────┘   └──────────────┘
```

Three integration points, all via existing surfaces:

1. `save_conversation` writes raw `.md` to `$THROUGHLINE_RAW_ROOT`;
   the existing watchdog picks up automatically.
2. `recall_memory` HTTP POSTs to `localhost:8000/v1/rag`; the
   rag_server is unchanged.
3. `list_topics` reads `daemon.taxonomy.VALID_X_SET` + walks
   `$THROUGHLINE_VAULT_ROOT` for card counts.

Zero shared core changes — confirmed by an audit before
implementation. See [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) for
how this fits into the broader pipeline.

---

## Limitations (Phase 1)

These are explicit Phase 1 cuts. Most graduate to Phase 2 if dogfood
data justifies them:

- **No `wait_for_refine`** — the param exists in the
  `save_conversation` schema but is currently a no-op. Adding it
  requires polling daemon state, which is Phase 2 polish.
- **No reflection tools** — Open Threads / Contradiction Surfacing
  / Drift Detection (the differentiation features sketched in
  ROADMAP) are Phase 2+, gated behind a 4-criteria dogfood
  decision after Phase 1 ships.
- **No SSE / network transport** — only stdio. Add SSE if a real
  use case (remote MCP, multi-machine setup) emerges.
- **No `--doctor` subcommand on the MCP server itself** — for now,
  use `python -m throughline_cli doctor` which checks the same
  prerequisites the MCP server depends on. Phase 1.5 polish.

---

## Reporting issues

If something doesn't work as described:

1. Run `python -m throughline_cli doctor` and capture the output
   (redact paths if you prefer).
2. Capture relevant lines from `~/throughline_runtime/logs/refine_daemon.log`.
3. [Open an issue](https://github.com/jprodcc-rodc/throughline/issues/new?template=bug_report.yml).

For security-sensitive issues, see [`SECURITY.md`](../SECURITY.md).
