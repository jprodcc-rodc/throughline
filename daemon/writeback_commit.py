"""Real frontmatter writeback for stage 8 — hybrid approach.

Per the user's architectural decision (2026-04-28+1):

- ``position_signal`` and ``open_questions`` (ADD-once fields) →
  surgical text append to existing frontmatter, NEVER touching
  bytes already there. No PyYAML round-trip = no formatting drift
  on user's existing keys.

- ``reflection.*`` (daemon-refreshable fields: status, last_pass) →
  sidecar JSON file ``<card_dir>/.<card_name>.reflection.json``.
  Daemon refreshes on every pass without ever modifying the
  frontmatter block. Survives YAML edits in the card and never
  collides with hand-written reflection annotations the user
  might add.

- Atomic write: ``tempfile.NamedTemporaryFile`` + ``os.replace``
  inside the same dir as the card (so cross-device renames don't
  fail).

- Backup: before any modification, write
  ``<card_dir>/.<card_name>.backup-<unix_timestamp>``. User can
  ``rm`` later to clean up; daemon never auto-deletes (paranoid by
  design).

- Idempotency: if all ``additions`` keys already exist in the
  frontmatter (via the parsed dict), skip surgical append. If the
  sidecar already has the same content, skip rewrite.

This module is the **highest-blast-radius** code in the daemon —
mutates user vault files. Default writeback path
(``--commit-writeback`` flag) is OFF.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


_FENCE = "---"


def _find_frontmatter_bounds(text: str) -> Optional[tuple[int, int]]:
    """Return (start_of_yaml, end_of_yaml) or None if no
    well-formed frontmatter."""
    if not text.startswith(_FENCE + "\n"):
        return None
    end_marker = "\n" + _FENCE + "\n"
    end_idx = text.find(end_marker, len(_FENCE) + 1)
    if end_idx == -1:
        return None
    return (len(_FENCE) + 1, end_idx)


def _parse_existing_keys(yaml_block: str) -> set[str]:
    """Return the set of TOP-LEVEL keys in the YAML block. Used for
    idempotency: surgical append skips keys already present."""
    try:
        import yaml  # type: ignore[import-untyped]
        parsed = yaml.safe_load(yaml_block)
    except Exception:
        return set()
    if not isinstance(parsed, dict):
        return set()
    return set(parsed.keys())


def _yaml_dump_value(key: str, value: Any) -> str:
    """Render a single (key, value) pair as YAML text suitable for
    appending. Uses PyYAML's safe_dump but strips the trailing
    newline + leading document marker.

    Falls back to a manual dump for the simple cases (string, list)
    if PyYAML isn't available.
    """
    try:
        import yaml  # type: ignore[import-untyped]
        # default_flow_style=False forces block style for readability
        text = yaml.safe_dump(
            {key: value},
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        # safe_dump always ends with newline; we want it
        return text
    except ImportError:  # pragma: no cover
        # Naive fallback: only handles strings and lists of strings
        if isinstance(value, str):
            return f"{key}: {json.dumps(value)}\n"
        if isinstance(value, list):
            lines = [f"{key}:"]
            for v in value:
                lines.append(f"  - {json.dumps(v)}")
            return "\n".join(lines) + "\n"
        return f"{key}: {json.dumps(value)}\n"


def surgical_yaml_append(card_text: str, additions: dict[str, Any]) -> tuple[str, list[str]]:
    """Append YAML key-value pairs at the end of the frontmatter
    block in ``card_text``. Existing fm content untouched.

    Returns ``(new_text, added_keys)``. ``added_keys`` is the
    subset of ``additions`` actually appended (keys already present
    are skipped for idempotency).

    If the card has no frontmatter, prepends a fresh fm block.
    """
    bounds = _find_frontmatter_bounds(card_text)

    if bounds is None:
        # Card has no frontmatter — synthesize one
        fm_text = ""
        for k, v in additions.items():
            fm_text += _yaml_dump_value(k, v)
        return f"---\n{fm_text}---\n{card_text}", list(additions.keys())

    fm_start, fm_end = bounds
    fm_yaml = card_text[fm_start:fm_end]
    existing_keys = _parse_existing_keys(fm_yaml)

    to_add = {k: v for k, v in additions.items() if k not in existing_keys}
    if not to_add:
        return card_text, []

    appended = ""
    for k, v in to_add.items():
        appended += _yaml_dump_value(k, v)

    # Make sure the existing fm ends in a newline before we tack on
    # new content; if it doesn't, prepend one.
    fm_block = fm_yaml
    if not fm_block.endswith("\n"):
        fm_block = fm_block + "\n"

    new_fm = fm_block + appended
    new_text = (
        card_text[:fm_start] + new_fm + card_text[fm_end:]
    )
    return new_text, list(to_add.keys())


def sidecar_path_for(card_path: Path) -> Path:
    """Return the path of the reflection sidecar file for a given
    card. Lives in the same dir as the card, prefixed with
    ``.<filename>`` so it's hidden by default in shells / file
    managers but co-located for ``rg``-friendliness."""
    return card_path.parent / f".{card_path.name}.reflection.json"


def write_sidecar(card_path: Path, reflection: dict[str, Any]) -> tuple[bool, Optional[Path]]:
    """Write reflection fields to the sidecar JSON. Returns
    ``(was_changed, sidecar_path)``. ``was_changed`` False when
    the sidecar already has the same content (idempotency)."""
    sidecar = sidecar_path_for(card_path)
    new_content = json.dumps(reflection, indent=2, ensure_ascii=False, sort_keys=True)
    if sidecar.exists():
        try:
            existing = sidecar.read_text(encoding="utf-8")
            if existing.strip() == new_content.strip():
                return False, sidecar
        except OSError:
            pass
    _atomic_write(sidecar, new_content)
    return True, sidecar


def _atomic_write(target: Path, content: str) -> None:
    """Write ``content`` to ``target`` via NamedTemporaryFile +
    os.replace in the same directory. Same-dir is critical on
    Windows + cross-device situations where rename across mounts
    fails."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(target.parent),
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        os.replace(tmp_name, target)
    except Exception:
        # Best-effort cleanup
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def write_backup(card_path: Path) -> Optional[Path]:
    """Write a timestamped backup of the card before mutation.
    Returns the backup path, or None if the card couldn't be read."""
    if not card_path.exists():
        return None
    try:
        content = card_path.read_text(encoding="utf-8")
    except OSError:
        return None
    ts = int(datetime.now().timestamp())
    backup = card_path.parent / f".{card_path.name}.backup-{ts}"
    try:
        _atomic_write(backup, content)
    except OSError:
        return None
    return backup


