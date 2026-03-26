# Report output CI guard (20260327_ROFC)

## Workflow

- `.github/workflows/report-layout.yml` on PR when `reports/**`, `scripts/**`, `src/report_output/**` change.

## Check

- `python scripts/maintenance/verify_report_layout.py --base origin/main` (fallback `HEAD~1`).
- New `.md`/`.json`/`.csv` under `reports/` must be either:
  - `reports/daily/<YYYY-MM-DD>/DAILY_MARKET_SESSION_REPORT.*`, or
  - under `reports/daily/<YYYY-MM-DD>/evidence/**`.

## Local

- `make verify_report_layout`

## Note

- “Canonical report missing for a session” is enforced operationally by running the market-session pipeline; no static tree scan in CI (avoids false positives on fresh clones).
