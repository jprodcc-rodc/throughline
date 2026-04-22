# -*- coding: utf-8 -*-
"""
config/taxonomy.example.py
--------------------------

Example custom taxonomy override. If this file exists (renamed to
`config/taxonomy.py`, with the example-suffix dropped), the daemon imports
from here *instead of* `daemon/taxonomy.py`. That lets forkers change the JD
tree, the XYZ axes, or the legal-leaf whitelist without editing vendored code.

How to use:
    1. Copy this file to `config/taxonomy.py`.
    2. Edit the lists / dicts below to match your vault's folder layout.
    3. Restart the daemon. `_load_taxonomy()` in `daemon/refine_daemon.py`
       prefers `config/taxonomy.py` over the bundled default.

Design rules to preserve (the router relies on these):
    - `JD_ROOTS` keys are 2-digit strings, values are full folder names.
    - `JD_FALLBACK_PATH` must exist in the vault, and must be outside any
      ingested (Qdrant-upserted) subtree. The daemon writes here when the
      subpath router cannot find a confident leaf.
    - `JD_LEAF_PATHS_BY_DOMAIN` entries are forward-slash paths relative to
      the vault root. They MUST start with the matching JD root folder name.
    - `VALID_X_SET`, `VALID_Y_SET`, `VALID_Z_SET` are the closed vocabulary
      the refiner is allowed to emit. Do NOT rely on the LLM to invent new
      tags -- any tag it emits that is not in these sets is dropped.

What is safe to change:
    - Add / remove leaves in `JD_LEAF_PATHS_BY_DOMAIN`. No code changes.
    - Add / remove `VALID_X_SET` entries. No code changes (but make sure the
      `prompts/en/refine.md` inputs match if you want the refiner to know).
    - Rename a top-level root (e.g. `"10_Tech_Infrastructure"` ->
      `"10_IT"`). But you MUST edit `prompts/en/route_domain.md` AND
      `prompts/en/route_subpath.md` to match, or the router prompt will
      produce labels your validator rejects.

What is NOT safe to change:
    - The 2-digit JD key format. Several parts of the daemon parse paths
      by splitting on underscore and taking the first token.
    - `DEFAULT_PRIMARY_X`. If the refiner fails to emit a valid primary_x,
      this is the fallback; keep it in `VALID_X_SET`.
"""

from typing import Iterable, List, Dict, Optional

# =========================================================
# 1) XYZ axes
# =========================================================

# Y = form: what *kind* of note is this? (SOP, decision, mechanism, ...)
VALID_Y_SET: List[str] = [
    "y/Mechanism",
    "y/Decision",
    "y/Architecture",
    "y/SOP",
    "y/Optimization",
    "y/Troubleshooting",
    "y/Reference",
]

# X = domain: what is it *about*? Multi-valued on-disk; the router picks one.
# Edit this list to match the subject areas that matter to you.
VALID_X_SET: List[str] = [
    # Generic examples -- keep what you need, delete what you don't.
    "AI/LLM",
    "AI/Agent",
    "Tech/PKM",
    "Tech/Software",
    "Tech/Network",
    "Health/Medicine",
    "Health/Biohack",
    "Study/Linguistics",   # example: replace with your own learning track
    "Life/Finance",
    "Life/Home",
    "Creative/Writing",
    "Inbox/Unclassified",  # <-- do NOT remove; this is the fallback primary_x
]

# Z = relation: how does this note relate to neighbours? (node, boundary, ...)
VALID_Z_SET: List[str] = [
    "z/Node",
    "z/Boundary",
    "z/Pipeline",
    "z/Matrix",
]

VALID_X = set(VALID_X_SET)
VALID_Y = set(VALID_Y_SET)
VALID_Z = set(VALID_Z_SET)

DEFAULT_PRIMARY_X = "Inbox/Unclassified"


# =========================================================
# 2) Johnny-Decimal top-level roots
# =========================================================

# Keys are the 2-digit code; values are the literal folder name in your vault.
# Both must match: the router emits a label like "40_Cognition_PKM", and the
# daemon resolves it by looking up the 2-digit prefix here.
JD_ROOTS: Dict[str, str] = {
    "10": "10_Tech_Infrastructure",
    "20": "20_Health_Biohack",
    "30": "30_Biz_Ops",
    "40": "40_Cognition_PKM",
    "50": "50_Hobbies_Passions",
    "60": "60_Creative_Arts",
    "70": "70_AI",
    "80": "80_Gaming",
    "90": "90_Life_Base",
}

# Human-readable one-liner per root (shown in dashboards).
JD_DOMAIN_MAP: Dict[str, str] = {
    "10": "Tech Infrastructure",
    "20": "Health Biohack",
    "30": "Biz Ops",
    "40": "Cognition PKM",
    "50": "Hobbies Passions",
    "60": "Creative Arts",
    "70": "AI",
    "80": "Gaming",
    "90": "Life Base",
}

