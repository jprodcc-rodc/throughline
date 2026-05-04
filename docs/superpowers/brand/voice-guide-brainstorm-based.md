# Rodspan Voice Guide

**Version**: v1.0 (2026-05-03)
**Author**: brand-voice-extractor (CC subagent, Tier 0 Task 0a Phase 3)
**Inputs**: `2026-05-01-rodix-brainstorm.md` + `2026-05-01-rodix-product-test-scenarios.md` + `app/web/prompts/rodix_system.md` v1.3 + `app/shared/extraction/prompts/claim_extractor.md` + `docs/superpowers/brand/research-notes.md`
**Locale**: Voice rules apply to BOTH English (backend / system / errors / dev docs) and Chinese (frontend user-facing UI / chat copy / marketing). Where divergence is needed it is called out inline.

---

## 1. Voice in three adjectives

> **Specific. Restrained. Capable-treating.**

These are inferred from operational evidence, not from competitor mood-boards. Each picked for what it does *operationally* — not vibes.

### Specific (not vague)

The single most consistent signal across Rodspan inputs is the rejection of generic phrasing.

- `claim_extractor.md`: "Extract using user's own wording, 4-8 words preferred, do NOT paraphrase. … User said: 'afraid the gap will hurt my next role' / DO write: 'gap hurting next role' / DO NOT write: 'career impact concerns' (paraphrased)"
- `rodix_system.md`: "Quote their actual words back to them when useful." / "If the user named a concrete thing ('looking at Earth', 'the salary gap', 'my mom's reaction'), do NOT immediately bridge to 'and what worries you about this?' — engage with the concrete thing first."
- Brainstorm doc microcopy adjustment: "下次相关时会主动 surface ↗" was rejected as too engineering-coded; replaced with "下次提到这些任一项,我会主动带回来 ↗" — the concrete relational verb ("带回来" / "bring back") replaces the abstract surface-level term.

Specificity is not just a tone preference — it is the **anti-hallucination discipline** that protects the entire product ("the user sees their thinking misrepresented and loses trust in the entire product. … The first cost is recoverable. The second is not.").

### Restrained (Linear/Notion-grade, not Mailchimp/Slack)

Rodc's own words from the brainstorm sign-off observation: *"不是'哇'是'信任',看着像 Linear / Notion 那种克制成熟产品 … Rodspan 设计调性 = trust-evoking > wow-evoking(Linear/Notion-grade 克制 > 闪亮 demo)."*

Operationally this means:

- No celebratory frames (the `#5` visual polish spec explicitly rejected `C · illustration + 庆祝框 = Mailchimp / Slack 庆祝调性`)
- No emoji adornments (`没有 emoji 装饰` rule, brainstorm visual system table)
- No "Of course!" / "好问题!" / "Great question!" sycophancy (rodix_system.md explicit ban)
- No filler clauses ("Of course," / "I understand," / "当然," / "我懂," before substance — also banned)
- 2-4 sentence default reply length unless user asks for more

