# `#9a` History Import — Implementation Plan

> **For agentic workers:** Use `superpowers:test-driven-development` per task.

**Goal:** Implement C · Reality-aware async import flow with email-primary fallback. ChatGPT export only(P1)。1 屏 2 路径(推荐启动 export → 等 → 上传 / 已有 zip → 直接 drop)+ wait state visual signal + email + browser push reminder。

**Architecture:** Frontend single-screen 2-path UI · backend zip parser + import scheduler · email infrastructure(reused for `#b-auth` later)· browser Notifications API for push。

**Tech Stack:** Python `zipfile` · Pydantic schema · SMTP via `aiosmtplib` 或 Resend API(Rodc 决定)· Browser Notifications API

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | 1 屏 2 路径并排 grid: 左推荐(琥珀边框 RECOMMENDED card + "用 OpenRouter →" 不,这里是 "启动 export →" + push/email checkbox)/ 右 BYOK("已有 zip · 直接上传" + drop zone). 等待期间 vault tab 顶部 banner "⏱ ChatGPT 历史合并中". |
| 产品策略假设 | **解构瓶颈** = nice-to-have. 不假装 1-3 小时 wait 是 instant. 让用户在等期间用产品 = retention 杀手锏. (per failure mode positive lesson) |
| 适合 / 不适合 | **适合**: 全部 P1 alpha(70% 没 zip + 20% 有 zip + 10% 都行). **不适合**: P2 才支持的 Claude/Cherry/Markdown sources. |
| Trade-off | + 覆盖 70% 没 zip + 20% 有 zip + 等待留客机制 + brand 一致性 / − 工程稍大(2 路径 + email + push)+ Email 必须扎实(Notifications API tab 关失效) |
| 最大风险 | Email infrastructure P1 不到位 → 用户没收提醒 → 不回来上传 → import 完成率低 → vault 失去历史素材.**缓解**:Email P1 必做(已有 `#b-auth` 用户 email);browser push P1 占位 UI 但只 in-tab 工作;P2 加 真后端 Web Push/FCM. |

## Ambiguity flag

⚠️ **有产品决策点**:
- Email 后端选择(SMTP 自管 vs Resend / Postmark API)— Rodc 决定
- ChatGPT export zip schema — 验证 OpenAI 实际格式后再写 parser(可能要 1 个 sample zip 来 calibrate)
- "等待期间合并"语义:zip 上传后,新 cards 跟之前自动归并到同一 vault — 实施 detail

## Files

**Modify**:
- `app/web/server.py` — add `/api/import/start`,`/api/import/upload`,`/api/import/preview`,`/api/import/process`,`/api/import/status`
- `app/web/static/index.html` — add import view(can be fullscreen or modal in Settings)
- `app/web/static/app.js` — import flow state machine
- `app/web/static/app.css` — import view styles + vault wait banner

**Create**:
- `app/shared/import_py/__init__.py`
- `app/shared/import_py/chatgpt_parser.py` — parse OpenAI export zip
- `app/shared/import_py/import_scheduler.py` — track in-progress imports + scheduled reminders
- `app/shared/email/sender.py` — abstract email send(SMTP or API per Rodc decision)
- `app/shared/email/templates.py` — email templates with [PRODUCT_NAME] placeholders
- `app/shared/email/test_sender.py`
- `app/shared/import_py/test_chatgpt_parser.py`

**Test**: `app/web/test_import_api.py`

## Bite-sized TDD tasks

- [ ] **Task 1: Decide email backend(blocked: Rodc decision)**
  - **PRODUCT DECISION POINT**: SMTP vs Resend API. Document in plan and dispatch with chosen.
  - Default(if Rodc not yet decided): Resend API(simpler, less moving parts, dev plan free tier).
  - Commit `docs: email backend decision = Resend (or SMTP per Rodc)`

