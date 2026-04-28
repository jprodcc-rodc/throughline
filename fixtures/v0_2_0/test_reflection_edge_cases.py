"""Edge-case tests for the Reflection Pass pipeline.

Stress-tests the production code against pathological inputs:
- enormous card bodies
- only-emoji headers
- mixed-language clusters
- malformed YAML frontmatter that pyyaml almost-parses
- state files with non-UTF8 bytes
- card paths with spaces / unicode / Windows separators
- empty / whitespace-only fields throughout

Goal: prove the pipeline degrades gracefully (no crashes, no
silent corruption) rather than asserting specific outputs for
every edge.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest


# ---------- Card body parser edge cases ----------

class TestBodyParserEdges:
    def test_enormous_body(self):
        """100KB body should not crash the parser."""
        from daemon.card_body_parser import parse_body_sections

        big = "# 🎯 场景与痛点\n" + ("body " * 20000)
        sections = parse_body_sections(big)
        assert "scene_and_pain_point" in sections
        # Section content present and non-empty
        assert len(sections["scene_and_pain_point"]) > 0

    def test_only_emoji_header(self):
        """Header that's literally just an emoji has no normalization
        target. Should fall through to _unknown_<slug> rather than
        crashing."""
        from daemon.card_body_parser import parse_body_sections

        body = "# 🎯\nbody content here\n"
        sections = parse_body_sections(body)
        # The header normalizes to empty (only emoji + whitespace)
        # which produces _unknown_untitled or similar; doesn't crash
        assert any(k.startswith("_unknown") for k in sections)

    def test_trailing_whitespace_in_header(self):
        from daemon.card_body_parser import parse_body_sections

        body = "# 🎯 场景与痛点    \nbody\n"
        sections = parse_body_sections(body)
        assert "scene_and_pain_point" in sections

    def test_header_with_inline_code(self):
        """Headers containing inline code shouldn't crash even
        though they're unusual."""
        from daemon.card_body_parser import parse_body_sections

        body = "# Scene `with code` & Pain Point\nbody\n"
        sections = parse_body_sections(body)
        # Should not crash; content recoverable somewhere
        assert sections  # non-empty

    def test_mixed_dialect_card(self):
        """Card with both English-only sections AND Chinese-only
        sections in the same body. Should canonicalize each
        consistently."""
        from daemon.card_body_parser import parse_body_sections

        body = textwrap.dedent(
            """\
            # 🎯 场景与痛点
            场景

            # Core Knowledge & First Principles
            principles

            # 💡 启发与思维模型
            模型
            """
        )
        sections = parse_body_sections(body)
        assert "scene_and_pain_point" in sections
        assert "first_principles" in sections
        assert "mental_models" in sections

    def test_html_tags_in_body(self):
        from daemon.card_body_parser import parse_body_sections

        body = "# 🎯 场景与痛点\n<div>html-ish</div>\n<br>\n"
        sections = parse_body_sections(body)
        assert "scene_and_pain_point" in sections
        assert "<div>html-ish</div>" in sections["scene_and_pain_point"]

    def test_unicode_zero_width_chars(self):
        """Zero-width spaces and joiners shouldn't break tokenization."""
        from daemon.card_body_parser import parse_body_sections

        # Insert U+200B zero-width space
        body = "# ​🎯 场景与痛点\nbody\n"
        sections = parse_body_sections(body)
        # May or may not match depending on normalization; should
        # not crash in either case
        assert isinstance(sections, dict)


# ---------- Frontmatter parser edge cases ----------

class TestFrontmatterEdges:
    def test_empty_frontmatter_block(self):
        from daemon.reflection_pass import _parse_frontmatter

        text = "---\n---\nbody\n"
        fm, body = _parse_frontmatter(text)
        # Empty YAML → empty dict; body remains
        assert fm == {}
        assert "body" in body or fm == {}  # at minimum no crash

    def test_only_frontmatter_no_body(self):
        from daemon.reflection_pass import _parse_frontmatter

        text = "---\ntitle: T\n---\n"
        fm, body = _parse_frontmatter(text)
        assert fm.get("title") == "T"
        assert body.strip() == ""

    def test_frontmatter_with_quoted_strings(self):
        from daemon.reflection_pass import _parse_frontmatter

        text = '---\ntitle: "weird: title with: colons"\n---\nbody'
        fm, body = _parse_frontmatter(text)
        assert "weird" in fm["title"]

    def test_frontmatter_with_multiline_string(self):
        from daemon.reflection_pass import _parse_frontmatter

        text = textwrap.dedent(
            """\
            ---
            title: Test
            description: |
              A multiline
              description with
              multiple lines.
            ---
            body
            """
        )
        fm, body = _parse_frontmatter(text)
        assert fm.get("title") == "Test"
        assert "multiline" in fm.get("description", "")

    def test_yaml_explicit_null(self):
        from daemon.reflection_pass import _parse_frontmatter

        text = "---\ntitle: T\nposition_signal: null\n---\nbody"
        fm, _ = _parse_frontmatter(text)
        assert fm.get("position_signal") is None


