"""`python -m throughline_cli uninstall` — cross-platform teardown.

Parity with `scripts/uninstall.sh` (macOS/Linux) and
`scripts/uninstall.ps1` (Windows). The shell scripts remain useful
for CI / automation; this Python CLI is the ergonomic default for
interactive teardown.

What this touches:
- `~/.throughline/` — wizard config + any stored state. Removed by
  default (`--keep-config` to retain).
- `$THROUGHLINE_STATE_DIR` (default `~/throughline_runtime/state/`)
  — daemon state, cost stats, taxonomy observations. Removed by
  default (`--keep-state` to retain).
- `$THROUGHLINE_LOG_DIR`  (default `~/throughline_runtime/logs/`)
  — rotating logs. Removed by default (`--keep-logs` to retain).
- `$THROUGHLINE_RAW_ROOT` (default `.../openwebui_raw/`) — raw
  conversation exports. Removed by default (`--keep-raw` to retain).
- Qdrant collection — NOT dropped by default (`--drop-collection`
  to opt in). Deleting is a one-way operation; re-ingest costs
  money.
- Refined vault — NEVER touched. Always the user's data.
- Docker Qdrant container — stopped if `--stop-qdrant` is passed
  AND a container named `throughline-qdrant` is found running.
- OpenWebUI Filter Function — NOT touched. User must remove from
  OpenWebUI Admin → Functions manually; we print the hint.

Every destructive step is prompted unless `--yes` is passed.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, List, Optional


# =========================================================
# Path resolution
# =========================================================

def _config_dir() -> Path:
    override = os.environ.get("THROUGHLINE_CONFIG_DIR")
    return Path(override).expanduser() if override else (Path.home() / ".throughline")


def _state_dir() -> Path:
    return Path(
        os.environ.get(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()


def _log_dir() -> Path:
    return Path(
        os.environ.get(
            "THROUGHLINE_LOG_DIR",
            str(Path.home() / "throughline_runtime" / "logs"),
        )
    ).expanduser()


def _raw_root() -> Path:
    return Path(
        os.environ.get(
            "THROUGHLINE_RAW_ROOT",
            str(Path.home() / "throughline_runtime" / "sources" / "openwebui_raw"),
        )
    ).expanduser()


def _qdrant_url() -> str:
    return os.environ.get("QDRANT_URL", "http://localhost:6333").rstrip("/")


def _qdrant_collection() -> str:
    return (
        os.environ.get("RAG_COLLECTION")
        or os.environ.get("QDRANT_COLLECTION")
        or "obsidian_notes"
    )


# =========================================================
# Individual teardown steps
# =========================================================

def _rm_dir(path: Path, label: str, out: Callable[[str], None]) -> None:
    if not path.exists():
        out(f"  [dim]skip:[/] {label} ({path}) does not exist")
        return
    try:
        shutil.rmtree(path)
        out(f"  [green]removed:[/] {label} ({path})")
    except OSError as e:
        out(f"  [red]failed:[/] {label} ({path}) — {e}")


def _drop_qdrant_collection(out: Callable[[str], None]) -> None:
    url = f"{_qdrant_url()}/collections/{_qdrant_collection()}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if 200 <= resp.status < 300:
                out(f"  [green]dropped:[/] collection "
                     f"{_qdrant_collection()!r} at {url}")
            else:
                out(f"  [yellow]unexpected:[/] DELETE returned "
                     f"{resp.status}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            out(f"  [dim]skip:[/] collection {_qdrant_collection()!r} "
                 f"not found")
        else:
            out(f"  [red]failed:[/] DELETE {url} -> {e}")
    except urllib.error.URLError as e:
        out(f"  [red]failed:[/] {url} unreachable — {e.reason}")


def _stop_qdrant_container(out: Callable[[str], None]) -> None:
    """Stop `throughline-qdrant` if running. Noop if Docker isn't
    installed or the container isn't there. Never removes the
    Qdrant data volume — that's a separate conscious decision."""
    for cmd in (["docker", "stop", "throughline-qdrant"],
                 ["docker", "rm", "throughline-qdrant"]):
        try:
            subprocess.run(cmd, check=False, capture_output=True, timeout=30)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            out("  [dim]skip:[/] docker not available or container "
                 "not found")
            return
    out("  [green]stopped:[/] Docker container throughline-qdrant "
         "(data volume throughline_qdrant_data preserved)")


# =========================================================
# CLI
# =========================================================

