# ALPACA_DASHBOARD_TRADE_COUNT_FIX

## Before
- Situation strip first block used **direction readiness** (`state/direction_readiness.json` → `telemetry_trades` / `total_trades`, tail fallback), labeled “Trades reviewed: X/100”.

## After
- First block: **Total trades (post-era)**, **Next milestone** (100 or 250 or past milestones), **Remaining** to next.
- Source: `compute_canonical_trade_count(root, floor_epoch=None)` in `dashboard.py` `_get_situation_data_sync`.
- API fields: `total_trades_post_era`, `next_trade_milestone`, `remaining_to_next_milestone` (legacy `trades_reviewed*` retained for other readers).
- SSR: `_render_initial_situation_html`; client refresh: `loadSituationStrip` in embedded dashboard script.