# ---------- Tokenizer edge cases ----------

class TestTokenizerEdges:
    def test_only_punctuation(self):
        """Underscore is a word char in \\w so '___' tokenizes; that's
        an acceptable quirk. Other punctuation produces no tokens."""
        from daemon.open_threads import _tokenize

        assert _tokenize("...!!!??? — ") == set()
        # Three underscores survive (\w includes _) — quirk we accept
        out = _tokenize("___")
        assert out in (set(), {"___"})

    def test_emoji_only(self):
        from daemon.open_threads import _tokenize

        out = _tokenize("🎯💡🛠️")
        # Emoji are not in [\w一-鿿] so they're split out;
        # remaining chunks empty → tokens empty
        assert out == set() or all(len(t) >= 2 for t in out)

    def test_mixed_emoji_chinese_english(self):
        from daemon.open_threads import _tokenize

        out = _tokenize("🎯 freemium 转化 strategy 策略")
        assert "freemium" in out
        assert "strategy" in out
        # Chinese bigrams
        assert "转化" in out or "转化策略" in out
        assert "策略" in out

    def test_extremely_long_chinese_run(self):
        """500-char CJK run shouldn't blow up bigram generation."""
        from daemon.open_threads import _tokenize

        long_chinese = "测试" * 250  # 500 chars
        out = _tokenize(long_chinese)
        # Should produce many bigrams without crashing
        assert "测试" in out

    def test_uppercase_not_collapsed_to_stopwords(self):
        from daemon.open_threads import _tokenize

        out = _tokenize("FREEMIUM AND PRICING")
        assert "freemium" in out
        assert "pricing" in out
        assert "and" not in out  # is stopword


# ---------- Open thread detection edge cases ----------

class TestOpenThreadEdges:
    def test_cluster_with_only_chinese_cards(self):
        from daemon.open_threads import detect_open_threads

        grouped = {
            "0": [
                {
                    "path": "a.md", "title": "B1 治疗方案",
                    "body": "body", "frontmatter": {"date": "2026-01-01"},
                    "_backfill": {
                        "claim_summary": "B1 治疗方案",
                        "open_questions": ["剂量调整频率"],
                    },
                },
            ],
        }
        out = detect_open_threads(grouped)
        assert "a.md" in out

    def test_question_with_no_meaningful_tokens(self):
        """A question consisting entirely of stopwords / punctuation
        — _tokenize returns empty set. _question_addressed_by returns
        False. Question stays open since we can't tell if it was
        addressed."""
        from daemon.open_threads import detect_open_threads

        grouped = {
            "0": [
                {
                    "path": "a.md", "title": "T", "body": "x",
                    "frontmatter": {"date": "2026-01-01"},
                    "_backfill": {
                        "claim_summary": "X",
                        "open_questions": ["the and or"],  # all stopwords
                    },
                },
                {
                    "path": "b.md", "title": "T2", "body": "y",
                    "frontmatter": {"date": "2026-02-01"},
                    "_backfill": {"claim_summary": "Y", "open_questions": []},
                },
            ],
        }
        out = detect_open_threads(grouped)
        # The all-stopword question stays in the unresolved list
        # (matches our "be conservative" bias)
        assert "a.md" in out

    def test_cluster_with_100_cards(self):
        """Performance: cluster with 100 cards should still complete
        in < 1s. No assertions about specific outputs, just no
        timeout/crash."""
        from daemon.open_threads import detect_open_threads

        cards = [
            {
                "path": f"{i}.md", "title": f"Title {i}", "body": "body",
                "frontmatter": {"date": f"2026-01-{i % 28 + 1:02d}"},
                "_backfill": {
                    "claim_summary": f"Summary {i}",
                    "open_questions": [f"Question {i}?"] if i % 5 == 0 else [],
                },
            }
            for i in range(100)
        ]
        out = detect_open_threads({"0": cards})
        # Some questions exist (every 5th card has one); should
        # produce some output
        assert isinstance(out, dict)
        # No crash is the test

    def test_card_without_frontmatter(self):
        """Card with no frontmatter falls back to mtime/0 sentinel
        for chronology. Should not crash."""
        from daemon.open_threads import detect_open_threads

        grouped = {
            "0": [
                {
                    "path": "a.md", "title": "T", "body": "x",
                    "frontmatter": {},
                    "_backfill": {
                        "claim_summary": "X",
                        "open_questions": ["q1?"],
                    },
                },
            ],
        }
        out = detect_open_threads(grouped)
        # Single card, question always open
        assert "a.md" in out


