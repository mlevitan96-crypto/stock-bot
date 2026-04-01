# Coverage after strict chain verification

Same warehouse invocation and artifact as baseline for this session:

- **Report:** `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1745.md`
- **DATA_READY:** NO  
- **blocked_candidate_coverage_pct:** 21.66%

Strict completeness moved to **ARMED**; **DATA_READY** remains **NO** for an independent warehouse reason (blocked-intent bucket coverage), which continues to block integrity precheck (`checkpoint_100_precheck_ok`) and milestone arming.

See `ALPACA_COVERAGE_PARSE_AFTER_FIX.json` for `parse_coverage_smoke_check.py` output against the latest coverage markdown.
