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

    # Step 5a — LLM provider backend (U28 multi-provider)
    # Which HTTP endpoint / env var to use. See
    # `throughline_cli.providers` for the full registry.
    llm_provider: str = "openrouter"
    # Step 5b — model id, SCOPED to the provider above. OpenRouter
    # expects namespace-prefixed IDs ("anthropic/claude-sonnet-4.6");
    # direct providers expect their own IDs ("claude-sonnet-4-5-20250929"
    # for Anthropic, "gpt-5-mini" for OpenAI, "Qwen/Qwen2.5-72B-Instruct"
    # for SiliconFlow, etc.).
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

    # Step 14 — Taxonomy (U13 + U27.1)
    # minimal: ship config/taxonomy.minimal.py as starting point; U27
    #   observes drift and growth candidates for user approval.
    # derive_from_{vault,imports}: one-shot LLM derivation (U13) via
    #   scripts/derive_taxonomy.py. Best for 100+ cards.
    # jd / para / zettel: fallback templates.
    taxonomy_source: str = "minimal"

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
    # Schema migration marker. Bumped when the WizardConfig shape
    # changes in a way that old configs need a silent migration for
    # (e.g. U28 added `llm_provider`). `load()` uses this to detect
    # pre-migration files and backfill defaults.
    config_schema_version: int = 2


# Current schema version. Bump when you add a field whose default
# depends on another field's value (simple additions don't require
# a bump — tomllib returns the dataclass default for unknown keys).
_CURRENT_SCHEMA_VERSION = 2


def _migrate(cfg: WizardConfig, raw: dict) -> bool:
    """Bring an older config forward to the current schema.

    `cfg` is the dataclass populated with raw values (plus defaults
    for missing fields). `raw` is the dict straight from TOML — lets
    us tell "field not in file" from "field set to the default".

    Returns True iff the caller should rewrite the config file. Safe
    no-op for already-current configs.
    """
    changed = False
    stored_version = raw.get("config_schema_version")

    # --- Migration: U28 multi-provider (no stored version -> v2) ---
    # Pre-U28 configs have no `llm_provider` field. If the raw dict is
    # missing it, backfill from the active env var (autodetect) or fall
    # back to "openrouter" — which is what the daemon would have been
    # doing implicitly anyway.
    if "llm_provider" not in raw:
        try:
            from . import providers as _p
            autodetected = _p.detect_configured_provider()
        except Exception:
            autodetected = None
        cfg.llm_provider = autodetected or "openrouter"
        changed = True

    if stored_version != _CURRENT_SCHEMA_VERSION:
        cfg.config_schema_version = _CURRENT_SCHEMA_VERSION
        changed = True
    return changed


def load() -> WizardConfig:
    """Load config from disk, or return defaults if no file exists.

    Runs schema migrations silently — if the on-disk config predates
    a field that later releases added, we backfill sensible defaults
    and write the config back to disk. No prompt; migrations are
    non-destructive by contract.
    """
    p = config_path()
    if not p.exists():
        return WizardConfig()
    with p.open("rb") as f:
        data = tomllib.load(f)
    cfg = WizardConfig()
    for k, v in data.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)
    # Apply any migrations. `_migrate` returns True when the file
    # needs rewriting; we do that in a try-except so a read-only
    # config (e.g. mounted as Docker secret) doesn't crash the load.
    try:
        if _migrate(cfg, data):
            try:
                save(cfg)
            except OSError:
                pass  # Read-only filesystem -- migration is in-memory only.
    except Exception:
        # Never let a migration bug prevent startup.
        pass
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


# =========================================================
# Schema validation (unknown keys, enum drift, type mismatches)
# =========================================================
#
# The wizard + daemon + migrations tolerate unknown keys silently —
# the philosophy is "never crash on a stale config file". That's
# the right runtime behaviour, but it's bad feedback: a user who
# typos `dailey_budget_usd = 5` gets the default ($20) silently.
# validate() surfaces those problems so the doctor + any UI can
# show them.

