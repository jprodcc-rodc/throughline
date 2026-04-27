"""Phase 2 scaffolding tests for daemon.reflection_pass.

Verifies the Reflection Pass module's *structure* and the few
real-logic pieces (frontmatter parsing, vault walk, pass result
shape). Stages 3-8 are explicit stubs at this commit; their tests
will land alongside their real implementations per
docs/POSITION_METADATA_SCHEMA.md milestone order.

What these tests DO cover:
- Module import (`daemon.reflection_pass`) without a real vault
- `_parse_frontmatter` on well-formed / malformed / no-frontmatter
- `_read_card` on real fs reads + missing files
- `_walk_vault_for_cards` honors Johnny-Decimal layout
- `run_pass(dry_run=True)` against a synthetic mini-vault, no rag_server
- CLI entry parses --dry-run / --vault / --high-threshold

What these tests do NOT cover (gated on real impl):
- Stage 3 cluster name resolution (LLM)
- Stage 4 back-fill (LLM)
- Stages 5-7 detection logic
- Stage 8 atomic writeback
- Real `mcp_server.topic_clustering` clustering against a non-trivial
  vault — that's exercised by `private/clustering_experiment/run_from_json.py`
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------- Module import ----------

def test_reflection_pass_module_imports():
    """`daemon.reflection_pass` import works in minimal env."""
    import daemon.reflection_pass as rp

    assert hasattr(rp, "run_pass")
    assert hasattr(rp, "PassResult")
    assert callable(rp.run_pass)
    assert callable(rp.main)


def test_pass_result_shape():
    """PassResult exposes the expected counters."""
    from daemon.reflection_pass import PassResult

    r = PassResult(
        started_at="2026-04-28T00:00:00Z",
        finished_at="2026-04-28T00:01:00Z",
        cards_scanned=0,
        cards_reflectable=0,
        cards_excluded=0,
        cards_with_position_signal=0,
        cards_clustered=0,
        clusters_count=0,
        cluster_names_resolved=0,
        backfill_completed=0,
        open_threads_detected=0,
        contradictions_detected=0,
        drift_phases_computed=0,
        cards_updated=0,
        dry_run=True,
    )
    assert r.dry_run is True
    assert r.stages_completed == []
    assert r.stages_skipped == []
    assert r.errors == []
    # Phase 2 stage 1.5 counters present
    assert r.cards_reflectable == 0
    assert r.cards_excluded == 0


# ---------- Stage 1.5 reflectable filter ----------

class TestIsReflectableCard:
    """Per docs/POSITION_METADATA_SCHEMA.md § "Vault format addendum",
    the reflectable subset is cards with slice_id (refiner output) or
    non-empty managed_by (user-curated master profiles). Empty
    managed_by + no slice_id = system files / drafts; excluded."""

    def test_card_with_slice_id_is_reflectable(self):
        from daemon.reflection_pass import is_reflectable_card

        card = {"frontmatter": {"slice_id": "abc123", "title": "T"}}
        assert is_reflectable_card(card) is True

    def test_card_with_managed_by_is_reflectable(self):
        from daemon.reflection_pass import is_reflectable_card

        for mb in [
            "manual_profile_interview",
            "manual_master_dispensary",
            "manual_master_backup",
            "refine_thinker_daemon_v9",
        ]:
            card = {"frontmatter": {"managed_by": mb, "title": "T"}}
            assert is_reflectable_card(card) is True, f"{mb} should be reflectable"

    def test_card_with_empty_managed_by_and_no_slice_id_is_excluded(self):
        from daemon.reflection_pass import is_reflectable_card

        card = {"frontmatter": {"managed_by": "", "title": "Auto Refine Log"}}
        assert is_reflectable_card(card) is False

    def test_card_with_neither_field_is_excluded(self):
        from daemon.reflection_pass import is_reflectable_card

        # System file with title + tags but neither provenance marker
        card = {"frontmatter": {"title": "OpenWebUI Saved Index", "tags": ["system"]}}
        assert is_reflectable_card(card) is False

    def test_card_with_no_frontmatter_is_excluded(self):
        from daemon.reflection_pass import is_reflectable_card

        card = {"frontmatter": {}}
        assert is_reflectable_card(card) is False

    def test_card_with_none_frontmatter_is_excluded(self):
        from daemon.reflection_pass import is_reflectable_card

        # Defensive: missing 'frontmatter' key
        assert is_reflectable_card({}) is False

    def test_card_with_non_dict_frontmatter_is_excluded(self):
        from daemon.reflection_pass import is_reflectable_card

        # Defensive: malformed YAML can produce non-dict
        card = {"frontmatter": "not a dict"}
        assert is_reflectable_card(card) is False

    def test_managed_by_none_is_excluded(self):
        """yaml.safe_load can produce explicit None for empty fields."""
        from daemon.reflection_pass import is_reflectable_card

        card = {"frontmatter": {"managed_by": None, "title": "T"}}
        assert is_reflectable_card(card) is False

    def test_slice_id_empty_string_is_excluded(self):
        from daemon.reflection_pass import is_reflectable_card

        card = {"frontmatter": {"slice_id": "", "title": "T"}}
        assert is_reflectable_card(card) is False


# ---------- Frontmatter parsing ----------

class TestParseFrontmatter:
    def test_no_frontmatter_returns_full_text(self):
        from daemon.reflection_pass import _parse_frontmatter

        text = "# Just a heading\n\nBody"
        fm, body = _parse_frontmatter(text)
        assert fm == {}
        assert body == text

    def test_well_formed_frontmatter(self):
        from daemon.reflection_pass import _parse_frontmatter

        text = textwrap.dedent(
            """\
            ---
            title: My Card
            tags:
              - Health/Biohack
              - y/Mechanism
            ---
            # Body heading

            Body text.
            """
        )
        fm, body = _parse_frontmatter(text)
        assert fm["title"] == "My Card"
        assert fm["tags"] == ["Health/Biohack", "y/Mechanism"]
        assert body.startswith("# Body heading")

    def test_malformed_yaml_returns_empty(self):
        """Daemon should skip the card not crash; treat as no fm."""
        from daemon.reflection_pass import _parse_frontmatter

        text = "---\ntitle: [unclosed list\n---\nBody\n"
        fm, body = _parse_frontmatter(text)
        # Either the parse succeeds (yaml is permissive about some
        # bad input) or the function returns empty dict + full text.
        # Both are acceptable; the invariant is "doesn't raise".
        assert isinstance(fm, dict)
        assert isinstance(body, str)

    def test_missing_closing_fence(self):
        """Frontmatter without closing --- → treated as no fm."""
        from daemon.reflection_pass import _parse_frontmatter

        text = "---\ntitle: foo\nbody continues forever\nno closing"
        fm, body = _parse_frontmatter(text)
        assert fm == {}
        assert body == text

    def test_position_signal_passes_through(self):
        """Phase 2 schema: position_signal is the new field; ensure
        it round-trips through frontmatter parsing."""
        from daemon.reflection_pass import _parse_frontmatter

        text = textwrap.dedent(
            """\
            ---
            title: My Card
            position_signal:
              topic_cluster: pricing_strategy
              stance: against usage-based for early-stage SaaS
              reasoning:
                - LTV math is unpredictable
                - churn risk severe pre-PMF
              confidence: asserted
              emit_source: user_stated
            ---
            Body
            """
        )
        fm, _ = _parse_frontmatter(text)
        ps = fm["position_signal"]
        assert ps["topic_cluster"] == "pricing_strategy"
        assert ps["confidence"] == "asserted"
        assert len(ps["reasoning"]) == 2


# ---------- Vault walk ----------

class TestVaultWalk:
    def test_finds_cards_under_jd_dirs(self, tmp_path):
        from daemon.reflection_pass import _walk_vault_for_cards

        # Build a Johnny-Decimal-shaped mini-vault
        for d in ["10_Tech", "30_Biz_Ops", "70_AI/70.01_LLM_Brain"]:
            (tmp_path / d).mkdir(parents=True)
        (tmp_path / "10_Tech" / "card1.md").write_text("body", encoding="utf-8")
        (tmp_path / "30_Biz_Ops" / "card2.md").write_text("body", encoding="utf-8")
        (tmp_path / "70_AI/70.01_LLM_Brain" / "card3.md").write_text("body", encoding="utf-8")

        cards = _walk_vault_for_cards(tmp_path)
        names = sorted(p.name for p in cards)
        assert names == ["card1.md", "card2.md", "card3.md"]

    def test_skips_non_jd_dirs(self, tmp_path):
        from daemon.reflection_pass import _walk_vault_for_cards

        (tmp_path / "templates").mkdir()
        (tmp_path / "drafts").mkdir()
        (tmp_path / "templates" / "tpl.md").write_text("x", encoding="utf-8")
        (tmp_path / "drafts" / "d.md").write_text("x", encoding="utf-8")

        cards = _walk_vault_for_cards(tmp_path)
        assert cards == []

    def test_skips_readme_and_index(self, tmp_path):
        from daemon.reflection_pass import _walk_vault_for_cards

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "README.md").write_text("x", encoding="utf-8")
        (tmp_path / "10_Tech" / "index.md").write_text("x", encoding="utf-8")
        (tmp_path / "10_Tech" / "real_card.md").write_text("x", encoding="utf-8")

        cards = _walk_vault_for_cards(tmp_path)
        assert [p.name for p in cards] == ["real_card.md"]

    def test_missing_vault_returns_empty(self, tmp_path):
        from daemon.reflection_pass import _walk_vault_for_cards

        bogus = tmp_path / "does_not_exist"
        cards = _walk_vault_for_cards(bogus)
        assert cards == []


# ---------- _read_card ----------

class TestReadCard:
    def test_reads_card_with_frontmatter(self, tmp_path):
        from daemon.reflection_pass import _read_card

        path = tmp_path / "10_Tech" / "card.md"
        path.parent.mkdir()
        path.write_text(
            "---\ntitle: T\ntags: [a, b]\n---\nbody\n",
            encoding="utf-8",
        )
        c = _read_card(path)
        assert c is not None
        assert c["title"] == "T"
        assert c["tags"] == ["a", "b"]
        assert c["body"].startswith("body")
        assert c["position_signal"] is None

    def test_returns_none_on_missing_file(self, tmp_path):
        from daemon.reflection_pass import _read_card

        c = _read_card(tmp_path / "nope.md")
        assert c is None

    def test_falls_back_to_filename_for_title(self, tmp_path):
        from daemon.reflection_pass import _read_card

        path = tmp_path / "my_card_name.md"
        path.write_text("body only no frontmatter", encoding="utf-8")
        c = _read_card(path)
        assert c is not None
        assert c["title"] == "my_card_name"


# ---------- run_pass dry-run on synthetic vault ----------

class TestRunPassDryRun:
    def test_empty_vault_returns_error(self, tmp_path):
        from daemon.reflection_pass import run_pass

        result = run_pass(vault_root=tmp_path, dry_run=True)
        assert result.cards_scanned == 0
        assert result.errors  # non-empty
        assert "No cards" in result.errors[0]

    def test_dry_run_does_not_write_state(self, tmp_path):
        """dry_run skips state file persistence even if state path
        is given. Cards need slice_id to be reflectable per the
        2026-04-28 schema addendum filter."""
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "card.md").write_text(
            "---\ntitle: T\nslice_id: x\n---\nbody\n", encoding="utf-8"
        )

        state_file = tmp_path / "state.json"
        # Patch out the cluster stage to avoid network calls
        with patch("daemon.reflection_pass._stage_cluster", return_value={}):
            result = run_pass(
                vault_root=tmp_path,
                dry_run=True,
                state_file=state_file,
            )

        assert result.dry_run is True
        assert result.cards_scanned == 1
        assert result.cards_reflectable == 1
        # dry_run + state_file → state file should NOT be written
        assert not state_file.exists()

    def test_actual_run_writes_state(self, tmp_path):
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "card.md").write_text(
            "---\ntitle: T\nslice_id: x\n---\nbody\n", encoding="utf-8"
        )

        state_file = tmp_path / "state.json"
        with patch("daemon.reflection_pass._stage_cluster", return_value={}):
            result = run_pass(
                vault_root=tmp_path,
                dry_run=False,
                state_file=state_file,
            )

        assert state_file.exists()
        persisted = json.loads(state_file.read_text(encoding="utf-8"))
        assert persisted["cards_scanned"] == 1
        assert persisted["cards_reflectable"] == 1
        assert persisted["dry_run"] is False

    def test_position_signal_count(self, tmp_path):
        """cards_with_position_signal counts reflectable cards that
        actually have the new schema field. Cards in this test all
        have slice_id (so they're reflectable)."""
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "with_ps.md").write_text(
            "---\n"
            "title: T\n"
            "slice_id: aaa\n"
            "position_signal:\n"
            "  topic_cluster: foo\n"
            "  stance: yes\n"
            "  confidence: asserted\n"
            "---\nbody\n",
            encoding="utf-8",
        )
        (tmp_path / "10_Tech" / "no_ps.md").write_text(
            "---\ntitle: U\nslice_id: bbb\n---\nbody\n", encoding="utf-8"
        )

        with patch("daemon.reflection_pass._stage_cluster", return_value={}):
            result = run_pass(vault_root=tmp_path, dry_run=True)

        assert result.cards_scanned == 2
        assert result.cards_reflectable == 2
        assert result.cards_excluded == 0
        assert result.cards_with_position_signal == 1


