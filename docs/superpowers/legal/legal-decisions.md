# Legal decisions — TODO list for Rodc

> **Author:** legal-drafter (Tier 2 Task 8). **Date:** 2026-05-03. **Status:** Items Rodc must resolve before publishing the privacy policy and terms of service. Each item lists: what it is, why it blocks publication, the recommended default, and the cost of getting it wrong.
>
> Companions: `privacy-policy-draft.md` (PP), `terms-of-service-draft.md` (ToS), `legal-review-notes.md` (self-review).

## P0 — Must close before any public publication

### 1. Anthropic Zero Data Retention status

**What.** PP Sections 5, 12, and 20 contain a load-bearing claim about Anthropic's retention of inference inputs. The draft brackets it as a TODO. Either Rodix is enrolled in Anthropic's ZDR programme (then we say so), or it is not (then we honestly disclose 30-day retention).

**Why this blocks publication.** This is the most legally exposed claim in the policy. Saying "we have ZDR" when we don't is a material misrepresentation. Saying nothing leaves the user without information GDPR Art. 13(1)(e) requires (recipients of personal data + retention periods).

**Recommended default.** Verify ZDR status before publishing. If Rodix's commercial tier qualifies for ZDR, enrol; the cost is typically reduced via Anthropic's Pro / Enterprise tiers. If ZDR is unavailable at Phase 1 alpha pricing, disclose 30-day retention honestly; this is brand-coherent (anti-spin Decision 6) and will not surprise users who read the friends-intro.

**Cost of getting it wrong.** Material misrepresentation in a privacy policy is actionable under FTC §5 (US) and equivalent under most national consumer-protection regimes. Practical cost at Phase 1 alpha scale: low-probability of FTC action, moderate-probability of Anthropic relationship damage if our policy misrepresents their terms.

**Action item:** Rodc to contact Anthropic sales (`sales@anthropic.com`) to confirm ZDR eligibility for Rodix's tier. **Lead time: 1-3 days.** **Block:** PP cannot ship until this is closed.

### 2. Crisis-content protocol implementation status

**What.** PP Section 14 and ToS Section 8 contain crisis-content-handling language. The clauses describe intent and resources (988, Crisis Text Line) but explicitly note that the protocol implementation (Wave 1c) has not yet shipped.

**Why this blocks publication.** Per `legal-review-notes.md` Stress test 1, this is the single largest legal-exposure point in the documents. Per Escalation #2, this is also the single largest brand-vs-product gap. Brand and legal converge on the same recommendation: **ship Wave 1c before publishing the policy**, or accept assumption-of-risk language in the ToS that acknowledges the gap explicitly.

**Recommended default.** Ship Wave 1c crisis-content protocol with Phase 1 alpha. The protocol scope is in Escalation #2: detection trigger (intent classifier extension with `safety` category), resource scope (988 + Crisis Text Line + 1-sentence "this isn't what Rodix is built for"), register (matter-of-fact, non-Caregiver), escalation path (warm refresh button, no continuation of crisis-toned thread). Phase 1 alpha cannot ship without this.

**Cost of getting it wrong.** A Phase 1 alpha launch with no crisis protocol exposes Rodix to (a) negligent-design claims under the Garcia v. Character.AI line of cases, (b) brand-integrity damage if the first crisis user encounters Caregiver register, (c) regulatory attention if a serious incident occurs. The expected value of shipping protocol vs not is heavily skewed toward shipping.

**Action item:** Rodc + CC to scope and ship Wave 1c crisis-content protocol. **Lead time: 3-5 days for protocol + 1 day for policy clause refinement.** **Block:** PP and ToS should not ship before Wave 1c, *or* the clauses must be revised to a "future implementation" framing with explicit assumption-of-risk language per Stress test 1 P0 recommendation.

### 3. Legal entity name + jurisdiction

**What.** PP Section 1 and ToS Sections 1 and 12 reference the legal entity name and governing-law jurisdiction. The draft brackets these as TODO pending US LLC registration.

