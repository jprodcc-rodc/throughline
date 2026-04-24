"""Tests for `throughline_cli refine --dry-run`.

Verifies the no-LLM preview path:
- Parses a raw markdown file, renders the refiner system + user
  prompts, prints a structured report — without calling any LLM.
- Unknown / missing / bad input surfaces friendly errors.
- Flags (`--show-full-prompt`, `--pack`, `--no-color`) round-trip.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


def _write_raw(tmp_path: Path, body: str = "") -> Path:
    """Produce a raw-conversation markdown file that
    parse_raw_conversation() accepts."""
    p = tmp_path / "raw" / "2026-04-25" / "test-conv.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    text = body or (
        "---\n"
        "conversation_id: test-conv-001\n"
        "source_model: gpt-4\n"
        "---\n\n"
        "## user\n"
        "How do I set up PyTorch MPS on an M2 Mac?\n\n"
        "## assistant\n"
        "Install the nightly build and use `torch.device('mps')` "
        "with a CPU fallback for unsupported ops.\n"
    )
    p.write_text(text, encoding="utf-8")
    return p


class TestRefineDryRunHappyPath:
    def test_runs_without_llm_and_writes_report(self, tmp_path, monkeypatch,
                                                  capsys):
        """A well-formed raw file produces a zero-cost preview
        report on stdout. No HTTP calls, no LLM, exit 0."""
        raw = _write_raw(tmp_path)

        # Guarantee no accidental LLM call.
        import urllib.request
        monkeypatch.setattr(
            urllib.request, "urlopen",
            lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("dry-run must NOT call the network")))

        from throughline_cli import refine
        buf = io.StringIO()
        rc = refine.run_dry_run(raw, color=False, out=buf)
        assert rc == 0

        out = buf.getvalue()
        assert "throughline refine --dry-run" in out
        assert "test-conv-001" in out
        assert "Slicer tier" in out
        assert "No LLM call was made." in out
        # Refiner prompt preview: contains one of the canonical
        # six sections from the refiner template.
        assert "Core Knowledge" in out or "Scene & Pain Point" in out or \
               "Pitfalls" in out or "[SLICE]" in out
        # The user prompt preview includes the formatted conversation.
        assert "USER: How do I set up PyTorch MPS" in out

    def test_deterministic_single_slice_even_for_large_input(self, tmp_path):
        """A large conversation would normally trigger the slicer
        LLM, but dry-run forces the deterministic single-slice path
        so nothing costs money."""
        # 20 messages × 500 chars → well past the single-slice
        # thresholds (6 msgs / 4000 chars).
        msgs = []
        for i in range(20):
            msgs.append(f"## user\n{'padding ' * 62} question {i}\n")
            msgs.append(f"## assistant\n{'response ' * 55} answer {i}\n")
        body = (
            "---\nconversation_id: big-conv\n---\n\n" + "\n".join(msgs)
        )
        raw = _write_raw(tmp_path, body=body)

        from throughline_cli import refine
        buf = io.StringIO()
        rc = refine.run_dry_run(raw, color=False, out=buf)
        assert rc == 0
        out = buf.getvalue()
        # Tier report tells the user which slicer model WOULD fire,
        # but the dry-run itself uses deterministic single-slice.
        assert "Slicer tier" in out
        assert "Slice count    : 1" in out
        # Either one-shot or long-context tier mention is present.
        assert "slicer" in out.lower()

    def test_show_full_prompt_expands(self, tmp_path):
        raw = _write_raw(tmp_path)
        from throughline_cli import refine
        buf_trunc = io.StringIO()
        buf_full = io.StringIO()
        refine.run_dry_run(raw, color=False, out=buf_trunc,
                            show_full_prompt=False)
        refine.run_dry_run(raw, color=False, out=buf_full,
                            show_full_prompt=True)
        # Full version is at least as long as truncated.
        assert len(buf_full.getvalue()) >= len(buf_trunc.getvalue())

    def test_no_color_strips_ansi(self, tmp_path):
        raw = _write_raw(tmp_path)
        from throughline_cli import refine
        buf = io.StringIO()
        refine.run_dry_run(raw, color=False, out=buf)
        # No ANSI escape codes in the plain-text output.
        assert "\033[" not in buf.getvalue()


class TestRefineDryRunErrors:
    def test_missing_file_returns_error_exit(self, tmp_path, capsys):
        from throughline_cli import refine
        rc = refine.run_dry_run(tmp_path / "nope.md", color=False,
                                 out=io.StringIO())
        assert rc == 2
        err = capsys.readouterr().err
        assert "not found" in err

    def test_unparseable_file_returns_error(self, tmp_path, capsys):
        bad = tmp_path / "raw" / "bad.md"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text("no frontmatter, no messages", encoding="utf-8")
        from throughline_cli import refine
        rc = refine.run_dry_run(bad, color=False, out=io.StringIO())
        assert rc == 2
        err = capsys.readouterr().err
        assert "could not parse" in err.lower()

    def test_dry_run_flag_required(self, tmp_path, capsys):
        """Calling `refine <path>` without --dry-run refuses to
        proceed (we don't have a real-refine CLI path in v0.2.x)."""
        raw = _write_raw(tmp_path)
        from throughline_cli import refine
        rc = refine.main([str(raw)])
        assert rc == 2
        err = capsys.readouterr().err
        assert "--dry-run is required" in err


class TestRefineSubcommandDispatch:
    def test_main_help_prints_usage(self, capsys):
        from throughline_cli import refine
        rc = refine.main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "--dry-run" in out

    def test_main_no_args_prints_usage(self, capsys):
        from throughline_cli import refine
        rc = refine.main([])
        assert rc == 2
        out = capsys.readouterr().out
        assert "Usage" in out or "--dry-run" in out

    def test_main_missing_path_errors(self, capsys):
        from throughline_cli import refine
        rc = refine.main(["--dry-run"])
        assert rc == 2
        err = capsys.readouterr().err
        assert "missing path" in err.lower()

    def test_dispatcher_routes_to_refine(self, tmp_path, monkeypatch):
        """Top-level __main__ dispatcher wires `refine` to the
        module's main()."""
        raw = _write_raw(tmp_path)

        import urllib.request
        monkeypatch.setattr(
            urllib.request, "urlopen",
            lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("dry-run must NOT hit network")))

        from throughline_cli.__main__ import main
        rc = main(["refine", "--dry-run", str(raw), "--no-color"])
        assert rc == 0
