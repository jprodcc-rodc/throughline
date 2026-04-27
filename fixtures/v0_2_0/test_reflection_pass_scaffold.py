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

# ---------- Stage 3 (resolve_cluster_names) — real impl ----------

class TestResolveClusterNames:
    """Stage 3 takes a Callable namer and produces canonical names
    per cluster, with persistence cache to avoid re-naming on
    subsequent passes when membership hasn't shifted."""

    def _empty_result(self):
        from daemon.reflection_pass import PassResult
        return PassResult(
            started_at="x", finished_at="y",
            cards_scanned=0, cards_reflectable=0, cards_excluded=0,
            cards_with_position_signal=0,
            cards_clustered=0, clusters_count=0,
            cluster_names_resolved=0, backfill_completed=0,
            open_threads_detected=0, contradictions_detected=0,
            drift_phases_computed=0, cards_updated=0, dry_run=False,
        )

    def test_no_clusters_skipped(self):
        from daemon.reflection_pass import _stage_resolve_cluster_names

        result = self._empty_result()
        names = _stage_resolve_cluster_names(
            {}, result, dry_run=False, namer=lambda titles: "x",
        )
        assert names == {}
        assert any("no clusters" in s for s in result.stages_skipped)

    def test_no_namer_skipped(self):
        """When namer is None (no API key configured), skip cleanly
        and report so in stages_skipped — don't crash."""
        from daemon.reflection_pass import _stage_resolve_cluster_names

        result = self._empty_result()
        grouped = {"0": [{"path": "a.md", "title": "A"}]}
        names = _stage_resolve_cluster_names(
            grouped, result, dry_run=False, namer=None,
        )
        assert names == {}
        assert any("no namer" in s.lower() for s in result.stages_skipped)

    def test_dry_run_skipped_even_with_namer(self):
        from daemon.reflection_pass import _stage_resolve_cluster_names

        result = self._empty_result()
        called = []

        def namer(titles):
            called.append(titles)
            return "should_not_run"

        grouped = {"0": [{"path": "a.md", "title": "A"}]}
        _stage_resolve_cluster_names(
            grouped, result, dry_run=True, namer=namer,
        )
        # Namer must NOT be invoked under dry_run
        assert called == []
        assert any("dry-run" in s for s in result.stages_skipped)

    def test_calls_namer_per_cluster(self):
        from daemon.reflection_pass import _stage_resolve_cluster_names

        result = self._empty_result()
        seen = []

        def namer(titles):
            seen.append(tuple(titles))
            return f"cluster_of_{len(titles)}"

        grouped = {
            "0": [
                {"path": "a.md", "title": "alpha"},
                {"path": "b.md", "title": "beta"},
            ],
            "1": [
                {"path": "c.md", "title": "gamma"},
            ],
        }
        names = _stage_resolve_cluster_names(
            grouped, result, dry_run=False, namer=namer,
        )

        assert names == {"0": "cluster_of_2", "1": "cluster_of_1"}
        assert ("alpha", "beta") in seen
        assert ("gamma",) in seen
        assert result.cluster_names_resolved == 2

    def test_caches_by_signature(self):
        """When prior pass named cluster with same membership, reuse
        the name without calling namer again."""
        from daemon.reflection_pass import _stage_resolve_cluster_names

        result = self._empty_result()
        called = []

        def namer(titles):
            called.append(titles)
            return "fresh_name"

        # Membership signature is "{cid}|{sorted_paths_csv}"
        prior = {
            "0|a.md,b.md": "cached_name",
        }
        grouped = {
            "0": [
                {"path": "a.md", "title": "alpha"},
                {"path": "b.md", "title": "beta"},
            ],
        }
        names = _stage_resolve_cluster_names(
            grouped, result, dry_run=False, namer=namer,
            cluster_names_state=prior,
        )

        assert names == {"0": "cached_name"}
        # No call: cache hit
        assert called == []

    def test_cache_invalidated_when_membership_changes(self):
        """If a prior cluster's signature shifts (path added/removed),
        cache miss → namer called fresh."""
        from daemon.reflection_pass import _stage_resolve_cluster_names

        result = self._empty_result()
        called = []
        def namer(titles):
            called.append(titles)
            return "fresh_name"

        # Old signature was {0, [a.md]}; new cluster has more cards
        prior = {"0|a.md": "stale_name"}
        grouped = {
            "0": [
                {"path": "a.md", "title": "alpha"},
                {"path": "new.md", "title": "new card"},  # membership changed
            ],
        }
        names = _stage_resolve_cluster_names(
            grouped, result, dry_run=False, namer=namer,
            cluster_names_state=prior,
        )
        assert names["0"] == "fresh_name"
        assert called  # namer was called

    def test_namer_failure_logged_other_clusters_continue(self):
        from daemon.reflection_pass import _stage_resolve_cluster_names

        result = self._empty_result()

        def namer(titles):
            if "broken" in titles[0]:
                raise RuntimeError("LLM 500")
            return "ok_name"

        grouped = {
            "0": [{"path": "a.md", "title": "broken card"}],
            "1": [{"path": "b.md", "title": "good card"}],
        }
        names = _stage_resolve_cluster_names(
            grouped, result, dry_run=False, namer=namer,
        )
        # Cluster 0 failed; cluster 1 succeeded
        assert names == {"1": "ok_name"}
        assert any("naming failed" in e for e in result.errors)
        assert result.cluster_names_resolved == 1
        # stage message is honest about counts
        msg = next(s for s in result.stages_completed if "resolve_cluster_names" in s)
        assert "1 named" in msg
        assert "1 failed" in msg

    def test_empty_titles_skipped(self):
        """Cluster whose titles are all empty/whitespace can't be
        named — skip gracefully without invoking namer."""
        from daemon.reflection_pass import _stage_resolve_cluster_names

        result = self._empty_result()
        called = []
        def namer(titles):
            called.append(titles)
            return "x"

        grouped = {
            "0": [{"path": "a.md", "title": ""}, {"path": "b.md", "title": "   "}],
        }
        names = _stage_resolve_cluster_names(
            grouped, result, dry_run=False, namer=namer,
        )
        assert names == {}
        assert called == []  # never invoked
        assert "1 failed" in next(
            s for s in result.stages_completed if "resolve_cluster_names" in s
        )


