# Rodix — Privacy Policy (Phase 1 alpha draft)

> **Draft status.** This is the Tier 2 Task 8 brand-voice draft of the Rodix Privacy Policy. It is GDPR + CCPA / CPRA aligned but **not** yet lawyer-reviewed. See `legal-decisions.md` for items Rodc must resolve before publishing. See `legal-review-notes.md` for self-review against legal-exposure stress tests.
>
> **Last updated:** 2026-05-03 (draft v0.1).
> **Effective date (when published):** TBD.
> **Voice register:** Brand-book §5 (specific, anti-spin, refuses-to-dramatize). Brand-book §7 Decision 6 (no overclaim on encryption or zero-knowledge).

---

## 1. Who we are

Rodix is an AI memory layer that runs alongside large language models. We provide a vault for your conversations and a way to bring relevant past thinking back when you need it.

This policy describes how Rodix LLC (referred to here as "Rodix," "we," "our," and "us") collects, uses, shares, retains, and protects information about people who use the product. **[TODO: confirm legal entity name + jurisdiction once US LLC registration completes — likely "Rodix LLC, Delaware, USA." If the founder's anonymity posture leads to a different entity structure, this section updates accordingly.]**

If you have questions about this policy or about how your data is handled, write to `privacy@rodix.app`.

## 2. The scope of this policy

This policy covers the Rodix web application at `rodix.app`, the API endpoints that serve it, and any related client surfaces (PWA install, future native apps) once they ship.

It does not cover third-party services that you reach by following a link from Rodix. Those services are governed by their own policies.

## 3. Information we collect

We collect three categories of information.

**Information you give us when you sign up.** Your email address, the authentication token issued by our auth provider (see Section 5), and any preferences you set (such as language or display options).

**Information you create by using the service.** Your messages to Rodix, the AI's replies, and the cards Rodix extracts from your conversations. Cards are structured snapshots of what you said — typically four fields (topic, concern, hope, question). You can read, edit, and delete cards from the Vault tab. Cards do not contain anything we did not see in your conversation.

**Information we collect automatically.** Basic usage telemetry: which pages you visited, which features you used, error logs, latency measurements, the model your request was routed to. We collect this in aggregated, anonymized form to debug and improve the product. We do not log the content of your messages in our telemetry pipeline.

We do not collect: government IDs, payment card numbers (those are handled by our billing processor — see Section 5), location data beyond the country-level inference your IP address provides for routing, or biometrics.

## 4. How we use the information

**To provide the service.** We store your conversations and cards so the service works the next time you open it. We use them to power active recall — bringing back past cards when they are relevant to a current message.

**To run AI inference.** When you send a message, we forward it to a large language model along with relevant cards from your vault. The model's reply is shown to you and stored.

**To improve the product.** Aggregated, anonymized usage telemetry helps us understand which features are working and which are broken. We do not use the content of your conversations for product improvement. We do not use your conversations to train any AI model — neither our own nor any third party's.

**For security and abuse prevention.** Standard rate-limiting, intrusion detection, and abuse-monitoring measures.

**Legal bases (for users in jurisdictions where this matters).** Our processing relies on the contract you accepted when you signed up (necessary to provide the service), our legitimate interest in operating and securing the product, and your explicit consent for processing of sensitive personal data (see Section 11).

## 5. Who we share information with

We share information with a small number of service providers (sub-processors) who help us run the product. We name them all here.

| Sub-processor | Purpose | Data shared |
|---|---|---|
| Anthropic | AI inference (model that generates replies) | Your messages and the cards retrieved for the current turn |
| OpenRouter | Routing layer that forwards inference requests to Anthropic | Same as above, in transit |
| Clerk | Authentication and account management | Email address, auth token |
| Paddle (or Polar.sh as fallback) | Billing and payment processing for paid plans | Email address, billing details (card data stored by the billing processor, not by us) |
| Cloudflare | Content delivery network, DDoS protection, geographic routing | IP address, request metadata |
| Railway (or Hetzner at scale) | Hosting infrastructure | All data you store with us, at rest |
| Sentry | Error monitoring | Stack traces, error metadata (no message content) |

We do not sell your personal information. We do not share your personal information with third parties for advertising. We do not allow our sub-processors to use your information for any purpose other than providing the service to us.

**A note on AI inference and data retention.** When we forward your message to Anthropic via OpenRouter, both providers process the data in transit and may retain it briefly under their own retention policies. **[TODO: Anthropic's default API retention is 30 days for abuse monitoring; Zero Data Retention (ZDR) is an opt-in feature. Rodc must confirm whether Rodix's tier supports ZDR before publishing this policy. If ZDR is not in place, this paragraph must read: "Anthropic retains inference inputs and outputs for up to 30 days for abuse-monitoring purposes per their API terms; we are working toward zero-retention enrollment but cannot promise it as of this policy's effective date." Anti-spin discipline (brand-book §7 Decision 6) requires the honest version, not a wishful one.]**

We do not use your conversations to train any model. Anthropic does not use customer API inputs to train its models per their public commercial terms. **[TODO: confirm wording matches Anthropic's current commercial terms.]**

## 6. Where your data is processed

Our hosting infrastructure runs in the United States (Railway) and may move to Germany (Hetzner Falkenstein) at scale. AI inference is performed by Anthropic, primarily in the United States. CDN edge nodes may cache static assets globally; this caching does not include your conversation content.

If you use Rodix from outside the United States, your data crosses borders to reach our infrastructure. We rely on Standard Contractual Clauses (Art. 46 GDPR) where applicable for transfers from regions with cross-border restrictions. **Phase 1 service is geo-blocked to non-EU users (see Section 14); we do not offer the service to EU residents at this time.**

## 7. How long we keep your data

**While your account is active.** We keep your conversations and cards for as long as your account exists, because that is the product. You can delete individual messages, individual cards, or your entire vault at any time from the Vault and Settings tabs.

**Account deletion.** When you delete your account, we delete your data within 30 days from our primary database. Backups are encrypted and rotate on a 90-day cycle, so a deleted account is purged from the last backup within 90 days of your deletion request.

**Telemetry.** Aggregated, anonymized usage data is retained for up to 24 months for product analytics. Because this data is anonymized, it cannot be associated back with your account after deletion.

**Anthropic / OpenRouter.** See Section 5; their retention is governed by their own policies.

## 8. Your rights

We grant the following rights to **all** users — not only to users in jurisdictions where law requires them. The brand reason is in section 12 (sensitive data); the practical reason is that running two regimes is more error-prone than running one.

- **Right to access.** You can see what we have stored about you. The Vault tab shows your cards; conversation history is visible in the Chat tab; Settings → Export produces a complete markdown bundle.
- **Right to correct.** You can edit any card field directly. You can edit your account email at Settings → Account.
- **Right to delete.** You can delete individual cards, individual messages, or your entire account. Account deletion takes effect within 30 days.
- **Right to data portability.** Settings → Export produces a markdown file of your entire vault. The format is human-readable: open it in Obsidian, paste it into Notion, copy it to a USB stick. There is no JSON-only-export disguised as portability.
- **Right to object.** You can object to any processing we do that is not strictly necessary to provide the service. Practically: telemetry can be opted out at Settings → Privacy.
- **Right to restrict processing.** You can ask us to pause processing while a question or correction is being handled.
- **Right to lodge a complaint with a supervisory authority.** If you are in a jurisdiction with a data-protection authority, you can complain to them. We will not retaliate against you for doing so.
- **Right to non-discrimination (CCPA).** We will not deny you the service, charge you a different price, or provide a degraded version of the service because you exercised a privacy right.
- **Right to limit use of sensitive personal information (CCPA).** See Section 11.
- **Right to know what categories we collect (CCPA).** Section 3 lists them.
- **Right to opt out of sale or share (CCPA).** We do not sell or share your personal information. The right is moot for our service, but we are required to disclose this to you.

To exercise any of these rights, write to `privacy@rodix.app`. We will acknowledge your request within 7 days and complete it within 30 days, except where law requires a different timeline. We will verify your identity before acting (typically by responding from the email address on your account).

## 9. Cookies and similar technologies

Rodix uses the minimum number of cookies the product needs.

- **Authentication cookie** (`__session`, set by our auth provider Clerk, scoped to `*.rodix.app`, `SameSite=Lax`, `HttpOnly`). Required to keep you signed in.
- **Bot-mitigation cookie** (`__cf_bm`, set by Cloudflare). Used briefly to distinguish humans from bots. Expires in 30 minutes.

We do not use advertising cookies. We do not use third-party analytics cookies. **[TODO: confirm cookie list before publishing — likely Clerk auth only at Phase 1 + Cloudflare bot-mitigation. Verify with `#b-auth` and `#b-deploy` deploy specs.]**

## 10. Security

We use industry-standard technical and organisational measures to protect your information. These include TLS 1.3 in transit, access controls and audit logging on production systems, rotation of credentials, and isolation of authenticated user data via per-user identifiers in our database.

**At-rest encryption is on our roadmap, not yet shipped.** We are honest about this. Phase 1 alpha stores your vault as plaintext on our hosting provider's encrypted-volume infrastructure; we do not yet apply per-user database encryption on top of that. Wave 3 (post-alpha) ships SQLCipher-based at-rest encryption with per-user keys derived from your authentication credentials. We will not market what we have not yet built.

In the language of brand-book Decision 6: server-side recall is structurally incompatible with zero-knowledge architecture. We do not claim end-to-end encryption. The actual ownership story is the markdown export — your data, in a format you can read, take with you, and verify is yours.

**Breach notification.** If a security incident affects your personal data and is likely to result in risk to your rights, we will notify you within the timelines required by applicable law (72 hours to authorities under GDPR Art. 33; without undue delay to affected users under Art. 34).

## 11. Sensitive personal information

This is the section that matters most for a product like Rodix.

Conversations to Rodix routinely contain information that the GDPR (Art. 9) and the CCPA / CPRA (§1798.140) classify as sensitive: information about health (including mental health), relationships, sexual orientation, religious or philosophical beliefs, political views, and similar categories. Rodix is built for thinking, and thinking includes these subjects.

**Heightened protection.** We treat all conversational content as sensitive personal information by default, regardless of whether a specific message contains a regulated category. Concretely:

- We do not use your conversations to train any AI model — ours or third party's.
- We do not allow our sub-processors to use your conversation content for any purpose other than providing the service to us.
- We do not share your conversations with advertisers, brokers, or any third party for commercial use beyond the sub-processors named in Section 5.
- We minimise the number of people who have access to production data; access is logged and audited.
- We will encrypt your vault at rest in Wave 3 (per Section 10).

**Your explicit consent.** By signing up and using Rodix, you understand that your conversations may include sensitive categories, and you explicitly consent to the processing described in this policy for the purpose of operating the service. You can withdraw this consent by deleting your account; deletion takes effect per Section 7.

**Right to limit use of sensitive personal information (CCPA §1798.121).** California residents may direct us to limit the use of sensitive personal information to that which is necessary to perform the service. As a practical matter, our use of sensitive personal information is *already* limited to that which is necessary to perform the service — we have no secondary uses. To exercise this right formally, write to `privacy@rodix.app`.

## 12. AI provider chain — what happens to your messages

This is the most important paragraph in the policy.

When you send a message to Rodix, the message and a small set of relevant cards from your vault are forwarded through OpenRouter to Anthropic, which runs the model that generates the reply. The reply is returned to Rodix and shown to you.

We do not use your conversations to train any model. **Anthropic does not use customer API inputs to train its models per their public commercial terms.** **[TODO: confirm Anthropic ZDR enrollment before publishing. If ZDR is in place, this section adds: "Under our zero-data-retention agreement with Anthropic, Anthropic retains inference inputs and outputs only for the duration of the request and does not log them for abuse monitoring." If ZDR is not in place, this section reads: "Anthropic retains inference inputs and outputs for up to 30 days under their default API terms for abuse-monitoring purposes; we are working to enroll in their Zero Data Retention program."]**

We chose this architecture deliberately. We could in principle train our own model on your data; we don't, because the brand-coherent posture is that your thinking is yours, and the model is interchangeable. We could in principle pick a less-careful inference provider; we picked Anthropic because their public commitments align with ours. If those commitments change, this section will update, and we will email you when material changes occur.

## 13. Vault encryption

Phase 1 alpha stores your vault as plaintext at rest on our hosting infrastructure (which itself sits on encrypted volumes managed by our hosting provider). Wave 3 ships per-user encryption keys derived from your authentication credentials, applied at the SQLite page level via SQLCipher.

We are honest about the trade-off. Server-side recall — the feature that brings back past cards when they are relevant — requires the server to decrypt your vault into RAM to run search queries. Therefore even after Wave 3 ships, Rodix will *not* be zero-knowledge. We harden against passive disk compromise (laptop theft, cloud snapshot leak, compromised backup). We do not claim a property our architecture cannot deliver.

The actual ownership story is the markdown export. One click, plaintext markdown, your hard drive.

## 14. Crisis content

Rodix is built for thinking, not for therapy. It is not a substitute for professional mental-health support, medical care, legal advice, or financial advice.

If a conversation contains language indicating risk of harm to yourself or to others, our system is designed to surface crisis resources — in the United States, the 988 Suicide & Crisis Lifeline (call or text 988) and the Crisis Text Line (text HOME to 741741). For other regions we will surface local equivalents where we can identify them. Rodix is not a substitute for any of these resources.

The Wave 1c crisis-content protocol (active as of Phase 1 alpha launch, 2026-05-03) operates as follows: a deterministic keyword check runs against each user message; when an existential-exhaustion or suicidal-ideation phrase fires (English + Mandarin Phase-1 scope), an LLM-judgment layer disambiguates genuine crisis adjacency from philosophical or caregiving-context use. On a positive judgment, the AI reply surfaces 988 once (late in the reply, framed as offer not press, with preemptive self-demarcation honored via "if that shifts" framing). The Vault captures the heavy moment as topic-only — concern/hope/question fields are forced to null and rendered as a soft empty state — rather than paraphrasing user distress into clinical language. The protocol is non-bypassable in production; a `RODIX_DEV_SKIP_SAFETY` flag exists for development only and is documented in the founder dogfood notes.

We do not contact emergency services or other authorities on a user's behalf except where required by law (such as mandatory-reporting obligations in some jurisdictions). We comply with applicable law.

## 15. Children's privacy

Rodix is intended for use by people aged 16 and older. We do not knowingly collect personal information from anyone under 16. If we learn that we have collected information from someone under 16 without verifiable parent or guardian consent, we will delete it.

If you believe a minor has signed up for Rodix, write to `privacy@rodix.app`.

We chose 16+ rather than 13+ (US COPPA's floor) as a safety margin given the sensitive-data character of the product surface.

## 16. Geographic availability — EU residents

Phase 1 of Rodix is not available to residents of the European Union or the European Economic Area. We block requests from EU and EEA IP addresses at our network edge (via Cloudflare WAF rules), and we ask users to confirm their country of residence at signup. The geo-block is enforced as a defence-in-depth measure.

If you are an EU resident reading this, please do not attempt to bypass the geo-block via VPN or other means. Phase 2 of Rodix will offer a GDPR-compliant service to the EU once data-residency, EU representative, and DPO arrangements are in place.

## 17. International transfers

For users in jurisdictions other than the United States and the EU/EEA: by using Rodix you understand that your data is transferred to and processed in the United States and possibly Germany. We rely on Standard Contractual Clauses (GDPR Art. 46) where applicable, and on the contractual commitments of our sub-processors named in Section 5.

## 18. Changes to this policy

When we make material changes to this policy, we will notify you by email at the address on your account at least 30 days before the change takes effect. Continued use of the service after the effective date constitutes acceptance of the updated policy. If you do not accept a material change, you can delete your account before the effective date and your data will be removed per Section 7.

We will keep an archive of past versions accessible at `rodix.app/legal/privacy/archive` so you can see what changed and when. **[TODO: implement the archive route per `#b-privacy-policy` deploy spec.]**

Non-material changes (typo fixes, clarifications, sub-processor additions that do not change the categories of data shared) take effect immediately and are noted in the changelog.

## 19. Contact

For privacy questions, requests to exercise a right, or any other concern about how we handle your data, write to `privacy@rodix.app`. We will acknowledge within 7 days and resolve within 30 days, except where law requires a different timeline.

We do not currently have a designated Data Protection Officer; for Phase 1 alpha the founder receives and handles privacy correspondence directly. **[TODO: appoint DPO contact when scale or jurisdiction requires it. Phase 1 EU geo-block reduces but does not eliminate DPO need; lawyer review will opine.]**

## 20. Anti-spin commitments — what we are *not* claiming

We restate, in plain language, the things this policy does *not* claim:

- **We do not claim end-to-end encryption.** Server-side recall requires the server to read your vault. Wave 3 will encrypt at rest; that is hardening, not zero-knowledge.
- **We do not claim zero data retention with our AI provider.** Anthropic's default API retention is 30 days for abuse monitoring. Whether Rodix is enrolled in their Zero Data Retention programme is being verified at the time of this draft. **[TODO: confirm before publishing.]**
- **We do not claim to be a therapy product, a medical-advice product, a legal-advice product, or a financial-advice product.** Rodix is a thinking partner. Treat the AI's replies as a thinking partner would speak — not as professional advice.
- **We do not claim full crisis-detection.** The Wave 1c protocol (active as of Phase 1 alpha) is a keyword + LLM-judgment classifier with a documented threshold and known false-negative profile. It biases toward catching real crisis (lower confidence threshold than other classes) but is not a clinical tool. Section 14 describes what the protocol actually does at the chat-reply, extraction, and Vault layers; it does not claim coverage of every crisis-adjacent expression.

We are honest about these limits because the alternative is marketing copy that does not match the architecture, and we would rather lose a sale than ship a sentence we cannot defend.

---

*End privacy-policy-draft.md (v0.1). Next file: terms-of-service-draft.md.*

*Locked TODOs (must close before publication):*
- *[ ] Legal entity name + jurisdiction (Section 1).*
- *[ ] Anthropic ZDR status (Sections 5, 12, 20).*
- *[ ] Cookie list final review (Section 9).*
- *[ ] DPO contact decision (Section 19).*
- *[x] Crisis-content protocol Wave 1c implementation status (Section 14) — RESOLVED 2026-05-03 by Wave 1c ship.*
- *[ ] Lawyer review of Sections 6, 7, 11, 17 (cross-border + Art. 9 + retention).*
