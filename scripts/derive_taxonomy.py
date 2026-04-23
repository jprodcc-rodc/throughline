"""U13 — propose a taxonomy from the user's actual content.

Two input modes, both single-shot LLM calls via throughline_cli/llm.py:

    --from-vault PATH       scan top-level directories + 3-5 sample
                            Markdown card titles from each, let the
                            LLM infer categories.
    --from-imports PATH     scan raw MDs (typically the wizard's
                            import output at $THROUGHLINE_RAW_ROOT)
                            and derive a taxonomy from the titles.

Output:
    config/taxonomy.py  — rendered Python module with VALID_X_SET /
                          VALID_Y_SET / VALID_Z_SET constants plus
                          an auto-generated header timestamp.

The LLM proposal is shown inline first; `--yes` skips the
review prompt.

Usage:
    python scripts/derive_taxonomy.py --from-vault ~/ObsidianVault
    python scripts/derive_taxonomy.py --from-imports ~/throughline_runtime/sources/openwebui_raw --yes
    python scripts/derive_taxonomy.py --from-vault ~/vault --out config/taxonomy.derived.py
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Optional

# Make repo-root-relative imports work when run as a script.
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from throughline_cli import llm
from throughline_cli import prompts as prompt_lib


# ---- sampling ----

_SAMPLES_PER_DIR = 5  # cards per top-level dir to send to LLM


def _read_title(md_path: Path) -> str:
    """Grab the YAML title or first # heading; fall back to stem."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return md_path.stem
    # YAML frontmatter title
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            for line in text[3:end].splitlines():
                line = line.strip()
                if line.startswith("title:"):
                    t = line[len("title:"):].strip().strip('"').strip("'")
                    if t:
                        return t
    # First H1
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()[:120]
    return md_path.stem


