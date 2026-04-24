# Sample data

Synthetic conversations for first-time users to see the throughline
loop without needing their own export. Wired up as:

```bash
python -m throughline_cli import sample
```

## What's inside

- **`claude_sample.jsonl`** — 10 synthetic Claude-format conversations
  (`chat_messages` shape) spanning AI, hardware, health, biz, and
  creative topics. Variety is deliberate so the taxonomy observer
  (U27.3) has signal to detect drift across domains.

## What it isn't

- **Not your data.** All conversations are fabricated. Never paste
  these into anything you care about being correct.
- **Not exhaustive.** Real exports have hundreds-to-thousands of
  conversations. This is enough to verify the loop works, not to
  benchmark performance.
- **Not a fixture for the test suite.** The pytest fixtures live
  under `fixtures/`. This directory is shipped as user-facing
  sample data.

## Recording a wizard demo

`record_wizard_demo.sh` is an asciinema-friendly script that drives
`python install.py` end-to-end against the bundled sample, with
deterministic answers fed via a heredoc. Useful for producing a
reproducible terminal cast for the README / blog / docs without
anyone having to type or screen-record.

```bash
# Install asciinema once (macOS: brew, Debian/Ubuntu: apt, other: pipx).
asciinema rec demo/wizard.cast \
    --command "bash samples/record_wizard_demo.sh" \
    --idle-time-limit 1.5 \
    --title "throughline install wizard"

asciinema play demo/wizard.cast       # replay
asciinema upload demo/wizard.cast     # share (optional)
```

The script uses a throwaway `THROUGHLINE_CONFIG_DIR` so a recording
session doesn't clobber your real `~/.throughline/config.toml`.
