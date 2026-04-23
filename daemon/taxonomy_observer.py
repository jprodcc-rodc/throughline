"""U27.3 · Taxonomy growth observer.

Append-only log of every successful refine's (primary_x, proposed_x_ideal)
pair. The daemon calls `record_taxonomy_observation()` once per card
written to disk; nothing else writes to this log, and the daemon never
reads it back. Scanning + clustering happens on-demand from the U27.4
CLI (`throughline_cli.taxonomy`).

Extracted from `daemon.refine_daemon` so the CLI and unit tests can
exercise the observer without pulling in the full daemon import surface
(watchdog, Qdrant client, embedder, etc.).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


_log = logging.getLogger(__name__)


def _default_state_dir() -> Path:
    return Path(
        os.getenv(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()


def default_observations_file() -> Path:
    """Resolve the default `state/taxonomy_observations.jsonl` path.

    Resolved lazily (not at import time) so tests can set
    `THROUGHLINE_STATE_DIR` via monkeypatch.setenv and have it take
    effect on the next call.
    """
    return _default_state_dir() / "taxonomy_observations.jsonl"


def record_taxonomy_observation(
    card_id: str,
    title: str,
    primary_x: str,
    proposed_x_ideal: str,
    state_file: Optional[Any] = None,
) -> bool:
    """Append one observation to the taxonomy log.

    The record shape matches the U27 design doc:

        {"ts": "...Z", "card_id": "...", "title": "...",
         "primary_x": "...", "proposed_x_ideal": "..."}

    `proposed_x_ideal` falls back to `primary_x` when empty, so older
    prompts / mocks that never surface the field still produce a
    well-formed no-drift row.

    Returns True on success, False on any OSError. Filesystem errors
    MUST be swallowed — the refine pipeline cannot tolerate being
    broken by a taxonomy bookkeeping hiccup.
    """
    path = state_file if state_file is not None else default_observations_file()
    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "card_id": card_id,
        "title": title,
        "primary_x": primary_x,
        "proposed_x_ideal": proposed_x_ideal or primary_x,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except OSError as e:
        try:
            _log.warning("taxonomy observation append failed: %s", e)
        except Exception:
            pass
        return False
