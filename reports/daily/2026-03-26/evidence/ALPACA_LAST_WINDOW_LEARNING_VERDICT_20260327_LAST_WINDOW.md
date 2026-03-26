# CSA — last-window learning verdict

**TS:** `20260327_LAST_WINDOW`

## Interpretation

Case A: exit 0, trades_incomplete==0 (trades_seen=44). SRE repair batches applied: 0, rounds_executed: 0.

## Metrics (final_gate)

```json
{
  "trades_seen": 44,
  "trades_complete": 44,
  "trades_incomplete": 0,
  "EXIT_TS_UTC_EPOCH_MAX": 1774555200.0,
  "OPEN_TS_UTC_EPOCH": 1774548000.0
}
```

## Runner exit code

`0`

## CSA verdict line

**CSA_VERDICT: LAST_WINDOW_LEARNING_SAFE**