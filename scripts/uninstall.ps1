# throughline uninstall — Windows PowerShell equivalent of scripts/uninstall.sh.
#
# Removes the runtime footprint of a throughline install. Prompts
# before each destructive action.
#
# Flags:
#   -Yes              assume 'yes' to every prompt
#   -KeepVault        keep the refined Markdown cards in $VAULT_PATH (default)
#   -DeleteVault      explicitly delete the vault
#   -KeepState        keep ~/.throughline + runtime state files
#   -DropCollection   also drop the Qdrant collection
#
# What it touches:
#   ~/.throughline/       wizard config
#   $THROUGHLINE_RUNTIME_ROOT (default ~/throughline_runtime)
#   Qdrant container      stops the local 'qdrant' Docker container
#   OpenWebUI Filter      NOT touched — remove manually from Functions UI

[CmdletBinding()]
param(
    [switch]$Yes,
    [switch]$KeepVault = $true,
    [switch]$DeleteVault,
    [switch]$KeepState,
    [switch]$DropCollection
)

if ($DeleteVault) { $KeepVault = $false }

function Ask($prompt) {
    if ($Yes) { return $true }
    $ans = Read-Host "$prompt [y/N]"
    return $ans -eq "y" -or $ans -eq "Y"
}

Write-Output "throughline uninstall"
Write-Output "-----------------------"

# 1. Qdrant container
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $running = docker ps -a --format "{{.Names}}" 2>$null
    if ($running -contains "qdrant") {
        if (Ask "stop + remove local Docker container 'qdrant'?") {
            docker stop qdrant 2>$null | Out-Null
            docker rm qdrant   2>$null | Out-Null
            Write-Output "  qdrant container removed (data in ~/qdrant_storage/ kept)"
        }
    }
}

# 2. Drop Qdrant collection (opt-in)
if ($DropCollection) {
    $qdrantUrl = if ($env:QDRANT_URL) { $env:QDRANT_URL } else { "http://localhost:6333" }
    $collection = if ($env:RAG_COLLECTION) { $env:RAG_COLLECTION } `
                  elseif ($env:QDRANT_COLLECTION) { $env:QDRANT_COLLECTION } `
                  else { "obsidian_notes" }
    if (Ask "DELETE collection '$collection' from $qdrantUrl? (all vectors lost)") {
        try {
            Invoke-RestMethod -Method Delete -Uri "$qdrantUrl/collections/$collection" | Out-Null
            Write-Output "  collection $collection dropped"
        } catch {
            Write-Output "  drop failed (is Qdrant reachable?)"
        }
    }
}

# 3. ~/.throughline wizard config
$cfgDir = Join-Path $HOME ".throughline"
if (-not $KeepState -and (Test-Path $cfgDir)) {
    if (Ask "remove $cfgDir (wizard config)?") {
        Remove-Item -Recurse -Force $cfgDir
        Write-Output "  removed $cfgDir"
    }
}

# 4. Runtime: raw + logs + state
$runtime = if ($env:THROUGHLINE_RUNTIME_ROOT) { $env:THROUGHLINE_RUNTIME_ROOT } else { Join-Path $HOME "throughline_runtime" }
if (Test-Path $runtime -and -not $KeepState) {
    if (Ask "remove $runtime (raw exports + logs + state)?") {
        Remove-Item -Recurse -Force $runtime
        Write-Output "  removed $runtime"
    }
}

# 5. Vault (user content — keep by default)
$vault = if ($env:VAULT_PATH) { $env:VAULT_PATH } elseif ($env:THROUGHLINE_VAULT_ROOT) { $env:THROUGHLINE_VAULT_ROOT } else { $null }
if (-not $KeepVault -and $vault -and (Test-Path $vault)) {
    Write-Output "refined vault at: $vault"
    if (Ask "DELETE every refined card in ${vault}? (user content)") {
        Remove-Item -Recurse -Force $vault
        Write-Output "  removed $vault"
    }
} elseif ($vault -and (Test-Path $vault)) {
    Write-Output "kept vault: $vault (pass -DeleteVault to remove)"
}

Write-Output ""
Write-Output "Uninstall complete."
Write-Output "Still manual:"
Write-Output "  - OpenWebUI Admin -> Functions -> delete the throughline_filter entry"
Write-Output "  - rm -rf <repo dir> if you are done with the source tree"
