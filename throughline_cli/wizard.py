"""v0.2.0 install wizard — 16 steps, mission-branched.

Entry point:
    python install.py          (at repo root)
    python -m throughline_cli  (once packaging lands)

Each step is a function that takes the running `WizardConfig`, prompts
the user, updates the config in place, and returns. Mission branching
in step 2 sets `cfg.mission` which subsequent steps read to decide
whether to skip (`return None`) or run.

Every step has a sensible default — pressing Enter walks the user
onto a working Full-flywheel config without any typing.
"""
from __future__ import annotations

import sys
from typing import Callable, Optional

from .config import WizardConfig, load, save


# --- tiny prompt helpers (avoid rich dep for now; easy to upgrade later) ---

def _prompt(msg: str, default: str = "") -> str:
    """Blocking prompt with default. Ctrl-C -> clean exit."""
    suffix = f" [{default}]" if default else ""
    try:
        raw = input(f"{msg}{suffix} > ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        sys.exit(130)
    return raw if raw else default


def _choice(msg: str, options: list[tuple[str, str, str]], default_key: str) -> str:
    """Prompt with numbered choices. Returns the chosen key.

    options = [(key, label, description), ...]
    """
    print(f"\n{msg}")
    default_idx = 1
    for i, (key, label, desc) in enumerate(options, 1):
        mark = "  (default)" if key == default_key else ""
        print(f"  [{i}] {label}{mark}")
        if desc:
            print(f"       {desc}")
        if key == default_key:
            default_idx = i
    raw = _prompt("Choose", str(default_idx))
    try:
        idx = int(raw)
    except ValueError:
        print(f"  ! Not a number, using default.")
        idx = default_idx
    if not 1 <= idx <= len(options):
        print(f"  ! Out of range, using default.")
        idx = default_idx
    return options[idx - 1][0]


def _yes_no(msg: str, default: bool = True) -> bool:
    default_s = "Y/n" if default else "y/N"
    raw = _prompt(msg, default_s).lower()
    if raw in ("y", "yes"):
        return True
    if raw in ("n", "no"):
        return False
    return default


# --- step functions ---
# Each step returns None (ran) or the sentinel "SKIPPED" string so the
# orchestrator can record completed_steps accurately.

def step_01_env(cfg: WizardConfig) -> Optional[str]:
    print("\n[1/16] Checking Python + dependencies...")
    print(f"  Python: {sys.version.split()[0]}")
    print("  (dependency install handled separately by pip install -e . ; "
          "this step is a placeholder until we can shell out safely.)")
    return None


def step_02_mission(cfg: WizardConfig) -> Optional[str]:
    """U24 — the single most important branch in the wizard."""
    print("\n[2/16] Mission — what is throughline for you?")
    cfg.mission = _choice(
        "Pick your mission:",
        [
            ("full",
             "Full flywheel (default, recommended)",
             "chat -> cards in Obsidian + RAG -> better chat"),
            ("rag_only",
             "RAG-only",
             "chat -> RAG retrieval only. Cards are machine food, not notes you read. Cheapest refine (~$0.001/conv)."),
            ("notes_only",
             "Notes-only",
             "chat -> refined notes in Obsidian. No RAG, no vector DB installed."),
        ],
        default_key="full",
    )
    # Mission-dependent adjustments to defaults
    if cfg.mission == "rag_only":
        cfg.card_structure = "rag_optimized"
        cfg.refine_tier = "skim"  # RAG-only inherently cheap
    elif cfg.mission == "notes_only":
        cfg.vector_db = "none"
        cfg.embedder = "none"
        cfg.reranker = "none"
    return None


def step_03_vector_db(cfg: WizardConfig) -> Optional[str]:
    """U21 — skipped for Notes-only missions."""
    if cfg.mission == "notes_only":
        print("\n[3/16] Vector DB — SKIPPED (Notes-only mission, no RAG).")
        return "SKIPPED"
    print("\n[3/16] Vector DB")
    cfg.vector_db = _choice(
        "Pick a vector DB backend:",
        [
            ("qdrant",     "Qdrant (needs Docker)",          "Production-ready. Millions of cards. Default for Full."),
            ("chroma",     "Chroma (pip install)",           "Embeddable. Lowest setup. Good to 10K cards."),
            ("lancedb",    "LanceDB (embedded Rust)",        "File-based. Fast. Good to 100K."),
            ("duckdb_vss", "DuckDB with VSS extension",      "SQL-friendly. File-based. Good to 100K."),
            ("sqlite_vec", "SQLite with sqlite-vec",         "Smallest footprint. Good to 10K."),
            ("pgvector",   "pgvector (requires Postgres)",   "If you already run Postgres."),
        ],
        default_key="qdrant" if cfg.privacy != "local_only" else "chroma",
    )
    return None


def step_04_api_key(cfg: WizardConfig) -> Optional[str]:
    print("\n[4/16] API key")
    print("  For v0.2.0-dev we do not collect the key here; set it via env var")
    print("  OPENROUTER_API_KEY (or OPENAI_API_KEY) in your shell. Re-run")
    print("  `python install.py --step 4` once you have it set.")
    return None


def step_05_llm_provider(cfg: WizardConfig) -> Optional[str]:
    """U11 — provider matrix."""
    print("\n[5/16] LLM provider for refine / slice / route")
    cfg.llm_provider_id = _choice(
        "Pick a default provider model:",
        [
            ("anthropic/claude-sonnet-4.6",  "Anthropic Sonnet 4.6",    "Default, balanced quality/cost"),
            ("anthropic/claude-haiku-4.5",   "Anthropic Haiku 4.5",     "Cheap / fast"),
            ("anthropic/claude-opus-4.7",    "Anthropic Opus 4.7",      "Expensive / best quality"),
            ("openai/gpt-5-mini",            "OpenAI GPT-5-mini",       "Alt cheap option"),
            ("google/gemini-3-flash",        "Google Gemini 3 Flash",   "Alt cheap option; judgement-friendly"),
            ("xai/grok-3",                   "xAI Grok 3",              "Timely content, coding"),
            ("deepseek/v3.2",                "DeepSeek v3.2",           "Cheapest Sonnet-class alternative"),
        ],
        default_key="anthropic/claude-sonnet-4.6",
    )
    # Auto-derive prompt family (U22)
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
    print("\n[6/16] Privacy level")
    cfg.privacy = _choice(
        "How much of the pipeline may hit the cloud?",
        [
            ("local_only", "Local-only",  "Ollama + bge-m3 only. Slowest, fully private."),
            ("hybrid",     "Hybrid",      "Refine via API, embed/rerank locally. Default."),
            ("cloud_max",  "Cloud-max",   "Everything via API. Fastest, most exposed."),
        ],
        default_key="hybrid",
    )
    return None


def step_07_retrieval(cfg: WizardConfig) -> Optional[str]:
    """U12 + U20 — embedder + reranker paired."""
    if cfg.mission == "notes_only":
        print("\n[7/16] Retrieval backend — SKIPPED (Notes-only mission).")
        return "SKIPPED"
    print("\n[7/16] Retrieval backend (embedder + reranker)")
    cfg.embedder = _choice(
        "Embedder:",
        [
            ("bge-m3",                      "BGE-M3 (local, 1024d)",                       "Default, 9/10 quality, needs ~8GB RAM"),
            ("openai-text-embedding-3-large", "OpenAI text-embedding-3-large (API, 3072d)", "No local GPU needed"),
            ("nomic-embed-text-v1.5",       "nomic-embed v1.5 (local, 768d)",              "Lighter, 8/10 quality"),
            ("all-MiniLM-L6-v2",            "all-MiniLM-L6-v2 (local, 384d)",              "CPU-only minimum viable"),
            ("voyage-3",                    "Voyage voyage-3 (API, 1024d)",                "Long-document retrieval"),
        ],
        default_key="bge-m3",
    )
    cfg.reranker = _choice(
        "Reranker:",
        [
            ("bge-reranker-v2-m3",    "BGE reranker v2-m3 (local)",    "Default, 9/10, 2.3GB model"),
            ("bge-reranker-v2-gemma", "BGE reranker v2-gemma (local)", "Newer, larger"),
            ("cohere-rerank-v3",      "Cohere rerank-v3 (API)",        "No local RAM"),
            ("voyage-rerank-2",       "Voyage rerank-2 (API)",         "Long-text friendly"),
            ("jina-rerank-v2",        "Jina reranker v2 (API)",        "Cheapest API"),
            ("skip",                  "Skip reranker (embedding-only)", "Fastest, least precise, 7/10"),
        ],
        default_key="bge-reranker-v2-m3",
    )
    return None


def step_08_prompt_family(cfg: WizardConfig) -> Optional[str]:
    """U22 — auto-derived, confirm only."""
    print("\n[8/16] Prompt family")
    print(f"  Auto-derived from provider: {cfg.prompt_family}")
    print("  (Claude -> XML tags / GPT -> Markdown+JSON / Gemini -> structured / else generic)")
    if not _yes_no("Accept?", default=True):
        cfg.prompt_family = _choice(
            "Override prompt family:",
            [
                ("claude",  "claude (XML tags)", ""),
                ("gpt",     "gpt (Markdown+JSON)", ""),
                ("gemini",  "gemini (structured)", ""),
                ("generic", "generic (plain Markdown)", ""),
            ],
            default_key="generic",
        )
    return None


def step_09_import_source(cfg: WizardConfig) -> Optional[str]:
    """U2 — import adapters; with cold-start warning if fresh."""
    print("\n[9/16] Import source")
    cfg.import_source = _choice(
        "Do you have existing LLM chat history to import?",
        [
            ("chatgpt",  "ChatGPT export (ZIP)",           ""),
            ("claude",   "Claude export (ZIP)",            ""),
            ("gemini",   "Gemini Google Takeout (ZIP)",    ""),
            ("multiple", "Multiple sources",               "Run the wizard again per source later"),
            ("none",     "No, start fresh",                "Cold start: RAG silent for ~50 conversations"),
        ],
        default_key="none",
    )
    if cfg.import_source == "none" and cfg.mission != "notes_only":
        print("\n  ⚠  Cold-start warning")
        print("     Starting with an empty knowledge base means:")
        print("     - RAG will not fire for ~50 conversations (~2 weeks of typical use)")
        print("     - Initial replies feel like plain ChatGPT (no enrichment)")
        print("     - Cards accumulate organically as you chat.")
        if not _yes_no("Still proceed with a fresh start?", default=True):
            print("  -> Re-pick import source:")
            return step_09_import_source(cfg)
    if cfg.import_source != "none":
        cfg.import_path = _prompt("Path to the export file", "~/Downloads/export.zip")
    return None


def step_10_import_scan(cfg: WizardConfig) -> Optional[str]:
    if cfg.import_source == "none":
        print("\n[10/16] Import scan — SKIPPED (fresh start).")
        return "SKIPPED"
    print(f"\n[10/16] Import scan ({cfg.import_source})")
    print("  (U2 adapter not yet implemented — stub prints intended action only.)")
    print(f"  Would scan: {cfg.import_path}")
    return None


def step_11_refine_tier(cfg: WizardConfig) -> Optional[str]:
    """U15 — three tiers, 40x cost spread."""
    if cfg.mission == "rag_only":
        print("\n[11/16] Refine tier — FIXED to 'skim' (RAG-only mission).")
        return "SKIPPED"
    print("\n[11/16] Refine tier")
    cfg.refine_tier = _choice(
        "How deep should the refiner think on each conversation?",
        [
            ("skim",   "Skim   (~$0.005/conv, one Haiku call)",        "Index old chat history, quick searchability"),
            ("normal", "Normal (~$0.04/conv, Sonnet 6-section)",       "Daily use, balanced. Default."),
            ("deep",   "Deep   (~$0.20/conv, Opus multi-pass + critique)", "Research-grade, decisions, long-term memory"),
        ],
        default_key="normal",
    )
    return None


def step_12_card_structure(cfg: WizardConfig) -> Optional[str]:
    """U16 — card structure; fixed for RAG-only missions (U25)."""
    if cfg.mission == "rag_only":
        print("\n[12/16] Card structure — FIXED to 'rag_optimized' (U25 format).")
        return "SKIPPED"
    print("\n[12/16] Card structure")
    cfg.card_structure = _choice(
        "Pick a card shape:",
        [
            ("compact",  "Compact (title + 1 paragraph + tags)",           "Zettelkasten-style, single-claim cards"),
            ("standard", "Standard (6-section skeleton)",                  "Balanced. Default."),
            ("detailed", "Detailed (6 sections + sidebar)",                "Research-grade, power users"),
        ],
        default_key="standard",
    )
    return None


def step_13_preview(cfg: WizardConfig) -> Optional[str]:
    """U17 + U23 — preview + 5-dial constrained edit."""
    print("\n[13/16] First-card preview + 5-dial edit")
    print("  (Preview runs a real refine on ONE conversation at the chosen tier.")
    print("   Not yet implemented in skeleton — stub accepts defaults for the 5 dials.)")
    # Accept defaults for now; future code will show a rendered card here.
    return None


def step_14_taxonomy(cfg: WizardConfig) -> Optional[str]:
    """U13 — LLM-derived from user's content, with template fallback."""
    print("\n[14/16] Taxonomy")
    cfg.taxonomy_source = _choice(
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
    print("\n[15/16] Daily USD budget cap")
    print("  Daemon pauses its refine queue once daily spend hits this cap.")
    raw = _prompt("Daily budget (USD)", str(cfg.daily_budget_usd))
    try:
        cfg.daily_budget_usd = float(raw)
    except ValueError:
        print(f"  ! Not a number, keeping ${cfg.daily_budget_usd}")
    return None


def step_16_summary(cfg: WizardConfig) -> Optional[str]:
    """Final confirm + write."""
    print("\n[16/16] Summary")
    print("  mission           :", cfg.mission)
    if cfg.mission != "notes_only":
        print("  vector_db         :", cfg.vector_db)
    print("  llm_provider      :", cfg.llm_provider_id)
    print("  privacy           :", cfg.privacy)
    if cfg.mission != "notes_only":
        print("  embedder          :", cfg.embedder)
        print("  reranker          :", cfg.reranker)
    print("  prompt_family     :", cfg.prompt_family)
    print("  import_source     :", cfg.import_source,
          f"({cfg.import_path})" if cfg.import_path else "")
    print("  refine_tier       :", cfg.refine_tier)
    print("  card_structure    :", cfg.card_structure)
    print("  taxonomy_source   :", cfg.taxonomy_source)
    print("  daily_budget_usd  : $", cfg.daily_budget_usd)
    if not _yes_no("Write this to ~/.throughline/config.toml?", default=True):
        print("Aborted — no config written.")
        sys.exit(0)
    return None


# --- orchestrator ---

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
    """Run the wizard. If `only_step` is set, jump to that single step."""
    cfg = cfg or load()
    for n, fn in ALL_STEPS:
        if only_step is not None and n != only_step:
            continue
        result = fn(cfg)
        if result != "SKIPPED":
            if n not in cfg.completed_steps:
                cfg.completed_steps.append(n)
    path = save(cfg)
    print(f"\nConfig written: {path}")
    return cfg


def effective_step_list(mission: str) -> list[int]:
    """Return the step numbers that actually execute for a given mission.

    Pure function, used by tests to verify branching without touching I/O.
    """
    steps = list(range(1, 17))
    if mission == "notes_only":
        steps = [s for s in steps if s not in (3, 7, 10)]  # 10 skipped if no import
    elif mission == "rag_only":
        steps = [s for s in steps if s not in (12,)]  # card structure fixed
    return steps


def main(argv: Optional[list[str]] = None) -> int:
    # Windows terminals default to GBK / cp1252; reconfigure stdio to UTF-8
    # so the wizard's box-drawing + warnings render instead of crashing.
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if callable(reconf):
            try:
                reconf(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
    argv = argv if argv is not None else sys.argv[1:]
    only = None
    for a in argv:
        if a.startswith("--step"):
            # allow --step=3 or --step 3
            tail = a.split("=", 1)[1] if "=" in a else None
            if tail is None and len(argv) > argv.index(a) + 1:
                tail = argv[argv.index(a) + 1]
            if tail:
                try:
                    only = int(tail)
                except ValueError:
                    print(f"Bad --step value: {tail}", file=sys.stderr)
                    return 2
    run_wizard(only_step=only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
