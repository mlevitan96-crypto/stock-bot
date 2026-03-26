# Readiness unlock — Policy (Phase 5)

**Do NOT force readiness.** Allow the system to accumulate trades naturally.

---

## Conditions for direction readiness

- **telemetry_trades >= 100** (exit_attribution records with non-empty direction_intel_embed.intel_snapshot_entry)
- **pct_telemetry >= 90%** (telemetry_trades / total_trades from exit_attribution)

Governance logic: `src/governance/direction_readiness.py` (is_direction_ready, update_and_persist_direction_readiness). Typically run by cron (e.g. scripts/governance/check_direction_readiness_and_run.py).

---

## When readiness flips TRUE

- **state/direction_readiness.json** has `"ready": true`, `telemetry_trades` >= 100, `pct_telemetry` >= 90.
- **Direction replay** may auto-run (depends on your cron/trigger).
- **Dashboard banner** transitions from "Directional intelligence accumulating (X/100)" to "Directional replay results available" or "RESULTS" when replay has completed.

---

## No synthetic or forced counts

Readiness must reflect real trades only. No backfill of direction_intel_embed into historical records for the purpose of reaching 100; new trades after deploy must drive the counter.

---

*Ref: memory_bank/TELEMETRY_STANDARD.md, src/governance/direction_readiness.py.*