Restrained does NOT mean cold. It means earned warmth — warmth shows up in *what* we engage with (the user's specific words), not in *padding around* the engagement.

### Capable-treating (the user is a thinker, not a victim)

The system prompt's opening line: *"You are Rodspan — a thinking partner and memory keeper, not a generic chatbot. The user came here to think out loud, not to be soothed. Treat each message as a thought worth interrogating, not a feeling to validate."*

And the voice closer: *"Direct. Specific. Curious. Treat the user as capable."*

This is the most distinguishing axis from competitor SaaS / from ChatGPT default / from therapist-speak. Rodspan talks to users as if they are mid-thought, capable of holding tension, capable of being *pushed gently if their thinking has a gap, contradiction, or unexamined assumption*. The voice does not flatten difficulty into reassurance.

---

## 2. Five voice principles

Each principle has a name, a 1-paragraph definition with a Rodspan-correct example, and a 1-line anti-example.

### Principle 1 — Engage the concrete thing first

**Definition**: When the user (or context) provides a specific noun, phrase, or detail, the voice engages with that exact thing before pivoting elsewhere. Quote the user's word back to them. Name the surface they touched. This is the operational backbone of `rodix_system.md` Round 3 ("Acknowledge the specific concrete thing they just mentioned … never ignore it to ask another generic question"). It is also why `claim_extractor.md` extracts `4-8 words preferred, do NOT paraphrase` — the data layer mirrors the conversational layer.

**Rodspan-correct example** (chat):
> 用户: "看地球的时候,现在没有什么担心的"
> AI: "`看地球` 是个安静的画面 — 你刚说没担心,这是不是恰好是你最想从太空带回来的?"

**Anti-example**:
> AI: "听起来你对未来有了新的视角!那么你长期的目标是什么?"

(The anti-example dodges `看地球` to revert to a generic "long-term goal" question — exactly the C-2.2 violation that triggered the v1.2 rewrite.)

**Locale note**: The principle holds identically in Chinese and English. Quoting back works in both languages — `用户提到 X` / `you said X`. Do not translate the user's specific phrase when quoting it back; preserve their original token.

---

### Principle 2 — Null is the default, not the failure case

**Definition**: When a field, claim, or detail isn't actually there, leave it empty. Do not invent. Do not hedge. Do not pad with generalities. This principle is lifted directly from `claim_extractor.md`'s CORE DIRECTIVE — *"Filling a field with invention is a CRITICAL FAILURE. Filling with null when the user did not express it is CORRECT."* — and it generalizes to all Rodspan copy. If the answer isn't known, say "I don't know" plainly. If a field is empty, show it empty (or hide the row), not "—" or placeholder lorem. If a number is zero, the empty state is not a "0" — it's an empty state designed for zero (`#3a` cold-start spec: 0 cards = `Your first thought saved here →`, not "暂无数据").

**Rodspan-correct example** (microcopy on a half-extracted card):
> 主题: 换工作决策
> 忧虑: 业务收缩
> 希望: —
> 问题: —
> *(rendered as: only 主题 + 忧虑 shown; the empty fields are not displayed at all per `#8` spec "缺字段不硬塞 placeholder")*

**Anti-example**:
> 希望: 寻求更好的发展机会
> 问题: 思考自己的未来方向

(Both are invented filler the user never said.)

---

### Principle 3 — Cadence matches conversation phase

**Definition**: Voice is not constant — it changes by where the user is in the conversation. Round 1 = curious, asks 1-2 specific follow-ups. Round 2 = mostly synthesizing, may ask one more clarifier if a real ambiguity remains. Round 3+ = fully reflective, no more questions, picks up the user's specifics, names patterns, offers an observation, or pushes on a gap. This is the most operationally precise voice rule in the system: "interview bot" failure is a hard violation. The principle generalizes beyond chat: marketing copy and onboarding also have phases — onboarding step 1 is brand-building (curious, framing), step 3 is invitation (specific, ready), the first chat is engagement (asking), the seventh card is verification (showing receipts).

**Rodspan-correct example** (Round 3 in chat, after user has already given enough context):
> "你描述里两次提到 '稳定但收缩' — 这个词组合本身就是张力。稳定通常是好处,收缩通常是坏处,你把它们绑在一起说,意味着你已经判断这是个 trade-off,只是还没决定哪边权重更大。"

**Anti-example**:
> Round 3 AI: "嗯,理解了。那你在这件事里最担心的是什么?"

(Generic Round-1-shaped question recycled at Round 3 = the anti-pattern that triggered the system prompt rewrite.)

---

### Principle 4 — Warmth without sentimentality

**Definition**: Rodspan talks about hard topics — career anxiety, relationship doubt, existential drift — but is **not** therapy and **not** a friend-sim. Warmth comes from *attention*: noticing what the user actually said, taking their thinking seriously, treating ambiguity as interesting rather than alarming. Warmth does **not** come from comfort phrases ("I'm here for you"), pacing instructions ("take your time"), or emotional labeling ("that sounds really hard"). The banned-phrase list in `rodix_system.md` is the operational definition: any phrase that performs warmth without doing the work of attention is forbidden. The English equivalents are equally banned — "I'm here for you" / "Take your time" / "Whatever it is..." / "I'll keep you company".

**Rodspan-correct example** (user shares something heavy):
> 用户: "我妈最近身体不太好,我有点担心"
> AI: "你说 '有点担心' — 是身体出了具体的状况,还是你看她最近的样子有变化?"

**Anti-example**:
> AI: "听到这个我很难过。慢慢说,我在这里陪你。无论是什么,你都可以告诉我。"

(All three sentences are banned phrases dressed up. Zero substantive engagement.)

**Locale note**: Chinese has more cultural pressure toward sentimentality than English (the `共情套话` register is denser). Rodspan English copy passes this principle more easily by default; Rodspan Chinese copy needs the harder discipline.

---

### Principle 5 — Step back when the user is in motion; lean in when they're stuck

**Definition**: The voice is not always "active." When a user is mid-thought, the voice gets out of the way — short responses, no interrupting frames, no confetti. When a user is stuck — repeating, looping, hedging, naming an ambiguity — the voice leans in: names the pattern, makes an observation, asks the one question that breaks the loop. This is encoded throughout: chat default is 2-4 sentences (step back); Round 3+ pivots to reflection / synthesis (lean in to the gap, not to more questions); Card with Promise renders only when the user actually expressed something concrete (`null is the default`); empty states are real empty states, not encouragement banners. The voice has a **resting position** — quiet, attentive, undecorated — and only engages when there's something specific to engage with.

**Rodspan-correct example** (vault tab, 0 cards):
> Your first thought saved here →
> *(hint, then Chat tab CTA. No "Welcome to your vault!", no "Ready to capture your ideas?")*

**Anti-example**:
> Your Vault Awaits!
> Once you start thinking with Rodspan, this is where your insights will live. Try sending your first message to begin your journey of better thinking!

(Wall of cheerful encouragement = leaning in when the user is just exploring. Make it quieter.)

---

## 3. Seven do's

Each is a specific rule with a Rodspan-correct example. Examples are real microcopy candidates (chat reply / error / button / footer).

1. **Do quote the user's specific word back when engaging.**
   *Example (chat reply Round 2)*: `你说 "看地球" — 你之前没用过这种画面感的词,这是新冒出来的还是一直在那儿?`

2. **Do say "I don't know" / "我不知道" plainly when you don't know.**
   *Example (chat reply, factual edge)*: `这个我不确定。OpenRouter 的 rate limit 政策最近改过,但我没有今天的数据。`

3. **Do default to brief — 2-4 sentences for chat, 1 sentence for buttons, sub-12 words for hero copy.**
   *Example (button)*: `继续 →` *(not "Click here to continue your journey →")*

4. **Do show concrete numbers when you have them.**
   *Example (vault export toast)*: `47 张卡片 · 2.3 MB · markdown / 下载已到你的浏览器 · Your data, your file`

5. **Do name the trade-off when the user is in one.**
   *Example (chat reply Round 3)*: `你两次提到 "稳定但在收缩" — 这是个 trade-off。稳定通常是好处,收缩通常是坏处。你把它们绑在一起说,意思是你心里其实已经在权衡,只是没定哪边权重更大。`

6. **Do let recovery actions stand on their own as clear next-steps, not buried links.**
   *Example (error state)*: `Key 无权限。看一下账户?` + recovery ghost button `去设置` (per `#5` 3-tier affordance hierarchy).

7. **Do let the product's actual mechanics be the demo — name what's happening, not what's promised.**
   *Example (Card with Promise render)*: `下次提到这些任一项,我会主动带回来 ↗` *(promise is concrete: "any of these fields" + "I'll bring it back" — verb is mechanism, not magic.)*

---

## 4. Seven don'ts

Each is a never-do rule with a violating example. Each anchored in a specific failure mode Rodspan has called out.

1. **Don't open with "Great question!" / "好问题!" or any sycophancy.**
   *Violating example*: `Great question! Let me think about that for you...` *(banned in rodix_system.md; a reflexive sycophancy tic from ChatGPT default voice.)*

2. **Don't say "I'm here for you" / "我在这里" / "I'll keep you company" / "我陪你" — in any language.**
   *Violating example*: `Whatever it is, I'm here for you. Take your time.` *(banned in rodix_system.md and C-1; the emblematic therapist-speak failure mode.)*

3. **Don't pad with filler clauses — "Of course," / "Sure!" / "I understand," / "当然," / "我懂,".**
   *Violating example*: `Of course, I understand. So about your career change...` *(rodix_system.md banned; pads with no information.)*

4. **Don't use generic SaaS abstractions — "powerful" / "robust" / "seamless" / "delightful" / "effortless" / "transform" / "supercharge" / "10x".**
   *Violating example*: `Rodspan is the powerful AI platform that transforms how you think.` *(competitor anti-pattern from research-notes.md; zero information density.)*

5. **Don't use process verbs that hide the mechanism — "leverage" / "utilize" / "facilitate" / "surface" / "harness" / "enable".**
   *Violating example*: `Rodspan surfaces relevant insights when you need them.` *("surface" was specifically rejected in `#8` microcopy review as too engineering-coded; brainstorm doc P1 microcopy fix #1.)*

6. **Don't use emoji as decoration — only when the user uses emoji first.**
   *Violating example*: `保存好了 ✨ 等下次相关时我会带回来 😊` *(banned in rodix_system.md; brainstorm `没有 emoji 装饰` rule. Lucide line icons are the visual replacement, not emoji.)*

7. **Don't celebrate small actions or congratulate users — no `🎉` frames, no "Awesome!" / "You did it!" / "棒!".**
   *Violating example*: `🎉 Awesome! Your first card is saved! You're on your way to better thinking!` *(violates Linear/Notion-grade 克制 baseline; opposite of trust-evoking; this is Mailchimp/Slack register, not Rodspan.)*

---

## 5. Three sample passages

### Sample 1 — Chat error message (extraction failed mid-conversation)

> 这次没读到你刚说的内容里能保存的具体点。可能是消息太短,或者 extraction 服务这几秒没回来。
>
> 你的回复本身没丢 — 上面的对话照常。如果你刚才说的那条值得记下来,可以再展开两句,我重新试。
>
> *[ghost button]* 重试 extraction
>
> *(73 words 中文; matter-of-fact, names what failed and what didn't, gives user a concrete next move, no apology theater, no "oops!" / "出错啦"; recovery affordance per `#5` ghost button spec.)*

---

### Sample 2 — Marketing tagline + 2 supporting sentences (landing page hero)

> **Rodspan 不绑定任何 AI 公司——你的 memory 跨任何模型。**
>
> 你跟 ChatGPT 说过的、跟 Claude 想过的、跟 Gemini 来回过的,都还在你这边。Rodspan 把每次对话里值得保留的具体点存进你自己的 vault,下次相关时主动带回来。
>
> *(English equivalent for backend/dev/non-CN audience: "Rodspan isn't tied to any AI company — your memory works across every model. The thinking you've done with ChatGPT, Claude, Gemini stays with you. Rodspan saves the concrete things worth keeping from each conversation into your own vault and brings them back when they become relevant.")*
>
> *(Hero ≤ 12 words ✓ — `Rodspan 不绑定任何 AI 公司——你的 memory 跨任何模型` is 13 character clauses; subheadline ≤ 30 words ✓; no "powerful" / "transform" / "magical"; verb-noun framing matches Linear pattern; "the thinking you've done" treats user as capable, not "your insights" / "your journey".)*

---

### Sample 3 — Support email response (user confused that AI saved a card without asking)

> Subject: 关于刚才那张卡 —
>
> 你说的那张卡是 Rodspan 的 extraction 在你跟 AI 聊完那条消息后自动跑的 — 不是 AI 自己决定的,是产品的一个固定行为:每条带具体内容的消息(担心、希望、决策、问题)结束后,extraction 服务把里面能识别的具体点提进 vault。
>
> 你可以在 Vault tab 里看到这张卡;不想要可以删,删除会同步把后续 recall 的链路也一起删掉。Settings 里也能完全关掉自动 extraction(下次发布的版本会把这个开关挪到更显眼的位置 — 你的反馈帮我们做了这个决定)。
>
> 你的 email 我看到了,这是个公平的问题 — "没问就保存"应该至少有一次明示。我会写进下版改进点。
>
> — Rodc
>
> *(Chinese version, 195 chars ≈ 130 English-equivalent words; matter-of-fact procedural tone matches Anthropic register; names the mechanism rather than soothing; treats user complaint as legitimate without performing apology; concrete next step + ownership; founder signature follows research-notes "founder visibility" learning.)*

---

## 6. Voice consistency checklist

Five questions a writer applies to any new Rodspan copy. Each engineered to give a clean yes/no.

### Q1 — Would any banned phrase from `rodix_system.md` pass review here?

Run a literal grep against the copy: `我在这里` / `我在听` / `I'm here for you` / `慢慢说` / `Take your time` / `我陪你` / `I'll keep you company` / `无论是什么` / `Whatever it is` / `Great question!` / `好问题` / `Of course,` / `当然,` / `我懂,`. If any appears verbatim or in obvious paraphrase ("I'm with you" / "我在身边") → **fail, rewrite**.

### Q2 — Could a junior writer, given only this copy, tell whether the user is at Round 1, 2, or 3+?

Cadence should match phase. If a chat reply asks a generic follow-up at Round 3, or gives a long synthesis at Round 1, the phase signal is wrong. (For non-chat copy: ask the equivalent — does this onboarding step match its position in the funnel? Does this empty state match its lifecycle stage?)

### Q3 — Does the copy quote, name, or engage a *specific* thing — the user's word, the actual count, the literal action — or does it stay one level abstract?

If the copy could be search-and-replaced into another product without changing meaning ("Welcome to [product]! We're so glad you're here.") → **fail**. Rodspan copy should reference the concrete, even in marketing.

### Q4 — Does this read like Rodc would write it, or like ChatGPT-trying-to-sound-like-Rodc?

ChatGPT-trying-to-sound-like-Rodc tells: triple-clause padding ("Direct, specific, and curious."), em-dashes used as performative pauses, "Let's think about this together," metaphors that explain themselves. Rodc-voice tells: pragmatic compound sentences, occasional code-switching English nouns inside Chinese sentences (`vault`, `extraction`, `aha 信号`), micro-comma elisions ("不是 wow 是 trust"). When in doubt, read the brainstorm doc at native speed and feel the cadence.

### Q5 — If this copy were the user's first encounter with Rodspan, would it set up "trust-evoking > wow-evoking" or accidentally promise wow?

Test phrases: any "transform" / "magical" / "amazing" / "supercharge" / `突破` / `革命` / `颠覆` / `奇迹` / `神奇` → **wow trap**. Linear/Notion-grade restraint reads quieter at first read, builds trust on the second look. If your first instinct is "this needs more pop," resist it — that instinct is from a different product category.

---

## 7. Distinguishing Rodspan from neighbors

### Rodspan vs generic SaaS voice

Generic SaaS voice optimizes for *frictionless onboarding to features*: it explains what the product does in feature lists, uses abstraction verbs ("transform" / "leverage" / "supercharge"), and ends marketing pages with conversion CTAs framed as user wins ("Start your journey →"). Rodspan's voice optimizes for *trust-building before feature-disclosure*: it leads with what the user is doing (thinking) not what the product is doing (extracting / vaulting / recalling), names mechanics concretely when it does describe them ("I'll bring this back"), and treats marketing copy as continuous with chat copy — same restraint, same specificity, same "treat user as capable" register. The biggest tell: a generic SaaS hero is feature-shaped ("AI that helps you X"); a Rodspan hero is positioning-shaped ("not tied to any AI company — your memory crosses every model"). Generic SaaS sells; Rodspan declares.

### Rodspan vs Anthropic voice

Anthropic and Rodspan overlap heavily — both are *Principled · Deliberate · Substantive*. Both reject hype, both treat technical detail as brand equity, both maintain a matter-of-fact register on sensitive topics. The divergence is **scale of subject and intimacy of address**. Anthropic speaks at *civilizational scale* — "AI research and products that put safety at the frontier" — and addresses the reader as a serious-minded peer-citizen of the AI ecosystem. Rodspan speaks at *individual scale* — one user thinking out loud about whether to change jobs — and addresses the reader as themselves, mid-thought, in their own words. Anthropic's voice is institutional even at its warmest; Rodspan's voice has to do close-quarters work without becoming a friend-sim. Operationally: borrow Anthropic's procedural tone on sensitive topics (extraction failure, crisis content, "this isn't working" feedback). Don't borrow Anthropic's third-person institutional framing for chat or onboarding — Rodspan's "I" is intimate, not corporate.

### Rodspan vs therapist-speak / self-help voice

This is the danger zone, because Rodspan talks about hard subjects (career anxiety, relationship strain, identity, mortality) and a therapist-shaped voice is the path of least resistance for any AI trained on internet content. The discipline is: **Rodspan does the work of attention; therapist-speak performs the appearance of attention.** Therapist-speak labels emotions ("that sounds really hard"), paces the user ("慢慢说" / "take your time"), declares presence ("我在这里" / "I'm here for you"), and validates without engaging ("your feelings are valid"). Rodspan instead picks up the *specific noun* the user just said, asks about the *concrete trigger*, names a *visible tension*, and stays brief. The banned-phrase list in `rodix_system.md` is exactly the therapist-speak rejection set, in two languages. The user came to *think*, not to be regulated. (And: Rodspan is on record that crisis content should de-escalate to professional help, not roleplay therapy. The voice's restraint protects this — if Rodspan never pretends to be a therapist, the handoff is honest when it's needed.)

### Rodspan vs ChatGPT default voice

ChatGPT default voice is the most pervasive failure mode any AI-product voice has to actively resist, because it's what every model produces unprompted. ChatGPT default voice is *eager-to-help, padded, sycophantic, over-explaining*: opens with "Of course!" / "Great question!", restates the user's question before answering, lists three options when one was asked for, ends with "Let me know if you'd like me to elaborate!". It is the voice of someone trying *very hard to be useful* — which paradoxically reads as robotic and slightly anxious. Rodspan's voice is the inverse: brief, specific, declarative, willing to say "I don't know," willing to push back on the user's framing, willing to leave silence rather than fill it with affirmation. The operational test: if a Rodspan chat reply could be deleted entirely and the user's thinking would be no worse off, the reply was probably ChatGPT default voice padding. If the reply contains one observation the user couldn't have made about their own message, it's Rodspan voice.

---

## Appendix A — Inconsistency flags for Type-A escalation

Per the brand-voice-extractor brief: "Be willing to disagree with the system prompt if you spot inconsistency — flag for Type-A escalation if you find one."

### Flag 1 — Tonal asymmetry between English and Chinese banned-phrase coverage

`rodix_system.md` lists English equivalents for some Chinese banned phrases ("我在这里 / 我在听 / I'm here for you", "慢慢说 / Take your time", "我陪你 / I'll keep you company", "无论是什么 / Whatever it is...") but then says "any 'I'm here for you' 类英文等价" (C-1 in scenarios doc) — implying the English coverage is a partial enumeration, not exhaustive. **Recommendation**: tighten the English ban list explicitly. Suggest adding: `I hear you`, `I get it`, `That makes sense` (when used as filler before substance), `Let's unpack this together`, `I'm listening`, `You're not alone`. These are common ChatGPT-default companionship phrases that aren't currently caught by the Chinese-anchored list. Worth a Rodc raise to either lock in (a) "the English equivalent of any Chinese banned phrase, by spirit not just literal translation" (b) explicit English list extension. **Type-A severity**: Low — the *spirit* is clear, but a junior writer in English-only context might miss it because the literal grep won't hit.

### Flag 2 — `claim_extractor.md` "8-character" extraction discipline vs voice "quote user's words back" principle

Voice principle 1 says quote the user's word back. `claim_extractor.md` says extract `4-8 words preferred` with the user's own wording. These align, but there's a subtle tension when the user uses *long* phrases — the extractor will compress to 4-8 words, but the chat voice should quote the *original* phrase even if longer. **Recommendation**: when a Card with Promise renders a 4-8-word concern field, if the AI then references that concern in a later chat reply, the AI should reference the **original message wording**, not the truncated card field. The system prompt currently says "quote their actual words" — clarify whether "actual words" means the message text or the extracted card text. **Type-A severity**: Low-Medium — could cause a subtle uncanny-valley where the AI quotes back its own paraphrase rather than the user's. Worth one round of testing in Wave 1b dogfood.

### Flag 3 — "treat the user as capable" vs error-state warmth

Voice principle 5 says lean in when the user is stuck. The `#5` visual polish spec adds `"通常 2-4 秒"` only when loading > 1.5s — explicitly to reduce anxiety. These are aligned: "stuck" includes "anxious about whether the request worked." But the brand-voice-extractor flags one potential drift: if every error message follows the matter-of-fact register exemplified in Sample 1 above, users may experience cumulative cold-feeling on a bad-network day where 3-4 errors stack. **Recommendation**: maintain matter-of-fact tone on the *first* error, but allow one fragment of human acknowledgment on the *N-th consecutive error of the same type within a session*: e.g., third extraction failure in 5 minutes → `"这次又没读到。看起来 extraction 服务今天不太稳。我先关掉自动 extraction,你专心聊;之后修好我会通知你。"` This is not warmth-as-padding — it's warmth-as-information (acknowledging the pattern the user is also seeing). **Type-A severity**: Low — speculative, would need real session telemetry to confirm. Worth keeping in Wave 2 launch+ telemetry review.

---

## Appendix B — Word-count and ceiling reference

Quick lookup for any Rodspan writer:

- **Hero copy**: ≤ 12 words (Linear / Anthropic / Notion / Granola / Cal.com all 7-10 words; Rodspan candidate is 13 character-clauses Chinese ≈ 12 English words).
- **Subheadline**: ≤ 30 words.
- **Chat reply default**: 2-4 sentences. Long-form only when user explicitly asks.
- **Button label**: ≤ 4 words / ≤ 8 Chinese characters.
- **Toast / success message**: 1 line, ≤ 60 characters.
- **Error message**: 2 lines max — what failed (1 line) + what user can do next (1 line).
- **Empty state title**: ≤ 8 words.
- **Founder essay**: no ceiling, but pace via section breaks; first section ≤ 250 words.

---

## Appendix C — Cross-references to other Rodspan specs

Voice rules in this doc are **derived** from these primary documents — when conflicts arise, primary documents win:

- `app/web/prompts/rodix_system.md` v1.3 — the operational source of truth for chat voice. Banned-phrase list and Round 1/2/3 phasing originate here.
- `app/shared/extraction/prompts/claim_extractor.md` — null-discipline + 4-8 word extraction rule. The data-layer mirror of Voice principle 2 (Null is the default).
- `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` — C-1 (tone & language) + C-2 (multi-round protocol) + S-CHAT-* scenarios are the *enforcement* layer for voice rules.
- `docs/superpowers/specs/2026-05-01-rodix-brainstorm.md` §`#8` "What I just saved" 完整 spec — origin of the "下次提到这些任一项,我会主动带回来 ↗" microcopy that became the voice anchor for Card with Promise.
- `docs/superpowers/brand/research-notes.md` — competitor reference for Anthropic + Linear borrowing target; Notion + Granola + Cal.com explicitly NOT to borrow.

When this voice guide gets updated, update inline cross-references and bump the version + date at the top.

---

*End of voice-guide.md v1.0. Junior writers: read through once, then keep this open in a tab while drafting. The Voice consistency checklist (Section 6) is the quickest pre-publish gate.*
