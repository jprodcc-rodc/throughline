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

    **This is the DEFAULT save path** for the host LLM (you) on a
    Claude Desktop / Code / Cursor / Continue.dev subscription. You
    synthesize the 6-section card from the conversation; this tool
    files it. No daemon LLM cost (daemon path was ~$0.04/save). Both
    paths write the same frontmatter shape; cards from either look
    identical to recall_memory + the Reflection Layer.

    For Claude Sonnet 4.x / Opus 4.x hosts the answer to "can I
    synthesize a coherent structured card?" is almost always YES —
    prefer this tool over the legacy daemon-queue path.

    CALL THIS PROACTIVELY WHEN:
    - User signals save intent: 'save this' / 'remember this' /
      'capture this' / 'store this' / '记住这个' / '保存这个' /
      '存下来' / '记下来'.
    - User explicitly says 'refined' / 'structured' / '精炼' /
      'as a card' anywhere in the request.
    - Conversation has hit a natural decision / synthesis point and
      you can summarize it into a 6-section card right now.
    - User asks to 'document this' / 'add to my knowledge base' /
      'add to throughline' / 'put this in the vault'.

    DO NOT CALL WHEN:
    - You genuinely cannot synthesize a coherent structured card
      (extremely long fragmented input, content outside your
      reasoning ability). Tell the user instead — don't save junk.
    - You cannot determine a good X-axis domain — call list_topics
      first to learn the user's taxonomy, then save with the right
      domain.
    - Trivia / small talk / acknowledgements ('thanks', 'ok',
      'got it') — don't pollute the vault.
    - The user is mid-thought and hasn't reached a save-worthy
      synthesis yet — wait for closure.
    - User explicitly says 'don't save' / '别存' / 'just chatting'.

    EXAMPLE TRIGGERS:
    User: "Save this whole conversation about my Postgres → SQLite
           decision."
      → save_refined_card(title="Postgres → SQLite decision",
          body=<6-section synthesis>, domain="Tech/Database")
    User: "记住这个药物清单。"
      → save_refined_card(title="Master 用药清单",
          body=<synthesized list>, domain="Health/Medicine",
          knowledge_identity="personal_persistent")
    User: "把今天讨论的产品定位策略存进 throughline。"
      → save_refined_card(title="产品定位策略 v2",
          body=<6-section card>, domain="Business/Strategy")
    User: "Capture this as a structured card."
      → save_refined_card(title=<derive from topic>,
          body=<refined>, domain=<from list_topics>)

    EXAMPLE NON-TRIGGERS:
    User: "What's a good database for OLTP?"
      (factual question; nothing to save yet)
    User: "Thanks, that helps."
      (acknowledgement; no save-worthy content)
    User: "Don't save this, I'm just venting."
      (explicit opt-out)
    User: "Show me what I've saved before."
      (this is recall_memory, not save)

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
