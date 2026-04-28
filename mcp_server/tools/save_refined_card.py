"""save_refined_card — host-LLM-refined save path (zero LLM cost).

The third save path, complementary to save_conversation:

- ``save_conversation`` queues raw conversation; daemon LLM refines
  it into a 6-section card. Daemon's REFINE_MODEL is paid (typical
  ~$0.04 / save on OpenRouter Sonnet 4.6).
- ``save_refined_card`` (this tool) is called by the host LLM AFTER
  it has synthesized the structured card itself. The tool just files
  the .md to vault. **The host LLM is subscription-billed, so this
  path is FREE for the user.**

When to use which:
- Host is Claude Desktop / Code / Cursor with a paid subscription:
  use ``save_refined_card``. The host LLM does the refining work
  on subscription budget.
- Host has no subscription but daemon has API budget: use
  ``save_conversation`` and let daemon refine via API.
- Host is a thin/free LLM that can't refine well: use
  ``save_conversation`` and rely on daemon's quality.

The two tools share frontmatter shape, so cards from either path
look identical in the vault.
"""
from __future__ import annotations

import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from mcp_server.config import get_vault_root


# Filename sanitisation: keep alnum / hyphen / underscore / dot /
# CJK; collapse runs of other chars to a single underscore.
_FILENAME_BAD_RE = re.compile(r"[^A-Za-z0-9._一-鿿-]+")

_VALID_KNOWLEDGE_IDENTITY = {
    "universal",
    "personal_persistent",
    "personal_ephemeral",
    "contextual",
}


def _sanitize_filename(title: str, max_len: int = 100) -> str:
    """Coerce a card title into a vault-safe filename stem."""
    raw = title.strip()
    if not raw:
        return "untitled"
    s = _FILENAME_BAD_RE.sub("_", raw)
    s = re.sub(r"_+", "_", s).strip("_.")
    s = s[:max_len].strip("_.")
    return s or "untitled"


def _build_frontmatter(
    *,
    title: str,
    domain: str,
    knowledge_identity: str,
    extra_tags: Optional[list[str]],
    source_platform: str,
) -> str:
    """Render YAML frontmatter for a refined card."""
    now = datetime.now(timezone.utc)
    iso = now.strftime("%Y-%m-%d %H:%M")
    tag_lines = [f"  - {domain}"]
    for t in (extra_tags or []):
        if t and isinstance(t, str):
            tag_lines.append(f"  - {t}")

    fm = (
        "---\n"
        f'title: "{title}"\n'
        f"date: {iso}\n"
        f"updated: {iso}\n"
        f"source_platform: {source_platform}\n"
        "tags:\n"
        + "\n".join(tag_lines)
        + "\n"
        f'knowledge_identity: "{knowledge_identity}"\n'
        'managed_by: "host_llm_refined"\n'
        "---\n\n"
    )
    return fm


def _resolve_card_path(
    vault_root: Path,
    domain: str,
    title: str,
) -> Path:
    """Compute the destination .md path under vault_root.

    Domain "Health/Biohack" routes to vault_root/Health/Biohack/<title>.md.
    If the file already exists, append a -2 / -3 / ... suffix until
    a free name is found (never overwrites).
    """
    domain_path = vault_root / domain
    domain_path.mkdir(parents=True, exist_ok=True)
    stem = _sanitize_filename(title)
    candidate = domain_path / f"{stem}.md"
    if not candidate.exists():
        return candidate
    n = 2
    while True:
        candidate = domain_path / f"{stem}-{n}.md"
        if not candidate.exists():
            return candidate
        n += 1


