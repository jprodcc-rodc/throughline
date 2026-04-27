"""LLM-backed drift segmenter for Reflection Pass stage 7.

Given a chronological list of back-filled cards on one topic,
returns a phase segmentation: each phase represents a coherent
stance period; phase boundaries align with reasoning shifts.

Same architectural pattern as ``llm_namer`` / ``llm_extractor`` /
``llm_judge``: stdlib urllib, OPENROUTER_API_KEY → OPENAI_API_KEY
fallback, explicit error structs.

V1 of ``get_position_drift`` returns per-card trajectory entries
because stage 7 isn't implemented. Stage 7 enriches that into
per-phase trajectory: groups consecutive cards with similar
stance into a single phase entry, with phase_name + transition
labels. Tool surface stays the same shape; the host LLM presents
the trajectory more legibly.

Per the design doc § "Drift Detection", four kinds of drift:

- ``healthy_evolution``: new info → reasoning updated
- ``drift_without_reasoning``: stance moved but reasoning didn't
- ``following_trends``: industry zeitgeist pulled the user
- ``mood_swings``: different views in different states

This segmenter labels the topic-level drift_kind plus per-phase
boundaries. The drift_kind classification is a judgment call;
the prompt instructs the LLM to default to ``healthy_evolution``
when uncertain (most thinking IS healthy evolution; the other
three are the diagnostic-interesting cases).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional


# ---------- exceptions ----------

class LLMSegmenterError(Exception):
    """LLM endpoint returned an error or malformed segmentation."""


class LLMSegmenterUnavailable(LLMSegmenterError):
    """No API key or endpoint unreachable."""


# ---------- defaults ----------

DEFAULT_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.5-flash"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_TOKENS = 1500  # phase output is heavier than other LLM uses


_VALID_DRIFT_KINDS = {
    "healthy_evolution",
    "drift_without_reasoning",
    "following_trends",
    "mood_swings",
    "unsegmented",  # fallback when LLM unsure
}


_SYSTEM_PROMPT = """You segment a chronological sequence of cards on \
one topic into stance phases.

Each PHASE is a contiguous run of cards sharing similar stance + \
reasoning. Phase boundaries align with reasoning shifts (new info, \
new constraints, condition changes, position reversals).

Return JSON ONLY in this shape:

{
  "drift_kind": "healthy_evolution" | "drift_without_reasoning" | \
"following_trends" | "mood_swings" | "unsegmented",
  "phases": [
    {
      "phase_name": "ONE-LINE label of this phase's stance",
      "stance": "ONE-SENTENCE summary of the stance held during this phase",
      "started_card_index": 0,
      "ended_card_index": 2,
      "transition_reason": "ONE-SENTENCE explanation of why the next phase emerged (empty for last phase)"
    },
    ...
  ]
}

Indices reference the input cards array (0-based, inclusive on \
both ends). Phases must cover all input cards without gaps.

Definitions of drift_kind:

- healthy_evolution: each phase transition has reasoning behind \
it; new information / new constraints justify the shift. \
Default when uncertain — most thinking IS healthy evolution.
- drift_without_reasoning: stance moved but reasoning didn't \
update; user may not have noticed the shift.
- following_trends: industry zeitgeist or external pressure \
pulled the user's stance, not their own reasoning.
- mood_swings: stance differs across phases without consistent \
context — different views likely from different emotional \
states.
- unsegmented: cards are too few / too uniform / too disjoint \
to segment meaningfully.

