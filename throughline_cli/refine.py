"""`python -m throughline_cli refine --dry-run <path.md>`

Reads a raw conversation markdown file, walks the same slicer +
refiner-prompt pipeline the daemon would walk, and prints *what
would be sent* to the LLM — without actually calling it.

The value: contributors can see what their refiner gets as input
without burning API credits. Tuning the dials / picking a pack /
iterating on prompt templates all benefit from a zero-cost preview.

Design choice: dry-run always uses the deterministic single-slice
path so small AND large conversations produce a visible preview
without a slicer-LLM call. If you explicitly want to see what the
slicer LLM would produce, run without --dry-run (which costs
money and is the normal daemon flow).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


USAGE = """\
Usage:
    python -m throughline_cli refine --dry-run <path/to/raw.md> [options]

Shows what prompts WOULD be sent to the refiner for the given raw
conversation — without calling any LLM.

Options:
    --dry-run              Required. Safety switch: no real refine.
    --show-full-prompt     Print the full refiner system prompt (no
                            truncation). Default truncates to ~20 lines.
    --pack <name>          Override pack auto-detection (wraps the
                            refiner system prompt with the pack's
                            modifier).
    --no-color             Disable ANSI colors in the output.

Positional:
    <path/to/raw.md>       A file the daemon would pick up from
                            $THROUGHLINE_RAW_ROOT (frontmatter + `##
                            user` / `## assistant` message sections).
"""


def _load_refine_module():
    """Import `daemon.refine_daemon` with env guards so a
    misconfigured shell (no LLM key) doesn't crash the dry-run —
    dry-run doesn't call LLMs anyway."""
    try:
        from daemon import refine_daemon as rd
        return rd
    except Exception as e:
        print(f"Could not import daemon.refine_daemon: {e}", file=sys.stderr)
        print("Hint: run from repo root so `daemon/` is on sys.path.",
              file=sys.stderr)
        return None


def _colorize(s: str, color: str, enabled: bool) -> str:
    if not enabled:
        return s
    codes = {
        "dim":    "\033[2m",
        "bold":   "\033[1m",
        "cyan":   "\033[36m",
        "green":  "\033[32m",
        "yellow": "\033[33m",
    }
    return f"{codes.get(color, '')}{s}\033[0m"


def _tier_for(rd, n_msgs: int, total_chars: int) -> tuple:
    """Replicate dispatch_slicer's decision tree (without the
    side-effect of calling the slicer) so we can tell the user
    which tier + model would have fired.

    Returns (tier_label, model_name_or_dash).
    """
    if (n_msgs <= rd.SLICE_SINGLE_THRESHOLD_MSGS
            and total_chars <= rd.SLICE_SINGLE_THRESHOLD_CHARS):
        return ("single (deterministic — no slicer LLM)", "—")
    if (n_msgs <= rd.SLICE_ONESHOT_MAX_MSGS
            and total_chars <= rd.SLICE_ONESHOT_MAX_CHARS):
        return ("one-shot slicer (Sonnet-class)", rd.SLICE_ONESHOT_MODEL)
    return ("long-context slicer (Opus-class)", rd.SLICE_OPUS_MODEL)


def _truncate_lines(s: str, max_lines: int) -> str:
    lines = s.splitlines()
    if len(lines) <= max_lines:
        return s
    kept = lines[:max_lines]
    return "\n".join(kept) + f"\n... [{len(lines) - max_lines} more lines — pass --show-full-prompt to see all]"


def _resolve_pack(rd, pack_name: str):
    """Best-effort pack resolution. Returns (pack_obj_or_None,
    resolved_name_for_display)."""
    if not pack_name:
        return None, "(none — base refiner prompt)"
    try:
        from packs.pack_runtime import PackRegistry
        reg = PackRegistry()
        pack = reg.get(pack_name)
        if pack is None:
            return None, f"{pack_name} (not found — falling back to base)"
        return pack, pack_name
    except Exception as e:
        return None, f"{pack_name} (resolution failed: {e})"


def _render_refiner_prompts(rd, slice_text: str, pack) -> tuple:
    """Reconstruct the refiner system + user prompt the daemon
    would send, without calling the LLM. Matches `_refine_slice`
    prompt construction."""
    if pack is not None:
        try:
            refiner_prompt = pack.refiner_prompt()
        except Exception:
            refiner_prompt = rd._build_refiner_prompt()
    else:
        refiner_prompt = rd._build_refiner_prompt()
    system_prompt = rd._apply_user_dials(refiner_prompt)
    user_prompt = (
        f"[SLICE]\n{slice_text[:rd.MAX_SLICE_CHARS_FOR_REFINER]}"
        f"\n\nEmit the card JSON now."
    )
    return system_prompt, user_prompt


