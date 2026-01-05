# Comprehensive Daily Trading Analysis

## Overview

The `comprehensive_daily_trading_analysis.py` script generates a complete analysis of each trading day including:

1. **Executed Trades** - Wins, losses, P&L, win rates
2. **Blocked Trades** - All blocking reasons, score distributions
3. **UW Blocked Entries** - Composite scoring rejections
4. **Signal Analysis** - Signals generated vs executed, execution rates
5. **Gate Events** - Gate blocking patterns
6. **Performance Recommendations** - Actionable insights for improvement
7. **Counter-Intelligence Analysis** - What we did vs didn't do

## Usage

### On Droplet (Recommended)

Run after market close to analyze the day's trading:

```bash
cd ~/stock-bot
git pull origin main
python3 comprehensive_daily_trading_analysis.py
```

### Output Files

The script generates three files in the `reports/` directory:

1. **`daily_analysis_summary_YYYY-MM-DD.md`** - Markdown summary report (GitHub-friendly)
2. **`daily_analysis_detailed_YYYY-MM-DD.md`** - Detailed markdown report (GitHub-friendly)
3. **`daily_analysis_YYYY-MM-DD.json`** - JSON data file (for programmatic analysis)

All reports are automatically committed to Git and pushed to GitHub.

## Report Contents

### Summary Report Includes:
- Executive summary (trades, win rate, P&L)
- Executed trades overview
- Blocked trades breakdown
- UW blocked entries analysis
- Signal generation statistics
- Gate events summary
- Performance recommendations

### Detailed Report Includes:
- Complete summary (expandable)
- Detailed executed trades list (top 50)
- Detailed blocked trades list (top 50)
- Full analysis data

### JSON Data Includes:
- All raw data for programmatic analysis
- Complete trade records
- Complete blocked trade records
- Signal statistics
- Gate event data

## Performance Recommendations

The script automatically generates recommendations based on:
- Win rate analysis (target: 60%)
- Execution rate analysis (optimal: 5-50%)
- Blocking patterns (are we too strict/lenient?)
- Signal quality (average scores)
- Toxicity filtering effectiveness

## Data Sources

The script analyzes:
- `logs/attribution.jsonl` - Executed trades
- `state/blocked_trades.jsonl` - Blocked trades
- `data/uw_attribution.jsonl` - UW blocked entries
- `logs/signals.jsonl` - Signal generation
- `logs/gate.jsonl` - Gate events

## GitHub Integration

All reports are automatically:
1. Generated in `reports/` directory
2. Committed to Git
3. Pushed to GitHub

You can download reports directly from the GitHub repository at:
`https://github.com/mlevitan96-crypto/stock-bot/reports/`

## Scheduling

To run automatically after market close, add to crontab:

```bash
# Run daily analysis at 4:30 PM ET (20:30 UTC) Monday-Friday
30 20 * * 1-5 cd /root/stock-bot && python3 comprehensive_daily_trading_analysis.py >> logs/daily_analysis.log 2>&1
```

## Example Output

See `reports/daily_analysis_summary_YYYY-MM-DD.md` for example output format.

## Integration with Other Analysis Tools

This script complements:
- `counter_intelligence_analysis.py` - Deep counter-intelligence analysis
- `friday_eow_audit.py` - End-of-week structural audits
- `daily_alpha_audit.py` - Daily alpha metrics
