"""Tests for U2 ChatGPT export adapter.

Covers:
- mapping-tree walk: single-branch (linear) and multi-branch (regenerate)
  cases, picking children[-1] at each fork.
- Content-type extraction: text / code / multimodal_text / image_asset /
  skipped metadata (model_editable_context, tether_quote, etc.)
- Role normalisation: user / assistant / tool / system-None.
- UNIX-timestamp `create_time` float parsing into calendar date.
- Title / conv_id extraction with sensible fallbacks.
- JSON-array and JSON-object input shapes; empty/malformed input.
- File discovery: .json file / ZIP / directory.
- Dry-run does NOT write; real run writes + manifest; --limit caps
  scanned count.
"""
from __future__ import annotations

import json
import sys
import zipfile
from datetime import date, datetime
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli.adapters import chatgpt_export


# ---------- synthetic mapping-tree fixtures ----------

def _linear_mapping(conv_id: str,
                    *turns: tuple[str, str]) -> dict:
    """Build a linear ChatGPT mapping tree: root -> system -> user -> assistant -> ...

    turns = [("user", "hi"), ("assistant", "hey"), ...]
    """
    nodes: dict[str, dict] = {}
    root_id = "root-" + conv_id
    nodes[root_id] = {"id": root_id, "parent": None, "children": [],
                      "message": None}
    prev_id = root_id
    for i, (role, text) in enumerate(turns):
        nid = f"node-{conv_id}-{i}"
        nodes[nid] = {
            "id": nid, "parent": prev_id, "children": [],
            "message": {
                "author": {"role": role},
                "content": {"content_type": "text", "parts": [text]},
                "create_time": 1_700_000_000 + i,
            },
        }
        nodes[prev_id]["children"].append(nid)
        prev_id = nid
    return nodes


def _build_conv(conv_id: str, title: str,
                create_ts: float,
                *turns: tuple[str, str]) -> dict:
    return {
        "id": conv_id,
        "title": title,
        "create_time": create_ts,
        "update_time": create_ts + 60,
        "mapping": _linear_mapping(conv_id, *turns),
    }


def _sample_convs() -> list[dict]:
    # Unix timestamps: 2024-03-15 ≈ 1710489600, 2024-04-02 ≈ 1712016000
    return [
        _build_conv(
            "conv-001", "MPS setup",
            1710489600,
            ("user", "How do I enable MPS on M2?"),
            ("assistant", "Use torch.device('mps')."),
            ("user", "And fallback?"),
            ("assistant", "PYTORCH_ENABLE_MPS_FALLBACK=1."),
        ),
        _build_conv(
            "conv-002", "PARA notes",
            1712016000,
            ("user", "Explain PARA."),
            ("assistant", "Projects, Areas, Resources, Archive."),
        ),
    ]


def _branched_conv() -> dict:
    """One conversation with an edit/regenerate branch.

    Structure (root -> u1 -> a1_old AND a1_new (children[-1]) -> u2 -> a2)

    Walk should take children[-1] at the fork, so a1_old gets skipped
    and a1_new + u2 + a2 appear.
    """
    return {
        "id": "conv-branched",
        "title": "Branched",
        "create_time": 1720000000,
        "mapping": {
            "root": {"id": "root", "parent": None,
                     "children": ["u1"], "message": None},
            "u1": {"id": "u1", "parent": "root", "children": ["a1_old", "a1_new"],
                   "message": {"author": {"role": "user"},
                               "content": {"content_type": "text",
                                           "parts": ["first question"]}}},
            "a1_old": {"id": "a1_old", "parent": "u1", "children": [],
                       "message": {"author": {"role": "assistant"},
                                   "content": {"content_type": "text",
                                               "parts": ["old answer"]}}},
            "a1_new": {"id": "a1_new", "parent": "u1", "children": ["u2"],
                       "message": {"author": {"role": "assistant"},
                                   "content": {"content_type": "text",
                                               "parts": ["new answer"]}}},
            "u2": {"id": "u2", "parent": "a1_new", "children": ["a2"],
                   "message": {"author": {"role": "user"},
                               "content": {"content_type": "text",
                                           "parts": ["follow-up"]}}},
            "a2": {"id": "a2", "parent": "u2", "children": [],
                   "message": {"author": {"role": "assistant"},
                               "content": {"content_type": "text",
                                           "parts": ["final reply"]}}},
        },
    }


