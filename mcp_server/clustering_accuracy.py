"""Accuracy metrics for the topic-clustering experiment.

Compares a clustering result against user-provided ground-truth
labels to produce the engineering-gate number: pairwise accuracy
≥75% on the maintainer's vault before shipping the Reflection
Pass daemon.

Three metrics, all computed without sklearn (kept dep-light):

1. **Pairwise accuracy** — for each pair of cards, did clustering
   agree with ground truth on whether they're in the same cluster?
   The headline metric the brief's gate is written against.

2. **Homogeneity** — are clustering's clusters pure with respect
   to ground truth? (Each predicted cluster contains cards from
   only one ground-truth cluster?)

3. **Completeness** — are ground-truth clusters preserved by
   clustering? (Cards from the same ground-truth cluster end up in
   the same predicted cluster?)

Homogeneity + completeness are the H/C/V-measure trio (V-measure
is their harmonic mean). We don't ship sklearn just for these —
the formulas are short.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AccuracyReport:
    """Result of comparing a clustering against ground truth.

    All metrics are floats in [0.0, 1.0] except `confusion`, which
    is a per-cluster breakdown for debugging false-positive cases.
    """
    pairwise_accuracy: float
    homogeneity: float
    completeness: float
    v_measure: float
    n_cards: int
    n_predicted_clusters: int
    n_truth_clusters: int
    pairs_total: int
    pairs_agreed: int
    pairs_false_positive: int  # predicted-same, truth-different
    pairs_false_negative: int  # predicted-different, truth-same

    def __str__(self) -> str:
        gate = "PASS" if self.pairwise_accuracy >= 0.75 else "FAIL"
        return (
            f"AccuracyReport ({gate} the 75% gate)\n"
            f"  pairwise_accuracy:   {self.pairwise_accuracy:.3f}\n"
            f"  homogeneity:         {self.homogeneity:.3f}\n"
            f"  completeness:        {self.completeness:.3f}\n"
            f"  v_measure:           {self.v_measure:.3f}\n"
            f"  cards:               {self.n_cards}\n"
            f"  predicted clusters:  {self.n_predicted_clusters}\n"
            f"  truth clusters:      {self.n_truth_clusters}\n"
            f"  pairs total:         {self.pairs_total}\n"
            f"  pairs agreed:        {self.pairs_agreed}\n"
            f"  false positives:     {self.pairs_false_positive}  "
            f"(predicted-same but truth-different — these cause "
            f"false-positive contradictions)\n"
            f"  false negatives:     {self.pairs_false_negative}  "
            f"(predicted-different but truth-same — these cause "
            f"missed Open Threads)"
        )


def load_ground_truth(path: Path) -> dict[str, str]:
    """Read ground truth from JSON or YAML-shaped JSON.

    Expected shape::

        {
          "cards": {
            "<card-path-1>": "<topic-label-1>",
            "<card-path-2>": "<topic-label-2>",
            ...
          }
        }

    Or the top-level dict directly:

        {
          "<card-path>": "<topic-label>",
          ...
        }
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "cards" in raw and isinstance(raw["cards"], dict):
        return {str(k): str(v) for k, v in raw["cards"].items()}
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items()}
    raise ValueError(
        f"ground truth at {path} must be a dict (or a dict with `cards` key)"
    )


def compute_pairwise_accuracy(
    predicted_index: dict[str, int],
    truth_labels: dict[str, str],
) -> tuple[float, int, int, int, int]:
    """For each card pair, check if clustering and ground truth
    agree on same-vs-different cluster membership.

    Returns:
        (accuracy, total_pairs, agreed_pairs, false_positive_pairs,
         false_negative_pairs)
    """
    paths = sorted(set(predicted_index) & set(truth_labels))
    if len(paths) < 2:
        return 1.0, 0, 0, 0, 0

    total = 0
    agreed = 0
    false_pos = 0  # predicted-same, truth-different
    false_neg = 0  # predicted-different, truth-same

    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            pi, pj = paths[i], paths[j]
            pred_same = predicted_index[pi] == predicted_index[pj]
            truth_same = truth_labels[pi] == truth_labels[pj]
            total += 1
            if pred_same == truth_same:
                agreed += 1
            elif pred_same and not truth_same:
                false_pos += 1
            else:
                false_neg += 1

    accuracy = agreed / total if total else 1.0
    return accuracy, total, agreed, false_pos, false_neg


