"""Tests for `python -m throughline_cli stats`."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import stats


# -----------------------------------------------------------------
# Frontmatter parsing
# -----------------------------------------------------------------

class TestExtractFrontmatter:
    def test_quoted_string(self):
        fm = stats._extract_frontmatter(
            '---\n'
            'title: "hello"\n'
            'primary_x: "Tech/PKM"\n'
            '---\n'
            '# body\n'
        )
        assert fm["title"] == "hello"
        assert fm["primary_x"] == "Tech/PKM"

    def test_unquoted_scalar(self):
        fm = stats._extract_frontmatter(
            '---\n'
            'date: 2026-04-25\n'
            'knowledge_identity: universal\n'
            '---\n'
        )
        assert fm["date"] == "2026-04-25"
        assert fm["knowledge_identity"] == "universal"

    def test_list(self):
        fm = stats._extract_frontmatter(
            '---\n'
            'tags: [AI/LLM, y/Decision, z/Node]\n'
            '---\n'
        )
        assert fm["tags"] == ["AI/LLM", "y/Decision", "z/Node"]

    def test_quoted_list(self):
        fm = stats._extract_frontmatter(
            '---\n'
            'tags: ["a", "b"]\n'
            '---\n'
        )
        assert fm["tags"] == ["a", "b"]

    def test_no_frontmatter(self):
        assert stats._extract_frontmatter("# plain markdown\n") == {}

    def test_empty_list(self):
        fm = stats._extract_frontmatter(
            '---\n'
            'tags: []\n'
            '---\n'
        )
        assert fm["tags"] == []


# -----------------------------------------------------------------
# Vault scan
# -----------------------------------------------------------------

def _write_card(dir_: Path, name: str, primary_x: str,
                  date: str = "2026-04-20",
                  body: Optional[str] = None):
    """Write a realistic-size refined card (>100 bytes so the
    stub-skip heuristic doesn't drop it)."""
    if body is None:
        body = (
            "# Scene & Pain Point\n"
            "Filler body long enough to pass the 100-byte stub guard.\n"
            "\n# Core Knowledge & First Principles\n"
            "More filler. More filler. More filler.\n"
        )
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / f"{name}.md").write_text(
        '---\n'
        f'title: "{name}"\n'
        f'primary_x: "{primary_x}"\n'
        f'date: {date}\n'
        '---\n\n'
        + body,
        encoding="utf-8",
    )


class TestScanVault:
    def test_missing_vault(self, tmp_path):
        result = stats.scan_vault(tmp_path / "never")
        assert result["vault_exists"] is False
        assert result["total_cards"] == 0

    def test_counts_cards_by_domain(self, tmp_path):
        _write_card(tmp_path, "c1", "Tech/PKM", date="2026-04-20")
        _write_card(tmp_path, "c2", "Tech/PKM", date="2026-04-21")
        _write_card(tmp_path, "c3", "Health/Biohack", date="2026-04-22")

        result = stats.scan_vault(tmp_path)
        assert result["total_cards"] == 3
        assert result["by_domain"]["Tech/PKM"] == 2
        assert result["by_domain"]["Health/Biohack"] == 1

    def test_skips_plain_markdown_without_frontmatter(self, tmp_path):
        _write_card(tmp_path, "card", "Tech/PKM")
        (tmp_path / "notes.md").write_text(
            "# just a note with no frontmatter\n\nContent goes here.",
            encoding="utf-8",
        )
        result = stats.scan_vault(tmp_path)
        assert result["total_cards"] == 1

    def test_skips_tiny_files(self, tmp_path):
        """Buffer stubs (< 100 bytes) shouldn't count as cards."""
        _write_card(tmp_path, "real", "Tech/PKM")
        (tmp_path / "stub.md").write_text("x", encoding="utf-8")
        result = stats.scan_vault(tmp_path)
        assert result["total_cards"] == 1

    def test_oldest_newest_largest(self, tmp_path):
        _write_card(tmp_path, "oldcard", "Tech", date="2024-01-01")
        _write_card(tmp_path, "newcard", "Tech", date="2026-04-25")
        _write_card(tmp_path, "bigcard", "Tech",
                     date="2025-06-15", body="x" * 5000)

        result = stats.scan_vault(tmp_path)
        assert result["oldest_title"] == "oldcard"
        assert result["oldest_date"] == "2024-01-01"
        assert result["newest_title"] == "newcard"
        assert result["newest_date"] == "2026-04-25"
        assert result["largest_title"] == "bigcard"
        assert result["largest_bytes"] > 4000

    def test_walks_subdirs(self, tmp_path):
        _write_card(tmp_path / "10_Tech", "c1", "Tech/PKM")
        _write_card(tmp_path / "20_Health" / "20.01_Biohack", "c2", "Health/Biohack")
        result = stats.scan_vault(tmp_path)
        assert result["total_cards"] == 2