Be conservative. False-positive ``drift_without_reasoning`` or \
``mood_swings`` labels demoralize the user. When uncertain, \
return ``healthy_evolution``.
"""


# ---------- env-var resolution ----------

def resolve_endpoint_and_key() -> tuple[Optional[str], Optional[str]]:
    api_key = (
        os.environ.get("OPENROUTER_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
        or None
    )
    explicit_url = os.environ.get("OPENROUTER_URL", "").strip()
    if explicit_url:
        url = explicit_url
    else:
        base = os.environ.get("OPENAI_BASE_URL", "").strip()
        if base:
            base = base.rstrip("/")
            url = (
                base if base.endswith("/chat/completions")
                else base + "/chat/completions"
            )
        else:
            url = DEFAULT_URL
    return url, api_key


def resolve_model() -> str:
    return (
        os.environ.get("THROUGHLINE_SEGMENTER_MODEL", "").strip()
        or os.environ.get("THROUGHLINE_NAMER_MODEL", "").strip()
        or DEFAULT_MODEL
    )


# ---------- response parser ----------

def _parse_segmentation(content: str, n_cards: int) -> dict:
    """Validate LLM response shape + index bounds."""
    s = content.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1:]
        if s.endswith("```"):
            s = s[: -3]
        s = s.strip()
    if not s.startswith("{"):
        first = s.find("{")
        if first != -1:
            s = s[first:]
    if not s.endswith("}"):
        last = s.rfind("}")
        if last != -1:
            s = s[: last + 1]

    try:
        parsed = json.loads(s)
    except (ValueError, TypeError) as exc:
        raise LLMSegmenterError(f"Not JSON: {exc}: {content!r}") from exc

    if not isinstance(parsed, dict):
        raise LLMSegmenterError(f"Response is not an object: {parsed!r}")

    drift_kind = parsed.get("drift_kind")
    if drift_kind not in _VALID_DRIFT_KINDS:
        raise LLMSegmenterError(f"drift_kind invalid: {parsed!r}")

    phases_raw = parsed.get("phases")
    if not isinstance(phases_raw, list):
        raise LLMSegmenterError(f"phases not a list: {parsed!r}")

    cleaned_phases = []
    for p in phases_raw:
        if not isinstance(p, dict):
            continue
        try:
            start = int(p.get("started_card_index", -1))
            end = int(p.get("ended_card_index", -1))
        except (ValueError, TypeError):
            continue
        if start < 0 or end < 0 or start >= n_cards or end >= n_cards:
            # Out of bounds — skip this phase rather than corrupt
            continue
        if start > end:
            continue
        cleaned_phases.append({
            "phase_name": str(p.get("phase_name", ""))[:200],
            "stance": str(p.get("stance", ""))[:300],
            "started_card_index": start,
            "ended_card_index": end,
            "transition_reason": str(p.get("transition_reason", ""))[:300],
        })

    if not cleaned_phases:
        raise LLMSegmenterError(
            f"No valid phases survived index validation: {parsed!r}"
        )

    return {
        "drift_kind": drift_kind,
        "phases": cleaned_phases,
    }


# ---------- main entry ----------

def segment_cluster(
    cards: list[dict],
    *,
    topic: str = "",
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT,
    extra_headers: Optional[dict[str, str]] = None,
) -> dict:
    """Segment a chronological list of back-filled cards into
    stance phases.

    Args:
        cards: list of dicts, each with at minimum ``title`` (str),
            ``stance`` (str), ``reasoning`` (list[str]), ``date``
            (str). Cards must be chronologically sorted (caller's
            responsibility).
        topic: optional cluster name for context.

    Returns:
        ``{drift_kind: str, phases: [{phase_name, stance, started_card_index,
        ended_card_index, transition_reason}, ...]}``.

    Raises:
        LLMSegmenterUnavailable: missing key / unreachable.
        LLMSegmenterError: malformed response or no valid phases.
    """
    if not cards:
        raise LLMSegmenterError("segment_cluster: cards list is empty")
    if len(cards) < 2:
        # Single-card "cluster" can't have phases — return trivial
        # one-phase segmentation without firing LLM.
        return {
            "drift_kind": "unsegmented",
            "phases": [{
                "phase_name": str(cards[0].get("title", ""))[:200],
                "stance": str(cards[0].get("stance", ""))[:300],
                "started_card_index": 0,
                "ended_card_index": 0,
                "transition_reason": "",
            }],
        }

    resolved_url, resolved_key = resolve_endpoint_and_key()
    final_url = url or resolved_url
    final_key = api_key or resolved_key
    final_model = model or resolve_model()

    if not final_key:
        raise LLMSegmenterUnavailable(
            "No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY."
        )

    # Build user prompt with cards listed by index
    lines = [f"Topic: {topic or '(unspecified)'}\n"]
    lines.append(f"Cards ({len(cards)}, chronological):\n")
    for i, c in enumerate(cards):
        date = str(c.get("date", "?"))
        title = str(c.get("title", ""))[:100]
        stance = str(c.get("stance", ""))[:200]
        reasoning_bullets = "; ".join(
            (c.get("reasoning") or [])[:3]
        )[:300]
        lines.append(
            f"[{i}] {date} — {title}\n"
            f"    stance: {stance}\n"
            f"    reasoning: {reasoning_bullets}\n"
        )
    user_prompt = "\n".join(lines) + "\nSegment into phases."

    payload = {
        "model": final_model,
        "temperature": 0.1,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {final_key}",
        "Content-Type": "application/json",
        "X-Title": "throughline-drift-segmenter",
    }
    if extra_headers:
        for k, v in extra_headers.items():
            if k.lower() != "x-title":
                headers.setdefault(k, v)

    body_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        final_url, data=body_bytes, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.URLError as exc:
        raise LLMSegmenterUnavailable(f"LLM endpoint unreachable: {exc}") from exc
    except (TimeoutError, OSError) as exc:
        raise LLMSegmenterUnavailable(f"LLM call timeout/socket: {exc}") from exc

    try:
        envelope = json.loads(data.decode("utf-8", errors="replace"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise LLMSegmenterError(f"Response not JSON: {exc}") from exc

    try:
        content = envelope["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMSegmenterError(
            f"Response missing choices[0].message.content: {envelope!r}"
        ) from exc

    return _parse_segmentation(content, n_cards=len(cards))
