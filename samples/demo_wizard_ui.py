"""VISUAL component demo (NOT the install — see install.py for that).

This script is a 30-second visual showcase of the THREE new UI
components used INSIDE the 16-step install wizard. It is NOT itself
a wizard. It does not configure anything, install anything, or
write any file.

The real install is still:
    python install.py             # full 16-step wizard
    python install.py --express   # auto-detect + 1-command install

This file shows only the LOOK of the components those wizards use:
- T1: arrow-key picker (used in 10 of the 16 wizard steps)
- T2: rich spinner during blocking ops (steps 10, 13, 16)
- T3: hierarchical summary tree (step 16's final summary)

Run it to see how the components render in your terminal — then go
run the real wizard.
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
    ui.section_title("UI component preview — NOT an install")
    ui.print_blank()
    ui.info_line(
        "[bold yellow]This is not the wizard.[/] It's a 30-second visual "
        "demo of the 3 reusable UI components the wizard uses internally. "
        "Nothing here writes config or calls an LLM."
    )
    ui.info_line(
        "[dim]For the real install, exit this and run "
        "[green]python install.py[/][dim] (16 steps) or "
        "[green]python install.py --express[/][dim] (1 command).[/]"
    )
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
        "The wizard's step 3 (vector DB picker) is now a multi-line "
        "menu with arrow-key navigation. To prove you can see it:"
    )
    ui.print_blank()
    ui.info_line(
        "[bold yellow]Round 1:[/] press [bold]Enter[/] to accept the "
        "default ([cyan]Qdrant[/]). You should see a 6-line menu with "
        "[cyan]❯[/] pointing at the highlighted row."
    )
    ui.print_blank()
    options = [
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
    ]
    pick1 = ui.pick_option(
        "Round 1 — accept default with Enter:",
        options,
        default_key="qdrant",
    )
    ui.info_line(
        f"[green]✓[/] Round 1 picked: [bold]{pick1}[/]")
    ui.print_blank()

    ui.info_line(
        "[bold yellow]Round 2:[/] this time the default is [cyan]chroma[/]. "
        "Press [bold]↓ ↓[/] (down arrow twice) then [bold]Enter[/] to "
        "land on [cyan]duckdb_vss[/]. Try it — proves the arrow keys "
        "work and your pick wasn't predetermined."
    )
    ui.print_blank()
    pick2 = ui.pick_option(
        "Round 2 — navigate with ↓ ↓ then Enter:",
        options,
        default_key="chroma",
    )
    if pick2 == "duckdb_vss":
        ui.info_line(
            f"[green]✓[/] Round 2 picked: [bold]{pick2}[/] — arrow-key "
            f"navigation confirmed. Cursor started on chroma, you "
            f"pressed ↓ ↓ Enter, landed on duckdb_vss.")
    elif pick2 == "chroma":
        ui.info_line(
            f"[yellow]Round 2 picked: [bold]{pick2}[/] — you hit Enter "
            f"without navigating. The cursor was on chroma (the new "
            f"default), so you accepted it. Run again and try ↓ ↓.[/]")
    elif pick2 == "qdrant":
        # If we reach this branch, questionary's `default=` parameter
        # is being ignored — the cursor stuck on the first option
        # (qdrant). This was an actual bug fixed in the same commit
        # that updated this demo (was passing a Choice instance, now
        # passing the value string). Surface as a warning if it
        # somehow reappears.
        ui.info_line(
            f"[red]Round 2 picked: [bold]{pick2}[/] — this means the "
            f"cursor started on qdrant, not chroma. The default= "
            f"parameter is being ignored. Open an issue.[/]")
    else:
        ui.info_line(
            f"[green]✓[/] Round 2 picked: [bold]{pick2}[/] — arrow-key "
            f"navigation confirmed (you landed somewhere other than the "
            f"chroma default).")
    ui.print_blank()

    # ---- T2: animated spinner ----
    ui.section_title("[2/3] T2: animated spinner")
    ui.info_line(
        "Step 13 (first-card preview) blocks for 5-30 seconds while "
        "the LLM responds. Without the spinner, the screen sat blank "
        "and users wondered if the wizard hung. Watch for the rotating "
        "[bold]⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏[/] character at the start of each "
        "phase — it stays animated for the full duration:"
    )
    ui.print_blank()
    with ui.status("Phase 1/3 — connecting to api.anthropic.com...") as s:
        time.sleep(2.5)
        s.update("Phase 2/3 — sending refiner prompt + slice (1.2 KB)...")
        time.sleep(2.5)
        s.update("Phase 3/3 — awaiting response (cache miss; ~2-30s typical)...")
        time.sleep(2.5)
    ui.info_line("[green]✓[/] LLM call complete (faked) — total ~7.5s "
                  "with three phase transitions.")
    ui.info_line(
        "[dim]Note: rich's `console.status()` clears its line on exit, "
        "so the spinner leaves no trace once done. That's by design — "
        "the user only sees what's NEW after the operation finishes.[/]"
    )
    ui.print_blank()

    # ---- T3: summary tree ----
    ui.section_title("[3/3] T3: step-16 summary tree")
    ui.info_line("Final step. Same data the old flat KV listing showed, "
                  "but grouped semantically:")
    ui.print_blank()
    _demo_tree(_make_demo_cfg())
    ui.print_blank()
    ui.section_title("Demo finished — nothing was installed")
    ui.info_line(
        "[bold]No config was written. No LLM was called.[/] This was "
        "purely a visual preview of the wizard's 3 reusable UI "
        "components."
    )
    ui.info_line("")
    ui.info_line("[bold]To actually install throughline, run ONE of:[/]")
    ui.info_line(
        "  [green]python install.py --express[/]     "
        "[dim]# 1 command, auto-detects your API key, ~3 seconds[/]"
    )
    ui.info_line(
        "  [green]python install.py[/]               "
        "[dim]# full 16-step wizard, every option explained[/]"
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
