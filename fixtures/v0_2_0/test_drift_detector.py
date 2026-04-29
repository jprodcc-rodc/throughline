"""P0-2 Task 2.3: pin detect_drift() behavior with fully-mocked LLM
judge + Vault. No real LLM calls; this exercises the algorithm
gates only. The LLM-judge integration with a real Haiku-tier model
is a separate concern (Task 2.3 implementation step), unblocked by
this contract.
"""
from __future__ import annotations

from typing import Optional

import pytest

from mcp_server.claim_schema import Claim
from mcp_server.drift_detector import (
    DEFAULT_JUDGE_CONFIDENCE_THRESHOLD,
    SIGNIFICANT_DELTA,
    DriftReport,
    JudgeVerdict,
    Vault,
    _parse_iso8601,
    _severity,
    _time_gap_days,
    detect_drift,
)


# ── builders -------------------------------------------------------------


def _claim(
    *,
    subject_canonical: str = "postgres",
    predicate: str = "suitable_for",
    stance: float = 0.5,
    hedging: float = 0.1,
    kind: str = "stance",
    timestamp: Optional[str] = "2026-04-29T10:00:00Z",
    raw: str = "raw",
) -> Claim:
    return Claim(
        subject="Postgres",
        subject_canonical=subject_canonical,
        predicate=predicate,
        stance=stance,
        hedging=hedging,
        kind=kind,
        raw_text=raw,
        timestamp=timestamp,
    )


class _FakeVault:
    """Minimal in-memory Vault implementation for mock tests."""

    def __init__(self, claims: list[Claim], context: Optional[str] = None):
        self._claims = list(claims)
        self._context = context
        self.find_claims_calls: list[dict] = []  # for assertion in tests

    def find_claims(
        self,
        *,
        subject_canonical: str,
        predicate_similar_to: str,
        before: Optional[str],
    ) -> list[Claim]:
        self.find_claims_calls.append({
            "subject_canonical": subject_canonical,
            "predicate_similar_to": predicate_similar_to,
            "before": before,
        })
        return [
            c for c in self._claims
            if c.subject_canonical == subject_canonical
        ]

    def context_between(
        self,
        prior: Claim,
        current: Claim,
    ) -> Optional[str]:
        return self._context


def _judge_drift(
    *,
    is_drift: bool = True,
    confidence: float = 0.9,
    explanation: str = "stance reversed",
):
    """Returns a callable matching the LLMJudge protocol that
    returns a fixed JudgeVerdict regardless of input."""
    def _judge(*, prior, current, intervening_context):
        return JudgeVerdict(
            is_genuine_drift=is_drift,
            explanation=explanation,
            confidence=confidence,
        )
    return _judge


# ── algorithm gates -------------------------------------------------------


def test_returns_none_when_kind_is_fact():
    """Facts are not drift-trackable -- they get UPDATED, not drifted."""
    current = _claim(kind="fact", stance=1.0)
    prior = _claim(kind="stance", stance=-1.0,
                   timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])
    assert detect_drift(current, vault, _judge_drift()) is None


def test_returns_none_when_kind_is_preference():
    current = _claim(kind="preference", stance=1.0)
    prior = _claim(kind="stance", stance=-1.0,
                   timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])
    assert detect_drift(current, vault, _judge_drift()) is None


def test_stance_kind_is_drift_trackable():
    current = _claim(kind="stance", stance=1.0)
    prior = _claim(kind="stance", stance=-1.0,
                   timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])
    result = detect_drift(current, vault, _judge_drift())
    assert result is not None


def test_commitment_kind_is_drift_trackable():
    current = _claim(kind="commitment", stance=1.0)
    prior = _claim(kind="stance", stance=-1.0,
                   timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])
    result = detect_drift(current, vault, _judge_drift())
    assert result is not None


def test_returns_none_when_no_history():
    current = _claim(stance=1.0)
    vault = _FakeVault([])  # empty
    assert detect_drift(current, vault, _judge_drift()) is None


def test_returns_none_when_delta_below_threshold():
    """|stance_delta| < SIGNIFICANT_DELTA (0.6) is too small to surface."""
    current = _claim(stance=0.4)
    prior = _claim(stance=0.0, timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])
    # delta=0.4, below 0.6 threshold -- judge should never even be called
    judge = _judge_drift()
    assert detect_drift(current, vault, judge) is None


