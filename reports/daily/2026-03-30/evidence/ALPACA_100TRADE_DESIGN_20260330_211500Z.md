# ALPACA_100TRADE_DESIGN_20260330_211500Z

## Trigger

- `unique_closed_trades >= checkpoint_100_trade_count` (default 100) for current `session_anchor_et`.

## Idempotency

- `checkpoint_100_info_sent` — informational Telegram delivered.
- `checkpoint_100_deferred_sent` — one drift alert if first hit at 100 was degraded; allows later informational send when pre-check passes.

## Pre-send integrity (all required)

1. Coverage file exists; age ≤ `warehouse_coverage_file_max_age_hours`.
2. Parsed `DATA_READY: YES`.
3. No threshold violations (`coverage_thresholds_pct` vs join/fee/slippage).
4. Exit attribution tail probe: no schema_reasons.
5. `evaluate_completeness` → `LEARNING_STATUS == ARMED`.

Pager (post-close / direction) **excluded** from this gate.

## Messages

- **Green:** `[ALPACA] 100-TRADE CHECKPOINT` + counts, coverage lines, strict, “on track for 250”.
- **Deferred:** `ALPACA DATA INTEGRITY ALERT (100-trade checkpoint deferred)` + degradation bullets.

## Non-goals

- No operator action line on green path.
- No second systemd timer.
- 250 milestone unchanged.
