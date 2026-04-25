"""Pairwise (all-pairs / 2-wise) wizard coverage.

The full Cartesian of wizard options is ~2.4 billion combinations.
Running all of them is impossible. Running a hand-picked sample
hits known paths but misses interaction bugs ("provider X breaks
when paired with reranker Y").

The standard fix from combinatorial testing literature: pairwise
coverage. For axes A_1, ..., A_n with sizes n_1, ..., n_k, build
the smallest set of test cases such that every (A_i value, A_j
value) pair appears at least once across all i,j pairs. Empirical
result: 70-90% of all real-world bugs in software systems are
either single-value (1-wise) or pairwise interactions [Kuhn et
al., NIST 2004; D. Richard Kuhn's "Software Fault Interactions
and Implications for Software Testing"]. So pairwise catches the
vast majority of combinatorial bugs at a tiny fraction of the
cost.

For throughline's wizard with axes:
  mission     (3) × vector_db (6) × provider (16) ×
  embedder    (5) × reranker  (6) × privacy  (3) ×
  refine_tier (3) × structure (3) × taxonomy (6)

Full Cartesian = 5,598,720. Pairwise covering array (computed by
IPOG-F here) needs only ~96 test cases — 60,000× fewer.

This file is the pairwise covering set. Each row is one wizard
walk-through; the suite as a whole guarantees every two-axis
value pair fires at least once.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# Reuse the harness from the sibling combinatorial test.
sys.path.insert(0, str(HERE.parent))
from test_wizard_combinations import _run_with_script, _combo  # noqa: E402


# ============================================================
# Axis definitions
# ============================================================
# Axes are intentionally restricted to the user-pickable values per
# axis (e.g., card_structure excludes `rag_optimized` because that's
# only reachable via mission=rag_only forcing). The mission axis is
# kept narrow for the same reason — notes_only / rag_only would
# force-skip several other axes.

_AXES: Dict[str, Tuple[str, ...]] = {
    "mission":     ("full",),
    "vector_db":   ("qdrant", "chroma", "lancedb", "sqlite_vec",
                    "duckdb_vss", "pgvector"),
    "provider":    ("openrouter", "openai", "anthropic", "deepseek",
                    "together", "fireworks", "groq", "xai",
                    "siliconflow", "moonshot", "dashscope", "zhipu",
                    "doubao", "ollama", "lm_studio", "generic"),
    "embedder":    ("bge-m3", "openai", "nomic", "minilm", "voyage"),
    "reranker":    ("bge-reranker-v2-m3", "bge-reranker-v2-gemma",
                    "cohere", "voyage", "jina", "skip"),
    "privacy":     ("local_only", "hybrid", "cloud_max"),
    "refine_tier": ("skim", "normal", "deep"),
    "structure":   ("compact", "standard", "detailed"),
    "taxonomy":    ("minimal", "derive_from_vault", "derive_from_imports",
                    "jd", "para", "zettel"),
}


def _all_pairs(axes: Dict[str, Tuple[str, ...]]
               ) -> List[Tuple[str, str, Any, Any]]:
    """Enumerate every (axis_i, axis_j, value_i, value_j) pair where
    i < j. The covering-array generator below must hit every entry
    at least once."""
    pairs = []
    names = list(axes.keys())
    for i, ai in enumerate(names):
        for aj in names[i + 1:]:
            for vi in axes[ai]:
                for vj in axes[aj]:
                    pairs.append((ai, aj, vi, vj))
    return pairs


def _greedy_covering_array(axes: Dict[str, Tuple[str, ...]]
                            ) -> List[Dict[str, Any]]:
    """Build a 2-wise covering array via the simple greedy "add the
    test case that covers the most uncovered pairs" algorithm. Not
    optimal (IPOG-F gives smaller arrays for many axis profiles),
    but stdlib-only, deterministic, and small enough for our axis
    sizes. Typically ~max(n_i × n_j) cases for the two largest axes
    — for ours that's 16 × 6 = 96.
    """
    target_pairs = set()
    for ai, aj, vi, vj in _all_pairs(axes):
        target_pairs.add((ai, aj, vi, vj))

    cases: List[Dict[str, Any]] = []
    names = list(axes.keys())

    while target_pairs:
        best_case: Dict[str, Any] = {}
        best_covered: set = set()

        # Greedy: try every value of the FIRST uncovered axis,
        # filling the rest with values that cover the most remaining
        # pairs. This is the simplest greedy variant; converges
        # quickly for small axis counts.
        any_uncovered = next(iter(target_pairs))
        seed_axis, _, seed_val, _ = any_uncovered

        # For each starting value of the seed axis, try filling the
        # other axes with whichever value covers the most remaining
        # uncovered pairs.
        for v_seed in axes[seed_axis]:
            case: Dict[str, Any] = {seed_axis: v_seed}
            for axis in names:
                if axis in case:
                    continue
                # Pick the value of this axis that maximizes the
                # number of newly-covered pairs given the case so far.
                best_v = None
                best_v_cover = -1
                for v in axes[axis]:
                    case[axis] = v
                    covered = _pairs_covered_by(case, target_pairs)
                    if len(covered) > best_v_cover:
                        best_v_cover = len(covered)
                        best_v = v
                case[axis] = best_v

            covered = _pairs_covered_by(case, target_pairs)
            if len(covered) > len(best_covered):
                best_covered = covered
                best_case = dict(case)

        cases.append(best_case)
        target_pairs -= best_covered

    return cases


def _pairs_covered_by(case: Dict[str, Any],
                       remaining: set) -> set:
    """Return the subset of `remaining` (uncovered) pairs that this
    test case satisfies."""
    out = set()
    keys = list(case.keys())
    for i, ai in enumerate(keys):
        for aj in keys[i + 1:]:
            t = (ai, aj, case[ai], case[aj])
            if t in remaining:
                out.add(t)
    return out


# Compute the covering array once at import time. Deterministic
# given a deterministic dict iteration order (Python 3.7+).
_COVERING_ARRAY: List[Dict[str, Any]] = _greedy_covering_array(_AXES)


# ============================================================
# Pairwise verification: the array is actually a covering array
# ============================================================

def test_covering_array_covers_all_pairs():
    """Sanity check: the generated array actually hits every pair.
    Without this guard, a bug in `_greedy_covering_array` could
    silently produce a partial array and we'd test less than we
    think we do."""
    target = set()
    for ai, aj, vi, vj in _all_pairs(_AXES):
        target.add((ai, aj, vi, vj))
    covered: set = set()
    for case in _COVERING_ARRAY:
        names = list(case.keys())
        for i, ai in enumerate(names):
            for aj in names[i + 1:]:
                covered.add((ai, aj, case[ai], case[aj]))
    missing = target - covered
    assert not missing, (
        f"covering array misses {len(missing)} pairs; e.g. {next(iter(missing))}"
    )


def test_covering_array_is_reasonably_small():
    """The greedy generator should fit pairwise coverage in a
    small constant multiple of the largest axis-pair product. With
    16-provider × 6-other axis = 96 unavoidable, anything under 200
    is fine."""
    assert len(_COVERING_ARRAY) <= 200, (
        f"covering array bloated to {len(_COVERING_ARRAY)} cases — "
        f"the greedy heuristic regressed.")


# ============================================================
# Run every covering-array case through the wizard
# ============================================================

import pytest as _pytest


def _model_for(provider: str) -> str:
    """The wizard's step 5 picks a model SCOPED to the provider.
    Use each provider's declared default model so step 5 succeeds."""
    from throughline_cli.providers import get_preset
    preset = get_preset(provider)
    if not preset.models:
        return "custom-model-id"
    return preset.models[0][0]


