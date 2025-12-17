# Executive Summary Dashboard - When Data Appears

## ⏰ **When Learning & Data Runs**

### **Learning System**
- **First Run**: Immediately when `main.py` starts
- **Subsequent Runs**: Every 60 minutes (1 hour)
- **Files Updated**: 
  - `data/comprehensive_learning.jsonl` - Learning results
  - `data/counterfactual_results.jsonl` - Counterfactual analysis
  - `state/signal_weights.json` - Updated weights

### **Executive Summary Data**
- **Trade Data**: Reads from `data/attribution.jsonl` (updated in real-time as trades execute)
- **Learning Data**: Reads from learning files (updated hourly)
- **Dashboard Refresh**: Every 30 seconds when Executive Summary tab is active

## 📊 **What Will Show**

### **If You Have Trades:**
- ✅ Full trade list with P&L
- ✅ 2-day and 5-day P&L metrics
- ✅ Signal performance analysis (top/bottom signals)
- ✅ Learning insights (weight adjustments, counterfactuals)
- ✅ Written executive summary

### **If You Have No Trades Yet:**
- ✅ Shows "No trades found" message
- ✅ Shows P&L metrics as $0.00 (0 trades, 0% win rate)
- ✅ Shows "No signal data available"
- ✅ Shows "No weight adjustments yet"
- ✅ Shows basic written summary with zero trades

## 🔍 **Troubleshooting**

### **Nothing Shows on Dashboard:**
1. Check browser console (F12) for JavaScript errors
2. Check dashboard logs for API errors
3. Verify `/api/executive_summary` endpoint returns data:
   ```bash
   curl http://localhost:5000/api/executive_summary | python3 -m json.tool
   ```

### **No Trade Data:**
- Trades only appear after trades have been executed
- Check `data/attribution.jsonl` exists and has data
- Verify trading bot is running and executing trades

### **No Learning Data:**
- Learning runs every hour, so data may not appear immediately
- Check `data/comprehensive_learning.jsonl` exists
- Verify learning orchestrator is running (check `/health` endpoint)

## ✅ **Testing**

To test the executive summary generator manually:

```bash
# Test the generator
python3 executive_summary_generator.py

# Test the API endpoint
curl http://localhost:5000/api/executive_summary | python3 -m json.tool
```

## 📝 **Data Requirements**

The Executive Summary will show meaningful data when:
1. **Trades exist**: `data/attribution.jsonl` has trade records
2. **Learning has run**: At least one learning cycle has completed (runs hourly)
3. **Counterfactuals processed**: Blocked trades exist and counterfactual analyzer has run

**Note**: Even with no data, the dashboard will load and show "No data" messages - it will not error out.