# ---------- mapping walk ----------

class TestMappingWalk:
    def test_linear_walk(self):
        conv = _sample_convs()[0]
        msgs = chatgpt_export._walk_mapping(conv)
        # 4 turns (system=None root is skipped because its message is None)
        assert len(msgs) == 4
        roles = [m["author"]["role"] for m in msgs]
        assert roles == ["user", "assistant", "user", "assistant"]

    def test_branched_walk_picks_most_recent(self):
        conv = _branched_conv()
        msgs = chatgpt_export._walk_mapping(conv)
        texts = [m["content"]["parts"][0] for m in msgs]
        assert "old answer" not in texts
        assert "new answer" in texts
        assert texts == ["first question", "new answer", "follow-up", "final reply"]

    def test_empty_mapping(self):
        assert chatgpt_export._walk_mapping({"mapping": {}}) == []
        assert chatgpt_export._walk_mapping({}) == []

    def test_mapping_without_root_picks_any_parentless(self):
        # No node has parent==None in mapping value; adapter should still
        # not crash. Synthetic pathological case.
        conv = {"mapping": {"a": {"id": "a", "parent": "z", "children": []}}}
        # parent 'z' doesn't exist in mapping but parent is not None —
        # adapter fallback picks first node, walks zero children.
        msgs = chatgpt_export._walk_mapping(conv)
        assert msgs == []  # no message field on that node

    def test_cycle_safe(self):
        """Malformed export with a cycle shouldn't hang."""
        mapping = {
            "a": {"id": "a", "parent": None, "children": ["b"],
                  "message": {"author": {"role": "user"},
                              "content": {"content_type": "text",
                                          "parts": ["x"]}}},
            "b": {"id": "b", "parent": "a", "children": ["a"],
                  "message": {"author": {"role": "assistant"},
                              "content": {"content_type": "text",
                                          "parts": ["y"]}}},
        }
        msgs = chatgpt_export._walk_mapping({"mapping": mapping})
        # Must terminate; exact length tolerates implementation detail.
        assert len(msgs) <= 3


# ---------- text extraction ----------

class TestExtractText:
    def _mk(self, content):
        return {"content": content}

    def test_text_parts(self):
        out = chatgpt_export._extract_text(self._mk({
            "content_type": "text",
            "parts": ["first", "second"],
        }))
        assert "first" in out and "second" in out

    def test_empty_parts(self):
        out = chatgpt_export._extract_text(self._mk({
            "content_type": "text",
            "parts": [""],
        }))
        assert out == ""

    def test_code_content_becomes_fenced(self):
        out = chatgpt_export._extract_text(self._mk({
            "content_type": "code",
            "language": "python",
            "text": "print('hi')",
        }))
        assert out.startswith("```python")
        assert "print('hi')" in out
        assert out.endswith("```")

    def test_multimodal_mix(self):
        out = chatgpt_export._extract_text(self._mk({
            "content_type": "multimodal_text",
            "parts": [
                "Look at this:",
                {"content_type": "image_asset_pointer",
                 "asset_pointer": "file-service://abc123"},
                "and comment.",
            ],
        }))
        assert "Look at this:" in out
        assert "[Image: file-service://abc123]" in out
        assert "and comment." in out

    def test_skipped_content_types_return_empty(self):
        for ct in ("model_editable_context", "user_editable_context",
                   "system_error", "tether_browsing_display",
                   "tether_quote"):
            out = chatgpt_export._extract_text(self._mk({
                "content_type": ct, "parts": ["should be ignored"],
            }))
            assert out == ""

    def test_old_text_field_fallback(self):
        out = chatgpt_export._extract_text(self._mk({
            "content_type": "some_future_type",
            "text": "plain text fallback",
        }))
        assert out == "plain text fallback"

    def test_missing_content(self):
        assert chatgpt_export._extract_text({}) == ""


