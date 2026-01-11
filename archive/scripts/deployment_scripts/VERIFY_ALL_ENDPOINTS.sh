#!/bin/bash
# Comprehensive verification script for all 11 UW API endpoints

cd ~/stock-bot

echo "=========================================="
echo "COMPREHENSIVE ENDPOINT VERIFICATION"
echo "=========================================="
echo ""

# Check daemon status
echo "[1] UW Daemon Status:"
if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    echo "✅ UW daemon is running"
    ps aux | grep -E "uw.*daemon|uw_flow_daemon" | grep -v grep | head -1
else
    echo "❌ UW daemon is NOT running"
    exit 1
fi
echo ""

# Check recent log activity for new endpoints
echo "[2] Recent Endpoint Activity (last 100 lines):"
if [ -f "logs/uw_daemon.log" ]; then
    echo "Checking for new endpoint calls..."
    tail -100 logs/uw_daemon.log | grep -E "Updated|Error|market_tide|oi_change|etf_flow|iv_rank|shorts_ftds|max_pain|greek|greeks" | tail -30
    echo ""
    
    # Count endpoint updates
    echo "Endpoint update counts:"
    tail -500 logs/uw_daemon.log | grep -c "Updated market_tide" && echo "  market_tide: ✅" || echo "  market_tide: ❌"
    tail -500 logs/uw_daemon.log | grep -c "Updated oi_change" && echo "  oi_change: ✅" || echo "  oi_change: ❌"
    tail -500 logs/uw_daemon.log | grep -c "Updated etf_flow" && echo "  etf_flow: ✅" || echo "  etf_flow: ❌"
    tail -500 logs/uw_daemon.log | grep -c "Updated iv_rank" && echo "  iv_rank: ✅" || echo "  iv_rank: ❌"
    tail -500 logs/uw_daemon.log | grep -c "Updated ftd_pressure" && echo "  shorts_ftds: ✅" || echo "  shorts_ftds: ❌"
    tail -500 logs/uw_daemon.log | grep -c "Updated greek_exposure" && echo "  greek_exposure: ✅" || echo "  greek_exposure: ❌"
    tail -500 logs/uw_daemon.log | grep -c "Updated greeks" && echo "  greeks: ✅" || echo "  greeks: ❌"
    tail -500 logs/uw_daemon.log | grep -c "Updated max_pain" && echo "  max_pain: ✅" || echo "  max_pain: ❌"
else
    echo "⚠️  No log file found"
fi
echo ""

# Check cache for enriched signals
echo "[3] Cache Status - Enriched Signals:"
python3 << 'PYEOF'
import json
import time
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
if not cache_file.exists():
    print("❌ Cache file not found")
    exit(1)

cache_data = json.loads(cache_file.read_text())
sample_symbol = [k for k in cache_data.keys() if not k.startswith("_")][0] if cache_data else None

if not sample_symbol:
    print("❌ No ticker data in cache")
    exit(1)

symbol_data = cache_data.get(sample_symbol, {})
if isinstance(symbol_data, str):
    try:
        symbol_data = json.loads(symbol_data)
    except:
        symbol_data = {}

print(f"Sample symbol: {sample_symbol}")
print("")

# Check all 11 endpoints
endpoints_status = {}

# 1. option_flow (via flow_trades)
flow_trades = symbol_data.get("flow_trades", [])
endpoints_status["option_flow"] = len(flow_trades) > 0

# 2. dark_pool
dark_pool = symbol_data.get("dark_pool", {})
endpoints_status["dark_pool"] = bool(dark_pool)

# 3. greek_exposure (part of greeks)
greeks = symbol_data.get("greeks", {})
endpoints_status["greek_exposure"] = bool(greeks.get("gamma_exposure") or greeks.get("total_gamma"))

# 4. greeks (basic)
endpoints_status["greeks"] = bool(greeks)

# 5. iv_rank
iv_rank = symbol_data.get("iv_rank", {})
endpoints_status["iv_rank"] = bool(iv_rank)

# 6. market_tide (market-wide)
market_tide = cache_data.get("_market_tide", {})
endpoints_status["market_tide"] = bool(market_tide.get("data"))

# 7. max_pain (part of greeks)
endpoints_status["max_pain"] = bool(greeks.get("max_pain"))

# 8. net_impact (market-wide)
top_net = cache_data.get("_top_net_impact", {})
endpoints_status["net_impact"] = bool(top_net.get("data"))

# 9. oi_change
oi_change = symbol_data.get("oi_change", {})
endpoints_status["oi_change"] = bool(oi_change)

# 10. etf_flow
etf_flow = symbol_data.get("etf_flow", {})
endpoints_status["etf_flow"] = bool(etf_flow)

# 11. shorts_ftds (stored as ftd_pressure)
ftd_pressure = symbol_data.get("ftd_pressure", {})
endpoints_status["shorts_ftds"] = bool(ftd_pressure)

print("Endpoint Status:")
for endpoint, status in endpoints_status.items():
    status_icon = "✅" if status else "❌"
    print(f"  {status_icon} {endpoint}")

print("")
print(f"Total endpoints found: {sum(endpoints_status.values())}/11")

# Show details for found endpoints
print("")
print("Details:")
if endpoints_status["option_flow"]:
    print(f"  option_flow: {len(flow_trades)} trades")
if endpoints_status["dark_pool"]:
    print(f"  dark_pool: {dark_pool.get('print_count', 0)} prints")
if endpoints_status["greek_exposure"] or endpoints_status["greeks"]:
    print(f"  greeks: {len(greeks)} fields")
if endpoints_status["iv_rank"]:
    print(f"  iv_rank: {iv_rank}")
if endpoints_status["market_tide"]:
    last_update = market_tide.get("last_update", 0)
    age_min = (time.time() - last_update) / 60 if last_update else 999
    print(f"  market_tide: age {age_min:.1f} min")
if endpoints_status["net_impact"]:
    last_update = top_net.get("last_update", 0)
    age_min = (time.time() - last_update) / 60 if last_update else 999
    print(f"  net_impact: age {age_min:.1f} min")
if endpoints_status["oi_change"]:
    print(f"  oi_change: {oi_change}")
if endpoints_status["etf_flow"]:
    print(f"  etf_flow: {etf_flow}")
if endpoints_status["shorts_ftds"]:
    print(f"  shorts_ftds: {ftd_pressure}")
if endpoints_status["max_pain"]:
    print(f"  max_pain: {greeks.get('max_pain')}")
PYEOF

echo ""
echo "[4] Next Steps:"
echo "  - If endpoints show ❌, wait 5-15 minutes for polling intervals"
echo "  - Monitor logs: tail -f logs/uw_daemon.log"
echo "  - Re-run this script: ./VERIFY_ALL_ENDPOINTS.sh"
echo ""
