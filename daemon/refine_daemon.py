#!/usr/bin/env python3
"""Throughline Refine Daemon.

Pipeline:
  OpenWebUI raw MD (watchdog) -> Extension Value Judge (Gemini Flash) ->
  Echo Guard (cosine + Haiku judge) -> Slicer (Sonnet/Opus dispatch) ->
  Refiner (six-section body + knowledge_identity + XYZ tags) ->
  Domain + Subpath routing -> Dedup (Qdrant cosine) ->
  Dual-write (formal JD path + buffer stub) -> Qdrant upsert.

Pack-aware: a matched pack overrides slicer/refiner prompts, routing
base_path, and knowledge_identity policies. See `packs/pack_runtime.py`
for pack match precedence (prefix > source_model > topic_pin > route_prefix).

Intent modes (detected from user marker messages):
  /brainstorm -> forced personal_ephemeral, relaxed retention gates
  /decision   -> forced personal_persistent, tighter retention gates
  @refine     -> bypass extension judge + echo guard (user force-trigger)

Environment variables (all optional, see config/.env.example):
  THROUGHLINE_VAULT_ROOT            : Obsidian vault root (default ~/ObsidianVault)
  THROUGHLINE_RAW_ROOT              : raw conversation MD root
  THROUGHLINE_STATE_DIR             : daemon state directory
  THROUGHLINE_FORBIDDEN_PREFIXES_JSON : path to JSON list of Qdrant-forbidden prefixes
  OPENROUTER_API_KEY                : LLM API key
  REFINE_SLICE_MODEL, REFINE_MODEL  : model overrides
  QDRANT_URL, QDRANT_COLLECTION     : Qdrant endpoint + default collection
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from queue import Queue, Empty
from threading import Thread, Lock
from typing import Any, Dict, List, Optional, Tuple

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from daemon.taxonomy import (
    JD_ROOT_MAP,
    JD_LEAF_WHITELIST,
    JD_FALLBACK_PATH,
    VALID_X_SET,
    VALID_Y_SET,
    VALID_Z_SET,
    normalize_route_path,
    is_valid_leaf_route,
)
from daemon.taxonomy_observer import record_taxonomy_observation
from daemon.budget import budget_exceeded as _budget_exceeded, load_budget as _load_daily_budget
from daemon.dials import load_dials_from_config as _load_dials, render_dial_modifier as _render_dials
from packs.pack_runtime import PackRegistry

# Soft-import source-model opt-out guard. Daemon runs fine without it.
try:
    from daemon.pack_source_model_guard import evaluate_source_model as _source_model_guard
except Exception:  # pragma: no cover - daemon stays alive if guard missing
    _source_model_guard = None


# =========================================================
# Helpers for env parsing
# =========================================================

def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


# =========================================================
# Core paths
# =========================================================

VAULT_ROOT = Path(os.getenv("THROUGHLINE_VAULT_ROOT", str(Path.home() / "ObsidianVault"))).expanduser()
RAW_ROOT = Path(os.getenv("THROUGHLINE_RAW_ROOT", str(Path.home() / "throughline_runtime" / "sources" / "openwebui_raw"))).expanduser()
STATE_DIR = Path(os.getenv("THROUGHLINE_STATE_DIR", str(Path.home() / "throughline_runtime" / "state"))).expanduser()
LOG_DIR = Path(os.getenv("THROUGHLINE_LOG_DIR", str(Path.home() / "throughline_runtime" / "logs"))).expanduser()
PACKS_DIR = Path(os.getenv("THROUGHLINE_PACKS_DIR", str(Path(__file__).parent.parent / "packs"))).expanduser()

STATE_FILE = STATE_DIR / "refine_state.json"
LOG_FILE = LOG_DIR / "refine_daemon.log"
COST_STATS_FILE = STATE_DIR / "cost_stats.json"

BUFFER_DIR = VAULT_ROOT / "00_Buffer" / "00.03_Refined_Notes"
DAEMON_ISSUES_PATH = VAULT_ROOT / "00_Buffer" / "00.02_Data_Ingest" / "00.02.07_Daemon_Issues.md"
AUTO_REFINE_LOG_PATH = VAULT_ROOT / "00_Buffer" / "00.02_Data_Ingest" / "00.02.08_Auto_Refine_Log.md"
REFINE_INDEX_PATH = VAULT_ROOT / "00_Buffer" / "00.02_Data_Ingest" / "00.02.04_Refine_Processing_Index.md"

SYNAPSE_MARKER = os.getenv("REFINE_SYNAPSE_MARKER", "> [!info] Synapse link")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =========================================================
# LLM + pricing config
# =========================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# U28 · provider-aware LLM endpoint resolution.
# Resolved once at module load; change requires a daemon restart
# (same as every other env-driven default in this file).
try:
    from throughline_cli.active_provider import resolve_endpoint_and_key as _resolve_llm
    _LLM_URL, _LLM_KEY, _LLM_EXTRA_HEADERS, _LLM_PROVIDER_ID = _resolve_llm()
except Exception as _e:  # pragma: no cover -- defensive
    _LLM_URL = "https://openrouter.ai/api/v1/chat/completions"
    _LLM_KEY = OPENROUTER_API_KEY or None
    _LLM_EXTRA_HEADERS = {
        "HTTP-Referer": "https://github.com/jprodcc-rodc/throughline",
        "X-Title":      "throughline",
    }
    _LLM_PROVIDER_ID = "openrouter"
OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
LLM_TITLE = os.getenv("THROUGHLINE_LLM_TITLE", "throughline-refine-daemon")

SLICE_MODEL = os.getenv("REFINE_SLICE_MODEL", "anthropic/claude-sonnet-4.6")
SLICE_ONESHOT_MODEL = os.getenv("REFINE_SLICE_ONESHOT_MODEL", "anthropic/claude-sonnet-4.6")
SLICE_OPUS_MODEL = os.getenv("REFINE_SLICE_OPUS_MODEL", "anthropic/claude-opus-4")
REFINE_MODEL = os.getenv("REFINE_MODEL", "anthropic/claude-sonnet-4.6")
ROUTE_MODEL = os.getenv("REFINE_ROUTE_MODEL", "anthropic/claude-sonnet-4.6")
ECHO_JUDGE_MODEL = os.getenv("ECHO_JUDGE_MODEL", "anthropic/claude-haiku-4.5")
EPHEMERAL_JUDGE_MODEL = os.getenv("EPHEMERAL_JUDGE_MODEL", "anthropic/claude-haiku-4.5")
EXT_JUDGE_MODEL = os.getenv("EXT_JUDGE_MODEL", "google/gemini-3-flash-preview")
EXT_JUDGE_MAX_TOKENS = env_int("EXT_JUDGE_MAX_TOKENS", 200)
EXT_JUDGE_MIN_NEW_MSGS = env_int("EXT_JUDGE_MIN_NEW_MSGS", 2)
EXT_JUDGE_MIN_NEW_CHARS = env_int("EXT_JUDGE_MIN_NEW_CHARS", 200)

# Pricing table ($/1M tokens, input/output). Safe fallback for unknown models.
MODEL_PRICING = {
    "anthropic/claude-sonnet-4.6": (3.0, 15.0),
    "anthropic/claude-opus-4": (15.0, 75.0),
    "anthropic/claude-haiku-4.5": (0.80, 4.0),
    "google/gemini-3-flash-preview": (0.075, 0.30),
}


# =========================================================
# Slice / Refine / Route tuning knobs
# =========================================================

SLICE_SINGLE_THRESHOLD_MSGS = env_int("REFINE_SLICE_SINGLE_THRESHOLD_MSGS", 6)
SLICE_SINGLE_THRESHOLD_CHARS = env_int("REFINE_SLICE_SINGLE_THRESHOLD_CHARS", 4000)
SLICE_ONESHOT_MAX_MSGS = env_int("REFINE_SLICE_ONESHOT_MAX_MSGS", 60)
SLICE_ONESHOT_MAX_CHARS = env_int("REFINE_SLICE_ONESHOT_MAX_CHARS", 60000)

REFINE_MAX_TOKENS = env_int("REFINE_MAX_TOKENS", 6000)
SLICE_MAX_TOKENS = env_int("REFINE_SLICE_MAX_TOKENS", 4000)
ROUTE_MAX_TOKENS = env_int("REFINE_ROUTE_MAX_TOKENS", 400)

# Method H retention gates
RETENTION_MIN_USER_RATIO = env_float("RETENTION_MIN_USER_RATIO", 0.18)
RETENTION_MIN_BODY_CHARS = env_int("RETENTION_MIN_BODY_CHARS", 400)
RETENTION_MIN_SECTIONS_COMPLETE = env_int("RETENTION_MIN_SECTIONS_COMPLETE", 3)

# Dedup
DEDUP_COSINE_THRESHOLD = env_float("DEDUP_COSINE_THRESHOLD", 0.90)
DEDUP_DATE_WINDOW_DAYS = env_int("DEDUP_DATE_WINDOW_DAYS", 14)

# Echo Guard
ECHO_GUARD_ENABLED = env_bool("ECHO_GUARD_ENABLED", True)
ECHO_PASS_BELOW = env_float("ECHO_PASS_BELOW", 0.60)
ECHO_JUDGE_WINDOW_LO = env_float("ECHO_JUDGE_WINDOW_LO", 0.60)
ECHO_JUDGE_WINDOW_HI = env_float("ECHO_JUDGE_WINDOW_HI", 0.80)
ECHO_BLOCK_ABOVE = env_float("ECHO_BLOCK_ABOVE", 0.80)
ECHO_FP_MIN_CHARS = env_int("ECHO_FP_MIN_CHARS", 10)
ECHO_AGE_BYPASS_DAYS = env_int("ECHO_AGE_BYPASS_DAYS", 30)

# Ephemeral judge
EPHEMERAL_GREY_USER_LO = env_int("EPHEMERAL_GREY_USER_LO", 10)
EPHEMERAL_GREY_USER_HI = env_int("EPHEMERAL_GREY_USER_HI", 80)

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
# Historically this was QDRANT_COLLECTION with default "knowledge_notes", which
# silently diverged from rag_server / ingest_qdrant (RAG_COLLECTION,
# "obsidian_notes"). Unified under RAG_COLLECTION; QDRANT_COLLECTION remains
# a deprecated fallback so existing .env files keep working.
QDRANT_COLLECTION = (
    os.getenv("RAG_COLLECTION")
    or os.getenv("QDRANT_COLLECTION")
    or "obsidian_notes"
)
QDRANT_UPSERT_ENABLED = env_bool("QDRANT_UPSERT_ENABLED", True)
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://127.0.0.1:8000/v1/embeddings")

# macOS notifications
MACOS_NOTIFY_ENABLED = env_bool("MACOS_NOTIFY_ENABLED", sys.platform == "darwin")

# Watchdog debounce
DEBOUNCE_SECONDS = env_int("DEBOUNCE_SECONDS", 8)
MAX_RETRY = env_int("MAX_RETRY", 2)


# =========================================================
# Qdrant forbidden-prefix allow-list (opt-in via JSON config)
# =========================================================

def _load_forbidden_prefixes() -> Tuple[str, ...]:
    """Return a tuple of path prefixes that must never be upserted to the
    default Qdrant collection. Paths are forward-slash normalised.

    Configured via env `THROUGHLINE_FORBIDDEN_PREFIXES_JSON` pointing to a
    JSON list. Empty tuple by default (no forbidden prefixes). Users who
    keep private / sensitive subdirectories in their vault can list them
    here to prevent them being embedded into the shared collection.
    """
    path = os.getenv("THROUGHLINE_FORBIDDEN_PREFIXES_JSON", "")
    if not path:
        return ()
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return ()
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return tuple(str(x).strip().replace(os.sep, "/") for x in data if str(x).strip())
    except Exception:
        pass
    return ()


_QDRANT_DEFAULT_FORBIDDEN_PREFIXES: Tuple[str, ...] = _load_forbidden_prefixes()


# =========================================================
# Logging
# =========================================================

_LOG_LOCK = Lock()


def log(msg: str) -> None:
    line = f"[{now_str()}] {msg}"
    print(line, flush=True)
    try:
        ensure_dir(LOG_FILE.parent)
        with _LOG_LOCK:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        pass


_COST_STATS_LOCK = Lock()


def _atomic_write_json(path: Path, payload: Any) -> None:
    """Write JSON with a temp-file-rename so a concurrent reader
    never sees a half-written file. The watchdog daemon has many
    threads + the user's stats / cost CLIs may read mid-write;
    truncate-then-write would let them parse garbage."""
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    # os.replace is atomic on POSIX + Windows.
    os.replace(tmp, path)


def _record_cost(step_name: str, model: str, input_tokens: int, output_tokens: int) -> None:
    """Append a cost entry to state/cost_stats.json keyed by date+step."""
    if not step_name or not model:
        return
    # Clamp to non-negative — providers occasionally return missing /
    # garbled usage values that decode as negative ints, and
    # negative cost would underflow the daily-budget check, silently
    # raising the cap.
    input_tokens = max(0, int(input_tokens or 0))
    output_tokens = max(0, int(output_tokens or 0))
    pricing = MODEL_PRICING.get(model, (3.0, 15.0))
    cost = (input_tokens * pricing[0] + output_tokens * pricing[1]) / 1_000_000.0
    today = datetime.now().strftime("%Y-%m-%d")
    # Lock the read-modify-write window: without this, two concurrent
    # refine threads would both load the same baseline, both compute
    # updates against it, and the second write would clobber the
    # first thread's increments — silent cost-tracking loss.
    with _COST_STATS_LOCK:
        try:
            stats: Dict[str, Any] = {}
            if COST_STATS_FILE.exists():
                stats = json.loads(COST_STATS_FILE.read_text(encoding="utf-8"))
            by_date = stats.setdefault("by_date", {})
            day = by_date.setdefault(today, {})
            step = day.setdefault(step_name, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0})
            step["calls"] += 1
            step["input_tokens"] += input_tokens
            step["output_tokens"] += output_tokens
            step["cost"] = round(step["cost"] + cost, 6)
            dates = sorted(by_date.keys())
            for d in dates[:-30]:
                del by_date[d]
            _atomic_write_json(COST_STATS_FILE, stats)
        except Exception as e:
            log(f"WARN | cost stats write failed: {e}")


def log_maintenance_issue(conv_id: str, step: str, error: str, action_hint: str, title_hint: str = "") -> None:
    """Append a failure entry for the user to triage during their next maintenance pass.

    The daemon does NOT auto-retry. Failed conversations keep a ``*_failed``
    status in state plus their raw_hash (so the next tick SKIP_UNCHANGEs
    them). The user periodically reads this file in Claude Code to bulk-triage.
    """
    try:
        DAEMON_ISSUES_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not DAEMON_ISSUES_PATH.exists():
            DAEMON_ISSUES_PATH.write_text(
                "---\n"
                "title: Daemon Issues Log\n"
                "tags: [Dashboard, Daemon, Maintenance]\n"
                "---\n\n"
                "# Daemon Issues Log\n\n"
                "Conversations the daemon failed to process are recorded here. "
                "Open your Claude Code session and ask it to bulk-triage entries "
                "with `status: pending`.\n\n"
                "**Maintenance command** (ask your assistant):\n"
                "> Scan `00.02.07_Daemon_Issues.md` for `status: pending` entries, "
                "classify each as prompt / bug / permanent_reject / retry-worthy, "
                "then report back.\n\n"
                "---\n\n",
                encoding="utf-8",
            )
        entry = (
            f"## [{now_str()}] {step} failed | conv={conv_id[:8]}\n"
            f"- **title_hint**: {title_hint or '(n/a)'}\n"
            f"- **step**: `{step}`\n"
            f"- **error**: `{str(error)[:400]}`\n"
            f"- **suggested_action**: {action_hint}\n"
            f"- **status**: pending\n\n"
        )
        with open(DAEMON_ISSUES_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        log(f"DAEMON_ISSUE_LOGGED | conv={conv_id[:8]} | step={step}")
    except Exception as e:
        log(f"WARN | log_maintenance_issue failed: {e}")


# =========================================================
# Notifications (optional; soft-import daemon.notify if present)
# =========================================================

try:
    from daemon.notify import notify as _notify_user
except Exception:  # pragma: no cover
    def _notify_user(title: str, body: str, group: str = "throughline-flywheel") -> None:
        return None


# =========================================================
# Prompts (English-only; schemas preserved verbatim)
# =========================================================

SLICE_SYSTEM_PROMPT = r"""<task>
You are a conversation slicer. Input is an OpenWebUI conversation (user + assistant turns).
Emit a JSON list of slices where each slice represents ONE coherent knowledge unit.
</task>

