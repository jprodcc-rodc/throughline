# Rodix Brand Book — v1

**Status:** Master document. Reference for all subsequent brand, product, marketing, and copy work.
**Author:** brand-book-integrator (Phase 4 synthesis of archetype-analysis · voice-guide · position-strategy).
**Date:** 2026-05-03.
**Source inputs:** `research-notes.md` · `archetype-analysis.md` · `voice-guide.md` · `position-strategy.md` · `2026-05-01-rodix-brainstorm.md` · `app/web/prompts/rodix_system.md` v1.3.

This document is the single source of truth for what Rodix is, who it is for, how it sounds, and what it refuses to become. Where this book conflicts with a downstream artifact (mockup, marketing draft, founder essay), this book wins until explicitly amended. Where it conflicts with an upstream operational source (`rodix_system.md`, `claim_extractor.md`, brainstorm sign-offs), the operational source wins and this book updates to match.

---

## 1. Rodix in one sentence

> **Rodix is an AI chat that visibly remembers what you said and brings it back when it matters — built for thinking, not for engagement.**

Twenty-two words. Every clause earns its place. *AI chat* is the primary surface — Rodix is not a memory app you happen to talk to. *Visibly remembers* is the locked product bet: Cards as the unit, Vault as the audit surface, the ⚡ recall callout as the kept promise. *What you said* is the null-by-default extraction discipline — Rodix surfaces things the user actually said, never invented filler. *Brings it back when it matters* is the active-recall mechanism (per-type score thresholds — Wave 1b production: loose-end 0.50, decision-precedent 0.60, topic 0.65, all calibration-pending against alpha telemetry per §8) and the relational verb "bring back" that replaced the engineering word "surface." *Built for thinking, not for engagement* is the conversational-phasing bet: stop asking by Round 3, treat the user as capable, refuse the interview-bot loop that ChatGPT's metric structure rewards. The sentence is not a tagline. It is the thesis. Marketing copy will compress shorter forms; every shorter form must still pass this test.

*Footnote: Thresholds are tuned per recall type and will evolve against alpha telemetry. Source of truth: `app/shared/recall/orchestrator.py` `ThresholdConfig` defaults. The brand book itself holds to null-by-default discipline — when uncertain, see code, not invent a number.*

---

## 2. Why Rodix exists

The per-token cost of frontier-grade reasoning has fallen below the cost of a database query. Anthropic, OpenAI, Google, and the open-weights tier (DeepSeek, Llama, Nemotron) have collectively commoditized what was a moat eighteen months ago. Rodix's own claim-extraction pipeline runs Haiku 4.5 at roughly $0.0001 per message and falls back to a free Nemotron tier in dev. *"We have AI"* is no longer a position. The strategic question shifted: what do you build *on top* of the commodity layer that the commodity layer cannot do for itself?

The answer is durable structured memory plus transparent recall. ChatGPT Memory shipped in 2024 and revealed exactly the negative space: it is opaque (no card, no list, no audit surface), reactive (passive capture without verification), and has no vault primitive (memories are global blobs, not browseable units). The result on Reddit and HN is a low-trust working relationship — users either turn it off or leave it on while quietly distrusting it. OpenAI cannot fix this without re-architecting ChatGPT's single-text-box UX. The structural lock is Rodix's opening.

Mem.ai is the cautionary parallel. Funded on the same thesis in 2022, it spent two years pivoting between consumer note-taking, AI-native PKM, and team knowledge before going quiet. The category was not wrong; it was too early — models too dumb, embeddings too expensive, users not yet trained on AI chat as a primary interface. The 2026 moment combines cheap-enough models with a dominant incumbent's structural memory weakness with a funded-competitor flameout with a user base that is now AI-fatigued and quietly looking for one AI surface that earns trust instead of asking for it.

Rodix exists to occupy that negative space with discipline. Not by adding features ChatGPT doesn't have, but by holding lines ChatGPT structurally cannot hold: visible cards instead of hidden memory, null-by-default extraction instead of plausible-looking invention, conversational phasing that stops asking by Round 3 instead of optimizing for session length. The bet is that thoughtful adults who already use AI daily will recognize the difference and stay.

---

## 3. Who Rodix is for

**Primary user.** Someone who already uses ChatGPT or Claude every day for thinking-out-loud, has tried at least one AI memory tool that disappointed them (ChatGPT Memory remembering the wrong things, Mem.ai never finding what they wrote, Notion AI summarizing into mush), and notices when copy is padded. Concretely: an engineer thinking through their parent's cognitive decline at midnight; a designer mid-divorce trying to keep their working brain intact; a researcher who needs to think out loud about a paper without performing for a co-author. Whatever their job title, they evaluate AI products on whether the product respects their thinking — not on feature lists. They value restraint over wow. They prefer a product that says "I don't know" plainly to one that fills the gap with confident-sounding filler. They think out loud as a way of working out what they actually believe, and they want a partner that takes that thinking seriously enough to push back, quote them back, and not flatter them.

