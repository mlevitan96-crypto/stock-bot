# Comprehensive Dashboard and UW API Monitoring Fix

## Issues Identified

1. **Dashboard Flask not installed** - Fixed by ensuring venv is used
2. **UW API endpoints not displayed** - Need to verify sre_monitoring returns them
3. **UW endpoint health checking** - Currently only checks cache, not actual connectivity
4. **Dashboard SRE endpoint** - May not be properly calling get_sre_health()

## Current Status

### ✅ What's Working

1. **sre_monitoring.py**:
   - `get_comprehensive_health()` includes `uw_api_endpoints` (line 607)
   - `check_uw_api_health()` checks all endpoints from `UW_ENDPOINT_CONTRACTS`
   - Returns health status for each endpoint

2. **dashboard.py**:
   - `/api/sre/health` endpoint exists and calls `get_sre_health()`
   - SRE dashboard HTML includes "UW API Endpoints Health" section
   - Frontend JavaScript renders `uw_api_endpoints` from response

### ⚠️ Potential Issues

1. **UW endpoint health checking method**:
   - Currently checks cache freshness and error logs
   - Does NOT make actual API calls (this is intentional to avoid quota usage)
   - If cache is stale, endpoints show as "stale" or "no_cache"
   - If UW daemon isn't running, all endpoints show as "daemon_not_running"

2. **UW daemon status**:
   - If `uw_flow_daemon.py` or `uw_integration_full.py` isn't running, cache won't update
   - This causes all UW endpoints to show as unhealthy

## Fixes Applied

### Script 1: `COLLECT_ALL_LOGS_AND_FIX.sh`
- Collects all dashboard logs
- Tests all API endpoints
- Tests UW API connectivity
- Checks UW cache status
- Creates comprehensive diagnostic report

### Script 2: `FIX_DASHBOARD_AND_UW_MONITORING.sh`
- Ensures Python venv is set up
- Verifies dashboard code structure
- Tests UW API connectivity
- Checks UW daemon status
- Restarts dashboard with fixes

### Script 3: `COMPREHENSIVE_DASHBOARD_FIX.py`
- Analyzes dashboard.py code structure
- Verifies sre_monitoring.py structure
- Tests /api/sre/health endpoint
- Provides detailed fix recommendations

## How to Use

### Step 1: Collect Diagnostics
```bash
cd ~/stock-bot
./COLLECT_ALL_LOGS_AND_FIX.sh
```

This creates `diagnostics_full_YYYYMMDD_HHMMSS/` with:
- All dashboard logs
- SRE health JSON
- All API endpoint responses
- UW API connectivity test
- UW cache status
- Process status
- Summary JSON

### Step 2: Review Summary
```bash
cat diagnostics_full_*/SUMMARY.json | python3 -m json.tool
```

### Step 3: Apply Fixes
```bash
./FIX_DASHBOARD_AND_UW_MONITORING.sh
```

### Step 4: Verify
```bash
# Test dashboard
curl http://localhost:5000/api/sre/health | python3 -m json.tool | grep -A 5 "uw_api_endpoints"

# Run comprehensive check
python3 COMPREHENSIVE_DASHBOARD_FIX.py
```

## Expected Results

After fixes, you should see:

1. **Dashboard running** on port 5000
2. **SRE endpoint** (`/api/sre/health`) returning:
   ```json
   {
     "uw_api_endpoints": {
       "market_tide": {"status": "healthy", ...},
       "greek_exposure": {"status": "healthy", ...},
       ...
     }
   }
   ```

3. **SRE Dashboard** showing:
   - Signal Components Health section
   - **UW API Endpoints Health section** (with all endpoints)
   - Trade Engine & Execution Pipeline section

## Troubleshooting

### If UW endpoints show as "daemon_not_running":
```bash
# Check if UW daemon is running
pgrep -f "uw.*daemon|uw_flow_daemon|uw_integration"

# Start UW daemon
python uw_flow_daemon.py
# OR
python uw_integration_full.py
```

### If UW endpoints show as "stale" or "no_cache":
```bash
# Check cache file
ls -lh data/uw_flow_cache.json

# Check cache age
python3 -c "import time, os; print(f\"Cache age: {(time.time() - os.path.getmtime('data/uw_flow_cache.json'))/60:.1f} minutes\")"
```

### If dashboard doesn't show UW endpoints:
1. Check `/api/sre/health` response includes `uw_api_endpoints`
2. Check browser console for JavaScript errors
3. Verify SRE dashboard HTML includes UW endpoints section

## Code Verification

### sre_monitoring.py (lines 583-615)
```python
def get_comprehensive_health(self) -> Dict[str, Any]:
    result = {
        ...
        "uw_api_endpoints": {},
        ...
    }
    
    # Check UW API endpoints
    uw_health = self.check_uw_api_health()
    result["uw_api_endpoints"] = {
        name: {
            "status": h.status,
            "error_rate_1h": h.error_rate_1h,
            "avg_latency_ms": h.avg_latency_ms,
            "last_error": h.last_error
        }
        for name, h in uw_health.items()
    }
```

### dashboard.py (lines 1125-1152)
```javascript
// Update API endpoints
const apis = data.uw_api_endpoints || {};
const apiContainer = document.getElementById('api-container');
if (Object.keys(apis).length === 0) {
    apiContainer.innerHTML = '<div class="loading">No API endpoints found</div>';
} else {
    apiContainer.innerHTML = Object.entries(apis).map(([name, health]) => {
        // Render each endpoint...
    }).join('');
}
```

## Next Steps

1. Run `COLLECT_ALL_LOGS_AND_FIX.sh` to gather all diagnostic data
2. Review `diagnostics_full_*/SUMMARY.json` for issues
3. Run `FIX_DASHBOARD_AND_UW_MONITORING.sh` to apply fixes
4. Verify dashboard shows UW endpoints in SRE tab
5. If issues persist, check UW daemon is running and cache is being updated
