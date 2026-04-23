#!/usr/bin/env bash
# throughline uninstall — macOS / Linux.
#
# Removes the runtime footprint of a throughline install. Safe to re-run.
# Prompts before each destructive action; flags skip prompts:
#   --yes              assume 'yes' to every prompt (non-interactive use)
#   --keep-vault       keep the refined Markdown cards in $VAULT_PATH
#   --keep-state       keep ~/.throughline + runtime state files
#   --drop-collection  also drop the Qdrant collection (NOT default —
#                      this deletes every refined vector; re-ingest
#                      would re-embed the same vault but cost money)
#
# What it touches:
#   services              launchd plists (Mac) / systemd units (Linux)
#   ~/.throughline/       wizard config + any stored state
#   $THROUGHLINE_RAW_ROOT (default ~/throughline_runtime) state + logs
#   Qdrant container      stops the local Docker container named 'qdrant'
#   OpenWebUI Filter      NOT touched — remove manually from Functions UI

set -euo pipefail

YES=0
KEEP_VAULT=1  # vault is user data — default is to KEEP
KEEP_STATE=0
DROP_COLLECTION=0

for arg in "$@"; do
  case "$arg" in
    --yes)             YES=1 ;;
    --keep-vault)      KEEP_VAULT=1 ;;
    --delete-vault)    KEEP_VAULT=0 ;;
    --keep-state)      KEEP_STATE=1 ;;
    --drop-collection) DROP_COLLECTION=1 ;;
    -h|--help)
      sed -n '2,/^set -eu/p' "$0" | sed 's/^# \?//' | sed '$d'
      exit 0 ;;
    *)
      echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

ask() {
  local prompt="$1"
  if [ "$YES" = "1" ]; then return 0; fi
  read -r -p "$prompt [y/N] " ans
  [ "$ans" = "y" ] || [ "$ans" = "Y" ]
}

echo "throughline uninstall"
echo "-----------------------"

# 1. Services
if [ "$(uname)" = "Darwin" ]; then
  for label in com.example.throughline.rag-server com.example.throughline.refine-daemon com.example.throughline.sync; do
    plist="$HOME/Library/LaunchAgents/${label}.plist"
    if [ -f "$plist" ]; then
      if ask "stop + remove launchd service ${label}?"; then
        launchctl bootout "gui/$(id -u)" "$plist" 2>/dev/null || true
        rm -f "$plist"
        echo "  removed $plist"
      fi
    fi
  done
else
  for unit in throughline-rag-server throughline-refine-daemon; do
    if systemctl --user is-enabled --quiet "$unit" 2>/dev/null; then
      if ask "disable + stop systemd --user service ${unit}?"; then
        systemctl --user disable --now "$unit"
        rm -f "$HOME/.config/systemd/user/${unit}.service"
        systemctl --user daemon-reload
        echo "  removed $unit"
      fi
    fi
  done
fi

# 2. Qdrant container
if command -v docker >/dev/null 2>&1; then
  if docker ps -a --format '{{.Names}}' | grep -qx qdrant; then
    if ask "stop + remove local Docker container 'qdrant'?"; then
      docker stop qdrant >/dev/null 2>&1 || true
      docker rm qdrant >/dev/null 2>&1 || true
      echo "  qdrant container removed (data in ~/qdrant_storage/ kept)"
    fi
  fi
fi

# 3. Drop Qdrant collection (opt-in)
if [ "$DROP_COLLECTION" = "1" ]; then
  qdrant_url="${QDRANT_URL:-http://localhost:6333}"
  collection="${RAG_COLLECTION:-${QDRANT_COLLECTION:-obsidian_notes}}"
  if ask "DELETE collection '${collection}' from ${qdrant_url}? (all vectors lost)"; then
    curl -s -X DELETE "${qdrant_url}/collections/${collection}" >/dev/null && \
      echo "  collection ${collection} dropped" || \
      echo "  drop failed (is Qdrant reachable?)"
  fi
fi

# 4. ~/.throughline (wizard config + any token cache)
if [ "$KEEP_STATE" = "0" ] && [ -d "$HOME/.throughline" ]; then
  if ask "remove ~/.throughline (wizard config)?"; then
    rm -rf "$HOME/.throughline"
    echo "  removed ~/.throughline"
  fi
fi

# 5. Runtime: raw + logs + state (NOT the refined vault)
runtime="${THROUGHLINE_RUNTIME_ROOT:-$HOME/throughline_runtime}"
if [ -d "$runtime" ] && [ "$KEEP_STATE" = "0" ]; then
  if ask "remove $runtime (raw exports + logs + state)?"; then
    rm -rf "$runtime"
    echo "  removed $runtime"
  fi
fi

# 6. Vault (user content — keep by default)
if [ "$KEEP_VAULT" = "0" ]; then
  vault="${VAULT_PATH:-${THROUGHLINE_VAULT_ROOT:-}}"
  if [ -n "$vault" ] && [ -d "$vault" ]; then
    echo "refined vault at: $vault"
    if ask "DELETE every refined card in $vault? (user content)"; then
      rm -rf "$vault"
      echo "  removed $vault"
    fi
  fi
else
  vault="${VAULT_PATH:-${THROUGHLINE_VAULT_ROOT:-}}"
  [ -n "$vault" ] && [ -d "$vault" ] && echo "kept vault: $vault (pass --delete-vault to remove)"
fi

echo ""
echo "Uninstall complete."
echo "Still manual:"
echo "  - OpenWebUI Admin → Functions → delete the throughline_filter entry"
echo "  - pip uninstall throughline / rm -rf <repo dir> if you're done"
