# ALPACA_250_MILESTONE_BLOCK_PROOF

## Production-equivalent snapshot (read-only, no send)
- **milestone_counting_basis:** `integrity_armed`
- **session_anchor_et (now):** `2026-04-01`
- **arm_disk session_anchor_et:** `2026-04-01`
- **arm_epoch_utc used for snap:** `None`
- **snap.integrity_armed:** False
- **snap.unique_closed_trades:** 0
- **snap.count_floor_utc_iso:** `(not armed — waiting for green DATA_READY + coverage + strict ARMED + exit probe)`
- **target:** 250
- **should_fire_milestone:** False

## Why `unique_closed_trades` is 0 when unarmed
- **Code:** `milestone.py` `build_milestone_snapshot` — if `integrity_armed` basis and `arm_epoch_utc is None`, returns snapshot with **0** trades.
