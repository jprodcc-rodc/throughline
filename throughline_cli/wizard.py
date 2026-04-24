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
from datetime import datetime
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
    ui.info_line("Keys are not persisted inside this config — set them "
                 "in your shell as env vars. Each provider uses its own "
                 "variable name; the wizard's multi-provider step (U28) "
                 "enumerates them per choice. Re-run "
                 "`python install.py --step 4` after setting the key.")
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
    if cfg.import_source in ("chatgpt", "claude", "gemini"):
        # Loop until the user gives a path that exists — fail fast here
        # rather than at step 10 where the adapter would stack-trace.
        while True:
            raw = ui.ask_text("Path to the export file",
                              "~/Downloads/export.zip")
            from pathlib import Path
            p = Path(raw).expanduser()
            if p.exists():
                cfg.import_path = str(p)
                break
            ui.info_line(f"[yellow]Not found:[/] {p}")
            if not ui.ask_yes_no("Try again?", default=True):
                ui.info_line("Switching to 'No, start fresh'.")
                cfg.import_source = "none"
                cfg.import_path = None
                break
    elif cfg.import_source == "multiple":
        ui.info_line("Multiple-source import runs the wizard once per source later. "
                     "For v0.2.0 first pass, pick one primary source now; run "
                     "`python -m throughline_cli import <other> <path>` afterwards.")
        cfg.import_source = "none"
    return None


