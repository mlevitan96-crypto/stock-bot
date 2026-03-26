# Alpaca repair loop — iteration 0 (analysis only)

**TS:** `20260327_0200Z`

## Outcome

No emitter/code fix applied in this iteration (would require additive backfill or execution-path investigation per trade). **Ranked defect** recorded in JSON.

## Strict gate

`trades_incomplete=6` with identical missing-leg pattern across all six `trade_id`s:

- `entry_decision_not_joinable_by_canonical_trade_id`
- `missing_unified_entry_attribution`
- `no_orders_rows_with_canonical_trade_id`
- `missing_exit_intent_for_canonical_trade_id`

## Hypothesis

Subset of closes (symbols PFE, QQQ, WMT, HOOD, LCID, CAT in this window) did not receive the same multi-stream telemetry fan-out as the 83 complete trades—likely batch/ETF or timing path gaps, not gate relaxation.

## Next iteration (out of scope here)

Targeted additive reconstruction from broker/API truth or single-code-path fix in emitters, then re-run `run_alpaca_droplet_learning_cert_final.py`.
