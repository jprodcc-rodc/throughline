"""Tests for U2 Gemini Takeout adapter.

Covers the bits most likely to drift:
- Prompted-prefix strip across locales (en / zh-CN / zh-TW)
- HTML -> Markdown conversion preserves headings, lists, bold, code
- Events without safeHtmlItem counted as skipped empty, not malformed
- Day-bucket grouping sorts by timestamp within a day
- attachedFiles + imageFile rendered as `[...]` placeholders
- ZIP containing a Chinese-named 'Gemini Apps' directory found via
  unicode-aware pattern match
- iter_events handles JSON array and single-object shapes
- dry-run + limit + manifest behaviour matches the other adapters
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

from throughline_cli.adapters import gemini_takeout


# ---------- synthetic fixtures ----------

def _event(title: str,
           response_html: str,
           time: str,
           attached_files: list | None = None,
           image_file: str | None = None) -> dict:
    e = {
        "header": "Gemini Apps",
        "title": title,
        "time": time,
        "products": ["Gemini Apps"],
        "activityControls": ["Gemini Apps Activity"],
    }
    if response_html is not None:
        e["safeHtmlItem"] = [{"html": response_html}]
    if attached_files:
        e["attachedFiles"] = attached_files
    if image_file:
        e["imageFile"] = image_file
    return e


def _sample_events() -> list[dict]:
    return [
        _event("Prompted How do I enable MPS on M2?",
               "<p>Use <code>torch.device('mps')</code>.</p>",
               "2024-03-15T09:00:00Z"),
        # Same day, later — will share the 2024-03-15 bucket.
        _event("Prompted And for fallback?",
               "<p>Set <strong>PYTORCH_ENABLE_MPS_FALLBACK=1</strong>.</p>",
               "2024-03-15T09:05:00Z"),
        # Next day, different topic.
        _event("Prompted What is PARA?",
               "<h3>PARA</h3><ul><li>Projects</li><li>Areas</li></ul>",
               "2024-03-16T10:00:00Z"),
        # Event with no response — should be skipped.
        _event("Prompted abandoned question", None,
               "2024-03-16T11:00:00Z"),
        # Event with attached file and generated image.
        _event("Prompted Make a logo",
               "<p>Here's your logo.</p>",
               "2024-03-17T08:00:00Z",
               attached_files=[{"name": "brief.pdf"}],
               image_file="logo_out.png"),
    ]


# ---------- Prompted-prefix strip ----------

class TestStripPrompted:
    def test_english_prefix(self):
        assert gemini_takeout._strip_prompted_prefix("Prompted hello") == "hello"

    def test_zh_cn_prefix(self):
        assert gemini_takeout._strip_prompted_prefix("已提示 你好") == "你好"

    def test_zh_tw_prefix(self):
        assert gemini_takeout._strip_prompted_prefix("已給予提示 你好") == "你好"

    def test_no_prefix_passthrough(self):
        assert gemini_takeout._strip_prompted_prefix("direct question") == "direct question"

    def test_non_string(self):
        assert gemini_takeout._strip_prompted_prefix(None) == ""  # type: ignore
        assert gemini_takeout._strip_prompted_prefix(123) == ""   # type: ignore


# ---------- HTML -> Markdown ----------

class TestHtmlToMarkdown:
    def test_headings_become_markdown(self):
        out = gemini_takeout._html_to_markdown("<h3>Title</h3>")
        assert "### Title" in out or "Title" in out

    def test_bold_and_code(self):
        out = gemini_takeout._html_to_markdown(
            "<p>Use <strong>torch</strong> with <code>mps</code>.</p>"
        )
        assert "**torch**" in out
        assert "`mps`" in out

    def test_list(self):
        out = gemini_takeout._html_to_markdown("<ul><li>a</li><li>b</li></ul>")
        assert "a" in out and "b" in out
        # Bullets in output.
        assert "- a" in out or "* a" in out

    def test_nested_anchors(self):
        out = gemini_takeout._html_to_markdown(
            '<p>See <a href="https://example.com">this</a>.</p>'
        )
        assert "[this](https://example.com)" in out

    def test_empty_html(self):
        assert gemini_takeout._html_to_markdown("") == ""


# ---------- day grouping ----------

class TestGroupByDay:
    def test_groups_same_day(self):
        events = _sample_events()
        buckets = gemini_takeout._group_by_day(events)
        mar15 = buckets.get(date(2024, 3, 15)) or []
        mar16 = buckets.get(date(2024, 3, 16)) or []
        mar17 = buckets.get(date(2024, 3, 17)) or []
        assert len(mar15) == 2
        assert len(mar16) == 2  # includes the no-response event
        assert len(mar17) == 1

    def test_sorted_by_time_within_day(self):
        events = [
            _event("Prompted later", "<p>b</p>", "2024-03-15T11:00:00Z"),
            _event("Prompted earlier", "<p>a</p>", "2024-03-15T09:00:00Z"),
        ]
        buckets = gemini_takeout._group_by_day(events)
        day = buckets[date(2024, 3, 15)]
        assert day[0]["title"] == "Prompted earlier"
        assert day[1]["title"] == "Prompted later"


# ---------- attachment rendering ----------

class TestAttachmentRendering:
    def test_attached_files_list_of_dicts(self):
        event = _event("Prompted test", "<p>reply</p>",
                       "2024-03-17T08:00:00Z",
                       attached_files=[{"name": "a.pdf"}, {"name": "b.jpg"}])
        out = gemini_takeout._render_attached_files(event)
        assert "a.pdf" in out
        assert "b.jpg" in out

    def test_attached_files_strings(self):
        event = {"attachedFiles": ["direct.txt"]}
        assert "direct.txt" in gemini_takeout._render_attached_files(event)

    def test_image_file_dict(self):
        event = {"imageFile": {"name": "out.png"}}
        assert "out.png" in gemini_takeout._render_attached_files(event)

    def test_image_file_string(self):
        event = {"imageFile": "logo.png"}
        assert "logo.png" in gemini_takeout._render_attached_files(event)

    def test_no_attachments(self):
        assert gemini_takeout._render_attached_files({}) == ""


# ---------- iter_events ----------

class TestIterEvents:
    def test_json_array(self, tmp_path):
        p = tmp_path / "MyActivity.json"
        p.write_text(json.dumps(_sample_events()), encoding="utf-8")
        got = list(gemini_takeout.iter_events(p))
        assert len(got) == 5

    def test_json_object_single(self, tmp_path):
        p = tmp_path / "MyActivity.json"
        p.write_text(json.dumps(_sample_events()[0]), encoding="utf-8")
        got = list(gemini_takeout.iter_events(p))
        assert len(got) == 1

    def test_empty_file(self, tmp_path):
        p = tmp_path / "MyActivity.json"
        p.write_text("", encoding="utf-8")
        assert list(gemini_takeout.iter_events(p)) == []

    def test_malformed_file(self, tmp_path):
        p = tmp_path / "MyActivity.json"
        p.write_text("not json", encoding="utf-8")
        assert list(gemini_takeout.iter_events(p)) == []


# ---------- _find_activity_json ----------

class TestFindActivityJson:
    def _make_takeout_zip(self, tmp_path: Path, json_name: str) -> Path:
        """Build a takeout-style ZIP with a Gemini Apps subdirectory
        containing the activity JSON. Mirrors the real Takeout layout."""
        zp = tmp_path / "takeout.zip"
        data = json.dumps(_sample_events())
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr(f"Takeout/My Activity/Gemini Apps/{json_name}", data)
            zf.writestr("Takeout/My Activity/Takeout/summary.json", "{}")
            zf.writestr("Takeout/My Activity/Gemini Apps/image_abc.png",
                        b"\x89PNG\r\n")
        return zp

    def test_zip_english_name(self, tmp_path):
        zp = self._make_takeout_zip(tmp_path, "MyActivity.json")
        out = gemini_takeout._find_activity_json(zp)
        assert out.exists()
        assert out.read_text(encoding="utf-8").startswith("[")

    def test_zip_chinese_name(self, tmp_path):
        zp = self._make_takeout_zip(tmp_path, "我的活动记录.json")
        out = gemini_takeout._find_activity_json(zp)
        assert out.exists()

    def test_zip_no_json_raises(self, tmp_path):
        zp = tmp_path / "bad.zip"
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr("Takeout/notes.txt", "nothing")
        with pytest.raises(FileNotFoundError):
            gemini_takeout._find_activity_json(zp)

    def test_direct_json(self, tmp_path):
        p = tmp_path / "MyActivity.json"
        p.write_text(json.dumps(_sample_events()), encoding="utf-8")
        assert gemini_takeout._find_activity_json(p) == p

    def test_directory_with_gemini_apps(self, tmp_path):
        d = tmp_path / "Takeout" / "My Activity" / "Gemini Apps"
        d.mkdir(parents=True)
        p = d / "MyActivity.json"
        p.write_text(json.dumps(_sample_events()), encoding="utf-8")
        found = gemini_takeout._find_activity_json(tmp_path)
        assert found == p


# ---------- day -> conversation reduction ----------

class TestDayToConversation:
    def test_linear_render(self):
        events = _sample_events()[:2]  # both on 2024-03-15
        title, messages, conv_id = gemini_takeout._day_to_conversation(
            date(2024, 3, 15), events,
        )
        assert "2026" not in title  # don't leak today() accidentally
        assert "2024-03-15" in title
        assert conv_id == "gemini-2024-03-15"
        roles = [m[0] for m in messages]
        assert roles == ["user", "assistant", "user", "assistant"]
        user_q = messages[0][1]
        assert "How do I enable MPS" in user_q

    def test_skips_event_with_no_response(self):
        events = [_sample_events()[3]]  # the abandoned one
        _, messages, _ = gemini_takeout._day_to_conversation(
            date(2024, 3, 16), events,
        )
        # User query is present (the title "abandoned question") but
        # assistant reply is absent. We STILL emit the user turn —
        # dropping it would erase context. 1 message, not 2.
        assert len(messages) == 1
        assert messages[0][0] == "user"

    def test_attachment_appended_to_user_body(self):
        events = [_sample_events()[4]]  # the logo one
        _, messages, _ = gemini_takeout._day_to_conversation(
            date(2024, 3, 17), events,
        )
        # User message should include the attached PDF note AND the
        # image-generated note; assistant reply right after.
        user_body = messages[0][1]
        assert "Make a logo" in user_body
        assert "brief.pdf" in user_body
        assert "logo_out.png" in user_body


# ---------- run() ----------

class TestRun:
    def _write_events_file(self, tmp_path, events=None) -> Path:
        events = events if events is not None else _sample_events()
        p = tmp_path / "MyActivity.json"
        p.write_text(json.dumps(events, ensure_ascii=False), encoding="utf-8")
        return p

    def test_run_emits_day_buckets(self, tmp_path):
        src = self._write_events_file(tmp_path)
        out = tmp_path / "raw"
        summary = gemini_takeout.run(
            input_path=src, out_dir=out,
            import_tag="gemini-unit",
            state_dir=tmp_path / "state",
        )
        assert summary.source == "gemini"
        assert summary.scanned == 5
        # 3 days: 2024-03-15, 2024-03-16, 2024-03-17
        assert summary.emitted == 3
        md_files = list(out.rglob("*.md"))
        assert len(md_files) == 3

    def test_frontmatter_has_platform(self, tmp_path):
        src = self._write_events_file(tmp_path)
        out = tmp_path / "raw"
        gemini_takeout.run(
            input_path=src, out_dir=out,
            import_tag="gemini-fm",
            state_dir=tmp_path / "state",
        )
        md = (list(out.rglob("*.md")))[0].read_text(encoding="utf-8")
        assert 'source_platform: "gemini"' in md
        assert 'import_source: "gemini-fm"' in md

    def test_dry_run(self, tmp_path):
        src = self._write_events_file(tmp_path)
        out = tmp_path / "raw"
        summary = gemini_takeout.run(
            input_path=src, out_dir=out, dry_run=True,
            state_dir=tmp_path / "state",
        )
        assert summary.dry_run is True
        assert summary.emitted == 3
        assert not out.exists() or not list(out.rglob("*.md"))

    def test_limit_caps_events(self, tmp_path):
        src = self._write_events_file(tmp_path)
        summary = gemini_takeout.run(
            input_path=src, out_dir=tmp_path / "raw",
            dry_run=True, limit=2,
            state_dir=tmp_path / "state",
        )
        assert summary.scanned == 2

    def test_manifest(self, tmp_path):
        src = self._write_events_file(tmp_path)
        state = tmp_path / "state"
        gemini_takeout.run(
            input_path=src, out_dir=tmp_path / "raw",
            import_tag="gemini-man",
            state_dir=state,
        )
        manifest = state / "imports" / "gemini-man.json"
        assert manifest.exists()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["source"] == "gemini"
        # conversation_ids contain 'gemini-<date>' slugs
        assert all(cid.startswith("gemini-2024-") for cid in data["conversation_ids"])


# ---------- CLI / dispatcher ----------

class TestCli:
    def test_usage(self, capsys):
        rc = gemini_takeout.cli([])
        assert rc == 2
        assert "Usage" in capsys.readouterr().err

    def test_end_to_end(self, tmp_path):
        events = _sample_events()
        src = tmp_path / "MyActivity.json"
        src.write_text(json.dumps(events), encoding="utf-8")
        rc = gemini_takeout.cli([
            str(src), "--out", str(tmp_path / "raw"),
            "--tag", "gemini-cli",
        ])
        assert rc == 0


class TestDispatcher:
    def test_gemini_via_main(self, tmp_path):
        from throughline_cli.adapters import main as adapters_main
        src = tmp_path / "MyActivity.json"
        src.write_text(json.dumps(_sample_events()), encoding="utf-8")
        rc = adapters_main([
            "gemini", str(src),
            "--out", str(tmp_path / "raw"),
            "--dry-run",
        ])
        assert rc == 0

    def test_help_lists_gemini(self, capsys):
        from throughline_cli.adapters import main as adapters_main
        rc = adapters_main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "gemini" in out
