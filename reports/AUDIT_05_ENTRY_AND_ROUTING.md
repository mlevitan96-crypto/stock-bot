# Audit §5: Entry and Routing

**Generated:** 2026-01-27T03:25:13.282569+00:00
**Date:** 2026-01-26

## Result
- **PASS:** False
- **Reason:** no audit_dry_run entries in orders.jsonl (submit_entry path not exercised or failed)

## Evidence
- **entry_dryrun_stdout:** [CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=$150,000
✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $182,085.77, Equity: $50,284.89
submit_entry result: (Order({   'asset_class': 'us_equity',
    'asset_id': 'b28f4066-5c6d-479b-a2af-85dc1a8f16fb',
    'canceled_at': None,
    'client_order_id': 'SPY_buy_0.7217819352417247_1769484311296_24f53542',
    'created_at': '2026-01-27T03:25:11.306221127Z',
    'expired_at': None,
    'expires_at': '2026-01-27T21:00
- **entry_dryrun_stderr:** DEBUG: AUDIT_MODE=1, AUDIT_DRY_RUN=1
DEBUG: After import - AUDIT_MODE=1, AUDIT_DRY_RUN=1
INFO:state_manager:State loaded successfully: 16 positions
DEBUG: Result type: <class 'tuple'>
DEBUG: First element: Order({   'asset_class': 'us_equity',
    'asset_id': 'b28f4066-5c6d-479b-a2af-85dc1a8f16fb',
    'canceled_at': None,
    'client_order_id': 'SPY_buy_0.7217819352417247_1769484311296_24f53542',
    'created_at': '2026-01-27T03:25:11.306221127Z',
    'expired_at': None,
    'expires_at': '2026
- **entry_dryrun_rc:** 0
- **orders_dry_run_count:** 0