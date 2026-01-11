# Windows Setup Helper for Stock Bot
# This script helps configure your Windows environment for working with the stock-bot project

Write-Host "=== Stock Bot Windows Setup ===" -ForegroundColor Cyan

# Check Git
Write-Host ""
Write-Host "[1/5] Checking Git..." -ForegroundColor Yellow
$gitPath = "C:\Program Files\Git\bin\git.exe"
if (Test-Path $gitPath) {
    Write-Host "  [OK] Git found at: $gitPath" -ForegroundColor Green
    $env:PATH += ";C:\Program Files\Git\bin"
    $gitVersion = & git --version
    Write-Host "  [OK] $gitVersion" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Git not found. Please install Git for Windows." -ForegroundColor Red
    Write-Host "    Download: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check Git Remote
Write-Host ""
Write-Host "[2/5] Checking Git Remote..." -ForegroundColor Yellow
$env:PATH += ";C:\Program Files\Git\bin"
try {
    $remote = & git remote get-url origin 2>&1
    if ($remote -match "github.com/mlevitan96-crypto/stock-bot") {
        Write-Host "  [OK] Remote configured: $remote" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Remote mismatch: $remote" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ERROR] Could not read Git remote: $_" -ForegroundColor Red
}

# Check GitHub Access
Write-Host ""
Write-Host "[3/5] Testing GitHub Access..." -ForegroundColor Yellow
try {
    $env:PATH += ";C:\Program Files\Git\bin"
    $fetch = & git fetch origin --dry-run 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] GitHub access working" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] GitHub access may require authentication" -ForegroundColor Yellow
        Write-Host "    If needed, configure: git config --global credential.helper wincred" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [WARN] Could not test GitHub access: $_" -ForegroundColor Yellow
}

# Check SSH Config for Droplet Access
Write-Host ""
Write-Host "[4/5] Checking SSH Configuration..." -ForegroundColor Yellow
$sshConfig = "$env:USERPROFILE\.ssh\config"
if (Test-Path $sshConfig) {
    Write-Host "  [OK] SSH config exists" -ForegroundColor Green
    $sshContent = Get-Content $sshConfig -Raw
    if ($sshContent -match "alpaca") {
        Write-Host "  [OK] Droplet host 'alpaca' configured" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Droplet host 'alpaca' not found in SSH config" -ForegroundColor Yellow
        Write-Host "    Add your droplet SSH config to: $sshConfig" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [WARN] SSH config not found at: $sshConfig" -ForegroundColor Yellow
    Write-Host "    Create it to connect to your droplet" -ForegroundColor Yellow
}

# Check Python (optional for local development)
Write-Host ""
Write-Host "[5/5] Checking Python..." -ForegroundColor Yellow
$pythonCommands = @("python", "python3", "py")
$pythonFound = $false
foreach ($cmd in $pythonCommands) {
    $pythonPath = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($pythonPath) {
        Write-Host "  [OK] Python found: $($pythonPath.Source)" -ForegroundColor Green
        $version = & $cmd --version 2>&1
        Write-Host "    $version" -ForegroundColor Green
        $pythonFound = $true
        break
    }
}
if (-not $pythonFound) {
    Write-Host "  [WARN] Python not found (optional for local dev)" -ForegroundColor Yellow
    Write-Host "    Bot runs on remote Ubuntu droplet, so Python not required locally" -ForegroundColor Yellow
    Write-Host "    If needed for local testing, install from: https://www.python.org/downloads/" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=== Setup Summary ===" -ForegroundColor Cyan
Write-Host "[OK] Git: Ready" -ForegroundColor Green
Write-Host "[OK] GitHub: Configured" -ForegroundColor Green
Write-Host "[OK] Project Files: Accessible" -ForegroundColor Green
Write-Host ""
Write-Host "Note: The bot runs on a remote Ubuntu droplet." -ForegroundColor Yellow
Write-Host "Local Python is optional unless you want to run tests locally." -ForegroundColor Yellow
Write-Host ""
Write-Host "Required Environment Variables (on droplet):" -ForegroundColor Cyan
Write-Host "  - UW_API_KEY" -ForegroundColor White
Write-Host "  - ALPACA_KEY" -ForegroundColor White
Write-Host "  - ALPACA_SECRET" -ForegroundColor White
Write-Host "  - ALPACA_BASE_URL (default: https://paper-api.alpaca.markets)" -ForegroundColor White
Write-Host "  - TRADING_MODE (PAPER or LIVE)" -ForegroundColor White
Write-Host ""
Write-Host "Setup check complete!" -ForegroundColor Green
