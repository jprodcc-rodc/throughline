"""CLI driver for the topic-clustering accuracy experiment.

Walks the user's vault, loads ground-truth labels from JSON, runs
the clustering algorithm at the requested threshold(s), prints
the accuracy report. Used to determine whether the engineering
gate (≥75% pairwise accuracy on author's vault) passes — i.e.
whether the Reflection Layer daemon can ship.

Usage:

    python -m mcp_server.clustering_experiment \\
        --vault ~/ObsidianVault \\
        --ground-truth ground_truth.json \\
        --threshold 0.75

Or sweep multiple thresholds:

    python -m mcp_server.clustering_experiment \\
        --vault ~/ObsidianVault \\
        --ground-truth ground_truth.json \\
        --sweep 0.55,0.60,0.65,0.70,0.75,0.80

Ground-truth file format::

    {
      "cards": {
        "10_Tech/2026-01-15_pricing.md": "pricing_strategy",
        "20_Health/2026-04-02_keto.md": "keto_rebound",
        ...
      }
    }

Card paths are vault-relative. Labels are arbitrary strings; the
metric is "do clustering and ground truth agree on which pairs
share a label", not "did clustering pick the right name".

See `docs/TOPIC_CLUSTERING_EXPERIMENT.md` for the full walk-through
and how to produce a ground-truth file.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from mcp_server.clustering_accuracy import (
    AccuracyReport,
    evaluate,
    load_ground_truth,
)
from mcp_server.rag_client import (
    RAGClientError,
    RAGServerUnreachable,
    embed_batch,
)
from mcp_server.topic_clustering import (
    CardForClustering,
    cluster_cards,
    cluster_index,
)


_FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def load_card(md_path: Path, vault_root: Path) -> CardForClustering | None:
    """Parse a single .md file from the vault into a clustering
    input record. Returns None on parse failure (silently
    skipped — clustering doesn't need every card)."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    m = _FM_RE.match(text)
    if not m:
        # No frontmatter — treat full text as body, derive title
        # from filename
        title = md_path.stem.replace("_", " ").replace("-", " ")
        body = text
        existing_tags: tuple[str, ...] = ()
    else:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            return None
        title = str(fm.get("title", md_path.stem.replace("_", " ")))
        body = text[m.end():]
        tags_raw = fm.get("tags") or []
        existing_tags = tuple(
            str(t) for t in tags_raw
            if isinstance(t, str)
        )

    rel_path = str(md_path.relative_to(vault_root)).replace("\\", "/")
    return CardForClustering(
        path=rel_path,
        title=title.strip(),
        body=body.strip(),
        existing_tags=existing_tags,
    )


def load_vault_cards(vault_root: Path,
                      restrict_to: set[str] | None = None
                      ) -> list[CardForClustering]:
    """Walk vault for *.md, parse each, return cards.

    If `restrict_to` is provided, only include cards whose
    relative path is in that set — useful when ground truth covers
    a sample, not the whole vault.
    """
    if not vault_root.exists():
        raise FileNotFoundError(
            f"vault not found: {vault_root}"
        )
    out: list[CardForClustering] = []
    for md_path in vault_root.rglob("*.md"):
        if md_path.is_dir():
            continue
        rel = str(md_path.relative_to(vault_root)).replace("\\", "/")
        if restrict_to is not None and rel not in restrict_to:
            continue
        card = load_card(md_path, vault_root)
        if card is not None:
            out.append(card)
    return out


def run_experiment(
    vault_root: Path,
    truth_labels: dict[str, str],
    high_threshold: float,
    low_threshold: float = 0.55,
    body_chars: int = 300,
) -> AccuracyReport:
    """Single-threshold experiment. Returns the accuracy report.

    Loads cards restricted to the ground-truth set (no point
    clustering cards we can't measure against).
    """
    cards = load_vault_cards(
        vault_root, restrict_to=set(truth_labels.keys())
    )
    if not cards:
        raise RuntimeError(
            "no cards in vault matched the ground-truth paths. "
            "Check `--vault` points at the right directory and "
            "ground-truth keys are vault-relative."
        )

    # The real embedder via rag_server. Caller is responsible for
    # ensuring rag_server is running; we let RAGServerUnreachable
    # propagate with the existing helpful message.
    def _embed(texts: list[str]) -> list[list[float]]:
        return embed_batch(texts)

    clusters = cluster_cards(
        cards,
        embed_fn=_embed,
        high_threshold=high_threshold,
        low_threshold=low_threshold,
        body_chars=body_chars,
    )
    predicted = cluster_index(clusters)
    return evaluate(predicted, truth_labels)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m mcp_server.clustering_experiment",
        description=(
            "Topic-clustering accuracy experiment. Engineering "
            "gate for the Reflection Layer daemon (≥75% pairwise "
            "accuracy required before the daemon ships). See "
            "docs/TOPIC_CLUSTERING_EXPERIMENT.md."
        ),
    )
    parser.add_argument(
        "--vault", required=True,
        help="vault root directory (e.g. ~/ObsidianVault)",
    )
    parser.add_argument(
        "--ground-truth", required=True,
        help="JSON file mapping card relpath → topic label",
    )
    parser.add_argument(
        "--threshold", type=float, default=0.75,
        help="cosine similarity above which two cards are same "
             "topic (default: 0.75)",
    )
    parser.add_argument(
        "--low-threshold", type=float, default=0.55,
        help="cosine similarity below which two cards are "
             "definitely different (default: 0.55). "
             "Values in (low_threshold, threshold) are ambiguous "
             "and currently default to 'different' since this "
             "experiment doesn't use an LLM judge.",
    )
    parser.add_argument(
        "--sweep", type=str, default=None,
        help="comma-separated list of high thresholds to try "
             "(e.g. 0.60,0.65,0.70,0.75,0.80). Overrides "
             "--threshold.",
    )
    parser.add_argument(
        "--body-chars", type=int, default=300,
        help="card body characters included in embedding text "
             "(default: 300)",
    )
    args = parser.parse_args(argv)

    vault = Path(args.vault).expanduser().resolve()
    truth_path = Path(args.ground_truth).expanduser().resolve()
    truth_labels = load_ground_truth(truth_path)
    print(
        f"loaded {len(truth_labels)} ground-truth labels from {truth_path}"
    )
    print(f"vault: {vault}")
    print()

    thresholds = (
        [float(x) for x in args.sweep.split(",")]
        if args.sweep else [args.threshold]
    )

    best: tuple[float, AccuracyReport] | None = None
    for thr in thresholds:
        print(f"=== threshold = {thr:.2f} ===")
        try:
            report = run_experiment(
                vault, truth_labels,
                high_threshold=thr,
                low_threshold=args.low_threshold,
                body_chars=args.body_chars,
            )
        except RAGServerUnreachable as exc:
            print(
                f"ERROR: rag_server unreachable. {exc}",
                file=sys.stderr,
            )
            return 2
        except RAGClientError as exc:
            print(
                f"ERROR: rag_server error: {exc}",
                file=sys.stderr,
            )
            return 2
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(report)
        print()
        if best is None or report.pairwise_accuracy > best[1].pairwise_accuracy:
            best = (thr, report)

    if len(thresholds) > 1 and best is not None:
        thr, report = best
        gate = "PASS" if report.pairwise_accuracy >= 0.75 else "FAIL"
        print(
            f"best: threshold={thr:.2f}, "
            f"pairwise_accuracy={report.pairwise_accuracy:.3f}, "
            f"gate={gate}"
        )

    return 0 if (best and best[1].pairwise_accuracy >= 0.75) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