class TestRunPassReflectableFilter:
    """End-to-end: stage 1.5 filter excludes system / draft cards
    from downstream stages."""

    def test_excluded_cards_dont_enter_clustering(self, tmp_path):
        """Cards with neither slice_id nor managed_by are filtered
        before stage 2; clustering should see only reflectable cards."""
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        # Reflectable: has slice_id
        (tmp_path / "10_Tech" / "refined.md").write_text(
            "---\ntitle: Refined\nslice_id: abc\n---\nbody\n",
            encoding="utf-8",
        )
        # Reflectable: has managed_by
        (tmp_path / "10_Tech" / "profile.md").write_text(
            "---\ntitle: Profile\nmanaged_by: manual_profile_interview\n---\nbody\n",
            encoding="utf-8",
        )
        # Excluded: system index file
        (tmp_path / "10_Tech" / "log.md").write_text(
            "---\ntitle: Auto Refine Log\nmanaged_by: ''\n---\nlog content\n",
            encoding="utf-8",
        )
        # Excluded: no provenance fields
        (tmp_path / "10_Tech" / "draft.md").write_text(
            "---\ntitle: Draft\n---\ndraft body\n",
            encoding="utf-8",
        )

        captured = []

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            for c in cards:
                captured.append(c["title"])
            return {}

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            result = run_pass(vault_root=tmp_path, dry_run=True)

        # Stats: 4 scanned, 2 reflectable, 2 excluded
        assert result.cards_scanned == 4
        assert result.cards_reflectable == 2
        assert result.cards_excluded == 2

        # Clustering only saw the 2 reflectable cards
        assert sorted(captured) == ["Profile", "Refined"]

    def test_all_excluded_returns_error(self, tmp_path):
        """If every card is filtered out, run_pass reports an error
        explaining why (vault has frontmatter but no provenance)."""
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "log1.md").write_text(
            "---\ntitle: System Log 1\n---\nbody\n",
            encoding="utf-8",
        )
        (tmp_path / "10_Tech" / "log2.md").write_text(
            "---\ntitle: System Log 2\nmanaged_by: ''\n---\nbody\n",
            encoding="utf-8",
        )

        result = run_pass(vault_root=tmp_path, dry_run=True)

        assert result.cards_scanned == 2
        assert result.cards_reflectable == 0
        assert result.cards_excluded == 2
        # Error message is honest about why
        assert any("reflectable" in err.lower() for err in result.errors)

    def test_filter_message_appears_in_stages_completed(self, tmp_path):
        """The CLI surface should explicitly show the filter ran +
        how many it kept vs excluded — not silently drop cards."""
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "good.md").write_text(
            "---\ntitle: G\nslice_id: a\n---\nbody\n", encoding="utf-8"
        )
        (tmp_path / "10_Tech" / "skip.md").write_text(
            "---\ntitle: S\n---\nbody\n", encoding="utf-8"
        )

        with patch("daemon.reflection_pass._stage_cluster", return_value={}):
            result = run_pass(vault_root=tmp_path, dry_run=True)

        # stages_completed should mention filter_reflectable
        filter_msgs = [s for s in result.stages_completed if "filter_reflectable" in s]
        assert len(filter_msgs) == 1
        # Message should include both kept + excluded counts
        assert "1 kept" in filter_msgs[0]
        assert "1 excluded" in filter_msgs[0]


