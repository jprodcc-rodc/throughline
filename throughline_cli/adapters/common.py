"""Shared adapter helpers.

- ImportSummary: per-run statistics dataclass returned by every adapter.
- resolve_out_dir(): dispatch CLI flag / config.toml / env / hardcoded.
- Manifest writing: records which conversations were emitted under which
  import_source tag, so bulk purge can locate + delete them later.
- Frontmatter + render helpers used by multiple adapters.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional


DEFAULT_RAW_ROOT = Path.home() / "throughline_runtime" / "sources" / "openwebui_raw"
DEFAULT_STATE_DIR = Path.home() / "throughline_runtime" / "state"


@dataclass
class ImportSummary:
    source: str
    import_tag: str
    scanned: int = 0
    emitted: int = 0
    skipped_no_content: int = 0
    skipped_malformed: int = 0
    total_tokens_estimate: int = 0
    out_dir: str = ""
    manifest_path: Optional[str] = None
    dry_run: bool = False
    sample_paths: list[str] = field(default_factory=list)

    def estimated_usd_normal(self) -> float:
        """Rough Sonnet 4.6 cost for Normal-tier refine of this many tokens.
        ~$3/M in + $15/M out at current pricing; use mid-blend $10/M to
        keep it a single honest number."""
        return round(self.total_tokens_estimate / 1_000_000 * 10, 2)

    def estimated_usd_skim(self) -> float:
        """Rough Haiku 4.5 cost at Skim tier. ~$1/M in + $5/M out,
        average $3/M."""
        return round(self.total_tokens_estimate / 1_000_000 * 3, 2)


def resolve_out_dir(cli_override: Optional[str]) -> Path:
    """Priority: --out flag > $THROUGHLINE_RAW_ROOT > wizard config.toml
    > hardcoded default. The config.toml hook is prepared but not read
    here to keep this helper dependency-free for tests."""
    if cli_override:
        return Path(cli_override).expanduser()
    env = os.environ.get("THROUGHLINE_RAW_ROOT", "").strip()
    if env:
        return Path(env).expanduser()
    return DEFAULT_RAW_ROOT


def make_import_tag(source: str, today: Optional[date] = None) -> str:
    """`import_source` frontmatter value + manifest filename stem."""
    today = today or date.today()
    return f"{source}-{today.isoformat()}"


def safe_conv_id(s: str) -> str:
    """Slug-safe fragment of a conversation UUID for filenames."""
    return re.sub(r"[^A-Za-z0-9_-]", "", s)[:36] or "anon"


def target_path(out_dir: Path, conv_date: date, conv_id: str) -> Path:
    """$OUT/YYYY-MM/YYYY-MM-DD_{conv_id}.md — matches OpenWebUI exporter."""
    month_dir = out_dir / f"{conv_date.year:04d}-{conv_date.month:02d}"
    return month_dir / f"{conv_date.isoformat()}_{safe_conv_id(conv_id)}.md"


def render_markdown(title: str,
                    messages: list[tuple[str, str]],
                    metadata: dict) -> str:
    """Emit raw MD in the OpenWebUI exporter shape the daemon consumes.

    messages = [(role, text), ...] where role is 'user' or 'assistant'.
    Roles render as H1 headers ('# User' / '# Assistant') separating
    turns.
    """
    fm_lines = ["---"]
    for k in ("title", "date", "updated", "source_platform",
              "source_conversation_id", "source_updated_at",
              "import_source"):
        if k in metadata:
            v = metadata[k]
            if isinstance(v, str):
                v = v.replace('"', '\\"')
                fm_lines.append(f'{k}: "{v}"')
            else:
                fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    out = ["\n".join(fm_lines), ""]
    if title:
        out.append(f"# {title}")
        out.append("")
    for role, text in messages:
        display = role.capitalize()
        out.append(f"# {display}")
        out.append("")
        out.append(text.rstrip())
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def estimate_tokens(text: str) -> int:
    """Crude char/4 token estimate — good enough for cost-warning
    accuracy (we don't ship tiktoken by default to keep deps light).
    """
    return max(1, len(text) // 4)


def write_manifest(out_dir: Path,
                   summary: ImportSummary,
                   conv_ids: list[str],
                   state_dir: Optional[Path] = None) -> Path:
    """Write state/imports/<tag>.json with the list of conversation UUIDs
    emitted in this run. Used later by `throughline purge --import-source X`.
    """
    state_dir = state_dir or DEFAULT_STATE_DIR
    imports_dir = state_dir / "imports"
    imports_dir.mkdir(parents=True, exist_ok=True)
    path = imports_dir / f"{summary.import_tag}.json"
    payload = {
        "tag": summary.import_tag,
        "source": summary.source,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "out_dir": str(out_dir),
        "emitted": summary.emitted,
        "conversation_ids": conv_ids,
        "summary": asdict(summary),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    summary.manifest_path = str(path)
    return path
