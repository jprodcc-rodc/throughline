# Rodspan Product Test Scenarios

> **For agentic workers:** This is the canonical user-journey verification list. Run relevant scenarios at end of every task / wave / before any "done" claim. If a scenario fails: trigger fix dispatch, do NOT mark task complete. This document is version-controlled — CC may extend, Rodc reviews.

**Version**: v1.3 (2026-05-01)  
**Scope**: Wave 1a (demo-ready) + Wave 1b (fully functional). Wave 2-3 scenarios added when those waves start.  
**Author**: 外部 Opus 起草 v1.0/v1.1 → Rodc review → CC 维护扩展(v1.2: S-CHAT-VISUAL · v1.3: C-2 分阶段 protocol + S-CHAT-6)

---

## How to use this document

### For CC (self-verification)

Every task has **relevant scenarios** listed in its `## References` section. Before claiming task done:

1. Identify which scenarios cover this task
2. Run each scenario manually (browser walk-through)
3. For each scenario, verify "应该看到 / 不应该看到" 全部对
4. Any failure → trigger fix dispatch with scenario name + observed gap
5. All pass → task can be marked done

**Special rule**: Do NOT mark a task done while any "应该看到" is missing or any "不应该看到" is present. Even one failure means task is not done.

### For Rodc (sanity check)

When CC claims wave done, Rodc walks 3-5 random scenarios at desktop + iPad to spot-check. **Rodc does not run all 25** — that's CC's job. Rodc only verifies CC's verification.

### Naming convention

- `S-OB-N` = Onboarding scenarios (Step / Skip / Reset)
- `S-CHAT-N` = Chat behavior scenarios (System prompt / Follow-up / Tone)
- `S-CARD-N` = Card with Promise scenarios (When triggers / When doesn't)
- `S-VAULT-N` = Vault tab scenarios (Cards management / Cold start)
- `S-NAV-N` = Navigation / IA scenarios (Tab switching / State preservation)
- `S-IMPORT-N` = History import scenarios
- `S-SETTINGS-N` = Settings panel scenarios
- `S-CROSS-N` = Cross-feature integration scenarios
- `S-MOBILE-N` = Mobile-specific scenarios
- `S-EDGE-N` = Edge cases / error handling

---

## Foundational Conventions

These conventions inform all scenarios. Violations of any are **automatic failures** regardless of which scenario.

### C-1: Tone & language

- AI **never** uses these phrases (Rodspan is a thinking partner, not a generic empathetic chatbot):
  - "我在这里"
  - "我陪你"
  - "慢慢说"
  - "我在认真听"
  - "无论是什么问题"
  - "你可以从最模糊的地方开始"
  - "说出来的过程本身就能让思绪变得更清晰"
  - "你想说说看吗"
  - 任何 "I'm here for you" 类英文等价
- AI **never** outputs emoji (no `😊`, `❤️`, `✨`, etc.) unless user uses emoji first
- AI responses default to **2-4 sentences** unless user explicitly asks for long form

### C-2: AI behavior patterns

#### C-2.1 Topic class → behavior shape

- User shares a **thoughtful** topic (life decision / creative work / learning / abstract thinking) → enter the multi-round protocol in C-2.2.
- User asks a **factual / technical** question (how does X work / what is Y) → AI directly answers, no follow-up.
- User asks **chitchat** (天气 / 时间 / 简单问候) → AI brief response, no follow-up.

#### C-2.2 Multi-round protocol for thoughtful topics

A thoughtful conversation has phases. The AI **must not** loop on follow-up questions across all rounds — that produces an interview-bot experience, not a thinking partner.

- **Round 1**: AI asks **1-2 specific follow-up questions** to understand. Concrete angles only (what triggered this / what specifically worries them / what's at stake / what they've tried). Generic "你担心什么 / 长期目标是什么" repeated across rounds is forbidden.
- **Round 2**: AI may ask **one more** follow-up if a genuine ambiguity remains. Otherwise begin synthesizing — pick up the most specific or surprising thing the user said.
- **Round 3 and beyond**: AI **stops asking follow-ups** and pivots fully to reflection / synthesis / perspective. Hard rule: by round 3 the user has given enough; the AI's job becomes naming patterns, engaging with concrete details (quote their actual words), or pushing on gaps and assumptions. A single observation is more valuable than another question.

If the user's last message contained a concrete specific (e.g., 用户在第 3 轮说 "看地球的时候,现在没有什么担心的"), the AI **must** engage with that concrete thing first ("看地球" — that's a sublime image; what changed when you said it just now?). It must NOT bridge to another generic "你担心什么 / 长期目标" question.

#### C-2.3 Examples

- Wrong (round 1): 用户"我在考虑换工作" → AI 直接给"换工作要考虑 ABC..."
- Right (round 1): 用户"我在考虑换工作" → AI 问"是什么 trigger 你这次想换?当前最让你不舒服的具体是什么?"
- Wrong (round 3): 用户已说 3 轮 → AI 第 3 轮再问"你担心什么 / 长期目标是什么"
- Right (round 3): 用户已说 3 轮 → AI 反思 / synthesis / 接住用户最近一句的具体细节

