"""throughline command-line tooling package.

Contains the install wizard, config persistence, import adapters,
self-growing taxonomy CLI (U27.4), and the doctor diagnostic command.

The package is imported by the top-level `install.py` shim so that
`python install.py` works without any additional packaging. Once
`pip install -e .` (or a future PyPI release) is in play, the
console-script entry points declared in `pyproject.toml` resolve to:

    throughline-install   -> throughline_cli.wizard:main
    throughline-import    -> throughline_cli.adapters:main
    throughline-taxonomy  -> throughline_cli.taxonomy:main
    throughline-doctor    -> throughline_cli.doctor:main

`__version__` is sourced from package metadata when an installed
distribution is present, falling back to the literal below for
source checkouts where `pip install -e .` hasn't been run.
"""
from __future__ import annotations

# Single literal kept in sync with `pyproject.toml::project.version`.
# v0.2.x maintenance bumps update both; v0.3 will fold the literal into
# a `versioningit` / `setuptools-scm` flow when one is chosen.
_FALLBACK_VERSION = "0.2.0"


def _resolve_version() -> str:
    try:
        # importlib.metadata is stdlib from 3.8+; the package name we
        # ask for matches `pyproject.toml::project.name`.
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover — unreachable on 3.11+
        return _FALLBACK_VERSION
    try:
        return version("throughline")
    except PackageNotFoundError:
        # Source checkout without `pip install -e .` — fall back.
        return _FALLBACK_VERSION


__version__ = _resolve_version()
