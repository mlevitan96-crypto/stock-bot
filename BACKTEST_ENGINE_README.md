# Historical Replay Engine - No Look-Forward Bias Backtest

## Overview

The Historical Replay Engine provides a realistic backtest of the trading bot using Alpaca's granular historical data API. It replays the last 30 days of UW Flow Alerts with realistic execution friction and temporal liquidity constraints to verify bot performance.

## Key Features

1. **Tick-Level Execution**: Uses Alpaca's historical trades API for realistic price simulation
2. **Latency Penalty**: Applies 0.5 basis point latency penalty to all entries
3. **Specialist Strategy Rotator Testing**: Tests the 0.75 score threshold increase during mid-day (11:30-13:30 EST)
4. **Stale Trade Exit Analysis**: Tests closing positions at 90 minutes if P&L < ±0.2%
5. **Alpha Decay Measurement**: Measures how long signals stay profitable before mean reversion
6. **Comprehensive Metrics**: Win rate, Sharpe ratio, profit factor, capacity analysis

## Requirements

- Python 3.7+
- Alpaca API credentials (ALPACA_API_KEY, ALPACA_API_SECRET)
- Attribution log files:
  - `data/uw_attribution.jsonl` (primary signal source)
  - `logs/attribution.jsonl` or `logs/composite_attribution.jsonl` (fallback)

## Installation

No additional dependencies required beyond the existing project dependencies:
- `alpaca-trade-api` (or use REST API directly via requests)
- `pytz` (for timezone handling)

## Usage

### Basic Usage

```bash
python historical_replay_engine.py --days 30
```

### Command Line Options

- `--days N`: Number of days to backtest (default: 30)
- `--output PATH`: Custom output path for JSON report (default: `reports/backtest_report_YYYYMMDD_HHMMSS.json`)
- `--no-specialist`: Disable specialist strategy rotator test
- `--no-stale-exits`: Disable stale trade exit test

### Example

```bash
# Run full backtest with all tests
python historical_replay_engine.py --days 30 --output reports/my_backtest.json

# Run backtest without specialist rotator test
python historical_replay_engine.py --days 30 --no-specialist

# Run backtest for last 60 days
python historical_replay_engine.py --days 60
```

## Programmatic Usage

```python
from historical_replay_engine import HistoricalReplayEngine
from pathlib import Path

# Initialize engine
engine = HistoricalReplayEngine(
    latency_penalty_bps=0.5,
    stale_exit_minutes=90,
    stale_exit_pnl_threshold=0.002  # ±0.2%
)

# Run backtest
metrics = engine.run_backtest(
    days=30,
    test_specialist=True,
    test_stale_exits=True
)

# Generate report
report = engine.generate_report(output_path=Path("reports/backtest.json"))

# Access individual trades
for trade in engine.simulated_trades:
    print(f"{trade.symbol}: {trade.pnl_usd:.2f} ({trade.pnl_pct:.2%})")
```

## Output Format

The backtest generates a comprehensive JSON report with:

### Backtest Summary
- Total trades, win rate, total P&L
- Sharpe ratio, profit factor, max drawdown
- Average hold time

### Specialist Strategy Analysis
- Mid-day (11:30-13:30 EST) win rate vs overall win rate
- Comparison of mid-day vs non-mid-day performance
- Whether specialist rotator improves Sharpe ratio

### Stale Exit Analysis
- Number of trades closed via stale exit rule
- Capacity freed percentage
- Rule effectiveness

### Alpha Decay Analysis
- Average minutes until signal becomes unprofitable
- Note: Full measurement requires tick-level price history

### Objective Assessment
- Target: 60% win rate under realistic execution friction
- Achievement status

## How It Works

### Signal Loading
1. Loads signals from `data/uw_attribution.jsonl` (primary)
2. Falls back to `logs/attribution.jsonl` or `logs/composite_attribution.jsonl`
3. Filters signals from last N days
4. Sorts chronologically

