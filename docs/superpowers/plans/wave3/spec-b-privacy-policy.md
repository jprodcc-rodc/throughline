# `#b-privacy-policy` — Privacy Policy + ToS publication, coordinated with Tier 2 Task 8

> **Status:** Strategic-design depth (not implementer-ready). Wave 3 dossier. Author: wave3-plan-architect. 2026-05-03.

## 1. Goal

Phase 1 alpha launch (Wave 3): publish the Privacy Policy + Terms of Service produced in Tier 2 Task 8, surface them at `/privacy` and `/terms` routes (Cloudflare-cached for performance), and ensure pre-launch checklist items close before any user signs up. This dossier is the *publication* + *legal-compliance audit* layer; Task 8 produces the body copy.

## 2. Strategic context

Friends-intro voice: "Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture). Encryption hardening on the post-launch roadmap. Export is plaintext markdown — that's the actual ownership story." The privacy policy must encode this honest disclosure, not the SaaS-default "your data is encrypted and never shared" generic. Brand-book §7 Decision 6 names this discipline as "anti-spin operationalized at the highest-stakes claim."

## 3. Design options

(a) **iubenda / Termly auto-generated policy** — $20-50/mo subscription, fill-in-the-blanks template. Reject: policy will read like SaaS-default; brand voice cannot accommodate template register; iubenda templates over-claim ("end-to-end encryption" boilerplate).

(b) **Custom hand-written policy reviewed by lawyer** — $1.5k-3k for a one-time review with US/UK-jurisdiction privacy lawyer. Accepts brand voice; brand-fit excellent.

