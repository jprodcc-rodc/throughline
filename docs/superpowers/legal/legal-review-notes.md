# Legal review notes — self-review (Lens 4 hard challenge)

> **Author:** legal-drafter (Tier 2 Task 8). **Date:** 2026-05-03. **Status:** Self-review against five legal-exposure stress tests, before lawyer pass. This is anti-spin discipline (brand-book §7 Decision 6) applied to legal drafting: name what the drafts do *not* defend against, and recommend specific edits.
>
> Companion to `privacy-policy-draft.md` (PP) and `terms-of-service-draft.md` (ToS). Drafts are at v0.1.

## Stress test 1 — Crisis disclosure exposure

**Question.** If a user discloses risk of self-harm or harm to others in a Rodix conversation, and a related real-world incident occurs, and a plaintiff (the user, family, or another harmed party) sues us alleging that Rodix's response to the disclosure was negligent or harmful — which clause defends us, and is it strong enough?

**Verdict.** Defended in three clauses, but the defence is **weaker than it should be** for the period before Wave 1c ships.

**The defending clauses.**

- ToS Section 8 (Disclaimers): "AI replies are not professional advice… Rodix is not a therapy product… If you are experiencing a mental-health crisis, please reach out to a qualified professional… **The crisis-content protocol referenced in Section 14 of the Privacy Policy is intended to surface these resources within the product; its full implementation is planned for a near-term release. Until that release ships, do not rely on Rodix to detect or respond to a crisis.**"
- PP Section 14 (Crisis content): documents intent and resources (988, Crisis Text Line); explicitly notes implementation gap.
- ToS Section 9 (Limitation of liability): caps damages at fees paid in last 12 months or USD $100, whichever greater.

**Why the defence is weaker than it should be.**

1. The "do not rely on Rodix to detect or respond to a crisis" sentence is honest but is essentially an admission that the product surface can produce harmful behaviour. A plaintiff's lawyer will read it as "Rodix knew it had this gap and shipped anyway." That can cut against the defendant in negligence theory (foreseeability + reasonable care).
2. Section 9's liability cap is enforceable against contract-based claims but not always against tort claims for personal injury, especially when the alleged harm is to a third party (e.g., user discloses intent to harm another, harm occurs, the harmed party sues). California, Texas, and several state-courts have weakened liability caps in negligence cases involving foreseeable harm.
3. The Garcia v. Character.AI line of cases is shifting the law. Plaintiff theories include negligent design and failure-to-warn. A waiver-of-warning sentence may not insulate against design-claim theories.

**Recommended edit (P0).** Add to ToS Section 8, between the existing crisis paragraph and the "AI replies may be wrong" paragraph, an explicit assumption-of-risk acknowledgement:

> *"You acknowledge that the service is a thinking partner, not a crisis-response system. By using Rodix, you assume the risk that the AI may produce content that is incorrect, unhelpful, or potentially distressing in moments of crisis. You agree to seek qualified professional help and emergency services as appropriate without relying on Rodix to do so for you."*

This is a contract-level assumption-of-risk plus an affirmative duty on the user's side. It does not eliminate negligence-theory exposure, but it strengthens the contract-claim defence and provides a clear waiver-of-reliance for negligence-theory analysis.

**Recommended edit (P1).** Ship Wave 1c crisis-content protocol *before* publishing this policy. The protocol-clause-without-protocol gap is the single largest legal exposure flagged in this review. Per Escalation #2: this is a P0-or-fast-follow decision Rodc must make. Recommendation: **ship crisis-protocol with Phase 1 alpha. The legal review confirms what brand review already concluded.**

## Stress test 2 — EU resident slips through geo-block

**Question.** If an EU resident (Germany, France, etc.) bypasses the Cloudflare geo-block via VPN or location spoofing, signs up, and a German DPA later receives a complaint (theirs or about them), what is our exposure to a GDPR fine, and which clause limits it?

**Verdict.** Exposure is limited but **not eliminated**. The geo-block + signup attestation is defence-in-depth, not zero-exposure.

**The defending mechanisms.**

