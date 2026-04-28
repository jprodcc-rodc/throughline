"""Phase 1 Week 2 commit 4 — list_topics real-logic tests.

Covers:
- taxonomy_reader.list_domains: full list, prefix filter, exact-match,
  no-match-empty, daemon-import-fail returns empty
- taxonomy_reader.count_cards_per_domain: empty vault, real-shape
  vault scan, frontmatter parsing edge cases (no fm / malformed yaml
  / non-list tags), cache TTL
- list_topics tool: success path, prefix filter, include_card_counts
  toggle, daemon-import-fail error path
- helpers: _domain_from_tags edge cases
"""
from __future__ import annotations

import time
from unittest.mock import patch

import pytest


# ---------- helpers ----------

class TestDomainFromTags:
    def test_first_non_axis_tag_wins(self):
        from mcp_server.taxonomy_reader import _domain_from_tags

        assert (
            _domain_from_tags(["Health/Biohack", "y/Mechanism", "z/Node"])
            == "Health/Biohack"
        )

    def test_axis_only_returns_empty(self):
        from mcp_server.taxonomy_reader import _domain_from_tags

        assert _domain_from_tags(["y/SOP", "z/Boundary"]) == ""

    def test_empty_list_returns_empty(self):
        from mcp_server.taxonomy_reader import _domain_from_tags

        assert _domain_from_tags([]) == ""

    def test_non_list_returns_empty(self):
        """frontmatter parse may produce a string if YAML is weird."""
        from mcp_server.taxonomy_reader import _domain_from_tags

        assert _domain_from_tags("not a list") == ""
        assert _domain_from_tags(None) == ""

    def test_skips_non_string_items(self):
        from mcp_server.taxonomy_reader import _domain_from_tags

        # YAML can produce ints / nulls in lists
        assert _domain_from_tags([42, None, "Health/Biohack"]) == "Health/Biohack"


# ---------- list_domains ----------

class TestListDomains:
    def test_returns_full_set_when_no_prefix(self):
        """daemon.taxonomy.VALID_X_SET ships ~33 domains."""
        from mcp_server.taxonomy_reader import list_domains

        domains = list_domains()
        assert len(domains) > 5  # actual is ~33; conservative check
        assert "Health/Biohack" in domains
        assert "AI/LLM" in domains

    def test_prefix_filter_health(self):
        from mcp_server.taxonomy_reader import list_domains

        health_domains = list_domains(prefix="Health")
        assert all(d.startswith("Health") for d in health_domains)
        assert "Health/Biohack" in health_domains
        assert "AI/LLM" not in health_domains

    def test_prefix_no_match_returns_empty(self):
        from mcp_server.taxonomy_reader import list_domains

        assert list_domains(prefix="NonExistentDomain") == []

    def test_prefix_no_false_positive_on_partial(self):
        """'Heal' must NOT match 'Health/X' — prefix needs / or
        exact-match boundary."""
        from mcp_server.taxonomy_reader import list_domains

        assert list_domains(prefix="Heal") == []

    def test_exact_match_works(self):
        from mcp_server.taxonomy_reader import list_domains

        assert list_domains(prefix="Health/Biohack") == ["Health/Biohack"]


# ---------- count_cards_per_domain ----------

