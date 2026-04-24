"""Public functions in throughline_cli/ and daemon/ must declare
return types.

Private (_-prefixed) functions are exempt; __init__ is exempt; async
def obeys the same rule. We don't require argument annotations yet
(too many dataclass-y places where arg types come from context),
but return types are the cheapest documentation you can ship and
they unblock downstream mypy work.

Ruff F + E9 doesn't catch `-> Missing`. We do it via AST here so the
check runs in under a second and stays hermetic.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import List

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]


SCOPED_DIRS = ("throughline_cli", "daemon")


def _find_missing_return_annotations() -> List[str]:
    missing: List[str] = []
    for d in SCOPED_DIRS:
        base = REPO_ROOT / d
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if node.name.startswith("_"):
                    continue
                if node.name == "__init__":
                    continue
                if node.returns is None:
                    missing.append(f"{rel}:{node.lineno} def {node.name}")
    return missing


class TestPublicFunctionsAreTyped:
    def test_public_surface_has_return_annotations(self):
        missing = _find_missing_return_annotations()
        assert not missing, (
            "Public functions without return type annotation:\n  "
            + "\n  ".join(missing)
            + "\nAdd `-> <type>` to each. Use `-> None` if the function "
              "returns nothing."
        )
