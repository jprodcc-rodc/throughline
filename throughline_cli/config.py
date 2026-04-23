"""Config persistence for the install wizard.

Stores user choices in `~/.throughline/config.toml`. All 16 wizard
steps write one or more keys into this file; subsequent runs load
the file and treat prior values as defaults.

Schema is defined as a dataclass so IDE / type-checker can catch
drift between steps and config readers. TOML is chosen over JSON
because it's human-readable, supports comments, and is Python-native
(tomllib builtin in 3.11+).
"""
from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# tomllib is stdlib on 3.11+; tomli-w is the write side.
if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - fallback for 3.10 / 3.9
    import tomli as tomllib  # type: ignore


def config_dir() -> Path:
    override = os.environ.get("THROUGHLINE_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".throughline"


def config_path() -> Path:
    return config_dir() / "config.toml"


@dataclass
class WizardConfig:
    """User-visible wizard state, one field per significant decision.

    Default values reflect the 'press Enter everywhere' path for a
    Full-flywheel user. Mission branching overrides some of these at
    runtime (e.g. Notes-only blanks `vector_db`, `embedder`,
    `reranker`).
    """
    # Step 2 — Mission (U24)
    mission: str = "full"  # full | rag_only | notes_only

    # Step 3 — Vector DB (U21)
    vector_db: str = "qdrant"  # qdrant | chroma | lancedb | duckdb_vss | sqlite_vec | pgvector | none

    # Step 4 — API key (stored via keyring/env; this is just a pointer)
    api_key_source: str = "env"  # env | keyring | file

    # Step 5 — LLM provider (U11)
    llm_provider_id: str = "anthropic/claude-sonnet-4.6"

    # Step 6 — Privacy level (U18)
    privacy: str = "hybrid"  # local_only | hybrid | cloud_max

    # Step 7 — Retrieval backend (U12 + U20)
    embedder: str = "bge-m3"
    reranker: str = "bge-reranker-v2-m3"  # or "skip"

    # Step 8 — Prompt family (U22, auto-derived from provider)
    prompt_family: str = "claude"  # claude | gpt | gemini | generic

    # Step 9 — Import source (U2)
    import_source: str = "none"  # none | chatgpt | claude | gemini | multiple
    import_path: Optional[str] = None

    # Step 11 — Refine tier (U15)
    refine_tier: str = "normal"  # skim | normal | deep

    # Step 12 — Card structure (U16); ignored when mission == rag_only (U25 fixed)
    card_structure: str = "standard"  # compact | standard | detailed | rag_optimized

    # Step 13 — 5-dial preview overrides (U23)
    dial_tone: str = "neutral"  # formal | neutral | casual
    dial_length: str = "medium"  # short | medium | long
    dial_sections: list[str] = field(
        default_factory=lambda: [
            "scenario", "core_knowledge", "execution",
            "avoid", "insight", "summary",
        ]
    )
    dial_register: str = "technical"  # technical | plain | eli5
    dial_keep_verbatim: bool = False

    # Step 14 — Taxonomy (U13)
    taxonomy_source: str = "derive_from_imports"  # derive_from_vault | derive_from_imports | jd | para | zettel

    # Step 15 — Daily budget cap (U3)
    daily_budget_usd: float = 20.0

    # Step 10 — transient scan results; filled by the adapter dry-run
    # so step 16 summary can cite real numbers and step 16 confirm can
    # trigger the real import. Persisted so `reconfigure` shows the
    # last-seen numbers until re-scanned.
    import_scanned: int = 0
    import_emitted: int = 0
    import_est_tokens: int = 0
    import_est_normal_cost_usd: float = 0.0
    import_est_skim_cost_usd: float = 0.0

    # Metadata
    wizard_version: str = "0.2.0-dev"
    completed_steps: list[int] = field(default_factory=list)


def load() -> WizardConfig:
    """Load config from disk, or return defaults if no file exists."""
    p = config_path()
    if not p.exists():
        return WizardConfig()
    with p.open("rb") as f:
        data = tomllib.load(f)
    cfg = WizardConfig()
    for k, v in data.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    return cfg


def save(cfg: WizardConfig) -> Path:
    """Write config to disk, creating parent directory if needed."""
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    # Hand-render TOML to keep the file tidy + free of tomli-w dependency.
    with p.open("w", encoding="utf-8") as f:
        f.write("# throughline wizard config — regenerated every save.\n")
        f.write(f"# Wizard version: {cfg.wizard_version}\n\n")
        for k, v in asdict(cfg).items():
            f.write(f"{k} = {_toml_value(v)}\n")
    return p


def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if v is None:
        return '""'
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, list):
        items = ", ".join(_toml_value(x) for x in v)
        return "[" + items + "]"
    raise TypeError(f"unhandled TOML value type: {type(v).__name__}")
