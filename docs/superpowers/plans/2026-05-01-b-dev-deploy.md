# `#b-dev-deploy` — Implementation Plan(v1.2 简化版 per Rodc directive)

> **For agentic workers:** Use `superpowers:test-driven-development` per task.

**Goal:** 局域网 dev 部署,让 Rodc 在桌面 dev,iPad / 家人 PC 实时访问 review 进展。**最简方案**(per Rodc v1.2 Issue 2 directive):FastAPI bind `0.0.0.0:8000` + 启动打印 LAN URL + 防火墙文档。**HTTP only**,不 HTTPS / mkcert / Tailscale / hosts / mDNS。

**Architecture:** uvicorn `--host 0.0.0.0` + Python `socket` lib 枚举非 loopback IPv4 + console 打印 + Win/macOS firewall 放行文档。

**Tech Stack:** Python `socket` standard lib(已在 `app/web/__main__.py` 用过)+ FastAPI uvicorn 已支持 0.0.0.0 binding

**Rodc directive 严格遵守**:
- ❌ NOT mkcert / 不做任何 self-signed cert
- ❌ NOT Tailscale / 不做 VPN
- ❌ NOT hosts 文件 / mDNS / rodix.local 域名
- ❌ NOT HTTPS

**Trade-off accepted**:
- Browser Notifications API 在 HTTP 不可用(secure context required)→ dev/家人 review 不需要,production `#b-deploy` 真 TLS 后自然恢复
- Clipboard API 部分受限 → 同上

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | Console 输出例:`[PRODUCT_NAME] dev server: http://192.168.1.42:8000 (LAN) / http://127.0.0.1:8000 (local)`. iPad 浏览器输 http://192.168.1.42:8000 直接访问。 |
| 产品策略假设 | Rodc sustainability + 家人 review onboarding 需要内网访问。最简方案胜过完整方案 — dev 阶段不需要 secure context 功能。 |
| 适合 / 不适合 | **适合**: dev 阶段 + 内网 review。**不适合**: production deploy(production = `#b-deploy` Wave 3,真 TLS)。 |
| Trade-off | + 极简(3 tasks 不是 10)+ 无 cert 信任问题 / − Notifications API 不可用 dev / 局域网 plain HTTP 在不信任网络下 unsafe(但内网 OK) |
| 最大风险 | 防火墙没放行 → iPad 连不上 → 看着像产品 bug。**缓解**:文档第一段就教 firewall step,加 Rodc 桌面端 manual verification("从 iPad 访问成功"是 done 标准)。 |

## Ambiguity flag

✓ **无 ambiguity**(Rodc directive 严格 spec)。

## Files

**Modify**:
- `app/web/__main__.py` — 启动时打印 LAN IPv4 URL(已有 `_lan_ipv4()` helper,扩展为枚举所有非 loopback 接口)

**Create**:
- `docs/DEV_LAN_ACCESS.md` — Windows + macOS firewall 放行步骤 + iPad/家人 PC 访问指南

**Test**: `app/web/test_lan_url_print.py`(unit test for IP enumeration logic)

## Bite-sized TDD tasks(简化版 · 3 tasks)

- [ ] **Task 1: Enumerate non-loopback IPv4 interfaces**
  - Write failing test `test_lan_url_print.py::test_enumerate_returns_lan_ips` — function `enumerate_lan_ipv4()` returns list of non-127.* / non-0.0.0.0 IPv4 addresses
  - Implement using Python `socket` standard lib(no extra deps):
    ```python
    import socket
    
    def enumerate_lan_ipv4() -> list[str]:
        """Return non-loopback IPv4 addresses on this machine."""
        ips = []
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                ip = info[4][0]
                if not ip.startswith("127.") and ip != "0.0.0.0":
                    ips.append(ip)
        except socket.gaierror:
            pass
        # Fallback: existing _lan_ipv4 trick
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            fallback = s.getsockname()[0]
            s.close()
            if fallback not in ips and not fallback.startswith("127."):
                ips.append(fallback)
        except OSError:
            pass
        return list(dict.fromkeys(ips))  # dedupe preserving order
    ```
  - PASS
  - Commit `feat(dev): enumerate non-loopback IPv4 interfaces`