def _adapter_limit() -> Optional[int]:
    """Honour THROUGHLINE_IMPORT_LIMIT env var so power users can cap
    the wizard's import at N items for smoke tests without pulling
    the adapter's --limit flag into the wizard UI."""
    import os as _os
    raw = _os.environ.get("THROUGHLINE_IMPORT_LIMIT", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _run_adapter_dry_run(cfg: WizardConfig):
    """Dispatch to the adapter's run() in dry-run mode; returns a
    summary dict (scanned/emitted/tokens/costs) or None on failure."""
    from pathlib import Path as _P
    path = _P(cfg.import_path) if cfg.import_path else None
    if path is None:
        return None
    if cfg.import_source == "claude":
        from .adapters import claude_export as adp
    elif cfg.import_source == "chatgpt":
        from .adapters import chatgpt_export as adp
    elif cfg.import_source == "gemini":
        from .adapters import gemini_takeout as adp
    else:
        return None
    try:
        summary = adp.run(path, dry_run=True, limit=_adapter_limit())
    except Exception as e:
        ui.info_line(f"[red]Scan failed:[/] {type(e).__name__}: {e}")
        return None
    return summary


def _import_source_tag(cfg: WizardConfig) -> str:
    """Stable tag the adapter writes into every imported MD's
    frontmatter. Exposed here so the U4 consent panel and step 16
    summary display the exact string users would later pass to
    bulk-purge tooling."""
    return f"{cfg.import_source}-{datetime.now().strftime('%Y-%m-%d')}"


def _privacy_consent_panel(cfg: WizardConfig) -> bool:
    """U4 — explicit dry-run consent before any imported data leaves the
    machine. Shown inline at the tail of step 10 so the user sees the
    scan numbers AND the provider + privacy level on one screen before
    agreeing.

    Returns True on consent (or when privacy mode makes consent moot).
    On False, the caller resets `import_source` to 'none' so nothing
    is ever uploaded. The wizard itself continues — the user can still
    finish config for a future manual import."""
    if cfg.privacy == "local_only":
        ui.info_line(
            "[green]Privacy=local_only → all refine stays on this machine; "
            "no consent gate required.[/]"
        )
        return True

    tag = _import_source_tag(cfg)
    tokens = cfg.import_est_tokens
    cost = cfg.import_est_normal_cost_usd
    provider = cfg.llm_provider_id
    ui.warn_box(
        "Privacy dry-run — explicit consent required",
        f"About to send ~{tokens:,} tokens (~${cost:.2f}) from your "
        f"{cfg.import_source} history to:\n"
        f"    provider : {provider}\n"
        f"    privacy  : {cfg.privacy}\n"
        f"Every imported file will carry `import_source: {tag}` in its "
        f"frontmatter so you can bulk-purge this batch later.\n"
        f"Provider's data-retention policy applies once data leaves this machine."
    )
    return ui.ask_yes_no("Proceed with import?", default=True)


def step_10_import_scan(cfg: WizardConfig) -> Optional[str]:
    """U2 — real dry-run scan. Stores counts + estimated cost on cfg
    so step 16 summary can cite them and the real import can kick off
    after the final confirm."""
    if cfg.import_source == "none":
        ui.step_header(10, TOTAL, "Import scan — SKIPPED (fresh start)")
        return "SKIPPED"
    ui.step_header(10, TOTAL, f"Import scan ({cfg.import_source})")
    ui.info_line(f"Running dry-run on {cfg.import_path}...")
    summary = _run_adapter_dry_run(cfg)
    if summary is None:
        ui.info_line("[yellow]Scan skipped — step 16 confirm will offer retry.[/]")
        cfg.import_scanned = 0
        cfg.import_emitted = 0
        cfg.import_est_tokens = 0
        cfg.import_est_normal_cost_usd = 0.0
        cfg.import_est_skim_cost_usd = 0.0
        return None
    # Save transient scan results to cfg for step 16 + logging.
    cfg.import_scanned = summary.scanned
    cfg.import_emitted = summary.emitted
    cfg.import_est_tokens = summary.total_tokens_estimate
    cfg.import_est_normal_cost_usd = summary.estimated_usd_normal()
    cfg.import_est_skim_cost_usd = summary.estimated_usd_skim()
    ui.kv_row("scanned",       str(summary.scanned))
    ui.kv_row("would emit",    str(summary.emitted))
    ui.kv_row("tokens",        f"{summary.total_tokens_estimate:,}")
    ui.kv_row("Normal cost",   f"${summary.estimated_usd_normal():.2f}")
    ui.kv_row("Skim cost",     f"${summary.estimated_usd_skim():.2f}")
    if summary.sample_paths:
        ui.info_line("sample output paths:")
        for p in summary.sample_paths[:3]:
            ui.info_line(f"  {p}")
    ui.info_line("[dim]Nothing written yet. Real import runs after step 16 confirm.[/]")
    # U4 — consent gate. If the user declines, we null the import
    # source so step 16 never triggers the real import; subsequent
    # steps proceed so the rest of the config still gets written.
    if not _privacy_consent_panel(cfg):
        ui.info_line(
            "[yellow]Import declined. Config will still save, but no "
            "conversations will be uploaded. Re-run the wizard and "
            "answer yes to import later.[/]"
        )
        cfg.import_source = "none"
        cfg.import_path = None
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


_DEFAULT_TAXONOMY_X = "AI/LLM, Tech/Network, Health/Medicine, Creative/Video, Game/Mechanics, Biz/Ops, Life/Base"
_DEFAULT_TAXONOMY_Y = "y/SOP, y/Mechanism, y/Decision, y/Architecture, y/Optimization, y/Troubleshooting, y/Reference"
_DEFAULT_TAXONOMY_Z = "z/Node, z/Boundary, z/Pipeline, z/Matrix"


def _variant_for_cfg(cfg: WizardConfig) -> str:
    """Map (mission, tier) to the refiner prompt variant filename."""
    if cfg.mission == "rag_only":
        return "rag_optimized"
    return cfg.refine_tier  # skim | normal | deep


def _preview_adapter(cfg: WizardConfig):
    if cfg.import_source == "claude":
        from .adapters import claude_export as adp
        return adp
    if cfg.import_source == "chatgpt":
        from .adapters import chatgpt_export as adp
        return adp
    if cfg.import_source == "gemini":
        from .adapters import gemini_takeout as adp
        return adp
    return None


def _format_messages_as_user_msg(messages: list[tuple[str, str]]) -> str:
    """Render (role, text) pairs as a plain-text conversation block
    the refiner can consume."""
    lines: list[str] = []
    for role, text in messages:
        lines.append(f"{role.upper()}:")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).rstrip()


