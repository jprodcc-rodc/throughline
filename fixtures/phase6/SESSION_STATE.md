# Phase 6 Session State

**Purpose:** Cross-session continuity anchor. If the conversation is summarized or a new session opens, read this file FIRST to pick up exactly where the last session left off. This is the single source of truth for Phase 6 progress.

**Last updated:** 2026-04-25 — README polish wave shipped; FEATURE FREEZE in effect

## ⛔ DIRECTIVE: FEATURE FREEZE UNTIL DISTRIBUTION CATCHES UP

User explicit directive (2026-04-25):

> "README改完 + Hero GIF做完 + 第一期视频发了之前——不要再改产品。
> 你现在有1个star。你的任务是让这1个变成10个，不是加更多功能。
> Distribution > Features，在这个阶段。"

**Do NOT ship new product features until ALL three land:**

1. ☐ README polish — DONE 2026-04-25 (tagline, status, front-block,
   trimmed comparison, trimmed badges, Quickstart moved to #2, card
   example swapped to keto-rebound scenario)
2. ☐ Hero GIF — user will record. 10-15s: ChatGPT forgets you →
   throughline-enabled OpenWebUI remembers → card auto-generates in
   Obsidian. Tools: Arcade / Screen Studio / ScreenToGif.
3. ☐ First YouTube video (4-6 min) — user will record.
   Hook: "I had 500 conversations with ChatGPT and Claude over the
   past year. Most of them are gone. Here's what I built to never
   lose another one." Structure documented below in "Human-action queue".

## Feature backlog (DO NOT EXECUTE WITHOUT EXPLICIT UNFREEZE)

Recorded in priority order for the unfreeze signal:

1. **Anthropic native Messages API adapter** (v0.3) — currently
   `/v1/openai` shim; real adapter unlocks cache control, tool use,
   200k context reliably.
2. **daemon LLM integration tests** — provider wiring is mock-only
   at the HTTP boundary; need one real "config.toml → active_provider
   → daemon.call_llm_json" round-trip via mocked HTTP server.
3. **Uninstall CLI** — `python -m throughline_cli uninstall` alongside
   the existing `scripts/uninstall.sh/.ps1`.
4. **prompts/README.md expansion** — contributor onboarding for
   new-language and new-tier/family prompts.
5. **Type annotations audit** — public functions in `daemon/` lacking
   return types; enable mypy in CI downstream.

Any new feature work outside this list ALSO waits for unfreeze.

## Human-action queue (items I literally cannot do)

- **Hero GIF** — 10-15s three-scene demo. See the full storyboard
  below under "Hero GIF spec".
- **First YouTube video** — 4-6 min. Script outline below under
  "YouTube spec".
- **Mermaid → PNG via excalidraw** — front-page diagram aesthetics.
  User chose to defer the visual upgrade; README no longer has a
  front-block mermaid anyway (replaced with before/after text), so
  this is lower priority. Still tracked.
- **Medical-scenario card example** — user asked for their
  real (redacted) medical scenario. I declined to fabricate; kept
  the keto-rebound scenario from the bundled samples/claude_sample.jsonl
  as a placeholder. User can swap in their own redacted card at
  README.md § "What a refined card looks like" anytime.
- **Star the repo** from the user's own account.
- **Pin 1-3 good-first-issue tickets** on the Issues tab.
- **Watch → Custom** on the repo page (instructions given earlier).
- **asciinema demo recording** via `samples/record_wizard_demo.sh`.
- **Post to HN / Reddit / X / awesome-lists** — user's voice.

## Hero GIF spec (user will record)

Target: 10-15 seconds. Three scenes:

- **Scene 1 (5s):** User asks a context-dependent question in plain
  ChatGPT → response says "I don't have information about your
  medical history / your project / your preferences…". User visibly
  frustrated.
- **Scene 2 (5s):** Same user, same question, in OpenWebUI with
  throughline Filter enabled. Status line shows `⚡ auto recall:
  3 cards · conf=0.91`. AI response uses the user's real context.
- **Scene 3 (3s):** Cut to Obsidian vault. A new card appears in
  the graph as the conversation finishes refining.

Tools: Arcade.software (simplest, upload-to-generate) / Screen
Studio (Mac, auto-zoom, network look) / ScreenToGif (Windows, free).

## YouTube spec (user will record)

Target: 4-6 minutes. First-episode structure:

- **0:00-0:30 · Hook** — personal pain point, real, not acted.
  "I'm AuDHD, I have complex medical history, and I'm tired of
  explaining myself to every new chat."
- **0:30-1:15 · Problem** — why existing memory tools fall short.
  ChatGPT memory is black-box; only records labels not thinking.
- **1:15-2:30 · Demo** — the core. OpenWebUI question → RAG
  recall → AI answer with real background → Obsidian card view.
- **2:30-3:30 · Key tech point** — tell it as story, not architecture:
  "It doesn't just know my drug list. It remembers WHY I chose
  this combination. It's not memory of facts — it's memory of
  my thinking."
- **3:30-4:30 · Who you are + open source** — "I built this in
  12 days with Claude Code. I'm not a startup, I'm one person
  with AuDHD who couldn't find this tool. It's open source."
- **4:30-5:00 · CTA + next-episode teaser** — "If you felt this
  same frustration, try it. If you're building for neurodivergent
  users, contribute. Next: how I handle the refine pipeline with
  317 tests in 12 days."

Recording principles: real face (build trust), real screen recording
(no AI-generated visuals, no stock footage, no HeyGen), lav mic for
audio, user's own IELTS-7.5 English (don't over-polish), slow pace
with pauses.

---

## Where we are right now (TL;DR for next session)

**Repo visibility: PUBLIC** (was PRIVATE until yesterday).
<https://github.com/jprodcc-rodc/throughline>
<https://jprodcc-rodc.github.io/throughline/> ← docs site also live

**Latest commit on `main`:** README polish wave pending commit; prior `95dc425` + `261cf63` (docker compose + GH Pages bootstrap), 712 passed / 10 xfailed. CI green across lint + pytest 3.11 + pytest 3.12 + docs. · **GitHub:** `jprodcc-rodc/throughline`

**Tagline chosen (2026-04-25):** `"Stop re-explaining yourself to every new chat."`
— replaces the earlier "The thread that turns every LLM conversation…"
per user feedback; emotional directness beats product-essay prose.

