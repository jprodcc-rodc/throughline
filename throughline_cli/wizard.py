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


_VECTOR_DB_DEP_HINT: dict[str, tuple[tuple[str, ...], str]] = {
    # vector_db key -> (importable module names, install hint)
    "chroma":     (("chromadb",),                  "pip install chromadb"),
    "lancedb":    (("lancedb", "pyarrow"),         "pip install lancedb pyarrow  (or `pip install throughline[lancedb]`)"),
    "duckdb_vss": (("duckdb",),                    "pip install duckdb           (or `pip install throughline[duckdb-vss]`)"),
    "sqlite_vec": (("sqlite_vec",),                "pip install sqlite-vec       (or `pip install throughline[sqlite-vec]`)"),
    "pgvector":   (("psycopg",),                   "pip install 'psycopg[binary]' (or `pip install throughline[pgvector]`)"),
}


def _check_vector_db_available(vector_db: str) -> tuple[bool, str]:
    """Return (available, hint). Available=False when an optional dep
    is missing; hint is the user-facing install command."""
    deps_hint = _VECTOR_DB_DEP_HINT.get(vector_db)
    if not deps_hint:
        return True, ""  # qdrant uses stdlib urllib; nothing to check.
    deps, hint = deps_hint
    for d in deps:
        try:
            __import__(d)
        except ImportError:
            return False, hint
    return True, ""


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
    # --- proactive optional-dep check (catches the silent-stub trap)
    available, hint = _check_vector_db_available(cfg.vector_db)
    if not available:
        ui.info_line(
            f"[yellow]Heads-up:[/] {cfg.vector_db!r} is selected but its "
            f"Python dep is not installed. Without it, the daemon's first "
            f"refine will raise RuntimeError. Run:\n  {hint}"
        )
    # --- pgvector-specific: needs a DSN to a running Postgres
    if cfg.vector_db == "pgvector":
        import os as _os
        if not (_os.environ.get("PGVECTOR_DSN")
                or _os.environ.get("DATABASE_URL")):
            ui.info_line(
                "[yellow]Heads-up:[/] PGVECTOR_DSN and DATABASE_URL are "
                "both unset. The daemon will try "
                "`postgresql://localhost/throughline` by default. Set "
                "PGVECTOR_DSN to your real DB before starting the daemon."
            )
    return None


def step_04_api_key(cfg: WizardConfig) -> Optional[str]:
    """U28 — pick the provider BACKEND first so step 5 can scope
    model IDs to that provider. Backward-compat default: openrouter."""
    from . import providers as _providers
    ui.step_header(4, TOTAL, "LLM provider backend")
    ui.intro("Which HTTP endpoint handles your LLM calls. Same key "
             "variable per provider; model IDs in the next step are "
             "scoped to whatever you pick here. Default is OpenRouter, "
             "which routes to most models through a single key.")

    presets = _providers.list_presets()

    # Group by region for cleaner display: global / cn / local / custom.
    def _group_label(region: str) -> str:
        return {
            "global": "— Global",
            "cn":     "— China (大陆 access)",
            "local":  "— Local (self-hosted)",
            "custom": "— Custom",
        }.get(region, "")

    options: list[tuple[str, str, str]] = []
    current_region: Optional[str] = None
    for p in presets:
        if p.region != current_region:
            # Not an option — pick_option doesn't support section headers,
            # so we embed the region hint in the description of the next
            # provider instead.
            current_region = p.region
        region_tag = f"[{p.region}] "
        # Auto-detect: if the user already has the env var set, prefix
        # the display name with a small indicator.
        key_set = bool(__import__("os").environ.get(p.env_var, "").strip())
        marker = "● " if key_set else ""
        options.append((
            p.id,
            f"{marker}{region_tag}{p.name}",
            f"{p.notes}  (env: {p.env_var})",
        ))

    # Smart default: if a key is already set for some provider, default
    # to that; else OpenRouter.
    autodetected = _providers.detect_configured_provider()
    default_key = autodetected or "openrouter"

    cfg.llm_provider = ui.pick_option(
        "Pick an LLM provider:",
        options,
        default_key=default_key,
    )

    preset = _providers.get_preset(cfg.llm_provider)
    key_set = bool(__import__("os").environ.get(preset.env_var, "").strip())
    if key_set:
        ui.info_line(f"[green]{preset.env_var} is set.[/] "
                      f"The preview (step 13) will call {preset.name}.")
    else:
        if preset.signup_url:
            ui.info_line(
                f"[yellow]{preset.env_var} is NOT set.[/] Get a key at "
                f"{preset.signup_url}, then export it in your shell "
                f"(e.g. `export {preset.env_var}=sk-...`) and re-run "
                f"`python install.py --step 4` to verify."
            )
        else:
            ui.info_line(
                f"[yellow]{preset.env_var} is NOT set.[/] Also set "
                f"THROUGHLINE_LLM_URL to your custom endpoint, then "
                f"re-run `python install.py --step 4`."
            )
    return None


