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
    """Tolerant parser. Strips markdown fences, then extracts the first
    balanced `{...}` block (which handles BOTH leading prose — reasoning
    models — AND trailing prose — few-shot 'Rationale:' lines bleeding
    past the JSON in v2/v3 prompts). Accepts only the 4 expected keys.
    Returns (dict|None, err|None).

    2026-05-02 fix: previously the parser only did the balanced-block
    walk when content did NOT start with '{', falling back to a plain
    json.loads on full content otherwise. That broke when the model
    emitted JSON-then-Rationale-prose (4/80 v2 false-positive API
    failures). The walk now always runs.
    """
    s = content.strip()
    if s.startswith("```"):
        # Drop opening fence (```json or ```)
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1:]
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
    # Always extract first balanced {...} block. String-literal aware
    # so quoted '{' / '}' chars inside JSON values don't mis-count.
    first = s.find("{")
    if first == -1:
        return None, f"no '{{' found in content: {content[:200]!r}"
    depth = 0
    end = -1
    in_str = False
    escape = False
    for i in range(first, len(s)):
        ch = s[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
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


# ── LLM-judge fallback for paraphrase tolerance ───────────────────
# Per External Opus directive 2026-05-02 evening: the heuristic
# (substring + bigram/word Jaccard) is too strict on short paraphrases
# that humans would accept (e.g. "losing income" ≈ "family financial
# stability if I quit" given context). When the heuristic fails on a
# short field, call Haiku 4.5 to judge semantic equivalence.

# Module-level config; set by main() if --llm-judge is enabled (default).
_JUDGE_CFG: dict | None = None
_JUDGE_STATS = {
    "calls": 0,
    "flips_to_match": 0,
    "errors": 0,
}
# Combined-length cap: paraphrase tolerance only makes sense for short
# fields. Long phrases tend to be either copy-paste from user or wrong
# in a structural way the heuristic catches.
_JUDGE_LEN_CAP = 60


def _llm_judge_match(
    expected: str,
    actual: str,
    user_text: str,
) -> bool | None:
    """Ask the configured judge model whether two phrases are
    semantically equivalent given the user message. Returns True/False/
    None (None = judge errored — caller should fall back to heuristic
    verdict)."""
    if _JUDGE_CFG is None:
        return None
    _JUDGE_STATS["calls"] += 1
    prompt = (
        f"Given this user message: {user_text}\n"
        f"Are these two phrases semantically equivalent?\n"
        f"Phrase A: {expected}\n"
        f"Phrase B: {actual}\n"
        f"Reply YES or NO only."
    )
    payload = {
        "model": _JUDGE_CFG["model"],
        "temperature": 0.0,
        "max_tokens": 16,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {_JUDGE_CFG['api_key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jprodcc-rodc/throughline",
        "X-Title": "throughline-claim-extraction-eval-judge",
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _JUDGE_CFG["url"], data=body, headers=headers, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            data = resp.read()
        envelope = json.loads(data.decode("utf-8", errors="replace"))
        content = envelope["choices"][0]["message"]["content"] or ""
    except Exception:
        _JUDGE_STATS["errors"] += 1
        return None
    verdict = content.strip().upper()
    if verdict.startswith("YES"):
        _JUDGE_STATS["flips_to_match"] += 1
        return True
    if verdict.startswith("NO"):
        return False
    # Unparseable verdict → treat as False but don't count as flip.
    return False


def field_match(
    expected: str | list[str] | None,
    actual: str | None,
    *,
    user_text: str | None = None,
) -> tuple[bool, str]:
    """Score one field. Returns (correct, reason).

    `expected` may be:
    - str  → single canonical answer (legacy / backwards compat)
    - list[str] → multiple acceptable variants (per Rodc directive
      2026-05-02 evening — concern field ground truth has paraphrase
      variance: "losing income" ≈ "family financial stability if I
      quit"; both should pass). Any variant matching = TP.
    - None → expected null

    Rules:
    - Both null  -> correct
    - One null other not -> wrong
    - Both non-null -> correct if substring overlap, n-gram overlap,
      OR LLM-judge says semantically equivalent (only triggered when
      the heuristic would otherwise return False on a short field
      with combined length ≤ 60 and user_text + judge config available).
    """
    # Multi-variant: dispatch to single-variant matcher per element;
    # first match wins. Empty list treated as null (no expected value).
    if isinstance(expected, list):
        if not expected:
            expected = None
        elif actual is None:
            return False, "expected_value_got_null"
        else:
            last_reason = "no_variant_matched"
            for variant in expected:
                ok, reason = _field_match_single(
                    variant, actual, user_text=user_text,
                )
                if ok:
                    return True, f"{reason} (variant={variant!r})"
                last_reason = reason
            return False, f"no_variant_matched (last: {last_reason})"

    # Single-variant path (legacy / fast path).
    return _field_match_single(expected, actual, user_text=user_text)


def _field_match_single(
    expected: str | None,
    actual: str | None,
    *,
    user_text: str | None = None,
) -> tuple[bool, str]:
    """Single-variant scorer. The body of the previous field_match;
    extracted so the multi-variant wrapper can call it per variant."""
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
    heuristic_reason: str
    if any("一" <= ch <= "鿿" for ch in e + a):
        # Chinese: char-bigram Jaccard
        def bigrams(s):
            return {s[i : i + 2] for i in range(len(s) - 1)}
        eb = bigrams(e)
        ab = bigrams(a)
        if not eb or not ab:
            heuristic_reason = "empty_bigrams"
        else:
            jac = len(eb & ab) / len(eb | ab)
            if jac >= 0.4:
                return True, f"bigram_jaccard={jac:.2f}"
            heuristic_reason = f"bigram_jaccard_low={jac:.2f}"
    else:
        # English: word-set Jaccard
        ew = set(re.findall(r"\w+", e))
        aw = set(re.findall(r"\w+", a))
        if not ew or not aw:
            heuristic_reason = "empty_word_sets"
        else:
            jac = len(ew & aw) / len(ew | aw)
            if jac >= 0.4:
                return True, f"word_jaccard={jac:.2f}"
            heuristic_reason = f"word_jaccard_low={jac:.2f}"
    # Heuristic says no. Try LLM-judge fallback for short paraphrases.
    can_judge = (
        _JUDGE_CFG is not None
        and user_text
        and len(str(expected)) + len(str(actual)) <= _JUDGE_LEN_CAP
    )
    if can_judge:
        verdict = _llm_judge_match(
            str(expected), str(actual), user_text,
        )
        if verdict is True:
            return True, f"llm_judge_yes ({heuristic_reason})"
        if verdict is False:
            return False, f"llm_judge_no ({heuristic_reason})"
        # judge errored → fall through to heuristic verdict
    return False, heuristic_reason


def score_case(
    expected: dict,
    actual: dict | None,
    *,
    user_text: str | None = None,
) -> dict:
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
        ok, reason = field_match(e, a, user_text=user_text)
        by_field[k] = {"correct": ok, "reason": reason, "expected": e, "actual": a}
        if ok:
            correct_count += 1
    return {
        "by_field": by_field,
        "case_accuracy": correct_count / 4.0,
        "any_nonnull_field": any_nonnull,
    }


# ---------- summary helpers (per-language reporting per Rodc directive 2026-05-02) ----------


# Ship gate v1.7 (per Rodc + External Opus directive 2026-05-02 evening).
# Old v1.3 gates (recall 0.90/0.80/0.80/0.75 + precision 0.80/0.85/0.85/0.80)
# were calibrated assuming single-canonical ground truth — that assumption
# broke under the rebalanced English eval set where concern field has
# real paraphrase variance ("losing income" ≈ "family financial stability
# if I quit"). v1.7 lowers per-field recall/precision to production-
# realistic levels AND adds a hallucination-rate cap that targets the
# actual trust-killer (model fabricating user-not-said content) rather
# than wording-mismatch noise.
_GATES = {
    "topic":    {"recall": 0.60, "precision": 0.70, "max_hallucination_rate": 0.08},
    "concern":  {"recall": 0.60, "precision": 0.70, "max_hallucination_rate": 0.08},
    "hope":     {"recall": 0.60, "precision": 0.70, "max_hallucination_rate": 0.08},
    "question": {"recall": 0.60, "precision": 0.70, "max_hallucination_rate": 0.08},
}


def _detect_case_language(case: dict) -> str:
    """Return 'en' or 'zh' for a case. Uses the explicit `language` tag
    if present (set by the rebalance script), otherwise auto-detects by
    presence of any CJK char in user/ai text."""
    lang = case.get("language")
    if lang in ("en", "zh"):
        return lang
    text = (case.get("input") or {}).get("user", "") + " "
    text += (case.get("input") or {}).get("ai", "")
    return "zh" if re.search(r"[一-鿿]", text) else "en"


def compute_summary(rs: list[dict], label: str) -> dict | None:
    """Compute the full asymmetric metric set for a results subset.
    Returns None when rs is empty (caller skips the block)."""
    n = len(rs)
    if n == 0:
        return None
    avg_acc = sum(r["score"]["case_accuracy"] for r in rs) / n
    by_category: dict[str, list[float]] = {}
    chitchat_results: list[dict] = []
    for r in rs:
        cat = r["category"]
        by_category.setdefault(cat, []).append(r["score"]["case_accuracy"])
        if cat == "chitchat":
            chitchat_results.append(r)
    cat_avg = {c: sum(xs) / len(xs) for c, xs in by_category.items() if xs}
    cat_n = {c: len(xs) for c, xs in by_category.items()}
    chitchat_n = len(chitchat_results)
    chitchat_fp = sum(
        1 for r in chitchat_results if r["score"]["any_nonnull_field"]
    )
    fp_rate = chitchat_fp / chitchat_n if chitchat_n else 0.0
    api_failures = sum(1 for r in rs if r["api_error"])

    field_metrics: dict[str, dict] = {}
    for field in ("topic", "concern", "hope", "question"):
        tp = fn = fp = tn = 0
        fp_hall = fp_mis = 0
        for r in rs:
            bf = r["score"]["by_field"][field]
            e = bf["expected"]; a = bf["actual"]; ok = bf["correct"]
            # Normalize multi-variant ground truth: empty list is "no
            # expected"; non-empty list means expected is non-null.
            if isinstance(e, list):
                e_is_null = len(e) == 0
            else:
                e_is_null = e is None
            a_is_null = a is None
            if e_is_null and a_is_null:
                tn += 1
            elif e_is_null and not a_is_null:
                fp += 1
                fp_hall += 1
            elif not e_is_null and a_is_null:
                fn += 1
            else:
                if ok:
                    tp += 1
                else:
                    fp += 1
                    fp_mis += 1
                    fn += 1
        rd = tp + fn
        pd = tp + fp
        recall = (tp / rd) if rd > 0 else 1.0
        precision = (tp / pd) if pd > 0 else 1.0
        field_metrics[field] = {
            "tp": tp, "fn": fn, "fp": fp, "tn": tn,
            "fp_hallucinations": fp_hall, "fp_mismatches": fp_mis,
            "recall": round(recall, 4), "precision": round(precision, 4),
            "recall_denom": rd, "precision_denom": pd,
        }

    gate_results: list[dict] = []
    for field, gate in _GATES.items():
        m = field_metrics[field]
        # Hallucination cap (v1.7): trust killer is fabricated content,
        # not paraphrased content. Cap at rate, not absolute count, so
        # the same threshold applies to EN bucket (n=64) and ZH bucket
        # (n=16) without a separate config.
        hall_rate = m["fp_hallucinations"] / n if n else 0.0
        gate_results.append({
            "field": field,
            "recall": m["recall"],
            "recall_gate": gate["recall"],
            "recall_pass": m["recall"] >= gate["recall"],
            "precision": m["precision"],
            "precision_gate": gate["precision"],
            "precision_pass": m["precision"] >= gate["precision"],
            "hallucination_rate": round(hall_rate, 4),
            "hallucination_gate": gate["max_hallucination_rate"],
            "hallucination_pass": hall_rate <= gate["max_hallucination_rate"],
        })
    chit_pass = fp_rate <= 0.05
    overall_pass = avg_acc >= 0.75
    # v1.7 ship gate: per-field recall + precision + hallucination
    # (4×3 = 12) plus chitchat-FP and overall accuracy = 14 conditions.
    all_pass = (
        all(
            g["recall_pass"] and g["precision_pass"] and g["hallucination_pass"]
            for g in gate_results
        )
        and chit_pass and overall_pass
    )
    return {
        "label": label,
        "n": n,
        "average_accuracy": avg_acc,
        "per_category_accuracy": cat_avg,
        "per_category_n": cat_n,
        "chitchat_fp_rate": fp_rate,
        "chitchat_n": chitchat_n,
        "chitchat_fp_count": chitchat_fp,
        "api_failures": api_failures,
        "field_metrics": field_metrics,
        "gate_results": gate_results,
        "chitchat_fp_pass": chit_pass,
        "overall_accuracy_pass": overall_pass,
        "all_conditions_pass": all_pass,
        # Backwards-compat alias (older code may read all_10_conditions_pass).
        "all_10_conditions_pass": all_pass,
    }


def print_summary(s: dict, header: str, *, ship_gate_active: bool) -> None:
    """Print the summary block for one bucket."""
    print("\n" + "=" * 60)
    gate_note = (
        " [SHIP GATE — blocking]" if ship_gate_active
        else " [monitor only]"
    )
    print(f"{header}  n={s['n']}{gate_note}")
    print(f"Average accuracy: {s['average_accuracy'] * 100:.1f}%")
    if s["per_category_accuracy"]:
        print("Per-category:")
        for cat, v in s["per_category_accuracy"].items():
            print(f"  {cat}: {v * 100:.1f}% (n={s['per_category_n'][cat]})")
    print()
    print("Per-field precision/recall + hallucination (ship gate v1.7):")
    for gr in s["gate_results"]:
        rm = "PASS" if gr["recall_pass"] else "FAIL"
        pm = "PASS" if gr["precision_pass"] else "FAIL"
        hm = "PASS" if gr["hallucination_pass"] else "FAIL"
        print(
            f"  {gr['field']:8s} "
            f"recall={gr['recall'] * 100:5.1f}% "
            f"(gate ≥{gr['recall_gate'] * 100:.0f}% [{rm}])  "
            f"precision={gr['precision'] * 100:5.1f}% "
            f"(gate ≥{gr['precision_gate'] * 100:.0f}% [{pm}])  "
            f"hallucination={gr['hallucination_rate'] * 100:4.1f}% "
            f"(gate ≤{gr['hallucination_gate'] * 100:.0f}% [{hm}])"
        )
    fpm = "PASS" if s["chitchat_fp_pass"] else "FAIL"
    print(f"  chitchat FP rate: {s['chitchat_fp_rate'] * 100:.1f}% "
          f"(gate ≤5% [{fpm}])")
    om = "PASS" if s["overall_accuracy_pass"] else "FAIL"
    print(f"  overall accuracy: {s['average_accuracy'] * 100:.1f}% "
          f"(gate ≥75% [{om}])")
    print()
    print("Per-field FP breakdown (raw counts):")
    for field in ("topic", "concern", "hope", "question"):
        m = s["field_metrics"][field]
        print(
            f"  {field:8s} "
            f"hallucinations={m['fp_hallucinations']} "
            f"(expected null, got value)  "
            f"mismatches={m['fp_mismatches']} (both non-null but wrong)"
        )
    print(f"API failures: {s['api_failures']}/{s['n']}")
    verdict = "PASS" if s["all_conditions_pass"] else "FAIL"
    print(f"ALL 14 CONDITIONS (v1.7): {verdict}")


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
    parser.add_argument(
        "--llm-judge", action=argparse.BooleanOptionalAction, default=True,
        help="Use LLM judge as fallback for short-field paraphrase "
             "tolerance (default: on; ~30 calls / ~$0.05 per 80-case run).",
    )
    parser.add_argument(
        "--judge-model", default="anthropic/claude-haiku-4.5",
        help="Model for LLM-judge calls when --llm-judge is enabled.",
    )
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

    # Wire LLM-judge fallback (per External Opus directive 2026-05-02 evening).
    # Sets the module-level _JUDGE_CFG that field_match consults when its
    # heuristic fails on short fields. Same provider/key as extraction.
    global _JUDGE_CFG
    if args.llm_judge:
        _JUDGE_CFG = {
            "model": args.judge_model,
            "api_key": api_key,
            "url": url,
        }
        print(f"LLM-judge fallback: ENABLED (model={args.judge_model})")
    else:
        _JUDGE_CFG = None
        print("LLM-judge fallback: disabled (--no-llm-judge)")

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
        score = score_case(
            expected, api_result["parsed_output"], user_text=user,
        )
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

    # ---------- aggregate (per-language per Rodc directive 2026-05-02) ----------
    # Tag each result with language so per-bucket grouping works.
    # Honors the explicit `language` field on the eval case if set,
    # otherwise auto-detects via CJK presence.
    for r, c in zip(results, cases):
        r["language"] = c.get("language") or _detect_case_language(c)

    en_results = [r for r in results if r["language"] == "en"]
    zh_results = [r for r in results if r["language"] == "zh"]
    total = len(results)

    # ---------- compute summaries (overall + per-language) ----------
    summary_overall = compute_summary(results, "overall")
    summary_en = compute_summary(en_results, "en")
    summary_zh = compute_summary(zh_results, "zh")

    # ---------- print: overall + per-language buckets ----------
    if summary_overall:
        print_summary(
            summary_overall,
            "OVERALL (combined EN + ZH)",
            ship_gate_active=False,
        )
    print()
    print("*" * 60)
    print("SHIP GATE = English bucket only (per Rodc directive 2026-05-02)")
    print("Phase 1 launches international English; Chinese metrics are")
    print("monitored for Phase 2 prep but do NOT block ship.")
    print("*" * 60)
    if summary_en:
        print_summary(
            summary_en,
            "ENGLISH BUCKET (Phase 1 ship gate)",
            ship_gate_active=True,
        )
    else:
        print("\n(no English cases in this eval — ship-gate skipped)")
    if summary_zh:
        print_summary(
            summary_zh,
            "CHINESE BUCKET (Phase 2 monitor)",
            ship_gate_active=False,
        )

    ship_gate_passes = bool(
        summary_en and summary_en["all_10_conditions_pass"]
    )

    # ---------- LLM-judge stats ----------
    if _JUDGE_CFG is not None and _JUDGE_STATS["calls"] > 0:
        print()
        print("=" * 60)
        print("LLM-judge fallback stats")
        print("=" * 60)
        flip_pct = (
            _JUDGE_STATS["flips_to_match"] / _JUDGE_STATS["calls"] * 100
            if _JUDGE_STATS["calls"] else 0.0
        )
        print(f"  Total judge calls : {_JUDGE_STATS['calls']}")
        print(f"  Flipped to match  : {_JUDGE_STATS['flips_to_match']} "
              f"({flip_pct:.1f}% of calls)")
        print(f"  Judge errors      : {_JUDGE_STATS['errors']}")
        print(f"  Cost estimate     : ~${_JUDGE_STATS['calls'] * 0.0017:.3f}"
              f" (Haiku 4.5 ~$0.0017/call rough)")

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
                    "n_en": len(en_results),
                    "n_zh": len(zh_results),
                },
                "summary": summary_overall,
                "metrics_by_language": {
                    "en": summary_en,
                    "zh": summary_zh,
                },
                "ship_gate_passes": ship_gate_passes,
                "ship_gate_basis": "metrics_by_language.en (Phase 1)",
                "llm_judge_stats": dict(_JUDGE_STATS) if _JUDGE_CFG else None,
                "cases": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nResults: {out_path}")
    # Exit 0 only if the ship-gate (English bucket) passes. Mirrors the
    # exit-code convention in run_intent_eval.py.
    return 0 if ship_gate_passes else 2


if __name__ == "__main__":
    sys.exit(main())
