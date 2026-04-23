"""v0.2.0 install wizard — 16 steps, mission-branched, TUI-coloured.

Entry point:
    python install.py          (at repo root)
    python -m throughline_cli  (once packaging lands)

Each step is a function that takes the running `WizardConfig`, prompts
the user, updates the config in place, and returns. Mission branching
in step 2 sets `cfg.mission` which subsequent steps read to decide
whether to skip (`return "SKIPPED"`) or run.

Every step has a sensible default — pressing Enter walks the user onto
a working Full-flywheel config without any typing. Visual rendering is
handled by the `ui` module; this file stays focused on flow + logic.

Tests stub `builtins.input` to drive the interactive paths; `ui` uses
`input()` under the hood so those stubs continue to work.
"""
from __future__ import annotations

import sys
from typing import Callable, Optional

from . import ui
from .config import WizardConfig, load, save


TOTAL = 16


# ---------- step functions ----------


def step_01_env(cfg: WizardConfig) -> Optional[str]:
    ui.step_header(1, TOTAL, "Python + dependencies")
    ui.info_line(f"Python: {sys.version.split()[0]}")
    ui.info_line("(Dependency install is handled separately via "
                 "`pip install -r requirements.txt` or `pip install -e .` — "
                 "this step is a placeholder until the wizard can shell "
                 "out safely.)")
    return None


def step_02_mission(cfg: WizardConfig) -> Optional[str]:
    """U24 — the single most important branch."""
    ui.step_header(2, TOTAL, "Mission — what is throughline for you?")
    ui.intro("The biggest choice in the wizard. It decides whether cards "
             "are for reading, for retrieval, or both. Same conversation, "
             "three different end states:")

    ui.subrule("[1] Full flywheel — cards in Obsidian AND indexed for RAG")
    ui.panel_example(
        "After each chat",
        "```\n"
        "Obsidian vault:   40_Learning/pytorch_mps_m2.md  (readable 6-section card)\n"
        "Vector DB:        card + embeddings, retrievable\n"
        "Next chat:        'how did I set up MPS?'\n"
        "                   -> RAG injects the card -> LLM cites it\n"
        "```\n",
        pick_if="you want Obsidian as knowledge garden AND you want the "
                "LLM to remember past conclusions.",
    )

    ui.subrule("[2] RAG-only — cards are machine food, you never read them")
    ui.panel_example(
        "After each chat",
        "```\n"
        "Vault:            NOT USED AS A READING SURFACE\n"
        "                  (files exist on disk, but dense, not prose)\n"
        "Vector DB:        title + entities + 3-8 atomic claims\n"
        "Next chat:        'how did I set up MPS?'\n"
        "                   -> RAG injects claims -> LLM cites them\n"
        "```\n",
        pick_if="you use throughline as pure LLM memory; Obsidian is not "
                "part of your workflow. Cheapest refine by 40x (~$0.001/conv).",
    )

    ui.subrule("[3] Notes-only — Obsidian cards, no RAG infrastructure")
    ui.panel_example(
        "After each chat",
        "```\n"
        "Obsidian vault:   40_Learning/pytorch_mps_m2.md  (readable 6-section card)\n"
        "Vector DB:        NOT INSTALLED\n"
        "Next chat:        normal LLM reply, no enrichment\n"
        "```\n",
        pick_if="you want a smart summariser that drops refined notes into "
                "Obsidian but don't want the daemon/embedder/Qdrant stack.",
    )

    cfg.mission = ui.pick_option(
        "Pick your mission:",
        [
            ("full",       "Full flywheel",  ""),
            ("rag_only",   "RAG-only",       ""),
            ("notes_only", "Notes-only",     ""),
        ],
        default_key="full",
    )
    # Mission-dependent default adjustments.
    if cfg.mission == "rag_only":
        cfg.card_structure = "rag_optimized"
        cfg.refine_tier = "skim"
    elif cfg.mission == "notes_only":
        cfg.vector_db = "none"
        cfg.embedder = "none"
        cfg.reranker = "none"
    return None


