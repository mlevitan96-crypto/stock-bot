# Coverage baseline (warehouse mission)

**Command (droplet):**

```bash
cd /root/stock-bot && PYTHONPATH=. python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py \
  --root /root/stock-bot --days 90 --max-compute
```

**Artifact:** `reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1745.md`

## Head summary (verbatim fields)

- **DATA_READY:** NO  
- **execution_join_coverage_pct:** 100.00  
- **fee_coverage_pct:** 100.00  
- **slippage_coverage_pct:** 100.00  
- **uw_coverage_pct:** 100.00  
- **blocked_candidate_coverage_pct:** 21.66% (170 / 785)

**Dominant warehouse blocker:** blocked/near-miss bucket coverage below gate; not caused by strict chain repair.

**Note:** This run was executed as part of the same verification session as the post-backfill strict audit (not a separate “pre-code” warehouse snapshot). Strict chain state does not change warehouse join counters; this file records the coverage surface **at verification time**.
