#!/bin/bash
# Verify risk management integration and bot status

echo "=== Bot Process Status ==="
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Bot is running"
    BOT_PID=$(pgrep -f "python.*main.py" | head -1)
    echo "   PID: $BOT_PID"
    echo "   Uptime: $(ps -p $BOT_PID -o etime= 2>/dev/null | xargs || echo 'unknown')"
else
    echo "❌ Bot is NOT running"
    echo "   Start it with: python3 main.py"
fi

echo ""
echo "=== Risk Management Code Integration ==="
if grep -q "run_risk_checks" main.py; then
    echo "✅ Risk checks found in main.py"
    echo "   Location: After position reconciliation"
else
    echo "❌ Risk checks NOT found in main.py"
fi

if grep -q "check_symbol_exposure\|check_sector_exposure" main.py; then
    echo "✅ Exposure checks found in main.py"
else
    echo "❌ Exposure checks NOT found in main.py"
fi

if grep -q "validate_order_size" main.py; then
    echo "✅ Order validation found in main.py"
else
    echo "❌ Order validation NOT found in main.py"
fi

echo ""
echo "=== Risk Management Module ==="
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from risk_management import run_risk_checks, get_risk_limits, is_paper_mode
    print('✅ Module imports successfully')
    mode = 'PAPER' if is_paper_mode() else 'LIVE'
    limits = get_risk_limits()
    print(f'✅ Mode: {mode}')
    print(f'✅ Daily loss limit: \${limits[\"daily_loss_dollar\"]}')
    print(f'✅ Max position: \${limits[\"max_position_dollar\"]}')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "=== Expected Behavior ==="
echo "Risk checks will run when:"
echo "  1. Bot completes a trading cycle"
echo "  2. After position reconciliation"
echo "  3. Before new orders are placed"
echo ""
echo "State files will be created on first run:"
echo "  - state/daily_start_equity.json (set at start of trading day)"
echo "  - state/peak_equity.json (tracks highest equity)"
echo "  - state/governor_freezes.json (if any freezes are triggered)"
echo ""
echo "To see risk checks in action, wait for next bot cycle and run:"
echo "  ./check_risk_logs.sh"