def _write_card(vault: "Path", filename: str, tags: list[str], title: str = "T"):
    """Helper: write a sample card with given tags."""
    fm_tags = "[" + ", ".join(tags) + "]"
    body = (
        "---\n"
        f"title: \"{title}\"\n"
        "date: 2026-04-01\n"
        f"tags: {fm_tags}\n"
        "---\n\n"
        "# Body\n\nLorem ipsum.\n"
    )
    path = vault / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class TestCountCardsPerDomain:
    def setup_method(self):
        from mcp_server.taxonomy_reader import clear_cache
        clear_cache()

    def test_empty_vault_returns_empty_dict(self, tmp_path):
        from mcp_server.taxonomy_reader import count_cards_per_domain

        result = count_cards_per_domain(vault_root=tmp_path)
        assert result == {}

    def test_missing_vault_returns_empty_dict(self, tmp_path):
        from mcp_server.taxonomy_reader import count_cards_per_domain

        missing = tmp_path / "does_not_exist"
        result = count_cards_per_domain(vault_root=missing)
        assert result == {}

    def test_counts_cards_by_x_axis_domain(self, tmp_path):
        from mcp_server.taxonomy_reader import count_cards_per_domain

        _write_card(tmp_path, "card1.md",
                    ["Health/Biohack", "y/Mechanism", "z/Node"])
        _write_card(tmp_path, "card2.md",
                    ["Health/Biohack", "y/Decision"])
        _write_card(tmp_path, "card3.md",
                    ["AI/LLM", "y/Architecture"])

        counts = count_cards_per_domain(vault_root=tmp_path,
                                         use_cache=False)
        assert counts.get("Health/Biohack") == 2
        assert counts.get("AI/LLM") == 1

    def test_counts_recursively_in_subdirs(self, tmp_path):
        from mcp_server.taxonomy_reader import count_cards_per_domain

        _write_card(tmp_path, "10_Health/card1.md", ["Health/Biohack"])
        _write_card(tmp_path, "20_Tech/sub/card2.md", ["Tech/Software"])

        counts = count_cards_per_domain(vault_root=tmp_path,
                                         use_cache=False)
        assert counts.get("Health/Biohack") == 1
        assert counts.get("Tech/Software") == 1

    def test_skips_files_without_frontmatter(self, tmp_path):
        from mcp_server.taxonomy_reader import count_cards_per_domain

        # No frontmatter — should be silently skipped
        (tmp_path / "no_fm.md").write_text(
            "Just a body, no fm\n", encoding="utf-8"
        )
        _write_card(tmp_path, "card.md", ["Health/Biohack"])

        counts = count_cards_per_domain(vault_root=tmp_path,
                                         use_cache=False)
        assert counts.get("Health/Biohack") == 1
        assert sum(counts.values()) == 1

    def test_skips_malformed_yaml(self, tmp_path):
        from mcp_server.taxonomy_reader import count_cards_per_domain

        (tmp_path / "bad.md").write_text(
            "---\n[: { : invalid yaml: : :\n---\n\nbody\n",
            encoding="utf-8",
        )
        _write_card(tmp_path, "good.md", ["Tech/PKM"])

        counts = count_cards_per_domain(vault_root=tmp_path,
                                         use_cache=False)
        assert counts.get("Tech/PKM") == 1
        assert "" not in counts  # malformed didn't sneak in

    def test_skips_axis_only_cards(self, tmp_path):
        """Cards with only y/* and z/* tags have no X-axis domain;
        excluded from counts."""
        from mcp_server.taxonomy_reader import count_cards_per_domain

        _write_card(tmp_path, "axis.md", ["y/SOP", "z/Boundary"])
        counts = count_cards_per_domain(vault_root=tmp_path,
                                         use_cache=False)
        assert counts == {}

    def test_cache_returns_same_result_within_ttl(self, tmp_path):
        from mcp_server.taxonomy_reader import count_cards_per_domain

        _write_card(tmp_path, "card1.md", ["Health/Biohack"])
        first = count_cards_per_domain(vault_root=tmp_path)

        # Add a new card; with cache, count shouldn't change
        _write_card(tmp_path, "card2.md", ["Health/Biohack"])
        second = count_cards_per_domain(vault_root=tmp_path)
        assert first == second  # cache hit

        # Force fresh scan
        third = count_cards_per_domain(vault_root=tmp_path,
                                        use_cache=False)
        assert third.get("Health/Biohack") == 2


# ---------- list_topics tool ----------