def step_13_preview(cfg: WizardConfig) -> Optional[str]:
    """U17 — first-card preview gate; U23 5-dial deferred."""
    ui.step_header(13, TOTAL, "First-card preview")
    if cfg.import_source == "none" or not cfg.import_path:
        ui.info_line("No import source selected — nothing to preview. Skipped.")
        return "SKIPPED"

    from pathlib import Path as _P
    from . import llm
    from . import prompts as prompt_lib

    # 1. Pull ONE conversation from the chosen source.
    adp = _preview_adapter(cfg)
    if adp is None:
        ui.info_line("[yellow]Unknown import_source; skipping preview.[/]")
        return "SKIPPED"
    ui.info_line("Parsing one sample conversation from the export...")
    try:
        picked = adp.preview_one(_P(cfg.import_path))
    except Exception as e:
        ui.info_line(f"[red]Preview parse failed:[/] {type(e).__name__}: {e}")
        return "SKIPPED"
    if not picked:
        ui.info_line("[yellow]No renderable conversation found. Skipped.[/]")
        return "SKIPPED"
    title, messages, conv_id = picked
    ui.kv_row("sample title", title or "(untitled)")
    ui.kv_row("sample id", conv_id)
    ui.kv_row("sample turns", str(len(messages)))

    # 2. Need an API key to refine. Without one, show the raw
    #    conversation instead and note how to enable the real path.
    key = llm.get_api_key()
    if not key:
        ui.warn_box(
            "No API key",
            "Set OPENROUTER_API_KEY (or OPENAI_API_KEY) in your shell and\n"
            "re-run `python install.py --step 13` to see a live-refined card.\n"
            "For now, the wizard will show the raw conversation the daemon\n"
            "would receive.",
        )
        snippet = "\n\n".join(f"**{r}**: {t[:400]}" for r, t in messages[:6])
        ui.panel_example("Raw conversation (no refine yet)", snippet)
        return None

    # 3. Load refiner prompt for this (variant, family) and format it.
    variant = _variant_for_cfg(cfg)
    try:
        system_prompt = prompt_lib.load_prompt("refiner", variant,
                                                cfg.prompt_family)
    except FileNotFoundError as e:
        ui.info_line(f"[yellow]{e}[/]")
        ui.info_line("Falling back to 'normal' variant.")
        system_prompt = prompt_lib.load_prompt("refiner", "normal",
                                                cfg.prompt_family)
    try:
        system_prompt = system_prompt.format(
            valid_x=_DEFAULT_TAXONOMY_X,
            valid_y=_DEFAULT_TAXONOMY_Y,
            valid_z=_DEFAULT_TAXONOMY_Z,
        )
    except (KeyError, IndexError):
        pass  # prompt has format placeholders outside ours; pass through

    conv_body = _format_messages_as_user_msg(messages)
    # Cap user message to a sane size — wizard preview is a sniff test,
    # not a production refine. 4000 chars ~ 1k tokens, plenty.
    if len(conv_body) > 4000:
        conv_body = conv_body[:4000] + "\n\n[...truncated for preview...]"

    # 4. Cost preflight + LLM call. Make spending money explicit —
    # before this gate, step 13 silently called the LLM and the user
    # only noticed on their provider bill.
    ui.info_line(
        f"Preview will call [bold]{cfg.llm_provider_id}[/] once "
        f"(~$0.01, depending on slice size and provider pricing)."
    )
    if not ui.ask_yes_no("Run the preview?", default=True):
        ui.info_line(
            "Skipped preview. The daemon will still refine cards "
            "normally once it starts; this step was only a sniff test."
        )
        return None
    try:
        content = llm.call_chat(
            model_id=cfg.llm_provider_id,
            system_prompt=system_prompt,
            user_message=conv_body,
            response_format={"type": "json_object"},
        )
    except llm.LLMError as e:
        ui.info_line(f"[red]LLM call failed:[/] {e}")
        ui.info_line("Wizard continuing; real refine during daemon ingest may still work.")
        return None

    # 5. Render the card. Content is expected to be JSON; try to pretty
    #    the body_markdown if present, else show raw.
    import json as _json
    try:
        card = _json.loads(content)
        body = card.get("body_markdown") or _json.dumps(card, ensure_ascii=False,
                                                         indent=2)
    except _json.JSONDecodeError:
        body = content
    ui.panel_example("Preview card (refined)", body)
    if ui.ask_yes_no("Card shape look right?", default=True):
        return None
    # U23 — 5-dial constrained edit. Re-render preview optionally;
    # regardless, persisted to cfg so daemon refines inherit.
    _dial_panel(cfg)
    if ui.ask_yes_no("Re-render preview with these dials? "
                      "(~$0.01 another refine)", default=False):
        _rerun_preview_with_dials(cfg, system_prompt, conv_body)
    return None


