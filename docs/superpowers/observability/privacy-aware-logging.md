# Rodix Wave 3 — Privacy-Aware Logging Discipline

> **Status:** Strategic-design depth. Wave 3 dossier. Author: observability-architect. 2026-05-03.
>
> **Anchors:** `observability-spec.md` §3 (logging strategy) · `cost-cap-design.md` §6 (privacy-aware metrics) · `brand/brand-book-v1.md` §7 Decision 1 (white-box / no shadow profile) + Decision 6 (anti-spin honest disclosure).
>
> **Brand commitment operationalized:** brand-book Decision 1 — *"There is no shadow profile. There is no inferred persona label the user cannot see."* Logs that capture user content would by definition create a hidden record the user cannot see — incompatible with Decision 1. This file is the discipline that makes Decision 1 enforceable.

## 1. Sentry `before_send` hook (Python)

Install `sentry-sdk[fastapi]` (Phase 1 free tier). Initialize in `app/web/server.py` startup:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Forbidden-content keys: stripped from any error event before transmission to Sentry.
# Mirrors observability-spec.md §3 forbidden-field list.
FORBIDDEN_CONTENT_KEYS = {
    "message_content",      # raw user message text
    "ai_reply",             # assistant turn text
    "card_content",         # vault card field text
    "recall_callout_content",  # active-recall surface text
    "topic", "concern", "hope", "question",  # vault card field names
    "user_message", "assistant_message",     # alt aliases
    "request_body", "response_body",         # raw HTTP bodies
}

def before_send_scrub(event, hint):
    """Strip user content from Sentry events before transmission.

    Why: brand-book Decision 1 forbids shadow profiles. Sentry-transmitted
    error events that include user message text would constitute a hidden
    user-content record off-platform.
    """
    # Strip request data (raw POST body)
    if "request" in event:
        event["request"].pop("data", None)
        # Headers: keep only allowlisted (drop cookie / authorization — default Sentry but explicit)
        if "headers" in event["request"]:
            allowed = {"host", "user-agent", "referer", "content-type"}
            event["request"]["headers"] = {
                k: v for k, v in event["request"]["headers"].items()
                if k.lower() in allowed
            }

    # Strip extra context keys
    if "extra" in event:
        for key in list(event["extra"].keys()):
            if key in FORBIDDEN_CONTENT_KEYS:
                event["extra"][key] = "<scrubbed>"

    # Strip stack-trace local variables (defense-in-depth — locals can capture user content)
    for exception in event.get("exception", {}).get("values", []):
        for frame in exception.get("stacktrace", {}).get("frames", []):
            if "vars" in frame:
                for var in list(frame["vars"].keys()):
                    if var in FORBIDDEN_CONTENT_KEYS:
                        frame["vars"][var] = "<scrubbed>"

    # User identifier: hash-only (never email)
    if "user" in event:
        event["user"] = {"id": event["user"].get("id_hash", "<unknown>")}

    return event

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,           # 10% perf trace sampling
    send_default_pii=False,           # CRITICAL — disables auto-PII collection
    before_send=before_send_scrub,
    environment=os.environ.get("RODIX_ENV", "production"),
)
```

**Defense-in-depth layers:**
1. `send_default_pii=False` (Sentry config) — disables Sentry's default PII auto-collection
2. `before_send_scrub` — strips request data + extra + stack-trace locals
3. Application code MUST NOT pass forbidden content into `sentry_sdk.set_extra()` / `sentry_sdk.set_context()` — enforced via `app/shared/observability/sentry_helpers.py` typed wrapper that whitelists allowed keys

## 2. Structured-logging emitter (Python)

Replace any `print()` / `logging.info()` calls in `app/web/server.py` and downstream modules with the structured emitter:

```python
import json, logging, sys
from datetime import datetime, timezone

ALLOWED_LOG_KEYS = {
    "timestamp", "level", "correlation_id", "user_id_hash",
    "op", "latency_ms", "success", "model",
    "tokens_input", "tokens_output", "error_class",
    "intent_class", "recall_trigger_type", "recall_score",
    "extraction_field_count",
}