# -----------------------------------------------------------------
# Taxonomy observations
# -----------------------------------------------------------------

class TestTaxonomyObsStats:
    def test_missing_file(self, tmp_path):
        result = stats.taxonomy_obs_stats(tmp_path / "nope.jsonl")
        assert result["exists"] is False
        assert result["total"] == 0

    def test_counts_drift(self, tmp_path):
        p = tmp_path / "obs.jsonl"
        lines = [
            {"primary_x": "Tech", "proposed_x_ideal": "Tech"},       # no drift
            {"primary_x": "Misc", "proposed_x_ideal": "AI/Agent"},   # drift
            {"primary_x": "Misc", "proposed_x_ideal": "AI/Agent"},   # drift (same tag)
            {"primary_x": "Misc", "proposed_x_ideal": "Climbing"},   # drift
        ]
        p.write_text(
            "\n".join(json.dumps(line) for line in lines) + "\n",
            encoding="utf-8",
        )
        result = stats.taxonomy_obs_stats(p)
        assert result["exists"] is True
        assert result["total"] == 4
        assert result["drift"] == 3
        # AI/Agent appeared twice — should lead the top_proposals list.
        tags = [r["tag"] for r in result["top_proposals"]]
        assert tags[0] == "AI/Agent"
        counts = {r["tag"]: r["count"] for r in result["top_proposals"]}
        assert counts["AI/Agent"] == 2
        assert counts["Climbing"] == 1

    def test_skips_bad_lines(self, tmp_path):
        p = tmp_path / "obs.jsonl"
        p.write_text(
            '{"primary_x": "Tech", "proposed_x_ideal": "AI/Agent"}\n'
            'not json\n'
            '\n'
            '{"primary_x": "Misc", "proposed_x_ideal": "Climbing"}\n',
            encoding="utf-8",
        )
        result = stats.taxonomy_obs_stats(p)
        assert result["total"] == 2
        assert result["drift"] == 2


# -----------------------------------------------------------------
# Lifetime cost
# -----------------------------------------------------------------

class TestLifetimeCost:
    def test_missing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "empty"))
        result = stats.lifetime_cost()
        assert result["exists"] is False
        assert result["total_usd"] == 0.0

    def test_aggregates(self, tmp_path, monkeypatch):
        state = tmp_path / "state"
        state.mkdir()
        (state / "cost_stats.json").write_text(
            json.dumps({
                "by_date": {
                    "2026-04-20": {"Refiner": {"calls": 10, "cost": 1.0}},
                    "2026-04-21": {"Refiner": {"calls": 5,  "cost": 0.5}},
                    "2026-04-22": {"Slicer":  {"calls": 2,  "cost": 0.1}},
                },
            }),
            encoding="utf-8",
        )
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state))
        result = stats.lifetime_cost()
        assert result["exists"] is True
        assert result["total_usd"] == pytest.approx(1.6, abs=1e-4)
        assert result["total_calls"] == 17


# -----------------------------------------------------------------
# CLI
# -----------------------------------------------------------------

class TestCli:
    def test_help(self, capsys):
        rc = stats.main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "stats" in out.lower()

    def test_unknown_arg(self, capsys):
        rc = stats.main(["--zztop"])
        assert rc == 2

    def test_human_output_integrates_all_sections(self, tmp_path, monkeypatch):
        # Vault with 2 cards.
        _write_card(tmp_path, "c1", "Tech/PKM", date="2026-04-20")
        _write_card(tmp_path, "c2", "Health/Biohack", date="2026-04-21")

        # Observations log with one drift.
        state = tmp_path / "state"
        state.mkdir()
        (state / "taxonomy_observations.jsonl").write_text(
            json.dumps({"primary_x": "Tech", "proposed_x_ideal": "AI/Agent"}) + "\n",
            encoding="utf-8",
        )
        (state / "cost_stats.json").write_text(
            json.dumps({"by_date": {"2026-04-21":
                                      {"Refiner": {"calls": 3, "cost": 0.42}}}}),
            encoding="utf-8",
        )

        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(state))

        captured: list[str] = []
        rc = stats.main([], out=captured.append)
        assert rc == 0
        text = " ".join(captured)
        # Vault section.
        assert "2 refined" in text
        assert "Tech/PKM" in text
        # Taxonomy section.
        assert "observation" in text
        assert "1 drift" in text
        # Cost section.
        assert "0.42" in text

    def test_json_output(self, tmp_path, monkeypatch, capsys):
        _write_card(tmp_path, "c1", "Tech/PKM")
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        monkeypatch.setenv("THROUGHLINE_STATE_DIR",
                            str(tmp_path / "nostate"))
        rc = stats.main(["--json"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["vault"]["total_cards"] == 1
        assert "taxonomy" in data
        assert "cost" in data
