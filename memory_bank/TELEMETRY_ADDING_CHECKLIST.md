# Telemetry Adding Checklist

Use this checklist when adding or changing telemetry so that new data cannot drift, misplace files, or fail to propagate. No step may be skipped for production telemetry.

---

## 1. Writer in the real hot path

- [ ] Add the write in the **actual** position-open or position-close path (e.g. inside `mark_open` or in the exit block in `main.py`), not only in a secondary or optional path.
- [ ] Use the **same** entry_ts (or trade_id) as the one persisted in position metadata so exit can join.
- [ ] Ensure the write is inside try/except and **never raises** (telemetry must not affect trading).

---

## 2. Persist entry snapshot for exit join (if applicable)

- [ ] If the new telemetry has an "entry" component that exit needs: store it in `state/position_intel_snapshots.json` (or a documented state file) keyed by a stable key (e.g. symbol:entry_ts[:19]).
- [ ] Document the key format in this checklist and in `TELEMETRY_STANDARD.md`.
- [ ] Ensure exit path loads using the **same** key (e.g. from context.entry_ts).

---

## 3. Embed into exit_attribution + exit_event

- [ ] If the new telemetry must appear on exit records: add the embed (e.g. `direction_intel_embed`) to both `build_exit_attribution_record` / `append_exit_attribution` and to the payload passed to `append_exit_event`.
- [ ] Always set the key (e.g. `direction_intel_embed`) to a dict; use empty `{}` on failure so schema and readers see a consistent shape.

---

## 4. Update schema validators

- [ ] Add or extend validators in `src/contracts/telemetry_schemas.py` for the new log type or new required/canonical fields.
- [ ] Update `memory_bank/TELEMETRY_STANDARD.md` with the new truth root or required fields.
- [ ] Run `scripts/audit/telemetry_contract_audit.py` and fix any new blocking issues.

---

## 5. Update dashboard endpoints (if applicable)

- [ ] If a new counter or health metric is needed: add or extend an API (e.g. `/api/telemetry_health` or `/api/direction_banner`) and document in dashboard runbook.
- [ ] Ensure the dashboard shows "coverage" (e.g. X/100) only when the **non-empty** contract is satisfied (see TELEMETRY_STANDARD.md).

---

## 6. Add or extend audit scripts

- [ ] Add the new log path to `scripts/audit/build_telemetry_io_map.py` (LOG_PATTERNS) if it is a new file.
- [ ] Extend `scripts/audit/telemetry_contract_audit.py` to validate the new log (and set blocking vs advisory for canonical fields per contract).
- [ ] If a dedicated audit exists (e.g. `audit_direction_intel_wiring.py`): add checks for the new telemetry and wire into `scripts/audit/telemetry_integrity_gate.py`.

---

## 7. Droplet verification steps

- [ ] Document in `scripts/run_data_integrity_verification_on_droplet.py` or in the runbook: what to verify after deploy (e.g. "new log exists after one entry", "exit record contains non-empty embed").
- [ ] Add a PASS/FAIL gate and exact failing condition to the droplet verification report.

---

## 8. Rollback notes

- [ ] Document rollback: which files to revert, that telemetry-only revert has no trading behavior change, and that additive fields may remain in logs until next deploy.

---

## Data Review & Analysis Requirements

All data review, backtesting, replay, and analysis that produce **conclusions** must run on the droplet. Local runs are non-authoritative.

**Checklist (all required for authoritative analysis):**

- [ ] Code deployed to droplet
- [ ] Droplet commit hash recorded
- [ ] Analysis script executed on droplet (with `DROPLET_RUN=1` and `--droplet-run --deployed-commit <hash>`)
- [ ] Artifacts fetched from droplet
- [ ] Report cites droplet run (commit + timestamp)
- [ ] Local runs (if any) explicitly labeled **NON-AUTHORITATIVE**

> **Governance violation:** Local analysis without droplet execution is invalid for conclusions. Use `--allow-local-dry-run` only for schema validation or dry-run debugging; never treat local output as authoritative.

---

## 9. Changelog

- [ ] Append an entry to `memory_bank/TELEMETRY_CHANGELOG.md` with date, change summary, and any deprecation/dual-read notes.

---

*Authority: memory_bank/TELEMETRY_STANDARD.md. Enforced by scripts/audit/telemetry_integrity_gate.py and CI/local `make telemetry_gate`.*
