"""Topic-clustering algorithm + accuracy metric tests.

Tests use synthetic embeddings (deterministic, no rag_server
dependency) to verify the algorithm's correctness independent of
real bge-m3 quality. Real-vault accuracy is measured by the
experiment harness (`mcp_server/clustering_experiment.py`) — those
results are vault-specific data, not regression tests.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mcp_server.topic_clustering import (
    CardForClustering,
    cluster_cards,
    cluster_index,
    cosine_similarity,
    _connected_components,
)
from mcp_server.clustering_accuracy import (
    AccuracyReport,
    compute_homogeneity_completeness,
    compute_pairwise_accuracy,
    evaluate,
    load_ground_truth,
)


# ---------- cosine_similarity ----------

class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        """Avoid /0; meaningful answer is 'undefined' but for our
        clustering use case 'no similarity' is the safe default."""
        assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0

    def test_different_lengths_raises(self):
        with pytest.raises(ValueError):
            cosine_similarity([1.0], [1.0, 2.0])

    def test_unnormalised_vectors_normalised_internally(self):
        # [3, 4] and [6, 8] have the same direction; cosine = 1
        assert cosine_similarity([3.0, 4.0], [6.0, 8.0]) == pytest.approx(1.0)


# ---------- connected components ----------

class TestConnectedComponents:
    def test_no_edges_each_node_singleton(self):
        comps = _connected_components(4, [])
        assert sorted(sorted(c) for c in comps) == [[0], [1], [2], [3]]

    def test_single_chain(self):
        comps = _connected_components(4, [(0, 1), (1, 2), (2, 3)])
        assert len(comps) == 1
        assert sorted(comps[0]) == [0, 1, 2, 3]

    def test_two_clusters(self):
        comps = _connected_components(5, [(0, 1), (1, 2), (3, 4)])
        sorted_comps = sorted(sorted(c) for c in comps)
        assert sorted_comps == [[0, 1, 2], [3, 4]]

    def test_redundant_edges_dont_break(self):
        comps = _connected_components(3, [(0, 1), (1, 2), (0, 2), (0, 1)])
        assert len(comps) == 1
        assert sorted(comps[0]) == [0, 1, 2]


# ---------- cluster_cards (algorithm correctness) ----------

def _make_card(path: str, title: str, body: str = "body") -> CardForClustering:
    return CardForClustering(path=path, title=title, body=body)


def _synthetic_embedder(group_assignments: dict[str, int],
                          dim: int = 8):
    """Test embedder: each card with the same `group_assignments[path]`
    gets the same one-hot embedding. Cosine similarity within a group
    is 1.0; across groups is 0.0.
    """
    def _embed(texts: list[str]) -> list[list[float]]:
        # We can't easily map text → path in this synthetic helper,
        # so the caller passes ordered texts that match the card order.
        # The real test wires this up via _embed_for_cards below.
        raise NotImplementedError("use _embed_for_cards instead")
    return _embed


def _embed_for_cards(cards: list[CardForClustering],
                       group_by_path: dict[str, int],
                       dim: int = 8):
    """Returns an embed_fn closure that produces per-card vectors
    based on the path → group mapping. Vectors of same group are
    identical → cosine similarity 1.0."""
    def _embed(texts: list[str]) -> list[list[float]]:
        vectors = []
        for i, _t in enumerate(texts):
            group = group_by_path[cards[i].path]
            vec = [0.0] * dim
            vec[group % dim] = 1.0
            vectors.append(vec)
        return vectors
    return _embed


class TestClusterCards:
    def test_empty_input_returns_empty(self):
        clusters = cluster_cards(
            [], embed_fn=lambda texts: []
        )
        assert clusters == []

    def test_singleton_card_one_cluster(self):
        cards = [_make_card("a.md", "lonely")]
        embed = _embed_for_cards(cards, {"a.md": 0})
        clusters = cluster_cards(cards, embed_fn=embed)
        assert len(clusters) == 1
        assert len(clusters[0]) == 1

    def test_two_same_topic_cards_one_cluster(self):
        cards = [
            _make_card("a.md", "pricing q1"),
            _make_card("b.md", "pricing q2"),
        ]
        embed = _embed_for_cards(cards, {"a.md": 0, "b.md": 0})
        # high_threshold low enough to pass our 1-hot synthetic
        # similarity (which is 1.0 within group); also nudge low
        # to keep low ≤ high
        clusters = cluster_cards(cards, embed_fn=embed,
                                   high_threshold=0.5,
                                   low_threshold=0.3)
        assert len(clusters) == 1
        assert len(clusters[0]) == 2

    def test_two_different_topic_cards_two_clusters(self):
        cards = [
            _make_card("a.md", "pricing"),
            _make_card("b.md", "keto rebound"),
        ]
        embed = _embed_for_cards(cards, {"a.md": 0, "b.md": 1})
        clusters = cluster_cards(cards, embed_fn=embed,
                                   high_threshold=0.5,
                                   low_threshold=0.3)
        assert len(clusters) == 2

    def test_three_topics_three_clusters(self):
        cards = [
            _make_card(f"c{i}.md", f"topic-{i % 3}-{i}")
            for i in range(9)
        ]
        groups = {f"c{i}.md": i % 3 for i in range(9)}
        embed = _embed_for_cards(cards, groups)
        clusters = cluster_cards(cards, embed_fn=embed,
                                   high_threshold=0.5,
                                   low_threshold=0.3)
        assert len(clusters) == 3
        # Each cluster has exactly 3 cards (i mod 3)
        sizes = sorted(len(c) for c in clusters)
        assert sizes == [3, 3, 3]

    def test_invalid_threshold_combo_raises(self):
        cards = [_make_card("a.md", "x"), _make_card("b.md", "y")]
        embed = _embed_for_cards(cards, {"a.md": 0, "b.md": 0})
        with pytest.raises(ValueError):
            cluster_cards(cards, embed_fn=embed,
                            low_threshold=0.9, high_threshold=0.5)

    def test_embed_fn_wrong_length_raises(self):
        cards = [_make_card("a.md", "x"), _make_card("b.md", "y")]
        bad_embed = lambda texts: [[1.0]]  # only 1 vector for 2 cards
        with pytest.raises(RuntimeError):
            cluster_cards(cards, embed_fn=bad_embed)

    def test_llm_judge_promotes_ambiguous_to_same_cluster(self):
        """Ambiguous pairs (between low and high) become same-cluster
        when the LLM judge says yes."""
        cards = [
            _make_card("a.md", "x"),
            _make_card("b.md", "y"),
        ]
        # Two unit vectors with cosine similarity 0.65 (in the
        # ambiguous band when high=0.75, low=0.55).
        import math
        cos = 0.65
        def embed(texts):
            return [
                [1.0, 0.0],
                [cos, math.sqrt(1.0 - cos * cos)],
            ]

        # Without LLM judge: ambiguous → different cluster
        clusters_without = cluster_cards(
            cards, embed_fn=embed,
            high_threshold=0.75, low_threshold=0.55,
        )
        assert len(clusters_without) == 2

        # With LLM judge saying YES: same cluster
        clusters_with = cluster_cards(
            cards, embed_fn=embed,
            high_threshold=0.75, low_threshold=0.55,
            llm_judge=lambda a, b: True,
        )
        assert len(clusters_with) == 1

    def test_llm_judge_exception_falls_back_to_different(self):
        """LLM failure on a pair shouldn't crash clustering."""
        cards = [_make_card("a.md", "x"), _make_card("b.md", "y")]
        import math
        cos = 0.65
        def embed(texts):
            return [
                [1.0, 0.0],
                [cos, math.sqrt(1.0 - cos * cos)],
            ]

        def crashing_judge(a, b):
            raise RuntimeError("LLM API down")
        clusters = cluster_cards(
            cards, embed_fn=embed,
            high_threshold=0.75, low_threshold=0.55,
            llm_judge=crashing_judge,
        )
        # Failure → conservative, treat as different
        assert len(clusters) == 2


