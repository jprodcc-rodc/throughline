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