- [ ] **Task 2: Print LAN URLs at server startup**
  - Modify `app/web/__main__.py` `_print_banner` to print all enumerated LAN URLs:
    ```
    [PRODUCT_NAME] dev server:
       http://192.168.1.42:8000  (LAN)
       http://10.0.0.5:8000      (LAN)
       http://127.0.0.1:8000     (local)
    
    To access from iPad / 家人 PC on same WiFi: open one of the LAN URLs above.
    First time? See docs/DEV_LAN_ACCESS.md for firewall setup.
    ```
  - Use `enumerate_lan_ipv4()` from Task 1
  - Manual test:`python -m app.web` → console output verified
  - Commit `feat(dev): print LAN URLs at server startup`

- [ ] **Task 3: Document firewall + iPad/家人 PC access**
  - Create `docs/DEV_LAN_ACCESS.md`:
    
    ```markdown
    # [PRODUCT_NAME] Dev LAN Access
    
    ## What this enables
    
    Run dev server on your desktop, access from iPad / family PC / phone on same WiFi.
    
    ## Step 1: Allow port 8000 through firewall
    
    ### Windows
    
    1. Open `Windows Defender Firewall with Advanced Security` (Win+S → search)
    2. Inbound Rules → New Rule
    3. Rule Type: **Port**
    4. Protocol: **TCP**, Specific local ports: **8000**
    5. Action: **Allow the connection**
    6. Profile: **Private** only (NOT Public)
    7. Name: `[PRODUCT_NAME] dev HTTP`
    
    ### macOS
    
    1. System Settings → Network → Firewall
    2. Click Options
    3. Add Python.app (or python binary) → Allow incoming connections
    4. Or: `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/python3`
    
    ## Step 2: Run server
    
    ```bash
    python -m app.web
    ```
    
    Console will print LAN URLs like `http://192.168.1.42:8000`.
    
    ## Step 3: Access from another device(same WiFi)
    
    Open the LAN URL in any browser:
    
    - iPad: Safari → type `http://192.168.1.42:8000`
    - 家人 PC: Chrome → 同上
    - Phone: 同上
    
    No cert warning(因为是 HTTP not HTTPS).
    
    ## Limitations
    
    - **Browser Notifications API** 在 HTTP 不可用(需 secure context)
    - **Clipboard API** 受限
    - 这些功能在 production deploy(`#b-deploy` 真 TLS)后自然恢复
    
    ## Troubleshooting
    
    - **iPad shows "Cannot connect"**: Firewall not allowing port 8000. Re-check Step 1.
    - **iPad on different WiFi**: must be same network as desktop.
    - **Multiple LAN IPs printed**: try each. Pick the one that works for your iPad's network segment.
    ```
  - Commit `docs(dev): LAN access setup guide`

## Done criteria

- [ ] FastAPI bind `0.0.0.0:8000`(已 default per `app/web/__main__.py`)✓
- [ ] 启动打印所有非 loopback LAN IPv4 URLs ✓
- [ ] Windows + macOS firewall 放行文档 ✓
- [ ] iPad / 家人 PC 访问步骤文档 ✓
- [ ] **iPad / 家人 PC 实测访问 http://192.168.x.x:8000 成功**(soak gate condition)✓

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位:plan + 文档全用占位
2. ✓ Desktop-first / cross-device dev infra
3. ✓ §7.4 5 项 articulated
4. ✓ Pre-mortem 4 modes:like-me ✓ / metric vs goal ✓ / reactive vs strategic ✓ / edge vs main(LAN dev 是 main path)
5. ✓ 桌面横向利用率:N/A
6. ✓ Mobile responsive:N/A(本身是 enabler)
7. ✓ Empty state:N/A

## References

- Scenarios: S-MOBILE-1 (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`) — iPad LAN access is the user-journey gate.
- Roadmap v1.2 §1.2 (#b-dev-deploy 简化版)
- Protocol v1.6 §5.2
- Rodc Issue 2 directive(2026-05-01)
- Trade-off note: Notifications API 等 secure-context 功能 dev 不可用,production `#b-deploy` 真 TLS 后恢复
