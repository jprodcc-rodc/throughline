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

UX layer 2 (added 2026-04-26):
    pick_option / ask_yes_no transparently use `questionary` for
    arrow-key navigation when stdin is a real TTY, falling back to
    the legacy numbered-input path otherwise. CI / pytest / piped
    stdin all hit the legacy path automatically — no test mock
    rewrites needed. Users who hate the new picker can force the
    legacy path with `THROUGHLINE_LEGACY_UI=1`.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree


# Single shared Console. force_terminal=False so piped output looks
# right in test captures; highlight=False so arbitrary '1.0' strings
# aren't auto-coloured as numbers inside our messages.
console = Console(highlight=False)


def _is_real_tty() -> bool:
    """Best-effort 'are we in front of a real human at a TTY' check.
    Reused by `_use_questionary` and by the spinner — a non-TTY (CI,
    pytest, redirected stdout) shouldn't render an animated spinner
    that just emits hundreds of frames into the captured log."""
    try:
        return bool(sys.stdout.isatty() and sys.stdin.isatty())
    except (AttributeError, ValueError):
        return False


class _NullStatus:
    """Drop-in replacement for `console.status()` when we don't have
    a TTY. Same context-manager interface, no animation."""
    def __init__(self, message: str):
        self.message = message

    def __enter__(self):
        # Print the message once so non-TTY users still see what
        # the wizard is waiting on.
        console.print(f"[dim]{self.message}[/]")
        return self

    def __exit__(self, *exc):
        return False

    def update(self, message: str) -> None:
        console.print(f"[dim]{message}[/]")


def status(message: str) -> "object":
    """Spinner context manager for blocking operations (LLM call,
    adapter run). Uses rich's animated `console.status` on real TTYs;
    falls back to a static print on CI / pytest / piped output so test
    captures stay clean.

    Returns a context manager. Concrete type is either
    `rich.status.Status` or `_NullStatus` — both expose the same
    enter/exit/update API but they don't share a base class so the
    return type is widened to `object` for the public surface."""
    if _is_real_tty() and os.environ.get("THROUGHLINE_LEGACY_UI", "").strip() == "":
        return console.status(f"[dim]{message}[/]", spinner="dots")
    return _NullStatus(message)


def _use_questionary() -> bool:
    """Return True iff we should use questionary for prompts.

    Falls back to legacy numbered input when:
    - stdin isn't a TTY (CI, pytest, piped input) — the existing
      `monkeypatch("builtins.input", ...)` test pattern works.
    - THROUGHLINE_LEGACY_UI is set — opt-out for users on terminals
      that mishandle the arrow-key navigation.
    - questionary isn't installed — keeps the wizard working on
      installs that skipped the optional dep.
    """
    if os.environ.get("THROUGHLINE_LEGACY_UI", "").strip():
        return False
    try:
        if not sys.stdin.isatty():
            return False
    except (AttributeError, ValueError):
        return False
    try:
        import questionary  # noqa: F401
    except Exception:
        return False
    return True


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


# ---------- wizard banner + progress ----------

_BANNER = r"""
 _   _                           _     _ _
| |_| |__  _ __ ___  _   _  __ _| |__ | (_)_ __   ___
| __| '_ \| '__/ _ \| | | |/ _` | '_ \| | | '_ \ / _ \
| |_| | | | | | (_) | |_| | (_| | | | | | | | | |  __/
 \__|_| |_|_|  \___/ \__,_|\__, |_| |_|_|_|_| |_|\___|
                           |___/
"""


def banner() -> None:
    """Print the welcome banner once at wizard startup. Uses cyan
    for the ASCII art + dim grey for the tagline."""
    # Version pulled dynamically so the banner never drifts from
    # pyproject.toml / package metadata.
    try:
        from . import __version__ as _v
    except Exception:
        _v = "dev"
    console.print()
    console.print(f"[bold cyan]{_BANNER}[/]")
    console.print(
        f"  [dim]install wizard · v{_v} · "
        "`python install.py --step N` to jump[/]"
    )
    console.print()


def progress_ticker(current: int, total: int) -> None:
    """Dim one-line progress indicator between steps.

    Renders as `● ● ● ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○ ○  (3/16)` with done/pending
    dots. Printed BEFORE the next step header so the user has a
    one-glance sense of 'how much further'."""
    done = "●" * current
    pending = "○" * (total - current)
    console.print(
        f"  [dim]{done}[/][dim bright_black]{pending}[/]  "
        f"[dim]({current}/{total})[/]"
    )


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


def summary_tree(groups: list[tuple[str, list[tuple[str, str]]]]) -> None:
    """Render a hierarchical summary tree (Tier-3 UX).

    `groups` is a list of (group_label, [(key, value), ...]) tuples.
    The tree shows each group as a top-level branch with key/value
    leaves below. Keys are cyan, values are bold; group labels are
    bold-cyan.

    On a real TTY, rich draws the unicode tree chars (├── etc.). On
    a non-TTY (CI, pytest), rich auto-strips the box-drawing into
    ASCII so test captures stay readable.
    """
    tree = Tree("[bold cyan]your throughline config[/]", guide_style="dim cyan")
    for group_label, items in groups:
        if not items:
            continue
        branch = tree.add(f"[bold cyan]{group_label}[/]")
        for k, v in items:
            branch.add(f"[cyan]{k}[/]: [bold]{v}[/]")
    console.print(tree)