# ---------- run_pass passes namer through end-to-end ----------

class TestRunPassNamerIntegration:
    def test_namer_passed_through_to_stage_3(self, tmp_path):
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "card.md").write_text(
            "---\ntitle: T\nslice_id: x\n---\nbody\n", encoding="utf-8"
        )

        # Fake cluster + fake namer
        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            for c in cards:
                c["_cluster_id"] = 0
            result.cards_clustered = len(cards)
            result.clusters_count = 1
            return {"0": cards}

        called = []
        def namer(titles):
            called.append(titles)
            return "real_name"

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            result = run_pass(
                vault_root=tmp_path, dry_run=False, namer=namer,
                state_file=tmp_path / "state.json",
            )

        assert called  # namer was invoked
        assert result.cluster_names_resolved == 1

    def test_no_namer_means_stage_3_skipped(self, tmp_path):
        """Default behavior (no namer) = stage 3 skipped, but
        clustering still runs (so we know what would be named)."""
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "card.md").write_text(
            "---\ntitle: T\nslice_id: x\n---\nbody\n", encoding="utf-8"
        )

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            result.cards_clustered = 1
            result.clusters_count = 1
            return {"0": cards}

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            result = run_pass(vault_root=tmp_path, dry_run=True)

        assert result.cluster_names_resolved == 0
        assert any("no namer" in s.lower() for s in result.stages_skipped)

    def test_cluster_names_persisted_when_file_given(self, tmp_path):
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "card.md").write_text(
            "---\ntitle: T\nslice_id: abc\n---\nbody\n", encoding="utf-8"
        )

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            for c in cards:
                c["_cluster_id"] = 0
            result.cards_clustered = 1
            result.clusters_count = 1
            return {"0": cards}

        cluster_names_path = tmp_path / "cluster_names.json"

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            run_pass(
                vault_root=tmp_path, dry_run=False,
                namer=lambda titles: "topic_xyz",
                cluster_names_file=cluster_names_path,
                state_file=tmp_path / "state.json",
            )

        assert cluster_names_path.exists()
        persisted = json.loads(cluster_names_path.read_text(encoding="utf-8"))
        # Key is signature "0|<sorted_paths>", value is name
        assert any(v == "topic_xyz" for v in persisted.values())


