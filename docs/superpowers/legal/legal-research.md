# Legal research notes — Rodix Privacy Policy + ToS reference patterns

> **Author:** legal-drafter (Tier 2 Task 8). **Date:** 2026-05-03. **Status:** Reference for the privacy-policy and ToS drafts in this directory. Not a substitute for lawyer review.

## 1. Method

WebFetch was not used in this pass. Pattern reference is drawn from training knowledge of Anthropic / Notion / Linear / Mem privacy policies plus the public GDPR (Regulation (EU) 2016/679, Articles 4, 6, 9, 12-22, 32) and CCPA / CPRA (Cal. Civ. Code §1798.100 et seq.) statutory definitions. Specific items that require a live source check are flagged TODO in `legal-decisions.md` (Anthropic Zero Data Retention status is the load-bearing one).

## 2. Standard sections every defensible SaaS privacy policy carries

In rough rendering order: (1) identity of controller / "who we are"; (2) what categories of personal data are collected; (3) purposes and legal bases (GDPR Art. 6); (4) recipients / sub-processors; (5) international data transfers (GDPR Ch. V; SCCs / adequacy); (6) retention periods; (7) data-subject rights (GDPR Art. 15-22) plus CCPA equivalents (right to know, right to delete, right to correct, right to opt-out of sale/share, right to limit use of sensitive personal information); (8) cookies / tracking; (9) children; (10) security measures (Art. 32); (11) changes to policy + notification; (12) contact / DPO. Most well-written examples (Linear, Anthropic) collapse this into 8-10 actual headings rather than 12, with rights folded under one section.

## 3. Patterns worth borrowing

- **Linear:** plain-prose register; sub-processor list as a table linked from the policy rather than embedded; explicit retention-period column. Low ceremony, named processors, dated revisions in the footer.
- **Notion:** structured headings with anchor links; explicit "What we don't do" mini-section (no selling personal information, no using content to train ML models without opt-in). The negation block reads honestly because it is specific.
- **Anthropic:** clear separation between consumer products and API customers; explicit ZDR enrollment language; named jurisdiction (California, USA) with international transfer addendum.
- **Mem.ai (memory product, closest competitor analogue):** explicit "we don't read your notes" + explicit "embeddings are computed and stored, content is encrypted at rest" — Rodix cannot copy this verbatim because Wave 1b is not encrypted at rest. The honest equivalent is the Decision-6 disclosure.
- **Standard Notes:** the canonical "honest disclosure" reference. Names trade-offs in plain prose ("we are end-to-end encrypted, which means we cannot recover your password and we cannot help you if you lose access"). Rodix borrows the *register*, not the substance.

## 4. GDPR — points the policy must cover