def step_03_vector_db(cfg: WizardConfig) -> Optional[str]:
    """U21 — skipped for Notes-only missions."""
    if cfg.mission == "notes_only":
        ui.step_header(3, TOTAL, "Vector DB — SKIPPED (Notes-only, no RAG)")
        return "SKIPPED"
    ui.step_header(3, TOTAL, "Vector DB")
    cfg.vector_db = ui.pick_option(
        "Pick a vector DB backend:",
        [
            ("qdrant",     "Qdrant (needs Docker)",          "Production-ready. Millions of cards. Default for Full."),
            ("chroma",     "Chroma (pip install)",           "Embeddable. Lowest setup. Good to 10K cards."),
            ("lancedb",    "LanceDB (embedded Rust)",        "File-based. Fast. Good to 100K."),
            ("duckdb_vss", "DuckDB + VSS extension",         "SQL-friendly. File-based. Good to 100K."),
            ("sqlite_vec", "SQLite + sqlite-vec",            "Smallest footprint. Good to 10K."),
            ("pgvector",   "pgvector (requires Postgres)",   "If you already run Postgres."),
        ],
        default_key="qdrant" if cfg.privacy != "local_only" else "chroma",
    )
    return None


def step_04_api_key(cfg: WizardConfig) -> Optional[str]:
    ui.step_header(4, TOTAL, "API key")
    ui.info_line("For v0.2.0-dev we don't collect the key here; set it via "
                 "env var OPENROUTER_API_KEY (or OPENAI_API_KEY) in your "
                 "shell. Re-run `python install.py --step 4` once set.")
    return None


def step_05_llm_provider(cfg: WizardConfig) -> Optional[str]:
    """U11 — provider matrix."""
    ui.step_header(5, TOTAL, "LLM provider")
    cfg.llm_provider_id = ui.pick_option(
        "Pick a default provider model:",
        [
            ("anthropic/claude-sonnet-4.6", "Anthropic Sonnet 4.6",  "Default, balanced quality/cost"),
            ("anthropic/claude-haiku-4.5",  "Anthropic Haiku 4.5",   "Cheap / fast"),
            ("anthropic/claude-opus-4.7",   "Anthropic Opus 4.7",    "Expensive / best quality"),
            ("openai/gpt-5-mini",           "OpenAI GPT-5-mini",     "Alt cheap option"),
            ("google/gemini-3-flash",       "Google Gemini 3 Flash", "Alt cheap; judgement-friendly"),
            ("xai/grok-3",                  "xAI Grok 3",            "Timely content, coding"),
            ("deepseek/v3.2",               "DeepSeek v3.2",         "Cheapest Sonnet-class alternative"),
        ],
        default_key="anthropic/claude-sonnet-4.6",
    )
    # Auto-derive prompt family (U22).
    if cfg.llm_provider_id.startswith("anthropic/"):
        cfg.prompt_family = "claude"
    elif cfg.llm_provider_id.startswith("openai/"):
        cfg.prompt_family = "gpt"
    elif cfg.llm_provider_id.startswith("google/"):
        cfg.prompt_family = "gemini"
    else:
        cfg.prompt_family = "generic"
    return None


def step_06_privacy(cfg: WizardConfig) -> Optional[str]:
    """U18 — privacy level, orthogonal to refine tier."""
    ui.step_header(6, TOTAL, "Privacy level")
    cfg.privacy = ui.pick_option(
        "How much of the pipeline may hit the cloud?",
        [
            ("local_only", "Local-only", "Ollama + bge-m3 only. Slowest, fully private."),
            ("hybrid",     "Hybrid",     "Refine via API, embed/rerank locally. Default."),
            ("cloud_max",  "Cloud-max",  "Everything via API. Fastest, most exposed."),
        ],
        default_key="hybrid",
    )
    return None


def step_07_retrieval(cfg: WizardConfig) -> Optional[str]:
    """U12 + U20 — embedder + reranker paired."""
    if cfg.mission == "notes_only":
        ui.step_header(7, TOTAL, "Retrieval backend — SKIPPED (Notes-only)")
        return "SKIPPED"
    ui.step_header(7, TOTAL, "Retrieval backend (embedder + reranker)")
    cfg.embedder = ui.pick_option(
        "Embedder:",
        [
            ("bge-m3",                       "BGE-M3 (local, 1024d)",                       "Default. 9/10 quality. ~8GB RAM."),
            ("openai-text-embedding-3-large","OpenAI text-embedding-3-large (API, 3072d)",  "No local GPU."),
            ("nomic-embed-text-v1.5",        "nomic-embed v1.5 (local, 768d)",              "Lighter, 8/10 quality."),
            ("all-MiniLM-L6-v2",             "all-MiniLM-L6-v2 (local, 384d)",              "CPU-only minimum viable."),
            ("voyage-3",                     "Voyage voyage-3 (API, 1024d)",                "Long-document retrieval."),
        ],
        default_key="bge-m3",
    )
    cfg.reranker = ui.pick_option(
        "Reranker:",
        [
            ("bge-reranker-v2-m3",    "BGE reranker v2-m3 (local)",     "Default. 9/10. 2.3GB model."),
            ("bge-reranker-v2-gemma", "BGE reranker v2-gemma (local)",  "Newer, larger."),
            ("cohere-rerank-v3",      "Cohere rerank-v3 (API)",         "No local RAM."),
            ("voyage-rerank-2",       "Voyage rerank-2 (API)",          "Long-text friendly."),
            ("jina-rerank-v2",        "Jina reranker v2 (API)",         "Cheapest API."),
            ("skip",                  "Skip reranker (embedding-only)", "Fastest, least precise. 7/10."),
        ],
        default_key="bge-reranker-v2-m3",
    )
    return None


