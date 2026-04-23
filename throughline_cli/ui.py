"""Shared TUI helpers for the install wizard.

Centralises every colour / panel / rule / prompt decision so the
wizard code itself stays declarative ('print this example card',
'ask this question') and the visual style can be tuned in one place.

Colour palette (semantic, not decorative):
    cyan        — step headers, option numbers
    blue        — example card panels
    green       — confirmed defaults, success
    yellow      — cold-start / spend warnings
    red         — errors, blocking prompts
    dim         — descriptions, fallback guidance

The wizard must remain usable without colour. rich auto-detects
non-TTY output (pipes, CI logs, `> out.txt`) and strips ANSI escapes;
users who want to force plain output set NO_COLOR=1.
"""
from __future__ import annotations

import sys
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text


# Single shared Console. force_terminal=False so piped output looks
# right in test captures; highlight=False so arbitrary '1.0' strings
# aren't auto-coloured as numbers inside our messages.
console = Console(highlight=False)


# ---------- headers / structure ----------

def step_header(step: int, total: int, title: str) -> None:
    """Big rule at the top of each wizard step."""
    console.print()
    console.rule(
        f"[bold cyan]\\[{step}/{total}][/] [bold white]{title}[/]",
        style="cyan",
        align="left",
    )


def section_title(title: str) -> None:
    """Non-wizard section header (used by adapters, purge, etc)."""
    console.print()
    console.rule(f"[bold cyan]{title}[/]", style="cyan", align="left")


def ensure_utf8_stdio() -> None:
    """Reconfigure stdout/stderr to UTF-8 on Windows. Idempotent."""
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if callable(reconf):
            try:
                reconf(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def intro(text: str) -> None:
    """One-paragraph description after a step header."""
    console.print(f"  [dim]{text}[/]")


def subrule(label: str) -> None:
    """Thin divider between sibling options inside one step."""
    console.print()
    console.rule(f"[bold]{label}[/]", style="blue", align="left")


def panel_example(title: str, body_markdown: str,
                  pick_if: Optional[str] = None) -> None:
    """Render a boxed example. Body is rendered as Markdown so code
    blocks, headings, and lists display cleanly."""
    md = Markdown(body_markdown.strip(), code_theme="monokai",
                  inline_code_theme="monokai")
    console.print(Panel(
        md,
        title=f"[bold blue]{title}[/]",
        title_align="left",
        border_style="blue",
        padding=(0, 1),
    ))
    if pick_if:
        console.print(f"  [italic dim]Pick if:[/] [dim]{pick_if}[/]")


def warn_box(title: str, body: str) -> None:
    console.print(Panel(
        Text(body, style="yellow"),
        title=f"[bold yellow]\u26a0  {title}[/]",
        title_align="left",
        border_style="yellow",
        padding=(0, 1),
    ))


def info_line(text: str) -> None:
    console.print(f"  [dim]{text}[/]")


def note(text: str) -> None:
    """Minor line — neutral tone, no emphasis."""
    console.print(f"  {text}")


def kv_row(key: str, value: str) -> None:
    """Summary-screen key/value line."""
    console.print(f"  [cyan]{key:<18}[/] [bold]{value}[/]")


# ---------- prompts (keep input() underneath for testability) ----------

def pick_option(question: str,
                options: list[tuple[str, str, str]],
                default_key: str) -> str:
    """Numbered choice prompt.

    options = [(key, label, description), ...]
    Returns the chosen key. Stdin is read via builtins.input so tests
    can monkeypatch it straight.
    """
    console.print(f"\n[bold]{question}[/]")
    default_idx = 1
    for i, (key, label, desc) in enumerate(options, 1):
        marker = "  [green](default)[/]" if key == default_key else ""
        console.print(f"  [cyan]\\[{i}][/] {label}{marker}")
        if desc:
            console.print(f"       [dim]{desc}[/]")
        if key == default_key:
            default_idx = i
    raw = ask_text("Choose", str(default_idx))
    try:
        idx = int(raw)
    except ValueError:
        console.print("  [yellow]Not a number, using default.[/]")
        idx = default_idx
    if not 1 <= idx <= len(options):
        console.print("  [yellow]Out of range, using default.[/]")
        idx = default_idx
    return options[idx - 1][0]


def ask_text(question: str, default: str = "") -> str:
    """Plain text input with default. Blue question, dim bracketed default."""
    suffix = f" [dim]\\[{default}][/]" if default else ""
    try:
        # Render the prompt via rich, but use builtins.input for stdin
        # so existing tests that monkeypatch input still work.
        console.print(f"[cyan]?[/] [bold]{question}[/]{suffix}", end=" ")
        raw = input("> ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[red]Aborted.[/]")
        sys.exit(130)
    return raw if raw else default


def ask_yes_no(question: str, default: bool = True) -> bool:
    default_s = "Y/n" if default else "y/N"
    raw = ask_text(question, default_s).lower()
    if raw in ("y", "yes"):
        return True
    if raw in ("n", "no"):
        return False
    return default


# ---------- convenience wrappers for the common output shapes ----------

def print_blank() -> None:
    console.print()
