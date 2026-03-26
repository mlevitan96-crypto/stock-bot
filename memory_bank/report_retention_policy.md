# Report retention policy (memory)

- **Canonical `DAILY_*`:** keep indefinitely; `prune_stale_reports.py` never deletes them.
- **Session `evidence/`:** delete all files when session calendar date is older than **N** days (default **3**) vs UTC `date.today()`.
- **Stray `reports/daily/<date>/*`:** non-`DAILY_*` report files at session root deleted when that session is expired (same calendar rule).
- **Legacy `reports/**` outside `reports/daily/`:** delete `.md`/`.json`/`.csv` when file **mtime** age **> N days** (not named `DAILY_*` — there should be none in legacy roots).
- **Logs / raw telemetry:** not reports; not pruned by this job.
- **Automation:** `scripts/maintenance/prune_stale_reports.py --retention-days 3` (`make prune_reports`).
- **CI:** `scripts/maintenance/verify_report_layout.py` — **strict `reports/` tree** (only `daily/…` + `state/`) + git-added path guard + **evidence ⇒ DAILY_*** (`.github/workflows/report-layout.yml`).
- **Bulk legacy cleanup:** `scripts/maintenance/repo_wide_report_cleanup.py` (rule-based move to `daily/<date>/evidence/` or delete if stale).
- **Stub dailies:** `scripts/maintenance/ensure_daily_stubs_for_evidence_sessions.py` for archive sessions that only have evidence.
- **Path rules module:** `scripts/maintenance/report_path_rules.py`.
