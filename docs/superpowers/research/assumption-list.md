# Rodix User Assumptions — Extracted from Tier 0 Inputs

**Total:** 47 assumptions extracted across 6 source documents.

**By category:** Validated 4 / Strong 18 / Weak 19 / Contradicted 6

**Source documents:**
1. `~/Downloads/rodix-friends-intro.md` (Rodc's friend-version intro, ~1,350 words body)
2. `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` v1.3 (33 scenarios across 8 categories)
3. `docs/superpowers/brand/brand-book-v1.md` v2 (master brand book, sections 1-8)
4. `docs/superpowers/brand/position-strategy.md` v2 (3 fail modes + 4 bets)
5. `docs/superpowers/brand/founder-narrative-arc.md` v1.1 (1,180 words)
6. `docs/superpowers/plans/2026-05-01-claim-extraction.md` v1.8 (eval set + ship gate)

---

## Category 1 — VALIDATED (n=4)

These are claims supported by external real-world signal — multi-vendor failure patterns visible in the public record, or directly verified in shipped code.

### V1. ChatGPT Memory and Gemini personalization features have shipped to mass distribution and produced visible user-trust failures.
- Source: friends-intro lines 161-167 ("ChatGPT memory, Gemini 'personalization,' Claude projects... They all share the same broken design"); position-strategy.md §1.1-1.3; brand-book-v1.md §2.
- Why validated: ChatGPT Memory rolled out 2024-2025 publicly; Gemini personalization shipped publicly; Claude projects shipped publicly. These are named, dated, datable market events — not Rodc speculation. The position-strategy explicitly cites public Reddit / HN reaction patterns. *"OpenAI rolled out ChatGPT Memory in 2024 and expanded it through 2025"* is a verifiable market fact.
- Risk if wrong: zero — this is the foundational Why-Now and is externally observable.
- Wave 2 / launch dependency: HN/Reddit launch narrative depends on this being mutually-known with the audience. If readers don't know about ChatGPT memory's failure shape, the founder essay's "iceberg of inferred labels" critique loses its mutual-knowledge anchor.

### V2. Vendor incentives structurally favor opaque, locked, vendor-bound memory implementations.
- Source: friends-intro lines 209-212 (*"vendors don't actually want you to own your AI memory. If your Claude memory worked in GPT, you'd switch tools whenever a better model came out. So they keep memory locked, opaque, and uneditable — by design"*); position-strategy.md §1.3; founder-narrative-arc.md Part 2.
- Why validated: the LTV-vs-portability conflict is a basic SaaS economics observation, not Rodc intuition. Three independent frontier vendors (OpenAI, Google, Anthropic) made the same architectural choice under the same incentive — this is corroborating multi-source evidence. Switching costs as LTV mechanism is well-established business literature.
- Risk if wrong: low — even if the analysis is wrong about *why*, the *fact* that all three vendors shipped lock-in-shaped memory is verified.
- Wave 2 / launch dependency: the entire defensibility thesis (brand-book §8 + position-strategy §8) rests on this. If vendor incentives shift (e.g., regulatory mandate for memory portability), Rodix's "competitors structurally cannot adopt" moat narrows.

### V3. Rodix's claim extractor produces hallucination ≤2.3% in the production-tier eval bucket (256 field decisions, EN).
- Source: claim-extraction plan v1.8 §"Hallucination as trust killer" lines 117-118; eval results from `fixtures/v0_2_0/eval/results-anthropic-claude-haiku-4-5-20260502T*.json`.
- Why validated: this is a directly measured signal from a 80-case eval set with multi-variant ground truth, not a projection. Trust-killer signal (hallucination) GREEN; conservatism (recall) RED. Reproducible.
- Risk if wrong: minimal at the eval-set level. The risk is generalization failure to production traffic — Wave 2 calibration trigger is set at >5% sustained as the kill switch. So the validation is bounded but real.
- Wave 2 / launch dependency: the entire ship-gate framework (trust-killer-vs-completeness split) and the "user trust collapse on invented worries" thesis (Decision 5 null-by-default) is operationalized by this number.

### V4. Markdown export with 4-field cards is shipped functional code, not aspirational positioning.
- Source: brand-book-v1.md §7 Decision 4 line 219 (*"The exporter (`app/shared/export/markdown_exporter.py`, `app/web/static/vault.js`) is shipped, not aspirational"*); position-strategy.md §3.4.
- Why validated: cited file paths exist in the codebase (CC and skeptic both verified during brand book Phase 4 review). Functional, not vapor.
- Risk if wrong: low — code exists. Risk is whether *users actually verify their data is theirs* by exporting (behavioral assumption — covered in W12 below).
- Wave 2 / launch dependency: the entire Bet 4 (real export) marketing claim and the friends-intro line *"Your data, your file"* depend on this being shippable — and it is.

---

## Category 2 — STRONG ASSUMPTION (n=18)

Rodc's intuition or n=1 lived experience as a heavy-user power-user. Plausible, not formally validated.

### S1. Heavy AI users (~2-3 hours/day across multiple providers) lose their own thinking across re-explanations and feel a "soul-tax."
- Source: friends-intro lines 189-199 (*"I kept losing my own thinking ... I'd just start over. Re-explain everything. Get a slightly different answer. The thinking didn't compound — it reset every time"*); founder-narrative-arc.md Part 1; brand-book-v1.md §3.
- Why strong (not validated): Rodc lived this for a year as a daily driver. n=1 self-report. No external survey, no HN thread cited, no third-party validation.
- Risk if wrong: foundational — if "re-explanation tax" is not a felt problem at scale among target users, the entire wedge narrows.
- Wave 2 / launch dependency: founder essay opening, HN narrative, landing-page hero ("ChatGPT remembers your name. Rodix remembers your thinking"), Wave 2 #active-recall-base entire trust-loop.

### S2. Heavy AI users tried incumbent memory features and got "mildly creeped out by what they assumed."
- Source: friends-intro lines 263-264 (4-condition list, condition 3); brand-book-v1.md §3 line 44.
- Why strong: Rodc's Gemini "corporate secretary" experience is the n=1 anchor. While ChatGPT memory has produced visible Reddit/HN backlash (corroborating signal exists), the specific frame "mildly creeped out" is Rodc's interpretation of what users feel.
- Risk if wrong: the friends-intro 4-condition self-selection list (line 259-269) breaks if users don't recognize themselves in this third condition.
- Wave 2 / launch dependency: founder-narrative-arc.md Closing depends on the 4-condition list resonating; brand-book §3 ICP definition.

### S3. Heavy AI users use 3+ AI tools and would benefit from cross-model memory.
- Source: friends-intro lines 261-262 (4-condition list, condition 2: *"Used three AIs for different things and wished they shared a brain"*); brand-book-v1.md §3.
- Why strong: Rodc himself uses ChatGPT + Claude + Gemini + others. n=1 confirmed. Whether this generalizes to even the heavy-user segment is unverified.
- Risk if wrong: Bet 2 (cross-model) becomes a feature without a felt user pain.
- Wave 2 / launch dependency: Bet 2 marketing claim. If most heavy users have settled on one model, cross-model is a "nice to have" not a wedge.

### S4. Heavy AI users want a record of how their thinking evolved on hard things, not just answers.
- Source: friends-intro lines 265-266 (4-condition list, condition 4: *"Wanted a record of how your thinking evolved on something hard, not just the answers"*); brand-book-v1.md §3.
- Why strong: Rodc's side-project example demonstrates this is real for him. The "kept moving the bar" insight from reading 3 cards back-to-back is the core product value claim. Generalization unverified.
- Risk if wrong: the side-project example feels personal but doesn't translate as universal user value.
- Wave 2 / launch dependency: Wave 2 #decision-journal-lite; Vault tab existence as first-class IA.

### S5. The user we want is not a generic curiosity-seeker or early adopter who tries every tool.
- Source: brand-book-v1.md §3 line 46 (*"Not a general curiosity-seeker. Not an early adopter who tries every tool. Someone who has accumulated enough hours-on-keyboard..."*).
- Why strong: Rodc's anti-target instinct based on personal-experience inference. No data on whether early-adopter retention is actually worse than heavy-user retention.
- Risk if wrong: Phase 1 alpha targeting (HN, IndieHackers) explicitly attracts curiosity-seekers — ironic mismatch.
- Wave 2 / launch dependency: acquisition channel selection; alpha cohort filtering.

### S6. Target users evaluate AI products on whether they respect their thinking, not on feature lists.
- Source: brand-book-v1.md §3 line 48 (*"Whatever their job title, they evaluate AI products on whether the product respects their thinking — not on feature lists"*).
- Why strong: Rodc's preference projected onto target user. No formal user research.
- Risk if wrong: marketing emphasis on "respect" / "sovereignty" register lands flat with users who actually want feature lists.
- Wave 2 / launch dependency: brand voice (anti-buzzword discipline §5); landing copy register.

### S7. Target users prefer plain "I don't know" to confident-sounding filler.
- Source: brand-book-v1.md §3 line 48 (*"They prefer 'I don't know' plainly to confident-sounding filler"*).
- Why strong: Rodc's preference. Not user-research backed.
- Risk if wrong: the "anti-spin" voice and `claim_extractor.md` null-by-default discipline produces a vault that feels sparse / undermined-confident, which users could read as "weak product."
- Wave 2 / launch dependency: §7 Decision 5 (null-by-default extraction); §5 "anti-spin" voice principle.

### S8. The target user's working context includes hard personal decisions (career / relationships / parent's decline / divorce).
- Source: brand-book-v1.md §3 line 48 (concrete examples: *"engineer thinking through a parent's cognitive decline at midnight; a designer mid-divorce trying to keep their working brain intact"*).
- Why strong: Rodc's side-project example is the only datapoint. The specific examples (parent decline, mid-divorce) are projected.
- Risk if wrong: the "thinking partner for hard things" frame doesn't match how heavy AI users actually use AI (which may be primarily research / coding / writing — see C2 below).
- Wave 2 / launch dependency: founder essay narrative; Wave 2 #intent-classifier "thoughtful" category definition; sample-prompt selection.

### S9. The "Gemini corporate-secretary" pattern of mis-categorization is structurally unfixable in inferred-persona memory designs.
- Source: friends-intro lines 201-207; founder-narrative-arc.md Part 1 P3.
- Why strong: Rodc's analytical claim about architecture. While the *fact* of the corporate-secretary experience is V1-validated, the structural claim (*"this is not a bug, this is the predictable output of a personalization system designed around inferred-persona labels"* — position-strategy.md §1.2) is Rodc's analysis. Plausible architectural claim.
- Risk if wrong: ChatGPT/Gemini could ship a fix without re-architecting (e.g., user-editable persona labels), partially closing Bet 1 as a moat.
- Wave 2 / launch dependency: Bet 1 (white-box cards) defensibility argument.

### S10. The user is solo (working alone), not collaborative — Rodix is for one person's thinking.
- Source: brand-book-v1.md §6 line 195 (*"Rodix is for the user alone with their thinking, not a dashboard for a team"*); §1 hero pitch contrast.
- Why strong: Rodc's solo workflow projected onto target user. Many heavy-AI workflows involve teams (e.g., engineering teams using AI for design discussions).
- Risk if wrong: enterprise / team segments are systematically excluded. Phase 1 launch geo of "English-speaking international" includes many team-AI users.
- Wave 2 / launch dependency: dark-mode-default visual choice; "private / late-night-thinking register" positioning; pricing model (per-user, no team tier).

### S11. Users know what they're thinking about and can verbalize it (the input model assumes deliberate user statement).
- Source: claim-extraction plan §"Bite-sized TDD tasks" Task 2 (*"sparse cases — only topic is present"*) implicitly assumes user produces interpretable input; rodix_system.md C-2.2 multi-round protocol assumes user gives "concrete specific" things to engage.
- Why strong: power-user assumption. Less articulate users may not produce parseable thoughts.
- Risk if wrong: extraction quality degrades for normal users; product feels "dumb" because vault is empty.
- Wave 2 / launch dependency: claim extraction quality gate; vault badge growth metric; #intent-classifier accuracy.

### S12. Users will stay in a thoughtful conversation through 3+ rounds with the AI.
- Source: scenarios S-CHAT-5 + S-CHAT-6 (multi-round depth pivot); rodix_system.md v1.3 Round 1/2/3 phasing.
- Why strong: assumes patience and willingness to follow Socratic phases. Modern AI usage is often single-shot. Rodc has lived this through his own dogfooding but normal users may bounce.
- Risk if wrong: Round 3+ "AI must pivot to reflection" rule never fires in practice; users leave at round 1 with a partial card.
- Wave 2 / launch dependency: rodix_system.md C-2.2 phasing rule; S-CHAT-6 scenario; Vault content quality.

### S13. Users want their AI to refuse generic "I'm here for you" empathy framing.
- Source: scenarios C-1 banned phrase list (*"我在这里 / 我陪你 / 慢慢说"*); brand-book-v1.md §5 Don'ts #4.
- Why strong: Rodc finds these sycophantic; assumes target users do too. Many users actually find these comforting (default ChatGPT register).
- Risk if wrong: the curated voice feels cold to a meaningful slice of would-be users.
- Wave 2 / launch dependency: rodix_system.md banned-phrase enforcement; §5 voice ceiling discipline; brand register at all touchpoints.

### S14. Users will edit cards in the Vault tab when something is wrong.
- Source: friends-intro line 178 (*"You see every one. Edit, delete, export"*); brand-book-v1.md §7 Decision 1 (every card editable).
- Why strong: Rodc's promise. Behavior-wise, many users never edit auto-generated content (cf. ChatGPT memory edit feature has low engagement based on public reports).
- Risk if wrong: white-box transparency is theoretical, not exercised. Vault becomes a dump rather than a curated artifact.
- Wave 2 / launch dependency: Wave 1b #3a Cards mgmt UI investment; Bet 1 substantive value (vs theoretical).

### S15. Users will understand "topic / concern / hope / question" 4-field schema without explanation.
- Source: friends-intro lines 222-230 ("Topic / Concern / Hope / Question"); claim-extraction plan §"Architecture" 4-field schema lock.
- Why strong: this is a cognitively demanding schema. Rodc finds it natural; first-time users may not.
- Risk if wrong: cards feel like a form, not capture-of-thinking. Onboarding has to over-explain.
- Wave 2 / launch dependency: onboarding step content; first-card aha moment; claim-extraction prompt design.

### S16. Users will recognize a recall callout (⚡ "I brought this back") as helpful, not intrusive.
- Source: brainstorm `#8` micro-adj 2 locked; brand-book-v1.md §7b first item; product test scenarios S-CARD-3 (Active Recall trigger).
- Why strong: Rodc designed this and assumes positive reaction. The brand-book §appendix (item 4 in reconciliation log) explicitly flags surveillance-fail-mode as a Wave 2 calibration risk: "if alpha users describe Rodix as 'creepy' or 'intrusive' rather than 'trusty' or 'thoughtful,' the verification mechanism has flipped polarity."
- Risk if wrong: recall callout reads as ChatGPT-memory-equivalent ("how does it know that?"). Trust collapses.
- Wave 2 / launch dependency: #active-recall-base entire trust mechanism; brand promise of "active recall vs personalization."

### S17. Users want continuity-of-thought specifically (not personalization) and will distinguish the two.
- Source: friends-intro lines 244-247 (*"They optimize for 'personalization' (knowing your name, your job). Rodix optimizes for continuity of thought"*); position-strategy.md §3.3.
- Why strong: this is the canonical pitch's load-bearing distinction. But "personalization" and "memory" and "continuity" are not crisp concepts in user vocabulary; many users use them interchangeably.
- Risk if wrong: hero pitch ("ChatGPT remembers your name. Rodix remembers your thinking") doesn't land — users hear it as the same thing in different words.
- Wave 2 / launch dependency: §1 canonical pitch; position §5; entire founder essay arc.

### S18. Users will treat markdown export as the credible signal that data ownership is real.
- Source: friends-intro lines 254-256 (*"Open it in Obsidian, paste it into Notion, throw it on a USB stick. Your data, your file"*); brand-book-v1.md §7 Decision 4.
- Why strong: a non-engineer-can-verify framing. Many users may not know what markdown is, may not export, and may not feel ownership through this mechanism.
- Risk if wrong: Bet 4 is real engineering work that users don't reach for; ownership signal doesn't fire.
- Wave 2 / launch dependency: §7 Decision 4 marketing claim; landing page export-as-trust-signal copy.

---

## Category 3 — WEAK ASSUMPTION (n=19)

CC inference, marketing-style projection, or scenarios-as-scaffolding-treated-as-data. No real basis.

### W1. Users will distribute messages across exactly 8 categories (career / relationships / chitchat / abstract / technical / sparse / mixed / emotional_rambling) at production-similar ratios to the 80-case eval set.
- Source: claim-extraction plan v1.8 §Eval set lines 92-100 (60 core + 20 boundary distributed across 8 categories).
- Why weak: the 80 cases are CC-and-Rodc-constructed scaffolding for eval, not derived from real-user-message logs. Rodc has not yet seen production traffic. The category list and distribution are projection.
- Risk if wrong: extraction quality on real user messages diverges from eval-set quality. Calibration trigger fires.
- Wave 2 / launch dependency: ship gate; Wave 2 telemetry calibration plan.

### W2. Users will pour out emotional content with low information density to Rodix ("emotional_rambling" category).
- Source: claim-extraction plan §Eval set, "6 `emotional_rambling`" boundary category lines 99-100.
- Why weak: the 6 emotional_rambling cases are CC-Rodc-constructed test inputs, NOT observed user behavior. Whether real users pour out emotional content to Rodix is an unverified assumption. (See D1 for the contradiction with banned-phrase list.)
- Risk if wrong: extractor handles a category that doesn't appear in production; or the inverse, real emotional content has different shape than constructed cases.
- Wave 2 / launch dependency: claim-extraction edge handling; D1 contradiction resolution.

### W3. Users will say "我想做宇航员" type aspirational short-phrases.
- Source: scenarios S-CHAT-4 Case 4a (*"我想做宇航员"*); S-CHAT-6 multi-round example.
- Why weak: this is a constructed test case from Rodc's live-walk on 2026-05-01. Single anecdote presented as scenario template; no evidence that users do this at scale.
- Risk if wrong: short-thoughtful classification overfitted to a non-representative example.
- Wave 2 / launch dependency: #intent-classifier C-4.3 boundary handling; S-CHAT-4 verification.

### W4. Users will write messages in the 5-200 character "classifier-decides" band.
- Source: scenarios C-4.3 lines 119-123 ("用户 message < 5 字符 → chitchat / > 200 字符 → thoughtful / 5-200 → classifier").
- Why weak: the 5-character and 200-character cutoffs are CC-Rodc heuristics, not derived from observed message-length distribution.
- Risk if wrong: cutoffs miscalibrated; classifier load shifts; UX edge cases proliferate.
- Wave 2 / launch dependency: #intent-classifier deployment economics (per-call cost calculation).

### W5. Users will engage with the recall callout's 4 feedback buttons ("用上了 / 不相关 / 已经想过 / 跳过").
- Source: brainstorm `#8` micro-adj 2 lock; brand-book-v1.md §7b first item.
- Why weak: 4-button feedback design is Rodc's instinct. No data on whether users will click any of them. Most micro-feedback features in apps have <5% engagement.
- Risk if wrong: telemetry that depends on button clicks (recall calibration) starves; 4 button labels in Chinese (Wave 1b string-level placeholder anyway) feel like clutter.
- Wave 2 / launch dependency: recall calibration telemetry; #active-recall-base UX.

### W6. Users will see Vault badge increment as a positive signal ("brand trust building core mechanism").
- Source: claim-extraction plan §7.4 (*"Vault 增长 = brand 信任建立的核心机制"*); brand-book §6 amber accent applies to badges.
- Why weak: Rodc's instinct that visible counter is positive. Many users find counters anxiety-inducing (cf. unread-badge fatigue in mobile apps). No A/B data.
- Risk if wrong: Vault badge feels like another notification noise rather than a trust signal.
- Wave 2 / launch dependency: IA-C cascade caveat (per claim-extraction plan §7.4); first-aha sequence.

### W7. Users will recognize and value the "thinking partner" register over generic "AI assistant" register.
- Source: scenarios C-1 banned-phrase rationale (*"Rodix 是 thinking partner, 不是 generic empathetic chatbot"*); brand-book-v1.md §4 archetype.
- Why weak: this is Rodc's category framing. "Thinking partner" is not an established product category; users may default to "ChatGPT-but-different" interpretation.
- Risk if wrong: positioning doesn't differentiate; users compare on feature parity to ChatGPT.
- Wave 2 / launch dependency: brand voice; landing page positioning; §4 archetype operational implications.

### W8. Users will accept 2-4 sentence default response length without complaining about brevity.
- Source: scenarios C-1 (*"AI 回复默认 2-4 sentences unless user explicitly asks"*); brand-book-v1.md §5 voice ceilings.
- Why weak: Rodc's preference. Many users prefer comprehensive ChatGPT-style answers. Brevity may be misread as "AI is dumb."
- Risk if wrong: users perceive Rodix as less capable; long-form-answer users churn.
- Wave 2 / launch dependency: rodix_system.md system prompt response-length constraint.

### W9. Users will input "今天有点累" as a low-confidence ambiguous case (not just chitchat).
- Source: scenarios S-CHAT-4 Case 4d (*"今天有点累" — could be chitchat OR thoughtful entry*).
- Why weak: CC-constructed case. Real users may overwhelmingly use this as just-greeting and find the follow-up "是身体上累还是心理上?发生什么了?" intrusive.
- Risk if wrong: fallback bias toward thoughtful causes false-positive follow-ups; users feel interrogated.
- Wave 2 / launch dependency: classifier fallback rule (#intent-classifier C-4.2); user-experience early friction.

### W10. Users will use sample prompts as ideation inspiration, not click-and-send shortcuts.
- Source: S-CHAT-VISUAL scenario (*"点击 → prefill composer (NOT 自动发送) — 用户可编辑后再发"*).
- Why weak: Rodc's design choice. Many users click-and-send as auto-message regardless of prefill design (Apple Watch quick-replies pattern). Behavior projection unverified.
- Risk if wrong: sample prompts become cookie-cutter messages; cards generated from canned input feel hollow.
- Wave 2 / launch dependency: Wave 1b S-CHAT-VISUAL spec; #intent-classifier first-message routing.

### W11. Users will keep cards in their vault rather than purging them.
- Source: scenarios S-VAULT-4 (delete confirmation existence implies deletion is exception, not norm); claim-extraction plan §7.4 *"Vault 增长"*.
- Why weak: Rodc's instinct that growth is positive. Some users will purge frequently (privacy/clutter instinct). No data.
- Risk if wrong: Vault grows then collapses; growth-as-trust-signal becomes contested.
- Wave 2 / launch dependency: long-tail vault-management UX; recall depends on retained cards.

### W12. Users will actually export their cards (not just notice the export option exists).
- Source: brand-book §7 Decision 4 (*"the only credible signal that the user owns the data"*); position-strategy §3.4.
- Why weak: notice-of-existence is not the same as use. Most users never export anything from any service. Whether the *option* is sufficient signal vs. *use* of the option is unverified.
- Risk if wrong: ownership-via-markdown is theoretical; the felt-trust signal is something else (e.g., founder transparency).
- Wave 2 / launch dependency: Bet 4 marketing claim load-bearing-ness.

### W13. Users will return to old cards weeks later (the "I killed the project that night" pattern).
- Source: friends-intro lines 274-318 (the side-project example); founder-narrative-arc.md Part 3 P1.
- Why weak: Rodc's specific behavioral pattern projected onto users. Most consumer apps see drop-off after first session; multi-week retention to a specific card is heroic.
- Risk if wrong: vault becomes write-only; recall fires but on stale unrelevant cards.
- Wave 2 / launch dependency: retention thesis; #active-recall-base value proposition.

### W14. Users will trust an anonymous solo founder working from Asia.
- Source: friends-intro lines 359-364 ("Solo, anonymous, working out of Asia, second half of a multi-year build"); position-strategy §2.3 framing as trust positioning.
- Why weak: Rodc's claim that anonymity is trust positioning. Anonymous founders have launch-stage trust deficits in privacy-sensitive products (especially when handling user thinking). Counter-evidence: Mullvad, Standard Notes succeeded with similar postures.
- Risk if wrong: alpha cohort can't get past "who is this person" question; signups stall.
- Wave 2 / launch dependency: founder essay; landing page founder section; HN narrative trust-build.

### W15. Users will perceive "we can't promise zero-knowledge" volunteering as anti-spin honesty rather than red flag.
- Source: brand-book §7 Decision 6; founder-narrative-arc Part 3 P1 inserted volunteered-limit.
- Why weak: Rodc's voice principle. Privacy-sensitive users may read "we can't promise zero-knowledge" as a stop-sign rather than an honesty signal.
- Risk if wrong: voluntary disclosure backfires; users churn on the explicit limit they wouldn't have known to ask about.
- Wave 2 / launch dependency: §5 anti-spin voice; founder essay technical paragraph; landing page security copy.

### W16. Users will think of Rodix as a layer on top of AI rather than as a replacement AI.
- Source: friends-intro lines 327-330 (*"Not 'better AI'. The AI underneath is whatever you choose. Rodix is the layer on top"*).
- Why weak: layer-vs-app conceptual model is product-category abstraction. Many users may default to "Rodix is a chatbot too, just different."
- Risk if wrong: pricing comparison is to ChatGPT subscription, not to "ChatGPT + Rodix"; positioning collapses to "another AI tool."
- Wave 2 / launch dependency: §6 (Constraints) BYOK fallback positioning; pricing thesis.

### W17. Users will participate in a per-conversation 1-cap / per-day 3-cap recall frequency without finding it too rare or too noisy.
- Source: position-strategy §3.3 (*"frequency caps (1 per conversation, 3 per day at the Free tier)"*); recall orchestrator code.
- Why weak: caps are engineering judgments. Real-usage may need rebalancing. No data.
- Risk if wrong: too-rare = recall feature feels broken; too-noisy = surveillance-fail-mode (per brand book §appendix item 4).
- Wave 2 / launch dependency: #active-recall-base calibration; surveillance-vs-trust polarity.

### W18. Users want a desktop-Web primary experience over mobile-native.
- Source: brand-book §3 (*"Phase 1 device priority is desktop Web primary"*); memory `project_device_priority.md`.
- Why weak: Rodc's choice based on his own desktop-thinking workflow. Heavy AI users on mobile (commute / bed / quick-thought capture) is a real segment; the friends-intro side-project example doesn't specify device.
- Risk if wrong: Phase 1 alpha users who prefer mobile churn before mobile lands in Phase 2 (launch+30) / Phase 3 (launch+90).
- Wave 2 / launch dependency: launch ammunition (100% desktop screenshots); device-priority phasing; alpha cohort device assumptions.

### W19. Users will engage thoughtfully across all 8 scenario categories at similar rates (the 33-scenario test set is representative).
- Source: scenarios doc lines 162-902 (33 scenarios across 8 categories presented as comprehensive verification); claim-extraction plan References to 10+ scenarios.
- Why weak: scenarios were CC-Rodc constructed for verification, not observed. Treating them as ground truth for "users will exhibit these patterns" is scaffolding-as-data conflation.
- Risk if wrong: scenario verification PASSes mask real-usage gaps; CC self-verification reports false positives.
- Wave 2 / launch dependency: every wave's "scenario verification" gate (per scenarios doc §How CC dispatches).

---

## Category 4 — CONTRADICTED (n=6)

### D1. "Users will pour out emotional content to Rodix" vs. "Rodix banned-phrase list refuses Caregiver register, with no crisis handling."
- Source A: claim-extraction plan §Eval set lines 99-100 (`6 emotional_rambling` boundary cases, *"long emotional venting with low information density"*) — extraction is built and tested for this user behavior.
- Source B: scenarios C-1 banned-phrase list (lines 50-59: `"我在这里 / 我陪你 / 慢慢说 / 我在认真听 / 无论是什么问题"` all banned); brand-book-v1.md §7 Decision 7 (*"Rodix is for thinking, not for engagement"*); §7b second item (*"crisis-content handoff protocol — NOT yet implemented"*); rodix_system.md prompt has zero crisis/safety/empathetic phrasing (Grep confirms zero matches for `crisis|self-harm|suicide|hotline|emergency|988`).
- Resolution attempted: brand-book §7b explicitly names this as Wave 1c (pre-launch) gap. The contradiction reveals that the 80-case eval extraction system handles emotional rambling, but the conversational system has no register designed for it. CC recommendation: emotional_rambling cases should output coarse topic only (no fake structured concern/hope) — extraction-side. AI conversational response should acknowledge limit and gracefully decline ("this is not what I'm built for, here are resources") — conversation-side. These two halves must align before launch.
- Risk if wrong: real users in distress hit the chat surface, AI refuses Caregiver register, user feels rejected; or AI accidentally drifts into Caregiver while extraction silently writes a card about their crisis (worst-case duplicating the Gemini "corporate secretary" failure shape with higher emotional stakes).
- Required decision: Rodc must finalize crisis-content protocol (resource scope, detection trigger, register on the way out) before Phase 1 alpha launch. This is THE highest-stakes user-assumption mismatch in the codebase.

### D2. "Cross-model is core to the wedge" vs. "Phase 1 keeps provider strategy simple and unstated to user."
- Source A: friends-intro lines 248-251 (Bet 2: *"Same memory works across providers... Cross-model from day one"*); position-strategy §3.2 (Bet 2 listed as one of four architectural commitments).
- Source B: friends-intro reading guide lines 117-119 (*"Do not assume BYOK is part of Phase 1 strategy. Phase 1 keeps provider strategy simple and unstated to user"*); position-strategy §6 first bullet (*"BYOK (bring-your-own-key) is NOT part of Phase 1 position"*).
- Resolution attempted: brand says "cross-model" is architectural; launch says "don't market it." CC recommendation: cross-model is a technical architecture commitment that pays off in Phase 2 / Wave 3, but Phase 1 marketing leads with "remembers your thinking" not "works across all models." Cross-model becomes substantiating evidence for the moat in founder essay, not the wedge in the hero. The contradiction is real but resolvable by phasing: Phase 1 = white-box + active recall + export are the lead bets; cross-model is dormant differentiator.
- Risk if wrong: launch copy boldly claims cross-model and users discover Phase 1 only ships one provider configuration → "false advertising" backlash on HN.
- Required decision: Rodc to confirm Phase 1 positioning de-emphasizes Bet 2 vs. v2 brand-book §7 Decision 2 (which lists it equal among 4 bets).

### D3. "Anti-target = restaurant-question users" vs. "Phase 1 acquisition channels = HN / IndieHackers / Twitter."
- Source A: friends-intro lines 271-272 (anti-target: *"If you ask AI 'what's a good restaurant in Lisbon' twice a week and that's it, you don't need this. ChatGPT's fine"*); brand-book-v1.md §3 (*"the anti-target is brand-defining"*).
- Source B: HN/IndieHackers/Twitter as Phase 1 launch channels (implicit in `~1,000 alpha users in first 30 days` target via founder essay + HN post per friends-intro lines 144 + founder-narrative-arc.md adaptation notes).
- Resolution attempted: HN/IndieHackers attract a wide curiosity-seeking pool. The anti-target frame says we *want* users to opt out. CC recommendation: launch copy must work through the four-condition self-selection list aggressively — the friends-intro 4-condition closing is the filter, and it must show up on the landing page above the fold so curiosity-seekers self-eliminate.
- Risk if wrong: alpha cohort skews curiosity-seeker / try-everything early adopter (S5 says we don't want them), retention is bad, post-launch metrics confirm the wrong cohort, Rodc scales the wrong product.
- Required decision: Rodc to confirm landing-page treatment of the 4-condition list (above fold? below fold? primary-CTA-gated?) before launch ammunition hardens.

### D4. "Heavy AI users use 3+ tools" vs. "One model wins decisively (fail mode 3)."
- Source A: friends-intro lines 188-189 (*"~2-3 hours a day, across ChatGPT, Claude, Gemini, plus a few more"*); brand-book §3 (*"a heavy AI user (~2-3 hours/day across multiple providers)"*); S3 above.
- Source B: position-strategy §4.3 fail mode 3 (*"Cross-model never matters because one model wins decisively"*); §4.3 confirmation signal: *"alpha behavior: > 80% of users settle on a single model and never switch"*.
- Resolution attempted: Rodc's heavy-user pattern is multi-provider; the fail mode is that this doesn't generalize. CC recommendation: instrument provider-switch telemetry on alpha to test directly. If <30% of alpha users use multiple providers in a 30-day window, the cross-model wedge is in trouble.
- Risk if wrong: Bet 2 is a real engineering investment (extraction model split-route, provider-agnostic schema) that doesn't pay off because users don't actually multi-tool.
- Required decision: define alpha telemetry metric for "multi-provider heavy user" segment size before alpha launch.

### D5. "Rodix optimizes for continuity-of-thought" vs. "Users want quick answers (fail mode 2)."
- Source A: friends-intro lines 241-247 (*"Rodix optimizes for continuity of thought — picking up where you actually left off"*); brand-book §1 + §3.
- Source B: position-strategy §4.2 fail mode 2 (*"users don't actually want continuity of thought, they want quick answers"*); §4.2 plausibility: *"ChatGPT engagement data... suggests that the modal heavy-user case is research / coding / writing assistance, not life-decision thinking-partner work"*.
- Resolution attempted: position-strategy explicitly flags this as a real fail mode the friends-intro doesn't fully resolve. CC recommendation: alpha cohort must be self-selected for life-decision use case, not heavy-AI-user generally. Acquisition messaging must filter for "thinking on hard things" specifically — not "AI memory" generically.
- Risk if wrong: foundational. If most heavy AI use is research/coding/writing, Rodix's positioning is targeting a narrow sub-segment that may not be self-sustaining at Phase 1 scale (≤1,000 alpha).
- Required decision: Rodc to articulate "if alpha shows narrow wedge insufficient, do we narrow further (preserve bet) or broaden (dissolve bet)?" — position-strategy §4.2 says narrow further; this must be operationalized as a pre-commit before alpha launch.

### D6. "Phase 1 is desktop-primary" vs. "Heavy AI users do quick-capture on mobile."
- Source A: brand-book §3 (*"Phase 1 device priority is desktop Web primary; mobile responsive does just enough to not visibly break"*); memory `project_device_priority.md`.
- Source B: friends-intro example "I open Rodix. I say: 'Thinking again about whether to kill the side project'" — the device is unspecified, but the implied workflow (turn-it-over for two months, talk on a walk to a friend) suggests mobile capture is part of the heavy-user pattern.
- Resolution attempted: Rodc's instinct says heavy thinking happens on desktop; the friends-intro example is ambiguous on device. CC recommendation: Phase 1 desktop-primary stands but landing page should not actively repel mobile users; "mobile native APP" is Phase 3 (+90) per memory note. Mobile responsive is a hard floor (per brand-book "responsive does just enough to not visibly break").
- Risk if wrong: meaningful slice of alpha cohort tries Rodix on mobile, finds it clunky, churns before desktop-aha can happen.
- Required decision: confirm or escalate the "mobile responsive = doesn't visibly break" floor; should it be raised to "mobile responsive = first-message capture works smoothly"?

---

## Top 5 most foundational assumptions

These are the assumptions on which the most subsequent decisions depend. If any are wrong, multiple Wave 2 specs / marketing decisions / pricing decisions cascade-fail.

### 1. **S1** — Heavy AI users feel a "soul-tax" from re-explaining and want continuity.
**Why foundational:** This is the entire wedge. Without it, Rodix is a memory feature in search of a need.
**Dependency tree:**
- Founder essay (founder-narrative-arc.md Part 1 entire opening)
- Hero pitch ("ChatGPT remembers your name. Rodix remembers your thinking.")
- Wave 2 #active-recall-base trust-loop ("Rodix optimizes for continuity of thought")
- Landing page above-the-fold problem statement
- HN narrative ("the day you came back to the problem")

### 2. **V2 + S9** — Vendor incentives structurally prevent fixing memory; mis-categorization is unfixable in inferred-persona designs.
**Why foundational:** This is the entire defensibility moat. If incumbents *can* fix the four bets without dismantling their products, Rodix is a 12-month head start, not a structural moat.
**Dependency tree:**
- Brand-book §8 five-year coherence test
- Position-strategy §8 escalation candidate (architectural-commitments-as-moat)
- Pricing rationale (no premium to charge if competitors will copy)
- Funding strategy (per position-strategy §8: "outside capital must accept the moat or is incompatible")
- Acquisition channel (HN narrative leans on this argument)
- 5-year roadmap (assumes head start period before catch-up)

### 3. **S17** — Users will distinguish "continuity of thought" from "personalization" cleanly.
**Why foundational:** The canonical pitch's load-bearing distinction. If users hear "ChatGPT remembers your name. Rodix remembers your thinking" as the same thing in different words, the entire 8-word hero collapses.
**Dependency tree:**
- §1 canonical pitch (brand-book + position-strategy + founder-narrative-arc all anchor on this)
- All hero copy variants (twitter / HN / video / email signature)
- Wave 2 #active-recall-base feature framing
- Onboarding step 3 ("first thought" prompt design)
- Wave 1b S-CHAT-VISUAL sample-prompt copy

### 4. **S15** — Users will understand the 4-field schema (topic / concern / hope / question) without explanation.
**Why foundational:** Schema is the entire data model. If users find it confusing or restrictive, every card is a friction surface.
**Dependency tree:**
- Claim-extraction plan v1.8 entire schema lock
- Wave 1b #3a Cards mgmt UI (master-detail rendering of 4 fields)
- Markdown export structure
- Recall callout content (which field surfaces)
- Onboarding "your first thought" content
- Brand-book §7 Decision 1 white-box thinking cards

### 5. **D1** — "Users will pour out emotional content" vs. "no Caregiver register, no crisis handling shipped."
**Why foundational:** The most blocking contradiction in the codebase. Touches user safety, brand register, and the gap between the 8-category extraction model and the system prompt's intentional refusal of empathetic register. Phase 1 alpha launch cannot ship cleanly through this without explicit Rodc resolution.
**Dependency tree:**
- Wave 1c crisis-content handoff protocol (per brand-book §7b)
- rodix_system.md emergency-register addition
- Geo-block scope (EU geo-blocked partly for sensitive-personal-data exposure — implicit recognition that personal-thinking data IS sensitive)
- Insurance / liability stance for solo founder
- 4-condition closing list filter ("hard thing" implies emotional weight)
- Founder-narrative-arc.md Closing register matching

---

## Top 3 contradictions Rodc must resolve

### D1. Emotional content category vs. banned Caregiver register, no crisis protocol
- **Cost of NOT resolving:** A user in actual distress hits chat, AI refuses comfort register per banned-phrase list, extractor silently writes a card about their crisis labeled `topic: depression` or worse. Worst-case Gemini-corporate-secretary failure with higher emotional stakes. Insurance liability for solo founder is non-trivial.
- **Recommended Rodc resolution path:**
  1. Decide register on the way out: graceful refusal ("Rodix is built for thinking through hard problems, not for emotional support — if you're in crisis, please reach 988 / Samaritans / etc.") with no Caregiver phrasing.
  2. Decide detection trigger: explicit safety language (self-harm / suicide / acute crisis keywords) → bypass extraction entirely, surface resource banner, no card written.
  3. Decide resource scope: US 988, Samaritans (UK/Ireland), international list for English-speaking-international Phase 1.
  4. Add crisis test cases to S-CHAT category in scenarios doc (currently 0 such cases).
  5. Update rodix_system.md with crisis-detection block before Phase 1 alpha launch.

### D5. "Continuity-of-thought wedge" vs. "Users want quick answers (fail mode 2)"
- **Cost of NOT resolving:** alpha cohort fails to differentiate Rodix from ChatGPT, retention is bad, post-launch metrics suggest wrong wedge, Rodc burns 30 days iterating on the wrong cohort. Position-strategy §4.2 explicitly flags this as a real-not-strawman fail mode.
- **Recommended Rodc resolution path:**
  1. Pre-commit decision tree before alpha: if first-session intent classifier shape skews >70% factual / chitchat, do we (a) narrow further (target only thinking-partner segment, accept smaller alpha) or (b) broaden product to absorb quick-answer use case?
  2. Position-strategy §4.2 already recommends (a). Brand-book §7 Decision 7 already commits to (a). But the *operational pre-commit* has not been made.
  3. Required: Rodc-signed-off statement that "if intent shape skews factual, we narrow not broaden" before alpha launches, so the iteration during alpha doesn't drift into broadening under traffic pressure.

### D2. Cross-model as Bet 2 hero-equal vs. Phase 1 keeps provider strategy unstated
- **Cost of NOT resolving:** Launch copy claims cross-model as a load-bearing differentiator while Phase 1 ships single-provider in dev. HN reader checks, finds Phase 1 = OpenRouter + nvidia-free + Anthropic-direct fallback (per memory `project_app_state_2026_05_02.md`). Trust collapses on the claim that contradicts visible reality.
- **Recommended Rodc resolution path:**
  1. Decide: Phase 1 hero leads with three bets (white-box + active recall + export), and cross-model is *substantiating evidence in founder essay* not *Bet listed in hero*.
  2. Position-strategy §6 already says BYOK is not Phase 1 position. Extend that to: cross-model is *architectural promise that the product will hold*, not Phase 1 functional claim.
  3. Update brand-book §1 hero pitch unpacking (currently lists all 4 bets as load-bearing) to clarify Phase 1 emphasis vs. architectural promise.
  4. Update founder-narrative-arc.md Part 3 wording about cross-model from descriptive ("The same memory works...") to architectural ("The architecture is cross-model from day one — Phase 1 ships through OpenRouter + Anthropic-direct, post-launch adds first-class Gemini / GPT alongside").

---

*End assumption-list.md — extracted by Tier 0 Task 0c subagent, 2026-05-03. CC inference layer; Rodc must confirm or revise the categorization, especially the Validated/Strong boundary which is set strictly per task instruction.*
