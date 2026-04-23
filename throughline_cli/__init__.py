"""throughline command-line tooling package.

Contains the v0.2.0 install wizard, config persistence, and (later)
per-subcommand modules for `reconfigure`, `import`, `uninstall`, etc.

The package is imported by the top-level `install.py` shim so that
`python install.py` works without any additional packaging. Future
pyproject-based entry points will resolve to `throughline_cli.wizard:main`.
"""

__version__ = "0.2.0-dev"
