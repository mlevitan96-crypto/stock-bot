# Repo report lockdown (permanent)

**TS:** `20260326_LOCKDOWN`

## CI (`.github/workflows/report-layout.yml`)

On every pull request, `verify_report_layout.py` enforces:

1. **Strict on-disk tree** — no new sprawl under `reports/` outside canonical daily layout + `reports/state/`.
2. **Git added paths** — new `.md`/`.json`/`.csv` under `reports/` must match the same contract.
3. **Evidence completeness** — if `evidence/` has report-like files, `DAILY_MARKET_SESSION_REPORT.md` must exist and be non-empty.

## Code

- `scripts/maintenance/report_path_rules.py` — single source of allowed paths.
- `scripts/maintenance/verify_report_layout.py` — CI entrypoint.
- `scripts/maintenance/repo_wide_report_cleanup.py` — rule-based move/delete for legacy sprawl.
- `scripts/maintenance/ensure_daily_stubs_for_evidence_sessions.py` — stub daily files for archive sessions.

## Legacy directories

`reports/audit/` and other non-daily roots are **not** valid targets for new report output. Reintroduction of report files there will fail the strict tree check.
