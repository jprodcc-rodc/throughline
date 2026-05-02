# `#b-auth` — Passwordless magic link + Google OAuth (optional)

> **Status:** Strategic-design depth (not implementer-ready). Wave 3 dossier. Author: wave3-plan-architect (Tier 1 Task 2). 2026-05-03.

## 1. Goal

Phase 1 launch: a single passwordless sign-in path (magic link to email) that lets the alpha cohort (≤1,000 users) reach the product without password-management overhead, without exposing Rodc's solo-anonymous-founder posture to Apple Developer enrollment, and without surfacing identity claims the brand book has not yet authorized. Phase 2 (launch+30): Google OAuth as a secondary path for users who have Google sign-in habit. Phase 3 (launch+90): optional Apple OAuth once mobile native ships and Apple's $99/yr developer program is acceptable cost.

## 2. Strategic context

The friends-intro positions Rodix as "your data, your file" — auth must not contradict that by introducing a vendor that holds account state Rodc cannot extract. Magic-link-first matches the anti-spin / refuses-to-dramatize register (no celebratory "welcome!" account creation flow) and avoids the sycophancy register `rodix_system.md` v1.3 bans.

## 3. Design options

(a) **Auth0** — mature, enterprise-priced ($240/mo entry tier above 7k MAU), heavy lock-in via proprietary user store. Brand-fit poor: default UI is corporate-blue. Reject.

(b) **Clerk** — free 10k MAU tier, JWT-based, customizable UI matching Inter / amber tokens, magic link + Google OAuth available out of the box, "users export" admin API for portability. Medium lock-in (JWT format proprietary; export path exists but session-token rotation requires user action on migration).

(c) **Supabase Auth** — free tier generous, but bundles a Postgres-backed user store that pulls Rodix toward a non-SQLite architecture incompatible with the local-first single-tenant Wave 1b code surface. Reject.

(d) **Custom JWT + magic link via Resend/Postmark** — zero vendor lock-in, but ships ~1.5k LOC of cryptographic discipline (token rotation, replay prevention, rate limiting per email) for a solo founder. Time cost > value at Phase 1.

## 4. Recommended approach

**Clerk free tier**, magic link as primary, Google OAuth toggle hidden by default. Rationale: 1-day integration vs 5-7 days custom; brand-customizable UI; export path exists (mitigates lock-in panic); 10k MAU free tier covers Phase 1 ≤1,000 users with 10x headroom.

## 5. Vendor / tool choice

**Clerk** at `clerk.com`. Free Hobby tier (10k MAU). Lock-in: medium. JWT verification key is rotatable; user records exportable via Clerk admin API as JSON; if migration becomes urgent, a 2-day port to custom JWT (option d above) becomes feasible because Clerk's user model is small (email + auth_id + metadata).

## 6. Legal / compliance audit

GDPR exposure: Clerk is GDPR-compliant per their public policy. EU geo-block at Cloudflare layer (per `#b-deploy`) prevents EU users from reaching the Clerk widget — defence-in-depth. Cookie disclosure: Clerk auth cookie is `__session`, scoped to `*.rodix.app`, must appear in privacy policy cookie list (`#b-privacy-policy`). PII collected: email address only at Phase 1; no names, no phone numbers, no profile photos.

## 7. Rollback / migration if vendor changes

If Clerk pricing or AUP changes hostile (e.g., requires real-name founder verification): export user records via admin API (1-2 hr), provision custom JWT verifier, send password-reset-style migration emails to existing users. Estimated migration cost: 5-7 days engineering. Lock-in score: medium (because email is the natural primary key, not Clerk's internal ID).

## 8. Cost estimate

Phase 1 (≤1,000 MAU): **$0/mo** (free Hobby tier covers up to 10k MAU). At $10k MRR scale (~5k paying ≈ ~15k MAU mixed): **$25/mo** Pro tier; at 50k MAU: ~$100/mo. Auth cost is negligible vs Anthropic/OpenRouter spend at any scale Rodix reaches in 18 months.

## 9. Lead-time blockers

**Zero.** Self-serve Clerk signup; Phase 1 alpha can integrate in 1 day. No vendor approval, no compliance review.

## 10. Open decisions for Rodc (Type-A)

- **TA-1:** Magic-link copy register — auth email subject + body must match brand-book §5 voice (specific / anti-spin / refuses-to-dramatize). Confirm template before launch.
- **TA-2:** Anonymous-founder posture vs Clerk's "company name" requirement — Rodc to decide whether to register Clerk as `Rodix` (LLC), as a personal account under pseudonym, or via Stripe Atlas LLC entity (cross-coordinated with `#b-paddle`).
- **TA-3:** Google OAuth off-by-default at Phase 1 vs available — confirm decision; default recommendation is hidden until Phase 2 to keep auth surface minimal.

## 11. Implementation outline (high-level, not implementer-ready)

1. Create Clerk account; configure Inter font + amber accent in Clerk dashboard.
2. Add Clerk JWT verification middleware to `app/web/server.py` request layer.
3. Add `auth_user_id` column to user-scoped tables (cross-coord with `#b-multitenant`).
4. Wire magic-link flow into landing page sign-in CTA; hide Google OAuth toggle behind feature flag.
5. Migrate Wave 1b single-user vault → first authenticated user's vault (cross-coord with `#b-multitenant` migration).

## 12. Risk register

1. **Clerk pricing/AUP shift** — medium probability over 24mo; mitigated by export-based migration plan above.
2. **Magic-link deliverability** — Clerk uses SendGrid by default; corporate email filters can drop magic links. Alpha-tester support email channel must surface this. Mitigation: monitor Clerk delivery metrics first 2 weeks post-launch.
3. **Founder anonymity exposure via Clerk billing** — Clerk dashboard requires payment method when upgrading from free; tied to `#b-paddle` LLC registration timing. Risk: Rodc forced to upgrade before LLC ready.
