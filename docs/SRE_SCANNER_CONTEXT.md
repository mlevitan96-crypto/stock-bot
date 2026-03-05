# SRE Anomaly Scanner — Context

## Purpose

The SRE (Site Reliability / behavioral) scanner performs **read-only** behavioral delta detection: it compares recent activity (e.g. last 10 minutes) vs a rolling baseline (e.g. 24h) and emits structured anomaly events. It does not change code, config, or runtime behavior.

**Outputs:** `reports/audit/SRE_STATUS.json`, `reports/audit/SRE_EVENTS.jsonl`.

## Automation anomalies ingestion

SRE treats **Cursor Automations** governance outputs as behavioral/repo signals. It does **not** depend on automations to run; if automations are unavailable, SRE still operates on runtime signals alone.

- **Input:** `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json` (written by Governance Integrity automation or `scripts/automations/run_governance_integrity_once.py`).
- **When** `status` is `anomalies` (or `anomalies_detected` is true):
  - SRE writes **`reports/audit/SRE_AUTOMATION_ANOMALY_<date>.md`** with: failed checks, details, tags (e.g. REPO_DRIFT, GOVERNANCE_DRIFT), recommended follow-ups.
  - SRE sets **`automation_anomalies_present: true`** in `SRE_STATUS.json`.
- **Tags** used for correlation: REPO_DRIFT, GOVERNANCE_DRIFT, AUTOMATION_ANOMALY. These help correlate with runtime anomalies and deploy anomalies without duplicating CSA’s strategic role.

## How automation anomalies influence SRE reports

- Automation anomalies are **soft alerts**: they do not by themselves change the SRE `overall_status` (OK vs ANOMALIES_DETECTED), which is driven by runtime events (rate anomalies, silence, distribution drift, etc.).
- The SRE_AUTOMATION_ANOMALY_*.md artifact is available for human and CSA review; CSA already ingests governance status and includes it in Automation Evidence.
- SRE focuses on **behavior and anomaly correlation**; CSA remains the strategic layer for verdicts and overrides.

## Runner

- **Script:** `scripts/sre/run_sre_anomaly_scan.py`
- **Args:** `--base-dir`, `--observed-minutes`, `--baseline-hours`
- **Droplet:** Installed via `scripts/sre/install_sre_scheduler_on_droplet.py` (cron or systemd as configured).
