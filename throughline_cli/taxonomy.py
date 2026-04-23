"""U27.4 · Taxonomy growth CLI.

Reads the observation log written by U27.3, clusters drift rows, applies
thresholds, and lets the user approve or reject each growth candidate.

Subcommands (dispatched from `__main__.py`):

    python -m throughline_cli taxonomy
        Non-interactive status. Prints current VALID_X_SET + growth
        candidates grouped by parent + sample titles. Exits 0.

    python -m throughline_cli taxonomy review
        Interactive walk-through. For each candidate:
          [a]dd              append tag to active taxonomy.py
          [r]eject forever   record in config/taxonomy_rejected.json
          [n]ame-as-different  user supplies preferred form
          [s]kip             do nothing this round

    python -m throughline_cli taxonomy reject <tag>
        Unattended reject by normalized tag (for scripting / undo flows).

Invariants (from docs/TAXONOMY_GROWTH_DESIGN.md §P1-P5):
    - Daemon observer appends; CLI detector reads; only the review
      command's `add`/`name-as-different` action writes to taxonomy.py.
    - Adding a leaf never renames existing leaves (grandfathering).
    - Thresholds guard against volume/time binges and user-vetoed tags.
    - Shares the rendered-module format with U13, so either tool can
      edit the same file.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set


# =========================================================
# Paths
# =========================================================

REPO_ROOT = Path(__file__).resolve().parents[1]


def _state_dir() -> Path:
    return Path(
        os.getenv(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()


def observations_path() -> Path:
    return _state_dir() / "taxonomy_observations.jsonl"


def history_path() -> Path:
    return _state_dir() / "taxonomy_history.jsonl"


def rejected_path() -> Path:
    return REPO_ROOT / "config" / "taxonomy_rejected.json"


def active_taxonomy_path() -> Path:
    """Write target for `add` / `name-as-different` actions.

    Always `config/taxonomy.py`. The shipped `taxonomy.minimal.py` is
    read-only seed content; edits land in the user override file. If it
    doesn't exist yet, callers bootstrap it from the active module
    (usually minimal) before the first write.
    """
    return REPO_ROOT / "config" / "taxonomy.py"


# =========================================================
# Thresholds
# =========================================================

def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


def min_count_threshold() -> int:
    return env_int("TAXONOMY_GROWTH_MIN_COUNT", 5)


def min_day_span_threshold() -> int:
    return env_int("TAXONOMY_GROWTH_MIN_DAYS", 3)


def observation_window_days() -> int:
    return env_int("TAXONOMY_GROWTH_WINDOW_DAYS", 14)


# =========================================================
# Normalisation
# =========================================================

_NORMALISE_SEPARATORS = re.compile(r"[\s_\-]+")
_MULTI_SLASH = re.compile(r"/{2,}")


def normalize_tag(raw: str) -> str:
    """Canonical form for clustering.

    `AI/Agent`, `ai/agents`, `AI Agent`, `AI_Agent`, `AI-Agent` all
    collapse to `ai/agent`. MVP is string-based per design §Layer 3;
    v0.3+ can upgrade to embedding similarity.

    Rules:
    - lowercase
    - strip leading/trailing whitespace and slashes
    - `_`, `-`, whitespace → `/`
    - collapse runs of `/`
    - trailing `s` stripped off each segment for naive singularisation
      (`agents` → `agent`, `mechanisms` → `mechanism`). Two-letter and
      three-letter segments (AI, ML, OS, RAG, SQL) are left alone so
      we don't butcher acronyms into garbage.
    """
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    s = s.lower()
    s = _NORMALISE_SEPARATORS.sub("/", s)
    s = _MULTI_SLASH.sub("/", s).strip("/")
    parts = []
    for seg in s.split("/"):
        if len(seg) > 3 and seg.endswith("s"):
            parts.append(seg[:-1])
        else:
            parts.append(seg)
    return "/".join(parts)


def split_parent(normalized: str) -> tuple[str, bool]:
    """Return (parent_form, has_slash). Parent is the first segment of
    the normalized tag; `has_slash` tells the caller whether the
    candidate is nested (`ai/agent`) or flat (`climbing`)."""
    if "/" in normalized:
        return normalized.split("/", 1)[0], True
    return normalized, False


# =========================================================
# Data classes
# =========================================================

@dataclass
class GrowthCandidate:
    """One clustered drift signal, post-threshold, ready for review."""
    tag: str                      # display form (first-seen casing)
    normalized: str               # clustering key
    parent: str                   # first segment of display form
    parent_exists: bool           # whether `parent` already appears in VALID_X_SET
    count: int
    day_span_days: int
    sample_titles: List[str] = field(default_factory=list)
    first_seen: Optional[str] = None  # ISO ts of earliest observation
    last_seen: Optional[str] = None


# =========================================================
# Observation loading
# =========================================================

def load_observations(path: Optional[Path] = None,
                       window_days: Optional[int] = None,
                       now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Read the JSONL log, drop anything older than the window.

    Bad lines are skipped silently — the log is append-only, so a
    partial write from a prior daemon crash should not prevent the user
    from running review today.
    """
    p = path if path is not None else observations_path()
    if not p.exists():
        return []
    window = window_days if window_days is not None else observation_window_days()
    cutoff = (now or datetime.now(timezone.utc))
    cutoff_epoch = cutoff.timestamp() - window * 86400
    rows: List[Dict[str, Any]] = []
    for raw_line in p.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = rec.get("ts")
        if isinstance(ts, str):
            parsed = _parse_ts(ts)
            if parsed is None or parsed.timestamp() < cutoff_epoch:
                continue
        rows.append(rec)
    return rows


