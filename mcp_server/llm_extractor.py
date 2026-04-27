"""LLM-backed card-essence extractor for Reflection Pass stage 4.

Path A back-fill (per ``docs/POSITION_METADATA_SCHEMA.md`` §
"Backward compatibility") for legacy cards that don't have
``position_signal`` or ``open_questions`` in frontmatter.

Schema this returns is intentionally minimal — the bare signal that
downstream stages 5 (open thread detection) and 6 (contradiction
surfacing) need:

::

    {
      "claim_summary": "...",   # 1-sentence summary of card's posture
      "open_questions": [...],  # unresolved questions in body
    }

The full ``position_signal`` frontmatter object the back-fill
stage emits is assembled from:

- ``stance`` <- claim_summary (this LLM extraction)
- ``reasoning`` <- card_body_parser.get_section("first_principles")
  + bullet split (NO LLM — structural)
- ``conditions`` <- null (rarely recoverable; LLM hallucinates here)
- ``confidence`` <- "asserted" (legacy cards trust)
- ``emit_source`` <- "refiner_inferred"
- ``topic_assignment`` <- "daemon_clustered"
- ``topic_cluster`` <- from cluster_names cache (separate from
  this extraction)

Keeping the LLM contract narrow (just 2 fields) reduces hallucination
surface. Caller composes the full schema. Cache file deduplicates by
card mtime so re-runs only fire LLM for new/changed cards.

Same architectural pattern as ``llm_namer.py``: stdlib urllib,
zero deps, OPENROUTER_API_KEY/OPENAI_API_KEY env-var fallback,
explicit error structs (LLMExtractorError / LLMExtractorUnavailable).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional


# ---------- exceptions ----------

class LLMExtractorError(Exception):
    """LLM endpoint returned an error or malformed extraction."""


class LLMExtractorUnavailable(LLMExtractorError):
    """No API key or endpoint unreachable."""


# ---------- defaults (mirror llm_namer for operator simplicity) ----------

DEFAULT_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.5-flash"
DEFAULT_TIMEOUT = 60.0  # extraction is heavier than naming
DEFAULT_MAX_TOKENS = 800  # ~6 reasoning bullets + ~5 open questions safely


_SYSTEM_PROMPT = """You analyze refined knowledge-management cards and \
extract two fields:

1. claim_summary: ONE sentence (≤ 30 words) summarizing the card's central \
claim, decision, or stance. If the card is purely descriptive (a how-to, \
reference, or definition) without a stance, write a neutral 1-sentence \
summary of what the card teaches. NEVER fabricate a stance.

2. open_questions: a list of 0-5 short strings, each a SPECIFIC unresolved \
question explicitly raised in the card body or strongly implied by an \
incomplete reasoning chain. Skip rhetorical questions, skip questions \
already answered later in the same card. Empty list when nothing fits.

The card may be written in Chinese, English, or mixed. Return your \
answer in the SAME language as the card's body. If the card uses \
bilingual section headers like "# 🚧 避坑与边界 (Pitfalls & Gotchas)", \
treat the content of the "Pitfalls" / "迭代路径" section as the primary \
source of open_questions.

Return JSON ONLY, no prose before or after, no markdown fences, no \
explanation. Schema:

