# Prompts

This directory contains the **canonical English prompts** used by the Throughline pipeline. The files here are a **documentation and review surface**, not a runtime loader: the prompts remain hardcoded inside the Python source for performance and packaging reasons. If you edit a file here, you will also need to edit the matching string in the Python source listed under `**Used by:**`.

## Layout

- `en/` — English prompts, shipped by default. These mirror the strings hardcoded in `filter/openwebui_filter.py` and `daemon/refine_daemon.py` verbatim.
- `zh/` — Chinese prompts. Intentionally empty in the open-source tree. The upstream private codebase was Chinese-first; the translations that ship here are in `en/`. Community translations are welcome via PR — open a PR adding a `zh/<name>.md` (or `fr/`, `ja/`, etc.) that matches the structure under `en/`.

## Why prompts are NOT loaded from disk at runtime

Three reasons:

1. **No surprise filesystem dependency.** Both the Filter (runs inside OpenWebUI's Functions sandbox) and the daemon (runs as a launchd / systemd service) should be self-contained. A missing prompt file at startup would be a silent outage.
2. **Performance.** System prompts are concatenated once per LLM call. Re-reading them from disk per call would be wasteful; caching them would re-introduce the same hardcoding in memory.
3. **Packaging.** Shipping the Filter as a single-file OpenWebUI Function is a hard requirement — it is uploaded through the Admin Panel or pushed via the `/api/v1/functions` REST endpoint. A multi-file prompt tree would require bundling, which is out of scope for v1.

If you want runtime-switchable prompts (e.g., via a `PROMPT_LANG` valve), see the backlog entry in `docs/OPENSOURCE_NOTES.md` — this is a v2 feature.

## File structure

Each `en/*.md` file follows the same header shape so you can diff them against the hardcoded strings:

```
# <Prompt name>

**Used by:** `<path/to/file.py>` :: `<symbol>`
**Model:** `<default model>`
**Inputs:** `<placeholder1>`, `<placeholder2>`

---

<prompt body verbatim>

---

**Notes:**
- <any non-obvious behavior>
```

The prompt body between the `---` markers is the **literal** string used at runtime. If it ever drifts from the hardcoded Python string, the hardcoded Python string is authoritative — please file an issue so the markdown can catch up.

## File inventory

| File | Role | Called from |
|---|---|---|
| `en/recall_judge.md` | Decide `needs_rag` / `mode` / `aggregate` / `topic_shift` / `reformulated_query` per user turn | Filter inlet |
| `en/slice.md` | Carve a raw conversation into coherent knowledge slices | Daemon SLICE stage |
| `en/refine.md` | Turn one slice into a six-section knowledge card (JSON) | Daemon REFINE stage |
| `en/route_domain.md` | Pick one top-level JD domain (10–90) for a refined card | Daemon DOMAIN stage |
| `en/route_subpath.md` | Pick a leaf subpath under a chosen domain; fallback-aware | Daemon SUBPATH stage |
| `en/ephemeral_judge.md` | Decide whether a short message is worth refining at all | Daemon pre-SLICE gate |
| `en/extension_judge.md` | Decide whether newly-appended messages are worth a re-refine | Daemon ExtensionGuard |
| `en/echo_judge.md` | Decide whether a slice is substantively new vs. an echo of top-1 | Daemon EchoGuard (grey zone) |

## Customising prompts without forking

The intended v1 path is:

1. Fork the repo.
2. Edit the matching hardcoded string in the `.py` file.
3. Run the existing tests (Phase 6 regression fixtures) to confirm schema parity.

Do **not** silently tweak tone while preserving the schema — many downstream validators (card retention gate, cost gate, confidence tier badges) assume specific fields and confidence ranges. See each prompt's `**Notes:**` for the non-negotiable fields.