<slice_rules>
1. A slice is a (start_idx, end_idx) range covering a complete Q&A or discussion.
2. Follow-ups refining the same topic -> merge into the same slice.
3. Topic shifts -> new slice.
4. Small talk / pleasantries / ephemeral chatter -> emit a slice with keep=false, skip_reason="non_question" or "ephemeral".
5. Prefer over-slicing to under-slicing when boundaries are unclear (merged slices are hard to split later).
</slice_rules>

<keep_rules>
- keep=true when the slice contains concrete, reusable knowledge (a decision, a procedure, a fact, an architecture, a technique).
- keep=false for: non-questions, pure chitchat, API echo, test messages, LLM self-identification questions, content that is purely ephemeral (date-bound weather, today's lunch, etc.).
</keep_rules>

<title_hint>
A short human-friendly hint (<= 40 chars) summarising the slice topic. Used only for logging / dashboard; the refiner generates the final title.
</title_hint>

<output_schema>
Emit a JSON object with a single `slices` field:
{
  "slices": [
    {"start_idx": 1, "end_idx": 4, "title_hint": "Qdrant payload filter design", "keep": true, "skip_reason": ""},
    {"start_idx": 5, "end_idx": 6, "title_hint": "small talk", "keep": false, "skip_reason": "non_question"}
  ]
}
start_idx / end_idx are 1-based message indices. Return {"slices": []} if nothing in the conversation is a real knowledge unit.
</output_schema>

<output_rule>
Emit JSON only. Emit nothing outside the JSON object.
</output_rule>"""


REFINE_SYSTEM_PROMPT_TEMPLATE = r"""<task>
You are the refiner. Input is a conversation slice. Emit a structured knowledge card
as JSON, following the schema and body skeleton below.
</task>

<output_schema>
Emit a single JSON object with these fields:
- title: short, specific, no filler words ("about / practice / answer" are banned).
- primary_x: one of {valid_x}
- visible_x_tags: list of X tags (at least one, using the same vocabulary as primary_x).
- form_y: one of {valid_y}
- z_axis: one of {valid_z}
- knowledge_identity: one of ["universal", "personal_persistent", "personal_ephemeral", "contextual"]
- body_markdown: six-section body (see skeleton below)
- claim_sources: list of provenance tags (see provenance table)
- pack_meta: object (may be empty {{}}), pack-specific metadata such as exam_type
</output_schema>

<knowledge_identity>
- universal: general-purpose knowledge anyone can reuse (default when in doubt).
- personal_persistent: long-lived personal facts / decisions (medication, own hardware topology, chosen stack).
- personal_ephemeral: time-bound personal status (today's plan, short-term experiment).
- contextual: meaningful only within a specific situation (use sparingly; be strict).
Distribution guidance: universal ~60%, personal_persistent ~35%, contextual ~5%, personal_ephemeral rare.
</knowledge_identity>

<claim_provenance>
Tag every non-trivial claim in body_markdown with one of:
- user_stated      : the user asserted it in the slice.
- user_confirmed   : the LLM proposed it and the user confirmed (explicit yes/agreement).
- llm_unverified   : stated by the LLM, not confirmed by the user. Include with a caution marker.
- llm_speculation  : explicitly hypothetical / "could be" / "might" -- keep only if load-bearing.
Add the full list of used tags to `claim_sources`. Drop pure llm_speculation unless the slice is explicitly a brainstorm.
</claim_provenance>

<anti_pollution_rule>
Do NOT invent facts. Do NOT assume the user has something they never mentioned.
If a claim has no basis in the slice, drop it.
</anti_pollution_rule>

<pollution_case>
Example (wrong): slice says "I'm learning Python"; card body says "The user is a senior engineer with 10 years of Python experience." -> fabrication; rewrite.
</pollution_case>

<brainstorm_no_decision>
If the slice is a brainstorm with no decision, set knowledge_identity="personal_ephemeral"
and note in body that this is exploratory, not a commitment.
</brainstorm_no_decision>

<de_individualization>
Replace concrete private identifiers with generic placeholders:
- private IPs  -> use `192.0.2.10` (TEST-NET-1) or similar
- home paths   -> `/path/to/...`
- UNC paths    -> `\\192.0.2.10\share`
- personal emails / SSH aliases -> `user@example.com`, `host`
Keep names of public tools / products.
</de_individualization>

<body_skeleton>
The body_markdown MUST follow this six-section skeleton (use these exact headings):

# Scene & Pain Point
One paragraph: what problem is being solved, for whom, why it matters.

# Core Knowledge & First Principles
The underlying mechanism, why it works, key facts.

# Detailed Execution Plan
Step-by-step instructions, commands, code snippets, config.

# Pitfalls & Boundaries
What breaks it, common mistakes, edge cases, when NOT to apply.

# Insights & Mental Models
Broader lesson, analogy, re-usable pattern.

# Length Summary
A single-sentence recall anchor for the whole card.

# Key Supplementary Details
(Optional) tables, reference links, extra context. Omit the heading if empty.
</body_skeleton>

<length_adaptive>
- Thin slice (one tip / one command)    -> short card, do not pad sections.
- Medium slice (discussion + decision)  -> ~500-1500 chars body.
- Thick slice (architecture / workflow) -> up to ~5000 chars; expand each section.
Do not pad structure with filler; empty sections can stay as a single line.
</length_adaptive>

<critical_output_rule>
Emit JSON only. Inside body_markdown, use straight ASCII quotes, not the curly
typographic variants \u201c ... \u201d. Emit nothing outside the JSON object.
</critical_output_rule>"""


DOMAIN_PROMPT = r"""<task>
You are the top-level domain router. Pick exactly ONE domain for the given card.
</task>

<domains>
- 10_Tech_Infrastructure : networking, servers, Linux admin, virtualization, hardware, self-host.
- 20_Health_Biohack      : medicine, supplements, clinical protocols, sleep, biohacking.
- 30_Biz_Ops             : business ops, accounting, legal, HR, logistics, commerce workflows.
- 40_Cognition_PKM       : learning methods, language study (e.g. PTE), reading notes, knowledge workflows.
- 50_Hobbies_Passions    : hobbies, outdoor, travel, food & drink, workshop.
- 60_Creative_Arts       : music, film, design, writing, art.
- 70_AI                  : LLMs, RAG, agents, embeddings, prompts, AI tooling.
- 80_Gaming              : game mechanics, playthroughs, game-dev tech.
- 90_Life_Base           : daily life, home, personal admin, pets, misc life ops.
</domains>

<priority_boundaries>
- PTE / language study -> always 40_Cognition_PKM
- RAG / LLM plumbing -> 70_AI (even if the user runs it on self-hosted infra)
- Self-host infra supporting AI -> 10_Tech_Infrastructure ONLY when the card is about the infra layer; otherwise 70_AI.
- Supplement / nutrition / medication card -> 20_Health_Biohack.
- Default when truly ambiguous -> 40_Cognition_PKM (generic knowledge-worker stuff).
</priority_boundaries>

<output_schema>
Emit JSON only:
{"domain": "40_Cognition_PKM", "reason": "<<= 60 chars>"}
</output_schema>"""


SUBPATH_PROMPT_TEMPLATE = r"""<task>
Pick exactly one leaf subpath under domain `{domain}` for the card below.
</task>

<allowed_leaves>
{allowed_leaves}
</allowed_leaves>

<priority_boundaries>
- Follow the card's primary_x and body headings to disambiguate.
- If truly nothing fits, return the fallback path provided in `fallback_path` (not an error).
</priority_boundaries>

<output_schema>
Emit JSON only:
{{"subpath": "40_Cognition_PKM/40.03_Learning/40.03.04_PTE", "reason": "<<= 60 chars>", "fallback_path": "{fallback}"}}

If no leaf fits, set `subpath` equal to `fallback_path` and put the reason in `reason`.
</output_schema>"""


EPHEMERAL_JUDGE_SYSTEM_PROMPT = r"""<role>
You are the ephemeral-content gate. Decide whether a short user message is worth
turning into a reusable knowledge card, or is fleeting chatter the system should skip.
</role>

<keep_criteria>
Mark keep=true if ANY holds:
- The user stated a concrete decision, fact, plan, or configuration.
- The user asked a substantive question that has a generalisable answer.
- The user reported a symptom / observation that is part of a longer thread.
- The slice contains a reusable method, template, or command.
</keep_criteria>

<skip_criteria>
Mark keep=false for:
- Greetings, filler, pleasantries, test messages.
- Single-line status with no follow-up ("running now", "ok").
- Pure venting / mood updates with no actionable content.
- Questions about the LLM itself.
- Duplicate echoes of content already returned by RAG.
</skip_criteria>

<fail_safe>
When genuinely unsure, bias toward keep=true. A false keep costs one cheap refine;
a false skip loses knowledge permanently.
</fail_safe>

<output>
Emit exactly one JSON object:
{"verdict": "keep" | "skip", "reason": "<<= 60 chars>"}
</output>"""


EXT_JUDGE_SYSTEM_PROMPT = r"""<role>
You are the conversation extension value judge for a personal knowledge refine pipeline.
</role>

<context>
A user's conversation was already refined into knowledge cards. The user then sent more messages.
Decide whether the new messages are worth triggering an automatic re-refine.
</context>

<noise_criteria>
Classify as noise (do not re-refine):
- network stutter / retry / accidental send / IME garbage
- single-line pleasantries ("thanks", "ok", "got it")
- filler chat with no new knowledge / status / decision
- questions about the LLM itself
- pure test messages
- user echoing back RAG-recalled content
</noise_criteria>

<worth_criteria>
Classify as worth if ANY holds:
- user added new personal fact / status / decision
- user confirmed or rejected the LLM's prior suggestion
- user asked a new related question AND got a substantive answer
- user gave feedback, correction, or a new observation
- new section in a workflow / architecture / troubleshooting chain
</worth_criteria>

<fail_safe>
Bias toward worth when ambiguous. A false worth just costs one silent refine call;
a false noise loses knowledge permanently.
</fail_safe>

<output>
Respond with exactly one JSON object:
{"verdict": "noise" | "worth", "reason": "<brief, under 60 chars>"}
</output>"""


# =========================================================
# LLM HTTP client
# =========================================================

def _repair_unescaped_quotes(s: str) -> str:
    """Best-effort: strip markdown fences that wrap LLM JSON output."""
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1]
        if s.endswith("```"):
            s = s[: -3]
    return s.strip()


def parse_json_loose(raw: str) -> Any:
    """Tolerant JSON parser for LLM output (strips code fences + trailing commas)."""
    if raw is None:
        raise ValueError("empty response")
    s = _repair_unescaped_quotes(str(raw))
    s2 = re.sub(r",(\s*[}\]])", r"\1", s)
    return json.loads(s2)


def call_llm_json(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    step_name: str = "",
    retries: int = 2,
) -> Any:
    """POST to the active LLM provider, return parsed JSON. Records cost on success.

    Provider (URL + api key + extra headers) is resolved once at module
    load via `throughline_cli.active_provider.resolve_endpoint_and_key`.
    Precedence: `THROUGHLINE_LLM_PROVIDER` env > `llm_provider` in
    config.toml > first provider whose env var has a key > `openrouter`.

    Honours legacy `OPENROUTER_URL` / `THROUGHLINE_LLM_URL` env-var
    overrides so existing deployments don't need a migration.
    """
    if not _LLM_KEY:
        raise RuntimeError(
            f"No API key for provider={_LLM_PROVIDER_ID!r}. "
            f"Set the provider's env var (e.g. {_LLM_PROVIDER_ID.upper()}_API_KEY) "
            f"or export OPENROUTER_API_KEY for the legacy path."
        )
    import urllib.request

    # Anthropic: dispatch through the native /v1/messages adapter.
    # Returns the same parsed-JSON shape as the OpenAI-compat path
    # (the adapter rewrites usage field names so _record_cost keeps
    # working without a branch).
    if _LLM_PROVIDER_ID == "anthropic":
        from throughline_cli.anthropic_adapter import (
            call_messages as _anthropic_call,
            AnthropicAdapterError as _AnthErr,
        )
        # Derive base_url from the resolved endpoint (_LLM_URL points
        # at `.../chat/completions` for OpenAI-compat providers; for
        # Anthropic the resolver built `.../chat/completions` too but
        # we want `.../messages` — strip and rebuild).
        base_url = _LLM_URL
        for suffix in ("/chat/completions", "/messages"):
            if base_url.endswith(suffix):
                base_url = base_url[: -len(suffix)]
                break
        last_err_a: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                text, usage = _anthropic_call(
                    model=model,
                    system_prompt=system_prompt,
                    user_message=user_prompt,
                    api_key=_LLM_KEY,
                    base_url=base_url,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=180.0,
                )
                if step_name:
                    _record_cost(
                        step_name, model,
                        int(usage.get("prompt_tokens", 0) or 0),
                        int(usage.get("completion_tokens", 0) or 0),
                    )
                return parse_json_loose(text)
            except _AnthErr as e:
                last_err_a = e
                if attempt < retries:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
        if last_err_a:
            raise last_err_a

    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {_LLM_KEY}",
        "Content-Type": "application/json",
        "X-Title": LLM_TITLE,
    }
    # Merge provider-specific headers (OpenRouter HTTP-Referer etc.)
    # without clobbering X-Title above (daemon wants its own title so
    # cost dashboards can tell wizard preview apart from real refines).
    for k, v in _LLM_EXTRA_HEADERS.items():
        if k.lower() != "x-title":
            headers.setdefault(k, v)
    body = json.dumps(payload).encode("utf-8")

    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(_LLM_URL, data=body, method="POST", headers=headers)
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            obj = json.loads(raw)
            # Defensive: an empty `choices` array used to fall through
            # to `[{}]`-default → empty content → parse_json_loose
            # silently returning {}. That masked rate-limit / safety-
            # filter / quota responses as "successful empty refine"
            # which then wrote a malformed card or got dropped without
            # a log line. Surface explicitly so retry / log fires.
            choices = obj.get("choices") or []
            if not choices:
                raise RuntimeError(
                    f"LLM returned 200 with empty choices array: {raw[:300]}"
                )
            content = choices[0].get("message", {}).get("content", "")
            # Anthropic-shape `stop_reason` (or OpenAI-shape `finish_reason`)
            # of "max_tokens" / "length" means the response was truncated
            # mid-emit. Downstream JSON parsing will likely fail, but the
            # log line tells the user WHY rather than just "JSON parse error".
            finish = (choices[0].get("finish_reason")
                       or choices[0].get("stop_reason"))
            if finish in ("length", "max_tokens"):
                log(f"WARN | {step_name or 'LLM'} response truncated "
                    f"(finish_reason={finish}); raise max_tokens")
            usage = obj.get("usage", {}) or {}
            if step_name:
                _record_cost(step_name, model,
                             int(usage.get("prompt_tokens", 0) or 0),
                             int(usage.get("completion_tokens", 0) or 0))
            return parse_json_loose(content)
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            raise
    if last_err:
        raise last_err
    raise RuntimeError("LLM call failed without exception")


# =========================================================
# State management
# =========================================================

_STATE_LOCK = Lock()


def load_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {"files": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"files": {}}


def save_state(state: Dict[str, Any]) -> None:
    # Atomic write so a concurrent loader never sees a half-written
    # file. Lock guards against in-process write races between
    # daemon threads.
    with _STATE_LOCK:
        _atomic_write_json(STATE_FILE, state)


# =========================================================
# Conversation parsing
# =========================================================

@dataclass
class Message:
    role: str
    content: str


@dataclass
class RawConversation:
    conv_id: str
    raw_path: Path
    messages: List[Message] = field(default_factory=list)
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    source_model: str = ""


_FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_MSG_SPLIT_RE = re.compile(r"^## (user|assistant)\s*$", re.MULTILINE | re.IGNORECASE)


def _parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        fm = {}
    return fm, text[m.end():]


def _parse_messages(body: str) -> List[Message]:
    parts = _MSG_SPLIT_RE.split(body)
    messages: List[Message] = []
    for i in range(1, len(parts), 2):
        role = parts[i].strip().lower()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        messages.append(Message(role=role, content=content))
    return messages


def parse_raw_conversation(raw_path: Path) -> Optional[RawConversation]:
    try:
        text = raw_path.read_text(encoding="utf-8-sig")
    except Exception as e:
        log(f"WARN | parse_raw_conversation read failed: {raw_path}: {e}")
        return None
    fm, body = _parse_frontmatter(text)
    conv_id = str(fm.get("conversation_id") or fm.get("id") or raw_path.stem)
    messages = _parse_messages(body)
    if not messages:
        return None
    return RawConversation(
        conv_id=conv_id,
        raw_path=raw_path,
        messages=messages,
        frontmatter=fm,
        source_model=str(fm.get("source_model") or fm.get("model") or ""),
    )


# =========================================================
# Intent mode detection (@refine / /brainstorm / /decision)
# =========================================================

_INTENT_REFINE_RE = re.compile(r"(?:^|\s|\b)@refine\b", re.IGNORECASE)
_INTENT_BRAINSTORM_RE = re.compile(r"(?:^|\s)/brainstorm\b", re.IGNORECASE)
_INTENT_DECISION_RE = re.compile(r"(?:^|\s)/decision\b", re.IGNORECASE)


def _detect_intent_mode(messages: List[Message]) -> Dict[str, bool]:
    text = "\n".join(m.content for m in messages if m.role == "user")
    return {
        "refine_force": bool(_INTENT_REFINE_RE.search(text)),
        "brainstorm": bool(_INTENT_BRAINSTORM_RE.search(text)),
        "decision": bool(_INTENT_DECISION_RE.search(text)),
    }


# =========================================================
# Ephemeral pattern helpers
# =========================================================

_EPHEMERAL_PATTERNS = [
    re.compile(r"^\s*(hi|hello|hey|thanks|thank you|ok|okay|got it|cool|nice)\s*[.!?]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*[!?.,]+\s*$"),
]

_STRUCTURE_KEYWORDS = [
    "step", "steps", "config", "configuration", "procedure", "decision",
    "architecture", "module", "api", "schema", "pipeline", "install",
]

_DAEMON_CONCEPT_ANCHOR_RE = re.compile(
    r"\b(qdrant|rag|llm|embedding|prompt|agent|pipeline|router|refiner|slicer|obsidian|taxonomy|filter|cache|kernel)\b",
    re.IGNORECASE,
)


def _short_user_text(conv: RawConversation) -> str:
    return "\n".join(m.content for m in conv.messages if m.role == "user").strip()


def _maybe_ephemeral_short(conv: RawConversation) -> bool:
    user_text = _short_user_text(conv)
    if len(user_text) < 10:
        return True
    if any(p.match(user_text) for p in _EPHEMERAL_PATTERNS):
        return True
    return False


# =========================================================
# Echo Guard (cosine + Haiku judge)
# =========================================================

def _embed_text(text: str) -> Optional[List[float]]:
    if not text:
        return None
    import urllib.request
    try:
        body = json.dumps({"input": text[:4000]}).encode("utf-8")
        req = urllib.request.Request(EMBEDDING_URL, data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if isinstance(data, dict):
            if "embedding" in data:
                return data["embedding"]
            if "data" in data and data["data"]:
                return data["data"][0].get("embedding")
        return None
    except Exception as e:
        log(f"WARN | embed failed: {e}")
        return None


def _qdrant_search(vector: List[float], limit: int = 3) -> List[Dict[str, Any]]:
    if not QDRANT_UPSERT_ENABLED:
        return []
    import urllib.request
    try:
        body = json.dumps({"vector": vector, "limit": limit, "with_payload": True}).encode("utf-8")
        req = urllib.request.Request(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/search",
            data=body, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("result", []) or []
    except Exception as e:
        log(f"WARN | qdrant search failed: {e}")
        return []


def _llm_echo_judge(fp_text: str, top1_title: str, top1_body: str) -> Optional[str]:
    """Return 'echo' or 'new' or None on error."""
    user_prompt = (
        "The user's new input is below. Decide whether it is substantively new "
        "knowledge, or merely a paraphrase / echo of the existing top-1 card "
        "retrieved by RAG.\n\n"
        f"[NEW INPUT]\n{fp_text[:1500]}\n\n"
        f"[EXISTING CARD TITLE]\n{top1_title}\n\n"
        f"[EXISTING CARD BODY]\n{top1_body[:1500]}\n\n"
        "Reply with JSON {\"verdict\": \"echo\" | \"new\", \"reason\": \"...\"}."
    )
    try:
        data = call_llm_json(
            model=ECHO_JUDGE_MODEL,
            system_prompt="You are a strict echo/new judge. Respond JSON only.",
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=200,
            step_name="EchoJudge",
        )
        verdict = str((data or {}).get("verdict", "")).strip().lower()
        return verdict if verdict in {"echo", "new"} else None
    except Exception as e:
        log(f"WARN | EchoJudge failed: {e}")
        return None


def _pre_slice_echo_guard(conv: RawConversation) -> Optional[Dict[str, Any]]:
    """Return {"block": True, "reason": "..."} to skip, or None to proceed."""
    if not ECHO_GUARD_ENABLED:
        return None
    user_text = _short_user_text(conv)
    if _INTENT_REFINE_RE.search(user_text):
        return None  # @refine bypasses echo guard
    if len(user_text) < ECHO_FP_MIN_CHARS:
        return None
    vec = _embed_text(user_text[:2500])
    if not vec:
        return None
    results = _qdrant_search(vec, limit=1)
    if not results:
        return None
    top = results[0]
    score = float(top.get("score", 0.0))
    payload = top.get("payload", {}) or {}
    top1_title = str(payload.get("title", ""))
    top1_body = str(payload.get("body_preview", ""))
    top1_date = str(payload.get("date", ""))
    try:
        if top1_date:
            t = datetime.strptime(top1_date[:10], "%Y-%m-%d")
            if (datetime.now() - t).days > ECHO_AGE_BYPASS_DAYS:
                return None
    except Exception:
        pass
    if score < ECHO_PASS_BELOW:
        return None
    if score >= ECHO_BLOCK_ABOVE:
        return {"block": True, "reason": f"echo_hard_block cosine={score:.3f} vs '{top1_title}'"}
    verdict = _llm_echo_judge(user_text, top1_title, top1_body)
    if verdict == "echo":
        return {"block": True, "reason": f"echo_llm_judge cosine={score:.3f} vs '{top1_title}'"}
    return None


# =========================================================
# Method H retention gates
# =========================================================

def _size_aware_min_ratio(slice_chars: int) -> float:
    if slice_chars < 500:
        return 0.25
    if slice_chars < 1500:
        return 0.22
    return RETENTION_MIN_USER_RATIO


def _count_sections_complete(body_md: str) -> int:
    headings = [
        "# Scene & Pain Point", "# Core Knowledge", "# Detailed Execution",
        "# Pitfalls", "# Insights", "# Length Summary",
    ]
    count = 0
    for h in headings:
        if h in body_md and len(body_md.split(h, 1)[-1].strip()) > 40:
            count += 1
    return count


def _retention_gates_pass(slice_chars: int, body_chars: int, body_md: str) -> Tuple[bool, str]:
    ratio = body_chars / max(slice_chars, 1)
    min_ratio = _size_aware_min_ratio(slice_chars)
    if body_chars < RETENTION_MIN_BODY_CHARS:
        return False, f"body_chars={body_chars} < {RETENTION_MIN_BODY_CHARS}"
    complete = _count_sections_complete(body_md)
    if complete < RETENTION_MIN_SECTIONS_COMPLETE:
        return False, f"sections_complete={complete} < {RETENTION_MIN_SECTIONS_COMPLETE}"
    if ratio < min_ratio:
        return False, f"ratio={ratio:.2f} < {min_ratio:.2f}"
    return True, "ok"


# =========================================================
# Slicer dispatch
# =========================================================

@dataclass
class SliceSpec:
    start_idx: int
    end_idx: int
    title_hint: str = ""
    keep: bool = True
    skip_reason: str = ""
    slice_text: str = ""


def _format_conversation(messages: List[Message]) -> str:
    return "\n\n".join(f"[{i}] {m.role.upper()}: {m.content}"
                       for i, m in enumerate(messages, 1))


def _slice_single(conv: RawConversation) -> List[SliceSpec]:
    text = _format_conversation(conv.messages)
    return [SliceSpec(start_idx=1, end_idx=len(conv.messages),
                      title_hint="single", slice_text=text)]


def _slice_with_llm(conv: RawConversation, model: str, slicer_prompt: str) -> List[SliceSpec]:
    text = _format_conversation(conv.messages)
    user_prompt = f"[CONVERSATION]\n{text[:SLICE_ONESHOT_MAX_CHARS]}\n\nEmit JSON now."
    data = call_llm_json(
        model=model,
        system_prompt=slicer_prompt,
        user_prompt=user_prompt,
        temperature=0.1,
        max_tokens=SLICE_MAX_TOKENS,
        step_name="Slicer",
    )
    slices_raw = data.get("slices") if isinstance(data, dict) else None
    if not isinstance(slices_raw, list):
        return []
    specs: List[SliceSpec] = []
    for s in slices_raw:
        if not isinstance(s, dict):
            continue
        start = int(s.get("start_idx", 1))
        end = int(s.get("end_idx", start))
        keep = bool(s.get("keep", True))
        skip_reason = str(s.get("skip_reason", ""))
        title = str(s.get("title_hint", ""))[:80]
        slice_msgs = conv.messages[max(start - 1, 0):min(end, len(conv.messages))]
        slice_text = _format_conversation(slice_msgs)
        specs.append(SliceSpec(start_idx=start, end_idx=end, title_hint=title,
                               keep=keep, skip_reason=skip_reason, slice_text=slice_text))
    return specs


def dispatch_slicer(conv: RawConversation, slicer_prompt: Optional[str] = None) -> List[SliceSpec]:
    n_msgs = len(conv.messages)
    total_chars = sum(len(m.content) for m in conv.messages)
    prompt = slicer_prompt or SLICE_SYSTEM_PROMPT
    if n_msgs <= SLICE_SINGLE_THRESHOLD_MSGS and total_chars <= SLICE_SINGLE_THRESHOLD_CHARS:
        return _slice_single(conv)
    if n_msgs <= SLICE_ONESHOT_MAX_MSGS and total_chars <= SLICE_ONESHOT_MAX_CHARS:
        return _slice_with_llm(conv, SLICE_ONESHOT_MODEL, prompt)
    return _slice_with_llm(conv, SLICE_OPUS_MODEL, prompt)


# =========================================================
# Refiner
# =========================================================

@dataclass
class RefinedResult:
    title: str
    primary_x: str
    visible_x_tags: List[str]
    form_y: str
    z_axis: str
    knowledge_identity: str
    body_markdown: str
    claim_sources: List[str]
    pack_meta: Dict[str, Any] = field(default_factory=dict)
    # U27.2 · Refiner's UNCONSTRAINED preferred X tag. Equal to primary_x
    # for a perfect fit; diverges when the refiner would have preferred a
    # tag outside VALID_X_SET. U27.3 observer logs the pair so U27.4 can
    # propose taxonomy growth. Defaults to primary_x so older prompts /
    # mocks that never emit the field still record a benign no-drift row.
    proposed_x_ideal: str = ""


def _build_refiner_prompt() -> str:
    return REFINE_SYSTEM_PROMPT_TEMPLATE.format(
        valid_x=", ".join(sorted(VALID_X_SET)),
        valid_y=", ".join(sorted(VALID_Y_SET)),
        valid_z=", ".join(sorted(VALID_Z_SET)),
    )


def _apply_user_dials(system_prompt: str) -> str:
    """U23 — append user-tuned dial instructions when set.

    Called after prompt selection so dials apply uniformly to the
    base template AND any pack override. Empty appendage when all
    dials are at defaults so untouched configs pay zero token overhead.
    """
    tail = _render_dials(_load_dials())
    return system_prompt + tail if tail else system_prompt


MAX_SLICE_CHARS_FOR_REFINER = env_int("REFINE_MAX_SLICE_CHARS", 60000)


def _refine_slice(slice_text: str, refiner_prompt: Optional[str] = None,
                   pack_hint: str = "") -> Optional[RefinedResult]:
    system_prompt = _apply_user_dials(refiner_prompt or _build_refiner_prompt())
    user_prompt = f"[SLICE]\n{slice_text[:MAX_SLICE_CHARS_FOR_REFINER]}\n\nEmit the card JSON now."
    data = call_llm_json(
        model=REFINE_MODEL,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=REFINE_MAX_TOKENS,
        step_name="Refiner",
    )
    if not isinstance(data, dict):
        return None
    try:
        primary_x = str(data["primary_x"]).strip()
        proposed_x_ideal = str(data.get("proposed_x_ideal") or primary_x).strip() or primary_x
        return RefinedResult(
            title=str(data["title"]).strip()[:200],
            primary_x=primary_x,
            visible_x_tags=[str(x) for x in data.get("visible_x_tags", []) if x],
            form_y=str(data["form_y"]).strip(),
            z_axis=str(data["z_axis"]).strip(),
            knowledge_identity=str(data.get("knowledge_identity", "universal")).strip(),
            body_markdown=str(data.get("body_markdown", "")).strip(),
            claim_sources=[str(x) for x in data.get("claim_sources", []) if x],
            pack_meta=dict(data.get("pack_meta") or {}),
            proposed_x_ideal=proposed_x_ideal,
        )
    except KeyError as e:
        log(f"WARN | refine missing key: {e}")
        return None


def refine_with_retention_guard(conv: RawConversation, spec: SliceSpec,
                                 refiner_prompt: Optional[str] = None,
                                 pack_hint: str = "") -> Tuple[Optional[RefinedResult], int, int]:
    slice_chars = len(spec.slice_text)
    refined = _refine_slice(spec.slice_text, refiner_prompt=refiner_prompt, pack_hint=pack_hint)
    if refined is None:
        return None, slice_chars, 0
    body_chars = len(refined.body_markdown)
    ok, reason = _retention_gates_pass(slice_chars, body_chars, refined.body_markdown)
    if not ok:
        log(f"RETENTION_FAIL | conv={conv.conv_id[:8]} | {reason}")
        return None, slice_chars, body_chars
    return refined, slice_chars, body_chars


# =========================================================
# Domain + subpath routing (Bug #2 fallback to System_Inbox)
# =========================================================

def route_domain(refined: RefinedResult) -> str:
    user_prompt = (
        f"[CARD]\n"
        f"title: {refined.title}\n"
        f"primary_x: {refined.primary_x}\n"
        f"visible_x_tags: {refined.visible_x_tags}\n"
        f"form_y: {refined.form_y}\n"
        f"body_preview: {refined.body_markdown[:1500]}\n\n"
        f"Emit JSON now."
    )
    try:
        data = call_llm_json(
            model=ROUTE_MODEL,
            system_prompt=DOMAIN_PROMPT,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=ROUTE_MAX_TOKENS,
            step_name="DomainRouter",
        )
        dom = str(data.get("domain", "")).strip()
        if dom in JD_ROOT_MAP:
            return dom
    except Exception as e:
        log(f"WARN | domain router failed: {e}")
    return "40_Cognition_PKM"


def route_subpath(refined: RefinedResult, domain: str, base_path_override: str = "") -> str:
    if base_path_override:
        return normalize_route_path(base_path_override)
    allowed = [p for p in JD_LEAF_WHITELIST if p.startswith(domain + "/") or p == domain]
    if not allowed:
        return JD_FALLBACK_PATH
    prompt = SUBPATH_PROMPT_TEMPLATE.format(
        domain=domain,
        allowed_leaves="\n".join(f"- {p}" for p in allowed),
        fallback=JD_FALLBACK_PATH,
    )
    user_prompt = (
        f"[CARD]\n"
        f"title: {refined.title}\n"
        f"primary_x: {refined.primary_x}\n"
        f"body_preview: {refined.body_markdown[:1500]}\n\n"
        f"Emit JSON now."
    )
    try:
        data = call_llm_json(
            model=ROUTE_MODEL,
            system_prompt=prompt,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=ROUTE_MAX_TOKENS,
            step_name="SubpathRouter",
        )
        sub = str(data.get("subpath", "")).strip()
        sub = normalize_route_path(sub)
        if is_valid_leaf_route(sub):
            return sub
        log(f"ROUTE_FALLBACK | invalid subpath={sub!r} | using {JD_FALLBACK_PATH}")
        return JD_FALLBACK_PATH
    except Exception as e:
        log(f"WARN | subpath router failed: {e} | using {JD_FALLBACK_PATH}")
        return JD_FALLBACK_PATH


# =========================================================
# Dedup check (Qdrant cosine)
# =========================================================

def _check_duplicate_in_qdrant(refined: RefinedResult) -> Optional[Dict[str, Any]]:
    if not QDRANT_UPSERT_ENABLED:
        return None
    vec = _embed_text(f"{refined.title}\n{refined.body_markdown[:2000]}")
    if not vec:
        return None
    results = _qdrant_search(vec, limit=3)
    for r in results:
        score = float(r.get("score", 0.0))
        if score < DEDUP_COSINE_THRESHOLD:
            continue
        payload = r.get("payload", {}) or {}
        dup_date = str(payload.get("date", ""))
        try:
            if dup_date:
                t = datetime.strptime(dup_date[:10], "%Y-%m-%d")
                if (datetime.now() - t).days > DEDUP_DATE_WINDOW_DAYS:
                    continue
        except Exception:
            pass
        return {"score": score, "title": payload.get("title", ""), "path": payload.get("path", "")}
    return None


# =========================================================
# Qdrant upsert
# =========================================================

def _point_id_from_path(path_str: str) -> int:
    norm = path_str.replace(os.sep, "/")
    h = hashlib.md5(norm.encode("utf-8")).hexdigest()[:16]
    return int(h, 16)


def _normalize_for_prefix_check(rel_path: str) -> str:
    """Defense-in-depth path normalization for the forbidden-prefix
    check. Collapses `..` / `./`, swaps `os.sep` to `/`, and lower-
    cases on case-insensitive filesystems (Windows / case-insensitive
    macOS) so a path like `00_Buffer/private/x.md` can't slip past a
    `00_Buffer/Private` prefix.

    Today `rel_path` always comes from validated route strings inside
    the daemon, but `_upsert_note_to_qdrant` is a public-shaped
    function — a future contributor or external script might call it
    with arbitrary input. Normalize once, here, before the comparison."""
    # os.path.normpath collapses `..`, `./`, and runs of separators;
    # then convert any backslashes to forward slashes for stable
    # cross-platform comparison.
    cleaned = os.path.normpath(rel_path).replace(os.sep, "/").lstrip("/")
    # NTFS + APFS-default are case-insensitive; lowercase the test
    # path AND the prefixes (done at load time below) so the check
    # behaves the same on every OS.
    if os.name == "nt" or sys.platform == "darwin":
        cleaned = cleaned.lower()
    return cleaned


def _upsert_note_to_qdrant(rel_path: str, title: str, body_full: str,
                             knowledge_identity: str, tags: List[str],
                             source_conversation_id: str,
                             collection: Optional[str] = None) -> bool:
    if not QDRANT_UPSERT_ENABLED:
        return False
    col = collection or QDRANT_COLLECTION
    norm_path = _normalize_for_prefix_check(rel_path)
    if col == QDRANT_COLLECTION:
        for bad in _QDRANT_DEFAULT_FORBIDDEN_PREFIXES:
            bad_norm = (bad.lower()
                         if (os.name == "nt" or sys.platform == "darwin")
                         else bad)
            if norm_path.startswith(bad_norm):
                log(f"QDRANT_SKIP_FORBIDDEN | path={norm_path} | prefix={bad}")
                return False
    vec = _embed_text(f"{title}\n{body_full[:2000]}")
    if not vec:
        return False
    import urllib.request
    body = json.dumps({
        "points": [{
            "id": _point_id_from_path(norm_path),
            "vector": vec,
            "payload": {
                "title": title,
                "knowledge_identity": knowledge_identity,
                "tags": tags,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "path": norm_path,
                "body_preview": body_full[:500],
                "body_full": body_full[:20000],
                "source_conversation_id": source_conversation_id,
            },
        }]
    }).encode("utf-8")
    try:
        req = urllib.request.Request(
            f"{QDRANT_URL}/collections/{col}/points?wait=true",
            data=body, method="PUT",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 300
    except Exception as e:
        log(f"WARN | qdrant upsert failed: {e}")
        return False


# =========================================================
# Pack policy helpers
# =========================================================

def _apply_ki_policies(refined: RefinedResult, policies: Dict[str, Any],
                       intent_mode: Dict[str, bool]) -> None:
    if intent_mode.get("decision"):
        refined.knowledge_identity = "personal_persistent"
    elif intent_mode.get("brainstorm"):
        refined.knowledge_identity = "personal_ephemeral"
    ki_force = policies.get("ki_force")
    if ki_force in {"universal", "personal_persistent", "personal_ephemeral", "contextual"}:
        refined.knowledge_identity = ki_force


def _get_slicer_prompt(pack: Optional[Any]) -> str:
    if pack is not None and hasattr(pack, "slicer_prompt") and pack.slicer_prompt:
        return pack.slicer_prompt
    return SLICE_SYSTEM_PROMPT


def _get_refiner_prompt(pack: Optional[Any]) -> str:
    if pack is not None and hasattr(pack, "refiner_prompt") and pack.refiner_prompt:
        return pack.refiner_prompt
    return _build_refiner_prompt()


def _get_pack_policies(pack: Optional[Any]) -> Dict[str, Any]:
    if pack is None:
        return {}
    try:
        return dict(getattr(pack, "policies", {}) or {})
    except Exception:
        return {}


def _get_pack_route_base(pack: Optional[Any], refined: RefinedResult) -> str:
    if pack is None:
        return ""
    routing = getattr(pack, "routing", None) or {}
    base = routing.get("base_path", "")
    by_exam = routing.get("by_exam_type", {}) or {}
    exam_type = str((refined.pack_meta or {}).get("exam_type", ""))
    if exam_type and exam_type in by_exam:
        return f"{base.rstrip('/')}/{by_exam[exam_type]}"
    return base or ""


# =========================================================
# Dual-write (formal + buffer stub)
# =========================================================

_FRONTMATTER_TEMPLATE = (
    "---\n"
    "title: {title}\n"
    "date: {date}\n"
    "updated: {updated}\n"
    "source_platform: \"openwebui\"\n"
    "source_conversation_id: \"{conv_id}\"\n"
    "source_raw_path: \"{raw_rel}\"\n"
    "slice_id: \"{slice_id}\"\n"
    "managed_by: \"refine_daemon\"\n"
    "route_to: \"{route_to}\"\n"
    "knowledge_identity: \"{ki}\"\n"
    "tags:\n{tags_yaml}"
    "---\n\n"
)


def _render_tags_yaml(refined: RefinedResult) -> str:
    tags = set(refined.visible_x_tags)
    tags.add(refined.form_y)
    tags.add(refined.z_axis)
    return "".join(f"  - {t}\n" for t in sorted(t for t in tags if t))


def _slugify(title: str) -> str:
    s = re.sub(r"[^\w\- ]+", "", title)
    s = s.strip().replace(" ", "_")
    return s[:80] or "untitled"


def write_dual_note(conv: RawConversation, refined: RefinedResult,
                     route_to: str, intent_mode: Dict[str, bool],
                     pack_collection: str = "") -> Tuple[Optional[Path], Optional[Path]]:
    """Write formal note + buffer stub. Returns (formal_path, buffer_path)."""
    slug = _slugify(refined.title)
    today = datetime.now().strftime("%Y-%m-%d")
    slice_id = hashlib.md5(f"{conv.conv_id}:{refined.title}".encode("utf-8")).hexdigest()[:16]
    fn = f"{today}_{slug}.md"

    formal_dir = VAULT_ROOT / route_to
    formal_dir.mkdir(parents=True, exist_ok=True)
    formal_path = formal_dir / fn

    raw_rel = str(conv.raw_path).replace(str(RAW_ROOT), "").lstrip(os.sep).replace(os.sep, "/")
    fm = _FRONTMATTER_TEMPLATE.format(
        title=refined.title.replace('"', "'"),
        date=now_str(),
        updated=now_str(),
        conv_id=conv.conv_id,
        raw_rel=raw_rel,
        slice_id=slice_id,
        route_to=route_to,
        ki=refined.knowledge_identity,
        tags_yaml=_render_tags_yaml(refined),
    )
    body = fm + refined.body_markdown + "\n"
    try:
        formal_path.write_text(body, encoding="utf-8")
    except Exception as e:
        log(f"ERROR | write_formal_note failed: {e}")
        return None, None

    buffer_path: Optional[Path] = None
    try:
        BUFFER_DIR.mkdir(parents=True, exist_ok=True)
        stub_fn = f"{today}_{slug}__stub.md"
        stub_path = BUFFER_DIR / stub_fn
        stub_fm = fm.replace(
            "---\n\n",
            f"triage_status: \"pending\"\nformal_path: \"{route_to}/{fn}\"\n---\n\n",
        )
        stub_body = (stub_fm +
                     f"> Stub pointing to [[{route_to}/{fn}|{refined.title}]]\n\n" +
                     refined.body_markdown[:800] + "\n")
        stub_path.write_text(stub_body, encoding="utf-8")
        buffer_path = stub_path
    except Exception as e:
        log(f"WARN | buffer stub write failed: {e}")

    rel_path = f"{route_to}/{fn}"
    tags_list = sorted(set(refined.visible_x_tags) | {refined.form_y, refined.z_axis})
    _upsert_note_to_qdrant(
        rel_path=rel_path,
        title=refined.title,
        body_full=refined.body_markdown,
        knowledge_identity=refined.knowledge_identity,
        tags=[t for t in tags_list if t],
        source_conversation_id=conv.conv_id,
        collection=pack_collection or QDRANT_COLLECTION,
    )
    return formal_path, buffer_path


# =========================================================
# Refine Processing Index dashboard
# =========================================================

def update_refine_index(conv_id: str, title: str, route_to: str, status: str,
                         slice_count: int = 0, note: str = "") -> None:
    try:
        REFINE_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not REFINE_INDEX_PATH.exists():
            REFINE_INDEX_PATH.write_text(
                "---\n"
                "title: Refine Processing Index\n"
                "tags: [Dashboard, Daemon, Refine]\n"
                "---\n\n"
                "# Refine Processing Index\n\n"
                "Recent conversations processed by the refine daemon.\n\n"
                "| time | conv_id | title | status | slices | route_to | note |\n"
                "|---|---|---|---|---|---|---|\n",
                encoding="utf-8",
            )
        row = f"| {now_str()} | `{conv_id[:8]}` | {title[:60]} | {status} | {slice_count} | {route_to} | {note[:80]} |\n"
        with open(REFINE_INDEX_PATH, "a", encoding="utf-8") as f:
            f.write(row)
    except Exception as e:
        log(f"WARN | update_refine_index failed: {e}")


# =========================================================
# Extension Value Judge
# =========================================================

def _ext_judge_prefilter(new_msgs_count: int, new_chars: int) -> Tuple[bool, str]:
    if new_msgs_count < EXT_JUDGE_MIN_NEW_MSGS:
        return False, f"new_msgs={new_msgs_count} < {EXT_JUDGE_MIN_NEW_MSGS}"
    if new_chars < EXT_JUDGE_MIN_NEW_CHARS:
        return False, f"new_chars={new_chars} < {EXT_JUDGE_MIN_NEW_CHARS}"
    return True, ""


def _judge_extension_value(existing_titles: List[str], new_msgs_text: str) -> Dict[str, str]:
    user_prompt = (
        "[EXISTING CARD TITLES]\n" + "\n".join(f"- {t}" for t in existing_titles) + "\n\n"
        "[NEW MESSAGES]\n" + new_msgs_text[:8000] + "\n\n"
        "Is the new content worth triggering a re-refine?"
    )
    try:
        data = call_llm_json(
            model=EXT_JUDGE_MODEL,
            system_prompt=EXT_JUDGE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=EXT_JUDGE_MAX_TOKENS,
            step_name="ExtensionValueJudge",
        )
        verdict = str((data or {}).get("verdict", "")).strip().lower()
        if verdict not in {"noise", "worth"}:
            return {"verdict": "worth", "reason": f"invalid verdict={verdict!r}, fallback worth"}
        return {"verdict": verdict, "reason": str(data.get("reason", ""))[:200]}
    except Exception as e:
        log(f"WARN | ExtensionValueJudge failed: {e} — fallback to worth (safe)")
        return {"verdict": "worth", "reason": f"judge_error: {str(e)[:100]}"}


# =========================================================
# Main pipeline: process_raw_file
# =========================================================

_PACK_REGISTRY: Optional[PackRegistry] = None


def _get_pack_registry() -> PackRegistry:
    global _PACK_REGISTRY
    if _PACK_REGISTRY is None:
        _PACK_REGISTRY = PackRegistry(PACKS_DIR)
    return _PACK_REGISTRY


def refine_kept_slices(
    *,
    conv: RawConversation,
    kept: List[SliceSpec],
    pack: Optional[Any] = None,
    pack_name: str = "",
    policies: Optional[Dict[str, Any]] = None,
    intent_mode: Optional[Dict[str, bool]] = None,
) -> int:
    """Extracted inner loop of `process_raw_file` for testability.

    Takes pre-sliced kept specs and runs the per-slice pipeline:
        refine_with_retention_guard
        -> _apply_ki_policies
        -> dedup check against Qdrant (if policies allow)
        -> route (pack_base OR domain + subpath)
        -> write_dual_note
        -> record_taxonomy_observation

    Returns the number of cards successfully written to disk.

    Kept separate from process_raw_file so tests can drive this
    without setting up watchdog + state-file persistence. The outer
    function handles budget / hash / state / parse / source-model
    guard / ephemeral gate / extension judge / slice dispatch;
    everything else — the expensive bit — lives here.
    """
    policies = policies if policies is not None else {}
    intent_mode = intent_mode if intent_mode is not None else {}
    refiner_prompt = _get_refiner_prompt(pack)
    any_written = 0

    for spec in kept:
        try:
            refined, _, _ = refine_with_retention_guard(
                conv, spec, refiner_prompt=refiner_prompt, pack_hint=pack_name)
        except Exception as e:
            log(f"ERROR | refine failed: {e}")
            log_maintenance_issue(conv.conv_id, "refine", str(e),
                                  "check slice + rerun", title_hint=spec.title_hint)
            continue
        if refined is None:
            continue
        _apply_ki_policies(refined, policies, intent_mode)

        if policies.get("dedup_enabled", True):
            dup = _check_duplicate_in_qdrant(refined)
            if dup:
                log(f"DEDUP_SKIP | conv={conv.conv_id[:8]} | "
                    f"dup='{dup.get('title','')}' | "
                    f"score={dup.get('score'):.3f}")
                continue

        pack_base = _get_pack_route_base(pack, refined)
        if pack_base:
            route_to = normalize_route_path(pack_base)
        else:
            domain = route_domain(refined)
            route_to = route_subpath(refined, domain)

        pack_collection = policies.get("qdrant_collection") or ""
        formal_path, _buffer_path = write_dual_note(
            conv, refined, route_to=route_to,
            intent_mode=intent_mode, pack_collection=pack_collection)
        if formal_path:
            any_written += 1
            update_refine_index(conv.conv_id, refined.title, route_to, "ok",
                                slice_count=1, note=pack_name or "-")
            log(f"WRITTEN | conv={conv.conv_id[:8]} | "
                f"title={refined.title[:40]} | route={route_to}")
            # U27.3 · observe the (primary_x, proposed_x_ideal) pair
            # so the CLI can later propose taxonomy growth. Uses the
            # same slice_id recipe as write_dual_note so card_id
            # matches the frontmatter.
            card_id = hashlib.md5(
                f"{conv.conv_id}:{refined.title}".encode("utf-8")
            ).hexdigest()[:16]
            record_taxonomy_observation(
                card_id=card_id,
                title=refined.title,
                primary_x=refined.primary_x,
                proposed_x_ideal=refined.proposed_x_ideal,
            )
    return any_written


def process_raw_file(abs_path: Path) -> None:
    if not abs_path.exists() or not abs_path.is_file():
        return
    if abs_path.suffix.lower() != ".md":
        return
    try:
        if abs_path.stat().st_size == 0:
            return
    except Exception:
        return

    # U3 — daily budget cap. When today's spend is at/above the cap,
    # skip WITHOUT touching state. The raw file stays unprocessed so
    # the next day (new cost_stats date bucket = $0 spent) or the
    # next daemon restart picks it up. Logged once per skip for
    # observability.
    if _budget_exceeded(stats_path=COST_STATS_FILE):
        cap = _load_daily_budget()
        log(f"BUDGET_PAUSE | today over ${cap} cap | skip={abs_path.name}")
        return

    raw_hash = hashlib.md5(abs_path.read_bytes()).hexdigest()
    state = load_state()
    files_state = state.setdefault("files", {})
    key = str(abs_path).replace(os.sep, "/")
    prev = files_state.get(key, {})
    if prev.get("raw_hash") == raw_hash and prev.get("status") in {"ok", "permanent_reject"}:
        return

    conv = parse_raw_conversation(abs_path)
    if conv is None:
        log(f"SKIP | parse_failed | {abs_path}")
        return
    log(f"PROCESS | conv={conv.conv_id[:8]} | msgs={len(conv.messages)} | file={abs_path.name}")

    pack_hint_from_guard = ""
    if _source_model_guard and conv.source_model:
        try:
            verdict = _source_model_guard(conv.source_model)
            if isinstance(verdict, dict):
                if verdict.get("action") == "skip":
                    log(f"SOURCE_MODEL_OPTOUT | conv={conv.conv_id[:8]} | model={conv.source_model} | reason={verdict.get('reason', '')}")
                    files_state[key] = {"raw_hash": raw_hash, "status": "source_model_skipped"}
                    save_state(state)
                    return
                pack_hint_from_guard = str(verdict.get("pack_hint", "") or "")
        except Exception as e:
            log(f"WARN | source_model_guard error: {e}")

    intent_mode = _detect_intent_mode(conv.messages)

    if not intent_mode["refine_force"] and _maybe_ephemeral_short(conv):
        log(f"SKIP | ephemeral_short | conv={conv.conv_id[:8]}")
        files_state[key] = {"raw_hash": raw_hash, "status": "ephemeral_skipped"}
        save_state(state)
        return

    if not intent_mode["refine_force"]:
        echo_verdict = _pre_slice_echo_guard(conv)
        if echo_verdict and echo_verdict.get("block"):
            log(f"ECHO_BLOCK | conv={conv.conv_id[:8]} | {echo_verdict['reason']}")
            files_state[key] = {"raw_hash": raw_hash, "status": "echo_blocked"}
            save_state(state)
            return

    registry = _get_pack_registry()
    try:
        pack = registry.detect(
            conversation_text="\n".join(m.content for m in conv.messages),
            source_model=conv.source_model,
            pack_hint=pack_hint_from_guard,
        )
    except Exception as e:
        log(f"WARN | pack.detect failed: {e}")
        pack = None
    pack_name = getattr(pack, "name", "") if pack is not None else ""
    if pack_name:
        log(f"PACK_MATCHED | conv={conv.conv_id[:8]} | pack={pack_name}")

    slicer_prompt = _get_slicer_prompt(pack)
    try:
        specs = dispatch_slicer(conv, slicer_prompt=slicer_prompt)
    except Exception as e:
        log(f"ERROR | slicer failed: {e}")
        log_maintenance_issue(conv.conv_id, "slice", str(e), "check raw MD + rerun")
        files_state[key] = {"raw_hash": raw_hash, "status": "slice_failed"}
        save_state(state)
        return

    kept = [s for s in specs if s.keep and len(s.slice_text.strip()) > 50]
    log(f"SLICE_RESULT | conv={conv.conv_id[:8]} | total={len(specs)} | kept={len(kept)}")
    if not kept:
        files_state[key] = {"raw_hash": raw_hash, "status": "no_keep_slices"}
        save_state(state)
        update_refine_index(conv.conv_id, "(all slices skipped)", "-", "skipped", slice_count=len(specs))
        return

    policies = _get_pack_policies(pack)
    any_written = refine_kept_slices(
        conv=conv,
        kept=kept,
        pack=pack,
        pack_name=pack_name,
        policies=policies,
        intent_mode=intent_mode,
    )

    if any_written == 0:
        files_state[key] = {"raw_hash": raw_hash, "status": "no_cards_written"}
        save_state(state)
        update_refine_index(conv.conv_id, "(no cards written)", "-", "empty", slice_count=len(kept))
        return

    files_state[key] = {
        "raw_hash": raw_hash, "status": "ok",
        "cards": any_written, "updated": now_str(),
    }
    save_state(state)
    try:
        _notify_user("Refine complete",
                     f"{any_written} card(s) written from conv {conv.conv_id[:8]}")
    except Exception:
        pass


# =========================================================
# Watchdog queue + debounce worker
# =========================================================

_queue: "Queue[Path]" = Queue()
_queued_set: set = set()
_queued_lock = Lock()


class RawWatcher(FileSystemEventHandler):
    def on_created(self, event) -> None:
        self._enqueue(event)

    def on_modified(self, event) -> None:
        self._enqueue(event)

    def _enqueue(self, event):
        if event.is_directory:
            return
        p = Path(event.src_path)
        if p.suffix.lower() != ".md":
            return
        with _queued_lock:
            if p in _queued_set:
                return
            _queued_set.add(p)
        _queue.put(p)


def debounce_worker() -> None:
    while True:
        try:
            p = _queue.get(timeout=1.0)
        except Empty:
            continue
        try:
            time.sleep(DEBOUNCE_SECONDS)
            with _queued_lock:
                _queued_set.discard(p)
            for attempt in range(MAX_RETRY + 1):
                try:
                    process_raw_file(p)
                    break
                except Exception as e:
                    log(f"ERROR | process_raw_file attempt {attempt+1}: {e}")
                    log(traceback.format_exc())
                    time.sleep(5 * (attempt + 1))
        except Exception as e:
            log(f"ERROR | debounce_worker outer: {e}")


def queue_existing_raw() -> None:
    if not RAW_ROOT.exists():
        log(f"WARN | RAW_ROOT does not exist: {RAW_ROOT}")
        return
    count = 0
    for p in RAW_ROOT.rglob("*.md"):
        with _queued_lock:
            if p in _queued_set:
                continue
            _queued_set.add(p)
        _queue.put(p)
        count += 1
    log(f"QUEUE_EXISTING | enqueued {count} raw files from {RAW_ROOT}")


# =========================================================
# Main entry
# =========================================================

def main() -> None:
    ensure_dir(STATE_DIR)
    ensure_dir(LOG_DIR)
    log("=" * 60)
    log("Throughline refine daemon starting")
    log(f"VAULT_ROOT = {VAULT_ROOT}")
    log(f"RAW_ROOT   = {RAW_ROOT}")
    log(f"PACKS_DIR  = {PACKS_DIR}")
    log(f"STATE_DIR  = {STATE_DIR}")
    log(f"QDRANT     = {QDRANT_URL} / {QDRANT_COLLECTION}")
    log(f"LLM PROV   = {_LLM_PROVIDER_ID} -> {_LLM_URL}")
    log(f"LLM KEY    = {'set' if _LLM_KEY else 'MISSING — set provider env var!'}")
    log("=" * 60)

    worker = Thread(target=debounce_worker, daemon=True, name="debounce_worker")
    worker.start()

    queue_existing_raw()

    if RAW_ROOT.exists():
        observer = Observer()
        observer.schedule(RawWatcher(), str(RAW_ROOT), recursive=True)
        observer.start()
        log(f"WATCHING | {RAW_ROOT}")
    else:
        observer = None
        log(f"NOT_WATCHING | RAW_ROOT missing: {RAW_ROOT}")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        log("SIGINT received, shutting down")
    finally:
        if observer:
            observer.stop()
            observer.join(timeout=5)


if __name__ == "__main__":
    main()
