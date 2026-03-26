# Telemetry Standard — SAFE_TO_APPLY PR Checklist

**Scope:** Institutionalize telemetry as a governed contract (Memory Bank, enforcement, dashboard, droplet verification). No live trading behavior changes.

---

## Deliverables

| Item | Path |
|------|------|
| Memory Bank standard | memory_bank/TELEMETRY_STANDARD.md |
| Adding checklist | memory_bank/TELEMETRY_ADDING_CHECKLIST.md |
| Changelog | memory_bank/TELEMETRY_CHANGELOG.md |
| Schema authority | src/contracts/telemetry_schemas.py (existing) |
| Contract audit (strict-canonical) | scripts/audit/telemetry_contract_audit.py --strict-canonical |
| Integrity gate | scripts/audit/telemetry_integrity_gate.py |
| Makefile target | make telemetry_gate |
| Dashboard Telemetry Health | /api/telemetry_health + Telemetry Health tab (More menu) |
| Droplet verification | scripts/run_data_integrity_verification_on_droplet.py (PASS/FAIL verdict, failing gates) |
| Board review | reports/board/TELEMETRY_STANDARD_BOARD_REVIEW.md |

---

## Gates (must pass)

- [ ] `make telemetry_gate` exits 0 once new exit records (with canonical direction/side/position_side) exist. Until then, use `make telemetry_gate_legacy` to pass with legacy-only data.
- [ ] `python scripts/audit/telemetry_contract_audit.py --strict-canonical --n 50` produces no blocking failures for exit_attribution/exit_event when those logs contain records written after the data-integrity deployment.
- [ ] Dashboard loads and Telemetry Health tab shows log status and direction coverage.
- [ ] Droplet verification script runs and writes VERDICT: PASS or FAIL with explicit failing gates (run after deploy + trades for PASS).

---

## Runbook / PR checklist

- **Before merge:** Run `make telemetry_gate` locally. Ensure no new telemetry is added without updating memory_bank/TELEMETRY_ADDING_CHECKLIST.md and TELEMETRY_CHANGELOG.md.
- **After deploy:** Run `python scripts/run_data_integrity_verification_on_droplet.py`; expect PASS once intel_snapshot_entry exists and at least one exit has non-empty direction_intel_embed.

---

## Rollback

Revert Memory Bank docs, scripts/audit/telemetry_integrity_gate.py, Makefile, dashboard Telemetry Health (API + tab + loader), and droplet verification changes. No schema migration; telemetry writers unchanged.

---

*Ref: memory_bank/TELEMETRY_STANDARD.md, reports/board/TELEMETRY_STANDARD_BOARD_REVIEW.md.*
