# Audit §7: Exit Logic

**Generated:** 2026-01-27T03:41:37.307127+00:00
**Date:** 2026-01-26

## Result
- **PASS:** True
- **Reason:** OK

## Evidence
- **force_exits_stdout:** [CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=$150,000
Emitted exit_intent for 3 synthetic exits
- **force_exits_stderr:** 
- **force_exits_rc:** 0
- **exit_intent_count:** 24
- **exit_paths_exercised:** {'stop': 7, 'tp': 7, 'trail': 0, 'time': 7, 'decay': 0, 'counter': 0, 'displacement': 0, 'eod': 0}