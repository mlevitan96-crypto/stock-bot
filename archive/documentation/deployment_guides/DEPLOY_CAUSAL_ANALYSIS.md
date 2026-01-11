# Deploy Causal Analysis Engine

## What Was Built

**Causal Analysis Engine** - Deep learning system that answers WHY signals win or lose.

### Key Features

1. **Deep Context Extraction**:
   - Market regime (RISK_ON, RISK_OFF, NEUTRAL, MIXED)
   - Time of day (OPEN, MID_DAY, CLOSE, AFTER_HOURS)
   - Day of week
   - Signal strength (WEAK, MODERATE, STRONG)
   - Flow magnitude (LOW, MEDIUM, HIGH)
   - IV regime, volatility regime, market trend, sector

2. **Pattern Recognition**:
   - Identifies which conditions lead to success vs failure
   - Analyzes feature combinations that work together
   - Root cause investigation for losing trades

3. **Predictive Insights**:
   - "USE_WHEN" recommendations (when to use each signal)
   - "AVOID_WHEN" recommendations (when to avoid each signal)
   - Feature combination analysis

## Deployment Steps

```bash
cd ~/stock-bot
git pull origin main

# Process all historical trades for causal analysis
python3 causal_analysis_engine.py

# Query why questions
python3 query_why_analysis.py --component options_flow --question why_underperforming
python3 query_why_analysis.py --component dark_pool --question when_works_best
python3 query_why_analysis.py --all

# Restart services (optional - causal analysis runs automatically during daily learning)
pkill -f "deploy_supervisor"
sleep 3
screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py"
```

## How It Works

1. **Enhanced Context Capture**: Every trade now stores full context (time, regime, signal strength, etc.)
2. **Automatic Analysis**: Causal engine processes trades during daily learning batch
3. **Query Interface**: Use `query_why_analysis.py` to ask specific questions

## Example Output

```
WHY ANALYSIS: OPTIONS_FLOW
================================================================================

options_flow underperforms when:
  - regime: RISK_OFF
  - time: CLOSE
  - trend: BEARISH
  - flow_mag: LOW

Evidence: 15 trades, 26.7% win rate, -0.45% avg P&L

RECOMMENDATION: Avoid using options_flow when: regime=RISK_OFF, time=CLOSE, trend=BEARISH, flow_mag=LOW

options_flow works best when:
  - regime: RISK_ON
  - time: OPEN
  - trend: BULLISH
  - flow_mag: HIGH

Evidence: 22 trades, 72.7% win rate, +1.23% avg P&L

RECOMMENDATION: Use options_flow when: regime=RISK_ON, time=OPEN, trend=BULLISH, flow_mag=HIGH
```

## Integration

- **Automatic**: Runs during daily learning batch
- **Enhanced Context**: All trades now include time_of_day, signal_strength, flow_magnitude, etc.
- **Component Reports**: Now include regime_performance and sector_performance breakdowns

This enables **PREDICTIVE understanding** - know WHY and WHEN to use signals, not just reactive adjustments.
