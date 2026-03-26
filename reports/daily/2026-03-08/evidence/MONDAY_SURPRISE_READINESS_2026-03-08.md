# Monday Surprise Readiness

**Date:** 2026-03-08

## A) Time-based
- Market open: engine uses Alpaca clock; timezone UTC in logs.
- DST: no DST-dependent logic; timestamps UTC.
- Pre-market vs regular: session gating in execution.

## B) Data edge cases
- Empty universe: build_daily_universe / trade_universe_v2; empty list => no trades.
- Partial data: enrichment defaults missing to neutral; composite still computed.
- Stale caches: uw_flow_cache freshness decay; DECAY_MINUTES=180.
- First-bar: no special first-bar sizing explosion; POSITION_SIZE_USD cap.

## C) Control-plane
- Kill switch: TRADING_MODE=HALT or systemctl stop stock-bot.
- Config reload: requires restart; no hot reload.
- Cron: verified in Monday readiness; overlap possible, no mutex.

## D) Economic
- max_positions: caps open positions; can suppress at open if full.
- CI: confidence interval can block; logged in gate_diagnostic.
- Exit on open: B2 suppresses early signal_decay exit <30min in paper.
- Sizing: POSITION_SIZE_USD fixed; no first-bar explosion.
