#!/usr/bin/env bash
#
# Mirror root-level docs into docs/ so mkdocs can pull them into the
# site without overriding mkdocs's docs_dir restriction. The root
# copies stay authoritative for GitHub's direct rendering; the
# docs/*.md copies are build artefacts.
#
# Files synced:
#     README.md     -> docs/index.md
#     CHANGELOG.md  -> docs/changelog.md
#     ROADMAP.md    -> docs/roadmap.md
#     CONTRIBUTING.md    -> docs/contributing.md
#     SECURITY.md   -> docs/security.md
#     CODE_OF_CONDUCT.md -> docs/code-of-conduct.md
#
# Runs both in CI (.github/workflows/docs.yml) and locally before
# `mkdocs serve`. Idempotent — reruns just overwrite.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

copy() {
    local src="$1"
    local dest="$2"
    if [ ! -f "$src" ]; then
        echo "warning: $src not found, skipping" >&2
        return 0
    fi
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
    echo "synced: $src -> $dest"
}

copy README.md             docs/index.md
copy CHANGELOG.md          docs/changelog.md
copy ROADMAP.md            docs/roadmap.md
copy CONTRIBUTING.md       docs/contributing.md
copy SECURITY.md           docs/security.md
copy CODE_OF_CONDUCT.md    docs/code-of-conduct.md
