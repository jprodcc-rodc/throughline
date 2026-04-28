"""LLM-backed contradiction judge for Reflection Pass stage 6.

Given a pair of stances (with reasoning + dates) on the same
topic, returns a structured judgment: are they actually
contradicting, OR is the later stance an evolution / refinement /
narrower-scoping of the earlier one?

Same architectural pattern as ``llm_namer`` and ``llm_extractor``:
stdlib urllib, OPENROUTER_API_KEY → OPENAI_API_KEY env-var
fallback, explicit error structs.

Why a dedicated judge step matters: V1 of ``check_consistency``
returns ALL historical positions in a cluster and lets the host
LLM judge contradiction in conversation. That's correct but
chatty — for clusters with 5+ cards, the host wades through
several non-contradicting positions before finding the real
conflict (or there is none and the user gets surfaced 5
historical-but-irrelevant positions).

Stage 6 enrichment narrows the list at daemon time. The
``check_consistency`` tool can then return only pairs where this
LLM has tagged ``is_contradiction: true``, falling back to the
full list when stage 6 hasn't run.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Optional


# ---------- exceptions ----------

class LLMJudgeError(Exception):
    """LLM endpoint returned an error or malformed judgment."""


class LLMJudgeUnavailable(LLMJudgeError):
    """No API key or endpoint unreachable."""


# ---------- defaults (mirror llm_namer / llm_extractor) ----------

DEFAULT_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.5-flash"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_TOKENS = 600  # 200 truncated 1/237 verbose evolution responses
                          # observed during 2026-04-28 real-vault E2E
DEFAULT_RETRIES = 2  # extra attempts on transient network errors;
                     # WinError 10060 hit 4/237 pairs in same E2E run
_RETRY_BACKOFF_SECONDS = 0.5  # first sleep; doubled per attempt


_SYSTEM_PROMPT = """You judge whether two stances on the same topic are \
actually contradicting each other, or whether the later stance is an \
evolution / refinement / narrower-scoping of the earlier one.

Return JSON ONLY in this shape:

{
  "is_contradiction": true | false,
  "kind": "direct_reversal" | "scope_narrowing" | "evolution" | \
"orthogonal" | "agreement",
  "reasoning_diff": "ONE sentence explaining the difference."
}

Definitions:

- direct_reversal: later stance asserts the opposite of earlier with no \
new conditions or context. THIS is a contradiction.
- scope_narrowing: later stance still holds the earlier reasoning but \
adds a precondition (e.g. "X is true, but only under condition Y"). \
NOT a contradiction.
- evolution: earlier stance's reasoning is updated by new info or \
later experience. Later stance is consistent IF the earlier reasoning \
is read in the original context. NOT a contradiction.
- orthogonal: stances are about different facets of the topic and don't \
actually contradict each other. NOT a contradiction.
- agreement: stances align. NOT a contradiction.