# ---------- Stage stubs return correct skip markers ----------

def test_stub_stages_record_skips():
    """Stages 3-8 are stubs; verify they append the right messages
    to result.stages_skipped so the CLI surface is honest about
    what didn't run."""
    from daemon.reflection_pass import (
        PassResult,
        _stage_resolve_cluster_names,
        _stage_backfill_position_signal,
        _stage_detect_open_threads,
        _stage_detect_contradictions,
        _stage_compute_drift,
        _stage_writeback,
    )

    result = PassResult(
        started_at="x", finished_at="y",
        cards_scanned=0, cards_reflectable=0, cards_excluded=0,
        cards_with_position_signal=0,
        cards_clustered=0, clusters_count=0,
        cluster_names_resolved=0, backfill_completed=0,
        open_threads_detected=0, contradictions_detected=0,
        drift_phases_computed=0, cards_updated=0, dry_run=False,
    )
    _stage_resolve_cluster_names({}, result, dry_run=False)
    _stage_backfill_position_signal([], result, dry_run=False)
    _stage_detect_open_threads({}, result, dry_run=False)
    _stage_detect_contradictions({}, result, dry_run=False)
    _stage_compute_drift({}, result, dry_run=False)
    _stage_writeback([], result, dry_run=False)

    # All 6 stub stages should have recorded a skip message
    assert len(result.stages_skipped) == 6
    # Each skip message should contain "stub" or "dry-run" so the
    # CLI surface is unambiguous about what didn't run
    for msg in result.stages_skipped:
        assert "stub" in msg.lower() or "dry-run" in msg.lower()