def step_08_prompt_family(cfg: WizardConfig) -> Optional[str]:
    """U22 — auto-derived, confirm only."""
    ui.step_header(8, TOTAL, "Prompt family")
    ui.info_line(f"Auto-derived from provider: [bold]{cfg.prompt_family}[/]")
    ui.info_line("Claude -> XML tags / GPT -> Markdown+JSON / "
                 "Gemini -> structured output / else generic plain.")
    if not ui.ask_yes_no("Accept?", default=True):
        cfg.prompt_family = ui.pick_option(
            "Override prompt family:",
            [
                ("claude",  "claude (XML tags)",          ""),
                ("gpt",     "gpt (Markdown+JSON schema)", ""),
                ("gemini",  "gemini (structured output)", ""),
                ("generic", "generic (plain Markdown)",   ""),
            ],
            default_key="generic",
        )
    return None


def step_09_import_source(cfg: WizardConfig) -> Optional[str]:
    """U2 — import adapters, with cold-start warning if fresh."""
    ui.step_header(9, TOTAL, "Import source")
    cfg.import_source = ui.pick_option(
        "Do you have existing LLM chat history to import?",
        [
            ("chatgpt",  "ChatGPT export (ZIP)",           ""),
            ("claude",   "Claude export (ZIP)",            ""),
            ("gemini",   "Gemini Google Takeout (ZIP)",    ""),
            ("multiple", "Multiple sources",               "Run the wizard again per source later."),
            ("none",     "No, start fresh",                "Cold start: RAG silent for ~50 conversations."),
        ],
        default_key="none",
    )
    if cfg.import_source == "none" and cfg.mission != "notes_only":
        ui.warn_box(
            "Cold-start warning",
            "Starting with an empty knowledge base means:\n"
            "  - RAG will not fire for ~50 conversations (~2 weeks of typical use)\n"
            "  - Initial replies feel like plain ChatGPT (no enrichment)\n"
            "  - Cards accumulate organically as you chat.",
        )
        if not ui.ask_yes_no("Still proceed with a fresh start?", default=True):
            ui.info_line("Re-picking import source...")
            return step_09_import_source(cfg)
    if cfg.import_source != "none":
        cfg.import_path = ui.ask_text("Path to the export file",
                                       "~/Downloads/export.zip")
    return None


def step_10_import_scan(cfg: WizardConfig) -> Optional[str]:
    if cfg.import_source == "none":
        ui.step_header(10, TOTAL, "Import scan — SKIPPED (fresh start)")
        return "SKIPPED"
    ui.step_header(10, TOTAL, f"Import scan ({cfg.import_source})")
    ui.info_line("(U2 adapter not yet implemented — stub prints intended "
                 "action only.)")
    ui.info_line(f"Would scan: {cfg.import_path}")
    return None