### C-3: State integrity

- Onboarding **completed or skipped** → all UI state reset to "fresh user" (no test chat residue, no orphan data)
- Tab switch (Chat → Vault → Chat) → previous tab state preserved (scroll position, selected card, draft message)
- Browser refresh → all persistent state survives (chat history if any, vault, settings)
- Browser refresh during onboarding → onboarding restarts from step 1 (don't half-resume)

### C-4: Card with Promise trigger discipline (LLM-classifier driven, NOT string-match)

#### C-4.1 核心原则

每条 user message **先过 LLM classifier**,不用固定词组匹配。

**Classifier 任务**:把每条 user message 分成 3 类:
- **chitchat**: 寒暄 / 招呼 / 短回应 / 闲聊,没有具体思考内容
- **thoughtful**: 包含具体担心 / 希望 / 困惑 / 决策 / 反思,需要 thinking partner 介入
- **factual**: 询问客观事实 / 技术问题 / 知识查询,需要直接答

#### C-4.2 路由规则

| Classifier 结果 | AI behavior | Card 触发 |
|---|---|---|
| chitchat (confidence > 0.8) | 简短回 (1-2 sentences) | ✗ 不触发 |
| thoughtful (confidence > 0.8) | 先问 follow-up,然后给观点 | ✓ 触发 |
| factual (confidence > 0.8) | 直接答,简洁准确 | ✗ 不触发 |
| 任何分类 confidence ≤ 0.8 | **fallback 当 thoughtful 处理** | 触发(safe default) |
| Classifier timeout / error | fallback 当 thoughtful + log alert | 触发(safe default) |

**关键设计**:fallback bias 偏 thoughtful,**宁可触发 follow-up 浪费用户 1 次问答,不可漏抓 thoughtful → 用户失望产品 dumb**。

#### C-4.3 边界优化

为了不浪费 classifier call:
- 用户 message < 5 字符 → 跳过 classifier 直接当 chitchat(`嗯` `哦` 这种明显的)
- 用户 message > 200 字符 → 跳过 classifier 直接当 thoughtful(长文本默认是 thoughtful)
- 5 ≤ message ≤ 200 字符 → classifier 决定

#### C-4.4 Classifier model 选择

- **dev mode**: 跟 chat 同 model (`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`)
  - 验证准确率,如 < 85% raise 给 Rodc 决策
- **production mode**: 推荐独立 cheap fast model (Claude Haiku 4.5 / Gemini 2.5 Flash / 类似)
  - 跟 chat model 解耦,chat 升级不影响 classifier
  - 成本 ~$0.0001/call,延迟 100-300ms

#### C-4.5 Classifier accuracy gate

跟 #claim-extraction 一样,classifier 必须过 eval:

```
Eval set: 60 条真实用户消息样本
- 20 chitchat 样本
- 25 thoughtful 样本(包括各种边界:短 thoughtful / 长 chitchat)
- 15 factual 样本

人工标注 ground truth → classifier 跑 → 算准确率

Threshold: 准确率 >= 85% (P1 baseline)。
< 85% → raise 给 Rodc 决策:
  (a) 切 paid model
  (b) 改 prompt
  (c) 接受临时 + telemetry 调
```

#### C-4.6 AI response 检验(独立维度)

C-4 控制 user intent 路由。AI response 质量是**独立维度**:

- AI response **永远不应该**包含 C-1 列出的废话短语(那是 system prompt failure,不是 trigger discipline failure)
- 如发现 AI response 含 C-1 phrase → log + alert + Rodc raise(改 system prompt,不是改 trigger)
- 不要用"AI response 含 C-1 phrase 就不触发 Card"作为补丁(治标不治本)

---

## Wave 1a Scenarios (demo-ready)

### S-OB-1: 全新用户首次访问

**Setup**: 清空 localStorage(模拟全新设备)→ 打开 `http://127.0.0.1:8765`

**应该看到**:
- Onboarding step 1 自动出现(全屏 wizard)
- Step 1: brand + tagline `[PRODUCT_NAME] 不绑定任何 AI 公司——你的 memory 跨任何模型`
- Progress indicator: `Step 1 of 3`
- Primary CTA: "Get started" (琥珀色实心按钮)
- Secondary link: "Already have an account? Sign in" (灰色)

**不应该看到**:
- 任何 chat 界面 / chat 历史
- 任何 vault 数据 / 卡片
- 任何 toast / notification
- 旧版黑色蓝色调(应是新视觉:深灰背景 + 琥珀 accent)

---

### S-OB-2: Onboarding 完整走完(dev mode)

**Setup**: dev mode (RODIX_DEV=1 或 hostname rodix.local)

**操作流程**:
1. Step 1 → 点 "Get started" → 进 Step 2
2. Step 2 → 看到 "DEV MODE · 已自动配置" 提示 → 点 "继续(已自动配置)" → 进 Step 3
3. Step 3 → 看到 "你想从哪个话题开始?" 或类似 → 点 sample prompt 或自己输入 → 完成

**应该看到**:
- Progress 正确递增 (1/3 → 2/3 → 3/3)
- Step 切换有平滑过渡(不是硬跳)
- 完成后:**Chat tab 全新空状态**,顶部 brand + Vault badge `0`
- localStorage `onboarding_completed = true`

**不应该看到**:
- 任何上次测试遗留的 chat 对话
- 任何 vault 旧数据
- 完成后 onboarding 再次跳出
- Step 之间的状态不一致(比如 Step 2 选了 OpenRouter,Step 3 显示用的是别的)

---

### S-OB-3: Onboarding 部分跳过

**Setup**: 全新用户

**操作流程**:
1. Step 1 → "Get started"
2. Step 2 → 点 "先跳过"
3. Step 3 → 进入

**应该看到**:
- Step 2 跳过,直接到 Step 3
- Step 3 内容正常显示
- 完成 Step 3 后,Chat tab 显示 hint "**先配 AI 才能聊** [配置]"
- 点 hint 链接 → 跳到 Settings 模态(#1a)
- localStorage `onboarding_completed = true` 但 `pending_ai_setup = true`

**不应该看到**:
- 跳过后直接退出 onboarding(应该继续 Step 3)
- Chat tab 没有 hint 但用户也没法发消息(用户陷入死循环)

---

### S-OB-4: 浏览器中途刷新 onboarding

**Setup**: 全新用户,onboarding step 2 中途

**操作流程**:
1. 进入 onboarding,走到 Step 2
2. 浏览器刷新(F5)

**应该看到**:
- 重新从 Step 1 开始(不半路恢复)
- Step 1 内容跟首次一致

**不应该看到**:
- "你已完成 Step 1,从 Step 2 继续"(此 P1 不实施 resume,简化)
- onboarding 跳过 / 跳到 chat

---

### S-OB-5: 已完成用户回访

**Setup**: localStorage `onboarding_completed = true`

**操作流程**: 打开 `http://127.0.0.1:8765`

**应该看到**:
- **跳过 onboarding**,直接进 Chat tab
- 之前的 chat 历史 / vault 状态保留

**不应该看到**:
- onboarding 再次跳出
- chat 历史丢失

---

### S-CHAT-VISUAL: Chat tab default empty state

> **Phase**: **Wave 1b target** (deferred per 2026-05-01 Rodc adjust). Sample-prompt copy needs Rodc-written content; brand anchor needs `#r-name-final` lock + `#rename-user-facing`. Implemented together with `#8` real feature + `#intent-classifier`.

**Setup**: 已完成 onboarding · 进入 Chat tab · 对话历史为空(localStorage `throughline.app.conversation.v1` 为空 / `Onboarding.reset()` 后回访 / `startNewConversation` 后)

**应该看到**(Wave 1b target):
- **居中 brand anchor**:`Rodspan` 56px (desktop) / 40px (mobile),Inter 600 字重(after `#r-name-final` lock + `#rename-user-facing`)
- **Tagline**:一句话简介,14px,`--text-secondary` 颜色,max-width 480px(Rodc 后续 lock 精确文案)
- **3-4 个 sample prompt cards**:左对齐文本,深 surface 背景,hover 时琥珀 border + soft bg
  - 点击 → **prefill composer**(NOT 自动发送)
  - 用户可编辑后再发
- 顶栏(brand · Vault badge · 新对话 · 服务器状态)
- 底部 composer(textarea + 琥珀 send button)

**不应该看到**:
- 空白 canvas(brand / tagline / prompts 任一缺失 → fail)
- 字体跳脱 Inter(任何 system-default fallback 是失败信号)
- 点击 sample prompt 直接发出请求(应只 prefill input)
- 缺 hover affordance(border-color 不变 = 死 button)

**Why this scenario exists**:
2026-05-01 Rodc 浏览器测试发现 chat tab 进去 80% 空白 → 用户不知道做什么 → "产品 dumb" 印象。也是 `#5` v1.1 empty-state pattern 在 chat surface 的实例化。Wave 1a 阶段保留旧 single-line hint(non-blocking · CC self-verify);Wave 1b 整批替换。

---

### S-CHAT-1: 用户输入 thoughtful 想法

**Setup**: 已完成 onboarding,在 Chat tab(Wave 1b 后:经过空状态点击 sample prompt 或直接打字)

**输入**: `我最近在想要不要换工作`

**应该看到**:
- AI 回复**先问 1-2 个具体 follow-up**,例如:
  - "是什么让你这次想换?当前工作让你不舒服的具体是什么?"
  - "你之前换过几次工作?这次跟之前的考虑有什么不同?"
- AI 回复 **2-4 sentences**(不长篇大论)
- AI 回复**不含 C-1 列表的废话**
- AI 回复**不含 emoji**
- AI 回复**不直接给"换工作要考虑 ABC"答案**(因为 follow-up 还没问)

**不应该看到**:
- "我在这里 / 慢慢说 / 我在认真听" 类共情套话
- emoji
- 长篇大论的 generic 换工作建议
- 直接给 framework 没问 follow-up

---

### S-CHAT-2: 用户输入 chitchat

**Setup**: Chat tab

**输入**: `你好` 或 `今天天气怎么样` 或 `在吗`

**应该看到**:
- AI 简短友好回复 (1-2 sentences)
- 例:"在的。今天想聊什么?"

**不应该看到**:
- AI 触发 follow-up question(chitchat 不需要)
- AI 长篇 introspection prompt
- Card with Promise 触发(chitchat 不该记)

---

### S-CHAT-3: 用户输入技术 / 事实性问题

**Setup**: Chat tab

**输入**: `Python 里 list 和 tuple 有什么区别` 或 `什么是 OAuth`

**应该看到**:
- AI **直接回答**,简洁准确 (3-6 sentences)
- 不问 follow-up(技术问题已经明确)

**不应该看到**:
- AI 问 "你为什么想了解这个" 类的 follow-up
- AI 给空洞共情("学习是个好习惯")
- Card with Promise 触发(纯技术问题非个人思考)

---

### S-CHAT-4: Classifier 边界 case 测试

**Setup**: Chat tab,classifier ready

**测试用例**(每个独立 verify):

#### Case 4a: 短 thoughtful(字数少但内容有重量)

**输入**: `我想做宇航员` (7 字)

**应该看到**:
- Classifier 判 thoughtful (confidence > 0.8) — 这不是 chitchat,是表达了一个 aspiration
- AI **问 follow-up**(per S-CHAT-1):"是什么 trigger 你想到这个?是最近的事还是一直的想法?"
- Card with Promise **触发**(可能用户后续会展开)

**不应该看到**:
- 因为字数少就当 chitchat 不触发
- AI 共情套话

#### Case 4b: 长 chitchat(字数多但内容空洞)

**输入**: `你好啊朋友最近怎么样啊我也挺好的就是随便看看你这个东西` (28 字)

**应该看到**:
- Classifier 判 chitchat (confidence > 0.8) — 字虽多,无具体思考内容
- AI 简短友好回应:"在的。今天想聊什么具体的?"
- Card 不触发

**不应该看到**:
- 因为字数多就当 thoughtful 触发 follow-up
- 触发 Card

#### Case 4c: 极短(< 5 字)边界

**输入**: `嗯` 或 `哦`

**应该看到**:
- 跳过 classifier(per C-4.3)直接当 chitchat
- AI 极简回应或不主动 prompt
- Card 不触发

#### Case 4d: 边界模糊低 confidence

**输入**: `今天有点累` (5 字 - 可能是 chitchat 也可能是 thoughtful entry)

**应该看到**:
- Classifier 可能输出 thoughtful confidence 0.6 / chitchat confidence 0.4
- 触发 fallback 规则(per C-4.2):**当 thoughtful 处理**
- AI 问 follow-up:"是身体上累还是心理上?发生什么了?"
- Card 触发(safe default)

**不应该看到**:
- 直接当 chitchat 不响应(漏抓真 thoughtful)
- AI 给空洞回应("注意休息哦")

#### Case 4e: Classifier 失败 fallback

**Setup**: 故意 mock classifier timeout

**输入**: 任意 thoughtful 消息

**应该看到**:
- Classifier timeout → fallback 当 thoughtful
- AI 正常问 follow-up
- log alert (开发可见,用户不可见)

**不应该看到**:
- 用户体验 degraded (网络错 / 等待 spinner 卡死)
- 直接报错告诉用户 "classifier 失败"

---

### S-CHAT-5: 完整对话流(thoughtful + AI follow-up + 用户回答)

**Setup**: Chat tab

**对话**:
- 用户: `我在想要不要换工作`
- AI: [问 follow-up]
- 用户: `当前工作收入稳定但业务在收缩,有 2 个 offer 但都不完美`
- AI: [基于 follow-up 答案,给具体观点]

**应该看到**:
- 第一轮:AI 问 follow-up(per S-CHAT-1)
- 第二轮:AI 给**有针对性的观点**,引用用户提到的具体细节("收入稳定 vs 业务收缩"、"2 个不完美 offer")
- 第二轮后:**Card with Promise 触发**(用户已表达完整 thoughtful content)
- Card 4 字段填合理:
  - 主题:换工作决策
  - 忧虑:业务收缩 / offer 不完美
  - 希望:更好的工作机会
  - 问题:如何在不完美中选择

**不应该看到**:
- AI 第二轮回复跟用户回答脱节(说明 AI 没用上 follow-up 的答案)
- Card 4 字段填空洞或错位
- Card 第一轮就触发(应该等用户充分表达再触发)

---

### S-CHAT-6: 多轮对话深度推进(C-2.2 protocol enforcement)

**Setup**: Chat tab · 跟 thoughtful 主题进行 3+ 轮对话

**对话样例**(来自 2026-05-01 Rodc live walk 的真实 bug 复现):
- 用户: `我想做宇航员`
- AI(轮 1): 问 1-2 个具体 follow-up,例如"是什么 trigger 你想到这个?长期想了多久了?"
- 用户: `因为能上太空`
- AI(轮 2): 可再问一个真有 ambiguity 的 follow-up,或者开始 synthesize。例如"上太空里你最在乎什么 — 失重、距离、孤独?"
- 用户: `看地球的时候,现在没有什么担心的`
- AI(轮 3): **必须 pivot 到 reflection / synthesis,不能再循环 follow-up**

**应该看到**(第 3 轮 AI 回复):
- 接住用户具体输入(`看地球` / `现在没有什么担心的`)— 直接 engage with 这个 specific thing
- Reflection / synthesis / 观点(可能是命名 pattern · 引用之前轮的具体细节 · 指出用户思考里的 tension 或 gap)
- 单一 observation 比再问一个问题更有价值
- 例:"`看地球`是个安静的画面 — 你刚说没担心,这是不是恰好是你最想从太空带回来的?"

**不应该看到**(C-2.2 hard violations):
- AI 第 3 轮还在问 generic follow-up(`你担心什么` / `长期目标关联` / `你想说说看吗`)
- AI 第 3 轮重复之前轮已经问过的问题 shape(变体也算 — `担心 → 挑战 → 风险` 是同一形状)
- AI 忽略用户提的具体词(`看地球`)绕回 generic question
- "interview bot" 感觉(每轮都问 1-2 个问题,从不给观点)
- 用户已答 3 轮但 AI 从未引用用户原话中的任何具体词

**Why this scenario exists**:
2026-05-01 Rodc live walk:用户跟 AI 跑 "我想做宇航员" → 3 轮 → AI 一直在问 follow-up loop,从未接住 `看地球` 这种具体细节。问题根因是 system prompt + C-2 v1.1 写得"必须问 follow-up"太硬。v1.2 引入分阶段 protocol 修这个 anti-pattern。

---

### S-CARD-1: Card 触发后的 Vault badge 动画

**Setup**: Chat tab,刚触发了一张 Card with Promise

**应该看到**:
- 顶部 Vault badge 数字 +1(从 0 → 1)
- Badge 有 brief amber pulse 动画(~600ms)
- Card 渲染在 AI 回复下方,琥珀色边框 + 4 字段 + promise 行 "下次提到这些任一项,我会主动带回来 ↗"

**不应该看到**:
- Badge 数字不变
- Badge 闪一下又消失
- Card 颜色偏离琥珀色 (#d97706)

---

### S-CARD-2: AI response 含 C-1 废话(应判为 system prompt 失败)

**Setup**: Chat tab

**模拟**: AI 回复包含 "我在这里 / 慢慢说 / 我陪你" (C-1 列出的废话)

**应该看到**:
- 这是 **system prompt failure 信号**,不是 trigger discipline issue
- 系统应 log + alert(dev / Rodc 可见)
- 触发 Rodc raise → 改 system prompt(治本)
- Card 触发逻辑独立判定(by C-4 classifier on user message)

**不应该看到**:
- 用 trigger 判断打补丁("AI 含 C-1 → 不触发 Card") — 这是治标不治本
- 用户体验异常(用户不应感知到 alert)

**Note**: 这条 scenario 主要给 dev 用。production 应该几乎不会发生(system prompt lock 后)。如频繁发生,说明 system prompt 没真正 lock 进 model。

---

### S-NAV-1: Tab 切换状态保留

**Setup**: 已有几条 chat + 几张 vault cards

**操作流程**:
1. Chat tab 输入了一段未发送的草稿
2. 切到 Vault tab
3. 切回 Chat tab

**应该看到**:
- 草稿仍在 input(未丢失)
- chat 历史滚动位置保留
- 之前的对话气泡仍在

**不应该看到**:
- 草稿消失
- chat 滚动到顶部 / 底部(应保持原位)
- chat 历史变空

---

### S-NAV-2: Vault badge 数字一致性

**Setup**: 跨多次访问

**应该看到**:
- Vault badge 数字 = vault 实际卡片数(随时一致)
- 新增 / 删除卡片后 badge 立刻同步

**不应该看到**:
- Badge 显示 5 但 vault 里 3 张
- 刷新后 badge 重置成 0(应从 backend 读真实计数)

---

### S-MOBILE-1: iPad 横屏访问

**Setup**: iPad (768-1024px viewport),浏览器输 `http://192.168.x.x:8765`

**应该看到**:
- 完整加载,无 horizontal scroll
- 字体清晰可读 (16px+)
- 按钮可触达(44px+ tap target,per WCAG)
- Chat input 不被键盘遮挡

**不应该看到**:
- 横向滚动条
- 字小到看不清
- 按钮挤在一起难以点击

---

### S-MOBILE-2: 手机竖屏 (375px)

**Setup**: iPhone SE viewport (375px)

**应该看到**:
- Layout 自适应单列
- Master-detail (Vault tab) 折叠成 list-only,点 card 推 fullscreen detail + back ←
- Onboarding 各 step 单列展示
- Card with Promise 4 字段保持纵向

**不应该看到**:
- 横向 scroll
- 文字 overflow 出 viewport
- Button 重叠 / 挤压

---

### S-EDGE-1: 网络断开

**Setup**: Chat tab,关掉网络(开发者工具 Network → Offline)

**操作**: 输入消息发送

**应该看到**:
- Error state: "连接失败,稍后重试" + Lucide alert-circle icon + ghost recovery button
- 用户消息保留在 input(可重新发送)

**不应该看到**:
- 静默失败(用户不知道哪出错)
- 消息直接消失
- App 卡死

---

### S-EDGE-2: 模型 API 返回错误 (401 / 5xx)

**Setup**: 故意配错 API key 或模型 down

**操作**: 发送消息

**应该看到**:
- Error state 区分 3 种:
  - Format wrong: "Key 格式不对,检查一下?"
  - No permission: "Key 无权限,看一下账户?"
  - Network: "暂时连不上,稍后重试"
- 每个都有 ghost recovery button

**不应该看到**:
- 通用 "出错了"(不告诉用户是什么错)
- Stack trace 暴露给用户

---

### S-SETTINGS-1: Dev mode 默认值预填

**Setup**: dev mode (`RODIX_DEV=1` 或 hostname `rodix.local`)

**操作**: 打开 Settings 模态(齿轮图标)

**应该看到**:
- 顶部横幅:"DEV MODE · 默认免费模型"
- Provider: OpenRouter (预填)
- Model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (预填)
- Key field: 显示 `RODIX_DEV` env 提供的 key (masked,只显示后 4 位)

**不应该看到**:
- 强制用户输 key(dev mode 应自动)
- 横幅缺失
- 默认值是别的 model(应锁到 nvidia 30b a3b)

---

### S-SETTINGS-2: Production mode 强制 BYOK

**Setup**: production mode (无 `RODIX_DEV`)

**操作**: 全新用户走 onboarding step 2

**应该看到**:
- Step 2 显示 OpenRouter 推荐 card + secondary BYOK link
- 用户必须输 provider + key 才能继续
- "继续(已自动配置)" CTA 不出现

**不应该看到**:
- 自动跳过 step 2
- 默认值预填
- DEV MODE 横幅(production 不该有)

---

## Wave 1b Scenarios (fully functional)

### S-VAULT-1: 0 卡片冷启动

**Setup**: vault 完全空(全新用户 + 0 cards)

**操作**: 切到 Vault tab

**应该看到**:
- 完整 empty state: 居中图标 (Lucide file-text 32px line stroke 1.2px)
- Title: "Your first thought saved here →"
- Hint: 简短解释 + Chat tab CTA
- 无 list / 无 stats / 无 sticky headers

**不应该看到**:
- 空 list(产品 dumb)
- "暂无数据" 这种 generic empty
- Stats 区块(0 卡片不该有 stats)

---

### S-VAULT-2: 1-5 卡片冷启动

**Setup**: vault 有 3 张卡片(today/本周内)

**操作**: 切到 Vault tab

**应该看到**:
- 35/65 master-detail layout
- 左 list: 时间分组 sticky headers ("今天" 琥珀色)
- 默认选中第一张卡(顶部)
- 右 detail panel: 完整渲染选中卡 (4 字段 + recall 历史 + 关联对话引述)

**不应该看到**:
- detail panel 空着(应自动选第一张)
- 时间分组错(7 天前的卡进了"今天")
- Stats 区块(< 6 张不该有 stats)

---

### S-VAULT-3: 6-50 卡片正常态

**Setup**: vault 15 张卡片,跨多日

**操作**: 切到 Vault tab

**应该看到**:
- 35/65 layout
- 左 list: 时间分组 (今天 / 本周 / 本月 / 历史) - 空 group 跳过
- 默认 NO selection,右侧显示 stats:
  - 总卡数 (15)
  - 7 天活跃图
  - 最常 recall 主题 (placeholder if no recall yet)
- 点 card → 切换到 detail view

**不应该看到**:
- 默认选中第一张(应空 detail + stats)
- 缺时间分组(应有 sticky headers)

---

### S-VAULT-4: Card 删除二次确认

**Setup**: Vault tab,选中一张 card

**操作**: 点 ⋮ → 删除

**应该看到**:
- 确认 modal: "永久删除这张卡?这将删除关联的 N 次 recall 记录。"
- "取消" + "确认删除" 两个 button (确认 = error red)
- 确认后:卡从 list 消失 + Vault badge -1 + recall 记录 cascade 删除

**不应该看到**:
- 直接删除无确认
- Cascade 删除失败(留下 orphan recall events)

---

### S-VAULT-5: Markdown 导出

**Setup**: Vault tab,有几张 cards

**操作**: 点 "导出全部 ↓"

**应该看到**:
- 触发文件下载 (`vault-export-YYYY-MM-DD.md`)
- 下载后 toast: "47 张卡片 · 2.3 MB · markdown / 下载已到你的浏览器 · Your data, your file"
- markdown 文件结构:每张卡 frontmatter (date / topic) + 4 字段 sections

**不应该看到**:
- 下载失败 / 文件损坏
- Toast 缺 brand 叙事("Your data, your file")
- markdown 内容混乱(应清晰按时间排序)

---

### S-CARD-3: Active Recall 触发(Wave 1b real feature)

**Setup**: vault 已有几张卡片(主题 A)。用户在 Chat tab 输入跟主题 A 相关的新问题。

**操作**: 用户发送消息

**应该看到**:
- AI 回答之前 / 同时,在 chat stream 出现 **Recall 触发卡**:
  - 标签: "⚡ 我把这个带回来了"
  - 内容: 引用旧卡的相关字段 + 时间 + 链接 "→ 跳到 Vault 查看"
  - 4 个反馈按钮: "用上了 / 不相关 / 已经想过 / 跳过"
- AI 回答利用了召回的旧卡内容(引用具体细节)

**不应该看到**:
- 召回卡跟当前问题不相关(误召回)
- 召回卡每次都触发(应有 threshold,> 0.75 才触发)
- AI 回答没引用召回内容(召回了但没用)

---

### S-CARD-4: 同主题去重(连续 3 条 same topic)

**Setup**: 用户连续 3 条都聊"换工作"主题

**应该看到**:
- 第 1 条: 完整 Card with Promise (4 字段)
- 第 2 条: 完整 Card (新内容 / 新角度)
- 第 3 条: **简化 Card** "已记下 #N · 与之前相关 ↗"
- 简化 card 视觉跟完整不同(更紧凑,无 4 字段展开)

**不应该看到**:
- 连续 3 个完整 card(产品 noisy)
- 第 3 条不触发任何 card(应该至少有 reference)

---

### S-IMPORT-1: ChatGPT export 直接上传

**Setup**: 用户已有 ChatGPT export zip 文件

**操作**:
1. Settings 或 Onboarding step 4 → 进入 import view
2. 点 "已有 zip · 直接上传"
3. Drop zone 拖入 zip

**应该看到**:
- Zip 上传成功后:preview 显示
  - Conversation count
  - Date range
  - Sample first 3 conversation titles
- Selection options: All / Last 6 months / Last 90 days / Custom date range
- "Import" CTA 启动

**不应该看到**:
- Zip 解析失败无错误提示
- Preview 缺关键信息

---

### S-IMPORT-2: ChatGPT export 推荐路径(等待期)

**Setup**: 用户没 zip,选推荐路径

**操作**:
1. 点 "启动 export → 跳到 ChatGPT 设置"
2. 浏览器开新 tab 到 ChatGPT export 页

**应该看到**:
- Email + push 两个 checkbox(默认勾选)
- "等邮件期间,你可以继续用 [PRODUCT_NAME]" 提示
- 后台 schedule 一个 2h 后的 reminder
- Vault tab 顶部出现 banner: "⏱ ChatGPT 历史合并中 · 预计 X 小时(启动于 14:23)"

**不应该看到**:
- 用户必须等待无法继续用产品
- 没有任何后台 reminder(用户被遗忘)

---

### S-IMPORT-3: Import 完成后 vault 合并

**Setup**: 用户启动了 import + 上传了 zip + 处理完成

**应该看到**:
- 卡片合并到 vault
- **卡片保留原始 timestamp**(import 时间 ≠ 卡片 timestamp)
- Vault tab 时间分组按真实日期(几个月前的对话进"历史"组)
- 总卡数大幅增长

**不应该看到**:
- 所有 imported 卡时间标记成 "今天"(失去时间维度)
- 跟今天的 native 卡冲突(应能区分但都在 vault 里)

---

### S-CROSS-1: Onboarding → 第一次 chat → 第一张卡

**Setup**: 全新用户

**操作流程**:
1. 走完 onboarding
2. Chat tab 输入第一条消息(thoughtful)
3. 收到 AI 回复

**应该看到**:
- 整体 flow 流畅,无中断
- 第一条 chat 触发第一张 Card
- Vault badge 从 0 → 1 动画
- 用户可以切到 Vault 看到这张卡

**不应该看到**:
- 中间 flow 卡住 / 错误
- 第一张卡内容空洞 / 错位
- Vault tab 进去找不到刚生成的卡

---

### S-CROSS-2: Settings 改 model → chat 立即使用新 model

**Setup**: 已 working 状态

**操作流程**:
1. 打开 Settings 模态
2. 改 model (e.g., 切到 OpenAI gpt-4)
3. 保存 + 关闭 modal
4. Chat 发新消息

**应该看到**:
- 新消息使用新 model 回答
- 之前的 chat 历史不影响(只影响新对话)

**不应该看到**:
- 仍用旧 model
- 改 model 后所有历史 chat 重置

---

### S-CROSS-3: 删 vault card → recall trigger 不再用这张

**Setup**: 有 vault card A,之前触发过 recall

**操作流程**:
1. Vault tab 删除 card A
2. Chat 输入跟 card A 相关的新问题

**应该看到**:
- Recall **不触发**(因为 source card 已删)
- AI 正常回答,无召回卡

**不应该看到**:
- 仍触发 recall 但点击链接 404
- 出现 "card not found" error

---

## Cross-cutting verification

### Visual consistency (全 scenarios 适用)

每个 scenario 都隐式 verify:
- 颜色: 深灰背景 (#18181b) + 琥珀 accent (#d97706) + Inter 字体
- 按钮 3-tier: Primary 实心 / Recovery ghost / Secondary link
- States: Loading 3-dot pulse + 1.5s 阈值 / Error Lucide alert / Success Lucide check + 品牌叙事 / Empty pattern
- Icons: Lucide line-stroke 1.5-1.8px

如有任何视觉跳脱(老色号 / 老字体 / 缺 icon)→ 视为 scenario 失败。

### Accessibility baseline

- 所有 interactive elements 有 `aria-label` 或 visible text
- Focus state 可见(键盘 tab navigation)
- Color contrast WCAG AA (text 4.5:1 / large text 3:1)
- Tap targets ≥ 44x44px (mobile)

### Performance baseline

- 首屏加载 < 2s (本地 dev server)
- Tab 切换 < 100ms (instant feel)
- Chat AI 回复首字 < 3s (model latency 不算)
- Card 触发动画 ≤ 600ms

---

## How CC dispatches scenario verification

### Per task

每个 per-feature plan 在 `## References` section 列出 relevant scenarios。

例:
```markdown
## References
- Scenarios: S-OB-1, S-OB-2, S-OB-3, S-OB-4, S-OB-5, S-MOBILE-1, S-MOBILE-2
```

implementer 完成后,subagent flow:
1. spec review (existing)
2. code review (existing)
3. **scenario verification** (NEW step):
   - dispatch fresh subagent
   - subagent runs each listed scenario in browser (puppeteer / manual sim)
   - report PASS / FAIL per scenario
4. 全 PASS → mark complete
5. 任一 FAIL → fix dispatch with scenario name + observed gap

### Per wave

每 wave done 之前,Rodc walks 3-5 random scenarios at desktop + iPad to spot-check CC's verification claim.

Spot-check FAIL → wave 不算 done,fix dispatch。

### 维护

CC 在每个 wave 实施时,如果发现 scenario 没覆盖到的 user journey:
- 加新 scenario 到这份文档
- Commit message: `docs: add scenario S-XXX-N for <feature>`
- Rodc 不需 review 每个新 scenario,只在 wave 末统一过一遍

---

## Open scenarios (Wave 2-3 + Launch+)

These are placeholders for scenarios to be added when those waves start. NOT to verify in Wave 1a/1b.

- **Wave 2**: Active recall threshold tuning / Decision journal lite
- **Wave 3**: Auth (signup / verify email / password reset / session) / Encryption / Multi-tenant / Paddle (subscribe / cancel / refund) / Privacy policy display
- **Launch+**: Real public chat with anonymous user / High-volume vault performance / Mobile native APP

When those waves start, CC extends this doc with new scenarios.

---

## Failure mode reference

If you hit one of these patterns, **stop and re-think before fixing**:

### F-1: 修了一个 scenario 触发另一个失败

cause: 改动有 side effect / 没考虑 cross-feature interaction
解法: 不修单点,review affected scenarios 一起处理

### F-2: scenario 描述跟实施时不符

cause: scenario 写得太抽象 / 太具体
解法: 修 scenario 描述,跟 Rodc + Opus sync,不是修代码 fit scenario

### F-3: scenario PASS 但 Rodc spot-check FAIL

cause: scenario 没覆盖到这个 user journey
解法: 加新 scenario,然后 fix

---

## Version history

- **v1.0 (2026-05-01)**: 初版。25 scenarios cover Wave 1a + 1b。外部 Opus 起草。
- **v1.1 (2026-05-01)**: Rodc 反馈后 chitchat detection 改 LLM classifier(不再固定词组)。C-4 重写 / S-CHAT-4 改 5 cases / S-CARD-2 重新 frame as system prompt failure。
- **v1.2 (2026-05-01)**: Rodc browser test 后加 S-CHAT-VISUAL(Wave 1b target,chat tab default empty state · brand anchor + tagline + sample prompts)。Issue 3 (error tech 隐藏) 落 Wave 1a;Issues 1/2/4(rename / chat empty / message labels)deferred to Wave 1b 整批跑(等 #r-name-final lock + Rodc 写 sample prompt copy + #8 real / #intent-classifier 同步)。S-CHAT-1 setup 也补充提及 sample prompt path(forward-looking)。
- **v1.3 (2026-05-01)**: Rodc live walk 暴露 multi-round follow-up loop 反模式。C-2 重写为分阶段 protocol(round 1: 1-2 follow-up · round 2: 最多再 1 个 follow-up 或 synthesize · round 3+: 必须 pivot 到 reflection / synthesis,接住用户具体输入)。新增 S-CHAT-6 多轮对话深度推进 scenario。`prompts/rodix_system.md` 同步加分阶段 + 反模式禁令。

---

*Rodspan Product Test Scenarios · CC self-verification reference · Rodc spot-check reference*
