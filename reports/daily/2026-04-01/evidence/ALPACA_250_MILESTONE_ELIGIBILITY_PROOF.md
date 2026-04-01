# 250 milestone eligibility (integrity basis) — closure proof, **no Telegram send**

## Method

Same snapshot path as production: `scripts/run_alpaca_telegram_integrity_cycle.py --dry-run --skip-warehouse --no-self-heal`  
→ `telemetry/alpaca_telegram_integrity/runner_core.py::run_integrity_cycle` builds milestone from `build_milestone_snapshot` + `should_fire_milestone` (send suppressed when `--dry-run`).

## Config basis

`config/alpaca_telegram_integrity.json`: `milestone_counting_basis`: **`integrity_armed`**, `milestone_trade_count`: **250**.

## Observed values (`ALPACA_INTEGRITY_CYCLE_DRYRUN_POSTFIX.json`)

| Field | Value |
|-------|--------|
| `milestone_counting_basis` | `integrity_armed` |
| `milestone.integrity_armed` | **true** |
| `milestone.unique_closed_trades` | **16** |
| `milestone.session_anchor_et` | `2026-04-01` |
| `milestone_integrity_arm.arm_epoch_utc` | **set** (not null) |

## State file (`state/alpaca_milestone_250_state.json`, embedded in context)

```json
{
  "fired_milestone": false,
  "last_count": 16,
  "session_anchor_et": "2026-04-01"
}
```

## `should_fire` for target 250

`unique_closed_trades (16) >= 250` is **false** → **`should_fire` false**.  
`fired_milestone` is **false** for this anchor (not “already fired”).

## Verdict

- **Floored to 0 under integrity_armed?** **NO** — count is **16** with arm epoch present.
- **Eligible to fire 250 right now?** **NO** — count **&lt; 250**.
- **Reason:** threshold not reached (not arm missing, not already fired).
