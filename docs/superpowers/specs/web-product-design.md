# Rodspan Web Product Design Spec

**Status**: Brainstorm signed-off 2026-05-01. Implementation-ready (P1 launch).
**Authority**: This is the canonical spec for the Rodspan web product (chat + vault). Companion: `marketing-site-design.md`. Source of decisions: `2026-05-01-rodspan-brainstorm.md` (session log).
**Governing protocol**: `~/Downloads/throughline-collaboration-protocol.md` v1.4.

---

## 1. Product framing

> Rodspan 是 "AI chat with memory",**不是** "memory app with chat"。
> 用户来 Rodspan 是因为 ChatGPT 体验不够好,不是因为想要 vault 系统。

This framing governs every design decision — chat is the primary canvas, vault is the differentiated layer. Information architecture (top tabs with Chat default), visual hierarchy, and feature priorities all derive from this.

**Design tone baseline**: trust-evoking > wow-evoking. Linear / Notion / Stripe-tier 克制成熟,not Mailchimp / Slack 性格化庆祝。每条 UI 决策保持这个 baseline。

---

## 2. Naming + copy discipline

Per protocol §5.5.1:
- **临时代号**: `throughline` — 内部代码 / module / vault path / env vars / 内部文档
- **候选最终**: `Rodspan` — 候选 brand,**未最终敲定**(等 `#r-name-final` 正式 resolve)
- **placeholder**: `[PRODUCT_NAME]` — 所有用户可见文案(UI 字符串 / 网站 / 邮件 / 错误消息)

Rule: **don't hardcode "Rodspan" or "throughline" in user-facing copy**. The moment `#r-name-final` resolves → global replace `[PRODUCT_NAME]` → final name.

Internal code retains `throughline_*` until `#rename-internal` (P2, post-launch) executes the migration.

---

## 3. Visual design system

### 3.1 Colors

| Token | Hex | Use |
|---|---|---|
| Background | `#18181b` | App canvas (warm dark, B Raycast-style) |
| Surface | `#27272a` | Cards, bubbles, input bg |
| Surface raised | `#1c1c1f` | Modal, popover, drawer |
| Text primary | `#fafafa` | Body, titles |
| Text secondary | `#a1a1aa` | Subtitles, metadata |
| Text tertiary | `#71717a` | Captions, hints |
| Border subtle | `rgba(255,255,255,0.05)` | Section dividers |
| Border medium | `rgba(255,255,255,0.08)` | Modal borders |
| **Accent (brand)** | **`#d97706`** | **琥珀,custom — NOT Raycast `#ff5e1a`** |
| Error | `#ef4444` | Error icon / border / text |
| Success | `#22c55e` | Success icon / "用上了" highlight |

### 3.2 Typography

- **Font**: **Inter** (Google Fonts) — weights 400 / 500 / 600 / 700
- Mobile fallback: Chinese OS default (PingFang / Noto Sans CJK) — acceptable degradation
- P2 review:重审 IBM Plex Sans / Geist / 自定义,目前 Inter 锁定但边界可疑

### 3.3 Spacing + radius

- Border radius: 6-10px(modal/card 8-10px;button 6-7px;chip/badge 6px;icon 5px)
- Spacing scale: 4 / 6 / 8 / 10 / 12 / 14 / 18 / 22 / 28 / 36 px
- Density: 平衡型(Linear/Notion-tier),不紧凑也不宽松

### 3.4 Icons

- **Library**: Lucide(open-source · MIT)
- **Default size**: 16-18px (states / inline) / 22-24px (navigation)
- **Line stroke**: 1.5-1.8px

### 3.5 Animation

- Loading: 3-dot pulse,1.4s infinite ease-in-out,3 dots staggered 0.2s
- Transitions: 150-200ms ease default
- Loading "通常 2-4 秒"灰色 secondary 文字仅在 loading > 1.5s 时显示

### 3.6 State affordance hierarchy

