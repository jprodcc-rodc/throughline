"""Topic clustering — Reflection Layer engineering gate.

Per `docs/REFLECTION_LAYER_DESIGN.md` § "Engineering risks" + the
brief's § 7 risk 1: the Reflection Layer's three sub-functions
(Open Threads / Contradiction Surfacing / Drift Detection) all
depend on correctly grouping cards by topic. False-positive
contradictions (caused by mis-clustered cards) kill user trust
on first occurrence.

Engineering gate: clustering accuracy ≥75% on the maintainer's
vault (≥2,300 cards) before shipping the Reflection Pass daemon.
This module implements the algorithm; the experiment harness in
`mcp_server/clustering_experiment.py` measures accuracy against
user-provided ground truth.

Algorithm: hybrid embedding-similarity + (optional) LLM
boundary judgment.

1. Embed each card via bge-m3 (rag_server `/v1/embeddings`).
2. Build a similarity graph: edges between cards above a high
   threshold are "definitely same cluster"; below low threshold
   are "definitely different".
3. For pairs in the ambiguous middle band, optionally ask an LLM
   judge ("are these two cards on the same topic?").
4. Connected components on the resulting graph = clusters.

The LLM judge is `Optional[Callable]` so tests can run without
real LLM calls + so the experiment can quantify how much the LLM
contributes vs pure embedding.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass(frozen=True)
class CardForClustering:
    """A card reduced to the fields clustering needs.

    `path` is the unique identifier (vault-relative or absolute,
    consumer's choice — clustering itself doesn't care, but the
    accuracy harness uses it as the ground-truth join key).
    """
    path: str
    title: str
    body: str
    existing_tags: tuple[str, ...] = field(default_factory=tuple)


# Type alias for the embedder callable — accepts a list of strings,
# returns a list of equal-length embedding vectors. Real production
# embedder is `mcp_server.rag_client.embed_batch`; tests pass a
# synthetic version that returns deterministic vectors per input.
EmbedFn = Callable[[list[str]], list[list[float]]]


# Type alias for the LLM judge — accepts (card_a, card_b) and
# returns True if they're on the same topic, False otherwise.
# `None` means skip LLM judgment (embedding-only clustering).
LLMJudgeFn = Callable[[CardForClustering, CardForClustering], bool]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors.

    bge-m3 outputs are already L2-normalised, so cosine is just
    the dot product. We don't assume that here — recompute norms
    so this works on any embedding vendor.
    """
    if len(a) != len(b):
        raise ValueError(f"vector length mismatch: {len(a)} vs {len(b)}")
    if not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _card_text_for_embedding(card: CardForClustering,
                               body_chars: int = 300) -> str:
    """The text we feed to the embedder per card.

    Title + first N chars of body. Title-only loses too much
    signal on cards with terse titles; full body is too noisy
    (the back half of a 6-section card is often "summary +
    boundaries" boilerplate). 300 chars is a tunable starting
    point — clustering experiment can vary this.
    """
    return f"{card.title.strip()}\n\n{card.body.strip()[:body_chars]}"


def _connected_components(n: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    """Pure-stdlib union-find connected components.

    Tested independently in test_topic_clustering.py.
    """
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path compression
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    for i, j in edges:
        union(i, j)

    components: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        components.setdefault(root, []).append(i)
    return list(components.values())


def cluster_cards(
    cards: list[CardForClustering],
    embed_fn: EmbedFn,
    high_threshold: float = 0.75,
    low_threshold: float = 0.55,
    llm_judge: Optional[LLMJudgeFn] = None,
    body_chars: int = 300,
) -> list[list[CardForClustering]]:
    """Cluster cards by topic.

    Args:
        cards: Cards to cluster. Order is preserved within each
            output cluster (stable on input order for ties).
        embed_fn: Callable taking a batch of strings and returning
            embedding vectors (one per input). Production:
            `mcp_server.rag_client.embed_batch`. Tests: synthetic.
        high_threshold: Cosine similarity at-or-above which two
            cards are definitely same topic.
        low_threshold: Cosine similarity at-or-below which two
            cards are definitely different. Pairs in (low, high)
            are ambiguous.
        llm_judge: Optional callable (card_a, card_b) → bool.
            Called for ambiguous pairs only. If None, ambiguous
            pairs default to "different cluster" (conservative —
            we'd rather over-cluster than create false-positive
            same-topic links that produce false-positive
            contradictions in the Reflection Layer).
        body_chars: Number of body characters to include in each
            card's embedding text.

    Returns:
        List of clusters; each cluster is a list of CardForClustering.
        Singletons (cards that didn't match anything) are returned
        as length-1 clusters.
    """
    if not cards:
        return []
    if low_threshold > high_threshold:
        raise ValueError(
            f"low_threshold ({low_threshold}) must be ≤ "
            f"high_threshold ({high_threshold})"
        )

    texts = [_card_text_for_embedding(c, body_chars) for c in cards]
    embeddings = embed_fn(texts)
    if len(embeddings) != len(cards):
        raise RuntimeError(
            f"embed_fn returned {len(embeddings)} vectors for "
            f"{len(cards)} cards"
        )

    n = len(cards)
    edges: list[tuple[int, int]] = []
    ambiguous: list[tuple[int, int]] = []

    for i in range(n):
        for j in range(i + 1, n):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim >= high_threshold:
                edges.append((i, j))
            elif sim >= low_threshold:
                ambiguous.append((i, j))
            # else: < low_threshold → no edge, no LLM call

    # Phase 2: LLM judgment on ambiguous pairs
    if llm_judge is not None and ambiguous:
        for i, j in ambiguous:
            try:
                if llm_judge(cards[i], cards[j]):
                    edges.append((i, j))
            except Exception:
                # LLM failure on one pair shouldn't kill the whole
                # clustering. Conservative: treat as different.
                pass

    components = _connected_components(n, edges)
    return [[cards[idx] for idx in comp] for comp in components]


def cluster_index(clusters: list[list[CardForClustering]]) -> dict[str, int]:
    """{card.path → cluster index}. Convenience for accuracy
    metrics + downstream Reflection daemon integration."""
    out: dict[str, int] = {}
    for idx, cluster in enumerate(clusters):
        for card in cluster:
            out[card.path] = idx
    return out