# ---------- cluster_index ----------

class TestClusterIndex:
    def test_index_assigns_cluster_ids_per_card(self):
        c1 = _make_card("a.md", "x")
        c2 = _make_card("b.md", "y")
        c3 = _make_card("c.md", "z")
        idx = cluster_index([[c1, c2], [c3]])
        assert idx == {"a.md": 0, "b.md": 0, "c.md": 1}


# ---------- accuracy metrics ----------

class TestPairwiseAccuracy:
    def test_perfect_agreement(self):
        pred = {"a": 0, "b": 0, "c": 1}
        truth = {"a": "X", "b": "X", "c": "Y"}
        acc, total, agreed, fp, fn = compute_pairwise_accuracy(pred, truth)
        assert acc == 1.0
        assert agreed == total == 3  # 3 pairs
        assert fp == 0
        assert fn == 0

    def test_perfect_disagreement(self):
        # Predict cluster of 3, truth says all different
        pred = {"a": 0, "b": 0, "c": 0}
        truth = {"a": "X", "b": "Y", "c": "Z"}
        acc, total, agreed, fp, fn = compute_pairwise_accuracy(pred, truth)
        assert total == 3
        assert agreed == 0
        assert fp == 3  # all 3 pairs are predicted-same / truth-different
        assert fn == 0

    def test_split_cluster_false_negatives(self):
        pred = {"a": 0, "b": 1, "c": 2}
        truth = {"a": "X", "b": "X", "c": "X"}
        acc, total, agreed, fp, fn = compute_pairwise_accuracy(pred, truth)
        assert total == 3
        assert agreed == 0
        assert fp == 0
        assert fn == 3

    def test_partial_agreement_below_75_percent(self):
        # Mixed: some right, some wrong
        pred = {"a": 0, "b": 0, "c": 1, "d": 1}
        truth = {"a": "X", "b": "X", "c": "X", "d": "Y"}
        # pairs:
        #   a-b: pred-same(0,0), truth-same(X,X) → agree
        #   a-c: pred-different, truth-same(X,X) → false neg
        #   a-d: pred-different, truth-different → agree
        #   b-c: pred-different, truth-same(X,X) → false neg
        #   b-d: pred-different, truth-different → agree
        #   c-d: pred-same(1,1), truth-different(X,Y) → false pos
        # 3 agreed / 6 total = 0.5
        acc, total, agreed, fp, fn = compute_pairwise_accuracy(pred, truth)
        assert total == 6
        assert agreed == 3
        assert acc == 0.5
        assert fp == 1
        assert fn == 2

    def test_keys_intersection_used(self):
        """Keys in only one of pred/truth are silently dropped."""
        pred = {"a": 0, "b": 0, "extra": 1}
        truth = {"a": "X", "b": "X", "missing": "Y"}
        acc, total, agreed, _, _ = compute_pairwise_accuracy(pred, truth)
        # Only a and b in intersection → 1 pair
        assert total == 1


