# Rodix Brainstorm — Session Log

**Date**: 2026-05-01
**Status**: In progress (brainstorming skill, clarifying questions phase)
**Authority**: This is an interim session record. Final spec docs (`web-product-design.md` + `marketing-site-design.md`) will be authored when brainstorm completes.
**Governing protocol**: `~/Downloads/throughline-collaboration-protocol.md` v1.2 (no human-time units, P0/P1/P2/P3 + item codes + dependencies, §5.5 rename split, §5.5.1 naming hierarchy)

---

## Naming hierarchy (per protocol §5.5.1)

| Tier | Identity | Status | Where used |
|---|---|---|---|
| 创始人网名 | Rodc | Stable | personal ID |
| 产品名(临时代号) | throughline | Stable until `#r-name-final` | code / internal spec / docs |
| 产品名(候选最终) | Rodix | **Candidate, NOT yet locked** | nothing yet — only after `#r-name-final` resolves |
| 公司名 | TBD | depends on `#r-company` | — |

**Discipline**: All user-facing copy (mockups / UI / website / email / errors) uses `[PRODUCT_NAME]` placeholder. Internal code stays `throughline_*`. Global replace `[PRODUCT_NAME]` → final name happens at the moment `#r-name-final` resolves.

---

## Strategic foundation (locked earlier this session)

### B-重 SaaS strategy

The app pivot strategy is **B-重**: server-side vault with at-rest encryption (per-user keys, KMS-managed), strict access controls, full export + delete. NOT zero-knowledge — recall/embedding requires server-side plaintext access. ADR-002 (local-first) is evolved into two layers:

- **Layer 1 (Web app, launch path)**: server-side vault, encrypted at rest, ops-trusted but operationally minimal access
- **Layer 2 (Desktop app, Phase 2)**: true local-first vault on user's machine

### A+C architectural constraints (carried forward to B-重)

1. **Storage abstraction**: web routes don't directly `import sqlite3` — go through adapter. Don't pre-design `VaultStorage` interface; let it emerge when B-重's storage layer is written.
2. **Memory engine decoupled from storage**: ✓ already done — recall evaluators are pure functions taking structured data.
3. **Frontend → API only**: ✓ already true (browser has no file access).
4. **`user_id` discipline split**:
   - **4a (now)**: API/route signatures carry `user_id`, default `"local-user"`
   - **4b (B-重)**: DB schema adds `user_id` columns + FTS5/vec indices rebuild — separate # item

### Alpha invitation split (per protocol §5.4)

- **`#r-alpha-batch1`** (P1): 5-10 共创者 / dogfooders, invited when `app/` has occupant version
- **`#r-alpha-batch2`** (P1): 15-20 testimonial sources, invited only when real features (`#claim-extraction` real-time + `#8` real version + `#9b` first-insight) are operational

---

## Locked design decisions (this session)

### Visual system

| Aspect | Lock | Notes |
|---|---|---|
| Style direction | **B · Raycast warm dark** | (vs Linear cool dark / Adaptive light+dark) |
| Background | `#18181b` | Slightly warm dark |
| Surface | `#27272a` | Card / bubble bg |
| Text primary | `#fafafa` | |
| Text secondary | `#a1a1aa` | |
| Border | `rgba(255,255,255,0.05)` | Subtle |
| **Accent** | **`#d97706` 琥珀** | Custom — NOT Raycast's `#ff5e1a` to avoid copy-cat optics |
| Font | **Inter** | (vs IBM Plex Sans) — 2、3、4、6、7 字重 via Google Fonts |
| Decorations | None | No emoji `●` adornments per Rodc's "没有 emoji 装饰" rule |

### Information architecture

**`#IA` = C · Top Tabs Equal Billing** (locked 2026-05-01 after UX skill 回测; supersedes prior 单抽屉分区 lock)

