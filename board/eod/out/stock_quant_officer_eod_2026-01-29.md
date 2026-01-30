# Stock Quant Officer EOD — 2026-01-29

**Verdict:** CAUTION

## Summary

No end-of-day bundle files were provided for 2026-01-29. As a result, no quantitative analysis of trading performance, market regime, or sector context could be performed. This report reflects a critical data gap.

## P&L metrics

```json
{
  "total_pnl_usd": null,
  "total_pnl_pct": null,
  "trades": null,
  "wins": null,
  "losses": null,
  "win_rate": null,
  "max_drawdown_pct": null
}
```

## Regime context

```json
{
  "regime_label": "Unknown",
  "regime_confidence": null,
  "notes": "No attribution or exit attribution data available to determine market regime."
}
```

## Sector context

```json
{
  "sectors_traded": [],
  "sector_pnl": {},
  "notes": "No trade data available to determine sector performance."
}
```

## Recommendations

- **[high]** Ensure EOD Bundle Files Are Present
  The 8 canonical EOD bundle files are essential for quantitative review. Please ensure these files are generated and accessible at the expected location for future analysis.

- **[medium]** Verify File Paths and Generation Process
  Investigate why the EOD bundle files for 2026-01-29 were not found. Confirm the correct paths and that the `stock-bot` and related processes are generating these files as expected.

## Citations

- `attribution`: attribution.jsonl missing
- `exit_attribution`: exit_attribution.jsonl missing
- `master_trade_log`: master_trade_log.jsonl missing
- `blocked_trades`: blocked_trades.jsonl missing
- `daily_start_equity`: daily_start_equity.json missing
- `peak_equity`: peak_equity.json missing
- `signal_weights`: signal_weights.json missing
- `daily_universe_v2`: daily_universe_v2.json missing

## Falsification criteria

- **eod_bundle_present** (file_system_check): The 8 canonical EOD bundle files for 2026-01-29 are found in the expected directory.
- **eod_bundle_non_empty** (file_content_check): The located EOD bundle files contain valid, non-empty JSONL/JSON content.