def _atomic_write(path: Path, content: str) -> None:
    """Write atomically via NamedTemporaryFile + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_str = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=path.name,
        suffix=".tmp",
    )
    tmp = Path(tmp_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(str(tmp), str(path))
    except Exception:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def save_refined_card(
    title: str,
    body: str,
    domain: str,
    knowledge_identity: str = "universal",
    extra_tags: Optional[list[str]] = None,
    source_platform: str = "claude_desktop",
) -> dict:
    """Save a host-LLM-refined card directly to the vault — zero
    daemon LLM cost. The host LLM (you) does the refining work on
    its own subscription budget; this tool just files the result.

    **This is the DEFAULT save path** when the host LLM (you) is on
    a Claude Desktop / Code / Cursor / Continue.dev subscription.
    save_conversation is the legacy raw-queue path that costs ~$0.04
    per save (daemon's paid OpenRouter refine call). This tool is
    free — you do the refining on subscription budget that the user
    already pays.

    Both tools write the same frontmatter shape to the same vault;
    cards from either path look identical to recall_memory + the
    Reflection Layer. The only difference is who paid for the LLM
    work that synthesized the body.

    Decision flow when user says 'save' / 'remember' / 记住 / 保存:
    1. CAN you synthesize the conversation into a coherent
       structured card right now? → call save_refined_card (free)
    2. Are you a thin LLM that can't synthesize well? → call
       save_conversation (paid, daemon refines)
    3. Did the user explicitly ask for raw save? → call
       save_conversation

    For Claude Sonnet 4.x / Opus 4.x hosts the answer to (1) is
    almost always YES — prefer this tool.

    Call this when:
    - User says 'save this' / 'remember this' / 记住这个 / 保存这个
      / '存下来' / 'capture this' (any save intent).
    - User said 'refined' / 'refined conversation' / '精炼' /
      'structured' anywhere in the request.
    - You can synthesize the conversation into a 6-section card.
    - You want the card retrievable from the vault immediately
      (this tool writes directly; no daemon queue).

    Do NOT call:
    - When you genuinely cannot synthesize a coherent structured
      card (extremely long fragmented input, content outside your
      domain). Fall back to save_conversation.
    - When you cannot determine a good X-axis domain (call
      list_topics first to learn the user's taxonomy).
    - For trivia / small talk / acknowledgements (don't save those
      via either tool).

    Recommended body shape — 6 sections, free-form headers. Vault
    convention example::

        # Scene & Pain Point
        ...

        # Core Knowledge & First Principles
        ...

        # Detailed Execution Plan
        ...

        # Pitfalls & Boundaries
        ...

        # Insights & Mental Models
        ...

        # Summary
        ...

    English / Chinese / mixed all fine — the vault stores them verbatim.

    Args:
        title: Human-readable card title (becomes the filename).
        body: Refined card body in markdown.
        domain: X-axis taxonomy domain — one of the values from
            ``list_topics``. Examples: 'Health/Biohack', 'AI/LLM',
            'Tech/Network'.
        knowledge_identity: One of 'universal' (generic),
            'personal_persistent' (durable personal — meds, current
            projects), 'personal_ephemeral' (time-bounded), or
            'contextual' (strong context binding). Default 'universal'.
        extra_tags: Optional y/ (form) and z/ (relation) axis tags.
            Examples: ['y/SOP', 'z/Pipeline'].
        source_platform: Frontmatter provenance label. Defaults to
            'claude_desktop'; override when known.

    Returns:
        On success::

            {
                "card_path": "/Users/.../Health/Biohack/title.md",
                "knowledge_identity": "universal",
                "domain": "Health/Biohack",
                "host_refined": True,
                "_status": "ok",
            }

        On invalid input or filesystem error::

            {
                "card_path": None,
                "_status": "error",
                "_message": "<reason>",
            }
    """
    if not title or not title.strip():
        return {
            "card_path": None,
            "_status": "error",
            "_message": "title must be non-empty",
        }
    if not body or not body.strip():
        return {
            "card_path": None,
            "_status": "error",
            "_message": "body must be non-empty",
        }
    if not domain or not domain.strip():
        return {
            "card_path": None,
            "_status": "error",
            "_message": (
                "domain must be non-empty (call list_topics for the "
                "active X-axis taxonomy)"
            ),
        }
    if knowledge_identity not in _VALID_KNOWLEDGE_IDENTITY:
        return {
            "card_path": None,
            "_status": "error",
            "_message": (
                f"knowledge_identity must be one of "
                f"{sorted(_VALID_KNOWLEDGE_IDENTITY)!r}; "
                f"got {knowledge_identity!r}"
            ),
        }

    vault_root = get_vault_root()
    if not vault_root or not vault_root.exists():
        return {
            "card_path": None,
            "_status": "error",
            "_message": (
                f"Vault root not found at {vault_root}. Set "
                "THROUGHLINE_VAULT_ROOT or run `python install.py "
                "--express`."
            ),
        }

    fm = _build_frontmatter(
        title=title.strip(),
        domain=domain.strip(),
        knowledge_identity=knowledge_identity,
        extra_tags=extra_tags,
        source_platform=source_platform,
    )
    full_content = fm + body.strip() + "\n"

    try:
        target = _resolve_card_path(
            vault_root=vault_root,
            domain=domain.strip(),
            title=title.strip(),
        )
        _atomic_write(target, full_content)
    except OSError as exc:
        return {
            "card_path": None,
            "_status": "error",
            "_message": f"filesystem error: {exc}",
        }

    return {
        "card_path": str(target),
        "knowledge_identity": knowledge_identity,
        "domain": domain.strip(),
        "host_refined": True,
        "_status": "ok",
    }