# ---------- Stage 4 (back-fill) — real impl ----------

class TestBackfillStage:
    """Stage 4 takes a Callable extractor; fills card['_backfill']
    in-memory. Cache file dedupes by path|mtime."""

    def _empty_result(self):
        from daemon.reflection_pass import PassResult
        return PassResult(
            started_at="x", finished_at="y",
            cards_scanned=0, cards_reflectable=0, cards_excluded=0,
            cards_with_position_signal=0,
            cards_clustered=0, clusters_count=0,
            cluster_names_resolved=0, backfill_completed=0,
            open_threads_detected=0, contradictions_detected=0,
            drift_phases_computed=0, cards_updated=0, dry_run=False,
        )

    def test_no_eligible_cards_skipped(self):
        """All cards have position_signal already → nothing to do."""
        from daemon.reflection_pass import _stage_backfill_position_signal

        result = self._empty_result()
        cards = [{"path": "a.md", "title": "A", "body": "...",
                  "position_signal": {"stance": "x"}}]

        _stage_backfill_position_signal(
            cards, result, dry_run=False, extractor=lambda t, b: {}
        )
        assert any("nothing eligible" in s for s in result.stages_skipped)

    def test_no_extractor_skipped(self):
        from daemon.reflection_pass import _stage_backfill_position_signal

        result = self._empty_result()
        cards = [{"path": "a.md", "title": "A", "body": "...",
                  "position_signal": None}]

        _stage_backfill_position_signal(
            cards, result, dry_run=False, extractor=None
        )
        assert any("no extractor" in s.lower() for s in result.stages_skipped)

    def test_dry_run_does_not_invoke_extractor(self):
        from daemon.reflection_pass import _stage_backfill_position_signal

        result = self._empty_result()
        called = []
        def extractor(t, b):
            called.append((t, b))
            return {"claim_summary": "X", "open_questions": []}

        cards = [{"path": "a.md", "title": "A", "body": "body",
                  "position_signal": None}]
        _stage_backfill_position_signal(
            cards, result, dry_run=True, extractor=extractor,
        )
        assert called == []
        assert any("dry-run" in s for s in result.stages_skipped)

    def test_calls_extractor_per_eligible_card(self, tmp_path):
        from daemon.reflection_pass import _stage_backfill_position_signal

        # Real files so _file_signature can stat them
        f1 = tmp_path / "a.md"
        f1.write_text("body a", encoding="utf-8")
        f2 = tmp_path / "b.md"
        f2.write_text("body b", encoding="utf-8")

        result = self._empty_result()
        seen = []
        def extractor(t, b):
            seen.append((t, b))
            return {
                "claim_summary": f"summary of {t}",
                "open_questions": [f"q? for {t}"],
            }

        cards = [
            {"path": str(f1), "title": "A", "body": "body a",
             "position_signal": None},
            {"path": str(f2), "title": "B", "body": "body b",
             "position_signal": None},
        ]
        _stage_backfill_position_signal(
            cards, result, dry_run=False, extractor=extractor,
        )

        assert len(seen) == 2
        # Each card now has a _backfill key with the extracted essence
        assert cards[0]["_backfill"] == {
            "claim_summary": "summary of A",
            "open_questions": ["q? for A"],
        }
        assert cards[1]["_backfill"]["claim_summary"] == "summary of B"
        assert result.backfill_completed == 2

    def test_cache_hit_skips_extractor(self, tmp_path):
        from daemon.reflection_pass import (
            _stage_backfill_position_signal, _file_signature,
        )

        f1 = tmp_path / "a.md"
        f1.write_text("body", encoding="utf-8")
        sig = _file_signature(str(f1))
        prior = {sig: {"claim_summary": "cached", "open_questions": []}}

        result = self._empty_result()
        called = []
        def extractor(t, b):
            called.append((t, b))
            return {"claim_summary": "fresh", "open_questions": []}

        cards = [{"path": str(f1), "title": "A", "body": "body",
                  "position_signal": None}]
        _stage_backfill_position_signal(
            cards, result, dry_run=False, extractor=extractor,
            backfill_state=prior,
        )

        # Cache hit: extractor not called
        assert called == []
        assert cards[0]["_backfill"]["claim_summary"] == "cached"

    def test_cache_invalidated_when_mtime_changes(self, tmp_path):
        """If file mtime shifted (user edited card), prior cache
        signature won't match — extractor fires fresh."""
        import time
        from daemon.reflection_pass import _stage_backfill_position_signal

        f1 = tmp_path / "a.md"
        f1.write_text("body", encoding="utf-8")
        # Cache key uses CURRENT mtime; bake an OLD mtime into prior
        prior = {f"{f1}|0": {"claim_summary": "stale", "open_questions": []}}

        result = self._empty_result()
        called = []
        def extractor(t, b):
            called.append((t, b))
            return {"claim_summary": "fresh", "open_questions": []}

        cards = [{"path": str(f1), "title": "A", "body": "body",
                  "position_signal": None}]
        _stage_backfill_position_signal(
            cards, result, dry_run=False, extractor=extractor,
            backfill_state=prior,
        )

        assert called  # called fresh
        assert cards[0]["_backfill"]["claim_summary"] == "fresh"

    def test_extractor_failure_other_cards_continue(self, tmp_path):
        from daemon.reflection_pass import _stage_backfill_position_signal

        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("x", encoding="utf-8")
        f2.write_text("y", encoding="utf-8")

        result = self._empty_result()
        def extractor(t, b):
            if "broken" in t:
                raise RuntimeError("LLM 500")
            return {"claim_summary": "ok", "open_questions": []}

        cards = [
            {"path": str(f1), "title": "broken card", "body": "x",
             "position_signal": None},
            {"path": str(f2), "title": "good card", "body": "y",
             "position_signal": None},
        ]
        _stage_backfill_position_signal(
            cards, result, dry_run=False, extractor=extractor,
        )

        assert "_backfill" not in cards[0]
        assert cards[1]["_backfill"]["claim_summary"] == "ok"
        assert any("backfill failed" in e for e in result.errors)
        assert result.backfill_completed == 1

    def test_malformed_extractor_return_recorded_as_failure(self, tmp_path):
        """Defense: if extractor returns wrong shape, treat as
        failure not crash."""
        from daemon.reflection_pass import _stage_backfill_position_signal

        f1 = tmp_path / "a.md"
        f1.write_text("body", encoding="utf-8")

        result = self._empty_result()
        def extractor(t, b):
            return "not a dict"  # malformed

        cards = [{"path": str(f1), "title": "A", "body": "body",
                  "position_signal": None}]
        _stage_backfill_position_signal(
            cards, result, dry_run=False, extractor=extractor,
        )

        assert "_backfill" not in cards[0]
        assert any("malformed shape" in e for e in result.errors)
        assert result.backfill_completed == 0


