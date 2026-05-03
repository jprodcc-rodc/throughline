# FAQ

Questions a discerning user actually asks. If yours isn't here, send it: support@rodix.app.

### 1. Is this just ChatGPT but more annoying?

No. ChatGPT is a chat interface to a model. Rodix is a memory layer that sits across whatever AI you're using — it captures the structure of what you said as a card, brings it back when topics return, and lets you export everything as markdown. The AI underneath is whoever you choose. Rodix is the layer on top.

### 2. What's actually different from Mem.ai or Reflect?

Mem and Reflect are notes apps with AI features bolted on; you write into them, they help you organize. Rodix is the inverse: you talk to AI normally, and Rodix writes itself from the conversation. You don't take notes in Rodix — Rodix takes notes from your AI conversations. Different input model, different value.

### 3. Why won't ChatGPT just ship this same thing?

OpenAI could ship cards tomorrow. The reason they haven't, and probably won't, is that the architecture Rodix requires — memory the user owns, model interchangeable, transparency by default, real export — contradicts the LTV model that funds ChatGPT. If your Claude memory worked in GPT, you'd switch tools when a better model came out. They keep memory locked, opaque, and uneditable by design. The bet isn't that any single feature is uncopyable — it's that the *whole shape* is structurally unavailable to anyone whose business depends on you not leaving.

### 4. Is my data zero-knowledge encrypted?

No, and we won't claim it is. Phase 1 is server-side recall with at-rest plaintext. Promising zero-knowledge would be a lie given the architecture — searching your past cards before each AI call requires the server to read them. Encryption hardening is on the post-launch roadmap. The actual ownership story today is markdown export. The Privacy Summary has the full picture.

### 5. What happens to my cards if I switch from Claude to GPT-5?

Nothing. The cards are stored independently of the model. When you change which AI is generating replies, the same memory comes with you. Phase 1 routes through Anthropic Haiku 4.5 by default; cross-model expansion (direct GPT, direct Claude, Gemini) lands post-launch. The cards themselves don't care which model produced them.

### 6. Can I export everything and leave?

Yes. Settings → Export → markdown files on your hard drive. One click. No "premium tier required for export" nonsense. The export button is a guarantee, not an upsell — and we put it in the Privacy Summary because it's the credible signal that the data is yours.

### 7. What format is the export?

Plaintext markdown. One file per card, plus an index file. Cards have a YAML frontmatter block (date, topic, source conversation ID) and the four fields as headed sections. Open them in Obsidian, paste into Notion, throw on a USB stick, run them through your own scripts. Not a JSON dump nobody can read — markdown, because that's the only format where a non-engineer can verify their data is theirs.

### 8. How is this different from a journaling app?

You don't write into Rodix. You talk to AI normally — about whatever you'd talk to AI about — and the cards generate themselves from those conversations. Journaling apps are intentional capture; Rodix is incidental capture. If you're already doing 2–3 hours/day of AI chat on hard things, the cards accumulate without any extra discipline on your part.

### 9. Why is this English-only?

Phase 1 launch geography is English-speaking international. The frontend supports Chinese and the extraction pipeline has a Chinese eval set, but the brand work, the founder essay, and the alpha-onboarding flow are anchored on English-first launch. Chinese launch is a Phase 2+ decision; not abandoned, just sequenced.

### 10. When will Chinese launch?

Honest answer: not committed to a date. Phase 2 is ~30 days post-launch and focuses on PWA install + Tauri desktop. Chinese-market launch needs separate work (compliance, localization beyond UI strings, channel strategy) and isn't on the Phase 2 roadmap as scoped. Closer estimate: months, not weeks. Sign up for the email list if you want the announcement.

### 11. Why is the EU blocked?

GDPR exposure on personal-thinking data is non-trivial for a solo founder, and shipping without proper compliance would be the wrong call. Phase 1 ships geo-blocked at the auth and routing layer. Phase 2+ adds EU support with the appropriate compliance work (DPA, lawful basis, sub-processor disclosures). If you're in the EU: not yet, and we're not going to fake-launch it.

### 12. Who's building this? Why solo / anonymous?

Solo, anonymous, working out of Asia, second half of a multi-year build. The anonymity is not posture — it's a signal that the value claim is the architecture, not a personal brand. Rodc is a real person; "anonymous" means the public-facing identity is a handle, not a LinkedIn profile. Support emails come from a human; the founder essay is on the site. If you need legal recourse, the Privacy Policy has the responsible entity.

### 13. How much does it cost? When?

Pricing is not yet finalized. Phase 1 alpha is free for the cohort. Public launch will introduce a subscription tier at a price point that hasn't been announced — we'd rather decide it correctly than commit early and regret it. The pricing thesis is: enough to make the product sustainable for one founder, low enough that "thinking partner" doesn't become "another SaaS bill." When pricing is set, current alpha users will get early-cohort terms.

### 14. What if I want to delete a card or stop a memory from forming?

Vault → click the card → Delete. Deletion also removes the card from future recall. If you want to stop extraction entirely, Settings has a switch to turn auto-extraction off — chat still works, no cards get written. Per-conversation recall scope and "let's start fresh" intent detection are Wave 3 work, post-launch.

### 15. What if I'm having a hard time / mental health crisis?

Rodix is not built for crisis support, and pretending it is would be worse than naming the limit. If you're in distress right now: **988** (US Suicide and Crisis Lifeline), **Samaritans 116 123** (UK & Ireland), or your local equivalent — `findahelpline.com` has international numbers. Rodix's crisis-content protocol (live as of Phase 1 alpha) detects explicit safety language and surfaces 988 once — late in the reply, framed as offer not press, with self-demarcation honored. The Vault captures the heavy moment as topic-only (concern/hope/question rows hidden) rather than paraphrasing distress into clinical language. You can also email support@rodix.app — a human reads it.
