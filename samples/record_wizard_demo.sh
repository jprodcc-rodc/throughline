#!/usr/bin/env bash
#
# Auto-driven wizard demo for asciinema recording.
#
# What this is for: producing a deterministic terminal cast that
# walks through `python install.py` end-to-end against the bundled
# sample export, so README / docs / blog posts can embed a
# recording without anyone having to type or screen-record live.
#
# Usage:
#
#     # Install asciinema once.
#     #   macOS:        brew install asciinema
#     #   Debian/Ubuntu: sudo apt install asciinema
#     #   Other:         pipx install asciinema
#
#     # Record (this script is the program asciinema records):
#     asciinema rec demo/wizard.cast \
#         --command "bash samples/record_wizard_demo.sh" \
#         --idle-time-limit 1.5 \
#         --title "throughline install wizard"
#
#     # Replay locally:
#     asciinema play demo/wizard.cast
#
#     # Upload (optional):
#     asciinema upload demo/wizard.cast
#
# Why bash + a heredoc instead of expect / pexpect: the wizard's
# step functions all read from `builtins.input()`, which respects
# stdin redirection. A heredoc is the smallest reproducible
# automation surface — no third-party dep, runs identically on
# macOS / Linux / git-bash on Windows.
#
# What this DOESN'T do: it doesn't run the rag_server / daemon /
# OpenWebUI Filter. The cast ends at the wizard's "Next 3 steps"
# panel, which is the natural cliffhanger for a 60-90s demo.
# Recording the full Filter loop requires a live OpenWebUI
# container and is out of scope for this script.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Use a throwaway config dir so the demo doesn't clobber the
# recorder's real ~/.throughline setup.
DEMO_DIR="$(mktemp -d)"
export THROUGHLINE_CONFIG_DIR="$DEMO_DIR/config"
export THROUGHLINE_STATE_DIR="$DEMO_DIR/state"
export THROUGHLINE_RAW_ROOT="$DEMO_DIR/raw"

# Friendly banner — asciinema picks this up at the start of the cast.
cat <<EOF
# ─────────────────────────────────────────────────────────────────
# throughline · install wizard demo
# ─────────────────────────────────────────────────────────────────
# Synthetic config dir: $DEMO_DIR
# Sample import:        samples/claude_sample.jsonl (10 conversations)
# This is recorded — answer any prompt with the suggested key.
# ─────────────────────────────────────────────────────────────────
EOF

sleep 1

# Heredoc-driven answers, one per wizard step.
# Annotated below so a reader of the cast file (or this script) can
# tell what each blank line means.
python install.py <<'WIZARD_INPUT'
                                         # 1.  env check (no input)
                                         # 2.  mission: Enter = Full
                                         # 3.  vector_db: Enter = qdrant
                                         # 4.  api key: Enter (env var)
                                         # 5.  llm provider: Enter = sonnet-4.6
                                         # 6.  privacy: Enter = hybrid
                                         # 7.  retrieval: Enter = bge defaults
                                         # 8.  prompt family: Enter (auto-derived)
4
samples/claude_sample.jsonl              # 9b. import path → bundled sample
                                         # 10. import scan + privacy consent
y
                                         # 11. refine tier: Enter = normal
                                         # 12. card structure: Enter = standard
                                         # 13. preview cost preflight
n
                                         # 14. taxonomy: Enter = minimal
                                         # 15. budget: Enter = $20.00
                                         # 16. summary confirm
y
WIZARD_INPUT

echo
echo "# ─────────────────────────────────────────────────────────────────"
echo "# Wizard finished. The Next 3 Steps panel above shows what to do."
echo "# (Demo dir was \$THROUGHLINE_CONFIG_DIR=$DEMO_DIR — clean up if you like.)"
echo "# ─────────────────────────────────────────────────────────────────"
