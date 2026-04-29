"""P0-2 Task 2.3 + 2.4 -- claim-level drift and consistency analysis.

Per private/SPEC_DEEP_OPTIMIZATION.md § P0-2 and the design doc
at docs/CLAIM_STANCE_SCORING.md.

Two pure functions, side-effect-free, fully mock-testable:
- `detect_drift(current, vault, judge)` -> DriftReport | None
  Compares current claim to its MOST RECENT prior on the same
  subject_canonical. Surfaces a single DriftReport when the
  stance shifted dramatically AND the LLM judge confirms.
- `detect_consistency_issues(current, vault, judge)` ->
    list[ConsistencyReport]
  Compares current claim to ALL relevant priors. Surfaces every
  prior the LLM judge rules as a genuine contradiction (not
  context-justified). Mirror of drift but multi-prior.

Architecture:
- `Vault` is a Protocol so callers can plug in different storage
  backends (vault filesystem walker, sqlite cache, etc.) without
  the detector caring.
- `LLMJudge` is also a Protocol so the cheap-judge model
  (Haiku per spec § Out of Scope rule 4) can be swapped, and
  tests can pass mock judges without LLM calls.

Invariants both functions preserve:
1. Embedding is for retrieval (find candidate priors), NEVER for
   judgment. Drift / contradiction verdict comes from LLM judge.
2. LLM judge is the LAST word. Algorithmic threshold is a pre-
   filter; if threshold passes but judge says no, no report.
3. Hedging modulates severity but not threshold. A high-hedging
   reversal is still a candidate; the severity score just gets
   damped to reflect that the user wasn't fully committed.
4. The functions do not mutate inputs. Vault and Claim instances
   are read-only here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Protocol

from mcp_server.claim_schema import Claim


# ── thresholds (tunable; document with reasoning) ──────────────────────

# Minimum |stance delta| to even consider a candidate. Below this,
# the stance shift is small enough that it's likely just rephrasing
# or context-shift, not an actual drift. Spec section P0-2 Task 2.3
# uses 0.6 ("at least cross the neutral line"); we expose it as a
# named constant so future tuning has a single point to change.
SIGNIFICANT_DELTA = 0.6

# Default judge confidence threshold below which we suppress the
# DriftReport (avoid noise from low-confidence judge calls). 0.5
# is a conservative pre-filter; spec doesn't pin a value, so we
# default to "barely-better-than-coinflip" and let callers raise.
DEFAULT_JUDGE_CONFIDENCE_THRESHOLD = 0.5


# ── output shape ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class JudgeVerdict:
    """LLM judge's structured output. The judge is the last word on
    whether two stance-shifted Claims represent a genuine drift vs
    a context-justified rephrasing."""

    is_genuine_drift: bool
    explanation: str
    confidence: float = 1.0  # 0.0 (uncertain) .. 1.0 (certain)


@dataclass(frozen=True)
class DriftReport:
    """Returned when a genuine drift is detected. Carries enough
    context for the host LLM to surface the drift gently to the
    user (per the existing soft-mode framing in check_consistency)."""

    severity: float                # 0..1, hedging-damped magnitude
    prior: Claim
    current: Claim
    time_gap_days: Optional[float]  # None if either timestamp missing
    llm_explanation: str
    judge_confidence: float


@dataclass(frozen=True)
class ConsistencyReport:
    """Returned for each prior the LLM judge ruled as a genuine
    contradiction with the current claim. detect_consistency_issues
    returns a LIST of these (vs detect_drift's single DriftReport),
    because consistency surfaces every relevant historical conflict
    so the host LLM can present them all to the user. Soft-mode
    framing handled at the MCP-tool layer, not here."""

    severity: float                # 0..1, hedging-damped magnitude
    prior: Claim
    current: Claim
    time_gap_days: Optional[float]  # None if either timestamp missing
    llm_explanation: str
    judge_confidence: float


# ── Vault + LLMJudge protocols ─────────────────────────────────────────


class Vault(Protocol):
    """Anything that can return prior Claims for the same subject is
    a Vault. The drift detector doesn't care about underlying storage."""

    def find_claims(
        self,
        *,
        subject_canonical: str,
        predicate_similar_to: str,
        before: Optional[str],
    ) -> list[Claim]:
        """Return Claims with matching subject_canonical and
        similar predicate, dated strictly before the cutoff. Empty
        list if none. The 'similar predicate' match is the Vault's
        concern (exact, embedding similarity, etc.); the detector
        consumes whatever it returns."""
        ...

    def context_between(
        self,
        prior: Claim,
        current: Claim,
    ) -> Optional[str]:
        """Return any intervening conversation / card content the
        judge should consider when ruling on whether the apparent
        drift is context-justified. None if not available -- the
        judge will rule with priors-only."""
        ...


class LLMJudge(Protocol):
    """Callable that takes two Claims and returns a JudgeVerdict.

    Implementations:
    - Production: a wrapper around Haiku-tier LLM (see spec rule 4)
    - Tests: a lambda or mock returning a hand-crafted JudgeVerdict
    """

    def __call__(
        self,
        *,
        prior: Claim,
        current: Claim,
        intervening_context: Optional[str],
    ) -> JudgeVerdict:
        ...


# ── helpers ─────────────────────────────────────────────────────────────


def _parse_iso8601(ts: Optional[str]) -> Optional[datetime]:
    """Best-effort parse of an ISO 8601 timestamp string. Returns
    None if the input is None or unparseable -- drift detection
    proceeds without the time-gap field rather than failing."""
    if not ts:
        return None
    s = ts.rstrip("Z")
    s = s.replace("+00:00", "")
    try:
        # Python's fromisoformat handles "YYYY-MM-DDTHH:MM:SS" and
        # variants. If the string had a Z suffix we stripped, treat
        # it as UTC.
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _time_gap_days(prior: Claim, current: Claim) -> Optional[float]:
    p = _parse_iso8601(prior.timestamp)
    c = _parse_iso8601(current.timestamp)
    if p is None or c is None:
        return None
    return (c - p).total_seconds() / 86400.0


def _severity(stance_delta: float, prior: Claim, current: Claim) -> float:
    """severity = |delta| * (1 - max(hedgings)).

    Justification: a |delta|=2.0 reversal between two flat
    assertions (hedging=0) is severity 2.0 -- maximum. A |delta|=2.0
    reversal where the current claim was hedged (hedging=0.5) drops
    to severity 1.0 because the user is signaling uncertainty
    themselves. Symmetric on the prior side: if the prior was
    already a tentative position, less of a "real" drift to surface."""
    hedge = max(prior.hedging, current.hedging)
    return abs(stance_delta) * (1.0 - hedge)


# ── algorithm ───────────────────────────────────────────────────────────


def detect_drift(
    current_claim: Claim,
    vault: Vault,
    llm_judge: LLMJudge,
    *,
    significant_delta: float = SIGNIFICANT_DELTA,
    judge_confidence_threshold: float = DEFAULT_JUDGE_CONFIDENCE_THRESHOLD,
) -> Optional[DriftReport]:
    """Decide whether `current_claim` represents a genuine drift
    relative to historical claims on the same subject_canonical.

    Returns None when:
    - Current claim isn't drift-trackable (kind != stance | commitment)
    - No history found for this subject_canonical + predicate
    - Stance delta below `significant_delta`
    - LLM judge rules `is_genuine_drift=False`
    - LLM judge confidence below `judge_confidence_threshold`

    Returns a DriftReport when all gates pass.

    All inputs are read-only; the function is side-effect-free.
    """
    # Gate 1: only stance / commitment Claims are drift-trackable.
    # Facts get *updated* (a new fact replaces an old one without
    # being "drift"); preferences are too granular and noisy.
    if current_claim.kind not in ("stance", "commitment"):
        return None

    # Gate 2: retrieve candidate priors. Vault decides what
    # "predicate_similar_to" means.
    history = vault.find_claims(
        subject_canonical=current_claim.subject_canonical,
        predicate_similar_to=current_claim.predicate,
        before=current_claim.timestamp,
    )
    if not history:
        return None

    # Pick the most-recent prior for the delta. If the history
    # has timestamps, sort by them; otherwise rely on caller
    # ordering. Ascending sort + take last == most-recent.
    sorted_history = sorted(
        history,
        key=lambda c: _parse_iso8601(c.timestamp) or datetime.min.replace(tzinfo=timezone.utc),
    )
    most_recent = sorted_history[-1]

    # Gate 3: algorithmic threshold check.
    stance_delta = current_claim.stance - most_recent.stance
    if abs(stance_delta) < significant_delta:
        return None

    # Gate 4: LLM judge has the last word.
    intervening = vault.context_between(most_recent, current_claim)
    verdict = llm_judge(
        prior=most_recent,
        current=current_claim,
        intervening_context=intervening,
    )
    if not verdict.is_genuine_drift:
        return None
    if verdict.confidence < judge_confidence_threshold:
        return None

    severity = _severity(stance_delta, most_recent, current_claim)

    return DriftReport(
        severity=severity,
        prior=most_recent,
        current=current_claim,
        time_gap_days=_time_gap_days(most_recent, current_claim),
        llm_explanation=verdict.explanation,
        judge_confidence=verdict.confidence,
    )


def detect_consistency_issues(
    current_claim: Claim,
    vault: Vault,
    llm_judge: LLMJudge,
    *,
    significant_delta: float = SIGNIFICANT_DELTA,
    judge_confidence_threshold: float = DEFAULT_JUDGE_CONFIDENCE_THRESHOLD,
) -> list[ConsistencyReport]:
    """Find ALL prior claims the LLM judge rules as genuine
    contradictions with `current_claim`.

    Mirror of `detect_drift` but multi-prior: drift returns the
    most-recent prior as a single DriftReport (focus: time
    evolution); consistency returns every conflicting prior as a
    list of ConsistencyReports (focus: point-comparison).

    Returns an empty list when:
    - Current claim isn't drift-trackable (kind != stance | commitment)
    - No history found for this subject_canonical + predicate
    - Every prior fails the algorithmic delta threshold OR the LLM
      judge ruled them context-justified

    Returns a populated list when one or more priors passed all
    gates. Each entry is sorted by judge confidence (descending) so
    the most-confident contradictions surface first to the host LLM.

    All inputs are read-only; the function is side-effect-free.
    """
    # Gate 1: only stance / commitment Claims are drift-trackable.
    if current_claim.kind not in ("stance", "commitment"):
        return []

    # Gate 2: retrieve all candidate priors. Vault decides what
    # "predicate_similar_to" means.
    history = vault.find_claims(
        subject_canonical=current_claim.subject_canonical,
        predicate_similar_to=current_claim.predicate,
        before=current_claim.timestamp,
    )
    if not history:
        return []

    # Pre-compute intervening_context once per prior the judge sees.
    # Caller's Vault may use this hook for per-pair context fetches;
    # we don't cache across pairs.
    reports: list[ConsistencyReport] = []
    for prior in history:
        # Gate 3: algorithmic threshold per pair.
        stance_delta = current_claim.stance - prior.stance
        if abs(stance_delta) < significant_delta:
            continue

        # Gate 4: LLM judge ruling per pair.
        intervening = vault.context_between(prior, current_claim)
        verdict = llm_judge(
            prior=prior,
            current=current_claim,
            intervening_context=intervening,
        )
        if not verdict.is_genuine_drift:
            continue
        if verdict.confidence < judge_confidence_threshold:
            continue

        severity = _severity(stance_delta, prior, current_claim)
        reports.append(ConsistencyReport(
            severity=severity,
            prior=prior,
            current=current_claim,
            time_gap_days=_time_gap_days(prior, current_claim),
            llm_explanation=verdict.explanation,
            judge_confidence=verdict.confidence,
        ))

    # Sort by judge confidence descending so most-certain
    # contradictions surface first.
    reports.sort(key=lambda r: r.judge_confidence, reverse=True)
    return reports