| 层级 | 形态 | 用途 |
|---|---|---|
| **Primary CTA** | 琥珀实心 (`#d97706` bg / white text) | 常规动作("继续 / 保存 / 用 OpenRouter / 去 Chat") |
| **Recovery action** | 琥珀边框 ghost (transparent / `#d97706` border + text) | error 后的下一步("去设置 / 重试") |
| **Secondary link** | 灰色文字 link | 辅助资源("更多帮助 ↗ / 查看文档") |

---

## 4. Information architecture

**`#IA = C · Top Tabs Equal Billing`** (locked).

**结构**:
- 顶栏 3 tabs:**Chat**(default)/ **Vault**(数字 badge)/ **Decisions**(数字 badge)
- 左抽屉(汉堡):只装 conversations 列表
- 顶栏齿轮入口 → `#1a` 设置模态
- Vault badge 显示卡片总数;聊完 `+1` 是第二次 aha 信号

**为什么 C**: chat-first 心智不破(主流 ChatGPT/Claude 用户 mental model),但 Vault tab 立刻 surface 产品差异化(memory 是真实可访问的东西不是黑盒)。`#claim-extraction` 实时触发是 IA-C 信任成立的核心机制(badge 不长 = tabs 是装饰)。

**Cascade rules**(每 IA 决策影响下游):

| 下游 | IA-C 调整 |
|---|---|
| `#3a` 卡片管理列表 | 落 Vault tab 主区(全屏 list view,drawer 不再装) |
| `#1a` 设置面板 | drawer 不再装 settings;入口改为顶栏齿轮 |
| `#8` What I just saved | inline 在 chat 内 + 顶栏 Vault badge `+1` = 第二次 aha |
| `#9a` 历史导入 | 导入完跳 Vault tab + badge 显示导入卡片数 |
| Drawer | 只装 conversations |

---

## 5. Feature specs

### 5.1 Onboarding (`#2a`)

**整体形态**: B 压缩 3 步。

| Step | 内容 |
|---|---|
| Step 1 | Welcome + 价值主张合并屏。副标题: `[PRODUCT_NAME] 不绑定任何 AI 公司——你的 memory 跨任何模型`。CTA: Continue |
| Step 2 | AI 接入(独立屏,不复用 `#1a` 全字段模态)— 见 5.2 |
| Step 3 | First conversation。落 Chat tab。`#2b` first-insight magic moment 钩子(P2 跳 Vault tab 看刚生成的卡) |

**Skip 路径**(锁定 = a):每步可 skip;**skip 仅跳过本步,不跳出 onboarding 流程**。第 3 步 chat 入口标"先配 AI 才能聊",defer 不 escape。

### 5.2 Onboarding Step 2 — AI 接入(C 改进版)

**形态**: C · Default 推荐 + 进阶 fallback。

**视觉层级**:
- 顶栏 [PRODUCT_NAME] brand: `#d97706` / 18px / 700-weight(显眼度远超 OpenRouter 提及)
- Recommended card(琥珀边框):标题"用 OpenRouter" + 描述"不需要 OpenAI / Anthropic 账号,3 分钟拿到 key 后通用 30+ 模型" + "为什么是 OpenRouter"卡块(brand 叙事化)+ Primary CTA"用 OpenRouter →"
- Secondary link:"已有 OpenAI / Anthropic / Gemini key? 用我自己的 key →" → 进 step 2.5 子流程(provider grid + key input)
- Phase 2 hint(small print):"未来 [PRODUCT_NAME] Free Trial 上线后,这里会改成'用 [PRODUCT_NAME] Free 30 条 →'"
- Skip: 跳过本步,进 step 3

### 5.3 Settings panel (`#1a`)

**形态**: A · 中央模态(从顶栏齿轮进入)。

**字段**:
- LLM Provider(下拉:OpenRouter / OpenAI / Anthropic / Ollama 本机)
- API Key 输入 + Test connection 按钮 + 失败诊断
- Vault 路径
- Save / Cancel

**实施细节**:
- Test connection 必做,失败诊断要明确给"key 格式不对 / 没权限 / network error"
- Key 加密存储(per `feedback_collab_protocol.md` placeholder discipline 也适用)
- 移动端模态自动全屏

### 5.4 Chat surface

**Primary canvas**(Chat tab default)。

#### 5.4.1 Layout 共通元素

