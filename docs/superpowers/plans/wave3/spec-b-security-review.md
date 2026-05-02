# `#b-security-review` — Self-audit checklist + recurring discipline

> **Status:** Strategic-design depth (not implementer-ready). Wave 3 dossier. Author: wave3-plan-architect. 2026-05-03.

## 1. Goal

Phase 1 alpha launch (Wave 3): a self-audit pass before public traffic + a recurring weekly discipline. No external pen-test budget at Phase 1 (solo founder, brand-book §2 anti-spin honesty about resources). The goal is to ship a defensible baseline — not "secure" in the marketing sense, but "checked the foreseeable failure modes" in the friends-intro honest sense.

## 2. Strategic context

Brand-book §7 Decision 6 commits to honest disclosure. `#b-security-review` makes this operational: a checklist Rodc can run, fails public, names what was checked, names what wasn't. Sensitive personal data (mental-health / political / sexual-orientation conversational disclosures per GDPR Art. 9) raises the stakes — a security incident on Rodix's data is materially worse than a typical SaaS breach.

## 3. Design options

(a) **Self-audit checklist + recurring weekly discipline** — Rodc runs through a fixed list before each release; CI enforces dependency-freshness. Cost: solo-founder time. No external party validates.

(b) **External pen-test before alpha** — $5k-15k for a 3-day engagement from a reputable firm. Catches things Rodc would miss. Reject at Phase 1 budget; revisit at $10k MRR.

(c) **Hybrid: self-audit + bug-bounty program (HackerOne / Intigriti)** — pay for findings post-launch; cheaper than pen-test, scales with traffic. Reasonable Phase 2 option.

## 4. Recommended approach

**Option (a) at Phase 1 launch.** Migrate to (c) at Wave 4 once revenue covers bug-bounty payout reserve. The checklist below is the minimum baseline; CI gates enforce the parts that lend themselves to automation.

### Checklist (run before each release)

**Secrets:**
- [ ] All API keys in environment variables (verified `Grep` for hardcoded `sk-` / `or-v1-` / `pk_live_` patterns across `app/`).
- [ ] No secrets in git history (`gitleaks` scan in CI).
- [ ] Anthropic + OpenRouter + Clerk + Paddle keys rotated at Phase 1 alpha launch (separate dev / prod keys).
- [ ] Frontend never receives backend secrets (verify `app/web/static/*` is API-key-free).

**SQL injection:**
- [ ] All SQL goes through parameterized queries (`?` placeholders). Wave 1b discipline already; CI gate via `bandit` + manual `Grep` for f-string SQL.
- [ ] FTS5 / vec0 virtual-table queries use parameterized binds (vec0 has known parameter-binding subtleties; verified per-call).

**XSS:**
- [ ] Frontend escapes user input via DOM `textContent` (not `innerHTML`) on all user-supplied strings. Wave 1b convention; spot-check `app/web/static/*.js` extraction renderers.
- [ ] Content-Security-Policy header set: `default-src 'self'; script-src 'self'; style-src 'self' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; connect-src 'self' clerk.rodix.app api.openrouter.ai api.anthropic.com`.
- [ ] No inline `<script>` in templates; nonce-based CSP if dynamic JS needed.

**CSRF:**
- [ ] Clerk auth tokens (JWT in `Authorization: Bearer`) — not cookie-based, so CSRF moot for `/api/*`. Verify session cookie on Clerk widget is `SameSite=Lax`.
- [ ] State-changing endpoints (DELETE, PUT, POST) require valid JWT; no GET endpoints mutate state.

**Rate limiting:**
- [ ] Per-user rate limit on `/api/chat` (10 req/min default; see Task 13 cost-cap which supersedes this with token-based caps).
- [ ] Per-IP rate limit on unauth endpoints (sign-in, magic-link request) at Cloudflare WAF.
- [ ] Magic-link requests rate-capped per email (Clerk default).

**Dependency audit:**
- [ ] `pip-audit` weekly in CI; alert on CRITICAL / HIGH CVEs.
- [ ] `npm audit` (or equivalent) weekly on frontend deps if any (Phase 1 frontend is vanilla JS, minimal deps).
- [ ] Pin `requirements.txt` to exact versions; no `>=` ranges.

