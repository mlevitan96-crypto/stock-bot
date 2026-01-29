# Audit §5: Entry and Routing

**Generated:** 2026-01-27T03:41:33.385808+00:00
**Date:** 2026-01-26

## Result
- **PASS:** True
- **Reason:** OK

## Evidence
- **entry_dryrun_stdout:** [CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=$150,000
✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $181,585.59, Equity: $50,284.89
submit_entry result: (<src.audit_guard.create_mock_order.<locals>.MockOrder object at 0x76f1a2937e60>, 692.73, 'limit', 0.7217819352417247, 'dry_run')
- **entry_dryrun_stderr:** DEBUG: AUDIT_MODE=1, AUDIT_DRY_RUN=1
DEBUG: After import - AUDIT_MODE=1, AUDIT_DRY_RUN=1
INFO:state_manager:State loaded successfully: 16 positions
DEBUG: Result type: <class 'tuple'>
DEBUG: First element: <src.audit_guard.create_mock_order.<locals>.MockOrder object at 0x76f1a2937e60>
DEBUG: Order ID: AUDIT-DRYRUN-2fa26047032a
- **entry_dryrun_rc:** 0
- **orders_dry_run_count:** 3
- **audit_dry_run_check_count:** 3
- **mock_return_count:** 3