def _parse_ts(ts: str) -> Optional[datetime]:
    try:
        # observer writes "%Y-%m-%dT%H:%M:%SZ"
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# =========================================================
# Rejection registry
# =========================================================

def load_rejected_tags(path: Optional[Path] = None) -> Set[str]:
    p = path if path is not None else rejected_path()
    if not p.exists():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {str(x) for x in (data.get("rejected_tags") or [])}


def add_rejected_tag(normalized: str, path: Optional[Path] = None) -> None:
    p = path if path is not None else rejected_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    current = load_rejected_tags(p)
    current.add(normalized)
    p.write_text(
        json.dumps({"rejected_tags": sorted(current)}, indent=2),
        encoding="utf-8",
    )


# =========================================================
# Detector
# =========================================================

def detect_candidates(
    observations: Iterable[Dict[str, Any]],
    valid_x: Iterable[str],
    rejected_tags: Optional[Set[str]] = None,
    min_count: Optional[int] = None,
    min_days: Optional[int] = None,
) -> List[GrowthCandidate]:
    """Cluster drift rows and return candidates above both thresholds.

    Deduplicates by `card_id` per normalized tag so repeated refines of
    the same card don't inflate count (design §P5).
    """
    rejected = rejected_tags if rejected_tags is not None else set()
    threshold_n = min_count if min_count is not None else min_count_threshold()
    threshold_d = min_days if min_days is not None else min_day_span_threshold()
    valid_normals = {normalize_tag(v) for v in valid_x}

    # cluster_key -> dict(first_seen_ts, last_seen_ts, card_ids, titles, display_form)
    clusters: Dict[str, Dict[str, Any]] = {}

    for rec in observations:
        primary = str(rec.get("primary_x") or "").strip()
        proposed = str(rec.get("proposed_x_ideal") or "").strip()
        if not proposed or proposed == primary:
            continue  # not a drift row
        norm = normalize_tag(proposed)
        if not norm or norm in rejected:
            continue
        if norm in valid_normals:
            continue  # already in taxonomy under some casing
        card_id = str(rec.get("card_id") or "")
        title = str(rec.get("title") or "").strip()
        ts = _parse_ts(str(rec.get("ts") or ""))

        c = clusters.setdefault(norm, {
            "display": proposed,
            "card_ids": set(),
            "titles": [],
            "first_ts": None,
            "last_ts": None,
        })
        if card_id in c["card_ids"]:
            continue
        c["card_ids"].add(card_id)
        if title and title not in c["titles"]:
            c["titles"].append(title)
        if ts is not None:
            if c["first_ts"] is None or ts < c["first_ts"]:
                c["first_ts"] = ts
            if c["last_ts"] is None or ts > c["last_ts"]:
                c["last_ts"] = ts

    out: List[GrowthCandidate] = []
    valid_parents = {normalize_tag(v).split("/", 1)[0] for v in valid_x}

    for norm, c in clusters.items():
        count = len(c["card_ids"])
        if count < threshold_n:
            continue
        if c["first_ts"] is None or c["last_ts"] is None:
            day_span = 0
        else:
            day_span = max(0, (c["last_ts"] - c["first_ts"]).days)
        if day_span < threshold_d:
            continue
        parent, nested = split_parent(norm)
        out.append(GrowthCandidate(
            tag=c["display"],
            normalized=norm,
            parent=c["display"].split("/", 1)[0] if nested else c["display"],
            parent_exists=parent in valid_parents,
            count=count,
            day_span_days=day_span,
            sample_titles=list(c["titles"][:3]),
            first_seen=c["first_ts"].strftime("%Y-%m-%dT%H:%M:%SZ") if c["first_ts"] else None,
            last_seen=c["last_ts"].strftime("%Y-%m-%dT%H:%M:%SZ") if c["last_ts"] else None,
        ))
    out.sort(key=lambda g: (-g.count, g.normalized))
    return out


