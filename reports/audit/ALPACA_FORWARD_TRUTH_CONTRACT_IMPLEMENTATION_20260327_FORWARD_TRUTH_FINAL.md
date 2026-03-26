# Alpaca forward truth contract — implementation

**Timestamp:** `20260327_FORWARD_TRUTH_FINAL`

## Runner

**Path:** `scripts/audit/alpaca_forward_truth_contract_runner.py`

**Behavior:**

1. Computes `open_ts_epoch = max(STRICT_EPOCH_START, time.time() − window_hours×3600)` and `forward_since_epoch = open_ts_epoch`.
2. Calls `evaluate_completeness(root, open_ts_epoch=..., forward_since_epoch=..., audit=True)` (same module as CLI gate).
3. Precheck or structural `main.py` path → exit **1**, minimal JSON + MD.
4. If `trades_incomplete > 0`, loops up to `--repair-max-rounds` times:
   - Subprocess: `alpaca_strict_six_trade_additive_repair.py --apply --repair-all-incomplete-in-era --open-ts-epoch <open_ts_epoch> --max-repair-rounds <internal>` (default internal **1** per iteration).
   - Sleeps `--repair-sleep-seconds`.
   - Re-runs the strict gate.
5. If `trades_incomplete == 0` → writes run JSON + MD (**CERT_OK**), exit **0**. Removes stale incident files at the same paths if present.
6. Else → writes run JSON, **INCIDENT** JSON + MD (sample ≤50 `trade_id`s, reason histogram, recoverable vs unbackfillable via `build_lines_for_trade`), exit **2**.

**CLI flags:** `--window-hours`, `--repair-max-rounds`, `--repair-sleep-seconds`, `--repair-internal-rounds-per-iteration`, `--json-out`, `--md-out`, `--incident-md`, `--incident-json`, `--root`.

## Repair primitive (unchanged semantics)

**Path:** `scripts/audit/alpaca_strict_six_trade_additive_repair.py`  
**New flag:** `--max-repair-rounds` (default 8) caps internal flush rounds for `--repair-all-incomplete-in-era`.

## Artifacts

- Per run: `reports/ALPACA_FORWARD_TRUTH_RUN_<TS>.json`, `reports/audit/ALPACA_FORWARD_TRUTH_RUN_<TS>.md`  
- On incident: `reports/ALPACA_FORWARD_TRUTH_INCIDENT_<TS>.json`, `reports/audit/ALPACA_FORWARD_TRUTH_INCIDENT_<TS>.md`  
- `<TS>` = `date -u +%Y%m%d_%H%M%SZ` from `deploy/systemd/alpaca-forward-truth-contract-run.sh`

## Deploy helper

**Path:** `scripts/audit/run_alpaca_forward_truth_contract_deploy.py` — git sync, upload, `systemctl daemon-reload`, enable timer, manual run, journal capture.
