# `#5` Visual Polish — Implementation Plan

> **For agentic workers:** Use `superpowers:test-driven-development` per task.

**Goal:** Apply locked visual system tokens(B Raycast warm dark + amber `#d97706` + Inter + Lucide line icons + 3-tier affordance hierarchy)consistently across all surfaces. Implement state visual system per `#5` 4 micro-adjustments。

**Architecture:** CSS custom properties for token system(centralized in `app.css`)+ Lucide SVG inline definitions reused via `<use>` references + state rendering helpers in JS。

**Tech Stack:** CSS variables · Lucide icons(MIT, vendored)· no JS framework

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | Single comprehensive design token sheet + Lucide icon SVG sprite + state visual style B(text + line icons,no celebration). 3-tier affordance:Primary 实心 / Recovery ghost 边框 / Secondary 灰色 link. Loading 3-dot pulse 1.4s. |
| 产品策略假设 | trust > wow baseline · Linear/Notion-tier 克制成熟 · 跟 IA-C/`#8`/`#3a` 调性一致. |
| 适合 / 不适合 | **适合**: 全部 SaaS 知识工作者目标用户. **不适合**: 性格化产品偏好(Mailchimp/Slack 调性)— 我们明确不是. |
| Trade-off | + 跟 IA-C 已锁定调性精确匹配 + 实现 incrementally(token sheet 优先,逐 surface 应用) / − Inter 中文 fallback 边界(P2 review) |
| 最大风险 | Token system 未集中导致"硬编码颜色散落"(回到 brainstorm 之前的状态)。**通过 CSS variables + lint check 缓解**。 |

## Ambiguity flag

✓ **无 ambiguity**(token spec + 4 micro-adj 全 locked)。

## Files

**Modify**:
- `app/web/static/app.css` — replace existing styles with token-based system

**Create**:
- `app/web/static/tokens.css` — design tokens(can be merged into app.css, but separate for clarity)
- `app/web/static/icons.svg` — Lucide SVG sprite
- `app/web/static/states.js` — state rendering helpers(loading/error/success)

**Test**: visual regression manual test at viewports 375px / 768px / 1280px / 1600px

## Bite-sized TDD tasks

- [ ] **Task 1: Tokens CSS file**
  - Create `tokens.css` with CSS custom properties:
    ```css
    :root {
      --bg: #18181b;
      --surface: #27272a;
      --surface-raised: #1c1c1f;
      --text-primary: #fafafa;
      --text-secondary: #a1a1aa;
      --text-tertiary: #71717a;
      --border-subtle: rgba(255,255,255,0.05);
      --border-medium: rgba(255,255,255,0.08);
      --accent: #d97706;
      --error: #ef4444;
      --success: #22c55e;
      --radius-sm: 6px;
      --radius-md: 8px;
      --radius-lg: 10px;
      --space-1: 4px; --space-2: 6px; --space-3: 8px;
      --space-4: 12px; --space-5: 18px; --space-6: 24px;
      --font-stack: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
    }
    ```
  - Include Inter Google Fonts `@import` at top
  - Commit `feat(css): design tokens centralized`

- [ ] **Task 2: Inter font load + global font apply**
  - In `index.html` `<head>` add Google Fonts preconnect + Inter weights 400/500/600/700
  - In `tokens.css` apply `body { font-family: var(--font-stack); }`
  - Test in browser: text renders Inter
  - Commit `feat(css): Inter global font`

- [ ] **Task 3: Lucide SVG sprite**
  - Create `icons.svg` containing `<symbol id="...">` definitions for icons used:
    - `settings`(gear)/ `menu`(hamburger)/ `plus`(new chat)/ `chevron-down`(展开)/ `chevron-right` / `external-link`(↗)/ `check-circle`(success)/ `alert-circle`(error)/ `file-down`(download)/ `upload-cloud`(import)/ `file-text`(card)/ `more-vertical`(⋮)/ `arrow-left`(back)/ `zap`(⚡ recall)
  - Use Lucide icons from https://lucide.dev (MIT, vendored)
  - Commit `feat(icons): Lucide SVG sprite vendored`

- [ ] **Task 4: Icon helper**
  - In `app.js` add `icon(name, size=18)` helper returning `<svg width="${size}" height="${size}"><use href="/static/icons.svg#${name}"/></svg>`
  - Stroke 1.5-1.8px applied via CSS `svg use` selector
  - Replace existing inline SVGs in `index.html` with `<use>` references
  - Commit `feat(ui): Lucide icon helper + sprite refs`

