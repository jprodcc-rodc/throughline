# -*- coding: utf-8 -*-
"""
taxonomy.py
-----------

Central "classification constitution" for the knowledge flywheel. Defines:

1. The legal X / Y / Z tag sets.
2. The nine top-level JD (Johnny-Decimal) domain roots and the whitelist of
   leaf paths where notes are allowed to land.
3. Helper utilities for splitting "visible multi-X" tags from the single
   "machine primary X" the routing layer consumes.
4. Routing validation utilities.

This file ships with a sensible generic default tree. Downstream users who
want a different vault layout can override by placing a `taxonomy.py` at
`<repo>/config/taxonomy.py`; the daemon imports the override in preference
to this default if present (see `daemon/refine_daemon.py :: _load_taxonomy`).

XYZ tag semantics (preserved from the upstream design):
  - X axis = domain (what is this about). Multi-valued on-disk; single-
    valued for the router's benefit.
  - Y axis = form  (what kind of note is this: SOP, architecture, decision…).
  - Z axis = relation (how does this note relate to its neighbours: node,
    boundary, pipeline, matrix).
"""

from typing import Iterable, List, Dict, Optional

# =========================================================
# 1) XYZ constitution
# =========================================================

VALID_Y_SET: List[str] = [
    "y/Mechanism",
    "y/Decision",
    "y/Architecture",
    "y/SOP",
    "y/Optimization",
    "y/Troubleshooting",
    "y/Reference",
]

VALID_X_SET: List[str] = [
    "Biz/Monetization",
    "Biz/Ops",
    "Biz/Marketing",
    "Creative/Photo",
    "Creative/Video",
    "Creative/Design",
    "AI/LLM",
    "AI/Image",
    "AI/Video",
    "AI/Audio",
    "AI/Agent",
    "Tech/PKM",
    "Tech/Software",
    "Tech/Network",
    "Hardware/PC",
    "Hardware/Peripherals",
    "Hardware/Audio",
    "Study/Math",
    "Study/Physics",
    "Study/Linguistics",
    "Health/Medicine",
    "Health/Biohack",
    "Health/Psy",
    "Health/Fitness",
    "Health/Mindset",
    "Life/Finance",
    "Life/Home",
    "Life/Legal",
    "Life/Hobbies",
    "Life/Pets",
    "Game/Console",
    "Game/Mechanics",
    "Inbox/Unclassified",
]

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
# 2) JD top-level domains
# =========================================================

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

# Fallback path when the router cannot place a note confidently. Lives under
# the non-Qdrant-ingested 00_Buffer tree so bad routing never pollutes RAG.
JD_FALLBACK_PATH = "00_Buffer/00.00_System_Inbox"


# =========================================================
# 3) Whitelist of leaf paths allowed to accept final note writes
# =========================================================

