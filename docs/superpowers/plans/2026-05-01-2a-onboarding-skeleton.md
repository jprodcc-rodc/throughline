# `#2a` Onboarding Skeleton — Implementation Plan

> **For agentic workers:** Use `superpowers:test-driven-development` per task.

**Goal:** Implement 3-step onboarding wizard(B 压缩 3 步)on first visit。Step 1 Welcome+价值主张 / Step 2 AI 接入(C 改进版)/ Step 3 First conversation。Skip = (a)只跳本步。

**Architecture:** Client-side first-visit detection(localStorage flag)+ 3 sequential 屏 in `onboarding.html` 或 inline overlay on `index.html`。Step 2 是独立简化屏(NOT 复用 `#1a` 模态)。

**Tech Stack:** Pure HTML/CSS/JS · localStorage · existing `app/web/static/`

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | 3-screen wizard with progress bar `Step N of 3`. Step 1: Welcome + tagline副标题"`[PRODUCT_NAME]` 不绑定任何 AI 公司——你的 memory 跨任何模型". Step 2: AI 接入 C 改进版(推荐 OpenRouter card + 进阶 fallback link). Step 3: 进 chat tab,标 hint"先配 AI 才能聊"if skip step 2. |
| 产品策略假设 | ChatGPT/Claude 付费用户的 90 秒目标 + brand 信任建设。每步可 skip 但 NOT 跳出 onboarding(per Skip = (a)). |
| 适合 / 不适合 | **适合**: 首次访问的 alpha 测试者(Step 1 7 秒拦截 / Step 2 有 zip 用户走 secondary)。**不适合**: 已注册用户(localStorage flag 跳过)。 |
| Trade-off | + 3 步压缩对齐 90 秒目标 + Step 2 独立简化屏不复用 `#1a` modal / − Step 1 copy 待 Rodc 写,占位 `[PRODUCT_NAME]` |
| 最大风险 | localStorage 跨设备不同步 → 同一用户多设备会重做 onboarding。**P1 接受这个限制**;P2 加 server-side flag in `#b-auth` 时统一。 |

## Ambiguity flag

⚠️ **有产品决策点**:Step 1 / Step 3 文案待 Rodc 写。结构 + 视觉 + 流程逻辑无歧义。

## Dev mode behavior(v1.1 新增 per finding 5)

**Dev mode**(`RODIX_DEV=1` 或 hostname `rodix.local`):
- Step 2 "推荐 OpenRouter" 按钮 → 跳过真实 OpenRouter 注册流程(跨设备 friction 大)
- 自动配 dev mode default(per `#1a` plan):provider=OpenRouter, model=`nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`,key 从 env `OPENAI_API_KEY`(Rodc 桌面环境)
- Step 2 显示 "DEV MODE · 已自动配置" 提示 + 直接进 Step 3
- 仍展示推荐 OpenRouter card UX(让家人 review 友好度)但 CTA 改为 "继续(已自动配置)"

**Production mode**: per existing tasks(force BYOK paste-and-go 或 secondary BYOK path)。

家人 review 时:dev mode 让家人能完整走流程而不需 OpenRouter 账号,**仍能反馈 onboarding UX 友好度**。

## Files

**Modify**:
- `app/web/static/index.html` — add onboarding overlay markup
- `app/web/static/app.js` — first-visit detection + step navigation
- `app/web/static/app.css` — onboarding styles per `#5` tokens

**Create**:
- `app/web/static/onboarding.js` — onboarding state machine + flow

**Test**: `app/web/test_onboarding_flow.py`(headless browser test)

## Bite-sized TDD tasks

- [ ] **Task 1: First-visit detection**
  - Write failing test:`test_onboarding_flow.py::test_first_visit_shows_step1` — open app fresh(no localStorage flag), Step 1 visible
  - Implement `app.js` check:`if (!localStorage.getItem('onboarding_completed')) { showOnboarding(); }`
  - PASS
  - Commit `feat(onboarding): first-visit detection`

- [ ] **Task 2: Step 1 markup with progress + tagline placeholder**
  - Write `index.html` markup for `<div id="onboarding-step1">` with:
    - 3-segment progress bar(first segment amber `#d97706`, others `#27272a`)
    - `STEP 1 OF 3` label
    - Brand `[PRODUCT_NAME]` 18px amber 700-weight
    - Heading: TBD copy(Rodc fill); placeholder "Hi."
    - Subtitle: `[PRODUCT_NAME] 不绑定任何 AI 公司——你的 memory 跨任何模型`
    - Primary CTA "Get started"
    - Secondary "Already have an account? Sign in"(grey)
  - No JS yet
  - Commit `feat(onboarding): step1 markup with placeholder copy`

