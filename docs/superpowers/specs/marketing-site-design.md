# Rodix Marketing Site Design Spec

**Status**: Skeleton signed-off 2026-05-01(visual system + structure + module 优先度 + 对标参考)。**Copy TBD by Rodc**(per Rodc directive: "文案这块等我,改一次重写所有页面成本太高,先别动")。
**Authority**: Companion to `web-product-design.md`. Visual system shared. Source of decisions: `2026-05-01-rodix-brainstorm.md`.
**Governing protocol**: `~/Downloads/throughline-collaboration-protocol.md` v1.4.

---

## 1. Visual system (inherited from web product)

完整 token spec 见 `web-product-design.md` §3. 关键摘要:

- **Style**: B Raycast warm dark · `#18181b` bg / `#27272a` surface
- **Accent**: `#d97706` 琥珀(custom,跟 Raycast 拉开距离)
- **Font**: Inter(P2 review IBM Plex / Geist / 自定义)
- **Icons**: Lucide line icons,16-24px,1.5-1.8px stroke
- **Tone baseline**: trust-evoking > wow-evoking
- **3 级 affordance hierarchy**: Primary 实心 / Recovery ghost / Secondary link

**反面教材**(避免):
- ChatGPT 当前 landing(太拼贴)
- 默认 Tailwind template(千篇一律)
- 中国 SaaS 出海风格(过度堆砌)
- 2023 AI 风(渐变紫色)
- 2024-2025 SaaS"现代化"陷阱(默认 Inter + 16px radius + 大量留白 + 渐变 = 没差异化)

---

## 2. Brand 叙事核心

**候选 tagline**(brainstorm 中浮现,Rodc to validate during copy phase):

> `[PRODUCT_NAME] 不绑定任何 AI 公司——你的 memory 跨任何模型`
>
> `[PRODUCT_NAME] doesn't bind to any AI company. Your memory crosses every model.`

应用范围:
- Onboarding Step 1 + Step 2 副标题(已用)
- Landing page hero(候选)
- Launch 视频开场(候选)
- Founder essay 入题(候选)

**核心叙事支柱**(推导自所有产品决策):
1. "AI chat with memory" — chat 是产品,memory 是差异化(不是 chat 工具,也不是 memory 工具)
2. "诚实告知 reality" — ChatGPT export 1-3 小时不装作 instant;隐私承诺不夸大成 zero-knowledge
3. "Your data, your file" — 导出 = 资产,不是功能
4. Linear / Notion / Stripe-tier 克制成熟,不是 Mailchimp / Slack 庆祝

---

## 3. Site map (10 modules)

| # | Module | Priority | 对标 |
|---|---|---|---|
| `#w-landing` | Landing page | **P0** | Linear / Raycast / Cursor |
| `#w-features` | Features 子页 | **P1** | Linear features / Notion use cases |
| `#w-pricing` | Pricing | **P0** | Linear pricing / Superhuman / Raycast Pro |
| `#w-privacy-page` | Privacy / Security | **P0** | Proton / 1Password / Anthropic trust |
| `#w-about` | About | P3 | Linear about / Stripe about |
| `#w-blog` | Blog | P3 | Anthropic research / Stripe blog |
| `#w-changelog` | Changelog | P2 | Linear changelog |
| `#w-docs` | Docs / Help | **P1** | Linear docs / Vercel docs / Notion help |
| `#w-launch-video` | Launch video(60-90 秒) | **P0** | Linear launch / Arc launch / Cron launch |
| `#w-launch-assets` | HN/PH/Twitter ammo | **P0** | (depends on launch type) |
| `#w-press-kit` | Press kit | **P1** | (standard SaaS) |
| `#w-founder-essay` | Founder essay(1500-2500 字) | **P1** | personal blog / Substack |
| `#w-emails` | Email + 通知系统 | distributed in P0/P1 features | Stripe transactional / Linear notifications / Substack |
| `#r-social` | Social media 身份(`@rodix` / GitHub `rodix-app` / LinkedIn) | **P0**(name lock 后立即) | — |

---

## 4. Landing page (`#w-landing`)

**Priority**: **P0** · 对标 Linear / Raycast / Cursor.

### Sections(从上到下)

