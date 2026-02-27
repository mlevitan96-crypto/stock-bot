# Phase 7 / Phase 8 Dashboard proof

Sample JSON responses for the Attribution & Effectiveness tab (Phase 8 UX).

**Trade ID lookup:** Uses live logs only (`logs/attribution.jsonl`, `logs/exit_attribution.jsonl`), last 5000/3000 lines. For backtest trades, use effectiveness tables or export from the backtest dir.

## Sample responses (saved as files)

- **sample_attribution_trade.json** — Example response from `GET /api/attribution/trade/<trade_id>`: joined entry/exit attribution, exit_quality_metrics, blame_hint.
- **sample_effectiveness_signals.json** — Example response from `GET /api/effectiveness/signals` including `source_mtime` (Phase 8 freshness).

## Screenshots (capture manually)

Please add one screenshot per panel when verifying the dashboard:

1. **Attribution & Effectiveness tab — top:** Data freshness badge (source_mtime, source path, "From latest backtest" or "From reports fallback") + Trade ID search box + Look up.
2. **Attribution & Effectiveness tab — trade lookup result:** Entry attribution table, Exit attribution table, Exit quality (MFE/MAE/giveback/time_in_trade/exit_efficiency), Blame hint line.
3. **Attribution & Effectiveness tab — effectiveness tables:** Signal Effectiveness, Exit Effectiveness, Counterfactual Exit, each with "Download JSON" link.

Save screenshots as `effectiveness_freshness.png`, `effectiveness_trade_lookup.png`, `effectiveness_tables.png` (or similar) in this directory.
