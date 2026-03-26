# Massive PnL review rerun (20260327_MKTS_FINAL)

## Pipeline

1. `alpaca_pnl_market_session_unblock_pipeline.py`
2. `alpaca_pnl_session_demo_fixture.py`
3. `alpaca_forward_truth_contract_runner.py` (market session epochs)
4. `alpaca_pnl_cohort_alignment_check.py`
5. `alpaca_pnl_massive_final_review.py --output-dir evidence/`
6. `assemble_daily_market_session_report.py`

## Canonical (operator)

- `reports/daily/2026-03-26/DAILY_MARKET_SESSION_REPORT.md`
