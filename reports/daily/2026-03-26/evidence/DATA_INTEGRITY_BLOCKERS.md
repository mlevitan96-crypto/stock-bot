# Data Integrity — Blockers

**Status:** Verification FAILED. Do not consider the system telemetry-complete until these are resolved and verification is re-run.

**Run time (UTC):** 2026-03-03  
**Droplet commit:** a3c703a0e6699b6ccf240415bac585da1cf11d45 (match with expected)

---

## Failing gates

1. **logs/intel_snapshot_entry.jsonl must exist after at least one entry**  
   - Root cause: Entry capture (capture_entry_intel_telemetry) is not running on the droplet, or the code that writes this file is not deployed. The data-integrity change that calls capture_entry_intel_telemetry inside mark_open with the same entry_ts as metadata may not be on droplet main yet.
2. **logs/intel_snapshot_exit.jsonl must exist after at least one close**  
   - Consequence of entry capture not running; exit intel is written by the same code path.
3. **logs/direction_event.jsonl must exist**  
   - Same; written by direction_intel on entry/exit.
4. **At least one exit_attribution record must have non-empty direction_intel_embed.intel_snapshot_entry**  
   - Exit attribution currently has 0/100 with embed. Requires: (a) entry snapshot stored in state at open, (b) capture_exit_intel_telemetry loading it and attaching to rec["direction_intel_embed"].

---

## Exact failure point

- **Entry capture never runs on droplet.** Either the branch with `mark_open` + capture_entry_intel_telemetry and exit embed changes has not been merged to main and deployed, or the droplet has not pulled/restarted after merge.
- **telemetry_contract_audit.py on droplet** failed with ImportError (validate_attribution from telemetry_schemas). The upload of telemetry_schemas.py was interrupted (connection dropped). Re-run verification after ensuring src/contracts/telemetry_schemas.py is present on droplet.

---

## Next actions

1. **Merge and deploy** the data-integrity PR (entry capture in mark_open, exit direction_intel_embed always set, canonical fields, single-append master_trade_log, prune position_intel_snapshots) to main and pull on droplet. Restart any services that run main.py.
2. **Ensure droplet has** src/contracts/telemetry_schemas.py (and scripts/audit/telemetry_contract_audit.py) so contract audit and verification can run.
3. **Let the system run** until at least 5 positions open and 5 close (real trades).
4. **Re-run verification:**  
   `python scripts/run_data_integrity_verification_on_droplet.py --expected-commit <deployed_commit>`  
   Optionally add `--since-ts <deploy_ts>` to restrict the embed check to post-deploy records.
5. When verification returns **VERDICT: PASS**, update or replace this file with a one-line "Blockers resolved as of <date>. See DATA_INTEGRITY_FINAL_CERTIFICATION.md."

---

*Generated after droplet verification run. See reports/audit/DATA_INTEGRITY_DROPLET_VERIFICATION.md.*