- [ ] **Task 2: Email sender abstraction**
  - Write failing test `test_sender.py::test_send_email_with_template` — `EmailSender(backend='resend' or 'smtp').send(to, subject, body)` → returns `{ok: true, message_id: ...}`
  - Implement abstraction with backend selector(starts with Resend per default; SMTP later if Rodc switches)
  - Mock Resend API in test
  - PASS
  - Commit `feat(email): sender abstraction with backend selector`

- [ ] **Task 3: Email templates with [PRODUCT_NAME]**
  - Create `templates.py` with templates:
    - `import_ready`:Subject `继续 [PRODUCT_NAME] · 历史可以合并了`. Body per `#9a` micro-adj 3 spec verbatim with `[PRODUCT_NAME]` placeholder + dynamic vars `{user_name}, {start_time}, {today_card_count}`.
  - Test rendering with sample vars
  - PASS
  - Commit `feat(email): import_ready template with [PRODUCT_NAME] placeholder`

- [ ] **Task 4: ChatGPT export zip parser**
  - **NEEDS_CONTEXT**: get sample ChatGPT export zip from Rodc(real export)— this validates parser against actual schema
  - Write failing test `test_chatgpt_parser.py::test_parse_real_export` using sample zip:
    - Returns list of `Conversation(id, title, messages: [{role, content, timestamp}])`
  - Implement parser:open zip → read `conversations.json` → schema validation → return Conversation list
  - PASS
  - Commit `feat(import): ChatGPT export zip parser`

- [ ] **Task 5: Import scheduler**
  - Write failing test `test_import_scheduler.py::test_register_pending_import` — `scheduler.start_pending(user_id, source='chatgpt', expected_at=now+2h)` → tracks in DB
  - Implement scheduler with new schema migration v3.1 if needed(or use existing tables)
  - On expected_at: schedule email send via `EmailSender`
  - PASS
  - Commit `feat(import): import scheduler with email trigger`

- [ ] **Task 6: POST /api/import/start endpoint**
  - Write failing test `test_import_api.py::test_start_returns_session_id` — POST starts pending import(no zip yet)+ schedules email reminder + returns `{session_id, expected_at}`
  - Implement endpoint
  - PASS
  - Commit `feat(api): POST /api/import/start with reminder`

- [ ] **Task 7: POST /api/import/upload endpoint**
  - Write failing test `test_upload_parses_zip_returns_preview` — POST with zip file → returns preview `{conversation_count, date_range, sample_titles: [first 3]}`
  - Implement endpoint using parser
  - PASS
  - Commit `feat(api): POST /api/import/upload with parse + preview`

- [ ] **Task 8: POST /api/import/process endpoint**
  - Write failing test `test_process_creates_cards_and_merges` — POST with `session_id` + `selected_conversation_ids` → creates cards in vault(reusing existing card adapter)+ marks import done
  - **Merge semantics**:new cards from import 跟 today's chat cards 合并 to single vault. Per spec "几小时前的对话会合并到你今天 vault 里". Cards keep their original timestamps(not "imported at"), so time-grouping in `#3a` shows them in correct date groups.
  - Implement endpoint
  - PASS
  - Commit `feat(api): POST /api/import/process with vault merge`

- [ ] **Task 9: GET /api/import/status endpoint**
  - Write failing test `test_status_returns_pending_or_done` — pending session returns `{status: 'pending', started_at, expected_at}`; completed returns `{status: 'done', completed_at, card_count}`
  - Implement endpoint
  - PASS
  - Commit `feat(api): GET /api/import/status`

- [ ] **Task 10: Frontend import view markup**
  - Add `<section id="import-view">` accessible from Settings ("导入历史")或 Onboarding step 4(可选,P1 spec 不做 onboarding step 4)
  - Markup per屏 20 spec:title + tagline + 2-path grid(recommended OpenRouter 改成 ChatGPT export start path / BYOK 直接 drop)
  - Drop zone with Lucide upload-cloud icon
  - Apply `#5` tokens
  - Commit `feat(ui): import view markup`