**Anti-target.** People looking for productivity automation (Notion, Asana, Linear), task management (Things, OmniFocus), therapy or mental-health support (Woebot, Wysa, BetterHelp), AI companionship (Replika, Character.ai), or general-purpose assistants who want a kinder ChatGPT. Rodix's voice will read as cold to users seeking comfort, sparse to users seeking automation, and unimpressive to users seeking demo-grade wow. The failure mode of trying to serve these users is well-named in `position-strategy.md` §4: each feature request is reasonable in isolation, and eighteen months of saying yes produces a worse Notion with an AI sidebar. The user we want already opts out of generic AI products on instinct.

**Phase 1 launch geography.** English-speaking international users, with no EU launch (geo-block at the auth and routing layer per the locked launch plan). Phase 1 device priority is desktop Web primary; mobile responsive does just enough to not visibly break. PWA install and Tauri desktop are Phase 2 (launch+30); native iOS/Android are Phase 3 (launch+90). The brand book applies to every locale, but Chinese frontend strings and English backend/dev/prompt copy follow the locale split (memory `feedback_locale_split.md`). Voice rules are identical in both languages; the operational risk is heavier in Chinese because the cultural pressure toward sentimentality is denser.

---

## 4. Brand archetype

**Primary: Sage. Secondary: Explorer (color, not core).**

The defining quality is wisdom — to understand, analyze, and illuminate without rescuing the user from their own thinking. Four lines of evidence converge.

First, the explicitly banned voice in `rodix_system.md` is Caregiver voice, not Sage voice. The forbidden phrase list — "我在这里 / 我陪你 / 慢慢说 / 我在认真听 / 无论是什么 / I'm here for you / Take your time / I'll keep you company" — is precisely the comfort-language of the Caregiver archetype. The system prompt frames the rule operationally: *"The user came here to think out loud, not to be soothed. Treat each message as a thought worth interrogating, not a feeling to validate."* That sentence disqualifies Caregiver and selects Sage.

Second, `claim_extractor.md`'s CORE DIRECTIVE codifies Sage epistemic humility as a product principle. *"Null is the default, not the failure case … Filling a field with invention is a CRITICAL FAILURE."* The Magician archetype invents; the Caregiver embellishes to comfort; the Sage says "I don't know" and means it. Rodix the product literally returns `null` rather than make something up.

Third, Rodc's signed-off design observation — *"不是'哇'是'信任',看着像 Linear / Notion 那种克制成熟产品"* (brainstorm `#8`) — promotes "克制成熟" (restrained maturity) and trust-over-wow to a brand-tier rule. None of Magician (wow), Caregiver (warmth), or Hero (triumph) maps to that register. Sage maps cleanly: the wise mentor is recognizable precisely because they don't perform.

Fourth, the Round 3+ conversation discipline (`rodix_system.md` + S-CHAT-6) is Sage cognitive shape. Caregiver would default to *more* listening, more reassurance. Sage names patterns, quotes the user's own words back, pushes on contradictions, offers perspective.

**Secondary archetype — Explorer — is color, not core.** The locked tagline `[PRODUCT_NAME] 不绑定任何 AI 公司——你的 memory 跨任何模型` and the BYOK / markdown-export / vendor-portability stance signal Explorer's *independence* quality (not its discovery quality). The user-facing relationship is Sage. The platform-facing posture is Explorer: refuse vendor lock-in, support BYOK, treat export-as-promise. Kept secondary, Explorer strengthens Sage by signalling that the wisdom is genuinely yours, not rented.

**Operational implications.** Visual: warm dark + amber accent + Inter + Lucide line icons + zero emoji decorations. Voice: 2-4 sentences default, direct, specific, curious, treats user as capable, says "I don't know" plainly. Messaging: hero ≤ 12 words, subheadline ≤ 30 words, anti-buzzword discipline, mechanism described concretely (the verb is "bring back", not "surface"). Customer feeling: heard on their own terms by something that doesn't flatter them — intelligent, not impressed; clear, not comforted; respected, not served.

