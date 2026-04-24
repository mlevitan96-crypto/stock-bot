# ALPACA_MASSIVE_AUDIT_TRIGGER_DEPENDENCY

## Script: `scripts/audit/alpaca_250_audit_readiness_mission.py`
Uses `exit_attribution.jsonl` tail, matrix files, file presence — **no** `arm_epoch_utc` / `integrity_arm_state` references in script body (static review of mission entry).

## Telegram 250 milestone
- **Depends on arming** when `milestone_counting_basis` is `integrity_armed`: milestone count is 0 until `arm_epoch_utc` set.

## systemd: integrity cycle
- **`alpaca-telegram-integrity.service`** runs `scripts/run_alpaca_telegram_integrity_cycle.py` — this is where `update_integrity_arm_state(..., cp_ok)` runs.

## Verdict
- **Massive / 250-trade readiness mission:** **not gated** on `arm_epoch_utc` in the mission script itself (data surfaces + joins).
- **250 Telegram milestone:** **gated** on armed session count when basis is `integrity_armed`.
