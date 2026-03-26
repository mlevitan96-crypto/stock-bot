# Massive PnL review rerun (20260327_MKTS_FINAL)

## Pipeline

1. `alpaca_pnl_market_session_unblock_pipeline.py`
2. `alpaca_pnl_session_demo_fixture.py`
3. `alpaca_forward_truth_contract_runner.py` (market session epochs)
4. `alpaca_pnl_cohort_alignment_check.py`
5. `alpaca_pnl_massive_final_review.py`

## Artifacts

- Truth: `reports/ALPACA_MARKET_SESSION_TRUTH_20260327_MKTS_FINAL.json`
- Cohort IDs: `reports/ALPACA_MARKET_SESSION_COMPLETE_TRADE_IDS_20260327_MKTS_FINAL.json`
- Closeout: `reports/audit/ALPACA_PNL_REVIEW_CLOSEOUT_20260327_MKTS_FINAL.md`
