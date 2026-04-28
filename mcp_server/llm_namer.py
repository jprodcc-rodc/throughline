"""LLM-backed cluster namer for Reflection Pass stage 3.

Given a list of card titles in a cluster, calls an OpenAI-compatible
chat-completions endpoint and returns a single snake_case topic
name (e.g. ``"pricing_strategy"``).

Architectural choice: this is a thin HTTP client (stdlib urllib,
no external deps) rather than reusing ``daemon.refine_daemon.call_llm_json``.
The daemon's helper resolves provider config at module load and
imports a chain of throughline_cli adapters; mcp_server stays
decoupled from daemon/ for the same reason it stays decoupled from
the OpenWebUI Filter form (different deployment surfaces, different
upgrade cadences).

Same env-var contract as the daemon for operator simplicity:

- ``OPENROUTER_API_KEY`` — required to issue real calls
- ``OPENROUTER_URL`` — optional override
  (default ``https://openrouter.ai/api/v1/chat/completions``)
- ``THROUGHLINE_NAMER_MODEL`` — model id
  (default ``google/gemini-2.5-flash``; cheap, fast, multilingual)

Per the locked decision Q3 in
``private/MCP_SCAFFOLDING_PLAN.md`` § 12.A: tools and helpers in
mcp_server/ surface explicit error structs rather than raising —
the host LLM (Claude / Cursor / Continue) handles errors
gracefully. ``LLMNamerError`` / ``LLMNamerUnavailable`` follow the
same shape as ``rag_client.RAGClientError`` /
``RAGServerUnreachable``.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Optional


# ---------- exceptions ----------

class LLMNamerError(Exception):
    """LLM endpoint returned an error or malformed response."""


class LLMNamerUnavailable(LLMNamerError):
    """No API key or endpoint unreachable. Distinguishable from other
    errors so the daemon can fall back to a synthetic name without
    raising on every cluster."""


# ---------- defaults ----------

DEFAULT_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.5-flash"
DEFAULT_TIMEOUT = 30.0


_SYSTEM_PROMPT = (
    "You name clusters of related notes. Given the titles of cards in "
    "one cluster, return EXACTLY ONE snake_case topic identifier of "
    "1-4 lowercase English words separated by underscores. No "
    "punctuation, no whitespace, no quotes. The name should be the "
    "tightest accurate summary; if titles span multiple clear "
    "subtopics, name the dominant one. Examples of good output: "
    "pricing_strategy, b1_thiamine_therapy, soft_router_setup, "
    "diablo_4_build_optimization. Do NOT explain. Output the "
    "identifier only."
)


# ---------- public API ----------

def resolve_endpoint_and_key() -> tuple[Optional[str], Optional[str]]:
    """Read URL + API key from environment.

    Resolution order for the API key:

    1. ``OPENROUTER_API_KEY`` (matches the daemon's convention)
    2. ``OPENAI_API_KEY`` (matches the broad ecosystem pattern of
       "use the OpenAI client lib pointed at OpenRouter / Groq /
       any OpenAI-compatible provider")

    Resolution order for the URL:

    1. ``OPENROUTER_URL`` (explicit override)
    2. ``OPENAI_BASE_URL`` + ``/chat/completions`` suffix when
       absent (the OPENAI_BASE_URL convention is "the API root
       without ``/chat/completions``")
    3. ``DEFAULT_URL`` (OpenRouter)

    Returns:
        (url, api_key). Either may be None when not configured. The
        caller is responsible for deciding whether to attempt a call;
        ``name_cluster`` raises ``LLMNamerUnavailable`` when key is
        absent.
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
    """Read namer model id from env (default: gemini-2.5-flash)."""
    return os.environ.get("THROUGHLINE_NAMER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


_VALID_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,79}$")


def _sanitize_name(raw: str) -> str:
    """Coerce model output into the snake_case contract.

    LLMs occasionally emit decorative wrapping (quotes, asterisks,
    "Topic: foo", trailing period). Strip aggressively, then validate.
    Returns empty string when unable to recover a valid identifier.
    """
    s = raw.strip()
    # Strip wrapping quotes / backticks / asterisks
    s = re.sub(r"^[\"'`*\s]+|[\"'`*\s]+$", "", s)
    # Strip leading "Topic:" / "Name:" prefix the model sometimes adds
    s = re.sub(r"^(?:topic|name|cluster|label)\s*:\s*", "", s, flags=re.I)
    # Take only the first line
    s = s.split("\n")[0].strip()
    # Lowercase + collapse whitespace to underscore
    s = re.sub(r"\s+", "_", s.lower())
    # Drop any trailing period or comma
    s = s.rstrip(".,;")
    # Replace any leftover non-snake-case chars with underscore
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if _VALID_NAME_RE.match(s):
        return s
    return ""


def name_cluster(
    titles: list[str],
    *,
    url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT,
    extra_headers: Optional[dict[str, str]] = None,
) -> str:
    """Call LLM to name a cluster.

    Args:
        titles: Card titles in this cluster. Function trims to first
            20 to keep prompt size bounded; the model doesn't need
            more than that to disambiguate a topic.
        url: Override endpoint URL (else env / default).
        api_key: Override API key (else env).
        model: Override model id (else env / default).
        timeout: HTTP timeout in seconds.
        extra_headers: Optional headers (e.g. OpenRouter HTTP-Referer
            for cost-attribution dashboards).

    Returns:
        snake_case topic name (e.g. ``"pricing_strategy"``).

    Raises:
        LLMNamerUnavailable: when API key is missing or endpoint is
            unreachable.
        LLMNamerError: when the call returns a non-2xx response or
            the model output cannot be sanitized into a valid name.
    """
    if not titles:
        raise LLMNamerError("name_cluster: titles list is empty")

    resolved_url, resolved_key = resolve_endpoint_and_key()
    final_url = url or resolved_url
    final_key = api_key or resolved_key
    final_model = model or resolve_model()

    if not final_key:
        raise LLMNamerUnavailable(
            "No API key found. Set OPENROUTER_API_KEY or "
            "OPENAI_API_KEY (when using OpenAI-compatible endpoints "
            "like OpenRouter / Groq), or pass api_key= explicitly."
        )

    # Bound prompt size: take first 20 titles, truncate each to 200 chars.
    sample = titles[:20]
    titles_text = "\n".join(f"- {t.strip()[:200]}" for t in sample)
    user_prompt = (
        f"Cluster contains {len(titles)} cards. Showing {len(sample)} titles:\n\n"
        f"{titles_text}\n\nName this cluster:"
    )

    payload = {
        "model": final_model,
        "temperature": 0.1,
        "max_tokens": 32,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {final_key}",
        "Content-Type": "application/json",
        "X-Title": "throughline-cluster-namer",
    }
    if extra_headers:
        for k, v in extra_headers.items():
            if k.lower() != "x-title":
                headers.setdefault(k, v)

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(final_url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.URLError as exc:
        raise LLMNamerUnavailable(f"LLM endpoint unreachable: {exc}") from exc
    except (TimeoutError, OSError) as exc:
        raise LLMNamerUnavailable(f"LLM call timeout/socket error: {exc}") from exc

    try:
        parsed = json.loads(data.decode("utf-8", errors="replace"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise LLMNamerError(f"LLM response not JSON: {exc}") from exc

    try:
        choice = parsed["choices"][0]
        content = choice["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMNamerError(
            f"LLM response missing choices[0].message.content: {parsed!r}"
        ) from exc

    name = _sanitize_name(content)
    if not name:
        raise LLMNamerError(
            f"LLM emitted unusable cluster name: {content!r}"
        )
    return name
