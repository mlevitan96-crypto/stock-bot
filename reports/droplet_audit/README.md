# Droplet operational readiness audit reports

This folder holds **dated subfolders** with the output of the operational readiness audit run on the droplet (cron).

- **Schedule:** Weekdays 21:32 UTC (after EOD), via `scripts/run_droplet_audit_and_sync.sh`
- **Layout:** `YYYY-MM-DD/audit_summary.txt` (full log), `YYYY-MM-DD/audit_result.json` (date, exit_code, status)
- **Sync:** The same cron job adds this folder and pushes to GitHub so reports appear here.
