# Alpha User Notes

> Friction log from a static audit of `DEPLOYMENT.md` against the real
> codebase, done immediately post-v0.1.0 by the author playing the role of
> a fresh external user. The goal is to fix install blockers before any
> alpha user hits them, and to give later external users a running log of
> known rough edges.
>
> External contributors: if you hit a stumble not in this log, please
> open an issue — your PR or bug report becomes the next section.

---

## Post-v0.1.0 static audit (2026-04-23)

Performed against commit `fc08259`, before any external user ran the
guide. Every item below is either already fixed or has a concrete next
step.

### Fixed in this audit

| # | Issue | Fix |
|---|---|---|
| 1 | `requirements.txt` referenced in Step 1 (`pip install -r requirements.txt`) did not exist at the repo root. A fresh clone would have failed immediately after `git clone`. | Added `requirements.txt` with loose pins covering `fastapi`, `uvicorn[standard]`, `torch`, `transformers`, `pydantic`, `pyyaml`, `watchdog`, `pytest`. |
| 2 | `DEPLOYMENT.md § Step 5` named the daemon refine-status valve `DAEMON_REFINE_URL`, but the actual Filter exposes it as `REFINE_STATUS_URL` (plus `REFINE_STATUS_ENABLED` and `REFINE_STATUS_TIMEOUT`). A user looking for `DAEMON_REFINE_URL` in the OpenWebUI Valves pane would not find it. | Renamed in the doc. The valve reference table now matches the code. |
| 3 | `DEPLOYMENT.md § Step 6` gave `export INGEST_EXTRA_WHITELIST='00_Buffer/00.00_Overview'` as the example, but `scripts/ingest_qdrant.py` parses this env var as a JSON list via `_parse_json_list`. The bare-string form would raise `json.JSONDecodeError` on startup. | Example now shows the JSON-list form: `'["00_Buffer/00.00_Overview"]'`. Also clarified that `INGEST_INCLUDE` accepts exact folder names and/or `re:`-prefixed regexes, not glob patterns. |

### Second pass (2026-04-23, same day, after `6213448`)

Deeper audit across all 14 sub-READMEs + architecture docs. Seven fixes
applied in one follow-up commit; one finding triaged as non-issue.

| # | Issue | Fix |
|---|---|---|
| 4 | **Collection-name mismatch would silently empty RAG.** `.env.example` set `QDRANT_COLLECTION=knowledge_notes` and `daemon/refine_daemon.py` defaulted to `knowledge_notes`, but `rag_server/rag_server.py` and `scripts/ingest_qdrant.py` both read `RAG_COLLECTION` defaulting to `obsidian_notes`. A user following the defaults would write into `knowledge_notes` and read from `obsidian_notes` — silent empty retrieval. | Unified on `RAG_COLLECTION=obsidian_notes` in `.env.example`. `daemon/refine_daemon.py` now reads `RAG_COLLECTION` first and falls back to `QDRANT_COLLECTION` (deprecated) so existing `.env` files keep working. Default changed from `knowledge_notes` to `obsidian_notes`. |
| 5 | **`EMBEDDING_URL` default pointed at a nonexistent endpoint.** `daemon/refine_daemon.py` and `.env.example` default to `http://127.0.0.1:8000/embed`, but the rag_server only exposes `/v1/embeddings`. First daemon embed call on default settings returns 404. | Default changed to `http://127.0.0.1:8000/v1/embeddings` in both places. `daemon/README.md` updated to match. |
| 6 | **`refine_status` curl example used wrong query parameter.** `docs/DEPLOYMENT.md` Step 7 and `docs/FILTER_BADGE_REFERENCE.md` § 9 both gave `?conversation_id=<uuid>`, but the endpoint expects `?conv_id=<uuid>`. | Both docs now say `?conv_id=`. |
| 7 | **Valve name drift.** `docs/FILTER_BADGE_REFERENCE.md` referenced `DAEMON_REFINE_URL` in three places (§ 9 prose, states table, § FAQ), but the actual Filter valve is `REFINE_STATUS_URL`. Same drift the previous audit fixed in `DEPLOYMENT.md`; this doc was missed. | All three references renamed. |
| 8 | **Pack-detection order was wrong in ARCHITECTURE.md.** §4 listed `marker → topic_pin → source_model → route_hint`, but `PackRegistry.detect()` runs `prefix → source_model → topic_pin → route_prefix`. Positions 2 and 3 swapped. | Corrected to match code, with a one-sentence rationale on why the ordering is explicit-marker > model-preset > keyword > routing-target. |
| 9 | **Inconsistent example path.** `scripts/README.md` gave `INGEST_EXTRA_WHITELIST='["00_Inbox/overview"]'` as the example; `docs/DEPLOYMENT.md` Step 6 gave `'["00_Buffer/00.00_Overview"]'`. Neither is wrong but the mismatch forces the reader to guess which is canonical. | Unified on `00_Buffer/00.00_Overview` (the form `ARCHITECTURE.md § 6` discusses). |
| 10 | **Daemon README model defaults were under-specified.** `Sonnet 4.6` and `Haiku 4.5 / Gemini 3 Flash` are friendly names, but the env vars take OpenRouter IDs. A user setting `REFINE_MODEL=Sonnet 4.6` gets a 400. | Spelled out full OpenRouter IDs (`anthropic/claude-sonnet-4.6`, etc.). |