# ---------- run_pass plumbing for back-fill ----------

class TestRunPassBackfillIntegration:
    def test_extractor_fires_when_passed(self, tmp_path):
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "card.md").write_text(
            "---\ntitle: T\nslice_id: x\n---\nbody content\n",
            encoding="utf-8",
        )

        called = []
        def extractor(t, b):
            called.append(t)
            return {"claim_summary": "X", "open_questions": []}

        with patch("daemon.reflection_pass._stage_cluster", return_value={}):
            result = run_pass(
                vault_root=tmp_path, dry_run=False,
                extractor=extractor,
                state_file=tmp_path / "state.json",
            )

        assert called == ["T"]
        assert result.backfill_completed == 1

    def test_backfill_state_persisted(self, tmp_path):
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "card.md").write_text(
            "---\ntitle: T\nslice_id: x\n---\nbody\n", encoding="utf-8"
        )

        backfill_path = tmp_path / "backfill.json"

        with patch("daemon.reflection_pass._stage_cluster", return_value={}):
            run_pass(
                vault_root=tmp_path, dry_run=False,
                extractor=lambda t, b: {
                    "claim_summary": "X", "open_questions": []
                },
                backfill_state_file=backfill_path,
                state_file=tmp_path / "state.json",
            )

        assert backfill_path.exists()
        persisted = json.loads(backfill_path.read_text(encoding="utf-8"))
        assert persisted  # non-empty
        # Some key contains the card path
        assert any("card.md" in k for k in persisted)


# ---------- Stage 8 (writeback preview) ----------

