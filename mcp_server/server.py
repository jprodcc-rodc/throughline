"""FastMCP application factory.

Phase 1 (v0.2.x, shipped) registered 3 real tools:
- save_conversation, recall_memory, list_topics

Phase 2 (v0.3, in progress) adds 3 more for the Reflection Layer:
- find_loose_ends, check_consistency, get_position_drift

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
from mcp_server.tools.save_refined_card import save_refined_card
from mcp_server.tools.recall_memory import recall_memory
from mcp_server.tools.list_topics import list_topics
from mcp_server.tools.find_loose_ends import find_loose_ends
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
    #
    # NOTE: save_conversation (raw-queue → daemon refines via paid
    # API) is deliberately NOT registered as an MCP tool. MCP-aware
    # hosts (Claude Desktop / Code / Cursor / Continue.dev) are
    # always subscription-billed → save_refined_card (host-LLM
    # refines on subscription budget) is the only save path users
    # should ever hit through MCP. Removing save_conversation
    # eliminates the docstring tie-break problem where Claude could
    # accidentally pick the paid path.
    #
    # The OpenWebUI Filter form is unaffected — it never used the
    # MCP save_conversation tool. OpenWebUI's exporter writes raw
    # .md to RAW_ROOT directly and the daemon picks up via watchdog.
    # The save_conversation function still ships in the package
    # (for callers that import the module directly, e.g. bulk
    # import scripts) but is not auto-exposed via MCP.
    app.tool()(save_refined_card)
    app.tool()(recall_memory)
    app.tool()(list_topics)

    # Phase 2: Reflection Layer (currently stub-tier; real impl
    # in subsequent commits once daemon + position_signal land).
    app.tool()(find_loose_ends)
    app.tool()(check_consistency)
    app.tool()(get_position_drift)

    # Discovery / onboarding entry point — closes the cold-start gap
    # where a fresh-install user with 0 cards has no natural trigger
    # for any of the other 6 tools.
    app.tool()(throughline_status)

    # Slash-command prompts — surface in MCP-aware hosts (Claude
    # Desktop / Code / Cursor) as `/<server>:<prompt>` shortcuts.
    # Each expands into a chat message that triggers the matching
    # tool flow + summary, so power users don't have to retype the
    # natural-language phrase every time.
    @app.prompt()
    def overview() -> str:
        """Quick vault state check + next-step menu.

        Triggers throughline_status and asks the user what to do
        next: list topics, surface open threads, or recall on a
        specific topic.
        """
        return (
            "Call the throughline_status tool. Then summarise the "
            "result in one or two short paragraphs covering: "
            "tagged_card_count and total_md_files (mention the gap "
            "as profile drafts / indexes / pending-taxonomy items), "
            "domain_count, last Reflection Pass age, and overall "
            "_status. Finish with a one-line menu offering: list "
            "topics / surface open threads / recall on a query / "
            "save the current conversation."
        )

    @app.prompt()
    def loose_ends() -> str:
        """Surface unfinished reasoning grouped by topic.

        Triggers find_loose_ends and walks the user through the
        most-recently-touched loose ends, offering to resume any
        of them.

        Renamed from /threads (2026-04-28) to differentiate from
        Anthropic's Cowork **persistent agent thread** (2026-04-09
        GA), which is a TASK execution agent — completely different
        shape from throughline's introspective surfacing of
        unfinished thinking.
        """
        return (
            "Call the find_loose_ends tool with limit=5. Format "
            "the result as a numbered list, one entry per loose "
            "end: topic_cluster name + most recent date + a "
            "one-line summary of the open questions. Then ask the "
            "user which one they want to resume, or whether to "
            "surface more (re-call with limit=10)."
        )

    @app.prompt()
    def save_card() -> str:
        """Refine + save the current conversation as a card — zero
        LLM cost path.

        Tells the host LLM to synthesize a 6-section card from the
        conversation context using its own subscription, pick a
        domain, then call save_refined_card.
        """
        return (
            "Synthesize the current conversation into a structured "
            "knowledge card. Pick a coherent thread / decision / "
            "design rationale to capture; do not save trivia or "
            "small talk.\n\n"
            "Build a 6-section markdown body covering: scene & pain "
            "point, core knowledge & first principles, detailed "
            "execution plan, pitfalls & boundaries, insights & "
            "mental models, summary. English / Chinese / mixed all "
            "fine.\n\n"
            "Call list_topics first to learn the user's active X-axis "
            "taxonomy, then pick a domain that fits the content. Use "
            "knowledge_identity 'universal' unless the content is "
            "clearly personal_persistent (durable personal — e.g. "
            "current meds, ongoing projects).\n\n"
            "Finally call save_refined_card with the synthesized "
            "title / body / domain / knowledge_identity — this path "
            "is zero LLM cost (you do the refining on subscription, "
            "the tool just files the .md to vault). Report the "
            "card_path back to the user."
        )

    return app