JD_LEAF_PATHS_BY_DOMAIN: Dict[str, List[str]] = {
    "10": [
        "10_Tech_Infrastructure/10.01_Terminal_Devices/10.01.01_PC_Workstations",
        "10_Tech_Infrastructure/10.01_Terminal_Devices/10.01.02_Mobile_&_EDC",
        "10_Tech_Infrastructure/10.01_Terminal_Devices/10.01.03_Peripherals",
        "10_Tech_Infrastructure/10.02_Network_Storage/10.02.01_Networking_Gear",
        "10_Tech_Infrastructure/10.02_Network_Storage/10.02.02_NAS_Servers",
        "10_Tech_Infrastructure/10.02_Network_Storage/10.02.03_Backup_Doomsday",
        "10_Tech_Infrastructure/10.03_Cybersec_Privacy/10.03.01_Passwords_Auth",
        "10_Tech_Infrastructure/10.03_Cybersec_Privacy/10.03.02_Privacy_Anon",
        "10_Tech_Infrastructure/10.04_Audio_HiFi/10.04.01_Gear_Review",
        "10_Tech_Infrastructure/10.04_Audio_HiFi/10.04.02_Acoustics",
        "10_Tech_Infrastructure/10.05_Software_Coding/10.05.01_OS_Envs",
        "10_Tech_Infrastructure/10.05_Software_Coding/10.05.02_Web_Dev",
        "10_Tech_Infrastructure/10.05_Software_Coding/10.05.03_Data_Scripts",
    ],
    "20": [
        "20_Health_Biohack/20.01_Quantified_Self/20.01.01_Daily_Logs",
        "20_Health_Biohack/20.01_Quantified_Self/20.01.02_Biomarkers_DNA",
        "20_Health_Biohack/20.02_Meds_Supps/20.02.01_Psychiatric_Meds",
        "20_Health_Biohack/20.02_Meds_Supps/20.02.02_Somatic_Meds",
        "20_Health_Biohack/20.02_Meds_Supps/20.02.03_Nutrition",
        "20_Health_Biohack/20.03_Clinical/20.03.01_ENT",
        "20_Health_Biohack/20.03_Clinical/20.03.02_Dental",
        "20_Health_Biohack/20.03_Clinical/20.03.03_Surgery",
        "20_Health_Biohack/20.04_Mental_Psy/20.04.01_Psychiatry",
        "20_Health_Biohack/20.04_Mental_Psy/20.04.02_Neurodiversity",
        "20_Health_Biohack/20.04_Mental_Psy/20.04.03_Psychotherapy",
        "20_Health_Biohack/20.05_Medical_Records/20.05.01_Psychiatry_Visits",
        "20_Health_Biohack/20.05_Medical_Records/20.05.02_ENT_Records",
        "20_Health_Biohack/20.05_Medical_Records/20.05.03_Physical_Exams",
        "20_Health_Biohack/20.05_Medical_Records/20.05.04_Dental_Optometry",
        "20_Health_Biohack/20.05_Medical_Records/20.05.05_General_Somatic",
        "20_Health_Biohack/20.06_Fitness",
    ],
    "30": [
        "30_Biz_Ops/30.01_Strategy/30.01.01_Decision_Models",
        "30_Biz_Ops/30.01_Strategy/30.01.02_Team_Outsource",
        "30_Biz_Ops/30.02_Product/30.02.01_Digital_Products",
        "30_Biz_Ops/30.02_Product/30.02.02_Services",
        "30_Biz_Ops/30.02_Product/30.02.03_Pricing",
        "30_Biz_Ops/30.03_Growth/30.03.01_Content_Marketing",
        "30_Biz_Ops/30.03_Growth/30.03.02_Sales_Funnel",
        "30_Biz_Ops/30.03_Growth/30.03.03_CRM",
        "30_Biz_Ops/30.04_Finance/30.04.01_Accounting",
        "30_Biz_Ops/30.04_Finance/30.04.02_Legal_Taxes",
        "30_Biz_Ops/30.05_Review/30.05.01_Weekly",
        "30_Biz_Ops/30.05_Review/30.05.02_Monthly",
        "30_Biz_Ops/30.05_Review/30.05.03_Quarterly",
    ],
    "40": [
        "40_Cognition_PKM/40.01_PKM_OS/40.01.01_Methodology",
        "40_Cognition_PKM/40.01_PKM_OS/40.01.02_Obsidian_Tools",
        "40_Cognition_PKM/40.01_PKM_OS/40.01.03_AI_PKM_Flow",
        "40_Cognition_PKM/40.02_Cognition/40.02.01_Mental_Models",
        "40_Cognition_PKM/40.02_Cognition/40.02.02_Philosophy",
        "40_Cognition_PKM/40.03_Learning/40.03.01_Language",
        "40_Cognition_PKM/40.03_Learning/40.03.02_Tech_Skills",
        "40_Cognition_PKM/40.03_Learning/40.03.03_Neuro_Learning",
        "40_Cognition_PKM/40.03_Learning/40.03.04_PTE",
        "40_Cognition_PKM/40.04_Hard_Science/40.04.01_Acad_Bio",
        "40_Cognition_PKM/40.04_Hard_Science/40.04.02_Acad_Chem",
        "40_Cognition_PKM/40.04_Hard_Science/40.04.03_Physics_Math",
        "40_Cognition_PKM/40.04_Hard_Science/40.04.04_Systems_Theory",
    ],
    "50": [
        "50_Hobbies_Passions/50.01_Workshop/50.01.01_Tinkering",
        "50_Hobbies_Passions/50.01_Workshop/50.01.02_DIY_Projects",
        "50_Hobbies_Passions/50.02_Outdoor/50.02.01_Activity_Logs",
        "50_Hobbies_Passions/50.02_Outdoor/50.02.02_Gear",
        "50_Hobbies_Passions/50.03_Travel/50.03.01_Trip_Logs",
        "50_Hobbies_Passions/50.03_Travel/50.03.02_Guides",
        "50_Hobbies_Passions/50.04_Food_Drink/50.04.01_Recipes",
        "50_Hobbies_Passions/50.04_Food_Drink/50.04.02_Equipment",
    ],
    "60": [
        "60_Creative_Arts/60.01_Photography/60.01.01_Camera_Ops",
        "60_Creative_Arts/60.01_Photography/60.01.02_Lighting_Setup",
        "60_Creative_Arts/60.02_3D_VFX/60.02.01_Modeling",
        "60_Creative_Arts/60.02_3D_VFX/60.02.02_Simulation",
        "60_Creative_Arts/60.03_Video_Editing/60.03.01_Cut_SOP",
        "60_Creative_Arts/60.03_Video_Editing/60.03.02_Media_Mgmt",
        "60_Creative_Arts/60.04_Motion_Graphics/60.04.01_Keyframes",
        "60_Creative_Arts/60.04_Motion_Graphics/60.04.02_Compositing",
        "60_Creative_Arts/60.05_Color_Grading/60.05.01_Color_Theory",
        "60_Creative_Arts/60.05_Color_Grading/60.05.02_Grading_SOP",
        "60_Creative_Arts/60.06_Audio_Engineering/60.06.01_Music_Theory",
        "60_Creative_Arts/60.06_Audio_Engineering/60.06.02_Mixing_Chains",
    ],
    "70": [
        "70_AI/70.01_LLM_Brain/70.01.01_Theory_&_Models",
        "70_AI/70.01_LLM_Brain/70.01.02_Prompt_Vault",
        "70_AI/70.01_LLM_Brain/70.01.03_Agent_Systems",
        "70_AI/70.01_LLM_Brain/70.01.04_Deployment_Env",
        "70_AI/70.01_LLM_Brain/70.01.05_Workflows",
        "70_AI/70.02_Image_Generation/70.02.01_Open_Source_Gen",
        "70_AI/70.02_Image_Generation/70.02.02_Closed_Source_Gen",
        "70_AI/70.02_Image_Generation/70.02.03_ControlNet",
        "70_AI/70.03_Video_Generation/70.03.01_Video_Gen",
        "70_AI/70.03_Video_Generation/70.03.02_Face_Cloning",
        "70_AI/70.04_Audio_Generation/70.04.01_Music_Gen",
        "70_AI/70.04_Audio_Generation/70.04.02_Voice_Cloning",
        "70_AI/70.05_Model_Training/70.05.01_Data_Prep",
        "70_AI/70.05_Model_Training/70.05.02_LoRA_Finetune",
        "70_AI/70.06_AI_Automation/70.06.01_MCP_Protocol",
        "70_AI/70.06_AI_Automation/70.06.02_RPA_Orchestration",
        "70_AI/70.06_AI_Automation/70.06.03_Computer_Use",
    ],
    "80": [
        "80_Gaming/80.01_Library_Logs/80.01.01_Playlogs",
        "80_Gaming/80.01_Library_Logs/80.01.02_Backlog_Mgmt",
        "80_Gaming/80.02_Mechanics_Builds/80.02.01_Guides",
        "80_Gaming/80.02_Mechanics_Builds/80.02.02_Game_Economy",
        "80_Gaming/80.03_Modding_Tech/80.03.01_Mod_Configs",
        "80_Gaming/80.03_Modding_Tech/80.03.02_Server_Hosting",
        "80_Gaming/80.04_Heavy_Titles/80.04.01_Title_A",
        "80_Gaming/80.04_Heavy_Titles/80.04.02_Title_B",
    ],
    "90": [
        "90_Life_Base/90.01_Core_Infra/90.01.01_Identity_Docs",
        "90_Life_Base/90.01_Core_Infra/90.01.02_Digital_Subs",
        "90_Life_Base/90.02_Home_Property/90.02.01_Decor_DIY",
        "90_Life_Base/90.02_Home_Property/90.02.02_Appliances",
        "90_Life_Base/90.03_Immigration/90.03.01_Visa_Paperwork",
        "90_Life_Base/90.03_Immigration/90.03.02_Local_Guides",
        "90_Life_Base/90.04_Legal_Civil/90.04.01_Contracts",
        "90_Life_Base/90.04_Legal_Civil/90.04.02_Disputes_Logs",
        "90_Life_Base/90.05_Pets_Companions/90.05.01_Cats_Care",
        "90_Life_Base/90.05_Pets_Companions/90.05.02_Dogs_Care",
        "90_Life_Base/90.05_Pets_Companions/90.05.03_Other_Pets",
        "90_Life_Base/90.06_Personal_Finance/90.06.01_Loans_Debts",
        "90_Life_Base/90.06_Personal_Finance/90.06.02_Insurance_Taxes",
    ],
}

