# [PRODUCT_NAME] Dev LAN Access

## What this enables

Run dev server on your desktop, access from iPad / family PC / phone on same WiFi. HTTP only(no TLS in dev). For production deployment with TLS see `#b-deploy`.

## Step 1: Allow port 8765 through firewall

### Windows

1. Open `Windows Defender Firewall with Advanced Security` (Win+S → search)
2. Inbound Rules → New Rule
3. Rule Type: **Port**
4. Protocol: **TCP**, Specific local ports: **8765**
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

Console will print all LAN URLs like `http://192.168.1.42:8765`.

## Step 3: Access from another device(same WiFi)

Open the LAN URL in any browser:

- iPad: Safari → type `http://192.168.1.42:8765`
- 家人 PC: Chrome → 同上
- Phone: 同上

No cert warning(因为是 HTTP not HTTPS).

## Limitations

- **Browser Notifications API** 在 HTTP 不可用(需 secure context)
- **Clipboard API** 受限
- 这些功能在 production deploy(`#b-deploy` 真 TLS)后自然恢复

## Troubleshooting

- **iPad shows "Cannot connect"**: Firewall not allowing port 8765. Re-check Step 1.
- **iPad on different WiFi**: must be same network as desktop.
- **Multiple LAN IPs printed**: try each. Pick the one that works for your iPad's network segment.
- **Port 8765 already in use**: another instance running. Find it via `netstat -ano | findstr :8765` (Windows) and kill it, or pass `--port 8800` flag to use a different port.