(c) **Custom policy using friends-intro voice + open-source template (e.g., Standard Notes' policy as honest-disclosure precedent) + Tier 2 Task 8 copy** — Rodc plus CC iteration; no formal lawyer pass at Phase 1 alpha. Higher risk profile, lower cost.

## 4. Recommended approach

**Option (b) at Phase 1 paid launch; option (c) is acceptable at Phase 1 alpha (free) launch only.** Rationale: paid launch implies financial transaction → higher legal exposure → lawyer-reviewed policy is the only defensible posture. Alpha-only launch with no payment processing has lower exposure and supports option (c). Brand voice flows from Tier 2 Task 8; legal compliance flows from option (b) review. The two passes coexist: lawyer ensures GDPR / CCPA / state-privacy compliance; voice ensures brand fit; conflicts resolved in favor of lawyer on legal substance, in favor of voice on register.

## 5. Vendor / tool choice

- **Lawyer:** US/UK-jurisdiction privacy lawyer with SaaS startup experience. Stripe Atlas referral network is a starting point. Budget: $2k for one-time review + $500/yr for material updates.
- **Hosting:** static markdown rendered to HTML in `app/web/docs/privacy.md` + `app/web/docs/terms.md` (file paths exist). Cloudflare-cached.
- **DPO contact:** dedicated email (e.g., `dpo@rodix.app`); routed to Rodc's primary inbox at Phase 1.

Lock-in: zero. Policy text is plain markdown owned by Rodc.

## 6. Legal / compliance audit

**Pre-launch checklist (must close before any user signs up):**

- [ ] **LLC registration complete** (cross-coord `#b-paddle` Stripe Atlas LLC formation). Privacy policy entity name = LLC entity name. Anonymity-vs-LLC tension is a Type-A escalation (see TA-2 below).
- [ ] **Anthropic ZDR (Zero Data Retention) confirmed** — Anthropic API by default retains content 30 days for abuse monitoring; ZDR opt-in is available for Pro/Enterprise tiers. Verify Rodix's tier supports ZDR or document the 30-day retention in privacy policy. **TODO: web_fetch Anthropic's policy at launch readiness time.**
- [ ] **OpenRouter data policy reviewed** — OpenRouter is a routing layer; data flows through their infrastructure to underlying providers. Policy must list OpenRouter as a sub-processor and clarify routing.
- [ ] **DPO contact email** active + monitored: `dpo@rodix.app`.
- [ ] **Cookie disclosure**: at Phase 1 the only cookies are Clerk auth (`__session`, `SameSite=Lax`); Cloudflare may set `__cf_bm` for bot mitigation. List these.
- [ ] **Sub-processor list:** Clerk (auth), Paddle (billing), Anthropic (AI inference), OpenRouter (AI routing), Cloudflare (CDN+DNS+WAF), Railway/Hetzner (hosting), Sentry (error tracking).
- [ ] **GDPR exposure at edge:** EU geo-block at Cloudflare layer (`#b-deploy`) + user-declared residence at signup (dual-layer defense). Privacy policy explicitly states "Rodix does not target the EU; users from EU jurisdictions are routed-blocked at network layer."
- [ ] **Sensitive personal data:** Art. 9 GDPR categories (health / political / religious / sexual orientation) appear in conversational disclosures. Heightened-protection clauses required: explicit consent paragraph, retention policy, deletion path.
- [ ] **Crisis-content protocol disclosure:** if Wave 1c implements safety-resource banner (per `D1` in `assumption-list.md`), policy must disclose triggers + handling.
- [ ] **Children:** policy must state "13+ only" (US COPPA) or "16+ only" (GDPR aligned, even with EU geo-blocked). Recommendation: 16+ for safety margin.
- [ ] **Right-to-erasure path:** documented endpoint or email request route; cross-coord `#b-multitenant` (cascade DELETE on user_id).
- [ ] **Data portability path:** markdown export already shipped; document explicitly in policy.

## 7. Rollback / migration if vendor changes

Privacy policy is owned text; any vendor change (Clerk → custom JWT, Paddle → Polar, Cloudflare → other) requires sub-processor list update. Updates to material clauses require user notification (email) + 30-day grace before effective. Lock-in: zero.

## 8. Cost estimate

Phase 1 alpha (free): **$0** if option (c) self-written; **$500-2k** if option (b) lawyer review at alpha. Phase 1 paid launch: **$2k** lawyer review + $500/yr maintenance. At $10k MRR scale: same plus quarterly policy review ($1k/yr addtl).

## 9. Lead-time blockers

**Lawyer engagement: 2-4 weeks** for a thorough review. Schedule to overlap with `#b-paddle` AUP review window — the same lawyer can also opine on MoR contract terms. **LLC registration: 2 weeks** (Stripe Atlas). **Anthropic ZDR confirmation: 1-3 days** (sales contact). Total lead time from "today" to "publishable policy ready for paid launch": **~4 weeks**, parallelizable with `#b-paddle` AUP review.

## 10. Open decisions for Rodc (Type-A)

- **TA-1:** Lawyer engagement timing — review at alpha (free) launch or only at paid launch? Recommendation: paid launch; alpha can ship with self-written policy + brand-voice review.
- **TA-2:** **Anonymous-founder posture vs LLC public records.** LLC formation creates public records exposing ownership in many jurisdictions. Privacy policy entity name = LLC entity name. This is a real conflict with friends-intro "Solo, anonymous, working out of Asia" register. Possible mitigations: (i) Wyoming LLC has shielded ownership (no member listing on state records); (ii) holding-entity layer with nominee director. Both add ~$300/yr ongoing cost. Rodc must decide.
- **TA-3:** Anthropic ZDR — does Rodix pay for Pro/Enterprise tier to get ZDR, or accept default 30-day retention and disclose? Recommendation: ZDR if cost-feasible at Phase 1; otherwise disclose honestly per anti-spin discipline.
- **TA-4:** Crisis-content protocol Wave 1c implementation — privacy policy disclosure depends on whether Wave 1c ships before alpha. Recommendation: ship Wave 1c before alpha; policy disclosure follows automatically.

## 11. Implementation outline (high-level)

1. Tier 2 Task 8 produces brand-voice draft policy + ToS.
2. Lawyer engagement (Phase 1 paid only): 2-4 week review.
3. Reconcile lawyer markup with brand-voice draft; brand voice yields on legal substance, holds on register.
4. Render markdown to HTML; serve at `/privacy` and `/terms`.
5. Add policy version + last-updated date in footer.
6. Implement DPO email forwarding + auto-acknowledge (24hr SLA per GDPR best practice).
7. Document update-notification flow: email all users on material change + 30-day grace.

## 12. Risk register

1. **Self-written policy missing GDPR clause** — moderate probability if Rodc skips lawyer review at alpha. Mitigation: lawyer review at alpha-to-paid transition (worst case is 30-day grace + republish).
2. **Anthropic / OpenRouter sub-processor data residency** — both route through US datacenters; some users may object even with EU geo-block in place (e.g., Swiss user worried about US PATRIOT Act exposure). Disclosure mitigates; cannot eliminate.
3. **Sensitive personal data clause inadequate for Art. 9 categories** — lawyer must specifically opine on conversational-disclosure clause; if missing, Rodix faces heightened breach-liability.