def step_05_llm_provider(cfg: WizardConfig) -> Optional[str]:
    """U11 + U28 — model picker SCOPED to whatever provider step 4
    chose. Model IDs differ per provider; the registry knows them."""
    from . import providers as _providers
    ui.step_header(5, TOTAL, "LLM model")

    preset = _providers.get_preset(cfg.llm_provider)
    if not preset.models:
        # Generic / custom provider: user has to supply the model ID.
        ui.info_line(
            f"[yellow]{preset.name} is a generic endpoint — no preset "
            f"model list.[/] Enter the model ID your endpoint expects."
        )
        cfg.llm_provider_id = ui.ask_text(
            "Model ID", default=cfg.llm_provider_id or "").strip()
    else:
        ui.intro(f"Models offered by {preset.name}. Defaults are "
                  f"the provider's most-used one; press Enter for the "
                  f"first entry, pick another, or choose 'Other' to "
                  f"paste a model ID directly from the provider's "
                  f"docs (in case our list is stale).")
        options = [(mid, label, "") for mid, label in preset.models]
        # Append the universal escape hatch — if our verified list
        # doesn't include the model the user wants (or our list has
        # drifted), they can paste any ID directly.
        options.append(
            ("__OTHER__",
             f"Other — type your own {preset.name} model ID",
             "Use this if our list is missing what you want or a "
             "model 404'd at preview. Paste from the provider's docs."),
        )
        chosen = ui.pick_option(
            f"Pick a model from {preset.name}:",
            options,
            default_key=preset.models[0][0],
        )
        if chosen == "__OTHER__":
            # Fall-through: same UX as a generic-provider model entry.
            cfg.llm_provider_id = ui.ask_text(
                f"Model ID for {preset.name}",
                default=cfg.llm_provider_id or "",
            ).strip()
        else:
            cfg.llm_provider_id = chosen

    # Auto-derive prompt family (U22) from the model ID.
    mid = cfg.llm_provider_id.lower()
    if "claude" in mid or cfg.llm_provider == "anthropic":
        cfg.prompt_family = "claude"
    elif ("gpt" in mid
            or cfg.llm_provider == "openai"
            # OpenAI's reasoning models use "o4-mini" / "o3-pro"
            # naming, no "gpt" substring. Catch them so step 8's
            # auto-derive doesn't fall through to "generic" for an
            # obvious OpenAI model.
            or mid.startswith("o4-") or mid.startswith("o3-")
            or mid.startswith("openai/o4-") or mid.startswith("openai/o3-")):
        cfg.prompt_family = "gpt"
    elif "gemini" in mid:
        cfg.prompt_family = "gemini"
    else:
        cfg.prompt_family = "generic"
    return None


_LOCAL_PROVIDERS = frozenset({"ollama", "lm_studio", "generic"})


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
    # --- cross-step validation: local_only + cloud LLM provider is a
    # contradiction the user almost certainly didn't intend.
    if (cfg.privacy == "local_only"
            and cfg.llm_provider not in _LOCAL_PROVIDERS):
        ui.info_line(
            f"[yellow]Conflict warning:[/] privacy=local_only but "
            f"llm_provider={cfg.llm_provider!r} sends every refine call "
            f"to a cloud endpoint. To honour local-only, re-run "
            f"`python install.py --step 4` and pick `ollama` or `lm_studio` "
            f"(or set up a generic localhost endpoint)."
        )
    # --- inverse: local LLM + cloud_max is harmless but probably an
    # accident worth flagging once.
    if (cfg.privacy == "cloud_max"
            and cfg.llm_provider in _LOCAL_PROVIDERS):
        ui.info_line(
            f"[yellow]Heads-up:[/] privacy=cloud_max but "
            f"llm_provider={cfg.llm_provider!r} is a local endpoint, so "
            f"refine calls stay on this machine regardless. The "
            f"cloud_max label only matters for embed/rerank."
        )
    return None