# ---------- U23 · 5-dial preview-edit panel ----------

def _dial_panel(cfg: WizardConfig) -> None:
    """Ask the user 5 constrained questions and persist the answers.

    Kept separate from step_13_preview so the logic is testable via
    monkeypatched input() without needing an LLM. Each dial has a
    safe default matching the current cfg value, so the user can
    `Enter-Enter-Enter` through dials they don't care about."""
    ui.subrule("5-dial constrained edit (U23)")
    ui.intro("Five dials tune how the refiner writes. Each has a "
             "safe default — press Enter on any to keep the current "
             "setting. Choices persist to config.toml so the daemon "
             "refines inherit them.")
    cfg.dial_tone = ui.pick_option(
        "Tone",
        [
            ("formal",  "Formal — professional prose, no contractions",  ""),
            ("neutral", "Neutral — match source register (default)",     ""),
            ("casual",  "Casual — contractions OK, still no slang",      ""),
        ],
        default_key=cfg.dial_tone,
    )
    cfg.dial_length = ui.pick_option(
        "Length",
        [
            ("short",  "Short — < 500 chars; bullets over paragraphs",  ""),
            ("medium", "Medium — 500-1500 chars (default)",              ""),
            ("long",   "Long — 1500-5000 chars; expand each section",   ""),
        ],
        default_key=cfg.dial_length,
    )
    cfg.dial_register = ui.pick_option(
        "Language register",
        [
            ("technical", "Technical — assume domain knowledge (default)", ""),
            ("plain",     "Plain — avoid unexplained jargon",              ""),
            ("eli5",      "ELI5 — analogies + everyday words",             ""),
        ],
        default_key=cfg.dial_register,
    )
    cfg.dial_keep_verbatim = ui.ask_yes_no(
        "Keep-verbatim: preserve direct quotes / commands / code literally?",
        default=cfg.dial_keep_verbatim,
    )
    # Sections toggle — only enter the per-section keep/drop loop if
    # the user explicitly wants to prune. Most users keep all 6.
    from daemon.dials import ALL_SECTIONS, SECTION_LABELS
    if ui.ask_yes_no(
        "Drop any body sections? (most users keep all 6)", default=False,
    ):
        kept: list[str] = []
        for key in ALL_SECTIONS:
            if ui.ask_yes_no(
                f"  Keep section '{SECTION_LABELS[key]}'?",
                default=(key in cfg.dial_sections),
            ):
                kept.append(key)
        if kept:
            cfg.dial_sections = kept
        else:
            ui.info_line("[yellow]All sections dropped — that would break "
                         "the schema. Keeping current selection.[/]")


