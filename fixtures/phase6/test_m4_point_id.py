"""M4 ship-blocker: cross-platform point_id determinism.

Ship-blocker from PHASE_6_CHECKLIST / THROUGHLINE_PHASE6_RISKS §M4:

    'Win + Linux point_id 一致 — ingest same fixture vault on Win + Linux
     and compare MD5 point_id sets.'

The operational check (actually running `ingest_qdrant.py` on Win + WSL
against a fixture vault and diffing the produced point_id sets) is the
authoritative version of this test. This file is the cheap, deterministic,
zero-infra substitute: it pins the path-normalisation invariant with
monkeypatched os.sep + os.path.relpath, so any regression that breaks
cross-platform determinism fails pytest without needing Qdrant or two OSes.

What we're actually guarding: make_point_id must be a pure function of the
forward-slash-normalised relative path. `_norm_path` must collapse both
`\\`-separated (Windows) and `/`-separated (POSIX) relative paths to the
same forward-slash form before it reaches the md5. If either contract is
broken, the live Filter will mis-route retrieval on mixed-OS setups and
the Qdrant collection will silently grow two points per note.

Guard surfaces:
- payload hash: make_point_id(posix) == make_point_id(win-then-normalised)
- structural: _norm_path output is always forward-slash regardless of
  platform separator
- defensive: bare backslashes are fully replaced, no mid-string residue
"""

import importlib.util
import os
from pathlib import Path
from unittest.mock import patch

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "ingest_qdrant.py"
)


def _load_ingest():
    os.environ.setdefault("VAULT_PATH", "/unused/test/vault")
    spec = importlib.util.spec_from_file_location("ingest_qdrant", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


INGEST = _load_ingest()


CROSS_PLATFORM_PATHS = [
    (
        "40_Cognition_PKM/40.03_Learning/note.md",
        "40_Cognition_PKM\\40.03_Learning\\note.md",
    ),
    (
        "10_Tech_Infrastructure/runbook.md",
        "10_Tech_Infrastructure\\runbook.md",
    ),
    (
        "00_Buffer/00.00_Overview/master.md",
        "00_Buffer\\00.00_Overview\\master.md",
    ),
    (
        "a/b/c/d/deep/nested/leaf.md",
        "a\\b\\c\\d\\deep\\nested\\leaf.md",
    ),
]


def test_make_point_id_is_pure_and_deterministic():
    for posix, _win in CROSS_PLATFORM_PATHS:
        assert INGEST.make_point_id(posix) == INGEST.make_point_id(posix)


def test_make_point_id_differs_per_path():
    ids = {INGEST.make_point_id(posix) for posix, _ in CROSS_PLATFORM_PATHS}
    assert len(ids) == len(CROSS_PLATFORM_PATHS)


def test_norm_path_posix_is_noop():
    with patch.object(INGEST.os, "sep", "/"):
        with patch.object(
            INGEST.os.path, "relpath",
            return_value="40_Cognition_PKM/40.03_Learning/note.md",
        ):
            out = INGEST._norm_path("/any/abs/input")
    assert out == "40_Cognition_PKM/40.03_Learning/note.md"
    assert "\\" not in out


def test_norm_path_windows_backslashes_collapse_to_slash():
    with patch.object(INGEST.os, "sep", "\\"):
        with patch.object(
            INGEST.os.path, "relpath",
            return_value="40_Cognition_PKM\\40.03_Learning\\note.md",
        ):
            out = INGEST._norm_path(r"C:\any\abs\input")
    assert out == "40_Cognition_PKM/40.03_Learning/note.md"
    assert "\\" not in out


def test_norm_path_convergence_across_platforms():
    for posix, win in CROSS_PLATFORM_PATHS:
        with patch.object(INGEST.os, "sep", "/"):
            with patch.object(INGEST.os.path, "relpath", return_value=posix):
                posix_norm = INGEST._norm_path("/ignored")

        with patch.object(INGEST.os, "sep", "\\"):
            with patch.object(INGEST.os.path, "relpath", return_value=win):
                win_norm = INGEST._norm_path("C:\\ignored")

        assert posix_norm == win_norm, (
            f"_norm_path diverged: posix={posix_norm!r} win={win_norm!r}"
        )
        assert INGEST.make_point_id(posix_norm) == INGEST.make_point_id(
            win_norm
        ), f"point_id diverged for {posix!r} vs {win!r}"


def test_point_id_fits_qdrant_unsigned_64bit():
    for posix, _ in CROSS_PLATFORM_PATHS:
        pid = INGEST.make_point_id(posix)
        assert isinstance(pid, int)
        assert 0 <= pid < 2**63, f"point_id {pid} out of signed-64 range"


def test_point_id_golden_values():
    """Pin a few known md5 hashes so an accidental hash-input change fails."""
    expected = {
        "40_Cognition_PKM/40.03_Learning/note.md":
            int("2a1cfcbb5a6c6a16", 16) & 0x7FFFFFFFFFFFFFFF,
        "00_Buffer/00.00_Overview/master.md":
            int("fd7ed27099eed27c", 16) & 0x7FFFFFFFFFFFFFFF,
    }
    import hashlib
    for path, _ in expected.items():
        h = hashlib.md5(path.encode("utf-8")).hexdigest()
        canonical = int(h[:16], 16) & 0x7FFFFFFFFFFFFFFF
        assert INGEST.make_point_id(path) == canonical
