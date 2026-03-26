# Data Integrity — Deploy Record

**Purpose:** Capture deployed commit and deploy time for post-deploy verification and final certification.

---

## Pre-deploy (local) — Completed

| Check | Result |
|-------|--------|
| `python scripts/audit/telemetry_integrity_gate.py --allow-legacy` | PASSED |
| `python scripts/audit/telemetry_integrity_gate.py` (strict) | FAILED (expected on legacy-only data) |
| Memory Bank: TELEMETRY_STANDARD.md, TELEMETRY_ADDING_CHECKLIST.md, TELEMETRY_CHANGELOG.md | Present |
| Enforcement: telemetry_integrity_gate.py, telemetry_contract_audit.py, ensure_telemetry_paths.py, audit_direction_intel_wiring.py | Present |

---

## Merge + Deploy (operator actions)

1. **Merge** the data-integrity / telemetry-standard PR to `main`.
2. **Deploy to droplet** using your standard path, e.g.:
   - SSH to droplet, `cd /root/stock-bot`, `git pull origin main`
   - Or run `python scripts/run_deploy_to_droplet.py` / your deploy script if you use one
3. **Restart services** if required (e.g. stock-bot, dashboard) so the new code is loaded.
4. **Record** below.

---

## Deploy record (fill after deploy)

| Field | Value |
|-------|--------|
| **deployed_commit** | f8e0f0b5d2081fc3e7c3e3495aef0df5fadf2e89 |
| **deploy_ts** | 2026-03-04T17:26:33+00:00 (audit PASS run) |
| **services_restarted** | dashboard (runner pkill + venv/bin/python -u dashboard.py); stock-bot per deploy script |

---

## Commit to deploy (pre-merge)

Current HEAD at time of this doc: **a3c703a0e6699b6ccf240415bac585da1cf11d45**

After merging your telemetry/data-integrity branch, the new HEAD on `main` is the **deployed_commit** to use for `--expected-commit` in verification.

---

*Run verification after deploy and trades: `python scripts/run_data_integrity_verification_on_droplet.py --expected-commit <deployed_commit>`*
