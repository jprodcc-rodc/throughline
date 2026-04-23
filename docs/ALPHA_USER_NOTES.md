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

## External alpha reports

*(empty — first alpha user will fill in here)*
