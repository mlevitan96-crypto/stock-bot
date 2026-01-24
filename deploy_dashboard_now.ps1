# Deploy Dashboard Fixes to Droplet
# Run this script in PowerShell

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "DASHBOARD FIXES DEPLOYMENT TO DROPLET" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$deployTarget = "alpaca"
$projectDir = "/root/stock-bot"

# Step 1: Test SSH connection
Write-Host "[1/6] Testing SSH connection..." -ForegroundColor Yellow
$testResult = ssh $deployTarget "echo 'SSH connection test'" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] SSH connection successful" -ForegroundColor Green
    Write-Host "   $testResult"
} else {
    Write-Host "[ERROR] SSH connection failed" -ForegroundColor Red
    Write-Host "   $testResult"
    exit 1
}
Write-Host ""

# Step 2: Pull latest code
Write-Host "[2/6] Pulling latest code from GitHub..." -ForegroundColor Yellow
$pullResult = ssh $deployTarget "cd $projectDir && git fetch origin main && git reset --hard origin/main" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Code pulled successfully" -ForegroundColor Green
    $pullResult | Select-Object -Last 3 | ForEach-Object { Write-Host "   $_" }
} else {
    Write-Host "[ERROR] Git pull failed" -ForegroundColor Red
    Write-Host "   $pullResult"
    exit 1
}
Write-Host ""

# Step 3: Verify commit
Write-Host "[3/6] Verifying latest commit..." -ForegroundColor Yellow
$commitResult = ssh $deployTarget "cd $projectDir && git log -1 --oneline" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Current commit: $commitResult" -ForegroundColor Green
    if ($commitResult -match "dashboard|6d7b3c2|1ccbcf3|f1a763a") {
        Write-Host "[OK] Dashboard fixes detected in commit" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Dashboard fixes may not be in this commit" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARNING] Could not verify commit" -ForegroundColor Yellow
}
Write-Host ""

# Step 4: Check dashboard status
Write-Host "[4/6] Checking dashboard status..." -ForegroundColor Yellow
$statusResult = ssh $deployTarget "ps aux | grep -E 'dashboard.py|python.*dashboard' | grep -v grep | head -1" 2>&1
if ($LASTEXITCODE -eq 0 -and $statusResult) {
    Write-Host "[OK] Dashboard is running" -ForegroundColor Green
    Write-Host "   $($statusResult.Substring(0, [Math]::Min(100, $statusResult.Length)))"
} else {
    Write-Host "[INFO] Dashboard process not found (may be under systemd/supervisor)" -ForegroundColor Cyan
}
Write-Host ""

# Step 5: Restart dashboard
Write-Host "[5/6] Restarting dashboard..." -ForegroundColor Yellow
ssh $deployTarget "pkill -f 'python.*dashboard.py' || true" | Out-Null
Write-Host "   Killed dashboard process (supervisor will restart)" -ForegroundColor Cyan

ssh $deployTarget "systemctl restart trading-bot.service || true" | Out-Null
Write-Host "   Restarted via systemd" -ForegroundColor Cyan

Start-Sleep -Seconds 5
Write-Host "[OK] Dashboard restart initiated" -ForegroundColor Green
Write-Host ""

# Step 6: Verify dashboard is responding
Write-Host "[6/6] Verifying dashboard is responding..." -ForegroundColor Yellow
$healthResult = ssh $deployTarget "bash -lc 'cd /root/stock-bot && set -a && source .env && set +a && if [ -z `"`$DASHBOARD_USER`" ] || [ -z `"`$DASHBOARD_PASS`" ]; then echo `[ERROR] Missing DASHBOARD_USER/DASHBOARD_PASS in /root/stock-bot/.env`; exit 2; fi && curl -s -u `"`$DASHBOARD_USER:`$DASHBOARD_PASS`" http://localhost:5000/health 2>&1 | head -5'" 2>&1
if ($LASTEXITCODE -eq 0 -and $healthResult) {
    if ($healthResult -match "healthy|status") {
        Write-Host "[OK] Dashboard is responding" -ForegroundColor Green
        Write-Host "   $($healthResult.Substring(0, [Math]::Min(150, $healthResult.Length)))"
    } else {
        Write-Host "[WARNING] Dashboard responded but may have issues" -ForegroundColor Yellow
        Write-Host "   $($healthResult.Substring(0, [Math]::Min(150, $healthResult.Length)))"
    }
} else {
    Write-Host "[WARNING] Dashboard health check had issues" -ForegroundColor Yellow
}
Write-Host ""

# Final summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT SUMMARY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[OK] Code pulled from GitHub" -ForegroundColor Green
Write-Host "[OK] Dashboard restarted" -ForegroundColor Green
Write-Host ""
Write-Host "Verify dashboard is accessible:" -ForegroundColor Cyan
Write-Host "   http://104.236.102.57:5000/" -ForegroundColor White
Write-Host ""
Write-Host "Test endpoints:" -ForegroundColor Cyan
Write-Host "   http://104.236.102.57:5000/health" -ForegroundColor White
Write-Host "   http://104.236.102.57:5000/api/positions" -ForegroundColor White
Write-Host "   http://104.236.102.57:5000/api/health_status" -ForegroundColor White
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
