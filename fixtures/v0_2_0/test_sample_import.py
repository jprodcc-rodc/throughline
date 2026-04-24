"""Tests for the bundled `import sample` source.

The sample export is shipped at samples/claude_sample.jsonl. The
`import sample` subcommand routes to the Claude adapter with that
path. These tests make sure:

- the bundled file actually exists (CI catches a missing file
  before users see "FileNotFoundError")
- it parses cleanly through the Claude adapter
- the import dispatcher tags it with `sample-YYYY-MM-DD` by default
- a user-supplied --tag overrides the auto-tag
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


SAMPLE_PATH = REPO_ROOT / "samples" / "claude_sample.jsonl"


class TestSampleFilePresent:
    def test_file_exists(self):
        assert SAMPLE_PATH.exists(), (
            f"Bundled sample missing: {SAMPLE_PATH}. "
            f"Did samples/ get excluded from a git op?"
        )

    def test_each_line_parses(self):
        for i, line in enumerate(
            SAMPLE_PATH.read_text(encoding="utf-8").splitlines(), start=1
        ):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise AssertionError(
                    f"Sample line {i} is not valid JSON: {e}"
                ) from e
            assert "uuid" in rec, f"line {i} missing uuid"
            assert "chat_messages" in rec, f"line {i} missing chat_messages"
            assert len(rec["chat_messages"]) >= 2, (
                f"line {i} has < 2 messages — taxonomy needs both sides"
            )

    def test_count_is_ten(self):
        """README + UX flow promise 10 conversations. Pin the count."""
        n = sum(1 for line in SAMPLE_PATH.read_text(encoding="utf-8").splitlines()
                if line.strip())
        assert n == 10

    def test_topic_diversity(self):
        """Variety matters for U27 taxonomy growth signals — a sample
        of 10 conversations on the same topic doesn't exercise the
        observer. Check that conversation NAMES touch at least 5
        distinct keyword domains."""
        names = []
        for line in SAMPLE_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            names.append(json.loads(line)["name"].lower())
        domains_hit = set()
        for n in names:
            for kw, dom in [
                ("pytorch", "AI"), ("rag", "AI"), ("mcp", "AI"),
                ("keto", "Health"), ("renal", "Health"),
                ("camera", "Creative"), ("video", "Creative"),
                ("color", "Creative"),
                ("saas", "Biz"), ("tax", "Biz"),
                ("game", "Game"), ("puzzle", "Game"),
            ]:
                if kw in n:
                    domains_hit.add(dom)
        assert len(domains_hit) >= 5, (
            f"Sample diversity too narrow: only {domains_hit}. "
            f"Add variety so the U27 observer has signal."
        )


class TestImportSampleDispatcher:
    def test_dispatcher_routes_to_claude_adapter(self, tmp_path,
                                                   monkeypatch, capsys):
        """`import sample --dry-run` should run the Claude adapter
        against the bundled file and emit the standard summary."""
        from throughline_cli.adapters import main as adapters_main
        rc = adapters_main([
            "sample", "--dry-run",
            "--out", str(tmp_path / "out"),
        ])
        assert rc == 0
        out = capsys.readouterr().out
        # The Claude adapter prints "emitted N" — our 10-conv sample
        # should show 10.
        assert "emitted" in out
        assert "10" in out

    def test_default_tag_is_sample_yyyy_mm_dd(self, tmp_path, capsys):
        """When the user doesn't supply --tag, dispatcher auto-tags
        `sample-YYYY-MM-DD` so bulk-purge of just the samples is one
        tag. Verified by running a real import (not dry-run) and
        reading the manifest."""
        from throughline_cli.adapters import main as adapters_main
        out_dir = tmp_path / "out"
        rc = adapters_main([
            "sample",
            "--out", str(out_dir),
        ])
        assert rc == 0
        # Manifest path is announced in stdout.
        out = capsys.readouterr().out
        assert "sample-" in out
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in out

    def test_user_tag_overrides_default(self, tmp_path, capsys):
        from throughline_cli.adapters import main as adapters_main
        rc = adapters_main([
            "sample", "--dry-run",
            "--tag", "custom-test-tag",
            "--out", str(tmp_path / "out"),
        ])
        assert rc == 0
        # User tag appears, default doesn't.
        out = capsys.readouterr().out
        assert "custom-test-tag" in out
        # No automatically-prefixed `sample-YYYY-MM-DD` (the user
        # explicitly opted out by passing --tag).
        assert f"sample-{datetime.now().strftime('%Y-%m-%d')}" not in out


class TestSampleListedInUsage:
    def test_usage_mentions_sample(self, capsys):
        from throughline_cli.adapters import main as adapters_main
        rc = adapters_main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "sample" in out
        # Hint that no path is needed.
        assert "zero arg" in out or "no path" in out or "zero-arg" in out