# =========================================================
# Active taxonomy loading
# =========================================================

def load_valid_x_from_config() -> List[str]:
    """Read VALID_X_SET from the active taxonomy module.

    Prefers `config/taxonomy.py` (user overrides / U13 output / prior
    U27 adds) over `config/taxonomy.minimal.py` (shipped seed).
    Returns the values as a sorted list; order does not matter because
    VALID_X_SET is a set semantically.
    """
    for candidate in (active_taxonomy_path(),
                       REPO_ROOT / "config" / "taxonomy.minimal.py"):
        if candidate.exists():
            return _extract_valid_x(candidate)
    return []


def _extract_valid_x(module_path: Path) -> List[str]:
    """Exec-isolate the module so the real daemon taxonomy isn't
    polluted by random import side-effects."""
    namespace: Dict[str, Any] = {}
    source = module_path.read_text(encoding="utf-8")
    exec(compile(source, str(module_path), "exec"), namespace)
    val = namespace.get("VALID_X_SET")
    if val is None:
        return []
    return sorted(str(x) for x in val)


# =========================================================
# Add action — surgical insert into VALID_X_SET literal
# =========================================================

_VALID_X_LITERAL = re.compile(
    r"(VALID_X_SET\s*=\s*\{)(.*?)(\n\s*\})",
    re.DOTALL,
)


