# PowerShell script to check trading bot status
# Usage: .\check_status.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TRADING BOT STATUS CHECK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if data directory exists
$dataDir = "data"
$stateDir = "state"

if (-not (Test-Path $dataDir)) {
    Write-Host "[WARNING] Data directory does not exist" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
}

if (-not (Test-Path $stateDir)) {
    Write-Host "[WARNING] State directory does not exist" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
}

# Check Last Order
Write-Host "=== LAST ORDER STATUS ===" -ForegroundColor Green
$ordersFile = Join-Path $dataDir "live_orders.jsonl"
if (Test-Path $ordersFile) {
    $lastLine = Get-Content $ordersFile -Tail 1
    if ($lastLine) {
        try {
            $lastOrder = $lastLine | ConvertFrom-Json
            $orderTime = [DateTimeOffset]::FromUnixTimeSeconds($lastOrder._ts).LocalDateTime
            $age = (Get-Date) - $orderTime
            $ageHours = [math]::Round($age.TotalHours, 1)
            $ageMinutes = [math]::Round($age.TotalMinutes, 1)
            
            Write-Host "Last Order: $ageHours hours ago ($ageMinutes minutes)" -ForegroundColor $(if ($ageHours -gt 3) { "Yellow" } else { "Green" })
            Write-Host "  Time: $orderTime"
            Write-Host "  Event: $($lastOrder.event)"
            Write-Host "  Symbol: $($lastOrder.symbol)"
            Write-Host "  Side: $($lastOrder.side)"
            Write-Host "  Qty: $($lastOrder.qty)"
            
            if ($ageHours -gt 3) {
                $marketOpen = (Get-Date).Hour -ge 9 -and (Get-Date).Hour -lt 16 -and (Get-Date).DayOfWeek -ne [DayOfWeek]::Saturday -and (Get-Date).DayOfWeek -ne [DayOfWeek]::Sunday
                if ($marketOpen) {
                    Write-Host "  [WARNING] Market is open but no recent orders!" -ForegroundColor Yellow
                } else {
                    Write-Host "  [INFO] Market is closed - this is normal" -ForegroundColor Cyan
                }
            }
        } catch {
            Write-Host "[ERROR] Could not parse last order: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "[INFO] Orders file exists but is empty" -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] Orders file does not exist yet" -ForegroundColor Yellow
}

Write-Host ""

# Check Heartbeat/Doctor
Write-Host "=== DOCTOR/HEARTBEAT STATUS ===" -ForegroundColor Green
$heartbeatFiles = @(
    (Join-Path $stateDir "system_heartbeat.json"),
    (Join-Path $stateDir "heartbeat.json")
)

$heartbeatFound = $false
foreach ($hbFile in $heartbeatFiles) {
    if (Test-Path $hbFile) {
        $heartbeatFound = $true
        try {
            $heartbeat = Get-Content $hbFile | ConvertFrom-Json
            $hbTime = $null
            
            # Try different timestamp fields
            if ($heartbeat.timestamp) {
                $hbTime = [DateTimeOffset]::FromUnixTimeSeconds($heartbeat.timestamp).LocalDateTime
            } elseif ($heartbeat._ts) {
                $hbTime = [DateTimeOffset]::FromUnixTimeSeconds($heartbeat._ts).LocalDateTime
            } elseif ($heartbeat.last_heartbeat) {
                $hbTime = [DateTimeOffset]::FromUnixTimeSeconds($heartbeat.last_heartbeat).LocalDateTime
            }
            
            if ($hbTime) {
                $age = (Get-Date) - $hbTime
                $ageMinutes = [math]::Round($age.TotalMinutes, 1)
                
                $statusColor = if ($ageMinutes -lt 5) { "Green" } elseif ($ageMinutes -lt 30) { "Yellow" } else { "Red" }
                Write-Host "Last Heartbeat: $ageMinutes minutes ago" -ForegroundColor $statusColor
                Write-Host "  Time: $hbTime"
                Write-Host "  File: $hbFile"
                
                if ($ageMinutes -gt 30) {
                    Write-Host "  [CRITICAL] Heartbeat is very stale!" -ForegroundColor Red
                } elseif ($ageMinutes -gt 5) {
                    Write-Host "  [WARNING] Heartbeat is getting stale" -ForegroundColor Yellow
                } else {
                    Write-Host "  [OK] Heartbeat is fresh" -ForegroundColor Green
                }
            } else {
                Write-Host "[WARNING] Could not find timestamp in heartbeat file" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[ERROR] Could not parse heartbeat file: $_" -ForegroundColor Red
        }
        break
    }
}

if (-not $heartbeatFound) {
    Write-Host "[WARNING] Heartbeat file not found" -ForegroundColor Yellow
    Write-Host "  Checked: $($heartbeatFiles -join ', ')"
}

Write-Host ""

# Check if services are running (if process-compose is available)
Write-Host "=== SERVICE STATUS ===" -ForegroundColor Green
try {
    $pcStatus = process-compose ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $pcStatus
    } else {
        Write-Host "[INFO] process-compose not available or not running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[INFO] Could not check process-compose status" -ForegroundColor Yellow
}

Write-Host ""

# Try to check API endpoints
Write-Host "=== API ENDPOINT STATUS ===" -ForegroundColor Green
$endpoints = @(
    @{Url="http://localhost:8081/health"; Name="Main Bot Health"},
    @{Url="http://localhost:5000/health"; Name="Dashboard Health"}
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint.Url -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] $($endpoint.Name): Running" -ForegroundColor Green
            try {
                $data = $response.Content | ConvertFrom-Json
                if ($data.last_heartbeat_age_sec) {
                    $ageSec = $data.last_heartbeat_age_sec
                    $ageMin = [math]::Round($ageSec / 60, 1)
                    Write-Host "  Heartbeat age: $ageMin minutes"
                }
            } catch {
                # Not JSON or parse error, skip
            }
        }
    } catch {
        Write-Host "[INFO] $($endpoint.Name): Not responding" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Check complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
