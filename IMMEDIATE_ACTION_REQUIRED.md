# IMMEDIATE ACTION REQUIRED - NO TRADES

## Status: 🔴 CRITICAL - Trading Not Active

## Quick Diagnosis

Run these commands on the droplet:

```bash
cd ~/stock-bot
python3 fix_trading_issues.py
python3 diagnose_no_trades.py
```

## Most Common Issues Preventing Trades

### 1. **Bot Not Running** ⚠️ CRITICAL
- **Check**: `ps aux | grep "python.*main.py"`
- **Fix**: Restart bot via systemd or screen session
- **Command**: `systemctl restart trading-bot.service` or `screen -dmS trading bash -c "cd ~/stock-bot && python3 main.py"`

### 2. **UW Daemon Not Running** ⚠️ CRITICAL
- **Check**: `ps aux | grep "uw_flow_daemon"`
- **Fix**: Restart daemon
- **Command**: `systemctl restart trading-bot.service`

### 3. **Cache Stale or Missing** ⚠️ CRITICAL
- **Check**: `ls -lh data/uw_flow_cache.json`
- **Fix**: Restart UW daemon to refresh cache
- **Expected**: Cache should be < 10 minutes old during market hours

### 4. **Freeze Flags Active** ⚠️ CRITICAL
- **Check**: `cat state/freeze_flags.json`
- **Fix**: **MANUAL INTERVENTION REQUIRED** - Review freeze reasons and clear flags
- **Location**: `state/freeze_flags.json`

### 5. **Adaptive Weights Not Initialized** ⚠️ HIGH
- **Check**: `python3 -c "import json; print(len(json.load(open('state/signal_weights.json')).get('weight_bands', {})))"`
- **Fix**: Run `fix_trading_issues.py` or `python3 reset_adaptive_weights.py`
- **Expected**: 21 components initialized

### 6. **Self-Healing Threshold Raised** ⚠️ MEDIUM
- **Check**: `cat state/self_healing_threshold.json`
- **Fix**: Automatically resets after 24 hours or winning trade
- **Impact**: Raises MIN_EXEC_SCORE by 0.5 points (from 2.0 to 2.5)

### 7. **Market Closed** ℹ️ INFO
- **Check**: Current time in ET (9:30 AM - 4:00 PM ET, Mon-Fri)
- **Fix**: Wait for market to open

### 8. **No Signals Generated** ⚠️ HIGH
- **Check**: `tail -20 data/uw_attribution.jsonl` or `tail -20 logs/attribution.jsonl`
- **Fix**: Verify UW daemon is running and cache is fresh
- **Expected**: Signals should be generated every cycle

### 9. **Signals Below Threshold** ⚠️ MEDIUM
- **Check**: Look at recent signals in attribution.jsonl - check `score` field
- **Fix**: Signals need score >= MIN_EXEC_SCORE (default 2.0, or 2.5 if self-healing activated)
- **Impact**: Low scores won't pass the entry gate

### 10. **Expectancy Gate Blocking** ⚠️ MEDIUM
- **Check**: Look for "expectancy_blocked" in logs
- **Fix**: Expectancy gate blocks trades with negative EV in certain stages
- **Impact**: Even high scores can be blocked if expectancy is too low

### 11. **At Position Capacity** ⚠️ MEDIUM
- **Check**: `python3 -c "import alpaca_trade_api as api; from dotenv import load_dotenv; import os; load_dotenv(); a = api.REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), os.getenv('ALPACA_BASE_URL')); print(len(a.list_positions()))"`
- **Fix**: Wait for positions to close or manually close some
- **Max**: 16 concurrent positions

### 12. **Symbol on Cooldown** ℹ️ INFO
- **Check**: Look for "symbol_on_cooldown" in logs
- **Fix**: Wait 15 minutes after last trade in symbol
- **Impact**: Prevents overtrading same symbol

## Execution Gates (All Must Pass)

A signal must pass ALL of these gates to trade:

