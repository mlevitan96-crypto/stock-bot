# Pull latest EOD reports from GitHub to local board/eod/out/.
# Run from repo root or any subdir; use weekdays after droplet sync (21:32 UTC).
# Ensures board/eod/out/ matches origin/main (droplet source of truth) to avoid conflicts.
# Usage: .\scripts\pull_eod_to_local.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $repoRoot

Write-Host "Pull EOD: repo root $repoRoot"
git fetch origin
# Align board/eod/out/ with origin so pull never conflicts (droplet is source of truth).
try { git checkout origin/main -- board/eod/out/ } catch { }
$pull = git pull origin main
Write-Host $pull
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done. EOD outputs in board/eod/out/"
