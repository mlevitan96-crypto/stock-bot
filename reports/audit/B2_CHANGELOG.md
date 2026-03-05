# B2 Live Paper — Changelog

**Generated (UTC):** 2026-03-03

## What changed

- **Feature flag:** `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT` (env, default `false`). When `true`, the early signal_decay exit path (position hold < 30 minutes) is **suppressed**; the position is not closed on signal_decay alone until hold ≥ 30 min.
- **Instrumentation:** On every suppressed early signal_decay exit, a structured event is emitted:
  - `event_type`: `b2_suppressed_signal_decay_exit`
  - `trade_id`, `symbol`, `side`, `timestamp`, `reason` (signal_decay), `hold_minutes`, `decay_ratio`, `entry_score`, `current_composite`
  - Written to `logs/b2_suppressed_signal_decay.jsonl` and via `log_event("exit", "b2_suppressed_signal_decay_exit", ...)`.
- **Paper-only enforcement:** Unchanged from existing behavior: when `TRADING_MODE=PAPER` (or paper mode detected) and `ALPACA_BASE_URL` does not contain "paper", any live order path raises `RuntimeError`, increments `state/paper_safety_violation.json` count, and logs a CRITICAL `paper_safety_violation` event.
- **Config:** `TRADING_MODE` is now read from env via `get_env("TRADING_MODE", "PAPER")` so droplet can explicitly set PAPER.

## What explicitly did NOT change

- No gate changes (score floors, expectancy gates, etc.).
- No sizing changes (position size, notional, etc.).
- No symbol or session restrictions.
- No other exit paths (stop-loss, profit target, trail stop, or signal_decay for hold ≥ 30 min) were modified.
- No change to live order submission logic other than the existing paper_safety check.
