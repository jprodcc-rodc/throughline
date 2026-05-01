# Session Handoff — 2026-05-01 EOD

> **For the CC starting the next session**: read this first, then `MEMORY.md` index, then the linked specs/plans.

## Context in 30 seconds

- **Wave 1a (demo-ready)**: signed off by Rodc. Phase-aware system prompt v1.3 verified working on `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` via 3-round live walk.
- **Wave 1b (fully functional)**: in flight. Two of N items done at code level; one blocked on auth; one plan ready for dispatch.
- **Current immediate blocker**: OpenRouter API key. Old key (`sk-or-v1-46487e...`) returns 401 "User not found" (revoked or quota-dead). Rodc set a new key in their terminal but the prior CC session's bash inherited the old env. **First action in a fresh session**: verify env has a working key.

## Current state matrix

| Item | Status | Files / pointer |
|---|---|---|
| Wave 1a | ✅ DONE | All ABC fixes + ISSUE 3 (error UX) + sk-or-v1 routing fix landed |
| `#1a` settings panel | ✅ DONE | `app/shared/secrets/`, `/api/settings*` endpoints, gear icon modal |
| `#w-docs` outline | ✅ DONE | `app/web/docs/` 6 files; Rodc fills copy |
| `#intent-classifier` code | ✅ DONE | `app/shared/intent/`, integrated into `/api/chat` chat path; 17 unit tests + 1 integration skipped |
| `#intent-classifier` eval gate | ❌ BLOCKED | OpenRouter 401 — needs new working key |
| `#claim-extraction` plan v1.3 | 📋 REVIEW-PASSED | `docs/superpowers/plans/2026-05-01-claim-extraction.md`; awaits classifier eval green before dispatch |
| `#3a` cards mgmt | 🔜 NOT STARTED | Wave 1b later |
| `#9a` history import | 🔜 NOT STARTED | Wave 1b later |

## First actions in the new session

1. **Verify OpenRouter auth** (60s):

   ```bash
   python -c "
   from throughline_cli.active_provider import resolve_endpoint_and_key
   import requests
   url, key, headers, pid = resolve_endpoint_and_key()
   print(f'provider={pid}, key_prefix={(key or \"\")[:12]}')
   hdrs = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json', **headers}
   r = requests.post(url, headers=hdrs, json={
       'model': 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
       'messages': [{'role': 'user', 'content': 'say hi'}],
       'max_tokens': 50,
   }, timeout=30)
   print(f'status={r.status_code}, body={r.text[:200]}')
   "
   ```

   - If `status=200` → proceed to step 2
   - If `status=401` "User not found" → key is stale; ask Rodc for the new key value (or have them restart CC again with the env actually exported)

2. **Run intent classifier eval** (~3-5 min, real LLM calls):

   ```bash
   python fixtures/v0_2_0/eval/run_intent_eval.py
   ```

   - Reads 100 cases from `fixtures/v0_2_0/eval/intent_cases.json`
   - Writes results to `fixtures/v0_2_0/eval/results-intent-nvidia-...-<timestamp>.json`
   - Prints overall accuracy + per-class precision/recall + per-boundary-category accuracy + 4-way gate verdict

3. **Verify asymmetric gate** (4 conditions):

   - `overall_accuracy >= 0.85`
   - `recall(thoughtful) >= 0.90`
   - `precision(chitchat) >= 0.75`
   - `recall(factual) >= 0.85`

4. **Branch decision**:

   - **All 4 hold** → `#intent-classifier` complete. Dispatch `#claim-extraction` implementer (see plan v1.3 + the dispatch-prompt template used for `#1a` and `#intent-classifier`). Implementer brief should mirror those — full project context, app/ gitignored, locale split, existing patterns to mimic, asymmetric gate criteria, etc.
   - **Any fail** → raise to Rodc per plan v1.3 risk register options (a/b/c/d). Print confusion matrix + per-category breakdown so Rodc can see WHICH boundary cases drag accuracy down.

## How to dispatch implementer subagents