def _rerun_preview_with_dials(cfg: WizardConfig, system_prompt: str,
                                conv_body: str) -> None:
    """Re-call the LLM with the dial modifier appended so the user
    can see the shape shift before committing to bulk refine."""
    from . import llm
    from daemon.dials import Dials, render_dial_modifier
    dials = Dials(
        tone=cfg.dial_tone, length=cfg.dial_length,
        sections=list(cfg.dial_sections), register=cfg.dial_register,
        keep_verbatim=cfg.dial_keep_verbatim,
    )
    tail = render_dial_modifier(dials)
    if not tail:
        ui.info_line("Dials are at defaults — nothing would change. "
                     "Skipping re-render.")
        return
    prompt_with_dials = system_prompt + tail
    ui.info_line(f"Calling {cfg.llm_provider_id} with dial overrides...")
    try:
        content = llm.call_chat(
            model_id=cfg.llm_provider_id,
            system_prompt=prompt_with_dials,
            user_message=conv_body,
            response_format={"type": "json_object"},
        )
    except llm.LLMError as e:
        ui.info_line(f"[red]Re-render failed:[/] {e}")
        return
    import json as _json
    try:
        card = _json.loads(content)
        body = card.get("body_markdown") or _json.dumps(
            card, ensure_ascii=False, indent=2)
    except _json.JSONDecodeError:
        body = content
    ui.panel_example("Preview card (dial-adjusted)", body)


