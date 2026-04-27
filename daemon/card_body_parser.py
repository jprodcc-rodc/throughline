"""Refined-card body section parser.

Splits a card's body markdown into named sections so downstream
Reflection Pass stages can extract specific content (open
questions from the Pitfalls section, reasoning from the First
Principles section, etc.) without re-deriving the parsing logic.

Handles two header dialects in the wild:

1. **English-only** (per public refiner prompts in
   ``prompts/en/refiner.deep.generic.md``)::

       # Scene & Pain Point
       # Core Knowledge & First Principles
       # Detailed Execution Plan
       # Pitfalls & Boundaries
       # Insights & Mental Models
       # Length Summary

2. **Bilingual emoji + Chinese + English-in-parens** (per author's
   real vault, calibrated 2026-04-28; see
   ``docs/POSITION_METADATA_SCHEMA.md`` § "Vault format addendum")::

       # 🎯 场景与痛点 (Context & Anchor)
       # 🧠 核心知识与底层原理 (First Principles)
       # 🛠️ 详细执行方案 (Execution & Code)
       # 🚧 避坑与边界 (Pitfalls & Gotchas)
       # 💡 心智模型 (Mental Models)
       # 📏 篇幅总结

Section names are canonicalized to snake_case via a known-mapping
table. Headers that don't match a known section drop into a
``_unknown_<slug>`` bucket so callers can still see them but won't
collide with named sections.

Pure stdlib. No LLM, no network, no filesystem.
"""
from __future__ import annotations

import re
from typing import Optional


# Top-level section markers are H1 only ("# foo"). H2 ("## bar") is
# treated as content within the current H1 section. The user's vault
# uses H2 for sub-divisions inside the larger sections.
_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


# Canonical name table. Keys are normalized header strings
# (lowercased, whitespace-collapsed, emoji stripped); values are
# canonical snake_case names.
_HEADER_CANONICAL: dict[str, str] = {
    # English-only headers from public refiner prompts.
    "scene & pain point":                     "scene_and_pain_point",
    "core knowledge & first principles":      "first_principles",
    "detailed execution plan":                "execution_plan",
    "pitfalls & boundaries":                  "pitfalls_and_boundaries",
    "insights & mental models":               "mental_models",
    "length summary":                         "length_summary",
    "self-critique":                          "self_critique",
    "cross-references":                       "cross_references",
    "open questions":                         "open_questions",

    # Bilingual headers (Chinese + English-in-parens). Both halves
    # below the table normalization step end up canonicalized to
    # the same snake_case so callers don't need to know which
    # dialect a vault uses.
    "场景与痛点 (context & anchor)":           "scene_and_pain_point",
    "核心知识与底层原理 (first principles)":   "first_principles",
    "详细执行方案 (execution & code)":         "execution_plan",
    "详细执行方案 (execution)":                "execution_plan",
    "避坑与边界 (pitfalls & gotchas)":         "pitfalls_and_boundaries",
    "避坑与迭代路径 (debugging & iteration)":  "pitfalls_and_boundaries",
    "避坑与迭代路径 (debugging iteration)":    "pitfalls_and_boundaries",
    "心智模型 (mental models)":                "mental_models",
    "心智模型 (insights & mental models)":     "mental_models",
    "启发与思维模型 (insights & mental models)": "mental_models",
    "篇幅总结":                                "length_summary",
    "篇幅总结 (length)":                       "length_summary",
    "自我评议":                                "self_critique",
    "自我评议 (self-critique)":                "self_critique",
    "交叉引用":                                "cross_references",
    "交叉引用 (cross-references)":             "cross_references",
    "开放问题":                                "open_questions",
    "开放问题 (open questions)":               "open_questions",

    # Chinese-only headers (no English in parens). The user's vault
    # has many cards with this dialect — they pre-date the public
    # bilingual prompt schema. See POSITION_METADATA_SCHEMA.md
    # § "Vault format addendum" — calibrated 2026-04-28 against
    # 163-card frontmatter sample.
    "场景与痛点":                              "scene_and_pain_point",
    "核心知识与底层原理":                      "first_principles",
    "详细执行方案":                            "execution_plan",
    "避坑与边界":                              "pitfalls_and_boundaries",
    "避坑与迭代路径":                          "pitfalls_and_boundaries",
    "心智模型":                                "mental_models",
    "启发与思维模型":                          "mental_models",
}


