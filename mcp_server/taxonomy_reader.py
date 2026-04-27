"""Read the active throughline taxonomy + count cards per domain.

No LLM calls, no API hits. Two data sources:

1. **`daemon.taxonomy.VALID_X_SET`** — the active X-axis domain
   list. The daemon already does the override resolution
   (`config/taxonomy.py` user override → bundled default), so we
   just import what it loaded. If the import fails (daemon not
   installed in this Python env), fall back to an empty list and
   surface that as a doctor-able state.

2. **Vault frontmatter scan** — walk the configured vault for
   `*.md` files, parse YAML frontmatter, count by X-axis domain
   (the first tag in `tags[]` that isn't `y/*` or `z/*`).

Vault scan is cached for 60s to avoid re-walking on every MCP
`list_topics` call. Cache is module-level + clear-able for tests.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Optional

import yaml

from mcp_server.config import get_vault_root


_VAULT_CACHE_TTL_SEC = 60
_vault_cache: dict[str, tuple[float, dict[str, int]]] = {}
_FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def clear_cache() -> None:
    """Drop the vault scan cache. Call between tests."""
    _vault_cache.clear()


def list_domains(prefix: Optional[str] = None) -> list[str]:
    """Return the active VALID_X_SET (domain whitelist). If
    `prefix` is set, return only domains starting with it
    (prefix-match on the leading segment, e.g. 'Health' matches
    'Health/Medicine' and 'Health/Biohack').

    Empty list returned if `daemon.taxonomy` can't be imported —
    let the caller decide how to surface that.
    """
    try:
        from daemon.taxonomy import VALID_X_SET
    except ImportError:
        return []

    domains = list(VALID_X_SET)
    if prefix:
        # Match exact OR prefix + "/" boundary
        return [d for d in domains
                if d == prefix or d.startswith(prefix + "/")]
    return domains


def count_cards_per_domain(
    vault_root: Optional[Path] = None,
    use_cache: bool = True,
) -> dict[str, int]:
    """Walk the vault for `*.md` cards, parse frontmatter, count
    by X-axis domain. Returns a {domain: count} dict.

    Empty dict if the vault root doesn't exist (typical for fresh
    installs that haven't run the daemon yet).

    Cached for 60s per vault_root unless `use_cache=False`.
    """
    vault_root = vault_root or get_vault_root()
    cache_key = str(vault_root)
    now = time.time()

    if use_cache and cache_key in _vault_cache:
        ts, counts = _vault_cache[cache_key]
        if now - ts < _VAULT_CACHE_TTL_SEC:
            return counts

    counts: dict[str, int] = {}
    if not vault_root.exists():
        _vault_cache[cache_key] = (now, counts)
        return counts

    for md_path in vault_root.rglob("*.md"):
        domain = _read_card_domain(md_path)
        if domain:
            counts[domain] = counts.get(domain, 0) + 1

    _vault_cache[cache_key] = (now, counts)
    return counts


# ---------- helpers ----------

def _read_card_domain(md_path: Path) -> str:
    """Parse the first 3KB of a card, return its X-axis domain
    tag (or empty string if not parseable / not present).

    Reading just the head keeps a 1000-card vault scan to a few
    seconds even on slow disks; frontmatter is always at file
    start so reading more buys nothing.
    """
    try:
        head = md_path.read_text(encoding="utf-8", errors="replace")[:3000]
    except OSError:
        return ""

    m = _FM_RE.match(head)
    if not m:
        return ""

    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return ""

    return _domain_from_tags(fm.get("tags") or [])


def _domain_from_tags(tags) -> str:
    """First non-axis tag is the X-axis domain. y/* and z/* are
    form/relation axis tags and skipped."""
    if not isinstance(tags, list):
        return ""
    for t in tags:
        if not isinstance(t, str):
            continue
        if t.startswith("y/") or t.startswith("z/"):
            continue
        return t
    return ""