ALL_JD_LEAF_PATHS: List[str] = [
    path
    for code in JD_ROOT_ORDER
    for path in JD_LEAF_PATHS_BY_DOMAIN[code]
]

ALL_JD_ROOTS: List[str] = [JD_ROOTS[code] for code in JD_ROOT_ORDER]


# =========================================================
# 4) Basic utilities
# =========================================================

def unique_keep_order(items: Iterable[str]) -> List[str]:
    out = []
    seen = set()
    for item in items:
        s = str(item).strip()
        if not s:
            continue
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def normalize_path(path: str) -> str:
    return str(path).replace("\\", "/").strip().strip("/")


def normalize_tag(tag: str) -> str:
    return str(tag).strip()


# =========================================================
# 5) Tag splitting utilities
# =========================================================

def filter_valid_x(tags: Iterable[str]) -> List[str]:
    return [t for t in unique_keep_order(tags) if t in VALID_X]


def filter_valid_y(tags: Iterable[str]) -> List[str]:
    return [t for t in unique_keep_order(tags) if t in VALID_Y]


def filter_valid_z(tags: Iterable[str]) -> List[str]:
    return [t for t in unique_keep_order(tags) if t in VALID_Z]


def split_machine_tags(tags: Iterable[str]) -> Dict[str, List[str]]:
    """
    Split a tag list into:
    - x: visible X tags (may be multiple)
    - y: Y tags (should usually be a single value)
    - z: Z tags (should usually be a single value)
    - others: everything else
    """
    tags = unique_keep_order(tags)
    xs = [t for t in tags if t in VALID_X]
    ys = [t for t in tags if t in VALID_Y]
    zs = [t for t in tags if t in VALID_Z]
    others = [t for t in tags if t not in VALID_X and t not in VALID_Y and t not in VALID_Z]

    return {
        "x": xs,
        "y": ys,
        "z": zs,
        "others": others,
    }


