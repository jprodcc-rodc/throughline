# Rodix Implementation Roadmap

**Version**: v1.2 (2026-05-01)
**v1.2 修订**: Rodc v1.1 review 3 HIGH issues 入档:(1) §1.4 加 #r-payment-fallback-research(P1,Paddle denial 真 mitigation)(2) §1.2 #b-dev-deploy 简化(Rodc directive: 0.0.0.0 + LAN URL print + 防火墙,不 HTTPS/mkcert/hosts)(3) #3a mock fixture 用 `rodix_dev.db` 隔离 dogfood 真 data
**v1.1 修订**: 外部 Opus 8 findings 入档:(1) Paddle individual seller 不依赖 #r-company → launch 不再被 #r-company 6-12 周 lead-time 阻塞 (2) 新增 #b-dev-deploy 局域网开发部署(sustainability)(3) 新增 #r-email-service(#9a + #b-auth 的依赖)(4) 删 #r-alpha-batch1/2(Rodc anonymous solo founder,直接 public launch)(5) Wave 1 拆 1a(demo-ready)+ 1b(fully functional)(6) Soak gate 定义 sharpened (per protocol §8.3 v1.5)(7) Dev mode 默认 OpenRouter free 模型 (8) `#3a` 用 mock fixtures(Choice A)解耦 #claim-extraction
**v1.0**: 初版 master roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement individual feature plans (created on-demand per wave). This roadmap is the **control plane** — item index, dependencies, critical path, sequence. Detailed bite-sized TDD plans are written per-item when each wave starts.

**Goal:** Ship Rodix soft launch — chat-with-memory SaaS product with marketing site, end-to-end encrypted vault (at-rest, per-user keys), BYOK + commission proxy auth, Paddle payments, public domain + TLS.

**Architecture:**
- **App backend**: Python FastAPI extending existing `app/web/server.py`. Adds auth + encryption + multi-tenant DB + Paddle integration + production deploy.
- **App frontend**: existing `app/web/static/` HTML/JS/CSS extended with B-style design tokens (Lucide icons + Inter font + amber `#d97706` accent + IA-C top tabs).
- **Marketing site**: new code base (recommendation: Astro for SSG + island + Markdown changelog). Separate from app/.
- **DB migration**: SQLite v3 → v4 with `user_id` columns + FTS5/vec rebuild (`#b-multitenant`).
- **Deploy target**: TBD VPS/container (Hetzner / Railway / Fly / DigitalOcean), TLS via Let's Encrypt.

**Tech Stack:**
- Backend: Python 3.12 + FastAPI + Uvicorn + SQLite + sqlite-vec (existing app/ stack)
- Auth: TBD (FastAPI-Users / Authlib / custom — pick during `#b-auth` plan)
- Payment: Paddle
- Frontend (app): HTML/CSS/JS (no framework, Lucide icons + Inter font)
- Frontend (marketing): Astro (recommended) or Next.js — pick during `#w-landing` plan
- Deploy: TBD (decision at `#b-deploy` plan)

**Governing protocol**: `~/Downloads/throughline-collaboration-protocol.md` v1.4
**Source specs:** 
- `docs/superpowers/specs/web-product-design.md`
- `docs/superpowers/specs/marketing-site-design.md`
- `docs/superpowers/specs/2026-05-01-rodix-brainstorm.md` (session log)

---

## 1. Item Index (per protocol §5)

### 1.1 Web Product (CC implements · `app/web/` + extensions)

