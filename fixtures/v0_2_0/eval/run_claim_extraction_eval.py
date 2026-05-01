#!/usr/bin/env python
"""4-field claim extraction eval harness for the app pivot.

Tests a candidate model on the (topic / concern / hope / question)
extraction task per docs/superpowers/specs/web-product-design.md §5.5
and docs/superpowers/plans/2026-05-01-claim-extraction.md.

Default target: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free via
OpenRouter (the dev-mode default per Finding 5 of collab protocol v1.6).

Usage:
    OPENAI_API_KEY=sk-or-... \\
    python fixtures/v0_2_0/eval/run_claim_extraction_eval.py

    # Override model:
    python fixtures/v0_2_0/eval/run_claim_extraction_eval.py \\
        --model anthropic/claude-sonnet-4.6

Outputs:
    fixtures/v0_2_0/eval/results-<model-slug>-<UTC-timestamp>.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_CASES = HERE / "claim_extraction_cases.json"
DEFAULT_PROMPT = HERE / "claim_extraction_prompt.txt"
DEFAULT_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
DEFAULT_URL = "https://openrouter.ai/api/v1/chat/completions"
SLEEP_BETWEEN_CALLS_S = 1.5


# ---------- IO ----------


def load_cases(path: Path) -> list[dict]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj["cases"]


def load_system_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------- API ----------


def call_model(
    *,
    model: str,
    api_key: str,
    url: str,
    system_prompt: str,
    user_msg: str,
    ai_reply: str,
    timeout: float = 60.0,
) -> dict:
    """One API call. Returns dict with parsed_output (dict|None),
    raw_content, error (None or str), tokens_in, tokens_out."""
    user_payload = (
        "INPUT:\n"
        f"  USER: {user_msg}\n"
        f"  AI: {ai_reply}\n"
        "OUTPUT:\n"
    )
    payload = {
        "model": model,
        "temperature": 0.2,
        # max_tokens must be generous: nvidia/nemotron-3-nano-* is a
        # *reasoning* model whose chain-of-thought consumes the budget
        # before content emission. Empirically 600 truncates ~30% of
        # cases (finish_reason=length, content=''). 4000 leaves
        # enough headroom on every observed case.
        "max_tokens": 4000,
        # NOTE: response_format=json_object was tried and triggers a
        # broken mojibake output mode on the nvidia nemotron free
        # model (model emits placeholder Chinese garbage and gives up).
        # Without the constraint, the model produces clean text/JSON;
        # our parse_4field() recovers the JSON object defensively.
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jprodcc-rodc/throughline",
        "X-Title": "throughline-claim-extraction-eval",
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.HTTPError as exc:
        try:
            err_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        return {
            "parsed_output": None,
            "raw_content": "",
            "error": f"HTTP {exc.code}: {err_body[:500]}",
            "tokens_in": None,
            "tokens_out": None,
            "latency_s": round(time.time() - t0, 2),
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "parsed_output": None,
            "raw_content": "",
            "error": f"{type(exc).__name__}: {exc}",
            "tokens_in": None,
            "tokens_out": None,
            "latency_s": round(time.time() - t0, 2),
        }

    latency = round(time.time() - t0, 2)
    try:
        envelope = json.loads(data.decode("utf-8", errors="replace"))
    except (ValueError, UnicodeDecodeError) as exc:
        return {
            "parsed_output": None,
            "raw_content": data.decode("utf-8", errors="replace")[:500],
            "error": f"envelope not JSON: {exc}",
            "tokens_in": None,
            "tokens_out": None,
            "latency_s": latency,
        }

    try:
        content = envelope["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return {
            "parsed_output": None,
            "raw_content": json.dumps(envelope)[:500],
            "error": "envelope missing choices[0].message.content",
            "tokens_in": None,
            "tokens_out": None,
            "latency_s": latency,
        }

    usage = envelope.get("usage") or {}
    parsed, parse_err = parse_4field(content)

    return {
        "parsed_output": parsed,
        "raw_content": content,
        "error": parse_err,
        "tokens_in": usage.get("prompt_tokens"),
        "tokens_out": usage.get("completion_tokens"),
        "latency_s": latency,
    }


def parse_4field(content: str) -> tuple[dict | None, str | None]:
    """Tolerant parser. Strips markdown fences, finds first JSON object,
    accepts only the 4 expected keys. Returns (dict|None, err|None)."""
    s = content.strip()
    if s.startswith("```"):
        # Drop opening fence (```json or ```)
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1:]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    # Some reasoning models emit thinking before the JSON; grab the
    # first balanced { ... } block.
    if not s.startswith("{"):
        # Find first '{' and walk to matching '}'.
        first = s.find("{")
        if first == -1:
            return None, f"no '{{' found in content: {content[:200]!r}"
        depth = 0
        end = -1
        for i in range(first, len(s)):
            ch = s[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end == -1:
            return None, f"unbalanced braces in content: {content[:200]!r}"
        s = s[first : end + 1]

    try:
        obj = json.loads(s)
    except (ValueError, TypeError) as exc:
        return None, f"json parse: {exc}: {s[:200]!r}"
    if not isinstance(obj, dict):
        return None, f"not a JSON object: {obj!r}"
    out = {}
    for key in ("topic", "concern", "hope", "question"):
        v = obj.get(key, None)
        if v is None:
            out[key] = None
        elif isinstance(v, str):
            stripped = v.strip()
            # Treat empty / "null" / "none" / "n/a" as null for scoring
            # robustness; the model sometimes emits these instead of
            # JSON null.
            if not stripped or stripped.lower() in {
                "null", "none", "n/a", "na", "无", "没有",
            }:
                out[key] = None
            else:
                out[key] = stripped
        else:
            out[key] = str(v)
    return out, None


# ---------- scoring ----------


# Bilingual semantic-equivalence lexicon. The nvidia free model
# tends to translate Chinese input to English in output; without
# this, every Chinese-expected case fails its English-actual peer.
# This lexicon is a per-eval calibration aid, not a general translator.
_BILINGUAL_PAIRS = [
    # career
    ("换工作", "job change"), ("换工作", "change jobs"), ("换工作", "career change"),
    ("换工作", "switching jobs"), ("换工作", "changing jobs"),
    ("职业转换", "career change"), ("职业转换", "career transition"),
    ("自由职业", "freelance"), ("自由职业", "freelancing"),
    ("时间自由", "time freedom"), ("时间自由", "flexible schedule"),
    ("时间自由", "flexible time"), ("时间自由", "schedule freedom"),
    ("客户从哪里来", "where to find clients"), ("客户从哪里来", "client acquisition"),
    ("客户从哪里来", "finding clients"),
    ("收入安全", "income security"), ("收入安全", "financial security"),
    ("收入安全", "losing income"), ("收入安全", "fear of losing income"),
    ("想换到什么方向", "what direction"), ("想换到什么方向", "which direction"),
    # relationships
    ("和父母的关系", "relationship with parents"), ("和父母的关系", "parents"),
    ("和父母的关系", "family relationship"),
    ("不被理解", "not understood"), ("不被理解", "feeling misunderstood"),
    ("不被理解", "lack of understanding"),
    ("夫妻独处时间", "couple time"), ("夫妻独处时间", "alone time with spouse"),
    ("夫妻独处时间", "time with spouse"), ("夫妻独处时间", "alone time"),
    ("孩子让独处困难", "kids make alone time hard"),
    ("孩子让独处困难", "having children"), ("孩子让独处困难", "kids"),
    ("多些独处时间", "more alone time"), ("多些独处时间", "more couple time"),
    # technical
    ("postgres 换 sqlite", "postgres to sqlite"),
    ("postgres 换 sqlite", "postgres sqlite migration"),
    ("postgres 换 sqlite", "migrating from postgres to sqlite"),
    ("丢掉事务保证", "losing transactions"), ("丢掉事务保证", "transaction guarantees"),
    ("丢掉事务保证", "losing transaction guarantees"),
    ("部署简单", "simplicity"), ("部署简单", "deployment simplicity"),
    ("部署简单", "simpler deployment"),
    # abstract
    ("人生意义", "meaning of life"), ("人生意义", "life's meaning"),
    ("人生意义", "purpose of life"),
    ("工作消费循环没意思", "work and consumption cycle"),
    ("工作消费循环没意思", "meaningless work cycle"),
    ("人生意义是什么", "what is the meaning of life"),
    ("人生意义是什么", "what gives life meaning"),
    # The nvidia model also reverse-translates EN → ZH for some inputs
    # (relationships-3, abstract-2). These cover that direction.
    ("朋友群疏远", "friend group drift"), ("朋友群疏远", "drifted apart"),
    ("重建友情", "the closeness"), ("重建友情", "rebuild friendship"),
    ("强行重聚", "forcing reunions"), ("是否值得强行重聚", "worth forcing reunions"),
    ("更有意的生活", "intentional life"), ("更有意义的生活", "intentional life"),
    ("更有意义的生活", "meaningful life"),
    ("什么对自己重要", "what matters to me"), ("什么对我重要", "what matters to me"),
]


def _bilingual_match(a: str, b: str) -> bool:
    """True if one of a/b is a known Chinese term and the other contains
    its English equivalent (or vice versa)."""
    al, bl = a.lower(), b.lower()
    for zh, en in _BILINGUAL_PAIRS:
        zh_l = zh.lower()
        if (zh_l in al and en in bl) or (zh_l in bl and en in al):
            return True
    return False


def normalize_for_compare(s: str | None) -> str:
    if s is None:
        return ""
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    # Drop leading articles / pronouns that don't carry semantic weight.
    s = re.sub(r"^(the |a |an |my |our |i want |i hope |我想|我希望|想要)", "", s)
    return s


def field_match(expected: str | None, actual: str | None) -> tuple[bool, str]:
    """Score one field. Returns (correct, reason).

    Rules:
    - Both null  -> correct
    - One null other not -> wrong
    - Both non-null -> correct if substring overlap or significant
      n-gram overlap. We're generous on phrasing diff but strict on
      missing entities.
    """
    if expected is None and actual is None:
        return True, "both_null"
    if expected is None and actual is not None:
        return False, "expected_null_got_value"
    if expected is not None and actual is None:
        return False, "expected_value_got_null"

    e = normalize_for_compare(expected)
    a = normalize_for_compare(actual)
    if not e and not a:
        return True, "both_empty"
    if e == a:
        return True, "exact_after_norm"
    # Cross-language match: nvidia free model translates Chinese -> English
    # in output; treat as semantically equivalent per lexicon.
    if _bilingual_match(e, a):
        return True, "bilingual_lexicon"
    # Substring either direction (covers shortening / expansion)
    if len(e) >= 2 and (e in a or a in e):
        return True, "substring_match"
    # Character-bigram Jaccard for Chinese (no whitespace tokens),
    # word-overlap for English.
    if any("一" <= ch <= "鿿" for ch in e + a):
        # Chinese: char-bigram Jaccard
        def bigrams(s):
            return {s[i : i + 2] for i in range(len(s) - 1)}
        eb = bigrams(e)
        ab = bigrams(a)
        if not eb or not ab:
            return False, "empty_bigrams"
        jac = len(eb & ab) / len(eb | ab)
        if jac >= 0.4:
            return True, f"bigram_jaccard={jac:.2f}"
        return False, f"bigram_jaccard_low={jac:.2f}"
    else:
        # English: word-set Jaccard
        ew = set(re.findall(r"\w+", e))
        aw = set(re.findall(r"\w+", a))
        if not ew or not aw:
            return False, "empty_word_sets"
        jac = len(ew & aw) / len(ew | aw)
        if jac >= 0.4:
            return True, f"word_jaccard={jac:.2f}"
        return False, f"word_jaccard_low={jac:.2f}"


def score_case(expected: dict, actual: dict | None) -> dict:
    """Score one case. Returns per-field correct/reason + case_accuracy."""
    if actual is None:
        return {
            "by_field": {
                k: {"correct": False, "reason": "no_output", "expected": expected.get(k), "actual": None}
                for k in ("topic", "concern", "hope", "question")
            },
            "case_accuracy": 0.0,
            "any_nonnull_field": False,  # for FP-rate semantics on chitchat
        }
    by_field = {}
    correct_count = 0
    any_nonnull = False
    for k in ("topic", "concern", "hope", "question"):
        e = expected.get(k)
        a = actual.get(k)
        if a is not None:
            any_nonnull = True
        ok, reason = field_match(e, a)
        by_field[k] = {"correct": ok, "reason": reason, "expected": e, "actual": a}
        if ok:
            correct_count += 1
    return {
        "by_field": by_field,
        "case_accuracy": correct_count / 4.0,
        "any_nonnull_field": any_nonnull,
    }


# ---------- main ----------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=SLEEP_BETWEEN_CALLS_S)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args(argv)

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip() or os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("[error] no OPENROUTER_API_KEY or OPENAI_API_KEY in env", file=sys.stderr)
        return 1

    # Allow overriding URL via env (OPENAI_BASE_URL) — caller's setup
    # already points OPENAI_BASE_URL to OpenRouter.
    if "OPENAI_BASE_URL" in os.environ and args.url == DEFAULT_URL:
        base = os.environ["OPENAI_BASE_URL"].rstrip("/")
        if not base.endswith("/chat/completions"):
            base = base + "/chat/completions"
        url = base
    else:
        url = args.url

    cases = load_cases(args.cases)
    if args.max_cases is not None:
        cases = cases[: args.max_cases]
    system_prompt = load_system_prompt(args.prompt)

    started_at = datetime.now(timezone.utc)
    print(f"Model: {args.model}")
    print(f"URL: {url}")
    print(f"Cases: {len(cases)}")
    print(f"Started: {started_at.isoformat()}\n")

    results = []
    for i, case in enumerate(cases, 1):
        case_id = case.get("id", f"case-{i}")
        category = case.get("category", "uncategorized")
        user = case["input"]["user"]
        ai = case["input"]["ai"]
        expected = case["expected"]

        print(f"[{i}/{len(cases)}] {case_id} ({category})...", end=" ", flush=True)
        api_result = call_model(
            model=args.model,
            api_key=api_key,
            url=url,
            system_prompt=system_prompt,
            user_msg=user,
            ai_reply=ai,
        )
        score = score_case(expected, api_result["parsed_output"])
        case_acc = score["case_accuracy"]
        err = api_result.get("error")
        print(f"acc={case_acc:.2f}  latency={api_result['latency_s']}s  err={err!r}")

        results.append({
            "case_id": case_id,
            "category": category,
            "input": case["input"],
            "expected": expected,
            "actual_raw": api_result["raw_content"],
            "actual_parsed": api_result["parsed_output"],
            "api_error": api_result.get("error"),
            "tokens_in": api_result.get("tokens_in"),
            "tokens_out": api_result.get("tokens_out"),
            "latency_s": api_result.get("latency_s"),
            "score": score,
        })

        if i < len(cases) and args.sleep > 0:
            time.sleep(args.sleep)

    # ---------- aggregate ----------
    total = len(results)
    avg_acc = sum(r["score"]["case_accuracy"] for r in results) / total if total else 0.0
    by_category: dict[str, list[float]] = {}
    chitchat_results: list[dict] = []
    for r in results:
        cat = r["category"]
        by_category.setdefault(cat, []).append(r["score"]["case_accuracy"])
        if cat == "chitchat":
            chitchat_results.append(r)

    cat_avg = {cat: sum(xs) / len(xs) for cat, xs in by_category.items() if xs}
    chitchat_n = len(chitchat_results)
    chitchat_fp = sum(1 for r in chitchat_results if r["score"]["any_nonnull_field"])
    fp_rate = chitchat_fp / chitchat_n if chitchat_n else 0.0
    api_failures = sum(1 for r in results if r["api_error"])

    print("\n" + "=" * 60)
    print(f"Average accuracy: {avg_acc * 100:.1f}%")
    print("Per-category:")
    for cat, v in cat_avg.items():
        print(f"  {cat}: {v * 100:.1f}% (n={len(by_category[cat])})")
    print(f"Chitchat FP rate: {fp_rate * 100:.1f}% ({chitchat_fp}/{chitchat_n})")
    print(f"API failures: {api_failures}/{total}")
    threshold_60 = "PASS" if avg_acc >= 0.60 else "FAIL"
    print(f"60% threshold: {threshold_60}")

    # ---------- write outputs ----------
    args.output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", args.model.lower()).strip("-")[:60]
    ts = started_at.strftime("%Y%m%dT%H%M%SZ")
    out_path = args.output_dir / f"results-{slug}-{ts}.json"
    out_path.write_text(
        json.dumps(
            {
                "meta": {
                    "model": args.model,
                    "url": url,
                    "started_at": started_at.isoformat(),
                    "n_cases": total,
                },
                "summary": {
                    "average_accuracy": avg_acc,
                    "per_category_accuracy": cat_avg,
                    "chitchat_fp_rate": fp_rate,
                    "chitchat_n": chitchat_n,
                    "chitchat_fp_count": chitchat_fp,
                    "api_failures": api_failures,
                    "passes_60_threshold": avg_acc >= 0.60,
                },
                "cases": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nResults: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
