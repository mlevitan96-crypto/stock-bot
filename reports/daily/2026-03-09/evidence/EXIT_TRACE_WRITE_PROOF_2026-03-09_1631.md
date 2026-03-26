# Exit Trace Write-Health PROOF — 2026-03-09_1631

**Generated:** 2026-03-09T16:31:36.708035+00:00

## SRE runtime verification

- exit_decision_trace.jsonl exists: True, size: 134403

- exit_trace_write_health.jsonl exists: yes, size: 666

## Write-health content check

- Health records in window: 4
- Records with ts within 5 min: 4
- written=true: 4
- written=false: 0

### Last 5 write-health records

- 1. ts=2026-03-09T16:29:02.836482+00:00 trade_id=open_AMD_2026-03-09T16:06:14.496Z written=True error_type=None
- 2. ts=2026-03-09T16:31:54.065961+00:00 trade_id=open_BA_2026-03-09T16:05:05.641Z written=True error_type=None
- 3. ts=2026-03-09T16:32:20.621839+00:00 trade_id=open_BA_2026-03-09T16:05:05.641Z written=True error_type=None
- 4. ts=2026-03-09T16:33:29.430778+00:00 trade_id=open_CVX_2026-03-09T16:02:39.925Z written=True error_type=None

## CSA verdict

- **EXIT_TRACE_WRITE_HEALTH_PROVEN**: Write-health telemetry is live; no silent trace write failures.