| # | Subject | Priority | Done criteria summary | Depends |
|---|---|---|---|---|
| `#1a` | Settings panel: provider/key/vault path/test connection | **P0** | A 中央模态 + 4 fields + test connection 成功 + 失败诊断 (3 路径) + key 加密存储 | — |
| `#1b` | Settings: recall threshold slider | P2 | 滑块 + telemetry-driven 默认值 | `#recall-quality` |
| `#2a` | Onboarding 3 步 (B + step 2 = C 改进版) | **P1** | 3 屏 + skip = (a) + Phase 2 hint + brand 副标题 | — |
| `#2b` | Onboarding first-insight magic moment | P2 | Step 3 完成后跳 Vault tab 看刚生成的卡 | `#claim-extraction` |
| `#3a` | Cards mgmt 列表 (Vault tab) | **P1** | 35/65 master-detail + 4 级 cold start (0 / 1-5 / 6-50 / 50+) + Recall summary 阈值 3 + 删除 + Markdown 导出 | — |
| `#3b` | Cards 结构化视图 (claims/decisions/questions 分类) | P2 | 切换 view + filter | `#claim-extraction` |
| `#4` | 对话管理 重命名/归档/删除 | P2 | endpoint 已存在,纯前端 UI | — |
| `#5` | 视觉抛光 (B + Lucide tokens + 4 micro-adj) | **P1** | All states 用 Lucide icons + 3 级 affordance hierarchy + LOAD 1.5s 阈值 + SUCCESS "Your data, your file" + ERROR ghost button | 视觉系统已锁 |
| `#6a` | PWA shell (manifest + service worker + icons) | P2 | 浏览器可安装 + 离线壳 | — |
| `#6b` | PWA install UX (prompt + 引导) | P3 | install prompt + onboarding | `#b-deploy` |
| `#7` | README + 截图 | P3 | 跟 launch 公开 repo 一起 | — |
| `#8` 占位 | placeholder UI | **P0** | 空架子接 backend 即立即 work | — |
| `#8` 真功能 | Card with Promise + recall trigger | **P1** | A 形态 + see→trust→verify 三段 aha + 3 P1 micro-adj + 4 telemetry buttons (用上了/不相关/已经想过/跳过) | `#claim-extraction` |
| `#9a` | History import (C async + email primary) | **P1** | C 形态 2 路径 + 4 micro-adj + Email 主 fallback + 浏览器 Notifications API push + ChatGPT only (Claude/Cherry/Markdown 标 P2) | — |
| `#9b` | History import first-insight | P2 | 3 magic insights generation 在 import 完成后 | `#claim-extraction` |
| `#intent-classifier` | LLM-based user message classifier (chitchat/thoughtful/factual) | **P0** | 60-sample eval ≥ 85% accuracy on dev nvidia model + boundary opts (<5 chars / >200 chars short-circuit) + low-confidence fallback to thoughtful + timeout/error fallback + log alerts. Replaces ABC string-match bleed-stop in `#8` placeholder per v1.1 C-4.6. | — |
| `#claim-extraction` | 实时触发 claim 抽取 | **P0** | post-chat hook + 后台队列 + 4 字段 entity 提取 + **Vault badge 增长在 alpha 测试可观察** (per IA-C cascade caveat) | `#intent-classifier` |
| `#recall-quality` | Recall 质量打磨 + 阈值校准 | **P1** | threshold-learning loop + 真实数据 telemetry | 真实数据 |
| `#decision-journal-lite` | Decision Journal 实时触发 | P2 | (defer post-launch) | `#claim-extraction` |
| `#active-recall-base` | Active Recall standard threshold | **P1** | 0.75 threshold + 4 evaluators wired (topic / drift / loose end / decision precedent) | `#recall-quality` |
| `#active-recall-lowthreshold` | low-threshold mode (Try Free 催化剂) | P2 | (defer) | `#active-recall-base` |

### 1.2 B-重 SaaS Layer + Dev Infrastructure (CC implements)(v1.1 修订)