The pattern that worked for `#1a` and `#intent-classifier`:

- One implementer subagent per plan (foreground)
- Brief: full project context block (gitignored note, locale split, existing patterns, defensive parsing tricks for nvidia model: `max_tokens >= 3000`, NO `response_format: json_object`)
- Plan path + skip-Commit-for-app-files note + per-task adjustments
- Failure handling: stop and report on blocker, don't guess

Two prior dispatch prompts are in conversation history; either is a solid template. The key elements:

- Explain `app/` is gitignored — implementer skips Commit lines for app/* tasks but DOES commit fixtures/ artifacts
- Point at `app/web/server.py::_load_rodix_system_prompt()` as the locked-prompt loader pattern
- Point at `throughline_cli.active_provider.resolve_endpoint_and_key()` as the provider resolver (which now correctly routes `sk-or-v1*` keys to OpenRouter regardless of which env var holds the key)
- Point at `fixtures/v0_2_0/eval/run_claim_extraction_eval.py` as the existing eval runner shape to mirror

## Test command shortcuts

```bash
# Full suite (no integration tests)
python -m pytest app/ fixtures/v0_2_0/test_active_provider.py --override-ini="testpaths=app" --override-ini="addopts=" -q

# Just classifier integration eval (real LLM)
RUN_INTEGRATION=1 python -m pytest app/shared/intent/test_classifier_integration.py -v

# Specific module
python -m pytest app/web/test_settings.py -v --override-ini="testpaths=app" --override-ini="addopts="
```

Expected at session-end: **527 passed + 1 skipped**.

## Things NOT to revert / undo

- Settings panel + KeyStorage in `app/shared/secrets/` — Rodc accepted #1a
- Classifier integration in `/api/chat` (`_should_show_placeholder` deleted; `result.intent == THOUGHTFUL` gate; `_PLACEHOLDER_BANNED_PHRASES` removed) — these were anti-patterns that v1.1 C-4.6 explicitly forbade; classifier work resolved the violation
- `pyproject.toml` `markers = ["integration: ..."]` registration
- `throughline_cli/providers.py::detect_configured_provider` `sk-or-v1*` prefix sniff
- `test_server.py::client` and `vector_client` fixtures' `monkeypatch.setenv` for vault dir
- v1.3 system prompt (`app/web/prompts/rodix_system.md`) phase-aware multi-round behavior

## Things still pending (Wave 1b + later)

- `#claim-extraction` dispatch (after classifier eval green)
- `#3a` cards management (Wave 1b — not started)
- `#9a` history import (Wave 1b — not started)
- `#rename-user-facing` (Wave 1b end-pass after `#r-name-final` brand lock)
- ISSUE 1 (rename throughline → Rodix) — deferred to `#rename-user-facing`
- ISSUE 2 (chat empty state with sample prompts) — deferred; needs Rodc-written sample prompt copy + #8 real feature + classifier integration
- ISSUE 4 (remove message labels) — deferred with #8 real feature
- Rodc's own 5-round subjective dogfood gate for `#claim-extraction` (Task 15)

## Cross-session handoff sanity check

Code on disk should match this list (run `ls` to verify):

- `app/shared/secrets/__init__.py`, `key_storage.py`, `test_key_storage.py`
- `app/shared/intent/__init__.py`, `classifier.py`, `test_classifier.py`, `test_classifier_integration.py`
- `app/shared/intent/prompts/intent_classifier.md`
- `app/web/prompts/rodix_system.md`
- `app/web/test_settings.py`, `test_chat_placeholder.py` (rewritten with classifier-based tests)
- `app/web/static/index.html` has `<button id="btn-settings">` + `<dialog id="settings-modal">`
- `app/web/static/app.css` has `.settings-modal`, `.error-recovery` classes
- `app/web/static/app.js` has `loadSettings()`, `testConnection()`, `saveSettings()` functions
- `app/web/server.py` has `/api/settings*` endpoints, `_key_storage()`, `_should_show_placeholder_for_intent()`, classifier import + call