def run_dry_run(raw_path: Path, *,
                 show_full_prompt: bool = False,
                 pack_name: str = "",
                 color: bool = True,
                 out=None) -> int:
    """Main dry-run routine. Returns an exit code.

    Split from main() so tests can call it directly with a tmp
    path + capture stdout via the `out` parameter.
    """
    out = out or sys.stdout
    rd = _load_refine_module()
    if rd is None:
        return 2

    if not raw_path.exists():
        print(f"Error: file not found: {raw_path}", file=sys.stderr)
        return 2

    conv = rd.parse_raw_conversation(raw_path)
    if conv is None:
        print(f"Error: could not parse conversation at {raw_path}.",
              file=sys.stderr)
        print("Expected frontmatter + `## user` / `## assistant` sections.",
              file=sys.stderr)
        return 2

    n_msgs = len(conv.messages)
    total_chars = sum(len(m.content) for m in conv.messages)
    tier_label, tier_model = _tier_for(rd, n_msgs, total_chars)
    pack_obj, pack_display = _resolve_pack(rd, pack_name)
    intent_mode = rd._detect_intent_mode(conv.messages)

    # ----- header -----
    bar = "=" * 60
    print(bar, file=out)
    print(_colorize("throughline refine --dry-run", "bold", color), file=out)
    print(bar, file=out)
    print(f"File           : {raw_path}", file=out)
    print(f"conv_id        : {conv.conv_id}", file=out)
    print(f"Messages       : {n_msgs}", file=out)
    print(f"Total chars    : {total_chars:,}", file=out)
    print(f"Source model   : {conv.source_model or '(unknown)'}", file=out)
    intent_flags = [k for k, v in intent_mode.items() if v]
    print(f"Intent flags   : {', '.join(intent_flags) if intent_flags else '(none)'}",
          file=out)
    print(f"Pack           : {pack_display}", file=out)
    print("", file=out)

    # ----- slicer tier that WOULD be selected -----
    print(_colorize("→ Slicer tier", "cyan", color), file=out)
    print(f"  Would dispatch : {tier_label}", file=out)
    print(f"  Slicer model   : {tier_model}", file=out)
    print("", file=out)

    # ----- dry-run uses deterministic single-slice path -----
    specs = rd._slice_single(conv)
    print(_colorize("→ Slices (deterministic single-slice path for dry-run)",
                     "cyan", color), file=out)
    print(f"  Slice count    : {len(specs)}", file=out)
    print("", file=out)

    # ----- refiner prompt preview per slice -----
    for i, spec in enumerate(specs, 1):
        if not spec.keep:
            print(_colorize(f"── Slice {i} [SKIP {spec.skip_reason}]",
                             "yellow", color), file=out)
            continue
        sys_prompt, user_prompt = _render_refiner_prompts(
            rd, spec.slice_text, pack_obj)
        print(_colorize(f"── Slice {i}: {spec.title_hint or '(no title hint)'}",
                         "green", color), file=out)
        print(f"   Messages {spec.start_idx}–{spec.end_idx}  "
              f"({len(spec.slice_text):,} chars)", file=out)
        print("", file=out)
        print(_colorize("   Refiner SYSTEM prompt (→ LLM, role=system):",
                         "dim", color), file=out)
        render_sys = sys_prompt if show_full_prompt else \
            _truncate_lines(sys_prompt, 20)
        for line in render_sys.splitlines():
            print(f"     {line}", file=out)
        print("", file=out)
        print(_colorize("   Refiner USER prompt (→ LLM, role=user):",
                         "dim", color), file=out)
        render_user = user_prompt if show_full_prompt else \
            _truncate_lines(user_prompt, 20)
        for line in render_user.splitlines():
            print(f"     {line}", file=out)
        print("", file=out)

    # ----- footer: cost + reminders -----
    print(bar, file=out)
    print(_colorize("No LLM call was made.", "bold", color), file=out)
    print(f"Refine model (if called) : {rd.REFINE_MODEL}", file=out)
    print("Run without --dry-run (via the daemon or a refine script) "
          "to actually refine.", file=out)
    print(bar, file=out)
    return 0


def main(argv) -> int:
    """Entry point from __main__.py dispatch. `argv` does not
    include the subcommand itself."""
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0 if argv and argv[0] in ("-h", "--help", "help") else 2

    p = argparse.ArgumentParser(
        prog="throughline_cli refine", add_help=False)
    p.add_argument("path", nargs="?", help="Raw markdown conversation.")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview-only mode (required).")
    p.add_argument("--show-full-prompt", action="store_true",
                   help="Print full refiner prompts (no truncation).")
    p.add_argument("--pack", default="", metavar="NAME",
                   help="Override pack auto-detection.")
    p.add_argument("--no-color", action="store_true",
                   help="Disable ANSI color output.")
    p.add_argument("-h", "--help", action="store_true")
    try:
        args = p.parse_args(argv)
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 2

    if args.help:
        print(USAGE)
        return 0

    if not args.dry_run:
        print("Error: --dry-run is required.", file=sys.stderr)
        print("This subcommand only supports the preview-only flow "
              "in v0.2.x. Use the daemon or scripts/ingest tools to "
              "actually refine.", file=sys.stderr)
        return 2

    if not args.path:
        print("Error: missing path to raw markdown file.", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2

    return run_dry_run(
        Path(args.path).expanduser().resolve(),
        show_full_prompt=args.show_full_prompt,
        pack_name=args.pack,
        color=not args.no_color,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
