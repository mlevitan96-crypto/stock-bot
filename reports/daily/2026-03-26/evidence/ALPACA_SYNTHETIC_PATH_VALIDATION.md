# ALPACA SYNTHETIC PATH VALIDATION
Generated: 2026-03-19T17:29:27.346657+00:00

## Dry-run / audit evidence (no live orders)
- orders.jsonl with dry_run=true: 0
- system_events branch_taken=mock_return: 0

## Controlled validation
- Full path to entry/exit: use existing full_system_audit.py with AUDIT_MODE=1 AUDIT_DRY_RUN=1
- Inject known-good signals: mock_signal_injection or test harness (read-only)
- Telemetry emission: verified in Phase 4
