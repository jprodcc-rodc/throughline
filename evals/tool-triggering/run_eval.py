#!/usr/bin/env python
"""Tool-triggering eval harness for throughline MCP tools.

Per private/SPEC_DEEP_OPTIMIZATION.md P0-1 Task 1.2.

Goal: measure whether the host LLM (Claude Desktop / Code / Cursor) actually
fires the right MCP tool in response to common conversational signals,
based ONLY on the tool's docstring. The four differentiation tools
(get_position_drift / check_consistency / find_loose_ends / recall_memory)
are the eval target — these are throughline's moat, and passive-only triggering
makes them effectively non-existent.

Usage:
    # Dry-run — validates fixture shape + tool schema construction without
    # touching the Anthropic API. Run this in CI / locally to catch fixture
    # regressions.
    python -m evals.tool-triggering.run_eval --no-llm

    # Real run (default model: claude-opus-4-7).
    ANTHROPIC_API_KEY=sk-ant-... python -m evals.tool-triggering.run_eval

    # Smaller model / cheaper baseline.
    python -m evals.tool-triggering.run_eval --model claude-sonnet-4-6

    # Subset for fast iteration.
    python -m evals.tool-triggering.run_eval --max-cases 5

Outputs:
    evals/tool-triggering/results/<UTC-date>.md   — markdown summary report
    evals/tool-triggering/results/<UTC-date>.jsonl — per-case raw runs
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union, get_type_hints


HERE = Path(__file__).resolve().parent
DEFAULT_FIXTURES_DIR = HERE / "fixtures"
DEFAULT_OUTPUT_DIR = HERE / "results"

# Allow direct script invocation (`python evals/tool-triggering/run_eval.py`)
# in addition to `python -m`. Without this, mcp_server.tools.* imports fail
# because the project root isn't on sys.path.
_PROJECT_ROOT = HERE.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# All 7 host-callable MCP tools; the model sees the full surface so cross-tool
# false positives are visible in the report.
ALL_TOOLS = [
    "save_refined_card",
    "recall_memory",
    "list_topics",
    "find_loose_ends",
    "check_consistency",
    "get_position_drift",
    "throughline_status",
]

# The 4 differentiation tools we score. Buckets in fixture filenames
# (drift / consistency / loose_ends / recall) map 1:1 to these.
BUCKET_TO_TOOL = {
    "drift": "get_position_drift",
    "consistency": "check_consistency",
    "loose_ends": "find_loose_ends",
    "recall": "recall_memory",
}
EVAL_TOOLS = list(BUCKET_TO_TOOL.values())

SYSTEM_PROMPT = """You are connected to the user's local "throughline" knowledge base via 7 MCP tools.

Your job in this evaluation: for the user's latest message, decide which tool(s) (if any) to call based ONLY on:
1. The conversation context (if provided)
2. The user's latest message
3. Each tool's description (CALL THIS PROACTIVELY WHEN / DO NOT CALL WHEN / EXAMPLE TRIGGERS / EXAMPLE NON-TRIGGERS)