def test_judge_not_called_when_delta_below_threshold():
    """Cost optimization: the judge is the expensive part. Don't fire
    it for small deltas."""
    current = _claim(stance=0.4)
    prior = _claim(stance=0.0, timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])

    judge_calls = []

    def tracking_judge(*, prior, current, intervening_context):
        judge_calls.append(1)
        return JudgeVerdict(is_genuine_drift=True, explanation="x")

    detect_drift(current, vault, tracking_judge)
    assert judge_calls == []  # never invoked


def test_returns_none_when_judge_says_no():
    """LLM judge has the last word. Even with big delta, judge can veto."""
    current = _claim(stance=1.0)
    prior = _claim(stance=-1.0, timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])
    assert detect_drift(current, vault, _judge_drift(is_drift=False)) is None


def test_returns_none_when_judge_confidence_below_threshold():
    """Low-confidence judge calls are suppressed to avoid noise."""
    current = _claim(stance=1.0)
    prior = _claim(stance=-1.0, timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])
    # default threshold is 0.5; pass 0.3
    assert detect_drift(
        current, vault, _judge_drift(confidence=0.3)
    ) is None


def test_returns_drift_when_all_gates_pass():
    current = _claim(stance=1.0, hedging=0.0)
    prior = _claim(stance=-1.0, hedging=0.0,
                   timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])
    report = detect_drift(current, vault, _judge_drift())
    assert isinstance(report, DriftReport)
    assert report.prior is prior
    assert report.current is current
    assert report.severity == pytest.approx(2.0)  # |1.0 - (-1.0)| * (1-0) = 2.0
    assert report.judge_confidence == 0.9
    assert report.llm_explanation == "stance reversed"


# ── most-recent selection ------------------------------------------------


def test_most_recent_prior_is_picked():
    """When history has multiple Claims, the most-recent (by
    timestamp) is used for the delta."""
    current = _claim(stance=1.0)
    very_old = _claim(stance=-1.0, timestamp="2024-01-01T00:00:00Z",
                      raw="old")
    recent = _claim(stance=0.5, timestamp="2026-04-01T00:00:00Z",
                    raw="recent")  # delta only 0.5 -> below threshold
    vault = _FakeVault([very_old, recent])
    # Algorithm picks recent (delta=0.5), which is below threshold
    # -> returns None even though very_old has a big delta.
    assert detect_drift(current, vault, _judge_drift()) is None


def test_history_order_independent():
    """Same data in different list order should produce the same result."""
    current = _claim(stance=1.0)
    a = _claim(stance=-1.0, timestamp="2024-01-01T00:00:00Z", raw="a")
    b = _claim(stance=-0.9, timestamp="2025-06-01T00:00:00Z", raw="b")
    c = _claim(stance=-0.8, timestamp="2026-01-01T00:00:00Z", raw="c")

    vault1 = _FakeVault([a, b, c])
    vault2 = _FakeVault([c, a, b])
    vault3 = _FakeVault([b, c, a])

    j = _judge_drift()
    r1 = detect_drift(current, vault1, j)
    r2 = detect_drift(current, vault2, j)
    r3 = detect_drift(current, vault3, j)
    assert r1 is not None and r2 is not None and r3 is not None
    # same prior selected in all three (the most-recent timestamp)
    assert r1.prior.raw_text == "c"
    assert r2.prior.raw_text == "c"
    assert r3.prior.raw_text == "c"


# ── severity calculation -------------------------------------------------


def test_severity_max_when_no_hedging():
    current = _claim(stance=1.0, hedging=0.0)
    prior = _claim(stance=-1.0, hedging=0.0,
                   timestamp="2026-01-01T00:00:00Z")
    assert _severity(2.0, prior, current) == pytest.approx(2.0)


def test_severity_damped_by_current_hedging():
    current = _claim(stance=1.0, hedging=0.5)
    prior = _claim(stance=-1.0, hedging=0.0,
                   timestamp="2026-01-01T00:00:00Z")
    # |2.0| * (1 - max(0.5, 0.0)) = 2.0 * 0.5 = 1.0
    assert _severity(2.0, prior, current) == pytest.approx(1.0)


def test_severity_damped_by_prior_hedging():
    current = _claim(stance=1.0, hedging=0.0)
    prior = _claim(stance=-1.0, hedging=0.7,
                   timestamp="2026-01-01T00:00:00Z")
    # |2.0| * (1 - max(0.0, 0.7)) = 2.0 * 0.3 = 0.6
    assert _severity(2.0, prior, current) == pytest.approx(0.6)


def test_severity_zero_when_one_side_fully_hedged():
    current = _claim(stance=1.0, hedging=1.0)
    prior = _claim(stance=-1.0, hedging=0.0,
                   timestamp="2026-01-01T00:00:00Z")
    # full uncertainty on one side -> no real "drift" to surface
    assert _severity(2.0, prior, current) == pytest.approx(0.0)


