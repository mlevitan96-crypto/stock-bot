# Alpaca learning status summary

## LEARNING SAFE — strict cohort complete; safe to treat as learning-greenlight input.

| Field | Value |
|---|---|
| timestamp_utc | `2026-03-26T22:18:32.103673+00:00` |
| window_hours | 2 |
| window_start_epoch | 1774548000.0 |
| window_end_epoch | 1774555200.0 |
| verdict | **LEARNING_SAFE** |
| trades_seen | 44 |
| trades_incomplete | 0 |
| sre_auto_repair.ran | False |
| sre_auto_repair.actions_applied | 0 |
| sre_auto_repair.residual_incompletes | 0 |
| exit_code | 0 |
| commit_sha | `235fe9ad407ad0a5ee19d0081b2396371438d9c4` |
| runner | `alpaca_forward_truth_runner` |

## Why this verdict

Process exited **0** (CERT_OK) with **trades_incomplete == 0** and at least one exit in the evaluated cohort. Forward truth contract + SRE engine completed; see `proof_links` for JSON evidence.

## Proof artifacts

- `reports/ALPACA_LAST_WINDOW_TRUTH_20260327_LAST_WINDOW.json`

## Notes

- synthesis_from_truth_json_and_exit_code