Rules:
- If no tool fits, respond with text only — do not call a tool.
- If multiple tools fit, call all of them.
- Do not call a tool just because a keyword appears; follow the docstring's decision guide.
- Do not ask the user a clarifying question — pick the best decision from the information given.
"""


# ---------- type-annotation → JSON schema ---------------------------------


def _annotation_to_schema(ann: Any) -> dict:
    """Best-effort Python annotation → JSON schema. Handles the patterns
    used by the 7 throughline tools: str/int/bool/float/list[X]/Optional[X]
    /X | None. Anything unrecognized falls back to {"type": "string"}."""
    import types

    origin = getattr(ann, "__origin__", None)
    args = getattr(ann, "__args__", ())

    # Optional[X] / X | None — strip the None branch and recurse on X.
    if origin in (Union,) or (
        hasattr(types, "UnionType") and origin is types.UnionType
    ):
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _annotation_to_schema(non_none[0])
        # Union of multiple non-None — fall through to generic.

    # list[X]
    if origin is list:
        if args:
            return {"type": "array", "items": _annotation_to_schema(args[0])}
        return {"type": "array"}

    if ann is str:
        return {"type": "string"}
    if ann is int:
        return {"type": "integer"}
    if ann is bool:
        return {"type": "boolean"}
    if ann is float:
        return {"type": "number"}
    if ann is dict:
        return {"type": "object"}

    return {"type": "string"}


def build_tool_definitions(tool_names: list[str] = ALL_TOOLS) -> list[dict]:
    """Introspect mcp_server.tools.* into Anthropic Messages API tool defs.
    Description is the full docstring (Decision Guide format). Schema is
    derived from the function signature."""
    defs = []
    for name in tool_names:
        mod = importlib.import_module(f"mcp_server.tools.{name}")
        fn = getattr(mod, name)

        try:
            hints = get_type_hints(fn)
        except Exception:
            hints = {}

        sig = inspect.signature(fn)
        properties: dict = {}
        required: list[str] = []
        for param_name, param in sig.parameters.items():
            ann = hints.get(param_name, param.annotation)
            properties[param_name] = _annotation_to_schema(ann)
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        defs.append({
            "name": name,
            "description": (fn.__doc__ or "").strip(),
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        })
    return defs


# ---------- fixture loading -----------------------------------------------


@dataclass
class EvalCase:
    bucket: str
    polarity: str  # "positive" or "negative"
    context: str
    user_msg: str
    expected_tools: list[str]
    expected_params: dict
    rationale: str
    source_file: str

    def case_id(self) -> str:
        return f"{self.bucket}-{self.polarity}"


def load_fixtures(fixtures_dir: Path) -> list[EvalCase]:
    """Walk fixtures/<bucket>-<polarity>.jsonl files and parse cases.
    Lines starting with `//` are treated as comments and skipped. JSON
    parse errors are reported to stderr but don't abort the run."""
    cases: list[EvalCase] = []
    for path in sorted(fixtures_dir.glob("*.jsonl")):
        stem = path.stem
        if "-" not in stem:
            continue
        bucket, polarity = stem.rsplit("-", 1)
        if polarity not in ("positive", "negative"):
            continue
        with path.open(encoding="utf-8") as f:
            for line_num, raw_line in enumerate(f, 1):
                line = raw_line.strip()
                if not line or line.startswith("//"):
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    print(
                        f"[warn] {path.name}:{line_num} JSON parse error: {e}",
                        file=sys.stderr,
                    )
                    continue
                if "user_msg" not in obj:
                    print(
                        f"[warn] {path.name}:{line_num} missing user_msg",
                        file=sys.stderr,
                    )
                    continue
                cases.append(EvalCase(
                    bucket=bucket,
                    polarity=polarity,
                    context=obj.get("context", "") or "",
                    user_msg=obj["user_msg"],
                    expected_tools=obj.get("expected_tools", []) or [],
                    expected_params=obj.get("expected_params", {}) or {},
                    rationale=obj.get("rationale", "") or "",
                    source_file=path.name,
                ))
    return cases


# ---------- scoring -------------------------------------------------------


@dataclass
class ToolStats:
    tp: int = 0  # tool was expected and was selected
    fp: int = 0  # tool was selected but not expected (overtriggering)
    fn: int = 0  # tool was expected but not selected (missed)
    tn: int = 0  # tool was not expected and not selected

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def fp_rate(self) -> float:
        denom = self.fp + self.tn
        return self.fp / denom if denom > 0 else 0.0


def score_case(
    selected: set[str], expected: list[str], stats: dict[str, ToolStats]
) -> None:
    """Update per-tool TP/FP/FN/TN tallies based on a single case."""
    expected_set = set(expected)
    for tool in EVAL_TOOLS:
        was_expected = tool in expected_set
        was_selected = tool in selected
        if was_expected and was_selected:
            stats[tool].tp += 1
        elif was_expected and not was_selected:
            stats[tool].fn += 1
        elif not was_expected and was_selected:
            stats[tool].fp += 1
        else:
            stats[tool].tn += 1


# ---------- API runner ----------------------------------------------------


