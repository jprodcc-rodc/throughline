"""`python -m throughline_cli doctor` — one-shot health check.

Each check answers ONE question with ✓ / ✗ / ! and a remediation hint
when it fails. Order is deliberate: dependencies first (Python, deps),
then config, then services, then runtime artefacts. Fail fast on the
fundamental stuff so the user doesn't read 12 ✗ lines that all collapse
to "you didn't run the wizard yet".

Exit code:
    0 — every check passed
    1 — at least one check failed (suitable for CI / scripts)

Usage:
    python -m throughline_cli doctor
    python -m throughline_cli doctor --quiet      # only print failures
    python -m throughline_cli doctor --json       # machine-readable
"""
from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, List, Optional


@dataclass
class CheckResult:
    name: str
    status: str  # "ok" | "warn" | "fail"
    detail: str = ""
    fix: str = ""


# =========================================================
# Individual checks
# =========================================================

def check_python_version() -> CheckResult:
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 11):
        return CheckResult("python_version", "ok",
                            f"Python {major}.{minor} (>= 3.11 required)")
    return CheckResult(
        "python_version", "fail",
        f"Python {major}.{minor} < 3.11",
        fix="Install Python 3.11+ (the wizard + daemon use stdlib tomllib).",
    )


def check_required_imports() -> CheckResult:
    """Soft-import every runtime package and report missing ones."""
    required = [
        "fastapi", "pydantic", "watchdog", "yaml", "rich",
        "markdownify",
    ]
    missing = []
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if not missing:
        return CheckResult("required_imports", "ok",
                            f"all {len(required)} runtime packages importable")
    return CheckResult(
        "required_imports", "fail",
        f"missing: {', '.join(missing)}",
        fix="Run `pip install -r requirements.txt` in your venv.",
    )


def check_optional_imports() -> CheckResult:
    """Optional backends — informational only."""
    optional = ["torch", "transformers", "openai", "chromadb"]
    available = []
    missing = []
    for mod in optional:
        try:
            __import__(mod)
            available.append(mod)
        except ImportError:
            missing.append(mod)
    detail = f"present: {', '.join(available) or 'none'}"
    if missing:
        detail += f" | absent: {', '.join(missing)}"
    return CheckResult(
        "optional_imports",
        "ok" if available else "warn",
        detail,
        fix=("Install only what you need: `pip install torch transformers` "
              "for the local bge-m3 path; `pip install openai` for the "
              "OpenAI / OpenRouter paths; `pip install chromadb` for "
              "VECTOR_STORE=chroma."),
    )


def _config_dir() -> Path:
    override = os.environ.get("THROUGHLINE_CONFIG_DIR")
    return Path(override).expanduser() if override else (Path.home() / ".throughline")


def check_config_file() -> CheckResult:
    p = _config_dir() / "config.toml"
    if p.exists():
        size = p.stat().st_size
        return CheckResult("config_file", "ok", f"{p} ({size} bytes)")
    return CheckResult(
        "config_file", "fail",
        f"missing: {p}",
        fix="Run `python install.py` (the install wizard).",
    )


def check_config_schema() -> CheckResult:
    """Validate the on-disk TOML against the WizardConfig schema —
    catch typos, stale fields from older releases, and enum drift
    (e.g. privacy = 'cloudmax' instead of 'cloud_max').

    No schema file; authoritative definition is `config.WizardConfig`
    + `config._KNOWN_VALUES`. Passes when no issues; warns otherwise
    (never fails — a bad config shouldn't block the doctor from
    completing other checks)."""
    p = _config_dir() / "config.toml"
    if not p.exists():
        return CheckResult(
            "config_schema", "warn",
            "no config file yet — nothing to validate",
            fix="Run the wizard first.",
        )
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:  # pragma: no cover
            import tomli as tomllib  # type: ignore
        with p.open("rb") as f:
            raw = tomllib.load(f)
    except Exception as e:
        return CheckResult(
            "config_schema", "fail",
            f"could not parse {p.name}: {e}",
            fix=f"Open {p} and fix the TOML syntax error.",
        )
    try:
        from . import config as _config
        issues = _config.validate(raw)
    except Exception as e:
        return CheckResult(
            "config_schema", "warn",
            f"validator unavailable: {e}",
        )
    if not issues:
        return CheckResult(
            "config_schema", "ok",
            f"{len(raw)} keys, all recognized",
        )
    # Compact rendering: first issue inline, rest in the fix hint.
    head = issues[0]
    detail = f"{len(issues)} issue(s); first: {head.kind} on {head.key!r} — {head.detail}"
    fix_parts: list[str] = []
    for it in issues:
        line = f"{it.kind}: {it.key}"
        if it.suggestion:
            line += f" → did you mean {it.suggestion!r}?"
        elif it.detail:
            line += f" ({it.detail})"
        fix_parts.append(line)
    return CheckResult(
        "config_schema", "warn",
        detail,
        fix="; ".join(fix_parts),
    )


