# ALPACA TELEMETRY SURFACES — Writability

- Service user (systemctl): `root`
- Check window: writable + mtime within **24h** OR path missing (FAIL if required)

| Surface | Path | Exists | Writable | Age (s) | Recent (<24h) | Verdict |
|---------|------|--------|----------|---------|---------------|--------|
| run.jsonl (trade_intent / exit_intent) | `logs/run.jsonl` | True | True | 2155 | yes | **PASS** |
| orders.jsonl | `logs/orders.jsonl` | True | True | 6816 | yes | **PASS** |
| positions.jsonl | `logs/positions.jsonl` | False | True | n/a | yes | **PASS** |
| attribution.jsonl | `logs/attribution.jsonl` | True | True | 6816 | yes | **PASS** |
| exit_attribution.jsonl | `logs/exit_attribution.jsonl` | True | True | 8244 | yes | **PASS** |
| system_events.jsonl | `logs/system_events.jsonl` | True | True | 82 | yes | **PASS** |
| signal_context.jsonl | `logs/signal_context.jsonl` | False | True | n/a | yes | **PASS** |
| telemetry.jsonl | `logs/telemetry.jsonl` | True | True | 82 | yes | **PASS** |
| pnl_reconciliation.jsonl | `logs/pnl_reconciliation.jsonl` | False | True | n/a | yes | **PASS** |
| master_trade_log.jsonl | `logs/master_trade_log.jsonl` | True | True | 6816 | yes | **PASS** |
| composite_attribution.jsonl | `logs/composite_attribution.jsonl` | False | True | n/a | yes | **PASS** |
| reconcile.jsonl | `logs/reconcile.jsonl` | True | True | 2460 | yes | **PASS** |
| data/pnl_attribution.jsonl | `data/pnl_attribution.jsonl` | False | True | n/a | yes | **PASS** |
| state/position_metadata.json | `state/position_metadata.json` | True | True | 2460 | yes | **PASS** |
| state/regime_detector_state.json | `state/regime_detector_state.json` | True | True | 6799 | yes | **PASS** |

## Notes

- Core append-only logs: `run.jsonl`, `orders.jsonl`, `attribution.jsonl`, `exit_attribution.jsonl`, `system_events.jsonl`.
- Missing optional files may PASS if the directory is writable (first write creates them).
