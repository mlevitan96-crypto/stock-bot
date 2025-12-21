# Learning Engine Current State & Coverage Analysis

## What the Learning Engine Currently Analyzes

### ✅ Currently Processed

1. **`logs/attribution.jsonl`** (PARTIALLY)
   - **What it reads**: Records with `type="attribution"` from TODAY only
   - **What it extracts**:
     - P&L percentage (`pnl_pct`)
     - Signal components (`context.components`)
     - Market regime (`context.market_regime`)
     - Sector (defaults to "unknown")
   - **What it learns**:
     - Component performance (wins/losses per component)
     - Component multipliers (adaptive weights)
     - Regime-specific performance
     - Sector-specific performance
   - **Limitations**:
     - Only processes TODAY's trades (historical ignored)
     - Requires `context.components` to exist
     - Only called daily (not after each trade)

2. **Exit Signal Learning** (PARTIALLY)
   - **What it reads**: Exit events from `log_exit_attribution()`
   - **What it extracts**:
     - Exit reason (parsed for exit signals)
     - P&L percentage
   - **What it learns**:
     - Exit signal performance (via exit model)
   - **Limitations**:
     - Only processes exits that go through `log_exit_attribution()`
     - Exit signal parsing is basic (string matching)
     - Not all exit reasons are mapped to exit components

### ❌ NOT Currently Analyzed

1. **`logs/exit.jsonl`**
   - **What's logged**: All exit events with reasons, timestamps, P&L
   - **Why not analyzed**: No code reads this file for learning
   - **Impact**: Exit signal weights not optimized based on actual exit outcomes

2. **`logs/signals.jsonl`**
   - **What's logged**: Signal generation events, clusters, scores
   - **Why not analyzed**: No code reads this file for learning
   - **Impact**: Cannot learn which signal patterns lead to better outcomes

3. **`logs/orders.jsonl`**
   - **What's logged**: Order execution events, fills, slippage
   - **Why not analyzed**: No code reads this file for learning
   - **Impact**: Cannot learn execution quality, slippage patterns, or order timing

4. **`data/daily_postmortem.jsonl`**
   - **What's logged**: Daily summaries (P&L, win rate, drawdown)
   - **Why not analyzed**: No code reads this file for learning
   - **Impact**: Cannot track long-term trends or regime changes

5. **`data/uw_attribution.jsonl`**
   - **What's logged**: UW signal attribution (flow, dark pool, insider)
   - **Why not analyzed**: No code reads this file for learning
   - **Impact**: Cannot learn UW-specific signal patterns

6. **Historical Trades**
   - **What's logged**: All trades in `logs/attribution.jsonl`
   - **Why not analyzed**: `learn_from_outcomes()` only processes today's trades
   - **Impact**: Learning resets daily, losing historical performance data

## Current Learning Architecture

### Entry Signal Learning (AdaptiveSignalOptimizer)

**Components Tracked** (21 total):
- `options_flow`, `dark_pool`, `insider`, `iv_term_skew`, `smile_slope`
- `whale_persistence`, `event_alignment`, `temporal_motif`, `toxicity_penalty`
- `regime_modifier`, `congress`, `shorts_squeeze`, `institutional`
- `market_tide`, `calendar_catalyst`, `etf_flow`, `greeks_gamma`
- `ftd_pressure`, `iv_rank`, `oi_change`, `squeeze_score`

**What it tracks per component**:
- Wins/losses
- Total P&L
- EWMA win rate
- EWMA P&L
- Contribution when winning vs losing
- Sector-specific performance
- Regime-specific performance

**How it updates weights**:
- Requires 30+ samples per component
- Uses Wilson confidence intervals
- Bayesian updates with EWMA smoothing
- Multipliers range: 0.25x to 2.5x

### Exit Signal Learning (ExitSignalModel)

**Components Tracked** (7 total):
- `entry_decay`, `adverse_flow`, `drawdown_velocity`
- `time_decay`, `momentum_reversal`, `volume_exhaustion`, `support_break`

**What it tracks**:
- Timely exits vs late exits
- False alarms
- EWMA timing performance

**Current Status**: Partially implemented, not fully utilized

## Data Flow Issues

### Issue 1: Historical Trades Ignored
- **Current**: `learn_from_outcomes()` only processes today's trades
- **Code**: Line 1942 in `main.py`: `if not rec.get("ts", "").startswith(today):`
- **Impact**: Learning resets daily, losing historical data
- **Fix**: Track last processed trade ID, process all unprocessed trades

### Issue 2: Learning Only Runs Daily
- **Current**: `learn_from_outcomes()` called in `daily_and_weekly_tasks_if_needed()`
- **Impact**: Trades closed during day aren't learned from until EOD
- **Fix**: Call learning immediately after each trade close

### Issue 3: Exit Events Not Fully Analyzed
- **Current**: Exit learning only happens in `log_exit_attribution()` if exit components are parsed
- **Impact**: Many exit events in `logs/exit.jsonl` are not analyzed
- **Fix**: Process `logs/exit.jsonl` for exit signal learning

### Issue 4: Execution Quality Not Learned
- **Current**: Order execution data logged but not analyzed
- **Impact**: Cannot optimize order timing, sizing, or execution strategy
- **Fix**: Analyze `logs/orders.jsonl` for execution patterns

## Recommendations

### Priority: HIGH

1. **Process Historical Trades**
   - Modify `learn_from_outcomes()` to process all unprocessed trades
   - Track last processed trade ID in state file
   - Run once to backfill all historical data

2. **Analyze Exit Events**
   - Process `logs/exit.jsonl` for exit signal learning
   - Feed exit outcomes to exit model
   - Improve exit timing based on what actually worked

3. **Enable Continuous Learning**
   - Call learning after each trade close
   - Don't wait for EOD batch processing
   - Faster adaptation to market changes

### Priority: MEDIUM

4. **Analyze Order Execution**
   - Process `logs/orders.jsonl` for execution quality
   - Track slippage, fill quality, timing patterns
   - Optimize order execution strategy

5. **Analyze Signal Patterns**
   - Process `logs/signals.jsonl` for signal pattern learning
   - Learn which signal combinations work best
   - Improve signal selection criteria

### Priority: LOW

6. **Analyze Daily Summaries**
   - Process `data/daily_postmortem.jsonl` for regime detection
   - Track long-term performance trends
   - Adjust strategy based on regime changes

## Verification

Run the audit script to see current state:

```bash
cd ~/stock-bot
python3 audit_learning_coverage.py
```

This will show:
- What logs exist and have data
- What the learning system currently analyzes
- What gaps exist
- Specific recommendations

## Next Steps

1. **Run audit script** to see exact current state
2. **Review gaps** identified by audit
3. **Prioritize fixes** based on impact
4. **Implement fixes** starting with HIGH priority items
5. **Verify** learning system is analyzing all relevant data
