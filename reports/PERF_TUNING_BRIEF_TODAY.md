# Performance Tuning Brief — Today

**Generated:** 2026-01-28T22:55:45.492605+00:00
**Date:** 2026-01-28

## 1) What happened today

- **Net PnL (USD):** -23.64
- **Win rate (%):** 41.36
- **Max drawdown (USD):** -49.95
- **Trade count:** 162
- **Trade intents:** 1552 (entered: 53, blocked: 1499)

## 2) What diagnostics say (blocked vs exits)

**Blocked counterfactuals:**
- **displacement_blocked:** count=1499, avg CF PnL (30m)=0.0, % would win (30m)=0.0

**Exit quality:**
- **trail_stop(-0.0%)+signal_decay(0.71):** count=1, avg PnL=-8.64, left on table (avg)=None, avg time (min)=2.07
- **signal_decay(0.60):** count=21, avg PnL=0.4785, left on table (avg)=None, avg time (min)=34.29
- **signal_decay(0.58):** count=9, avg PnL=-0.6189, left on table (avg)=None, avg time (min)=12.93
- **signal_decay(0.59):** count=25, avg PnL=-0.4458, left on table (avg)=None, avg time (min)=25.77
- **signal_decay(0.56):** count=3, avg PnL=0.0033, left on table (avg)=None, avg time (min)=0.48
- **signal_decay(0.54):** count=4, avg PnL=0.16, left on table (avg)=None, avg time (min)=8.72
- **signal_decay(0.57)+flow_reversal:** count=4, avg PnL=0.14, left on table (avg)=None, avg time (min)=1.14
- **signal_decay(0.42)+flow_reversal:** count=1, avg PnL=1.76, left on table (avg)=None, avg time (min)=3.63
- **signal_decay(0.39)+flow_reversal:** count=1, avg PnL=-5.0, left on table (avg)=None, avg time (min)=2.52
- **signal_decay(0.57):** count=5, avg PnL=0.126, left on table (avg)=None, avg time (min)=34.22
- **signal_decay(0.59)+flow_reversal:** count=5, avg PnL=-0.0567, left on table (avg)=None, avg time (min)=29.97
- **signal_decay(0.49):** count=4, avg PnL=-1.965, left on table (avg)=None, avg time (min)=41.64
- **signal_decay(0.56)+flow_reversal:** count=1, avg PnL=-1.43, left on table (avg)=None, avg time (min)=70.72
- **signal_decay(0.55)+flow_reversal:** count=3, avg PnL=0.105, left on table (avg)=None, avg time (min)=51.02
- **signal_decay(0.44)+flow_reversal:** count=1, avg PnL=-0.77, left on table (avg)=None, avg time (min)=61.24
- **signal_decay(0.48)+flow_reversal:** count=1, avg PnL=-0.11, left on table (avg)=None, avg time (min)=1.14
- **signal_decay(0.47)+flow_reversal:** count=2, avg PnL=-0.4125, left on table (avg)=None, avg time (min)=33.95
- **signal_decay(0.24):** count=3, avg PnL=-0.1133, left on table (avg)=None, avg time (min)=16.17
- **signal_decay(0.18):** count=2, avg PnL=-0.345, left on table (avg)=None, avg time (min)=41.79
- **signal_decay(0.14):** count=1, avg PnL=0.0, left on table (avg)=None, avg time (min)=9.51
- **signal_decay(0.27):** count=5, avg PnL=-1.052, left on table (avg)=None, avg time (min)=14.65
- **signal_decay(0.28):** count=2, avg PnL=-0.105, left on table (avg)=None, avg time (min)=5.67
- **signal_decay(0.51):** count=2, avg PnL=-0.715, left on table (avg)=None, avg time (min)=7.67
- **signal_decay(0.52):** count=2, avg PnL=-1.67, left on table (avg)=None, avg time (min)=13.37
- **signal_decay(0.54)+flow_reversal:** count=1, avg PnL=-0.52, left on table (avg)=None, avg time (min)=12.07
- **signal_decay(0.43):** count=1, avg PnL=0.29, left on table (avg)=None, avg time (min)=13.15
- **signal_decay(0.55):** count=2, avg PnL=-2.835, left on table (avg)=None, avg time (min)=8.47
- **stale_alpha_cutoff(121min,-0.01%):** count=1, avg PnL=-6.7693, left on table (avg)=None, avg time (min)=121.01
- **signal_decay(0.92)+stale_alpha_cutoff(121min,-0.00%):** count=1, avg PnL=-2.0635, left on table (avg)=None, avg time (min)=120.86
- **signal_decay(0.20):** count=3, avg PnL=-0.01, left on table (avg)=None, avg time (min)=49.31
- **signal_decay(0.33):** count=1, avg PnL=1.06, left on table (avg)=None, avg time (min)=47.01
- **signal_decay(0.45)+flow_reversal:** count=1, avg PnL=0.64, left on table (avg)=None, avg time (min)=32.07
- **signal_decay(0.45):** count=1, avg PnL=0.08, left on table (avg)=None, avg time (min)=55.78
- **signal_decay(0.41):** count=1, avg PnL=-0.03, left on table (avg)=None, avg time (min)=1.33
- **stale_alpha_cutoff(120min,-0.00%):** count=1, avg PnL=-3.296, left on table (avg)=None, avg time (min)=120.46
- **stale_alpha_cutoff(120min,-0.01%):** count=1, avg PnL=-1.22, left on table (avg)=None, avg time (min)=120.1
- **stale_alpha_cutoff(120min,0.02%):** count=1, avg PnL=3.17, left on table (avg)=None, avg time (min)=120.28
- **flow_reversal+stale_alpha_cutoff(120min,0.00%):** count=2, avg PnL=0.66, left on table (avg)=None, avg time (min)=120.45
- **signal_decay(0.43)+flow_reversal:** count=1, avg PnL=0.0, left on table (avg)=None, avg time (min)=35.45
- **signal_decay(0.40)+flow_reversal:** count=1, avg PnL=-0.96, left on table (avg)=None, avg time (min)=58.57
- **trail_stop:** count=2, avg PnL=0.58, left on table (avg)=None, avg time (min)=49.86
- **signal_decay(0.53):** count=1, avg PnL=0.02, left on table (avg)=None, avg time (min)=3.77
- **signal_decay(0.40):** count=1, avg PnL=0.01, left on table (avg)=None, avg time (min)=2.72
- **signal_decay(0.60)+flow_reversal:** count=3, avg PnL=-0.4933, left on table (avg)=None, avg time (min)=19.21
- **stale_alpha_cutoff(120min,0.00%):** count=1, avg PnL=0.7, left on table (avg)=None, avg time (min)=120.1
- **trail_stop+signal_decay(0.90):** count=1, avg PnL=-0.19, left on table (avg)=None, avg time (min)=35.19
- **signal_decay(0.31):** count=1, avg PnL=0.86, left on table (avg)=None, avg time (min)=92.81
- **signal_decay(0.32):** count=1, avg PnL=-0.14, left on table (avg)=None, avg time (min)=92.62
- **signal_decay(0.36):** count=1, avg PnL=-2.88, left on table (avg)=None, avg time (min)=84.22
- **signal_decay(0.39):** count=1, avg PnL=-0.09, left on table (avg)=None, avg time (min)=84.22
- **signal_decay(0.15):** count=3, avg PnL=0.04, left on table (avg)=None, avg time (min)=32.83
- **signal_decay(0.29):** count=1, avg PnL=0.67, left on table (avg)=None, avg time (min)=37.22
- **signal_decay(0.22):** count=1, avg PnL=-2.6, left on table (avg)=None, avg time (min)=33.37
- **signal_decay(0.26):** count=1, avg PnL=0.09, left on table (avg)=None, avg time (min)=29.93
- **signal_decay(0.17):** count=2, avg PnL=-0.32, left on table (avg)=None, avg time (min)=13.42
- **signal_decay(0.16):** count=2, avg PnL=0.565, left on table (avg)=None, avg time (min)=15.88
- **signal_decay(0.46):** count=1, avg PnL=-1.055, left on table (avg)=None, avg time (min)=4.36
- **signal_decay(0.58)+flow_reversal:** count=2, avg PnL=-1.31, left on table (avg)=None, avg time (min)=30.59
- **signal_decay(0.49)+flow_reversal:** count=1, avg PnL=0.92, left on table (avg)=None, avg time (min)=31.25
- **signal_decay(0.46)+flow_reversal:** count=1, avg PnL=0.09, left on table (avg)=None, avg time (min)=0.69
- **signal_decay(0.30):** count=1, avg PnL=0.2, left on table (avg)=None, avg time (min)=20.28
- **signal_decay(0.52)+flow_reversal:** count=1, avg PnL=-0.15, left on table (avg)=None, avg time (min)=25.72

