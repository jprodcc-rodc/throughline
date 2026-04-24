# Testing

## Current test suite

The full regression suite lives under `fixtures/`:

```bash
pytest fixtures/ -q
```

As of v0.2.x tip: **700+ tests passing, 10 xfailed**, run time under
a minute. CI enforces pytest on Python 3.11 + 3.12 plus ruff lint
(F + E9) before any merge to `main` (see
[`.github/workflows/test.yml`](../.github/workflows/test.yml)).

CodeQL runs weekly on the `security-and-quality` suite
([`.github/workflows/codeql.yml`](../.github/workflows/codeql.yml)).
Dependabot opens PRs Mondays for major pip / github-actions bumps.

---

## Phase 6 regression (pre-v0.1.0, historical)

Before the project went public as v0.1.0 on 2026-04-23, the English
rewrite had never been A/B'd against the original private Chinese
build. Phase 6 was the regression pass that validated the rewrite
before tagging — five gates, ~$0.44 in real LLM spend.

Run the individual live-API gates with `python fixtures/phase6/run_h*.py`
(needs `OPENROUTER_API_KEY`); the offline assertions run as part of
the main `pytest fixtures/`.

| Gate | Scope | Status |
|---|---|---|
| **H1** RecallJudge classification drift | 48 EN turns × real Haiku 4.5 | **45/48 PASS (93.8%)** — 3 brainstorm-mode drift accepted as known EN-tone limitation |
| **H2** Cheap-gate short-turn routing | 20 EN turns offline | **10/20 MATCH + 10 documented gaps** — first-turn bare pronouns fall through to judge (accepted ~$0.003/turn cost) |
| **H3 code** Card injection wrapper + truncation | 9 offline assertions | **9/9 PASS** — card bodies always wrapped as DATA not INSTRUCTIONS |
| **H3 Haiku** Injection/PII/roleplay resistance | 31 EN turns × real Haiku 4.5 | **31/31 PASS (100%)** — zero compliance, zero leakage across 7 fingerprints |
| **H4** 4 refiner prompts (refine + route_domain) | 8 EN fixtures × real Sonnet 4.6 | **15/16 PASS (93.8%)** — 1 WARN on universal-vs-personal tension, zero structural failures |

Per-gate deep dives live in `fixtures/phase6/H*_ANALYSIS.md`. The
full run log is in
[`fixtures/phase6/SESSION_STATE.md`](../fixtures/phase6/SESSION_STATE.md)
— that file is also the live cross-session work tracker, kept up to
date after v0.1.0.

See [`docs/PHASE_6_CHECKLIST.md`](PHASE_6_CHECKLIST.md) for the
original pre-public-flip checklist template (useful for future
private → public repo transitions).

---

## Writing new tests

Tests go under `fixtures/v0_2_0/` (the current release line).
Phase-6-era tests under `fixtures/phase6/` are frozen audit
fixtures; don't extend them.

Conventions (see [`CONTRIBUTING.md`](../CONTRIBUTING.md) § House
style):

- Prefer mocking the HTTP boundary (`urllib.request.urlopen`) over
  mocking the provider SDK — keeps tests portable across the 16
  providers.
- `monkeypatch.setenv("THROUGHLINE_CONFIG_DIR", str(tmp_path))` is
  the canonical way to keep per-test config isolated from the
  developer's real `~/.throughline`.
- Use the bundled sample export (`samples/claude_sample.jsonl`) for
  integration tests that need multiple realistic conversations.
