"""Native Anthropic Messages API adapter.

The `anthropic` provider in `providers.py` previously routed through
Anthropic's OpenAI-compat shim (`/v1/openai`). That worked but gave
up:

- Prompt caching (`cache_control: {"type": "ephemeral"}` on content
  blocks) — the shim ignores it, forcing full re-tokenisation on
  every refine that shares a stable system prompt.
- Tool-use native block shape — the shim approximates via OpenAI's
  function-call format; anything beyond simple call/response
  fractures.
- Accurate usage telemetry — the shim translates token-count field
  names, rounding sometimes.

This module handles the direct `/v1/messages` shape: `x-api-key`
auth, `anthropic-version` header, `system` as a top-level field,
`content` array in the response, `input_tokens` / `output_tokens`
in usage. Callers still pass (system_prompt, user_message) tuples
and get a string back — the translation happens inside.

Used by:
- `throughline_cli/llm.py::call_chat` when `provider_id == "anthropic"`
- `daemon/refine_daemon.py::call_llm_json` when the resolved provider
  at module-load time is `anthropic`
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

# Anthropic API version. Pinned here so a bump is a conscious change,
# not something a dependency update sneaks in. Update alongside the
# changelog note when Anthropic ships a new stable version.
ANTHROPIC_API_VERSION = "2023-06-01"

# Base URL. Overridable for Azure / self-hosted / test harness.
DEFAULT_BASE_URL = "https://api.anthropic.com/v1"


class AnthropicAdapterError(RuntimeError):
    """Anything the adapter can't translate into an OpenAI-compatible
    return. Callers (llm.call_chat / daemon.call_llm_json) re-raise
    as their module's error type."""


def _build_request_body(
    *,
    model: str,
    system_prompt: str,
    user_message: str,
    temperature: float,
    max_tokens: int,
    response_format: Optional[dict] = None,
    enable_prompt_caching: bool = True,
) -> Dict[str, Any]:
    """Translate an OpenAI-shape call into Anthropic's Messages body.

    - system_prompt lives at the top level (not as a `role=system` message)
    - user_message becomes a single user-role content block
    - temperature + max_tokens pass through verbatim
    - response_format is currently ignored (Anthropic has no native
      JSON-mode equivalent; our prompts already instruct the model
      to emit JSON-only). Left on the signature so call sites don't
      need to strip it per-provider.
    - enable_prompt_caching: attaches `cache_control={"type":"ephemeral"}`
      to the system block, which Anthropic caches for ~5 minutes
      between requests. Cheap free wins for repeat refines sharing
      the same system prompt.
    """
    # We keep response_format on the signature only so callers can
    # pass through their OpenAI shape uniformly. Referenced here to
    # avoid a lint fail on unused kwargs; pulled only when we add
    # an Anthropic-native equivalent (likely via tools-as-schema in
    # a later release).
    _ = response_format

    system_block: Any
    if enable_prompt_caching:
        system_block = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]
    else:
        system_block = system_prompt

    body: Dict[str, Any] = {
        "model": model,
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "system": system_block,
        "messages": [
            {"role": "user", "content": user_message},
        ],
    }
    return body


def _parse_response(raw: str) -> Tuple[str, Dict[str, int]]:
    """Extract (text, usage) from an Anthropic response body.

    Returns usage renamed to OpenAI-shape field names
    (`prompt_tokens` / `completion_tokens`) so downstream cost
    trackers that already key off those names keep working.

    `usage` carries an extra `_truncated: True` flag when the
    response stopped on `max_tokens`. Caller can surface a
    user-visible warning instead of letting the truncated body
    fail downstream JSON parsing with a misleading "bad JSON"
    error.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise AnthropicAdapterError(f"non-JSON response: {raw[:300]}") from e

    # Anthropic content is an array of {type: "text", text: "..."}
    # blocks (or tool_use blocks, which we don't use here).
    content_list = data.get("content") or []
    text_parts: list = []
    for block in content_list:
        if isinstance(block, dict) and block.get("type") == "text":
            part = block.get("text")
            if isinstance(part, str):
                text_parts.append(part)
    text = "".join(text_parts)
    if not text:
        raise AnthropicAdapterError(
            f"no text blocks in response: {raw[:300]}"
        )

    # Rename usage fields so cost trackers don't need branching.
    raw_usage = data.get("usage") or {}
    usage = {
        "prompt_tokens":     int(raw_usage.get("input_tokens") or 0),
        "completion_tokens": int(raw_usage.get("output_tokens") or 0),
    }
    # Surface truncation as a sticky bit on the usage dict. We use an
    # underscored key so existing cost-tracker code that walks the dict
    # ignores it.
    if data.get("stop_reason") == "max_tokens":
        usage["_truncated"] = True
    return text, usage


def call_messages(
    *,
    model: str,
    system_prompt: str,
    user_message: str,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    temperature: float = 0.0,
    max_tokens: int = 4000,
    response_format: Optional[dict] = None,
    timeout: float = 60.0,
    enable_prompt_caching: bool = True,
) -> Tuple[str, Dict[str, int]]:
    """Send one Anthropic `/v1/messages` request.

    Returns `(text, usage)` where usage uses OpenAI-shape names
    (`prompt_tokens` / `completion_tokens`). Raises
    `AnthropicAdapterError` on any non-recoverable failure.

    Prompt caching is enabled by default — the system prompt is
    tagged `cache_control: ephemeral` which gives us ~5-minute
    cache hits for refines sharing the same system prompt. The
    refiner runs the same system prompt per slice so this is
    strictly a win.
    """
    body = _build_request_body(
        model=model,
        system_prompt=system_prompt,
        user_message=user_message,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        enable_prompt_caching=enable_prompt_caching,
    )
    url = base_url.rstrip("/") + "/messages"
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", ANTHROPIC_API_VERSION)
    # Opt into the prompt-caching beta header too — some accounts
    # still require it even on recent API versions.
    if enable_prompt_caching:
        req.add_header("anthropic-beta", "prompt-caching-2024-07-31")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body_snippet = ""
        try:
            body_snippet = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        raise AnthropicAdapterError(
            f"HTTP {e.code}: {e.reason}  {body_snippet}"
        ) from None
    except urllib.error.URLError as e:
        raise AnthropicAdapterError(f"network: {e.reason}") from None

    return _parse_response(raw)
