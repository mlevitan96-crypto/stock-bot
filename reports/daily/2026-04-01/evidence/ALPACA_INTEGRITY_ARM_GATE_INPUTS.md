# ALPACA_INTEGRITY_ARM_GATE_INPUTS

Each gate below is evaluated in `_checkpoint_100_integrity_ok` + runner-fed `cov_reasons` / `schema_reasons`.

## Gate: warehouse coverage artifact present
- **expected_source:** `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_*.md` (latest by mtime) — `warehouse_summary.load_latest_coverage`
- **observed_path:** `/root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1649.md`
- **exists:** True
- **mtime_utc:** `2026-04-01T16:49:55.250496+00:00`
- **size_bytes:** `573`
- **pass/fail:** PASS
- **code_condition_reference:** `cov.path is None` → append `missing_coverage_artifact` (`runner_core.py` `_checkpoint_100_integrity_ok`)

## Gate: coverage artifact age
- **max_age_h (config):** 36.0
- **observed age_hours:** 0.14
- **pass/fail:** PASS
- **code_condition_reference:** `cov.age_hours > max_age_h` → `coverage_artifact_stale`

## Gate: DATA_READY == YES
- **observed data_ready_yes:** None
- **pass/fail:** FAIL
- **code_condition_reference:** `cov.data_ready_yes is not True` → `DATA_READY not YES (or unknown)`

## Gate: coverage % thresholds
- **thresholds_pct (config):** `{"execution_join": 95.0, "fee": 95.0, "slippage": 80.0}`
- **observed:** execution_join=100.0, fee=100.0, slippage=100.0
- **cov_reasons (threshold + warehouse stale line):**
```
(none)
```
- **pass/fail (_coverage_vs_thresholds subset):** PASS
- **code_condition_reference:** `_coverage_vs_thresholds` in `runner_core.py`

## Gate: stale_or_missing_warehouse_coverage (runner precondition)
- **observed:** appended to cov_reasons when path missing OR age > max_age
- **present in cov_reasons:** False

## Gate: exit_attribution tail schema probe
- **expected_source:** `logs/exit_attribution.jsonl` last **400** lines
- **exit file exists:** True
- **last row exit/ts (sampled tail read):** `2026-04-01T16:39:46.485839+00:00`
- **lines_scanned:** 315
- **missing_field_counts:** `{'symbol': 0, 'exit_ts': 0, 'trade_id': 0}`
- **schema_reasons:** `[]`
- **pass/fail:** PASS
- **code_condition_reference:** `runner_core.py` — `cnt > max(5, lines_scanned // 4)`

## Gate: strict completeness LEARNING_STATUS == ARMED
- **strict_error (if any):** ``
- **LEARNING_STATUS:** `'BLOCKED'`
- **pass/fail:** FAIL
- **code_condition_reference:** `strict.get('LEARNING_STATUS') != 'ARMED'` in `_checkpoint_100_integrity_ok`

## Composite precheck (this run, read-only)
- **cp_ok:** False
- **cp_bad (ordered):**
```
[
  "DATA_READY not YES (or unknown)",
  "strict LEARNING_STATUS is not ARMED (got 'BLOCKED')"
]
```