def pick_primary_x(x_tags: Iterable[str], preferred: Optional[str] = None) -> str:
    """
    The machine layer keeps only a single primary X.
    - If `preferred` is legal, use it.
    - Otherwise pick the first legal X.
    - Otherwise fall back to Inbox/Unclassified.
    """
    xs = filter_valid_x(x_tags)

    if preferred and preferred in VALID_X:
        return preferred

    if xs:
        return xs[0]

    return DEFAULT_PRIMARY_X


def machine_metadata_from_tags(
    tags: Iterable[str],
    preferred_primary_x: Optional[str] = None,
) -> Dict[str, object]:
    """
    Extract machine-layer metadata from frontmatter tags:
    - domain_x: the single primary X
    - form_y:   the single primary Y
    - z_axis:   the single primary Z
    `visible_x_tags` is also returned for UI use.
    """
    parsed = split_machine_tags(tags)

    domain_x = pick_primary_x(parsed["x"], preferred=preferred_primary_x)
    form_y = parsed["y"][0] if parsed["y"] else ""
    z_axis = parsed["z"][0] if parsed["z"] else ""

    return {
        "domain_x": domain_x,
        "form_y": form_y,
        "z_axis": z_axis,
        "visible_x_tags": parsed["x"],
        "other_tags": parsed["others"],
    }


