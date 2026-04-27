"""Reflection Pass daemon — Phase 2 v0.3 scaffolding.

Periodic offline pass that aggregates card-level position_signal
emissions (refiner output) into the cross-card metadata that the
Reflection Layer's MCP tools query: `find_open_threads`,
`check_consistency`, `get_position_drift`.

Per `docs/POSITION_METADATA_SCHEMA.md` § "Reflection Pass daemon —
schema interaction", the pass has 8 stages:

    1. load cards
    2. cluster via mcp_server.topic_clustering
    3. resolve canonical cluster names (LLM)
    4. fill missing position_signal (Path A back-fill, LLM)
    5. detect open threads (no LLM, structural)
    6. detect contradictions (LLM-judged on pairs)
    7. compute drift trajectories (LLM-summarized phases)
    8. write back to vault frontmatter

This module's current state: **scaffolding stub**.

What's real now:
- The pass orchestration shape (`run_pass()`, dry-run mode)
- Card discovery + frontmatter parsing (uses existing helpers)
- Stage-2 clustering via `mcp_server.topic_clustering.cluster_cards`
  (real, since the engineering gate cleared 2026-04-28 at 0.975
  pairwise accuracy)
- Pass watermark / state file (`reflection_pass_state.json`)
- CLI entry point: `python -m daemon.reflection_pass`

What's stub:
- Stages 3-8 are placeholder no-ops with TODO comments
- Each subsequent commit fills in one stage at a time
  (per POSITION_METADATA_SCHEMA milestone order)

Why scaffold first: lets the user run `--dry-run` immediately to
verify schema-compatibility on their vault before any real writes.
Mirrors the MCP Phase 1 stub-first pattern (`5776f3d`).

Engineering gate cleared 2026-04-28 at 0.975 pairwise accuracy
(best threshold 0.70). Phase 2 implementation is unblocked.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional


# Optional yaml dep — daemon already requires it; fall back to JSON
# at module load if missing so the scaffold-import test can run in
# minimal environments.
try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover — daemon install always has yaml
    yaml = None  # type: ignore[assignment]


_log = logging.getLogger(__name__)


# ---------- defaults ----------

def _default_state_dir() -> Path:
    return Path(
        os.getenv(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()


def _default_vault_root() -> Path:
    return Path(
        os.getenv(
            "THROUGHLINE_VAULT_ROOT",
            str(Path.home() / "ObsidianVault"),
        )
    ).expanduser()


def default_state_file() -> Path:
    """Resolve the default `state/reflection_pass_state.json` path.

    Resolved lazily (not import-time) so tests can set
    `THROUGHLINE_STATE_DIR` via `monkeypatch.setenv`.
    """
    return _default_state_dir() / "reflection_pass_state.json"


def default_open_threads_file() -> Path:
    """Resolve default ``state/reflection_open_threads.json`` path.

    Persists the stage-5 output: the list of cards with unresolved
    open questions, plus their cluster name and last-touched date.
    The ``find_open_threads`` MCP tool reads this file rather than
    rescanning the vault on every call.
    """
    return _default_state_dir() / "reflection_open_threads.json"


def default_backfill_state_file() -> Path:
    """Resolve default ``state/reflection_backfill_state.json`` path.

    Persists ``card_path|mtime -> {claim_summary, open_questions}``
    so re-runs skip cards already extracted whose body hasn't
    changed since.
    """
    return _default_state_dir() / "reflection_backfill_state.json"


def _load_backfill_state(path: Path) -> dict[str, dict]:
    """Read persisted card_signature -> essence dict. Returns empty
    on missing/unparseable (treat as cold start)."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def default_cluster_names_file() -> Path:
    """Resolve the default `state/reflection_cluster_names.json` path.

    This file persists ``cluster_signature -> canonical_name`` so
    repeated passes don't re-call the LLM to re-name unchanged
    clusters. Cluster signature includes the membership path list
    so re-clustering with shifted membership invalidates the cache
    naturally.
    """
    return _default_state_dir() / "reflection_cluster_names.json"


