# Tool-Triggering Eval Harness

Measures whether the host LLM (Claude Desktop / Code / Cursor) actually
fires the right MCP tool when given common conversational signals,
based ONLY on the tool's docstring.

The four differentiation tools are the eval target:

| Eval bucket    | MCP tool name             | What it does                                |
| -------------- | ------------------------- | ------------------------------------------- |
| `drift`        | `get_position_drift`      | Surface arc of stance evolution on a topic  |
| `consistency`  | `check_consistency`       | Confront a current claim with prior stances |
| `loose_ends`   | `find_loose_ends`         | Resume unfinished thinking                  |
| `recall`       | `recall_memory`           | Retrieve cards relevant to a query          |

These are throughline's moat. The other 3 tools (`save_refined_card`,
`list_topics`, `throughline_status`) are loaded as part of the surface
the model sees, so cross-tool false positives are visible in the report,
but they're not scored.

## Why this exists

MCP tool descriptions are the entire calling contract. A tool that
exists but never gets fired (because the description is unclear) is a
tool that effectively doesn't exist. This harness catches that.

Spec target per
[`private/SPEC_DEEP_OPTIMIZATION.md`](../../private/SPEC_DEEP_OPTIMIZATION.md)
P0-1:

- Per-tool **F1 ≥ 0.75**
- Per-tool **false-positive rate ≤ 0.15** (overtriggering annoys users)

## Layout

```
evals/tool-triggering/
  fixtures/
    drift-positive.jsonl       cases that SHOULD fire get_position_drift
    drift-negative.jsonl       cases that look like they might but should NOT
    consistency-positive.jsonl
    consistency-negative.jsonl
    loose_ends-positive.jsonl
    loose_ends-negative.jsonl
    recall-positive.jsonl
    recall-negative.jsonl
  run_eval.py                  the harness
  results/                     dated reports + raw runs land here
  README.md                    you're reading it
```

## Fixture format

One JSON object per line. `//` comments at line start are ignored.

```jsonc
{
  "context": "",                          // optional prior turns as a string
  "user_msg": "Where was I before lunch?",// the user's latest message
  "expected_tools": ["find_loose_ends"],  // tools that SHOULD fire (empty = none)
  "expected_params": {},                  // optional — informational, not asserted
  "rationale": "Session-start retrospective — textbook trigger."
}
```

`expected_tools` uses the **MCP tool name** (e.g. `find_loose_ends`),
not the bucket name (`loose_ends`).

For negative cases (`expected_tools: []`), the harness still scores
across all 4 differentiation tools — a fixture in `drift-negative.jsonl`
that accidentally fires `find_loose_ends` will count as an FP for
`find_loose_ends`. This catches the cross-tool overtriggering that
single-tool evals miss.

## Running

### Dry-run (no API calls)

```bash
python -m evals.tool-triggering.run_eval --no-llm
```

Validates fixture shape + tool-schema construction. CI-safe — no
ANTHROPIC_API_KEY needed. Exits 1 if any of the 4 buckets is missing
positive or negative coverage.

### Real run

```bash
ANTHROPIC_API_KEY=sk-ant-... python -m evals.tool-triggering.run_eval
```

Default model is `claude-opus-4-7`. Use `--model claude-sonnet-4-6` for
a cheaper baseline; `--model claude-haiku-4-5` to test what the cheapest
host would do.

Outputs land in `results/`:
- `<UTC-date>.md` — markdown report (per-tool F1 + per-case log)
- `<UTC-date>.jsonl` — raw per-case responses for re-analysis

### Faster iteration

```bash
python -m evals.tool-triggering.run_eval --max-cases 5
```

## Cost

Tool definitions + system prompt are cached via top-level
`cache_control: {type: "ephemeral"}` — the first case writes the cache
(~1.25× cost), every subsequent case reads (~0.1× cost). Estimated
full-run cost on `claude-opus-4-7` for 24 fixture cases:

- ~10K cached prefix tokens × first-case write + 23 × 0.1 × 10K
- + 24 × ~150 user input + 24 × ~200 output
- ≈ 35K input @ $5/M = $0.18 + 5K output @ $25/M = $0.13
- **≈ $0.30 per full run**

Cheaper on Sonnet 4.6 (~$0.10) or Haiku 4.5 (~$0.04).

## Growing the fixture set

Per spec Task 1.3, the target is **≥30 real cases** sourced from the
maintainer's own Claude conversation history. Don't LLM-generate new
fixtures — they overfit to the same docstring the eval is measuring.

When you add cases:

1. Pick a bucket × polarity file based on what the case tests.
2. Append a JSON line with `context` (if multi-turn), `user_msg`,
   `expected_tools`, and `rationale`.
3. Re-run `--no-llm` to verify the file still parses.
4. Re-run for real to see if the new case shifts F1 or FP rate.

If a case keeps failing across multiple runs and prompt revisions,
that's the eval doing its job: the docstring needs another pass, or
the case is genuinely ambiguous and should be split.

## Caveats

- **Single-turn proxy.** Real MCP usage is multi-turn, with the host
  LLM having seen many prior tool calls and results. The eval feeds
  one user message at a time. Multi-turn dynamics (priming effects,
  recent-tool bias) are not captured here.
- **No ground-truth params.** `expected_params` is informational —
  the harness doesn't assert exact param values, only which tools
  fired. Param-correctness is a separate eval.
- **Different model = different result.** Tool-selection behavior
  varies between Opus / Sonnet / Haiku and across model versions.
  Track which model the report is from.
