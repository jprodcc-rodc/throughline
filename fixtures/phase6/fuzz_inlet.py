"""Phase 6 shape-mode inlet fuzz (ported from private repo bug_probes).

Zero-API adversarial body-shape fuzz on Filter.inlet(). Tests that the
shipped English Filter survives malformed / nested / oversized / None-typed
bodies without crashing. Covers shape attacks that would bypass any
prompt-level defense.

The --real variant (adversarial content appended to user queries) is
intentionally NOT ported to this repo — Phase 6 H3 Haiku-side already
exercises injection/roleplay/PII resistance against the RecallJudge,
which is the primary attack surface. Body-shape robustness is the
complementary concern.

Usage:
    python fixtures/phase6/fuzz_inlet.py
"""

import asyncio
import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILTER_PATH = ROOT / "filter" / "openwebui_filter.py"
RESULTS_PATH = ROOT / "fixtures" / "phase6" / "fuzz_inlet_results.json"


def load_filter_module():
    spec = importlib.util.spec_from_file_location("openwebui_filter", FILTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BODY_SHAPE_CASES = [
    ("empty body", {}),
    ("messages None", {"messages": None, "chat_id": "x"}),
    ("messages str", {"messages": "hello", "chat_id": "x"}),
    ("messages int", {"messages": 42, "chat_id": "x"}),
    ("messages nested list", {"messages": [["user", "hi"]], "chat_id": "x"}),
    ("missing chat_id", {"messages": [{"role": "user", "content": "hi"}]}),
    (
        "duplicate system msgs",
        {
            "messages": [
                {"role": "system", "content": "A"},
                {"role": "system", "content": "B"},
                {"role": "user", "content": "hi"},
            ],
            "chat_id": "x",
        },
    ),
    ("msg content None", {"messages": [{"role": "user", "content": None}], "chat_id": "x"}),
    ("msg content number", {"messages": [{"role": "user", "content": 42}], "chat_id": "x"}),
    ("msg content huge", {"messages": [{"role": "user", "content": "x" * 200000}], "chat_id": "x"}),
    ("no user msg", {"messages": [{"role": "assistant", "content": "hi"}], "chat_id": "x"}),
    (
        "40-turn hist",
        {
            "messages": [
                {"role": "user" if i % 2 else "assistant", "content": f"t{i}"}
                for i in range(40)
            ],
            "chat_id": "x",
        },
    ),
    # English-specific additions
    (
        "unicode rtl marker only",
        {"messages": [{"role": "user", "content": "\u202e\u202d"}], "chat_id": "x"},
    ),
    (
        "zero-width bomb",
        {"messages": [{"role": "user", "content": "hello" + "\u200b" * 500}], "chat_id": "x"},
    ),
    (
        "null bytes",
        {"messages": [{"role": "user", "content": "\x00\x00\x00continue"}], "chat_id": "x"},
    ),
    ("messages empty list", {"messages": [], "chat_id": "x"}),
    (
        "role missing",
        {"messages": [{"content": "hi"}], "chat_id": "x"},
    ),
]


async def run_shape():
    mod = load_filter_module()
    f = mod.Filter()
    crashed = []
    bad_shape = []

    for label, body in BODY_SHAPE_CASES:
        body_in = copy.deepcopy(body)
        try:
            out = await f.inlet(body_in, __user__=None, __event_emitter__=None)
        except Exception as e:
            crashed.append({"label": label, "type": type(e).__name__, "msg": str(e)[:200]})
            continue
        if not isinstance(out, dict):
            bad_shape.append({"label": label, "msg": f"out is {type(out).__name__}"})

    total = len(BODY_SHAPE_CASES)
    bugs = len(crashed) + len(bad_shape)

    print("=" * 70)
    print(f"fuzz_inlet --shape: {total} body cases")
    print("=" * 70)
    print(f"  crashed:   {len(crashed)}")
    print(f"  bad shape: {len(bad_shape)}")
    if crashed:
        print("--- CRASHED ---")
        for c in crashed:
            print(f"  [{c['label']}] {c['type']}: {c['msg']}")
    if bad_shape:
        print("--- BAD SHAPE ---")
        for b in bad_shape:
            print(f"  [{b['label']}] {b['msg']}")
    print(f"\nBUGS FOUND: {bugs}")

    RESULTS_PATH.write_text(
        json.dumps({
            "total": total, "bugs": bugs,
            "crashed": crashed, "bad_shape": bad_shape,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return bugs


def main():
    bugs = asyncio.run(run_shape())
    sys.exit(1 if bugs > 0 else 0)


if __name__ == "__main__":
    main()
