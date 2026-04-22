# Scripts

Operational scripts for Throughline. Run them against a live RAG server
(`../rag_server/rag_server.py`) and Qdrant instance.

## Catalog

| Script | Purpose |
|---|---|
| `ingest_qdrant.py` | One-shot vault -> Qdrant ingest. Embeds every Markdown note via `bge-m3` and upserts one point per note. |

---

## `ingest_qdrant.py`

Walks a vault, reads frontmatter (title / knowledge_identity / date / tags) +
body of every `.md` file, embeds the first ~2000 chars with bge-m3, and
upserts a single point per note into the configured Qdrant collection.

### Usage

```bash
export VAULT_PATH=/absolute/path/to/your/vault
export RAG_EMBED_URL=http://localhost:8000/v1     # rag_server's base
export QDRANT_URL=http://localhost:6333
export RAG_COLLECTION=obsidian_notes              # optional, default shown
python ingest_qdrant.py
```

The script is **idempotent**: re-running it refreshes every note in place
(point IDs are content-path-derived md5 hashes, so new content simply
overwrites the old vector and payload).

### Scanning rules

By default the script only walks folders whose name matches the
Johnny-Decimal convention `[1-9]0_*` (e.g. `10_Tech`, `20_Health`,
`90_Archive`). Everything else at the vault root — inboxes, buffer
folders, private profile folders — is ignored so that raw or sensitive
content never ends up in the RAG index.

Override via env vars:

| Variable | Default | Purpose |
|---|---|---|
| `VAULT_PATH` | (required) | Absolute path to vault root |
| `RAG_EMBED_URL` | `http://localhost:8000/v1` | OpenAI-compatible embedding endpoint |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant HTTP endpoint |
| `RAG_COLLECTION` | `obsidian_notes` | Qdrant collection name |
| `INGEST_VECTOR_SIZE` | `1024` | Dimension of the embedding |
| `INGEST_BATCH_SIZE` | `20` | Embedding + upsert batch size |
| `INGEST_INCLUDE` | `["re:^[1-9]0_"]` | JSON list of top-level folder patterns to scan. Prefix `re:` for regex; anything else is an exact folder name. |
| `INGEST_EXTRA_WHITELIST` | `[]` | JSON list of extra relative paths inside the vault to also scan. Useful for opting in a specific overview / dashboard folder. |

Example — scan the default JD folders plus a curated overview subfolder:

```bash
export INGEST_EXTRA_WHITELIST='["00_Inbox/overview"]'
```

### Windows / Mac / Linux gotcha — forward-slash normalisation

> **This is the single most important correctness fix in the ingest path.**

Point IDs are derived from the note's relative path via md5. On Windows the
native separator is `\`; on macOS/Linux it is `/`. If you ingest the same
vault from both platforms without normalising, you produce **two** point IDs
per note and end up with a duplicated collection.

The script always normalises with `.replace(os.sep, "/")` before hashing and
before writing the `path` payload field. **Preserve this behaviour if you
modify the script.** See `_norm_path()` and `make_point_id()` in
`ingest_qdrant.py`.

Symptom if the normalisation regresses: collection point count is ~2x the
expected note count, and the same note retrieves twice per query.

### Frontmatter expected

```yaml
---
title: "Short descriptive name"
knowledge_identity: universal          # or personal_persistent / personal_ephemeral / contextual
date: 2026-04-21 12:34                  # or 2026-04-21
tags:
  - some/tag
  - another/tag
---
```

All frontmatter fields are optional; missing values default sensibly
(`title` falls back to the filename, `knowledge_identity` defaults to
`universal`, etc.). The body below the frontmatter is truncated to 20k
characters for `body_full` and 500 characters for `body_preview`.

Files encoded with a UTF-8 BOM are handled transparently (`utf-8-sig`).
