# One-time cleanup: delete old local and remote branches so only main (and optional staging) remain.
# See docs/CLEANUP_AND_BRANCH_POLICY.md. Run from repo root.
# Usage: .\scripts\cleanup_old_branches.ps1          # dry-run
#        .\scripts\cleanup_old_branches.ps1 -Execute # actually delete

param(
    [switch]$Execute
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$localToDelete = @(
    "audit-fixes-deployment",
    "data-integrity/high-water-giveback",
    "export-20251223-214834",
    "export-20251223-215324",
    "export-20251223-215748",
    "fix-all-issues-20251224-135727"
)
$remoteToDelete = @(
    "cursor/stock-trading-bot-review-2377",
    "data-integrity/high-water-giveback",
    "export-20251223-195855",
    "export-20251223-204922",
    "export-20251223-214834",
    "export-20251223-215324",
    "export-20251223-215748"
)

if (-not $Execute) {
    Write-Host "DRY RUN. To actually delete branches, run: .\scripts\cleanup_old_branches.ps1 -Execute"
    Write-Host ""
    Write-Host "Would delete LOCAL branches:"
    $localToDelete | ForEach-Object { Write-Host "  - $_" }
    Write-Host "Would delete REMOTE branches:"
    $remoteToDelete | ForEach-Object { Write-Host "  - origin/$_" }
    exit 0
}

# Ensure we're on main
$branch = git branch --show-current
if ($branch -ne "main") {
    Write-Host "Not on main (current: $branch). Checkout main first: git checkout main"
    exit 1
}

Write-Host "Deleting local branches..."
foreach ($b in $localToDelete) {
    $exists = git branch --list $b 2>$null
    if ($exists) {
        git branch -D $b
        Write-Host "  deleted local: $b"
    }
}

Write-Host "Deleting remote branches..."
foreach ($b in $remoteToDelete) {
    git push origin --delete $b 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "  deleted remote: $b" }
}

git fetch --prune
Write-Host "Done. Remaining branches:"
git branch -a