class TestHomogeneityCompleteness:
    def test_perfect_clustering_all_metrics_one(self):
        pred = {"a": 0, "b": 0, "c": 1, "d": 1}
        truth = {"a": "X", "b": "X", "c": "Y", "d": "Y"}
        h, c, v = compute_homogeneity_completeness(pred, truth)
        assert h == pytest.approx(1.0)
        assert c == pytest.approx(1.0)
        assert v == pytest.approx(1.0)

    def test_singleton_clusters_high_homogeneity_low_completeness(self):
        """Each prediction is its own cluster → homogeneity is high
        (each cluster is pure since it has only 1 element), but
        completeness is low (truth clusters are split). For 2 truth
        clusters of 2 each, completeness is exactly 0.5."""
        pred = {"a": 0, "b": 1, "c": 2, "d": 3}
        truth = {"a": "X", "b": "X", "c": "Y", "d": "Y"}
        h, c, v = compute_homogeneity_completeness(pred, truth)
        assert h == pytest.approx(1.0)
        assert c == pytest.approx(0.5)
        assert 0.0 < v < 1.0

    def test_one_giant_cluster_low_homogeneity_high_completeness(self):
        """All predicted to be one cluster → completeness is high
        (truth clusters not split), homogeneity is low (mixed)."""
        pred = {"a": 0, "b": 0, "c": 0, "d": 0}
        truth = {"a": "X", "b": "X", "c": "Y", "d": "Y"}
        h, c, v = compute_homogeneity_completeness(pred, truth)
        assert h < 0.5
        assert c == pytest.approx(1.0)


# ---------- evaluate report ----------

class TestEvaluate:
    def test_perfect_report_passes_gate(self):
        pred = {"a": 0, "b": 0, "c": 1}
        truth = {"a": "X", "b": "X", "c": "Y"}
        rep = evaluate(pred, truth)
        assert rep.pairwise_accuracy == 1.0
        assert rep.n_cards == 3
        assert rep.n_predicted_clusters == 2
        assert rep.n_truth_clusters == 2
        assert "PASS" in str(rep)

    def test_failing_report_marks_fail(self):
        pred = {"a": 0, "b": 0, "c": 0}
        truth = {"a": "X", "b": "Y", "c": "Z"}
        rep = evaluate(pred, truth)
        assert rep.pairwise_accuracy < 0.75
        assert "FAIL" in str(rep)


# ---------- load_ground_truth ----------

class TestLoadGroundTruth:
    def test_with_cards_wrapper(self, tmp_path):
        path = tmp_path / "gt.json"
        path.write_text(json.dumps({
            "cards": {"a.md": "X", "b.md": "Y"},
        }), encoding="utf-8")
        result = load_ground_truth(path)
        assert result == {"a.md": "X", "b.md": "Y"}

    def test_flat_dict(self, tmp_path):
        path = tmp_path / "gt.json"
        path.write_text(json.dumps({"a.md": "X", "b.md": "Y"}),
                         encoding="utf-8")
        result = load_ground_truth(path)
        assert result == {"a.md": "X", "b.md": "Y"}

    def test_invalid_shape_raises(self, tmp_path):
        path = tmp_path / "gt.json"
        path.write_text("[1,2,3]", encoding="utf-8")
        with pytest.raises(ValueError):
            load_ground_truth(path)