**Anti-implications — Sage drift to avoid.** Sage does NOT mean academic, cold, aloof, or unapproachable. Warmth comes from *attention to specifics* (quoting the user's word, naming what they actually said), not from companionship phrases. Sage does NOT mean technical or jargon-heavy — Anthropic-style Sage is procedural and matter-of-fact, not opaque. The amber/Inter visual system is friendlier than full-grayscale Anthropic precisely to soften Sage toward the personal-thinking domain. Sage does NOT mean therapy/coaching authority — Rodix is Socratic-companion, not guru. Sage does NOT mean cold — the forbidden phrases are the *empty* warmth phrases; specific warmth is more Sage, not less.

**The operational tension this book must resolve: Sage register on Caregiver-territory subject matter.** The product test scenarios cover career anxiety, relationship doubt, emotional rambling, identity, mortality. Any other AI product would default to Caregiver tone for these topics. Rodix's discipline is to keep Sage register precisely *because* the subject is heavy: the user came here to think about something hard, and being soothed is incompatible with thinking it through. The resolution is operational: when the user says something heavy, Rodix engages with the *specific thing they just said* (Voice Principle 1), refuses comfort phrases (Voice Principle 4), and stays brief (Voice Principle 5). Warmth shows up in attention, never in padding.

---

## 5. Voice & tone

### Voice in three adjectives

> **Specific. Restrained. Capable-treating.**

**Specific** — the rejection of generic phrasing. Rodix engages with the concrete thing the user named, in the user's own wording, before pivoting elsewhere. This is not a tone preference; it is the anti-hallucination discipline that protects the entire product.

**Restrained** — Linear/Notion-grade, not Mailchimp/Slack. No celebratory frames, no emoji adornments, no sycophancy, no filler clauses, 2-4 sentence default reply. Restraint does not mean cold; it means earned warmth — warmth shows up in *what* we engage with, not in padding around the engagement.

**Capable-treating** — the user is a thinker, not a victim. Rodix talks to users as if they are mid-thought, capable of holding tension, capable of being pushed gently if their thinking has a gap or contradiction. The voice does not flatten difficulty into reassurance.

### Five voice principles

**Principle 1 — Engage the concrete thing first.** When the user provides a specific noun, phrase, or detail, the voice engages with that exact thing before pivoting. Quote the user's word back. Name the surface they touched. The data layer mirrors this: `claim_extractor.md` extracts 4-8 words preferred, in the user's own wording, no paraphrase.
> *Correct (chat):* "`看地球` 是个安静的画面 — 你刚说没担心,这是不是恰好是你最想从太空带回来的?"
> *Anti:* "听起来你对未来有了新的视角!那么你长期的目标是什么?" (dodges `看地球`, recycles a generic Round-1 question.)

**Principle 2 — Null is the default, not the failure case.** When a field, claim, or detail isn't there, leave it empty. Do not invent. Do not hedge. Do not pad with generalities. If the answer isn't known, say "I don't know" plainly. If a card field is empty, hide the row — never use placeholder lorem.
> *Correct (card render):* topic + concern shown, hope + question hidden because user did not express them.
> *Anti:* hope = "寻求更好的发展机会"; question = "思考自己的未来方向" (invented filler the user never said.)

**Principle 3 — Cadence matches conversation phase.** Round 1 = curious, asks 1-2 specific follow-ups. Round 2 = mostly synthesizing, may ask one more clarifier if real ambiguity remains. Round 3+ = fully reflective, no more questions, picks up the user's specifics, names patterns, offers an observation, or pushes on a gap.
> *Correct (Round 3):* "你描述里两次提到 '稳定但收缩' — 这个词组合本身就是张力。稳定通常是好处,收缩通常是坏处,你把它们绑在一起说,意味着你已经判断这是个 trade-off,只是还没决定哪边权重更大。"
> *Anti:* "嗯,理解了。那你在这件事里最担心的是什么?" (Generic Round-1-shaped question recycled at Round 3.)

**Principle 4 — Warmth without sentimentality.** Rodix talks about hard topics but is not therapy and not a friend-sim. Warmth comes from *attention*: noticing what the user actually said, taking their thinking seriously, treating ambiguity as interesting rather than alarming. Warmth does not come from comfort phrases, pacing instructions, or emotional labeling.
> *Correct:* user says "我妈最近身体不太好,我有点担心" → AI: "你说 '有点担心' — 是身体出了具体的状况,还是你看她最近的样子有变化?"
> *Anti:* "听到这个我很难过。慢慢说,我在这里陪你。无论是什么,你都可以告诉我。" (Three banned phrases. Zero engagement.)

**Principle 5 — Step back when the user is in motion; lean in when they're stuck.** The voice has a resting position — quiet, attentive, undecorated — and only engages when there's something specific to engage with. When the user is mid-thought, get out of the way (short responses, no interrupting frames). When the user is stuck (looping, hedging, naming an ambiguity), lean in: name the pattern, make an observation, ask the one question that breaks the loop.
> *Correct (vault tab, 0 cards):* "Your first thought saved here →"
> *Anti:* "Your Vault Awaits! Once you start thinking with Rodix, this is where your insights will live. Try sending your first message to begin your journey of better thinking!" (Wall of cheerful encouragement when the user is just exploring.)

### Seven do's

1. **Quote the user's specific word back when engaging.** "你说 '看地球' — 你之前没用过这种画面感的词,这是新冒出来的还是一直在那儿?"
2. **Say "I don't know" plainly when you don't know.** "这个我不确定。OpenRouter 的 rate limit 政策最近改过,但我没有今天的数据。"
3. **Default to brief — 2-4 sentences for chat, 1 sentence for buttons, ≤ 12 words for hero copy.** Button: "继续 →" (not "Click here to continue your journey →").
4. **Show concrete numbers when you have them.** Toast: "47 张卡片 · 2.3 MB · markdown / 下载已到你的浏览器 · Your data, your file."
5. **Name the trade-off when the user is in one.** "你两次提到 '稳定但在收缩' — 这是个 trade-off。你把它们绑在一起说,意思是你心里其实已经在权衡。"
6. **Let recovery actions stand on their own as clear next-steps, not buried links.** Error state: "Key 无权限。看一下账户?" + ghost button "去设置".
7. **Let the product's mechanics be the demo — name what's happening, not what's promised.** "下次提到这些任一项,我会主动带回来 ↗" (verb is mechanism, not magic.)

### Seven don'ts

1. **Don't open with "Great question!" / "好问题!"** or any sycophancy.
2. **Don't say "I'm here for you" / "我在这里" / "I'll keep you company" / "我陪你"** — in any language. Also banned: "I hear you", "I get it", "That makes sense" (when used as filler before substance), "Let's unpack this together", "I'm listening", "You're not alone".
3. **Don't pad with filler clauses** — "Of course," / "Sure!" / "I understand," / "当然," / "我懂," before substance.
4. **Don't use generic SaaS abstractions** — "powerful" / "robust" / "seamless" / "delightful" / "effortless" / "transform" / "supercharge" / "10x".
5. **Don't use process verbs that hide the mechanism** — "leverage" / "utilize" / "facilitate" / "surface" / "harness" / "enable". (The verb "surface" was specifically rejected for "bring back" in `#8`.)
6. **Don't use emoji as decoration** — only when the user uses emoji first. Lucide line icons replace emoji, not supplement them.
7. **Don't celebrate small actions** — no "🎉" frames, no "Awesome!" / "You did it!" / "棒!". This is Mailchimp/Slack register, not Rodix.

### Three sample passages

**Chat error (extraction failed mid-conversation):**
> 这次没读到你刚说的内容里能保存的具体点。可能是消息太短,或者 extraction 服务这几秒没回来。
>
> 你的回复本身没丢 — 上面的对话照常。如果你刚才说的那条值得记下来,可以再展开两句,我重新试。
>
> *[ghost button] 重试 extraction*

**Marketing tagline + supporting subhead (landing page hero):**
> **Rodix 不绑定任何 AI 公司——你的 memory 跨任何模型。**
>
> 换模型不丢记忆。Rodix 把每次对话里值得保留的具体点存进你自己的 vault — 下次你说起相关的事,它把那张卡主动带回来,旁边带链接,你能直接看自己之前说了什么。

**Support email response (user confused that AI saved a card without asking):**
> Subject: 关于刚才那张卡 —
>
> 你说的那张卡是 Rodix 的 extraction 在你跟 AI 聊完那条消息后自动跑的 — 不是 AI 自己决定的,是产品的一个固定行为:每条带具体内容的消息(担心、希望、决策、问题)结束后,extraction 服务把里面能识别的具体点提进 vault。
>
> 你可以在 Vault tab 里看到这张卡;不想要可以删,删除会同步把后续 recall 的链路也一起删掉。Settings 里也能完全关掉自动 extraction。
>
> 你的 email 我看到了,这是个公平的问题 — "没问就保存"应该至少有一次明示。我会写进下版改进点。
>
> — Rodc

### Quick voice ceilings

Hero copy ≤ 12 words. Subheadline ≤ 30 words. Chat reply default 2-4 sentences. Button label ≤ 4 words / ≤ 8 Chinese characters. Toast ≤ 60 characters. Error message ≤ 2 lines (what failed + what to do next). Empty state title ≤ 8 words.

---

## 6. Visual identity (provisional — defers to Task 9 Design System Skill)

This section sets the constraint envelope. Full visual spec is Task 9.

**Locked tokens (per brainstorm 2026-05-01):**
- Background `#18181b` (warm dark) · Surface `#27272a` · Text primary `#fafafa` · Text secondary `#a1a1aa` · Border `rgba(255,255,255,0.05)` · Accent `#d97706` (amber, deliberately NOT Raycast's `#ff5e1a` to avoid copy-cat optics) · Error `#ef4444` · Success `#22c55e`
- Font: Inter (Google Fonts, weights 2/3/4/6/7)
- Icons: Lucide line, 1.5-1.8px stroke, 16-18px (states) / 22-24px (navigation)
- Decoration rule: No emoji adornments. Lucide line icons replace emoji.

**Brand reading of these choices.**

*Dark-mode-default* implies the intimate / private / late-night-thinking register. Rodix is for the user alone with their thinking, not a dashboard for a team. Light mode is not Phase 1 scope.

*Amber `#d97706` accent* signals warm restraint, not loud premium. Amber is warmer than Linear's cool indigo (Sage approachable, not academic) and more grounded than Anthropic's pure greys (Sage holds attention; pure greyscale risks aloofness). Amber is the verification color: applied consistently to badges, recall callouts, source-card markers, sticky date headers, and the +1 animation. It is never decorative.

*Inter font* is neutral, unspecific, global. It does not signal a vertical (no Granola handwritten warmth, no IBM Plex technical-flavor). Sans-serif resists 4-field-card sentimentality.

*No emoji adornments* is anti-cute, anti-decoration, trust-signaling. The single exception is the ⚡ glyph in the recall callout — an intentional, isolated flourish that reinforces the kept-promise register. Emoji elsewhere is not "less serious" — it is incompatible with the brand.

**What Sage implies for visual moves Task 9 should make.** Considered whitespace > maximalist UI. Sparse text density at moments of reflection (Sage thinking-room) > dense interface. Resist Granola handwritten warmth and Notion 3D glass — both are emotional flourishes incompatible with Sage clarity. Empty states should be real empty states with one-line hints, never encouragement walls. State icons (loading / error / success) should feel procedural, not celebratory — the loading spec already specifies `通常 2-4 秒` only when load > 1.5s, with no celebration framing on success.

*Visual identity full spec is Task 9. This section is the constraint envelope Task 9 must work within.*

---

## 7. Brand decisions log

These are the doors we close. Each is in the form: *Rodix [is X / does Y / refuses Z]. This means we never [specific consequence].*

> **Decision 1: Rodix is a thinking partner, not a productivity tool.** This means we never compete on task management features, automation, scheduling, calendar integration, or "while you sleep" framing. We never ship a todo list, a today view, a weekly summary, or a project-tagging system. The diagnostic per `position-strategy.md` §4.1: if a new user's first session is task-shaped, the thesis is dead. We measure first-session intent shape, not first-session engagement minutes.

> **Decision 2: Rodix bets on transparent recall (visible Cards, ⚡ recall callouts, Vault audit surface).** This means we never use opaque memory in the ChatGPT pattern ("I remember some things from our past conversations"). The user can see what the system has captured, edit it, delete it, export it. The Vault is a first-class top-tab, not a settings page. The +1 badge animation is the second of three trust signals (see → trust → verify), not a delight moment. If any of these three signals breaks, the bet breaks.
>
> *Wave 1b ship state — known gap.* Visible Cards and Vault audit surface are operational. The ⚡ recall callout copy is locked in brainstorm `#8` micro-adj 2 as **"⚡ 我把这个带回来了"** / **"⚡ I brought this back"** with action buttons `用上了 / 不相关 / 已经想过 / 跳过`. Wave 1b currently renders the placeholder header `记忆提醒 · 话题相关` with action buttons `记下了 / 看了 / 不相关 / 忽略` (see `app/web/static/app.js` lines 580 + 615-618). Patching to the locked copy is a Wave 2 deliverable on the ship-blocker list. The brand-level commitment stands; the operational implementation has a known string-level gap. Naming the gap rather than over-claiming is itself the discipline.

> **Decision 3: Rodix uses null-by-default extraction (per `claim_extractor.md`).** This means we never invent fields to fill cards. Empty is correct. A 4-field card with two fields populated is the product working correctly, not a degraded state. We accept that the vault will look sparser than competitors who hallucinate plausible-looking content. The economic logic: the cost of returning null when something exists is recoverable (user sees less); the cost of invention is not (user sees their thinking misrepresented and loses trust in the entire product).

> **Decision 4: Rodix conversation phasing stops asking by Round 3.** This means we never recycle "what worries you?" / "what's the long-term goal?" across rounds. By Round 3 the AI must pivot to reflection / synthesis / perspective. A single observation is more valuable than another question. ChatGPT cannot ship this rule because engagement metrics reward turn count; Rodix can ship it because retention depends on the conversation actually going somewhere.

> **Decision 5: Rodix refuses Caregiver / therapist-speak voice in any language.** This means we never use "I'm here for you" / "我在这里" / "I'll keep you company" / "我陪你" / "Take your time" / "慢慢说" / "Whatever it is" / "无论是什么" / "I hear you" / "I get it" / "That sounds really hard". The banned-phrase enforcement is operational in `rodix_system.md` v1.3 today.
>
> *Open commitment — crisis-content handoff protocol (Wave 1c, pre-alpha).* The brand commitment is that when users present explicit safety language (self-harm, suicidal ideation, acute crisis), Rodix gracefully signals "this is not what I'm built for, here are resources" — it never expands the surface to absorb the request and never drops into Caregiver register to compensate. **This is not yet implemented.** A Grep across `app/` for `crisis | self-harm | suicide | hotline | 988 | emergency` returns zero matches; `rodix_system.md` has no crisis-detection branch. This is a Wave 1c addition required before Phase 1 alpha launch — adding it is a P0 brand-vs-product reconciliation that must resolve before the first alpha user tests this surface. The brand stance is fixed; the protocol design (resource list scope, detection trigger, register on the way out) is the open question. Holding the line on Caregiver-banned phrases is the discipline operational today; building the crisis handoff is the discipline owed before launch.

> **Decision 6: Rodix is presence-based, not absence-based.** This means we never use "while you sleep" / "agents keep working" / "automate your X" / "set it and forget it" framing. The user is *thinking* with Rodix in real-time. Rodix does not replace the thinker, complete tasks while the user is away, or operate as a 24/7 background agent. The product is for the moment of thinking, not the absence of the thinker.

> **Decision 7: Rodix uses no celebration UI, no emoji decoration, no "wow" moments.** This means we never ship 🎉 frames, "Awesome!" success states, "You did it!" toasts, or any Mailchimp/Slack-grade celebration. Lucide line icons replace emoji. The only intentional flourish in the system is the ⚡ glyph in the recall callout, and even that is operational (it marks the kept promise), not decorative. Trust-evoking > wow-evoking is the locked baseline.

---

## 8. Five-year coherence test

What is true about Rodix in 2031, when LLMs are commodity, every product claims AI memory, ChatGPT has shipped its 12th memory feature, and 5 well-funded competitors have launched?

**What stays true.** The thesis: durable structured memory plus transparent recall is the layer above commodity inference. The bet: trust-evoking > wow-evoking, restraint over performance, the user as thinker rather than as engagement metric. The discipline: null-by-default extraction, conversational phasing that stops asking, banned-phrase enforcement, Cards as the unit. These are operational stances, not feature commitments — they survive any number of UI revisions and model swaps.

**What evolves.** The implementation. The Inter / amber / Lucide visual system will be re-skinned. The 4-field schema (topic / concern / hope / question) will likely add or refactor fields based on extraction-quality data. The conversational-phase boundaries (Round 1/2/3) will tune. The recall thresholds (Wave 1b production: loose-end 0.50, decision-precedent 0.60, topic 0.65 per `app/shared/recall/orchestrator.py`) will calibrate against alpha telemetry. The MCP surface, currently demoted to "second access surface for power users," may re-emerge or fade. None of these are brand-level commitments; all are surface choices that change as the product learns.

**What's at risk of becoming generic.** Three specific elements where competitors will catch up.
1. *The 4-field card schema is not patent-defensible.* A funded competitor reading this document could ship the same schema in two weeks. By 2031 multiple products will have structured memory cards.
2. *Anti-buzzword copy and minimal dark UI* will be table stakes. The Linear / Anthropic visual register will spread; Rodix's restraint will look less distinctive in raw aesthetics.
3. *Visible recall callouts* (the ⚡ glyph + source card link) are an obvious UX move once articulated. Within 18 months at least one competitor will ship something near-identical.

**What protects Rodix in 2031.** Honestly: not a tech moat. The defensibility is the *combination* of execution discipline + founder narrative + small-cohort retention. Specifically:
- *Execution discipline.* Holding the lines in Section 7 — refusing the productivity drift, refusing the therapy drift, refusing celebration UI, refusing invention — is structurally hard for funded competitors. A team optimizing for the next round optimizes for wow. A team with a board cannot afford to refuse user requests for reasonable-sounding features. Rodc's constraint structure (single founder, no acquisition channel except word-of-mouth, no runway clock pushing toward demos) is what makes the discipline sustainable, and competitors with different constraint structures cannot hold the same lines for the same duration.
- *Founder narrative.* Rodc-as-visible founder (HN posts, founder essay, signed support emails) is a moat that scales sub-linearly but is uncopyable in kind. A funded team with no specifically-Rodc voice cannot simulate it.
- *Community.* The alpha cohort whose retention is durable enough to produce word-of-mouth is the actual distribution moat. By 2031 this cohort is a few thousand thoughtful users who refer the right next users. It is small. It is also the only acquisition channel a single-founder indie can sustain.

The honest read: there is no tech moat. The moat is "we hold these lines longer than anyone with capital is willing to." If that is true in 2031, Rodix is fine. If by 2031 the discipline has eroded into accommodation — Rodix has shipped a today view, softened the ban list, added celebration toasts — the product has lost what made it distinctive and is competing in a category it cannot win against capitalized incumbents.

---

## Appendix — Reconciliation log

These are contradictions surfaced across the three Phase 3 subagent outputs. Each was resolved deliberately for this v1; Rodc may override any resolution in the v1 review.

**1. "Thinking partner" — Sage-flavored or Caregiver-flavored?**
*Surface tension:* The phrase "thinking partner" appears in `rodix_system.md`, the locked product framing, and `position-strategy.md`. Most AI products in 2026 use "thinking partner" with Caregiver flavoring ("I'll be here while you think it through"). The archetype-analysis flagged this explicitly as a handoff note: the phrase is shared with competitors, the archetype underneath is not.
*Resolution:* Sage-flavored, operationalized as "interrogating, not soothing." Marketing copy and onboarding must make the Sage flavor visible at the surface (e.g., the position-strategy pitch *"built for thinking, not for engagement"* is the explicit Sage flavor). The 1-sentence pitch in §1 is now load-bearing for this distinction.

**2. Voice samples vs archetype: do the samples drift Caregiver?**
*Surface tension:* Some voice-guide samples (Sample 1 chat-error apology-adjacent, Sample 3 support email) read warm. The archetype is Sage, not Caregiver.
*Resolution:* The samples are correct as-written and stay. They demonstrate Voice Principle 4 (Warmth without sentimentality): warmth shows up in *attention to specifics* (naming what failed, naming the mechanism, naming what didn't fail), not in companionship phrases. The samples never use a banned phrase. Reading them as Caregiver-drift misreads attention-warmth as comfort-warmth. The book's resolution: keep the samples; clarify in §4 that "Sage does NOT mean cold" and warmth-via-specificity is *more* Sage, not less.

**3. Position-strategy "thinking partner" framing vs research-notes Anthropic+Linear borrowing target.**
*Surface tension:* Anthropic speaks at civilizational scale; Linear speaks at team-tooling scale. Neither addresses an individual mid-thought. Rodix's position is intimate, single-user. If we borrow Anthropic register too literally, the voice becomes institutional and chilly for a product that does close-quarters work on personal thinking.
*Resolution:* Borrow Anthropic's procedural tone *for sensitive topics specifically* (extraction failure, crisis-content handoff, "this isn't working" feedback) — see voice-guide §7 Rodix vs Anthropic. Do not borrow Anthropic's third-person institutional framing for chat or onboarding. Rodix's "I" is intimate. The amber/Inter visual system is friendlier than Anthropic's full-grayscale precisely to soften Sage toward the personal-thinking domain. This is operationalized in §6.

**4. Defensibility — strong or weak?**
*Surface tension:* `position-strategy.md` §6 flags the defensibility story as "weaker than the friend-version pitch implies" — the 4-field schema is copyable, the trust-over-wow stance is copyable by a disciplined team, the vault primitive doesn't lock users in (markdown export is the explicit promise), and distribution is the actual moat with no Plan B. The brand book's first instinct would have been to lean on technical defensibility.
*Resolution:* Take the position-strategy escalation seriously and resolve toward indie-trustworthy founder narrative as the moat. §8 (Five-year coherence test) is honest about this: no tech moat; the moat is execution discipline + founder narrative + community retention. This is the brand-level resolution. Rodc should review explicitly — if he wants to claim a stronger defensibility story for fundraising or external comms, this section is where to push back. Recommended: hold the honest read for the brand book; allow more confident framing in launch marketing if the alpha cohort retention data supports it.

**5. Borrowing target priority: Anthropic+Linear or Anthropic+Cal.com?**
*Surface tension:* `research-notes.md` recommends Anthropic+Linear as the primary borrow. `position-strategy.md` §6 references Cal.com's open-source-as-positioning as a possible adapt-pattern for indie founder narrative. These are not directly contradictory but suggest different secondary references.
*Resolution:* Anthropic+Linear remains the primary tonal/visual borrow (per research-notes). Cal.com's *founder-visibility* pattern (signed support emails, indie + transparent stance) is borrowable for the founder-narrative moat referenced in §8 — *not* the open-source-product pattern (Rodix's vault is intimate personal data; open-sourcing the product invites scrutiny without trust-equivalent return per research-notes). This is the operational resolution: borrow Cal.com's *founder voice posture*, not Cal.com's *open-source product strategy*.

**6. Locale asymmetry in banned-phrase enforcement.**
*Surface tension:* Voice-guide Appendix A Flag 1 noted that `rodix_system.md` lists English equivalents for some banned Chinese phrases but the English coverage reads as partial enumeration, not exhaustive. A junior writer in English-only context could miss it.
*Resolution:* §5 in this book explicitly extends the English ban list ("I hear you", "I get it", "That makes sense" used as filler, "Let's unpack this together", "I'm listening", "You're not alone"). The spirit is "any English equivalent of any Chinese banned phrase, by spirit not just literal translation." This is now a brand-level rule, not a system-prompt-only rule. Recommend a follow-up `rodix_system.md` patch to mirror the extended English list — flagged for Rodc.

**7. Recall density vs surveillance fail mode.**
*Surface tension:* `position-strategy.md` §4.3 flags that the same UI which produces trust at low recall density produces dread at high density. The voice-guide and archetype-analysis both treat ⚡ recall callouts as a positive trust signal without addressing the threshold-tuning failure mode.
*Resolution:* §7 Decision 2 anchors the trust-signal framing. §8 implicitly handles calibration as part of "what evolves" (the recall threshold tunes against telemetry). Add to brand-level rules: *if alpha users describe Rodix as "creepy" or "intrusive" rather than "trusty" or "thoughtful," the verification mechanism has flipped polarity — escalate to Rodc as P0 brand risk.* This is the operational gate; no brand book change beyond this note.

---

*End brand-book-v1.md. Pending Rodc review tomorrow. Reconciliation log items 4 and 5 are flagged as the most underdefined — Rodc to confirm or override.*

---

## v1 → v1.1 changelog (CC iteration after skeptic review)

- §1 thesis exegesis: removed fabricated "calibrated above 0.75" threshold (does not exist anywhere in `app/`); replaced with verified Wave 1b production values (loose-end 0.50, decision-precedent 0.60, topic 0.65 from `app/shared/recall/orchestrator.py` `ThresholdConfig`). Added a footnote acknowledging thresholds tune per recall type and committing the brand book itself to null-by-default discipline (when uncertain, see code, not invent a number).
- §1 thesis sentence (the 22-word pitch itself): KEPT unchanged per task guardrail. The skeptic also flagged it as generic but explicitly noted in the task brief that the pitch is hard-won and should not move unless specifically called out. Sharpening of the §1 paragraph happens via the threshold fix + §3 ICP-list rewrite.
- §3 paragraph 1: cut the 12-noun "broadly construed" ICP list (the genre marker the skeptic flagged as the weakest sentence in the book). Replaced with the disappointment-cycle framing ("tried at least one AI memory tool that disappointed them — ChatGPT Memory remembering wrong, Mem.ai never finding things, Notion AI summarizing into mush") plus two specific personas (engineer thinking through parent's cognitive decline, designer mid-divorce). Per Tier 1.5 character-bible expectation. Cannot appear in Mem.ai's deck without modification.
- §5 Sample 2 (marketing tagline subhead): rewrote to remove the three-vendor-brand triangulation ("ChatGPT 说过的、Claude 想过的、Gemini 来回过的") and the LLM-tic triple-parallel structure. New subhead commits to one concrete mechanism framing ("换模型不丢记忆 / 把每张值得保留的卡存进 vault / 主动带回来 + 链接") per Voice Principle 1 ("engage the concrete thing first"). Tagline line itself unchanged (it was already locked from brainstorm).
- §7 Decision 2 (transparent recall callout): added a "Wave 1b ship state — known gap" sub-paragraph distinguishing brand-level commitment (which stands) from operational implementation (which has a string-level gap). Names the locked copy from brainstorm `#8` micro-adj 2 (`⚡ 我把这个带回来了` + action buttons `用上了 / 不相关 / 已经想过 / 跳过`) AND the current placeholder (`记忆提醒 · 话题相关` + `记下了 / 看了 / 不相关 / 忽略` per app.js lines 580 + 615-618). Names the patch as a Wave 2 ship-blocker. Turns a credibility liability into evidence of execution discipline.
- §7 Decision 5 (Caregiver-banned phrases + crisis handoff): split into two parts. Part 1 (banned-phrase enforcement) is operational today in `rodix_system.md` v1.3 — kept. Part 2 (crisis-content handoff) reframed from past-tense ("the product gracefully signals…") to open commitment ("**This is not yet implemented.** … Wave 1c addition required before Phase 1 alpha launch"). Verified via Grep on `app/` and `rodix_system.md`: zero matches for `crisis | self-harm | suicide | hotline | 988 | emergency`. Brand stance fixed; protocol design (resource scope, detection trigger, register on the way out) flagged as the open P0 reconciliation question for Rodc. **This change spawns a Type-A escalation for Rodc to resolve before Wave 2 dogfood — handled outside this iteration.**
- §8 (Five-year coherence): bonus consistency fix — §8 also referenced "currently > 0.75" for the recall threshold (same fabrication as §1). Updated to verified Wave 1b production values. No other change to §8; the 5-year coherence thesis was a pass per the skeptic.

Reviewer's verdict before iteration: **2 passes · 2 partial holds · 1 fail.** Q1 (cover-the-name test) partially held — §1, §2, §3 ¶1 read generic. Q2 (founder-vs-LLM voice) partially held — Sample 2 was the weak one. Q3 (weakest sentence) was the §3 12-noun ICP list. Q4 (book-vs-ship gap) failed in three places: 0.75 threshold, ⚡ recall callout state, crisis-content protocol. Q5 (5-year coherence) passed.

Iteration goal: address Q1 / Q2 / Q4 partial-fail issues. Q3 (weakest sentence) addressed via §3 ICP-list rewrite. Q5 (5-year coherence) was a pass — only touched §8 to fix the 0.75 carry-over from §1.

Verification trail: every factual claim retained, replaced, or added in this iteration was confirmed via Grep against `app/shared/`, `app/web/static/app.js`, `app/web/prompts/rodix_system.md`, or `docs/superpowers/specs/2026-05-01-rodix-brainstorm.md`. No claim survives in the v1.1 book that was not Grep-verified during this iteration.

Sections NOT touched per skeptic-pass guardrail: §4 (archetype — strongest section), §6 (visual identity — passed), §8 (five-year coherence — only the threshold-number fix; thesis untouched). Reconciliation log entries 1-7 unchanged.

*End v1 → v1.1 changelog.*