def test_stub_writeback_dry_run_distinct_from_actual():
    """Stage 8 distinguishes dry-run from actual; both currently no-op
    but the messages differ so the CLI is honest."""
    from daemon.reflection_pass import PassResult, _stage_writeback

    def _empty(dry):
        return PassResult(
            started_at="", finished_at="",
            cards_scanned=0, cards_reflectable=0, cards_excluded=0,
            cards_with_position_signal=0,
            cards_clustered=0, clusters_count=0,
            cluster_names_resolved=0, backfill_completed=0,
            open_threads_detected=0, contradictions_detected=0,
            drift_phases_computed=0, cards_updated=0, dry_run=dry,
        )

    r1 = _empty(dry=True)
    _stage_writeback([], r1, dry_run=True)
    assert "dry-run" in r1.stages_skipped[0].lower()

    r2 = _empty(dry=False)
    _stage_writeback([], r2, dry_run=False)
    assert "stub" in r2.stages_skipped[0].lower()


# ---------- CLI ----------

class TestCLI:
    def test_main_with_no_vault_returns_error(self, tmp_path, monkeypatch, capsys):
        """No vault + bogus default → run_pass reports no cards."""
        from daemon.reflection_pass import main

        # Point default vault root to an empty tmp_path
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path / "empty"))
        rc = main([])
        out = capsys.readouterr().out
        assert rc == 1  # error path
        assert "No cards" in out or "errors" in out

    def test_main_with_dry_run_synthetic_vault(self, tmp_path, capsys):
        """--dry-run path produces a result without crashing on a
        small synthetic vault. Patches cluster stage to skip the
        rag_server network call. Card has slice_id so it survives
        the stage 1.5 reflectable filter."""
        from daemon.reflection_pass import main

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "c.md").write_text(
            "---\ntitle: T\nslice_id: x\n---\nbody\n", encoding="utf-8"
        )
        with patch("daemon.reflection_pass._stage_cluster", return_value={}):
            rc = main(["--dry-run", "--vault", str(tmp_path)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "dry_run:  True" in out
        assert "cards scanned:                1" in out
        assert "cards reflectable:            1" in out
        assert "cards excluded (logs/drafts): 0" in out

    def test_main_threshold_args_parse(self, tmp_path):
        """--high-threshold + --low-threshold parse and propagate."""
        from daemon.reflection_pass import main

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "c.md").write_text(
            "---\ntitle: T\nslice_id: x\n---\nbody\n", encoding="utf-8"
        )
        captured = {}

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            captured["high"] = high_threshold
            captured["low"] = low_threshold
            return {}

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            main([
                "--dry-run",
                "--vault", str(tmp_path),
                "--high-threshold", "0.65",
                "--low-threshold", "0.40",
            ])

        assert captured["high"] == 0.65
        assert captured["low"] == 0.40