def step_07_retrieval(cfg: WizardConfig) -> Optional[str]:
    """U12 + U20 — embedder + reranker paired.

    The KEYS below MUST match either rag_server.embedders._REGISTRY /
    _ALIASES (embedder) or rag_server.rerankers._REGISTRY / _ALIASES
    (reranker). The pick keys land in config.toml verbatim; the
    daemon + rag_server look them up via create_embedder / create_reranker.
    Picking a key that's not in the registry would fail at runtime
    with a ValueError — see fixtures/v0_2_0/test_wizard_step7_keys.py
    for the regression guard.
    """
    if cfg.mission == "notes_only":
        ui.step_header(7, TOTAL, "Retrieval backend — SKIPPED (Notes-only)")
        return "SKIPPED"
    ui.step_header(7, TOTAL, "Retrieval backend (embedder + reranker)")
    cfg.embedder = ui.pick_option(
        "Embedder:",
        [
            ("bge-m3", "BGE-M3 (local, 1024d)",
             "Default. 9/10 quality. ~8GB RAM."),
            ("openai", "OpenAI text-embedding-3-large (API, 3072d)",
             "No local GPU. Set EMBEDDER_MODEL to pick a specific OpenAI model."),
            ("nomic",  "nomic-embed v1.5 (local, 768d)",
             "Lighter, 8/10 quality. v0.2.x routes via bge-m3."),
            ("minilm", "all-MiniLM-L6-v2 (local, 384d)",
             "CPU-only minimum viable. v0.2.x routes via bge-m3."),
            ("voyage", "Voyage voyage-3 (API, 1024d)",
             "Long-document retrieval. v0.2.x uses OpenAI-compat shape."),
        ],
        default_key="bge-m3",
    )
    cfg.reranker = ui.pick_option(
        "Reranker:",
        [
            ("bge-reranker-v2-m3",    "BGE reranker v2-m3 (local)",
             "Default. 9/10. 2.3GB model."),
            ("bge-reranker-v2-gemma", "BGE reranker v2-gemma (local)",
             "v0.2.x routes via bge-m3."),
            ("cohere", "Cohere rerank-v3.5 (API)",
             "No local RAM. Set COHERE_RERANK_MODEL to switch model."),
            ("voyage", "Voyage rerank-2 (API)",
             "Long-text friendly. Set VOYAGE_RERANK_MODEL to switch."),
            ("jina",   "Jina reranker v2 (API, multilingual)",
             "Multilingual default. Set JINA_RERANK_MODEL to switch."),
            ("skip",   "Skip reranker (embedding-only)",
             "Fastest, least precise. 7/10."),
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


def _run_adapter_with_progress(adp, path, *, dry_run: bool):
    """Run the import adapter wrapped in a rich.Progress UI.

    Adapters that accept a `progress_cb` kwarg get a real progress
    bar with bar + percent + ETA. Adapters that don't (older
    signatures or future ones we haven't instrumented yet) fall back
    to the simple spinner via `ui.status` — same code path the
    wizard had before progress bars existed.

    Why detect the kwarg instead of just calling: keeps the per-
    adapter instrumentation incremental. Right now only
    gemini_takeout.run() takes progress_cb; claude_export and
    chatgpt_export will be added as users hit them.
    """
    import inspect as _inspect
    try:
        sig = _inspect.signature(adp.run)
        supports_progress = "progress_cb" in sig.parameters
    except (TypeError, ValueError):
        supports_progress = False

    if not supports_progress or not ui._is_real_tty():
        # Fallback: legacy spinner. Also kicks in for non-TTY (CI /
        # pytest / piped) so test captures stay clean.
        with ui.status(f"Scanning export at {path}..."):
            return adp.run(path, dry_run=dry_run, limit=_adapter_limit())

    from rich.progress import (
        Progress, SpinnerColumn, BarColumn,
        TaskProgressColumn, TextColumn, TimeElapsedColumn,
    )

    # Human-readable label per phase key (adapters speak these). New
    # phases auto-fall-back to a Title-cased version of the key.
    _PHASE_LABELS = {
        "scanning_events": "Scanning events",
        "processing_days": "Processing days",
        "processing":      "Processing conversations",
    }

    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=ui.console,
        transient=False,
    ) as progress:
        # Tasks lazy-created on first emit per phase. Generic across
        # claude / chatgpt (single phase) and gemini (two phases) —
        # the wizard doesn't need to know what the adapter decides
        # to emit, only how to render whatever phases show up.
        tasks: dict = {}

        def cb(phase: str, current: int, total: int) -> None:
            label = _PHASE_LABELS.get(phase, phase.replace("_", " ").title())
            if phase not in tasks:
                # Lazy-create on first sighting. total=None marks
                # indeterminate while we wait for a determinate tick.
                tasks[phase] = progress.add_task(
                    f"{label}...",
                    total=total if total > 0 else None,
                    start=True,
                )
                if total <= 0:
                    return
            tid = tasks[phase]
            if total > 0:
                # Determinate update: covers both progress mid-flight
                # and the final tick (current==total fills the bar).
                progress.update(tid, total=total, completed=current)
            else:
                progress.update(tid, completed=current)

        return adp.run(path, dry_run=dry_run, limit=_adapter_limit(),
                       progress_cb=cb)


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
        summary = _run_adapter_with_progress(adp, path, dry_run=True)
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

    # Note: examples are device/OS-neutral by design. Don't swap to
    # platform-specific topics (M2 Mac, Windows registry, etc.) —
    # users misread those as "the wizard detected my hardware".
    ui.subrule("[1] Skim — ~$0.005/conv (one Haiku call)")
    ui.panel_example(
        "Skim output (example — same for every user, not auto-detected)",
        "# FastAPI dev server with hot-reload\n\n"
        "Use `uvicorn main:app --reload`. The `--reload` flag watches "
        "all Python files in the working directory. Drop it for "
        "production and add `--workers 4` behind nginx instead.\n\n"
        "`#fastapi` `#python`\n",
        pick_if="you want a searchable index of old chat history. Card "
                "is a flashcard, not a knowledge note. Cost for 1,247 "
                "imported conversations: ~$6.",
    )

    ui.subrule("[2] Normal — ~$0.04/conv (Sonnet slice + refine + route · default)")
    ui.panel_example(
        "Normal output — the full 6-section skeleton",
        "# FastAPI dev server with hot-reload\n\n"
        "## Scenario & pain point\n"
        "You're iterating on routes; restarting the server after every "
        "edit kills flow. Need autoreload that's also production-safe.\n\n"
        "## Core knowledge & first principles\n"
        "uvicorn is an ASGI server. `--reload` runs a watchdog that "
        "kills + respawns workers on file change. Production uses "
        "multiple workers behind a reverse proxy.\n\n"
        "## Execution — step-by-step\n"
        "1. Dev: `uvicorn main:app --reload`.\n"
        "2. Production: `uvicorn main:app --host 0.0.0.0 --port 8000 "
        "--workers 4` behind nginx.\n"
        "3. Lock the bind addr in `--host` only when nginx is in front.\n\n"
        "## Avoid — pitfalls and edges\n"
        "Don't use `--reload` in production (single worker, no signal "
        "handling). Don't expose `0.0.0.0` directly to the internet.\n\n"
        "## Insight & mental model\n"
        "uvicorn = the ASGI process. nginx = the public face. They have "
        "different jobs; conflate them and you'll end up with a "
        "dev-server in production.\n\n"
        "## Summary\n"
        "Dev: `uvicorn ... --reload`. Prod: `--workers 4` behind nginx. "
        "Never the same flags.\n",
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
        with ui.status(f"Calling {cfg.llm_provider_id} (one refine pass)..."):
            content = llm.call_chat(
                model_id=cfg.llm_provider_id,
                system_prompt=system_prompt,
                user_message=conv_body,
                response_format={"type": "json_object"},
                provider_id=cfg.llm_provider,
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
            provider_id=cfg.llm_provider,
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
    ui.intro(
        "Taxonomy = which folders / domain tags exist for the refiner "
        "to drop cards into. WHATEVER you pick here, the U27 self-"
        "growing loop is always on: every refine logs a "
        "(primary_x, proposed_x_ideal) observation, and "
        "`throughline_cli taxonomy review` surfaces growth candidates "
        "once 5+ cards over 3+ days drift toward a tag you don't yet "
        "have. So this step picks the SEED — the system grows from "
        "there forever."
    )
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
            ("derive_from_vault",   "Derive from my existing Obsidian vault (manual, post-wizard)",
             "U13: one-shot LLM pass over your vault dirs + sample cards. Best if you have 100+ refined cards already. Run `python scripts/derive_taxonomy.py --from-vault <path>` AFTER the wizard."),
            ("derive_from_imports", "Derive from my imported conversations (runs NOW, ~$0.05)",
             "U13 variant: at the end of step 16, the wizard samples 30 titles from your imports and asks the LLM to cluster them into a taxonomy. Writes config/taxonomy.py automatically. Needs >=30 imported conversations + import_source != 'none'."),
            ("jd",                  "Fallback: Johnny Decimal template (static, no LLM)",
             "10-90 number-prefixed top-level folders (10_Tech, 20_Health, ...). Does NOT look at your data."),
            ("para",                "Fallback: PARA template (static, no LLM)",
             "Projects / Areas / Resources / Archive. Does NOT look at your data."),
            ("zettel",              "Fallback: Zettelkasten template (static, no LLM)",
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
    try:
        summary = _run_adapter_with_progress(adp, path, dry_run=False)
    except Exception as e:
        ui.info_line(f"[red]Import failed:[/] {type(e).__name__}: {e}")
        return
    ui.kv_row("wrote", str(summary.emitted))
    ui.kv_row("out dir", summary.out_dir)
    if summary.manifest_path:
        ui.kv_row("manifest", summary.manifest_path)


# Per-tier per-conversation cost estimates (USD). Sources: wizard
# step 11 prose + the daemon's MODEL_PRICING table + observed typical
# conversation lengths (~3K input tokens, ~2K output tokens per
# refine call, midpoint of the cost-spread examples).
#
# We deliberately do NOT extrapolate to a monthly figure. Real usage
# is bursty and project-driven (10 hours one day, 20 idle days).
# Multiplying per-conv cost by an assumed daily rate misrepresents
# this for most users. Better to surface only what the user can
# directly reason about: the unit cost they pay per refine + the
# daily cap they configured.
_TIER_COST_PER_CONV: dict[str, float] = {
    "skim":   0.005,   # one Haiku call
    "normal": 0.040,   # Sonnet 6-section
    "deep":   0.200,   # Opus multi-pass + critique
}


def _per_conv_cost(refine_tier: str) -> float:
    """Estimated USD cost per refined conversation at the given tier."""
    return _TIER_COST_PER_CONV.get(refine_tier, 0.04)


def _format_cost_line(refine_tier: str, daily_cap_usd: float) -> str:
    """Build the single-line cost summary. Only mentions per-
    conversation cost + the daily cap — no monthly extrapolation,
    because real usage is bursty and any "X/month" figure would
    misrepresent it for most users."""
    per_conv = _per_conv_cost(refine_tier)
    if per_conv <= 0:
        return ""
    max_per_day = int(daily_cap_usd / per_conv) if per_conv else 0
    return (f"~${per_conv:.3f} per conversation on the {refine_tier} "
            f"tier. Daily cap: ${daily_cap_usd:g} (≈ {max_per_day:,} "
            f"refines max/day; daemon pauses + resets at midnight).")


def _build_summary_groups(cfg: WizardConfig) -> list[tuple[str, list[tuple[str, str]]]]:
    """Group cfg fields semantically for the summary tree (Tier-3 UX).
    Pure function — exposed for tests."""
    groups: list[tuple[str, list[tuple[str, str]]]] = []

    # 1. Mission + storage — "what's it for, where does it live"
    storage_items: list[tuple[str, str]] = [("mission", cfg.mission)]
    if cfg.mission != "notes_only":
        storage_items.append(("vector_db", cfg.vector_db))
    groups.append(("Mission & Storage", storage_items))

    # 2. LLM — provider, model, prompt family, privacy posture
    llm_items: list[tuple[str, str]] = [
        ("provider",      cfg.llm_provider),
        ("model",         cfg.llm_provider_id),
        ("prompt_family", cfg.prompt_family),
        ("privacy",       cfg.privacy),
    ]
    groups.append(("LLM", llm_items))

    # 3. Retrieval — embedder + reranker (skipped for notes_only)
    if cfg.mission != "notes_only":
        groups.append(("Retrieval", [
            ("embedder", cfg.embedder),
            ("reranker", cfg.reranker),
        ]))

    # 4. Refine pipeline — tier, card shape, taxonomy seed
    groups.append(("Refine pipeline", [
        ("tier",           cfg.refine_tier),
        ("card_structure", cfg.card_structure),
        ("taxonomy",       cfg.taxonomy_source),
    ]))

    # 5. Import — only when there's something to import
    src = cfg.import_source + (f" ({cfg.import_path})" if cfg.import_path else "")
    import_items: list[tuple[str, str]] = [("source", src)]
    if cfg.import_source != "none" and cfg.import_scanned:
        import_items.append(("scanned", str(cfg.import_scanned)))
        import_items.append(("emit_est", str(cfg.import_emitted)))
        import_items.append((
            "est_cost",
            f"${cfg.import_est_normal_cost_usd:.2f} (Normal) "
            f"/ ${cfg.import_est_skim_cost_usd:.2f} (Skim)",
        ))
    groups.append(("Import", import_items))

    # 6. Cost guardrails — daily cap (the cost LINE prints separately
    # below the tree, since it's a sentence not a leaf).
    groups.append(("Cost guardrails", [
        ("daily_budget", f"${cfg.daily_budget_usd}"),
    ]))

    return groups


def step_16_summary(cfg: WizardConfig) -> Optional[str]:
    ui.step_header(16, TOTAL, "Summary")
    ui.summary_tree(_build_summary_groups(cfg))

    # --- Cost line: per-conversation unit cost + daily cap ---------
    # No monthly extrapolation: real usage is bursty (heavy week +
    # idle weeks), so any "$N/month" figure would misrepresent it for
    # most users. Surface what the user controls: cost per refine and
    # the daily cap (which IS the worst-case spend per day).
    ui.print_blank()
    ui.info_line(
        f"[dim]Cost: {_format_cost_line(cfg.refine_tier, cfg.daily_budget_usd)}[/]"
    )

    # Skip the confirm prompt + import in dry-run mode — run_wizard()
    # is responsible for the "DRY RUN" footer and for not writing
    # config.toml. The import adapter writes raw MD files (separate
    # from config.toml), so it must also be guarded by the same flag.
    if _DRY_RUN_ACTIVE:
        ui.info_line(
            "[dim](dry run — confirm prompt skipped; import not run)[/]"
        )
        return None

    will_derive_taxonomy = (
        cfg.taxonomy_source == "derive_from_imports"
        and cfg.import_source in ("claude", "chatgpt", "gemini")
        and cfg.import_path
    )

    confirm_q = "Write this to ~/.throughline/config.toml"
    if cfg.import_source != "none":
        confirm_q += " and run the import now"
    if will_derive_taxonomy:
        confirm_q += (" and derive taxonomy from your imports "
                      "(~$0.05, one LLM call)")
    confirm_q += "?"
    if not ui.ask_yes_no(confirm_q, default=True):
        ui.info_line("[red]Aborted — no config written, no import run.[/]")
        sys.exit(0)

    # Kick off the real import immediately so the user sees the result
    # before the wizard exits. Skip for 'none' / missing path.
    if cfg.import_source in ("claude", "chatgpt", "gemini") and cfg.import_path:
        ui.print_blank()
        ui.section_title("Running import...")
        _run_adapter_for_real(cfg)

    # Now that raw MD is on disk, run U13 taxonomy derivation if the
    # user picked derive_from_imports at step 14. Without this hook
    # the wizard wrote `taxonomy_source = "derive_from_imports"` to
    # config.toml but did nothing — the user had to remember to run
    # `python scripts/derive_taxonomy.py --from-imports ...` later.
    if will_derive_taxonomy:
        ui.print_blank()
        ui.section_title("Deriving taxonomy from your imports...")
        _run_taxonomy_derivation_from_imports(cfg)
    return None


def _run_taxonomy_derivation_from_imports(cfg: WizardConfig) -> None:
    """Sample 30 titles from the just-imported raw MD, send to the
    LLM via the taxonomy_deriver prompt, render config/taxonomy.py.

    Costs ~$0.01-0.05 per run (30 titles is a small payload). All
    failures are non-fatal — wizard continues, user can re-run via
    `python scripts/derive_taxonomy.py --from-imports <raw_root>`.
    """
    import os as _os
    import sys as _sys
    from pathlib import Path as _P

    # Resolve raw root: same precedence as the daemon.
    raw_root_env = _os.environ.get("THROUGHLINE_RAW_ROOT", "").strip()
    if raw_root_env:
        raw_root = _P(raw_root_env).expanduser()
    else:
        raw_root = _P.home() / "throughline_runtime" / "sources" / "openwebui_raw"

    if not raw_root.exists():
        ui.info_line(
            f"[yellow]Skipping taxonomy derivation:[/] raw root "
            f"{raw_root} does not exist. Run "
            f"[green]python scripts/derive_taxonomy.py --from-imports "
            f"<your-raw-root>[/] manually after the daemon writes "
            f"some cards."
        )
        return

    # Lazy-import the script's helpers so the wizard module doesn't
    # pull derive_taxonomy at import time (the script imports llm
    # which expects an env var).
    _sys.path.insert(0, str(_P(__file__).resolve().parents[1] / "scripts"))
    try:
        import derive_taxonomy as _td
    except ImportError as e:
        ui.info_line(f"[yellow]Could not import derive_taxonomy: {e}[/]")
        return

    titles = _td.sample_imports(raw_root, cap=30)
    if not titles:
        ui.info_line(
            f"[yellow]No imported MD files found under {raw_root}. "
            f"Skipping derivation; re-run via the script later if "
            f"the import wrote files to a different location.[/]"
        )
        return

    ui.kv_row("sampled titles", str(len(titles)))
    ui.kv_row("provider", cfg.llm_provider_id)

    user_msg = _td.format_imports_input(titles)
    try:
        with ui.status(
            f"Calling {cfg.llm_provider_id} for taxonomy derivation..."
        ):
            proposal = _td.call_deriver(
                user_msg,
                provider_id=cfg.llm_provider_id,
                family=cfg.prompt_family,
            )
    except Exception as e:
        ui.info_line(f"[red]Derivation failed:[/] {type(e).__name__}: {e}")
        ui.info_line(
            "[dim]Wizard continues. Re-run later: "
            f"python scripts/derive_taxonomy.py --from-imports {raw_root}[/]"
        )
        return

    # Render + write taxonomy.py.
    rendered = _td.render_taxonomy_module(proposal)
    out_path = _P(__file__).resolve().parents[1] / "config" / "taxonomy.py"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
    except OSError as e:
        ui.info_line(f"[red]Could not write {out_path}: {e}[/]")
        return

    ui.info_line(f"[green]✓ Wrote derived taxonomy:[/] {out_path}")
    n_x = len(proposal.get("x_domains") or [])
    n_y = len(proposal.get("y_forms") or [])
    n_z = len(proposal.get("z_axes") or [])
    ui.info_line(
        f"  x_domains={n_x} · y_forms={n_y} · z_axes={n_z}"
    )


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


# Module-level flag toggled by run_wizard(dry_run=True). Read by
# step_16_summary so the import-adapter call (which writes raw MD
# files to disk) gets skipped in dry-run mode. Module-level instead
# of a cfg field because dry_run is a transient run-time choice,
# not config the wizard should persist.
_DRY_RUN_ACTIVE = False


def run_wizard(cfg: Optional[WizardConfig] = None,
               only_step: Optional[int] = None,
               step_filter: Optional[list[int]] = None,
               dry_run: bool = False) -> WizardConfig:
    """Run the wizard.

    - `only_step=N`    — run exactly step N, skip everything else.
    - `step_filter=…`  — run the listed steps in order, skip others.
      Used by --reconfigure mode to let the user pick a subset
      (e.g. "change step 5 + step 15" without walking 1-4 + 6-14).
    - Both `None`      — full 16-step run (first-time install or
      --force). Banner + ticker + next-steps panel all shown.
    - `dry_run=True`   — walk every step interactively but skip the
      final config save AND the import-adapter run. Lets users
      preview the full 16-step UX without touching disk. Same
      contract as `--express --dry-run`.
    """
    global _DRY_RUN_ACTIVE
    _DRY_RUN_ACTIVE = bool(dry_run)
    try:
        cfg = cfg or load()
        full_run = only_step is None and step_filter is None
        if full_run:
            # Full run: show the banner once at the top.
            ui.banner()
            if dry_run:
                ui.info_line(
                    "[bold yellow]DRY RUN MODE[/] — wizard will walk all "
                    "steps but will NOT write config.toml and will NOT "
                    "run the import adapter."
                )
                ui.print_blank()
        for n, fn in ALL_STEPS:
            if only_step is not None and n != only_step:
                continue
            if step_filter is not None and n not in step_filter:
                continue
            # Progress ticker between steps (not before step 1 when doing a
            # full run; redundant with the banner).
            if full_run and n > 1:
                ui.progress_ticker(n - 1, TOTAL)
            result = fn(cfg)
            if result != "SKIPPED":
                if n not in cfg.completed_steps:
                    cfg.completed_steps.append(n)
        if full_run:
            ui.progress_ticker(TOTAL, TOTAL)
        if dry_run:
            ui.print_blank()
            ui.info_line(
                "[bold yellow]DRY RUN: config NOT written.[/] Re-run "
                "without --dry-run to commit your choices to "
                "~/.throughline/config.toml."
            )
        else:
            path = save(cfg)
            ui.print_blank()
            ui.info_line(f"[green]Config written:[/] {path}")
        if full_run and not dry_run:
            _print_next_steps_panel(cfg)
        return cfg
    finally:
        # Always clear the module-level flag so a later programmatic
        # run_wizard() call doesn't accidentally inherit dry-run mode.
        _DRY_RUN_ACTIVE = False


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
    python install.py                     Full run, but shows a
                                          reconfigure picker if a
                                          prior config exists.
    python install.py --express           One-command install with
                                          auto-detected provider + sane
                                          defaults. No prompts. (~3 sec)
    python install.py --express --dry-run Preview --express without
                                          writing config.
    python install.py --dry-run           Walk all 16 steps interactively
                                          but skip the final config save
                                          AND the import adapter. Useful
                                          for previewing the wizard's UX
                                          without touching disk.
    python install.py --step N            Re-run only step N.
    python install.py --step=N            Same, equals form.
    python install.py --reconfigure       Alias for the picker (skip
                                          the detection prompt).
    python install.py --force             Skip the reconfigure picker,
                                          always run all 16 steps.
    python install.py --help | -h         Print this help and exit.

Examples:
    python install.py                     First-time setup
    python install.py --express           Already exported an API key?
                                          Skip the 16-step interview.
    python install.py --step 4            Change LLM provider only
    python install.py --step 13           Re-run first-card preview
    python install.py --step 15           Change daily budget cap
    python install.py --reconfigure       Pick which steps to re-run

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
    <PROVIDER>_API_KEY         LLM key the preview call reads (provider
                               name depends on step 4 choice)
"""


# Step registry for --reconfigure / picker display. The tuple is
# (step_n, title, default_when_selected). Kept separate from
# ALL_STEPS so the labels stay short enough for a picker line.
_STEP_LABELS: list[tuple[int, str]] = [
    (1,  "Python + deps"),
    (2,  "Mission (Full / RAG-only / Notes-only)"),
    (3,  "Vector DB"),
    (4,  "LLM provider backend"),
    (5,  "LLM model"),
    (6,  "Privacy level"),
    (7,  "Retrieval backend (embedder + reranker)"),
    (8,  "Prompt family"),
    (9,  "Import source"),
    (10, "Import scan + consent"),
    (11, "Refine tier (Skim / Normal / Deep)"),
    (12, "Card structure"),
    (13, "First-card preview + 5 dials"),
    (14, "Taxonomy strategy"),
    (15, "Daily USD budget cap"),
    (16, "Summary + save"),
]


def _parse_step_selection(raw: str) -> list[int]:
    """Parse '5', '5,7,11', '9-13', '5,9-13' into a sorted unique list
    of step numbers. Raises ValueError on garbage input."""
    out: set[int] = set()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            lo_s, hi_s = part.split("-", 1)
            lo, hi = int(lo_s), int(hi_s)
            if lo > hi:
                raise ValueError(f"range {part!r} descends")
            for n in range(lo, hi + 1):
                if 1 <= n <= TOTAL:
                    out.add(n)
        else:
            n = int(part)
            if 1 <= n <= TOTAL:
                out.add(n)
    if not out:
        raise ValueError("no valid step numbers found")
    return sorted(out)


def _reconfigure_picker(cfg: WizardConfig) -> list[int]:
    """Present the reconfigure menu for an existing config and return
    the list of step numbers to actually run. Empty list = exit.

    The menu is deliberately minimal — three choices, no nested
    submenus, one input() call per choice. Kept testable by
    monkeypatching builtins.input.
    """
    ui.print_blank()
    ui.section_title("Existing config detected — reconfigure mode")
    ui.info_line("A config.toml was found at the usual location. You "
                 "don't have to re-run every step; pick what to change.")
    ui.print_blank()

    # Show the current values for the most commonly-changed fields so
    # the user can see what's already set.
    ui.kv_row("mission",       cfg.mission)
    ui.kv_row("llm_provider",  f"{cfg.llm_provider} · {cfg.llm_provider_id}")
    ui.kv_row("refine_tier",   cfg.refine_tier)
    ui.kv_row("daily_budget",  f"${cfg.daily_budget_usd}")
    ui.kv_row("taxonomy",      cfg.taxonomy_source)
    ui.print_blank()

    choice = ui.pick_option(
        "What do you want to do?",
        [
            ("pick", "Pick specific steps to re-run",
             "Enter a comma-separated list like `5,9-13,15`. Skipped "
             "steps keep their saved values."),
            ("all", "Run all 16 steps",
             "Same as running install.py on a fresh machine. Your "
             "existing values become the defaults (press Enter to keep)."),
            ("summary", "Show summary and exit",
             "Print the current config and do nothing else. Useful to "
             "audit what's saved."),
            ("cancel", "Cancel and exit without changes", ""),
        ],
        default_key="pick",
    )

    if choice == "cancel":
        ui.info_line("Cancelled.")
        return []

    if choice == "summary":
        # Run just step 16 (summary) which prints all fields; that
        # function exits the wizard when the user declines to save,
        # so we do the same here by returning the singleton.
        return [16]

    if choice == "all":
        return list(range(1, TOTAL + 1))

    # choice == "pick"
    while True:
        raw = ui.ask_text(
            "Which steps? (e.g. 5 · 5,9 · 9-13 · 5,9-13,15)",
            default="",
        ).strip()
        if not raw:
            ui.info_line("No steps selected — exiting.")
            return []
        try:
            steps = _parse_step_selection(raw)
        except ValueError as e:
            ui.info_line(f"[yellow]Invalid: {e}. Try again.[/]")
            continue
        # Always append step 16 (summary + save) so the picked steps
        # actually persist to config.toml.
        if 16 not in steps:
            steps.append(16)
        return steps


def run_express(dry_run: bool = False) -> int:
    """Single-command install for the 'I have an API key, just give
    me a working config' user. Auto-detects the LLM provider from
    env, fills in sensible defaults for everything else, writes
    config + prints the next-steps panel.

    Returns:
        0 on success, 2 if no provider key is detected and the user
        needs to run the wizard normally to pick one.
    """
    from .config import save, WizardConfig
    from . import providers as _providers

    autodetected = _providers.detect_configured_provider()
    if not autodetected:
        ui.banner()
        ui.section_title("Express install — no LLM key detected")
        ui.print_blank()
        ui.info_line(
            "Express mode auto-detects whichever LLM provider's env "
            "var is exported (OPENAI_API_KEY, ANTHROPIC_API_KEY, "
            "OPENROUTER_API_KEY, …). None are set on this shell."
        )
        ui.info_line("")
        ui.info_line(
            "Either:\n"
            "  1. Export an API key for one of the 16 supported "
            "providers, then re-run [green]python install.py "
            "--express[/].\n"
            "  2. Run the full wizard ([green]python install.py[/]) "
            "to pick a provider interactively, including ollama for "
            "fully-local installs that don't need a cloud key."
        )
        return 2

    preset = _providers.get_preset(autodetected)
    cfg = WizardConfig(
        mission="full",
        vector_db="qdrant",
        api_key_source="env",
        llm_provider=autodetected,
        llm_provider_id=preset.models[0][0] if preset.models else "",
        privacy="local_only" if autodetected in ("ollama", "lm_studio")
                else "hybrid",
        embedder="bge-m3",
        reranker="bge-reranker-v2-m3",
        prompt_family=("claude" if "claude" in (preset.models[0][0]
                                                 if preset.models
                                                 else "").lower()
                       else "gpt" if "gpt" in (preset.models[0][0]
                                                if preset.models
                                                else "").lower()
                       else "generic"),
        import_source="none",
        refine_tier="normal",
        card_structure="standard",
        taxonomy_source="minimal",
        daily_budget_usd=20.0,
        completed_steps=list(range(1, 17)),
    )

    ui.banner()
    ui.section_title(
        f"Express install — auto-detected {preset.name}"
        + ("  [DRY RUN]" if dry_run else ""))
    ui.print_blank()
    ui.info_line(f"[dim]LLM provider:[/] {preset.name} (env: {preset.env_var})")
    ui.info_line(f"[dim]Model:[/]        {cfg.llm_provider_id or '(none)'}")
    ui.info_line(f"[dim]Mission:[/]      {cfg.mission}")
    ui.info_line(f"[dim]Privacy:[/]      {cfg.privacy}")
    ui.info_line(f"[dim]Vector DB:[/]    {cfg.vector_db}")
    ui.info_line(f"[dim]Refine tier:[/]  {cfg.refine_tier}")
    ui.info_line(f"[dim]Daily budget:[/] ${cfg.daily_budget_usd}")
    ui.info_line(
        f"[dim]Cost:[/] "
        f"{_format_cost_line(cfg.refine_tier, cfg.daily_budget_usd)}"
    )
    ui.print_blank()

    if dry_run:
        ui.info_line("[yellow]DRY RUN: config NOT written. "
                      "Re-run without --dry-run to commit.[/]")
        return 0

    path = save(cfg)
    ui.info_line(f"[green]Config written:[/] {path}")
    ui.print_blank()
    _print_next_steps_panel(cfg)
    ui.print_blank()
    ui.info_line(
        "[dim]Want to customize? Run [green]python install.py "
        "--reconfigure[/][dim] to pick which steps to redo.[/]"
    )
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    # Windows terminals default to GBK / cp1252; reconfigure stdio to UTF-8
    # so box characters + emoji render instead of crashing. Idempotent --
    # __main__ also calls this before dispatching.
    ui.ensure_utf8_stdio()
    argv = argv if argv is not None else sys.argv[1:]
    only = None
    force_full = False
    force_picker = False
    express = False
    dry_run = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help", "help"):
            print(WIZARD_USAGE)
            return 0
        if a == "--force":
            force_full = True
        elif a == "--reconfigure":
            force_picker = True
        elif a == "--express":
            express = True
        elif a == "--dry-run":
            dry_run = True
        elif a.startswith("--step"):
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

    # --express short-circuits everything else (explicit user intent).
    if express:
        return run_express(dry_run=dry_run)

    # Build kwargs lazily so existing test mocks of `run_wizard` that
    # don't take `dry_run` keep working — only thread the kwarg
    # through when the user actually asked for it.
    extra: dict = {"dry_run": True} if dry_run else {}

    # --step N short-circuits the picker (explicit user intent).
    if only is not None:
        run_wizard(only_step=only, **extra)
        return 0

    # Reconfigure picker: show it when a config.toml exists and the
    # user didn't pass --force. Also shown when --reconfigure was
    # passed explicitly (even on a fresh install, though with fewer
    # useful choices).
    from .config import config_path, load as _load
    existing = config_path().exists()
    if (existing or force_picker) and not force_full:
        cfg = _load()
        selected = _reconfigure_picker(cfg)
        if not selected:
            return 0
        # If the user picked "all" we run the whole wizard unhindered;
        # otherwise we run steps in order and let the skipped ones
        # keep their cfg values.
        if selected == list(range(1, TOTAL + 1)):
            run_wizard(cfg=cfg, **extra)
        else:
            run_wizard(cfg=cfg, step_filter=selected, **extra)
        return 0

    # Fresh install or --force: run the whole wizard.
    run_wizard(**extra)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
