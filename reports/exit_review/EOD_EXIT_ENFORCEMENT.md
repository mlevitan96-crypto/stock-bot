# EOD exit enforcement (daily)

Wire into daily EOD so that:

1. **Run exit effectiveness v2**
   ```bash
   python scripts/analysis/run_exit_effectiveness_v2.py --start YYYY-MM-DD --end YYYY-MM-DD
   ```
   Output: `reports/exit_review/exit_effectiveness_v2.json`, `exit_effectiveness_v2.md`.

2. **Run dashboard truth audit** (includes Exit Truth panel when contract has it).
   ```bash
   bash scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh
   ```
   Or the EOD script that runs the audit: `bash scripts/run_dashboard_truth_audit.sh /tmp/dashboard_contract.json ...`

3. **Fail EOD if**
   - `logs/exit_truth.jsonl` is missing or stale (e.g. no lines in last 24h when trading).
   - Exit truth coverage below threshold (e.g. lines per day).
   - Dashboard truth audit reports FAIL for any panel (including Exit Truth).
   - Objective function regresses beyond tolerance (optional; compare effectiveness_aggregates or exit_effectiveness_v2 overall vs baseline).

Add these checks to the EOD script or cron so they run daily and block completion on failure.