# ── timestamp parsing ---------------------------------------------------


@pytest.mark.parametrize("ts, expected_year", [
    ("2026-04-29T10:00:00Z", 2026),
    ("2026-04-29T10:00:00", 2026),
    ("2026-04-29T10:00:00+00:00", 2026),
])
def test_parse_iso8601_handles_common_forms(ts, expected_year):
    dt = _parse_iso8601(ts)
    assert dt is not None
    assert dt.year == expected_year


@pytest.mark.parametrize("bad", [None, "", "not a date", "2026-13-01"])
def test_parse_iso8601_returns_none_on_garbage(bad):
    assert _parse_iso8601(bad) is None


def test_time_gap_days_basic():
    a = _claim(timestamp="2026-04-29T00:00:00Z")
    b = _claim(timestamp="2026-04-30T00:00:00Z")
    assert _time_gap_days(a, b) == pytest.approx(1.0)


def test_time_gap_days_returns_none_on_missing_timestamp():
    a = _claim(timestamp=None)
    b = _claim(timestamp="2026-04-30T00:00:00Z")
    assert _time_gap_days(a, b) is None


def test_drift_report_carries_time_gap():
    current = _claim(stance=1.0,
                     timestamp="2026-04-29T00:00:00Z")
    prior = _claim(stance=-1.0,
                   timestamp="2026-01-29T00:00:00Z")
    vault = _FakeVault([prior])
    report = detect_drift(current, vault, _judge_drift())
    assert report is not None
    assert report.time_gap_days is not None
    # 90 days approx
    assert 89 < report.time_gap_days < 91


# ── vault interaction (find_claims call shape) --------------------------


def test_find_claims_called_with_correct_args():
    current = _claim(
        subject_canonical="usage_based_pricing",
        predicate="suitable_for",
        stance=1.0,
        timestamp="2026-04-29T10:00:00Z",
    )
    vault = _FakeVault([])
    detect_drift(current, vault, _judge_drift())
    assert vault.find_claims_calls == [{
        "subject_canonical": "usage_based_pricing",
        "predicate_similar_to": "suitable_for",
        "before": "2026-04-29T10:00:00Z",
    }]


def test_judge_receives_intervening_context():
    """The judge gets context_between() result so it can rule on
    whether intervening conversation justifies the stance flip."""
    current = _claim(stance=1.0)
    prior = _claim(stance=-1.0, timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior], context="user said 'requirements changed'")

    captured: dict = {}

    def capturing_judge(*, prior, current, intervening_context):
        captured["intervening_context"] = intervening_context
        return JudgeVerdict(is_genuine_drift=True, explanation="x")

    detect_drift(current, vault, capturing_judge)
    assert captured["intervening_context"] == "user said 'requirements changed'"


# ── threshold tuning ----------------------------------------------------


def test_custom_significant_delta_threshold():
    """Caller can raise the threshold (less sensitive) or lower it
    (more sensitive)."""
    current = _claim(stance=0.4)
    prior = _claim(stance=0.0, timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])
    # Default 0.6: returns None (delta=0.4)
    assert detect_drift(current, vault, _judge_drift()) is None
    # Lowered to 0.3: now fires
    result = detect_drift(
        current, vault, _judge_drift(),
        significant_delta=0.3,
    )
    assert result is not None


def test_custom_judge_confidence_threshold():
    current = _claim(stance=1.0)
    prior = _claim(stance=-1.0, timestamp="2026-01-01T00:00:00Z")
    vault = _FakeVault([prior])
    # Default 0.5: confidence 0.6 fires
    assert detect_drift(
        current, vault, _judge_drift(confidence=0.6),
    ) is not None
    # Raised to 0.8: same confidence 0.6 suppressed
    assert detect_drift(
        current, vault, _judge_drift(confidence=0.6),
        judge_confidence_threshold=0.8,
    ) is None


# ── module-level constants are sane ------------------------------------


def test_module_constants_sane():
    assert 0.0 < SIGNIFICANT_DELTA < 2.0  # in valid stance-delta range
    assert 0.0 <= DEFAULT_JUDGE_CONFIDENCE_THRESHOLD <= 1.0


# ── Vault protocol shape ------------------------------------------------


def test_fake_vault_satisfies_protocol():
    """structural subtyping: _FakeVault is a Vault by virtue of
    having matching method signatures."""
    v: Vault = _FakeVault([])
    # Just verifying assignment doesn't fail under typing
    assert v is not None
