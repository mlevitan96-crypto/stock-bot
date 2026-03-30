# ALPACA_100TRADE_DISCOVERY_20260330_211500Z

## Current milestone stack

| Concern | Module / file | Notes |
|--------|----------------|-------|
| Session open (09:30 ET, weekday-aware) | `telemetry/alpaca_telegram_integrity/session_clock.py` | Shared baseline for all session-scoped counts |
| Canonical counting | `telemetry/alpaca_telegram_integrity/milestone.py` → `count_since_session_open` | `build_trade_key(symbol, side, entry_ts)`; dedupe set; `exit_ts >= open_epoch` |
| 250 milestone guard | `state/alpaca_milestone_250_state.json` | `should_fire_milestone` / `mark_milestone_fired` |
| Cycle orchestration | `telemetry/alpaca_telegram_integrity/runner_core.py` | Loads coverage, strict gate, exit probe, pager, then Telegram sends |

## Extension point for 100-trade

- **Correct place:** `runner_core.run_integrity_cycle` **after** `cov`, `strict`, `schema_reasons`, and `max_age` exist, **before** the 250-milestone block.
- **Guard:** new `state/alpaca_100trade_sent.json` via `checkpoint_100.py` (load/save only) so **250 logic and file remain untouched**.