**Why this blocks publication.** A privacy policy and ToS without a named controller / contracting entity is unenforceable as a contract and non-compliant under GDPR Art. 13(1)(a). Cannot publish without this.

**Recommended default.** Per `#b-paddle` Type-A escalation TA-1 + TA-2: Delaware LLC via Stripe Atlas, named "Rodix LLC" unless founder anonymity posture demands a holding-entity layer. Wyoming LLC is the alternative if shielded ownership is the higher priority. Both add ~$300/yr ongoing cost; Wyoming is the privacy-preferring choice.

**Cost of getting it wrong.** A wrong jurisdiction choice creates portability cost (re-form in correct jurisdiction, update all policies, notify users — moderate operational cost but recoverable). A wrong-or-missing entity name is non-compliant and ships an unsigned contract.

**Action item:** Rodc to (a) decide on jurisdiction (Delaware vs Wyoming vs other), (b) initiate Stripe Atlas registration. **Lead time: 2 weeks for LLC formation.** **Block:** PP and ToS cannot publish before LLC entity is named; alpha launch can ship with placeholder if Rodc accepts the risk that early-alpha users would need to re-accept upon LLC formalisation.

### 4. Founder anonymity posture vs LLC public records

**What.** Per `#b-paddle` Type-A escalation TA-2: LLC formation creates public records exposing ownership in many jurisdictions. The friends-intro framing "Solo, anonymous, working out of Asia" is in tension with this. Mitigation options: Wyoming LLC with shielded ownership; holding-entity layer with nominee director.

**Why this blocks publication.** The privacy policy must name a controller; the ToS must name a contracting party; both will appear in WHOIS, in public LLC records, and in the live policy itself. Rodc cannot ship the public site as "Rodc" pseudonym only.

**Recommended default.** Wyoming LLC with shielded ownership (no member listing on state records). This preserves anonymity at the WHOIS / state-records level while satisfying contracting-entity requirements. Add ~$300/yr for registered agent + filing.

**Cost of getting it wrong.** Choosing Delaware (default) leaks founder identity via state registration database. Recoverable: re-form in Wyoming and re-file. Cost: ~$1k + 2-week delay.

**Action item:** Rodc to decide between Wyoming (shielded) vs Delaware (cheaper, more standard). Confirm with Stripe Atlas whether they support Wyoming. **Lead time: 1 day decision; 2 weeks formation.** **Block:** must close before LLC registration begins.

## P1 — Must close before paid launch

### 5. Lawyer review

**What.** Per `#b-privacy-policy` Type-A escalation TA-1: lawyer review at alpha (free) launch vs only at paid launch. The drafts in this directory are written to the standard of "as defensible as solo-founder-self-serve gets" (per task brief), not lawyer-grade.

**Why this matters.** Specific clauses that need lawyer eyes:
- ToS Section 9 (limitation of liability) — wording survives in some jurisdictions, fails in others.
- ToS Section 10 (indemnification) — scope and enforceability.
- ToS Section 12 (governing law + arbitration) — Delaware vs alternative; arbitration clause yes/no.
- PP Sections 6, 7, 11, 17 (cross-border transfers + Art. 9 SPI + retention) — GDPR-specific traps.

**Recommended default.** Lawyer review *required* at paid-launch readiness. Lawyer review *optional* at alpha if Rodc accepts the residual risk of self-written policy + 30-day grace + republish-on-discovery. Budget: $2k for one-time review with a US/UK SaaS-experienced privacy lawyer (Stripe Atlas referral network is the start point).

**Cost of getting it wrong.** Self-written policy missing a clause specific to a user's jurisdiction → moderate probability of complaint, low probability of fine at Phase 1 alpha scale. Lawyer-reviewed policy reduces this to negligible.