def _entropy(label_counts: dict[object, int], total: int) -> float:
    """Shannon entropy in bits of a label distribution."""
    if total == 0:
        return 0.0
    h = 0.0
    for c in label_counts.values():
        if c == 0:
            continue
        p = c / total
        h -= p * math.log2(p)
    return h


def _conditional_entropy(
    a_labels: list[object],
    b_labels: list[object],
) -> float:
    """H(A|B) — entropy of A given B."""
    n = len(a_labels)
    if n == 0:
        return 0.0
    # P(B=b) and P(A=a, B=b)
    joint: dict[tuple[object, object], int] = {}
    b_marg: dict[object, int] = {}
    for a, b in zip(a_labels, b_labels):
        joint[(a, b)] = joint.get((a, b), 0) + 1
        b_marg[b] = b_marg.get(b, 0) + 1

    h = 0.0
    for (a, b), nab in joint.items():
        nb = b_marg[b]
        # contribution: P(a,b) * log( P(b)/P(a,b) )
        # = (nab/n) * log(nb/nab)
        h += (nab / n) * math.log2(nb / nab) if nab > 0 else 0.0
    return h


def compute_homogeneity_completeness(
    predicted_index: dict[str, int],
    truth_labels: dict[str, str],
) -> tuple[float, float, float]:
    """Standard homogeneity / completeness / V-measure.

    Definitions (per Rosenberg & Hirschberg 2007):
      homogeneity   = 1 - H(C|K) / H(C)
      completeness  = 1 - H(K|C) / H(K)
      V-measure     = 2 * h * c / (h + c)

    Where C = ground truth clustering, K = predicted clustering.
    H(C|K) reads "entropy of C given K".
    """
    paths = sorted(set(predicted_index) & set(truth_labels))
    if not paths:
        return 1.0, 1.0, 1.0

    pred_seq: list[object] = [predicted_index[p] for p in paths]
    truth_seq: list[object] = [truth_labels[p] for p in paths]

    pred_counts: dict[object, int] = {}
    truth_counts: dict[object, int] = {}
    for p in pred_seq:
        pred_counts[p] = pred_counts.get(p, 0) + 1
    for t in truth_seq:
        truth_counts[t] = truth_counts.get(t, 0) + 1

    n = len(paths)
    h_truth = _entropy(truth_counts, n)
    h_pred = _entropy(pred_counts, n)

    h_truth_given_pred = _conditional_entropy(truth_seq, pred_seq)
    h_pred_given_truth = _conditional_entropy(pred_seq, truth_seq)

    homogeneity = (
        1.0 - h_truth_given_pred / h_truth if h_truth > 0 else 1.0
    )
    completeness = (
        1.0 - h_pred_given_truth / h_pred if h_pred > 0 else 1.0
    )
    if homogeneity + completeness > 0:
        v_measure = 2 * homogeneity * completeness / (
            homogeneity + completeness
        )
    else:
        v_measure = 0.0
    return homogeneity, completeness, v_measure


def evaluate(
    predicted_index: dict[str, int],
    truth_labels: dict[str, str],
) -> AccuracyReport:
    """Run all metrics + return a structured report."""
    paths = sorted(set(predicted_index) & set(truth_labels))
    n_cards = len(paths)

    pred_clusters = {predicted_index[p] for p in paths}
    truth_clusters = {truth_labels[p] for p in paths}

    accuracy, total, agreed, fp, fn = compute_pairwise_accuracy(
        predicted_index, truth_labels
    )
    h, c, v = compute_homogeneity_completeness(
        predicted_index, truth_labels
    )

    return AccuracyReport(
        pairwise_accuracy=accuracy,
        homogeneity=h,
        completeness=c,
        v_measure=v,
        n_cards=n_cards,
        n_predicted_clusters=len(pred_clusters),
        n_truth_clusters=len(truth_clusters),
        pairs_total=total,
        pairs_agreed=agreed,
        pairs_false_positive=fp,
        pairs_false_negative=fn,
    )
