# ALPACA_TELEGRAM_IMPL_NOTES_20260330_190500Z

## Modules (`telemetry/alpaca_telegram_integrity/`)

- `session_clock.py` — effective 09:30 ET session open (weekends → prior Friday).
- `milestone.py` — JSONL scan `exit_attribution.jsonl`, `build_trade_key`, PnL sum, milestone state.
- `warehouse_summary.py` — latest `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md` parse; optional `run_warehouse_mission` subprocess.
- `checks.py` — `evaluate_completeness`, exit tail probe, SPI glob, cooldown helpers.
- `templates.py` — string formatting (defensive defaults).
- `self_heal.py` — mkdir; `systemctl try-restart alpaca-postclose-deepdive.service` if failed.
- `runner_core.py` — `run_integrity_cycle`.

## CLI

`scripts/run_alpaca_telegram_integrity_cycle.py` — writes append line to `logs/alpaca_telegram_integrity.log` each run for pager compatibility.

## Throttling

- Warehouse mission: every `warehouse_run_every_n_cycles` invocations, **and** only during US RTH ET.
- Alerts: `integrity_alert_cooldown_sec`, `strict_regression_alert_cooldown_sec`.

## Tests

`tests/test_alpaca_telegram_integrity.py`; `tests/test_telegram_failure_detector.py` updated for canonical log path (Windows skips for mtime tests).
