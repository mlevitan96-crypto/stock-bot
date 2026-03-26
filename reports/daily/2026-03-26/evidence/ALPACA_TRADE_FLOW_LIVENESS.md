# ALPACA TRADE FLOW LIVENESS
Generated: 2026-03-19T17:29:27.286953+00:00

## Counts (recent)
- exit_attribution (closed trades): 2000
- orders.jsonl: 2000
- run.jsonl (cycles): 1000
- gate_diagnostic (blocked/pass): 1000

## Liveness
- Signals firing: run.jsonl has records
- Entries attempted: run.jsonl + gate_diagnostic show candidate flow
- Orders submitted: orders.jsonl
- Trades opening/closing: exit_attribution

## If trade count low
- Suppression point: check gate_diagnostic (which gate blocks most), expectancy_gate_truth, score floor
- Attribute: signal (no candidates), gate (blocked), risk (position/size), infra (API/connectivity)