def _load_cluster_names(path: Path) -> dict[str, str]:
    """Read persisted cluster_signature -> name. Returns empty dict
    when file is missing or unparseable (treat as cold start)."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


# ---------- pass result types ----------

@dataclass
class PassResult:
    """Summary of a single Reflection Pass run.

    Returned to the CLI for human-readable reporting and persisted
    to `reflection_pass_state.json` so subsequent passes can be
    incremental.
    """
    started_at: str
    finished_at: str
    cards_scanned: int
    cards_reflectable: int        # stage 1.5: slice_id or managed_by set
    cards_excluded: int           # stage 1.5: filtered out (logs, indexes, drafts)
    cards_with_position_signal: int
    cards_clustered: int
    clusters_count: int
    cluster_names_resolved: int   # stage 3 (currently 0; stub)
    backfill_completed: int       # stage 4 (currently 0; stub)
    open_threads_detected: int    # stage 5 (currently 0; stub)
    contradictions_detected: int  # stage 6 (currently 0; stub)
    drift_phases_computed: int    # stage 7 (currently 0; stub)
    cards_updated: int            # stage 8 (currently 0; stub if dry_run)
    dry_run: bool
    stages_completed: list[str] = field(default_factory=list)
    stages_skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ---------- frontmatter helpers ----------

_FRONTMATTER_FENCE = "---"


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split a markdown card into (frontmatter dict, body markdown).

    Returns ({}, full_text) when no frontmatter is present. Returns
    ({}, full_text) when YAML parse fails — better to skip that card
    on this pass than crash the whole run.
    """
    if not text.startswith(_FRONTMATTER_FENCE + "\n"):
        return {}, text

    end_marker = "\n" + _FRONTMATTER_FENCE + "\n"
    end_idx = text.find(end_marker, len(_FRONTMATTER_FENCE) + 1)
    if end_idx == -1:
        return {}, text

    fm_text = text[len(_FRONTMATTER_FENCE) + 1 : end_idx]
    body = text[end_idx + len(end_marker) :]

    if yaml is None:
        return {}, text

    try:
        fm = yaml.safe_load(fm_text) or {}
    except Exception as exc:  # pragma: no cover — depends on user vault
        _log.warning("frontmatter parse failed: %s", exc)
        return {}, text

    if not isinstance(fm, dict):
        return {}, text
    return fm, body


