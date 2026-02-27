# Conditional Expectancy (Phase 2)

No replay data. Run `blocked_signal_expectancy_pipeline.py` first (and ensure score_snapshot.jsonl / blocked_trades.jsonl have attribution).

When data exists, this report will contain:
- **Expectancy by slice** (overall mean_pnl, n, win_rate) for: bucket, slice_uw, slice_regime_macro, slice_other, slice_flow, slice_dark_pool, slice_market_tide, slice_calendar.
- **Signal × condition** (mean_pnl_pct, n) for groups (uw, regime_macro, other_components) and components (flow, dark_pool, market_tide, calendar, regime, whale, event).
- **Interaction: uw × regime_macro** (mean_pnl_pct, n, win_rate per cell).
