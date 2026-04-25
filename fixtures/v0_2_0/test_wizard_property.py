"""Property-based / randomized wizard testing.

Pairwise covering arrays catch interaction bugs but operate on a
fixed sample. Property-based tests pick *random* valid configs
across many CI runs — over time, every long-tail combination has
been touched at least once.

Without a `hypothesis` dep we use stdlib `random` with a fixed
seed per session. The test runs N iterations; each iteration:
  1. Picks a random value for every wizard axis.
  2. Drives the wizard end-to-end.
  3. Asserts the resulting config validates clean.

A failing case prints both the seed and the picked combination so
a contributor can reproduce locally.

This complements the pairwise suite — pairwise gives a *proof* of
coverage on the 2-wise level; randomized gives *probability* of
catching higher-order bugs.
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path
from typing import Any, Dict


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))

sys.path.insert(0, str(HERE.parent))
from test_wizard_combinations import _run_with_script, _combo  # noqa: E402
from test_wizard_pairwise import _AXES, _model_for  # noqa: E402


# Default iterations per CI run. Override with PROPERTY_TEST_ITERATIONS=
# in env to run more locally (e.g. for a long-form fuzz session).
N_ITERS = int(os.environ.get("PROPERTY_TEST_ITERATIONS", "30"))


def _random_case(rng: random.Random) -> Dict[str, Any]:
    return {axis: rng.choice(values) for axis, values in _AXES.items()}


def _run_one_random_case(tmp_path, monkeypatch, case: Dict[str, Any]) -> None:
    answers = _combo(**{
        "vector DB":         case["vector_db"],
        "LLM provider":      case["provider"],
        "Pick a model":      _model_for(case["provider"]),
        "Model ID":          _model_for(case["provider"]),
        "Embedder":          case["embedder"],
        "Reranker":          case["reranker"],
        "pipeline may hit":  case["privacy"],
        "How deep":          case["refine_tier"],
        "card shape":        case["structure"],
        "card folders":      case["taxonomy"],
        "mission":           case["mission"],
    })
    cfg, _ = _run_with_script(tmp_path, monkeypatch, answers)

    from throughline_cli import config as cfg_mod
    import tomllib
    raw = tomllib.loads(
        (tmp_path / ".throughline" / "config.toml").read_text(
            encoding="utf-8"))
    issues = cfg_mod.validate(raw)
    assert issues == [], (
        f"random case {case} produced validation issues: " +
        "; ".join(f"{i.kind}:{i.key}={i.detail}" for i in issues))


def test_wizard_random_cases(tmp_path_factory, monkeypatch):
    """N random configs through the wizard. Fixed seed per session
    so a failing CI is reproducible from the printed seed."""
    seed = int(os.environ.get("PROPERTY_TEST_SEED", "20260425"))
    rng = random.Random(seed)
    print(f"\n[wizard property test] seed={seed} iters={N_ITERS}")

    failures = []
    for i in range(N_ITERS):
        case = _random_case(rng)
        case_dir = tmp_path_factory.mktemp(f"prop-{i}")
        # Each iteration needs a fresh monkeypatch context so module
        # reloads + env-var overrides from previous iters don't leak.
        with monkeypatch.context() as mp:
            try:
                _run_one_random_case(case_dir, mp, case)
            except AssertionError as e:
                failures.append((i, case, str(e)))
            except Exception as e:
                failures.append((i, case, f"{type(e).__name__}: {e}"))

    if failures:
        msg_lines = [f"{len(failures)}/{N_ITERS} random cases failed."
                      f" To reproduce: PROPERTY_TEST_SEED={seed}"]
        for i, case, err in failures[:5]:
            msg_lines.append(f"  iter {i}: {case}")
            msg_lines.append(f"    {err}")
        if len(failures) > 5:
            msg_lines.append(f"  ... +{len(failures) - 5} more")
        raise AssertionError("\n".join(msg_lines))