def sample_vault(vault_root: Path) -> dict:
    """Return {dir_name: [titles...]} from the vault's top-level dirs."""
    out: dict[str, list[str]] = {}
    for entry in sorted(vault_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        titles: list[str] = []
        for md in sorted(entry.rglob("*.md")):
            if len(titles) >= _SAMPLES_PER_DIR:
                break
            t = _read_title(md)
            if t:
                titles.append(t)
        if titles:
            out[entry.name] = titles
    return out


def sample_imports(raw_root: Path, cap: int = 30) -> list[str]:
    """Return a list of up to `cap` refined-card titles (flat)."""
    titles: list[str] = []
    for md in sorted(raw_root.rglob("*.md")):
        if len(titles) >= cap:
            break
        t = _read_title(md)
        if t:
            titles.append(t)
    return titles


def format_vault_input(sample: dict) -> str:
    """Render the vault sample as the user-message payload."""
    lines = ["My existing vault has these top-level directories with sample card titles:\n"]
    for d, titles in sample.items():
        lines.append(f"### {d}")
        for t in titles:
            lines.append(f"- {t}")
        lines.append("")
    lines.append("Propose a taxonomy per the schema in the system prompt.")
    return "\n".join(lines)


def format_imports_input(titles: list[str]) -> str:
    lines = [
        f"I have {len(titles)} freshly-refined cards from an import "
        "(no pre-existing directory structure). Titles:\n",
    ]
    for t in titles:
        lines.append(f"- {t}")
    lines.append("")
    lines.append("Propose a taxonomy per the schema in the system prompt.")
    return "\n".join(lines)


# ---- rendering ----

def render_taxonomy_module(proposal: dict) -> str:
    """Emit a Python module matching the shape of the example one."""
    now = _dt.datetime.now().isoformat(timespec="seconds")
    x = proposal.get("x_domains") or []
    y = proposal.get("y_forms") or []
    z = proposal.get("z_axes") or []
    rationale = proposal.get("rationale") or ""
    notes = proposal.get("notes") or []

    def _py_list(items):
        inner = ",\n    ".join(f'"{i}"' for i in items)
        return "{\n    " + inner + ",\n}"

    body = f'''"""Auto-derived taxonomy.

Generated: {now}
Source: throughline_cli scripts/derive_taxonomy.py

Rationale (from LLM):
    {rationale}
'''
    if notes:
        body += "\nNotes:\n"
        for n in notes:
            body += f"    - {n}\n"
    body += '"""\nfrom __future__ import annotations\n\n'
    body += f"VALID_X_SET = {_py_list(x)}\n\n"
    body += f"VALID_Y_SET = {_py_list(y)}\n\n"
    body += f"VALID_Z_SET = {_py_list(z)}\n"
    return body


# ---- LLM call ----

def call_deriver(user_msg: str,
                 *,
                 provider_id: str = "anthropic/claude-sonnet-4.6",
                 family: str = "claude") -> dict:
    """Load the taxonomy_deriver prompt for the given family, call LLM,
    return parsed JSON. Raises on any failure (caller decides to
    catch / surface)."""
    system_prompt = prompt_lib.load_prompt(
        "taxonomy_deriver", "main", family,
    )
    content = llm.call_chat(
        model_id=provider_id,
        system_prompt=system_prompt,
        user_message=user_msg,
        response_format={"type": "json_object"},
    )
    return json.loads(content)


# ---- CLI ----

def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Propose a taxonomy.py from the user's existing "
                    "content (vault or imports)."
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-vault", type=Path,
                     help="Path to an Obsidian-style Markdown vault root.")
    src.add_argument("--from-imports", type=Path,
                     help="Path to raw-import MD root (e.g. "
                          "$THROUGHLINE_RAW_ROOT).")
    parser.add_argument("--out", type=Path,
                        default=_REPO_ROOT / "config" / "taxonomy.py",
                        help="Where to write the rendered module. "
                             "Default: config/taxonomy.py")
    parser.add_argument("--provider",
                        default="anthropic/claude-sonnet-4.6",
                        help="LLM model id via OpenRouter. Default "
                             "anthropic/claude-sonnet-4.6.")
    parser.add_argument("--family", default="claude",
                        choices=["claude", "gpt", "gemini", "generic"],
                        help="Prompt family to load.")
    parser.add_argument("--yes", action="store_true",
                        help="Skip the proposal-review prompt; write "
                             "the derived module directly.")
    args = parser.parse_args(argv)

    # 1. Sample.
    if args.from_vault:
        root = args.from_vault.expanduser().resolve()
        if not root.exists():
            print(f"Vault path does not exist: {root}", file=sys.stderr)
            return 2
        sample = sample_vault(root)
        if not sample:
            print(f"No Markdown found in top-level dirs of {root}",
                  file=sys.stderr)
            return 2
        user_msg = format_vault_input(sample)
        source = f"vault {root}"
    else:
        root = args.from_imports.expanduser().resolve()
        if not root.exists():
            print(f"Imports path does not exist: {root}", file=sys.stderr)
            return 2
        titles = sample_imports(root)
        if not titles:
            print(f"No Markdown found under {root}", file=sys.stderr)
            return 2
        user_msg = format_imports_input(titles)
        source = f"imports {root} ({len(titles)} titles)"

    # 2. Call LLM.
    print(f"Source: {source}")
    print(f"Calling {args.provider} (family={args.family})...")
    try:
        proposal = call_deriver(user_msg, provider_id=args.provider,
                                 family=args.family)
    except llm.LLMError as e:
        print(f"LLM call failed: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"LLM returned non-JSON: {e}", file=sys.stderr)
        return 1

    # 3. Show proposal.
    print()
    print("Proposed taxonomy:")
    print(f"  x_domains: {proposal.get('x_domains')}")
    print(f"  y_forms:   {proposal.get('y_forms')}")
    print(f"  z_axes:    {proposal.get('z_axes')}")
    rationale = proposal.get("rationale", "")
    if rationale:
        print(f"  rationale: {rationale}")
    notes = proposal.get("notes", [])
    if notes:
        print("  notes:")
        for n in notes:
            print(f"    - {n}")
    print()

    # 4. Confirm.
    if not args.yes:
        ans = input(f"Write to {args.out}? [Y/n] ").strip().lower()
        if ans == "n" or ans == "no":
            print("Aborted. Nothing written.")
            return 0

    # 5. Render + write.
    module = render_taxonomy_module(proposal)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(module, encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
