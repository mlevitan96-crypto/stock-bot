# Truth JSON contract (20260327_MKTS_FINAL)

## Rules

1. `telemetry/alpaca_strict_completeness_gate.py` — `complete_trade_ids` cap ≥ 50k.
2. `scripts/audit/alpaca_forward_truth_contract_runner.py` — `collect_complete_trade_ids=True` on `_gate` and SRE `_gate`.
3. **Assertion:** if `trades_complete > 0` then `len(complete_trade_ids) > 0`; else runner exits **2** and writes INCIDENT.

## References

- `alpaca_forward_truth_contract_runner.py` (post-SRE enumeration check)
- `alpaca_sre_auto_repair_engine.py` (`collect_complete_trade_ids=True`)
