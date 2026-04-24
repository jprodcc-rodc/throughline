"""Thin OpenAI-compatible HTTP client for the install wizard's
preview gate (U17) and other first-pass LLM calls.

Deliberately uses urllib from the stdlib — no OpenAI / anthropic /
langchain dependency pulled in just to fire one chat completion. The
endpoint string defaults to OpenRouter but can be overridden so a
user routing through Anthropic / OpenAI / local Ollama directly only
needs to flip one env var.

Env vars read (in priority order):
    OPENROUTER_API_KEY    — preferred
    OPENAI_API_KEY        — fallback
    THROUGHLINE_LLM_URL   — override the completions endpoint

Returns the raw assistant-message content string. Caller parses JSON.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


def get_api_key() -> Optional[str]:
    for var in ("OPENROUTER_API_KEY", "OPENAI_API_KEY"):
        v = os.environ.get(var, "").strip()
        if v:
            return v
    return None


def get_endpoint() -> str:
    return os.environ.get("THROUGHLINE_LLM_URL", DEFAULT_ENDPOINT)


class LLMError(RuntimeError):
    pass


def call_chat(model_id: str,
              system_prompt: str,
              user_message: str,
              *,
              api_key: Optional[str] = None,
              endpoint: Optional[str] = None,
              response_format: Optional[dict] = None,
              temperature: float = 0.0,
              timeout: float = 60.0,
              referer: str = "https://github.com/jprodcc-rodc/throughline",
              title_header: str = "throughline-install-wizard") -> str:
    """Send one chat-completion request; return the assistant message
    content as a string. Raises LLMError on any failure mode so the
    wizard can catch + render a readable message."""
    key = api_key or get_api_key()
    if not key:
        raise LLMError(
            "no API key — set OPENROUTER_API_KEY or OPENAI_API_KEY in your "
            "shell, then re-run. (OpenRouter free tier signup: "
            "https://openrouter.ai)"
        )
    body: dict = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "temperature": temperature,
    }
    if response_format:
        body["response_format"] = response_format
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    url = endpoint or get_endpoint()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {key}")
    # OpenRouter requires HTTP-Referer + X-Title for routing metrics,
    # OpenAI ignores them, and Ollama is happy either way.
    req.add_header("HTTP-Referer", referer)
    req.add_header("X-Title", title_header)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body_snippet = ""
        try:
            body_snippet = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        raise LLMError(f"HTTP {e.code}: {e.reason}  {body_snippet}") from None
    except urllib.error.URLError as e:
        raise LLMError(f"network: {e.reason}") from None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise LLMError(f"non-JSON response: {raw[:300]}") from None
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise LLMError(f"unexpected response shape: {raw[:300]}") from None
