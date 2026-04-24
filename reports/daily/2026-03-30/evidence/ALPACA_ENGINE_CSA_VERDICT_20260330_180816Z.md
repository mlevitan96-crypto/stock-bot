# ALPACA ENGINE — CSA VERDICT

- UTC `20260330_180816Z`

## Exit pathways

- Positions with **entry_score<=0** (decay path inactive): **32**
- Count where **v2_exit_score>=0.80** but hold_floor blocked: **0**
- Count where **rule_based_would_close** (stop/decay/profit/trail, after B2 mask): **0**
- **B2** early decay suppression active: `True`

## Interpretation (evidence-limited)

- Majority of open positions show **entry_score<=0** in metadata → composite decay exits and some stale-regime gates that depend on score ratios are weakened or inactive.
- **Concurrent cap** reached → structural rotation depends on exits or displacement; if exits do not fire, book stalls.

See `ALPACA_EXIT_DIAGNOSTIC_20260330_180816Z.md` for per-symbol v2 score, trails, and flags.