def run_one_case(
    client,
    tool_defs: list[dict],
    system_prompt: str,
    model: str,
    case: EvalCase,
) -> tuple[set[str], dict]:
    """Send one case to the Messages API. Returns (selected_tool_names,
    summary_dict). cache_control on the system block caches tools +
    system together — first call writes (~1.25x), subsequent calls
    read (~0.1x)."""
    if case.context:
        user_content = (
            "[Conversation so far]\n"
            f"{case.context}\n\n"
            "[User's latest message]\n"
            f"{case.user_msg}"
        )
    else:
        user_content = case.user_msg

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }],
        tools=tool_defs,
        tool_choice={"type": "auto"},
        messages=[{"role": "user", "content": user_content}],
    )

    selected: set[str] = {
        b.name for b in response.content if b.type == "tool_use"
    }
    summary = {
        "stop_reason": response.stop_reason,
        "selected_tools": sorted(selected),
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_read_input_tokens": getattr(
            response.usage, "cache_read_input_tokens", 0
        ),
        "cache_creation_input_tokens": getattr(
            response.usage, "cache_creation_input_tokens", 0
        ),
    }
    return selected, summary


# ---------- report rendering ----------------------------------------------


def render_report(
    *,
    model: str,
    cases_run: int,
    cases_failed: int,
    stats: dict[str, ToolStats],
    raw_runs: list[dict],
    started_at: datetime,
) -> str:
    """Render a markdown report. Top section is the one-glance summary
    (per-tool F1 + pass/fail vs the spec's 0.75 threshold). Bottom section
    is the case-by-case log so failures are clickable."""
    lines: list[str] = []
    lines.append(f"# Tool-triggering eval — {started_at.strftime('%Y-%m-%d %H:%M UTC')}\n")
    lines.append(f"- Model: `{model}`")
    lines.append(f"- Cases run: {cases_run}")
    if cases_failed:
        lines.append(f"- Cases failed (API error): {cases_failed}")
    lines.append("")
    lines.append("## Per-tool scores\n")
    lines.append("Spec threshold: F1 ≥ 0.75 per tool, FP rate ≤ 0.15.\n")
    lines.append(
        "| Tool | TP | FP | FN | TN | Precision | Recall | F1 | FP rate | Verdict |"
    )
    lines.append(
        "|------|----|----|----|----|-----------|--------|----|---------|---------|"
    )
    for tool in EVAL_TOOLS:
        s = stats[tool]
        f1_pass = s.f1 >= 0.75
        fp_pass = s.fp_rate <= 0.15
        verdict = "PASS" if (f1_pass and fp_pass) else "FAIL"
        lines.append(
            f"| `{tool}` | {s.tp} | {s.fp} | {s.fn} | {s.tn} | "
            f"{s.precision:.2f} | {s.recall:.2f} | {s.f1:.2f} | "
            f"{s.fp_rate:.2f} | {verdict} |"
        )
    lines.append("")

    # Per-case details: every case, sorted by bucket then case index.
    lines.append("## Per-case results\n")
    lines.append("Cases marked `MISMATCH` are where the model's decision diverged from the fixture's expected tools.\n")
    for run in raw_runs:
        case = run["case"]
        expected = sorted(case["expected_tools"])
        selected = run["summary"]["selected_tools"]
        match = "OK" if expected == selected else "MISMATCH"
        case_id = f"{case['bucket']}-{case['polarity']}"
        lines.append(
            f"- **[{match}]** `{case_id}` — expected `{expected}` / "
            f"selected `{selected}`"
        )
        rationale = case.get("rationale", "")
        if rationale:
            lines.append(f"  - rationale: {rationale}")
        lines.append(f"  - user_msg: {case['user_msg'][:140]}")
    lines.append("")

    return "\n".join(lines)