Triaged as non-issue:
- `prompts/README.md` "community translations" line was flagged for not
  warning that PRs must also touch the hardcoded Python strings. The
  README already covers this in its opening paragraph (line 3) and
  explicitly calls runtime-switching a "v2 feature" (line 18). Adding
  more friction to the invitation would discourage the contributions
  the system actually wants.

### Known deferrable rough edges (not blockers)

- **Two env vars for one concept.** `VAULT_PATH` (used by `ingest_qdrant.py`)
  and `THROUGHLINE_VAULT_ROOT` (used by the daemon) refer to the same
  thing. The `.env.example` correctly defines both, and Step 1 tells the
  user to set both, so this works — but it is a smell. Future cleanup:
  unify under `THROUGHLINE_VAULT_ROOT` and have `ingest_qdrant.py`
  accept either.

- **Windows runtime not supported.** `DEPLOYMENT.md § Platform notes` is
  explicit: Windows is supported for *development* and *ingest* only.
  The daemon and RAG server expect macOS or Linux. If an alpha user
  tries on Windows Server, they will hit filesystem-path issues that
  are not in scope for v0.1.0.

- **`filter/README.md § 3` and `§ 4`** are referenced from
  `DEPLOYMENT.md § Step 5`. Both sections exist (confirmed: § 3
  "Installation", § 4 "Valves reference"). No action required.

- **bge-m3 / bge-reranker model download** (~5 GB total) blocks first
  RAG-server start for 2-10 minutes. Documented, but a CPU-only / slow-
  connection user might think the server is hung. Consider adding a
  progress log or a preflight `huggingface-cli download` step in a
  future revision.

- **No CI yet.** Phase 6 regression (`pytest fixtures/phase6/`) runs
  green locally but there is no GitHub Actions workflow. Planned for
  v0.3.0 per the release notes.

### Not audited (requires live environment)

The static audit cannot verify:

- Actual OpenWebUI 0.8.12 compatibility with the pasted Filter
  function (Valves registration, REST API push, etc.). This is the
  single biggest unknown for alpha users on fresh OpenWebUI installs.
- `curl http://localhost:8000/health` end-to-end.
- The Qdrant Docker command on Podman / rootless Docker.
- First-run bge-m3 model download on a machine without prior HF cache.

These are exactly the things the next alpha user will surface. When they
do, add the findings below as new subsections.

---

## v0.2.0 update (2026-04-24)

Resolved rough edges that were on the "deferrable" list in the
v0.1.0 audit:

- **"Windows runtime not supported"** → **Windows runtime works.**
  Wizard, adapters, daemon, rag_server, `doctor`, and the full test
  suite all run on Windows 10/11. Path normalisation was the
  blocker; `_norm_path` + the `test_m4_point_id` invariant
  guarantees cross-platform point-id determinism. Platform notes in
  `DEPLOYMENT.md` updated accordingly.
- **"bge-m3 / bge-reranker model download blocks first start"** →
  **mitigated by U6 pre-flight section.** `DEPLOYMENT.md` now leads
  with a `huggingface-cli download` step so the 4.6 GB download
  happens once up front, and `throughline_cli doctor` includes an
  `embedder_model_cache` check so users know which state they're in.
- **"No CI yet"** → **CI shipped.** GitHub Actions runs pytest on
  Python 3.11 + 3.12, ruff lint (F + E9), and CodeQL weekly, all
  required by branch protection before merge to `main`. Green
  badge on README.

Still valid / still deferrable:

- **Two env vars for one concept** (`VAULT_PATH` vs
  `THROUGHLINE_VAULT_ROOT`). Still a smell. v0.3 candidate.
- **OpenWebUI Filter installation** still a manual copy-paste into
  the Admin → Functions UI. Could be scripted via REST, but
  OpenWebUI's Functions API is not stable enough yet to commit to.
  The seeded issue [#7 Docker compose for one-command try-it-out]
  will change this for the evaluation path.

New rough edges surfaced by the v0.2.0 UX audit (2026-04-24):

| # | Issue | Status |
|---|---|---|
| 11 | Silent LLM charge at wizard step 13 (~$0.01 without consent) | Fixed in `bf71d3f` — explicit `ask_yes_no` cost preflight. |
| 12 | Wizard exit with no "what to do next" guidance | Fixed in `dabcaa9` — end-of-flow panel prints mission-tailored next steps. |
| 13 | User without an existing Claude/ChatGPT/Gemini export cannot evaluate the loop | Fixed in `0c7e1c8` — `python -m throughline_cli import sample` bundles 10 synthetic conversations. |
| 14 | `VAULT_PATH` missing → `sys.exit(2)` without remediation hint | Fixed in `f2d600a` — error messages now enumerate the fix (bash + PowerShell forms) and reference the wizard. |
| 15 | No one-shot way to tell "is my install working?" | Fixed in `dabcaa9` — `python -m throughline_cli doctor` runs 10 checks with ✓/!/✗ + remediation. |

---

## External alpha reports

*(empty — first alpha user will fill in here)*
