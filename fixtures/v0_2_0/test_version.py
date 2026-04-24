"""Tests for the package's __version__ surface.

Pinned because:
- Tools (uv, pip, dependabot, downstream packages) parse
  `pkg.__version__` at runtime — the attribute must always exist.
- A literal version drift (pyproject says one thing, __init__ says
  another) was a real regression once before this resolver landed.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[2]
sys.path.insert(0, str(REPO_ROOT))


class TestVersionAttribute:
    def test_attribute_exists(self):
        from throughline_cli import __version__
        assert isinstance(__version__, str)
        assert __version__  # non-empty

    def test_looks_like_semver(self):
        """v0.2.0, 0.2.1.dev0, 0.3.0a1 — must start with a digit and
        contain at least one dot."""
        from throughline_cli import __version__
        assert __version__[0].isdigit()
        assert "." in __version__

    def test_fallback_string_matches_pyproject(self):
        """Source-checkout fallback must equal `pyproject.toml`'s
        version. Otherwise a user without `pip install -e .` sees a
        different version than someone who installed from PyPI."""
        import sys as _sys
        if _sys.version_info >= (3, 11):
            import tomllib
        else:  # pragma: no cover
            import tomli as tomllib  # type: ignore
        with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
            pyproject_version = tomllib.load(fh)["project"]["version"]
        from throughline_cli import _FALLBACK_VERSION
        assert _FALLBACK_VERSION == pyproject_version

    def test_resolver_returns_string(self, monkeypatch):
        """When importlib.metadata raises PackageNotFoundError the
        resolver must fall back to the literal — not crash."""
        from throughline_cli import _resolve_version, _FALLBACK_VERSION
        # Force the PackageNotFoundError branch.
        import importlib.metadata as md

        def _raise(_name):
            raise md.PackageNotFoundError("simulated")

        monkeypatch.setattr(md, "version", _raise)
        assert _resolve_version() == _FALLBACK_VERSION


class TestVersionFlag:
    def test_dispatcher_version_flag(self, capsys):
        from throughline_cli.__main__ import main
        rc = main(["--version"])
        assert rc == 0
        out = capsys.readouterr().out
        assert out.startswith("throughline ")

    def test_dispatcher_short_flag(self, capsys):
        from throughline_cli.__main__ import main
        rc = main(["-V"])
        assert rc == 0
        assert "throughline" in capsys.readouterr().out

    def test_version_subcommand_word(self, capsys):
        from throughline_cli.__main__ import main
        rc = main(["version"])
        assert rc == 0
        assert "throughline" in capsys.readouterr().out