# ---------- main ----------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--fixtures-dir", type=Path, default=DEFAULT_FIXTURES_DIR,
        help="Directory of <bucket>-<polarity>.jsonl files",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help="Where to write report.md + raw.jsonl",
    )
    parser.add_argument(
        "--model", default="claude-opus-4-7",
        help="Anthropic model ID (default: claude-opus-4-7)",
    )
    parser.add_argument(
        "--max-cases", type=int, default=None,
        help="Stop after N cases (smoke-test mode)",
    )
    parser.add_argument(
        "--no-llm", action="store_true",
        help="Validate fixtures + tool schemas; skip API calls. Use in CI.",
    )
    args = parser.parse_args(argv)

    started_at = datetime.now(timezone.utc)

    # Load fixtures + tools — both used in dry-run and real-run paths.
    cases = load_fixtures(args.fixtures_dir)
    if args.max_cases is not None:
        cases = cases[: args.max_cases]
    tool_defs = build_tool_definitions()

    print(f"Loaded {len(cases)} cases from {args.fixtures_dir}")
    print(f"Built {len(tool_defs)} tool definitions: "
          f"{[t['name'] for t in tool_defs]}")

    if args.no_llm:
        # Sanity-print: how many cases per bucket × polarity.
        breakdown: dict[str, int] = {}
        for c in cases:
            key = c.case_id()
            breakdown[key] = breakdown.get(key, 0) + 1
        print("\nCases per bucket-polarity:")
        for k in sorted(breakdown):
            print(f"  {k}: {breakdown[k]}")
        # Verify the 4 P0 buckets each have at least 1 positive + 1 negative.
        missing: list[str] = []
        for bucket in BUCKET_TO_TOOL:
            for pol in ("positive", "negative"):
                if breakdown.get(f"{bucket}-{pol}", 0) == 0:
                    missing.append(f"{bucket}-{pol}")
        if missing:
            print(f"\n[warn] Missing fixtures: {missing}", file=sys.stderr)
            return 1
        # Verify each tool def has parameters resolved.
        for d in tool_defs:
            if not isinstance(d["input_schema"]["properties"], dict):
                print(f"[error] {d['name']} schema malformed",
                      file=sys.stderr)
                return 1
        print("\n[dry-run] OK -- fixtures + tool schemas validate.")
        return 0

    try:
        import anthropic
    except ImportError:
        print(
            "[error] pip install anthropic — required for non-dry-run.",
            file=sys.stderr,
        )
        return 1

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "[error] ANTHROPIC_API_KEY not set.", file=sys.stderr,
        )
        return 1

    client = anthropic.Anthropic()

    stats = {tool: ToolStats() for tool in EVAL_TOOLS}
    raw_runs: list[dict] = []
    cases_failed = 0

    print(f"\nRunning {len(cases)} cases against {args.model}...\n")
    for i, case in enumerate(cases):
        try:
            selected, summary = run_one_case(
                client, tool_defs, SYSTEM_PROMPT, args.model, case,
            )
        except Exception as e:
            cases_failed += 1
            print(
                f"  [{i+1}/{len(cases)}] {case.case_id()} "
                f"ERROR: {type(e).__name__}: {e}",
                file=sys.stderr,
            )
            continue
        score_case(selected, case.expected_tools, stats)
        raw_runs.append({
            "case": {
                "bucket": case.bucket,
                "polarity": case.polarity,
                "context": case.context,
                "user_msg": case.user_msg,
                "expected_tools": case.expected_tools,
                "expected_params": case.expected_params,
                "rationale": case.rationale,
                "source_file": case.source_file,
            },
            "summary": summary,
        })
        match = "OK" if sorted(selected) == sorted(case.expected_tools) else "DIFF"
        print(
            f"  [{i+1}/{len(cases)}] {case.case_id():>22}  "
            f"[{match}]  expected={sorted(case.expected_tools)} "
            f"selected={sorted(selected)}"
        )

    # Write outputs.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    today = started_at.strftime("%Y-%m-%d")
    raw_path = args.output_dir / f"{today}.jsonl"
    report_path = args.output_dir / f"{today}.md"

    with raw_path.open("w", encoding="utf-8") as f:
        for r in raw_runs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    report = render_report(
        model=args.model,
        cases_run=len(raw_runs),
        cases_failed=cases_failed,
        stats=stats,
        raw_runs=raw_runs,
        started_at=started_at,
    )
    report_path.write_text(report, encoding="utf-8")

    print(f"\nReport: {report_path}")
    print(f"Raw runs: {raw_path}")

    # Print summary table to stdout for visibility.
    print("\nPer-tool F1:")
    for tool in EVAL_TOOLS:
        s = stats[tool]
        verdict = "PASS" if (s.f1 >= 0.75 and s.fp_rate <= 0.15) else "FAIL"
        print(
            f"  {tool:>22}  P={s.precision:.2f} R={s.recall:.2f} "
            f"F1={s.f1:.2f}  FPR={s.fp_rate:.2f}  [{verdict}]"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
