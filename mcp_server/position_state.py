"""Shared helpers for MCP tools that read the Reflection Pass
positions state file (``reflection_positions.json``).

Used by ``check_consistency`` and ``get_position_drift`` tools.
Co-located in mcp_server/ so the tools don't import from daemon/
(architectural decoupling: mcp_server is a thin client of vault
state files, never imports daemon helpers directly).

Tokenizer here mirrors ``daemon.open_threads._tokenize`` semantics
(CJK bigram + English unigram + mini stopword set) but is
duplicated rather than shared. The two consumers may diverge over
time without forcing a daemon dependency on mcp_server.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional


_STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "with",
    "is", "are", "was", "were", "be", "been", "have", "has", "had",
    "do", "does", "did", "this", "that", "these", "those",
    "can", "could", "should", "would", "may", "might", "must",
    "what", "when", "where", "why", "how", "vs", "into", "from",
    "on", "at", "by", "as", "if", "but", "not", "so", "than",
    "i", "you", "he", "she", "it", "we", "they", "my", "your",
    "think", "thought", "thinking", "going", "want", "wants",
}

_STOPWORDS_CJK = {
    "的", "了", "是", "在", "和", "与", "或", "也", "都", "就",
    "如何", "什么", "为何", "为什", "怎么", "怎样", "可以", "需要",
    "应该", "已经", "还是", "还有", "因此", "因为", "所以",
    "我觉", "觉得", "我想", "想要", "应当",
}

_TOKEN_SPLIT_RE = re.compile(r"[^\w一-鿿]+")
_HAS_CJK = re.compile(r"[一-鿿]")


def tokenize(text: str) -> set[str]:
    """Lowercase, split on whitespace+punctuation, decompose CJK
    runs into 2-char bigrams. Mirrors the open_threads tokenizer."""
    s = text.lower()
    tokens: set[str] = set()
    for chunk in _TOKEN_SPLIT_RE.split(s):
        if not chunk:
            continue
        if _HAS_CJK.search(chunk):
            for i in range(len(chunk) - 1):
                bg = chunk[i: i + 2]
                if bg not in _STOPWORDS_CJK and len(bg) == 2:
                    tokens.add(bg)
            if 2 <= len(chunk) <= 6:
                tokens.add(chunk)
        else:
            if len(chunk) >= 2 and chunk not in _STOPWORDS_EN:
                tokens.add(chunk)
    return tokens


# ---------- state file resolver ----------

def _state_dir() -> Path:
    return Path(
        os.environ.get(
            "THROUGHLINE_STATE_DIR",
            str(Path.home() / "throughline_runtime" / "state"),
        )
    ).expanduser()


def resolve_positions_file() -> Path:
    """Match ``daemon.state_paths.default_positions_file()``."""
    return _state_dir() / "reflection_positions.json"


def resolve_contradictions_file() -> Path:
    """Match ``daemon.state_paths.default_contradictions_file()``.
    Stage 6 output; consumed by ``check_consistency`` when present."""
    return _state_dir() / "reflection_contradictions.json"


def load_contradictions(path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    """Load reflection_contradictions.json — same shape and
    error-handling as ``load_positions``. Returns None when missing /
    unreadable. Callers can then fall back to "return all cluster
    positions, host LLM judges contradiction"."""
    if path is None:
        path = resolve_contradictions_file()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def load_positions(path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    """Load the positions state file. Returns None on missing /
    unreadable / not-a-dict so callers can surface the absence as
    an error result rather than crashing."""
    if path is None:
        path = resolve_positions_file()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


# ---------- cluster matching ----------

def score_cluster_match(
    needle_tokens: set[str],
    cluster: dict[str, Any],
) -> float:
    """Return overlap fraction between needle tokens and cluster's
    aggregate vocabulary (cluster name + card titles + card stances).
    """
    if not needle_tokens:
        return 0.0

    cluster_tokens: set[str] = set()
    name = cluster.get("topic_cluster")
    if name:
        cluster_tokens.update(tokenize(str(name)))
    for card in cluster.get("cards", []):
        cluster_tokens.update(tokenize(str(card.get("title", ""))))
        stance = card.get("stance")
        if stance:
            cluster_tokens.update(tokenize(str(stance)))

    if not cluster_tokens:
        return 0.0
    overlap = needle_tokens & cluster_tokens
    return len(overlap) / len(needle_tokens)


def find_best_cluster(
    needle: str,
    state: dict[str, Any],
    min_score: float = 0.3,
) -> Optional[dict[str, Any]]:
    """Pick the cluster whose vocabulary best matches the needle
    text (a user statement or topic name).

    Returns None when no cluster scores above ``min_score``. The
    threshold ensures we don't return wildly-unrelated clusters
    just because they happen to share one stopword.
    """
    needle_tokens = tokenize(needle)
    if not needle_tokens:
        return None

    best = None
    best_score = 0.0
    for cluster in state.get("clusters", []):
        score = score_cluster_match(needle_tokens, cluster)
        if score > best_score:
            best_score = score
            best = cluster

    if best_score < min_score:
        return None
    return best


def find_cluster_by_topic(
    topic: str,
    state: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """Find a cluster by topic name. Tries exact substring match
    on ``topic_cluster`` first (case-insensitive), then falls back
    to ``find_best_cluster`` for token-overlap matching against
    title vocabulary.
    """
    needle = topic.lower().strip()
    if not needle:
        return None

    for cluster in state.get("clusters", []):
        name = (cluster.get("topic_cluster") or "").lower()
        if name and needle in name:
            return cluster

    # Fallback: token-overlap against cluster vocabulary
    return find_best_cluster(topic, state, min_score=0.2)