- PP Section 16 (Geographic availability): explicit statement that Phase 1 is not available to EU residents; geo-block enforced at Cloudflare WAF; signup asks for country of residence; we ask EU residents not to bypass via VPN.
- ToS Section 4 (Acceptable use): EU residency is a violation of acceptable use during Phase 1.
- The non-establishment defence under GDPR Art. 3: Rodix does not target the EU market. This is the substantive defence.

**Why the defence is meaningful but not airtight.**

1. GDPR Art. 3(2) extends scope to controllers outside the EU "where the processing activities are related to the offering of goods or services… to such data subjects in the Union" — irrespective of payment. The CJEU has read "offering" broadly. A solo VPN user is the easy case (probably no establishment); systematic bypass that we know about and don't act on is the hard case.
3. Once an EU resident's data lands in our systems, GDPR rights attach to them regardless of how they got the service. So the practical question is: do we have the operational capacity to honour Art. 15-22 rights for the EU resident who slipped through? The answer is yes, because PP Section 8 grants all rights to all users.
4. A maximum GDPR fine is the higher of €20M or 4% of global annual turnover. For a Phase 1 alpha startup with no revenue, the practical cap is €20M, but for negligible-scale violations the fines are typically much lower (€10k–€500k for SME-scale incidents per recent enforcement data).

**Recommended edit (P1).** Strengthen the geo-block discipline language in PP Section 16:

> *"If we discover that an account is held by an EU resident, we will close the account and delete the data within 30 days. To avoid this, please confirm your country of residence accurately at signup."*

This shifts the operational discipline (closing the account on discovery) from implicit to explicit. The reason: a complaint to a DPA is far more defensible if our policy commits us to the discovery-and-shutdown remedy.

**Recommended edit (P2).** Consider adding to ToS Section 4 explicit indemnification language for the EU-bypass case: if a user misrepresents residence and we incur a fine, the user indemnifies. Section 10 already covers this in general terms; making it explicit for this specific case is a marginal strengthening with low downside.

## Stress test 3 — Anthropic ZDR / training-data accuracy

**Question.** PP Section 12 asserts "We do not use your conversations to train any model. Anthropic does not use customer API inputs to train its models per their public commercial terms." Is this language accurate, or is it wishful?

**Verdict.** **Wishful in two specific places**, plus one TODO.

**Where it is accurate.**

- "We do not use your conversations to train any model" is accurate for Rodix-the-controller. We have no training pipeline. We have no plan to build one. This sentence is defensible.
- "Anthropic does not use customer API inputs to train its models per their public commercial terms" — Anthropic's public commercial terms (as of training cutoff) do commit to this for API customers; this is verifiable via Anthropic's published policy. The sentence is broadly accurate but deserves a citation footnote linking to the specific Anthropic policy version.

**Where it is wishful.**

1. The 30-day Anthropic retention window is currently the policy default, not Zero Data Retention. The draft acknowledges this in TODO brackets but the live published version must either (a) confirm ZDR is enrolled and use the ZDR sentence, or (b) honestly disclose 30-day retention. The draft cannot ship in TODO state.
2. "OpenRouter" sub-processor risk is under-discussed. OpenRouter is a routing layer; it has its own retention policies and data-handling practices that have not been audited in this draft. PP Section 5 lists OpenRouter as a sub-processor but does not characterise their retention. **OpenRouter's data policy must be verified** before publication; if OpenRouter retains any inference content longer than transit duration, the policy must disclose that.

**Recommended edit (P0).** Replace the bracketed TODO in PP Sections 5, 12, and 20 with one of two confirmed states before publication:

- **State A (ZDR confirmed):** "We have enrolled in Anthropic's Zero Data Retention programme. Under this agreement, Anthropic processes your inference inputs and outputs only for the duration of the request and does not retain them for abuse-monitoring or other purposes. Verified [date]."
- **State B (ZDR not confirmed):** "Anthropic's default API retention is 30 days, applied for abuse-monitoring purposes per their public commercial terms. We have not yet enrolled in their Zero Data Retention programme; enrollment is a roadmap item. We disclose this rather than imply otherwise."