JD_CODE_BY_ROOT = {v: k for k, v in JD_ROOTS.items()}
JD_ROOT_ORDER = ["10", "20", "30", "40", "50", "60", "70", "80", "90"]

# Fallback when the router cannot pick a leaf confidently. Keep this under
# `00_Buffer/` (or any folder that is NOT in your Qdrant ingest whitelist) so
# misrouted cards never pollute the RAG index.
JD_FALLBACK_PATH = "00_Buffer/00.00_System_Inbox"


# =========================================================
# 3) Legal-leaf whitelist
# =========================================================
# Every card ends up at one of these exact paths (or at JD_FALLBACK_PATH).
# The subpath router prompt is given the subset for the chosen domain.
# Edit freely to match your vault layout.

JD_LEAF_PATHS_BY_DOMAIN: Dict[str, List[str]] = {
    "10": [
        "10_Tech_Infrastructure/10.01_Terminal_Devices/10.01.01_PC_Workstations",
        "10_Tech_Infrastructure/10.02_Network_Storage/10.02.01_Networking_Gear",
        "10_Tech_Infrastructure/10.05_Software_Coding/10.05.01_OS_Envs",
        # Add your own leaves here -- they show up in the subpath router.
    ],
    "20": [
        "20_Health_Biohack/20.01_Quantified_Self/20.01.01_Daily_Logs",
        "20_Health_Biohack/20.02_Meds_Supps/20.02.03_Nutrition",
        "20_Health_Biohack/20.06_Fitness",
    ],
    "30": [
        "30_Biz_Ops/30.01_Strategy/30.01.01_Decision_Models",
        "30_Biz_Ops/30.04_Finance/30.04.01_Accounting",
    ],
    "40": [
        "40_Cognition_PKM/40.01_PKM_OS/40.01.01_Methodology",
        "40_Cognition_PKM/40.02_Cognition/40.02.01_Mental_Models",
        # Example leaf: replace with your own learning track
        "40_Cognition_PKM/40.03_Learning/40.03.04_PTE",
    ],
    "50": [
        "50_Hobbies_Passions/50.01_Workshop/50.01.01_Tinkering",
        "50_Hobbies_Passions/50.03_Travel/50.03.01_Trip_Logs",
        "50_Hobbies_Passions/50.04_Food_Drink/50.04.01_Recipes",
    ],
    "60": [
        "60_Creative_Arts/60.01_Photography/60.01.01_Camera_Ops",
        "60_Creative_Arts/60.03_Video_Editing/60.03.01_Cut_SOP",
    ],
    "70": [
        "70_AI/70.01_LLM_Brain/70.01.02_Prompt_Vault",
        "70_AI/70.01_LLM_Brain/70.01.03_Agent_Systems",
    ],
    "80": [
        "80_Gaming/80.01_Library_Logs/80.01.01_Playlogs",
        "80_Gaming/80.02_Mechanics_Builds/80.02.01_Guides",
    ],
    "90": [
        "90_Life_Base/90.01_Core_Infra/90.01.01_Identity_Docs",
        "90_Life_Base/90.05_Pets_Companions/90.05.03_Other_Pets",
    ],
}

ALL_JD_LEAF_PATHS: List[str] = [
    path
    for code in JD_ROOT_ORDER
    for path in JD_LEAF_PATHS_BY_DOMAIN[code]
]

ALL_JD_ROOTS: List[str] = [JD_ROOTS[code] for code in JD_ROOT_ORDER]


# =========================================================
# 4) Helper utilities (interface contract with the daemon)
# =========================================================
# Do NOT rename these functions. `daemon/refine_daemon.py` imports them by
# name. If you change the signatures, the daemon will fail at import time.

def split_primary_x(visible_x_tags: Iterable[str]) -> str:
    """Pick a single primary_x from a multi-valued visible_x_tags list.

    Strategy: return the first tag that is in `VALID_X`. If none match,
    return `DEFAULT_PRIMARY_X`.
    """
    for tag in (visible_x_tags or []):
        if tag in VALID_X:
            return tag
    return DEFAULT_PRIMARY_X


def is_valid_primary_x(tag: str) -> bool:
    """Guard used by the refiner post-processor."""
    return tag in VALID_X


def jd_root_for(path: str) -> Optional[str]:
    """Given a full leaf path, return the 2-digit JD code or None."""
    if not path:
        return None
    head = path.split("/", 1)[0]
    return JD_CODE_BY_ROOT.get(head)


def leaves_for_domain(code: str) -> List[str]:
    """Return the legal leaf whitelist for one JD domain (router input)."""
    return list(JD_LEAF_PATHS_BY_DOMAIN.get(code, []))