**README polish wave shipped items (autonomous):**
- New tagline + new status block (drops "for the author" wording
  that signaled "nobody else can use this")
- Badges trimmed from 5 → 3 (test + license + python)
- Quickstart moved from section #4 to section #2 (direct after
  "What it does") — matches user-flow logic
- "What it does" front block: mermaid replaced with before/after
  text pair + three bullet differentiators. Mermaid retained for
  the later "Architecture" section where a system diagram belongs.
- Comparison table: 8 dimensions → 5 (Markdown you can read /
  Works fully local / Self-growing taxonomy / Survives tool
  changes / Target user). Dropped noisy columns (plug-in vector
  store / plug-in embedder / cost-aware ingest) that bloated the
  table on mobile.
- Card example swapped: PyTorch MPS → keto-rebound (from bundled
  sample-002). Still real data; demonstrates "card captures
  your THINKING not just facts" better than a tech Q&A.
- `🧪 Phase 6 regression` section moved out of README to a new
  `docs/TESTING.md`; README now has a single pointer line in the
  repo-layout section.
- `🔗 Links` section: added Docs site URL prominently.
- Acknowledgments: LLM-provider inline list removed (duplicated
  the providers table); now just names the runtime deps.

**Deliberately NOT done (user explicitly deferred):**
- Mermaid → excalidraw / PNG export
- Hero GIF recording
- YouTube video recording
- Swapping the keto example for the user's real (redacted)
  medical scenario — won't fabricate medical data; user can swap
  in their own anytime at README.md § "What a refined card looks like"

**Late-stage milestones (since the last anchor):**

- **`9536ba0`** — daemon `call_llm_json()` finally reads provider
  from the registry. Was hardcoded OpenRouter even after U28
  shipped the registry. New `throughline_cli/active_provider.py`
  module resolves provider-id for non-wizard callers (daemon +
  scripts) with precedence env > config.toml > autodetect >
  "openrouter".
- **`c588f33`** — `throughline_cli doctor` gained `check_llm_provider_key`:
  verifies the resolved provider's env var is set. Warns (not
  fails) when absent so a fresh install's first doctor run stays
  green on the things that genuinely matter.
- **Repo flipped PUBLIC** via `gh repo edit --visibility public
  --accept-visibility-change-consequences`. First time the project
  is accessible to anyone on the internet.
- **`636d44e`** — README + DEPLOYMENT.md rebalanced so OpenRouter
  is listed alongside 15 other providers, not THE default. Regrouped
  the provider table by use case (Direct / Hosted open-weights /
  China / Multi-vendor proxy / Local / Escape hatch). Prose leads
  with "no preferred vendor — wizard auto-detects whichever env var
  you already have set." Existing `OPENROUTER_API_KEY` users keep
  working with zero friction; no behaviour change.
- **Repo description refreshed** to: "Turn every LLM conversation
  into searchable, self-growing personal knowledge. 16 LLM providers
  (Anthropic · OpenAI · DeepSeek · SiliconFlow · Moonshot · Ollama ·
  …) · OpenWebUI → refine → Obsidian vault → RAG."
- **Topics grew to 16**: added anthropic / openai / deepseek /
  siliconflow / ollama / local-first alongside the original
  openwebui / obsidian / rag / llm / PKM / qdrant / bge-m3 / etc.

**User-facing instructions I handed over (not in git):**
- How to flip `Watch → Custom` for Issues + PRs + Discussions
  (owner default is only "Participating & @mentions" — they
  miss new issue fire-and-forget without this).

**What next session can pick up from (still-executable autonomously):**
1. **config.toml migration** — pre-U28 installs don't have
   `llm_provider` field; wizard should detect + write-in silently
   on open.
2. **mkdocs site** — publish README + CHANGELOG + ROADMAP + docs/
   to `https://jprodcc-rodc.github.io/throughline` via GH Pages.
   Fresh visitor surface.
