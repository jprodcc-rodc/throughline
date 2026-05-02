# HN Launch Post — Show HN

**Title (under 80 chars):** `Show HN: Rodix — Memory layer for AI chat. Cross-model. White-box. Yours.`

*(76 chars including "Show HN: " prefix.)*

**URL field:** `https://rodix.app` (or alpha invite link at launch)

---

## Body

Rodix is a memory layer that sits over AI chat. Every meaningful exchange becomes a structured card with four named fields — topic, concern, hope, open question. You can read every card, edit it, delete it. When you start a new conversation, Rodix searches your past cards before the model generates and surfaces relevant prior thinking as a visible recall callout, with a link back to the source conversation.

The same vault works across providers. Switch from Claude to GPT-5, your memory comes with you.

How it actually works:

- Claim extraction runs on Haiku 4.5 via OpenRouter as the default ship config (`anthropic/claude-haiku-4.5` resolved at the extractor layer; provider-agnostic chat above it). Null-by-default extraction — empty fields are correct, never invented. A 4-field card with two fields populated is the product working as designed.
- Recall is server-side, scored against the vault on each new turn. SQLite + FTS5 with bigram tokenization for the active-recall scoring path; per-type thresholds are conservative on purpose (topic ≥ 0.65, stance_drift ≥ 0.70, loose_end ≥ 0.50, decision_precedent ≥ 0.60). Frequency caps: 1 per conversation, 3 per day on Free. Better to miss a borderline recall than fire a wrong one.
- Export is one-click plaintext markdown — frontmatter date + topic, four fields rendered as readable sections. The exporter ships in Wave 1b; it is not aspirational.

What I'd flag honestly before you sign up:

- Server-side recall with at-rest plaintext. So this is not zero-knowledge, and won't pretend to be. Encryption hardening is on the post-launch roadmap; per-user keys are Wave 3. The real ownership story today is the markdown export — your data, your file.
- Phase 1 is English-only. EU is geo-blocked at the auth and routing layer (GDPR + sensitive personal-thinking data; I don't have the legal capacity to do that right). Chinese launch is post-Phase-1.
- Single-user app, no team / collaboration features. Vault scoped to one user, no shared memory. By design, not on the roadmap.
- Phase 1 device priority is desktop Web. Mobile is responsive but Phase 1 ammunition is desktop screenshots; mobile is "doesn't break," not "fully optimized." PWA install + Tauri are Phase 2.
- Why no Stripe Atlas / formal entity: solo, anonymous, working out of Asia, indie-pace, no investor capital. Pricing is TBD and I want to keep optionality on it through alpha. If that disqualifies it for you, fair.
- Indie pace. I'm one person. Bug response is direct (email me) but not 24/7.

The shape of the bet: each frontier vendor's memory feature contradicts something in their business model. ChatGPT can't ship a vault primitive without admitting how much of the model's behavior is driven by inferred labels users can't audit. Gemini can't fix the persona-inference failure mode without abandoning the "we know you" frame. Claude projects can't go cross-model without lowering switching costs to zero. So the user-aligned memory layer is structurally available to a builder whose business doesn't depend on lock-in. That's the bet.

I'll be in this thread. Try it, break it, tell me what's wrong. I'll respond to every comment.

— Rodc

---

## Notes for Rodc on posting

- Best window: Tuesday-Thursday, 8-10am ET. Avoid Mondays (overhang from weekend) and Fridays (decay before the curve catches).
- Post the URL field as the alpha link. Body field per above.
- First-comment reply (within 5 min of posting): either nothing, or a one-liner like "Happy to walk through the recall scoring path or the extraction prompt if anyone's curious — code is in the repo." Don't dramatize the launch.
- If asked about pricing: "Pricing is TBD — I want to see how alpha goes before I commit. Likely a free tier + a paid tier; not committing to numbers yet."
- If asked "is this open source": "The recall orchestrator and the extractor prompt are in a public repo (link). The full app stack isn't open source today — that's a Phase 2 question I'm leaving open."
- If someone says it's like mem.ai: "Mem.ai's failure was distribution-shaped, not product-shaped — they had a similar bet on user-owned memory, and the indie team I learned the most from. The architectural difference: their cards were free-text auto-tagged; Rodix locks four fields with a null-default extractor that refuses to invent."
- If someone says "why not BYOK": "BYOK isn't Phase 1. Onboarding has a fallback link to it but I'm keeping provider strategy simple at launch. Reasonable people will disagree; happy to revisit after I see alpha behavior."

---

*Word count: 595 words in the main body. Voice tested: friends-intro register with HN-specific compression. Mechanism named at every step. Volunteered limits front and center. No "we" — solo founder writing as "I." No exclamation marks. No "transform / leverage / supercharge."*
