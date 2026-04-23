"""Prompt family loader (U22).

Different LLM families respond best to different prompt shapes:

    claude  -> XML tags (<task>, <output_schema>, <critical_output_rule>)
    gpt     -> Markdown headers + explicit JSON schema
    gemini  -> Markdown headers + structured-output hints
    generic -> Markdown headers, plain language (LCD fallback)

Prompt files live in `prompts/en/` with the naming convention:

    {name}.{variant}.{family}.md

E.g. `refiner.normal.claude.md` is the refiner prompt at Normal tier
authored for Claude. `load_prompt("refiner", "normal", "gpt")` tries:

    refiner.normal.gpt.md        (exact match)
    refiner.normal.generic.md    (family fallback)

and raises `FileNotFoundError` if neither is present.

Each file is a full documentation Markdown doc with a fenced code
block holding the actual prompt text. `_extract_prompt_body` returns
just the code-block content so downstream callers get clean prompt
text suitable for sending to an LLM.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPT_DIR = REPO_ROOT / "prompts" / "en"


# Family fallback chain — maps each family to the list of families to
# try in order. Claude-specific XML prompts degrade gracefully to the
# generic Markdown version if the Claude-specific file is missing.
FAMILY_FALLBACK: dict[str, list[str]] = {
    "claude":  ["claude",  "generic"],
    "gpt":     ["gpt",     "generic"],
    "gemini":  ["gemini",  "generic"],
    "generic": ["generic"],
}


def load_prompt(name: str,
                variant: str = "normal",
                family: str = "generic") -> str:
    """Load a prompt by (name, variant, family) with family fallback.

    Returns the prompt body (contents of the first fenced code block
    in the target file). Raises FileNotFoundError if no matching file
    exists after fallback.
    """
    chain = FAMILY_FALLBACK.get(family, [family, "generic"])
    tried = []
    for f in chain:
        path = PROMPT_DIR / f"{name}.{variant}.{f}.md"
        tried.append(path.name)
        if path.exists():
            return _extract_prompt_body(
                path.read_text(encoding="utf-8"),
                source=str(path),
            )
    raise FileNotFoundError(
        f"No prompt for name='{name}' variant='{variant}' family='{family}'. "
        f"Tried fallback chain: {tried}. "
        f"Search directory: {PROMPT_DIR}"
    )


def available_variants(name: str, family: str = "generic") -> list[str]:
    """Return sorted list of variants available for (name, family).

    Used by the wizard to populate tier choices dynamically, so new
    variants become selectable without wizard code changes.
    """
    chain = FAMILY_FALLBACK.get(family, [family, "generic"])
    out: set[str] = set()
    for f in chain:
        for p in PROMPT_DIR.glob(f"{name}.*.{f}.md"):
            # p.stem is e.g. "refiner.normal.claude"
            parts = p.stem.split(".")
            if len(parts) == 3 and parts[0] == name and parts[2] == f:
                out.add(parts[1])
    return sorted(out)


def _extract_prompt_body(text: str, source: str = "?") -> str:
    """Pull the first fenced code block out of a documentation file.

    Files follow the shape:

        # Title
        **Used by:** ...
        ---
        ```
        <prompt body>
        ```
        ---
        **Notes:** ...

    If the file has no code fence, the whole file is returned (some
    future variant may not need the documentation wrapper).
    """
    if "```" not in text:
        return text.strip()
    lines = text.splitlines()
    start = None
    end = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Match an opening or closing fence; allow `language` hint on
        # the opening fence (e.g. ```text or ```xml).
        if stripped == "```" or stripped.startswith("```"):
            if start is None and stripped.startswith("```"):
                start = i + 1
            elif start is not None and stripped == "```":
                end = i
                break
    if start is None or end is None:
        # Malformed — unclosed fence. Return the whole file so caller
        # can still recover; don't silently truncate.
        return text.strip()
    return "\n".join(lines[start:end]).strip()