def step_11_refine_tier(cfg: WizardConfig) -> Optional[str]:
    """U15 — three tiers, 40x cost spread, examples per tier."""
    if cfg.mission == "rag_only":
        ui.step_header(11, TOTAL,
                       "Refine tier — FIXED to 'skim' (RAG-only mission)")
        ui.info_line("RAG-only mode uses a single Haiku call to emit "
                     "title + entities + 3-8 claims per conversation. "
                     "~$0.001/conv.")
        return "SKIPPED"

    ui.step_header(11, TOTAL, "Refine tier")
    ui.intro("Tier controls how many LLM passes each conversation gets and "
             "which model does them. Same input, three output densities. "
             "Below: the SAME source conversation refined at each tier, "
             "showing what you pay for and what you get.")

    ui.subrule("[1] Skim — ~$0.005/conv (one Haiku call)")
    ui.panel_example(
        "Skim output",
        "# PyTorch MPS on M2 Mac\n\n"
        "Use `torch.device('mps')`. Install via conda nightly channel. "
        "Set `PYTORCH_ENABLE_MPS_FALLBACK=1` for unsupported ops.\n\n"
        "`#pytorch`\n",
        pick_if="you want a searchable index of old chat history. Card "
                "is a flashcard, not a knowledge note. Cost for 1,247 "
                "imported conversations: ~$6.",
    )

    ui.subrule("[2] Normal — ~$0.04/conv (Sonnet slice + refine + route · default)")
    ui.panel_example(
        "Normal output — the full 6-section skeleton",
        "# PyTorch MPS on M2 Mac\n\n"
        "## Scenario & pain point\n"
        "Why this matters. What triggered you to search it up.\n\n"
        "## Core knowledge & first principles\n"
        "Metal Performance Shaders backend, cousin to CUDA, dispatches via torch.\n\n"
        "## Execution — step-by-step\n"
        "1. Install via conda nightly.\n"
        "2. Use `torch.device('mps')`.\n"
        "3. Flip `PYTORCH_ENABLE_MPS_FALLBACK=1` if ops are missing.\n\n"
        "## Avoid — pitfalls and edges\n"
        "Sparse ops / some reductions still hit CPU.\n\n"
        "## Insight & mental model\n"
        "Treat `mps` like `cuda` with a smaller op set.\n\n"
        "## Summary\n"
        "MPS on M2 = near-CUDA dev ergonomics with known gaps.\n",
        pick_if="daily use, readable cards, balanced quality/cost. "
                "Cost for 1,247 imports: ~$48.",
    )

    ui.subrule("[3] Deep — ~$0.20/conv (Opus multi-pass + critique + refs)")
    ui.panel_example(
        "Deep output — Normal's 6 sections PLUS:",
        "## Self-critique (from pass 2)\n"
        "- 'Avoid' section weak on memory-fragmentation at large batch; "
        "pass 2 pulled 2 stackoverflow threads to strengthen it.\n"
        "- 'Core knowledge' should link FSDP/DDP for multi-GPU interop.\n\n"
        "## Cross-refs (from pass 3)\n"
        "- Card: M1 MPS benchmarking notes (72% overlap)\n"
        "- Card: CUDA -> MPS migration checklist (54% overlap)\n"
        "- Open question propagated from: pytorch-2.0 release card\n",
        pick_if="decision-making, research projects, 'this matters for "
                "months', or you want an audit trail of what the refiner "
                "considered and dismissed. Cost for 1,247 imports: ~$240.",
    )

    ui.info_line(f"Current daily budget cap: ${cfg.daily_budget_usd}. "
                 f"Smart suggestion will show at step 15.")
    cfg.refine_tier = ui.pick_option(
        "How deep should the refiner think on each conversation?",
        [
            ("skim",   "Skim   (~$0.005/conv, one Haiku call)",             ""),
            ("normal", "Normal (~$0.04/conv, Sonnet 6-section)",            ""),
            ("deep",   "Deep   (~$0.20/conv, Opus multi-pass + critique)",  ""),
        ],
        default_key="normal",
    )
    return None


