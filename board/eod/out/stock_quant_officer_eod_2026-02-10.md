# Stock Quant Officer EOD — 2026-02-10

**Verdict:** NO_GO

## Summary

The system experienced a negative P&L day, with a low win rate of approximately 20%. The majority of exits were due to signal decay and a significant number of potential trades were blocked by system constraints and expectancy score breaches.

## P&L metrics

```json
{
  "total_pnl_usd": -35.65,
  "total_pnl_pct": -0.071,
  "trades": 2223,
  "wins": 446,
  "losses": 591,
  "win_rate": 0.2,
  "max_drawdown_pct": null
}
```

## Regime context

```json
{
  "regime_label": "BEAR",
  "regime_confidence": null,
  "notes": "Market regime inferred from daily_universe_v2.json."
}
```

## Sector context

```json
{
  "sectors_traded": [
    "ENERGY",
    "TECH",
    "UNKNOWN",
    "BIOTECH"
  ],
  "sector_pnl": null,
  "notes": "Sector P&L breakdown not available in the provided bundle summary."
}
```

## Recommendations

- **[high]** 
  

- **[high]** 
  

- **[medium]** 
  

## Citations

- `attribution`: Total P&L USD, trades, wins, losses, and exit reasons were derived from this source.
- `exit_attribution`: Exit counts and specific exit reasons, including 'profit' and 'stop', are attributed to this source.
- `daily_start_equity`: Daily starting equity of 50098.6 USD used for total P&L percentage calculation.
- `peak_equity`: Peak equity of 52566.86 USD is noted, but not directly used for daily max drawdown calculation due to lack of intra-day data.
- `blocked_trades`: Counts and reasons for blocked trades, such as 'displacement_blocked' and 'max_positions_reached', are taken from this source.
- `daily_universe_v2`: Market regime ('BEAR') and sample sectors ('ENERGY', 'TECH', 'UNKNOWN', 'BIOTECH') are derived from this file.

## Falsification criteria

- **fc-1** (attribution): If the total P&L USD for the next EOD bundle remains negative, the current verdict of 'NO_GO' will be confirmed as accurate and the proposed actions were insufficient or ineffective.
- **fc-2** (attribution): If the win rate does not increase above 0.25 within the next 3-5 trading days, the optimization of 'signal_decay' thresholds was not successful.
- **fc-3** (blocked_trades): If the count of 'displacement_blocked' and 'max_positions_reached' trades does not decrease by at least 20% in the next 3-5 trading days, the adjustments to the blocked trade logic were ineffective.