class TestListTopicsTool:
    def setup_method(self):
        from mcp_server.taxonomy_reader import clear_cache
        clear_cache()

    def test_success_with_card_counts(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        _write_card(tmp_path, "card1.md", ["Health/Biohack"])
        _write_card(tmp_path, "card2.md", ["AI/LLM"])

        from mcp_server.tools import list_topics
        result = list_topics()

        assert result["_status"] == "ok"
        # Active VALID_X_SET has ~33 entries; we expect all returned
        assert len(result["domains"]) > 5

        # Find specific domains
        d_map = {d["path"]: d["card_count"] for d in result["domains"]}
        assert d_map.get("Health/Biohack") == 1
        assert d_map.get("AI/LLM") == 1
        # Domains with no cards still appear with count=0
        assert d_map.get("Hardware/PC") == 0

        assert result["total_cards"] >= 2

    def test_include_card_counts_false_skips_vault_scan(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        _write_card(tmp_path, "card.md", ["Health/Biohack"])

        from mcp_server.tools import list_topics
        result = list_topics(include_card_counts=False)

        assert result["_status"] == "ok"
        # All card_counts should be None when we opted out
        for d in result["domains"]:
            assert d["card_count"] is None
        assert result["total_cards"] == 0

    def test_prefix_filter_returns_subset(self, tmp_path, monkeypatch):
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))

        from mcp_server.tools import list_topics
        result = list_topics(prefix="Health", include_card_counts=False)

        assert result["_status"] == "ok"
        for d in result["domains"]:
            assert d["path"].startswith("Health")

    def test_empty_vault_includes_cold_start_hint(
        self, tmp_path, monkeypatch
    ):
        """Fresh vault (taxonomy loaded, 0 cards): add hint so the
        host LLM teaches save_conversation rather than silently
        listing 30+ domains all with card_count=0."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))

        from mcp_server.tools import list_topics
        result = list_topics()

        assert result["_status"] == "ok"
        assert result["total_cards"] == 0
        assert "_message" in result
        msg = result["_message"].lower()
        assert "save_conversation" in msg or "remember" in msg, (
            f"hint should reference save_conversation; got: {msg!r}"
        )

    def test_populated_vault_omits_cold_start_hint(
        self, tmp_path, monkeypatch
    ):
        """When cards exist, the hint must NOT fire — host LLM
        should treat the response as normal."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))
        _write_card(tmp_path, "c.md", ["Health/Biohack"])

        from mcp_server.tools import list_topics
        result = list_topics()

        assert result["total_cards"] >= 1
        assert "_message" not in result

    def test_no_card_counts_omits_cold_start_hint(
        self, tmp_path, monkeypatch
    ):
        """Without include_card_counts we can't distinguish empty
        vault from skipped scan — hint must not fire to avoid
        false-positive teaching when the user just opted out."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))

        from mcp_server.tools import list_topics
        result = list_topics(include_card_counts=False)

        assert result["total_cards"] == 0
        assert "_message" not in result

    def test_prefix_no_match_returns_ok_empty(self, tmp_path, monkeypatch):
        """A prefix that legitimately matches nothing is NOT an
        error — taxonomy is loaded, just the user's query was
        narrow."""
        monkeypatch.setenv("THROUGHLINE_VAULT_ROOT", str(tmp_path))

        from mcp_server.tools import list_topics
        result = list_topics(prefix="DefinitelyNotAThing",
                              include_card_counts=False)

        assert result["_status"] == "ok"
        assert result["domains"] == []
        assert result["total_cards"] == 0

    def test_daemon_import_failure_returns_error(self, monkeypatch):
        """When daemon.taxonomy can't be imported / has empty
        VALID_X_SET (broken install), list_topics surfaces an
        error pointing at doctor.

        Cleanest mock: empty out daemon.taxonomy.VALID_X_SET so
        list_domains() returns an empty list both with and without
        a prefix, triggering the error path.
        """
        import daemon.taxonomy

        monkeypatch.setattr(daemon.taxonomy, "VALID_X_SET", [])

        from mcp_server.tools import list_topics
        result = list_topics()

        assert result["_status"] == "error"
        assert "doctor" in result["_message"].lower()
