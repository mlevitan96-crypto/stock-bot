# Alpaca PnL review — scope (20260327_PNL_FINAL)

## Today (UTC) vs session

- **Calendar date (operator):** 2026-03-26 (workspace `user_info`).
- **NYSE regular session (America/New_York):** 09:30–16:00 ET on that calendar date.
- **Certified strict window (artifact-backed):** last-window forward truth `reports/ALPACA_LAST_WINDOW_TRUTH_20260327_LAST_WINDOW.json`: `OPEN_TS_UTC_EPOCH`=1774548000.0, `EXIT_TS_UTC_EPOCH_MAX`=1774555200.0 (2h ending NYSE cash close 16:00 ET → epoch 1774555200).
- **Label:** `EXECUTED_QUALIFIED_LAST_WINDOW` — **not** full calendar UTC day unless a separate daily gate JSON is provided with `exit_ts_max` = end-of-session and `complete_trade_ids` populated.

## Qualified definition (strict)

1. Forward chain `forward_truth_contract` = CERT_OK and `trades_incomplete` = 0 for the evaluated gate.
2. Each trade: full strict matrix (intent entered, unified entry, orders keyed, exit_intent, unified exit terminal, exit_attribution row with pnl + positive exit_price).
3. Cohort membership per `FORWARD_SINCE_UTC_EPOCH` and open-time parsed from `trade_id`.

## Blockers (fail-closed)

- **B1** `complete_trade_ids`: artifact lacks full enumeration: have 0 ids, expected 44 (re-run forward truth runner with collect_complete_trade_ids; see telemetry gate + scripts/audit/alpaca_forward_truth_contract_runner.py).
- **B3** `execution_joined.jsonl.gz`: replay_bundle_empty_or_tiny_bytes=48
- **B3** `fills.jsonl.gz`: replay_bundle_empty_or_tiny_bytes=37
- **B4** `workspace_exit_attribution_window`: local logs/exit_attribution.jsonl has 0 exits in [1774548000.0,1774555200.0] but certified JSON claims n=44 — droplet slice not in workspace.

## Queries / reproduction

```bash
python scripts/audit/alpaca_forward_truth_contract_runner.py --root <DROPLET_ROOT> \
  --window-hours 2 --window-end-epoch 1774555200 \
  --json-out reports/ALPACA_LAST_WINDOW_TRUTH_<NEW_TS>.json \
  --md-out reports/audit/ALPACA_LAST_WINDOW_TRUTH_<NEW_TS>.md \
  --incident-md reports/audit/_incident.md --incident-json reports/audit/_incident.json
```

Gate implementation: `telemetry/alpaca_strict_completeness_gate.py` (`evaluate_completeness`).
Runner now passes `collect_complete_trade_ids=True` so `complete_trade_ids` is populated on next CERT_OK run.