def emit_log(level: str, **fields):
    """Emit one JSON log line. Drops any non-allowlisted key.

    Why: brand-book Decision 1. Allowlist (not denylist) is the safer default —
    new fields require explicit review before they can be logged.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
    }
    for k, v in fields.items():
        if k in ALLOWED_LOG_KEYS:
            record[k] = v
        else:
            # Critical: drop non-allowlisted key, do not raise (logging must not break flow)
            # but emit a meta-warning to the same stream
            record.setdefault("_dropped_keys", []).append(k)
    print(json.dumps(record), file=sys.stdout, flush=True)
```

**Allowlist (not denylist) rationale:** denylist requires updating every time a new content field is added (extraction_card_topic / recall_callout_text / etc.) — easy to miss. Allowlist requires explicit review before any new field is logged. If a future engineer needs a new structural metric, they add it to `ALLOWED_LOG_KEYS` after confirming it does not embed user content.

## 3. Quarterly privacy audit

**Mechanism:** quarterly cron job (Cloudflare Workers + Loki query API, or local script run by Rodc) executes a known-test-message-string sweep against the prior 30 days of logs. Confirms zero matches.

**Test fixtures:** `tests/privacy/known_strings.txt` contains 10 distinctive multi-word strings that Rodc has used in dogfood sessions over the audit period (e.g. `"Side project shutdown / Sunk cost - 200 hours in"` from friends-intro example, `"corporate secretary"` from the Gemini critique passage, etc.). Rodc maintains this list privately — adding new strings each quarter from his own real usage.

**Audit script (pseudo-code):**

```bash
# Run quarterly. Reports zero-match → audit passes.
for fixture in $(cat tests/privacy/known_strings.txt); do
    matches=$(loki-cli query --range 30d --selector '{app="rodix"}' "$fixture" | wc -l)
    if [ "$matches" -gt 0 ]; then
        echo "FAIL: '$fixture' found in $matches log entries — leak"
        exit 1
    fi
done
echo "PASS: zero matches across $(wc -l fixtures) fixtures over 30d"
```

**Audit failure response:**
1. Halt new log emission via feature-flag (Rodc decision).
2. Identify leak source (which `op`, which code path, which release).
3. Patch via additional `before_send_scrub` rule OR allowlist enforcement gap.
4. Loki retention purge (immediate — do not wait for 30d auto-purge).
5. Brand-book Decision 1 incident postmortem in `decisions.md`.
6. Public disclosure if external user content was exposed (per privacy-policy Article 33 GDPR-equivalent commitment — see `wave3/spec-b-privacy-policy.md`).

**Rodc time per audit:** ~30 min quarterly (run script, review report, update fixture list). Ops fatigue tolerable.

## 4. 30-day retention enforcement

**Loki configuration (Hetzner migration):**

```yaml
# loki-config.yaml
limits_config:
  retention_period: 720h   # 30 days
  retention_stream:
    - selector: '{app="rodix", level="DEBUG"}'
      period: 24h          # DEBUG retained only 1 day (extra paranoia)
compactor:
  retention_enabled: true
  compaction_interval: 10m
```

**Railway-resident logs (Phase 1 alpha pre-Hetzner):** Railway's Cloudwatch-equivalent retention defaults to 7 days on the free tier — *less than 30 days, but acceptable.* Migration trigger to Hetzner self-hosted Loki: when Rodc wants the full 30-day retention OR when Railway log-volume crosses cost threshold.

**Retention test:** part of CI suite. Writes a known-marker log line at deploy time + 31 days; confirms it has been purged by `audit_retention_test.sh` (cron, weekly).

## 5. PostHog event schema discipline

PostHog events are **structural-only** by configuration:

```python
posthog.capture(
    distinct_id=user_id_hash,           # never raw email
    event="chat_turn_completed",
    properties={
        "intent_class": intent,         # label, not text
        "tokens_input": tokens_in,
        "tokens_output": tokens_out,
        "latency_ms": latency,
        "model": "claude-haiku-4-5-20251001",
        "success": True,
        # NEVER:
        # "message_content": user_msg,
        # "ai_reply_text": reply,
        # "card_topic": topic,
    }
)
```

PostHog event-emitter wrapper at `app/shared/observability/posthog_helpers.py` enforces the same allowlist as the structured logger.

## 6. Audit-trail summary

Every layer that could carry user content has a discipline:

| Layer | Mechanism | Audit |
|---|---|---|
| Sentry events | `before_send_scrub` + allowlist wrapper | Quarterly Sentry event export grep |
| App logs (stdout JSON) | `emit_log` allowlist | Quarterly Loki query against fixtures |
| PostHog events | typed `posthog_helpers.py` wrapper | Quarterly PostHog event export grep |
| Sentry stack traces | `before_send_scrub` strips locals | Same as Sentry event audit |
| HTTP request logs (Cloudflare) | Cloudflare logs do NOT include POST bodies by default | Annual Cloudflare config review |

Three layers with positive allowlists, two layers with default-deny configurations. The discipline is enforceable via grep — no ML, no clever pattern-matching. If an audit fails, the failure is loud and the fix is one allowlist change.

---

*End privacy-aware-logging.md. Operationalizes brand-book §7 Decision 1 + Decision 6 across the observability stack.*
