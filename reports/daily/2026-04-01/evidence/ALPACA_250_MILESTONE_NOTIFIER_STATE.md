# ALPACA_250_MILESTONE_NOTIFIER_STATE

## Config
- `config/alpaca_telegram_integrity.json`: `milestone_trade_count` = **250**
- `milestone_counting_basis` = **integrity_armed**
- `enabled` = **True**

## Persisted state file
- Path: `state/alpaca_milestone_250_state.json`
```json
{
  "fired_milestone": false,
  "last_count": 0,
  "session_anchor_et": "2026-04-01"
}
```

## Integrity arm (when basis=integrity_armed)
- Path: `state/alpaca_milestone_integrity_arm.json`
```json
{
  "arm_epoch_utc": null,
  "armed_at_utc_iso": null,
  "session_anchor_et": "2026-04-01"
}
```
- **Precheck note (for arm update):** arm_epoch read from state/alpaca_milestone_integrity_arm.json (read-only)

## Computed snapshot (this run)
```json
{
  "session_anchor_et": "2026-04-01",
  "counting_basis": "integrity_armed",
  "count_floor_utc_iso": "(not armed \u2014 waiting for green DATA_READY + coverage + strict ARMED + exit probe)",
  "integrity_armed": false,
  "unique_closed_trades": 0,
  "realized_pnl_sum_usd": 0.0,
  "sample_trade_keys": []
}
```

## should_fire_milestone(target)
- **notifier_trade_count** (snap.unique_closed_trades): **0**
- **fired_milestone** (from should_fire in-memory state; resets on new session_anchor_et): **False**
- **should_fire now:** **False**
- **last_count** in returned state: **0**
- **notifier_last_trade_id_seen** (chronological last in floored set): ``
- **Floored trade count (recomputed):** 0 (floor_epoch=None)
- **Floor stats:** {"note": "integrity not armed \u2014 no floor; notifier uses 0 trades"}