### Trade Execution Simulation
1. For each signal:
   - Fetches historical price at signal timestamp (tick-level or 1-minute bars)
   - Applies 0.5 bps latency penalty to entry price
   - Applies specialist rotator filter (if enabled): only takes signals that pass threshold + 0.75 during 11:30-13:30 EST
   - Creates simulated trade entry

### Exit Simulation
Exits are checked in priority order:
1. **Stale Trade Exit**: 90 minutes, P&L < ±0.2%
2. **Trailing Stop**: 1.5% (or 1.0% in MIXED regime)
3. **Time Exit**: 240 minutes (4 hours)
4. **Profit Target**: 2% (first target)

### Metrics Calculation
- Win rate, profit factor, Sharpe ratio
- Specialist vs non-specialist performance
- Stale exit effectiveness
- Alpha decay estimation

## Key Differences from Live Trading

1. **No Real Orders**: All trades are simulated using historical data
2. **Perfect Market Data**: Uses Alpaca's historical data (may have 15-minute delay for recent data)
3. **Simplified Exit Logic**: Some exit conditions simplified (e.g., high water mark tracking)
4. **No API Rate Limits**: Can fetch data faster than real-time

## Limitations

1. **Historical Data Availability**: Alpaca has 15-minute delay for "historical" classification
2. **Tick Data**: Falls back to 1-minute bars if tick data unavailable
3. **Exit Logic Simplification**: Some complex exit conditions (signal decay, flow reversal) are simplified
4. **Alpha Decay Measurement**: Currently estimated based on trade outcomes; full measurement requires continuous price history
5. **No Order Slippage**: Uses exact prices from historical data (latency penalty simulates some friction)

## Alpaca API Requirements

The backtest uses Alpaca's Market Data API v2:
- Endpoint: `https://data.alpaca.markets/v2/stocks/{symbol}/trades` (tick-level)
- Fallback: `https://data.alpaca.markets/v2/stocks/{symbol}/bars` (bar-level)

Requires valid API credentials. Uses same authentication as Trading API.

## Example Output

```json
{
  "backtest_summary": {
    "total_trades": 145,
    "win_rate": "62.07%",
    "total_pnl_usd": "$2,345.67",
    "sharpe_ratio": "1.85",
    "profit_factor": "2.34",
    "max_drawdown": "8.5%"
  },
  "specialist_strategy_analysis": {
    "mid_day_window": "11:30-13:30 EST",
    "mid_day_win_rate": "68.42%",
    "improvement": "Yes"
  },
  "stale_exit_analysis": {
    "stale_exits": 23,
    "capacity_freed_pct": "15.86%"
  },
  "objective_assessment": {
    "target_win_rate": "60%",
    "achieved_win_rate": "62.07%",
    "meets_target": "Yes"
  }
}
```

## Troubleshooting

### "No signals found"
- Check that attribution log files exist
- Verify log files have data from the specified time period
- Check file paths in `config/registry.py`

### "Could not get price for {symbol}"
- Alpaca API may not have historical data for that symbol/time
- Try using longer time windows around the target time
- Check API credentials are valid

### "API rate limit exceeded"
- Add delays between API calls
- Reduce number of symbols or time period
- Use bar data instead of tick data for faster execution

## Integration with Main Bot

The backtest engine can be integrated into the main bot for periodic validation:

```python
# In main.py or separate validation script
from historical_replay_engine import HistoricalReplayEngine

def run_weekly_backtest():
    engine = HistoricalReplayEngine()
    metrics = engine.run_backtest(days=30)
    
    if metrics.win_rate < 0.55:
        # Alert if performance degrades
        send_alert(f"Backtest win rate below threshold: {metrics.win_rate:.2%}")
    
    return metrics
```

## Next Steps

1. **Full Alpha Decay Measurement**: Implement continuous price history tracking
2. **Signal Decay Integration**: Add current signal score lookup for decay detection
3. **Flow Reversal Detection**: Integrate UW API for flow reversal signals
4. **High Water Mark Tracking**: Proper implementation for trailing stops
5. **Multi-Timeframe Analysis**: Test performance across different market regimes
