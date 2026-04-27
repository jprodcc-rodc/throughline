"""Tests for daemon.reflection_explain — single-card diagnostic."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
    return tmp_path


def _write(state_dir: Path, name: str, payload: dict):
    (state_dir / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ---------- core helpers ----------

class TestPathNormalization:
    def test_absolute_path_passes_through(self, tmp_path):
        from daemon.reflection_explain import _normalize_card_path

        p = tmp_path / "a.md"
        p.write_text("body", encoding="utf-8")
        result = _normalize_card_path(str(p))
        assert result == str(p)

    def test_nonexistent_passes_through(self):
        from daemon.reflection_explain import _normalize_card_path

        # Doesn't crash; returns str of the path even if missing
        result = _normalize_card_path("/totally/missing/x.md")
        assert "x.md" in result


class TestFindInPositions:
    def test_finds_by_full_path(self):
        from daemon.reflection_explain import _find_in_positions

        positions = {
            "clusters": [
                {
                    "cluster_id": "0",
                    "topic_cluster": "topic_x",
                    "size": 2,
                    "cards": [
                        {"card_path": "/a/b/card.md", "stance": "X"},
                        {"card_path": "/c/d/other.md", "stance": "Y"},
                    ],
                },
            ],
        }
        c, card = _find_in_positions("/a/b/card.md", positions)
        assert c is not None
        assert card["stance"] == "X"

    def test_finds_by_filename_suffix(self):
        from daemon.reflection_explain import _find_in_positions

        positions = {
            "clusters": [{
                "cluster_id": "0",
                "topic_cluster": "x",
                "size": 1,
                "cards": [{"card_path": "/abs/path/to/card.md", "stance": "S"}],
            }],
        }
        c, card = _find_in_positions("card.md", positions)
        assert c is not None
        assert card["stance"] == "S"

    def test_returns_none_when_absent(self):
        from daemon.reflection_explain import _find_in_positions

        positions = {"clusters": []}
        c, card = _find_in_positions("/x.md", positions)
        assert c is None
        assert card is None

    def test_handles_non_dict(self):
        from daemon.reflection_explain import _find_in_positions

        c, card = _find_in_positions("/x.md", "not a dict")  # type: ignore[arg-type]
        assert c is None
        assert card is None


class TestFindOpenThreads:
    def test_match_by_path(self):
        from daemon.reflection_explain import _find_open_threads_entry

        ot = {
            "open_threads": [
                {"card_path": "/a/b.md", "open_questions": ["q?"]},
            ],
        }
        result = _find_open_threads_entry("/a/b.md", ot)
        assert result is not None

    def test_no_match(self):
        from daemon.reflection_explain import _find_open_threads_entry

        ot = {"open_threads": []}
        assert _find_open_threads_entry("/x.md", ot) is None


class TestFindBackfill:
    def test_match_via_path_part(self):
        from daemon.reflection_explain import _find_in_backfill

        backfill = {
            "/a/b.md|123456": {"claim_summary": "S", "open_questions": []},
        }
        result = _find_in_backfill("/a/b.md", backfill)
        assert result is not None
        assert result["claim_summary"] == "S"

    def test_filename_suffix_match(self):
        from daemon.reflection_explain import _find_in_backfill

        backfill = {
            "/abs/path/card.md|999": {"claim_summary": "S", "open_questions": []},
        }
        result = _find_in_backfill("card.md", backfill)
        assert result is not None


# ---------- explain() integration ----------

class TestExplain:
    def test_no_state_files_doesnt_crash(self, state_dir):
        from daemon.reflection_explain import explain

        report = explain("/any/path/x.md")
        # Should produce a report mentioning the file presence + each
        # state file as missing
        assert "Reflection diagnostic" in report
        assert "✗" in report

    def test_card_in_positions_renders_cluster_info(self, state_dir):
        from daemon.reflection_explain import explain

        _write(state_dir, "reflection_positions.json", {
            "clusters": [{
                "cluster_id": "5",
                "topic_cluster": "pricing_strategy",
                "size": 2,
                "cards": [
                    {
                        "card_path": "/a/test.md",
                        "title": "Test",
                        "stance": "Use X",
                        "reasoning": ["r1"],
                        "open_questions": ["q?"],
                        "date": "2026-01-01",
                        "is_open_thread": False,
                        "is_backfilled": True,
                    },
                    {
                        "card_path": "/a/sister.md",
                        "title": "Sister",
                        "stance": None,
                        "reasoning": [],
                        "open_questions": [],
                        "date": "2026-02-01",
                        "is_open_thread": False,
                        "is_backfilled": False,
                    },
                ],
            }],
        })
        report = explain("/a/test.md")
        assert "cluster_id: 5" in report
        assert "pricing_strategy" in report
        assert "Use X" in report
        assert "Sister" in report  # sister card listed

    def test_open_thread_card_marked(self, state_dir):
        from daemon.reflection_explain import explain

        _write(state_dir, "reflection_open_threads.json", {
            "open_threads": [
                {
                    "card_path": "/a/test.md",
                    "topic_cluster": "topic_x",
                    "open_questions": ["q1?", "q2?"],
                    "last_touched": "2026-01-01",
                    "context_summary": "x",
                },
            ],
        })
        report = explain("/a/test.md")
        assert "✓ flagged as open-thread" in report
        assert "q1?" in report

    def test_writeback_preview_renders(self, state_dir):
        from daemon.reflection_explain import explain

        _write(state_dir, "reflection_writeback_preview.json", {
            "diffs": [
                {
                    "card_path": "/a/test.md",
                    "additions": {
                        "position_signal": {
                            "topic_cluster": "x",
                            "stance": "S",
                            "reasoning": ["r1"],
                        },
                        "open_questions": ["q1?"],
                        "reflection": {"status": "open_thread"},
                    },
                    "skipped_fields": [],
                },
            ],
        })
        report = explain("/a/test.md")
        assert "position_signal" in report
        assert "open_questions" in report
        assert "open_thread" in report

    def test_backfill_cached_renders(self, state_dir):
        from daemon.reflection_explain import explain

        _write(state_dir, "reflection_backfill_state.json", {
            "/a/test.md|999": {
                "claim_summary": "Cached stance",
                "open_questions": ["q?"],
            },
        })
        report = explain("/a/test.md")
        assert "Cached stance" in report

    def test_card_not_in_state_files(self, state_dir):
        """Card exists on disk but no state files have it (e.g.,
        Reflection Pass hasn't run, OR card was filtered)."""
        from daemon.reflection_explain import explain

        # Empty positions — card not there
        _write(state_dir, "reflection_positions.json", {"clusters": []})
        report = explain("/x/y/z.md")
        assert "card not found in positions" in report


# ---------- CLI ----------

class TestExplainCLI:
    def test_explain_short_circuits_pass_run(self, state_dir, capsys):
        from daemon.reflection_pass import main

        rc = main(["--explain", "/some/card.md"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Reflection diagnostic" in out
