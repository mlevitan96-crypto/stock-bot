# ALPACA strict gate — forward segmentation (20260326_1707Z)

## Command (droplet)

`PYTHONPATH=/root/stock-bot venv/bin/python telemetry/alpaca_strict_completeness_gate.py --root . --audit --open-ts-epoch 1774458080 --forward-since-epoch 1774544849.0`

## Exit code

`1` (non-zero when `LEARNING_STATUS` != ARMED or forward rules fail)

## Summary (from parsed JSON)

| Segment | seen | complete | incomplete |
|---------|-----:|---------:|-----------:|
| Legacy | 221 | 104 | 117 |
| Forward | 0 | 0 | 0 |

- **FORWARD_COHORT_VACUOUS:** True
- **FORWARD_CHAIN_PERFECT:** False
- **LEARNING_STATUS:** BLOCKED

Full JSON: `reports/ALPACA_STRICT_GATE_FORWARD_20260326_1707Z.json`

## Tooling note

An earlier bundle could mark `strict_gate_json_parse_error` if a parser used `rfind("{")` (nested structures). `run_forward_cert_on_droplet.py` now uses `find("{")` + `JSONDecoder.raw_decode`.
