# Alpaca 2000-trade edge discovery — board review

- **Frozen dataset:** 36 trades, hash `5ea13259ab84c83b`
- **Report dir:** `alpaca_edge_2000_20260317_1721`

## Data integrity

- **Join coverage (entry):** 0.0%
- **Join coverage (exit):** 0.0%
- **Snapshot null rates (exit):** mfe=6/7, mae=6/7, pnl_unrealized=7/7, margins=7/7

**If join coverage < threshold, lever attribution conclusions are invalid.**

## Top helpful/harmful entry components (by contribution → expectancy)

- **a**: n=3, mean_contrib=0.0000, mean_pnl=$0.00
## Worst 5% trades: dominant entry + dominant exit + gate states

- Trade 0 (PnL=$0.00): dominant_entry=—, dominant_exit=—, gates=[lead_gate=None,exhaustion_gate=None,funding_veto=None,whitelist=None]

## Near misses (small margin to threshold)

- Entry (|margin_to_threshold| < 0.5): 0 trades
- Exit (|pressure_margin_exit_now| < 0.1): 0 trades

## Candidate shortlist (mechanism-level)

See ALPACA_EDGE_PROMOTION_SHORTLIST_<TS>.md. Levers: weight/threshold/gate changes (not labels).

## Summary

**No live or paper changes.** CSA verdict required for any promotion.
