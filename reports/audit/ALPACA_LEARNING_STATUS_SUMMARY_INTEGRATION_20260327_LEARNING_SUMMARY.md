# Alpaca learning status summary — integration

**Timestamp:** `20260327_LEARNING_SUMMARY`

## `alpaca_forward_truth_contract_runner.py`

After writing the run truth JSON (all terminal paths: precheck **1**, structural **1**, CERT_OK **0**, INCIDENT **2`), calls `_emit_learning_summary` via importlib load of `alpaca_learning_status_summary.py`. Failures are logged to stderr and do not change runner exit codes.

## `alpaca_last_window_learning_verify.py`

After the forward truth subprocess and last-window verdict MD, emits the same rolling summary from the last-window truth JSON and subprocess exit code.

## Forward truth systemd timer

Deploy uploads `alpaca_learning_status_summary.py` with the runner (`run_alpaca_forward_truth_contract_deploy.py`).