def step_12_card_structure(cfg: WizardConfig) -> Optional[str]:
    """U16 — card structure; fixed for RAG-only (U25)."""
    if cfg.mission == "rag_only":
        ui.step_header(12, TOTAL,
                       "Card structure — FIXED to 'rag_optimized' (U25)")
        ui.panel_example(
            "Fixed RAG-optimized format",
            "```yaml\n"
            "---\n"
            'title: "Setting up PyTorch on M2 Mac with MPS backend"\n'
            "entities: [PyTorch, M2 Mac, MPS, Apple Silicon, GPU]\n"
            "---\n"
            "```\n"
            "- PyTorch 2.0+ supports MPS backend natively\n"
            "- Use `torch.device('mps')` instead of `cuda`\n"
            "- Fallback: `PYTORCH_ENABLE_MPS_FALLBACK=1`\n"
            "- Install: `conda install pytorch torchvision -c pytorch-nightly`\n"
            "- Verify: `torch.backends.mps.is_available()`\n",
        )
        return "SKIPPED"

    ui.step_header(12, TOTAL, "Card structure")
    ui.intro("A 'card' is what the refine daemon writes after each "
             "conversation. It lives in your Obsidian vault as Markdown "
             "AND is embedded into the RAG retrieval index. You can "
             "re-refine with a different shape later via "
             "`python install.py --step 12`. Three shapes ship:")

    ui.subrule("[1] Compact — title + one paragraph + tags")
    ui.panel_example(
        "Compact card",
        "# Setting up PyTorch MPS on M2 Mac\n\n"
        "PyTorch 2.0+ supports MPS natively via `torch.device('mps')`. "
        "Set `PYTORCH_ENABLE_MPS_FALLBACK=1` for unsupported ops. Install "
        "via `conda install pytorch torchvision -c pytorch-nightly`, then "
        "verify with `torch.backends.mps.is_available()`.\n\n"
        "`#pytorch` `#m2` `#mps`\n",
        pick_if="you think in single atomic claims, want small cards, "
                "prefer Zettelkasten-style linking over narrative notes.",
    )

    ui.subrule("[2] Standard — 6-section skeleton (default, current v0.1 shape)")
    ui.panel_example(
        "Standard card",
        "# Setting up PyTorch MPS on M2 Mac\n\n"
        "## Scenario & pain point\n"
        "Why this matters. What triggered you to search it up.\n\n"
        "## Core knowledge & first principles\n"
        "Metal Performance Shaders backend, cousin to CUDA.\n\n"
        "## Execution — step-by-step\n"
        "1. Install via conda nightly.\n"
        "2. Use `torch.device('mps')`.\n"
        "3. Flip `PYTORCH_ENABLE_MPS_FALLBACK=1` if ops are missing.\n\n"
        "## Avoid — pitfalls and edges\n"
        "Sparse ops / some reductions -> CPU.\n\n"
        "## Insight & mental model\n"
        "Treat 'mps' like 'cuda' with gaps.\n\n"
        "## Summary\n"
        "MPS on M2 = near-CUDA dev ergonomics with known gaps.\n",
        pick_if="you want cards a future-you can read cold and immediately "
                "recomprehend, with narrative scaffolding.",
    )

    ui.subrule("[3] Detailed — Standard + sidebar (research-grade)")
    ui.panel_example(
        "Detailed card (tail only — add after Standard's 6 sections)",
        "---\n"
        "Related cards: M1 GPU benchmarking notes, CUDA-MPS diff summary\n\n"
        "Contradictions: 2023 docs said 'experimental'; 2024 says GA\n\n"
        "Open questions: does FAISS-GPU work on MPS yet?\n\n"
        "Confidence: 0.85 (multi-source, 3 independent tests)\n",
        pick_if="decision-making / research projects; you want to track "
                "confidence + related work + open threads alongside content. "
                "Costs ~20% more per refine than Standard.",
    )

    ui.info_line("After you pick, step 13 refines ONE real conversation "
                 "with this shape so you can see the actual result before "
                 "committing to bulk refine.")
    cfg.card_structure = ui.pick_option(
        "Pick a card shape:",
        [
            ("compact",  "Compact (title + 1 paragraph + tags)",  ""),
            ("standard", "Standard (6-section skeleton)",         ""),
            ("detailed", "Detailed (6 sections + sidebar)",       ""),
        ],
        default_key="standard",
    )
    return None


def step_13_preview(cfg: WizardConfig) -> Optional[str]:
    """U17 + U23 — preview + 5-dial constrained edit."""
    ui.step_header(13, TOTAL, "First-card preview + 5-dial edit")
    ui.info_line("(Preview runs a real refine on ONE conversation at the "
                 "chosen tier. Not yet implemented in skeleton — stub "
                 "accepts defaults for the 5 dials.)")
    return None


def step_14_taxonomy(cfg: WizardConfig) -> Optional[str]:
    """U13 — LLM-derived from user's content, with template fallback."""
    ui.step_header(14, TOTAL, "Taxonomy")
    cfg.taxonomy_source = ui.pick_option(
        "How should throughline pick card folders?",
        [
            ("derive_from_vault",   "Derive from my existing Obsidian vault", "LLM scans vault dirs + samples, proposes taxonomy.py"),
            ("derive_from_imports", "Derive from my first 30 imported convs", "LLM clusters refined cards, proposes taxonomy.py"),
            ("jd",                  "Fallback: Johnny Decimal template",       "10-90 number-prefixed top-level folders"),
            ("para",                "Fallback: PARA template",                 "Projects / Areas / Resources / Archive"),
            ("zettel",              "Fallback: Zettelkasten template",         "Flat folder, linked atomic notes"),
        ],
        default_key="derive_from_imports" if cfg.import_source != "none" else "derive_from_vault",
    )
    return None


