# SHADOW_TRADING_CONFIRMATION_2026-01-20

## Data source
- **source**: `Droplet local logs (/root/stock-bot/logs)`
- **generated_utc**: `2026-01-20T16:45:23.899110+00:00`

## Summary
- **real_trades(attribution)**: `642`
- **shadow_events**: `1366`
- **divergences**: `107`
- **shadow_executed**: `152`
- **shadow_executed_with_entry_price**: `152`
- **avg(v2_score - v1_score)** (score_compare): `-0.0212`

## Real vs shadow (symbol overlap)
- **real_symbols**: `49`
- **shadow_executed_symbols**: `50`
- **overlap_symbols**: `47`
- **real_only_symbols**: `2`
- **shadow_only_symbols**: `3`

### Overlap (up to 25)
- AAPL, AMD, BA, BAC, C, COIN, COP, CVX, DIA, F, GM, GOOGL, HD, HOOD, INTC, IWM, JNJ, JPM, LCID, LOW, MA, META, MRNA, MS, MSFT

## Shadow executed samples (up to 5)
- NVDA buy qty=3 entry_price=181.0563 v2_score=3.039 ts=2026-01-20T16:03:48.792302+00:00
- TSLA buy qty=1 entry_price=425.93 v2_score=3.01 ts=2026-01-20T16:04:02.544357+00:00
- SPY buy qty=1 entry_price=683.48 v2_score=2.972 ts=2026-01-20T16:08:22.316392+00:00
- XLI buy qty=3 entry_price=164.685 v2_score=3.121 ts=2026-01-20T16:09:23.443839+00:00
- XLF buy qty=10 entry_price=53.91 v2_score=3.09 ts=2026-01-20T16:09:33.824127+00:00

## Shadow event types
- `score_compare`: `968`
- `shadow_executed`: `152`
- `divergence`: `107`
- `shadow_blocked`: `83`
- `shadow_candidate`: `56`

## Interpretation
- Presence of `shadow_executed` confirms the v2 hypothetical order-intent path is active.
- Presence of non-null `entry_price` confirms the new shadow trade enrichment is active.

