# Trade Pattern Analysis - December 2025

## Observations from Recent Trades

### Exit Reasons
**All trades exiting with: `"time_or_trail"`**

This means trades are closing due to:
- **Time-based exit**: Position held too long (likely 4 hours or 20 hours based on hold_min)
- **Trailing stop**: Hit trailing stop loss

### Trade Duration Patterns

**Two distinct holding patterns:**
1. **Short holds (~240 minutes = 4 hours)**: Intraday trades
2. **Long holds (~1200 minutes = 20 hours)**: Overnight positions

### Performance Observations

From the sample shown:
- **Wins**: AAPL (+0.87%), NVDA (+1.61%), QQQ (+1.65%), SPY (+1.05%), TSLA (+3.45%, +1.08%)
- **Losses**: TSLA (-3.62%, -1.63%), VEEV (-0.6%), MSFT (-0.23%, -0.33%, -1.57%), NVDA (-1.05%, -0.54%), QQQ (-0.14%, -0.22%), SPY (-0.22%, -0.11%)

**Pattern:**
- Small wins (0.5-3.5%)
- Small losses (0.1-3.6%)
- Most losses are smaller than wins (good risk management)
- But win rate is low (11.3% overall)

### Key Insights

1. **All exits are time/trailing stop** - No signal-based exits
   - This suggests signals aren't triggering exits
   - Or exit signals aren't being evaluated properly
   - May need to review exit evaluation logic

2. **Holding times are consistent** - Either 4 hours or 20 hours
   - Suggests time-based exits are working
   - But may be exiting too early on winners
   - Or too late on losers

3. **Win rate is low but risk/reward may be okay**
   - Average win: ~1.5%
   - Average loss: ~1.0%
   - If win rate improves, this could be profitable

## Recommendations

### 1. Review Exit Strategy
```bash
# Check exit evaluation logic
grep -A 10 "evaluate_exits" main.py

# Check why signal-based exits aren't triggering
grep -i "exit.*signal" logs/exit.jsonl | head -20
```

### 2. Analyze Win/Loss Distribution
```bash
# Calculate average win vs average loss
python3 -c "
import json
wins = []
losses = []
with open('logs/attribution.jsonl') as f:
    for line in f:
        if line.strip():
            rec = json.loads(line)
            pnl = rec.get('pnl_pct', 0)
            if pnl > 0:
                wins.append(pnl)
            elif pnl < 0:
                losses.append(pnl)
print(f'Wins: {len(wins)}, Avg: {sum(wins)/len(wins):.2f}%')
print(f'Losses: {len(losses)}, Avg: {sum(losses)/len(losses):.2f}%')
print(f'Win Rate: {len(wins)/(len(wins)+len(losses))*100:.1f}%')
"
```

### 3. Check Entry Criteria
- May be too loose (taking marginal trades)
- Consider raising composite score threshold
- Review signal quality at entry

### 4. Review Exit Timing
- Are winners being cut short?
- Are losers being held too long?
- Check if trailing stops are too tight

## Questions to Answer

1. **Why are all exits "time_or_trail"?**
   - Are signal-based exits not triggering?
   - Is exit evaluation running properly?

2. **Why is win rate so low (11.3%)?**
   - Entry criteria too loose?
   - Market conditions unfavorable?
   - Signal quality degraded?

3. **Are trailing stops optimal?**
   - Too tight (cutting winners)?
   - Too loose (allowing big losses)?

4. **Should we adjust time-based exits?**
   - 4 hours may be too short for some trades
   - 20 hours may be too long for others

## Next Steps

1. **Run detailed trade analysis script** (create one)
2. **Review exit evaluation code** for signal-based exits
3. **Check if entry criteria can be tightened**
4. **Analyze if trailing stops need adjustment**
5. **Review recent market conditions** (volatility, regime)