3. **Docker compose** (issue #7) — one-command evaluate.
4. **wizard `--reconfigure` mode** (issue #8).
5. **daemon LLM integration tests** — currently the provider
   wiring is mock-only. Need at least one "real daemon reads
   config.toml, calls through to a mocked HTTP layer" round-trip.
6. **Anthropic native Messages API adapter** — v0.3. Currently
   uses the `/v1/openai` shim; a proper adapter unlocks cache
   control, tool use, and 200k context reliably.

**Things that need YOU (not me):**
- **Watch → Custom** on the repo page.
- **Star/pin** a `good first issue` to the top of Issues tab.
- **HN / awesome-lists / r/LocalLLaMA / r/ObsidianMD posting** —
  your voice, not mine.
- **asciinema screencast** recording via `samples/record_wizard_demo.sh`.
- **PyPI publish** when you want `pip install throughline`.

---

## Historical (the rest of this file is the journey up to the public flip)


**Session ran `/effort max` + resumed multi-provider + fresh-clone audit in one stretch. Key deliveries beyond the earlier UX wave:**

### Fresh-clone audit (commit `cf5326c`)
- Literally `git clone`d to /tmp, new venv, walked the user flow.
- Found BLOCKER: `requirements.txt` had UTF-8 em-dashes that pip
  can't decode on Chinese-locale Windows (GBK codec) — AND pip
  returned exit 0 anyway. Users would think install worked.
  Fixed: pure ASCII + inline PYTHONUTF8=1 hint. Regression test
  in `TestRequirementsFileAscii`.
- Fixed: `python install.py --help` used to silently start the
  wizard; now prints WIZARD_USAGE with a full step list + env
  vars and exits 0.
- Fixed: stale "v0.2.0-dev" labels in banner + step 4 — banner
  now reads dynamically from `throughline_cli.__version__`.

### U28 multi-provider (commits `ab7e189` + `9536ba0`)
- **New module `throughline_cli/providers.py`** — 16 OpenAI-compatible
  provider presets grouped by region:
  - Global: openrouter, openai, anthropic (OpenAI-compat shim),
    deepseek, together, fireworks, groq, xai
  - China: siliconflow (硅基流动), moonshot (Kimi), dashscope (阿里
    Qwen), zhipu (智谱 GLM), doubao (字节豆包 / Volcengine Ark)
  - Local: ollama, lm_studio
  - Escape: generic (user-supplied base_url + key)
- **`llm.py` provider-aware** — `call_chat(provider_id=...)` reads
  endpoint + env var + extra headers from the preset. Unknown
  provider_id falls through to legacy chain (no crash). Error
  messages cite the provider's specific env var + signup URL.
- **Wizard step 4 + 5 split** — step 4 picks provider backend
  (auto-defaults to whichever env var is already set, ● marker
  next to providers with key configured); step 5 picks a model
  SCOPED to that provider's list. OpenRouter shows
  `anthropic/claude-sonnet-4.6` style; direct Anthropic shows
  `claude-sonnet-4-5-20250929`; SiliconFlow shows
  `Qwen/Qwen2.5-72B-Instruct`; etc. prompt_family auto-derivation
  still works across all provider shapes.
- **New module `throughline_cli/active_provider.py`** — resolves
  active provider for NON-wizard callers (daemon, scripts).
  Precedence: THROUGHLINE_LLM_PROVIDER env > llm_provider in
  config.toml > autodetect > "openrouter". Never raises.
- **Daemon `call_llm_json` wired** — module-load `_LLM_URL` /
  `_LLM_KEY` / `_LLM_EXTRA_HEADERS` / `_LLM_PROVIDER_ID` from
  `active_provider.resolve_endpoint_and_key()`. Provider-specific
  headers merged (daemon keeps its own X-Title so cost dashboards
  can distinguish wizard preview from real refines). Legacy
  OPENROUTER_URL / OPENROUTER_API_KEY still work. Startup log
  prints `LLM PROV = <id> -> <url>` + `LLM KEY = set | MISSING`.
- **Doctor gained `check_llm_provider_key`** — new 6th check
  (positioned between state_dir and qdrant). Reads the resolved
  provider and verifies its env var is set; warn (not fail) if
  missing so fresh installs don't see red on their first doctor
  run. Tested for each provider family.
- **57 new tests** split across `test_providers.py` (32),
  `test_llm_providers.py` (13), `test_active_provider.py` (12),
  plus extensions to `test_wizard.py` + `test_doctor.py`.
- **README updated** — real 16-preset provider table replacing
  the hand-wavy "direct OpenAI / Anthropic / …" line.
- **Backward compatibility guaranteed** — existing installs with
  just `OPENROUTER_API_KEY` set keep working without any config
  change. The resolver autodetects it, the daemon keeps routing
  to OpenRouter. No migration required.

### What else I did in the resume
- SESSION_STATE + DEPLOYMENT + ARCHITECTURE + ALPHA_USER_NOTES +
  PHASE_6_CHECKLIST + ONBOARDING_DATA_IMPORT all brought current
  with v0.2.x reality (commit `3ffd749`).
- `__version__` exposure via importlib.metadata + `--version` CLI
  flag (commit `9b932b4`).
- `.pre-commit-config.yaml` ruff F+E9 hooks for contributors.
- CHANGELOG `[Unreleased]` section scaffolded per Keep-a-Changelog.
- `samples/record_wizard_demo.sh` asciinema-ready wizard demo
  driver.
- docs/DESIGN_DECISIONS.md gained §10-13 covering v0.2.0-era
  design calls (aliased backends, proposed_x_ideal as separate
  field, dial defaults render to empty string, three-state doctor).

**v0.2.0 is live:** `git tag v0.2.0` + GitHub Release page. Release URL:
<https://github.com/jprodcc-rodc/throughline/releases/tag/v0.2.0>

**UX wave done in the resumed session after user slept (2026-04-24 mid-day):**
All 10 items from the user-journey friction analysis shipped, tests green,
CI green. Order of commits (bottom-up = newest first):

- **`d261b75`** — ruff F541 lint fix (dead `f` prefixes in the new
  wizard/doctor files, auto-fixed).
- **J · `f0786d8`** — issue templates → GitHub YAML form schema.
  Required fields, dropdowns, rendered-shell blocks. Bug template
  now asks for `doctor` output + active backend triple. Feature
  template has required "why now" + target-release dropdown.
- **I · `71f3aff`** — `CONTRIBUTING.md` expanded (dev-setup, claim-
  issue flow, commit conventions, house style) + `pyproject.toml`
  package skeleton (console scripts `throughline-{install, import,
  taxonomy, doctor}`, 5 optional-dep extras, ruff + pytest tool
  config consolidated).
- **H · `f2d600a`** — error-message remediation audit. Every user-
  facing `ERROR:` / `sys.exit()` now tells the user what to do next:
  `ingest_qdrant.py` VAULT_PATH + openai missing, pack_source_model_guard
  CLI, `llm.py` no-API-key path.
- **D+E+F+G · `bf71d3f`** — README polish + wizard preview cost
  preflight. (D) Comparison table vs mem0 / Letta / SuperMemory /
  OpenWebUI memory. (E) Real before/after card example using sample-001.
  (F) Wizard step 13 asks `ask_yes_no("Run the preview?")` before
  spending the user's ~$0.01. (G) Mermaid architecture diagram
  replacing ASCII flow — adds U27 observer/review loop arrows.
- **C · `0c7e1c8`** — bundled sample export. `samples/claude_sample.jsonl`
  (10 synthetic conversations across AI / Health / Creative / Biz /
  Game domains for U27 signal). New `python -m throughline_cli import
  sample` source routes through the Claude adapter with the bundled
  path and auto-tags `sample-YYYY-MM-DD`. Single biggest evaluation-
  funnel improvement — new users no longer need their own export.
- **A+B · `dabcaa9`** — wizard end-of-flow next-steps panel
  (tailored per mission: Full shows RAG server + daemon + Filter;
  RAG-only shows /v1/rag pointer; Notes-only skips both). Plus the
  brand-new `python -m throughline_cli doctor` command: 10 checks
  in dependency order (Python version → imports → config → state →
  services → caches), `CheckResult` dataclass with remediation
  hints, `--quiet` + `--json` modes, exit 1 iff any fail.

**Test count:** 586 passed, 10 xfailed (was 551 before UX wave; +35
new tests across doctor / sample import / preflight gate).

**UX friction points — before vs after:**

| Stage | Before | After (this session) |
|---|---|---|
| Evaluate | "how does this differ from mem0/Letta?" unanswered | README comparison table |
| Decide | ASCII diagram missing U27 feedback loop | Mermaid diagram with U27 arrows |
| Install | no export = can't try | `import sample` gets 10 refined cards, $0.03 |
| Install | step 13 silently charges ~$0.01 | explicit "Run preview?" ask |
| Install | wizard exits into silence | "Next 3 steps" panel with copy-paste cmds |
| First-Run | broken deploy = read 3 log files | `throughline_cli doctor` one-shot self-check |
| First-Run | `ERROR: VAULT_PATH` no hint | every error lists the fix command |
| Trust | `CONTRIBUTING.md` said "placeholder" | real onboarding: dev setup + claim flow + conventions |
| Trust | no `pip install -e .` path | `pyproject.toml` with console-script entry points |
| Trust | MD issue templates with HTML comments | YAML forms with dropdowns + required fields |

**GitHub CLI (`gh`) state:** installed at `C:\Program Files\GitHub CLI\gh.exe`,
on user PATH, authenticated as `jprodcc-rodc` via https OAuth. Use
`gh <command>` directly in new shells. Gotcha: `--git-protocol ssh --web`
stuck on a greyed-out authorize button in the previous session; use
`--git-protocol https --web` if re-authenticating.

**Branch protection:** user confirmed enabled (GitHub UI ruleset).
Required checks: `pytest (3.11)` + `pytest (3.12)` + `lint (ruff)`.

**What's genuinely left that I can execute autonomously (v0.2.x polish):**
1. **wizard `--reconfigure` mode** (issue #8) — existing config detected →
   menu of "run all / pick steps / show summary". Shell of design is in
   the issue; real impl is ~3 hours.
2. **`asciinema` screencast script** (text, no video) — bundle a shell
   script that drives the wizard through a sample import so users see
   the flow without me recording. Not as sexy as a GIF but autonomous.
3. **Type hints audit** — some public functions in `daemon/` lack
   return types. Tighter signatures for LSP/IDE UX without adding
   mypy to CI.
4. **`docs/ARCHITECTURE.md` sync** — likely stale on U12/U20/U21/U23/U27
   additions. Needs a read-through + rewrite of a couple sections.
5. **`docs/DEPLOYMENT.md` sync** — the manual 5-step install is still
   documented; should now lead with the wizard path and note the
   manual path as advanced/scripted.

**What requires YOU:**
- Demo GIF/screencast (recording) — or use asciinema if you want
  the auto-drive path.
- Posting to HN / awesome-obsidian / r/LocalLLaMA / r/ObsidianMD /
  r/selfhosted — your voice, your account.
- PyPI upload — needs account + API token + trusted-publishing setup.
- v0.3 branch kickoff when you're ready to start concrete driver
  work (lancedb / duckdb_vss / pgvector / sqlite_vec).

**Post-release hardening done in this extended session (2026-04-24 late):**
- **daemon import bug fix** (`6ce8534`) — `JD_ROOT_MAP`,
  `JD_LEAF_WHITELIST`, `normalize_route_path`, `is_valid_leaf_route`
  were referenced by `daemon/refine_daemon.py` but never exported from
  `daemon/taxonomy.py`. A fresh `git clone` + `python -m
  daemon.refine_daemon` ImportError'd at module load; author's local
  setup worked only because a local `config/taxonomy.py` override
  happened to re-export under the old names. Aliases added;
  `fixtures/v0_2_0/test_daemon_import_surface.py` pins the contract.
- **rag_server wired to U12/U20/U21** (`3568b22`) — before this commit
  the abstractions existed but `rag_server/rag_server.py` hard-coded
  bge-m3 + bge-reranker-v2-m3 + direct Qdrant HTTP. `EMBEDDER=openai`,
  `RERANKER=cohere`, `VECTOR_STORE=chroma` env vars now actually flip
  the backend end-to-end. Models lazy-load on first real call so
  `import rag_server.rag_server` stays fast. `qdrant_request()` kept
  for `/v1/rag/health` only.
- **Open-source scaffolding** (`ac90445`) — `.github/workflows/test.yml`
  (pytest on 3.11 + 3.12, <60s green), PR template, feature-request
  issue template + config.yml routing questions to Discussions,
  `SECURITY.md` (private advisory channel + in-scope surface),
  `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1 short form),
  `CHANGELOG.md` (v0.1.0 + v0.2.0 in-repo history), README badges (CI
  status / release / license / python), repo metadata via `gh` (10
  topics + description), GitHub Discussions enabled.
- **Dependabot** (`677421f`) — weekly scan of pip + github-actions,
  major-only (ignores semver-minor/patch noise).
- **ingest_qdrant.py CI fix** (`4d17bbd`) — deferred `openai` import
  into `_get_embed_client()` so the module loads without the optional
  dep (CI was failing at `from openai import OpenAI` → sys.exit(1)).
- **ruff + CodeQL + dead code** (`cf516e1`) — `.github/workflows/codeql.yml`
  weekly + on-push, `security-and-quality` query suite. `test.yml`
  gains a `lint` job running `ruff check --select F,E9 .`. Auto-fix
  pass cleaned 22 unused imports across daemon / ui / adapters /
  tests; 4 F841 unused locals hand-fixed. Ruff scope is intentionally
  narrow (F = pyflakes, E9 = syntax); widening to pycodestyle is a
  v0.3 decision.

**Test count:** 551 passed, 10 xfailed (up from 38 + 10 at v0.1.0).

**GitHub CLI (`gh`) is now installed at `C:\Program Files\GitHub CLI\gh.exe`
and on the user PATH. Authenticated as `jprodcc-rodc` via https OAuth.
New shells can just `gh <command>`. Previous auth attempt with
`--git-protocol ssh --web` stuck on a greyed-out authorize button —
switch to `--git-protocol https --web` and the device code flow works
cleanly.**

**Next session can pick from (suggestions the user was working through
but didn't yet execute — not commitments):**
1. **ROADMAP.md** — public v0.3+ direction (U27.5-.7, real lancedb /
   duckdb_vss / sqlite_vec / pgvector impls, docker compose, Voyage /
   Jina dedicated rerankers, potentially a PyPI release).
2. **README quickstart polish** — 5-step path from `git clone` to a
   working wizard + first card, placed near the top.
3. **Seed 2-3 "good first issue" tickets** on GitHub so the repo isn't
   an empty contributor funnel; create `good first issue` and
   `help wanted` labels via `gh`.
4. **Branch protection ruleset** — user was configuring via GitHub UI
   when session paused. Recommended config is already documented in
   chat: `main-branch-protection` ruleset, require status checks
   `pytest (3.11)` + `pytest (3.12)`, block force-push, restrict
   deletions, bypass list includes repo admin.

**Other outstanding (non-OSS, product-side):**
- Demo GIF / screencast of the wizard for the README.
- Docker compose for one-command try-it-out (blocked: needs OpenWebUI
  + Qdrant + daemon + vault-volume decisions).
- Posting to HN / awesome-lists / r/ObsidianMD / r/LocalLLaMA once
  onboarding polish lands.
- `v0.2.x` maintenance-release track if users report bugs against
  v0.2.0 (CHANGELOG.md + CI already in place to support this cleanly).

What works today end-to-end:
- `python install.py` → full 16-step wizard with banner + progress ticker
- 3 import adapters (claude / chatgpt / gemini) dogfooded against a real
  Gemini takeout; adapter trio wired INTO step 10 + step 16 of the wizard
- `python -m throughline_cli import <source> <path>` standalone CLI
- `python -m throughline_cli taxonomy [review | reject]` (U27.4 loop)
- Preview gate (step 13) calls real LLM via `throughline_cli/llm.py` with
  OPENROUTER_API_KEY / OPENAI_API_KEY fallback
- 8 refiner prompt variants (skim/normal/deep/rag_optimized × claude/generic)
- rag_server swappable: `EMBEDDER=openai RERANKER=cohere VECTOR_STORE=chroma` flips
  all three without code edits (U12/U20/U21 wired to FastAPI endpoints).
- daemon enforces `daily_budget_usd` cap (U3); 5-dial refiner tuning from
  `config.toml` flows into every refine (U23); every refine logs a
  `(primary_x, proposed_x_ideal)` pair to `state/taxonomy_observations.jsonl`
  for U27 growth signals.
- Filter cold-start 🌱 / 🌿 status line with 5-min Qdrant count cache
- Uninstall scripts for mac/linux + windows

What ships on first-user hit:
- `python -m throughline_cli import claude <zip>` → 48 MDs of their Claude
  history in < 30s, zero API cost
- Same for ChatGPT / Gemini (Gemini 7559 events → ~100 day MDs, ~$25 Normal)
- `python install.py` config wizard with sensible all-Enter defaults
- Fresh `git clone` → daemon imports without needing a local taxonomy.py
  override (pre-v0.2.0 regression fixed in `6ce8534`).

**Context (old v0.2.0 planning notes below):** U13 one-shot derivation **is shipped
   (commit `7504638`)**; the 2026-04-24 evening design pass identified
   that U13 alone fits only the ~25% of users with 100+ cards at
   install. v0.2.0 must also ship a **self-growing taxonomy** loop
   (U27) — see `docs/TAXONOMY_GROWTH_DESIGN.md` for the spec.
   **U27.1 shipped in `7518043`** — minimal skeletal taxonomy +
   wizard default follows card-count heuristic. **U27.2 shipped in
   `a0a16ee`** — 8 refiner prompts now emit `proposed_x_ideal`.
   **U27.3 shipped in `a724449`** — `daemon/taxonomy_observer.py`
   appends to `state/taxonomy_observations.jsonl` on every refine.
   **U27.4 shipped in `5026801`** — `throughline_cli/taxonomy.py`
   provides three commands: `taxonomy` (status), `taxonomy review`
   (interactive add/reject/name-as-different/skip walk-through),
   `taxonomy reject TAG` (unattended). Detector normalises tags
   (AI/Agent ≡ ai/agents ≡ AI_Agent), applies both count + day-span
   thresholds (P3), dedups by card_id (P5), honours
   `config/taxonomy_rejected.json`, and parent-infers. Add action
   surgically inserts into `VALID_X_SET` literal of
   `config/taxonomy.py` (bootstrapped from the minimal seed on
   first write so the shipped file stays untouched). 53 tests in
   `fixtures/v0_2_0/test_taxonomy_cli.py` cover every piece + an
   end-to-end round-trip (observe → detect → add → re-detect is
   empty). **U27 MVP loop now closed.** Remaining taxonomy work
   is v0.3+ only (U27.5 Filter hint, U27.6 batch re-refine,
   U27.7 deprecation).

   **All remaining v0.2.0 U items shipped this session:**
   - **U4** (`04f7fd0`) — wizard step 10 tail consent panel
     showing provider + privacy + import_source tag + explicit
     yes/no gate; local_only skips the prompt.
   - **U3** (`1373bf6`) — `daemon/budget.py` resolves the cap
     from env > config.toml; `process_raw_file` skips without
     touching state when today's spend ≥ cap. Zero cap = kill
     switch. Day rollover resets naturally.
   - **U23** (`7cbc402`) — `daemon/dials.py` renders a
     `<user_dials>` tail appended to every refiner system prompt
     when any of the 5 dials (tone/length/sections/register/
     keep_verbatim) are non-default. Wizard step 13's
     `_dial_panel()` drives the cfg; empty-on-default keeps
     untouched configs at zero token overhead.
   - **U12** (`b666ff4`) — `rag_server/embedders.py` with
     `BaseEmbedder` + `BgeM3Embedder` (lazy torch) +
     `OpenAIEmbedder` (stdlib urllib). Registry + alias map.
     `scripts/ingest_qdrant._resolve_vector_size()` now derives
     from the active embedder.
   - **U20** (`1fb0e9c`) — `rag_server/rerankers.py` with
     `BaseReranker` + `BgeRerankerV2M3` + `CohereReranker` +
     `SkipReranker`. Cohere re-aligns rel-sorted results to
     input order; missing API key falls back to Skip.
   - **U21** (this commit) — `rag_server/vector_stores.py` with
     `BaseVectorStore` + `QdrantStore` (stdlib urllib, matches
     wire calls the daemon already uses) + `ChromaStore`
     (optional dep, stub on missing install). Registry + alias
     map routes lancedb / duckdb_vss / sqlite_vec / pgvector →
     qdrant for now; v0.3+ ships the real impls.

   **v0.2.0 is feature-complete.** Next: tag + release, or
   dogfood through the wizard against a clean machine to shake
   out anything the test suite missed.

---

## v0.1.0 shipped 🎉

- Tag: `v0.1.0` → commit `cbbb92f`
- GitHub Release: https://github.com/jprodcc-rodc/throughline/releases/tag/v0.1.0
- Phase 6 ship-blockers all green (see next section)
- Post-v0.1.0 work rolled directly into v0.2.0 planning (below).

## v0.2.0 scope (rev 3, decided 2026-04-23 late evening)

After a third round of user additions, the wizard grows to 16 steps
but Mission branching (step 2) can shrink effective step count to
9-10 for specialised users. Six new U items landed; key architectural
observation: **card consumption mode (for reading vs for retrieval)
is an independent dimension the v0.1 architecture accidentally
welded to structure + tier**. Mission branch decouples them.

See the non-rev2 section below for the full list. Additions in rev3:

- **U20** Reranker swappable (paired with U12 in wizard step 7):
  bge-reranker-v2-m3 / v2-gemma local, Cohere / Voyage / Jina API,
  or skip.
- **U21** Vector DB swappable (wizard step 3): Qdrant (default Full),
  Chroma (default Local-only privacy), LanceDB, DuckDB-VSS,
  SQLite-vec, pgvector. `BaseVectorStore` abstraction spanning
  rag_server + daemon + ingest — largest engineering item.
- **U22** Prompt family per LLM (wizard step 8, auto-derived):
  Claude XML / GPT Markdown+JSON / Gemini structured / generic.
  ~48 prompt files (tier × mode × family), code-light but docs-heavy.
- **U23** Preview 5-dial constrained edit (wizard step 13): Tone,
  Length, Sections toggle, Language register, Keep-verbatim.
  No free-form prompt editing to preserve daemon schema.
- **U24** Mission branching (wizard step 2): Full flywheel /
  RAG-only / Notes-only. Decides which later steps apply.
- **U25** RAG-optimized card format (triggered by U24 RAG-only):
  title + entities + 3-8 atomic claims, no prose envelope.
  ~$0.001/conv. `prompts/en/refiner.rag_only.*.md`.

### The wizard's 16 steps (rev 3)

```
[1]  Python + venv + deps
[2]  Mission (U24) — Full / RAG-only / Notes-only    ← early branch
[3]  Vector DB (U21)  [skipped if Notes-only]
[4]  API key
[5]  LLM provider (U11)
[6]  Privacy level (U18)
[7]  Retrieval backend (U12 + U20)   [skipped if Notes-only]
[8]  Prompt family (U22) — auto-derived, confirm only
[9]  Import source (U2) + cold-start warning if fresh
[10] Import scan
[11] Refine tier (U15) + smart suggestion (U19)
[12] Card structure (U16)   [skipped if RAG-only, U25 format fixed]
[13] First-card preview (U17) + 5-dial constrained edit (U23)
[14] Taxonomy (U13)
[15] Daily budget cap (U3)
[16] Summary + confirm
```

## v0.2.0 scope (rev 2, decided 2026-04-23 evening)

**One sentence:** `python -m throughline install` is a 13-step wizard
that collects every onboarding decision with a sensible default per
step. All Enter = working config. Re-run any time to reconfigure.

**Everything in v0.2.0 orbits this one command.** The 13 steps
summon the underlying mechanisms (U1, U2, U3, U11-U19) — each step
surfaces a user decision that some code path has to honour.

### The wizard's 13 steps

```
[1]  Python + venv + deps
[2]  Docker / Qdrant
[3]  API key
[4]  LLM provider matrix (U11 — Anthropic / OpenAI / xAI / etc.)
[5]  Privacy level (U18 — Local-only / Hybrid / Cloud-max)
[6]  Embedder backend (U12 — bge-m3 / nomic / MiniLM / OpenAI)
[7]  Import source (U2 — ChatGPT / Claude / Gemini / fresh) + cold-
     start warning if fresh
[8]  Import scan (count + token estimate)
[9]  Refine tier (U15 — Skim / Normal / Deep, 40x cost spread)
     + smart suggestion (U19)
[10] Card structure (U16 — Compact / Standard / Detailed) via
     first-card preview (U17)
[11] Taxonomy (U13 — derive from vault / derive from imports /
     templates fallback)
[12] Daily budget cap (U3 — THROUGHLINE_MAX_DAILY_USD)
[13] Summary + confirm
```

### P0 work that underlies the wizard

- **U14** — the wizard itself (Rich-based CLI, config persistence
  to `~/.throughline/config.toml`).
- **U11** — LLM provider matrix (Grok via OpenRouter; doc-only, no
  code change).
- **U12** — embedder abstraction in `rag_server/rag_server.py`;
  `ingest_qdrant.py` derives VECTOR_SIZE from active embedder;
  Qdrant-rebuild flag on embedder change.
- **U13** — `scripts/derive_taxonomy.py` (LLM-derived from vault or
  imports); JD/PARA/Zettel templates demoted to fallback.
- **U15** — three refiner prompt variants (`refiner.skim.md`,
  `refiner.normal.md`, `refiner.deep.md`); pipeline
  parameterisation for stage count (Skim skips slicer, Deep adds
  critique).
- **U16** — same three-structure variant + first-card preview gate.
- **U17** — preview gate between step 10 and bulk refine.
- **U18** — privacy level as separate config axis; filters which
  models/endpoints the pipeline can use.
- **U19** — smart tier suggestion from corpus size + budget.
- **U2** — three adapters (see import section below).
- **U1** — cold-start Filter status line (🌱/🌿/full by card count).
- **U3** — daily budget cap enforced by daemon queue.
- **U4** — privacy-consent dry-run + `import_source` tag (now lives
  inside the wizard as step 7b).

### P1 shipped 2026-04-24

- **U5** — "Obsidian is optional" callout added to README.md top +
  DEPLOYMENT.md prerequisites. Plain Markdown files work in any
  editor; Obsidian is recommended, not required.
- **U6** — bge-m3 preflight section in DEPLOYMENT.md prerequisites.
  Suggests `pip install "huggingface_hub[cli]"` + two
  `huggingface-cli download` commands so the ~4.6 GB download happens
  once up front instead of blocking the first rag_server start.
- **U8** — scripts/uninstall.sh (macOS + Linux) + scripts/uninstall.ps1
  (Windows). Both prompt before each destructive step, default-keep
  the refined vault (user content), default-keep the Qdrant
  collection (--drop-collection to opt in), handle launchd / systemd
  / Docker container stops, clean ~/.throughline + runtime dir, hand
  off the OpenWebUI Filter removal as a manual step with a pointer.
- **~~U7~~** — taxonomy static templates **subsumed by U13**;
  JD/PARA/Zettel live on as wizard fallback only.

### v0.2.0 P0 shipped 2026-04-23 / 04-24

- **U14** wizard skeleton + TUI polish + step-10 adapter integration
- **U22** prompt family loader + normal/rag_optimized variants
- **U25** RAG-optimized card format (claude + generic)
- **U2** 3 import adapters (claude / chatgpt / gemini) — claude
  dogfooded 5 real bugs, gemini 0 bugs
- **U17** first-card preview (wizard step 13 calls real LLM via new
  throughline_cli/llm.py)
- **U15** tier matrix complete: skim / normal / deep × claude /
  generic = 8 prompt files
- **U1** cold-start status line in Filter (🌱 0-49 / 🌿 50-199 /
  silent 200+) with 5-min Qdrant count cache
- **U26** wizard banner + between-step progress ticker
- **U24** mission branching (baked into U14)
- **U3** daily USD cap scaffolded in wizard config; daemon
  enforcement still pending

### Still outstanding

- **U23** 5-dial constrained edit (preview iteration)
- **U13** taxonomy LLM derivation (wizard step 14 is currently
  template-only)
- **U3** daemon enforcement of THROUGHLINE_MAX_DAILY_USD
- **U4** import privacy-consent dry-run panel (tag exists; the
  interactive confirm pass needs stitching)
- **U12** embedder backend swappable (rag_server refactor)
- **U20** reranker swappable
- **U21** vector DB abstraction (biggest engineering item)

### Test counts (latest)

289 passed + 10 xfailed (was 38 + 10 at v0.1.0 tag). New sub-suites
across v0.2.0:
  - test_wizard.py          35
  - test_prompts.py         57
  - test_adapters_claude.py 55
  - test_adapters_chatgpt.py 41
  - test_adapters_gemini.py 38
  - test_preview.py         18
  - test_cold_start.py      15
Plus the 38 v0.1.0 Phase-6 cases still green.

**Deferred from v0.2.0 to v0.2.x marketing phase:**
- U9 — hero gif automation toolchain (Charm VHS + Remotion + OBS)
- U10 — dual-gif strategy (30s README loop + 60s import walkthrough)
- Design spec preserved in `docs/ONBOARDING_DATA_IMPORT.md` for later
  pickup; just not a v0.2.0 blocker.

**Deferred to v0.3.0:**
- B2 Merge & Synthesis (L3 cross-source aggregation; the correct home
  for "full aggregation" questions that adapters deliberately avoid).

**Private-repo ROADMAP** (`S:\syncthing\obsidian_python\docs\ROADMAP.md`,
commits `3f33621` / `428a73b`) has the same scope with the author's
personal notes attached. Public repo carries only the mechanism-level
plan.

---

## Where we are

Phase 6 = **English-only regression** for the open-source `throughline` repo (rewrite of a private upstream flywheel whose original natural language was not English). Every non-English artifact either stripped or rewritten; now validating the English rewrites don't regress behavior.

| Harness | Scope | Status | File(s) |
|---|---|---|---|
| **H1** | RecallJudge EN classification drift (48 cases × real Haiku 4.5) | ✅ **45/48 PASS (93.8%)** · 3 brainstorm drift accepted | `run_h1.py` · `recall_judge_en.jsonl` · `h1_results.json` · `H1_ANALYSIS.md` |
| **H2** | Cheap-gate short-turn behavior (20 cases offline) | ✅ **10/20 MATCH** · 10 gaps = intentional bare-pronoun regex strip (accepted as v0.1.0 cost) | `run_h2.py` · `pronouns_en.jsonl` · `h2_results.json` |
| **H3 code** | Card-injection wrapper + truncation (9 CD/LN cases offline) | ✅ **9/9 PASS** | `run_h3_code.py` · `h3_code_results.json` |
| **H3 Haiku** | Injection/PII/roleplay resistance (31 cases × real Haiku 4.5) | ✅ **31/31 PASS (100%)** after retry of 2 network timeouts · $0.17 | `run_h3_haiku.py` · `retry_h3_errors.py` · `h3_haiku_results.json` · `H3_ANALYSIS.md` |
| **H4** | 4 refiner prompts on EN raws (8 sampled cases × real Sonnet 4.6) | ✅ **15/16 PASS (93.8%)** · 1 WARN on personal/universal boundary, zero structural failures | `refiner_en.jsonl` · `h4_results.md` |

## Commits on this branch (public throughline, all pushed)

- `bac196a` — Phase 6 H1 fixture + runner + results + analysis
- `7a0f936` — Phase 6 H2 + H3 code + cheap-gate `thanks` fix + SESSION_STATE
- `8ab61dd` — Phase 6 H3 Haiku + H4 Sonnet-subagent + dual-layer injection guard doc
- `b0d8503` — CHINESE_STRIP_LOG backfill + README Phase 6 section + shape fuzz + overnight report

## Private-repo sync (done 2026-04-23)

Three files in `S:\syncthing\obsidian_python` updated to reflect Phase 6 completion:

- `docs/THROUGHLINE_PHASE6_RISKS.md` — §0 execution row flipped ✅, §1 regression results filled, §4 ship-blocker 4/7 checked, §5 overnight summary added
- `CLAUDE.md` — timeline header row for 2026-04-23 Phase 6 overnight added
- `docs/.internal/BUSINESS_ANALYSIS_ONEPAGER.md` — new §4.13 Phase 6 section, test-point count 317→420+, open-source-readiness table refreshed (prompt-language row + test-coverage row)

No `[mech]` commits on the private side this session — sync was docs-only.

## Key paths

| What | Where |
|---|---|
| Public repo (throughline) | `C:\Users\Jprod\code\throughline` |
| Private mirror (obsidian_python) | `S:\syncthing\obsidian_python` |
| Phase 6 fixtures + runners | `throughline/fixtures/phase6/` |
| Shipped Filter | `throughline/filter/openwebui_filter.py` |
| Shipped 8 EN prompts | `throughline/prompts/en/` |
| Chinese-strip log (HIGH-risk roll-up) | `throughline/docs/CHINESE_STRIP_LOG.md` |
| Phase 6 checklist (public) | `throughline/docs/PHASE_6_CHECKLIST.md` |
| Phase 6 risk mirror (private) | `S:\syncthing\obsidian_python\docs\THROUGHLINE_PHASE6_RISKS.md` |

## Credentials handling

- OpenRouter key rotated once in previous session. Current key visible in my context from a Read tool call on `C:\Users\Jprod\.tl_key` (file deleted after use). User's preference: use it for remaining Phase 6 runs without another rotation; user can re-rotate post-phase if desired.
- **Rule for next session:** if the key in Filter code history differs from the one in valves, user has rotated. Do NOT inline keys in user-visible commands; prefer `$env:OPENAI_API_KEY` via launchd/shell profile or pure-file-flow via `C:\Users\Jprod\.tl_key` with immediate `rm` after.

## Fixture calibration history (important — do not re-debug)

H1 went through two fixture versions because the initial fixture confused display-label `general` with JSON-value `auto`. Root-cause resolved. Calibrations per filter.py few-shot:

- **Line 1088-89:** no-anchor generic definition → `native`
- **Line 1091:** should-I/what-if (no anchor) → `brainstorm`
- **Line 1092:** explicit "decided …" → `decision`
- **Line 1094:** proxy-person ("my friend …") → `native`
- **Line 1095:** meta-self ("what's your …") → `native`

## Known English-only behavior gaps (accepted for v0.1.0)

1. **Brainstorm drift** — English "should we / what if / give me N ideas" classified as `native` instead of `brainstorm` by Haiku. Users must use `/recall` for explicit RAG. Ship as known limitation. (H1 B01/B02/B03)
2. **Bare-pronoun cheap-gate absent** — "it" / "that one" / "what about it" as first-turn inputs hit Haiku instead of being cheap-gated. Cost ~$0.003/turn. (H2 FT01-FT10)
3. **Thanks fix applied** — added "thanks / thank you / thx / ty / cheers" to `_NOISE_RE`. (filter/openwebui_filter.py:740-741)

## Pending work (overnight batch — all done)

1. ✅ H3 Haiku-side batch (31/31 PASS · $0.17)
2. ✅ H4 Sonnet subagent (15/16 PASS, 1 WARN)
3. ✅ Pytest wrappers (`test_phase6.py`, 21 passed + 10 xfailed)
4. ✅ EN fuzz probe pass (`fuzz_inlet.py` ported shape-only, 17/17 no-crash)
5. ✅ README Phase 6 public results section
6. ✅ Private-repo docs sync (THROUGHLINE_PHASE6_RISKS.md + CLAUDE.md + BUSINESS_ANALYSIS_ONEPAGER.md)
7. ✅ `docs/CHINESE_STRIP_LOG.md` populated with H1-H4 results
8. ✅ `PHASE6_OVERNIGHT_REPORT.md` written

## Ship-blocker status (2026-04-23)

All four pre-tag ship-blockers are green; `v0.1.0` is clear to tag.

- ✅ CJK + identity grep sweep (commit `68df132`): 3 leaks fixed (H1_ANALYSIS CN few-shot literals, SESSION_STATE RODC prose + CN column label, PHASE_6_CHECKLIST `non-RODC-persona`). Residual `rodc` tokens are all `jprodcc-rodc/throughline` GitHub URL / Copyright handle (tolerated per CHINESE_STRIP_LOG §whitelist) or inside CHINESE_STRIP_LOG itself (expected historical record).
- ✅ M4 cross-platform `point_id` determinism (commit `514aa26`): `fixtures/phase6/test_m4_point_id.py` 7/7 PASS — unit-test substitute for the operational Win+WSL diff check, pins `_norm_path` + `make_point_id` convergence + golden md5 values. Full Win+WSL live ingest remains as a post-tag nice-to-have.
- ⏳ Fresh-clone DEPLOYMENT.md walkthrough — deferred to Phase 7 dogfooding (alpha users). Not a pre-tag gate.

## Next actions (pick one)

**A. Tag v0.1.0 (ready now)**
   - `git tag v0.1.0 <sha>` — pick the commit, optionally sign/annotate
   - `git push origin v0.1.0`
   - Draft a GitHub release with the Phase 6 result table + accepted limitations
   - Estimated 10-15 min

**B. Phase 7 dogfooding prep**
   - Walk through `docs/DEPLOYMENT.md` as a fresh user (clean env, read-and-follow), log every stumble
   - Write `docs/ALPHA_USER_NOTES.md` with the friction points
   - Then invite 1-2 alpha users

**C. `[mech]`-class back-port from private repo**
   - `git -C S:\syncthing\obsidian_python log --grep='\[mech\]'` to find mech-level commits not yet in throughline
   - Hand-port each (no rebase/cherry-pick across repos; strip identity)
   - Run CHINESE_STRIP + identity scan after each port
   - Independent of A/B; any time

Recommendation: **A → B → C**. A gives a clean baseline tag for B to test against.

## Next session quick-start

```bash
# 1. Read this file first (continuity anchor)
# 2. Confirm no drift
cd C:\Users\Jprod\code\throughline
git log --oneline -10    # should show b0d8503 at tip, Phase 6 commits behind
git status               # should be clean

# 3. Start on next action A (ship-blocker sweep) unless user redirects
#    - CJK grep:      rg '[\u4e00-\u9fff]' --glob '!fixtures/**' --glob '!docs/CHINESE_STRIP_LOG.md'
#    - identity grep: use the private-side risk checklist for the full identity token list
#    - M4 point_id:   ingest same fixture vault on Win + WSL, diff qdrant point_id sets
```

## Phase roadmap ahead

- **Phase 6 (now):** Regression harnesses + results documented
- **Phase 7:** Private collaborator dogfooding (invite 1-2 alpha users)
- **Phase 8:** Public release v0.1.0 + HN Show post

---

_If reading this is the first thing you do in a new session: don't redo the fixture calibration — it's already correct. Start by checking background job outputs (H3 Haiku + H4 Sonnet) and continuing the overnight batch checklist above._
