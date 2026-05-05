# Intel Dashboard — 2026-01-01

## 1. Universe Overview
- Daily universe (v1): **14**
- Daily universe (v2, shadow-only): **14**
- Universe v1 version: `2026-01-20_universe_v1`
- Universe v2 version: `2026-01-20_universe_v2`

## 2. Premarket/Postmarket Intel
- Premarket intel symbols: **14** (version `2026-01-20_uw_v1`)
- Postmarket intel symbols: **14** (version `2026-01-20_uw_v1`)

## 3. Regime & Sector Profiles
- Regime: **NEUTRAL** (conf 0.25)
- Regime engine version: `2026-01-20_regime_v1`

## 4. UW Attribution Highlights (tail)
- **AAPL** dir=bullish uw_score_delta=0.10152
- **AAPL** dir=bullish uw_score_delta=0.1692
- **AAPL** dir=bullish uw_score_delta=0.10152
- **AAPL** dir=bullish uw_score_delta=0.1692
- **AAPL** dir=bullish uw_score_delta=0.10152
- **AAPL** dir=bullish uw_score_delta=0.1692
- **AAPL** dir=bullish uw_score_delta=0.10152
- **AAPL** dir=bullish uw_score_delta=0.1692
- **AAPL** dir=bullish uw_score_delta=0.10152
- **AAPL** dir=bullish uw_score_delta=0.1692

## 5. UW Intel P&L Summary
- Attribution records: **0**, matched: **0**
- No per-feature P&L aggregates available yet.

## 6. Health & Self-Healing Status
- Health: **OK**
- Checks: **19**
  - freshness:daily_universe: ok
  - freshness:core_universe: ok
  - freshness:daily_universe_v2: ok
  - freshness:premarket_intel: ok
  - freshness:postmarket_intel: ok
  - freshness:uw_usage_state: ok
  - freshness:regime_state: ok
  - freshness:uw_intel_pnl_summary: ok
  - schema:daily_universe: ok
  - schema:core_universe: ok
  - schema:daily_universe_v2: ok
  - schema:premarket_intel: ok

## 7. UW Flow Daemon Health
- Status: **healthy**
- PID ok: **True** (ExecMainPID=12345)
- Lock ok: **True** (lock_pid=12345, held=True)
- Poll fresh: **True** (age_sec=60.0)
- Crash loop: **False** (restarts=0)
- Endpoint errors: **False** (counts={'uw_invalid_endpoint_attempt': 0, 'uw_rate_limit_block': 0})
- Self-heal attempted: **False** (success=None)

## 8. Shadow Trading Snapshot (v2)
- Shadow trade candidates today: **0**
- No shadow trade candidates logged yet (ensure `SHADOW_TRADING_ENABLED=true` and v2 compare is running).

## 9. Exit Intelligence Snapshot (v2)
- Exit attributions: **0**
- Exit score stats: `{'max': None, 'mean': None, 'min': None, 'n': 0}`

## 10. Post-Close Analysis Pack
- Pack folder: `analysis_packs/2026-01-01/`
- Master summary: `analysis_packs/2026-01-01/MASTER_SUMMARY_2026-01-01.md`
- Critical flags: (none detected from current health state)
