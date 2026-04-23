"""Tests for U13 taxonomy derivation.

Covers:
- prompts/en/taxonomy_deriver.{claude,generic}.md load + resolve.
- _read_title handles YAML frontmatter / H1 / filename fallback.
- sample_vault groups by top-level directory; capped at N per dir.
- sample_imports flattens + caps total titles.
- format_*_input render stable summary payloads (LLM input contract).
- render_taxonomy_module emits a syntactically valid Python module.
- call_deriver path (mocked) returns parsed JSON.
- main() end-to-end with mocked LLM writes a valid module.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import derive_taxonomy as dt
from throughline_cli import prompts as prompt_lib


# ---- prompt file availability ----

class TestPromptPair:
    def test_claude_variant_loads(self):
        body = prompt_lib.load_prompt("taxonomy_deriver", "main", "claude")
        assert "<task>" in body
        assert "x_domains" in body

    def test_generic_variant_loads(self):
        body = prompt_lib.load_prompt("taxonomy_deriver", "main", "generic")
        assert "## Task" in body
        assert "<task>" not in body
        assert "x_domains" in body

    def test_gpt_falls_back(self):
        body_gpt = prompt_lib.load_prompt("taxonomy_deriver", "main", "gpt")
        body_gen = prompt_lib.load_prompt("taxonomy_deriver", "main", "generic")
        assert body_gpt == body_gen


# ---- _read_title ----

class TestReadTitle:
    def test_yaml_frontmatter(self, tmp_path):
        p = tmp_path / "card.md"
        p.write_text(
            '---\ntitle: "Setting up MPS"\nsource: test\n---\n\nbody',
            encoding="utf-8",
        )
        assert dt._read_title(p) == "Setting up MPS"

    def test_h1_fallback(self, tmp_path):
        p = tmp_path / "card.md"
        p.write_text("# My H1 Title\n\nbody", encoding="utf-8")
        assert dt._read_title(p) == "My H1 Title"

    def test_filename_last_resort(self, tmp_path):
        p = tmp_path / "fallback_name.md"
        p.write_text("just prose, no title", encoding="utf-8")
        assert dt._read_title(p) == "fallback_name"

    def test_unreadable_returns_stem(self, tmp_path):
        # Point at a directory (read will fail) — function should
        # degrade to stem rather than raise.
        p = tmp_path / "directory_not_file"
        p.mkdir()
        assert dt._read_title(p) == "directory_not_file"


# ---- sample_vault ----

class TestSampleVault:
    def _build_vault(self, tmp_path):
        """Simulate a JD-style vault with a few dirs + cards."""
        (tmp_path / "10_Tech" / "ai").mkdir(parents=True)
        (tmp_path / "10_Tech" / "ai" / "llm_setup.md").write_text(
            '---\ntitle: "LLM Setup"\n---\n',
            encoding="utf-8",
        )
        (tmp_path / "10_Tech" / "ai" / "mps_on_mac.md").write_text(
            "# MPS on Mac\n", encoding="utf-8",
        )
        (tmp_path / "20_Health").mkdir()
        (tmp_path / "20_Health" / "sleep.md").write_text(
            "# Sleep hygiene\n", encoding="utf-8",
        )
        # Dotfile should be skipped.
        (tmp_path / ".hidden").mkdir()
        (tmp_path / ".hidden" / "secret.md").write_text("# skipme", encoding="utf-8")
        return tmp_path

    def test_groups_by_top_level_dir(self, tmp_path):
        v = self._build_vault(tmp_path)
        sample = dt.sample_vault(v)
        assert set(sample) == {"10_Tech", "20_Health"}

    def test_caps_samples_per_dir(self, tmp_path):
        v = tmp_path / "vault"
        (v / "Big").mkdir(parents=True)
        # 10 files — should cap at _SAMPLES_PER_DIR (5).
        for i in range(10):
            (v / "Big" / f"card{i:02d}.md").write_text(f"# T{i}", encoding="utf-8")
        sample = dt.sample_vault(v)
        assert len(sample["Big"]) == dt._SAMPLES_PER_DIR

    def test_dotfile_dirs_skipped(self, tmp_path):
        v = self._build_vault(tmp_path)
        sample = dt.sample_vault(v)
        assert ".hidden" not in sample

    def test_empty_vault_returns_empty(self, tmp_path):
        v = tmp_path / "empty"
        v.mkdir()
        assert dt.sample_vault(v) == {}


# ---- sample_imports ----

class TestSampleImports:
    def test_flat_cap(self, tmp_path):
        for i in range(50):
            (tmp_path / f"c{i:02d}.md").write_text(f"# card{i}", encoding="utf-8")
        titles = dt.sample_imports(tmp_path, cap=30)
        assert len(titles) == 30

    def test_empty(self, tmp_path):
        assert dt.sample_imports(tmp_path) == []


# ---- input formatting ----

class TestFormatInputs:
    def test_vault_includes_dir_and_titles(self):
        sample = {"Tech": ["A", "B"], "Health": ["C"]}
        out = dt.format_vault_input(sample)
        assert "### Tech" in out
        assert "- A" in out
        assert "### Health" in out
        assert "- C" in out

    def test_imports_counts_titles(self):
        titles = ["X", "Y", "Z"]
        out = dt.format_imports_input(titles)
        assert "3 freshly-refined cards" in out
        assert "- X" in out


# ---- render_taxonomy_module ----

class TestRenderTaxonomy:
    def test_produces_parseable_python(self):
        proposal = {
            "x_domains": ["AI/LLM", "Tech/Network"],
            "y_forms": ["y/SOP", "y/Decision"],
            "z_axes": ["z/Node"],
            "rationale": "User talks mostly about AI and networking.",
            "notes": ["One note."],
        }
        module_src = dt.render_taxonomy_module(proposal)
        tree = ast.parse(module_src)
        names = {n.targets[0].id for n in tree.body
                 if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
        assert {"VALID_X_SET", "VALID_Y_SET", "VALID_Z_SET"} <= names

    def test_includes_rationale_in_docstring(self):
        proposal = {
            "x_domains": ["A/B"], "y_forms": ["y/S"], "z_axes": ["z/N"],
            "rationale": "because reasons",
            "notes": [],
        }
        module_src = dt.render_taxonomy_module(proposal)
        assert "because reasons" in module_src

    def test_empty_notes_omitted_cleanly(self):
        proposal = {
            "x_domains": ["A/B"], "y_forms": ["y/S"], "z_axes": ["z/N"],
            "rationale": "r", "notes": [],
        }
        module_src = dt.render_taxonomy_module(proposal)
        assert "Notes:" not in module_src  # only present when notes non-empty


# ---- call_deriver with mocked LLM ----

class TestCallDeriver:
    def test_mocked_call(self, monkeypatch):
        fake_response = {
            "x_domains": ["AI/LLM", "Creative/Writing"],
            "y_forms": ["y/SOP"],
            "z_axes": ["z/Node"],
            "rationale": "Derived from input.",
            "notes": [],
        }
        with patch("throughline_cli.llm.call_chat",
                   return_value=json.dumps(fake_response)):
            got = dt.call_deriver("fake input", family="claude")
        assert got == fake_response


# ---- main() end-to-end with mocks ----

class TestMainE2E:
    def test_from_vault_writes_module(self, tmp_path, monkeypatch):
        v = tmp_path / "vault"
        (v / "Tech" / "ai").mkdir(parents=True)
        (v / "Tech" / "ai" / "card.md").write_text("# AI note", encoding="utf-8")

        out = tmp_path / "taxonomy.py"

        fake = json.dumps({
            "x_domains": ["Tech/AI"], "y_forms": ["y/SOP"],
            "z_axes": ["z/Node"], "rationale": "r", "notes": [],
        })
        with patch("throughline_cli.llm.call_chat", return_value=fake):
            rc = dt.main([
                "--from-vault", str(v),
                "--out", str(out),
                "--yes",
            ])
        assert rc == 0
        assert out.exists()
        src = out.read_text(encoding="utf-8")
        assert "Tech/AI" in src
        # Parseable.
        ast.parse(src)

    def test_from_imports_writes_module(self, tmp_path, monkeypatch):
        imports = tmp_path / "raw"
        imports.mkdir()
        for i in range(3):
            (imports / f"{i}.md").write_text(f"# Card {i}", encoding="utf-8")
        out = tmp_path / "taxonomy.py"
        fake = json.dumps({
            "x_domains": ["Life/Misc"], "y_forms": ["y/Reference"],
            "z_axes": ["z/Node"], "rationale": "r", "notes": [],
        })
        with patch("throughline_cli.llm.call_chat", return_value=fake):
            rc = dt.main([
                "--from-imports", str(imports),
                "--out", str(out),
                "--yes",
            ])
        assert rc == 0
        assert "Life/Misc" in out.read_text(encoding="utf-8")

    def test_missing_source_returns_2(self, tmp_path):
        rc = dt.main([
            "--from-vault", str(tmp_path / "nonexistent"),
            "--out", str(tmp_path / "taxonomy.py"),
            "--yes",
        ])
        assert rc == 2

    def test_llm_error_returns_1(self, tmp_path):
        v = tmp_path / "v"
        (v / "A").mkdir(parents=True)
        (v / "A" / "c.md").write_text("# x", encoding="utf-8")
        from throughline_cli.llm import LLMError
        with patch("throughline_cli.llm.call_chat",
                   side_effect=LLMError("no key")):
            rc = dt.main([
                "--from-vault", str(v),
                "--out", str(tmp_path / "t.py"),
                "--yes",
            ])
        assert rc == 1
