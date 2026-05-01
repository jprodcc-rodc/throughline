# `#8` 占位 UI — Implementation Plan

> **For agentic workers:** Use `superpowers:test-driven-development` per task.

**Goal:** Implement "What I just saved" Card with Promise UI shell that renders below each AI reply. Backend hook stub returns mock 4 fields(real extraction comes in `#claim-extraction`)。Vault badge increment animation hooked up but reads from mock data。

**Architecture:** Frontend renders card UI inline after AI reply. Backend stub adds `_claim_placeholder` field to chat response. Real `#claim-extraction` replaces stub later.

**Tech Stack:** Existing chat path · pure HTML/CSS/JS · stub backend hook

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | A · Card with Promise:琥珀淡背景 + 边框 + 4 字段(主题/忧虑/希望/问题)+ promise 行"下次提到这些任一项,我会主动带回来 ↗" + Vault badge `+1` 动画(数字 highlight). |
| 产品策略假设 | UI shell ready 给 alpha demo 用 + `#claim-extraction` 完即可接通真数据。截图 / 录视频 launch demo 不被 backend 阻塞. |
| 适合 / 不适合 | **适合**: alpha 阶段 demo screenshot / 视频录制. **不适合**: 真用户 onboarding(占位文案让用户失望)— 因此 mark UI as "demo mode" until `#claim-extraction` lands. |
| Trade-off | + UI 早 ready 可 demo + 跟 `#claim-extraction` cleanly 对接 / − 占位文案没真实价值,alpha 用户会发现是 mock |
| 最大风险 | Alpha 用户看到占位文案以为是 final feature → 失望。**缓解**:`#claim-extraction` P0 同 wave 启动,占位 UI 在 wave 末已被替换。Alpha 邀请 batch 1 在 wave 1 + 2 完成后才发(per protocol §5.4)。 |

## Ambiguity flag

✓ **无 ambiguity**(spec locked, this is shell only)。

## Files

**Modify**:
- `app/web/server.py` — add stub field `_claim_placeholder` to `/api/chat` response
- `app/web/static/app.js` — render Card with Promise after each AI reply
- `app/web/static/app.css` — card styles
- `app/web/static/index.html` — Vault badge animation hook in topbar

**Test**: `app/web/test_chat_placeholder.py`

## Bite-sized TDD tasks

- [ ] **Task 1: Backend stub field**
  - Write failing test `test_chat_placeholder.py::test_chat_response_includes_placeholder` — POST `/api/chat` with user msg → response includes `_claim_placeholder: {topic, concern, hope, question}` with mock values
  - Implement stub in `server.py`:after AI reply,add hardcoded `_claim_placeholder = {topic: "(placeholder topic)", concern: "(...)", hope: "(...)", question: "(...)"}` 
  - PASS
  - Commit `feat(api): chat response stub _claim_placeholder field`

- [ ] **Task 2: Card markup helper**
  - In `app.js` add `renderClaimCard(claim)` function returning HTML string:
    ```html
    <div class="claim-card">
      <div class="claim-card-header">
        <span class="claim-card-label">已记下</span>
        <span class="claim-card-vault-hint">→ Vault +1</span>
      </div>
      <div class="claim-card-fields">
        <div class="field-row"><span class="field-key">主题</span><span class="field-val">${claim.topic}</span></div>
        <!-- ... 3 more fields ... -->
      </div>
      <div class="claim-card-promise">下次提到这些任一项,我会主动带回来 ↗</div>
    </div>
    ```
  - If field is null/empty → omit row(per spec edge case 1 "缺字段不硬塞")
  - Commit `feat(ui): claim card render helper`

- [ ] **Task 3: Card styles per spec**
  - CSS:`background: rgba(217,119,6,0.05); border: 1px solid rgba(217,119,6,0.2); border-radius: var(--radius-md); padding: 11px 14px;`
  - `.claim-card-label`:9px uppercase amber bold
  - `.field-key`:10px uppercase grey min-width 42px
  - `.field-val`:11px primary text
  - `.claim-card-promise`:9px secondary, top border subtle
  - Commit `feat(css): claim card visual per spec`

