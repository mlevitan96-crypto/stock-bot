# ALPACA_DIRECTIONAL_PNL_ANALYSIS

## Summary (tail sample, realized `pnl` present)

```json
{
  "LONG": {
    "n": 280,
    "sum_pnl": 28.8533,
    "win_rate": 0.5679,
    "expectancy": 0.103048,
    "p5": -4.2,
    "p50": 0.18,
    "p95": 3.77
  },
  "SHORT": {
    "n": 152,
    "sum_pnl": -17.45,
    "win_rate": 0.4737,
    "expectancy": -0.114803,
    "p5": -3.42,
    "p50": -0.04,
    "p95": 2.52
  },
  "UNKNOWN_SIDE": {
    "n": 0,
    "sum_pnl": 0.0,
    "win_rate": null,
    "expectancy": null
  }
}
```

## Regime × direction (top regimes by row count)

### Regime `mixed`
- **LONG**: n=280, sum_pnl=28.8533, win_rate=0.5679, E[pnl]=0.103048, p5=-4.2, p95=3.77
- **SHORT**: n=152, sum_pnl=-17.45, win_rate=0.4737, E[pnl]=-0.114803, p5=-3.42, p95=2.52

## Questions

- **Should we flip bias?** Evidence: `NO_FLIP_LONG_OUTPERFORMS_IN_TAIL` — based on expectancy in **this tail only**; not causal proof of alpha (confounders: symbol mix, time).
- **Gate direction by regime or confidence?** If regime cells are sparse (low n), gating increases variance; use shadow tests before production gates.

## Method

- Direction from `side` (normalized LONG/SHORT).
- PnL from `pnl` USD field.