def _ensure_taxonomy_file() -> Path:
    """Bootstrap config/taxonomy.py from the minimal seed if missing.

    We copy the minimal file verbatim so the user's subsequent edits
    (and U13 re-runs) have somewhere to land without clobbering the
    shipped seed.
    """
    out = active_taxonomy_path()
    if out.exists():
        return out
    seed = REPO_ROOT / "config" / "taxonomy.minimal.py"
    out.parent.mkdir(parents=True, exist_ok=True)
    if seed.exists():
        out.write_text(seed.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        # No seed — emit a minimal stub so the regex has something to
        # edit. Shouldn't happen in a normal install.
        out.write_text(
            'from __future__ import annotations\n\n'
            'VALID_X_SET = {\n    "Misc",\n}\n\n'
            'VALID_Y_SET = {\n    "y/Reference",\n}\n\n'
            'VALID_Z_SET = {\n    "z/Node",\n}\n',
            encoding="utf-8",
        )
    return out


def append_to_valid_x(tag: str, module_path: Optional[Path] = None) -> bool:
    """Insert `tag` into the VALID_X_SET literal.

    Returns True if the file was edited, False if the tag was already
    present (no-op). Raises ValueError if the file's VALID_X_SET block
    can't be located — safer to surface the failure than silently skip.
    """
    p = module_path if module_path is not None else _ensure_taxonomy_file()
    text = p.read_text(encoding="utf-8")
    m = _VALID_X_LITERAL.search(text)
    if m is None:
        raise ValueError(
            f"Could not find VALID_X_SET literal in {p}. "
            f"Aborting to avoid corrupting the file."
        )
    body = m.group(2)
    # Skip if tag (exact match) already present.
    # Match quoted string literals inside the set body.
    existing_exact = re.findall(r'"([^"]+)"', body)
    if tag in existing_exact:
        return False
    # Preserve the indentation of the last entry; fall back to 4 spaces.
    indent_match = re.search(r"\n(\s*)\"[^\"]+\",", body)
    indent = indent_match.group(1) if indent_match else "    "
    new_entry = f'\n{indent}"{tag}",'
    # Insert immediately before the closer.
    new_text = text[:m.end(2)] + new_entry + text[m.end(2):]
    p.write_text(new_text, encoding="utf-8")
    return True


# =========================================================
# History log
# =========================================================

def record_history(action: str, tag: str, *,
                    normalized: Optional[str] = None,
                    extra: Optional[Dict[str, Any]] = None,
                    path: Optional[Path] = None) -> None:
    p = path if path is not None else history_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "action": action,
        "tag": tag,
        "normalized": normalized or normalize_tag(tag),
    }
    if extra:
        rec.update(extra)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


# =========================================================
# Actions (pure, called by CLI + tests)
# =========================================================

def action_add(candidate: GrowthCandidate,
                module_path: Optional[Path] = None,
                history: Optional[Path] = None) -> bool:
    """Add the candidate's display form to VALID_X_SET and log it.

    Returns True if the file was edited, False if the tag was already
    present (e.g. user ran review twice and the file was updated out of
    band).
    """
    edited = append_to_valid_x(candidate.tag, module_path=module_path)
    record_history(
        "add", candidate.tag,
        normalized=candidate.normalized,
        extra={"count": candidate.count, "day_span_days": candidate.day_span_days},
        path=history,
    )
    return edited


def action_reject(candidate: GrowthCandidate,
                   rejected: Optional[Path] = None,
                   history: Optional[Path] = None) -> None:
    add_rejected_tag(candidate.normalized, path=rejected)
    record_history(
        "reject", candidate.tag,
        normalized=candidate.normalized,
        extra={"count": candidate.count},
        path=history,
    )


def action_name_as_different(candidate: GrowthCandidate,
                              preferred_tag: str,
                              module_path: Optional[Path] = None,
                              rejected: Optional[Path] = None,
                              history: Optional[Path] = None) -> bool:
    """Add the user's preferred tag AND reject the originally-proposed
    form so the detector doesn't re-surface it next round."""
    edited = append_to_valid_x(preferred_tag, module_path=module_path)
    add_rejected_tag(candidate.normalized, path=rejected)
    record_history(
        "name_as_different", candidate.tag,
        normalized=candidate.normalized,
        extra={
            "preferred_tag": preferred_tag,
            "count": candidate.count,
        },
        path=history,
    )
    return edited


# =========================================================
# CLI entry points
# =========================================================

USAGE = """\
throughline taxonomy — review self-growing taxonomy signals (U27).

Usage:
    python -m throughline_cli taxonomy              Status (non-interactive).
    python -m throughline_cli taxonomy review       Interactive approval loop.
    python -m throughline_cli taxonomy reject TAG   Reject a tag unattended.

Environment:
    TAXONOMY_GROWTH_MIN_COUNT   minimum cards before a tag is proposed
                                (default: 5)
    TAXONOMY_GROWTH_MIN_DAYS    minimum day-span across those cards
                                (default: 3 — guards against one-evening
                                 binges causing permanent taxonomy churn)
    TAXONOMY_GROWTH_WINDOW_DAYS observation window to scan
                                (default: 14)
    THROUGHLINE_STATE_DIR       observation + history log location
"""


