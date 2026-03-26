# ALPACA Rampant Summary — `20260325_0205`

## Dataset sizes
- run.jsonl: 2052 | orders: 16442 | signal_context: 1 | blocked: 19206 | exit_attribution: 2860
- outcomes w/ pnl_pct: 2858 | entry×exit joined (canonical_trade_id): 0

## Economics
- Included: exit `pnl_pct`, `exit_quality_metrics` when present; order economics fields when explicitly set.
- Excluded: silent fee/slippage; historical rows missing schema treated as unknown — not zero.

## Top 10 candidate edges (one line each; NOT PROMOTED)
1. `v2_exit.vol_expansion` | Δmean_pnl≈-0.09416 | n=2857 | exit_attribution
2. `v2_exit.score_deterioration` | Δmean_pnl≈-0.01828 | n=2857 | exit_attribution
3. `v2_exit.regime_shift` | Δmean_pnl≈-0.01016 | n=2857 | exit_attribution
4. `v2_exit.sentiment_deterioration` | Δmean_pnl≈-0.00886 | n=2857 | exit_attribution
5. `v2_exit.sector_shift` | Δmean_pnl≈-0.00700 | n=2857 | exit_attribution
6. `v2_exit.flow_deterioration` | Δmean_pnl≈0.00000 | n=2857 | exit_attribution
7. `v2_exit.darkpool_deterioration` | Δmean_pnl≈0.00000 | n=2857 | exit_attribution
8. `v2_exit.thesis_invalidated` | Δmean_pnl≈0.00000 | n=2857 | exit_attribution
9. `v2_exit.overnight_flow_risk` | Δmean_pnl≈0.00000 | n=2857 | exit_attribution
10. `v2_exit.earnings_risk` | Δmean_pnl≈0.00000 | n=2857 | exit_attribution

## Top 5 do-not-chase mirages
1. Features with |lift| ≈ 0 across quartiles (constant v2_exit components)
2. Exit-time predictors of same-bar pnl (reverse causality / leakage)
3. Single-split rankings without walk-forward agreement
4. High |lift| on n<100 after field filtering
5. Blocked-trade 'savings' without counterfactual execution path

## CSA — offline analysis legitimacy: **PASS**

## What to watch tomorrow (data only)
- Growth of `trade_intent` / `orders` rows carrying `decision_event_id` + `canonical_trade_id`.
- `signal_context.jsonl` volume (currently sparse = limited blocked/enter context joins).
- Order rows with `fee_excluded_reason` / `slippage_bps` for economics completeness.
- **No tuning or config changes** from this report.

**Full report:** `/root/stock-bot/reports/ALPACA_RAMPANT_ANALYSIS_20260325_0205.md`
