"""Tests for U27.3 — daemon taxonomy observer.

Covers `daemon.taxonomy_observer.record_taxonomy_observation()`, the
append-only JSONL sink that the U27.4 CLI later reads to propose
taxonomy growth.

Contract:
- Every successful refine appends ONE JSON line to
  `state/taxonomy_observations.jsonl`.
- Format: `{ts, card_id, title, primary_x, proposed_x_ideal}`.
- Append-only: repeated calls never rewrite earlier lines.
- `proposed_x_ideal` falls back to `primary_x` when empty, so the
  record is always well-formed.
- Filesystem errors are swallowed (returns False) — observer must
  NEVER break the refine loop.

Observer is extracted into its own module (`daemon/taxonomy_observer.py`)
so these tests bypass the broader daemon import surface (watchdog,
Qdrant client, embedder — all irrelevant to the observer contract).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from daemon.taxonomy_observer import (
    record_taxonomy_observation,
    default_observations_file,
)


class TestRecordObservation:
    def test_writes_single_jsonl_line(self, tmp_path):
        log = tmp_path / "taxonomy_observations.jsonl"
        ok = record_taxonomy_observation(
            card_id="abc123",
            title="Building MCP agents",
            primary_x="Misc",
            proposed_x_ideal="AI/Agent",
            state_file=log,
        )
        assert ok is True
        lines = log.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        rec = json.loads(lines[0])
        assert rec["card_id"] == "abc123"
        assert rec["primary_x"] == "Misc"
        assert rec["proposed_x_ideal"] == "AI/Agent"
        assert rec["title"] == "Building MCP agents"
        # Timestamp format: ISO-ish, UTC, ends with Z (design doc spec).
        assert rec["ts"].endswith("Z")
        assert "T" in rec["ts"]

    def test_appends_not_overwrites(self, tmp_path):
        log = tmp_path / "taxonomy_observations.jsonl"
        for i, tag in enumerate(["tag1", "tag2", "tag3"]):
            record_taxonomy_observation(
                card_id=f"id{i+1}", title="t",
                primary_x="Misc", proposed_x_ideal=tag,
                state_file=log,
            )
        lines = log.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 3
        ids = [json.loads(line)["card_id"] for line in lines]
        assert ids == ["id1", "id2", "id3"]

    def test_parent_dir_auto_created(self, tmp_path):
        log = tmp_path / "nested" / "deep" / "taxonomy_observations.jsonl"
        ok = record_taxonomy_observation(
            card_id="x", title="t",
            primary_x="Tech", proposed_x_ideal="Tech",
            state_file=log,
        )
        assert ok is True
        assert log.exists()

    def test_empty_proposed_falls_back_to_primary(self, tmp_path):
        """When refiner emits no proposed_x_ideal, the observation record
        must still be well-formed — use primary_x so downstream detector
        treats the row as no-drift."""
        log = tmp_path / "taxonomy_observations.jsonl"
        ok = record_taxonomy_observation(
            card_id="id", title="t",
            primary_x="Tech", proposed_x_ideal="",
            state_file=log,
        )
        assert ok is True
        rec = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
        assert rec["primary_x"] == "Tech"
        assert rec["proposed_x_ideal"] == "Tech"

    def test_valid_jsonl_one_record_per_line(self, tmp_path):
        log = tmp_path / "taxonomy_observations.jsonl"
        for i in range(5):
            record_taxonomy_observation(
                card_id=f"id{i}", title=f"t{i}",
                primary_x="Misc", proposed_x_ideal=f"Tag/{i}",
                state_file=log,
            )
        for line in log.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            assert set(rec.keys()) == {
                "ts", "card_id", "title", "primary_x", "proposed_x_ideal",
            }

    def test_unicode_tags_preserved(self, tmp_path):
        """Non-ASCII tags (Chinese, emoji) must round-trip — users outside
        English will tag in their language."""
        log = tmp_path / "taxonomy_observations.jsonl"
        record_taxonomy_observation(
            card_id="id", title="t",
            primary_x="Misc", proposed_x_ideal="AI/代理",
            state_file=log,
        )
        rec = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
        assert rec["proposed_x_ideal"] == "AI/代理"

    def test_returns_false_on_fs_error(self, tmp_path):
        """If the filesystem rejects the write, the observer must log +
        return False rather than propagate the OSError. The refine loop
        cannot tolerate being broken by a taxonomy bookkeeping hiccup."""

        class _Exploder:
            """Mimics the Path shape the observer uses (parent.mkdir,
            .open) but raises on open()."""
            parent = tmp_path  # parent.mkdir is a real operation that works

            def open(self, *a, **k):
                raise OSError("simulated disk full")

        ok = record_taxonomy_observation(
            card_id="id", title="t",
            primary_x="Tech", proposed_x_ideal="Tech",
            state_file=_Exploder(),
        )
        assert ok is False

    def test_large_append_sequence_preserved(self, tmp_path):
        """Simulate a long daemon run: 100 appends must all survive and
        preserve order. Guards against any accidental truncate mode."""
        log = tmp_path / "taxonomy_observations.jsonl"
        for i in range(100):
            record_taxonomy_observation(
                card_id=f"c{i:03d}", title=f"t{i}",
                primary_x="Tech", proposed_x_ideal=f"Tech/{i % 7}",
                state_file=log,
            )
        lines = log.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 100
        assert json.loads(lines[0])["card_id"] == "c000"
        assert json.loads(lines[-1])["card_id"] == "c099"


class TestDefaultObservationsFile:
    """The default path must honour THROUGHLINE_STATE_DIR at call time
    (not import time) so tests and alternate installs can redirect it."""

    def test_uses_env_var(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        p = default_observations_file()
        assert p == tmp_path / "taxonomy_observations.jsonl"

    def test_default_is_home_runtime(self, monkeypatch):
        monkeypatch.delenv("THROUGHLINE_STATE_DIR", raising=False)
        p = default_observations_file()
        assert p.name == "taxonomy_observations.jsonl"
        assert "throughline_runtime" in str(p)

    def test_env_var_respected_after_import(self, tmp_path, monkeypatch):
        """Path resolution must not be frozen at import time — writing to
        the observer after setting the env var must land in the new
        location. Otherwise the wizard's state dir choice is ignored by a
        long-running daemon that imported first."""
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        record_taxonomy_observation(
            card_id="id", title="t",
            primary_x="Tech", proposed_x_ideal="Tech",
            # state_file=None -> uses default_observations_file()
        )
        out = tmp_path / "taxonomy_observations.jsonl"
        assert out.exists()
        assert len(out.read_text(encoding="utf-8").splitlines()) == 1