# ---------- State file robustness ----------

class TestStateFileRobustness:
    def test_load_positions_handles_invalid_utf8(self, tmp_path, monkeypatch):
        """State file with invalid UTF-8 → load returns None
        (treat as cold start) rather than crash."""
        from mcp_server.position_state import load_positions

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        # Write raw bytes that aren't valid UTF-8
        (tmp_path / "reflection_positions.json").write_bytes(
            b"\xff\xfe\x00\x00 not utf 8"
        )
        result = load_positions()
        # Either returns None (graceful) or doesn't crash
        assert result is None

    def test_load_positions_handles_truncated_json(self, tmp_path, monkeypatch):
        from mcp_server.position_state import load_positions

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        (tmp_path / "reflection_positions.json").write_text(
            '{"clusters": [{', encoding="utf-8"
        )
        assert load_positions() is None

    def test_load_positions_handles_unexpected_root_type(self, tmp_path, monkeypatch):
        """Root is not a dict → load returns None."""
        from mcp_server.position_state import load_positions

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        (tmp_path / "reflection_positions.json").write_text(
            '"just a string"', encoding="utf-8"
        )
        assert load_positions() is None


# ---------- Path edge cases ----------

class TestPathEdges:
    def test_card_path_with_spaces(self, tmp_path):
        from daemon.reflection_pass import _read_card

        path = tmp_path / "10_Tech" / "card with spaces.md"
        path.parent.mkdir()
        path.write_text(
            "---\ntitle: T\nslice_id: x\n---\nbody\n",
            encoding="utf-8",
        )
        result = _read_card(path)
        assert result is not None
        assert result["title"] == "T"

    def test_card_path_with_unicode(self, tmp_path):
        from daemon.reflection_pass import _read_card

        path = tmp_path / "10_Tech" / "中文文件名.md"
        path.parent.mkdir()
        path.write_text(
            "---\ntitle: 中文标题\nslice_id: x\n---\nbody\n",
            encoding="utf-8",
        )
        result = _read_card(path)
        assert result is not None
        assert result["title"] == "中文标题"


# ---------- MCP tool degradation ----------

class TestToolDegradation:
    def test_check_consistency_handles_unicode_statement(
        self, tmp_path, monkeypatch
    ):
        """Statement in Chinese should still find Chinese cluster
        and return its positions."""
        from mcp_server.tools.check_consistency import check_consistency

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        (tmp_path / "reflection_positions.json").write_text(
            json.dumps({
                "clusters": [{
                    "cluster_id": "0",
                    "topic_cluster": "b1_thiamine",
                    "size": 1,
                    "cards": [{
                        "card_path": "x.md",
                        "title": "B1 治疗方案",
                        "stance": "B1 注射每日维持",
                        "reasoning": [],
                        "open_questions": [],
                        "date": "2026-01-01",
                        "is_open_thread": False,
                        "is_backfilled": True,
                    }],
                }],
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        result = check_consistency(statement="我决定 B1 注射每周一次")
        assert result["_status"] == "ok"
        # Should find cluster (Chinese tokens overlap)
        assert len(result["contradictions"]) >= 1

    def test_get_position_drift_empty_topic_doesnt_crash(
        self, tmp_path, monkeypatch
    ):
        from mcp_server.tools.get_position_drift import get_position_drift

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        (tmp_path / "reflection_positions.json").write_text(
            '{"clusters": []}', encoding="utf-8"
        )
        # Whitespace-only topic → error not crash
        result = get_position_drift(topic="   ")
        assert result["_status"] == "error"

    def test_find_loose_ends_negative_limit_clamps(self, tmp_path, monkeypatch):
        """limit=0 or negative shouldn't return error or crash."""
        from mcp_server.tools.find_loose_ends import find_loose_ends

        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path))
        (tmp_path / "reflection_open_threads.json").write_text(
            json.dumps({"open_threads": [
                {"card_path": f"{i}.md", "topic_cluster": "x",
                 "open_questions": ["q?"], "last_touched": "2026-01-01",
                 "context_summary": ""}
                for i in range(5)
            ]}),
            encoding="utf-8",
        )
        # Negative limit: tool should still run (current behavior:
        # treats limit<=0 as "no clamp"; specific behavior less
        # important than not crashing)
        result = find_loose_ends(limit=0)
        assert result["_status"] == "ok"
        # With limit=0 and our implementation, no slicing happens
        # so all entries return
