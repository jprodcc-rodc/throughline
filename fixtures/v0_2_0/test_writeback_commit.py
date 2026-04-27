"""Tests for daemon.writeback_commit — the real frontmatter
writeback path (hybrid surgical-append + sidecar JSON).

Tests run against tmp synthetic vault files; never touches real
user vault. Every test verifies idempotency / backup / format
preservation invariants.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest


# ---------- _find_frontmatter_bounds ----------

class TestFrontmatterBounds:
    def test_well_formed(self):
        from daemon.writeback_commit import _find_frontmatter_bounds

        text = "---\ntitle: T\n---\nbody\n"
        bounds = _find_frontmatter_bounds(text)
        assert bounds is not None
        start, end = bounds
        # Bounds = (after-opening-fence, before-closing-fence-newline)
        assert text[start:end].rstrip() == "title: T"

    def test_no_frontmatter(self):
        from daemon.writeback_commit import _find_frontmatter_bounds

        assert _find_frontmatter_bounds("# heading\nbody") is None

    def test_unclosed_frontmatter(self):
        from daemon.writeback_commit import _find_frontmatter_bounds

        assert _find_frontmatter_bounds("---\ntitle: T\nbody\n") is None


# ---------- surgical_yaml_append ----------

class TestSurgicalAppend:
    def test_appends_new_keys(self):
        from daemon.writeback_commit import surgical_yaml_append

        text = "---\ntitle: T\ntags:\n  - a\n  - b\n---\nbody\n"
        new_text, added = surgical_yaml_append(text, {
            "open_questions": ["q1?", "q2?"],
        })
        # Original content preserved exactly
        assert "title: T" in new_text
        assert "tags:" in new_text
        assert "- a" in new_text
        assert "- b" in new_text
        # New content appended
        assert "open_questions:" in new_text
        assert "q1?" in new_text
        assert added == ["open_questions"]

    def test_skips_existing_keys(self):
        """Idempotency: keys already in fm are not re-appended."""
        from daemon.writeback_commit import surgical_yaml_append

        text = "---\ntitle: T\nopen_questions:\n  - q1\n---\nbody"
        new_text, added = surgical_yaml_append(text, {
            "open_questions": ["new q?"],
        })
        # Nothing added
        assert added == []
        # Text identical
        assert new_text == text

    def test_partial_skip(self):
        """Mix of existing + new keys: only new appended."""
        from daemon.writeback_commit import surgical_yaml_append

        text = "---\ntitle: T\nopen_questions:\n  - q1\n---\nbody"
        new_text, added = surgical_yaml_append(text, {
            "open_questions": ["should be ignored"],
            "position_signal": {"stance": "X"},
        })
        assert added == ["position_signal"]
        assert "stance: X" in new_text
        # Original open_questions still has q1
        assert "q1" in new_text

    def test_no_frontmatter_synthesizes(self):
        """Card without fm → prepend a fresh fm block."""
        from daemon.writeback_commit import surgical_yaml_append

        text = "# heading\nbody content"
        new_text, added = surgical_yaml_append(text, {
            "title": "T",
            "open_questions": ["q?"],
        })
        assert new_text.startswith("---\n")
        assert "title: T" in new_text
        assert "open_questions:" in new_text
        assert "# heading" in new_text
        assert added == ["title", "open_questions"]

    def test_preserves_existing_format(self):
        """User's fm formatting should be byte-identical for
        existing fields."""
        from daemon.writeback_commit import surgical_yaml_append

        # Custom formatting: trailing spaces, comments, ordering
        text = textwrap.dedent(
            """\
            ---
            title: 'My Card'
            tags:
              - tag1   # comment here
              - tag2
            knowledge_identity: personal_persistent
            ---
            body
            """
        )
        new_text, _ = surgical_yaml_append(text, {
            "open_questions": ["q?"],
        })
        # Existing fm bytes preserved
        assert "title: 'My Card'" in new_text
        assert "tag1   # comment here" in new_text


# ---------- sidecar ----------

class TestSidecar:
    def test_sidecar_path_for(self, tmp_path):
        from daemon.writeback_commit import sidecar_path_for

        card = tmp_path / "10_Tech" / "card.md"
        sidecar = sidecar_path_for(card)
        assert sidecar.parent == card.parent
        assert sidecar.name == ".card.md.reflection.json"

    def test_write_sidecar_creates(self, tmp_path):
        from daemon.writeback_commit import write_sidecar, sidecar_path_for

        card = tmp_path / "card.md"
        card.write_text("body", encoding="utf-8")
        changed, sidecar = write_sidecar(card, {
            "status": "open_thread",
            "last_pass": "2026-04-28T12:00:00",
        })
        assert changed is True
        assert sidecar.exists()
        loaded = json.loads(sidecar.read_text(encoding="utf-8"))
        assert loaded["status"] == "open_thread"

    def test_sidecar_idempotent(self, tmp_path):
        from daemon.writeback_commit import write_sidecar

        card = tmp_path / "card.md"
        card.write_text("body", encoding="utf-8")

        payload = {"status": "concluded", "last_pass": "2026-04-28T12:00:00"}
        changed1, _ = write_sidecar(card, payload)
        assert changed1 is True

        changed2, _ = write_sidecar(card, payload)
        # Same content → no rewrite
        assert changed2 is False


# ---------- atomic write ----------

class TestAtomicWrite:
    def test_atomic_write_creates(self, tmp_path):
        from daemon.writeback_commit import _atomic_write

        target = tmp_path / "out.txt"
        _atomic_write(target, "hello\n")
        assert target.read_text(encoding="utf-8") == "hello\n"

    def test_atomic_write_overwrites(self, tmp_path):
        from daemon.writeback_commit import _atomic_write

        target = tmp_path / "out.txt"
        target.write_text("old", encoding="utf-8")
        _atomic_write(target, "new")
        assert target.read_text(encoding="utf-8") == "new"

    def test_no_temp_files_left_after(self, tmp_path):
        """Atomic-write should clean up its temp file after success."""
        from daemon.writeback_commit import _atomic_write

        target = tmp_path / "out.txt"
        _atomic_write(target, "data")
        # Only the target should exist, no .tmp leftovers
        files = sorted(p.name for p in tmp_path.iterdir())
        assert files == ["out.txt"]


# ---------- backup ----------

class TestBackup:
    def test_backup_writes_copy(self, tmp_path):
        from daemon.writeback_commit import write_backup

        card = tmp_path / "card.md"
        card.write_text("original content", encoding="utf-8")
        backup = write_backup(card)
        assert backup is not None
        assert backup.read_text(encoding="utf-8") == "original content"
        assert "backup-" in backup.name

    def test_missing_card_returns_none(self, tmp_path):
        from daemon.writeback_commit import write_backup

        result = write_backup(tmp_path / "nonexistent.md")
        assert result is None


# ---------- commit_card_writeback (integration) ----------

class TestCommitWriteback:
    def test_dry_run_doesnt_modify(self, tmp_path):
        from daemon.writeback_commit import commit_card_writeback

        card = tmp_path / "card.md"
        original = "---\ntitle: T\n---\nbody\n"
        card.write_text(original, encoding="utf-8")

        result = commit_card_writeback(
            card,
            additions={
                "position_signal": {"stance": "X"},
                "reflection": {"status": "open_thread"},
            },
            dry_run=True,
        )

        assert result["error"] is None
        assert result.get("would_change") is True
        # File unchanged
        assert card.read_text(encoding="utf-8") == original
        # No sidecar
        from daemon.writeback_commit import sidecar_path_for
        assert not sidecar_path_for(card).exists()

    def test_real_writeback_appends_fm_and_writes_sidecar(self, tmp_path):
        from daemon.writeback_commit import commit_card_writeback, sidecar_path_for

        card = tmp_path / "card.md"
        original = "---\ntitle: T\n---\nbody content\n"
        card.write_text(original, encoding="utf-8")

        result = commit_card_writeback(
            card,
            additions={
                "position_signal": {"stance": "X", "topic_cluster": "y"},
                "open_questions": ["q?"],
                "reflection": {"status": "open_thread", "last_pass": "2026-04-28"},
            },
            dry_run=False,
            backup=True,
        )

        assert result["error"] is None
        assert "position_signal" in result["frontmatter_keys_added"]
        assert "open_questions" in result["frontmatter_keys_added"]
        assert result["sidecar_changed"] is True

        # Card has new fm fields
        new_text = card.read_text(encoding="utf-8")
        assert "position_signal:" in new_text
        assert "stance: X" in new_text
        assert "open_questions:" in new_text
        # Original title preserved
        assert "title: T" in new_text
        # Body still there
        assert "body content" in new_text

        # Sidecar exists
        sidecar = sidecar_path_for(card)
        assert sidecar.exists()
        sidecar_data = json.loads(sidecar.read_text(encoding="utf-8"))
        assert sidecar_data["status"] == "open_thread"

        # Backup exists
        backups = list(tmp_path.glob(".card.md.backup-*"))
        assert len(backups) == 1
        assert backups[0].read_text(encoding="utf-8") == original

    def test_idempotent_second_run(self, tmp_path):
        """Running twice should be a no-op (no double-add fields)."""
        from daemon.writeback_commit import commit_card_writeback

        card = tmp_path / "card.md"
        card.write_text("---\ntitle: T\n---\nbody\n", encoding="utf-8")

        additions = {
            "position_signal": {"stance": "X"},
            "open_questions": ["q?"],
            "reflection": {"status": "open_thread", "last_pass": "2026-04-28"},
        }

        commit_card_writeback(card, additions, dry_run=False, backup=False)
        text_after_first = card.read_text(encoding="utf-8")

        result2 = commit_card_writeback(card, additions, dry_run=False, backup=False)
        text_after_second = card.read_text(encoding="utf-8")

        # Card text unchanged on second run (idempotent)
        assert text_after_first == text_after_second
        # No new keys added
        assert result2["frontmatter_keys_added"] == []
        # Sidecar same content → no change
        assert result2["sidecar_changed"] is False

    def test_skip_backup_when_disabled(self, tmp_path):
        from daemon.writeback_commit import commit_card_writeback

        card = tmp_path / "card.md"
        card.write_text("---\ntitle: T\n---\nbody\n", encoding="utf-8")

        commit_card_writeback(
            card,
            additions={"position_signal": {"x": "y"}},
            dry_run=False,
            backup=False,
        )
        backups = list(tmp_path.glob(".card.md.backup-*"))
        assert len(backups) == 0

    def test_missing_card_records_error(self, tmp_path):
        from daemon.writeback_commit import commit_card_writeback

        result = commit_card_writeback(
            tmp_path / "nonexistent.md",
            additions={"position_signal": {"x": "y"}},
            dry_run=False,
        )
        assert result["error"] is not None
        assert "does not exist" in result["error"]
