# Learning Schedule & Profitability Tracking

## 🎯 GOAL: Make Every Trade a Winner

The system is designed to continuously learn and improve profitability through multiple learning cycles.

## 📅 Learning Schedule

### **SHORT-TERM (Continuous)**
- **Frequency**: After every trade
- **Trigger**: Trade closes → `learn_from_trade_close()` called
- **What it does**:
  - Immediately learns from the trade outcome
  - Updates component weights in real-time
  - Records P&L and component performance
- **Location**: `log_exit_attribution()` in `main.py`

### **MEDIUM-TERM (Daily)**
- **Frequency**: Once per day, after market close
- **Trigger**: Market closes → `daily_and_weekly_tasks_if_needed()` → `learn_from_outcomes()`
- **What it does**:
  - Processes all new trades from today
  - Processes all exit events
  - Processes blocked trades and gate events
  - Updates component weights based on daily performance
  - Updates profitability tracking (daily metrics)
- **Location**: `main.py` line 5400-5401
- **Also runs**: Separate thread `run_comprehensive_learning_periodic()` (line 5645-5690)

### **WEEKLY**
- **Frequency**: Every Friday after market close
- **Trigger**: `is_friday() and is_after_close_now()` → Weekly adjustments
- **What it does**:
  - Weekly weight adjustments (`apply_weekly_adjustments()`)
  - Per-ticker profile retraining (`weekly_retrain_profiles()`)
  - Stability decay (`apply_weekly_stability_decay()`)
  - Updates profitability tracking (weekly metrics)
- **Location**: `main.py` line 5403-5418

### **MONTHLY**
- **Frequency**: First day of each month
- **Trigger**: `datetime.now(timezone.utc).day == 1`
- **What it does**:
  - Updates profitability tracking (monthly metrics)
  - Long-term trend analysis
- **Location**: `main.py` line 5404 (profitability tracking)

### **LONG-TERM (Historical Backfill)**
- **Frequency**: Manual or on-demand
- **Trigger**: Run `backfill_historical_learning.py`
- **What it does**:
  - Processes ALL historical data from logs
  - Rebuilds learning state from scratch
  - Useful after system updates or to catch up on missed data

## 📊 Profitability Tracking

### **What Gets Tracked**

1. **Daily Metrics** (updated daily after market close):
   - Total trades
   - Wins vs Losses
   - Win rate
   - Total P&L (USD and %)
   - Average P&L per trade
   - Expectancy

2. **Weekly Metrics** (updated every Friday):
   - Same as daily, but aggregated for the week

3. **Monthly Metrics** (updated first day of month):
   - Same as daily, but aggregated for the month

4. **30-Day Trends**:
   - Win rate improvement/decline
   - P&L trend (improving/declining)
   - Comparison: Recent 7 days vs older period

5. **Component Performance**:
   - Win rate per component
   - EWMA win rate (exponentially weighted moving average)
   - EWMA P&L per component
   - Total trades per component

### **Goal Status**
- **Target Win Rate**: 60%
- **Current Status**: Tracked daily
- **On Track**: ✅ if win rate ≥ 60%
- **Needs Improvement**: ⚠️ if win rate < 50%

## 🔄 Full Learning Cycle

```
1. SIGNAL GENERATED
   ↓
2. TRADE DECISION (Entry/Blocked)
   ↓
3. TRADE EXECUTED (or Blocked)
   ↓
4. SHORT-TERM LEARNING (immediately after trade close)
   - learn_from_trade_close()
   - Update weights in real-time
   ↓
5. DAILY LEARNING (after market close)
   - run_daily_learning()
   - Process all today's data
   - Update profitability tracking
   ↓
6. WEEKLY LEARNING (Friday after close)
   - Weekly weight adjustments
   - Profile retraining
   - Weekly profitability tracking
   ↓
7. MONTHLY LEARNING (first of month)
   - Monthly profitability tracking
   - Long-term trend analysis
   ↓
8. APPLY LEARNINGS
   - Updated weights applied to next trades
   - Better decisions = Better profitability
```

## 📈 How to Check Profitability

### **Quick Status Check**
```bash
python3 profitability_tracker.py
```

This shows:
- Today's performance
- This week's performance
- This month's performance
- 30-day trends (improving/declining)
- Goal status (on track?)
- Top performing components

### **View Historical Data**
```bash
cat state/profitability_tracking.json | python3 -m json.tool
```

## 🎯 Making Every Trade a Winner

### **How the System Works Toward This Goal**

1. **Continuous Learning**: Every trade teaches the system
2. **Component Optimization**: System learns which signals work best
3. **Exit Optimization**: System learns when to exit for maximum profit
4. **Blocked Trade Analysis**: System learns from missed opportunities
5. **Gate Optimization**: System learns which gates are too strict/loose
6. **Trend Detection**: System detects if performance is improving or declining

### **What Happens When Win Rate is Low**

- System automatically adjusts component weights
- Less effective components get lower weights
- More effective components get higher weights
- Gates may be adjusted (if adaptive gates enabled)
- System focuses on what works

### **Performance Improvement Indicators**

✅ **Improving**:
- Win rate trending up
- P&L trending up
- More wins than losses
- Expectancy positive

❌ **Declining**:
- Win rate trending down
- P&L trending down
- More losses than wins
- Expectancy negative

## 🔧 Manual Commands

### **Force Daily Learning Update**
```bash
python3 -c "from profitability_tracker import update_daily_performance; update_daily_performance()"
```

### **Force Weekly Learning Update**
```bash
python3 -c "from profitability_tracker import update_weekly_performance; update_weekly_performance()"
```

### **Force Monthly Learning Update**
```bash
python3 -c "from profitability_tracker import update_monthly_performance; update_monthly_performance()"
```

### **Run Full Historical Backfill**
```bash
python3 backfill_historical_learning.py
```

## 📝 Summary

**Learning Runs:**
- ✅ **Continuous**: After every trade
- ✅ **Daily**: After market close
- ✅ **Weekly**: Friday after market close
- ✅ **Monthly**: First day of month
- ✅ **On-Demand**: Historical backfill

**Profitability Tracking:**
- ✅ **Daily**: Updated daily
- ✅ **Weekly**: Updated Friday
- ✅ **Monthly**: Updated first of month
- ✅ **Trends**: 30-day analysis
- ✅ **Components**: Per-component performance

**Goal**: Make every trade a winner through continuous learning and optimization.

The system is **ALWAYS LEARNING** and **ALWAYS TRACKING** profitability to ensure continuous improvement toward the goal of making every trade profitable.
