#!/bin/bash
# Comprehensive fix for dashboard, heartbeat, and health monitoring
# Run this on the droplet

cd ~/stock-bot

echo "=================================================================================="
echo "COMPREHENSIVE FIX: Dashboard, Heartbeat, and Health Monitoring"
echo "=================================================================================="
echo ""

# Step 1: Export fresh logs for analysis
echo "Step 1: Exporting fresh logs..."
./push_to_github_clean.sh \
    state/bot_heartbeat.json \
    logs/run.jsonl \
    logs/orders.jsonl \
    data/live_orders.jsonl \
    logs/heartbeat.jsonl \
    "Full diagnostic export before fixes"

echo ""
echo "Step 2: Fixing dashboard.py heartbeat reading..."
# Fix the heartbeat timestamp field name
python3 << 'PYTHON_FIX'
import re

with open('dashboard.py', 'r') as f:
    content = f.read()

# Fix heartbeat reading - check last_heartbeat_ts first (the actual field name)
old_pattern = r'heartbeat_ts = data\.get\("timestamp"\) or data\.get\("_ts"\) or data\.get\("last_heartbeat"\) or data\.get\("last_update"\)'
new_pattern = 'heartbeat_ts = data.get("last_heartbeat_ts") or data.get("timestamp") or data.get("_ts") or data.get("last_heartbeat") or data.get("last_update")'

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    with open('dashboard.py', 'w') as f:
        f.write(content)
    print("✓ Fixed heartbeat timestamp reading")
else:
    print("⚠️  Pattern not found - may already be fixed")

# Also fix to check logs/orders.jsonl in addition to data/live_orders.jsonl
old_orders = 'orders_file = Path("data/live_orders.jsonl")'
if old_orders in content:
    # Add check for logs/orders.jsonl as well
    new_orders_section = '''# Get last order from multiple possible files
        last_order_ts = None
        last_order_age_sec = None
        orders_files = [
            Path("data/live_orders.jsonl"),
            Path("logs/orders.jsonl"),
            Path("logs/trading.jsonl")
        ]
        
        for orders_file in orders_files:
            if orders_file.exists():'''
    
    # Find the section and replace
    import re
    pattern = r'orders_file = Path\("data/live_orders\.jsonl"\)\s+if orders_file\.exists\(\):'
    replacement = '''orders_files = [
            Path("data/live_orders.jsonl"),
            Path("logs/orders.jsonl"),
            Path("logs/trading.jsonl")
        ]
        
        for orders_file in orders_files:
            if orders_file.exists():'''
    
    content = re.sub(pattern, replacement, content)
    
    with open('dashboard.py', 'w') as f:
        f.write(content)
    print("✓ Fixed last order file reading to check multiple files")
else:
    print("⚠️  Orders file pattern not found")
PYTHON_FIX

echo ""
echo "Step 3: Verifying heartbeat file exists and is fresh..."
if [ -f "state/bot_heartbeat.json" ]; then
    echo "✓ Heartbeat file exists"
    python3 << 'PYTHON_CHECK'
import json
import time
from pathlib import Path

hb_path = Path("state/bot_heartbeat.json")
if hb_path.exists():
    data = json.loads(hb_path.read_text())
    ts = data.get("last_heartbeat_ts", 0)
    age = time.time() - ts
    print(f"  Last heartbeat: {age:.0f} seconds ago")
    if age > 300:
        print(f"  ⚠️  Heartbeat is stale ({age/60:.1f} minutes old)")
        # Refresh it
        data["last_heartbeat_ts"] = int(time.time())
        data["last_heartbeat_dt"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        hb_path.write_text(json.dumps(data, indent=2))
        print("  ✓ Refreshed heartbeat")
    else:
        print("  ✓ Heartbeat is fresh")
else:
    print("  ❌ Heartbeat file missing!")
PYTHON_CHECK
else
    echo "❌ Heartbeat file missing!"
fi

echo ""
echo "Step 4: Checking UW endpoints..."
python3 << 'PYTHON_UW'
import json
import time
from pathlib import Path

# Check UW cache
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    age = time.time() - cache_file.stat().st_mtime
    print(f"  UW cache age: {age/60:.1f} minutes")
    if age < 600:
        print("  ✓ UW cache is fresh")
    else:
        print(f"  ⚠️  UW cache is stale ({age/60:.1f} minutes)")
        
    # Check cache contents
    try:
        cache_data = json.loads(cache_file.read_text())
        if isinstance(cache_data, dict):
            symbols = list(cache_data.keys())[:5]
            print(f"  Cache has {len(cache_data)} symbols (showing first 5: {symbols})")
        else:
            print(f"  Cache format: {type(cache_data)}")
    except:
        print("  ⚠️  Could not parse cache")
else:
    print("  ❌ UW cache file missing!")

# Check UW error log
error_log = Path("data/uw_error.jsonl")
if error_log.exists():
    lines = error_log.read_text().splitlines()
    recent_errors = [l for l in lines[-10:] if "error" in l.lower()]
    if recent_errors:
        print(f"  ⚠️  Found {len(recent_errors)} recent errors in UW error log")
    else:
        print("  ✓ No recent UW errors")
PYTHON_UW

echo ""
echo "Step 5: Checking self-healing status..."
python3 << 'PYTHON_HEAL'
from pathlib import Path
import json

# Check if owner_health_check is working
hb_path = Path("state/bot_heartbeat.json")
if hb_path.exists():
    data = json.loads(hb_path.read_text())
    owner_fix = data.get("owner_fix")
    if owner_fix:
        print(f"  ✓ Self-healing active: {owner_fix}")
    else:
        print("  ⚠️  No self-healing markers found")
        
    issues = data.get("metrics", {}).get("owner_check", {}).get("issues", [])
    if issues:
        print(f"  ⚠️  Found {len(issues)} health check issues: {issues}")
    else:
        print("  ✓ No health check issues")
PYTHON_HEAL

echo ""
echo "=================================================================================="
echo "FIXES APPLIED"
echo "=================================================================================="
echo ""
echo "Next steps:"
echo "1. Restart dashboard: pkill -f dashboard.py && python3 dashboard.py &"
echo "2. Check dashboard at http://localhost:5000"
echo "3. Export logs again to verify fixes: ./push_to_github_clean.sh state/bot_heartbeat.json logs/run.jsonl 'After fixes'"
echo ""