{"claim_summary": "...", "open_questions": ["...", "..."]}
"""


# ---------- public API ----------

def resolve_endpoint_and_key() -> tuple[Optional[str], Optional[str]]:
    """Same fallback logic as ``llm_namer.resolve_endpoint_and_key``:
    OPENROUTER_API_KEY first, then OPENAI_API_KEY; OPENROUTER_URL
    explicit, then OPENAI_BASE_URL + ``/chat/completions``, then
    ``DEFAULT_URL``.
    """
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
            if base.endswith("/chat/completions"):
                url = base
            else:
                url = base + "/chat/completions"
        else:
            url = DEFAULT_URL

    return url, api_key


def resolve_model() -> str:
    """Read extractor model id from env. Defaults to gemini-2.5-flash
    (fast, cheap, multilingual). Falls back to THROUGHLINE_NAMER_MODEL
    so operators can use one env var if they prefer (less env clutter)."""
    return (
        os.environ.get("THROUGHLINE_EXTRACTOR_MODEL", "").strip()
        or os.environ.get("THROUGHLINE_NAMER_MODEL", "").strip()
        or DEFAULT_MODEL
    )


# ---------- response parsing ----------

def _parse_response(content: str) -> dict:
    """Parse the LLM's text content into the expected schema.

    Tolerates: leading/trailing whitespace, markdown code fences,
    extra text wrapped around the JSON object.

    Validates: ``claim_summary`` is non-empty string,
    ``open_questions`` is a list of strings (empty allowed).

    Raises ``LLMExtractorError`` on unrecoverable malformed output.
    """
    s = content.strip()
    # Strip markdown fences if model wrapped output (despite system prompt)
    if s.startswith("```"):
        # Remove first fence line and trailing fence
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1:]
        if s.endswith("```"):
            s = s[: -3]
        s = s.strip()
    # If still wrapped in extra prose, find the JSON object boundaries
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
        raise LLMExtractorError(f"Could not parse JSON from LLM: {exc}: {content!r}") from exc

    if not isinstance(parsed, dict):
        raise LLMExtractorError(f"LLM response is not a JSON object: {parsed!r}")

    summary = parsed.get("claim_summary")
    if not isinstance(summary, str) or not summary.strip():
        raise LLMExtractorError(
            f"LLM response missing or empty claim_summary: {parsed!r}"
        )

    questions_raw = parsed.get("open_questions", [])
    if not isinstance(questions_raw, list):
        raise LLMExtractorError(
            f"LLM response open_questions not a list: {parsed!r}"
        )
    questions = [
        q.strip() for q in questions_raw
        if isinstance(q, str) and q.strip()
    ]

    return {
        "claim_summary": summary.strip(),
        "open_questions": questions,
    }


# ---------- main entry ----------

def extract_card_essence(
    title: str,
    body: str,
    *,
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT,
    body_chars: int = 4000,
    extra_headers: Optional[dict[str, str]] = None,
) -> dict:
    """Extract claim_summary + open_questions from a card.

    Args:
        title: Card title (frontmatter or filename).
        body: Card body markdown (frontmatter stripped).
        url, api_key, model: env-default-overridable. See
            ``resolve_endpoint_and_key`` / ``resolve_model``.
        timeout: HTTP timeout seconds (default 60s — extraction
            calls are heavier than naming).
        body_chars: Truncate body to this many chars before sending.
            Cards typically run 1.5-3K chars; 4K cap leaves headroom
            for first/last sections without blowing prompt budget.
        extra_headers: Optional headers (e.g., OpenRouter
            HTTP-Referer for cost-attribution dashboards).

    Returns:
        ``{"claim_summary": str, "open_questions": list[str]}``

    Raises:
        LLMExtractorUnavailable: missing API key, endpoint
            unreachable, timeout.
        LLMExtractorError: HTTP non-2xx, malformed JSON, response
            missing required fields.
    """
    if not title or not title.strip():
        raise LLMExtractorError("extract_card_essence: title is empty")
    if not body or not body.strip():
        raise LLMExtractorError("extract_card_essence: body is empty")

    resolved_url, resolved_key = resolve_endpoint_and_key()
    final_url = url or resolved_url
    final_key = api_key or resolved_key
    final_model = model or resolve_model()

    if not final_key:
        raise LLMExtractorUnavailable(
            "No API key found. Set OPENROUTER_API_KEY or "
            "OPENAI_API_KEY (when using OpenAI-compatible endpoints "
            "like OpenRouter / Groq), or pass api_key= explicitly."
        )

    body_excerpt = body.strip()[:body_chars]
    user_prompt = f"# {title.strip()}\n\n{body_excerpt}"

    payload = {
        "model": final_model,
        "temperature": 0.2,
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
        "X-Title": "throughline-position-extractor",
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
        raise LLMExtractorUnavailable(f"LLM endpoint unreachable: {exc}") from exc
    except (TimeoutError, OSError) as exc:
        raise LLMExtractorUnavailable(f"LLM call timeout/socket: {exc}") from exc

    try:
        parsed_envelope = json.loads(data.decode("utf-8", errors="replace"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise LLMExtractorError(f"LLM response not JSON: {exc}") from exc

    try:
        content = parsed_envelope["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMExtractorError(
            f"LLM response missing choices[0].message.content: {parsed_envelope!r}"
        ) from exc

    return _parse_response(content)
