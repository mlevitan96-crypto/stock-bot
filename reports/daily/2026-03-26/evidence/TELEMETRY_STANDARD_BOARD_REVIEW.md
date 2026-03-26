# Telemetry Standard — Board Review

**Purpose:** Institutionalize telemetry as a governed contract so future additions cannot drift, misplace files, or fail to propagate. Memory Bank standard, enforcement gates, dashboard visibility, droplet verification.

**Date:** 2026-03-03

---

## Personas

### Adversarial: Where can drift still happen?

- **Schema vs writers:** New code paths (e.g. reconciliation, backfill) might write to logs without going through the checklist; the IO map and gate only catch known patterns. **Mitigation:** TELEMETRY_ADDING_CHECKLIST is mandatory for any new telemetry; CI/local `make telemetry_gate` runs contract audit with strict-canonical; new writers should be added to build_telemetry_io_map.py patterns.
- **Naming mismatches:** Different modules might use different keys (e.g. entry_ts vs entry_timestamp). **Mitigation:** TELEMETRY_STANDARD.md and telemetry_schemas.py define canonical names; validators and audit report missing canonical fields; strict-canonical mode treats missing direction/side/position_side as blocking for exit_attribution/exit_event.
- **"Field exists but empty" trap:** Readiness could count records where direction_intel_embed is {} or intel_snapshot_entry is {}. **Mitigation:** Standard and direction_readiness logic require **non-empty** intel_snapshot_entry for telemetry-backed count; dashboard Telemetry Health shows direction X/100 from the same readiness state.
- **Hidden readers:** Reports, EOD, replay, and governance scripts read logs; if a path or field is moved, they can break. **Mitigation:** TELEMETRY_IO_MAP and DATA_CONTRACT_CHANGELOG document readers; deprecation requires dual-read period and changelog.

---

### Risk: Any chance telemetry changes affect decisions?

- **No.** All telemetry writes are best-effort (try/except, never raise). No scoring, sizing, or exit logic depends on success of telemetry capture. The gate and dashboard are read-only diagnostics. Adding or enforcing schema does not change order flow.

---

### SRE: Log growth, rotation, rollback, monitoring hooks

- **Log growth:** intel_snapshot_*.jsonl and direction_event.jsonl are append-only; position_intel_snapshots.json is pruned by age (30d). Rotation/size caps for intel logs are recommended in a follow-up (documented in DATA_INTEGRITY_PLAN and board review).
- **Rotation:** Not implemented in this change; SRE should add logrotate or equivalent for logs/intel_snapshot_*.jsonl and logs/direction_event.jsonl.
- **Rollback:** Revert Memory Bank docs, enforcement scripts, dashboard Telemetry Health, and droplet verification changes; no migration. Telemetry writers remain additive.
- **Monitoring:** Dashboard Telemetry Health panel shows log existence, last-write, and direction coverage. Alerting can hook on gate_status FAIL or direction_telemetry_trades regression (e.g. drop to 0 after being > 0).

---

### Product/Operator: Does this reduce future wiring failures?

- **Yes.** A single Memory Bank standard (TELEMETRY_STANDARD.md) and adding checklist (TELEMETRY_ADDING_CHECKLIST.md) force every new telemetry to: writer in hot path, persist for exit join, embed in exit_attribution/exit_event, update schemas, update audits, document droplet steps and rollback. The integrity gate (`make telemetry_gate`) fails the build if contract or direction wiring is broken. Dashboard Telemetry Health gives operators immediate visibility of canonical log presence and direction X/100 without running scripts by hand. Droplet verification produces a single PASS/FAIL verdict and exact failing gate, so deploy confidence is measurable.

---

## Finalization sign-off (2026-03-03)

- **Adversarial:** No hidden readers or empty-field masking; direction_readiness and Telemetry Health both require non-empty intel_snapshot_entry for counting. IO map and changelog document readers; strict-canonical gate enforces canonical fields on new exit records.
- **Risk:** Confirmed telemetry changes do not affect trading decisions; all writes are best-effort and read-only for dashboard/audit.
- **SRE:** Log growth, rotation, and rollback documented; monitoring via Telemetry Health and gate_status. Droplet verification produces PASS/FAIL and exact failing gates (see DATA_INTEGRITY_BLOCKERS.md until verification passes).
- **Product/Operator:** Future telemetry additions must follow Memory Bank checklist (TELEMETRY_ADDING_CHECKLIST.md); enforcement via telemetry_integrity_gate and droplet verification.

**Verification status:** Droplet verification has been run; current result FAIL (blockers documented in reports/audit/DATA_INTEGRITY_BLOCKERS.md). Sign-off applies to the standard and process; system is "telemetry-complete" only after blockers are resolved and verification re-run returns PASS.

---

## Droplet Data Authority sign-off (2026-03-03)

- **Adversarial:** Confirms no path exists to produce conclusions from local data. Analysis/replay/backtest entrypoints (trade_visibility_review, run_direction_replay_30d, backtest_governance_check, run_board_review_on_droplet_data, run_governance_48h_report_on_droplet) enforce `src/governance/droplet_authority.py`: local run without `--allow-local-dry-run` exits non-zero; local runs with `--allow-local-dry-run` are explicitly non-authoritative. Authoritative runs require execution on droplet with `DROPLET_RUN=1`, `--droplet-run`, and `--deployed-commit`.
- **SRE:** Confirms droplet-only enforcement (shared guard), rollback safety (no trading logic changes; revert Memory Bank + droplet_authority + script wiring + dashboard), and monitoring (Telemetry Health and Governance status expose `last_droplet_analysis`; banner "No authoritative data review has been run" when absent).
- **Product/Operator:** Confirms reduced false confidence from empty or local-only datasets. Reports and board recommendations must cite droplet run (deployed_commit + run_ts); task is FAILED if droplet execution did not occur. Dashboard shows last droplet analysis run (script, commit, run_ts) so operators see authority at a glance.

---

*Ref: memory_bank/TELEMETRY_STANDARD.md, memory_bank/TELEMETRY_ADDING_CHECKLIST.md, scripts/audit/telemetry_integrity_gate.py, src/governance/droplet_authority.py, reports/audit/DATA_INTEGRITY_DROPLET_VERIFICATION.md, reports/audit/DATA_INTEGRITY_BLOCKERS.md.*