# ---------- prompts (keep input() underneath for testability) ----------

def _pick_option_legacy(question: str,
                          options: list[tuple[str, str, str]],
                          default_key: str) -> str:
    """The classic numbered-input picker. Used when stdin isn't a
    TTY (pytest, CI, piped input) or when the user opts out via
    THROUGHLINE_LEGACY_UI=1."""
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


def _pick_option_arrow(question: str,
                         options: list[tuple[str, str, str]],
                         default_key: str) -> str:
    """Arrow-key navigation via questionary. Real TTYs only.

    Each option becomes a `Choice` whose visible title is
    `<label>  —  <description>` (truncated so even a 16-provider list
    fits on one line per item). The default option is pre-selected
    so pressing Enter immediately accepts it (the Tier-1 UX win:
    cursor is already on the recommended pick).
    """
    import questionary
    from questionary import Choice

    # Build choices with the default pre-selected. questionary uses
    # Choice.title for display + Choice.value for the returned key.
    #
    # IMPORTANT: pass `default=` as the VALUE STRING, not as the Choice
    # object. `Choice.__eq__` is identity-based, so passing a Choice
    # makes questionary's cursor-positioning logic compare two
    # different Choice instances and never match — the cursor would
    # silently land on the first item regardless of `default_key`. The
    # value-string branch falls into a `self.default == choice.value`
    # comparison which is plain string equality and works.
    choices = []
    for key, label, desc in options:
        # Render label + dim description in the same line. Truncate
        # description so the picker stays one-line-per-option.
        if desc:
            short_desc = desc if len(desc) <= 70 else desc[:67] + "..."
            title_text = f"{label}  —  {short_desc}"
        else:
            title_text = label
        choices.append(Choice(title=title_text, value=key))

    # Pointer + style overrides for Windows-terminal compatibility.
    # The default pointer (») doesn't always re-render on conhost
    # when the user navigates; an explicit ❯ + a high-contrast
    # selected-row style helps Windows Terminal / PowerShell ISE
    # reliably redraw the highlight on every arrow press.
    from questionary import Style
    pt_style = Style([
        ("pointer",         "fg:#00d7ff bold"),  # bright cyan ❯
        ("highlighted",     "fg:#000000 bg:#00d7ff bold"),  # selected row: dark text on cyan
        ("selected",        "fg:#00d7ff"),
        ("instruction",     "fg:#888888 italic"),
        ("question",        "bold"),
    ])
    try:
        answer = questionary.select(
            question,
            choices=choices,
            default=default_key,
            instruction="(↑/↓ to move · Enter to select)",
            qmark="?",
            pointer="❯",
            style=pt_style,
            use_jk_keys=False,        # disable j/k vim keys; some
                                       # terminals leak them as raw
                                       # chars when arrows mis-render.
            use_emacs_keys=False,     # same — emacs keybindings can
                                       # confuse Windows conhost.
        ).unsafe_ask()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[red]Aborted.[/]")
        sys.exit(130)
    if answer is None:
        # questionary returns None on Ctrl-C in some flows.
        return default_key
    return answer


def pick_option(question: str,
                options: list[tuple[str, str, str]],
                default_key: str) -> str:
    """Pick one of `options` (key, label, description tuples).
    Returns the chosen key. Auto-routes between the arrow-key
    questionary picker (real TTY) and the legacy numbered input
    (CI / pytest / piped stdin / THROUGHLINE_LEGACY_UI=1).

    The questionary path is wrapped in a defensive try/except for
    environments that pass the TTY check but trip the deeper
    `prompt_toolkit` console probe (mintty / git-bash / cygwin /
    weird PTY proxies on Windows). On any such failure we fall
    back to the legacy picker rather than crashing the wizard."""
    if _use_questionary():
        try:
            return _pick_option_arrow(question, options, default_key)
        except Exception as e:
            console.print(
                f"  [yellow]Arrow-key picker unavailable in this terminal "
                f"({type(e).__name__}); using numbered picker instead.[/]"
            )
            console.print(
                "  [dim]Set THROUGHLINE_LEGACY_UI=1 to skip this probe.[/]"
            )
    return _pick_option_legacy(question, options, default_key)


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
    """Y/N prompt. Routes to questionary.confirm on real TTYs;
    falls back to ask_text-based parsing for CI / pytest. Same
    defensive try/except as pick_option for terminals that pass
    `isatty()` but trip prompt_toolkit's console probe."""
    if _use_questionary():
        try:
            import questionary
            return bool(questionary.confirm(
                question, default=default,
                qmark="?",
            ).unsafe_ask())
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Aborted.[/]")
            sys.exit(130)
        except Exception:
            # Mintty / git-bash on Windows etc. — fall through
            # to the text-based path.
            pass
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