Be conservative: when in doubt, return is_contradiction=false. \
False-positive contradictions destroy user trust on first occurrence; \
false-negatives are recoverable next pass.
"""


# ---------- env-var resolution (DRY copy of namer's logic) ----------

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
    """``THROUGHLINE_JUDGE_MODEL`` first, then namer model fallback,
    then default."""
    return (
        os.environ.get("THROUGHLINE_JUDGE_MODEL", "").strip()
        or os.environ.get("THROUGHLINE_NAMER_MODEL", "").strip()
        or DEFAULT_MODEL
    )


# ---------- response parser ----------

_VALID_KINDS = {
    "direct_reversal", "scope_narrowing", "evolution",
    "orthogonal", "agreement",
}


def _parse_judgment(content: str) -> dict:
    """Parse LLM text into the documented schema. Tolerates fence
    wrapping + leading/trailing prose. Validates fields."""
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
        raise LLMJudgeError(f"Not JSON: {exc}: {content!r}") from exc

    if not isinstance(parsed, dict):
        raise LLMJudgeError(f"Response is not an object: {parsed!r}")

    is_contra = parsed.get("is_contradiction")
    if not isinstance(is_contra, bool):
        raise LLMJudgeError(f"is_contradiction missing or non-bool: {parsed!r}")

    kind = parsed.get("kind")
    if not isinstance(kind, str) or kind not in _VALID_KINDS:
        raise LLMJudgeError(f"kind missing or invalid: {parsed!r}")

    diff = parsed.get("reasoning_diff", "")
    if not isinstance(diff, str):
        diff = ""

    return {
        "is_contradiction": is_contra,
        "kind": kind,
        "reasoning_diff": diff.strip(),
    }


# ---------- transport ----------

def _urlopen_with_retry(req, *, timeout: float, retries: int) -> bytes:
    """POST with bounded retry on transient network errors.

    HTTP 4xx is treated as permanent (auth/contract) — no retry.
    HTTP 5xx, generic URLError, TimeoutError, and OSError get
    ``retries`` extra attempts with exponential backoff.

    Raises ``LLMJudgeUnavailable`` after the final attempt fails.
    """
    last_exc: Optional[BaseException] = None
    attempts = retries + 1
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if 400 <= exc.code < 500:
                raise LLMJudgeUnavailable(
                    f"LLM endpoint unreachable: {exc}"
                ) from exc
            last_exc = exc
        except urllib.error.URLError as exc:
            last_exc = exc
        except (TimeoutError, OSError) as exc:
            last_exc = exc
        if attempt < attempts - 1:
            time.sleep(_RETRY_BACKOFF_SECONDS * (2 ** attempt))
    raise LLMJudgeUnavailable(
        f"LLM endpoint unreachable after {attempts} attempts: {last_exc}"
    ) from last_exc


# ---------- main entry ----------

def judge_pair(
    earlier: dict,
    later: dict,
    *,
    topic: str = "",
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    extra_headers: Optional[dict[str, str]] = None,
) -> dict:
    """Judge whether ``later`` contradicts ``earlier`` on ``topic``.

    Args:
        earlier: dict with at minimum ``stance`` (str), ``reasoning``
            (list[str]), ``date`` (str). Caller provides whatever's
            on the position payload.
        later: same shape.
        topic: optional cluster name for context (helps LLM
            disambiguate when stances are short).
        url, api_key, model, timeout, extra_headers: same as
            ``llm_namer.name_cluster`` / ``llm_extractor.extract_card_essence``.

    Returns:
        ``{is_contradiction: bool, kind: str, reasoning_diff: str}``.

    Raises:
        LLMJudgeUnavailable: missing key / unreachable endpoint.
        LLMJudgeError: malformed response.
    """
    early_stance = (earlier.get("stance") or "").strip()
    late_stance = (later.get("stance") or "").strip()
    if not early_stance or not late_stance:
        raise LLMJudgeError("judge_pair: at least one stance is empty")

    resolved_url, resolved_key = resolve_endpoint_and_key()
    final_url = url or resolved_url
    final_key = api_key or resolved_key
    final_model = model or resolve_model()

    if not final_key:
        raise LLMJudgeUnavailable(
            "No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY, "
            "or pass api_key= explicitly."
        )

    early_reason = "\n".join(
        f"  - {r}" for r in (earlier.get("reasoning") or [])[:5]
    )
    late_reason = "\n".join(
        f"  - {r}" for r in (later.get("reasoning") or [])[:5]
    )
    user_prompt = (
        f"Topic: {topic or '(unspecified)'}\n\n"
        f"EARLIER stance ({earlier.get('date', '?')}):\n"
        f"  {early_stance}\n"
        f"  reasoning:\n{early_reason}\n\n"
        f"LATER stance ({later.get('date', '?')}):\n"
        f"  {late_stance}\n"
        f"  reasoning:\n{late_reason}\n\n"
        "Judge whether these contradict."
    )

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
        "X-Title": "throughline-contradiction-judge",
    }
    if extra_headers:
        for k, v in extra_headers.items():
            if k.lower() != "x-title":
                headers.setdefault(k, v)

    body_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        final_url, data=body_bytes, headers=headers, method="POST"
    )

    data = _urlopen_with_retry(req, timeout=timeout, retries=retries)

    try:
        envelope = json.loads(data.decode("utf-8", errors="replace"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise LLMJudgeError(f"Response not JSON: {exc}") from exc

    try:
        content = envelope["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMJudgeError(
            f"Response missing choices[0].message.content: {envelope!r}"
        ) from exc

    return _parse_judgment(content)
