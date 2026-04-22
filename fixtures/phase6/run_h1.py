"""Phase 6 H1 runner: English RecallJudge classification drift test.

Loads recall_judge_en.jsonl, calls the real Haiku via OpenRouter with the
shipped _RECALL_JUDGE_SYSTEM_PROMPT, and reports per-case PASS/FAIL plus
aggregate stats.

Usage:
    cd throughline repo root
    OPENAI_API_KEY=... python fixtures/phase6/run_h1.py
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "fixtures" / "phase6" / "recall_judge_en.jsonl"
FILTER_PATH = ROOT / "filter" / "openwebui_filter.py"
RESULTS_PATH = ROOT / "fixtures" / "phase6" / "h1_results.json"

API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
MODEL = os.environ.get("JUDGE_MODEL", "anthropic/claude-haiku-4.5")


def extract_system_prompt() -> str:
    src = FILTER_PATH.read_text(encoding="utf-8")
    marker = '_RECALL_JUDGE_SYSTEM_PROMPT = """'
    start = src.index(marker) + len(marker)
    end = src.index('"""', start)
    return src[start:end]


def build_user_msg(context: list, current_query: str) -> str:
    parts = []
    hist = [m for m in context if m.get("role") in ("user", "assistant")]
    hist = hist[-6:]
    if hist:
        lines = [f"{h['role']}: {(h['content'] or '')[:300]}" for h in hist]
        parts.append("<recent_history>\n" + "\n".join(lines) + "\n</recent_history>")
    parts.append(f"<current_query>{current_query}</current_query>")
    return "\n".join(parts)


def call_judge(system_prompt: str, user_msg: str, timeout: float = 15.0):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 500,
        "temperature": 0.0,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/chat/completions", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("HTTP-Referer", "https://github.com/jprodcc-rodc/throughline")
    req.add_header("X-Title", "Throughline-Phase6-H1")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        usage = data.get("usage", {})
        return content, usage, time.monotonic() - t0, None
    except Exception as e:
        return None, None, time.monotonic() - t0, str(e)


def parse_json_from_content(content: str):
    """Tolerant JSON parse: accept raw JSON or ```json ... ``` fenced."""
    s = content.strip()
    if s.startswith("```"):
        lines = s.splitlines()
        inner = []
        seen_fence = False
        for ln in lines:
            if ln.strip().startswith("```"):
                if seen_fence:
                    break
                seen_fence = True
                continue
            if seen_fence:
                inner.append(ln)
        s = "\n".join(inner).strip()
    try:
        return json.loads(s)
    except Exception:
        # try to extract the first {...} block
        i = s.find("{")
        j = s.rfind("}")
        if i != -1 and j > i:
            try:
                return json.loads(s[i : j + 1])
            except Exception:
                return None
        return None


def match(expected: dict, verdict: dict) -> tuple[bool, list[str]]:
    mismatches = []
    # mode comparison: expected has "mode"; verdict has "mode"
    for key in ("needs_rag", "mode"):
        if key in expected:
            e = expected[key]
            v = verdict.get(key)
            if e != v:
                mismatches.append(f"{key}: expected={e!r} got={v!r}")
    # aggregate / topic_shift: only check if expected set
    for key in ("aggregate", "topic_shift"):
        if key in expected:
            e = bool(expected[key])
            v = bool(verdict.get(key, False))
            if e != v:
                mismatches.append(f"{key}: expected={e} got={v}")
    return (len(mismatches) == 0, mismatches)


def main():
    if not API_KEY:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(2)

    system_prompt = extract_system_prompt()
    print(f"[setup] system prompt: {len(system_prompt)} chars, model: {MODEL}")
    print(f"[setup] fixture: {FIXTURE}")

    cases = []
    with FIXTURE.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    print(f"[setup] {len(cases)} cases to run\n")

    results = []
    pass_ct = 0
    fail_ct = 0
    err_ct = 0
    prompt_tokens_total = 0
    completion_tokens_total = 0

    for idx, case in enumerate(cases, 1):
        cid = case["id"]
        tag = case.get("tag", "")
        turn = case["turn"]
        context = case.get("context", [])
        expected = case["expected"]

        user_msg = build_user_msg(context, turn)
        content, usage, elapsed, err = call_judge(system_prompt, user_msg)

        if err:
            err_ct += 1
            print(f"[{idx:02d}/{len(cases)}] {cid:6s} [{tag:35s}] ERROR ({elapsed:.1f}s): {err[:80]}")
            results.append({"id": cid, "tag": tag, "status": "ERROR", "error": err[:200]})
            continue

        if usage:
            prompt_tokens_total += usage.get("prompt_tokens", 0)
            completion_tokens_total += usage.get("completion_tokens", 0)

        verdict = parse_json_from_content(content or "")
        if verdict is None:
            err_ct += 1
            print(f"[{idx:02d}/{len(cases)}] {cid:6s} [{tag:35s}] PARSE_FAIL ({elapsed:.1f}s): {(content or '')[:80]}")
            results.append({"id": cid, "tag": tag, "status": "PARSE_FAIL", "content": (content or "")[:500]})
            continue

        ok, mismatches = match(expected, verdict)
        if ok:
            pass_ct += 1
            status = "PASS"
            mm_str = ""
        else:
            fail_ct += 1
            status = "FAIL"
            mm_str = " | " + "; ".join(mismatches)
        conf = verdict.get("confidence", None)
        print(f"[{idx:02d}/{len(cases)}] {cid:6s} [{tag:35s}] {status} ({elapsed:.1f}s, conf={conf}){mm_str}")
        results.append({
            "id": cid, "tag": tag, "status": status,
            "expected": expected, "verdict": verdict,
            "mismatches": mismatches, "latency_s": round(elapsed, 2),
        })

    total = len(cases)
    print("\n" + "=" * 60)
    print(f"SUMMARY: {pass_ct}/{total} PASS ({pass_ct / total * 100:.1f}%), {fail_ct} FAIL, {err_ct} ERROR")
    print(f"Tokens: prompt={prompt_tokens_total}, completion={completion_tokens_total}")
    # Haiku 4.5 pricing (OpenRouter published): $1/Mtok in, $5/Mtok out as of 2026-04
    cost_usd = prompt_tokens_total / 1_000_000 * 1.0 + completion_tokens_total / 1_000_000 * 5.0
    print(f"Approx cost: ${cost_usd:.4f}")

    RESULTS_PATH.write_text(json.dumps({
        "total": total, "pass": pass_ct, "fail": fail_ct, "error": err_ct,
        "prompt_tokens": prompt_tokens_total, "completion_tokens": completion_tokens_total,
        "cost_usd": round(cost_usd, 4),
        "model": MODEL,
        "results": results,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Results: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