def build_visible_tags(
    primary_x: Optional[str] = None,
    visible_x_tags: Optional[Iterable[str]] = None,
    form_y: Optional[str] = None,
    z_axis: Optional[str] = None,
    other_tags: Optional[Iterable[str]] = None,
) -> List[str]:
    """
    Build the final frontmatter tag list:
    - the UI side allows multiple X values;
    - the machine-side primary X is usually also included.
    """
    tags: List[str] = []

    if form_y and form_y in VALID_Y:
        tags.append(form_y)

    x_pool = []
    if primary_x and primary_x in VALID_X:
        x_pool.append(primary_x)
    if visible_x_tags:
        for x in visible_x_tags:
            if x in VALID_X:
                x_pool.append(x)

    tags.extend(unique_keep_order(x_pool))

    if z_axis and z_axis in VALID_Z:
        tags.append(z_axis)

    if other_tags:
        tags.extend(unique_keep_order(other_tags))

    return unique_keep_order(tags)


# =========================================================
# 6) JD routing utilities
# =========================================================

def jd_root_from_code(code: str) -> str:
    return JD_ROOTS.get(str(code), "")


def jd_code_from_root(root_name: str) -> str:
    return JD_CODE_BY_ROOT.get(root_name, "")


def jd_code_from_path(path: str) -> str:
    """Infer which 10/20/.../90 root a path belongs to."""
    path = normalize_path(path)
    if not path:
        return ""

    root = path.split("/", 1)[0]
    return JD_CODE_BY_ROOT.get(root, "")


def allowed_leaf_paths(domain_code: Optional[str] = None) -> List[str]:
    if domain_code is None:
        return list(ALL_JD_LEAF_PATHS)
    return list(JD_LEAF_PATHS_BY_DOMAIN.get(str(domain_code), []))


def is_valid_leaf_path(path: str) -> bool:
    return normalize_path(path) in ALL_JD_LEAF_PATHS


def path_belongs_to_domain(domain_code: str, path: str) -> bool:
    return normalize_path(path) in JD_LEAF_PATHS_BY_DOMAIN.get(str(domain_code), [])


def coerce_target_path(domain_code: Optional[str], target_path: str) -> str:
    """
    Normalize the target_path emitted by the LLM router:
    1. If `domain_code` is set and `target_path` is whitelisted for that
       domain, pass through.
    2. Otherwise, if `target_path` is in the global leaf whitelist, pass through.
    3. Otherwise, fall back to JD_FALLBACK_PATH.
    """
    target_path = normalize_path(target_path)

    if domain_code and target_path in JD_LEAF_PATHS_BY_DOMAIN.get(str(domain_code), []):
        return target_path

    if target_path in ALL_JD_LEAF_PATHS:
        return target_path

    return JD_FALLBACK_PATH


# =========================================================
# 7) Light-touch validators
# =========================================================

def is_valid_primary_x(x: str) -> bool:
    return x in VALID_X


def is_valid_form_y(y: str) -> bool:
    return y in VALID_Y


def is_valid_z_axis(z: str) -> bool:
    return z in VALID_Z


def validate_machine_metadata(meta: Dict[str, str]) -> Dict[str, str]:
    """
    Light-touch cleanup of machine metadata.
    Does not force a Y or Z value if missing; just ensures X has a default.
    """
    domain_x = meta.get("domain_x", "")
    form_y = meta.get("form_y", "")
    z_axis = meta.get("z_axis", "")

    if domain_x not in VALID_X:
        domain_x = DEFAULT_PRIMARY_X

    if form_y not in VALID_Y:
        form_y = ""

    if z_axis not in VALID_Z:
        z_axis = ""

    return {
        "domain_x": domain_x,
        "form_y": form_y,
        "z_axis": z_axis,
    }


# =========================================================
# 8) Debug helper
# =========================================================

if __name__ == "__main__":
    print("taxonomy.py loaded")
    print(f"VALID_X_SET: {len(VALID_X_SET)}")
    print(f"VALID_Y_SET: {len(VALID_Y_SET)}")
    print(f"VALID_Z_SET: {len(VALID_Z_SET)}")
    print(f"JD leaf paths: {len(ALL_JD_LEAF_PATHS)}")
