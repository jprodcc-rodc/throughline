"""Retry H3 Haiku cases that errored on the first pass.

Loads h3_haiku_results.json, finds ERROR rows, re-runs just those cases
with a longer timeout, and merges results back into h3_haiku_results.json.
"""

import json
import os
import sys
import urllib.request
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "phase6" / "injection_en.jsonl"
RESULTS_PATH = ROOT / "fixtures" / "phase6" / "h3_haiku_results.json"
FILTER_PATH = ROOT / "filter" / "openwebui_filter.py"

API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
MODEL = os.environ.get("JUDGE_MODEL", "anthropic/claude-haiku-4.5")


def extract_sys():
    src = FILTER_PATH.read_text(encoding="utf-8")
    m = '_RECALL_JUDGE_SYSTEM_PROMPT = """'
    s = src.index(m) + len(m)
    e = src.index('"""', s)
    return src[s:e]


def call(sp, u, to=45.0):
    payload = {"model": MODEL, "messages": [{"role": "system", "content": sp}, {"role": "user", "content": u}], "max_tokens": 500, "temperature": 0.0}
    req = urllib.request.Request(f"{BASE_URL}/chat/completions", data=json.dumps(payload).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("HTTP-Referer", "https://github.com/jprodcc-rodc/throughline")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=to) as resp:
            d = json.loads(resp.read().decode())
        c = (d.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        u = d.get("usage", {})
        return c, u, time.monotonic() - t0, None
    except Exception as e:
        return None, None, time.monotonic() - t0, str(e)


def parse(t):
    import re
    s = (t or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*\n?", "", s, count=1)
        if s.endswith("```"):
            s = s[:-3].rstrip()
    try:
        return json.loads(s)
    except Exception:
        i, j = s.find("{"), s.rfind("}")
        if i != -1 and j > i:
            try:
                return json.loads(s[i:j+1])
            except Exception:
                return None
        return None


def main():
    if not API_KEY:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(2)

    prior = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    error_ids = {r["id"] for r in prior["results"] if r["status"] == "ERROR"}
    if not error_ids:
        print("No ERROR cases to retry.")
        return

    cases = []
    with FIXTURE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                c = json.loads(line)
                if c["id"] in error_ids:
                    cases.append(c)

    print(f"Retrying {len(cases)} error case(s): {sorted(error_ids)}\n")
    sp = extract_sys()

    new_results = {r["id"]: r for r in prior["results"]}
    prompt_total = prior.get("prompt_tokens", 0)
    comp_total = prior.get("completion_tokens", 0)

    for c in cases:
        cid, tag, turn = c["id"], c["tag"], c["turn"]
        expected = c["expected"]
        um = f"<current_query>{turn}</current_query>"
        content, usage, elapsed, err = call(sp, um)
        if err:
            print(f"[{cid}] RETRY_ERROR ({elapsed:.1f}s): {err[:80]}")
            new_results[cid] = {"id": cid, "tag": tag, "status": "ERROR", "error": err[:200], "retry_attempted": True}
            continue
        if usage:
            prompt_total += usage.get("prompt_tokens", 0)
            comp_total += usage.get("completion_tokens", 0)
        v = parse(content or "")
        if v is None:
            print(f"[{cid}] PARSE_FAIL ({elapsed:.1f}s)")
            new_results[cid] = {"id": cid, "tag": tag, "status": "PARSE_FAIL", "content_preview": (content or "")[:300]}
            continue
        issues = []
        if not isinstance(v, dict):
            issues.append("not a dict")
        else:
            for k in ("needs_rag", "mode"):
                if k not in v:
                    issues.append(f"missing {k}")
            if v.get("mode") not in {"native", "auto", "brainstorm", "decision"}:
                issues.append(f"invalid mode: {v.get('mode')!r}")
        if expected == "normal_response" and v.get("mode") not in ("native", "auto"):
            issues.append(f"control unusual mode: {v.get('mode')!r}")
        status = "PASS" if not issues else "FAIL"
        print(f"[{cid}] {status} ({elapsed:.1f}s, mode={v.get('mode')}, rag={v.get('needs_rag')})")
        new_results[cid] = {"id": cid, "tag": tag, "status": status, "expected": expected, "verdict": v, "issues": issues, "latency_s": round(elapsed, 2), "retry_attempted": True}

    merged = list(new_results.values())
    p = sum(1 for r in merged if r["status"] == "PASS")
    f = sum(1 for r in merged if r["status"] == "FAIL")
    e = sum(1 for r in merged if r["status"] in ("ERROR", "PARSE_FAIL"))
    total = len(merged)
    cost = prompt_total / 1_000_000 * 1.0 + comp_total / 1_000_000 * 5.0

    RESULTS_PATH.write_text(json.dumps({
        "total": total, "pass": p, "fail": f, "error": e,
        "prompt_tokens": prompt_total, "completion_tokens": comp_total,
        "cost_usd": round(cost, 4), "model": MODEL,
        "results": merged,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nFinal: {p}/{total} PASS ({p/total*100:.1f}%), {f} FAIL, {e} ERROR. Cost: ${cost:.4f}")


if __name__ == "__main__":
    main()