| # | Subject | Priority | Done criteria summary | Depends | Soak Gate (per §8.3 v1.5) |
|---|---|---|---|---|---|
| **`#b-dev-deploy`**(v1.2 简化) | **局域网 dev 部署:FastAPI bind 0.0.0.0:8000 + 启动打印 LAN IPv4 URL + 防火墙文档**。Rodc directive: HTTP only,不 mkcert / 不 Tailscale / 不 hosts / 不 HTTPS。Trade-off:Browser Notifications + Clipboard API 在 dev 不可用(secure context),production #b-deploy 真 TLS 后恢复 | **P0** | sustainability + Wave 1a demo-ready 必需 | 无 | iPad / 家人 PC 浏览器 http://192.168.x.x:8000 访问成功 |
| `#b-auth` | Auth (注册 + 登录 + 邮件验证 + 密码重置 + 会话 + 速率限制) | **P0** | 完整流 + email 投递成功 | `#r-email-service`(v1.1 修正) | Rodc 自己 dogfood 跑通完整注册流(verify email + 密码重置)无 P0 bug |
| `#b-encryption` | 静态加密 (KMS + per-user key) | **P0** | encrypted at rest + 强制访问审计 + key rotation 设计 | `#b-auth` | **Rodc dogfood 3 个日历日 + 累计 5 小时 active usage 无 P0 bug + 自动 monitoring 无 P0 alert**(v1.1 sharpened per §8.3 v1.5) |
| `#b-multitenant` | 多租户 DB 改造 (4b 完整版) | **P0** | schema v4 加 `user_id` 列 + FTS5/vec 索引重建 + adapter 全部走 user_id | `#b-encryption` | migration 演练 + 数据无丢失验证 |
| `#b-paddle` Phase A(v1.1 修正) | Paddle individual seller(中国身份 + Wise) | **P0** | webhook + 订阅状态 + 限额检查 + 退款 | `#r-domain` + Wise 账户(**NOT #r-company**) | **3 笔自己 sandbox 交易完整闭环(创建 / 续订 / 退款)** |
| `#b-paddle` Phase B(v1.1 新增) | Paddle 切换到公司主体 | **P2**(launch+30 内) | 数据迁移 + 客户通知 | `#r-company` 完成 | 切换演练成功 + 真实交易测试 |
| `#b-deploy` | 域名 + TLS + 部署 + observability + 备份 | **P0** | 至少 1 次备份恢复演练成功 | `#r-domain` + `#r-email-service`(v1.1 修正:加 email service 作为 deploy 完整性依赖) | **备份恢复演练 1 次成功 + 部署后连续 7 个日历日 uptime monitoring 无 P0 alert(downtime / 5xx spike / cert expiry warning)**(v1.1 sharpened) |
| `#b-security-review` | 安全审查 + 边界测试 | **P0** | 第三方扫描 + 自审 + key 处理 audit | 全部 `#b-*` | 第三方扫描通过 |
| `#b-privacy-policy` | Privacy Policy + ToS | **P0** | 律师签字 (3-10 天 lead-time per §8.2 类别 B) | 产品功能定稿 | 律师签字 |

### 1.3 Marketing Site (CC implements · `marketing/` 新代码 base)

| # | Subject | Priority | Done criteria summary | Depends |
|---|---|---|---|---|
| `#w-landing` | Landing page 框架 (8 sections per spec) | **P0** | Hero + 问题陈述 + 5 features + 截图 + privacy + pricing 缩略 + FAQ + footer | 视觉 system + Rodc 文案 |
| `#w-pricing` | Pricing 页 | **P0** | 3 档对比 + feature 表 + FAQ + B2B 占位 | `#b-paddle` |
| `#w-privacy-page` | Privacy / Security 页 | **P0** | "encrypted at rest, NOT zero-knowledge" 诚实声明 + ChatGPT memory 对比表 + Privacy Policy + ToS | ADR-002 evolution + `#b-privacy-policy` |
| `#w-features` | Features 单页(P1) / sub-pages(P2 SEO) | **P1** | 单页 features list 含动图/视频 demo | `#w-landing` |
| `#w-docs` | 基础 Docs (3-5 篇核心) | **P1** | Getting started / 历史导入教程 / API key 配置 / 隐私 / FAQ | — |
| `#w-changelog` | Changelog 启动 | P2 | 跟代码 release 联动 | — |
| `#w-blog` | Blog | P3 | (launch + 1 月) | — |
| `#w-about` | About 页 | P3 | (推迟) | — |
| `#w-launch-video` | Launch 视频 (60-90 秒) | **P0** | desktop 录屏 demo + Hook+Problem+Solution+Privacy+CTA 结构 | 产品功能完成 |
| `#w-launch-assets` | HN/PH/Twitter ammo | **P0** | 标题/正文/截图/视频/maker comment | `#w-landing` + `#w-launch-video` |
| `#w-press-kit` | Press kit | **P1** | logo / 截图 / 介绍文案 / 联系邮箱 | `#r-name-final` + 视觉 |
| `#w-founder-essay` | Founder essay (1500-2500 字) | **P1** | Rodc 写,launch 同步发(blog + Substack) | Rodc copy |

### 1.4 Rodc-only Items (NOT in CC writing-plans scope)(v1.1 修订)

These items execute outside CC's engineering planning. Listed here for cross-reference and dependency tracking only.

| # | Subject | Priority | External lead-time | Notes |
|---|---|---|---|---|
| `#r-name-final` | 最终敲定产品名 | **P0** | — | candidate Rodix; Rodc 决定后 update protocol §5.5.1 |
| `#r-domain` | 抢域名 (rodix.ai 优先) | **P0** | 几分钟 — 1 天 | depends `#r-name-final`;**launch critical path**(v1.1) |
| `#r-social` | 抢社交账号 (`@rodix` / GitHub `rodix-app`) | **P0** | 同上 | 同上 |
| **`#r-email-service`**(v1.1 新增) | Email 后端选型(Resend 推荐 / SendGrid / Postmark / Mailgun)+ DNS records(SPF/DKIM/DMARC)on rodix.app + API key | **P0** | 1-3 天(DNS 传播 + verification) | depends `#r-domain`;`#9a` + `#b-auth` 依赖;**launch critical path** |
| `#r-company` | 海外公司注册(代理 + 银行 + EIN) | **P1**(launch 后,v1.1 修正) | **6-12 周** | **不再 launch blocker(v1.1):Paddle Phase A individual seller 不依赖此项**。立即并行启动,Phase B 切换在 launch+30 内完成 |
| **`#r-payment-fallback-research`**(v1.2 新增) | 调研 LemonSqueezy / Polar.sh / Gumroad 对中国身份接受度 | **P1** | 1-2 小时调研(不立即注册) | 时机 = Paddle Phase A 申请同时启动。**Paddle denial 真 mitigation**(per Rodc Issue 1) |
| `#r-trademark` | USPTO 商标申请 | P2 | 6-12 月(launch 不阻塞) | `#r-company` + `#r-name-final` + 律师 |
| ~~`#r-alpha-batch1`~~(v1.1 删除) | — | — | — | **删除原因:Rodc anonymous solo founder,无 coworker network。launch model 改为 Rodc dogfood + 家人 review onboarding 友好度 + 直接 public launch 冷启动**。Documented tradeoff: 失去 pre-launch user feedback signal,通过 Rodc dogfood + 自动 monitoring + 家人 review 部分缓解 |
| ~~`#r-alpha-batch2`~~(v1.1 删除) | — | — | — | 同上 |

### 1.5 重命名 (per §5.5)

| # | Subject | Priority | Notes |
|---|---|---|---|
| `#rename-user-facing` | 用户可见 rename (网站/UI/邮件/错误消息/收据) | **P0/P1** distributed | NOT 单独 # — `#r-name-final` 完成时全局替换 `[PRODUCT_NAME]` → 最终名,各 P0/P1 项实施时承担 |
| `#rename-internal` | 内部 rename (`throughline_cli` → `rodix_cli` / vault path / env vars / DB / git repo / docker / 注释) | P2 | post-launch migration script 一次完成 |

---

## 2. Dependency Graph (v1.1 修订)

```
                                    ┌─ #r-name-final (Rodc, instant) ─────┐
                                    │                                      ├──→ #r-domain
                                    │                                      ├──→ #r-social
                                    │                                      └──→ #rename-user-facing(分布)
                                    │
                                    └─ #r-domain ──→ #r-email-service ──┬──→ #b-auth
                                                                        │
                                                                        └──→ #9a (email reminder)
                                    
[Paddle 不再依赖 #r-company (v1.1)]
   #r-domain + Wise ──→ #b-paddle Phase A (1-7 天) ──→ launch 用此
                                                          │
   #r-company (并行 6-12 周) ──→ #b-paddle Phase B (launch+30 切换)


[CC Wave 1a · DEMO-READY · v1.1 新增 milestone]
   #5 视觉抛光 ──→ #b-dev-deploy ──→ #2a Onboarding skel ──→ #8 占位 UI
                                                                │
   Done 信号:Rodc/家人 从 iPad 访问 https://rodix.local
            走完 onboarding + 看占位 Card with Promise + Vault badge 动画
            **家人 review onboarding 友好度** + Rodc 第一次 motivation checkpoint


[CC Wave 1b · FULLY FUNCTIONAL]
   #1a 设置面板 (P0, 加 dev mode default OpenRouter free) ──→
   #w-docs (5 篇核心 outline,Rodc 填 copy) ──→
   #intent-classifier (P0, 60-sample eval ≥85%, blocks #claim-extraction 启动) ──→
   #claim-extraction (P0, 加 dev mode + accuracy gate ≥60%) ──→
   #3a Cards mgmt (用 mock fixtures Choice A,4 套场景 0/3/15/60 卡 cover 4 级 cold start) ──→
   #9a History import (依赖 #r-email-service ready by Rodc parallel)


[CC Wave 2 - Real features (依赖 #claim-extraction)]
   #claim-extraction ──┬──→ #8 真功能 (P1, 替换占位)
                        ├──→ #2b first-insight (P2)
                        ├──→ #3b 结构化视图 (P2)
                        ├──→ #9b first-insight (P2)
                        └──→ #decision-journal-lite (P2)
   #recall-quality ──→ #active-recall-base ──→ #active-recall-lowthreshold (P2)
                  └──→ #1b threshold slider (P2)


[CC Wave 3 - B-重 SaaS upgrade]
   #b-auth (depends on #r-email-service) ──→
   #b-encryption (Rodc dogfood soak gate) ──→
   #b-multitenant ──→
   #b-deploy (depends on #r-domain + #r-email-service) ──→
   #b-security-review (depends on 全部 #b-*)
   
   #b-paddle Phase A (depends on #r-domain + Wise; PARALLEL 不等 #b-deploy)
   #b-privacy-policy (3-10 天律师,Rodc 推动)


[CC Wave 4 - Marketing + Launch ammo]
   #w-landing ──┬──→ #w-features
                ├──→ #w-launch-assets (also depends on #w-launch-video)
                └──→ #w-press-kit
   #w-launch-video (depends on 产品功能完成)
   #w-founder-essay (Rodc 写)
   #w-privacy-page (depends on #b-privacy-policy + ADR-002)


[Rodc 并行 5 任务流(不阻塞 CC)]
   1. #r-name-final → #r-domain → #r-social → #r-email-service(Wave 1a 完成前 ready)
   2. #r-company(立即启动 6-12 周,launch+30 切 Paddle Phase B 用)
   3. Wave 1a done 后:家人 review onboarding,准备 launch 文案
   4. Wave 2 done 后:#w-founder-essay 写
   5. Wave 4 done 后:HN/PH/Twitter cold launch
```

---

## 3. Critical Path Analysis (v1.1 修订)

**真 launch 瓶颈不再是 #r-company**(v1.1):

| 候选瓶颈 | Lead-time | 状态 |
|---|---|---|
| ~~#r-company~~ | ~~6-12 周~~ | **从 launch critical path 移除**(Paddle Phase A individual seller 不依赖此) |
| `#r-domain` + `#r-email-service` + `#b-paddle` Phase A | **总 1-7 天** | 新 critical path 外部部分 |
| 律师 review(`#b-privacy-policy`) | 3-10 天 | 跟 CC engineering parallel |
| CC engineering (Wave 1a → 1b → 2 → 3 → 4) | autonomous,fastest path | 占用 launch 准备主体 |

**真 launch readiness = max(CC engineering 全完, #r-domain + #r-email-service ready, Paddle Phase A approved, 律师 sign Privacy)**。

**Critical path sequence(v1.1)**:

1. **Day 0 (NOW)**: 
   - Rodc 锁 `#r-name-final`(instant)
   - Rodc 启动 `#r-domain`(几分钟到 1 天)+ `#r-social`
   - Rodc 启动 `#r-company`(6-12 周 parallel,launch 不依赖,只为 Phase B 切换准备)
   - CC 启动 **Wave 1a**(`#5` → `#b-dev-deploy` → `#2a` → `#8` 占位)

2. **Wave 1a 完成**:
   - Rodc + 家人 review onboarding 友好度
   - Rodc motivation checkpoint
   - Rodc 启动 `#r-email-service`(1-3 天 DNS verification)
   - CC 启动 **Wave 1b**

3. **Wave 1b 完成**:
   - 全部 P0/P1 web product 项 working
   - Rodc dogfood real features
   - CC 启动 **Wave 2**(real features depend on `#claim-extraction`)

4. **Wave 2 完成**:
   - see→trust→verify aha 闭环 Rodc 自己 dogfood 通过
   - CC 启动 **Wave 3 B-重**

5. **Wave 3 完成**:
   - SaaS layer ready
   - Rodc dogfood 3 日历日 + 5h active soak gates 通过
   - 律师 review 完(3-10 天 parallel)
   - Paddle Phase A 完(1-7 天 parallel)
   - CC 启动 **Wave 4 Marketing**

6. **Wave 4 完成**:
   - All P0 ✓ + soak gates ✓
   - HN / PH / Twitter cold launch

7. **Launch+30**:
   - `#r-company` 完成(并行跑了 6-12 周)
   - `#b-paddle` Phase B 切换公司主体
   - `#rename-internal` migration 跑

**Rodc 立即启动事项**(v1.1):
- 锁 `#r-name-final`(instant decision)
- `#r-domain`(几分钟,影响下游)
- `#r-social`(同上)
- `#r-company`(立即启动 6-12 周 parallel,不阻塞 launch)
- Wise 账户(if not already,for Paddle Phase A)
- 家人 review 准备(Wave 1a 完成时执行)

**Rodc 不再做**:
- ~~`#r-alpha-batch1` / `#r-alpha-batch2`~~(v1.1 删,直接 public launch)

**Documented tradeoff (Finding 3)**:
直接 public launch(无 alpha)= 失去 pre-launch user feedback signal,launch-day bug 风险 reputation damage 不可逆。**Mitigated by**:Rodc dogfood(per protocol §8.3 v1.5 sharpened soak gates)+ 家人 onboarding review(Wave 1a 完成时)+ 自动 monitoring。**Rodc 接受这个 tradeoff** 因为(a)solo founder 无 alpha-batch 社交资源 (b)protocol §8.3 sharpened soak gates 已 mitigate (c)HN/PH 允许 incremental rollout — 有 issues 可快速 patch。

---

## 4. Implementation Sequence (Waves)

### Wave 1a · DEMO-READY(v1.1 新增 sub-milestone per finding 6)

**条件**: 无外部依赖。视觉 system 已锁。

**Items(顺序 sequence per dependency)**:
1. `#5` 视觉抛光 P1(token system + Lucide icons)
2. `#b-dev-deploy` P0(mkcert HTTPS + rodix.local + iPad/家人 access)
3. `#2a` Onboarding 3 步骨架 P1(dev mode 跳过 BYOK 自动 free model)
4. `#8` 占位 UI P0(Card with Promise visual + Vault badge 动画)

**Wave 1a done 信号**:
- Rodc / 家人 从 iPad / 家人 PC 打开 https://rodix.local
- 完整走 onboarding(dev mode 自动配 OpenRouter free)
- 看占位 Card with Promise + Vault badge `+1` 动画
- **家人 review onboarding 友好度反馈**(non-tech 视角)
- Rodc **第一次 motivation checkpoint**

**Wave 1a 后 Rodc 同步动作**:
- 启动 `#r-email-service`(1-3 天)
- 准备 `#w-landing` 文案

### Wave 1b · FULLY FUNCTIONAL(v1.1 修订)

**条件**: Wave 1a 完成 + Rodc 收到家人反馈。

**Items**(顺序按 user-value 递增):
1. `#1a` 设置面板 P0(dev mode default + production force BYOK)
2. `#claim-extraction` P0(dev mode + accuracy gate ≥60%)
3. `#3a` 卡片管理(用 mock fixtures Choice A — 4 套场景 0/3/15/60 cover 4 级 cold start)
4. `#9a` 历史导入(依赖 `#r-email-service` ready)
5. `#w-docs`(5 篇核心 outline)

**Wave 1b done 信号**:
- 全部 P0/P1 web product 项 working
- `#claim-extraction` 真实 trigger,Vault badge 增长可观察
- `#3a` 真卡片 + 4 级 cold start 都正确
- `#9a` 上传 zip 流程通,email 提醒可触发
- Rodc dogfood real features

### Wave 2 — Real features (CC · 依赖 #claim-extraction)

- `#8` 真功能(替换占位)
- `#2b` first-insight magic moment (P2,可推到 launch+30)
- `#3b` 结构化视图 (P2)
- `#9b` first-insight (P2)
- `#recall-quality` + `#active-recall-base` P1
- `#decision-journal-lite` (P2)

**Wave 2 done 信号**: see → trust → verify 完整 aha 闭环可演示。

### Wave 3 — B-重 SaaS upgrade(v1.1 修订)

**条件**: Wave 2 完成 + `#r-email-service` ready。

- `#b-auth` 启动(depends on `#r-email-service`)
- `#b-encryption` 接 `#b-auth`
  - **Soak gate(v1.1 sharpened):Rodc dogfood 3 日历日 + 累计 5h active 无 P0 bug**
- `#b-multitenant` 接 `#b-encryption`
- `#b-paddle` Phase A(parallel,depends on `#r-domain` + Wise — NOT `#r-company`)
  - **Soak gate:3 笔 sandbox 完整闭环(创建/续订/退款)**
- `#b-deploy`(depends on `#r-domain` + `#r-email-service`)
  - **Soak gate(v1.1 sharpened):备份恢复 1 次 + 部署后 7 个日历日 uptime monitoring 无 P0 alert**
- `#b-security-review` 接全部 `#b-*`

**并行分支**:
- `#b-privacy-policy`(律师 3-10 天)
- `#w-landing` + `#w-features` + `#w-privacy-page`

### Wave 4 — Pre-launch polish + Marketing(v1.1 修订)

**条件**: Wave 3 + `#b-paddle` Phase A approved + 律师 review 完。

- `#w-pricing` 接 `#b-paddle` Phase A 真数据
- `#w-launch-video` 录(production demo)
- `#w-launch-assets` 准备(HN/PH/Twitter)
- `#w-press-kit`
- `#w-founder-essay`(Rodc 写)
- 全部 soak gates 通过

### Wave 5 — Soft launch(v1.1 修订:无 alpha 批次)

**条件**: 全 P0 ✓ + 全 soak gates ✓ + 律师 ✓。

- **直接 public launch**(per finding 3):HN Show HN / PH / Twitter cold
- Founder essay 发
- Monitor + 立即修 P0 issues
- ~~`#r-alpha-batch2` 邀请~~(v1.1 删)

### Wave 6 — Post-launch (P2 backlog)

- `#1b` recall threshold slider(基于 telemetry)
- `#2b` first-insight integration(if not in W2)
- `#3b` 结构化视图
- `#4` 对话管理 UI
- `#6a` PWA shell
- `#9b` first-insight
- `#decision-journal-lite`
- `#active-recall-lowthreshold`
- `#rename-internal` 一次性 migration
- `#w-changelog` 启动
- `#r-trademark` 申请

---

## 5. Per-Item Done Criteria (for tracking)

[完整 done criteria 见 §1 表格 + 两份 spec doc 详细 spec 节]

每项达 done 的 verification:
- ✓ done criteria 全部满足
- ✓ soak gate (B-重 P0 项必有)通过
- ✓ telemetry / alpha 反馈无 P0 bug
- ✓ 代码 reviewed(per `superpowers:requesting-code-review`)
- ✓ commit + push(per `feedback_commit_push.md`)

---

## 6. Rodc-only Items (not in CC writing-plans output)

**`#r-name-final`**: lock candidate Rodix → update protocol v1.5 §5.5.1。CC 待 lock 后跑全 repo grep `[PRODUCT_NAME]` → final name 全局替换。

**`#r-company`**: 海外公司代理 + 银行账户 + EIN。CC 在此期间完成全部 Wave 1-3 工程。

**`#r-domain`**: rodix.ai (优先) / .com / .io / .app — 同时查 + 注册多个。

**`#r-social`**: `@rodix` / `@rodix_ai` / GitHub `rodix-app` / Discord 服务器(Phase 3) / LinkedIn(`#r-company` 之后)。

**`#r-alpha-batch1`**: 5-10 共创者名单 + 邀请话术。Wave 1 完成后启动。

**`#r-alpha-batch2`**: 15-20 testimonials 来源名单。Wave 2 (P1 部分) + Wave 3 部分完成后启动。

**`#r-trademark`**: USPTO 商标 — `#r-company` + 律师选好后启动。launch 不阻塞(6-12 月)。

---

## 7. Per-feature Plan Templates (writing-plans 后续输出)

每个 # 项启动时,CC 写一个 per-feature implementation plan,含:
- bite-sized TDD tasks (2-5 minutes per step)
- exact file paths
- complete code in every step
- exact commands + expected output
- commit messages

第一批要写的 per-feature plans(Wave 1 启动时):
1. `2026-05-XX-1a-settings-panel.md`
2. `2026-05-XX-2a-onboarding-skeleton.md`
3. `2026-05-XX-3a-cards-management.md`
4. `2026-05-XX-5-visual-polish.md`
5. `2026-05-XX-8-placeholder-ui.md`
6. `2026-05-XX-9a-history-import.md`
7. `2026-05-XX-claim-extraction.md`
8. `2026-05-XX-w-docs.md`

---

## 8. Self-review (skill self-check)

**Spec coverage**:
- ✓ 所有 web product spec items (§5.1) 都在表格
- ✓ 所有 B-重 items (§5.2) 都在表格 + soak gates
- ✓ 所有 marketing items (§5.3) 都在表格
- ✓ Rodc-only (§5.4) 显式标记
- ✓ 重命名 (§5.5) 显式分类

**Placeholder scan**:
- TBD 项都是 Rodc-decision 占位(tech stack pick / domain pick / 文案 / 律师审核)
- 所有 CC 工程 items 有具体 done criteria
- 无"implement later" / "fill in details"等 plan failure pattern

**Type / 命名一致性**:
- # 编号跟 protocol §5 一致
- Done criteria 措辞跟 spec doc 一致
- 引用的 memory file paths 正确

**Scope check**:
- 这是 master roadmap,不是 per-feature plan
- per-feature plans 每 wave 启动时单独写
- 已显式说明这个分层

**Critical path 验证**:
- `#r-company` 6-12 周 是真 critical path(per §8.2.2)
- B-重 工程序列在 6-12 周内可完成
- Soak gates 每 P0 项有明确 condition

---

## 9. References

- Protocol v1.4: `~/Downloads/throughline-collaboration-protocol.md`
- Web product spec: `docs/superpowers/specs/web-product-design.md`
- Marketing site spec: `docs/superpowers/specs/marketing-site-design.md`
- Brainstorm session log: `docs/superpowers/specs/2026-05-01-rodix-brainstorm.md`
- Memory:
  - `feedback_collab_protocol.md`
  - `feedback_design_judgment_failures.md`(5 modes + 1 positive lesson + 7-item pre-push checklist)
  - `project_rodix_name.md`
  - `project_device_priority.md`
  - `reference_ux_skill.md`
  - `reference_collab_protocol.md`

---

*Roadmap version 1.0 (2026-05-01) · Master plan signed-off after spec sign-off · Per-feature implementation plans follow on-demand per wave*
