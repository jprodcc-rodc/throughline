"""Pack source_model guard — standalone opt-out / routing hints from the OpenWebUI model id.

Architecture constraints:
- Does NOT modify the daemon core. The daemon soft-imports this module at
  startup; if the import fails, daemon behavior is unchanged.
- Pure stdlib. Loads rules from `pack_source_model_config.json` next to this
  file; falls back to built-in defaults if no config file is present.
- Returns a verdict dict. The daemon decides whether to honor `skip` (abort
  refine), `force_ki` (override knowledge_identity), or `pack_hint` (seed
  PackRegistry).

Soft-import pattern for the daemon core (3 lines, one call site):

    try:
        from daemon.pack_source_model_guard import evaluate_source_model
    except Exception:
        evaluate_source_model = None

    # early in process_raw_file, right after parsing frontmatter:
    if evaluate_source_model is not None:
        v = evaluate_source_model(conv.source_model, conv.title)
        if v["action"] == "skip":
            log(f"SOURCE_MODEL_OPTOUT reason={v['reason']} model={conv.source_model}")
            return  # abort before SLICE/REFINE

Config schema (`pack_source_model_config.json`):

    {
      "rules": [
        {
          "pattern": "pte",                 # required
          "match": "contains",              # contains | equals | regex | prefix | suffix
          "case_sensitive": false,          # optional, default false
          "action": "allow",                # skip | allow | force_ki
          "ki_value": "personal_persistent",  # only if action=force_ki
          "pack_hint": "pte",               # optional — PackRegistry seed hint
          "reason": "route through PTE pack"
        }
      ],
      "default_action": "allow",            # fallback when no rule matches
      "default_reason": "no rule matched"
    }

Contract — `evaluate_source_model(source_model, title=None)` returns:

    {
      "action": "allow" | "skip" | "force_ki",
      "reason": str,
      "ki_value": str | None,
      "pack_hint": str | None,
      "matched_rule": int | None,   # index in rules list; None if default
      "source_model": str            # echoed back, normalized (lowercase strip)
    }

The guard is deterministic and cheap (regex compile cached per rule).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent
_DEFAULT_CONFIG_NAME = "pack_source_model_config.json"

# Built-in defaults ship with a single illustrative rule for the PTE example
# pack. End users can drop a `pack_source_model_config.json` next to this
# file to define their own source_model → pack routing or opt-out rules.
_BUILTIN_DEFAULTS = {
    "rules": [
        {
            "pattern": "pte",
            "match": "contains",
            "case_sensitive": False,
            "action": "allow",
            "pack_hint": "pte",
            "reason": "PTE preset model: route through PTE pack",
        },
    ],
    "default_action": "allow",
    "default_reason": "no opt-out rule matched",
}


class GuardConfigError(ValueError):
    pass


def _compile_rule(rule: dict, idx: int):
    """Validate and precompile a single rule. Returns a matcher callable(text)->bool."""
    if not isinstance(rule, dict):
        raise GuardConfigError(f"rule[{idx}] must be dict, got {type(rule).__name__}")
    pattern = rule.get("pattern")
    if not isinstance(pattern, str) or not pattern:
        raise GuardConfigError(f"rule[{idx}].pattern must be non-empty str")
    mode = rule.get("match", "contains")
    if mode not in {"contains", "equals", "regex", "prefix", "suffix"}:
        raise GuardConfigError(f"rule[{idx}].match={mode!r} invalid")
    action = rule.get("action", "allow")
    if action not in {"allow", "skip", "force_ki"}:
        raise GuardConfigError(f"rule[{idx}].action={action!r} invalid")
    if action == "force_ki":
        ki = rule.get("ki_value")
        if ki not in {"universal", "personal_persistent", "personal_ephemeral", "contextual"}:
            raise GuardConfigError(f"rule[{idx}].ki_value={ki!r} invalid for force_ki")
    cs = bool(rule.get("case_sensitive", False))

    if mode == "regex":
        flags = 0 if cs else re.IGNORECASE
        try:
            rx = re.compile(pattern, flags)
        except re.error as e:
            raise GuardConfigError(f"rule[{idx}].pattern regex invalid: {e}")
        return lambda txt: bool(rx.search(txt or ""))

    if cs:
        needle = pattern
        hay = lambda txt: txt or ""
    else:
        needle = pattern.lower()
        hay = lambda txt: (txt or "").lower()

    if mode == "contains":
        return lambda txt: needle in hay(txt)
    if mode == "equals":
        return lambda txt: hay(txt) == needle
    if mode == "prefix":
        return lambda txt: hay(txt).startswith(needle)
    if mode == "suffix":
        return lambda txt: hay(txt).endswith(needle)
    raise GuardConfigError(f"rule[{idx}] unreachable mode={mode}")


class SourceModelGuard:
    """Loads and evaluates rules. Cache-safe; instantiate once per daemon run."""

    def __init__(self, config_path: Optional[Path] = None, config_dict: Optional[dict] = None):
        if config_dict is not None:
            cfg = config_dict
            source = "inline"
        else:
            path = config_path or (_HERE / _DEFAULT_CONFIG_NAME)
            if path.is_file():
                try:
                    cfg = json.loads(path.read_text(encoding="utf-8"))
                    source = str(path)
                except Exception as e:
                    raise GuardConfigError(f"config parse {path}: {e}")
            else:
                cfg = _BUILTIN_DEFAULTS
                source = "<builtin-defaults>"

        if not isinstance(cfg, dict):
            raise GuardConfigError(f"config root must be object, got {type(cfg).__name__}")

        rules = cfg.get("rules", [])
        if not isinstance(rules, list):
            raise GuardConfigError("config.rules must be list")

        self._compiled = []
        for i, r in enumerate(rules):
            matcher = _compile_rule(r, i)
            self._compiled.append((i, r, matcher))

        self._default_action = cfg.get("default_action", "allow")
        if self._default_action not in {"allow", "skip", "force_ki"}:
            raise GuardConfigError(f"default_action={self._default_action!r} invalid")
        self._default_reason = cfg.get("default_reason", "no rule matched")
        self.source = source
        self.rules_count = len(self._compiled)

    def evaluate(self, source_model: Optional[str], title: Optional[str] = None) -> dict:
        # Defensive coerce: frontmatter YAML can occasionally surface non-str
        # types (int "4" → 4, bool "yes" → True, list for multi-value). Never crash.
        sm = str(source_model).strip() if source_model is not None and not isinstance(source_model, bool) else ""
        tl = str(title).strip() if title is not None and not isinstance(title, bool) else ""
        for idx, rule, matcher in self._compiled:
            if matcher(sm) or (tl and matcher(tl)):
                return {
                    "action": rule.get("action", "allow"),
                    "reason": rule.get("reason", f"matched rule[{idx}]"),
                    "ki_value": rule.get("ki_value"),
                    "pack_hint": rule.get("pack_hint"),
                    "matched_rule": idx,
                    "source_model": sm,
                }
        return {
            "action": self._default_action,
            "reason": self._default_reason,
            "ki_value": None,
            "pack_hint": None,
            "matched_rule": None,
            "source_model": sm,
        }


_SINGLETON: Optional[SourceModelGuard] = None


def _get_default() -> SourceModelGuard:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = SourceModelGuard()
    return _SINGLETON


def evaluate_source_model(source_model: Optional[str], title: Optional[str] = None) -> dict:
    """Convenience entry point for daemon soft-import.

    Reloads config if the file mtime changes between calls (cheap mtime check).
    """
    g = _get_default()
    cfg = _HERE / _DEFAULT_CONFIG_NAME
    if cfg.is_file():
        try:
            mtime = cfg.stat().st_mtime
        except OSError:
            mtime = None
        if mtime is not None and mtime != getattr(g, "_cfg_mtime", None):
            new_g = SourceModelGuard(config_path=cfg)
            new_g._cfg_mtime = mtime
            globals()["_SINGLETON"] = new_g
            g = new_g
    return g.evaluate(source_model, title)


def _cli():
    import argparse
    import sys
    ap = argparse.ArgumentParser(description="pack_source_model_guard dry-run")
    ap.add_argument("source_model", nargs="?", default="", help="source_model id to test")
    ap.add_argument("--title", default=None)
    ap.add_argument("--config", default=None, help="path to config json")
    ap.add_argument("--dump-defaults", action="store_true", help="print built-in default config + exit")
    args = ap.parse_args()

    if args.dump_defaults:
        print(json.dumps(_BUILTIN_DEFAULTS, indent=2, ensure_ascii=False))
        return 0

    g = SourceModelGuard(config_path=Path(args.config) if args.config else None)
    v = g.evaluate(args.source_model, args.title)
    print(json.dumps(v, indent=2, ensure_ascii=False))
    print(f"\n# config source: {g.source}", file=sys.stderr)
    print(f"# rules loaded: {g.rules_count}", file=sys.stderr)
    return 0 if v["action"] != "skip" else 2


if __name__ == "__main__":
    import sys
    try:
        sys.exit(_cli())
    except GuardConfigError as e:
        print(
            f"CONFIG ERROR: {e}\n"
            f"  → Pack source-model guard configuration is malformed.\n"
            f"    Check the YAML syntax of any pack file under `packs/`\n"
            f"    that defines `source_model:` rules. The daemon will\n"
            f"    still run with this guard disabled; the CLI is just\n"
            f"    refusing to evaluate against an invalid config.",
            file=sys.stderr,
        )
        sys.exit(3)