# ---------- role normalisation ----------

class TestRoleNormalisation:
    def test_user_variants(self):
        assert chatgpt_export._normalise_role("user") == "user"
        assert chatgpt_export._normalise_role("USER") == "user"

    def test_assistant(self):
        assert chatgpt_export._normalise_role("assistant") == "assistant"

    def test_tool_becomes_assistant(self):
        """Tool output (code interpreter, browsing, DALL-E) is rendered
        the same way as assistant text in ChatGPT's UI."""
        assert chatgpt_export._normalise_role("tool") == "assistant"

    def test_system_dropped(self):
        """System messages (hidden instructions) are skipped."""
        assert chatgpt_export._normalise_role("system") is None

    def test_none_and_non_string(self):
        assert chatgpt_export._normalise_role(None) is None
        assert chatgpt_export._normalise_role(42) is None


# ---------- conversation-level extractors ----------

class TestConvExtractors:
    def test_date_from_unix_float(self):
        d = chatgpt_export._extract_date({"create_time": 1710489600.0})
        assert d == datetime.fromtimestamp(1710489600.0).date()

    def test_date_falls_back_to_today(self):
        d = chatgpt_export._extract_date({"create_time": None})
        assert d == date.today()

    def test_date_iso_string_also_works(self):
        d = chatgpt_export._extract_date({"create_time": "2024-05-01T10:00:00Z"})
        assert d == date(2024, 5, 1)

    def test_conv_id_priority(self):
        assert chatgpt_export._extract_conv_id({"id": "a", "uuid": "b"}) == "a"
        assert chatgpt_export._extract_conv_id({"uuid": "c"}) == "c"
        assert chatgpt_export._extract_conv_id({}) == "unknown"

    def test_title_priority(self):
        assert chatgpt_export._extract_title({"title": "T", "name": "N"}) == "T"
        assert chatgpt_export._extract_title({"name": "N"}) == "N"
        assert chatgpt_export._extract_title({}) == ""


# ---------- iter_conversations ----------

