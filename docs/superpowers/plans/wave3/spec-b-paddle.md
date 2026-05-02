# `#b-paddle` — Paddle primary + Polar.sh fallback billing architecture

> **Status:** Strategic-design depth (not implementer-ready). Wave 3 dossier. Author: wave3-plan-architect. 2026-05-03. **CRITICAL PATH BLOCKER for paid launch.**

## 1. Goal

Phase 1 paid launch (Wave 3): a Merchant-of-Record billing layer that handles VAT / sales tax / refunds across 200+ countries on behalf of Rodc, who as a solo-anonymous-founder-from-Asia cannot personally register for sales tax in every US state, every EU member state (already geo-blocked), and every Asian jurisdiction. Polar.sh as fallback if Paddle approval delays exceed launch tolerance.

## 2. Strategic context

Friends-intro voice: "Solo, anonymous, working out of Asia, second half of a multi-year build" — this status is brand-trust positioning, but it intersects badly with US sales-tax compliance (Wayfair v. South Dakota: any seller with >$100k revenue or >200 transactions in a state owes sales tax there). Merchant-of-Record vendors absorb this exposure. The decision is not "MoR or not"; it's "which MoR, and what fallback if approval delays."

## 3. Design options

(a) **Paddle as MoR, primary** — handles VAT, sales tax, refunds, chargebacks across 200+ countries. Webhook-based subscription lifecycle. AUP review for new accounts is 2-4 weeks (Paddle vets sellers; anonymous-founder posture may extend review). Reputation: established (10+ years), used by Linear / Notion / RevenueCat. 5% + $0.50 per transaction.

(b) **Polar.sh as MoR** — newer (2024) but founder-friendly, Stripe-backed, faster onboarding (2-5 days). Lower fee: 4% + $0.40. AUP more lenient. Risk: smaller, less reputation, fewer enterprise integrations; could pivot or shut down.

(c) **Stripe direct** (not MoR) — Rodc personally responsible for tax registration globally. **Reject** for solo-anonymous-founder posture; the legal exposure is incompatible with §6 Constraints in `position-strategy.md`.

(d) **LemonSqueezy** — MoR, similar to Paddle, comparable fees, comparable onboarding time. Reasonable alternative to Polar but smaller community.

## 4. Recommended approach

**Paddle as primary, Polar.sh wired as fallback.** Webhook handlers standardized on a *subset of fields both vendors support*: `subscription.created`, `subscription.updated`, `subscription.canceled`, `payment.succeeded`, `payment.failed`. Both vendors emit these (with vendor-prefixed payload shapes). Application code dispatches on a normalized event format; vendor-specific adapter translates incoming webhook → normalized event.

Rationale: Paddle is the default because mature; Polar fallback exists as a contingency if Paddle AUP review delays Phase 1 paid launch by >4 weeks.

## 5. Vendor / tool choice

**Paddle** at `paddle.com`. Lock-in: medium-high. Customer subscription IDs are vendor-issued (cannot be ported to a different MoR without customer-side action — e.g., re-subscribe under new payment processor). Migration path exists but requires 2-4 weeks of dual-write + customer notification.

**Polar.sh** at `polar.sh`. Stripe-backed (Polar uses Stripe Connect under the hood); subscription IDs are Polar-issued. Migration similar to Paddle.

## 6. Legal / compliance audit

US sales tax: MoR absorbs full liability. Rodc not personally registered in any US state. EU VAT: Rodix is geo-blocked at Cloudflare for EU users; MoR also handles VAT in non-blocked European countries (Switzerland, UK, Norway). UK VAT MOSS: handled by MoR. Asian jurisdictions (Singapore GST, India GST, Japan JCT): MoR-handled. Card-network compliance (PCI-DSS): MoR is the merchant of record, not Rodc.

**Critical disclosure for `#b-privacy-policy`:** payment data flows to Paddle/Polar, not stored by Rodix. Privacy policy must list Paddle/Polar as a data processor. Their respective DPAs must be on file.

## 7. Rollback / migration if vendor changes

If Paddle AUP delays >4 weeks: switch primary to Polar.sh. If Paddle terminates account post-launch: customer-side migration via "your subscription is moving, please re-confirm" email; estimated 30-50% revenue loss in transition month (industry baseline). Lock-in score: medium-high — the subscription-ID-portability problem is real.

## 8. Cost estimate

Phase 1 (≤1,000 users, ~100 paying at $10/mo = $1k MRR): **Paddle ~$60/mo fees** (5% + $0.50 × 100 transactions). At $10k MRR (~1k paying at $10/mo): **Paddle ~$600/mo fees**. Polar fallback would be ~$480/mo at same scale. MoR fees are the largest cost-per-user line item after AI inference; comparable to Stripe direct (2.9% + $0.30) but worth the tax-compliance offload.

## 9. Lead-time blockers

**Paddle AUP review: 2-4 weeks for new accounts.** This is THE critical path blocker for paid launch. Anonymous-founder posture may extend review; Rodc may need to disclose LLC entity (Stripe Atlas timing dependency).

**Stripe Atlas LLC formation:** ~2 weeks for Delaware C-corp / LLC; required for both Paddle account legitimacy and Polar fallback. **Paddle approval cannot start until LLC ready.** Total lead time from "today" to "paid launch": **6-8 weeks.**

## 10. Open decisions for Rodc (Type-A)

- **TA-1:** Stripe Atlas LLC formation — Delaware LLC vs Delaware C-corp vs other jurisdiction. Recommendation: Delaware LLC (lower complexity, no double-taxation, sufficient for solo founder). $500 Stripe Atlas fee + $300/yr ongoing.
- **TA-2:** LLC name — "Rodix LLC" vs pseudonymous holding entity. Brand-book locks product name `Rodix`; LLC name should match unless Rodc's anonymity posture demands holding-entity layer. **This is a significant Type-A decision** because LLC public records expose ownership.
- **TA-3:** Free-tier vs paid-only at Phase 1 launch. Brand-book §6 (position-strategy) constraints leave pricing TBD per Task 4. `#b-paddle` integration must support both free + paid; **Type-A:** Rodc to confirm pricing model before MoR product configuration.
- **TA-4:** Polar.sh as fallback — pre-register account in parallel with Paddle, even if not used initially? Recommendation: yes, register in parallel; warm fallback is cheap insurance against Paddle AUP delay.

## 11. Implementation outline (high-level)

1. **Pre-launch (parallel work, 4-6 weeks before paid launch):** Stripe Atlas LLC; Paddle account application; Polar.sh fallback account; bank account; tax DPA paperwork.
2. Webhook normalization layer: vendor-agnostic `BillingEvent` schema; Paddle adapter + Polar adapter both emit normalized events.
3. `app/web/server.py` `/billing/webhook` endpoint with vendor-specific signature validation.
4. Subscription state in `users` table: `subscription_status`, `current_period_end`, `vendor`, `vendor_subscription_id`.
5. Cancellation flow: grace period + dunning + read-only mode (vault export still works).

## 12. Risk register

1. **Paddle AUP rejects anonymous-founder application** — moderate probability. Mitigation: Polar warm fallback; Stripe Atlas LLC creates legitimate entity.
2. **Cross-vendor webhook drift** — Paddle and Polar emit slightly different lifecycle events; normalization layer must handle edge cases (chargebacks, partial refunds, currency changes). Test coverage critical.
3. **Subscription-ID portability** — locked-in by design. If Rodc must migrate post-launch, expect 30-50% transition-month churn. Mitigated by paid-launch only after MoR choice is final.
