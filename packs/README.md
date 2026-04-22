# Packs

A **pack** is a domain-specific override bundle: it swaps out the slicer
prompt, the refiner prompt, and the routing base path, and can set
`knowledge_identity` and dedup policies. Use packs when a class of
conversations has its own vocabulary or card shape (e.g. exam prep, lab
notebooks, clinical notes).

## Layout

Each pack lives under `packs/<name>/` with:

```
packs/<name>/
├── pack.yaml      # trigger + routing + policies
├── slicer.md      # system prompt for the slicer stage
├── refiner.md     # system prompt for the refiner stage
└── skeleton.md    # (optional) body template the refiner reference
```

## Example: PTE pack

`packs/pte/` is a full working example. Its `pack.yaml` triggers on the
`pte` source_model, routes cards under
`40_Cognition_PKM/40.03_Learning/40.03.04_PTE/`, and preserves verbatim
prompt + reference answer in the card body (needed for memorising high-
scoring templates).

## `pack.yaml` schema

```yaml
name: pte
description: PTE exam prep
priority: 10

trigger:
  # Any of these matches -> pack fires. Precedence:
  # prefix > source_model > topic_pin > route_prefix.
  prefixes: ["[PTE]"]
  source_models: ["pte"]
  topic_pins: []
  route_prefix: ""

routing:
  base_path: "40_Cognition_PKM/40.03_Learning/40.03.04_PTE"
  # Optional: per-pack_meta.exam_type subdir.
  by_exam_type:
    DI: Speaking/DI
    SWT: Writing/SWT
    WFD: Listening/WFD

policies:
  ki_force: universal               # universal | personal_persistent | personal_ephemeral | contextual | null
  dedup_enabled: false              # skip the Qdrant cosine dedup check
  provenance_filter_enabled: false  # do not drop llm_unverified claims
  qdrant_collection: ""             # "" = use default collection
  qdrant_skip_default: false        # true = do not write to the default collection at all
```

## Detection precedence

`PackRegistry.detect()` matches in this order:

1. **prefix** — any pack whose `trigger.prefixes` appears in the raw
   conversation text.
2. **source_model** — frontmatter `source_model` field equals any
   `trigger.source_models`.
3. **topic_pin** — a topic hint passed in by the caller (e.g. from a
   heuristic topic router upstream).
4. **route_prefix** — last-ditch: the raw MD's `route_to` frontmatter
   starts with this.

The first rule that matches wins; ties break by `priority:` (higher first).

## Hot-reload

`PackRegistry` watches `pack.yaml` / `slicer.md` / `refiner.md` mtimes and
reloads on the next tick. You can edit a pack's prompts while the daemon
is running; the next conversation picks up the change.

## Writing your own pack

1. Copy `packs/pte/` to `packs/<your_pack_name>/`.
2. Edit `pack.yaml` — change `name`, `trigger.*`, `routing.base_path`.
3. Edit `slicer.md` — the rules for how to split conversations in your
   domain. Keep the `<output_schema>` block unchanged so the daemon's
   `dispatch_slicer` can parse the output.
4. Edit `refiner.md` — domain-specific card shape. Keep the JSON schema
   fields required by `RefinedResult` (title, primary_x, visible_x_tags,
   form_y, z_axis, knowledge_identity, body_markdown, claim_sources,
   pack_meta). Extra fields go into `pack_meta`.
5. Restart the daemon (or wait for the next mtime poll).

## Testing a pack

The quickest sanity check is to drop a hand-crafted raw MD into
`THROUGHLINE_RAW_ROOT` with the right `source_model` or prefix, then watch
`refine_daemon.log`:

```
PACK_MATCHED | conv=abcd1234 | pack=pte
WRITTEN | conv=abcd1234 | title=DI: Population chart | route=40_Cognition_PKM/40.03_Learning/40.03.04_PTE/Speaking/DI
```