| # | Section | Notes |
|---|---|---|
| 1 | **Hero** | 产品定位句 + 一个动画 demo。tagline 候选见 §2。"Get started" CTA(去 onboarding) |
| 2 | **Core problem statement** | "ChatGPT / Claude / Gemini — they all forget you. [PRODUCT_NAME] doesn't." 正面碰瓷三大 AI |
| 3 | **Core value demos**(3-5 features,每个一动图/视频) | (a) 跨 AI model 记忆 (b) 跨设备真同步 (c) 主动 memory(`#8` Card with Promise + recall) (d) Decision Journal(P2) (e) 历史导入(`#9a`) |
| 4 | **Real product screenshots**(NOT mockup) | 桌面截图 1280x800+,从 alpha 阶段 production build 截 |
| 5 | **Privacy / 数据所有权承诺** | "encrypted at rest with per-user keys / strict access controls / full export + delete / not zero-knowledge but honest" — 跟 `#w-privacy-page` 链接 |
| 6 | **Pricing**(简洁版) | 3 档对比 thumbnail + 链接到 `#w-pricing` 详情 |
| 7 | **FAQ**(短) | 5-7 关键 FAQ;长版去 `#w-docs` |
| 8 | **Footer** | 标准 footer |

### Key 文案 placeholder(Rodc to fill)

- Hero tagline → 见 §2 候选
- 三大 AI 对比文案
- 5 features 的每个 1-line description

### 视觉规则

- Desktop hero 占 90vh+,scroll trigger features
- Animation 克制(per "trust > wow" baseline,**不要 Mailchimp 庆祝感**)
- 真实截图(不用 mockup)— 跟 `web-product-design.md` 视觉系统完全一致

---

## 5. Features (`#w-features`)

**Priority**: P1 · landing 后做.

### Structure 选项

(a) 单页 features list(适合 P1 launch,简洁)
(b) Sub-pages(适合 P1+30,SEO 友好):`/features/cross-device` / `/features/cross-model` / `/features/active-recall` / `/features/decision-journal`

**P1 launch 推荐 (a)**;P2 切 (b) for SEO.

### Per-feature template(对每个功能)

- Feature name + 1-line tagline
- 1 个动图 / 视频(产品实际演示)
- Use case(1 段)
- 跟竞品(ChatGPT memory / Notion AI)的差异(1 段)
- "Try it →" CTA → onboarding

---

## 6. Pricing (`#w-pricing`)

**Priority**: **P0** · 对标 Linear / Superhuman / Raycast.

### Structure

| Tier | Notes |
|---|---|
| **Free** | BYOK(自己 OpenAI / Anthropic / OpenRouter key)。所有 P1 功能。Vault 大小限制(待定) |
| **Plus** | Try Free 30 条 commission proxy(P2 上线)+ 增加 Vault 大小 + Cloud sync(P2/3 上线后)|
| **Pro** | 所有功能 + 团队功能(P3) |

(具体定价 + 限额 等 `#b-paddle` + `#r-company` resolve 后定)

### Sections

1. 三档卡片对比(横向 grid,Linear pricing 模式)
2. 详细 feature 对比表
3. "Try Free 30 messages"解释(commission proxy 上线后)
4. FAQ(付费 / 退款 / API key)
5. B2B contact(占位,Phase 3 真做)

### 视觉

- Linear pricing 是金标 — 三档对比卡片 + clear differentiator + soft 高光在推荐档
- **不要 Mailchimp / Stripe 那种"5 档复杂"**,P1 阶段 3 档简洁

---

## 7. Privacy / Security (`#w-privacy-page`)

**Priority**: **P0** · 核心差异化支撑页 · 对标 Proton / 1Password / Anthropic trust.

### Sections

1. **数据所有权承诺**: encrypted at rest with per-user keys + strict access controls + full export + delete + 团队内部 access 审计
2. **技术诚实**: explicitly NOT zero-knowledge(因为 server-side recall 需要明文)。Server can decrypt for ops; we commit to not reading user data; logs every access
3. **跟 ChatGPT memory 对比表**: 对比 8-10 维度(可见性 / 可导出 / 加密 / 可删除 / 访问审计 / 第三方训练 / 跨产品 / 跨设备)
4. **完整 Privacy Policy + ToS**(legal text,launch 前律师 review,3-10 天 lead-time per 协议 §8.2 类别 B)
5. **Security disclosure 政策**(report security issues 邮箱 + PGP key)

### Brand 叙事关键

- **不夸大成 "zero-knowledge"** — 已在 brainstorm 锁定。诚实告知 = 信任建设
- 跟 `#9a` 的 "诚实告知 1-3 小时 reality" 一脉相承
- 跟 `#3a` 导出"Your data, your file"叙事一致

---

## 8. Launch assets

### 8.1 Launch video (`#w-launch-video`) — **P0**

60-90 秒。结构:
1. Hook(7 秒): "ChatGPT forgets you. I don't." 桌面屏 demo
2. Problem(15 秒): 跨设备 / 跨 AI / 跨时间 都忘
3. Solution demo(30 秒): `#8` Card with Promise + Vault tab badge `+1` + recall trigger
4. Privacy承诺(10 秒): "Your data stays yours"
5. CTA(5-10 秒): URL + Get started

