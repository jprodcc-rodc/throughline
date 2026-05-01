#!/usr/bin/env python
"""3-class intent classifier eval harness.

Tests the candidate dev model on the chitchat / thoughtful / factual
classification task per `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` §C-4
and `docs/superpowers/plans/2026-05-01-intent-classifier.md`.

Default target: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free via
OpenRouter (the dev-mode model lock per the plan + collab protocol v1.6).

The runner imports `app.shared.intent.classify` directly — no HTTP
round-trip — so it tests the same code path the chat server uses.

Usage:
    OPENAI_API_KEY=sk-or-... \\
    python fixtures/v0_2_0/eval/run_intent_eval.py

    # Skip rate-limit sleep for fast local iteration:
    python fixtures/v0_2_0/eval/run_intent_eval.py --sleep 0

Outputs:
    fixtures/v0_2_0/eval/results-intent-<model-slug>-<UTC-timestamp>.json

Schema of result file:
    {
      "meta": {model, url, started_at, n_cases},
      "summary": {
        "overall_accuracy": float,
        "per_class": {
          "chitchat": {precision, recall, f1, n},
          "thoughtful": {...},
          "factual": {...}
        },
        "confusion_matrix": {expected: {predicted: count}},
        "per_boundary_category_accuracy": {category: accuracy},
        "asymmetric_gate": {
          "overall_accuracy_passes": bool,
          "thoughtful_recall_passes": bool,
          "chitchat_precision_passes": bool,
          "factual_recall_passes": bool,
          "all_pass": bool
        },
        "api_failures": int
      },
      "cases": [{case_id, expected, actual, source, confidence, raw, ...}]
    }
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Make sure the repo root is on sys.path so `app.shared.intent` imports
# whether you launch from the repo root or from somewhere else.
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.shared.intent import IntentClass, classify  # noqa: E402

DEFAULT_CASES = HERE / "intent_cases.json"
DEFAULT_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
SLEEP_BETWEEN_CALLS_S = 1.5
GATE_OVERALL_ACCURACY = 0.85
GATE_THOUGHTFUL_RECALL = 0.90
GATE_CHITCHAT_PRECISION = 0.75
GATE_FACTUAL_RECALL = 0.85


# ── IO ────────────────────────────────────────────────────────────


def load_cases(path: Path) -> list[dict]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj["cases"]


# ── confusion matrix + metrics ────────────────────────────────────


def compute_metrics(results: list[dict]) -> dict[str, Any]:
    """Build confusion matrix + per-class precision/recall + overall."""
    classes = ["chitchat", "thoughtful", "factual"]
    cm = {e: {p: 0 for p in classes} for e in classes}
    correct = 0
    total = 0
    for r in results:
        e = r["expected_class"]
        p = r["predicted_class"]
        if e not in classes or p not in classes:
            continue
        cm[e][p] += 1
        total += 1
        if e == p:
            correct += 1

    overall = correct / total if total else 0.0

    per_class: dict[str, dict[str, float | int]] = {}
    for c in classes:
        tp = cm[c][c]
        fp = sum(cm[other][c] for other in classes if other != c)
        fn = sum(cm[c][other] for other in classes if other != c)
        n = tp + fn
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) else 0.0
        )
        per_class[c] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "n": n,
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }

    # Asymmetric gate per plan §"Locked decisions".
    gate = {
        "overall_accuracy_passes": overall >= GATE_OVERALL_ACCURACY,
        "thoughtful_recall_passes":
            per_class["thoughtful"]["recall"] >= GATE_THOUGHTFUL_RECALL,
        "chitchat_precision_passes":
            per_class["chitchat"]["precision"] >= GATE_CHITCHAT_PRECISION,
        "factual_recall_passes":
            per_class["factual"]["recall"] >= GATE_FACTUAL_RECALL,
    }
    gate["all_pass"] = all(gate.values())

    # Per-boundary-category accuracy (helps spot if the classifier
    # flunks specifically on, say, short_thoughtful).
    by_cat: dict[str, list[bool]] = {}
    for r in results:
        cat = r.get("category", "core")
        by_cat.setdefault(cat, []).append(
            r["expected_class"] == r["predicted_class"]
        )
    cat_acc = {
        cat: {
            "accuracy": sum(xs) / len(xs) if xs else 0.0,
            "n": len(xs),
            "correct": sum(xs),
        }
        for cat, xs in by_cat.items()
    }

    api_failures = sum(1 for r in results if r.get("source") == "fallback")

    return {
        "overall_accuracy": overall,
        "per_class": per_class,
        "confusion_matrix": cm,
        "per_boundary_category_accuracy": cat_acc,
        "asymmetric_gate": gate,
        "api_failures": api_failures,
        "n_total": total,
        "n_correct": correct,
    }


# ── CLI ───────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help="Recorded in the result file meta. The "
                             "actual model used is whatever "
                             "_resolve_llm_config() resolves.")
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=SLEEP_BETWEEN_CALLS_S)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args(argv)

    api_key = (
        os.environ.get("OPENROUTER_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
    )
    if not api_key:
        print(
            "[error] no OPENROUTER_API_KEY or OPENAI_API_KEY in env",
            file=sys.stderr,
        )
        return 1

    cases = load_cases(args.cases)
    if args.max_cases is not None:
        cases = cases[: args.max_cases]

    started_at = datetime.now(timezone.utc)
    print(f"Model (recorded): {args.model}")
    print(f"Cases: {len(cases)}")
    print(f"Started: {started_at.isoformat()}\n")

    results = []
    for i, case in enumerate(cases, 1):
        case_id = case["id"]
        category = case.get("category", "core")
        message = case["message"]
        expected = case["expected_class"]

        print(
            f"[{i}/{len(cases)}] {case_id} ({category}, exp={expected})...",
            end=" ", flush=True,
        )
        t0 = time.time()
        try:
            r = classify(message)
        except Exception as e:
            print(f"EXCEPTION: {type(e).__name__}: {e}")
            results.append({
                "case_id": case_id,
                "category": category,
                "message": message,
                "expected_class": expected,
                "predicted_class": "thoughtful",  # fallback bias
                "confidence": 0.0,
                "source": "fallback",
                "raw": None,
                "latency_s": round(time.time() - t0, 2),
                "exception": f"{type(e).__name__}: {e}",
                "correct": expected == "thoughtful",
            })
            continue
        latency = round(time.time() - t0, 2)
        ok = r.intent.value == expected
        mark = "OK" if ok else "X"
        print(
            f"{mark} pred={r.intent.value} conf={r.confidence:.2f} "
            f"src={r.source} t={latency}s",
        )

        results.append({
            "case_id": case_id,
            "category": category,
            "message": message,
            "expected_class": expected,
            "predicted_class": r.intent.value,
            "confidence": r.confidence,
            "source": r.source,
            "raw": r.raw,
            "latency_s": latency,
            "correct": ok,
        })

        # Sleep between calls only when the call actually hit the
        # network. Short-circuit cases don't need pacing.
        if (
            i < len(cases)
            and args.sleep > 0
            and r.source != "short_circuit"
        ):
            time.sleep(args.sleep)

    metrics = compute_metrics(results)

    # ── print summary ──
    print("\n" + "=" * 70)
    print(f"Overall accuracy: {metrics['overall_accuracy'] * 100:.1f}%  "
          f"({metrics['n_correct']}/{metrics['n_total']})")
    print()
    print("Per-class metrics:")
    for c in ("chitchat", "thoughtful", "factual"):
        m = metrics["per_class"][c]
        print(
            f"  {c:11s}  precision={m['precision'] * 100:5.1f}%  "
            f"recall={m['recall'] * 100:5.1f}%  f1={m['f1'] * 100:5.1f}%  "
            f"(n={m['n']} tp={m['tp']} fp={m['fp']} fn={m['fn']})",
        )
    print()
    print("Confusion matrix (rows=expected, cols=predicted):")
    classes = ("chitchat", "thoughtful", "factual")
    print(f"  {'':12s}" + "".join(f"{c:>12s}" for c in classes))
    for e in classes:
        row = metrics["confusion_matrix"][e]
        print(f"  {e:12s}" + "".join(f"{row[p]:>12d}" for p in classes))
    print()
    print("Per-boundary-category accuracy:")
    for cat, m in sorted(metrics["per_boundary_category_accuracy"].items()):
        print(
            f"  {cat:22s}  {m['accuracy'] * 100:5.1f}%  "
            f"(n={m['n']}, correct={m['correct']})",
        )
    print()
    print("Asymmetric gate:")
    g = metrics["asymmetric_gate"]
    overall = metrics["overall_accuracy"]
    pc = metrics["per_class"]
    flag = lambda b: "PASS" if b else "FAIL"  # noqa: E731
    print(f"  overall_accuracy >= {GATE_OVERALL_ACCURACY:.2f}    "
          f"actual={overall:.3f}  {flag(g['overall_accuracy_passes'])}")
    print(f"  thoughtful recall >= {GATE_THOUGHTFUL_RECALL:.2f}   "
          f"actual={pc['thoughtful']['recall']:.3f}  "
          f"{flag(g['thoughtful_recall_passes'])}")
    print(f"  chitchat precision >= {GATE_CHITCHAT_PRECISION:.2f}  "
          f"actual={pc['chitchat']['precision']:.3f}  "
          f"{flag(g['chitchat_precision_passes'])}")
    print(f"  factual recall >= {GATE_FACTUAL_RECALL:.2f}      "
          f"actual={pc['factual']['recall']:.3f}  "
          f"{flag(g['factual_recall_passes'])}")
    print(f"  ALL FOUR: {flag(g['all_pass'])}")
    print()
    print(f"API failures (source=fallback): {metrics['api_failures']}/"
          f"{metrics['n_total']}")

    # ── write outputs ──
    args.output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", args.model.lower()).strip("-")[:60]
    ts = started_at.strftime("%Y%m%dT%H%M%SZ")
    out_path = args.output_dir / f"results-intent-{slug}-{ts}.json"
    out_path.write_text(
        json.dumps(
            {
                "meta": {
                    "model": args.model,
                    "started_at": started_at.isoformat(),
                    "n_cases": len(results),
                    "gate_thresholds": {
                        "overall_accuracy": GATE_OVERALL_ACCURACY,
                        "thoughtful_recall": GATE_THOUGHTFUL_RECALL,
                        "chitchat_precision": GATE_CHITCHAT_PRECISION,
                        "factual_recall": GATE_FACTUAL_RECALL,
                    },
                },
                "summary": metrics,
                "cases": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nResults: {out_path}")
    return 0 if metrics["asymmetric_gate"]["all_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
