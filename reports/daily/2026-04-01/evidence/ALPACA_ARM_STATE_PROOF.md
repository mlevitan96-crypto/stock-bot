# Integrity session armed — proof (`arm_epoch_utc`)

## Current ET anchor

**2026-04-01** (`milestone_integrity_arm.session_anchor_et` in dry-run JSON).

## State file (droplet)

Captured in `ALPACA_INTEGRITY_CLOSURE_CONTEXT.md` section `alpaca_milestone_integrity_arm.json`:

```json
{
  "arm_epoch_utc": 1775071231.101308,
  "armed_at_utc_iso": "2026-04-01T19:20:31.101308+00:00",
  "session_anchor_et": "2026-04-01"
}
```

## Dry-run cross-check

`ALPACA_INTEGRITY_CYCLE_DRYRUN_POSTFIX.json`:

- `checkpoint_100_precheck_ok`: **true**
- `milestone_integrity_arm.arm_epoch_utc`: **present** (same anchor)
- `milestone.integrity_armed`: **true**
- `milestone.unique_closed_trades`: **16** (not floored to 0)

## Verdict

**YES** — `arm_epoch_utc` is set and recent for **`session_anchor_et: 2026-04-01`**.
