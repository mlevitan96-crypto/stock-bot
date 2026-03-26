# Data Integrity — SAFE_TO_APPLY PR Checklist

## Summary

Telemetry and data-integrity wiring only. No change to trading decisions. All proofs below passed locally; droplet verification required before merge.

---

## Gates passed

| Gate | Status |
|------|--------|
| Unit tests (telemetry schema + single-append guard) | Pass |
| scripts/ensure_telemetry_paths.py | Pass |
| scripts/audit/telemetry_contract_audit.py | Pass (no blocking schema failures) |
| Schema validators on sample records | Pass |
| Minimal diff to trading logic | Yes (telemetry only) |

---

## Droplet verification (required to merge)

- [ ] Deploy to droplet
- [ ] Generate at least 5 trades (open + close)
- [ ] Confirm `logs/intel_snapshot_entry.jsonl` exists and has records
- [ ] Confirm last exit_attribution records have `direction_intel_embed` with non-empty `intel_snapshot_entry` where entry ran
- [ ] Confirm `state/direction_readiness.json` has `telemetry_trades` > 0
- [ ] Confirm dashboard direction banner shows X/100 (not 0/100)

---

## Rollback

1. Revert PR (main.py, src/intelligence/direction_intel.py, utils/master_trade_log.py, new scripts/docs).
2. Redeploy.
3. No schema migration; additive fields only.

---

## Artifacts

- reports/audit/DATA_INTEGRITY_PLAN.md
- reports/audit/TELEMETRY_CONTRACT_AUDIT.md
- reports/audit/TELEMETRY_IO_MAP.md
- reports/audit/DATA_INTEGRITY_PROOF.md
- reports/board/DATA_INTEGRITY_BOARD_REVIEW.md
- docs/DATA_CONTRACT_CHANGELOG.md
- src/contracts/telemetry_schemas.py
- scripts/audit/telemetry_contract_audit.py
- scripts/audit/build_telemetry_io_map.py
- validation/scenarios/test_telemetry_contracts.py

---

*If any proof fails on droplet, stop and document in reports/audit/DATA_INTEGRITY_BLOCKERS.md.*
