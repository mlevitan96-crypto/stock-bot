# Deployment Instructions - Hardened Code

## Quick Deploy

Run on droplet:
```bash
cd /root/stock-bot
git pull origin main
systemctl restart trading-bot.service
python3 check_current_status.py
```

## What Was Fixed

1. ✅ **Portfolio Delta Gate** - Fixed to allow trading with 0 positions
2. ✅ **All API calls** - Hardened with error handling
3. ✅ **All state files** - Corruption handling + self-healing
4. ✅ **All divisions** - Guarded against divide by zero
5. ✅ **All type conversions** - Validated with safe defaults
6. ✅ **All dict/list access** - Made safe with .get() and length checks
7. ✅ **Syntax errors** - Fixed indentation issues

## Expected Behavior After Deployment

- ✅ Bot should NOT be blocked by `portfolio_already_70pct_long_delta` when there are 0 positions
- ✅ Bot should continue operating even if API calls fail
- ✅ Bot should process signals and place orders if quality thresholds are met
- ✅ Bot should self-heal from state file corruption

## Verification

After deployment, check:
```bash
# Check recent gate events - should NOT see portfolio_delta blocking with 0 positions
tail -30 logs/gate.jsonl | grep portfolio_already_70pct_long_delta

# Check recent cycles for orders
tail -10 logs/run.jsonl | jq -r '.clusters, .orders'

# Check recent orders
tail -20 logs/orders.jsonl | jq -r '.symbol, .action'
```