def commit_card_writeback(
    card_path: Path,
    additions: dict[str, Any],
    *,
    dry_run: bool = False,
    backup: bool = True,
) -> dict[str, Any]:
    """Apply writeback for a single card.

    Args:
        card_path: absolute path to the card .md file.
        additions: dict from stage 8's compute_writeback_diff —
            shape ``{position_signal?, open_questions?, reflection?}``.
        dry_run: when True, skip all I/O and return ``{would_change}``
            indicating what *would* happen.
        backup: when True, write a timestamped backup of the card
            BEFORE any mutation. Strongly recommended.

    Returns:
        dict with keys:
        - ``card_path``: str (echo of input)
        - ``frontmatter_keys_added``: list[str]
        - ``sidecar_changed``: bool
        - ``backup_path``: str or None
        - ``error``: str or None (None on success)
    """
    out: dict[str, Any] = {
        "card_path": str(card_path),
        "frontmatter_keys_added": [],
        "sidecar_changed": False,
        "backup_path": None,
        "error": None,
    }

    if not card_path.exists():
        out["error"] = f"card file does not exist: {card_path}"
        return out

    # Split additions into frontmatter (surgical-append) vs reflection
    # (sidecar). Per architectural decision:
    #   - position_signal, open_questions → frontmatter
    #   - reflection → sidecar (daemon-refreshable)
    fm_additions: dict[str, Any] = {}
    sidecar_payload: Optional[dict[str, Any]] = None

    if "position_signal" in additions:
        fm_additions["position_signal"] = additions["position_signal"]
    if "open_questions" in additions:
        fm_additions["open_questions"] = additions["open_questions"]
    if "reflection" in additions:
        sidecar_payload = additions["reflection"]

    if dry_run:
        out["would_change"] = True
        out["frontmatter_keys_added"] = list(fm_additions.keys())
        out["sidecar_changed"] = sidecar_payload is not None
        return out

    # Backup BEFORE any modification
    if backup and fm_additions:
        out["backup_path"] = (
            str(write_backup(card_path)) if write_backup(card_path) else None
        )

    # Surgical frontmatter append
    if fm_additions:
        try:
            text = card_path.read_text(encoding="utf-8")
            new_text, added_keys = surgical_yaml_append(text, fm_additions)
            if added_keys:
                _atomic_write(card_path, new_text)
                out["frontmatter_keys_added"] = added_keys
        except OSError as exc:
            out["error"] = f"frontmatter write failed: {exc}"
            return out

    # Sidecar reflection write (always refresh; daemon-managed metadata)
    if sidecar_payload is not None:
        try:
            changed, _ = write_sidecar(card_path, sidecar_payload)
            out["sidecar_changed"] = changed
        except OSError as exc:
            out["error"] = f"sidecar write failed: {exc}"
            return out

    return out
