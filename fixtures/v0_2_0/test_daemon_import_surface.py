"""Regression tests for the daemon's import surface.

Background: before this test, `daemon/refine_daemon.py` imported
JD_ROOT_MAP / JD_LEAF_WHITELIST / normalize_route_path /
is_valid_leaf_route from `daemon.taxonomy`, none of which were
exported. A user doing a fresh `git clone` could not start the
daemon — it ImportError'd at module load.

These tests pin the contract so the import surface can't silently
drift again. Every alias must be present AND functional.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from daemon import taxonomy as tax


class TestTaxonomyAliases:
    def test_jd_root_map_membership(self):
        """refine_daemon.py uses `if dom in JD_ROOT_MAP:` where `dom`
        is a root name (e.g. '40_Cognition_PKM'). Must support that."""
        assert "40_Cognition_PKM" in tax.JD_ROOT_MAP
        assert "10_Tech_Infrastructure" in tax.JD_ROOT_MAP
        assert "99_Bogus_Root" not in tax.JD_ROOT_MAP

    def test_jd_leaf_whitelist_iterable(self):
        """Iteration + startswith used at the caller."""
        leaves = list(tax.JD_LEAF_WHITELIST)
        assert len(leaves) > 0
        # Sample: every Tech leaf starts with '10_Tech_Infrastructure/'.
        tech_leaves = [p for p in leaves
                        if p.startswith("10_Tech_Infrastructure/")]
        assert len(tech_leaves) >= 3

    def test_normalize_route_path_callable(self):
        # Backslashes from Windows paths must normalise to forward.
        out = tax.normalize_route_path("10_Tech\\foo\\bar")
        assert out == "10_Tech/foo/bar"

    def test_is_valid_leaf_route_accepts_whitelisted(self):
        # Pick any entry from the whitelist; the checker must return True.
        sample = next(iter(tax.JD_LEAF_WHITELIST))
        assert tax.is_valid_leaf_route(sample) is True

    def test_is_valid_leaf_route_rejects_garbage(self):
        assert tax.is_valid_leaf_route("99_Nonsense/foo") is False


class TestDaemonImportable:
    """The critical acceptance test: `daemon.refine_daemon` must
    import cleanly on a fresh clone. If this regresses, the daemon
    won't even start and the user sees a wall-of-text traceback
    instead of a running watcher."""

    def test_refine_daemon_imports(self):
        # Force a fresh import even if a previous test grabbed it.
        for key in list(sys.modules.keys()):
            if key.startswith("daemon.refine_daemon"):
                del sys.modules[key]
        import daemon.refine_daemon as rd
        # Spot-check a few symbols exist.
        assert hasattr(rd, "RefinedResult")
        assert hasattr(rd, "process_raw_file")
        assert hasattr(rd, "record_taxonomy_observation")