def step_14_taxonomy(cfg: WizardConfig) -> Optional[str]:
    """U13 + U27.1 — LLM-derived vs skeletal-then-grown vs fallback template."""
    ui.step_header(14, TOTAL, "Taxonomy")
    # Pick a sensible default by scanned import size:
    #   - cold start (none / < 100 cards)         -> minimal (grows via U27)
    #   - warm import (>= 100 cards available)    -> derive_from_imports (U13)
    #   - vault-only user                         -> derive_from_vault (U13)
    have_imports = cfg.import_source != "none" and cfg.import_emitted >= 100
    if have_imports:
        default = "derive_from_imports"
    elif cfg.import_source == "none":
        default = "minimal"
    else:
        default = "minimal"  # small import -> minimal + grow, not U13
    cfg.taxonomy_source = ui.pick_option(
        "How should throughline pick card folders?",
        [
            ("minimal",             "Minimal starter (5 broad domains, grows automatically)",
             "Ship with Tech / Creative / Health / Life / Misc. The refiner observes what you actually write about; `throughline_cli taxonomy review` surfaces growth candidates for your approval. Best for <100 cards or cold start."),
            ("derive_from_vault",   "Derive from my existing Obsidian vault",
             "U13: one-shot LLM pass over your vault dirs + sample cards. Best if you have 100+ refined cards already."),
            ("derive_from_imports", "Derive from my imported conversations",
             "U13 variant: cluster titles from imported raw MD. Needs 30+ imported conversations."),
            ("jd",                  "Fallback: Johnny Decimal template",
             "10-90 number-prefixed top-level folders (10_Tech, 20_Health, ...)."),
            ("para",                "Fallback: PARA template",
             "Projects / Areas / Resources / Archive."),
            ("zettel",              "Fallback: Zettelkasten template",
             "Flat folder, linked atomic notes; almost no taxonomy."),
        ],
        default_key=default,
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


def _run_adapter_for_real(cfg: WizardConfig) -> None:
    """Invoke the chosen adapter in real (non-dry-run) mode after the
    user confirmed at step 16. Writes raw MD to $THROUGHLINE_RAW_ROOT
    and a manifest under state/imports/<tag>.json."""
    from pathlib import Path as _P
    path = _P(cfg.import_path) if cfg.import_path else None
    if path is None:
        return
    if cfg.import_source == "claude":
        from .adapters import claude_export as adp
    elif cfg.import_source == "chatgpt":
        from .adapters import chatgpt_export as adp
    elif cfg.import_source == "gemini":
        from .adapters import gemini_takeout as adp
    else:
        return
    ui.info_line(f"Importing {cfg.import_source} export — this may take a moment...")
    try:
        summary = adp.run(path, dry_run=False, limit=_adapter_limit())
    except Exception as e:
        ui.info_line(f"[red]Import failed:[/] {type(e).__name__}: {e}")
        return
    ui.kv_row("wrote", str(summary.emitted))
    ui.kv_row("out dir", summary.out_dir)
    if summary.manifest_path:
        ui.kv_row("manifest", summary.manifest_path)


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
    if cfg.import_source != "none" and cfg.import_scanned:
        ui.kv_row("import_scanned", str(cfg.import_scanned))
        ui.kv_row("import_emit_est", str(cfg.import_emitted))
        ui.kv_row("est. cost", f"${cfg.import_est_normal_cost_usd:.2f} (Normal) "
                              f"/ ${cfg.import_est_skim_cost_usd:.2f} (Skim)")
    ui.kv_row("refine_tier", cfg.refine_tier)
    ui.kv_row("card_structure", cfg.card_structure)
    ui.kv_row("taxonomy_source", cfg.taxonomy_source)
    ui.kv_row("daily_budget_usd", f"${cfg.daily_budget_usd}")
    if not ui.ask_yes_no("Write this to ~/.throughline/config.toml"
                          + (" and run the import now" if cfg.import_source != "none" else "")
                          + "?", default=True):
        ui.info_line("[red]Aborted — no config written, no import run.[/]")
        sys.exit(0)
    # Kick off the real import immediately so the user sees the result
    # before the wizard exits. Skip for 'none' / missing path.
    if cfg.import_source in ("claude", "chatgpt", "gemini") and cfg.import_path:
        ui.print_blank()
        ui.section_title("Running import...")
        _run_adapter_for_real(cfg)
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
    if only_step is None:
        # Full run: show the banner once at the top.
        ui.banner()
    for n, fn in ALL_STEPS:
        if only_step is not None and n != only_step:
            continue
        # Progress ticker between steps (not before step 1 when doing a
        # full run; redundant with the banner).
        if only_step is None and n > 1:
            ui.progress_ticker(n - 1, TOTAL)
        result = fn(cfg)
        if result != "SKIPPED":
            if n not in cfg.completed_steps:
                cfg.completed_steps.append(n)
    if only_step is None:
        ui.progress_ticker(TOTAL, TOTAL)
    path = save(cfg)
    ui.print_blank()
    ui.info_line(f"[green]Config written:[/] {path}")
    if only_step is None:
        _print_next_steps_panel(cfg)
    return cfg


def _print_next_steps_panel(cfg: WizardConfig) -> None:
    """Final hand-off — what to do AFTER the wizard finishes.

    Without this, users who Enter-Enter through 16 steps stare at an
    empty prompt and ask "now what?". The single most common adoption
    failure mode the project has shipped with so far. Tailored per
    mission so Notes-only users don't get told to start a RAG server
    they don't need.
    """
    ui.print_blank()
    ui.section_title("✅ Wizard complete — your next 3 steps")
    ui.print_blank()

    # Step ordering varies by mission. RAG-server + daemon for Full /
    # RAG-only; daemon only for Notes-only; Filter only when chats
    # actually feed back into a vault index.
    next_n = 1

    def _step(title: str, body_lines: list[str], pick_if: str = "") -> None:
        nonlocal next_n
        ui.console.print(f"  [bold cyan]{next_n}.[/] [bold]{title}[/]")
        for line in body_lines:
            ui.console.print(f"     {line}")
        if pick_if:
            ui.console.print(f"     [dim]{pick_if}[/]")
        ui.print_blank()
        next_n += 1

    if cfg.mission != "notes_only":
        _step(
            "Start the RAG server",
            [
                "[green]python rag_server/rag_server.py[/]",
                "[dim]Serves /v1/embeddings + /v1/rerank + /v1/rag on :8000.[/]",
            ],
            pick_if="Detached: see config/launchd.plist + config/systemd.service.",
        )

    _step(
        "Start the refine daemon",
        [
            "[green]python daemon/refine_daemon.py[/]",
            "[dim]Watches your raw conversations directory and writes "
            "refined cards into your vault.[/]",
        ],
        pick_if="On first start it catches up on any raw files already on disk.",
    )

    if cfg.mission == "full":
        _step(
            "Install the OpenWebUI Filter",
            [
                "Paste [green]filter/openwebui_filter.py[/] into",
                "OpenWebUI → Admin → Functions → New Function.",
                "Set the [cyan]RAG_SERVER_URL[/] valve to "
                "[green]http://localhost:8000[/], save, and enable for "
                "the models you use.",
            ],
            pick_if="See docs/DEPLOYMENT.md §Filter for screenshots.",
        )
    elif cfg.mission == "rag_only":
        _step(
            "Point your retrieval client at the RAG server",
            [
                "POST a query to "
                "[green]http://localhost:8000/v1/rag[/] (JSON body: "
                "[cyan]{\"query\": \"...\", \"top_k\": 10}[/]).",
                "[dim]The OpenAI-shape /v1/embeddings + /v1/rerank "
                "endpoints are also live for use by other tools.[/]",
            ],
        )

    # Cross-cutting tools the user will reach for soon.
    ui.console.print("  [dim]Health-check anytime:[/] "
                       "[green]python -m throughline_cli doctor[/]")
    ui.console.print("  [dim]Re-run a single step:[/]    "
                       "[green]python install.py --step N[/]")
    if cfg.mission != "notes_only":
        ui.console.print("  [dim]Review taxonomy growth signals:[/] "
                           "[green]python -m throughline_cli taxonomy review[/]")
    ui.print_blank()
    ui.info_line(
        "[dim]Full guide: docs/DEPLOYMENT.md  ·  "
        "Bug? https://github.com/jprodcc-rodc/throughline/issues[/]"
    )


def effective_step_list(mission: str) -> list[int]:
    """Pure function used by tests: which step numbers execute per mission."""
    steps = list(range(1, 17))
    if mission == "notes_only":
        steps = [s for s in steps if s not in (3, 7, 10)]
    elif mission == "rag_only":
        steps = [s for s in steps if s not in (12,)]
    return steps


WIZARD_USAGE = """\
throughline install wizard (16 steps, mission-branched, all-Enter defaults)

Usage:
    python install.py                     Full run (all 16 steps)
    python install.py --step N            Re-run only step N
    python install.py --step=N            Same, equals form
    python install.py --help | -h         Print this help and exit

Examples:
    python install.py                     First-time setup
    python install.py --step 5            Change LLM provider only
    python install.py --step 13           Re-run first-card preview
    python install.py --step 15           Change daily budget cap

Steps (see wizard banner for the full list):
    1 Python + deps      2 Mission        3 Vector DB
    4 API key            5 LLM provider   6 Privacy
    7 Retrieval          8 Prompt family  9 Import source
   10 Import scan       11 Refine tier  12 Card structure
   13 Preview + dials   14 Taxonomy    15 Daily budget
   16 Summary

Env vars that the wizard respects:
    THROUGHLINE_CONFIG_DIR     override ~/.throughline/ location
    THROUGHLINE_IMPORT_LIMIT   cap conversations imported (quick test)
    OPENROUTER_API_KEY         LLM key the preview call reads
"""


def main(argv: Optional[list[str]] = None) -> int:
    # Windows terminals default to GBK / cp1252; reconfigure stdio to UTF-8
    # so box characters + emoji render instead of crashing. Idempotent --
    # __main__ also calls this before dispatching.
    ui.ensure_utf8_stdio()
    argv = argv if argv is not None else sys.argv[1:]
    only = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help", "help"):
            print(WIZARD_USAGE)
            return 0
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
        else:
            # Unknown arg -- don't silently swallow.
            if a.startswith("-"):
                ui.console.print(f"[red]Unknown argument:[/] {a}")
                print()
                print(WIZARD_USAGE)
                return 2
        i += 1
    run_wizard(only_step=only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