对标:Linear launch / Arc launch / Cron launch。

### 8.2 HN Show HN (`#w-launch-assets`) — **P0**

预先准备:
- Title(< 80 chars)
- 正文(简洁 + 链接 + 1 截图)
- 评论区预演(预想 FAQ)

### 8.3 Product Hunt — **P0**

Logo / Gallery / 介绍文案 / Maker comment。

### 8.4 Twitter launch thread — **P0**

6-10 条推文 + 视频 / 截图。

### 8.5 Press kit (`#w-press-kit`) — **P1**

`/press` 或独立 zip:Logo 各种尺寸 / 截图集 / 创始人头像 / 一句话+一段+长版本介绍 / 联系邮箱。

### 8.6 Founder essay (`#w-founder-essay`) — **P1**

1500-2500 字深度文章 "为什么我做了 [PRODUCT_NAME]"。launch 同步发(blog + Substack)。

---

## 9. Email + notifications

部分 P0(分布在 features),整体由 #w-emails 统筹.

### Templates

| 触发 | Subject 候选 | 优先 |
|---|---|---|
| 注册欢迎 | (TBD) | **P0** |
| Magic link 登录(如做) | (TBD) | P1 |
| **历史导入完成提醒**(`#9a` 关键) | "继续 [PRODUCT_NAME] · 历史可以合并了" | **P0** |
| Decision Journal review 提醒 | (TBD) | P2 |
| Weekly digest("this week in your thinking") | (TBD) | P2 |
| Newsletter | (TBD,launch 时建邮件列表) | P2 |

### 视觉

- Stripe 交易邮件标杆(简洁文字,不堆图)
- Linear 通知邮件
- Substack newsletter 排版

### Engineering note

`#9a` 的 email 是 launch 关键路径(浏览器 push 关 tab 即失效,email 是真正回流通道)。Implementation 跟 `#b-auth` 同 user email 数据。

---

## 10. Social media identity

**Priority**: **P0**(name lock 后立即抢占 — 等不起).

| Platform | Handle 候选 |
|---|---|
| Twitter / X | `@rodix` 主 / `@rodix_ai` 备 |
| GitHub org | `rodix-app`(因 `rodix` 大概率被占) |
| Discord | `Rodix` 服务器(Phase 3 community) |
| LinkedIn | 公司页(`#r-company` 注册后) |

详细 setup 见 `memory/project_rodix_name.md`.

---

## 11. Item priority snapshot

### P0(launch 阻塞)

`#w-landing` · `#w-pricing` · `#w-privacy-page` · `#w-launch-video` · `#w-launch-assets` · `#r-social`(name 锁后)

### P1(launch must,可简化)

`#w-features` · `#w-docs`(3-5 篇核心)· `#w-press-kit` · `#w-founder-essay`

### P2(launch+30)

`#w-changelog`

### P3(backlog)

`#w-blog`(launch+1 月再启动)· `#w-about`(可推迟)

---

## 12. Cross-cutting

### Device priority

Marketing site 跟 web product 一致:**Phase 1 桌面优先**,移动响应式不崩。Launch 营销弹药(视频/截图)100% 用桌面 1600px+。Phase 2 看数据加 mobile 优化。

### Tech stack(待 Rodc 决)

- Astro(默认推荐:SSG + island + Markdown changelog 友好)
- Next.js(替代:更动态,适合 changelog/blog)
- 纯 HTML(最简,但 SEO/changelog 难维护)

域名 + repo 位置(同 repo 子目录 / 独立 repo)等 Rodc 定。

### Copy 阶段(Rodc to drive)

Per Rodc directive: "文案等我消化完回来对齐,改一次重写所有页面成本太高,先别动"。

CC 不写最终 copy,只用 `[PRODUCT_NAME]` / `[TAGLINE]` 占位。Rodc 定稿后全局替换 + 微调。

---

## 13. References

- Web product spec: `web-product-design.md`(visual system + features 详细)
- Brainstorm session log: `2026-05-01-rodix-brainstorm.md`
- Collab protocol: `~/Downloads/throughline-collaboration-protocol.md` v1.4
- UX skill: `~/Downloads/SKILL-ux-design-judgment.md`
- Onboarding spec(原始,部分被 brainstorm 推翻 / 部分保留): `private/APP_ONBOARDING_SPEC_2026-04-29.md`

---

*Spec version 1.0 (2026-05-01) · Skeleton signed-off · Copy TBD · Ready for writing-plans phase(structure / visual / engineering)*
