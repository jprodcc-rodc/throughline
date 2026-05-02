# Privacy Summary

This is the plain-English version. The full Privacy Policy is the legal document; this page is the honest one. Where they conflict, the Privacy Policy wins legally — but if anything here misrepresents what's actually true, that's a bug, and we want to hear about it.

## What Rodix collects

Three things, no surprises:

- **Your messages** — what you type into the chat.
- **The AI's replies** — what comes back.
- **Your generated cards** — the four-field structures Rodix extracts from thoughtful messages (topic, concern, hope, question), plus the IDs that connect each card to the conversation that produced it.

That's the user-data scope. We also log standard operational telemetry (request timestamps, model latency, error codes) and basic account info (email if you signed up that way; magic-link tokens during auth). No tracking pixels, no third-party analytics scripts on the chat surface.

## Where it lives

Server-side database. Phase 1 storage is at-rest plaintext. We are not zero-knowledge — promising zero-knowledge would be a lie given the architecture (server-side recall searches your cards before each AI call, which requires the server to read them). Encryption hardening is on the post-launch roadmap; per-user encryption keys are a Wave 3 commitment, not a Phase 1 claim. The actual ownership story today is markdown export.

## AI provider chain

Phase 1 routes through **OpenRouter → Anthropic Claude Haiku 4.5** for both chat and extraction. OpenRouter is the routing layer; Anthropic runs the model. Both providers have their own privacy postures and data-retention terms, which we link to in the full Privacy Policy. Anthropic ZDR (zero data retention) status for routed traffic is pending verification; we won't claim it until we've verified it. Cross-model support (Claude direct, GPT, Gemini) expands post-launch.

## What we don't do

- **No AI training on user data.** Your messages and cards are not used to train any model — ours, Anthropic's (per their terms for API traffic), or anyone else's.
- **No third-party advertising.** No ad pixels, no behavioral targeting, no data sold to brokers.
- **No opaque memory.** What Rodix has captured is in your Vault, fully visible, fully editable. There's no shadow profile, no inferred persona label, nothing the system "remembers" that you can't see.
- **No engagement-bait telemetry.** We don't track time-on-app, daily-active streaks, or message volume as success metrics. Rodix is not optimized for engagement.

## Crisis content

Rodix is built for thinking through hard things, not for mental health crisis support. When the upcoming Wave 1c crisis-content protocol ships (required before broader Phase 1 alpha), explicit safety language (self-harm, suicidal ideation, acute crisis keywords) will trigger a graceful handoff: Rodix will surface resources (988 in the US, Samaritans, international hotlines) and decline to extract a card from that message. We do not perform therapy. If you're in distress right now, please reach out — the FAQ has the numbers.

## Geo-block: EU

Phase 1 is not available in the EU. GDPR exposure on personal-thinking data is non-trivial for a solo founder, and shipping without proper compliance would be the wrong call. Phase 2 plans include EU support with the appropriate compliance work (DPA, lawful basis, sub-processor disclosures, the rest). If you're in the EU and want early access, the honest answer is: not yet.

## Export your data

Settings → Export. One click produces markdown files: one file per card, plus an index. Open them anywhere, keep them anywhere. This is the artifact you can verify is yours without trusting our UI.

## Delete your account

Settings → Delete Account. Confirmation is required. Once confirmed, your data is removed from active systems within 30 days. Backup retention follows standard SLA; the full Privacy Policy spells out the timeline. After 30 days, the only thing remaining is whatever you exported before deletion.

## Contact

Privacy questions, takedown requests, or anything that feels off: **support@rodix.app**. A human (Rodc) reads every email. Response within 72 hours, usually faster.
