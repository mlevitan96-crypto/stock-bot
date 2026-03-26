# Cohort alignment (20260327_MKTS_FINAL)

```json
{
  "aligned": true,
  "root": "C:\\Dev\\stock-bot\\artifacts\\alpaca_pnl_session_et_20260326",
  "window_start_epoch": 1774531800.0,
  "window_end_epoch": 1774555200.0,
  "cohort_trade_ids_count": 2,
  "expected_trades_complete": 2,
  "missing_trade_ids_in_exit_attribution": [],
  "cohort_ids_exit_timestamp_outside_window": [],
  "exits_in_window_count": 2,
  "window_trade_ids_sample": [
    "open_MKT1_2026-03-26T14:00:00+00:00",
    "open_MKT2_2026-03-26T15:30:00+00:00"
  ],
  "extras_in_window_not_in_cohort": []
}
```

## Droplet parity

Re-run `alpaca_forward_truth_contract_runner.py` on `/root/stock-bot` with the same `--window-start-epoch` / `--window-end-epoch`, then `scp` `logs/exit_attribution.jsonl` (session slice) and `reports/ALPACA_MARKET_SESSION_COMPLETE_TRADE_IDS_<TS>.json` into this workspace and re-run `alpaca_pnl_cohort_alignment_check.py` with `--root` pointing at the merged tree. This proof uses the **synthetic** fixture under `artifacts/alpaca_pnl_session_et_20260326` to validate the toolchain.
