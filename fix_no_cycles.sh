#!/bin/bash
# Force fix - clear freezes and verify bot is running

cd /root/stock-bot

echo "=========================================="
echo "FORCE FIX - NO CYCLES RUNNING"
echo "=========================================="
echo ""

# 1. Check if bot is running
echo "1. Checking bot process..."
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Bot process is running"
    ps aux | grep "python.*main.py" | grep -v grep | head -1
else
    echo "❌ Bot process NOT running!"
    echo "Starting bot..."
    systemctl start trading-bot.service
    sleep 5
fi
echo ""

# 2. Check and clear freezes
echo "2. Checking freezes..."
if [ -f "state/governor_freezes.json" ]; then
    python3 << 'EOF'
import json
from pathlib import Path
from datetime import datetime, timezone

freeze_file = Path("state/governor_freezes.json")
if freeze_file.exists():
    data = json.load(open(freeze_file))
    active = [k for k, v in data.items() if v.get("active", False)]
    if active:
        print(f"⚠️  Active freezes found: {active}")
        for key in active:
            data[key]["active"] = False
            data[key]["cleared_at"] = datetime.now(timezone.utc).isoformat()
        json.dump(data, open(freeze_file, 'w'), indent=2)
        print(f"✅ Cleared freezes: {active}")
    else:
        print("✅ No active freezes")
else:
    print("✅ No freeze file")
EOF
else
    echo "✅ No freeze file"
fi
echo ""

# 3. Check latest cycle
echo "3. Latest cycle status..."
if [ -f "logs/run.jsonl" ]; then
    tail -1 logs/run.jsonl | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Latest: {d.get('ts', 'N/A')}\")" 2>/dev/null || echo "Could not parse"
else
    echo "No run.jsonl file"
fi
echo ""

# 4. Verify fixes in code
echo "4. Verifying fixes..."
python3 << 'EOF'
import sys
sys.path.insert(0, '/root/stock-bot')
import uw_composite_v2

threshold = uw_composite_v2.get_threshold("AAPL", "base")
flow_weight = uw_composite_v2.get_weight("options_flow", "mixed")

print(f"Threshold: {threshold:.2f} (expected 2.7)")
print(f"Flow weight: {flow_weight:.3f} (expected 2.4)")

if abs(threshold - 2.7) < 0.1 and abs(flow_weight - 2.4) < 0.1:
    print("✅ All fixes verified")
else:
    print("❌ Fixes not working correctly!")
EOF
echo ""

# 5. Check for errors in recent logs
echo "5. Recent errors..."
if [ -f "logs/system.jsonl" ]; then
    tail -50 logs/system.jsonl | grep -i error | tail -5 || echo "No recent errors"
else
    echo "No system.jsonl"
fi
echo ""

echo "=========================================="
echo "FIX COMPLETE"
echo "=========================================="
