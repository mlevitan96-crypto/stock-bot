# ALPACA DEEP CSA VERDICT (Stage 2)

- UTC `20260330_181609Z`

1. **Threshold suppression:** At capture, no position met stop-loss, profit target, trail, stale windows, v2>=0.80, or structural `should_exit`.
2. **Stale windows:** 120m stale-trade and 12d stale-time gates did not apply given **age_min** and PnL (see DEEP_EXIT_MATH table).
3. **Decay:** With **entry_score==0** for all tracked rows, **decay_ratio exit is disabled** by construction in `evaluate_exits`.
4. **Structural:** No `should_exit` true in snapshot — not failing to fire; conditions not met (or module returned false).
5. **v2 exit score:** Values are far below **0.80** for all symbols at capture — under current intel, v2 exit promotion would not trigger.
