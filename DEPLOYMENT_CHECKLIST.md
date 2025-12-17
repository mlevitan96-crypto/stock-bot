# Risk Management Deployment Checklist

**Date**: 2025-12-17  
**Status**: Ready for Deployment

---

## ✅ Pre-Deployment Verification

Before deploying, verify the following on your local machine:

- [x] Code committed and pushed to git
- [ ] Review `risk_management.py` for any mode-specific settings
- [ ] Ensure `TRADING_MODE` environment variable is set correctly (PAPER or LIVE)

---

## 🚀 Deployment Steps

### 1. **Deploy to Droplet**

```bash
cd /root/stock-bot
source venv/bin/activate
git pull origin main --no-rebase
./deploy.sh
```

This will:
- Pull latest code
- Deploy with zero-downtime
- Enrich cache with computed signals
- Start new dashboard instance

---

## ✅ Post-Deployment Verification

### 2. **Check Risk Management Module Loads**

```bash
python3 -c "from risk_management import get_risk_limits, is_paper_mode; print(f'Mode: {\"PAPER\" if is_paper_mode() else \"LIVE\"}'); print(f'Limits: {get_risk_limits()}')"
```

**Expected Output:**
- Shows current mode (PAPER or LIVE)
- Displays risk limits dictionary

---

### 3. **Verify Risk Checks Run in Main Loop**

Check the logs to see risk checks running:

```bash
tail -f logs/*.log | grep -i "risk_management"
```

**Expected:**
- `risk_management.checks_passed` events each cycle
- Daily P&L calculation logs
- Peak equity updates (if equity increases)

---

### 4. **Verify Freeze State File Created**

```bash
ls -la state/governor_freezes.json
ls -la state/peak_equity.json
ls -la state/daily_start_equity.json
```

**Expected:**
- Files created after first run
- `daily_start_equity.json` should have today's date
- `peak_equity.json` should show current peak

---

### 5. **Check Dashboard for Risk Metrics**

1. Open dashboard at `http://your-server:5000/`
2. Check cycle metrics include `risk_metrics` section
3. Verify:
   - Current equity
   - Peak equity
   - Daily P&L
   - Drawdown %
   - Mode (PAPER/LIVE)

---

## 🧪 Testing Risk Limits (Paper Mode)

### **Test Daily Loss Limit**

**Method 1: Monitor in Logs**
```bash
tail -f logs/*.log | grep -i "daily_loss"
```

**What to Watch:**
- Daily P&L calculation
- If daily loss exceeds limit, should see `freeze` event

**Method 2: Check State Files**
```bash
cat state/daily_start_equity.json
cat state/governor_freezes.json
```

---

### **Test Exposure Limits**

The exposure limits are checked **per-order**, so they will:
- Block orders that would exceed symbol exposure (10% of starting equity)
- Block orders that would exceed sector exposure (30% of starting equity)
- Log the block but **not freeze** (allows trading other symbols)

**Check for exposure blocks:**
```bash
tail -f logs/*.log | grep -i "exposure"
```

---

### **Test Order Validation**

Order validation happens in `submit_entry()` and will:
- Block orders exceeding 95% of buying power
- Block orders exceeding max position size ($825 PAPER, $300 LIVE)
- Block orders below min position size ($50)

**Check for validation blocks:**
```bash
tail -f logs/*.log | grep -i "order_validation"
```

---

## 🔍 Monitoring During Trading

### **Real-Time Risk Monitoring**

```bash
# Watch all risk-related events
tail -f logs/*.log | grep -E "(risk_management|freeze|daily_pnl|drawdown|exposure)"
```

---

### **Check Current Risk State**

```bash
# View current risk state
python3 -c "
from risk_management import run_risk_checks, get_starting_equity, load_peak_equity
import sys
sys.path.insert(0, '.')
from main import Config
try:
    from alpaca_trade_api import REST
    api = REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
    results = run_risk_checks(api)
    import json
    print(json.dumps(results, indent=2, default=str))
except Exception as e:
    print(f'Error: {e}')
"
```

**Expected Output:**
- `safe_to_trade: true/false`
- Current equity, peak equity, daily P&L
- All check results

---

## ⚠️ What Happens When Limits Are Breached

