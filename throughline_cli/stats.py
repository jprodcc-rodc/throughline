"""`python -m throughline_cli stats` — vault + taxonomy stats.

Reads the vault (vault root + subtree) + taxonomy observations log
+ cost stats and produces a one-screen summary users will screenshot
for social posts. Pure read-only, no network.

Counts cards by scanning the vault for `.md` files with a
frontmatter `primary_x` field. Domain counts come from the
frontmatter, not from the daemon's Qdrant collection — the vault is
the source of truth; Qdrant is an index.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# =========================================================
# Paths
# =========================================================

def _vault_root() -> Path:
    """Resolve where refined cards live.

    Precedence: THROUGHLINE_VAULT_ROOT env > VAULT_PATH env >
    `~/ObsidianVault` (the daemon's documented default).
    """
    for var in ("THROUGHLINE_VAULT_ROOT", "VAULT_PATH"):
        v = os.environ.get(var, "").strip()
        if v:
            return Path(v).expanduser()
    return Path.home() / "ObsidianVault"


def _state_dir() -> Path:
    return Path(
        os.environ.get(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()


def _observations_path() -> Path:
    return _state_dir() / "taxonomy_observations.jsonl"


def _cost_stats_path() -> Path:
    return _state_dir() / "cost_stats.json"


# =========================================================
# Frontmatter extraction (tiny — no PyYAML required)
# =========================================================

_FRONT_RE = re.compile(
    r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL
)


def _extract_frontmatter(text: str) -> Dict[str, Any]:
    """Parse the YAML frontmatter block that sits at the top of every
    refined card. We don't require PyYAML; cards use a known shape
    (quoted strings, lists of quoted strings, numbers). Keep it tight
    and tolerant — unknown keys return whatever string-y form we can
    salvage."""
    m = _FRONT_RE.match(text)
    if not m:
        return {}
    out: Dict[str, Any] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # Quoted string → unwrap.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            out[key] = value[1:-1]
            continue
        # List of strings: [a, b, c] or ["a", "b"].
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                out[key] = []
                continue
            items = []
            for part in inner.split(","):
                part = part.strip()
                if len(part) >= 2 and part[0] == part[-1] and part[0] in "\"'":
                    items.append(part[1:-1])
                elif part:
                    items.append(part)
            out[key] = items
            continue
        # Unquoted scalar.
        out[key] = value
    return out


# =========================================================
# Vault scan
# =========================================================

def scan_vault(root: Optional[Path] = None,
                max_files: int = 20_000) -> Dict[str, Any]:
    """Walk the vault tree, collect per-card stats.

    max_files cap is a safety gate — nobody has 20k cards yet, but
    a rogue symlink loop would be bad.
    """
    root = root if root is not None else _vault_root()
    if not root.exists():
        return {
            "vault_root": str(root),
            "vault_exists": False,
            "total_cards": 0,
            "by_domain": {},
            "oldest_title": None,
            "oldest_date": None,
            "newest_title": None,
            "newest_date": None,
            "largest_title": None,
            "largest_bytes": 0,
        }

    total = 0
    by_domain: Counter = Counter()
    oldest: Tuple[str, str, Path] = ("", "", Path())
    newest: Tuple[str, str, Path] = ("", "", Path())
    largest: Tuple[str, int, Path] = ("", 0, Path())

    for p in root.rglob("*.md"):
        if total >= max_files:
            break
        try:
            size = p.stat().st_size
        except OSError:
            continue
        # Skip buffer stubs (small pointer files) and the runtime
        # issue log — they're not refined cards.
        if size < 100:
            continue
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:4096]
        except OSError:
            continue
        fm = _extract_frontmatter(head)
        primary_x = fm.get("primary_x") or fm.get("domain_x")
        if not primary_x:
            # Not a refined card (no primary_x in frontmatter).
            continue
        total += 1
        by_domain[str(primary_x)] += 1

        title = str(fm.get("title") or p.stem)
        date_str = str(fm.get("date") or "")

        if not oldest[1] or date_str < oldest[1]:
            oldest = (title, date_str, p)
        if not newest[1] or date_str > newest[1]:
            newest = (title, date_str, p)
        if size > largest[1]:
            largest = (title, size, p)

    return {
        "vault_root": str(root),
        "vault_exists": True,
        "total_cards": total,
        "by_domain": dict(by_domain.most_common()),
        "oldest_title": oldest[0] or None,
        "oldest_date": oldest[1] or None,
        "newest_title": newest[0] or None,
        "newest_date": newest[1] or None,
        "largest_title": largest[0] or None,
        "largest_bytes": largest[1],
    }


# =========================================================
# Taxonomy observations
# =========================================================

def taxonomy_obs_stats(path: Optional[Path] = None) -> Dict[str, Any]:
    p = path if path is not None else _observations_path()
    if not p.exists():
        return {"exists": False, "total": 0, "drift": 0,
                "top_proposals": []}
    total = 0
    drift = 0
    proposals: Counter = Counter()
    try:
        for raw_line in p.read_text(encoding="utf-8").splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                rec = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            total += 1
            primary = str(rec.get("primary_x") or "")
            proposed = str(rec.get("proposed_x_ideal") or "")
            if primary and proposed and primary != proposed:
                drift += 1
                proposals[proposed] += 1
    except OSError:
        return {"exists": False, "total": 0, "drift": 0,
                "top_proposals": []}
    top = proposals.most_common(5)
    return {
        "exists": True,
        "total": total,
        "drift": drift,
        "top_proposals": [{"tag": t, "count": n} for t, n in top],
    }


# =========================================================
# Lifetime cost total (quick rollup)
# =========================================================

def lifetime_cost() -> Dict[str, Any]:
    p = _cost_stats_path()
    if not p.exists():
        return {"exists": False, "total_usd": 0.0, "total_calls": 0}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"exists": False, "total_usd": 0.0, "total_calls": 0}
    total = 0.0
    calls = 0
    for day in (data.get("by_date") or {}).values():
        if not isinstance(day, dict):
            continue
        for rec in day.values():
            if isinstance(rec, dict):
                total += float(rec.get("cost") or 0.0)
                calls += int(rec.get("calls") or 0)
    return {"exists": True, "total_usd": round(total, 4),
            "total_calls": calls}


# =========================================================
# Rendering
# =========================================================

USAGE = """\
throughline stats — vault + taxonomy + lifetime-cost summary.

Usage:
    python -m throughline_cli stats [options]

Options:
    --json      Machine-readable output.
    -h, --help  Print this help and exit.

Reads:
    $THROUGHLINE_VAULT_ROOT / VAULT_PATH       (card count + domains)
    $THROUGHLINE_STATE_DIR / taxonomy_observations.jsonl
    $THROUGHLINE_STATE_DIR / cost_stats.json
"""


def _render_human(vault: Dict[str, Any],
                   obs: Dict[str, Any],
                   cost: Dict[str, Any],
                   out: Callable[[str], None]) -> None:
    out("")
    out("  [bold]Vault[/]")
    if not vault["vault_exists"]:
        out(f"    [yellow]no vault at {vault['vault_root']}[/]")
        out("    [dim]set THROUGHLINE_VAULT_ROOT or run install.py[/]")
    else:
        out(f"    {vault['total_cards']:>6} refined card(s)")
        if vault["by_domain"]:
            out("")
            out("    [dim]domains:[/]")
            for dom, n in list(vault["by_domain"].items())[:10]:
                out(f"      {dom:<24} {n}")
        if vault["oldest_title"]:
            out("")
            out(f"    oldest : {vault['oldest_date']} — "
                 f"{vault['oldest_title'][:60]}")
            out(f"    newest : {vault['newest_date']} — "
                 f"{vault['newest_title'][:60]}")
            out(f"    largest: {vault['largest_bytes']:>6} B — "
                 f"{vault['largest_title'][:60]}")

    out("")
    out("  [bold]Taxonomy growth (U27)[/]")
    if not obs["exists"]:
        out("    [dim]no observations yet — daemon hasn't refined[/]")
    else:
        out(f"    {obs['total']:>6} observation(s)")
        out(f"    {obs['drift']:>6} drift (primary_x != proposed_x_ideal)")
        if obs["top_proposals"]:
            out("")
            out("    [dim]top proposed tags:[/]")
            for row in obs["top_proposals"]:
                out(f"      {row['tag']:<24} {row['count']}")

    out("")
    out("  [bold]Lifetime LLM spend[/]")
    if not cost["exists"]:
        out("    [dim]no cost stats yet[/]")
    else:
        out(f"    ${cost['total_usd']:.4f} across {cost['total_calls']:,} LLM call(s)")


def _render_json(vault: Dict[str, Any],
                  obs: Dict[str, Any],
                  cost: Dict[str, Any]) -> None:
    print(json.dumps({
        "vault": vault,
        "taxonomy": obs,
        "cost": cost,
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }, indent=2, ensure_ascii=False))


def main(argv: List[str],
          *,
          out: Optional[Callable[[str], None]] = None,
          vault_override: Optional[Path] = None,
          obs_override: Optional[Path] = None) -> int:
    if out is None:
        try:
            from . import ui
            out = lambda s: ui.console.print(s)  # noqa: E731
        except Exception:
            out = print

    fmt = "human"
    for a in argv:
        if a in ("-h", "--help", "help"):
            print(USAGE)
            return 0
        if a == "--json":
            fmt = "json"
            continue
        print(f"Unknown argument: {a!r}\n", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2

    vault = scan_vault(vault_override)
    obs = taxonomy_obs_stats(obs_override)
    cost = lifetime_cost()

    if fmt == "json":
        _render_json(vault, obs, cost)
    else:
        _render_human(vault, obs, cost, out)
    return 0
