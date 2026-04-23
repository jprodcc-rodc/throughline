"""Tests for U2 Claude.ai export adapter.

Covers the common hotspots:
- JSONL parse with variant field names (uuid vs id, chat_messages vs
  messages, text vs content-as-list)
- Role normalisation (human / user / assistant / ai -> user/assistant)
- Skip conversations with no content or malformed payloads
- File path shape: $OUT/YYYY-MM/YYYY-MM-DD_{uuid}.md
- Frontmatter contains title / date / import_source / platform
- --dry-run does NOT write files
- --limit caps scanned conversations
- Manifest JSON written with the right tag + conversation UUIDs
- ZIP input is unpacked to a tempdir and processed transparently
- Missing input path raises a clean FileNotFoundError
"""
from __future__ import annotations

import json
import sys
import zipfile
from datetime import date
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli.adapters import claude_export
from throughline_cli.adapters.common import (
    ImportSummary, make_import_tag, render_markdown, target_path,
    safe_conv_id,
)


# ---------- synthetic Claude export fixtures ----------

def _sample_jsonl() -> list[dict]:
    """Three conversations across two months; third is malformed."""
    return [
        {
            "uuid": "11111111-aaaa-bbbb-cccc-000000000001",
            "name": "Setting up PyTorch on M2 Mac",
            "created_at": "2024-03-15T10:30:00Z",
            "updated_at": "2024-03-15T11:45:00Z",
            "chat_messages": [
                {"sender": "human", "text": "How do I enable MPS?"},
                {"sender": "assistant", "text": "Use torch.device('mps')."},
                {"sender": "human", "text": "And for fallback ops?"},
                {"sender": "assistant",
                 "content": [{"type": "text",
                              "text": "Set PYTORCH_ENABLE_MPS_FALLBACK=1."}]},
            ],
        },
        {
            "uuid": "22222222-dddd-eeee-ffff-000000000002",
            "title": "PARA vs Zettelkasten",
            "created_at": "2024-04-02T09:00:00Z",
            "messages": [
                {"role": "user", "content": "Which is better for research?"},
                {"role": "ai", "text": "Depends on entry point: PARA for action..."},
            ],
        },
        # Malformed: no messages / no chat_messages at all.
        {
            "id": "33333333-0000-0000-0000-000000000003",
            "name": "empty",
            "created_at": "2024-04-03T00:00:00Z",
        },
    ]


def _write_jsonl(tmp_path: Path,
                 rows: list[dict],
                 name: str = "conversations.jsonl") -> Path:
    p = tmp_path / name
    p.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    return p


# ---------- helpers ----------

class TestCommonHelpers:
    def test_safe_conv_id_strips_slashes(self):
        assert safe_conv_id("a/b?c") == "abc"

    def test_safe_conv_id_keeps_valid(self):
        assert safe_conv_id("abc-123_DEF") == "abc-123_DEF"

    def test_safe_conv_id_empty_fallback(self):
        assert safe_conv_id("!!!") == "anon"

    def test_target_path_shape(self):
        p = target_path(Path("/tmp/raw"), date(2024, 3, 15), "uuid-abc")
        assert p == Path("/tmp/raw/2024-03/2024-03-15_uuid-abc.md")

    def test_make_import_tag(self):
        tag = make_import_tag("claude", today=date(2026, 4, 23))
        assert tag == "claude-2026-04-23"

    def test_render_markdown_has_frontmatter_and_roles(self):
        body = render_markdown(
            title="Test Convo",
            messages=[("user", "hello"), ("assistant", "hi back")],
            metadata={
                "title": "Test Convo",
                "date": "2024-03-15",
                "source_platform": "claude",
                "source_conversation_id": "abc",
                "import_source": "claude-2026-04-23",
            },
        )
        assert body.startswith("---\n")
        assert 'title: "Test Convo"' in body
        assert "source_platform: \"claude\"" in body
        assert "import_source: \"claude-2026-04-23\"" in body
        assert "# User" in body
        assert "# Assistant" in body
        assert "hello" in body
        assert "hi back" in body

    def test_render_markdown_escapes_quotes_in_frontmatter(self):
        body = render_markdown(
            title='A "quoted" title',
            messages=[("user", "x")],
            metadata={"title": 'A "quoted" title',
                      "date": "2024-01-01",
                      "source_platform": "claude",
                      "source_conversation_id": "x",
                      "import_source": "claude-x"},
        )
        assert 'A \\"quoted\\" title' in body


# ---------- parsing ----------

