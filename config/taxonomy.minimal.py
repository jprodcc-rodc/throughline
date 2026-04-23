"""Minimal skeletal taxonomy — starter for cold-start + small-import users.

Shipped as the v0.2.0 default for users picking 'minimal' at wizard
step 14. Five broad domains wide enough to catch anything without
forcing false specificity on day one. Self-grows via U27: the refiner
emits `proposed_x_ideal` alongside the constrained `primary_x`, the
daemon logs the drift, and `python -m throughline_cli taxonomy review`
surfaces growth candidates for user approval.

Philosophy: it is safer to start with 5 catch-all domains and grow
to 12 well-fitting ones than to start with 15 specific ones and
discover half of them never get used.

See docs/TAXONOMY_GROWTH_DESIGN.md for the growth-loop spec.
"""
from __future__ import annotations


VALID_X_SET = {
    # Any technical / engineering / code content. Gets split later
    # by U27 review into Tech/AI, Tech/Network, Tech/Data, etc.
    "Tech",

    # Any creative / artistic / communication / writing content.
    # Grows to Creative/Writing, Creative/Video, Creative/Design, etc.
    "Creative",

    # Physiology / medicine / nutrition / fitness / mental health.
    # Grows to Health/Medicine, Health/Fitness, Health/Mental, etc.
    "Health",

    # Life logistics, finances, relationships, housing, travel,
    # immigration, non-technical decisions. Broader than Health but
    # narrower than Misc.
    "Life",

    # Explicit catch-all. If none of the above fit cleanly, route
    # here. U27 review treats Misc as a high-priority observation
    # bucket — cards landing here are the strongest growth signal.
    "Misc",
}


VALID_Y_SET = {
    # Step-by-step how-to content.
    "y/SOP",

    # A decision was made (or an irreversible conclusion reached).
    # These end up in `personal_persistent` knowledge_identity more
    # often than not.
    "y/Decision",

    # Explanation of underlying principles or mechanisms.
    "y/Mechanism",

    # Reference table / lookup / cheat-sheet material. Not a
    # narrative; a lookup asset.
    "y/Reference",
}


VALID_Z_SET = {
    # Card is about a discrete node or concept.
    "z/Node",

    # Card describes a process or flow of multiple steps.
    "z/Pipeline",

    # Card explores what is in scope vs out of scope, what breaks
    # the thing at the edges.
    "z/Boundary",
}