Either is defensible. The TODO state is not.

**Recommended edit (P1).** Add OpenRouter retention disclosure to PP Section 5. If OpenRouter retains nothing past transit, say so. If they retain logs or metadata, say so and characterise.

## Stress test 4 — Sensitive personal data clause strength

**Question.** PP Section 11 (sensitive personal information) is the clause that distinguishes Rodix's policy from a generic SaaS template. Is it the strongest version, or has it drifted toward boilerplate?

**Verdict.** **Stronger than boilerplate, but two specific weaknesses worth fixing.**

**Strengths.**

- Names the categories explicitly (mental health, relationships, sexual orientation, political views) rather than hiding behind "sensitive categories."
- Treats all conversational content as sensitive by default. This is brand-coherent and operationally simpler than maintaining a per-category classifier.
- Names the heightened-protection commitments concretely (no training, no third-party advertising use, minimised access, encrypt at rest in Wave 3).
- States explicit consent as the GDPR Art. 9 lawful basis.

**Weaknesses.**

1. **The "explicit consent" mechanism is procedurally weak.** GDPR Art. 9(2)(a) requires "explicit consent" — case law has read this strictly to mean a clear affirmative action, not a buried "by using the service you consent" clause. A signup checkbox specifically for sensitive-data consent is the gold standard. The draft as written relies on continued use as consent, which is enforceable for ordinary processing but contested for special-category data.
2. **The data minimisation commitment is qualitative rather than concrete.** "We minimise the number of people who have access to production data" is true but vague. A plaintiff's lawyer will probe "how many?" and "what audit logs prove this?"

**Recommended edit (P0 — specific to EU service when Phase 2 launches).** Add explicit consent mechanism. This is moot at Phase 1 (EU geo-blocked), but is a Wave 3+ requirement when EU service ships:

> *"At signup, EU and EEA residents will be asked to provide explicit, separate consent to the processing of conversational content that may contain special-category data under GDPR Art. 9. This consent is granular, separable from the main service-acceptance consent, and revocable. Phase 1 alpha is geo-blocked to non-EU users; this clause becomes operative in Phase 2."*

**Recommended edit (P1).** Tighten the access-control commitment in PP Section 11:

> *"Access to production conversational data is limited to operational staff with documented need-to-know; access events are logged in an immutable audit trail. At Phase 1 alpha the operational staff is the founder only. As the team grows, access roles will be documented and access logs reviewed quarterly."*

This converts "we minimise access" from rhetoric into a verifiable operational commitment.

## Stress test 5 — Hidden risk

**Question.** Is there anything in these documents that creates a problem we don't yet see?

**Verdict.** Three latent issues worth naming.

**Issue 1 — The "we do not contact authorities" sentence in PP Section 14.**

> *"We do not contact emergency services or other authorities on a user's behalf except where required by law (such as mandatory-reporting obligations in some jurisdictions). We comply with applicable law."*

**Risk.** This sentence is brand-coherent (anti-spin, no Caregiver register, no surveillance posture) and accurate today. But it commits us to an operational stance that has unintended consequences.

- Some US states (e.g., California, Texas) have mandatory-reporting statutes for licensed professionals; Rodix is not licensed, so these don't directly apply, but a court could in principle find an analogous duty. The "we comply with applicable law" tail covers this, but a plaintiff's lawyer can use the prior sentence to argue we held ourselves out as not-a-mandatory-reporter when actually a duty existed.
- The sentence could be read as a *promise* to users that we will not act, which then becomes inculpatory if we *do* act in a borderline case.

**Recommended edit (P2).** Soften to:

> *"We do not, as a default, contact emergency services or other authorities on a user's behalf. In rare cases where applicable law requires us to do so, or where we believe in good faith that there is an imminent threat of serious harm, we may report. Any such report is consistent with our commitment to minimise data sharing and comply with applicable law."*

This preserves the brand register (default position is non-reporting) while reserving the discretion that any reasonable controller needs.

**Issue 2 — The 14-day refund commitment in ToS Section 7.**