# Fields whose values MUST be one of a small known set. Anything
# outside is almost certainly a typo. (Not exhaustive — fields like
# `llm_provider_id` are free-form model strings and intentionally
# excluded.)
_KNOWN_VALUES: dict[str, tuple[str, ...]] = {
    "mission":         ("full", "rag_only", "notes_only"),
    "vector_db":       ("qdrant", "chroma", "lancedb",
                        "duckdb_vss", "duckdb-vss",
                        "sqlite_vec", "sqlite-vec",
                        "pgvector", "none"),
    "api_key_source":  ("env", "keyring", "file"),
    "privacy":         ("local_only", "hybrid", "cloud_max"),
    "prompt_family":   ("claude", "gpt", "gemini", "generic"),
    "import_source":   ("none", "chatgpt", "claude", "gemini", "multiple"),
    "refine_tier":     ("skim", "normal", "deep"),
    "card_structure":  ("compact", "standard", "detailed", "rag_optimized"),
    "dial_tone":       ("formal", "neutral", "casual"),
    "dial_length":     ("short", "medium", "long"),
    "dial_register":   ("technical", "plain", "eli5"),
    # taxonomy_source + embedder + reranker + llm_provider use their
    # own registries — validated against those at wizard time, not here.
}


def _closest(candidate: str, options) -> str | None:
    """Tiny Levenshtein-based suggester — no external dep. Returns
    the closest option if it's within edit distance 2, else None."""
    if not candidate:
        return None

    def _dist(a: str, b: str) -> int:
        if a == b:
            return 0
        if len(a) < len(b):
            a, b = b, a
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            curr = [i] + [0] * len(b)
            for j, cb in enumerate(b, 1):
                cost = 0 if ca == cb else 1
                curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
            prev = curr
        return prev[-1]

    best = None
    best_d = 3  # threshold: must be strictly better
    for opt in options:
        d = _dist(candidate.lower(), opt.lower())
        if d < best_d:
            best_d = d
            best = opt
    return best


@dataclass
class ValidationIssue:
    key: str
    kind: str   # "unknown_key" | "enum_mismatch" | "type_mismatch"
    detail: str
    suggestion: str = ""


def validate(raw: dict) -> list[ValidationIssue]:
    """Inspect a raw config dict (as loaded from TOML) for
    unknown keys, enum drift, and basic type mismatches.

    Returns an empty list for a clean config; one issue per problem
    otherwise. `load()` still succeeds even with validation
    failures — this function exists to surface problems on demand,
    not to block startup."""
    issues: list[ValidationIssue] = []
    known_fields = {f.name for f in WizardConfig.__dataclass_fields__.values()}
    known_fields_lower = {n.lower() for n in known_fields}

    for key, val in raw.items():
        # --- unknown keys (typos / stale field names)
        if key not in known_fields:
            suggestion = ""
            # Case-insensitive exact match → almost certainly a
            # capitalization typo, suggest the canonical form.
            if key.lower() in known_fields_lower:
                for name in known_fields:
                    if name.lower() == key.lower():
                        suggestion = name
                        break
            else:
                near = _closest(key, known_fields)
                if near is not None:
                    suggestion = near
            issues.append(ValidationIssue(
                key=key, kind="unknown_key",
                detail="not a recognized config field",
                suggestion=suggestion,
            ))
            continue

        # --- enum mismatches (known-values fields)
        if key in _KNOWN_VALUES and isinstance(val, str):
            opts = _KNOWN_VALUES[key]
            if val not in opts:
                suggestion = _closest(val, opts) or ""
                issues.append(ValidationIssue(
                    key=key, kind="enum_mismatch",
                    detail=f"value {val!r} is not one of {opts}",
                    suggestion=suggestion,
                ))

        # --- llm_provider: validated dynamically against the 16-entry
        # provider registry (loaded lazily to avoid a circular import
        # at module-load time). Intentionally not in _KNOWN_VALUES
        # because the registry can grow at runtime via
        # `register_preset()`.
        if key == "llm_provider" and isinstance(val, str):
            try:
                from . import providers as _p
                valid_ids = tuple(sorted(p.id for p in _p.list_presets()))
            except Exception:
                valid_ids = ()
            if valid_ids and val not in valid_ids:
                suggestion = _closest(val, valid_ids) or ""
                issues.append(ValidationIssue(
                    key=key, kind="enum_mismatch",
                    detail=f"provider {val!r} not in registry ({len(valid_ids)} known)",
                    suggestion=suggestion,
                ))

        # --- gross type mismatches (TOML parsers usually give us the
        # right type, but a human-edited file can break that).
        dflt = getattr(WizardConfig(), key, None)
        if dflt is not None and not isinstance(val, type(dflt)):
            # Allow int where float is expected (TOML distinguishes).
            if isinstance(dflt, float) and isinstance(val, int):
                continue
            # Allow any list type to match list default.
            if isinstance(dflt, list) and isinstance(val, list):
                continue
            issues.append(ValidationIssue(
                key=key, kind="type_mismatch",
                detail=(f"expected {type(dflt).__name__}, "
                        f"got {type(val).__name__}"),
            ))

    return issues


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
