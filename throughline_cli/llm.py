"""Thin OpenAI-compatible HTTP client for the install wizard's
preview gate (U17) and other first-pass LLM calls.

Deliberately uses urllib from the stdlib — no OpenAI / anthropic /
langchain dependency pulled in just to fire one chat completion.

**v0.2.x (U28) rewrite:** endpoint + API key resolved from a provider
registry (`throughline_cli.providers`). The caller passes
`provider_id="openrouter" | "openai" | "deepseek" | "siliconflow" |
…`, or omits it to get the legacy behaviour (auto-detect from whatever
env var is set, falling back to OpenRouter).

Env vars read (priority):
    1. the provider's specific var from providers.py
       (OPENROUTER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY,
        DEEPSEEK_API_KEY, TOGETHER_API_KEY, FIREWORKS_API_KEY,
        GROQ_API_KEY, XAI_API_KEY, SILICONFLOW_API_KEY,
        MOONSHOT_API_KEY, DASHSCOPE_API_KEY, ZHIPU_API_KEY,
        ARK_API_KEY, OLLAMA_API_KEY, LM_STUDIO_API_KEY,
        THROUGHLINE_LLM_API_KEY)
    2. legacy OPENROUTER_API_KEY > OPENAI_API_KEY (if no provider given)
    3. THROUGHLINE_LLM_URL overrides the base_url of the generic preset

Returns the raw assistant-message content string. Caller parses JSON.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Optional

from . import providers as _p

DEFAULT_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"


def get_api_key(provider_id: Optional[str] = None) -> Optional[str]:
    """Resolve an API key.

    - When `provider_id` is supplied AND known, reads that provider's env var.
    - When `provider_id` is unknown (typo, custom registry entry removed),
      falls back to the legacy chain so the call doesn't crash.
    - When omitted, falls back to the legacy OPENROUTER > OPENAI chain
      so pre-U28 callers keep working without a config update.
    """
    if provider_id:
        try:
            return _p.resolve_api_key(provider_id)
        except ValueError:
            return _p.legacy_key_lookup()
    return _p.legacy_key_lookup()


def get_endpoint(provider_id: Optional[str] = None) -> str:
    """Resolve the chat-completions endpoint URL.

    - Explicit, known provider: `<base_url>/chat/completions`.
    - Explicit, unknown provider: fall through to the legacy path.
    - No provider, `THROUGHLINE_LLM_URL` set: that value.
    - No provider, no env: OpenRouter default.
    """
    if provider_id:
        try:
            return _p.resolve_base_url(provider_id).rstrip("/") + "/chat/completions"
        except ValueError:
            pass
    return os.environ.get("THROUGHLINE_LLM_URL", DEFAULT_ENDPOINT)


class LLMError(RuntimeError):
    pass


def call_chat(model_id: str,
              system_prompt: str,
              user_message: str,
              *,
              provider_id: Optional[str] = None,
              api_key: Optional[str] = None,
              endpoint: Optional[str] = None,
              response_format: Optional[dict] = None,
              temperature: float = 0.0,
              timeout: float = 60.0,
              referer: str = "https://github.com/jprodcc-rodc/throughline",
              title_header: str = "throughline-install-wizard") -> str:
    """Send one chat-completion request; return the assistant message
    content as a string. Raises LLMError on any failure mode so the
    wizard can catch + render a readable message.

    Preset-aware behaviour when `provider_id` is supplied:
    - api_key auto-resolves from the provider's env var
    - endpoint auto-resolves to <base_url>/chat/completions
    - provider-specific extra headers (e.g. OpenRouter's
      HTTP-Referer + X-Title) are added automatically

    Explicit `api_key` + `endpoint` override the preset. This lets
    callers use a provider preset for URL discovery but a different
    key source (e.g. a 1Password-fetched token).
    """
    key = api_key or get_api_key(provider_id)
    if not key:
        # Give a provider-specific hint if we know which one the
        # caller wanted; fall back to the generic "signup OpenRouter".
        if provider_id:
            try:
                p = _p.get_preset(provider_id)
                raise LLMError(
                    f"no API key — set {p.env_var} in your shell, then "
                    f"re-run. (Signup: {p.signup_url or '<check provider docs>'})"
                )
            except ValueError:
                pass
        raise LLMError(
            "no API key — set OPENROUTER_API_KEY or OPENAI_API_KEY in "
            "your shell, then re-run. (OpenRouter free tier signup: "
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
    url = endpoint or get_endpoint(provider_id)
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {key}")
    # Provider-specific extra headers (OpenRouter routing metrics,
    # anthropic-version, etc.).
    if provider_id:
        try:
            preset = _p.get_preset(provider_id)
            for k, v in preset.extra_headers:
                req.add_header(k, v)
        except ValueError:
            pass
    else:
        # Legacy path: assume OpenRouter, which is what the default
        # endpoint is. The headers are cheap on every provider.
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