- **Art. 4 personal data:** any information relating to an identified or identifiable natural person. Conversation transcripts that include names, locations, employers, family members, medical situations, or political views all qualify.
- **Art. 6 lawful basis:** Rodix's basis is contract (Art. 6(1)(b)) — processing necessary to provide the service the user signed up for — plus legitimate interest (Art. 6(1)(f)) for security and abuse-prevention telemetry. We do **not** rely on consent (6(1)(a)) for service operation, because consent that can be withdrawn is not a defensible basis for "the user's vault must keep working."
- **Art. 9 special-category data (the load-bearing point for Rodix):** "data revealing racial or ethnic origin, political opinions, religious or philosophical beliefs, or trade union membership, and the processing of genetic data, biometric data for the purpose of uniquely identifying a natural person, data concerning health or data concerning a natural person's sex life or sexual orientation." Mental-health disclosures, relationship disclosures, political views, sexual-orientation disclosures all land here. Processing is prohibited by default unless one of the exceptions in Art. 9(2) applies. For Rodix the relevant exception is Art. 9(2)(a): explicit consent. Therefore the policy must (i) name that conversations may contain such categories, (ii) treat them with heightened protection, (iii) make explicit that the user understands and consents to this processing as part of using the service.
- **Art. 12-22 rights:** transparency, access, rectification, erasure, restriction, portability, objection, automated-decision-making restrictions. Rodix grants all of these to all users (Phase 1 EU geo-block notwithstanding) because the operational cost of a single rights regime is lower than maintaining two parallel regimes.
- **Art. 32 security:** "appropriate technical and organisational measures." At-rest plaintext at Phase 1 alpha is honest disclosure; encryption at rest ships Wave 3 (`spec-b-encryption.md`).
- **Art. 33-34 breach notification:** 72-hour authority notification + user notification when high risk. The policy must state we will comply.
- **Art. 44-49 international transfers:** when data leaves the EU, an Art. 46 mechanism (Standard Contractual Clauses or adequacy decision) applies. Phase 1 EU geo-block reduces but does not eliminate exposure (a Swiss user's data flowing through US Anthropic still requires SCC-grade protection).

## 5. CCPA / CPRA — points the policy must cover

- **§1798.140 personal information:** broader than GDPR — includes inferences drawn about a consumer (e.g., a topic tag derived from conversation). Rodix's white-box card model surfaces these inferences to the user, which is brand-coherent.
- **§1798.140 sensitive personal information:** includes "personal information that reveals…racial or ethnic origin, religious or philosophical beliefs, or union membership," "the contents of a consumer's mail, email, and text messages…" — conversations to Rodix unambiguously qualify. Right to limit use of SPI applies.
- **§1798.100 right to know; §1798.105 right to delete; §1798.106 right to correct; §1798.110 right to know what is collected; §1798.120 right to opt-out of sale/share; §1798.121 right to limit SPI.** Rodix does not sell or share personal information, so the opt-out is moot but must be disclosed.
- **§1798.135 notice at collection:** the categories collected and the purpose must be disclosed at the point of collection (i.e., signup) — covered by linking the privacy policy from the signup form.
- **Children:** §1798.120(c) — opt-in for sale/share of minors under 16. Rodix does not sell, but the 16+ posture per spec-b-privacy-policy maps cleanly here.

## 6. Rodix-specific tension points

- **Server-side recall vs zero-knowledge claim.** Wave 1b architecture decrypts the vault server-side to run FTS5 + vec0 queries. Marketing copy must not say "encrypted" or "zero-knowledge" without qualifier. Brand-book §7 Decision 6 names this anti-spin commitment. Friends-intro: *"Server-side recall (so we can't promise zero-knowledge — that would be a lie given the architecture)."*
- **Anthropic ZDR.** Anthropic's API by default retains content for 30 days for abuse monitoring; ZDR is an opt-in feature on certain commercial tiers. Rodix's policy cannot assert ZDR unless ZDR is contractually in place. **TODO: Rodc must verify before publishing.** If not in place, the policy honestly discloses 30-day Anthropic retention.
- **OpenRouter routing layer.** OpenRouter is a sub-processor that routes requests onward to underlying providers. Both must appear in the sub-processor list, and the policy must clarify that requests pass through OpenRouter infrastructure before reaching Anthropic.
- **Sensitive personal data implicit in the product surface.** Rodix is built for thinking; thinking includes mental-health, relationships, political views. The policy cannot pretend conversations are generic — the heightened-protection clauses (Art. 9 GDPR / SPI CCPA) must be explicit.
- **Crisis-content protocol gap.** Per Escalation #2: brand-stance is fixed (graceful handoff, 988 + Crisis Text Line, no Caregiver register expansion); Wave 1c implementation has not yet shipped. The policy clause documents intent and resources and must use anti-spin register: do not claim full crisis-detection that is not yet implemented.

## 7. ToS standard sections

Acceptance, description of service, accounts and responsibilities, acceptable use, intellectual property, billing (when paid), termination, disclaimers (incl. AI content + mental health), limitation of liability, indemnification, governing law, changes. Linear and Notion both cap liability at fees paid in last 12 months or a small dollar floor; Rodix mirrors that pattern.

**AI-content disclaimer is not boilerplate.** Recent class-action exposure for LLM products (Hyperia v. OpenAI; Garcia v. Character.AI) is centered on harm flowing from AI output. The disclaimer must be specific: not professional advice in domains (medical / legal / financial / mental health), users should not rely on AI for life decisions, AI is a thinking partner not a substitute for qualified professionals.

**Mental-health disclaimer must be specific.** Generic "consult a professional" is not enough; the clause must name the product limit (Rodix is for thinking, not therapy), name the user obligation (seek professional help in crisis), and gesture at resources (988 / Crisis Text Line — even if Wave 1c protocol has not shipped, the resource list belongs in the policy).

## 8. Out of scope for this pass

Cookie-banner consent UI, EU-specific GDPR consent flow (geo-blocked at Phase 1), CCPA "Do Not Sell" link (Rodix does not sell, so the link points to a generic privacy-rights endpoint), age-gating mechanism implementation. All these are Wave 3 deploy-spec items; the policy text must be ready for them.

---

*End legal-research.md. Next file: privacy-policy-draft.md.*
