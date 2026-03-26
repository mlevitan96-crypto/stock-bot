# Adversarial review — forward truth contract

**Timestamp:** `20260327_FORWARD_TRUTH_FINAL`

| Claim | Attack | Finding |
|-------|--------|---------|
| Real forward window, not fixtures | Runner could ignore wall clock | `open_ts_epoch` uses `time.time()` and `STRICT_EPOCH_START`; droplet JSON shows `run_utc` and cohort sizes consistent with live `/root/stock-bot/logs`. |
| Deterministic artifacts | Paths vary only by UTC timestamp | Wrapper sets `TS=$(date -u +%Y%m%d_%H%M%SZ)`; same inputs yield same gate output for fixed logs. |
| Repair bounded + idempotent | Unbounded loops / duplicate sidecars | Outer loop capped by `--repair-max-rounds`; subprocess uses `--max-repair-rounds` (default 1 per iteration); `_already_done` in repair prevents duplicate `strict_backfill_trade_id` rows. |
| Incident actionable | INCIDENT omits reasons | INCIDENT JSON includes `reason_histogram`, sample `trade_id`s, `unbackfillable_trade_ids`, and `next_actions_by_reason` map (when exit 2). |
| Scheduler active | Timer disabled | Bundle records timer **active (waiting)** and journal shows service runs. |

Residual: if SSH capture failed silently, rely on on-disk `reports/ALPACA_FORWARD_TRUTH_RUN_*.json` on the droplet (listed in bundle).
