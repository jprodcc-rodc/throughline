"""Phase 6 H2: English bare-pronoun cheap-gate gap test.

Loads pronouns_en.jsonl, imports the shipped Filter's _cheap_gate directly
(no API), and reports which cases are handled cheaply vs fall through to
the (hypothetical) judge. The throughline English build deliberately strips
the Chinese bare-pronoun regex, so we expect real behavioral gaps vs
fixture expectations for bare-pronoun first-turn cases.

Usage:
    python fixtures/phase6/run_h2.py
"""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "phase6" / "pronouns_en.jsonl"
FILTER_PATH = ROOT / "filter" / "openwebui_filter.py"
RESULTS_PATH = ROOT / "fixtures" / "phase6" / "h2_results.json"


def load_filter_module():
    spec = importlib.util.spec_from_file_location("openwebui_filter", FILTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    mod = load_filter_module()
    Filter = mod.Filter
    f = Filter()

    cases = []
    with FIXTURE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                cases.append(json.loads(line))

    print(f"[setup] {len(cases)} cases, Filter loaded from {FILTER_PATH}\n")

    results = []
    matches = 0
    gaps = 0
    for i, c in enumerate(cases, 1):
        cid = c["id"]
        tag = c["tag"]
        turn = c["turn"]
        has_history = bool(c.get("context"))
        expected_calls_judge = c["should_call_judge"]

        handled, info = f._cheap_gate(turn, has_history=has_history)
        actually_calls_judge = not handled
        cheap_path = info.get("cheap_gate") if info else "judge"

        if actually_calls_judge == expected_calls_judge:
            status = "MATCH"
            matches += 1
        else:
            status = "GAP "
            gaps += 1

        print(
            f"[{i:02d}/{len(cases)}] {cid:6s} [{tag:30s}] "
            f"{status} | query={turn!r:40s} → cheap_path={cheap_path:12s} "
            f"(expected_judge={expected_calls_judge}, actual_judge={actually_calls_judge})"
        )
        results.append({
            "id": cid, "tag": tag, "turn": turn, "status": status.strip(),
            "expected_calls_judge": expected_calls_judge,
            "actual_calls_judge": actually_calls_judge,
            "cheap_path": cheap_path,
        })

    print("\n" + "=" * 70)
    print(f"H2 SUMMARY: {matches}/{len(cases)} MATCH ({matches/len(cases)*100:.1f}%), {gaps} GAP")
    print("Gaps = fixture expected cheap-skip but English Filter falls through to judge.")
    print("Root cause: throughline English build strips Chinese bare-pronoun regex")
    print("(openwebui_filter.py:760-764). Whether to add an English equivalent is a")
    print("product decision — for v0.1.0 cost is ~$0.003/turn on short bare-pronoun inputs.")

    RESULTS_PATH.write_text(
        json.dumps({
            "total": len(cases), "matches": matches, "gaps": gaps,
            "results": results,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nResults: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
