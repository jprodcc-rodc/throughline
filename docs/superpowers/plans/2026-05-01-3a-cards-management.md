# `#3a` Cards Management — Implementation Plan

> **Status (2026-05-02):** v1.3 — Rodc reviewed v1.2,**1 push back incorporated** (mobile breakpoint 768-1023px clarification per Option A: ≥768px 都 35/65 + padding 调整,< 768px 单列)。**Approved for implementer dispatch** per protocol §5.5. Implementer can dispatch parallel with `#claim-extraction` (no shared deps; #3a uses mock fixtures Choice A).
> **For agentic workers:** Use `superpowers:test-driven-development` per task. Then `superpowers:subagent-driven-development` extended with `docs/superpowers/skills/scenario-verification.md`.
> **App/ gitignored** — `app/web/server.py` + `app/web/static/*` + `app/shared/storage_py/*` modifications do NOT go to git. Skip the per-task `Commit ...` lines for those files; they're disk-only. Files under `app/shared/storage_py/fixtures/cards/*.json` and tests therein are also gitignored. **Tracked**: nothing new — no fixtures/ artifacts here (mock fixtures live in app/, not fixtures/).

**Goal:** Implement Vault tab master-detail(35/65 桌面 full-bleed)with 时间分组 + 4 级 cold start + Recall summary 阈值 3 + 删除 + Markdown 导出。No dependency on `#claim-extraction` — uses mock fixtures (Choice A per finding 7) so #3a + #claim-extraction can dispatch in parallel.

**Architecture:** Client-side routing under Vault tab. Left list rendered from `/api/cards?group=time`(extends existing endpoint),right detail panel rendered from `/api/cards/{id}`(new endpoint). Cold start lifecycle = client-side rendering branch by `vault.length`。

**Tech Stack:** Pure HTML/CSS/JS · existing `/api/cards` endpoint(extend with grouping)+ new endpoints

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | 桌面 35/65 master-detail · full-bleed 撑满 viewport. 左:时间分组(今天/本周/本月/历史)+ sticky 琥珀 date headers + 选中态琥珀竖条. 每行 metadata: `时间 · N 字段 · N 次 recall`. 右:完整 detail panel(标题 + recall 计数琥珀标签 + 4 字段 + 关联对话引述 + Recall 历史 summary). |
| 产品策略假设 | "thinking history is your asset" narrative。time-based memory retrieval = 知识工作者 mental model。 |
| 适合 / 不适合 | **适合**: P1 alpha vault < 100 张 + 桌面重读型用户。**不适合**: P3 vault 几千+(需 search/filter)。 |
| Trade-off | + brand 叙事强 + 桌面横向 35/65 满 / − 实施略复杂(date grouping + sticky headers + 4-tier cold start) |
| 最大风险 | 1-5 张默认选中第一张 cold start 实现错(显示空架子)。**已通过 4-tier lifecycle spec 缓解**。 |

## Ambiguity flag

✓ **无 ambiguity**(spec 全面 locked)。Recall summary 阈值 3 P1 假设,P2 telemetry 调。

## Mock fixtures strategy(v1.2 修订 per Issue 3 — DB isolation)

`#3a` Wave 1b 实施时 `#claim-extraction` 可能未完成,**显式 commit 用 mock fixtures 解耦**(per finding 7 Choice A)。

**Issue 3 mitigation — Dev / Production DB isolation(必须先做)**:

| Mode | DB file | Switch trigger |
|---|---|---|
| Dev mode(`RODIX_DEV=1` 或 hostname `rodix.local`)| `~/[PRODUCT_NAME]/vault/.[PRODUCT_NAME]/index_dev.db` | env var |
| Production mode | `~/[PRODUCT_NAME]/vault/.[PRODUCT_NAME]/index.db` | default |

**关键纪律**:
- Fixture loader **只写 dev DB**(production endpoint 403)
- Dev DB 跟 production DB **完全隔离**(不同文件)
- Rodc dogfood 时切回 production mode(unset `RODIX_DEV`)→ 看自己真 vault
- 不会污染 dogfood 真 data,切换可控

**实施改动 in `app/shared/storage_py/`**:
- `vault_path.py` 加 `is_dev_mode()` check + 返回 `index_dev.db` vs `index.db`
- 现有 adapter 全自动用新 path(无 breaking change)

**4 套 fixture 数据 cover 4 级 cold start lifecycle**:

| Fixture | 卡片数 | 内容 | 用途 |
|---|---|---|---|
| `fixture_empty.json` | 0 | — | Cold start 0 张:empty state "Your first thought saved here →" |
| `fixture_few.json` | 3 | 3 张 today 内,各异主题 | Cold start 1-5 张:default-select first card,detail panel 实时填 |
| `fixture_medium.json` | 15 | 跨多日,主题多样,部分有 recall 历史(N=1, N=4 测试 summary toggle) | Cold start 6-50 张:stats 空白态 + sticky date headers + recall summary |
| `fixture_large.json` | 60 | 跨数月,deep recall 历史(N>20 测试 summary 大数字) | Cold start 50+ 张:stats + thinking trends placeholder + 无限滚动验证 |

每 fixture 是 JSON 文件,加载到 dev mode test endpoint `/api/dev/load-fixture?name=...`(only enabled in dev mode per `RODIX_DEV=1`)。

**好处**:
- `#3a` 实施完全独立 `#claim-extraction`(并行 dispatch 友好)
- Cold start 4 级 lifecycle 单元测试可控(fixture 是确定性数据)
- Demo screenshot 用 fixture_medium 状态,展示 product 形态而不是真实 Rodc 数据

**fixture 写哪儿**: `app/shared/storage_py/fixtures/cards/`

## Files

**Modify**:
- `app/web/server.py` — extend `/api/cards` with `?group=time`
- `app/web/static/index.html` — add Vault tab structure(per IA-C)
- `app/web/static/app.js` — vault view state machine + 4-tier rendering
- `app/web/static/app.css` — master-detail layout + sticky headers

**Create**:
- `app/web/server.py` — `/api/cards/{id}` GET(detail),`DELETE /api/cards/{id}`,`GET /api/cards/export?format=markdown`
- `app/shared/storage_py/cards_query.py` — time grouping logic(or extend `claim_adapter.py`)
- `app/shared/export/markdown_exporter.py`

**Test**: `app/web/test_cards_api.py`,`app/shared/storage_py/test_cards_query.py`,`app/shared/export/test_markdown_exporter.py`

## Bite-sized TDD tasks

- [ ] **Task 1: Cards query — time grouping**
  - Write failing test `test_cards_query.py::test_group_by_time` — given 5 cards across dates, returns `{今天:[...], 本周:[...], 本月:[...], 历史:[...]}` with correct group assignment(based on `created_at` vs `now`)
  - Implement `cards_query.group_by_time(cards, now)` pure function
  - PASS
  - Commit `feat(query): card time grouping`

- [ ] **Task 2: Cards query — empty group skip**
  - Write failing test `test_group_by_time_skips_empty_groups` — given 2 cards both today,returns `{今天:[...]}` only(not empty 本周/本月/历史)
  - Implement skip logic
  - PASS
  - Commit `feat(query): skip empty time groups`

- [ ] **Task 3: GET /api/cards?group=time**
  - Write failing test `test_cards_api.py::test_get_cards_grouped` — endpoint returns time-grouped JSON + each card has `recall_count`(query `recall_events` adapter)
  - Implement endpoint extending existing `/api/cards`
  - PASS
  - Commit `feat(api): GET /api/cards?group=time with recall counts`

- [ ] **Task 4: GET /api/cards/{id} detail**
  - Write failing test `test_get_card_detail_returns_4_fields_plus_recall_history` — single card returns full claim 4-fields + 关联对话 message ID + recall history list
  - Implement endpoint joining cards + claims + messages + recall_events
  - PASS
  - Commit `feat(api): GET /api/cards/{id} detail with recall history`

- [ ] **Task 5: DELETE /api/cards/{id}**
  - Write failing test `test_delete_card_removes_record_and_dependents` — deletes card + cascade removes claims/recall_events
  - Implement
  - PASS
  - Commit `feat(api): DELETE /api/cards/{id} with cascade`

- [ ] **Task 6: Markdown exporter**
  - Write failing test `test_markdown_exporter.py::test_export_card_to_markdown` — given card with 4 fields,produces markdown with frontmatter(date / topic)+ structured sections
  - Implement `markdown_exporter.export_cards(cards) -> str`
  - PASS
  - Commit `feat(export): markdown exporter for cards`

- [ ] **Task 7: GET /api/cards/export endpoint**
  - Write failing test for endpoint returning `Content-Type: text/markdown` with all cards
  - Implement endpoint reusing exporter
  - PASS
  - Commit `feat(api): GET /api/cards/export?format=markdown`

- [ ] **Task 8: Vault tab markup + IA-C tabs**
  - Modify `index.html` topbar to include 3 tabs(Chat default / Vault badge / Decisions badge)
  - Add `<section id="vault-tab">` with master-detail layout shell:`<aside class="vault-list">` 35% + `<main class="vault-detail">` 65%
  - Apply `#5` tokens(border `rgba(255,255,255,0.05)` / surface `#1c1c1f`)
  - Commit `feat(ui): vault tab markup with IA-C tabs`

- [ ] **Task 9: Vault list render — time-grouped**
  - JS:`renderVaultList(grouped)` iterating groups → sticky date headers(琥珀 today,grey others)→ row per card(标题 + metadata `14:23 · 4 字段 · 1 次 recall` + ⋮ menu)
  - Click row → highlight + render detail
  - Commit `feat(ui): vault time-grouped list rendering`

- [ ] **Task 10: Vault detail panel render**
  - JS:`renderCardDetail(card)` →
    - Header:title + 时间 + recall 计数琥珀标签 `已被 recall N 次`
    - 4 字段块(主题/忧虑/希望/问题,每个 entity 类型 LABEL + value)
    - 关联对话引述 with `→ 跳到对话 #X` link(切到 Chat tab + 滚到 message)
    - Recall 历史 summary(if N > 3: 一行 summary + 展开,else: full timeline inline)
  - Apply `#5` tokens
  - Commit `feat(ui): card detail panel render`

- [ ] **Task 11: 4-tier cold start lifecycle**
  - JS:`renderVaultEmptyState(vaultLength)`:
    - **0**:full empty state "Your first thought saved here →" + Chat tab CTA(no list, no stats)
    - **1-5**:default-select first card,detail panel populated
    - **6-50**:default no-select,right shows stats(总卡数 / 7 天活跃图 / 最常 recall 主题)— stats fetched from new `/api/vault/stats`
    - **50+**:stats + thinking trends(P2 hook,for now show same as 6-50)
  - Test all 4 paths manually with seed data
  - Commit `feat(ui): 4-tier cold start lifecycle`

- [ ] **Task 12: Recall summary toggle**
  - JS:`renderRecallHistory(card.recall_history)` → if length ≤ 3 inline timeline,else summary line `已 recall N 次 · M 次用上了 · 最近: ...` + click 展开
  - Commit `feat(ui): recall summary mode at threshold 3`

- [ ] **Task 13: Per-card actions(⋮ menu)**
  - JS:click ⋮ → tiny popup with `导出 / 删除`
  - 导出 → call `/api/cards/{id}/export` with `Accept: text/markdown` → trigger download
  - 删除 → confirmation modal → DELETE → reload list
  - Commit `feat(ui): card per-row actions`

- [ ] **Task 14: 导出全部 button**
  - JS:click "导出全部 ↓" in toolbar → call `/api/cards/export?format=markdown` → trigger download
  - SUCCESS state(per `#5` micro-adj 3): toast "导出 47 张卡片 · 2.3 MB · markdown / 下载已到你的浏览器 · Your data, your file"
  - Commit `feat(ui): bulk markdown export with brand 叙事`

- [ ] **Task 15: Responsive breakpoints**(v1.3 修订 per Rodc push back — explicit 768-1023px range per Option A)

  **Breakpoint table** (locked v1.3):

  | Viewport | Layout | Padding | Notes |
  |---|---|---|---|
  | **≥ 1024px**(desktop) | 35/65 master-detail full-bleed | comfortable: list 24px / detail 32px | default; spec §5.6 baseline |
  | **768-1023px**(iPad landscape) | **35/65 same as desktop** | tight: list 16px / detail 20px | only padding 缩小,不切 layout |
  | **< 768px**(phone / iPad portrait) | single column,push fullscreen detail + back ← | 16px | row click → detail view; 顶左 ← 回 list |

  **关键纪律**:768-1023px 不要切到 45/55 或浮层 — 简单 + 一致 > 多模式 layout。详 detail panel 在 iPad landscape 也用 35/65 (~614px wide) 完全够展开 4 字段块。

  **TDD**:
  - Write failing CSS unit test(or browser smoke at 1024px / 1023px / 768px / 375px)— layout 切换在正确断点
  - Implement `app.css` media queries:
    ```css
    /* default desktop ≥ 1024px */
    @media (min-width: 1024px) { ... }
    /* iPad landscape 768-1023px */
    @media (min-width: 768px) and (max-width: 1023px) { ... }
    /* phone / iPad portrait < 768px */
    @media (max-width: 767px) { ... }
    ```
  - Test viewport sizes: 1440 / 1024 / 1023 / 800 / 768 / 767 / 375
  - PASS
  - Commit `feat(ui): responsive breakpoints with iPad landscape clarity`

- [ ] **Task 15.5: DB isolation `index_dev.db` vs `index.db`(v1.2 加 per Issue 3)**
  - Write failing test `test_vault_path.py::test_dev_mode_uses_dev_db` — `RODIX_DEV=1` set → `vault_db_path()` returns `~/.../index_dev.db`;unset → `index.db`
  - Implement `vault_path.py::is_dev_mode()` + `vault_db_path()` 返回不同 path
  - All existing adapters automatically pick correct DB
  - PASS
  - Commit `feat(dev): isolate dev DB from production DB`

- [ ] **Task 16: Mock fixture loader endpoint(v1.1 加)**
  - Write failing test `test_cards_api.py::test_load_fixture_dev_mode_only` — POST `/api/dev/load-fixture?name=medium` in dev mode → loads `fixture_medium.json` cards into **`index_dev.db` only**;in production → 403
  - Implement endpoint guarded by `is_dev_mode()` check + writes only to dev DB(per Task 15.5)
  - Create 4 fixture JSON files in `app/shared/storage_py/fixtures/cards/` per spec(empty/few/medium/large)
  - Commit `feat(dev): card fixture loader endpoint with DB isolation`

- [ ] **Task 17: End-to-end manual test with fixtures**
  - In dev mode:
    - Load `fixture_empty` → verify cold start 0 empty state + Chat tab CTA
    - Load `fixture_few` → verify default-select first card,detail panel populated
    - Load `fixture_medium` → verify stats 空白态 + sticky headers + recall summary toggle
    - Load `fixture_large` → verify scroll + summary 大数字
  - Test recall summary(card with 5 recalls)→ summary mode + 展开
  - Export single + bulk
  - Delete card → list updates + dependents removed
  - Commit `chore(test): #3a end-to-end with 4 fixtures verified`

## Done criteria

- [ ] `#3a` Vault tab 35/65 master-detail full-bleed ✓
- [ ] 时间分组(今天/本周/本月/历史)+ 空 group skip ✓
- [ ] 选中态琥珀竖条 + metadata 行 ✓
- [ ] 完整 detail panel(标题 + recall 计数 + 4 字段 + 关联对话 + Recall summary)✓
- [ ] 4 级 cold start lifecycle 实现 ✓
- [ ] Recall summary 阈值 3 toggle ✓
- [ ] Markdown 导出(单卡 + 批量)✓
- [ ] 删除 with 二次确认 + cascade ✓

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位:plan 中 N/A(纯结构无 brand 字符串)
2. ✓ Desktop-first 35/65 + mobile collapse
3. ✓ §7.4 5 项 articulated
4. ✓ Pre-mortem 4 modes:全过(spec brainstorm 时已 5/5 ★)
5. ✓ 桌面横向 35/65
6. ✓ Mobile responsive 显式 task 15(v1.3:加 768-1023px iPad landscape 显式 breakpoint 表)
7. ✓ Empty state 4 级 lifecycle 显式 task 11

## Risk register

- **Mock fixtures drift from real `#claim-extraction` schema** → after `#claim-extraction` ships, fixture JSON shape (4 fields topic/concern/hope/question) may diverge from the actual claims table columns. **Mitigation**: Task 16 fixture schema mirrors what `#claim-extraction` plan v1.3 §"Files" §"Persistence" calls out (4 nullable TEXT columns + `message_id` foreign key). When `#claim-extraction` lands, run a one-shot fixture validator against the real schema and patch fixture JSONs. Tracked as a follow-up item, NOT a Wave 1b blocker.
- **Recall summary 阈值 3 wrong** → users see summary too eager (2 recalls collapses) or too late (10 recalls still inline). **Mitigation**: P1 ships at 3 (matches "数到 3 就 summarize" mental model); P2 telemetry-driven calibration via `#1b` recall threshold slider — already on roadmap.
- **Markdown export edge cases**:
  - Card body has triple-backticks → break frontmatter or fence. **Mitigation**: Task 6 escapes / wraps as needed; test_markdown_exporter has cases for nested fences.
  - Card body has YAML reserved chars in topic field → frontmatter parse breakage. **Mitigation**: quote topic always.
- **DB isolation drift** (Issue 3 root cause if mishandled) → Rodc dogfoods in `dev` mode forgetting to switch back, accidentally pollutes dev DB with real thinking. **Mitigation**: Task 15.5 makes `is_dev_mode()` explicit + visible top-bar banner ("DEV MODE · 用 mock data") so Rodc sees state at-a-glance. (Same pattern as `#1a` Settings panel DEV MODE banner.)
- **Mobile collapse master-detail UX feel** → 35/65 splits poorly at 768px (iPad portrait) — half-detail panel cramped. **Mitigation**: Task 15 collapses to single-column at < 768px so iPad portrait gets full-screen list / push-detail (same as phone). Desktop 35/65 only fires ≥ 1024px.
- **`/api/cards/export` long-running** for very large vaults (1000+) → request times out. **Mitigation**: P1 alpha vaults < 100 → not yet a concern. P2 markers note streaming export. Wave 4+ if a real user hits this. Add a comment in the endpoint referencing this debt.

## Post-launch follow-ups (P2)

- **Playwright upgrade for breakpoint smokes** (added 2026-05-02 per Rodc directive): when **INFRA 4** starts (after Wave 1b done + B-重 SaaS upgrade prep), upgrade the 6 regex-against-compiled-CSS assertions in Task 15 to real Playwright headless browser smokes at viewport sizes 1440 / 1024 / 1023 / 800 / 768 / 767 / 375. The regex smokes confirm CSS rules are *present and well-formed*; Playwright would confirm rules *render correctly across browsers*. Track with the rest of the test infra investments at INFRA 4.

## References

- Scenarios: S-VAULT-1, S-VAULT-2, S-VAULT-3, S-VAULT-4, S-VAULT-5, S-MOBILE-1, S-MOBILE-2 (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`)
- Spec: `web-product-design.md` §5.6
- Brainstorm: 屏 18 `#3a` redo desktop v2
- IA-C cascade: 卡片管理移到 Vault tab 主区,drawer 不再装
- P2 markers:1 次 recall 措辞 / 导出 brand 叙事(post-launch implement)