- [ ] **Task 11: Recommended path(start ChatGPT export)**
  - Click "启动 export → 跳到 ChatGPT 设置" → opens new tab to `https://chat.openai.com/#settings/data-controls`
  - Same time POST `/api/import/start` → records pending session + schedules email
  - Show inline:"等邮件期间,你可以继续用 [PRODUCT_NAME]"
  - Push checkbox + Email checkbox(both checked default)
  - Commit `feat(ui): recommended path with email scheduling`

- [ ] **Task 12: BYOK path(direct upload)**
  - Drop zone accepts zip file → POST `/api/import/upload` → render preview(conversation count + date range + sample titles)
  - "导入选项":All / Last 6 months / Last 90 days / Custom date range(per `APP_ONBOARDING_SPEC §四`)
  - "Import" CTA → POST `/api/import/process` → progress + done state(success "导入 N 张 · merged into vault")
  - Commit `feat(ui): BYOK direct upload with preview + selection`

- [ ] **Task 13: Browser Notifications API push(in-tab only)**
  - On `/api/import/start`,if push checkbox checked → `Notification.requestPermission()` then schedule `setTimeout(() => new Notification(...), 2 * 60 * 60 * 1000)` for 2h reminder
  - Document limitation:"browser push 仅在网页打开时触发"(per `#9a` engineering risk note)
  - Email is real fallback
  - Commit `feat(ui): in-tab browser push + 2h reminder`

- [ ] **Task 14: Vault tab wait banner**
  - When pending import exists,Vault tab shows top banner:`⏱ ChatGPT 历史合并中 · 预计 X 小时(启动于 14:23)`
  - Settings page status:`Import status: waiting for OpenAI · 启动于 14:23`
  - Apply `#5` tokens(small banner with amber accent)
  - Commit `feat(ui): vault wait state visual signal`

- [ ] **Task 15: Mobile responsive**
  - 2-path grid stack on <768px(recommended first, BYOK second)
  - Drop zone changes to "选择 zip"按钮(touchscreen friendly)
  - Test at 375px
  - Commit `feat(ui): import view mobile responsive`

- [ ] **Task 16: End-to-end manual test**
  - Path 1: 启动 export → email scheduled → manual trigger email send → click email → upload zip → preview → import → vault populated
  - Path 2: drop zip directly → preview → import
  - Verify wait banner appears + disappears after import done
  - Test with sample real ChatGPT export from Rodc
  - Commit `chore(test): #9a end-to-end manual verified`

## Done criteria

- [ ] `#9a` import flow:C 形态 2 路径 ✓
- [ ] Wait state visual signal(vault banner + Settings status)✓
- [ ] Email primary fallback(Resend or SMTP per Rodc)+ template with [PRODUCT_NAME]✓
- [ ] Browser Notifications API push(in-tab only,P2 升 Web Push/FCM)✓
- [ ] ChatGPT export only(Claude/Cherry/Markdown 显式标 P2)✓
- [ ] Selection UI:All / Last 6m / Last 90d / Custom ✓
- [ ] Vault merge semantics:cards keep original timestamps ✓

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位 全用
2. ✓ Desktop-first / mobile responsive task 15
3. ✓ §7.4 5 项 articulated
4. ✓ Pre-mortem(brainstorm 5/5 + 4 ★ — 解构瓶颈最强例)
5. ✓ 桌面横向(2-path grid)
6. ✓ Mobile responsive 显式
7. ✓ Empty state:N/A(本身就是 import 启动屏)+ Wait state covered task 14

## References

- Scenarios: S-IMPORT-1, S-IMPORT-2, S-IMPORT-3 (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`)
- Spec: `web-product-design.md` §5.7
- Brainstorm: 屏 20 `#9a` C async + 4 micro-adj
- Failure mode positive lesson:"Deconstruct Bottlenecks Into Nice-to-Have"(`feedback_design_judgment_failures.md`)
- Engineering risk:Browser Notifications API tab-only constraint → email primary