def _print_status(candidates: List[GrowthCandidate], valid_x: List[str],
                   out) -> None:
    out("Current VALID_X_SET:")
    for v in valid_x:
        out(f"  - {v}")
    out("")
    if not candidates:
        out("No growth candidates pass thresholds. Keep writing — "
            f"review needs >= {min_count_threshold()} cards over "
            f">= {min_day_span_threshold()} days for a tag to surface.")
        return
    out(f"{len(candidates)} growth candidate(s):")
    for i, c in enumerate(candidates, start=1):
        parent_note = (f"under existing {c.parent}"
                        if c.parent_exists else f"proposes NEW parent {c.parent}")
        out(f"  {i}. {c.tag}  ({parent_note})")
        out(f"     {c.count} cards · {c.day_span_days} days")
        if c.sample_titles:
            titles = ", ".join(f'"{t}"' for t in c.sample_titles)
            out(f"     sample: {titles}")


def cmd_status(out: Optional[Callable[[str], None]] = None) -> int:
    out = out or print
    valid_x = load_valid_x_from_config()
    observations = load_observations()
    rejected = load_rejected_tags()
    candidates = detect_candidates(observations, valid_x, rejected)
    _print_status(candidates, valid_x, out)
    return 0


def _prompt(label: str, reader: Callable[[str], str]) -> str:
    return reader(label).strip()


def cmd_review(reader: Callable[[str], str] = input,
                out: Optional[Callable[[str], None]] = None) -> int:
    """Interactive approval loop. One candidate at a time."""
    out = out or print
    valid_x = load_valid_x_from_config()
    observations = load_observations()
    rejected = load_rejected_tags()
    candidates = detect_candidates(observations, valid_x, rejected)

    if not candidates:
        out("No growth candidates pass thresholds.")
        return 0

    out(f"Found {len(candidates)} growth candidate(s). Review one-by-one.")
    out("Actions: [a]dd  [r]eject forever  [n]ame-as-different  [s]kip  [q]uit")
    out("")

    for i, c in enumerate(candidates, start=1):
        parent_note = (f"under existing {c.parent}"
                        if c.parent_exists else f"proposes NEW parent {c.parent}")
        out(f"Candidate {i}/{len(candidates)}: {c.tag}  ({parent_note})")
        out(f"  {c.count} cards · {c.day_span_days} days")
        if c.sample_titles:
            titles = ", ".join(f'"{t}"' for t in c.sample_titles)
            out(f"  sample titles: {titles}")
        choice = _prompt("  Action [a/r/n/s/q]: ", reader).lower()
        if choice in ("a", "add"):
            edited = action_add(c)
            out(f"  Added \"{c.tag}\" to VALID_X_SET." if edited
                else f"  \"{c.tag}\" was already in VALID_X_SET — no change.")
        elif choice in ("r", "reject"):
            action_reject(c)
            out(f"  Rejected \"{c.normalized}\". Will not resurface.")
        elif choice in ("n", "name"):
            preferred = _prompt("    Preferred tag: ", reader)
            if not preferred:
                out("  Empty name — skipping.")
                continue
            action_name_as_different(c, preferred)
            out(f"  Added \"{preferred}\"; rejected \"{c.normalized}\".")
        elif choice in ("q", "quit"):
            out("  Quitting review; remaining candidates untouched.")
            return 0
        else:
            out("  Skipped.")
    return 0


def cmd_reject_unattended(tag_arg: str,
                            out: Optional[Callable[[str], None]] = None) -> int:
    out = out or print
    norm = normalize_tag(tag_arg)
    if not norm:
        out(f"Invalid tag: {tag_arg!r}")
        return 2
    add_rejected_tag(norm)
    record_history("reject_unattended", tag_arg, normalized=norm)
    out(f"Rejected \"{norm}\". Will not be proposed again.")
    return 0


def main(argv: List[str]) -> int:
    if not argv:
        return cmd_status()
    head = argv[0]
    rest = argv[1:]
    if head in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    if head == "review":
        return cmd_review()
    if head == "reject":
        if not rest:
            print("taxonomy reject: missing TAG argument", file=sys.stderr)
            return 2
        return cmd_reject_unattended(rest[0])
    print(f"Unknown taxonomy subcommand: {head!r}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2