- 顶栏 3 tab: **Chat** (default) / **Vault** (with badge 数字) / **Decisions** (with badge)
- 左抽屉(汉堡)只装 conversations 列表
- 顶栏齿轮入口 → `#1a` 设置模态
- Vault badge 显示卡片总数;聊完后 `+1` 是第二次 aha 信号

**Locked product framing** (governs all future related decisions):

> Rodix 是 "AI chat with memory",不是 "memory app with chat"。
> 用户来 Rodix 是因为 ChatGPT 体验不够好,不是因为想要 vault 系统。
> Top tabs 的 hierarchy(Chat default、Vault discoverable)精确反映这个定位。

A · Always-on Vault Rail 是 "compromise"(平庸两全)、B · Vault-First Home 是 "产品野心叙事"但 alpha 阶段不可验证 + 心智冲击大。C 是产品策略对,不只是工程友好。

### IA-C cascade lock list

下游事项的具体调整(基于 IA-C 决定):

| # | 事项 | IA-C 影响 | Lock 决策 |
|---|---|---|---|
| `#2a` | Onboarding | 3 步骨架完成后落 Chat tab。Step 3 First conversation 后,推 first-insight 时跳 Vault tab 看刚生成的卡(P2 钩子) | 不改主体,加 P2 钩子描述 |
| `#3a` | 卡片管理列表 | drawer 不再装 cards;列表落 **Vault tab 主区**(全屏 list view) | 沿用 #3a 候选(A 紧凑/B 预览块/C 时间线),落点在 Vault tab |
| `#1a` | 设置面板入口 | drawer 不再装 settings;入口改为**顶栏齿轮图标** → 中央模态(模态主体不变) | 入口位置变,模态形态保持 A 中央模态 |
| `#8` | What I just saved | inline 在 chat 内出现 + **顶栏 Vault badge `+1`** = 第二次 aha 信号 | redo 中(skill 模板 + 4 信息层问题) |
| `#9a` | 历史导入 | 导入完跳 Vault tab,badge 显示导入卡片数 | 加 "完成后跳 Vault tab" 行为 |
| Drawer | 内容 | 只装 conversations(原 4 节缩为 1)。汉堡 = 切换会话 | 简化 drawer 实现 |
| `#claim-extraction` | done 标准 | **新增一条** | 见下 |

### `#8` "What I just saved" 完整 spec(signed-off 2026-05-01,改进版)

形态:**A · Card with Promise**(琥珀淡背景 + 边框 + 4 字段结构化 + promise 行)。

**4 信息层定义**:
1. **显示什么** — 4 字段对应 #claim-extraction entity 类型:
   - 主题 = topic / entity name(必填,无则不显示卡片)
   - 忧虑 = concern / fear / risk
   - 希望 = aspiration / goal / hope
   - 问题 = open question(用户提出但未回答的)
   - 缺字段不硬塞 placeholder
2. **可展开** — P1 launch:不可,默认全展示。P2(launch+30):基于 telemetry 引入"已稳定使用"自动转折叠态(类似 Adaptive Density),需 telemetry 支持
3. **触发条件 + edge case**:
   - 默认:每条 AI 回复后触发 #claim-extraction
   - Edge 1: 无可提取 entity → 不显示卡片,Vault badge 不动
   - Edge 2: #claim-extraction 失败 → 不显示卡片,后台静默重试 1 次,记 telemetry
   - Edge 3: 同主题反复抓取 → 简化为"已记下 #N · 与之前相关 ↗"