def check_state_dir() -> CheckResult:
    state_dir = Path(
        os.getenv(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()
    if state_dir.exists() and state_dir.is_dir():
        return CheckResult("state_dir", "ok", str(state_dir))
    return CheckResult(
        "state_dir", "warn",
        f"missing: {state_dir} (created on first daemon start)",
        fix="Will be created automatically when the refine daemon starts.",
    )


def _http_ping(url: str, timeout: float = 2.0) -> Optional[int]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status
    except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout, OSError):
        return None


def check_qdrant_reachable() -> CheckResult:
    url = os.getenv("QDRANT_URL", "http://localhost:6333").rstrip("/")
    status = _http_ping(f"{url}/healthz")
    if status == 200:
        return CheckResult("qdrant", "ok", f"{url} responding 200")
    if status is not None:
        return CheckResult(
            "qdrant", "warn",
            f"{url} responded {status} (expected 200)",
            fix="Confirm you're hitting Qdrant — that URL might be hosting something else.",
        )
    return CheckResult(
        "qdrant", "fail",
        f"{url} unreachable",
        fix=("Start Qdrant: `docker run -d -p 6333:6333 -p 6334:6334 "
              "-v qdrant_data:/qdrant/storage qdrant/qdrant`. Or set "
              "QDRANT_URL to an existing instance."),
    )


def check_rag_server_reachable() -> CheckResult:
    url = os.getenv("RAG_SERVER_URL", "http://localhost:8000").rstrip("/")
    status = _http_ping(f"{url}/v1/rag/health")
    if status == 200:
        return CheckResult("rag_server", "ok", f"{url} health 200")
    if status is not None:
        return CheckResult(
            "rag_server", "warn",
            f"{url}/v1/rag/health responded {status}",
        )
    return CheckResult(
        "rag_server", "warn",
        f"{url} unreachable (server not running?)",
        fix="Start it: `python rag_server/rag_server.py`.",
    )


def check_daemon_state() -> CheckResult:
    state_file = Path(
        os.getenv(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser() / "refine_state.json"
    if not state_file.exists():
        return CheckResult(
            "daemon_state", "warn",
            f"no state file at {state_file}",
            fix="Daemon hasn't run yet. Start it: `python daemon/refine_daemon.py`.",
        )
    try:
        import time
        age = time.time() - state_file.stat().st_mtime
    except OSError:
        return CheckResult("daemon_state", "warn",
                            f"can't stat {state_file}")
    if age < 86400:
        return CheckResult("daemon_state", "ok",
                            f"state file updated {int(age/60)} min ago")
    return CheckResult(
        "daemon_state", "warn",
        f"state file is {int(age/86400)} days stale",
        fix="Daemon may have stopped. Check ~/throughline_runtime/logs/refine_daemon.log.",
    )


def check_embedder_model_cache() -> CheckResult:
    """Warn if EMBEDDER=bge-m3 but the HF cache doesn't have it."""
    embedder = os.getenv("EMBEDDER", "bge-m3").lower()
    if embedder != "bge-m3":
        return CheckResult(
            "embedder_model_cache", "ok",
            f"EMBEDDER={embedder} (not local — no model download required)",
        )
    hf_cache = Path(os.getenv("HF_HOME") or
                     Path.home() / ".cache" / "huggingface")
    bge = hf_cache / "hub" / "models--BAAI--bge-m3"
    if bge.exists():
        return CheckResult(
            "embedder_model_cache", "ok",
            f"BAAI/bge-m3 cached at {bge}",
        )
    return CheckResult(
        "embedder_model_cache", "warn",
        f"bge-m3 model not in {hf_cache}",
        fix=("First /v1/embeddings call will download ~4.6 GB. "
              "Pre-download with: `huggingface-cli download BAAI/bge-m3` "
              "(see DEPLOYMENT.md §bge-m3 preflight)."),
    )


def check_llm_provider_key() -> CheckResult:
    """U28 · check that the resolved provider has a key set.

    Uses the same precedence as the daemon: env > config.toml >
    autodetect > openrouter. This is the check that catches the
    classic "wizard picked SiliconFlow but I forgot to export
    SILICONFLOW_API_KEY" failure mode.
    """
    try:
        from . import active_provider as ap
        from . import providers as pr
    except ImportError:  # pragma: no cover
        return CheckResult("llm_provider", "warn",
                            "couldn't import throughline_cli.active_provider")

    provider_id = ap.resolve_provider_id()
    try:
        preset = pr.get_preset(provider_id)
    except ValueError:
        return CheckResult(
            "llm_provider", "warn",
            f"resolved to unknown provider id {provider_id!r}",
            fix=("Run `python install.py --step 4` to re-pick, or "
                  "clear THROUGHLINE_LLM_PROVIDER env var."),
        )

    key = pr.resolve_api_key(provider_id)
    if key:
        return CheckResult(
            "llm_provider", "ok",
            f"{preset.name} · {preset.env_var} set",
        )
    # No key — but don't fail hard unless config explicitly picks this
    # provider (warn so fresh installs don't see red).
    return CheckResult(
        "llm_provider", "warn",
        f"{preset.name} selected but {preset.env_var} not set",
        fix=(f"Get a key at {preset.signup_url or '<check provider docs>'}, "
              f"then `export {preset.env_var}=...` in your shell. If you "
              f"meant a different provider, re-run `python install.py --step 4`."),
    )


def check_taxonomy_observations() -> CheckResult:
    p = Path(
        os.getenv(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser() / "taxonomy_observations.jsonl"
    if not p.exists():
        return CheckResult(
            "taxonomy_observations", "warn",
            f"no observations log at {p}",
            fix=("Daemon hasn't refined a card yet (or v0.2.0 wiring is "
                  "broken). Refine at least one card and re-run."),
        )
    try:
        rows = sum(1 for line in p.read_text(encoding="utf-8").splitlines()
                    if line.strip())
    except OSError:
        return CheckResult("taxonomy_observations", "warn",
                            f"can't read {p}")
    return CheckResult(
        "taxonomy_observations", "ok",
        f"{rows} observation(s) in {p.name}",
    )


def check_taxonomy_pending() -> CheckResult:
    """U27.5 — surface pending taxonomy growth candidates.

    The U27 loop's value collapses if users never run `taxonomy
    review`. The doctor is the obvious place to remind them. Status
    `ok` when nothing is pending; `warn` when the user has work to
    do — never `fail` because pending candidates are normal, not
    broken.
    """
    try:
        from . import taxonomy as tx
    except Exception as e:
        return CheckResult(
            "taxonomy_pending", "warn",
            f"taxonomy module unavailable: {e}",
        )
    n = tx.pending_candidates_count()
    if n == 0:
        return CheckResult(
            "taxonomy_pending", "ok",
            "no growth candidates pending review",
        )
    plural = "s" if n != 1 else ""
    return CheckResult(
        "taxonomy_pending", "warn",
        f"{n} taxonomy candidate{plural} pending review",
        fix=("Run `python -m throughline_cli taxonomy review` to "
              "approve / reject / rename each."),
    )


# =========================================================
# Runner
# =========================================================

# Ordered: prerequisites first, then config, then services, then
# runtime artefacts. A failure earlier should make later failures
# unsurprising.
DEFAULT_CHECKS: List[Callable[[], CheckResult]] = [
    check_python_version,
    check_required_imports,
    check_optional_imports,
    check_config_file,
    check_config_schema,
    check_state_dir,
    check_llm_provider_key,
    check_qdrant_reachable,
    check_rag_server_reachable,
    check_daemon_state,
    check_embedder_model_cache,
    check_taxonomy_observations,
    check_taxonomy_pending,
]


def run_all_checks(checks: Optional[List[Callable[[], CheckResult]]] = None
                    ) -> List[CheckResult]:
    return [c() for c in (checks or DEFAULT_CHECKS)]


# =========================================================
# CLI rendering
# =========================================================

_ICON = {"ok": "✓", "warn": "!", "fail": "✗"}
_COLOUR = {"ok": "green", "warn": "yellow", "fail": "red"}


def _render_human(results: List[CheckResult], quiet: bool = False) -> str:
    try:
        from . import ui
        console = ui.console
        out_lines: list[str] = []
        out_lines.append("")
        for r in results:
            if quiet and r.status == "ok":
                continue
            icon = _ICON[r.status]
            colour = _COLOUR[r.status]
            console.print(f"  [{colour}]{icon}[/] [bold]{r.name:<24}[/] "
                            f"[dim]{r.detail}[/]")
            if r.status != "ok" and r.fix:
                console.print(f"      [dim]→ {r.fix}[/]")
        # Summary footer
        n_ok = sum(1 for r in results if r.status == "ok")
        n_warn = sum(1 for r in results if r.status == "warn")
        n_fail = sum(1 for r in results if r.status == "fail")
        console.print()
        if n_fail:
            console.print(f"  [red]{n_fail} fail[/] · "
                            f"[yellow]{n_warn} warn[/] · "
                            f"[green]{n_ok} ok[/]")
        elif n_warn:
            console.print(f"  [yellow]{n_warn} warn[/] · "
                            f"[green]{n_ok} ok[/] (no failures)")
        else:
            console.print(f"  [green]All {n_ok} checks passed.[/]")
        return ""
    except Exception:
        # Fallback if rich isn't importable for some reason — keep
        # doctor working as a literal last-resort tool.
        return _render_plain(results, quiet=quiet)


def _render_plain(results: List[CheckResult], quiet: bool = False) -> str:
    lines = [""]
    for r in results:
        if quiet and r.status == "ok":
            continue
        lines.append(f"  {_ICON[r.status]} {r.name:<24} {r.detail}")
        if r.status != "ok" and r.fix:
            lines.append(f"      -> {r.fix}")
    n_fail = sum(1 for r in results if r.status == "fail")
    n_warn = sum(1 for r in results if r.status == "warn")
    n_ok = sum(1 for r in results if r.status == "ok")
    lines.append("")
    lines.append(f"  {n_fail} fail · {n_warn} warn · {n_ok} ok")
    out = "\n".join(lines)
    print(out)
    return out


def _render_json(results: List[CheckResult]) -> None:
    print(json.dumps([asdict(r) for r in results], indent=2,
                     ensure_ascii=False))


def main(argv: List[str]) -> int:
    quiet = False
    fmt = "human"
    for arg in argv:
        if arg in ("-q", "--quiet"):
            quiet = True
        elif arg == "--json":
            fmt = "json"
        elif arg in ("-h", "--help", "help"):
            print("Usage: python -m throughline_cli doctor "
                  "[--quiet | --json]")
            print("  --quiet  Only print warnings + failures.")
            print("  --json   Machine-readable output.")
            return 0
        else:
            print(f"Unknown argument: {arg!r}", file=sys.stderr)
            return 2

    results = run_all_checks()
    if fmt == "json":
        _render_json(results)
    else:
        _render_human(results, quiet=quiet)
    n_fail = sum(1 for r in results if r.status == "fail")
    return 1 if n_fail else 0
