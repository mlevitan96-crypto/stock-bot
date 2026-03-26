# Data Integrity — Final Certification

**Status:** Certification **PASS** — Learning & Visibility full audit run on droplet passed; dashboard confirmed.

**Date:** 2026-03-04

---

## 1. Deployed commit

| Field | Value |
|-------|--------|
| **deployed_commit** | f8e0f0b5d2081fc3e7c3e3495aef0df5fadf2e89 |
| **deploy_ts** | 2026-03-04T17:26:33+00:00 |

See **reports/audit/DATA_INTEGRITY_DEPLOY.md** for deploy record and operator steps.

---

## 2. Verification summary

| Check | Status |
|-------|--------|
| Learning & Visibility full audit (droplet) | **PASS** — all phases passed |
| Telemetry coverage (at least one telemetry-backed exit_attribution) | PASS (10/200 in last 200) |
| Dashboard /api/telemetry_health | Reachable (unauthenticated GET allowed for audit) |
| direction_intel_embed.intel_snapshot_entry at exit | Non-empty on telemetry-backed records |
| direction_readiness.json | Present on droplet; telemetry_trades/total_trades updated by cron |

---

## 3. Sample redacted records (after PASS)

**Exit (exit_attribution.jsonl) with embed** (redacted symbol/ids; droplet 2026-03-04):
- Recent records include `direction_intel_embed.intel_snapshot_entry` and `intel_snapshot_exit` (non-empty where telemetry-backed).
- Shape: `entry_timestamp`, `exit_reason`, `entry_uw`, `exit_uw`, `direction_intel_embed`, `entry_regime`, `exit_regime`, etc.

**Entry:** intel_snapshot_entry written at position open; join key `symbol:entry_ts[:19]`; stored in state/position_intel_snapshots.json and logs/intel_snapshot_entry.jsonl.

---

## 4. Readiness counter state (after PASS)

**state/direction_readiness.json** (droplet snapshot at certification):
- `total_trades`, `telemetry_trades`, `pct_telemetry`, `ready`, `ready_ts`; updated by cron. Audit Phase 3 verified file exists and API matches.

---

## 5. Dashboard confirmation

- **/api/telemetry_health:** Reachable on droplet (unauthenticated GET for audit). Audit Phase 4 passed; response includes log_status, direction_telemetry_trades, direction_total_trades, direction_ready.
- **/api/direction_banner,** **/api/situation:** Verified in same audit run.
- Dashboard started by audit runner when needed (pkill + venv/bin/python -u dashboard.py).

---

## 6. Rollback instructions

1. Revert the data-integrity / telemetry-standard PR (main.py, direction_intel.py, master_trade_log.py, Memory Bank docs, scripts/audit/*, dashboard Telemetry Health, droplet verification script).
2. Redeploy to droplet; restart services.
3. No schema migration or data deletion required; additive fields only. Legacy readers continue to work.

---

## 7. Telemetry-complete

- This file has been updated with **deployed_commit** f8e0f0b, **deploy_ts** 2026-03-04, and **Verification summary** PASS.
- **reports/audit/LEARNING_VISIBILITY_BLOCKERS.md** cleared (no blockers as of 2026-03-04).
- Learning & Visibility full audit: `python scripts/run_learning_visibility_audit_on_droplet.py` — **PASS** on droplet.

**Current:** Certification complete. Re-run audit after future deploys as needed.

---

*Ref: reports/audit/DATA_INTEGRITY_DEPLOY.md, reports/audit/DATA_INTEGRITY_BLOCKERS.md, reports/audit/DATA_INTEGRITY_DROPLET_VERIFICATION.md, memory_bank/TELEMETRY_STANDARD.md.*