## 3) Which shadow profiles improved expectancy

See SHADOW_TUNING_COMPARISON.md. Excerpt:

```
# Shadow Tuning Comparison

**Generated:** paper simulation only. NOT LIVE — no trading logic or config changed.

## Profile results (hypothetical PnL vs baseline)

| Profile | Hypothetical PnL (USD) | Δ vs baseline |
|---------|-------------------------|--------------|
| baseline | -23.64 | +0.00 |
| relaxed_displacement | -23.64 | +0.00 |
| higher_min_exec_score | -23.64 | +0.00 |
| exit_tighten | -23.64 | +0.00 |

## Summary

- **Best expectancy (hypothetical):** baseline (PnL -23.64 USD)

- **Relaxed displacement:** Adds counterfactual PnL from blocked trades; improves if blocks were costly.
- **Higher MIN_EXEC_SCORE:** Fewer trades (not simulated here); compare baseline vs fewer-entry scenario separately.
- **Exit tighten:** Adds heuristic savings from reduced left-on-table; improves if exits were late.

## NOT LIVE YET

Any config change (displacement, MIN_EXEC_SCORE, trailing-stop, time-exit) must be:
- CONFIG ONLY,
- DISABLED by default,
- Documented and applied only after human review.

```

## 4) Intelligence recommendations

| Entity type | Entity | Status | Confidence | Suggested action |
|-------------|--------|--------|------------|------------------|
| signal_family | alpha_signals | hurt | high | consider_downweight |
| signal_family | flow_signals | hurt | high | consider_downweight |
| signal_family | regime_signals | hurt | high | consider_downweight |
| signal_family | volatility_signals | hurt | high | consider_downweight |
| signal_family | dark_pool_signals | hurt | high | consider_downweight |
| gate | displacement_blocked | neutral | high | monitor_only |

## 5) NOT LIVE YET — Proposed config changes

The following are **recommendations only**; not applied. Any change that would affect live trading must be:
- CONFIG ONLY,
- DISABLED by default,
- Documented and applied only after human review.

- **PARAM_TUNING:** Consider relaxing displacement (e.g. DISPLACEMENT_MAX_PNL_PCT or DISPLACEMENT_SCORE_ADVANTAGE) if blocked counterfactuals show positive CF PnL.
- **PARAM_TUNING:** Consider increasing MIN_EXEC_SCORE if entry quality is poor.
- **PARAM_TUNING:** Consider tightening trailing-stop or time-exit if exit quality shows high left-on-table.
- **STRUCTURAL:** Add regime filter to reduce trading in hostile regimes.
- **STRUCTURAL:** Diversify symbols/themes to reduce single-name risk.
