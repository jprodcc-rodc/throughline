"""U28 · LLM provider registry — beyond OpenRouter.

v0.2.0 locked the preview gate (and ingest / daemon) into either
OPENROUTER_API_KEY or OPENAI_API_KEY. Real users run on many other
endpoints: direct Anthropic, direct OpenAI, Together / Fireworks /
Groq / DeepSeek for cheaper/faster inference, SiliconFlow / Moonshot /
DashScope / Zhipu / Doubao for Chinese-market access, Ollama /
LM Studio for fully local, etc.

This module exposes a registry of **OpenAI-compatible** provider
presets — each one is just a (base_url, env_var, signup_url,
default_models) tuple. Any endpoint that speaks OpenAI's
`POST /v1/chat/completions` is a one-line registry entry.

Non-compatible providers (Anthropic's Messages API, Google's Gemini
API) need a separate adapter and are deferred to v0.3. Users wanting
those today should route via OpenRouter, which exposes them under the
compatible shape.

Design goals:
- **Backward compatibility first.** Existing `OPENROUTER_API_KEY` +
  `OPENAI_API_KEY` users keep working without touching their config.
- **Data-driven.** New providers are dict entries, not new modules.
- **Escape hatch.** `generic` lets the user drop in any
  OpenAI-compatible URL + key var the registry doesn't know about.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ProviderPreset:
    """One row in the provider registry."""
    id: str
    name: str
    base_url: str
    env_var: str
    signup_url: str
    models: Tuple[Tuple[str, str], ...]  # (model_id, display_name)
    notes: str = ""
    # Extra headers to add on every request (beyond Authorization).
    # OpenRouter wants HTTP-Referer + X-Title for routing metrics.
    extra_headers: Tuple[Tuple[str, str], ...] = ()
    # Which region / audience this provider mostly targets. Useful
    # for the wizard to group presets sensibly.
    region: str = "global"


# =========================================================
# Presets
# =========================================================
# Keep alphabetical within each region block for predictable wizard
# display ordering. The first entry per provider's model list is
# treated as that provider's default when no model is specified.

_OPENROUTER = ProviderPreset(
    id="openrouter",
    name="OpenRouter",
    base_url="https://openrouter.ai/api/v1",
    env_var="OPENROUTER_API_KEY",
    signup_url="https://openrouter.ai",
    models=(
        ("anthropic/claude-sonnet-4.6",  "Anthropic Sonnet 4.6"),
        ("anthropic/claude-haiku-4.5",   "Anthropic Haiku 4.5"),
        ("anthropic/claude-opus-4.7",    "Anthropic Opus 4.7"),
        ("openai/gpt-5-mini",            "OpenAI GPT-5-mini"),
        ("openai/gpt-5",                 "OpenAI GPT-5"),
        ("google/gemini-3-flash",        "Google Gemini 3 Flash"),
        ("google/gemini-3-pro",          "Google Gemini 3 Pro"),
        ("xai/grok-3",                   "xAI Grok 3"),
        ("deepseek/v3.2",                "DeepSeek v3.2"),
        ("meta-llama/llama-3.3-70b",     "Meta Llama 3.3 70B"),
    ),
    notes="Routes to 300+ models through one key + one endpoint. Default if you don't want to think about this.",
    extra_headers=(
        ("HTTP-Referer", "https://github.com/jprodcc-rodc/throughline"),
        ("X-Title",      "throughline"),
    ),
)

_OPENAI = ProviderPreset(
    id="openai",
    name="OpenAI (direct)",
    base_url="https://api.openai.com/v1",
    env_var="OPENAI_API_KEY",
    signup_url="https://platform.openai.com",
    models=(
        ("gpt-5-mini",     "GPT-5-mini"),
        ("gpt-5",          "GPT-5"),
        ("gpt-4.1",        "GPT-4.1"),
        ("gpt-4.1-mini",   "GPT-4.1-mini"),
        ("o4-mini",        "o4-mini (reasoning)"),
    ),
    notes="Direct OpenAI API. No model IDs prefixed with 'openai/'.",
)

_ANTHROPIC = ProviderPreset(
    id="anthropic",
    name="Anthropic (direct, via OpenAI-compat shim)",
    base_url="https://api.anthropic.com/v1/openai",  # OpenAI compat shim
    env_var="ANTHROPIC_API_KEY",
    signup_url="https://console.anthropic.com",
    models=(
        ("claude-sonnet-4-5-20250929", "Claude Sonnet 4.5"),
        ("claude-opus-4-5-20250929",   "Claude Opus 4.5"),
        ("claude-haiku-4-5-20250929",  "Claude Haiku 4.5"),
    ),
    notes="Uses Anthropic's OpenAI-compatible shim at /v1/openai. Full native Messages API is v0.3.",
)

_DEEPSEEK = ProviderPreset(
    id="deepseek",
    name="DeepSeek (direct)",
    base_url="https://api.deepseek.com/v1",
    env_var="DEEPSEEK_API_KEY",
    signup_url="https://platform.deepseek.com",
    models=(
        ("deepseek-chat",     "DeepSeek-V3.2 (chat)"),
        ("deepseek-reasoner", "DeepSeek-R1 (reasoner)"),
    ),
    notes="Cheapest Sonnet-class alternative. Strong on code.",
)

_TOGETHER = ProviderPreset(
    id="together",
    name="Together.ai",
    base_url="https://api.together.xyz/v1",
    env_var="TOGETHER_API_KEY",
    signup_url="https://together.ai",
    models=(
        ("meta-llama/Llama-3.3-70B-Instruct-Turbo", "Llama 3.3 70B Turbo"),
        ("meta-llama/Llama-3.1-405B-Instruct-Turbo", "Llama 3.1 405B Turbo"),
        ("Qwen/Qwen2.5-72B-Instruct-Turbo", "Qwen2.5 72B Turbo"),
        ("deepseek-ai/DeepSeek-V3", "DeepSeek-V3"),
    ),
    notes="Hosted open-weights models. Fast, cheap for Llama/Qwen/DeepSeek.",
)

_FIREWORKS = ProviderPreset(
    id="fireworks",
    name="Fireworks.ai",
    base_url="https://api.fireworks.ai/inference/v1",
    env_var="FIREWORKS_API_KEY",
    signup_url="https://fireworks.ai",
    models=(
        ("accounts/fireworks/models/llama-v3p3-70b-instruct", "Llama 3.3 70B"),
        ("accounts/fireworks/models/qwen2p5-72b-instruct",    "Qwen 2.5 72B"),
        ("accounts/fireworks/models/deepseek-v3",              "DeepSeek V3"),
    ),
    notes="Fast open-weights inference. Model IDs carry the 'accounts/fireworks/' prefix.",
)

_GROQ = ProviderPreset(
    id="groq",
    name="Groq (fastest inference)",
    base_url="https://api.groq.com/openai/v1",
    env_var="GROQ_API_KEY",
    signup_url="https://console.groq.com",
    models=(
        ("llama-3.3-70b-versatile", "Llama 3.3 70B"),
        ("llama-3.1-8b-instant",    "Llama 3.1 8B (instant)"),
        ("qwen-qwq-32b",            "Qwen QwQ 32B"),
    ),
    notes="LPU inference; 10x latency advantage for real-time chat.",
)

_XAI = ProviderPreset(
    id="xai",
    name="xAI (Grok direct)",
    base_url="https://api.x.ai/v1",
    env_var="XAI_API_KEY",
    signup_url="https://console.x.ai",
    models=(
        ("grok-3",         "Grok 3"),
        ("grok-3-mini",    "Grok 3 Mini"),
    ),
    notes="Direct xAI endpoint. Use OpenRouter if you also want non-xAI models.",
)

# --- Chinese-market providers ---

_SILICONFLOW = ProviderPreset(
    id="siliconflow",
    name="SiliconFlow (硅基流动)",
    base_url="https://api.siliconflow.cn/v1",
    env_var="SILICONFLOW_API_KEY",
    signup_url="https://siliconflow.cn",
    models=(
        ("Qwen/Qwen2.5-72B-Instruct",    "Qwen2.5 72B"),
        ("Qwen/Qwen2.5-32B-Instruct",    "Qwen2.5 32B"),
        ("deepseek-ai/DeepSeek-V3",       "DeepSeek V3"),
        ("Qwen/QwQ-32B-Preview",         "QwQ 32B (reasoning)"),
        ("meta-llama/Meta-Llama-3.1-70B-Instruct", "Llama 3.1 70B"),
    ),
    notes="Chinese-market proxy; Qwen + DeepSeek + Llama with 大陆 access.",
    region="cn",
)

_MOONSHOT = ProviderPreset(
    id="moonshot",
    name="Moonshot (Kimi)",
    base_url="https://api.moonshot.cn/v1",
    env_var="MOONSHOT_API_KEY",
    signup_url="https://platform.moonshot.cn",
    models=(
        ("moonshot-v1-8k",   "Moonshot v1 (8k context)"),
        ("moonshot-v1-32k",  "Moonshot v1 (32k context)"),
        ("moonshot-v1-128k", "Moonshot v1 (128k context)"),
    ),
    notes="Kimi's direct API. Long-context strong for refining long chats.",
    region="cn",
)

_DASHSCOPE = ProviderPreset(
    id="dashscope",
    name="DashScope (Alibaba Qwen)",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    env_var="DASHSCOPE_API_KEY",
    signup_url="https://dashscope.aliyun.com",
    models=(
        ("qwen-max",          "Qwen Max"),
        ("qwen-plus",         "Qwen Plus"),
        ("qwen-turbo",        "Qwen Turbo"),
        ("qwen2.5-72b-instruct", "Qwen 2.5 72B"),
    ),
    notes="Alibaba's hosted Qwen. Uses OpenAI-compatible mode endpoint.",
    region="cn",
)

_ZHIPU = ProviderPreset(
    id="zhipu",
    name="Zhipu AI (智谱 GLM)",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    env_var="ZHIPU_API_KEY",
    signup_url="https://open.bigmodel.cn",
    models=(
        ("glm-4-plus",   "GLM-4 Plus"),
        ("glm-4",        "GLM-4"),
        ("glm-4-air",    "GLM-4 Air"),
        ("glm-4-flash",  "GLM-4 Flash (free tier)"),
    ),
    notes="GLM family. glm-4-flash has a generous free tier.",
    region="cn",
)

_DOUBAO = ProviderPreset(
    id="doubao",
    name="Doubao (字节豆包 / Volcengine Ark)",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    env_var="ARK_API_KEY",
    signup_url="https://console.volcengine.com/ark",
    models=(
        # ByteDance publishes "ep-xxxx" endpoint IDs rather than model
        # names; user must create an inference endpoint first and paste
        # its ID. These are placeholder display names.
        ("doubao-pro-32k",       "Doubao Pro (32k) [endpoint ID required]"),
        ("doubao-lite-32k",      "Doubao Lite (32k) [endpoint ID required]"),
    ),
    notes="Volcengine Ark = Doubao. Model ID must be the user's own endpoint (ep-xxxx), not a friendly name. See signup URL.",
    region="cn",
)

# --- Local / self-hosted ---

_OLLAMA = ProviderPreset(
    id="ollama",
    name="Ollama (local, default port)",
    base_url="http://localhost:11434/v1",
    env_var="OLLAMA_API_KEY",  # Ollama doesn't need a key but some forks do
    signup_url="https://ollama.com",
    models=(
        ("llama3.3:70b",   "Llama 3.3 70B"),
        ("qwen2.5:72b",    "Qwen 2.5 72B"),
        ("deepseek-v3:671b", "DeepSeek V3 (huge)"),
        ("gemma2:27b",     "Gemma 2 27B"),
    ),
    notes="Needs `ollama pull <model>` first. Auth: empty key works for vanilla Ollama; set OLLAMA_API_KEY=any value for forks that check.",
    region="local",
)

_LM_STUDIO = ProviderPreset(
    id="lm_studio",
    name="LM Studio (local, default port)",
    base_url="http://localhost:1234/v1",
    env_var="LM_STUDIO_API_KEY",
    signup_url="https://lmstudio.ai",
    models=(
        ("local-model",    "Whatever LM Studio is serving"),
    ),
    notes="The model ID is ignored by LM Studio; whatever you loaded in the GUI is what responds.",
    region="local",
)

_GENERIC = ProviderPreset(
    id="generic",
    name="Generic OpenAI-compatible endpoint",
    base_url="",  # user supplies
    env_var="THROUGHLINE_LLM_API_KEY",
    signup_url="",
    models=(),
    notes="Escape hatch for any provider not in the registry. Set THROUGHLINE_LLM_URL (base_url) + THROUGHLINE_LLM_API_KEY (key) and pick your own model ID.",
    region="custom",
)


_ALL_PRESETS: Tuple[ProviderPreset, ...] = (
    # Global
    _OPENROUTER, _OPENAI, _ANTHROPIC,
    _DEEPSEEK, _TOGETHER, _FIREWORKS, _GROQ, _XAI,
    # China
    _SILICONFLOW, _MOONSHOT, _DASHSCOPE, _ZHIPU, _DOUBAO,
    # Local / self-hosted
    _OLLAMA, _LM_STUDIO,
    # Escape hatch
    _GENERIC,
)

_REGISTRY: Dict[str, ProviderPreset] = {p.id: p for p in _ALL_PRESETS}


# =========================================================
# Public API
# =========================================================

def list_presets() -> List[ProviderPreset]:
    """Registry order = wizard display order."""
    return list(_ALL_PRESETS)


def get_preset(provider_id: str) -> ProviderPreset:
    """Raise ValueError on unknown ID; the wizard surfaces that."""
    p = _REGISTRY.get(provider_id.strip().lower())
    if p is None:
        raise ValueError(
            f"Unknown provider: {provider_id!r}. Known: "
            f"{', '.join(sorted(_REGISTRY.keys()))}"
        )
    return p


def register_preset(preset: ProviderPreset) -> None:
    """Plug-in point for downstream users adding a provider without
    patching this module."""
    _REGISTRY[preset.id] = preset


def presets_by_region(region: str) -> List[ProviderPreset]:
    return [p for p in _ALL_PRESETS if p.region == region]


def detect_configured_provider() -> Optional[str]:
    """Inspect env vars and return the first provider id with a key
    set, or None. Used for backward compat + auto-defaulting."""
    # Keep OpenRouter first so existing users don't get silently
    # swapped to another provider just because they happen to also
    # have OPENAI_API_KEY set.
    ordered = [_OPENROUTER, _OPENAI, _ANTHROPIC, _DEEPSEEK, _TOGETHER,
                _FIREWORKS, _GROQ, _XAI, _SILICONFLOW, _MOONSHOT,
                _DASHSCOPE, _ZHIPU, _DOUBAO]
    for p in ordered:
        v = os.environ.get(p.env_var, "").strip()
        if v:
            return p.id
    return None


def resolve_base_url(provider_id: str) -> str:
    """For the generic preset, fall back to THROUGHLINE_LLM_URL."""
    preset = get_preset(provider_id)
    if preset.id == "generic":
        return os.environ.get("THROUGHLINE_LLM_URL",
                               "https://openrouter.ai/api/v1").rstrip("/")
    return preset.base_url.rstrip("/")


def resolve_api_key(provider_id: str) -> Optional[str]:
    """Read the provider's specific env var. Returns None if unset."""
    preset = get_preset(provider_id)
    key = os.environ.get(preset.env_var, "").strip()
    return key or None


# =========================================================
# Backward compatibility shims for tests / existing callers
# =========================================================

def legacy_key_lookup() -> Optional[str]:
    """Mimic the pre-U28 two-env-var fallback: OPENROUTER_API_KEY
    then OPENAI_API_KEY. Still used by `throughline_cli.llm.get_api_key`
    when no provider id is in play."""
    for var in ("OPENROUTER_API_KEY", "OPENAI_API_KEY"):
        v = os.environ.get(var, "").strip()
        if v:
            return v
    return None
