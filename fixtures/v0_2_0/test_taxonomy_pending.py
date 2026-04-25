"""U27.5 — `taxonomy.pending_candidates_count()` + the
`check_taxonomy_pending` doctor check.

The pieces being tested:
- A non-interactive helper that returns the number of growth
  candidates currently waiting for review.
- A doctor check that warns when the number is > 0 with a
  pointer to `taxonomy review`, ok when 0.

Together these surface a U27 work item the user would otherwise
forget about (the growth loop is invisible until they think to
run the CLI).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


BASE = datetime(2026, 4, 20, 12, 0, 0, tzinfo=timezone.utc)


def _mkobs(card_id, title, primary_x, proposed, ts):
    return {
        "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "card_id": card_id,
        "title": title,
        "primary_x": primary_x,
        "proposed_x_ideal": proposed,
    }


def _write_obs_log(state_dir: Path, rows):
    state_dir.mkdir(parents=True, exist_ok=True)
    p = state_dir / "taxonomy_observations.jsonl"
    p.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    return p


def _drift_rows(tag: str, n: int = 8, span_days: int = 7):
    """Above-threshold drift observations for one tag."""
    rows = []
    for i in range(n):
        day_offset = (i * span_days) / max(1, n - 1)
        rows.append(_mkobs(
            card_id=f"{tag}-{i}",
            title=f"Drift card {i}",
            primary_x="Misc",
            proposed=tag,
            ts=BASE + timedelta(days=day_offset),
        ))
    return rows


# =========================================================
# pending_candidates_count
# =========================================================

class TestPendingCandidatesCount:
    def test_no_observation_log_returns_zero(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        from throughline_cli import taxonomy as tx
        # Reload the module to re-resolve the path lazily? Not needed —
        # all path helpers re-read env on each call.
        assert tx.pending_candidates_count() == 0

    def test_below_threshold_returns_zero(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        # 3 rows < the 5-card minimum
        _write_obs_log(tmp_path / "state", _drift_rows("AI/Agent", n=3))
        from throughline_cli import taxonomy as tx
        assert tx.pending_candidates_count() == 0

    def test_above_threshold_returns_count(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        _write_obs_log(tmp_path / "state",
                        _drift_rows("AI/Agent", n=8, span_days=10))
        from throughline_cli import taxonomy as tx
        assert tx.pending_candidates_count() == 1

    def test_multiple_clusters_counted_separately(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        rows = (_drift_rows("AI/Agent", n=8, span_days=10)
                + _drift_rows("Climbing", n=8, span_days=10))
        _write_obs_log(tmp_path / "state", rows)
        from throughline_cli import taxonomy as tx
        assert tx.pending_candidates_count() == 2

    def test_helper_never_raises(self, tmp_path, monkeypatch):
        """Whatever happens (broken log, missing config, etc.), the
        helper returns 0 — the doctor check + Filter callers must be
        able to call it without try/except."""
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        # Write garbage that load_observations will silently skip.
        (tmp_path / "state").mkdir(parents=True, exist_ok=True)
        (tmp_path / "state" / "taxonomy_observations.jsonl").write_text(
            "not json at all\nstill not json\n", encoding="utf-8")
        from throughline_cli import taxonomy as tx
        assert tx.pending_candidates_count() == 0


# =========================================================
# check_taxonomy_pending doctor check
# =========================================================

class TestCheckTaxonomyPending:
    def test_zero_pending_is_ok(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        from throughline_cli import doctor
        r = doctor.check_taxonomy_pending()
        assert r.status == "ok"
        assert "no growth candidates" in r.detail.lower()

    def test_pending_warns_with_count_and_remediation(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        _write_obs_log(tmp_path / "state",
                        _drift_rows("AI/Agent", n=8, span_days=10))
        from throughline_cli import doctor
        r = doctor.check_taxonomy_pending()
        assert r.status == "warn"
        assert "1 taxonomy candidate" in r.detail
        assert "taxonomy review" in r.fix

    def test_pending_pluralises(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        rows = (_drift_rows("AI/Agent", n=8, span_days=10)
                + _drift_rows("Climbing", n=8, span_days=10))
        _write_obs_log(tmp_path / "state", rows)
        from throughline_cli import doctor
        r = doctor.check_taxonomy_pending()
        assert r.status == "warn"
        assert "2 taxonomy candidates" in r.detail  # plural

    def test_check_is_in_default_checks(self):
        """`check_taxonomy_pending` must be wired into DEFAULT_CHECKS
        so it fires on every doctor run — not just when called
        directly."""
        from throughline_cli import doctor
        names = [c.__name__ for c in doctor.DEFAULT_CHECKS]
        assert "check_taxonomy_pending" in names


# =========================================================
# U27.7 — zero-usage leaf detection
# =========================================================

def _write_card(vault: Path, primary_x: str, title: str = "T",
                 body: str = None) -> Path:
    """Write a refined-card-shaped Markdown file the vault scanner
    will recognise (frontmatter + ≥100 bytes of body)."""
    p = vault / f"{primary_x.replace('/', '_')}_{title}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = body or (
        "# Scene & Pain Point\nReal scenario goes here.\n\n"
        "# Core Knowledge & First Principles\nUseful structured content.\n\n"
        "# Detailed Execution Plan\nStep one. Step two. Step three.\n\n"
        "# Pitfalls & Boundaries\nWatch out for X.\n\n"
        "# Insights & Mental Models\nFramework here.\n\n"
        "# Length Summary\nShort recap of the above sections.\n"
    )
    p.write_text(
        "---\n"
        f"title: \"{title}\"\n"
        f"primary_x: \"{primary_x}\"\n"
        "form_y: \"y/Reference\"\n"
        "z_axis: \"z/Node\"\n"
        "---\n\n"
        + body,
        encoding="utf-8",
    )
    return p


class TestDetectZeroUsageLeaves:
    def test_no_vault_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT",
                            str(tmp_path / "missing_vault"))
        from throughline_cli import taxonomy as tx
        out = tx.detect_zero_usage_leaves(valid_x=["A", "B", "C"])
        assert out == []

    def test_all_leaves_used_returns_empty(self, tmp_path, monkeypatch):
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        _write_card(vault, "AI/LLM", "card1")
        _write_card(vault, "Tech/PKM", "card2")
        from throughline_cli import taxonomy as tx
        out = tx.detect_zero_usage_leaves(valid_x=["AI/LLM", "Tech/PKM"])
        assert out == []

    def test_some_leaves_unused(self, tmp_path, monkeypatch):
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        _write_card(vault, "AI/LLM", "card1")
        # `Tech/PKM` and `Misc` have no cards.
        from throughline_cli import taxonomy as tx
        out = tx.detect_zero_usage_leaves(
            valid_x=["AI/LLM", "Tech/PKM", "Misc"])
        assert out == ["Misc", "Tech/PKM"]  # alphabetical

    def test_empty_valid_x_returns_empty(self, tmp_path, monkeypatch):
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        from throughline_cli import taxonomy as tx
        assert tx.detect_zero_usage_leaves(valid_x=[]) == []


class TestCmdZeroUsage:
    def test_no_unused_message(self, tmp_path, monkeypatch, capsys):
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        _write_card(vault, "AI/LLM", "c1")
        from throughline_cli import taxonomy as tx
        captured: list = []
        rc = tx.cmd_zero_usage(out=captured.append)
        # Patch valid_x via monkeypatch on load_valid_x_from_config
        # so the test doesn't depend on the active taxonomy file.
        # Re-run with explicit valid_x via monkeypatch shim.
        monkeypatch.setattr(tx, "load_valid_x_from_config",
                              lambda: ["AI/LLM"])
        captured = []
        rc = tx.cmd_zero_usage(out=captured.append)
        assert rc == 0
        joined = "\n".join(captured)
        assert "All 1" in joined or "Nothing to deprecate" in joined

    def test_unused_listed(self, tmp_path, monkeypatch):
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        _write_card(vault, "AI/LLM", "c1")
        from throughline_cli import taxonomy as tx
        monkeypatch.setattr(tx, "load_valid_x_from_config",
                              lambda: ["AI/LLM", "Tech/PKM", "Misc"])
        captured: list = []
        rc = tx.cmd_zero_usage(out=captured.append)
        assert rc == 0
        joined = "\n".join(captured)
        assert "Tech/PKM" in joined
        assert "Misc" in joined
        assert "deprecation" in joined.lower()

    def test_empty_valid_x_message(self, tmp_path, monkeypatch):
        from throughline_cli import taxonomy as tx
        monkeypatch.setattr(tx, "load_valid_x_from_config",
                              lambda: [])
        captured: list = []
        rc = tx.cmd_zero_usage(out=captured.append)
        assert rc == 0
        assert "empty" in "\n".join(captured).lower()

    def test_missing_vault_distinct_message(self, tmp_path, monkeypatch):
        """Regression: a missing vault must NOT print 'all leaves
        have at least one card' — that's a misleading false positive
        ('your vault is fine!') when actually the vault doesn't exist.
        Surface the vault-missing condition explicitly."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT",
                            str(tmp_path / "does_not_exist"))
        from throughline_cli import taxonomy as tx
        monkeypatch.setattr(tx, "load_valid_x_from_config",
                              lambda: ["AI/LLM", "Tech/PKM"])
        captured: list = []
        rc = tx.cmd_zero_usage(out=captured.append)
        assert rc == 0
        joined = "\n".join(captured)
        assert "Vault not found" in joined
        assert "All" not in joined  # not the false-positive message

    def test_dispatcher_routes_zero_usage(self, tmp_path, monkeypatch, capsys):
        vault = tmp_path / "vault"
        vault.mkdir()
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(vault))
        from throughline_cli import taxonomy as tx
        monkeypatch.setattr(tx, "load_valid_x_from_config",
                              lambda: ["AI/LLM"])
        rc = tx.main(["zero-usage"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "AI/LLM" in out or "deprecate" in out.lower()