class TestParsing:
    def test_extract_text_string_field(self):
        assert claude_export._extract_text({"text": "hi"}) == "hi"

    def test_extract_text_content_string(self):
        assert claude_export._extract_text({"content": "hi"}) == "hi"

    def test_extract_text_content_list(self):
        out = claude_export._extract_text({
            "content": [{"type": "text", "text": "a"},
                        {"type": "text", "text": "b"}]
        })
        assert "a" in out and "b" in out

    def test_extract_text_missing_returns_empty(self):
        assert claude_export._extract_text({}) == ""

    def test_normalise_role_variants(self):
        assert claude_export._normalise_role("human") == "user"
        assert claude_export._normalise_role("USER") == "user"
        assert claude_export._normalise_role("assistant") == "assistant"
        assert claude_export._normalise_role("claude") == "assistant"
        assert claude_export._normalise_role("system") is None
        assert claude_export._normalise_role("tool") is None
        assert claude_export._normalise_role(None) is None

    def test_extract_date_iso_with_z(self):
        d = claude_export._extract_date({"created_at": "2024-03-15T10:30:00Z"})
        assert d == date(2024, 3, 15)

    def test_extract_date_fallback_today(self):
        d = claude_export._extract_date({"created_at": "not-a-date"})
        assert d == date.today()

    def test_extract_conv_id_prefers_uuid(self):
        assert claude_export._extract_conv_id({"uuid": "abc", "id": "xyz"}) == "abc"

    def test_extract_conv_id_fallback_id(self):
        assert claude_export._extract_conv_id({"id": "xyz"}) == "xyz"

    def test_extract_conv_id_unknown(self):
        assert claude_export._extract_conv_id({}) == "unknown"

    def test_extract_messages_variant_fields(self):
        conv = {
            "messages": [
                {"role": "user", "content": "a"},
                {"role": "assistant", "text": "b"},
            ]
        }
        out = claude_export._extract_messages(conv)
        assert out == [("user", "a"), ("assistant", "b")]

    def test_extract_messages_drops_empty_text(self):
        conv = {"chat_messages": [
            {"sender": "human", "text": ""},
            {"sender": "assistant", "text": "ok"},
        ]}
        out = claude_export._extract_messages(conv)
        assert out == [("assistant", "ok")]


# ---------- integration: run() over a fixture ----------

class TestRun:
    def test_run_emits_correct_count_and_paths(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path / "cfg"))
        src = _write_jsonl(tmp_path, _sample_jsonl())
        out_dir = tmp_path / "raw"

        summary = claude_export.run(
            input_path=src,
            out_dir=out_dir,
            dry_run=False,
            import_tag="claude-2026-04-23",
            state_dir=tmp_path / "state",
        )

        assert summary.source == "claude"
        assert summary.import_tag == "claude-2026-04-23"
        assert summary.scanned == 3
        assert summary.emitted == 2
        assert summary.skipped_no_content == 1

        # Files in the right month buckets (safe_conv_id truncates at 36)
        f1 = out_dir / "2024-03" / "2024-03-15_11111111-aaaa-bbbb-cccc-000000000001.md"
        f2 = out_dir / "2024-04" / "2024-04-02_22222222-dddd-eeee-ffff-000000000002.md"
        assert f1.exists(), list((out_dir / "2024-03").iterdir())
        assert f2.exists(), list((out_dir / "2024-04").iterdir())

    def test_run_writes_frontmatter_with_import_source(self, tmp_path):
        src = _write_jsonl(tmp_path, _sample_jsonl()[:1])
        out_dir = tmp_path / "raw"
        claude_export.run(
            input_path=src,
            out_dir=out_dir,
            import_tag="claude-unit-test",
            state_dir=tmp_path / "state",
        )
        md_files = list(out_dir.rglob("*.md"))
        assert len(md_files) == 1
        txt = md_files[0].read_text(encoding="utf-8")
        assert "import_source: \"claude-unit-test\"" in txt
        assert "source_platform: \"claude\"" in txt
        assert '# User' in txt
        assert '# Assistant' in txt

    def test_dry_run_writes_nothing_but_counts(self, tmp_path):
        src = _write_jsonl(tmp_path, _sample_jsonl())
        out_dir = tmp_path / "raw-dry"
        summary = claude_export.run(
            input_path=src,
            out_dir=out_dir,
            dry_run=True,
            state_dir=tmp_path / "state",
        )
        assert summary.emitted == 2
        assert summary.scanned == 3
        assert summary.dry_run is True
        assert summary.total_tokens_estimate > 0
        # No files were written.
        assert not out_dir.exists() or not list(out_dir.rglob("*.md"))
        # Sample paths are populated so a dry-run report can echo them.
        assert len(summary.sample_paths) > 0

    def test_limit_caps_scanned(self, tmp_path):
        src = _write_jsonl(tmp_path, _sample_jsonl())
        out_dir = tmp_path / "raw-limit"
        summary = claude_export.run(
            input_path=src,
            out_dir=out_dir,
            dry_run=True,
            limit=1,
            state_dir=tmp_path / "state",
        )
        assert summary.scanned == 1

    def test_manifest_written(self, tmp_path):
        src = _write_jsonl(tmp_path, _sample_jsonl())
        out_dir = tmp_path / "raw-manifest"
        state = tmp_path / "state"
        summary = claude_export.run(
            input_path=src,
            out_dir=out_dir,
            import_tag="claude-manifest-test",
            state_dir=state,
        )
        manifest = state / "imports" / "claude-manifest-test.json"
        assert manifest.exists()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["tag"] == "claude-manifest-test"
        assert data["source"] == "claude"
        assert data["emitted"] == 2
        ids = data["conversation_ids"]
        assert len(ids) == 2
        assert any(i.startswith("11111111") for i in ids)
        assert any(i.startswith("22222222") for i in ids)

    def test_no_manifest_on_dry_run(self, tmp_path):
        src = _write_jsonl(tmp_path, _sample_jsonl())
        state = tmp_path / "state"
        summary = claude_export.run(
            input_path=src,
            out_dir=tmp_path / "raw",
            dry_run=True,
            state_dir=state,
        )
        assert summary.manifest_path is None
        assert not (state / "imports").exists() or not list(
            (state / "imports").iterdir()
        )


