# Alpaca last-5 learning-only audit (postfix)

**Command:**

```bash
cd /root/stock-bot && PYTHONPATH=. python3 scripts/audit/alpaca_postfix_learning_n_audit.py \
  --root . --deploy-floor-ts 1774670865 --n 5 --open-ts-epoch 0
```

## Summary

| Field | Value |
|-------|--------|
| LEARNING_STATUS | BLOCKED |
| learning_fail_closed_reason | postfix_insufficient_recent_closes |
| trades_seen | 0 |
| trades_complete | 0 |
| postfix_insufficient_closes | true |
| postfix_allow_intent_blocker | true |

## POSTFIX_META

```json
{
  "postfix_min_exit_ts_epoch": 1774670865.0,
  "postfix_recent_closes_limit": 5,
  "postfix_closes_in_window": 0
}
```

## Outcome

**FAIL (0/5)** — STOP; do not unblock learning until five postfix closes exist and audit returns ARMED with `trades_complete == 5`.
