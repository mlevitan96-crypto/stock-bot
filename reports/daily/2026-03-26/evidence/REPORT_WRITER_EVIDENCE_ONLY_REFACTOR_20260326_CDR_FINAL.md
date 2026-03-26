# Report writer evidence-only refactor (final)

**TS:** `20260326_CDR_FINAL`

## Policy

- Detailed outputs: `reports/daily/<ET-date>/evidence/` only.
- Canonical paste: `DAILY_MARKET_SESSION_REPORT.{md,json}` assembled last via `assemble_daily_market_session_report.py`.

## Aligned writers

- Alpaca PnL market session pipeline (`alpaca_pnl_market_session_unblock_pipeline.py`) + assembler.
- Alpaca PnL massive review: `--output-dir` → evidence (when set).
- Alpaca learning status summary + last-window verify + droplet fetch mirror → session `evidence/`.

## When next touched (migrate to evidence + env session date)

- Kraken / baseline scripts: `run_telemetry_learning_baselines.py` (currently `reports/` + `reports/audit/`).
- Forward cert / poll / replay gate scripts writing `reports/ALPACA_*` or `reports/audit/*`.
- Dashboard tab verify JSON default paths.
- `fetch_dashboard_accuracy_audit_from_droplet.py` (partial: `STOCKBOT_REPORT_EVIDENCE_DIR`).

## Reference

- `docs/CANONICAL_DAILY_REPORT_CONTRACT.md`
- `docs/REPO_REPORT_VISIBILITY_RULES.md`
