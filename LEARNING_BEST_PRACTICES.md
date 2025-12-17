# Learning System Best Practices for Trading Bots

## 🎯 **Recommended Approach**

### **1. Learning Frequency: Daily After Market Close**
- **Why**: 
  - Avoids overfitting to intraday noise
  - Allows full day's data to accumulate
  - Safer - no learning during active trading
  - Market conditions complete by close
  
- **When**: 4:30 PM ET (market close) + 15 min buffer = 4:45 PM ET = 9:45 PM UTC
- **Alternative**: Run at 5:00 PM ET / 10:00 PM UTC for safety margin

### **2. Cumulative Learning with Exponential Decay**
- **Why**:
  - Recent trades more relevant, but older trades still valuable
  - Prevents forgetting important patterns
  - Balances adaptability with stability
  
- **How**:
  - Weight trades: `weight = e^(-age_days / decay_halflife)`
  - Halflife = 30 days (trades older than 30 days have <50% weight)
  - All trades count, but recent ones matter more

### **3. Minimum Sample Sizes**
- **Weight adjustments**: Require 30+ trades minimum
- **Timing optimization**: Require 20+ trades per scenario
- **Sizing optimization**: Require 15+ trades per scenario
- **Counterfactuals**: Require 10+ blocked trades

### **4. Gradual Updates**
- **Weight updates**: 10% per day maximum (already implemented)
- **Prevents**: Overreacting to short-term patterns
- **Allows**: Steady adaptation over weeks/months

### **5. Confidence Intervals**
- **Use Wilson intervals** for win rates (already implemented)
- **Bootstrap** for Sharpe ratios
- **Only adjust** if confidence intervals clearly favor change

### **6. Regime-Aware Learning**
- **Separate learning** for different market regimes (bull/bear/volatile)
- **Current system** tracks regime performance
- **Consider**: Separate weight sets per regime

## 📊 **Current vs Recommended**

| Aspect | Current | Recommended | Status |
|--------|---------|-------------|--------|
| Frequency | Hourly | Daily after close | ❌ Needs update |
| Cumulative | EWMA (cumulative) | Exponential decay (better) | ⚠️ Partial |
| Sample size | 30 min | 30-50 min | ✅ Good |
| Update rate | 10% per cycle | 10% per day | ✅ Good |
| Confidence | Wilson intervals | ✅ Already using | ✅ Good |

## ✅ **What We'll Implement**

1. **Daily learning schedule** (after market close)
2. **Exponential decay** for trade weighting in analysis
3. **Cumulative tracking** with time-weighted importance
4. **Improved minimum samples** requirements