**Action item:** Rodc to engage privacy lawyer 4-6 weeks before paid launch. **Lead time: 2-4 weeks for review.** **Block:** paid launch cannot proceed without; alpha launch can proceed without (with residual risk acknowledged).

### 6. DPO contact decision

**What.** PP Section 19 references DPO contact. Phase 1 EU geo-block reduces but does not eliminate DPO need (a Swiss user, a UK user, a non-EU user under similar regulatory scope still triggers data-protection contact obligations).

**Why this matters.** GDPR Art. 37 requires a DPO when core activities involve large-scale processing of special-category data. Rodix's product surface arguably qualifies; lawyer review will opine. CCPA does not require DPO but does require contact for privacy requests.

**Recommended default.** No formal DPO at Phase 1 alpha. Privacy email (`privacy@rodix.app`) routed to founder inbox; auto-acknowledge within 24 hours; resolve within 30 days. When EU service ships (Phase 2+) or scale exceeds ~5k users, formal DPO appointment.

**Cost of getting it wrong.** Missing DPO when required is a GDPR violation but typically results in advisory rather than fine for SME-scale. Recoverable: appoint DPO retroactively.

**Action item:** Rodc to confirm Phase 1 alpha DPO posture (founder-as-contact). **Block:** none for alpha; required before EU service launch.

### 7. Cookie list final review

**What.** PP Section 9 lists cookies. Draft assumes Clerk auth `__session` + Cloudflare `__cf_bm` only. The actual cookie list at deploy time may differ.

**Why this matters.** Cookie disclosure is a GDPR + ePrivacy Directive requirement. CCPA also requires disclosure of tracking technologies. Mis-stating the cookie list is a policy-accuracy violation.

**Recommended default.** Verify cookie list at deploy time (after `#b-auth` and `#b-deploy` ship). Update PP Section 9 to match. Add cookie banner if the list grows beyond strictly-necessary cookies.

**Cost of getting it wrong.** Low for Phase 1 alpha (geo-blocked EU; CCPA requires disclosure but no opt-in for non-tracking cookies). Moderate for Phase 2 (EU service requires cookie consent banner if non-essential cookies are introduced).

**Action item:** Rodc + CC to verify cookie list before publishing. **Lead time: 1 hour audit. Block:** must close before publication.

### 8. Refund window operational feasibility

**What.** ToS Section 7 commits to 14-day refund window. Per `legal-review-notes.md` Issue 2, Paddle and Polar may not support 14-day refunds out of the box without manual intervention.

**Why this matters.** Promising what the operational stack cannot deliver creates false-promise exposure under consumer-protection law.

**Recommended default.** Confirm Paddle / Polar refund window capability. If 14-day requires manual intervention, either accept the operational cost or shorten the contractual window to 7 days.

**Cost of getting it wrong.** Low — a missed refund commitment is a customer-service issue more than a legal one. Recoverable by amendment.

**Action item:** Rodc + CC to confirm via `#b-paddle` deploy-spec validation. **Block:** none for alpha (free); must close before paid launch.

### 9. OpenRouter retention disclosure

**What.** PP Section 5 lists OpenRouter as a sub-processor but does not characterise their retention policy. Per `legal-review-notes.md` Stress test 3 P1.

**Why this matters.** GDPR Art. 13(1)(e) requires disclosure of recipients; sub-processor data handling must be characterised.

**Recommended default.** Audit OpenRouter's data policy. If they retain nothing past transit, state so. If they retain logs, characterise.

**Action item:** Rodc + CC to read OpenRouter's privacy policy at `https://openrouter.ai/privacy` and update PP Section 5. **Lead time: 1 hour.** **Block:** must close before publication.

## P2 — Items for later iteration

### 10. Trademark registration status

**What.** ToS Section 6 references Rodix as a trademark. Registration status is unconfirmed.

**Why this matters.** Without registered trademark, "Rodix" is a common-law mark in jurisdictions that recognise common-law marks (US) but offers thinner protection elsewhere. Phase 1 alpha can ship without registered mark; brand defence at scale benefits from registration.