1. ✅ **Composite Score** >= MIN_EXEC_SCORE (2.0 default, or 2.5 if self-healing active)
2. ✅ **Expectancy Gate** - EV must meet stage-specific floor
3. ✅ **Not Frozen** - No active freeze flags
4. ✅ **Position Capacity** - < 16 concurrent positions
5. ✅ **Symbol Cooldown** - Not traded in last 15 minutes
6. ✅ **Risk Limits** - Symbol/sector exposure within limits
7. ✅ **Market Open** - Trading hours (9:30 AM - 4:00 PM ET)
8. ✅ **UW Cache Fresh** - Data < 10 minutes old
9. ✅ **Adaptive Weights** - All 21 components initialized
10. ✅ **Regime Gate** - Symbol profile allows trading in current regime

## Diagnostic Commands

```bash
# Check bot status
ps aux | grep "python.*main.py"

# Check UW daemon
ps aux | grep "uw_flow_daemon"

# Check cache age
stat -c %Y data/uw_flow_cache.json | xargs -I {} date -d @{} +"%Y-%m-%d %H:%M:%S"

# Check freeze flags
cat state/freeze_flags.json | jq 'to_entries | map(select(.value.active == true))'

# Check recent signals
tail -20 data/uw_attribution.jsonl | jq -r '.score, .decision'

# Check positions
python3 -c "import alpaca_trade_api as api; from dotenv import load_dotenv; import os; load_dotenv(); a = api.REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), os.getenv('ALPACA_BASE_URL')); print(f\"Positions: {len(a.list_positions())}\")"

# Check adaptive weights
python3 -c "import json; w = json.load(open('state/signal_weights.json')); print(f\"Components: {len(w.get('weight_bands', {}))}\")"

# Check self-healing threshold
cat state/self_healing_threshold.json | jq '.adjustment, .consecutive_losses'
```

## Immediate Fixes

1. **Run auto-fix script**:
   ```bash
   python3 fix_trading_issues.py
   ```

2. **Run full diagnosis**:
   ```bash
   python3 diagnose_no_trades.py
   ```

3. **Check logs for signal generation**:
   ```bash
   tail -50 logs/bot.log | grep -E "cluster|composite_score|decide_and_execute"
   ```

4. **Check for blocked trades**:
   ```bash
   tail -50 logs/bot.log | grep -E "BLOCKED|gate|rejected"
   ```

5. **Restart bot if needed**:
   ```bash
   systemctl restart trading-bot.service
   # OR
   screen -dmS trading bash -c "cd ~/stock-bot && python3 main.py"
   ```

## What to Look For in Logs

- **"DEBUG decide_and_execute: Processing X clusters"** - Signals are being generated
- **"BLOCKED by score_below_min"** - Scores too low
- **"BLOCKED by expectancy_blocked"** - Expectancy gate blocking
- **"BLOCKED by max_positions_reached"** - At capacity
- **"BLOCKED by symbol_on_cooldown"** - Cooldown period
- **"No clusters found"** - No signals generated

## Next Steps

1. ✅ Run `fix_trading_issues.py` to auto-fix common issues
2. ✅ Run `diagnose_no_trades.py` for full diagnosis
3. ✅ Check logs for signal generation and blocking reasons
4. ✅ Verify market is open
5. ✅ Monitor for 10-15 minutes after fixes

## Expected Behavior

- **During Market Hours**: Bot should process signals every cycle (every 2 minutes)
- **Signal Generation**: Should see clusters being generated from UW cache
- **Trading**: Should see orders being placed when signals pass all gates
- **Logs**: Should see "DEBUG decide_and_execute" messages with cluster counts

## If Still No Trades After Fixes

1. Check if signals are being generated (look for clusters in logs)
2. Check signal scores (are they >= MIN_EXEC_SCORE?)
3. Check expectancy gate (are signals being blocked by EV?)
4. Check position capacity (are we at 16/16?)
5. Check freeze flags (are any still active?)
6. Check market hours (is market actually open?)

---

**Last Updated**: 2025-01-XX
**Status**: 🔴 CRITICAL - Investigation Required