def step_15_budget(cfg: WizardConfig) -> Optional[str]:
    """U3 — daily budget cap."""
    ui.step_header(15, TOTAL, "Daily USD budget cap")
    ui.info_line("Daemon pauses its refine queue once daily spend hits "
                 "this cap.")
    raw = ui.ask_text("Daily budget (USD)", str(cfg.daily_budget_usd))
    try:
        cfg.daily_budget_usd = float(raw)
    except ValueError:
        ui.info_line(f"[yellow]Not a number, keeping ${cfg.daily_budget_usd}[/]")
    return None


def step_16_summary(cfg: WizardConfig) -> Optional[str]:
    ui.step_header(16, TOTAL, "Summary")
    ui.kv_row("mission", cfg.mission)
    if cfg.mission != "notes_only":
        ui.kv_row("vector_db", cfg.vector_db)
    ui.kv_row("llm_provider", cfg.llm_provider_id)
    ui.kv_row("privacy", cfg.privacy)
    if cfg.mission != "notes_only":
        ui.kv_row("embedder", cfg.embedder)
        ui.kv_row("reranker", cfg.reranker)
    ui.kv_row("prompt_family", cfg.prompt_family)
    src = cfg.import_source + (f" ({cfg.import_path})" if cfg.import_path else "")
    ui.kv_row("import_source", src)
    ui.kv_row("refine_tier", cfg.refine_tier)
    ui.kv_row("card_structure", cfg.card_structure)
    ui.kv_row("taxonomy_source", cfg.taxonomy_source)
    ui.kv_row("daily_budget_usd", f"${cfg.daily_budget_usd}")
    if not ui.ask_yes_no("Write this to ~/.throughline/config.toml?",
                         default=True):
        ui.info_line("[red]Aborted — no config written.[/]")
        sys.exit(0)
    return None


# ---------- orchestrator ----------

ALL_STEPS: list[tuple[int, Callable[[WizardConfig], Optional[str]]]] = [
    (1,  step_01_env),
    (2,  step_02_mission),
    (3,  step_03_vector_db),
    (4,  step_04_api_key),
    (5,  step_05_llm_provider),
    (6,  step_06_privacy),
    (7,  step_07_retrieval),
    (8,  step_08_prompt_family),
    (9,  step_09_import_source),
    (10, step_10_import_scan),
    (11, step_11_refine_tier),
    (12, step_12_card_structure),
    (13, step_13_preview),
    (14, step_14_taxonomy),
    (15, step_15_budget),
    (16, step_16_summary),
]


def run_wizard(cfg: Optional[WizardConfig] = None,
               only_step: Optional[int] = None) -> WizardConfig:
    cfg = cfg or load()
    for n, fn in ALL_STEPS:
        if only_step is not None and n != only_step:
            continue
        result = fn(cfg)
        if result != "SKIPPED":
            if n not in cfg.completed_steps:
                cfg.completed_steps.append(n)
    path = save(cfg)
    ui.print_blank()
    ui.info_line(f"[green]Config written:[/] {path}")
    return cfg


def effective_step_list(mission: str) -> list[int]:
    """Pure function used by tests: which step numbers execute per mission."""
    steps = list(range(1, 17))
    if mission == "notes_only":
        steps = [s for s in steps if s not in (3, 7, 10)]
    elif mission == "rag_only":
        steps = [s for s in steps if s not in (12,)]
    return steps


def main(argv: Optional[list[str]] = None) -> int:
    # Windows terminals default to GBK / cp1252; reconfigure stdio to UTF-8
    # so box characters + emoji render instead of crashing.
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if callable(reconf):
            try:
                reconf(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    argv = argv if argv is not None else sys.argv[1:]
    only = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--step"):
            tail = a.split("=", 1)[1] if "=" in a else None
            if tail is None and i + 1 < len(argv):
                tail = argv[i + 1]
                i += 1
            if tail:
                try:
                    only = int(tail)
                except ValueError:
                    ui.console.print(f"[red]Bad --step value:[/] {tail}")
                    return 2
        i += 1
    run_wizard(only_step=only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