**Recommended default.** File US trademark via USPTO ($350 + ~$1k attorney fee) when LLC entity is in place. International trademark (Madrid Protocol) when Phase 2+ international scope is committed.

**Action item:** Rodc to budget trademark filing for Phase 2.

### 11. Arbitration / class-action-waiver clause

**What.** ToS Section 12 brackets a TODO for arbitration / class-action-waiver decision. US SaaS norm is to include arbitration + waiver; brand register may push toward simpler, court-of-Delaware language.

**Why this matters.** Arbitration + class-action-waiver clauses limit class-action exposure; their enforceability varies by jurisdiction. Some plaintiffs' lawyers refuse to take cases against products with strong arbitration clauses, which is a real defensive benefit.

**Recommended default.** Include arbitration + class-action-waiver clause, with a 30-day opt-out window for new users (this is the JAMS / FAA-friendly pattern). Lawyer review will opine on specific wording.

**Action item:** Rodc to confirm with privacy lawyer at the lawyer-review pass.

### 12. Founder signature format

**What.** ToS Section 17 closes with a founder signature. Phase 1 alpha posture is "Rodix Team" or pseudonym; paid-launch posture transitions to LLC entity.

**Recommended default.** "Rodix Team" at Phase 1 alpha; "Rodix LLC" at paid launch.

**Action item:** Rodc to decide signature format once anonymity-vs-LLC decision is made (item 4 above).

### 13. Policy archive routes

**What.** PP Section 18 and ToS Section 13 commit to archive routes (`rodix.app/legal/privacy/archive` and `rodix.app/legal/terms/archive`).

**Why this matters.** Material-change notification flows require users to be able to compare current and prior versions.

**Action item:** CC to implement archive routes per `#b-privacy-policy` deploy-spec implementation outline.

## Type-A escalations to lift to Rodc / Opus

The drafts surface **one new Type-A escalation** beyond Escalation #2 (already documented):

### TA new — Anonymous-founder posture vs ToS-Section-17 founder-signature

The friends-intro framing "Solo, anonymous, working out of Asia" is brand-coherent. Phase 1 alpha can hide the founder behind "Rodix Team." But:

- LLC public records (item 4 above) will eventually surface ownership.
- ToS Section 17 will eventually carry a real-name signature when LLC formalises.
- Privacy policy contact (`privacy@rodix.app`) is a routed inbox; the human behind it can be pseudonymous at first but eventually requires a real-name DPO contact for Phase 2 EU service.

**Question for Rodc:** Is the anonymity posture a Phase 1 alpha decision (acceptable to drop at LLC formalisation) or a long-term brand commitment (requires Wyoming-LLC + nominee-director architecture and ongoing operational discipline)?

**Default chosen by drafter:** Phase 1 alpha allows pseudonym; Phase 2 paid launch requires named LLC and (depending on jurisdiction reach) named DPO. Wyoming-LLC + shielded ownership is the privacy-preferring path that delays disclosure but does not eliminate it.

**Recommended action.** Rodc to decide between (a) drop anonymity at LLC formalisation, accept named LLC and named DPO at Phase 2, or (b) commit to long-term anonymity, invest in Wyoming + nominee architecture, accept the ~$300/yr ongoing cost. Decision drives several downstream items: ToS Section 17 wording, PP Section 19 DPO contact, founder-essay positioning, HN-post identity reveal.

This escalation is Type-A because it intersects brand strategy, legal strategy, and product launch posture.

---

*End legal-decisions.md.*

*Drafter sign-off: legal-drafter (Tier 2 Task 8). Drafts at v0.1. Anti-spin discipline holds across both drafts (verified in `legal-review-notes.md`). Three P0 items (Anthropic ZDR, Wave 1c crisis protocol, LLC entity name) block publication. Lawyer review required before paid launch. Recommended next step: Rodc closes P0 items in priority order.*
