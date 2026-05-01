# `#1a` Settings Panel — Implementation Plan

> **For agentic workers:** Use `superpowers:test-driven-development` for each task.

**Goal:** Implement Settings central modal accessible from Vault tab gear icon. 4 fields(provider / API key / vault path / save) + test connection + 3-path failure diagnosis + key 加密存储.

**Architecture:** FastAPI backend endpoint(`/api/settings` GET/POST + `/api/settings/test`)+ frontend modal component triggered by 顶栏齿轮按钮. Key 加密存储基于 OS keychain via `keyring` Python lib(fallback to encrypted file)。

**Tech Stack:** Python `keyring` lib · FastAPI · existing `app/web/server.py` + `static/index.html` + `static/app.js`

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | Central modal triggered from 顶栏齿轮 icon. Sections: Provider 下拉 / Key input + Test button / Vault path / Save. 失败诊断 inline 在 input 下方,3 路径 specific msg(format wrong / no permission / network)。 |
| 产品策略假设 | 设置不是日常 task,模态最少 chrome,改完即关。在 onboarding step 2 不复用此模态(那有独立简化版)。 |
| 适合 / 不适合 | **适合**: in-app 临时调整 settings(切 provider / 换 key / 看 vault 状态)。**不适合**: onboarding step 2 用(独立简化屏 only ask provider+key)。 |
| Trade-off | + 模态最少 chrome,跟 IA-A drawer 精神一致 + 移动自动全屏 / − 4 fields 全展开,onboarding 复用会显重 |
| 最大风险 | Key 加密机制选错。`keyring` lib 跨平台 OS keychain 是默认推荐,但若 alpha 用户有 keychain 权限问题,fallback 到 encrypted SQLite。**有产品决策点:** Rodc 选 keyring vs encrypted SQLite default。 |

## Ambiguity flag

⚠️ **有产品决策点**:Key 加密策略(`keyring` OS keychain vs encrypted SQLite vs both)。**Rodc v1.1 预答**:keyring 默认 + encrypted SQLite fallback,确认 OK。

## Dev mode behavior(v1.1 新增 per finding 5)

`#1a` 设置面板必须区分 dev vs production:

**Dev mode 检测条件**(任一 true):
- env var `RODIX_DEV=1`
- hostname == `rodix.local`(per `#b-dev-deploy`)

**Dev mode default 行为**:
- Provider 自动配 = OpenRouter
- Default model = `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`
- Key 从 env var `OPENAI_API_KEY` 读(不 force user 在 settings 输)
- Settings 模态打开时显示 "DEV MODE" 横幅 + 默认值 prefilled

**Production mode default**:
- 无默认 — onboarding step 2 force BYOK
- 用户必须在 settings 配 provider + key
- 无 "DEV MODE" 横幅

## Files

**Modify**:
- `app/web/server.py` — add settings endpoints
- `app/web/static/index.html` — add gear icon + modal markup
- `app/web/static/app.js` — modal show/hide + form handlers
- `app/web/static/app.css` — modal styles per `#5` token spec

**Create**:
- `app/shared/secrets/key_storage.py` — encrypted key persistence(keyring + fallback)
- `app/shared/secrets/test_key_storage.py`

**Test**: `app/web/test_settings.py`

## Bite-sized TDD tasks

- [ ] **Task 1: Spec key_storage interface**
  - Write failing test `test_key_storage.py::test_set_and_get_key` — `KeyStorage().set("OPENROUTER_API_KEY", "sk-or-v1-...")` then `get` returns same value.
  - Run pytest: should fail "module not found"
  - Implement minimal `key_storage.py` with `KeyStorage` class wrapping `keyring`(`keyring.set_password` / `get_password` with namespace `[PRODUCT_NAME]`)
  - Run pytest: PASS
  - Commit `feat(secrets): KeyStorage with keyring backing`

- [ ] **Task 2: Test fallback path**
  - Write failing test `test_key_storage.py::test_fallback_when_keyring_unavailable` — mock `keyring` to raise → KeyStorage falls back to encrypted SQLite
  - Implement fallback using existing `app/shared/storage_py/` adapter pattern + Fernet encryption
  - PASS
  - Commit `feat(secrets): SQLite fallback when keyring unavailable`

- [ ] **Task 3: Settings GET endpoint**
  - Write failing test `test_settings.py::test_get_settings_returns_provider_and_vault` — GET `/api/settings` returns `{provider, vault_path, key_set: bool}`(NEVER returns the actual key)
  - Implement endpoint reading from KeyStorage + env
  - PASS
  - Commit `feat(api): GET /api/settings`

- [ ] **Task 4: Settings POST endpoint**
  - Write failing test `test_settings.py::test_post_settings_persists_provider_and_key` — POST with provider/key/vault_path → KeyStorage updated
  - Implement endpoint
  - PASS
  - Commit `feat(api): POST /api/settings`

