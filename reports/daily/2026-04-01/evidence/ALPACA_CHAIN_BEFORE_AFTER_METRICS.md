# Strict chain — before / after metrics

**Evaluator:** `PYTHONPATH=. python3 scripts/alpaca_strict_completeness_gate.py --root /root/stock-bot --audit --open-ts-epoch 1774458080`

| Metric | Before (baseline JSON) | After (post-backfill JSON) |
|--------|------------------------|----------------------------|
| `LEARNING_STATUS` | BLOCKED | ARMED |
| `trades_seen` | 342 | 342 |
| `trades_complete` | 0 | 342 |
| `trades_incomplete` | 342 | 0 |
| `reason_histogram` | `live_entry_decision_made_missing_or_blocked`: 342; join-related keys populated | `{}` |
| Backfill script | — | `backfill_count 341 applied` |

**Backfill JSONL counts (droplet, `grep -c` on 2026-04-01 run):**

- `logs/strict_backfill_run.jsonl`: `entry_decision_made` 341, `canonical_trade_id_resolved` 341, `exit_intent` 441 (line count includes any prior backfill passes on host).
- `strict_backfill_orders.jsonl`: `grep -c canonical_trade_id` → 441 (same caveat).

**Integrity cycle strict (session default open_ts, not STRICT_EPOCH):** `trades_seen` 111, `trades_incomplete` 0, `LEARNING_STATUS` ARMED — see `chain_fix_mission/ALPACA_INTEGRITY_CYCLE_DRYRUN_FULL.json`.
