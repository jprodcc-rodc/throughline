"""Resolve the active LLM provider for NON-wizard callers.

Two callers need this:
- The install wizard's preview (already passes `cfg.llm_provider` directly).
- The daemon's `call_llm_json()`, which has no WizardConfig in scope
  and reads from env + config.toml.

This module centralises the precedence so both paths behave the same:

    1. `THROUGHLINE_LLM_PROVIDER` env var
    2. `llm_provider` field in `~/.throughline/config.toml`
    3. `throughline_cli.providers.detect_configured_provider()` — first
       provider whose env var has a key
    4. `"openrouter"` — final default, backward compatible with v0.2.0

The resolve functions return either a provider_id + its preset, or
fall back to the legacy OpenRouter endpoint. Callers use
`resolve_endpoint_and_key()` for the common "give me a URL + bearer
token" shape.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

from . import providers as _p


def _config_path() -> Path:
    override = os.environ.get("THROUGHLINE_CONFIG_DIR")
    base = Path(override).expanduser() if override else (Path.home() / ".throughline")
    return base / "config.toml"


def _read_toml_provider(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:  # pragma: no cover
            import tomli as tomllib  # type: ignore
        with path.open("rb") as fh:
            data = tomllib.load(fh)
        raw = data.get("llm_provider")
        return str(raw).strip().lower() if raw else None
    except (OSError, Exception):
        return None


def resolve_provider_id() -> str:
    """Return the active provider id. Never raises. Always returns a
    non-empty string — worst case it's "openrouter" (the v0.2.0 default)."""
    env = os.environ.get("THROUGHLINE_LLM_PROVIDER", "").strip().lower()
    if env:
        return env
    cfg_value = _read_toml_provider(_config_path())
    if cfg_value:
        return cfg_value
    autodetected = _p.detect_configured_provider()
    if autodetected:
        return autodetected
    return "openrouter"


def resolve_endpoint_and_key() -> Tuple[str, Optional[str], dict, str]:
    """Convenience for the daemon: returns a (url, api_key, extra_headers, provider_id)
    tuple ready to drop into an HTTP request.

    - `url` is always a complete `/chat/completions` URL
    - `api_key` may be None (caller should raise a legible error before
      hitting the network)
    - `extra_headers` are the provider-specific OpenRouter/etc. headers
      (empty dict for providers without any)
    - `provider_id` echoes back the resolved id so the caller can log
      "PROVIDER=openrouter" for debugging
    """
    provider_id = resolve_provider_id()

    # Legacy envelope escape hatch: if the user set OPENROUTER_URL directly
    # (the pre-U28 override point), honour it as the final URL rather than
    # re-deriving from the preset. Same for OPENAI_URL / THROUGHLINE_LLM_URL.
    legacy_override = (
        os.environ.get("OPENROUTER_URL")
        or os.environ.get("THROUGHLINE_LLM_URL")
    )

    try:
        preset = _p.get_preset(provider_id)
        if legacy_override:
            url = legacy_override
            if not url.endswith("/chat/completions"):
                url = url.rstrip("/") + "/chat/completions"
        else:
            url = preset.base_url.rstrip("/") + "/chat/completions"
        key = _p.resolve_api_key(provider_id) or _p.legacy_key_lookup()
        extra = dict(preset.extra_headers)
    except ValueError:
        # Unknown provider_id -- fall back to OpenRouter.
        url = (legacy_override
                or "https://openrouter.ai/api/v1/chat/completions")
        key = _p.legacy_key_lookup()
        extra = {
            "HTTP-Referer": "https://github.com/jprodcc-rodc/throughline",
            "X-Title": "throughline",
        }
        provider_id = "openrouter"

    return url, key, extra, provider_id
