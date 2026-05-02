# `#b-deploy` — Hetzner / Railway production deploy + Cloudflare DNS / EU geo-block

> **Status:** Strategic-design depth (not implementer-ready). Wave 3 dossier. Author: wave3-plan-architect. 2026-05-03.

## 1. Goal

Phase 1 alpha deploy (Wave 3): a hosted production endpoint at `rodix.app` (or chosen domain) serving the FastAPI backend (`app/web/server.py`), the static frontend (`app/web/static/*`), the SQLite vault, and ingress with TLS. Geo-block EU at edge (per brand-book §3 + position-strategy §6). DNS + SSL automated. Migrate from Railway → Hetzner if costs cross threshold at scale.

## 2. Strategic context

`#b-dev-deploy` (Wave 1b shipped) covers LAN-only HTTP for dev. `#b-deploy` is the production sister: real TLS, real domain, real edge layer. Brand-book §3 commits to EU geo-block; this must enforce at the routing layer, not the application layer (defence-in-depth, lower latency for blocked users seeing immediate refusal).

## 3. Design options

(a) **Railway** — $5-20/mo Phase 1 tier, auto-deploys from GitHub, vendor-friendly (zero ops), generous free tier for Phase 1 alpha. Lock-in: medium (Railway-specific config, but Dockerfile-based deploys port elsewhere). Pricing scales linearly; gets expensive at $50+/mo.

(b) **Fly.io** — distributed-by-default; great for global low-latency; pricing similar to Railway at small scale. More operational complexity (per-region machine management).

(c) **Hetzner Cloud** — $5/mo dedicated cloud (CX22 = 4GB RAM / 2 vCPU); manual ops (SSH, systemd, manual SSL via Let's Encrypt + nginx). Pros: cheap-at-scale ($5/mo regardless of traffic up to bandwidth caps); EU-data-sovereignty-friendly. Cons: Rodc must manage server hygiene, security patches, restarts.

(d) **Render** — comparable to Railway, slightly more transparent pricing.

## 4. Recommended approach

**Railway for Phase 1 (≤1,000 users); migrate to Hetzner when Railway costs cross $50/mo (~5k users projected).** Rationale: Railway zero-ops matches solo-founder constraint; vendor lock-in is acceptable at Phase 1 because Dockerfile-based deploys port to Hetzner with 1-day setup.

DNS: **Cloudflare free tier** (covers Phase 1 fully — DDoS, edge cache, geo-block via Page Rules / WAF custom rules). EU geo-block enforced at Cloudflare edge: WAF rule rejecting traffic from EU country codes (DE, FR, IT, ES, NL, PL, SE, BE, AT, etc.) + EFTA (NO, IS, LI) + UK at Phase 1. SSL: Cloudflare-managed (Universal SSL) + origin certificate to Railway/Hetzner.

## 5. Vendor / tool choice

- **Railway** primary deploy host (Phase 1).
- **Hetzner Cloud** scale-out host (Phase 2+).
- **Cloudflare** DNS + DDoS + WAF + geo-block; free tier sufficient.
- **Let's Encrypt** for origin certificate on Hetzner migration; Cloudflare handles edge cert independently.

Lock-in: low across the stack — Dockerfile-based deploys port between Railway and Hetzner; Cloudflare DNS/WAF rules export to JSON.

## 6. Legal / compliance audit

EU geo-block at Cloudflare edge implements brand-book §3 commitment + GDPR Article 3 (territorial scope) defense — Rodix targets non-EU markets at Phase 1, blocked at edge to defensibly assert non-establishment. Privacy-policy disclosure (`#b-privacy-policy`): hosting region (Railway US-West / Hetzner Falkenstein FSN1), data residency, sub-processor list (Railway, Cloudflare, AWS S3 if backups go offsite).

DNS WHOIS: Rodc anonymity preserved via WHOIS privacy (Cloudflare Registrar provides this free). LLC entity name on registration if `#b-paddle` LLC formation completes first.

## 7. Rollback / migration if vendor changes

Railway → Hetzner: 1-day migration (Dockerfile + secrets + DB file rsync). Cloudflare → alternative DNS (e.g., DNSimple, Bunny CDN): 2-4 hours, but loses edge geo-block — must re-implement at app layer. Lock-in score: low overall, except Cloudflare WAF custom-rule semantics are vendor-specific.

## 8. Cost estimate

Phase 1 (≤1,000 users): **$5-20/mo Railway** + $0 Cloudflare + $12/yr `.app` domain registration. Total: **~$20-30/mo**. At $10k MRR (~5k users): **$50-150/mo Railway** OR **$10-30/mo Hetzner** + $0 Cloudflare. Migration trigger: $50/mo Railway sustained for 2 months.

## 9. Lead-time blockers

External: domain registration (`rodix.app` or alternative) — 1 day, ICANN waiting period. Cloudflare account approval — instant (self-serve). Railway approval — instant. Hetzner approval — 1-2 days for new account. SSL: instant via Cloudflare; Let's Encrypt 5-min on origin.

**Total lead time: 2-3 days from go-decision to live deploy.** Not on critical path for Phase 1 paid launch (which is gated by `#b-paddle` AUP at 6-8 weeks).

## 10. Open decisions for Rodc (Type-A)

- **TA-1:** Domain choice — `rodix.app` vs `rodix.com` vs `rodix.io` vs `rodix.so`. Brand-book §6 visual locked; domain not locked. Recommendation: `rodix.app` for Phase 1 (cheaper, available, matches Phase 2 PWA "app" register).
- **TA-2:** EU geo-block UX — Cloudflare can return 451 (Unavailable for Legal Reasons) with custom HTML, or 403 with friendly message. Recommendation: 451 + minimal HTML page explaining "Rodix is not available in your region during alpha; sign up for waitlist" — friends-intro register applies (anti-spin, refuses-to-dramatize).
- **TA-3:** Backup strategy — Railway snapshots vs offsite (AWS S3 / Cloudflare R2). Recommendation: Cloudflare R2 daily encrypted snapshots; matches "your data, your file" honesty when paired with `#b-encryption`.

## 11. Implementation outline (high-level)

1. Register domain (`rodix.app`); transfer to Cloudflare Registrar.
2. Provision Railway project; connect GitHub repo; configure environment variables (Anthropic / OpenRouter / Clerk / Paddle keys).
3. Deploy Dockerfile-based image; smoke-test on Railway-issued subdomain.
4. Switch DNS A/AAAA to Railway; validate cert chain.
5. Cloudflare WAF: add EU country-code block + bot-mitigation rules.
6. Cloudflare Page Rules: cache static assets aggressively; bypass cache on `/api/*`.
7. Backup pipeline: nightly SQLite vacuum + R2 upload.
8. Status page: `status.rodix.app` (UptimeRobot free tier).

## 12. Risk register

1. **Railway pricing shift / outage** — moderate probability; mitigated by Hetzner fallback path.
2. **Cloudflare WAF false-positives blocking legitimate traffic** — initially low; WAF Logs review weekly first month.
3. **Solo-founder ops fatigue at Hetzner migration** — Hetzner manual ops add weekly hygiene tax. Mitigation: delay migration until Railway cost truly justifies.
