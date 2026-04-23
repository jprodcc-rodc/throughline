"""Tests for U27.4 — taxonomy growth CLI + detector.

Covers `throughline_cli.taxonomy`:

- `normalize_tag()`: the clustering key that collapses
  AI/Agent / ai/agents / AI_Agent / AI-Agent into one bucket.
- `detect_candidates()`: threshold enforcement, drift filtering,
  card_id dedup (P5), rejection-aware filtering, parent inference.
- `append_to_valid_x()`: surgical regex insert preserving existing
  comments + style of the shipped minimal seed.
- `action_add / action_reject / action_name_as_different`:
  filesystem side-effects (taxonomy.py edit, rejected.json update,
  history.jsonl append).
- `cmd_status` / `cmd_review` / `cmd_reject_unattended`: CLI wiring
  with mocked `input()` and captured `out()`.

Close the MVP U27 loop: synthetic observation log → detector →
review `a` action → taxonomy.py updated → re-run review sees nothing
because the tag is now in VALID_X_SET.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from throughline_cli import taxonomy as tax


# ------- normalize_tag -------

class TestNormalizeTag:
    @pytest.mark.parametrize("raw,expected", [
        ("AI/Agent", "ai/agent"),
        ("ai/agents", "ai/agent"),
        ("AI Agent", "ai/agent"),
        ("AI_Agent", "ai/agent"),
        ("AI-Agent", "ai/agent"),
        ("  AI/Agent  ", "ai/agent"),
        ("AI//Agent", "ai/agent"),
        ("/AI/Agent/", "ai/agent"),
        ("Climbing", "climbing"),
        ("mechanisms", "mechanism"),  # singular-fold
        ("AI", "ai"),                  # short acronym kept
        ("OS", "os"),                  # short acronym kept
        ("RAG", "rag"),                # 3-letter kept
        ("", ""),
    ])
    def test_cases(self, raw, expected):
        assert tax.normalize_tag(raw) == expected

    def test_none_is_empty(self):
        assert tax.normalize_tag(None) == ""


# ------- synthetic observation helpers -------

def _mkobs(card_id: str, title: str, primary_x: str,
            proposed: str, ts: datetime) -> dict:
    return {
        "ts": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "card_id": card_id,
        "title": title,
        "primary_x": primary_x,
        "proposed_x_ideal": proposed,
    }


BASE = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)


def _rows_for(tag: str, n: int, *, start_day: int = 0,
               span_days: int = 5, title_prefix: str = "Card") -> list:
    """Generate n synthetic drift observations for `tag` spread across
    span_days starting at BASE + start_day days."""
    rows = []
    for i in range(n):
        # Evenly distribute across span_days.
        day_offset = start_day + (i * span_days / max(1, n - 1)) if n > 1 else start_day
        ts = BASE + timedelta(days=day_offset)
        rows.append(_mkobs(
            card_id=f"{tag}-{i}",
            title=f"{title_prefix} {i}",
            primary_x="Misc",
            proposed=tag,
            ts=ts,
        ))
    return rows


# ------- detect_candidates -------

class TestDetectCandidates:
    def test_below_count_dropped(self):
        obs = _rows_for("AI/Agent", n=4, span_days=10)  # below 5
        cands = tax.detect_candidates(obs, valid_x=["Misc"])
        assert cands == []

    def test_below_day_span_dropped(self):
        obs = _rows_for("AI/Agent", n=8, span_days=1)  # same day
        cands = tax.detect_candidates(obs, valid_x=["Misc"])
        assert cands == []

    def test_passes_both_thresholds(self):
        obs = _rows_for("AI/Agent", n=8, span_days=11)
        cands = tax.detect_candidates(
            obs, valid_x=["Misc"],
            # window-loading happens in load_observations, not here
        )
        assert len(cands) == 1
        c = cands[0]
        assert c.tag == "AI/Agent"
        assert c.normalized == "ai/agent"
        assert c.count == 8
        assert c.day_span_days >= 3
        assert c.sample_titles[:3] == ["Card 0", "Card 1", "Card 2"]

    def test_no_drift_rows_excluded(self):
        """primary_x == proposed_x_ideal means perfect fit — not a
        growth signal."""
        rows = []
        for i in range(10):
            rows.append(_mkobs(
                card_id=f"c{i}", title=f"t{i}",
                primary_x="Tech", proposed="Tech",
                ts=BASE + timedelta(days=i),
            ))
        cands = tax.detect_candidates(rows, valid_x=["Tech", "Misc"])
        assert cands == []

    def test_valid_x_already_present_filtered(self):
        """If proposed_x_ideal is already in VALID_X_SET (maybe a
        casing variant), the signal is not growth — it's refiner choice
        disagreement, out of scope for U27."""
        obs = _rows_for("ai/agent", n=10, span_days=7)
        cands = tax.detect_candidates(obs, valid_x=["AI/Agent", "Misc"])
        assert cands == []

    def test_rejected_tags_filtered(self):
        obs = _rows_for("AI/Agent", n=10, span_days=7)
        cands = tax.detect_candidates(
            obs, valid_x=["Misc"],
            rejected_tags={"ai/agent"},
        )
        assert cands == []

    def test_card_id_dedup(self):
        """Same card_id refined twice counts once — P5 idempotency."""
        rows = []
        for i in range(10):
            rows.append(_mkobs(
                card_id=f"dup-{i}", title=f"t{i}",
                primary_x="Misc", proposed="AI/Agent",
                ts=BASE + timedelta(days=i),
            ))
        # Add duplicates of the first 5 card_ids.
        for i in range(5):
            rows.append(_mkobs(
                card_id=f"dup-{i}", title="repeat",
                primary_x="Misc", proposed="AI/Agent",
                ts=BASE + timedelta(days=i, hours=1),
            ))
        cands = tax.detect_candidates(rows, valid_x=["Misc"])
        assert len(cands) == 1
        assert cands[0].count == 10  # not 15

    def test_parent_exists_flag(self):
        obs = _rows_for("Tech/NewThing", n=6, span_days=10)
        cands = tax.detect_candidates(
            obs, valid_x=["Tech", "Misc"],
        )
        assert len(cands) == 1
        assert cands[0].parent_exists is True
        assert cands[0].parent == "Tech"

    def test_parent_does_not_exist(self):
        obs = _rows_for("Climbing", n=6, span_days=10)
        cands = tax.detect_candidates(obs, valid_x=["Misc"])
        assert len(cands) == 1
        assert cands[0].parent_exists is False
        assert cands[0].parent == "Climbing"

    def test_clustering_collapses_casing_variants(self):
        """AI/Agent + ai/agents + AI_Agent all cluster as one."""
        obs = []
        for form in ("AI/Agent", "ai/agents", "AI_Agent"):
            obs.extend(_rows_for(form, n=2, span_days=4))
        # 6 unique card_ids total, 4+ day span.
        cands = tax.detect_candidates(obs, valid_x=["Misc"])
        assert len(cands) == 1
        assert cands[0].count == 6

    def test_sort_by_count_desc(self):
        obs = []
        obs.extend(_rows_for("Climbing", n=6, span_days=10))
        obs.extend(_rows_for("AI/Agent", n=10, span_days=10))
        obs.extend(_rows_for("Baking", n=8, span_days=10))
        cands = tax.detect_candidates(obs, valid_x=["Misc"])
        assert [c.tag for c in cands] == ["AI/Agent", "Baking", "Climbing"]


# ------- load_observations -------

class TestLoadObservations:
    def test_missing_file_returns_empty(self, tmp_path):
        assert tax.load_observations(tmp_path / "nope.jsonl") == []

    def test_reads_jsonl(self, tmp_path):
        p = tmp_path / "obs.jsonl"
        now = datetime.now(timezone.utc)
        lines = [
            json.dumps({
                "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "card_id": f"c{i}", "title": "t",
                "primary_x": "Misc", "proposed_x_ideal": "AI/Agent",
            })
            for i in range(3)
        ]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        rows = tax.load_observations(p, window_days=30, now=now)
        assert len(rows) == 3

    def test_window_filters_old(self, tmp_path):
        p = tmp_path / "obs.jsonl"
        now = datetime(2026, 4, 24, 12, 0, 0, tzinfo=timezone.utc)
        old = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        fresh = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        p.write_text(
            json.dumps({"ts": old, "card_id": "old", "title": "t",
                        "primary_x": "M", "proposed_x_ideal": "X"}) + "\n"
            + json.dumps({"ts": fresh, "card_id": "new", "title": "t",
                           "primary_x": "M", "proposed_x_ideal": "X"}) + "\n",
            encoding="utf-8",
        )
        rows = tax.load_observations(p, window_days=14, now=now)
        assert len(rows) == 1
        assert rows[0]["card_id"] == "new"

    def test_skips_bad_lines(self, tmp_path):
        p = tmp_path / "obs.jsonl"
        now = datetime.now(timezone.utc)
        good = json.dumps({
            "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "card_id": "ok", "title": "t",
            "primary_x": "M", "proposed_x_ideal": "X",
        })
        p.write_text(good + "\n{not json}\n\n" + good + "\n",
                     encoding="utf-8")
        rows = tax.load_observations(p, window_days=30, now=now)
        assert len(rows) == 2


# ------- append_to_valid_x -------

def _minimal_module() -> str:
    return (
        '"""Seed."""\n'
        'from __future__ import annotations\n\n'
        'VALID_X_SET = {\n'
        '    "Tech",\n'
        '    "Creative",\n'
        '    "Health",\n'
        '    "Life",\n'
        '    "Misc",\n'
        '}\n\n'
        'VALID_Y_SET = {"y/Reference"}\n\n'
        'VALID_Z_SET = {"z/Node"}\n'
    )


class TestAppendToValidX:
    def test_inserts_new_tag(self, tmp_path):
        p = tmp_path / "taxonomy.py"
        p.write_text(_minimal_module(), encoding="utf-8")
        edited = tax.append_to_valid_x("AI/Agent", module_path=p)
        assert edited is True
        updated = p.read_text(encoding="utf-8")
        assert '"AI/Agent"' in updated
        # Extracted set should contain it.
        vals = tax._extract_valid_x(p)
        assert "AI/Agent" in vals
        assert "Tech" in vals  # existing preserved

    def test_noop_when_already_present(self, tmp_path):
        p = tmp_path / "taxonomy.py"
        p.write_text(_minimal_module(), encoding="utf-8")
        edited = tax.append_to_valid_x("Tech", module_path=p)
        assert edited is False
        # Exactly one occurrence still — regex did not double-add.
        assert p.read_text(encoding="utf-8").count('"Tech"') == 1

    def test_preserves_existing_entries(self, tmp_path):
        p = tmp_path / "taxonomy.py"
        p.write_text(_minimal_module(), encoding="utf-8")
        tax.append_to_valid_x("NewDomain", module_path=p)
        vals = tax._extract_valid_x(p)
        assert set(vals) == {"Tech", "Creative", "Health",
                              "Life", "Misc", "NewDomain"}

    def test_raises_when_literal_missing(self, tmp_path):
        p = tmp_path / "broken.py"
        p.write_text("# no valid_x_set here\n", encoding="utf-8")
        with pytest.raises(ValueError):
            tax.append_to_valid_x("Anything", module_path=p)

    def test_handles_commented_minimal_seed(self, tmp_path):
        """The shipped `taxonomy.minimal.py` has comments between each
        set entry. Inserter must not choke on those."""
        seed = REPO_ROOT / "config" / "taxonomy.minimal.py"
        if not seed.exists():
            pytest.skip("minimal seed not present")
        p = tmp_path / "taxonomy.py"
        p.write_text(seed.read_text(encoding="utf-8"), encoding="utf-8")
        edited = tax.append_to_valid_x("AI/Agent", module_path=p)
        assert edited is True
        vals = tax._extract_valid_x(p)
        assert "AI/Agent" in vals
        # Original 5 still there.
        for v in ("Tech", "Creative", "Health", "Life", "Misc"):
            assert v in vals


# ------- rejected.json -------

class TestRejected:
    def test_add_then_load(self, tmp_path):
        p = tmp_path / "rejected.json"
        tax.add_rejected_tag("ai/agent", path=p)
        tax.add_rejected_tag("tech/data", path=p)
        assert tax.load_rejected_tags(p) == {"ai/agent", "tech/data"}

    def test_idempotent(self, tmp_path):
        p = tmp_path / "rejected.json"
        tax.add_rejected_tag("ai/agent", path=p)
        tax.add_rejected_tag("ai/agent", path=p)
        assert tax.load_rejected_tags(p) == {"ai/agent"}
        # File still valid JSON.
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data["rejected_tags"] == ["ai/agent"]

    def test_missing_file_returns_empty(self, tmp_path):
        assert tax.load_rejected_tags(tmp_path / "nope.json") == set()


# ------- history log -------

class TestHistoryLog:
    def test_append(self, tmp_path):
        p = tmp_path / "history.jsonl"
        tax.record_history("add", "AI/Agent", path=p,
                            extra={"count": 8, "day_span_days": 11})
        tax.record_history("reject", "Garbage", path=p)
        lines = p.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 2
        rec = json.loads(lines[0])
        assert rec["action"] == "add"
        assert rec["tag"] == "AI/Agent"
        assert rec["count"] == 8


# ------- actions (high-level) -------

def _make_candidate(tag="AI/Agent", parent_exists=False, count=8,
                     days=11) -> tax.GrowthCandidate:
    return tax.GrowthCandidate(
        tag=tag,
        normalized=tax.normalize_tag(tag),
        parent=tag.split("/", 1)[0],
        parent_exists=parent_exists,
        count=count,
        day_span_days=days,
        sample_titles=["a", "b", "c"],
    )


class TestActions:
    def test_add(self, tmp_path):
        module = tmp_path / "taxonomy.py"
        module.write_text(_minimal_module(), encoding="utf-8")
        history = tmp_path / "history.jsonl"
        cand = _make_candidate("AI/Agent")
        edited = tax.action_add(cand, module_path=module, history=history)
        assert edited is True
        assert "AI/Agent" in tax._extract_valid_x(module)
        rec = json.loads(history.read_text(encoding="utf-8").splitlines()[0])
        assert rec["action"] == "add"

    def test_reject(self, tmp_path):
        rejected = tmp_path / "rejected.json"
        history = tmp_path / "history.jsonl"
        cand = _make_candidate("AI/Agent")
        tax.action_reject(cand, rejected=rejected, history=history)
        assert tax.load_rejected_tags(rejected) == {"ai/agent"}
        assert history.exists()

    def test_name_as_different(self, tmp_path):
        module = tmp_path / "taxonomy.py"
        module.write_text(_minimal_module(), encoding="utf-8")
        rejected = tmp_path / "rejected.json"
        history = tmp_path / "history.jsonl"
        cand = _make_candidate("AI/Agent")
        edited = tax.action_name_as_different(
            cand, preferred_tag="Tech/AI-Agent",
            module_path=module, rejected=rejected, history=history,
        )
        assert edited is True
        assert "Tech/AI-Agent" in tax._extract_valid_x(module)
        # Original proposal is blocked from resurfacing.
        assert tax.load_rejected_tags(rejected) == {"ai/agent"}


# ------- end-to-end loop (the whole point of U27) -------

class TestEndToEndLoop:
    def test_observe_then_add_then_no_candidate(self, tmp_path, monkeypatch):
        """Ship the round-trip: synthetic log → candidate → add action →
        tag is now in VALID_X_SET → next review sees nothing."""
        # Start with a minimal taxonomy file under tmp.
        module = tmp_path / "taxonomy.py"
        module.write_text(_minimal_module(), encoding="utf-8")
        history = tmp_path / "history.jsonl"

        obs = _rows_for("AI/Agent", n=8, span_days=11)
        valid_x_before = tax._extract_valid_x(module)
        assert "AI/Agent" not in valid_x_before

        cands = tax.detect_candidates(obs, valid_x=valid_x_before)
        assert len(cands) == 1

        # User picks Add.
        tax.action_add(cands[0], module_path=module, history=history)

        # Detector re-run sees the tag is now in VALID_X_SET → no
        # candidate surfaces.
        valid_x_after = tax._extract_valid_x(module)
        assert "AI/Agent" in valid_x_after
        cands_after = tax.detect_candidates(obs, valid_x=valid_x_after)
        assert cands_after == []

    def test_observe_then_reject_filters_forever(self, tmp_path):
        rejected = tmp_path / "rejected.json"
        history = tmp_path / "history.jsonl"
        obs = _rows_for("AI/Agent", n=8, span_days=11)

        cands = tax.detect_candidates(obs, valid_x=["Misc"])
        tax.action_reject(cands[0], rejected=rejected, history=history)

        # Next run with rejected set provided — candidate gone.
        cands2 = tax.detect_candidates(
            obs, valid_x=["Misc"],
            rejected_tags=tax.load_rejected_tags(rejected),
        )
        assert cands2 == []


# ------- CLI: cmd_review with mocked input -------

class TestCmdReview:
    def test_add_then_skip(self, tmp_path, monkeypatch):
        # Redirect state + config paths via env + monkeypatch so cmd_*
        # doesn't touch the real filesystem.
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        fake_config = tmp_path / "config"
        fake_config.mkdir()
        (fake_config / "taxonomy.py").write_text(_minimal_module(),
                                                   encoding="utf-8")
        monkeypatch.setattr(tax, "REPO_ROOT", tmp_path, raising=False)

        # Seed observations.
        obs_path = tmp_path / "state" / "taxonomy_observations.jsonl"
        obs_path.parent.mkdir(parents=True)
        now = datetime.now(timezone.utc)
        lines = []
        for i in range(8):
            rec = _mkobs(
                card_id=f"c{i}", title=f"AI card {i}",
                primary_x="Misc", proposed="AI/Agent",
                ts=now - timedelta(days=i),
            )
            lines.append(json.dumps(rec))
        # Add 6 Climbing drift rows too.
        for i in range(6):
            rec = _mkobs(
                card_id=f"cl{i}", title=f"Climb card {i}",
                primary_x="Misc", proposed="Climbing",
                ts=now - timedelta(days=i),
            )
            lines.append(json.dumps(rec))
        obs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        captured = []
        # Answer 'a' for first, 's' for second.
        answers = iter(["a", "s"])

        def fake_reader(_label):
            return next(answers)

        rc = tax.cmd_review(reader=fake_reader, out=captured.append)
        assert rc == 0
        out_text = "\n".join(captured)
        assert "Added" in out_text
        assert "Skipped" in out_text

        # AI/Agent should now be in VALID_X_SET; Climbing should not.
        vals = tax._extract_valid_x(fake_config / "taxonomy.py")
        assert "AI/Agent" in vals
        assert "Climbing" not in vals

    def test_quit_early(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        fake_config = tmp_path / "config"
        fake_config.mkdir()
        (fake_config / "taxonomy.py").write_text(_minimal_module(),
                                                   encoding="utf-8")
        monkeypatch.setattr(tax, "REPO_ROOT", tmp_path, raising=False)
        obs_path = tmp_path / "state" / "taxonomy_observations.jsonl"
        obs_path.parent.mkdir(parents=True)
        now = datetime.now(timezone.utc)
        lines = [json.dumps(_mkobs(f"c{i}", "t", "Misc", "AI/Agent",
                                     now - timedelta(days=i)))
                 for i in range(8)]
        obs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        captured = []
        answers = iter(["q"])
        rc = tax.cmd_review(reader=lambda _l: next(answers),
                             out=captured.append)
        assert rc == 0
        # Should NOT have edited the file.
        vals = tax._extract_valid_x(fake_config / "taxonomy.py")
        assert "AI/Agent" not in vals

    def test_reject_blocks_resurface(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        fake_config = tmp_path / "config"
        fake_config.mkdir()
        (fake_config / "taxonomy.py").write_text(_minimal_module(),
                                                   encoding="utf-8")
        monkeypatch.setattr(tax, "REPO_ROOT", tmp_path, raising=False)
        obs_path = tmp_path / "state" / "taxonomy_observations.jsonl"
        obs_path.parent.mkdir(parents=True)
        now = datetime.now(timezone.utc)
        lines = [json.dumps(_mkobs(f"c{i}", "t", "Misc", "Garbage/Tag",
                                     now - timedelta(days=i)))
                 for i in range(8)]
        obs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # First run: reject.
        rc = tax.cmd_review(reader=lambda _l: "r", out=lambda _s: None)
        assert rc == 0
        assert (fake_config / "taxonomy_rejected.json").exists()
        # Second run: nothing to review.
        captured = []
        rc = tax.cmd_review(reader=lambda _l: "?",  # unreachable
                             out=captured.append)
        assert rc == 0
        assert any("No growth candidates" in s for s in captured)


# ------- CLI: cmd_status -------

class TestCmdStatus:
    def test_prints_valid_x_and_candidates(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        fake_config = tmp_path / "config"
        fake_config.mkdir()
        (fake_config / "taxonomy.py").write_text(_minimal_module(),
                                                   encoding="utf-8")
        monkeypatch.setattr(tax, "REPO_ROOT", tmp_path, raising=False)

        obs_path = tmp_path / "state" / "taxonomy_observations.jsonl"
        obs_path.parent.mkdir(parents=True)
        now = datetime.now(timezone.utc)
        lines = [json.dumps(_mkobs(f"c{i}", f"t{i}", "Misc", "AI/Agent",
                                     now - timedelta(days=i)))
                 for i in range(6)]
        obs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        captured = []
        rc = tax.cmd_status(out=captured.append)
        assert rc == 0
        out = "\n".join(captured)
        assert "VALID_X_SET" in out
        assert "Tech" in out
        assert "AI/Agent" in out


# ------- CLI: cmd_reject_unattended -------

class TestCmdRejectUnattended:
    def test_writes_normalized(self, tmp_path, monkeypatch):
        fake_config = tmp_path / "config"
        fake_config.mkdir()
        monkeypatch.setenv("THROUGHLINE_STATE_DIR", str(tmp_path / "state"))
        monkeypatch.setattr(tax, "REPO_ROOT", tmp_path, raising=False)
        rc = tax.cmd_reject_unattended("AI_Agent", out=lambda _s: None)
        assert rc == 0
        data = json.loads((fake_config / "taxonomy_rejected.json").read_text(
            encoding="utf-8"))
        assert "ai/agent" in data["rejected_tags"]

    def test_rejects_empty_tag(self):
        rc = tax.cmd_reject_unattended("   ", out=lambda _s: None)
        assert rc == 2


# ------- main() dispatcher -------

class TestMainDispatcher:
    def test_help(self, capsys):
        rc = tax.main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "taxonomy" in out
        assert "review" in out

    def test_unknown_subcommand(self, capsys):
        rc = tax.main(["junk"])
        assert rc == 2

    def test_reject_requires_tag(self, capsys):
        rc = tax.main(["reject"])
        assert rc == 2