### **Daily Loss Limit:**
1. `freeze_trading()` is called
2. Freeze written to `state/governor_freezes.json`
3. Trading halts immediately (checked at start of `run_once()`)
4. Webhook alert sent (if configured)
5. Log event: `freeze.activated` with reason `daily_loss_dollar_limit` or `daily_loss_pct_limit`

### **Drawdown Limit:**
1. Same freeze process as above
2. Reason: `max_drawdown_exceeded`
3. Shows current vs peak equity and drawdown %

### **Equity Floor:**
1. Same freeze process
2. Reason: `account_equity_floor_breached`
3. Shows current equity vs floor

### **Exposure Limits:**
- **Does NOT freeze** - only blocks the specific order
- Logs: `risk_management.symbol_exposure_blocked` or `risk_management.sector_exposure_blocked`
- Trading continues for other symbols

### **Order Validation:**
- **Does NOT freeze** - only blocks the specific order
- Logs: `risk_management.order_validation_failed`
- Trading continues with corrected orders

---

## 🔧 Troubleshooting

### **Risk Management Module Not Found**

**Symptom:** Logs show `ImportError` for `risk_management`

**Fix:**
```bash
cd /root/stock-bot
source venv/bin/activate
python3 -c "import risk_management; print('OK')"
```

If error, check file exists:
```bash
ls -la risk_management.py
```

---

### **Wrong Mode Detected**

**Check current mode:**
```bash
echo $TRADING_MODE
python3 -c "from main import Config; print(Config.TRADING_MODE)"
```

**Fix:** Set environment variable:
```bash
export TRADING_MODE=PAPER  # or LIVE
# Then restart bot
```

---

### **Daily P&L Not Resetting**

**Check:** `state/daily_start_equity.json` date should match today

**Fix:** Delete and let it recreate:
```bash
rm state/daily_start_equity.json
# Next cycle will set new baseline
```

---

### **Peak Equity Not Updating**

**Check:** Current equity should be > peak equity for update

**Fix:** Manually check:
```bash
python3 -c "
from risk_management import load_peak_equity, update_peak_equity
peak = load_peak_equity()
print(f'Current peak: {peak}')
# Test update
new_peak = update_peak_equity(peak + 1)
print(f'New peak: {new_peak}')
"
```

---

## ✅ Success Criteria

After deployment, verify:

1. ✅ Risk management module loads without errors
2. ✅ Risk checks run each cycle (check logs)
3. ✅ State files are created (`peak_equity.json`, `daily_start_equity.json`)
4. ✅ Dashboard shows risk metrics in cycle summaries
5. ✅ Daily P&L calculates correctly (check logs)
6. ✅ Peak equity updates when account equity increases
7. ✅ No unexpected freezes during normal operation

---

## 🚨 Important Notes

1. **Freezes are Manual Override Only:**
   - Once frozen, must manually clear `state/governor_freezes.json`
   - Freezes are **never** auto-cleared for safety

2. **Daily P&L Resets Daily:**
   - Baseline set at first check of each day
   - Uses UTC date for consistency

3. **Exposure Limits Check Existing Positions:**
   - Checks current Alpaca positions
   - Uses `market_value` attribute from position objects

4. **Mode-Specific Limits:**
   - PAPER: $55k starting equity, higher limits
   - LIVE: $10k starting equity, stricter limits
   - Check mode before interpreting limits

---

## 📞 Next Steps After Successful Deployment

1. **Monitor for 24 hours** in paper mode
2. **Review all risk events** in logs
3. **Verify all limits** work as expected
4. **Check dashboard** for risk metrics
5. **Test freeze conditions** (carefully, in paper mode)
6. **Document any issues** or needed adjustments

---

## 🎯 Ready for Live Trading?

Before moving to LIVE mode:

- [ ] All risk limits tested and working
- [ ] Freeze mechanism tested (paper mode)
- [ ] Daily P&L tracking accurate
- [ ] Exposure limits preventing over-concentration
- [ ] Order validation preventing oversized orders
- [ ] Dashboard monitoring risk metrics correctly
- [ ] Confident in all safety mechanisms

Then:
```bash
export TRADING_MODE=LIVE
# Restart bot to pick up new mode
```