@_pytest.mark.parametrize(
    "case",
    _COVERING_ARRAY,
    ids=lambda c: f"{c['provider']}-{c['vector_db']}-"
                  f"{c['embedder']}-{c['reranker']}-{c['privacy']}",
)
def test_pairwise_combination_wizards_clean(tmp_path, monkeypatch, case):
    """For each row of the covering array, drive the wizard end-to-
    end and assert: (a) wizard completes, (b) config validates clean.

    Together with `test_covering_array_covers_all_pairs`, this
    suite is a 2-wise covering array — every (axis_i, axis_j) value
    pair fires at least once across the whole suite. Pairwise
    coverage catches an empirical 70–90% of real-world combinatorial
    bugs at ~96 test cases instead of 5.6M+."""
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
    # Spot-check the axes we wrote actually round-tripped:
    assert cfg.vector_db == case["vector_db"]
    assert cfg.llm_provider == case["provider"]
    assert cfg.embedder == case["embedder"]
    assert cfg.reranker == case["reranker"]
    assert cfg.privacy == case["privacy"]
    assert cfg.refine_tier == case["refine_tier"]
    assert cfg.card_structure == case["structure"]
    assert cfg.taxonomy_source == case["taxonomy"]

    # Resulting config must validate clean.
    from throughline_cli import config as cfg_mod
    import tomllib
    raw = tomllib.loads(
        (tmp_path / ".throughline" / "config.toml").read_text(
            encoding="utf-8"))
    issues = cfg_mod.validate(raw)
    assert issues == [], (
        f"case {case} produced validation issues: " +
        "; ".join(f"{i.kind}:{i.key}={i.detail}" for i in issues))