class TestStageWriteback:
    """Stage 8 is preview-only in this commit — never mutates vault
    files. The actual atomic frontmatter rewrite lands in a
    follow-up commit with --commit-writeback flag."""

    def test_preview_file_written_when_path_given(self, tmp_path):
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        (tmp_path / "10_Tech" / "card.md").write_text(
            "---\ntitle: T\nslice_id: x\n---\nbody\n", encoding="utf-8"
        )

        preview = tmp_path / "preview.json"

        # Simulate stage 4 producing a back-fill so stage 8 has
        # something to write into the preview.
        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            for c in cards:
                c["_cluster_id"] = 0
                c["_backfill"] = {
                    "claim_summary": "X stance",
                    "open_questions": ["q?"],
                }
            result.cards_clustered = len(cards)
            result.clusters_count = 1
            return {"0": cards}

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            run_pass(
                vault_root=tmp_path, dry_run=False,
                writeback_preview_file=preview,
                state_file=tmp_path / "state.json",
            )

        assert preview.exists()
        payload = json.loads(preview.read_text(encoding="utf-8"))
        assert "diffs" in payload
        # 1 card eligible, modified
        assert payload["cards_would_be_modified"] == 1
        diff = payload["diffs"][0]
        assert diff["card_path"].endswith("card.md")
        assert "position_signal" in diff["additions"]

    def test_no_vault_file_mutation(self, tmp_path):
        """Sanity: stage 8 does NOT touch the actual card file's
        contents in this commit, even when stages 3-5 produced
        in-memory mutations."""
        from daemon.reflection_pass import run_pass

        card_path = tmp_path / "10_Tech" / "card.md"
        card_path.parent.mkdir()
        original_contents = "---\ntitle: T\nslice_id: x\n---\nbody\n"
        card_path.write_text(original_contents, encoding="utf-8")

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            for c in cards:
                c["_cluster_id"] = 0
                c["_backfill"] = {
                    "claim_summary": "X",
                    "open_questions": ["q?"],
                }
            return {"0": cards}

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            run_pass(
                vault_root=tmp_path, dry_run=False,
                writeback_preview_file=tmp_path / "preview.json",
                state_file=tmp_path / "state.json",
            )

        # Card file content unchanged — preview-only commit
        assert card_path.read_text(encoding="utf-8") == original_contents


# ---------- Stage 6 (contradictions) — real impl ----------

