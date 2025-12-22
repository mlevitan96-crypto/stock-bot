# Causal Analysis Engine - Deep Learning & Reasoning System

## Problem Statement

**Current State**: Learning system tracks win/loss but doesn't explain WHY.

**User Requirement**: 
> "We can't just review the data. We have to know why it is winning or why it is losing. We need to know why flow lost today. What was it that caused the signal be underperforming. I want that answer for all signals and for all data. We have to know the reason, we have to know the why for data analysis. If we just look at one number for one day and adjust, it doesn't help us as we would just adjust each time we GUESSED wrong. We have to KNOW why ahead of time."

## Solution: Causal Analysis Engine

### What It Does

1. **Extracts Full Context** for every trade:
   - Market regime (RISK_ON, RISK_OFF, NEUTRAL, MIXED)
   - Time of day (OPEN, MID_DAY, CLOSE, AFTER_HOURS)
   - Day of week
   - Signal strength (WEAK, MODERATE, STRONG)
   - Flow magnitude (LOW, MEDIUM, HIGH)
   - IV regime (LOW, MEDIUM, HIGH)
   - Volatility regime
   - Market trend (BULLISH, BEARISH, SIDEWAYS)
   - Sector

2. **Analyzes Patterns**:
   - Which conditions lead to wins vs losses for each component
   - Feature combinations that work together
   - Context-specific performance patterns

3. **Answers WHY Questions**:
   - "Why did options_flow lose today?" → Specific conditions that caused failure
   - "When does dark_pool work best?" → Conditions that lead to success
   - "What conditions cause insider to fail?" → Failure patterns

4. **Generates Predictive Insights**:
   - "Use options_flow when: regime=RISK_ON, time=OPEN, flow_mag=HIGH"
   - "Avoid dark_pool when: regime=RISK_OFF, time=CLOSE, iv_regime=HIGH"

## Implementation

### Files Created

1. **`causal_analysis_engine.py`**: Core engine that analyzes trades and generates insights
2. **`query_why_analysis.py`**: Interactive tool to query "why" questions

### Integration Points

1. **Enhanced Context Capture** (`main.py` line ~1029):
   - Now captures time_of_day, day_of_week, signal_strength, flow_magnitude
   - Stores full context with every trade

2. **Automatic Analysis** (`comprehensive_learning_orchestrator_v2.py`):
   - Feeds trades to causal engine automatically
   - Generates insights after daily learning batch

3. **Component Reports** (`adaptive_signal_optimizer.py`):
   - Now includes regime_performance and sector_performance in reports
   - Shows context-aware performance breakdown

## Usage

### Process All Trades for Analysis

```bash
cd ~/stock-bot
python3 causal_analysis_engine.py
```

### Query WHY Questions

```bash
# Why is options_flow underperforming?
python3 query_why_analysis.py --component options_flow --question why_underperforming

# When does dark_pool work best?
python3 query_why_analysis.py --component dark_pool --question when_works_best

# What conditions cause insider to fail?
python3 query_why_analysis.py --component insider --question what_conditions_fail

# Analyze all components
python3 query_why_analysis.py --all
```

### Generate Insights Report

```bash
python3 -c "from causal_analysis_engine import CausalAnalysisEngine; engine = CausalAnalysisEngine(); engine.process_all_trades(); insights = engine.generate_insights(); import json; print(json.dumps(insights, indent=2))"
```

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

## Next Steps

1. **Run initial analysis** to process all historical trades
2. **Query specific components** to understand why they win/lose
3. **Use insights** to make predictive decisions (not just reactive adjustments)
4. **Monitor insights** as new trades come in to refine understanding

## Integration with Learning System

The causal analysis engine works alongside the existing learning system:

- **Learning System**: Adjusts weights based on performance (WHAT happened)
- **Causal Engine**: Explains WHY performance happened (WHEN/WHERE/WHY)

Together, they enable:
- **Predictive adjustments**: Know when to use signals BEFORE trading
- **Context-aware weighting**: Adjust weights based on market conditions
- **Root cause understanding**: Fix underlying issues, not just symptoms
