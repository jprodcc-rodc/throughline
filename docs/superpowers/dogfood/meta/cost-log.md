# Dogfood Cost Log

## Phase B sample-verify — 2026-05-03

Real Haiku 4.5 (`anthropic/claude-haiku-4.5`) via OpenRouter + production extractor. 5 chat calls + 5 extraction calls.

### Per-round chat (Haiku 4.5)

| Round | Prompt tokens | Completion tokens | Cost (USD) | Elapsed (s) |
|---|---|---|---|---|
| sarah-08 | 1,171 | 201 | $0.002176 | 3.85 |
| emma-08 | 1,182 | 340 | $0.002882 | 5.19 |
| mike-08 | 1,194 | 451 | $0.003449 | 6.73 |
| mike-01 | 957 | 212 | $0.002017 | 4.11 |
| daniel-06 | 1,238 | 265 | $0.002563 | 4.54 |
| **Chat subtotal** | **5,742** | **1,469** | **$0.013087** | 24.42 |

### Per-round extraction (Haiku 4.5 via OpenRouter through production extractor)

Cost not separately tracked by the extractor wrapper. Estimating from token usage parity (same model, same provider, similar input shape):

- Each extraction call: ~system_prompt(claim_extractor.md ≈ 1,400 tokens) + user_payload(user_msg + ai_reply ≈ 200-1500 tokens) → completion(~50-100 tokens for the JSON object).
- Estimated per-call cost: ~$0.0015-0.0025
- 5 extraction calls × ~$0.002 avg = **~$0.010** estimated

### Total Phase B spend

| Component | Cost |
|---|---|
| Chat (measured) | $0.013087 |
| Extraction (estimated) | ~$0.010 |
| **Phase B total** | **~$0.023** |

Well under the $0.50-1.50 budget allocated by the task brief.

### Notes

- All requests routed via OpenRouter (`anthropic/claude-haiku-4.5` slug). `provider` field returned `openrouter` from `resolve_endpoint_and_key()`.
- 0 retries; 0 timeouts; 0 HTTP errors across 5 rounds.
- Average chat latency 4.9s (range 3.9-6.7s). Extraction adds ~3-5s on top per round.
- Total wall-clock: ~50 seconds for the API calls; total Phase B execution including verification doc composition ~25-30 minutes.

### Raw outputs

Raw JSON outputs of all 5 rounds preserved at `docs/superpowers/dogfood/sample-verify/_raw/{round}.json` — chat content, usage tokens, elapsed, and extraction fields/raw all captured.
