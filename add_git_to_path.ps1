# Add Git to PATH for Current Session
# Run this script or add its contents to your PowerShell profile

$gitPath = "C:\Program Files\Git\bin"
if (Test-Path $gitPath) {
    if ($env:PATH -notlike "*$gitPath*") {
        $env:PATH += ";$gitPath"
        Write-Host "✓ Added Git to PATH: $gitPath" -ForegroundColor Green
        Write-Host "  Git version: $(git --version)" -ForegroundColor Green
        Write-Host "`nNote: This only affects the current PowerShell session." -ForegroundColor Yellow
        Write-Host "To make it permanent, add to your PowerShell profile:" -ForegroundColor Yellow
        Write-Host '  `$env:PATH += ";C:\Program Files\Git\bin"' -ForegroundColor Cyan
    } else {
        Write-Host "✓ Git already in PATH" -ForegroundColor Green
    }
} else {
    Write-Host "✗ Git not found at: $gitPath" -ForegroundColor Red
    Write-Host "  Please install Git for Windows: https://git-scm.com/download/win" -ForegroundColor Yellow
}
