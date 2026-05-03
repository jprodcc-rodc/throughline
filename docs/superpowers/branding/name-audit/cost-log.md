# Cost Log · Naming Audit

**Total monetary cost: ~$0** (no paid APIs; all queries via free WebSearch + bash curl)

---

## Web/API resources used

| Tool | Calls | Purpose | Monetary cost |
|---|---|---|---|
| `bash curl` to `rdap.org` (Google Registry redirect for .app) | 76 | Gate 1 .app TLD availability check | $0 (free RDAP service) |
| `bash curl` to `rdap.verisign.com` (Verisign for .com) | 76 | Gate 1 .com TLD availability check | $0 (free RDAP service) |
| `bash curl` retry batch | 4 | UNCLEAR HTTP 000 retries on slow RDAP calls | $0 |
| `WebSearch` Apple/Play Store collision (Gate 2) | 14 | Gate 2 App Store collision check on Gate-1 survivors | bundled in CC subscription |
| `WebSearch` software/SaaS web-crowded (Gate 3) | 13 | Gate 3 web-crowded check | bundled |
| `WebSearch` trademark EUIPO/USPTO/IP Australia (Gate 4) | 14 | Gate 4 TM rough check | bundled |
| `WebSearch` Rodex / RØDE X audio brand specific | 1 | Gate 4 special TM check (rule-3 RØDE conflict verification) | bundled |
| `WebFetch` rodix.app validation test | 3 | Pre-Gate-1 RDAP endpoint validation | bundled |
| `WebSearch` literal-phrase "rod span" / "rod keep" / "rod weave" / "rod root" (Gap 1 stress test) | 6 | Stress-test Gap 1 — literal-phrase technical-term collision | bundled |

**Total WebSearch calls: ~48**
**Total bash curl calls: ~156**
**Total WebFetch calls: 3**

---

## Notes on bash sandbox DNS finding

Initial Gate 1 attempt used `bash nslookup` for batch DNS resolution. The sandbox's `nslookup` returned RFC 2544 benchmarking-range addresses (198.18.x.x sequentially) for all queries — DNS interception, not real lookups. Confirmed by curl-over-HTTPS returning real RDAP data.

**Lesson:** For domain availability in CC sandbox, curl-over-RDAP works; bash `nslookup` does not. Documented in `02-gate-results.md` for future audit reuse.

---

## Cost compared to spec budget

Task spec §0 estimate: **$2-5** for web fetches + light LLM judge use.

Actual: **~$0**.

Under-budget reason: RDAP servers (Google Registry for .app via rdap.org / Verisign for .com) provide free domain availability lookups at scale. The spec assumed paid WHOIS APIs (Namecheap / Porkbun / GoDaddy lookups have per-call costs at high volume) but RDAP (the modern WHOIS replacement) is free at the registry level and worked cleanly via curl in CC's sandbox.

If the audit ran with paid APIs (Domainr / WhoisXML), cost would have been ~$1-3 for 228 domain lookups. Free RDAP made this $0.

If lawyer-grade TM clearance is run as next step (§10 in memo), $50-200 budget for spot-consult. Not part of this audit's cost.