def _read_card(path: Path) -> Optional[dict[str, Any]]:
    """Read a single card. Returns None if read fails (file deleted,
    permissions, etc.).

    Returned shape: ``{path, title, body, tags, position_signal,
    frontmatter}``. ``frontmatter`` is the raw dict for downstream
    stages that need fields beyond the convenience accessors.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        _log.warning("could not read %s: %s", path, exc)
        return None

    fm, body = _parse_frontmatter(text)

    return {
        "path": str(path),
        "title": fm.get("title", path.stem),
        "body": body,
        "tags": fm.get("tags", []) or [],
        "position_signal": fm.get("position_signal"),
        "frontmatter": fm,
    }


def is_reflectable_card(card: dict) -> bool:
    """Decide whether a parsed card belongs in the Reflection Pass.

    Calibrated 2026-04-28 against the author's real vault (2,477
    files; 163 with frontmatter). Of the 163 frontmatter-having
    cards, the reflectable subset is:

    - 63 cards with ``slice_id`` set — these came through the
      daemon's slicer/refiner pipeline (refiner output)
    - 9 cards with non-empty ``managed_by`` (e.g.
      ``manual_profile_interview``) — user-curated master profiles
      following the structured template

    The remaining 91 frontmatter cards have empty ``managed_by``
    AND no ``slice_id``: system index files (Auto Refine Log,
    OpenWebUI Saved Index, Refine Processing Index), profile
    drafts (RODC_Profile_Draft, IFS Parts maps), backup ops
    references, etc. They're not reasoning artifacts; the
    Reflection Layer's three sub-functions (Open Threads,
    Contradiction Surfacing, Drift Detection) don't apply.

    See ``docs/POSITION_METADATA_SCHEMA.md`` § "Vault format
    addendum" for the full vault calibration.

    Args:
        card: Parsed card dict from ``_read_card`` — must contain
            a ``frontmatter`` key (the raw YAML frontmatter dict).

    Returns:
        True if this card should enter Reflection Pass stages 2-8.
        False if it should be skipped (logs / indexes / drafts).
    """
    fm = card.get("frontmatter") or {}
    if not isinstance(fm, dict):
        return False
    if fm.get("slice_id"):
        return True
    # `managed_by` truthy check: empty string is filtered out, but
    # "manual_profile_interview" / "manual_master_dispensary" /
    # "manual_master_backup" / "refine_thinker_daemon_v9" all pass.
    if fm.get("managed_by"):
        return True
    return False


def _walk_vault_for_cards(vault_root: Path) -> list[Path]:
    """Find all `.md` files under vault_root that look like refined
    cards.

    Refined cards live under domain-prefixed directories (10_*, 20_*,
    ..., 90_*) per the Johnny-Decimal vault layout. We exclude
    template / readme / inbox files by checking that the immediate
    grandparent matches the JD prefix pattern. Conservative — better
    to skip a card than to flag a non-card.
    """
    if not vault_root.exists():
        return []

    out: list[Path] = []
    for md in vault_root.rglob("*.md"):
        if md.name.lower() in {"readme.md", "index.md"}:
            continue
        # Check that some ancestor directory is a JD-prefixed domain
        # (10_*, 20_*, etc). Daemon's actual write path uses this
        # invariant so we mirror it.
        if any(
            part[:2].isdigit() and part[2:3] == "_"
            for part in md.relative_to(vault_root).parts[:-1]
        ):
            out.append(md)
    return sorted(out)


# ---------- stage stubs ----------
# Each stage is a function taking (cards, result, dry_run, **opts)
# and mutating cards in-place + appending to result.stages_*.
# Currently all stages 3-8 are stubs with explicit TODO + the
# milestone reference from POSITION_METADATA_SCHEMA.md.


def _stage_cluster(
    cards: list[dict[str, Any]],
    result: PassResult,
    *,
    high_threshold: float = 0.70,
    low_threshold: float = 0.55,
) -> dict[str, list[dict[str, Any]]]:
    """Stage 2 — cluster cards by topic via embedding similarity.

    REAL (not stub). Wraps `mcp_server.topic_clustering.cluster_cards`
    which is the same pipeline used by the engineering gate
    experiment. Returns a dict mapping cluster_id -> list of cards.
    """
    from mcp_server.rag_client import embed_batch
    from mcp_server.topic_clustering import (
        CardForClustering,
        cluster_cards,
        cluster_index,
    )

    if not cards:
        result.stages_completed.append("cluster (empty)")
        return {}

    cluster_inputs = [
        CardForClustering(
            path=c["path"],
            title=c["title"],
            body=c["body"],
            existing_tags=tuple(c["tags"]) if isinstance(c["tags"], list) else (),
        )
        for c in cards
    ]

    clusters = cluster_cards(
        cluster_inputs,
        embed_fn=embed_batch,
        high_threshold=high_threshold,
        low_threshold=low_threshold,
        body_chars=300,
    )

    cidx = cluster_index(clusters)
    result.cards_clustered = len(cidx)
    grouped: dict[int, list[dict[str, Any]]] = {}
    for c in cards:
        cid = cidx.get(c["path"])
        if cid is None:
            continue
        grouped.setdefault(cid, []).append(c)
        c["_cluster_id"] = cid

    result.clusters_count = len(grouped)
    result.stages_completed.append(
        f"cluster ({result.cards_clustered} cards / "
        f"{result.clusters_count} clusters @ thr={high_threshold:.2f})"
    )
    return {str(k): v for k, v in grouped.items()}


ClusterNamer = Callable[[list[str]], str]


def _stage_resolve_cluster_names(
    grouped: dict[str, list[dict[str, Any]]],
    result: PassResult,
    *,
    dry_run: bool,
    namer: Optional[ClusterNamer] = None,
    cluster_names_state: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    """Stage 3 — assign canonical cluster names.

    For each cluster, call ``namer(titles)`` to get a snake_case
    topic identifier (e.g. ``"pricing_strategy"``). Names persist
    to ``cluster_names_state`` so the same cluster_id keeps the same
    name across passes — repeated runs don't re-call the LLM unless
    the cluster's membership has shifted enough to warrant it.

    Args:
        grouped: cluster_id -> list of card dicts.
        result: pass result accumulator (mutated).
        dry_run: when True, skip the actual call and report the
            stage as deferred. Cluster names won't be written, but
            the cluster_id list still tells you what *would* be
            named.
        namer: callable that takes card titles and returns a name.
            ``mcp_server.llm_namer.name_cluster`` is the stock
            implementation; tests pass a deterministic mock.
            When None, the stage is skipped (back-compat with stub
            CLI invocations that don't have an LLM configured).
        cluster_names_state: optional dict from previous pass
            (cluster_id -> name). When provided, clusters whose
            membership signature matches the prior pass keep their
            name without re-calling the namer.

    Returns:
        Dict mapping cluster_id -> canonical name. Empty when stage
        was skipped or all calls failed.
    """
    if not grouped:
        result.stages_skipped.append("resolve_cluster_names (no clusters)")
        return {}

    if namer is None:
        result.stages_skipped.append(
            f"resolve_cluster_names ({len(grouped)} clusters; "
            "no namer configured — pass --enable-llm-naming or "
            "set OPENROUTER_API_KEY)"
        )
        return {}

    if dry_run:
        result.stages_skipped.append(
            f"resolve_cluster_names ({len(grouped)} clusters; dry-run)"
        )
        return {}

    # IMPORTANT: do not rebind to {} via `or {}`. The caller passes
    # in a dict that we mutate in-place so subsequent passes see the
    # cache. Using `or {}` would silently break that contract for
    # cold-start runs (caller passes empty dict, we'd create a new
    # local dict, and the caller's reference would never see updates).
    if cluster_names_state is None:
        cluster_names_state = {}
    names: dict[str, str] = {}
    cached_hits = 0
    new_calls = 0
    failures = 0

    for cid, members in grouped.items():
        # Build a stable signature from cluster membership so we can
        # detect when a previously-named cluster's contents have
        # changed enough to warrant re-naming.
        member_paths = sorted(c.get("path", "") for c in members)
        signature = f"{cid}|{','.join(member_paths)}"
        prior = cluster_names_state.get(signature)
        if prior:
            names[cid] = prior
            cached_hits += 1
            continue

        titles = [str(c.get("title", "")).strip() for c in members]
        titles = [t for t in titles if t]
        if not titles:
            failures += 1
            continue
        try:
            name = namer(titles)
        except Exception as exc:  # noqa: BLE001 — namer can raise anything
            result.errors.append(
                f"cluster {cid} naming failed: {type(exc).__name__}: {exc}"
            )
            failures += 1
            continue
        if not name:
            failures += 1
            continue
        names[cid] = name
        cluster_names_state[signature] = name
        new_calls += 1

    result.cluster_names_resolved = len(names)
    result.stages_completed.append(
        f"resolve_cluster_names ({len(names)} named — "
        f"{cached_hits} cached, {new_calls} new"
        + (f", {failures} failed" if failures else "")
        + ")"
    )
    return names


EssenceExtractor = Callable[[str, str], dict]


def _file_signature(path_str: str) -> str:
    """Build cache key for a card. Combines path + file mtime so
    cache invalidates when the user edits the card. Falls back to
    just the path if stat fails (treat as 'always re-extract')."""
    p = Path(path_str)
    try:
        mtime = int(p.stat().st_mtime)
        return f"{path_str}|{mtime}"
    except OSError:
        return path_str


def _stage_backfill_position_signal(
    cards: list[dict[str, Any]],
    result: PassResult,
    *,
    dry_run: bool,
    extractor: Optional[EssenceExtractor] = None,
    backfill_state: Optional[dict[str, dict]] = None,
) -> None:
    """Stage 4 — Path A back-fill for legacy cards.

    For each card lacking ``position_signal`` in frontmatter, call
    the extractor (Callable) to derive ``claim_summary`` and
    ``open_questions``. Stores the result in
    ``card["_backfill"]`` (in-memory) — actual frontmatter
    writeback is stage 8's job.

    Cache: ``backfill_state`` keyed by ``path|mtime`` so re-runs
    skip cards already extracted whose mtime hasn't changed. The
    state dict is mutated in place (caller persists to disk).

    Args:
        cards: reflectable cards from stage 1.5.
        result: pass result accumulator (mutated).
        dry_run: when True, skip the actual call. Stage reports
            how many cards *would* be back-filled.
        extractor: callable taking (title, body) -> dict
            (``mcp_server.llm_extractor.extract_card_essence``).
            None = skip stage with explicit message.
        backfill_state: optional cache from prior pass.
    """
    eligible = [c for c in cards if not c.get("position_signal")]

    if not eligible:
        result.stages_skipped.append("backfill_position_signal (nothing eligible)")
        return

    if extractor is None:
        result.stages_skipped.append(
            f"backfill_position_signal ({len(eligible)} cards eligible; "
            "no extractor configured — pass --enable-llm-backfill or "
            "set OPENROUTER_API_KEY)"
        )
        return

    if dry_run:
        result.stages_skipped.append(
            f"backfill_position_signal ({len(eligible)} cards eligible; dry-run)"
        )
        return

    if backfill_state is None:
        backfill_state = {}

    cached_hits = 0
    new_calls = 0
    failures = 0

    for card in eligible:
        path = card.get("path", "")
        if not path:
            failures += 1
            continue

        sig = _file_signature(path)
        prior = backfill_state.get(sig)
        if prior:
            card["_backfill"] = prior
            cached_hits += 1
            continue

        title = str(card.get("title", "")).strip()
        body = str(card.get("body", "")).strip()
        if not title or not body:
            failures += 1
            continue

        try:
            essence = extractor(title, body)
        except Exception as exc:  # noqa: BLE001 — extractor can raise anything
            result.errors.append(
                f"backfill failed for {path}: {type(exc).__name__}: {exc}"
            )
            failures += 1
            continue

        # Validate extractor return shape (defense-in-depth — the
        # extractor itself validates, but mock extractors in tests
        # can be lax)
        if (not isinstance(essence, dict)
                or not isinstance(essence.get("claim_summary"), str)
                or not isinstance(essence.get("open_questions"), list)):
            result.errors.append(
                f"backfill returned malformed shape for {path}: {essence!r}"
            )
            failures += 1
            continue

        card["_backfill"] = essence
        backfill_state[sig] = essence
        new_calls += 1

    result.backfill_completed = cached_hits + new_calls
    result.stages_completed.append(
        f"backfill_position_signal ({result.backfill_completed} done — "
        f"{cached_hits} cached, {new_calls} new"
        + (f", {failures} failed" if failures else "")
        + ")"
    )


def _stage_detect_open_threads(
    grouped: dict[str, list[dict[str, Any]]],
    result: PassResult,
    *,
    dry_run: bool,
    threshold: float = 0.75,
) -> None:
    """Stage 5 — detect cards with unresolved open_questions.

    Pure structural (no LLM). For each card with back-filled
    open_questions, scan later cards in the same cluster for
    token-overlap evidence the question got addressed. Cards
    with at least one still-unresolved question are flagged
    in-memory as ``_open_thread: True`` with the unresolved
    list at ``_open_thread_questions``.

    Stage 8 (writeback) translates these to frontmatter.

    Args:
        grouped: cluster_id -> list of card dicts (from stage 2).
        result: pass result accumulator.
        dry_run: when True, computation still runs (it's free —
            no LLM, no I/O) but ``stages_completed`` notes "preview".
            Card mutations happen either way; stage 8 decides
            whether to persist them.
        threshold: token-overlap fraction required for a question
            to count as addressed (default 0.75 — conservative).
    """
    if not grouped:
        result.stages_skipped.append("detect_open_threads (no clusters)")
        return

    from daemon.open_threads import detect_open_threads

    unresolved_by_path = detect_open_threads(grouped, threshold=threshold)

    # Mutate cards in-place so stage 8 can pick up.
    flagged = 0
    for members in grouped.values():
        for card in members:
            still_open = unresolved_by_path.get(card.get("path", ""))
            if still_open:
                card["_open_thread"] = True
                card["_open_thread_questions"] = still_open
                flagged += 1
            else:
                card["_open_thread"] = False
                card["_open_thread_questions"] = []

    result.open_threads_detected = flagged
    label = "preview" if dry_run else "complete"
    result.stages_completed.append(
        f"detect_open_threads ({flagged} cards with unresolved questions, "
        f"{label})"
    )


def _stage_detect_contradictions(
    grouped: dict[str, list[dict[str, Any]]],
    result: PassResult,
    *,
    dry_run: bool,
) -> None:
    """Stage 6 — detect contradicting position_signals across cards.

    STUB. See POSITION_METADATA_SCHEMA milestone 7.

    Real impl: for each cluster with ≥2 cards having confidence:
    asserted, LLM-judge stance + reasoning pairs for contradiction.
    Write paths into `reflection.contradicts` array.
    """
    result.stages_skipped.append("detect_contradictions (stub)")


def _stage_compute_drift(
    grouped: dict[str, list[dict[str, Any]]],
    result: PassResult,
    *,
    dry_run: bool,
) -> None:
    """Stage 7 — segment each topic_cluster into drift phases.

    STUB. See POSITION_METADATA_SCHEMA milestone 8.

    Real impl: for each cluster with ≥3 cards, sort by
    conversation_date, LLM-segment into stance phases, write
    `reflection.drift_phase` per card.
    """
    result.stages_skipped.append("compute_drift (stub)")


def _stage_writeback(
    cards: list[dict[str, Any]],
    result: PassResult,
    *,
    dry_run: bool,
) -> None:
    """Stage 8 — atomic write-back of computed metadata to vault.

    STUB. Will be wired up once any of stages 3-7 produce metadata
    worth writing. Until then, dry_run + actual_run are equivalent.
    """
    if dry_run:
        result.stages_skipped.append("writeback (dry-run)")
    else:
        result.stages_skipped.append("writeback (stub — no real outputs yet)")


# ---------- orchestration ----------

def run_pass(
    vault_root: Optional[Path] = None,
    *,
    dry_run: bool = False,
    high_threshold: float = 0.70,
    low_threshold: float = 0.55,
    state_file: Optional[Path] = None,
    namer: Optional[ClusterNamer] = None,
    cluster_names_file: Optional[Path] = None,
    extractor: Optional["EssenceExtractor"] = None,
    backfill_state_file: Optional[Path] = None,
    open_threads_file: Optional[Path] = None,
) -> PassResult:
    """Run one Reflection Pass over the vault.

    Args:
        vault_root: Path to vault root. Defaults to
            `$THROUGHLINE_VAULT_ROOT` or `~/ObsidianVault`.
        dry_run: If True, do not write back to cards. Stages 1-7
            still run; stage 8 (writeback) is skipped. Useful for
            schema validation against an existing vault before
            committing to actual edits.
        high_threshold: Cosine similarity above which two cards are
            same topic. Default 0.70 per gate experiment best score.
        low_threshold: Pairs in (low, high) need LLM judge once
            wired. Default 0.55.
        state_file: Path to persist pass watermark. Defaults to
            `~/throughline_runtime/state/reflection_pass_state.json`.

    Returns:
        PassResult — summary of what was scanned + what stages ran.
    """
    vault_root = vault_root or _default_vault_root()
    state_file = state_file or default_state_file()
    started = datetime.now(timezone.utc).isoformat()

    paths = _walk_vault_for_cards(vault_root)
    all_cards = []
    for p in paths:
        c = _read_card(p)
        if c is not None:
            all_cards.append(c)

    # Stage 1.5 — filter to reflectable cards (slice_id or
    # managed_by set). Excluded cards are logs / indexes / drafts
    # that aren't reasoning artifacts; processing them would
    # pollute Open Threads / Contradiction Surfacing / Drift
    # Detection with non-reasoning content. See
    # docs/POSITION_METADATA_SCHEMA.md § "Vault format addendum".
    cards = [c for c in all_cards if is_reflectable_card(c)]
    excluded_count = len(all_cards) - len(cards)

    result = PassResult(
        started_at=started,
        finished_at="",
        cards_scanned=len(all_cards),
        cards_reflectable=len(cards),
        cards_excluded=excluded_count,
        cards_with_position_signal=sum(
            1 for c in cards if c.get("position_signal")
        ),
        cards_clustered=0,
        clusters_count=0,
        cluster_names_resolved=0,
        backfill_completed=0,
        open_threads_detected=0,
        contradictions_detected=0,
        drift_phases_computed=0,
        cards_updated=0,
        dry_run=dry_run,
    )

    if not all_cards:
        result.errors.append(
            f"No cards found under {vault_root}. Set "
            "THROUGHLINE_VAULT_ROOT or pass --vault."
        )
        result.finished_at = datetime.now(timezone.utc).isoformat()
        return result

    # Stage 1 — load + parse complete.
    result.stages_completed.append(
        f"load ({len(all_cards)} cards / "
        f"{result.cards_with_position_signal} with position_signal)"
    )
    # Stage 1.5 — reflectable filter applied.
    result.stages_completed.append(
        f"filter_reflectable ({len(cards)} kept / "
        f"{excluded_count} excluded — logs/indexes/drafts)"
    )

    if not cards:
        result.errors.append(
            f"No reflectable cards under {vault_root}. Vault has "
            f"{len(all_cards)} frontmatter cards but none have "
            "slice_id or managed_by set."
        )
        result.finished_at = datetime.now(timezone.utc).isoformat()
        return result

    # Stage 2 — real clustering.
    try:
        grouped = _stage_cluster(
            cards, result,
            high_threshold=high_threshold,
            low_threshold=low_threshold,
        )
    except Exception as exc:
        result.errors.append(f"cluster stage failed: {exc}")
        grouped = {}

    # Stage 3 — real (when namer configured); skipped under dry_run
    # or when no namer was passed (e.g., no API key in env).
    cluster_names_state = _load_cluster_names(cluster_names_file) if cluster_names_file else {}
    cluster_names = _stage_resolve_cluster_names(
        grouped, result,
        dry_run=dry_run,
        namer=namer,
        cluster_names_state=cluster_names_state,
    )

    # Stage 4 — Path A back-fill (real when extractor configured).
    backfill_state = (
        _load_backfill_state(backfill_state_file)
        if backfill_state_file else {}
    )
    _stage_backfill_position_signal(
        cards, result, dry_run=dry_run,
        extractor=extractor, backfill_state=backfill_state,
    )

    # Stages 5-8 — stubs.
    _stage_detect_open_threads(grouped, result, dry_run=dry_run)
    _stage_detect_contradictions(grouped, result, dry_run=dry_run)
    _stage_compute_drift(grouped, result, dry_run=dry_run)
    _stage_writeback(cards, result, dry_run=dry_run)

    result.finished_at = datetime.now(timezone.utc).isoformat()

    # Persist watermark (idempotent; small).
    if not dry_run and state_file:
        try:
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(
                json.dumps(asdict(result), indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            result.errors.append(f"state file write failed: {exc}")

    # Persist cluster names cache so the next pass reuses them.
    if not dry_run and cluster_names_file and cluster_names_state:
        try:
            cluster_names_file.parent.mkdir(parents=True, exist_ok=True)
            cluster_names_file.write_text(
                json.dumps(cluster_names_state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            result.errors.append(f"cluster names file write failed: {exc}")

    # Persist back-fill cache so re-runs skip stable cards.
    if not dry_run and backfill_state_file and backfill_state:
        try:
            backfill_state_file.parent.mkdir(parents=True, exist_ok=True)
            backfill_state_file.write_text(
                json.dumps(backfill_state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            result.errors.append(f"backfill state file write failed: {exc}")

    # Persist open-threads state so find_open_threads MCP tool can
    # read it without rescanning the vault on every call. Written
    # even on dry_run because stage 5 is pure structural — preview
    # equals real output.
    if open_threads_file:
        try:
            from daemon.open_threads import _card_timestamp
            entries: list[dict] = []
            for cid, members in grouped.items():
                cluster_name = cluster_names.get(cid) if cluster_names else None
                for card in members:
                    if not card.get("_open_thread"):
                        continue
                    questions = card.get("_open_thread_questions") or []
                    if not questions:
                        continue
                    backfill = card.get("_backfill") or {}
                    entries.append({
                        "card_path": card.get("path", ""),
                        "topic_cluster": cluster_name or f"cluster_{cid}",
                        "open_questions": questions,
                        "last_touched": _card_timestamp(card),
                        "context_summary": (
                            backfill.get("claim_summary") or ""
                        ),
                    })

            payload = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "vault_root": str(vault_root),
                "dry_run": dry_run,
                "open_threads": entries,
            }
            open_threads_file.parent.mkdir(parents=True, exist_ok=True)
            open_threads_file.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            result.errors.append(f"open_threads state file write failed: {exc}")

    return result


# ---------- CLI ----------

def _format_result(result: PassResult) -> str:
    """Pretty-print PassResult for the CLI."""
    lines = [
        "Reflection Pass result",
        f"  started:  {result.started_at}",
        f"  finished: {result.finished_at}",
        f"  dry_run:  {result.dry_run}",
        "",
        f"  cards scanned:                {result.cards_scanned}",
        f"  cards reflectable:            {result.cards_reflectable}",
        f"  cards excluded (logs/drafts): {result.cards_excluded}",
        f"  cards with position_signal:   {result.cards_with_position_signal}",
        f"  cards clustered:              {result.cards_clustered}",
        f"  clusters formed:              {result.clusters_count}",
        f"  cluster names resolved:       {result.cluster_names_resolved}",
        f"  back-fills completed:         {result.backfill_completed}",
        f"  open threads detected:        {result.open_threads_detected}",
        f"  contradictions detected:      {result.contradictions_detected}",
        f"  drift phases computed:        {result.drift_phases_computed}",
        f"  cards updated:                {result.cards_updated}",
        "",
        "  stages completed:",
    ]
    for stage in result.stages_completed:
        lines.append(f"    - {stage}")
    if result.stages_skipped:
        lines.append("  stages skipped (stubs):")
        for stage in result.stages_skipped:
            lines.append(f"    - {stage}")
    if result.errors:
        lines.append("  errors:")
        for err in result.errors:
            lines.append(f"    ! {err}")
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m daemon.reflection_pass",
        description=(
            "Run one Reflection Pass over the vault. Aggregates "
            "card-level position signals into the cross-card metadata "
            "the Reflection Layer's MCP tools query. See "
            "docs/POSITION_METADATA_SCHEMA.md for full design."
        ),
    )
    parser.add_argument(
        "--vault", type=str, default=None,
        help="Vault root path (defaults to $THROUGHLINE_VAULT_ROOT "
             "or ~/ObsidianVault).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Do not write back to cards. Stages 1-7 run; "
             "stage 8 is skipped. Use to validate schema "
             "compatibility before committing to real edits.",
    )
    parser.add_argument(
        "--high-threshold", type=float, default=0.70,
        help="Cosine similarity threshold for same-topic decisions "
             "(default 0.70 per gate experiment best score).",
    )
    parser.add_argument(
        "--low-threshold", type=float, default=0.55,
    )
    parser.add_argument(
        "--state-file", type=str, default=None,
        help="Path to pass watermark file. Defaults to "
             "$THROUGHLINE_STATE_DIR/reflection_pass_state.json.",
    )
    parser.add_argument(
        "--enable-llm-naming", action="store_true",
        help="Stage 3: call LLM to assign canonical snake_case "
             "names to each cluster. Requires OPENROUTER_API_KEY "
             "(or compatible env). Without this flag, stage 3 is "
             "skipped and clusters remain numeric ids.",
    )
    parser.add_argument(
        "--cluster-names-file", type=str, default=None,
        help="Path to persist cluster_signature -> name cache. "
             "Defaults to "
             "$THROUGHLINE_STATE_DIR/reflection_cluster_names.json.",
    )
    parser.add_argument(
        "--enable-llm-backfill", action="store_true",
        help="Stage 4: Path A back-fill — call LLM to extract "
             "claim_summary + open_questions for legacy cards "
             "(those without position_signal in frontmatter). "
             "Requires OPENROUTER_API_KEY (or OPENAI_API_KEY). "
             "Cache file dedupes by mtime so re-runs are cheap.",
    )
    parser.add_argument(
        "--backfill-state-file", type=str, default=None,
        help="Path to persist card_path|mtime -> essence cache. "
             "Defaults to "
             "$THROUGHLINE_STATE_DIR/reflection_backfill_state.json.",
    )
    parser.add_argument(
        "--open-threads-file", type=str, default=None,
        help="Path to persist stage 5 results (cards with "
             "unresolved open questions) for the find_open_threads "
             "MCP tool to read. Defaults to "
             "$THROUGHLINE_STATE_DIR/reflection_open_threads.json. "
             "Written on every pass (including --dry-run) since "
             "stage 5 is pure structural.",
    )
    args = parser.parse_args(argv)

    vault = Path(args.vault).resolve() if args.vault else None
    state = Path(args.state_file).resolve() if args.state_file else None
    cluster_names_path = (
        Path(args.cluster_names_file).resolve() if args.cluster_names_file
        else default_cluster_names_file()
    )

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    namer: Optional[ClusterNamer] = None
    if args.enable_llm_naming:
        try:
            from mcp_server.llm_namer import name_cluster
            namer = name_cluster
        except ImportError as exc:
            print(
                f"--enable-llm-naming requires mcp_server.llm_namer "
                f"({exc})",
                file=sys.stderr,
            )
            return 2

    extractor: Optional[EssenceExtractor] = None
    backfill_state_path: Optional[Path] = None
    if args.enable_llm_backfill:
        try:
            from mcp_server.llm_extractor import extract_card_essence
            extractor = extract_card_essence
        except ImportError as exc:
            print(
                f"--enable-llm-backfill requires "
                f"mcp_server.llm_extractor ({exc})",
                file=sys.stderr,
            )
            return 2
        backfill_state_path = (
            Path(args.backfill_state_file).resolve()
            if args.backfill_state_file
            else default_backfill_state_file()
        )

    open_threads_path = (
        Path(args.open_threads_file).resolve()
        if args.open_threads_file
        else default_open_threads_file()
    )

    result = run_pass(
        vault_root=vault,
        dry_run=args.dry_run,
        high_threshold=args.high_threshold,
        low_threshold=args.low_threshold,
        state_file=state,
        namer=namer,
        cluster_names_file=cluster_names_path if args.enable_llm_naming else None,
        extractor=extractor,
        backfill_state_file=backfill_state_path,
        open_threads_file=open_threads_path,
    )

    print(_format_result(result))
    return 0 if not result.errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