USAGE = """\
throughline uninstall — interactive teardown.

Usage:
    python -m throughline_cli uninstall [options]

Options:
    --yes               Assume yes for every prompt (non-interactive).
    --keep-config       Keep ~/.throughline/ (wizard config).
    --keep-state        Keep the state dir (daemon state + costs).
    --keep-logs         Keep the log dir.
    --keep-raw          Keep raw conversation exports.
    --drop-collection   Drop the Qdrant collection (one-way).
    --stop-qdrant       Stop the `throughline-qdrant` Docker container
                        (preserves the data volume).
    --dry-run           Print what WOULD be removed; change nothing.
    -h, --help          Print this help and exit.

What stays:
    Your refined vault (never touched).
    OpenWebUI Filter Function — remove manually from OpenWebUI
    Admin panel → Functions.
"""


def _ask(prompt: str, default_yes: bool,
          reader: Callable[[str], str] = input) -> bool:
    default_label = "Y/n" if default_yes else "y/N"
    raw = reader(f"  {prompt} [{default_label}] ").strip().lower()
    if not raw:
        return default_yes
    return raw in ("y", "yes")


def main(argv: List[str],
          *,
          reader: Callable[[str], str] = input,
          out: Optional[Callable[[str], None]] = None) -> int:
    # Routed output so tests can capture + suppress rich formatting.
    if out is None:
        try:
            from . import ui
            out = lambda s: ui.console.print(s)  # noqa: E731
        except Exception:
            out = print

    flags = {
        "yes": False,
        "keep_config": False,
        "keep_state": False,
        "keep_logs": False,
        "keep_raw": False,
        "drop_collection": False,
        "stop_qdrant": False,
        "dry_run": False,
    }
    for a in argv:
        if a in ("-h", "--help", "help"):
            print(USAGE)
            return 0
        key = a.lstrip("-").replace("-", "_")
        if key in flags:
            flags[key] = True
        else:
            print(f"Unknown argument: {a!r}\n", file=sys.stderr)
            print(USAGE, file=sys.stderr)
            return 2

    # Target inventory so the dry-run summary is informative.
    targets = [
        ("wizard config", _config_dir(),             flags["keep_config"]),
        ("daemon state",  _state_dir(),              flags["keep_state"]),
        ("logs",          _log_dir(),                flags["keep_logs"]),
        ("raw conversations", _raw_root(),           flags["keep_raw"]),
    ]

    out("throughline uninstall")
    out("  ---------------------")
    out(f"  qdrant URL   : {_qdrant_url()}")
    out(f"  qdrant coll. : {_qdrant_collection()}")
    out("")

    for label, path, keep in targets:
        if keep:
            out(f"  [dim]keep:[/] {label} ({path})")
        else:
            if flags["dry_run"]:
                out(f"  [yellow]would remove:[/] {label} ({path})")
            else:
                if flags["yes"] or _ask(f"remove {label} at {path}?",
                                          default_yes=False, reader=reader):
                    _rm_dir(path, label, out)
                else:
                    out(f"  [dim]skip:[/] {label}")

    # Qdrant collection — separate gate; default stays.
    if flags["drop_collection"]:
        if flags["dry_run"]:
            out(f"  [yellow]would drop:[/] Qdrant collection "
                 f"{_qdrant_collection()!r}")
        else:
            if flags["yes"] or _ask(
                f"drop Qdrant collection {_qdrant_collection()!r} "
                f"at {_qdrant_url()}? (one-way)",
                default_yes=False, reader=reader,
            ):
                _drop_qdrant_collection(out)
            else:
                out("  [dim]skip:[/] Qdrant collection")
    else:
        out(f"  [dim]keep:[/] Qdrant collection "
             f"{_qdrant_collection()!r} (pass --drop-collection to remove)")

    # Docker container.
    if flags["stop_qdrant"]:
        if flags["dry_run"]:
            out("  [yellow]would stop:[/] Docker container "
                 "throughline-qdrant")
        else:
            if flags["yes"] or _ask(
                "stop Docker container `throughline-qdrant`? "
                "(data volume preserved)",
                default_yes=True, reader=reader,
            ):
                _stop_qdrant_container(out)
            else:
                out("  [dim]skip:[/] Docker container")

    out("")
    out("  Your refined vault was NOT touched.")
    out("  To remove the OpenWebUI Filter function: OpenWebUI Admin "
         "panel -> Functions -> delete `throughline_filter`.")
    return 0
