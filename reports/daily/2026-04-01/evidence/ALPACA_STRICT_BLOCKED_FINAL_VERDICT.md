# ALPACA_STRICT_BLOCKED_FINAL_VERDICT

## What EXACTLY was blocking strict?

1. **Precheck (cleared):** `missing_alpaca_unified_events_jsonl` when neither primary nor strict-backfill unified file existed.
2. **Per-trade chain (still BLOCKED for all 111 trades in window):**
   - `live_entry_decision_made_missing_or_blocked`
   - `entry_decision_not_joinable_by_canonical_trade_id`
   - `missing_unified_entry_attribution`
   - `no_orders_rows_with_canonical_trade_id`
   - `missing_exit_intent_for_canonical_trade_id`
3. **Operational root causes on droplet (evidence):** `run.jsonl` has **no** `entry_decision_made`, **no** `exit_intent`, **no** `canonical_trade_id_resolved`, and **no** `trade_intent` with `decision_outcome: entered` in the sampled population; `orders.jsonl` has **20 / 5795** orders with `canonical_trade_id`. Unified log had only exit terminals after backfill, not entry attribution rows keyed to the same aliases.
4. **Aggregate fail-closed:** `LEARNING_STATUS: BLOCKED`, `learning_fail_closed_reason: incomplete_trade_chain` (see `ALPACA_STRICT_GATE_AUDIT.json`).

## Are all blockers fixed now?

**NO.** Precheck and unified terminal / import issues were addressed; **strict completeness remains BLOCKED** for every trade in the evaluated cohort due to the five per-trade reasons above.

## Does coverage parse `DATA_READY` deterministically now?

**YES.** Latest coverage includes `DATA_READY: YES` or `DATA_READY: NO`; `parse_coverage_smoke_check.json` shows `parse_ok: true` and `data_ready_yes: false` (non-null).

## Is the session armed now?

**NO.** `milestone_integrity_arm.arm_epoch_utc` is **null** for `session_anchor_et` `2026-04-01` (`ALPACA_INTEGRITY_CYCLE_DRYRUN.json`). Precheck failed on DATA_READY NO and strict not ARMED.

## Single remaining failing condition (if forced to one)

**Strict `LEARNING_STATUS` is not ARMED** because **every closed trade fails the completeness matrix** (starting with missing live `entry_decision_made` and missing joinable `trade_intent(entered)` / orders / exit_intent / unified entry). Evidence: `ALPACA_STRICT_GATE_AUDIT.json` `reason_histogram` and incomplete examples.