- [ ] **Task 5: Button system — 3-tier affordance**
  - CSS classes:
    ```css
    .btn-primary { background:var(--accent); color:white; border:none; ... }
    .btn-recovery { background:transparent; color:var(--accent); border:1px solid var(--accent); ... }
    .btn-secondary-link { background:none; color:var(--text-secondary); ... }
    ```
  - All have hover/active/disabled/loading states(per skill 5 button states)
  - Transition 150ms ease
  - Test in browser by inspecting each component
  - Commit `feat(css): 3-tier button affordance hierarchy`

- [ ] **Task 6: Loading state — 3-dot pulse + 1.5s threshold**
  - In `states.js`:`function showLoading(target, label='正在想...')` →
    - Inserts `<div class="loading"><span class="dot"></span>...x3<span class="label">${label}</span></div>`
    - Schedule timeout 1500ms → if loading still active,append small grey "通常 2-4 秒" hint
  - CSS `.dot` pulse 1.4s infinite ease-in-out staggered 0.2s(per spec)
  - Test:trigger loading > 1.5s,verify hint appears; < 1.5s,verify no hint
  - Commit `feat(states): loading 3-dot pulse with 1.5s threshold hint`

- [ ] **Task 7: Error state — Lucide alert-circle + recovery button**
  - In `states.js`:`function showError(target, {title, msg, recoveryAction})` →
    - Renders alert-circle icon + title + msg + recovery `btn-recovery` button
  - Test in browser via mock 401 from settings test connection → state renders correctly
  - Commit `feat(states): error with Lucide icon + ghost recovery`

- [ ] **Task 8: Success state — Lucide check-circle + brand 叙事**
  - In `states.js`:`function showSuccess(target, {title, msg})` →
    - Renders check-circle + title + msg
    - For export success specifically:msg = "47 张卡片 · 2.3 MB · markdown / 下载已到你的浏览器 · Your data, your file"
  - Apply `#5` micro-adj 3:no celebration box,just text + icon
  - Commit `feat(states): success with brand 叙事 (Your data, your file)`

- [ ] **Task 9: Empty state pattern**
  - In `states.js`:`function showEmpty(target, {icon, title, hint, ctaLabel, ctaAction})` →
    - Centered icon(line-stroke 1.2px,32-48px size for emphasis)+ title + hint + primary CTA
  - Apply to `#3a` 0-card vault state
  - Commit `feat(states): empty state pattern`

- [ ] **Task 10: Apply tokens to existing surfaces**
  - Sweep existing `app.css`:replace hardcoded colors(`#fff`,`#aaa`,etc.)with `var(--text-primary)` etc.
  - Replace hardcoded radii with `var(--radius-md)` etc.
  - Test: visual diff before/after — should be visually identical to current sign-off mockups
  - Commit `refactor(css): existing surfaces use tokens`

- [ ] **Task 11: Mobile viewport sweep**
  - Open at 375px: verify font readable / buttons tappable / no horizontal scroll
  - Fix any viewport issues
  - Commit `fix(css): mobile viewport polish`

- [ ] **Task 12: Visual regression manual check**
  - At 1280px / 1600px / 768px / 375px: open chat / settings modal / vault tab / state demos(loading / error / success / empty)
  - Verify all match `#5` spec(B + amber + Inter + Lucide + 3-tier)
  - Commit `chore(test): #5 visual regression manual verified`

## Done criteria

- [ ] All visual tokens centralized in `tokens.css` ✓
- [ ] Inter font globally applied + Google Fonts loaded ✓
- [ ] Lucide SVG sprite + icon helper ✓
- [ ] 3-tier button affordance ✓
- [ ] State visual system(loading 1.5s threshold + error ghost recovery + success "Your data, your file" + empty pattern)✓
- [ ] All existing surfaces use tokens(no hardcoded colors)✓
- [ ] Mobile viewport not broken ✓

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位:plan 中无 brand 硬编码
2. ✓ Desktop-first
3. ✓ §7.4 5 项 articulated
4. ✓ Pre-mortem 4 modes(brainstorm 已 5/5)
5. ✓ 桌面横向利用率(token system 不影响 layout)
6. ✓ Mobile responsive task 11 显式
7. ✓ Empty state pattern task 9

## References

- Scenarios: cross-cutting visual consistency baseline applies to all features (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` §"Visual consistency"). Plus standalone S-CHAT-VISUAL — `#5` empty-state pattern instantiated on the chat surface.
- Spec: `web-product-design.md` §3, §5.4
- Brainstorm: 屏 19 `#5` 视觉抛光收口
- 4 micro-adj:loading 1.5s 阈值 / error ghost button / success "Your data, your file" / 7 项 checklist 入协议(已完成)
