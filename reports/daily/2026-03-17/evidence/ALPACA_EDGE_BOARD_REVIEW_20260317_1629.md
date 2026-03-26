# Alpaca 2000-trade edge discovery — board review

- **Frozen dataset:** 3 trades, hash `N/A`
- **Report dir:** `alpaca_edge_2000_20260317_1629`

## Data integrity

- **Join coverage (entry):** N/A
- **Join coverage (exit):** N/A
- **Snapshot null rates (exit):** mfe=3/3, mae=3/3, pnl_unrealized=3/3, margins=3/3

**If join coverage < threshold, lever attribution conclusions are invalid.**

## Top helpful/harmful entry components (by contribution → expectancy)

- **a**: n=2, mean_contrib=0.0000, mean_pnl=$2250.00
## Worst 5% trades: dominant entry + dominant exit + gate states

- Trade 1 (PnL=$0.00): dominant_entry=—, dominant_exit=—, gates=[lead_gate=None,exhaustion_gate=None,funding_veto=None,whitelist=None]

## Near misses (small margin to threshold)

- Entry (|margin_to_threshold| < 0.5): 0 trades
- Exit (|pressure_margin_exit_now| < 0.1): 0 trades

## Candidate shortlist (mechanism-level)

See ALPACA_EDGE_PROMOTION_SHORTLIST_<TS>.md. Levers: weight/threshold/gate changes (not labels).

## Summary

**No live or paper changes.** CSA verdict required for any promotion.
