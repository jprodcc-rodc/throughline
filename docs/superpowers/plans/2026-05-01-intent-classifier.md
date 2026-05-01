# `#intent-classifier` — Implementation Plan

> **Status (2026-05-01):** v1.3 — Rodc + 外部 Opus reviewed, 4 push backs incorporated, **approved for implementer dispatch** per protocol §5.5.
> **For agentic workers:** Use `superpowers:test-driven-development` per task. Then `superpowers:subagent-driven-development` extended with `docs/superpowers/skills/scenario-verification.md`.
> **App/ gitignored** — `app/shared/intent/` + `app/web/*` modifications do NOT go to git. Skip the per-task `Commit ...` lines for those files; they're disk-only. Files under `fixtures/` (eval artifacts) DO commit.

**Goal:** LLM-based 3-class user-message classifier(chitchat / thoughtful / factual)backing the **full C-4 ruleset** (C-4.1 through C-4.6) in `docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md` v1.3. Replaces the Wave 1a string-match heuristic in `#8` (anti-pattern per C-4.6). Hard prerequisite for `#claim-extraction` (extraction must only fire on `thoughtful` or low-confidence fallback) and the real `#8`.

**Architecture:** New `app/shared/intent/` module exposing a single `classify(user_message) -> ClassifierResult`. **Internal Python helper only — no standalone HTTP endpoint** (per v1.3 push back 1, YAGNI: independent eval calls `classify()` directly, frontend draft-time hint isn't in spec, future bulk pre-classification adds wrapper if/when that demand materializes).

Single integration surface for v1.3:

- **Pre-route step inside `/api/chat`** (server-side, invisible to clients) — gates the placeholder Card AND the future real `#claim-extraction` trigger.

Boundary short-circuits run BEFORE any LLM call: `< 5 chars` → chitchat, `> 200 chars` → thoughtful.

**Tech Stack:** Python · OpenRouter compat HTTP path (reuses `requests` + `_resolve_llm_config`) · existing eval harness shape from `fixtures/v0_2_0/eval/` · pydantic for structured response

---

## §7.4 5 项 framing

| | |
|---|---|
| Visual | Backend feature — invisible. Visible signal: chitchat / factual messages no longer trigger empty Card; thoughtful messages still do. AI 行为 (follow-up vs direct) remains owned by system prompt; classifier only owns the Card + future extraction gate. |
| 产品策略假设 | "AI chat with memory" framing depends on the Card being a *meaningful* save, not a noisy auto-trigger on every reply. Without the classifier, every `"嗯"` produces a Card → Vault grows with junk → trust collapses. v1.1 scenarios explicitly forbid string-match patches (C-4.6 anti-pattern). |
| 适合 / 不适合 | **适合**:全部用户 — this is the runtime gate every chat turn passes through. **不适合**:N/A. |
| Trade-off | + clean trigger discipline + alignment with v1.1 C-4 + foundation for `#claim-extraction` and recall quality / − extra LLM call per turn (~100-300ms latency, ~$0.0001 production) / − classifier failure cascades to "always trigger" (acceptable per fallback bias) |
| 最大风险 | Classifier accuracy < 85% on 60-sample eval → too many chitchat→Card or thoughtful→no-Card → product feels dumb either way.**缓解**:eval gate before merge; failure raises to Rodc for (a) paid model / (b) prompt revision / (c) accept + telemetry; bias direction (low confidence → thoughtful) makes false-positives noisier than false-negatives, which is the right asymmetry. |

## Ambiguity flag

✓ **无 ambiguity** — Rodc v1.1 已前置决策。

Locked decisions:
- Class set: `{chitchat, thoughtful, factual}` (closed enum, no "other")
- Confidence threshold: 0.8 (per C-4.2)
- Fallback bias: `thoughtful` for low-confidence + timeout + error (per C-4.2 关键设计)
- Boundary opts: `< 5 chars` skip-classify chitchat, `> 200 chars` skip-classify thoughtful (per C-4.3)
- Dev model: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (per C-4.4 + memory model lock)
- **Production model: TBD Wave 3** — decision deferred per v1.3 push back 4 (no dogfood traffic data yet to inform the choice). Wave 3 deployment will pick based on telemetry. NOT a blocker for Wave 1b.
- **Asymmetric accuracy gate** on 100-sample eval (per v1.3 push back 3 — error-cost asymmetry: missing thoughtful = product dumb / mis-routing chitchat to thoughtful = harmless given fallback bias):
  - **Overall accuracy ≥ 85%**
  - **`thoughtful` recall ≥ 90%** — never miss a thoughtful (core value protection)
  - **`chitchat` precision ≥ 75%** — may over-route chitchat to thoughtful (acceptable per fallback design)
  - **`factual` recall ≥ 85%**
- Eval set: **100 samples** (35 chitchat / 40 thoughtful / 25 factual) per v1.3 push back 2 — 60 was too noisy for an 85% gate

## Files

**Create**:
- `app/shared/intent/__init__.py` — public `classify`, `ClassifierResult`, `IntentClass` exports
- `app/shared/intent/classifier.py` — main classify() implementation with boundary opts + LLM call + structured parse
- `app/shared/intent/prompts/intent_classifier.md` — locked classifier prompt (loaded at module import, same pattern as `app/web/prompts/rodix_system.md`)
- `app/shared/intent/test_classifier.py` — unit tests (boundary opts, parse, fallback, timeout)
- `app/shared/intent/test_classifier_integration.py` — integration test against eval set (skipped under -m unit)

**Modify**:
- `app/web/server.py` — `chat()` calls `classify(last_user_msg)` before placeholder gate. Result feeds (a) `_should_show_placeholder` replacement (b) Wave 1b real `#8` real claim extraction trigger (c) optional log/telemetry
- `app/web/server.py` — strip `_PLACEHOLDER_BANNED_PHRASES` and `_PLACEHOLDER_USER_MIN_LEN`; replace with classifier-based gate. (Wave 1a bleed-stop heuristic retired per C-4.6.)
- `app/web/test_chat_placeholder.py` — update tests to use classifier result, drop banned-phrase tests
- `app/web/test_settings.py` is unaffected (no overlap)

**No public HTTP endpoint** for the classifier in v1.3 (per push back 1). `classify()` is a Python function imported by `server.chat()`. Independent eval calls the function directly, no HTTP round-trip.

**New eval artifacts**:
- `fixtures/v0_2_0/eval/intent_cases.json` — 60 samples (20 chitchat / 25 thoughtful / 15 factual) with `expected_class` + `notes`
- `fixtures/v0_2_0/eval/intent_prompt.txt` — frozen prompt copy for reproducible eval
- `fixtures/v0_2_0/eval/run_intent_eval.py` — eval runner (mirrors `run_claim_extraction_eval.py`)
- `fixtures/v0_2_0/eval/results-intent-<model>-<timestamp>.json` — produced by runner

## Bite-sized TDD tasks

- [ ] **Task 1: ClassifierResult + IntentClass types**
  - Write failing test `test_classifier.py::test_intent_class_enum_closed` — `IntentClass` is `{CHITCHAT, THOUGHTFUL, FACTUAL}` (StrEnum), no `OTHER` value
  - Write failing test `test_classifier.py::test_classifier_result_shape` — `ClassifierResult(intent=..., confidence=0.0..1.0, source: 'short_circuit'|'llm'|'fallback', raw=Optional[str])`
  - Implement using `enum.StrEnum` + dataclass
  - PASS
  - Commit `feat(intent): ClassifierResult + IntentClass types`

- [ ] **Task 2: Boundary short-circuit — < 5 chars → chitchat**
  - Write failing test `test_classifier.py::test_short_user_msg_short_circuits_chitchat` — `classify("嗯")`, `classify("hi")`, `classify("")` all return `intent=CHITCHAT, confidence=1.0, source='short_circuit'`
  - Threshold: `len(msg.strip()) < 5`
  - Implement guard at top of `classify()` — returns before any LLM call
  - PASS
  - Commit `feat(intent): boundary short-circuit for short messages`

- [ ] **Task 3: Boundary short-circuit — > 200 chars → thoughtful**
  - Write failing test `test_classifier.py::test_long_user_msg_short_circuits_thoughtful` — `classify("a" * 201)` returns `intent=THOUGHTFUL, confidence=1.0, source='short_circuit'`
  - Threshold: `len(msg.strip()) > 200`
  - Implement second guard
  - PASS
  - Commit `feat(intent): boundary short-circuit for long messages`

- [ ] **Task 4: Locked classifier prompt + module-load**
  - Write failing test `test_classifier.py::test_prompt_loads_from_file` — module-level `_INTENT_PROMPT` is loaded from `app/shared/intent/prompts/intent_classifier.md` at import; non-empty; mentions all 3 classes
  - Create the prompt file with locked content (see "Prompt content" section below)
  - Implement `_load_intent_prompt()` mirroring `app/web/server._load_rodix_system_prompt()` pattern (with inline fallback)
  - PASS
  - Commit `feat(intent): locked classifier prompt`

- [ ] **Task 5: LLM call — happy path parse**
  - Write failing test `test_classifier.py::test_llm_call_returns_structured_result` — mock `requests.post` to return `'{"intent": "thoughtful", "confidence": 0.92, "rationale": "..."}'` content; `classify("我在考虑换工作要不要换")` returns `intent=THOUGHTFUL, confidence=0.92, source='llm'`
  - Implement `classify()` for 5 ≤ len ≤ 200: build messages [system=intent_prompt, user=msg], POST to `_resolve_llm_config()` URL, parse JSON content (defensive — model may emit prose around JSON, scan for first `{...}` block per `run_claim_extraction_eval.py` lessons-learned)
  - **Defensive parsing**: do NOT use `response_format: json_object` (per nvidia model finding from prior eval — triggers Chinese output mode breakage)
  - max_tokens 3000 (per nvidia reasoning model min)
  - PASS
  - Commit `feat(intent): LLM call + structured parse`

- [ ] **Task 6: Confidence threshold gate → fallback to thoughtful**
  - Write failing test `test_classifier.py::test_low_confidence_falls_back_to_thoughtful` — mock LLM to return `'{"intent": "chitchat", "confidence": 0.6}'`; result is `intent=THOUGHTFUL, confidence=0.6, source='fallback'` (we keep the LLM's confidence number for telemetry but override the class)
  - Threshold: `confidence < 0.8` → override class to `THOUGHTFUL`, set source to `'fallback'`
  - PASS
  - Commit `feat(intent): low-confidence fallback to thoughtful`

- [ ] **Task 7: Timeout → fallback to thoughtful + log alert**
  - Write failing test `test_classifier.py::test_timeout_falls_back_to_thoughtful` — mock `requests.post` to raise `requests.Timeout`; `classify("...")` returns `intent=THOUGHTFUL, confidence=0.0, source='fallback'`; assert a log/alert was emitted (use `caplog` to verify a WARNING with `intent_classifier_timeout` code)
  - Implement try/except `requests.RequestException` → log + return fallback
  - Timeout: 5s (classifier should be fast; if not, fall back)
  - PASS
  - Commit `feat(intent): timeout fallback + log alert`

- [ ] **Task 8: Malformed JSON → fallback + log**
  - Write failing test `test_classifier.py::test_malformed_response_falls_back` — mock LLM to return `"not json at all"`; result is `intent=THOUGHTFUL, source='fallback'`; log emitted
  - Implement: scan for JSON block; if absent OR `intent` not in `IntentClass` enum OR `confidence` not in [0, 1] → fallback + log
  - PASS
  - Commit `feat(intent): malformed-response fallback`

- [ ] **Task 9: 100-sample eval set + runner** (per v1.3 push back 2 — 60 was statistically too noisy for an 85% gate)
  - Create `fixtures/v0_2_0/eval/intent_cases.json` with **100 samples**:
    - **35 chitchat**:greetings / acks / weather / time-of-day / single-emoji + the boundary fans listed below
    - **40 thoughtful**:life decisions / aspirations / regrets / anxieties / abstract reflection + the boundary fans listed below
    - **25 factual**:technical / encyclopedic / how-to / definition lookups + the ambiguous fan listed below
  - **Boundary case quotas (must be present, not in addition — count toward their class total)**:
    - Short thoughtful (< 10 chars): **5-7** in the 40 thoughtful (e.g., `"我想做宇航员"`, `"该走了吗"`)
    - Long chitchat (> 30 chars): **5-7** in the 35 chitchat (rambling-but-empty greetings / non-substantive small talk)
    - Ambiguous factual (situational fact-questions where intent is genuinely close to thoughtful): **5** in the 25 factual (e.g., `"换工作时合同里 365 days notice 是什么意思"` — factual on its face but contextually thoughtful)
    - Multi-language mix: **5** spread across classes (英文 / 拼音 / 简单方言 — `"咋整"` / `"how 应该面对这个"` / etc.)
    - Emoji-containing chitchat: **3-5** in the 35 chitchat (`"😊 在吗"`, `"good 👍"`)
  - Each sample: `{"id", "message", "expected_class", "category", "notes"}` — `category` is the boundary tag (`short_thoughtful` / `long_chitchat` / `ambiguous_factual` / `multilingual` / `emoji_chitchat` / `core` for non-boundary)
  - Manual annotation: 30-60 minutes one-time cost, permanently reusable
  - Create `fixtures/v0_2_0/eval/intent_prompt.txt` — frozen copy of the prompt (so eval is reproducible if prompt evolves)
  - Create `fixtures/v0_2_0/eval/run_intent_eval.py` — runner: loads cases, calls `classify()`, computes per-class accuracy + overall + confusion matrix + **per-boundary-category accuracy** (so we see if the classifier flunks specifically on, say, short_thoughtful) + writes `results-intent-<model>-<ts>.json`
  - Manual run on `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`
  - Commit `eval(intent): 100-sample classifier eval set + runner` (fixtures/ IS tracked, this commit goes to git)

- [ ] **Task 10: Asymmetric accuracy gate enforcement** (per v1.3 push back 3 — error-cost is asymmetric: missing thoughtful = product fails / mis-routing chitchat is cheap given fallback)
  - Write failing test `test_classifier_integration.py::test_eval_meets_asymmetric_gate` (skipped under unit run; runs under `pytest -m integration`):
    - Loads `intent_cases.json` (100 samples per Task 9)
    - Calls `classify()` on each (real LLM call, dev model)
    - Computes confusion matrix → derives:
      - overall accuracy
      - per-class precision + recall
    - **Assertions** (all four must hold):
      - `overall_accuracy >= 0.85`
      - `recall(thoughtful) >= 0.90`  ← the protect-against-product-dumb gate
      - `precision(chitchat) >= 0.75`  ← lets us over-route chitchat to thoughtful as bias
      - `recall(factual) >= 0.85`
    - On any assertion FAIL: print the full confusion matrix + per-boundary-category breakdown so the failure is debuggable
  - **If FAIL on first run**: do NOT block — record results, raise to Rodc with the 4 options listed in §"Risk register" of this plan
  - PASS once all four assertions hold (or once Rodc explicitly accepts a temporary lower threshold + telemetry plan)
  - Commit `eval(intent): integration test enforces asymmetric 90/85/75/85 accuracy gate`

- [ ] **Task 11: Wire into /api/chat**
  - Modify `app/web/server.py`:
    - Import `classify` + `IntentClass` from `app.shared.intent`
    - In `chat()`, call `classify(last_user_message)` after auth/config checks, before LLM call
    - Replace `_should_show_placeholder()` body with: `result.intent == IntentClass.THOUGHTFUL` (covers low-confidence fallback path automatically since fallback overrides class to thoughtful)
    - Delete `_PLACEHOLDER_BANNED_PHRASES` + `_PLACEHOLDER_USER_MIN_LEN` constants
    - Optionally log `intent_classification` event with `result.dict()` for telemetry
  - Update `app/web/test_chat_placeholder.py`:
    - Drop `test_placeholder_hidden_for_empty_companionship_reply` (anti-pattern per v1.1 C-4.6 — system prompt failure handled separately)
    - Update `test_placeholder_hidden_for_short_user_message` to mock classifier returning chitchat instead of relying on the deleted heuristic
    - Add `test_placeholder_hidden_for_classifier_chitchat` — explicit happy-path (mock classifier → chitchat → null placeholder)
    - Add `test_placeholder_shown_for_classifier_thoughtful` — mock classifier → thoughtful → placeholder dict
    - Add `test_placeholder_shown_for_classifier_low_confidence` — mock classifier → low-conf chitchat → fallback overrides → placeholder dict (verifies fallback bias)
  - Run full test suite — should still pass (471 pre-existing + new classifier tests + updated placeholder tests)
  - Commit `feat(chat): wire intent classifier into /api/chat (replaces ABC bleed-stop)`

**Tasks 12 & 13 deleted in v1.3** — push back 1 (no standalone endpoint, YAGNI) and push back 4 (production model deferred to Wave 3, no env-var seam needed in Wave 1b). Plan is 11 tasks total.

## Done criteria

- [ ] `IntentClass` enum + `ClassifierResult` types ✓
- [ ] Boundary short-circuits (< 5 chars chitchat / > 200 chars thoughtful) ✓
- [ ] LLM call with defensive JSON parsing + max_tokens 3000 ✓
- [ ] Confidence < 0.8 → fallback override to thoughtful ✓
- [ ] Timeout / network error → fallback + log ✓
- [ ] Malformed JSON → fallback + log ✓
- [ ] **100-sample eval set** + runner committed ✓ (with boundary-category quotas met)
- [ ] **Asymmetric accuracy gate**: overall ≥ 85% · `thoughtful` recall ≥ 90% · `chitchat` precision ≥ 75% · `factual` recall ≥ 85% — all four hold OR Rodc-signed-off temporary threshold ✓
- [ ] Wired into /api/chat replacing ABC bleed-stop heuristic ✓
- [ ] Tests green: full app suite + new unit tests + integration eval test ✓
- [ ] **Scenario verification**: S-CHAT-1 (thoughtful + Card triggers via classifier), S-CHAT-2 (chitchat → no Card via classifier), S-CHAT-3 (factual → no Card via classifier), S-CHAT-4 (all 5 cases including boundaries 4a/4b/4c/4d/4e), S-CHAT-6 (multi-round depth pivot — classifier emits same class on each turn but system prompt v1.3 owns the per-round behavior; verify the integration doesn't break round 3+ pivot), S-CARD-1 (Vault badge animation when classifier returns thoughtful), S-CARD-2 (system prompt failure ≠ trigger gate — confirm classifier-based routing does NOT gate on AI reply phrases, restoring v1.1 C-4.6 alignment), S-CARD-3 (Active Recall trigger — classifier output flows through to recall scoring, deferred to Wave 2 `#active-recall-base` but gated here that the output is consumable) PASS ✓

## Prompt content (for Task 4)

The locked classifier prompt at `app/shared/intent/prompts/intent_classifier.md`:

```markdown
You classify a single user message into one of three intent classes:

- **chitchat** — greetings, acknowledgements, small talk, weather/time questions, single-character responses, content with no specific thought to engage with.
- **thoughtful** — the message contains a specific concern, hope, decision, reflection, aspiration, or struggle. The user wants to think with someone, not just chat. Length is not the signal; substance is. "我想做宇航员" is short but thoughtful. A rambling 30-字 greeting is long but chitchat.
- **factual** — the user is asking for objective information: technical questions, definitions, how-to lookups, encyclopedic queries. They want a direct answer, not a thinking partner.

Respond with valid JSON ONLY (no prose around it):

```
{"intent": "chitchat" | "thoughtful" | "factual", "confidence": 0.0-1.0, "rationale": "<one sentence>"}
```

Confidence calibration:
- 0.9+ when the class is unambiguous
- 0.7-0.9 when one alternative is plausible but the chosen class is clearly the best fit
- 0.5-0.7 when two classes feel close — be honest, the system handles this with a fallback rule
- < 0.5 only if the message is genuinely incoherent

Do NOT explain. Do NOT add prose before or after the JSON. Output JSON, period.
```

## §7.5 7 项

1. ✓ `[PRODUCT_NAME]` 占位:N/A(纯 backend,无 user-visible 字符串)
2. ✓ Desktop-first / cross-device:N/A(backend)
3. ✓ §7.4 5 项 articulated above
4. ✓ Pre-mortem 4 modes considered:like-me ✓ / metric vs goal (accuracy gate ≠ goal — goal is sane Card discipline) ✓ / reactive vs strategic (foundational, not patch) ✓ / edge vs main (boundary cases 4a-4e are the main path, not edges) ✓
5. ✓ 桌面横向利用率:N/A
6. ✓ Mobile responsive:N/A
7. ✓ Empty state:N/A(every chat turn classifies, no empty)

## Risk register

- **Free model fails the asymmetric gate** (any of: overall < 85% / `thoughtful` recall < 90% / `chitchat` precision < 75% / `factual` recall < 85%) → raise to Rodc with the 4 options:
  - (a) switch to paid dev model (Haiku 4.5 / Gemini 2.5 Flash) just for classifier
  - (b) revise classifier prompt + re-run eval
  - (c) accept temporary lower threshold + telemetry-driven calibration in Wave 2
  - (d) split-route: chat keeps free model, classifier uses paid (cost-isolated)
- **Free model rate-limit at LAN scale** → fallback path keeps product functional but Card discipline degrades to "always thoughtful". Acceptable for short windows; persistent → Rodc moves to paid model
- **Free model deprecated** → catch in `_resolve_llm_config()` provider; surface clearly in logs; Rodc swaps env var
- **Latency > 1s p95 on dev model** → degrades chat feel; raise to Rodc for paid model evaluation; do NOT add caching here (Wave 2+ if needed)
- **Production model selection deferred to Wave 3** — no telemetry yet; pick the model when dogfood data exists. Plan does not pre-commit Haiku 4.5 vs Gemini 2.5 Flash vs other.

## References

- Scenarios: S-CHAT-1, S-CHAT-2, S-CHAT-3, S-CHAT-4 (all 5 cases), S-CHAT-6 (multi-round protocol — system-prompt-side concern but classifier output feeds C-2.2 routing), S-CARD-1, S-CARD-2, S-CARD-3 (`docs/superpowers/specs/2026-05-01-rodix-product-test-scenarios.md`)
- Spec: scenarios spec §C-4 全条款 (C-4.1 核心原则 / C-4.2 路由规则 / C-4.3 边界优化 / C-4.4 model 选择 / C-4.5 accuracy gate / C-4.6 AI response 检验独立维度 — all six implemented or addressed)
- Roadmap: Wave 1b, between `#1a` / `#w-docs` and `#claim-extraction` (this plan unblocks `#claim-extraction`)
- Prior art: `fixtures/v0_2_0/eval/run_claim_extraction_eval.py` (eval pattern + nvidia model lessons-learned: max_tokens ≥ 3000, no `response_format: json_object`)
- v1.1 anti-pattern resolved: this plan replaces the Wave 1a string-match `_PLACEHOLDER_BANNED_PHRASES` heuristic in `app/web/server.py` (which violated v1.1 C-4.6)
- Memory model lock: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` for dev mode
