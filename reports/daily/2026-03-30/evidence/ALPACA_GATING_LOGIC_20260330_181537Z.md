# ALPACA GATING LOGIC (Stage 2)

- UTC `20260330_181537Z`

## Gate inventory

| gate | blocks | currently | detail |
| --- | --- | --- | --- |
| risk_freeze (run_once early return) | new entries | YES — max_drawdown_exceeded |  |
| capacity_limit | new entries (unless displacement) | YES | 32/32 |
| min_hold_seconds (exit_timing_policy) | exits that would otherwise fire | NO (all positions past floor) | min_hold_seconds=300 |
| B2 early signal_decay suppression | signal_decay exit when hold<30m | ENABLED in Config |  |
| decay_ratio exit | — | PATH OFF (all entry_score<=0) |  |
| stale_trade (120m + momentum) | — | not triggered (no row hit) |  |
| time stale (12d + flat pnl) | — | not triggered |  |
| regime-aware stale (PANIC) | stale-only exits in PANIC | OFF |  |
| v2_exit_score >= 0.80 | — | not triggered (no row >= 0.80) |  |
| exit_pressure_v3 | — | pathway OFF (env unset/false) |  |
| profit_target (engine decimal) | — | not hit |  |
| stop_loss (engine decimal) | — | not hit |  |
| trailing_stop (price vs trail) | — | not hit |  |
| structural_exit | — | not asserted |  |

## Notes

- **risk_freeze** stops the trading loop from placing new risk; it does not by itself disable `evaluate_exits` (see loop health).
- Rows under profit/stop/trail/v2/stale describe **why no automatic exit fired** at capture — triggers were not satisfied.