**Logging hygiene:**
- [ ] No conversation content in application logs (cards / messages NEVER logged in plaintext).
- [ ] No API keys in error tracebacks (env-var redaction at log layer).
- [ ] Sentry / equivalent: scrub PII filter configured; sample rate controls cost.

**Crisis-content handling (cross-coord with Wave 1c):**
- [ ] Per `D1` resolution in `assumption-list.md`: explicit safety language triggers resource banner, bypasses extraction. Verify implementation before alpha launch.

## 5. Vendor / tool choice

- **`pip-audit`** (PyPA, free) — Python CVE checker.
- **`bandit`** (PyCQA, free) — Python security linter.
- **`gitleaks`** (free, open-source) — secret-leak scanner.
- **Cloudflare WAF** — already in `#b-deploy`; doubles as rate-limit / bot-mitigation layer.
- **Sentry** ($26/mo team plan; free tier covers Phase 1) — error tracking.

Lock-in: zero across the audit toolchain (all FOSS or replaceable).

## 6. Legal / compliance audit

GDPR Article 32: technical measures — encryption-at-rest (`#b-encryption`), pseudonymization (auth_user_id not email in adapter layer), incident detection (Sentry). Article 33-34: breach notification within 72hr — incident response runbook needed (TA-2 below). SOC 2 / ISO 27001: not pursued at Phase 1 (cost-prohibitive); revisit at $100k MRR.

Sensitive personal data exposure: Art. 9 categories present in conversational content. Mitigation: encryption-at-rest + geo-block EU + heightened privacy-policy clauses + DPO contact.

## 7. Rollback / migration if vendor changes

Sentry → alternative (Honeybadger, Rollbar): 1-2 days. Cloudflare WAF → alternative: 2-4 hours, but loses managed bot-mitigation. Audit toolchain (`pip-audit` etc.): all FOSS, swap-in-place.

## 8. Cost estimate

Phase 1 (≤1,000 users): **$0/mo** (Sentry free tier 5k events/mo; pip-audit / bandit / gitleaks free). At $10k MRR scale: **$26/mo Sentry team** + ~$10/mo Cloudflare Pro upgrade for advanced WAF rules. Bug-bounty payout reserve: $1k/yr at Phase 2.

## 9. Lead-time blockers

External: zero (no vendor approval). Internal: ~5-7 days to walk the full checklist and remediate findings. Recurring: ~2hr/week ongoing discipline.

## 10. Open decisions for Rodc (Type-A)

- **TA-1:** External pen-test trigger threshold. Recommendation: $10k MRR or 30 days post-paid-launch, whichever earlier.
- **TA-2:** Incident response runbook — who is paged on Sentry CRITICAL? Solo founder = solo responder. Need 72hr GDPR breach notification template ready before alpha launch.
- **TA-3:** Logging policy lock — is "never log conversation content" sufficient, or do we need debug-only ephemeral logs (with TTL)? Recommendation: never-log-content holds; debug via local repro only.

## 11. Implementation outline (high-level)

1. Run the checklist end-to-end before Phase 1 alpha launch; document findings in `docs/security-audit-2026-XX-XX.md`.
2. CI: add `pip-audit`, `bandit`, `gitleaks` as required GitHub Actions checks.
3. Cloudflare WAF: configure rate limits + bot-mitigation rules + EU geo-block (cross-coord `#b-deploy`).
4. Sentry: integrate with PII scrubber + sample rate controls.
5. Incident-response runbook: write to `docs/incident-response.md`; rehearse once before launch.

## 12. Risk register

1. **Solo-founder audit blind spots** — Rodc cannot pen-test his own product effectively. Bug-bounty post-launch mitigates.
2. **Crisis-content handling regression** — every release must re-verify D1 mitigation (cross-coord Wave 1c).
3. **Cloudflare WAF false-negative on novel attack** — managed rules cover OWASP top 10; targeted attacks not covered. Acceptable at Phase 1; revisit at scale.
