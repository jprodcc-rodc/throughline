"""Pack loader and registry for the refine daemon.

A "pack" is a pluggable per-domain override bundle. Each pack contributes its
own slicer / refiner / skeleton prompts plus routing rules and policies. The
daemon core stays domain-agnostic; packs supply the domain knowledge.

Pack YAML schema (fields marked * are required):

    name*: str                      # must match directory name
    version: int = 1

    trigger:
      prefixes: [str]               # e.g. ['@pte', '@PTE']. Strict word-boundary match
                                    # against ANY user message.
      source_models: [str]          # e.g. ['pte']. Case-insensitive substring match
                                    # against conv.source_model.
      topic_pins: [str]             # keywords. Case-insensitive word-boundary match
                                    # against ANY user message.
      route_prefix: str             # JD path prefix (forward slashes). Post-hoc match:
                                    # fires when the daemon routes into this subtree.

    prompts:
      slicer: slicer.md             # relative path inside pack dir
      refiner: refiner.md
      skeleton: skeleton.md

    routing:
      base_path*: str               # JD vault path (forward slashes)
      by_exam_type: {str: str}      # exam_type -> subdir under base_path
      default_subdir: str = _Unsorted

    policies:
      ki_force: null | str          # 'universal' | 'personal_persistent' |
                                    # 'personal_ephemeral' | 'contextual' | null
      dedup_enabled: bool = true
      provenance_filter_enabled: bool = true
      skip_refine: bool = false     # opt-out: archive the raw file, skip slice/refine
                                    # (reserved for future archive-only packs)
      qdrant_collection: str = obsidian_notes   # write destination collection
      qdrant_skip_default: bool = false          # safety belt: hard-reject writes to
                                                 # default collection even if
                                                 # qdrant_collection is misconfigured

    assets:
      save_originals: bool = false          # copy `files` array from raw MD to vault
      dest_subdir: str = images             # relative to routing.base_path
      for_exam_types: null | [str]          # null = all; list restricts to these exam_types
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class PackSpecError(ValueError):
    """Raised when a pack.yaml is malformed."""


_PROMPT_FILES = ("slicer", "refiner", "skeleton")


def _strict_prefix_regex(prefix: str) -> re.Pattern:
    """Regex that matches `prefix` only at a command-invocation position.

    `@pte` matches `@pte foo` and `\\n@pte` but not `@ptextual` or `foo@pte`.
    Leading: start-of-string or whitespace (prefixes are commands, not inline tokens).
    Trailing: end-of-string, whitespace, or ASCII non-word char.
    """
    return re.compile(
        r"(?:^|\s)" + re.escape(prefix) + r"(?=$|\s|[^A-Za-z0-9_])",
        flags=re.IGNORECASE,
    )


def _word_boundary_regex(token: str) -> re.Pattern:
    """Regex that matches `token` only when flanked by non-ASCII-word chars.

    Designed to fire cleanly inside multilingual text: adjacent non-ASCII
    characters (CJK, Cyrillic, etc.) count as word boundaries because they are
    not in the ASCII `[A-Za-z0-9_]` class, while an ASCII letter immediately
    after the token blocks the match (so `@ptextual` does not match `pte`).
    """
    return re.compile(
        r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])",
        flags=re.IGNORECASE,
    )


@dataclass
class Pack:
    name: str
    version: int
    path: Path
    trigger: Dict[str, Any]
    prompts: Dict[str, str]          # name -> resolved prompt text ("" if unspecified)
    routing: Dict[str, Any]
    policies: Dict[str, Any]
    assets: Dict[str, Any]

    # Precomputed for detect()
    _prefix_patterns: List[re.Pattern] = field(default_factory=list, repr=False)
    _source_model_patterns: List[str] = field(default_factory=list, repr=False)  # lowercase substrings
    _topic_pin_patterns: List[re.Pattern] = field(default_factory=list, repr=False)
    _route_prefix_norm: str = field(default="", repr=False)

    # Staleness tracking (mtime snapshot taken at load time).
    _mtimes: Dict[str, float] = field(default_factory=dict, repr=False)

    # --- match helpers ---

    def matches_prefix(self, messages) -> bool:
        if not self._prefix_patterns:
            return False
        for msg in messages:
            if getattr(msg, "role", None) != "user":
                continue
            content = getattr(msg, "content", "") or ""
            for pat in self._prefix_patterns:
                if pat.search(content):
                    return True
        return False

    def matches_topic_pin(self, messages) -> bool:
        if not self._topic_pin_patterns:
            return False
        for msg in messages:
            if getattr(msg, "role", None) != "user":
                continue
            content = getattr(msg, "content", "") or ""
            for pat in self._topic_pin_patterns:
                if pat.search(content):
                    return True
        return False

    def matches_source_model(self, source_model) -> bool:
        """Case-insensitive substring match against conv.source_model.

        Designed for presets where the model id itself declares the pack intent
        (e.g. OpenWebUI "PTE" preset → source_model contains 'pte').
        Defensive coerce handles YAML frontmatter surfacing non-str values.
        """
        if not self._source_model_patterns:
            return False
        if source_model is None or isinstance(source_model, bool):
            return False
        try:
            hay = str(source_model).lower()
        except Exception:
            return False
        if not hay:
            return False
        for needle in self._source_model_patterns:
            if needle in hay:
                return True
        return False

    def matches_route_prefix(self, route_to: Optional[str]) -> bool:
        if not self._route_prefix_norm or not route_to:
            return False
        norm = route_to.replace("\\", "/").strip("/")
        return norm == self._route_prefix_norm or norm.startswith(self._route_prefix_norm + "/")

    # --- routing ---

    def resolve_routing(self, slice_meta: Dict[str, Any]) -> str:
        base = self.routing["base_path"].replace("\\", "/").strip("/")
        by_type = self.routing.get("by_exam_type") or {}
        key = ""
        for candidate_key in ("exam_type", "pack_routing_key"):
            v = (slice_meta or {}).get(candidate_key)
            if isinstance(v, str) and v.strip():
                key = v.strip()
                break
        subdir = by_type.get(key) or self.routing.get("default_subdir", "_Unsorted")
        subdir = str(subdir).replace("\\", "/").strip("/")
        return f"{base}/{subdir}" if subdir else base


# ---------- loading ----------


def _coerce_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return [str(x) for x in val if str(x).strip()]
    raise PackSpecError(f"expected list or string, got {type(val).__name__}")


def _require(d: Dict[str, Any], key: str, ctx: str) -> Any:
    if key not in d:
        raise PackSpecError(f"{ctx}: missing required field '{key}'")
    return d[key]


def load_pack(pack_dir: Path) -> Pack:
    yaml_path = pack_dir / "pack.yaml"
    if not yaml_path.exists():
        raise PackSpecError(f"pack.yaml not found in {pack_dir}")

    with yaml_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise PackSpecError(f"{yaml_path}: top-level must be a mapping")

    name = str(_require(raw, "name", str(yaml_path))).strip()
    if name != pack_dir.name:
        raise PackSpecError(f"{yaml_path}: name '{name}' must match dir name '{pack_dir.name}'")

    routing = raw.get("routing") or {}
    if not isinstance(routing, dict) or "base_path" not in routing:
        raise PackSpecError(f"{yaml_path}: routing.base_path is required")

    trigger = raw.get("trigger") or {}
    policies = raw.get("policies") or {}
    assets = raw.get("assets") or {}

    # Resolve prompts to text.
    prompts_meta = raw.get("prompts") or {}
    prompts: Dict[str, str] = {}
    mtimes: Dict[str, float] = {str(yaml_path): yaml_path.stat().st_mtime}
    for key in _PROMPT_FILES:
        rel = prompts_meta.get(key)
        if rel is None:
            prompts[key] = ""
            continue
        md_path = pack_dir / str(rel)
        if not md_path.exists():
            raise PackSpecError(f"{yaml_path}: prompts.{key} -> {rel} not found")
        prompts[key] = md_path.read_text(encoding="utf-8")
        mtimes[str(md_path)] = md_path.stat().st_mtime

    # Precompute match helpers.
    prefixes = _coerce_list(trigger.get("prefixes"))
    source_models = _coerce_list(trigger.get("source_models"))
    topic_pins = _coerce_list(trigger.get("topic_pins"))
    route_prefix = str(trigger.get("route_prefix") or "").replace("\\", "/").strip("/")

    return Pack(
        name=name,
        version=int(raw.get("version", 1)),
        path=pack_dir,
        trigger={
            "prefixes": prefixes,
            "source_models": source_models,
            "topic_pins": topic_pins,
            "route_prefix": route_prefix,
        },
        prompts=prompts,
        routing={
            "base_path": str(routing["base_path"]).replace("\\", "/").strip("/"),
            "by_exam_type": dict(routing.get("by_exam_type") or {}),
            "default_subdir": str(routing.get("default_subdir", "_Unsorted")).replace("\\", "/").strip("/"),
        },
        policies={
            "ki_force": policies.get("ki_force"),
            "dedup_enabled": bool(policies.get("dedup_enabled", True)),
            "provenance_filter_enabled": bool(policies.get("provenance_filter_enabled", True)),
            "skip_refine": bool(policies.get("skip_refine", False)),
            "qdrant_collection": str(policies.get("qdrant_collection", "obsidian_notes")),
            "qdrant_skip_default": bool(policies.get("qdrant_skip_default", False)),
        },
        assets={
            "save_originals": bool(assets.get("save_originals", False)),
            "dest_subdir": str(assets.get("dest_subdir", "images")).replace("\\", "/").strip("/"),
            "for_exam_types": (
                [str(x) for x in (assets.get("for_exam_types") or [])] or None
            ),
        },
        _prefix_patterns=[_strict_prefix_regex(p) for p in prefixes],
        _source_model_patterns=[p.lower() for p in source_models],
        _topic_pin_patterns=[_word_boundary_regex(p) for p in topic_pins],
        _route_prefix_norm=route_prefix,
        _mtimes=mtimes,
    )


# ---------- registry ----------


class PackRegistry:
    """Discovers packs under a root dir. Hot-reloads per `detect()` based on mtime.

    Usage:
        registry = PackRegistry(Path('packs'))
        pack = registry.detect(conv, route_hint=target_leaf_path)

    Detection precedence: prefix > source_model > topic_pin > route_prefix.
    Rationale:
      - prefix (`@pte`) is the user's explicit per-conv command — highest signal.
      - source_model declares intent at the model level — stronger than keyword
        scraping, but weaker than explicit per-message commands.
      - topic_pin is heuristic keyword match — lowest confidence.
      - route_prefix is a post-hoc re-filing hint.
    If multiple packs match at the same tier, the first by alpha-sorted name
    wins; a warning is emitted via the log callback (or discarded if none).
    """

    def __init__(self, root: Path, log_fn=None):
        self.root = Path(root)
        self._log = log_fn or (lambda msg: None)
        self._packs: List[Pack] = []
        self._dir_mtimes: Dict[str, float] = {}
        self._load_all()

    # --- loading ---

    def _load_all(self) -> None:
        packs: List[Pack] = []
        dir_mtimes: Dict[str, float] = {}
        if not self.root.exists():
            self._packs = []
            self._dir_mtimes = {}
            return
        for entry in sorted(self.root.iterdir()):
            if not entry.is_dir() or entry.name.startswith((".", "_")):
                continue
            pack_yaml = entry / "pack.yaml"
            if not pack_yaml.exists():
                continue
            try:
                pack = load_pack(entry)
            except PackSpecError as e:
                self._log(f"PACK_LOAD_ERROR | dir={entry.name} | err={e}")
                continue
            packs.append(pack)
            dir_mtimes[str(entry)] = entry.stat().st_mtime
        self._packs = packs
        self._dir_mtimes = dir_mtimes

    def _is_stale(self) -> bool:
        if not self.root.exists():
            return bool(self._packs)
        # New or removed pack dirs?
        current_dirs: Dict[str, float] = {}
        for entry in self.root.iterdir():
            if entry.is_dir() and not entry.name.startswith((".", "_")):
                current_dirs[str(entry)] = entry.stat().st_mtime
        if set(current_dirs.keys()) != set(self._dir_mtimes.keys()):
            return True
        # Any file inside a pack changed?
        for pack in self._packs:
            for tracked_path, tracked_mtime in pack._mtimes.items():
                try:
                    cur = Path(tracked_path).stat().st_mtime
                except OSError:
                    return True
                if cur != tracked_mtime:
                    return True
        return False

    def reload_if_stale(self) -> None:
        if self._is_stale():
            self._load_all()

    # --- detection ---

    def detect(self, conv, route_hint: Optional[str] = None) -> Optional[Pack]:
        self.reload_if_stale()
        if not self._packs:
            return None

        messages = getattr(conv, "messages", []) or []
        source_model = getattr(conv, "source_model", None)

        def collect(tier_fn, tier_name) -> List[Pack]:
            return [p for p in self._packs if tier_fn(p)]

        tiers: List[Tuple[str, List[Pack]]] = [
            ("prefix", collect(lambda p: p.matches_prefix(messages), "prefix")),
            ("source_model", collect(lambda p: p.matches_source_model(source_model), "source_model")),
            ("topic_pin", collect(lambda p: p.matches_topic_pin(messages), "topic_pin")),
            ("route_prefix", collect(lambda p: p.matches_route_prefix(route_hint), "route_prefix")),
        ]

        conv_id = getattr(conv, "conv_id", "?")
        for tier_name, matches in tiers:
            if not matches:
                continue
            if len(matches) > 1:
                self._log(
                    f"PACK_AMBIGUOUS | conv={conv_id} | tier={tier_name} | "
                    f"candidates={[p.name for p in matches]} | picked={matches[0].name}"
                )
            winner = matches[0]
            self._log(f"PACK_MATCHED | conv={conv_id} | pack={winner.name} | tier={tier_name}")
            return winner

        self._log(f"PACK_NONE | conv={conv_id}")
        return None

    # --- accessors ---

    @property
    def packs(self) -> List[Pack]:
        return list(self._packs)

    def get(self, name: str) -> Optional[Pack]:
        for p in self._packs:
            if p.name == name:
                return p
        return None