> *"If you are dissatisfied with a paid subscription, write to `support@rodix.app` within 14 days of the charge and we will refund the most recent charge."*

**Risk.** This is a generous, brand-coherent commitment but creates a contractual obligation that exceeds what the merchant of record (Paddle / Polar) may automatically support. If the MoR's billing flow does not support 14-day refunds out of the box, we have promised something we cannot operationalise without manual intervention.

**Recommended edit (P1).** Confirm with `#b-paddle` deploy spec that 14-day refunds are operationally feasible. If not, change to "within 7 days" (Paddle and Polar both support 7-day automatic refunds on most plans).

**Issue 3 — Latent training-data IP exposure.**

PP Section 12: *"We could in principle train our own model on your data; we don't, because the brand-coherent posture is that your thinking is yours, and the model is interchangeable."*

**Risk.** This sentence is rhetorically strong (anti-spin, brand-on-voice), but a future product change — e.g., shipping fine-tuned embeddings from user data, building a recommender model from card-graph patterns — would be a material policy change requiring user notice. The sentence is currently honest, but it locks future product decisions into a notification cycle.

**Recommended edit (P2).** Either soften to preserve product flexibility:

> *"As of this policy's effective date, we do not train any model on your data. If we ever consider a change to this commitment, we will provide notice and obtain consent before doing so."*

Or — and this is the brand-coherent option — keep the strong sentence and accept the lock-in. The brand value of the strong sentence outweighs the future-flexibility cost. **Recommendation: keep the strong sentence.** Brand-book §7 Decision 5 (null-by-default) and Decision 6 (anti-spin) both support keeping the sentence and treating it as a load-bearing commitment.

---

## Summary — priority order

**P0 (must fix before publication):**

1. Crisis-content clause: ship Wave 1c protocol, *or* revise PP Section 14 + ToS Section 8 to a more defensible state. Add assumption-of-risk language to ToS Section 8 (Stress test 1).
2. Anthropic ZDR confirmation: replace TODO bracket with one of two confirmed states (Stress test 3).
3. EU-resident discovery-and-shutdown clause in PP Section 16 (Stress test 2).

**P1 (must fix before paid launch):**

4. OpenRouter retention disclosure (Stress test 3).
5. Explicit consent mechanism for EU sensitive-data consent at Phase 2 (Stress test 4).
6. Operational access-control language in PP Section 11 (Stress test 4).
7. Refund window operational-feasibility check with `#b-paddle` (Issue 2).

**P2 (lawyer-review item):**

8. Soften "we do not contact authorities" sentence (Issue 1).
9. Lawyer review of all liability and indemnification clauses (ToS Sections 9, 10).
10. Decision on arbitration / class-action-waiver clauses (ToS Section 12).

---

## Anti-spin discipline check

Brand-book §7 Decision 6 commits to: "*we never claim zero-knowledge or end-to-end encryption when Wave 1b reality is server-side recall with at-rest plaintext.*"

Anti-spin discipline holds across both drafts:

- PP Section 10 honestly discloses at-rest plaintext at Phase 1, with Wave 3 SQLCipher hardening as the roadmap commitment.
- PP Section 13 explicitly states "even after Wave 3 ships, Rodix will *not* be zero-knowledge."
- PP Section 20 enumerates the not-claims: not end-to-end encryption, not (yet) Zero Data Retention, not a therapy product, not full crisis-detection.
- ToS Section 8 explicitly disclaims professional-advice replacement and crisis-response capability.
- The friends-intro language "your data, your file" is preserved as the actual ownership story (markdown export), not subordinated to encryption claims.

The honest-disclosure register that Rodc set in the friends-intro is preserved across all 20 policy sections and 17 ToS sections. The single residual anti-spin risk is the crisis-content clause (PP Section 14) — which is honest about its implementation gap but creates legal exposure. **The anti-spin discipline and the legal-defence interest pull in the same direction here: ship Wave 1c, then tighten the clause.** Brand and legal converge on the same recommendation.

---

*End legal-review-notes.md. Next file: legal-decisions.md.*