4. **Promise 兑现** — 不是文字承诺,是具体可见的兑现机制(#active-recall 触发卡)

**See → trust → verify 三段 aha 闭环**:
1. **See**: Card with Promise 显示 4 字段
2. **Trust**: Vault badge `+1`(动画:数字 highlight 琥珀)+ 切到 Vault tab 看到刚生成的卡
3. **Verify**: 后续聊到任一字段时 #active-recall 触发 recall 卡(琥珀边框 + ⚡ + AI 显式引用 open question)

**P1 实施级微调(2026-05-01 sign-off 时锁定)**:

| # | 当前 mockup | 改成 | 理由 |
|---|---|---|---|
| 1 | "下次相关时会主动 surface ↗" | "下次提到这些任一项,我会主动带回来 ↗"(英文:"I'll bring this back when relevant ↗") | 移除工程词 "surface",换成关系性叙事"带回来",跟 Rodix brand 调性一致 |
| 2 | "VAULT BROUGHT THIS BACK"(英文 caps) | "⚡ 我把这个带回来了"(英文:"⚡ I brought this back") | 中文产品里英文 caps 突兀;"带回来"跟 promise 措辞形成承诺-兑现呼应,双重 recall 信号 |
| 3 | 4 按钮当前显示 3 个(记下了 / 不相关 / 忽略),且"记下了"跟"已记下"语义重叠 | 4 按钮改:**用上了 / 不相关 / 已经想过 / 跳过** | 4 维度对应不同 telemetry 信号:用上了=action triggered, 不相关=extraction 错误, 已经想过=user resolved, 跳过=neutral non-engage。喂 #recall-quality 阈值校准 loop |

**Rodc 的反应观察(2026-05-01)**:"不是'哇'是'信任',看着像 Linear / Notion 那种克制成熟产品"。这比 wow 反应对长期价值更高。**Rodix 设计调性 = trust-evoking > wow-evoking**(Linear/Notion-grade 克制 > 闪亮 demo)。所有后续 UI 决策保持这个调性 baseline。

**移动端**: Card 全宽 stack,padding 收紧到 8px 10px,4 字段保持纵向 list。Recall 卡同样全宽,4 按钮在 <360px 屏可换行。

### `#2a` Onboarding 完整 spec(signed-off 2026-05-01)

**整体形态**: B 压缩 3 步 — Step 1 (Welcome + 价值主张合并) → Step 2 (AI 接入,C 改进版) → Step 3 (First conversation,落 Chat tab,first-insight 钩子推到 Vault tab — P2)。

**Step 2 = C · Default 推荐 + 进阶 fallback (改进版)** spec:

**视觉层级**:
- 顶栏 [PRODUCT_NAME] brand:`#d97706` 琥珀 / 18px / font-weight 700
- OpenRouter 提及在 secondary card 标题:13px 灰白文字,无 logo,无颜色
- "用我自己的 key" 是 text link,无 button 样式
→ [PRODUCT_NAME] brand 视觉权重 >> OpenRouter 提及,任何时候

**结构**:
1. Step 1 价值主张副标题:`[PRODUCT_NAME] 不绑定任何 AI 公司——你的 memory 跨任何模型`
2. Step 2 副标题:同上(brand 叙事一致)
3. Recommended card:
   - 标题:"用 OpenRouter"
   - 描述:`不需要 OpenAI / Anthropic 账号,3 分钟拿到 key 后通用 30+ 模型`(per 微调 2,告诉用户"不需要原本没有的账号")
   - "为什么是 OpenRouter" 卡块:`[PRODUCT_NAME] 不绑定任何 AI 公司,OpenRouter 让你的 memory 跨 30+ 模型自由切换`
   - Primary CTA:"用 OpenRouter →"
4. Secondary text link:"已有 OpenAI / Anthropic / Gemini key? 用我自己的 key →" — 进 step 2.5 子流程(provider grid + key input)
5. Phase 2 过渡 hint(底部 small print):"未来 [PRODUCT_NAME] Free Trial 上线后,这里会改成'用 [PRODUCT_NAME] Free 30 条 →'"
6. Skip 路径(见下)

**Skip 路径产品逻辑**(锁定 = (a),CC 推荐与 Rodc 倾向一致):
- Skip = **跳过本步,但留在 onboarding 流程里**
- 进入 step 3 first conversation 时,chat 入口显式标记"先配 AI 才能聊",用户能"了解后再决定"
- **不是**(b) 彻底跳出 onboarding 弹模态——onboarding 是 brand 信任建设,完整走完是 trust-building 资产
- 拒绝理由:(b) 让用户在没有 brand context 下进 chat,丢失价值传达,违反 skill "每步加速 aha"原则

**P1 实施级微调(2026-05-01 sign-off 时锁定,本次 4 项)**:

| # | 微调 | 实施动作 |
|---|---|---|
| 1 | 副标题硬编码"Rodix"违反 §5.5 | 改成 `[PRODUCT_NAME]` 占位,#r-name-final 解决时全局替换 |
| 2 | OpenRouter 卡片描述跟副标题重复 | 改成 `不需要 OpenAI / Anthropic 账号,3 分钟拿到 key 后通用 30+ 模型`,聚焦 OpenRouter 自身 |
| 3 | Skip 路径产品逻辑 | 锁定 = (a) skip 只跳本步不跳出 onboarding,chat 入口提示"先配 AI 才能聊" |
| 4 | Sign-off checklist 加一项 | 新增"OpenRouter 卡片描述跟副标题不重复"为常规检查项 |

**§5.5 占位合规巡检结果(2026-05-01)**:
- 当前 server (3497-) 服务文件:14 屏 1 处违规已 catch + P1 修复
- 历史 stale 文件(3441-/3472-):不再服务,archive
- Session doc 内引用:全是 §5.5.1 允许的内部讨论性使用,不算违规
- **新纪律**:CC 下次推 mockup 前主动 `grep "Rodix"` 巡检,有违规先修再推

**Brand 叙事资产(候选 tagline)**:
- `[PRODUCT_NAME] 不绑定任何 AI 公司——你的 memory 跨任何模型`
- 应用范围:onboarding 副标题(已用)+ Landing page hero(候选)+ launch 视频开头(候选)+ Founder essay 入题(候选)
- 来源:本次 brainstorm Rodc 拍板的产品 framing 具象化
- 状态:未 final 定稿,需在 Founder essay 写作时跟其他候选 tagline 一起评比

**Sign-off 检查项最终版**(供未来 onboarding step 类决策复用):
- ✓ 解法 1 措辞:brand 叙事卡块,不只是产品介绍
- ✓ 解法 2 视觉层级:[PRODUCT_NAME] brand 权重 >> 第三方 LLM 提及
- ✓ 解法 3 Phase 2 hint:小字标记切换 CTA 路径
- ✓ Skip 路径保留(skill onboarding checklist)
- ✓ Secondary BYOK 路径保留(C 内嵌 B fallback)
- ✓ **新加**:OpenRouter 卡片描述跟副标题不重复(per 微调 4)

### `#3a` 卡片管理列表 完整 spec (signed-off 2026-05-01)

**形态**: A · 时间分组 + 完整只读 detail + stats 空白态(桌面双栏 35/65 master-detail · full-bleed 撑满 viewport)。

**视觉结构**:
- 左 35%(max 480px): 时间分组(今天 / 本周 / 本月 / 历史),sticky 琥珀 date headers,组内 chronological,选中态琥珀竖条 + 左偏移
- 每行 metadata: `时间 · N 字段 · N 次 recall`(scannable 活跃度信号,Rodc 加分点)
- 右 65%: 完整 detail panel - 标题 + 来源对话 + recall 计数琥珀标签 + 4 字段块 + 关联对话引述(双向闭环) + Recall 历史 summary
- 顶栏: IA-C tabs 不变,加齿轮入口 → `#1a` 模态

**Cold start 4 级 lifecycle**(per Rodc Push 1):
- **0 张**: empty state "Your first thought saved here →" + Chat tab CTA(不显示 stats / 不显示空 list)
- **1-5 张**: 默认选中第一张(最新),右栏立刻显示 detail(消除"空架子"风险)
- **6-50 张**: 默认无选中,右栏显示 vault stats(总卡数 + 7 天活跃图 + 最常 recall 主题)
- **50+ 张**: stats + thinking trends(P2 演进项)

**Recall 历史 summary 模式**(per Rodc Push 2):
- N ≤ 3: 完整时间线 inline 显示(每条 recall + 用户 fb 详情)
- N > 3: summary 一行(`已 recall N 次 · M 次用上了 · 最近: ...`)+ 点击展开完整时间线
- 阈值 3 是 P1 假设;P2 telemetry 调
- Linear / Notion 模式

**Brand 叙事关联点**(P1 实施细节):
- 标题旁 "已被 recall N 次" 琥珀标签 → micro verify 信号(#8 promise 兑现的可见证据)
- "N 次用上了" 绿色 highlight → 商业转化第一信号
- "→ 跳到对话 #X" → chat ↔ vault 双向闭环
- stats 空白态(6+ 卡片时)→ "thinking history is your asset" 具象化

**操作 spec**:
- 删除: 单卡 ⋮ 菜单 → 二次确认 modal
- 导出: 顶栏 "导出全部 ↓" 或单卡 ⋮ "导出"
- 跳转: "→ 跳到对话 #X" 切到 Chat tab + 滚到对应 message

**P2 marker(Rodc 3 个轻量 push)**:
1. 左列"1 次 recall" 措辞 review:用户可能误读为"recall 了其他卡"。P2 telemetry 看 click-through,考虑改 "已用 1 次" 或加 hover tooltip
2. 导出格式分级:**P1 launch = Markdown only**(覆盖 90% 需求 + 工程量小 + 标准);JSON / PDF P2 看用户要什么再加
3. 导出 = brand 叙事核心(P2 实施时):
   - hover tooltip: `Export everything · You own your data`
   - 第一次点击 modal: `Choose format: Markdown · 47 cards · 2.3 MB · You can re-import anytime`
   - 这把"导出"从功能升级成承诺,跟 ADR-002 evolution 的"用户数据所有权"叙事打通

**移动响应式 (< 768px)**:
- 双栏 collapse 单列 list view
- 点击卡片 → push 全屏 detail view
- 顶部 ← 返回 list
- Linear / Mail mobile pattern

**Pre-mortem 5/5 全过 + 2 项 ★(strategic stats / 桌面横向利用率)**

### `#5` 视觉抛光收口 完整 spec (signed-off 2026-05-01)

**形态**: B · 文字 + Lucide line icons(states 视觉)+ 锁定的 design token spec。

**为什么 B**(Rodc 框架,深一层): B 不是"折中",是 Linear/Notion/Stripe 成熟 SaaS 的 visual baseline,精确匹配已锁定的 IA-C / `#8` / `#3a` 调性。
- A · 极简文字 = Vercel-CLI / 开发者工具调性 — 跟 `#8` Card with Promise 视觉权重不匹配
- C · illustration + 庆祝框 = Mailchimp / Slack 庆祝调性 — 跟 `#3a` detail panel 克制感冲突
- **B 是唯一不破坏系统一致性的选项**

**Design token spec(锁定)**:
- **Icon 库**: Lucide(open-source · MIT)
- **Icon size**: 16-18px(states)/ 22-24px(navigation)
- **Icon line stroke**: 1.5-1.8px
- **Color tokens**:
  - Error: `#ef4444`
  - Success: `#22c55e`
  - Loading + brand: `#d97706`
- **Loading animation**: 3-dot pulse,1.4s infinite ease-in-out,3 dots staggered 0.2s

**4 micro-adjustments (P1 实施)**:

| # | 微调 | 实施动作 |
|---|---|---|
| 1 | LOADING 加预期文案 | 仅在 loading > 1.5s 时显示 secondary 灰色文字 `通常 2-4 秒`。设定预期 = 减少焦虑 = brand 诚实度 micro-moment。<1.5s 不显示(正常请求不打扰) |
| 2 | ERROR "去设置" affordance 升级 | 文字 link → 琥珀边框 ghost button。Recovery 是关键 next-step,需要明确 affordance |
| 3 | SUCCESS 加 "Your data, your file" brand 叙事 | 文案 `✓ 导出 47 张卡片 · 2.3 MB · markdown` / `下载已到你的浏览器 · Your data, your file`。无庆祝框(保持 B 克制),brand 叙事不丢,跟 `#3a` "You own your data" hover tooltip + 导出 modal 形成 brand 一致性 |
| 4 | 7 项 cumulative pre-push checklist 入协议 v1.4 §7.5 | Rodc 改协议;CC 主动跑这 7 项,缺任何一项 = 协议违反 |

**3 级 affordance hierarchy (per Rodc 微调 2)**:

| 层级 | 形态 | 用途 |
|---|---|---|
| **Primary CTA** | 琥珀实心(`#d97706` bg / white text) | 常规动作("继续 / 保存 / 用 OpenRouter / 去 Chat") |
| **Recovery action** | 琥珀边框 ghost(transparent bg / `#d97706` border + text) | error 后的下一步("去设置 / 重试") |
| **Secondary link** | 灰色文字 link | 辅助资源("更多帮助 ↗ / 查看文档") |

**移动响应式**:icon size 22→18,布局保持(icon 左 + 文字右,不堆叠)。

**全 7 项 cumulative pre-push checklist 跑过 ✓**(per `feedback_design_judgment_failures.md`)。

### `#9a` 历史导入解析 完整 spec (signed-off 2026-05-01)

**形态**: C · Reality-aware async + email-primary fallback。1 屏 2 路径(推荐启动 export → wait → 提醒回来 / 已有 zip → 直接 drop)。

**核心产品 framing(Rodc 加分点)**: C 解构了"zip 完成"作为 launch must 的瓶颈地位:
- A/B 模型: zip → first use → activation(zip 是瓶颈)
- **C 模型: first use → activation → zip(锦上添花)**

C 把 1-3 小时 wait 变成产品 first session 窗口。Activation rate 不再依赖 zip 完成率;Retention 不依赖 import 成功;用户在等 zip 时已经经历 `#8` Card with Promise + #active-recall 完整 product loop。

**4 micro-adjustments (P1 实施)**:

| # | 微调 | 实施 |
|---|---|---|
| 1 | Wait 期间 messaging 优化 | `你不用等 ChatGPT — [PRODUCT_NAME] 现在就开始记。等 zip 回来,几小时前的对话会合并到你今天 vault 里。` 关系性叙事 + 让用户预期 zip 回来会发生什么 = 降低焦虑 |
| 2 | Push notification 文案 | 中:`你的 ChatGPT 历史回来了。继续刚才的思考 →` 英:`Your ChatGPT history is ready. Continue what you were thinking →` "继续刚才的思考"呼应用户 wait 期间已在 [PRODUCT_NAME] 思考的事实 |
| 3 | Email 提醒文案 | Subject: `继续 [PRODUCT_NAME] · 历史可以合并了`。Body 关键: `你 X 小时前在 [PRODUCT_NAME] 启动了 ChatGPT export。OpenAI 刚刚把 zip 发了过来。` + `[回 [PRODUCT_NAME] 上传 →]` 大按钮 + `上传后,你今天聊的 X 张卡片会跟过去几年的 thinking 合并到一个 vault 里。`。"你今天聊的 X 张卡片"让用户回头看自己的进展,引导回来不是因为"导入功能",是"看自己今天做了什么" |
| 4 | Wait 期间 vault visual signal | vault tab 顶部 banner: `⏱ ChatGPT 历史合并中 · 预计 X 小时`。设置页面 status: `Import status: waiting for OpenAI · 启动于 14:23`。让用户随时看到等待进展 = 产品诚实度延伸 |

**Engineering risk note(per Rodc)**: 浏览器 Notifications API 只在网页打开时有效。用户关 tab 后 push 触发不了。

**所以 Email 是真正的 fallback,不是次要选项**。文案 + 投递时机要按 Email 为主设计。

**P1 实施分级**:
- 浏览器 push(网页开着时)
- **Email**(关 tab 后的真正回流通道,主要)
- P2 加 Web Push / FCM(真后端 push 系统)

**P1 launch must scope**:
- ChatGPT export 只(Claude / Cherry / Markdown 显式标"P2 即将支持")
- 浏览器 Notifications API push(无后端)+ Email(主 fallback,已有 #b-auth)
- "等待期间 vault 增长 + 几小时后合并" merge 逻辑

**移动响应式**: 2 路径 stack(推荐先,直接上传后);drop zone 在 mobile 改"选择 zip"按钮。

**Pre-mortem 5/5 全过 + 4 项 ★**(空前最强): like-me ★ / metric vs goal ★ / reactive vs strategic ★ / edge vs main ★ / 桌面横向 ✓

### Device priority phasing (locked 2026-05-01)

**Phase 1 launch**: 桌面 Web 主战场,移动端响应式做到"不崩"即可。
- Mockup 主图按桌面布局,组件标注移动响应式策略,**不做独立移动 mockup**
- `#5` 视觉抛光 scope:桌面 viewport + 移动 CSS 不错乱(字体 / 按钮 / 无横向滚动)
- Launch 弹药 100% 桌面截图 / 视频

**Phase 2 launch+30**: 加 `#6b` PWA install UX + Tauri 桌面 native(评估升 P2)。

**Phase 3 launch+90**: 看数据加 iOS / Android native(`#m-ios-native` / `#m-android-native`,新 P3 backlog)+ B2B 团队版。

完整规则见 `memory/project_device_priority.md`。

### `#claim-extraction` done 标准更新(per Rodc directive)

`#claim-extraction` (P0) 的 done 标准追加一条:

> **Vault badge 增长在 alpha 测试中可观察** — 即:聊一次 → 顶栏 Vault badge 数字 `+1` → 切到 Vault tab 看到刚生成的卡片。这是 IA-C "Top Tabs Equal Billing" 产品策略能否成立的核心机制。如果 claim extraction 实时触发不通,顶栏 Vault badge 不长 → IA-C 退化为"装饰 tabs",产品定位空喊。

**遗留风险** (写入 launch readiness 检查):
- Vault badge 数字依赖 `#claim-extraction` 实时触发
- alpha 测试必须验证: 聊完 5 条 → Vault tab badge 显示 5 (或对应 claim 数)
- 不通 = `#claim-extraction` 不算完成 + IA-C 信任打折

### Per-subitem visual decisions

| # | Subject | Lock | Alternative considered |
|---|---|---|---|
| `#1a` | Settings panel layout | **A · 中央模态** | B 右侧滑入 / C 全屏替换 |
| `#8` | "What I just saved" 模块样式 | **A · Card with Promise (改进版,signed-off 2026-05-01)** | 见 `#8` 完整 spec 节 |
| `#2a` | Onboarding 整体 shape | **B · 压缩 3 步**(Step 2 = C 改进版,signed-off 2026-05-01) | 见 `#2a` 完整 spec 节 |
| `#3a` | 卡片管理列表 | **A · 时间分组 + 完整只读 detail + 4 级 cold start + Recall summary**(signed-off 2026-05-01) | 见 `#3a` 完整 spec 节 |
| `#5` | 视觉抛光收口(state visual style + token spec) | **B · 文字 + Lucide line icons**(signed-off 2026-05-01) | 见 `#5` 完整 spec 节 |
| `#9a` | 历史导入解析 | **C · Reality-aware async + email-primary fallback**(signed-off 2026-05-01) | 见 `#9a` 完整 spec 节 |

---

## Pending design decisions (in brainstorm queue)

| # | Subject | Status | Mockup pushed |
|---|---|---|---|
| `#3a` | 卡片管理列表形态 | **In flight** — Rodc to decide | `10-cards-list.html` (A 紧凑 / B 预览块 / C 时间线) |
| `#5` | 视觉抛光收口 | After `#3a` | — |
| `#9a` | 历史导入解析 + 上传 UI | After `#5` | — |

After all locked → write 2 spec docs → invoke `writing-plans` skill.

---

## Item priority snapshot (per protocol §5.1-5.4)

### P0 (Launch Blockers)

App: `#1a` 设置面板 (P0) · `#8` 占位 (P0) · `#claim-extraction` (P0)
B-重: `#b-auth` · `#b-encryption` · `#b-multitenant` · `#b-paddle` · `#b-deploy` · `#b-security-review` · `#b-privacy-policy`
Web: `#w-landing` · `#w-pricing` · `#w-privacy-page` · `#w-launch-video` · `#w-launch-assets`
Rodc: `#r-company` · `#r-domain` · `#r-social` · `#r-name-final`

### P1 (Launch Must, simplifiable)

`#2a` Onboarding · `#3a` 卡片管理 · `#5` 视觉抛光 · `#8` 真功能 · `#9a` 历史导入 · `#recall-quality` · `#active-recall-base` · `#w-features` · `#w-docs` · `#w-press-kit` · `#w-founder-essay` · `#r-alpha-batch1` · `#r-alpha-batch2`

### P2 (Launch+30 days)

`#1b` recall threshold · `#2b` first-insight integration · `#3b` 结构化视图 · `#4` 对话管理 · `#6a` PWA shell · `#9b` history import insights · `#decision-journal-lite` · `#active-recall-lowthreshold` · `#w-changelog` · `#r-trademark` · `#rename-internal`

### P3 (Backlog)

`#6b` PWA install UX · `#7` README + 截图 (until `app/` promotes public) · `#w-blog` · `#w-about` · 移动端 native · 桌面 native · B2B · LAN P2P sync · "Past Me" persona · etc.

---

## Brainstorm artifacts location

- **Visual companion mockups**: `.superpowers/brainstorm/3441-1777602959/content/`
  - `01-design-language.html` — original visual style options (now stale, before Rodix rename)
  - `02-design-language-rodix.html` — Rodix rename applied
  - `03-font-direction.html` — Inter vs IBM Plex Sans → Inter locked
  - `04-info-architecture.html` — IA A/B/C → A locked
  - `05-what-i-just-saved.html` — initial #8 options
  - `06-settings-panel.html` — #1a A/B/C → A locked
  - `07-what-i-just-saved-revisit.html` — #8 with attribute table → A locked
  - `08-onboarding-shape.html` — Onboarding (with stale "Rodix" hardcode)
  - `09-onboarding-shape-placeholder.html` — Onboarding with `[PRODUCT_NAME]` (correct) → B locked
  - `10-cards-list.html` — `#3a` cards list (in flight)
- **Server**: `http://localhost:54754` (running in background, 30-min idle timeout)
- **Auto-cleanup**: `.superpowers/` is gitignored

## Memory references (cross-session persistence)

- `feedback_collab_protocol.md` — banned time units, P0/P1/P2/P3 discipline
- `reference_collab_protocol.md` — pointer to protocol document
- `project_rodix_name.md` — naming hierarchy + placeholder discipline + `#r-domain`/`#r-social` recommendations

---

## Next milestones (no time estimates per protocol)

1. **Rodc decides `#3a` form** → unblocks remaining brainstorm
2. **`#5` visual polish + `#9a` 历史导入解析 brainstormed** → all visual decisions locked
3. **Two spec docs written** at `docs/superpowers/specs/`:
   - `web-product-design.md` (Rodix app — 14 sub-items + done criteria)
   - `marketing-site-design.md` (Rodix marketing site — 10 modules + structure)
4. **Spec self-review** → user review → approval
5. **Invoke `writing-plans` skill** → implementation plan with item codes + priority + dependencies

## Now-unblocked Rodc items (per `#r-name-final` candidate)

These can be started in parallel even before `#r-name-final` formally resolves (assuming Rodix sticks):

- `#r-domain`: check availability for rodix.ai / .com / .io / .app
- `#r-social`: claim @rodix / @rodix_ai / GitHub `rodix-app`
- `#r-company`: longest external lead-time, start immediately

---

*Session in progress. Update this file as more decisions lock.*