- 顶栏 IA-C tabs + 齿轮 + 汉堡(打开会话 drawer)
- 消息流容器(flex column,自动滚动到底)
- Composer:textarea + send button(琥珀实心)

#### 5.4.2 Default state — empty(对话历史为空)

> **Phase**: **Wave 1b target** (deferred per 2026-05-01 Rodc adjust). Wave 1a 阶段使用 single-line hint;真正的 empty-state pattern 跟 `#8` 真功能 + `#intent-classifier` + `#rename-user-facing` 一起 ship。

**Setup signal**:`conversation.length === 0`(localStorage `throughline.app.conversation.v1` 为空数组或缺失)。

**Layout**(消息流容器内,垂直居中):
1. **Brand anchor**:大字 `Rodspan`(56px desktop / 40px mobile,Inter 600 字重,letter-spacing -0.02em)
2. **Tagline**:一句话(14px,`--text-secondary`,max-width 480px),Wave 1a placeholder = `AI chat with memory · Your memory crosses every model`,Rodc 后续 lock 精确文案
3. **Sample prompt cards**(3-4 张,纵向 stack,max-width 480px):
   - Wave 1a placeholder copy(Rodc 后续 lock):
     - `我最近在想 [话题]`
     - `帮我整理这个想法`
     - `问 [Claude / ChatGPT / Gemini]: …`
     - `上传一份资料一起聊`
   - 点击行为:**prefill composer input**(NOT 直接 send)— 用户编辑后再发,避免一键发模板的尴尬
   - 视觉:左对齐文本,深色 surface,hover 时 accent border + soft amber bg
4. Composer 在底部(共通元素)

**Why empty state matters**:Rodc browser test 2026-05-01 发现没 anchor 的空 canvas → 用户不知道下一步 → 产品 dumb 印象。Per `#5` v1.1 empty-state pattern。

**Per Wave**:Wave 1a 必须有 default empty state(本节);Wave 1b `#3a`/`#9a`/`#1a` 引入更多空状态时各自的 plan 负责。

#### 5.4.3 Active state — 有对话历史

- 消息流(用户 right-aligned amber-tinted bubbles + AI left-aligned surface bubbles)
- 无 role label(per Issue 4 决策 Option A · 行业标准:bubble 位置 + 颜色已经区分,文字 label 是 noise)
- 每条 AI 回复后:`#8` What I just saved 卡片(见 5.5)
- 当 `#active-recall` 触发时:recall 卡片(琥珀边框 + ⚡ + AI 显式引用)在 AI 回复前出现

#### 5.4.4 Error state(在 active state 内)

per `#5` v1.1 error-state pattern:
- 一句话人话(Chinese)— 不暴露 model 名字 / status code / upstream chain
- ghost recovery button "查看配置"(Wave 1a 打开 server-status dialog 作为 stop-gap;Wave 1b `#1a` settings panel 上线后切到 settings)
- 详细错误日志(model chain / upstream JSON / stack)只 `console.error` 给 dev,不渲染给用户

### 5.5 What I just saved (`#8`)

**形态**: A · Card with Promise(改进版)。琥珀淡背景 + 边框 + 4 字段结构化 + promise 行。

**4 信息层 spec**:

| | spec |
|---|---|
| 显示什么 | 4 字段对应 #claim-extraction entity 类型: 主题 / 忧虑 / 希望 / 问题。缺字段不硬塞 placeholder |
| 可展开 | P1 launch:不可,默认全展示。P2:基于 telemetry 引入"已稳定使用"自动转折叠态 |
| 触发条件 | 默认每条 AI 回复后触发;Edge:无 entity → 不显示;extraction 失败 → 静默重试 1 次;同主题反复 → 简化"已记下 #N · 与之前相关 ↗" |
| Promise 兑现 | 不是文字承诺,是 `#active-recall` 触发卡(琥珀边框 + ⚡ + AI 显式引用 open question)+ Vault badge `+1` 动画 |

**See → trust → verify 三段 aha 闭环**:
1. **See**: Card with Promise 显示 4 字段
2. **Trust**: Vault badge `+1`(数字 highlight)+ 切到 Vault tab 看到刚生成的卡
3. **Verify**: 后续聊到任一字段时 #active-recall 触发 recall 卡

