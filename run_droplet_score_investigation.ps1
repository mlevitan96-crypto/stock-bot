# PowerShell script to run score stagnation investigation on droplet
# This bypasses Python execution issues

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "CONNECTING TO DROPLET FOR SCORE STAGNATION INVESTIGATION" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Try to find Python
$pythonPath = $null
$possiblePaths = @(
    "python",
    "python3", 
    "py",
    "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe",
    "$env:ProgramFiles\Python*\python.exe"
)

foreach ($path in $possiblePaths) {
    try {
        $fullPath = Get-Command $path -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source
        if ($fullPath -and (Test-Path $fullPath)) {
            $pythonPath = $fullPath
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonPath) {
    Write-Host "ERROR: Could not find Python executable" -ForegroundColor Red
    Write-Host "Please ensure Python is installed and in your PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "Using Python: $pythonPath" -ForegroundColor Green
Write-Host ""

# Run the investigation script
try {
    & $pythonPath run_droplet_investigation.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Script exited with code: $LASTEXITCODE" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR: Failed to run investigation script: $_" -ForegroundColor Red
    exit 1
}
