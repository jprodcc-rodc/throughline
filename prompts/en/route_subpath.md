# Subpath Router Prompt

**Used by:** `daemon/refine_daemon.py` :: `SUBPATH_PROMPT_TEMPLATE` (formatted at call time with the chosen `domain`, the list of `allowed_leaves`, and the domain's configured `fallback` leaf).
**Model:** `anthropic/claude-sonnet-4.6` (env `REFINE_ROUTE_MODEL`; temperature ~0, `response_format={"type":"json_object"}`)
**Inputs:**
- `{domain}` — the top-level domain chosen by `route_domain.md` (e.g. `40_Cognition_PKM`).
- `{allowed_leaves}` — newline-joined list of valid leaf paths from `daemon/taxonomy.py :: LEGAL_LEAVES` filtered to the chosen domain.
- `{fallback}` — the fallback path for this domain (usually `<domain>/System_Inbox/`).

The doubled braces `{{` and `}}` below are literal `{` and `}` after `.format(...)`.

---

```
<task>
Pick exactly one leaf subpath under domain `{domain}` for the card below.
</task>

<allowed_leaves>
{allowed_leaves}
</allowed_leaves>

<priority_boundaries>
- Follow the card's primary_x and body headings to disambiguate.
- If truly nothing fits, return the fallback path provided in `fallback_path` (not an error).
</priority_boundaries>

<output_schema>
Emit JSON only:
{{"subpath": "40_Cognition_PKM/40.03_Learning/40.03.04_PTE", "reason": "<<= 60 chars>", "fallback_path": "{fallback}"}}

If no leaf fits, set `subpath` equal to `fallback_path` and put the reason in `reason`.
</output_schema>
```

---

**Notes:**

- **Bug #2 fallback semantics** are preserved here. The previous behaviour (raise when no leaf matches) caused the daemon to crash on cards that genuinely did not fit any pre-existing leaf. The new contract is: **return `subpath == fallback_path`** and the daemon routes the card to the domain's `System_Inbox`, to be triaged by the user later. The daemon-side validator (`daemon/refine_daemon.py :: _validate_route`) accepts `subpath == fallback_path` without raising.
- The **`allowed_leaves` list is authoritative**. The LLM is not allowed to invent a new leaf. If `subpath` is not a member of `allowed_leaves` AND not equal to `fallback_path`, the validator raises and the daemon retries the call once, then gives up and writes the card into the buffer stub path with `triage_status=pending`.
- **Why `fallback_path` is repeated inside the output schema:** we want the LLM to explicitly *choose* the fallback, not silently drop to it. Making it a named field in the JSON means the LLM has to think about it.
- If you add a new leaf in `daemon/taxonomy.py :: LEGAL_LEAVES`, it becomes available to the router automatically — no prompt change needed.
- `reason` is logged; the dashboard (`00.02.04_Refine_Processing_Index.md`) renders it next to the routed card. Keep it under 60 chars.