- [ ] **Task 5: Test connection endpoint**
  - Write 3 failing tests for failure diagnosis paths:
    - `test_test_connection_invalid_format` — provider=openai but key doesn't start with sk- → returns `{ok: false, reason: "format"}`
    - `test_test_connection_no_permission` — mock 401 from provider → returns `{ok: false, reason: "no_permission"}`
    - `test_test_connection_network_error` — mock ConnectionError → returns `{ok: false, reason: "network"}`
  - Implement `/api/settings/test` calling provider's auth check endpoint(reuse existing `throughline_cli.providers.test_key`)
  - All PASS
  - Commit `feat(api): POST /api/settings/test with 3-path diagnosis`

- [ ] **Task 6: Frontend gear icon + modal markup**
  - Modify `app/web/static/index.html` — add gear icon to topbar(Lucide settings SVG, 18px, line stroke 1.5)
  - Add modal markup `<dialog id="settings-modal">` with 4 sections per spec
  - No JS yet, just markup
  - Commit `feat(ui): settings modal markup with gear icon`

- [ ] **Task 7: Frontend modal show/hide + GET render**
  - Add JS handler in `app.js`:click gear → fetch `/api/settings` → populate modal → `dialog.showModal()`
  - Apply `#5` 视觉抛光 token spec(modal bg `#1c1c1f` / border `rgba(255,255,255,0.08)` / 16px font / amber primary CTA)
  - Visual: provider 下拉(OpenRouter / OpenAI / Anthropic / Ollama)+ key input(masked,显 last 4 chars only)+ vault path readonly + 测试 ghost button + 保存 primary
  - Manual test in browser
  - Commit `feat(ui): settings modal load and show`

- [ ] **Task 8: Frontend save + test connection**
  - Click 测试 → POST `/api/settings/test` → render diagnosis inline below input(success: 绿色 ✓ + provider; failure: 红色 ✕ + reason msg)
  - Click 保存 → POST `/api/settings` → success toast → close modal
  - Apply `#5` 3-tier affordance:Save = primary 实心 / Test = ghost / "更多帮助" = secondary link
  - Manual test all paths
  - Commit `feat(ui): settings save and test connection`

- [ ] **Task 9: Mobile responsive**
  - Modal auto-fullscreen on `< 768px` viewport via CSS media query
  - Test at 375px viewport
  - Commit `feat(ui): mobile fullscreen settings modal`

- [ ] **Task 10: Dev mode detection + default(v1.1 加)**
  - Write failing test `test_settings.py::test_dev_mode_provides_defaults` — env `RODIX_DEV=1` set → GET `/api/settings` returns defaults pre-filled(provider=OpenRouter, model=nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free)
  - Implement detection:`is_dev_mode()` returns True if env var or hostname check
  - In modal:if dev mode → show "DEV MODE · 默认免费模型" 横幅 + prefill
  - PASS
  - Commit `feat(settings): dev mode detection + free model default`

- [ ] **Task 11: Final integration test**
  - Manual end-to-end:open app → 齿轮 → 模态 → 改 provider → 测试连接 → 保存 → 关闭 → 模态再打开 → 数据持久
  - Verify key encrypted at rest(check storage backend)
  - Test in dev mode(`RODIX_DEV=1`):defaults filled + DEV MODE banner
  - Test in production mode:无 defaults + 无 banner
  - Commit `chore(test): #1a end-to-end manual verified`

## Done criteria(per `web-product-design.md` §7 alignment)

- [ ] `#1a` 设置模态:provider 切换 ✓
- [ ] Key 输入 + test connection 成功 ✓
- [ ] 失败诊断 3 路径(format / no_permission / network)✓
- [ ] Key 加密存储(keyring + fallback)✓
- [ ] Vault path 显示 ✓
- [ ] 移动端自动全屏 ✓
- [ ] 跟 onboarding step 2 NOT 复用(独立简化屏 by `#2a`)✓

## §7.5 7 项 pre-push checklist(plan-adapted)

1. ✓ `[PRODUCT_NAME]` 占位:plan 中无硬编码"Rodix"
2. ✓ Desktop-first:modal 桌面中央 + 移动 fullscreen fallback
3. ✓ §7.4 5 项 articulated 在上方
4. ✓ Pre-mortem 4 modes considered:like-me OK / metric vs goal OK / reactive vs strategic OK / edge vs main OK
5. ✓ 桌面横向利用率:modal 居中,无 split layout(适合此场景)
6. ✓ Mobile responsive:fullscreen at <768px
7. ✓ Empty state:N/A(modal 总有 4 fields,无空状态)

## References

- Scenarios: S-SETTINGS-1, S-SETTINGS-2, S-EDGE-2 (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`)
- Spec: `web-product-design.md` §5.3
- Brainstorm: `2026-05-01-rodix-brainstorm.md` 屏 06 + `#1a` 完整 spec 节
- IA-C cascade: 顶栏齿轮入口 → modal,drawer 不再装 settings
