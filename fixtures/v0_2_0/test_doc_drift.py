"""Catch documentation drift against runtime contracts.

Documentation that asserts a specific number ("doctor runs N
checks", "16 LLM providers", etc.) drifts whenever the underlying
code changes. These tests pin the docs to the code so a future
contributor can't add a check without bumping the count in three
README sections.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


# ============================================================
# Doctor check count claims must match DEFAULT_CHECKS length
# ============================================================

class TestDoctorCheckCountClaims:
    def _actual_count(self) -> int:
        from throughline_cli.doctor import DEFAULT_CHECKS
        return len(DEFAULT_CHECKS)

    def test_readme_count_matches(self):
        """README.md mentions `N checks with remediation`."""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        m = re.search(r"doctor\s+#\s*(\d+)\s+check", readme)
        assert m, ("README.md no longer mentions doctor check count — "
                    "did the line get removed?")
        claimed = int(m.group(1))
        actual = self._actual_count()
        assert claimed == actual, (
            f"README.md claims doctor runs {claimed} checks, but "
            f"DEFAULT_CHECKS has {actual}. Update README.md so the "
            f"count matches.")

    def test_deployment_md_count_matches(self):
        """docs/DEPLOYMENT.md prints `All N checks passed.` in the
        sample output block."""
        deploy = (REPO_ROOT / "docs" / "DEPLOYMENT.md").read_text(
            encoding="utf-8")
        m = re.search(r"All (\d+) checks passed\.", deploy)
        assert m, ("DEPLOYMENT.md no longer mentions doctor check "
                    "count — did the sample output get removed?")
        claimed = int(m.group(1))
        actual = self._actual_count()
        assert claimed == actual, (
            f"DEPLOYMENT.md claims {claimed} checks, "
            f"DEFAULT_CHECKS has {actual}.")

    def test_architecture_md_count_matches(self):
        """docs/ARCHITECTURE.md §13.5 says `runs N checks`."""
        arch = (REPO_ROOT / "docs" / "ARCHITECTURE.md").read_text(
            encoding="utf-8")
        m = re.search(r"doctor.*?runs\s+(\d+)\s+checks", arch,
                       re.IGNORECASE | re.DOTALL)
        assert m, ("ARCHITECTURE.md no longer mentions doctor check "
                    "count — did the line get removed?")
        claimed = int(m.group(1))
        actual = self._actual_count()
        assert claimed == actual, (
            f"ARCHITECTURE.md claims {claimed} checks, "
            f"DEFAULT_CHECKS has {actual}.")


# ============================================================
# Provider count claims must match the registry
# ============================================================

class TestProviderCountClaims:
    def _actual_count(self) -> int:
        from throughline_cli.providers import list_presets
        return len(list_presets())

    def test_readme_16_providers_matches(self):
        """README.md repeatedly says '16 LLM providers'. Pin it to the
        actual registry size — adding a 17th provider must bump the
        copy too."""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        # Multiple phrasings: "16 LLM providers", "16 preset routes",
        # "16 OpenAI-compatible". Catch any "<n> ... provider" claim.
        matches = re.findall(
            r"(\d+)\s+(?:LLM\s+providers|preset\s+routes|"
            r"OpenAI-compatible|provider\s+(?:registry|presets))",
            readme)
        assert matches, "README.md no longer mentions a provider count"
        actual = self._actual_count()
        for claim in matches:
            assert int(claim) == actual, (
                f"README.md claims {claim} providers, registry has "
                f"{actual}. Update the prose or the registry.")