# ---------- source-shape detection ----------

class TestFindJsonl:
    def test_direct_jsonl(self, tmp_path):
        p = _write_jsonl(tmp_path, _sample_jsonl())
        assert claude_export._find_jsonl(p) == p

    def test_directory_contains_jsonl(self, tmp_path):
        d = tmp_path / "export"
        d.mkdir()
        p = _write_jsonl(d, _sample_jsonl())
        assert claude_export._find_jsonl(d) == p

    def test_zip_contains_jsonl(self, tmp_path):
        jsonl = _write_jsonl(tmp_path, _sample_jsonl(), name="_raw.jsonl")
        zip_path = tmp_path / "export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(jsonl, arcname="conversations.jsonl")
            # Decoy files that should be ignored.
            zf.writestr("users.json", "{}")
            zf.writestr("projects.json", "[]")
        extracted = claude_export._find_jsonl(zip_path)
        assert extracted.name == "conversations.jsonl"
        assert extracted.read_text(encoding="utf-8")

    def test_missing_path(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            claude_export._find_jsonl(tmp_path / "nope.jsonl")

    def test_directory_without_jsonl_raises(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        with pytest.raises(FileNotFoundError):
            claude_export._find_jsonl(d)


# ---------- CLI surface ----------

class TestCli:
    def test_help_prints_usage(self, capsys):
        rc = claude_export.cli([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "Usage" in err

    def test_cli_runs_end_to_end(self, tmp_path, capsys, monkeypatch):
        src = _write_jsonl(tmp_path, _sample_jsonl())
        out_dir = tmp_path / "raw"
        state = tmp_path / "state"
        monkeypatch.chdir(tmp_path)  # just for cleanliness
        rc = claude_export.cli([
            str(src),
            "--out", str(out_dir),
            "--tag", "claude-cli-test",
        ])
        # The adapter prints via rich to stdout; we don't assert on the
        # rendered text but the exit code and filesystem effect must be
        # right.
        assert rc == 0
        assert (out_dir / "2024-03").exists()

    def test_cli_unknown_flag_returns_2(self):
        rc = claude_export.cli(["nonexistent", "--no-such-flag"])
        assert rc == 2


# ---------- Cost-estimate sanity ----------

class TestCostEstimates:
    def test_tokens_scale_with_content(self, tmp_path):
        src = _write_jsonl(tmp_path, _sample_jsonl())
        small = claude_export.run(
            input_path=src, out_dir=tmp_path / "a",
            dry_run=True, limit=1, state_dir=tmp_path / "s",
        )
        full = claude_export.run(
            input_path=src, out_dir=tmp_path / "b",
            dry_run=True, state_dir=tmp_path / "s",
        )
        assert full.total_tokens_estimate >= small.total_tokens_estimate

    def test_usd_estimates_non_negative_and_skim_cheaper(self, tmp_path):
        src = _write_jsonl(tmp_path, _sample_jsonl())
        s = claude_export.run(
            input_path=src, out_dir=tmp_path / "raw",
            dry_run=True, state_dir=tmp_path / "s",
        )
        normal = s.estimated_usd_normal()
        skim = s.estimated_usd_skim()
        assert normal >= 0
        assert skim >= 0
        assert skim <= normal  # Haiku is cheaper than Sonnet


# ---------- subcommand dispatcher ----------

class TestMainDispatch:
    def test_import_claude_via_main(self, tmp_path, monkeypatch):
        from throughline_cli.adapters import main as adapters_main
        src = _write_jsonl(tmp_path, _sample_jsonl())
        out_dir = tmp_path / "raw"
        rc = adapters_main([
            "claude", str(src),
            "--out", str(out_dir),
            "--dry-run",
        ])
        assert rc == 0

    def test_import_unknown_source_returns_2(self):
        from throughline_cli.adapters import main as adapters_main
        rc = adapters_main(["notarealsource", "x"])
        assert rc == 2

    def test_help_subcommand(self, capsys):
        from throughline_cli.adapters import main as adapters_main
        rc = adapters_main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "claude" in out