class TestIterConversations:
    def test_json_array_shape(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps(_sample_convs()), encoding="utf-8")
        got = list(chatgpt_export.iter_conversations(p))
        assert len(got) == 2

    def test_single_object_shape(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps(_sample_convs()[0]), encoding="utf-8")
        got = list(chatgpt_export.iter_conversations(p))
        assert len(got) == 1

    def test_empty_file(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text("", encoding="utf-8")
        assert list(chatgpt_export.iter_conversations(p)) == []

    def test_malformed_file(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text("{not: json}", encoding="utf-8")
        assert list(chatgpt_export.iter_conversations(p)) == []


# ---------- _find_json ----------

class TestFindJson:
    def test_direct_json(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text("[]", encoding="utf-8")
        assert chatgpt_export._find_json(p) == p

    def test_directory(self, tmp_path):
        d = tmp_path / "export"
        d.mkdir()
        (d / "conversations.json").write_text("[]", encoding="utf-8")
        assert chatgpt_export._find_json(d).name == "conversations.json"

    def test_zip(self, tmp_path):
        jsonp = tmp_path / "_inner.json"
        jsonp.write_text("[]", encoding="utf-8")
        zp = tmp_path / "export.zip"
        with zipfile.ZipFile(zp, "w") as zf:
            zf.write(jsonp, arcname="conversations.json")
            zf.writestr("chat.html", "<html></html>")
            zf.writestr("message_feedback.json", "{}")
            zf.writestr("user.json", "{}")
        extracted = chatgpt_export._find_json(zp)
        assert extracted.name == "conversations.json"
        assert extracted.read_text(encoding="utf-8") == "[]"

    def test_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            chatgpt_export._find_json(tmp_path / "nope.json")

    def test_empty_directory(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        with pytest.raises(FileNotFoundError):
            chatgpt_export._find_json(d)


# ---------- run() integration ----------

class TestRun:
    def test_run_writes_correct_number_of_files(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps(_sample_convs()), encoding="utf-8")
        out = tmp_path / "raw"
        summary = chatgpt_export.run(
            input_path=p,
            out_dir=out,
            import_tag="chatgpt-unit",
            state_dir=tmp_path / "state",
        )
        assert summary.scanned == 2
        assert summary.emitted == 2
        assert summary.source == "chatgpt"
        # Month-bucketed paths.
        md_files = list(out.rglob("*.md"))
        assert len(md_files) == 2

    def test_branched_conversation_emits_latest_branch(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps([_branched_conv()]), encoding="utf-8")
        out = tmp_path / "raw"
        chatgpt_export.run(
            input_path=p, out_dir=out,
            import_tag="chatgpt-branch",
            state_dir=tmp_path / "state",
        )
        md = next(out.rglob("*.md")).read_text(encoding="utf-8")
        assert "new answer" in md
        assert "old answer" not in md

    def test_frontmatter_platform_is_chatgpt(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps(_sample_convs()[:1]), encoding="utf-8")
        out = tmp_path / "raw"
        chatgpt_export.run(
            input_path=p, out_dir=out,
            import_tag="chatgpt-fm",
            state_dir=tmp_path / "state",
        )
        md = next(out.rglob("*.md")).read_text(encoding="utf-8")
        assert 'source_platform: "chatgpt"' in md
        assert 'import_source: "chatgpt-fm"' in md

    def test_dry_run_writes_nothing(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps(_sample_convs()), encoding="utf-8")
        out = tmp_path / "raw"
        summary = chatgpt_export.run(
            input_path=p, out_dir=out,
            dry_run=True,
            state_dir=tmp_path / "state",
        )
        assert summary.dry_run is True
        assert summary.emitted == 2
        assert summary.total_tokens_estimate > 0
        assert not out.exists() or not list(out.rglob("*.md"))

    def test_limit(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps(_sample_convs()), encoding="utf-8")
        summary = chatgpt_export.run(
            input_path=p,
            out_dir=tmp_path / "raw",
            dry_run=True,
            limit=1,
            state_dir=tmp_path / "state",
        )
        assert summary.scanned == 1

    def test_manifest(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps(_sample_convs()), encoding="utf-8")
        state = tmp_path / "state"
        chatgpt_export.run(
            input_path=p,
            out_dir=tmp_path / "raw",
            import_tag="chatgpt-man",
            state_dir=state,
        )
        manifest = state / "imports" / "chatgpt-man.json"
        assert manifest.exists()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["source"] == "chatgpt"
        assert data["emitted"] == 2
        assert set(data["conversation_ids"]) == {"conv-001", "conv-002"}


# ---------- CLI / dispatcher ----------

class TestCli:
    def test_help_usage(self, capsys):
        rc = chatgpt_export.cli([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "Usage" in err

    def test_end_to_end(self, tmp_path):
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps(_sample_convs()), encoding="utf-8")
        rc = chatgpt_export.cli([
            str(p), "--out", str(tmp_path / "raw"),
            "--tag", "chatgpt-cli",
        ])
        assert rc == 0


class TestDispatcher:
    def test_import_chatgpt_via_main(self, tmp_path):
        from throughline_cli.adapters import main as adapters_main
        p = tmp_path / "conversations.json"
        p.write_text(json.dumps(_sample_convs()), encoding="utf-8")
        rc = adapters_main([
            "chatgpt", str(p),
            "--out", str(tmp_path / "raw"),
            "--dry-run",
        ])
        assert rc == 0

    def test_help_mentions_chatgpt(self, capsys):
        from throughline_cli.adapters import main as adapters_main
        rc = adapters_main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "chatgpt" in out
        assert "claude" in out
