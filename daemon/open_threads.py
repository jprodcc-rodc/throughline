"""Stage 5 — Open Thread detection.

For each card with non-empty ``open_questions`` (back-filled by
stage 4), scan later cards in the same cluster to see if any
question got addressed. Questions that remain unaddressed feed the
``find_open_threads`` MCP tool.

Pure stdlib. No LLM, no network. Tokenization handles Chinese +
English (CJK bigrams + English unigrams) so the bilingual vault
works without an external segmenter.

Bias: HIGH-conservative threshold (0.75). Better to surface an
extra "review this thread" reminder the user can dismiss than to
silently swallow a real open thread. False-positive direction =
"still open when actually resolved" = user sees an extra reminder,
trivial cost. False-negative = "marked resolved when actually
open" = user MISSES the unfinished thinking, defeats the feature.

Usage from ``reflection_pass._stage_detect_open_threads``::

    detect_open_threads(cards, grouped) -> dict[card_path, list[unresolved_qs]]

Cards with non-empty unresolved lists are flagged ``_open_thread: True``
in-memory. Stage 8 writes the flag to frontmatter atomically.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional


# Mini stopword set — tiny on purpose. Larger lists hurt more than
# help on niche technical vocabulary the user actually wants to
# surface. CJK side has the high-frequency particles only.
_STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "with",
    "is", "are", "was", "were", "be", "been", "have", "has", "had",
    "do", "does", "did", "this", "that", "these", "those",
    "can", "could", "should", "would", "may", "might", "must",
    "what", "when", "where", "why", "how", "vs", "into", "from",
    "on", "at", "by", "as", "if", "but", "not", "so", "than",
}

_STOPWORDS_CJK = {
    "的", "了", "是", "在", "和", "与", "或", "也", "都", "就",
    "如何", "什么", "为何", "为什", "怎么", "怎样", "可以", "需要",
    "应该", "已经", "还是", "还有", "因此", "因为", "所以",
}


_TOKEN_SPLIT_RE = re.compile(r"[^\w一-鿿]+")
_HAS_CJK = re.compile(r"[一-鿿]")


def _tokenize(text: str) -> set[str]:
    """Lowercase, split on whitespace+punctuation, decompose CJK
    runs into 2-char bigrams. Returns a set of meaningful tokens.

    Bigrams over CJK chars give us a tokenization-free way to match
    Chinese phrases without pulling in jieba. Coarse but stable.
    """
    s = text.lower()
    tokens: set[str] = set()
    for chunk in _TOKEN_SPLIT_RE.split(s):
        if not chunk:
            continue
        if _HAS_CJK.search(chunk):
            # Generate CJK bigrams. Unigrams are too noisy (every
            # character matches everywhere); 2-grams are about
            # right for the kind of phrase-level overlap we want.
            for i in range(len(chunk) - 1):
                bg = chunk[i: i + 2]
                if bg not in _STOPWORDS_CJK and len(bg) == 2:
                    tokens.add(bg)
            # Also keep the whole chunk if it's reasonable length —
            # catches monomorphic terms ("血小板") that should align
            # at full length.
            if 2 <= len(chunk) <= 6:
                tokens.add(chunk)
        else:
            # English-ish chunk
            if len(chunk) >= 2 and chunk not in _STOPWORDS_EN:
                tokens.add(chunk)
    return tokens


def _question_addressed_by(
    question: str,
    candidate_text: str,
    threshold: float = 0.75,
) -> bool:
    """Return True iff at least ``threshold`` fraction of the
    question's content tokens appear in ``candidate_text``."""
    q_tokens = _tokenize(question)
    if not q_tokens:
        # Empty / all-stopword question: don't claim it's addressed,
        # but it'll be filtered out before we get here in practice.
        return False
    c_tokens = _tokenize(candidate_text)
    if not c_tokens:
        return False
    overlap = q_tokens & c_tokens
    return len(overlap) / len(q_tokens) >= threshold


# ---------- card chronology ----------
# Hoisted to daemon.state_paths so reflection_pass + future stages
# share one definition. _card_timestamp kept as a module-local
# alias for back-compat with the test surface.

from daemon.state_paths import card_timestamp as _card_timestamp  # noqa: E402


# ---------- main entry ----------

def detect_open_threads(
    grouped: dict[str, list[dict[str, Any]]],
    *,
    threshold: float = 0.75,
    candidate_text_chars: int = 1500,
) -> dict[str, list[str]]:
    """For each card with back-filled open_questions, return the
    subset that haven't been addressed by later cards in the same
    cluster.

    Args:
        grouped: cluster_id -> list of card dicts.
        threshold: minimum question-token overlap for a candidate
            to count as addressing the question (default 0.75).
        candidate_text_chars: how many chars of each candidate's
            body to consider. Title is always included; body is
            truncated to bound work for large vaults.

    Returns:
        Dict mapping ``card['path']`` -> list of still-unresolved
        question strings. Cards with no remaining open questions
        are absent from the result; cards with no questions to
        begin with are also absent.

    Side effects: none. Caller decides whether to mutate the cards.
    """
    result: dict[str, list[str]] = {}

    for cid, members in grouped.items():
        # Sort by timestamp ascending so we can scan "later cards"
        # via index slicing.
        chronological = sorted(members, key=_card_timestamp)

        for i, card in enumerate(chronological):
            backfill = card.get("_backfill") or {}
            questions = backfill.get("open_questions") or []
            if not questions:
                continue

            later = chronological[i + 1:]
            if not later:
                # No subsequent card to potentially address it →
                # all questions still open.
                result[card["path"]] = list(questions)
                continue

            # For each question, check resolution against every
            # later card's title + body excerpt + claim_summary
            # (when back-filled).
            unresolved: list[str] = []
            for q in questions:
                addressed = False
                for cand in later:
                    text_parts = [str(cand.get("title", ""))]
                    cand_backfill = cand.get("_backfill") or {}
                    cs = cand_backfill.get("claim_summary")
                    if cs:
                        text_parts.append(str(cs))
                    body = str(cand.get("body", ""))[:candidate_text_chars]
                    text_parts.append(body)
                    candidate_text = "\n".join(text_parts)
                    if _question_addressed_by(q, candidate_text, threshold=threshold):
                        addressed = True
                        break
                if not addressed:
                    unresolved.append(q)

            if unresolved:
                result[card["path"]] = unresolved

    return result
