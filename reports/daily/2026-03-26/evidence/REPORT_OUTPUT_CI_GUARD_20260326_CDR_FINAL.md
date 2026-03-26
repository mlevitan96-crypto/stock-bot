# Report output CI guard (final)

**TS:** `20260326_CDR_FINAL`

## Checks

1. **Git added paths:** `.md`/`.json`/`.csv` under `reports/` in `git diff --diff-filter=A <base>..HEAD` must match:
   - `reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.*`, or
   - `reports/daily/<YYYY-MM-DD>/evidence/**`
2. **Working tree:** any `reports/daily/<YYYY-MM-DD>/evidence/` that contains at least one `.md`/`.json`/`.csv` must have non-empty `DAILY_MARKET_SESSION_REPORT.md` beside `evidence/`.

## Implementation

- `scripts/maintenance/verify_report_layout.py`
- Workflow: `.github/workflows/report-layout.yml` (runs on all pull requests)
- Local: `make verify_report_layout`

## Base ref fallback

Same as before: `origin/main` then `HEAD~1` if fetch fails.