**P1 实施级 micro-adjustments**:
1. "下次提到这些任一项,我会主动带回来 ↗"(不用 "surface")
2. "⚡ 我把这个带回来了"(英文 caps 改 sentence case + 关系性叙事)
3. 4 按钮: **用上了 / 不相关 / 已经想过 / 跳过**(对应不同 telemetry 信号,喂 #recall-quality 阈值校准 loop)

### 5.6 Cards management (`#3a`)

**形态**: A · 时间分组 + 完整只读 detail + stats 空白态(桌面双栏 35/65 master-detail · full-bleed)。

**视觉结构**:
- 左 35%(max 480px): 时间分组(今天 / 本周 / 本月 / 历史),sticky 琥珀 date headers,选中态琥珀竖条
- 每行 metadata: `时间 · N 字段 · N 次 recall`(scannable 活跃度信号)
- 右 65%: 完整 detail panel — 标题 + 来源对话 + recall 计数琥珀标签 + 4 字段块 + 关联对话引述(双向闭环) + Recall 历史 summary

**Cold start 4 级 lifecycle**:
- **0 张**: empty state "Your first thought saved here →" + Chat tab CTA
- **1-5 张**: 默认选中第一张(最新),右栏立刻显示 detail
- **6-50 张**: stats 空白态(总卡数 + 7 天活跃图 + 最常 recall 主题)
- **50+ 张**: stats + thinking trends(P2)

**Recall 历史 summary 模式**:
- N ≤ 3: 完整时间线 inline
- N > 3: summary 一行(`已 recall N 次 · M 次用上了 · 最近: ...`)+ 点击展开
- 阈值 3 P1 假设;P2 telemetry 调

**操作**:
- 删除: 单卡 ⋮ 菜单 → 二次确认
- 导出: 顶栏 "导出全部 ↓" 或单卡 ⋮ "导出"。**P1 = Markdown only**(JSON/PDF P2)
- 跳转: "→ 跳到对话 #X" 切到 Chat tab + 滚到对应 message

**P2 markers**:
1. 左列"1 次 recall"措辞 review(可能误读为"recall 了其他卡",P2 telemetry 看 click-through)
2. 导出 = brand 叙事核心(P2 实施 hover tooltip "Export everything · You own your data" + first-click modal "Choose format: Markdown · 47 cards · 2.3 MB · You can re-import anytime")

### 5.7 History import (`#9a`)

**形态**: C · Reality-aware async + email-primary fallback。1 屏 2 路径。

**核心 framing**: 把 1-3 小时 wait 变成 first session 窗口。Activation 不依赖 zip。

**2 路径**:
- **Recommended**: 启动 ChatGPT export → 用产品 → 提醒回来 → 上传
- **已有 zip**: 直接 drop → parse → preview → import

**4 micro-adjustments**:
1. Wait messaging: "你不用等 ChatGPT — [PRODUCT_NAME] 现在就开始记。等 zip 回来,几小时前的对话会合并到你今天 vault 里。"
2. Push notification copy: 中:"你的 ChatGPT 历史回来了。继续刚才的思考 →" 英:"Your ChatGPT history is ready. Continue what you were thinking →"
3. Email reminder copy: Subject "继续 [PRODUCT_NAME] · 历史可以合并了" + body 关键 "你 X 小时前在 [PRODUCT_NAME] 启动了 ChatGPT export... + 你今天聊的 X 张卡片会跟过去几年的 thinking 合并到一个 vault 里"
4. Wait state visual signal: vault tab 顶部 banner "⏱ ChatGPT 历史合并中 · 预计 X 小时" + Settings status

**Engineering**: 浏览器 Notifications API 只在 tab 开时有效 → **Email 是真正 fallback,不是次要选项**。P1 = browser push (tab 开) + Email (主); P2 = Web Push / FCM。

**P1 launch scope**: ChatGPT export only(Claude / Cherry / Markdown 显式标"P2 即将支持")。

---

## 6. Item priority + dependencies

| # | Subject | Priority | Depends |
|---|---|---|---|
| `#1a` | Settings panel: provider/key/vault path/test connection | **P0** | — |
| `#2a` | Onboarding 3 步骨架 | **P1** | — |
| `#3a` | 卡片管理 + Recall summary + 4 级 cold start | **P1** | — |
| `#4` | 对话管理(重命名/归档/删除) | P2 | — |
| `#5` | 视觉抛光(B + Lucide tokens + 4 micro-adj) | **P1** | 视觉系统已锁 |
| `#6a` | PWA shell | P2 | — |
| `#8` 占位 | placeholder UI | **P0** | — |
| `#8` 真功能 | Card with Promise + recall trigger | **P1** | `#claim-extraction` |
| `#9a` | 历史导入(C async + email primary) | **P1** | — |
| `#claim-extraction` | 实时触发 claim 抽取 | **P0** | — |
| `#recall-quality` | Recall 校准 + threshold-learning | **P1** | 真实数据 |
| `#active-recall-base` | standard threshold | **P1** | `#recall-quality` |

P2 backlog: `#1b` recall threshold slider · `#2b` first-insight integration · `#3b` 结构化视图 · `#4` 对话管理 · `#6a` PWA shell · `#9b` history import insights · `#decision-journal-lite` · `#active-recall-lowthreshold` · `#rename-internal`

---

## 7. Done criteria checklist (signed-off)

- [ ] `#1a` 设置模态:provider 切换 + key 输入 + test connection + 失败诊断 + 加密存储 ✓
- [ ] `#2a` Onboarding 3 步:Step 1 价值主张 + Step 2 AI 接入(C 改进版)+ Step 3 chat,Skip = (a) ✓
- [ ] `#3a` Vault tab 主区:35/65 master-detail + 4 级 cold start + Recall summary 阈值 3 ✓
- [ ] `#5` 视觉系统:B + Lucide + 4 micro-adj + 3 级 affordance hierarchy ✓
- [ ] `#8` Card with Promise:4 字段 + 3 段 aha + 3 micro-adj + 4 按钮 telemetry 维度 ✓
- [ ] `#9a` 历史导入:C async + email primary + 4 micro-adj + wait state visual ✓
- [ ] **Vault badge 增长在 alpha 测试中可观察**(per `#claim-extraction` done 标准追加)

---

## 8. Cross-cutting

### Device priority

Phase 1 launch = 桌面 Web 主战场,移动响应式 "不崩"。Phase 2 加 PWA install + Tauri。Phase 3 看数据加 native。Mockups 桌面布局,组件标移动响应式策略,**不画独立移动 mockup**。

### Brand 叙事

- "trust > wow" baseline
- "AI chat with memory" not "memory app with chat"
- "Your data, your file"(导出文案)
- "[PRODUCT_NAME] 不绑定任何 AI 公司——你的 memory 跨任何模型"(产品定位句,见 marketing-site-design.md tagline)
- "诚实告知 reality"(import 1-3 小时 wait + LLM 限制 + 隐私承诺都用这调子)

### ADR-002 evolution

Layer 1(Web app 现 launch): server-side vault, encrypted at rest with per-user keys, strict access controls, full export + delete。**NOT zero-knowledge**。

Layer 2(桌面 native, Phase 2): true local-first vault on user's machine。

---

## 9. References

- Brainstorm session log: `2026-05-01-rodspan-brainstorm.md`
- Marketing site spec: `marketing-site-design.md`
- Collab protocol: `~/Downloads/throughline-collaboration-protocol.md` v1.4
- UX skill: `~/Downloads/SKILL-ux-design-judgment.md`
- Memory:
  - `feedback_collab_protocol.md` — no time units rule
  - `feedback_design_judgment_failures.md` — 5 failure modes + 1 positive lesson + 7-item pre-push checklist
  - `project_rodix_name.md` — naming hierarchy
  - `project_device_priority.md` — Phase 1/2/3 device phasing
  - `reference_ux_skill.md` — skill pointer
  - `reference_collab_protocol.md` — protocol pointer

---

*Spec version 1.0 (2026-05-01) · Signed-off all design decisions · Ready for writing-plans phase*
