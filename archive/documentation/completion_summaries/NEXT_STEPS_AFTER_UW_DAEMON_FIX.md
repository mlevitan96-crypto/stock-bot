# Next Steps After UW Daemon Fix

## Summary of Changes

Updated `uw_flow_daemon.py` to fetch **ALL 11 endpoints** shown in the dashboard:

### ✅ Now Fetching (11 endpoints):
1. **option_flow** - `/api/option-trades/flow-alerts` ✅
2. **dark_pool** - `/api/darkpool/{ticker}` ✅
3. **greek_exposure** - `/api/stock/{ticker}/greek-exposure` ✅ (FIXED endpoint)
4. **greeks** - `/api/stock/{ticker}/greeks` ✅ (ADDED - separate from greek_exposure)
5. **iv_rank** - `/api/stock/{ticker}/iv-rank` ✅ (ADDED)
6. **market_tide** - `/api/market/market-tide` ✅ (ADDED)
7. **max_pain** - `/api/stock/{ticker}/max-pain` ✅ (ADDED)
8. **net_impact** - `/api/market/top-net-impact` ✅ (already fetching)
9. **oi_change** - `/api/stock/{ticker}/oi-change` ✅ (ADDED)
10. **option_flow** - Already fetching ✅
11. **shorts_ftds** - `/api/shorts/{ticker}/ftds` ✅ (ADDED)

### Polling Intervals (Optimized for Rate Limits):
- `option_flow`: 2.5 min (most critical)
- `dark_pool_levels`: 10 min
- `greek_exposure`: 30 min
- `greeks`: 30 min
- `market_tide`: 5 min (market-wide)
- `top_net_impact`: 5 min (market-wide)
- `oi_change`: 15 min
- `etf_flow`: 30 min
- `iv_rank`: 30 min
- `shorts_ftds`: 60 min
- `max_pain`: 15 min

## Next Steps

### Step 1: Pull Updated Code
```bash
cd ~/stock-bot
git pull origin main
```

### Step 2: Restart UW Daemon
```bash
# Stop existing daemon
pkill -f "uw.*daemon|uw_flow_daemon"

# Wait a moment
sleep 2

# Start with updated code
cd ~/stock-bot
source venv/bin/activate
nohup python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &

# Verify it's running
sleep 3
pgrep -f "uw.*daemon|uw_flow_daemon" && echo "✅ UW daemon running" || echo "❌ Failed to start"
```

### Step 3: Wait for Data to Populate
The daemon will start fetching all endpoints. Wait:
- **5 minutes** for market-wide endpoints (market_tide, top_net_impact)
- **15-30 minutes** for per-ticker endpoints (oi_change, etf_flow, iv_rank, etc.)

### Step 4: Verify All Endpoints Are Fetching
```bash
cd ~/stock-bot

# Check UW daemon logs for new endpoints
tail -100 logs/uw_daemon.log | grep -E "market_tide|oi_change|etf_flow|iv_rank|shorts_ftds|max_pain|greeks"

# Check cache for enriched signals
python3 << 'PYEOF'
import json
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache_data = json.loads(cache_file.read_text())
    sample_symbol = [k for k in cache_data.keys() if not k.startswith("_")][0] if cache_data else None
    if sample_symbol:
        symbol_data = cache_data.get(sample_symbol, {})
        if isinstance(symbol_data, str):
            try:
                symbol_data = json.loads(symbol_data)
            except:
                symbol_data = {}
        
        print(f"Checking {sample_symbol} for enriched signals:")
        enriched_signals = {
            "greeks_gamma": symbol_data.get("greeks", {}).get("gamma_exposure") if symbol_data.get("greeks") else None,
            "etf_flow": symbol_data.get("etf_flow"),
            "oi_change": symbol_data.get("oi_change"),
            "iv_rank": symbol_data.get("iv_rank"),
            "ftd_pressure": symbol_data.get("ftd_pressure"),
        }
        
        for sig, value in enriched_signals.items():
            if value not in (None, 0, 0.0, "", []):
                print(f"  ✅ {sig}: {value}")
            else:
                print(f"  ❌ {sig}: not found")
        
        # Check market-wide data
        market_tide = cache_data.get("_market_tide", {}).get("data")
        if market_tide:
            print(f"  ✅ market_tide: found in cache metadata")
        else:
            print(f"  ❌ market_tide: not found in cache metadata")
PYEOF
```

### Step 5: Re-run Comprehensive Diagnostics
```bash
cd ~/stock-bot
./COMPREHENSIVE_FIX_ALL_SIGNALS.sh
```

This will show:
- All 11 endpoints being fetched
- Enriched signals appearing in cache
- Signal components being logged to learning engine

## Expected Results

After 15-30 minutes, you should see:
- ✅ All 11 endpoints showing "healthy" in dashboard
- ✅ Enriched signals (`greeks_gamma`, `etf_flow`, `market_tide`, `oi_change`, `iv_rank`, `ftd_pressure`) in cache
- ✅ 22 signal components being logged (already working)
- ✅ Learning engine receiving all signal components

## Rate Limit Impact

**Estimated API calls per day:**
- Current: ~13,000 calls/day
- Added endpoints: ~2,000 calls/day
- **Total: ~15,000 calls/day** (at limit, but manageable)

The SmartPoller will automatically adjust if rate limits are hit.
