"""Self-contained demo of the wizard's three UX layers.

Run this in a REAL terminal (not piped, not in CI) to see:
- T1: questionary-based arrow-key picker
- T2: animated rich spinner during a simulated LLM call
- T3: hierarchical summary tree at step 16

    python samples/demo_wizard_ui.py

It does NOT call any LLM, does NOT write any config — purely a visual
demonstration so you can decide if you like the look before running
the actual wizard.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from throughline_cli import ui

    ui.banner()
    ui.section_title("throughline wizard UX demo (no real install)")
    ui.print_blank()

    if not sys.stdin.isatty():
        ui.info_line(
            "[yellow]This demo wants a real terminal — your stdin is "
            "redirected (pipe / CI / capture). Re-run interactively "
            "to see the arrow-key picker + animated spinner.[/]"
        )
        ui.info_line("Showing the static parts (banner + tree) only.")
        ui.print_blank()
        _demo_tree(_make_demo_cfg())
        return 0

    # ---- T1: arrow-key picker ----
    ui.section_title("[1/3] T1: arrow-key picker")
    ui.info_line(
        "Press [bold]↑/↓[/] to move, [bold]Enter[/] to select. The "
        "wizard's step 3 (vector DB picker) looks like this:"
    )
    ui.print_blank()
    pick = ui.pick_option(
        "Pick a vector DB backend (demo — your pick is discarded):",
        [
            ("qdrant",     "Qdrant (needs Docker)",
             "Production-ready. Millions of cards. Default for Full."),
            ("chroma",     "Chroma (pip install)",
             "Embeddable. Lowest setup. Good to 10K cards."),
            ("lancedb",    "LanceDB (embedded Rust)",
             "File-based. Fast. Good to 100K."),
            ("duckdb_vss", "DuckDB + VSS extension",
             "SQL-friendly. File-based. Good to 100K."),
            ("sqlite_vec", "SQLite + sqlite-vec",
             "Smallest footprint. Good to 10K."),
            ("pgvector",   "pgvector (requires Postgres)",
             "If you already run Postgres."),
        ],
        default_key="qdrant",
    )
    ui.info_line(f"[green]✓[/] You selected: [bold]{pick}[/] (discarded)")
    ui.print_blank()

    # ---- T2: animated spinner ----
    ui.section_title("[2/3] T2: animated spinner")
    ui.info_line(
        "Step 13 (first-card preview) blocks for 5-30 seconds while "
        "the LLM responds. Without the spinner, the screen sat blank "
        "and users wondered if the wizard hung. Now:"
    )
    ui.print_blank()
    with ui.status("Calling claude-sonnet-4-5-20250929 (one refine pass)..."):
        time.sleep(3.0)  # simulate LLM round-trip
    ui.info_line("[green]✓[/] LLM call complete (faked).")
    ui.print_blank()

    # ---- T3: summary tree ----
    ui.section_title("[3/3] T3: step-16 summary tree")
    ui.info_line("Final step. Same data the old flat KV listing showed, "
                  "but grouped semantically:")
    ui.print_blank()
    _demo_tree(_make_demo_cfg())
    ui.print_blank()
    ui.info_line(
        "[dim]This was a UX demo — no config written, no LLM called. "
        "Run [green]python install.py --express[/][dim] to do an actual "
        "install.[/]"
    )
    return 0


def _make_demo_cfg():
    from throughline_cli.config import WizardConfig
    return WizardConfig(
        mission="full",
        vector_db="qdrant",
        llm_provider="anthropic",
        llm_provider_id="claude-sonnet-4-5-20250929",
        privacy="hybrid",
        embedder="bge-m3",
        reranker="bge-reranker-v2-m3",
        prompt_family="claude",
        refine_tier="normal",
        card_structure="standard",
        taxonomy_source="minimal",
        daily_budget_usd=20.0,
        import_source="claude",
        import_path="/Users/me/claude_export.zip",
        import_scanned=1247,
        import_emitted=1190,
        import_est_normal_cost_usd=12.50,
        import_est_skim_cost_usd=2.30,
    )


def _demo_tree(cfg) -> None:
    from throughline_cli import ui
    from throughline_cli.wizard import _build_summary_groups, _format_cost_line
    ui.summary_tree(_build_summary_groups(cfg))
    ui.print_blank()
    ui.info_line(
        f"[dim]Cost: {_format_cost_line(cfg.refine_tier, cfg.daily_budget_usd)}[/]"
    )


if __name__ == "__main__":
    raise SystemExit(main())
