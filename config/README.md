# Config

This directory holds **example / template** configuration a fork or a new install needs to customize. Every file here either ships as a template (`*.example.*` / `*.plist` / `*.service`) or as a runtime-loaded JSON config referenced by an environment variable. Nothing in this directory is imported automatically by the daemon, RAG server, or Filter unless you explicitly point an env var at it.

## Files

| File | Purpose | Consumed by |
|---|---|---|
| `.env.example` | Full env-var reference for all three services. **Copy to `.env` and edit first.** | Services are started by your process manager with these env vars set. |
| `forbidden_prefixes.example.json` | Optional JSON list of vault-relative path prefixes that must never be upserted to the default Qdrant collection. | `daemon/refine_daemon.py` via `THROUGHLINE_FORBIDDEN_PREFIXES_JSON`. |
| `taxonomy.example.py` | Example XYZ + Johnny-Decimal tree. Rename to `taxonomy.py` to override the bundled default. | `daemon/refine_daemon.py :: _load_taxonomy()`. |
| `contexts_topics.example.json` | Example config for the Personal Context auto-builder (Filter's L1 context cards). Copy into your vault and point the builder at it. | Context auto-builder, which writes cards to be consumed by `filter/openwebui_filter.py`'s `CONTEXT_CARDS` valve. |
| `launchd/*.plist` | macOS launchd service templates (4 files). | `launchctl bootstrap` by the operator. |
| `systemd/*.service` | Linux systemd **user**-unit templates (2 files). | `systemctl --user enable --now` by the operator. |

## Editing order for a new fork

1. **Start with `.env.example`.** Copy to `.env` and fill in at least `OPENROUTER_API_KEY`, `THROUGHLINE_VAULT_ROOT`, `THROUGHLINE_RAW_ROOT`. Everything else has sensible defaults.
2. **Decide on a service manager.** macOS -> `launchd/*.plist`. Linux -> `systemd/*.service`. Both template sets expect the same env-var names the daemon reads; the only difference is how they are passed in.
3. **Optional: `forbidden_prefixes.example.json`.** Only needed if you have subtrees you do NOT want indexed into the default Qdrant collection. Copy to `forbidden_prefixes.json` and edit.
4. **Optional: `taxonomy.example.py`.** Only needed if your vault layout differs from the bundled JD tree. Copy to `taxonomy.py`. See the commentary inside the file for which fields are safe to change.
5. **Optional: `contexts_topics.example.json`.** Only needed if you want the Filter to inject per-topic personal context cards into the LLM prompt. Copy into `<vault>/00_Buffer/00.05_Profile/contexts_config.json` (or wherever your auto-builder expects it) and edit.

## Prompts

Prompt templates live in a sibling directory, **not** in `config/`. See [`../prompts/README.md`](../prompts/README.md) for the rationale and file inventory.

## Do not commit filled-in templates

Every `launchd/*.plist` and every `systemd/*.service` here has `{{PLACEHOLDER}}` tokens for your username, install path, and (in the refine-daemon plist) an optional slot for `OPENROUTER_API_KEY`. Once you fill those in, the resulting file is *yours* and should not go back into source control. The templates are deliberately marked with `com.example.` / un-templated paths so it is obvious they are not meant to run as-is.

## Secrets

- `OPENROUTER_API_KEY` is the only secret the daemon needs.
- On Linux, the systemd template reads it from a separate `EnvironmentFile=` — keep that file `chmod 600`.
- On macOS, the launchd template shows a slot for the key inside `EnvironmentVariables`. If you are on a multi-user host, prefer a wrapper script that `source`s a `chmod 600` file and execs the daemon, rather than embedding the key in the plist.
- The Filter auto-push plist (`filter-autopush.plist`) reads an OpenWebUI JWT from `~/.config/throughline/openwebui_token` — keep that file `chmod 600` as well.

## Linux note on the RAG server

The `systemd/throughline-rag-server.service` template sets `RAG_DEVICE=auto`, which on Linux falls back to CUDA if available, else CPU. The reranker's default batch size (100) was tuned for Apple MPS / CUDA; if you are on a CPU-only host and cold-start is slow, export `RAG_RERANK_BATCH_SIZE=16` or similar.