def _normalize_header(raw: str) -> str:
    """Strip leading emoji / variation-selectors / decorations /
    whitespace; lowercase. Used as lookup key into
    ``_HEADER_CANONICAL``.

    The character-class approach is fragile because emoji can
    be followed by U+FE0F variation selectors and other invisible
    modifiers that aren't in obvious Unicode ranges. Using
    ``isalpha()`` to find the first real word character is more
    robust: CJK ideographs return True for isalpha, so leading
    emojis + variation selectors + spaces are dropped while the
    Chinese / English content stays intact.

    Special-cased: also stop at '(' so headers that are entirely
    emoji + parenthesized English (rare) still produce a useful
    key.
    """
    s = raw
    for i, ch in enumerate(s):
        if ch.isalpha() or ch.isdigit() or ch == "(":
            s = s[i:]
            break
    else:
        s = ""
    # Collapse internal whitespace and trim trailing
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()


def _slug_for_unknown(raw: str) -> str:
    """Build a stable identifier for an unrecognized header. Used
    as the bucket name (``_unknown_<slug>``) so callers can still
    see the content even if we don't know its semantic role."""
    s = _normalize_header(raw)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "untitled"


# The recall-callout block the running daemon appends to body. We
# strip it from whichever section it lands in so Reflection Pass
# stages don't accidentally treat the recall results as user
# content. See POSITION_METADATA_SCHEMA.md § "Vault format
# addendum" point 3.
_RECALL_CALLOUT_RE = re.compile(
    r"\n\s*>\s*\[!info\]\s*🧠\s*神经突触连结.*",
    re.DOTALL,
)


# Some cards end with a markdown horizontal rule "---" separating
# the main body from the sidebar (Self-Critique / Cross-References /
# Open Questions per public refiner prompt). The sidebar headers
# also live below the rule in some vaults. Don't strip the rule
# itself; just don't treat it as a section boundary.


def parse_body_sections(body: str) -> dict[str, str]:
    """Split ``body`` markdown into named sections.

    Args:
        body: The card body (frontmatter already stripped). May be
            empty.

    Returns:
        Dict mapping canonical section name -> section content
        (markdown body of the section, excluding the header line).

        Sections appear in the order they are encountered. Content
        before the first header (rare; usually a leading TLDR
        paragraph) is keyed under ``_preamble``.

        Headers we don't recognize get a ``_unknown_<slug>`` key
        with the slug derived from the header text.

    Side effects: none. Pure function over the input string.
    """
    if not body:
        return {}

    # Strip the recall callout if present so it doesn't end up
    # masquerading as user content in the last section.
    body = _RECALL_CALLOUT_RE.sub("", body)

    # Find all H1 markers and their positions.
    matches = list(_H1_RE.finditer(body))

    sections: dict[str, str] = {}

    if not matches:
        # No H1 headers at all — treat entire body as preamble.
        # (Rare; happens for very-short cards or non-refined notes.)
        text = body.strip()
        if text:
            sections["_preamble"] = text
        return sections

    # Capture content before the first header as preamble (if
    # non-empty after strip).
    first_start = matches[0].start()
    preamble = body[:first_start].strip()
    if preamble:
        sections["_preamble"] = preamble

    # Walk header pairs. Each section's content is the text from
    # the end of the current header to the start of the next.
    for i, m in enumerate(matches):
        header_raw = m.group(1).strip()
        section_start = m.end()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(body)

        normalized = _normalize_header(header_raw)
        canonical = _HEADER_CANONICAL.get(normalized)
        if canonical is None:
            canonical = f"_unknown_{_slug_for_unknown(header_raw)}"

        content = body[section_start:section_end].strip()

        # If a card has duplicate headers (rare; happens in
        # hand-written notes), the *last* one wins. Concatenating
        # would silently merge unrelated content.
        sections[canonical] = content

    return sections


def get_section(body: str, section: str) -> Optional[str]:
    """Convenience: parse body and return the named section's
    content, or None if absent.

    Args:
        body: Card body markdown.
        section: Canonical section name (e.g. ``"first_principles"``,
            ``"open_questions"``).

    Returns:
        Section content string, or None when the section is
        missing.
    """
    return parse_body_sections(body).get(section)
