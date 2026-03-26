# Shadow exit surgical — 2026-03-09

**Authority:** Droplet. Shadow = counterfactual only; no live change.

## 1) Eligibility-to-exit lag distribution

- Count (trades with lag): 69
- Min / max (min): 2.22 / 144.72
- Mean / median (min): 42.71 / 7.88
- P90 / P95 (min): 109.88 / 135.25

## 2) First-firing exit condition

{
  "unknown": 68,
  "risk_stop": 37,
  "flow_reversal": 57,
  "signal_decay": 12
}

## 3) Shadow: exit-on-first-eligibility

- Current realized PnL (USD): -100.0052
- Shadow captured PnL (USD): 15.77
- Delta (shadow − realized): 115.7752

## 4) Best practices

- Do not promote shadow to live without further validation and A/B or phased rollout.
- Use lag distribution to set monitoring SLOs (e.g. p95 lag < N min).
- First-firing condition informs which exit rule to tune first.
