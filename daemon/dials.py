"""U23 · Preview 5-dial constrained edit — shared render path.

The wizard's step 13 lets the user adjust 5 dials:
    tone            formal | neutral | casual
    length          short | medium | long
    sections        which six-section headings to include
    register        technical | plain | eli5
    keep_verbatim   True → preserve direct-quote slices verbatim

Choices persist to `~/.throughline/config.toml` so the daemon picks
them up on its next refine. Both the wizard (for the live-preview
re-render) and the daemon (for every real refine) call
`render_dial_modifier()` to get a text block that gets appended to
the base refiner system prompt.

No free-form prompt editing: dials are constrained to a fixed
vocabulary so the daemon's downstream JSON schema (primary_x, form_y,
z_axis, six-section body) never fractures.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# =========================================================
# Canonical dial vocabulary
# =========================================================

VALID_TONES = ("formal", "neutral", "casual")
VALID_LENGTHS = ("short", "medium", "long")
VALID_REGISTERS = ("technical", "plain", "eli5")

ALL_SECTIONS = (
    "scenario",        # Scene & Pain Point
    "core_knowledge",  # Core Knowledge & First Principles
    "execution",       # Detailed Execution Plan
    "avoid",           # Pitfalls & Boundaries
    "insight",         # Insights & Mental Models
    "summary",         # Length Summary
)

# Human-facing section labels used in the dial modifier text.
SECTION_LABELS = {
    "scenario":       "Scene & Pain Point",
    "core_knowledge": "Core Knowledge & First Principles",
    "execution":      "Detailed Execution Plan",
    "avoid":          "Pitfalls & Boundaries",
    "insight":        "Insights & Mental Models",
    "summary":        "Length Summary",
}


@dataclass
class Dials:
    tone: str = "neutral"
    length: str = "medium"
    sections: List[str] = field(default_factory=lambda: list(ALL_SECTIONS))
    register: str = "technical"
    keep_verbatim: bool = False

    def is_default(self) -> bool:
        return (
            self.tone == "neutral"
            and self.length == "medium"
            and self.register == "technical"
            and self.keep_verbatim is False
            and sorted(self.sections) == sorted(ALL_SECTIONS)
        )


# =========================================================
# Loading from wizard config
# =========================================================

def _config_path() -> Path:
    override = os.environ.get("THROUGHLINE_CONFIG_DIR")
    base = Path(override).expanduser() if override else (Path.home() / ".throughline")
    return base / "config.toml"


def load_dials_from_config(path: Optional[Path] = None) -> Dials:
    """Read the dial_* fields out of the wizard-written config.toml.

    Any malformed value falls back to the Dials() default for its
    field — the daemon must never fail to refine because a dial value
    got typo'd.
    """
    p = path if path is not None else _config_path()
    if not p.exists():
        return Dials()
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:  # pragma: no cover
            import tomli as tomllib  # type: ignore
        with p.open("rb") as fh:
            data = tomllib.load(fh)
    except (OSError, Exception):
        return Dials()

    d = Dials()
    tone = str(data.get("dial_tone") or d.tone).strip().lower()
    if tone in VALID_TONES:
        d.tone = tone
    length = str(data.get("dial_length") or d.length).strip().lower()
    if length in VALID_LENGTHS:
        d.length = length
    register = str(data.get("dial_register") or d.register).strip().lower()
    if register in VALID_REGISTERS:
        d.register = register
    raw_sections = data.get("dial_sections")
    if isinstance(raw_sections, list):
        cleaned = [str(s).strip() for s in raw_sections if str(s).strip() in ALL_SECTIONS]
        if cleaned:
            d.sections = cleaned
    kv = data.get("dial_keep_verbatim")
    if isinstance(kv, bool):
        d.keep_verbatim = kv
    return d


# =========================================================
# Render as refiner prompt tail
# =========================================================

_TONE_DESCR = {
    "formal":  "formal, professional prose; no contractions; no colloquialisms",
    "neutral": "neutral prose; match the source register",
    "casual": "casual conversational prose; contractions OK; no slang",
}

_LENGTH_DESCR = {
    "short":  "short: body < 500 chars; prefer bullets over paragraphs",
    "medium": "medium: body 500-1500 chars",
    "long":   "long: body 1500-5000 chars; expand each section with examples",
}

_REGISTER_DESCR = {
    "technical": "technical register — assume a reader who knows the domain",
    "plain":     "plain-language register — avoid unexplained jargon",
    "eli5":      "explain-like-I'm-five — use analogies and everyday words",
}


def render_dial_modifier(dials: Optional[Dials] = None) -> str:
    """Return the text block to append to the refiner system prompt.

    Empty string when all dials are at defaults — we don't want to
    inject pointless tokens into every request for untouched configs.
    """
    d = dials if dials is not None else Dials()
    if d.is_default():
        return ""
    lines = ["", "<user_dials>"]
    lines.append("The user has tuned the following output dials; "
                 "honour them on top of the base schema:")
    if d.tone in _TONE_DESCR:
        lines.append(f"- Tone: {_TONE_DESCR[d.tone]}")
    if d.length in _LENGTH_DESCR:
        lines.append(f"- Length: {_LENGTH_DESCR[d.length]}")
    if d.register in _REGISTER_DESCR:
        lines.append(f"- Register: {_REGISTER_DESCR[d.register]}")
    if sorted(d.sections) != sorted(ALL_SECTIONS):
        kept = [SECTION_LABELS[s] for s in d.sections if s in SECTION_LABELS]
        dropped = [SECTION_LABELS[s] for s in ALL_SECTIONS
                    if s not in d.sections and s in SECTION_LABELS]
        if kept:
            lines.append(f"- Include ONLY these body sections: {', '.join(kept)}.")
        if dropped:
            lines.append(f"- OMIT these sections entirely: {', '.join(dropped)}.")
    if d.keep_verbatim:
        lines.append(
            "- Keep-verbatim: when the user's messages contain a direct "
            "command, code block, or key phrase, reproduce it literally in "
            "the body rather than paraphrasing it."
        )
    lines.append("</user_dials>")
    return "\n".join(lines)
