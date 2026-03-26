# Report output refactor (20260327_ROFC)

## Scripts updated

- `scripts/audit/alpaca_pnl_market_session_unblock_pipeline.py` — all artifacts → `reports/daily/<session-date-et>/evidence/`; calls assembler.
- `scripts/audit/alpaca_pnl_massive_final_review.py` — `--output-dir` for flat evidence output.
- `scripts/audit/assemble_daily_market_session_report.py` — **new**; writes `DAILY_MARKET_SESSION_REPORT.{md,json}`.
- `scripts/audit/fetch_dashboard_accuracy_audit_from_droplet.py` — `STOCKBOT_REPORT_EVIDENCE_DIR` overrides output dir.
- `scripts/maintenance/prune_stale_reports.py` — **new**.
- `scripts/maintenance/verify_report_layout.py` — **new**.

## Modules

- `src/report_output/paths.py`, `src/report_output/__init__.py`

## Docs

- `docs/REPORT_OUTPUT_CONTRACT.md`
- `docs/REPO_VISIBILITY_RULES.md`

## CI

- `.github/workflows/report-layout.yml`

## Makefile

- `verify_report_layout`, `prune_reports`