- [ ] **Task 3: Step 1 → Step 2 transition**
  - JS:click "Get started" → hide step1, show step2 placeholder
  - Test in browser
  - Commit `feat(onboarding): step1→step2 navigation`

- [ ] **Task 4: Step 2 markup(C 改进版)**
  - Markup `<div id="onboarding-step2">`:
    - Progress 2/3
    - Brand subtitle 重复(brand 叙事一致)
    - Recommended card: bordered amber, "用 OpenRouter →" primary CTA
    - "为什么是 OpenRouter" 卡块 inline
    - 描述:"不需要 OpenAI / Anthropic 账号,3 分钟拿到 key 后通用 30+ 模型"
    - Divider "或"
    - Secondary link "已有 OpenAI / Anthropic / Gemini key? 用我自己的 key →"
    - Phase 2 hint small print(per spec micro-adj)
    - Skip link
  - Commit `feat(onboarding): step2 AI 接入 markup`

- [ ] **Task 5: Step 2 OpenRouter path**
  - Click "用 OpenRouter →" → open new tab to OpenRouter signup → wait for user return → key paste field shown
  - Use `window.open('https://openrouter.ai/keys', '_blank')`
  - Display "Paste your key here when you have it" → input + Test connection button
  - On test success → save via `/api/settings` → next step
  - Commit `feat(onboarding): OpenRouter recommended path`

- [ ] **Task 6: Step 2 secondary BYOK path**
  - Click "用我自己的 key →" → in-place expand to provider grid(OpenAI / Anthropic / Gemini)+ key input + Test
  - Same save flow as above
  - Commit `feat(onboarding): BYOK secondary path`

- [ ] **Task 7: Step 2 skip handling(per spec Skip = (a))**
  - Click "先跳过" → skip step 2, proceed to step 3 BUT mark `pending_ai_setup: true` in localStorage
  - Step 3 chat 入口显示 hint "先配 AI 才能聊" + 链接到 `#1a` 设置 modal
  - Commit `feat(onboarding): skip step2 with chat-blocked hint`

- [ ] **Task 8: Step 3 First conversation**
  - Markup `<div id="onboarding-step3">`:
    - Progress 3/3
    - Heading: TBD copy(placeholder "你想从哪个话题开始?")
    - Sample prompts(`#2b` first-insight 钩子放这里 P2)
  - Click prompt → 自动填入 chat composer + 进 chat tab
  - "完成" CTA → set `localStorage.onboarding_completed=true` + close overlay
  - Commit `feat(onboarding): step3 first conversation`

- [ ] **Task 9: Mobile responsive**
  - All steps stack vertically at <768px
  - Provider grid in step 2 BYOK path collapse to single column
  - Test at 375px
  - Commit `feat(onboarding): mobile responsive`

- [ ] **Task 10: End-to-end manual test**
  - Fresh browser → 完整走 3 步 → vault loaded → reload page → onboarding NOT shown again
  - Test skip path → chat tab shows "先配 AI 才能聊" hint
  - Commit `chore(test): #2a end-to-end verified`

## Done criteria

- [ ] `#2a` 3 步骨架:Step 1 价值主张 + Step 2 AI 接入(C 改进版)+ Step 3 chat ✓
- [ ] Skip = (a):只跳本步,不跳出 onboarding ✓
- [ ] Step 1 副标题 = brand tagline `[PRODUCT_NAME] 不绑定任何 AI 公司——你的 memory 跨任何模型` ✓
- [ ] Step 2 视觉层级:`[PRODUCT_NAME]` 18px > OpenRouter mention 13px ✓
- [ ] Phase 2 hint small print 在 step 2 底部 ✓
- [ ] localStorage 持久,不重复 onboarding ✓

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位 全用
2. ✓ Desktop-first / mobile fallback
3. ✓ §7.4 5 项 articulated
4. ✓ Pre-mortem 4 modes(like-me ✓ / metric goal 90sec→aha ✓ / reactive vs strategic 落 brand 叙事 ✓ / edge vs main main path is 知识工作者 ✓)
5. ✓ 桌面横向:每步 1 屏中央
6. ✓ Mobile responsive 显式
7. ✓ Empty state:N/A(每步必有内容,reverse 是 first-visit detection 跳过)

## References

- Scenarios: S-OB-1, S-OB-2, S-OB-3, S-OB-4, S-OB-5, S-MOBILE-1, S-MOBILE-2 (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`)
- Spec: `web-product-design.md` §5.1, §5.2
- Brainstorm: 屏 09 + 屏 14
- 微调:Step 1 副标题改 `[PRODUCT_NAME]`(per `#2a` 微调 1)