- [ ] **Task 4: Render card after each AI reply**
  - In existing chat reply handler in `app.js`:after rendering AI message,if `response._claim_placeholder` present → append `renderClaimCard(...)` below it
  - Test: send user msg → AI reply → claim card visible below
  - Commit `feat(ui): claim card inline after AI reply`

- [ ] **Task 5: Vault badge increment animation**
  - In `index.html` topbar Vault tab,wrap badge number in `<span id="vault-badge">47</span>`
  - In `app.js`,after rendering claim card → animate `vault-badge`:
    - Increment number(47 → 48)
    - Brief amber highlight via CSS class `pulse-once` for 600ms
  - CSS `.pulse-once { animation: pulseOnce 600ms ease-out; }` with keyframe scale + amber glow
  - Commit `feat(ui): vault badge increment animation on save`

- [ ] **Task 6: Edge case rendering**
  - Mock backend response with various states:all 4 fields / 2 fields only / 0 fields(no card)
  - Verify edge cases:
    - 4 fields → full card rendered
    - 2 fields → only 2 rows(no placeholder injected)
    - 0 fields → no card rendered + Vault badge NOT incremented(per spec edge case 1)
  - Commit `feat(ui): claim card edge case handling`

- [ ] **Task 7: Mobile responsive**
  - At <768px:card full-width stack,padding 收紧 8px 10px,4 字段保持纵向
  - Test at 375px
  - Commit `feat(ui): claim card mobile responsive`

- [ ] **Task 8: End-to-end manual test**
  - Send chat → AI reply → claim card appears below with stub fields
  - Vault badge animation runs
  - Switch to Vault tab → no card actually persists(stub only,real persistence in `#claim-extraction`)
  - Document this state explicitly in alpha onboarding hint:"alpha 阶段 What I just saved 显示是占位,完整功能 launch+30 启用"
  - Commit `chore(test): #8 占位 UI end-to-end verified`

## Done criteria

- [ ] `#8` 占位 UI:Card with Promise 视觉完整(琥珀边框 + 4 字段 + promise 行)✓
- [ ] Vault badge `+1` 动画 ✓
- [ ] Edge case 处理(0/2/4 字段)✓
- [ ] Mobile responsive ✓
- [ ] Backend stub `_claim_placeholder` field ready for `#claim-extraction` swap ✓

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位:plan 中 N/A
2. ✓ Desktop-first / mobile responsive task 7
3. ✓ §7.4 5 项 articulated
4. ✓ Pre-mortem(brainstorm 5/5 + 3 micro-adj 改进)
5. ✓ 桌面横向(card inline 在 chat 流,无 split)
6. ✓ Mobile responsive 显式
7. ✓ Empty state(0 fields → no card)显式 task 6

## References

- Scenarios: S-CHAT-1, S-CHAT-2, S-CHAT-3, S-CHAT-4, S-CHAT-5, S-CHAT-6, S-CARD-1, S-CARD-2, S-NAV-2 (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`). S-CHAT-4 (Classifier 边界 case) requires `#intent-classifier` integration — Wave 1a placeholder uses bleed-stop heuristic, real verification of S-CHAT-4 deferred to Wave 1b. S-CHAT-6 (multi-round depth pivot) gated on system-prompt v1.3 + Rodc live walk.
- Spec: `web-product-design.md` §5.5
- Brainstorm: 屏 15 `#8` A 改进版
- See→trust→verify 三段 aha 闭环:placeholder 是第一段(see)。Trust 阶段(Vault badge `+1`)在本 plan 实现。Verify 阶段(`#active-recall` 触发)在 Wave 2 的 `#8` 真功能 + `#active-recall-base` 实现。
- 真功能 plan(Wave 2)将替换 stub `_claim_placeholder` with real `#claim-extraction` output
