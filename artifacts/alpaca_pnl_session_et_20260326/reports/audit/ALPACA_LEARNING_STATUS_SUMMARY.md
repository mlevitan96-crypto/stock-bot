# Alpaca learning status summary

## LEARNING SAFE — strict cohort complete; safe to treat as learning-greenlight input.

| Field | Value |
|---|---|
| timestamp_utc | `2026-03-26T22:59:32.185315+00:00` |
| window_hours | 72 |
| window_start_epoch | 1774531800.0 |
| window_end_epoch | 1774555200.0 |
| verdict | **LEARNING_SAFE** |
| trades_seen | 2 |
| trades_incomplete | 0 |
| sre_auto_repair.ran | False |
| sre_auto_repair.actions_applied | 0 |
| sre_auto_repair.residual_incompletes | 0 |
| exit_code | 0 |
| commit_sha | `f1122bca0e0c2e2153268a0dc9df9bfb0961f791` |
| runner | `alpaca_forward_truth_runner` |

## Why this verdict

Process exited **0** (CERT_OK) with **trades_incomplete == 0** and at least one exit in the evaluated cohort. Forward truth contract + SRE engine completed; see `proof_links` for JSON evidence.

## Proof artifacts

- `C:/Dev/stock-bot/reports/daily/2026-03-26/evidence/ALPACA_MARKET_SESSION_TRUTH_20260327_MKTS_FINAL.json`

## Notes

- synthesis_from_truth_json_and_exit_code