class TestContradictionStage:
    """Stage 6 takes a Callable judge; produces per-cluster pair
    judgments. Cache by (path-pair + stance hash)."""

    def _empty_result(self):
        from daemon.reflection_pass import PassResult
        return PassResult(
            started_at="x", finished_at="y",
            cards_scanned=0, cards_reflectable=0, cards_excluded=0,
            cards_with_position_signal=0,
            cards_clustered=0, clusters_count=0,
            cluster_names_resolved=0, backfill_completed=0,
            open_threads_detected=0, contradictions_detected=0,
            drift_phases_computed=0, cards_updated=0, dry_run=False,
        )

    def test_no_clusters_skipped(self):
        from daemon.reflection_pass import _stage_detect_contradictions

        result = self._empty_result()
        out = _stage_detect_contradictions(
            {}, result, dry_run=False, judge=lambda e, l, t: {},
        )
        assert out == {}
        assert any("no clusters" in s for s in result.stages_skipped)

    def test_no_judge_skipped(self):
        from daemon.reflection_pass import _stage_detect_contradictions

        result = self._empty_result()
        grouped = {"0": [{"path": "a.md", "_backfill": {"claim_summary": "X"}}]}
        out = _stage_detect_contradictions(
            grouped, result, dry_run=False, judge=None,
        )
        assert out == {}
        assert any("no judge" in s.lower() for s in result.stages_skipped)

    def test_dry_run_skipped(self):
        from daemon.reflection_pass import _stage_detect_contradictions

        result = self._empty_result()
        called = []
        def judge(e, l, t):
            called.append(True)
            return {"is_contradiction": True, "kind": "direct_reversal", "reasoning_diff": ""}

        grouped = {
            "0": [
                {"path": "a.md", "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {"claim_summary": "S1", "reasoning": []}},
                {"path": "b.md", "frontmatter": {"date": "2026-02-01"},
                 "_backfill": {"claim_summary": "S2", "reasoning": []}},
            ]
        }
        _stage_detect_contradictions(
            grouped, result, dry_run=True, judge=judge,
        )
        assert called == []
        assert any("dry-run" in s for s in result.stages_skipped)

    def test_judges_pairs_in_chronological_order(self):
        from daemon.reflection_pass import _stage_detect_contradictions

        result = self._empty_result()
        seen = []
        def judge(early, late, topic):
            seen.append((early["stance"], late["stance"]))
            return {
                "is_contradiction": True,
                "kind": "direct_reversal",
                "reasoning_diff": f"{early['stance']} vs {late['stance']}",
            }

        grouped = {
            "0": [
                {"path": "late.md", "frontmatter": {"date": "2026-03-01"},
                 "_backfill": {"claim_summary": "later", "reasoning": []}},
                {"path": "early.md", "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {"claim_summary": "earlier", "reasoning": []}},
            ],
        }
        out = _stage_detect_contradictions(
            grouped, result, dry_run=False, judge=judge,
            cluster_names={"0": "topic_x"},
        )
        # Pair is (earlier, later), regardless of input order
        assert seen == [("earlier", "later")]
        assert "0" in out
        assert out["0"][0]["card_a"] == "early.md"
        assert out["0"][0]["card_b"] == "late.md"
        assert result.contradictions_detected == 1

    def test_cluster_with_only_one_backfilled_skipped(self):
        from daemon.reflection_pass import _stage_detect_contradictions

        result = self._empty_result()
        called = []
        def judge(e, l, t):
            called.append(True)
            return {"is_contradiction": False, "kind": "agreement", "reasoning_diff": ""}

        grouped = {
            "0": [
                {"path": "a.md", "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {"claim_summary": "S", "reasoning": []}},
                {"path": "b.md", "frontmatter": {"date": "2026-02-01"},
                 "_backfill": {"claim_summary": None, "reasoning": []}},  # no stance
            ],
        }
        _stage_detect_contradictions(
            grouped, result, dry_run=False, judge=judge,
        )
        # Only 1 backfilled → no pairs → judge never called
        assert called == []

    def test_cache_hit_skips_judge(self):
        from daemon.reflection_pass import _stage_detect_contradictions

        result = self._empty_result()
        called = []
        def judge(e, l, t):
            called.append(True)
            return {"is_contradiction": False, "kind": "agreement", "reasoning_diff": "x"}

        # Pre-populate cache so the pair is already judged
        early_stance = "earlier"
        sig = f"a.md|b.md|{str(hash(early_stance))[:8]}"
        prior = {sig: {"is_contradiction": True, "kind": "direct_reversal",
                       "reasoning_diff": "cached"}}

        grouped = {
            "0": [
                {"path": "a.md", "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {"claim_summary": "earlier", "reasoning": []}},
                {"path": "b.md", "frontmatter": {"date": "2026-02-01"},
                 "_backfill": {"claim_summary": "later", "reasoning": []}},
            ],
        }
        out = _stage_detect_contradictions(
            grouped, result, dry_run=False, judge=judge,
            judge_state=prior,
        )
        # Cache hit
        assert called == []
        # Judgment came from cache
        assert out["0"][0]["is_contradiction"] is True
        assert out["0"][0]["reasoning_diff"] == "cached"

    def test_judge_failure_isolated(self):
        from daemon.reflection_pass import _stage_detect_contradictions

        result = self._empty_result()
        def judge(e, l, t):
            if "broken" in e["stance"]:
                raise RuntimeError("LLM 500")
            return {"is_contradiction": False, "kind": "agreement", "reasoning_diff": "x"}

        grouped = {
            "0": [
                {"path": "broken.md", "frontmatter": {"date": "2026-01-01"},
                 "_backfill": {"claim_summary": "broken stance", "reasoning": []}},
                {"path": "ok1.md", "frontmatter": {"date": "2026-02-01"},
                 "_backfill": {"claim_summary": "ok stance 1", "reasoning": []}},
                {"path": "ok2.md", "frontmatter": {"date": "2026-03-01"},
                 "_backfill": {"claim_summary": "ok stance 2", "reasoning": []}},
            ],
        }
        out = _stage_detect_contradictions(
            grouped, result, dry_run=False, judge=judge,
        )
        # 3 cards = 3 pairs (broken-ok1, broken-ok2, ok1-ok2)
        # First two fail; third succeeds
        assert any("naming failed" in e or "judge failed" in e
                   for e in result.errors)
        # Output has the 1 successful judgment
        assert "0" in out
        assert len(out["0"]) == 1


# ---------- run_pass plumbing for stage 6 ----------

class TestRunPassJudgeIntegration:
    def test_judge_passed_through(self, tmp_path):
        from daemon.reflection_pass import run_pass

        (tmp_path / "10_Tech").mkdir()
        # Two cards in same domain
        (tmp_path / "10_Tech" / "a.md").write_text(
            "---\ntitle: A\nslice_id: aa\ndate: 2026-01-01\n---\nbody\n",
            encoding="utf-8",
        )
        (tmp_path / "10_Tech" / "b.md").write_text(
            "---\ntitle: B\nslice_id: bb\ndate: 2026-02-01\n---\nbody\n",
            encoding="utf-8",
        )

        called = []
        def judge(early, late, topic):
            called.append((early["stance"], late["stance"]))
            return {
                "is_contradiction": True,
                "kind": "direct_reversal",
                "reasoning_diff": "differ",
            }

        def fake_extractor(t, b):
            return {
                "claim_summary": f"stance from {t}",
                "open_questions": [],
            }

        def fake_cluster(cards, result, *, high_threshold, low_threshold):
            for c in cards:
                c["_cluster_id"] = "0"
            result.cards_clustered = len(cards)
            result.clusters_count = 1
            return {"0": cards}

        with patch("daemon.reflection_pass._stage_cluster", side_effect=fake_cluster):
            result = run_pass(
                vault_root=tmp_path, dry_run=False,
                extractor=fake_extractor,
                judge=judge,
                state_file=tmp_path / "state.json",
                contradictions_file=tmp_path / "contra.json",
            )

        # 2 cards → 1 pair → judge called once
        assert len(called) == 1
        assert result.contradictions_detected == 1

        # Contradictions state file written
        assert (tmp_path / "contra.json").exists()


def test_stub_stages_record_skips():
    """Stages 6-7 are stubs; verify skip messages.

    Stages 3, 4, 5, 8 became real progressively (commits B, C, D, E);
    when called with no input data each records an appropriate
    skip message ("no clusters" / "nothing eligible" / "no cards").
    """
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
    _stage_resolve_cluster_names({}, result, dry_run=False, namer=lambda t: "x")
    _stage_backfill_position_signal([], result, dry_run=False, extractor=lambda t, b: {})
    _stage_detect_open_threads({}, result, dry_run=False)
    _stage_detect_contradictions({}, result, dry_run=False, judge=lambda e, l, t: {})
    _stage_compute_drift({}, result, dry_run=False, segmenter=lambda c, t: {})
    _stage_writeback([], result, dry_run=False)

    assert len(result.stages_skipped) == 6
    for msg in result.stages_skipped:
        msg_lower = msg.lower()
        assert (
            "stub" in msg_lower
            or "dry-run" in msg_lower
            or "no clusters" in msg_lower
            or "nothing eligible" in msg_lower
            or "no cards" in msg_lower
        )


def test_writeback_message_dry_run_label_distinct():
    """Stage 8 is now real (preview-only). With cards in input, the
    stage_completed message labels dry-run vs no-mutation modes
    differently so the CLI is honest about which path ran. With no
    cards, both modes report 'no cards' skip uniformly."""
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

    # No-cards path: same skip message regardless of dry_run
    r1 = _empty(dry=True)
    _stage_writeback([], r1, dry_run=True)
    assert "no cards" in r1.stages_skipped[0].lower()

    # Cards-present path: stage_completed message differs by dry_run
    cards = [
        {"path": "a.md", "title": "A", "body": "x", "frontmatter": {},
         "_backfill": {"claim_summary": "S", "open_questions": []},
         "_cluster_id": 0},
    ]
    r2 = _empty(dry=True)
    _stage_writeback(cards, r2, dry_run=True)
    msg2 = r2.stages_completed[-1].lower()
    assert "preview, dry-run" in msg2

    r3 = _empty(dry=False)
    _stage_writeback(cards, r3, dry_run=False)
    msg3 = r3.stages_completed[-1].lower()
    assert "preview, no vault mutation" in msg3


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
