# CSA Review — Alpaca Loss Forensics (Causal)

## Ranked drivers (evidence-backed)

1. **Truth Gate: entry-path join failed** [critical] — 67.5% < 80.0% — entry-quality causality not decision-grade
2. **Dominant loss exit reasons** [high] — signal_decay(1072), stale_alpha_cutoff(36), flow_reversal+stale_alpha_cutoff(32)
3. **Long leg drag** [high] — LONG PnL -440.20 vs SHORT -115.31
4. **Negative payoff ratio** [high] — avg_win/|avg_loss|=0.80
5. **Worst symbol bucket: MRNA** [medium] — cumulative -54.57
6. **Exit timing / give-back** [medium] — MFE>0 but loss in top-100 losers: 0

## Classification

- **Entry-quality vs exit-timing:** Use entry composite vs MFE/MAE on losers; high MFE+loss suggests exit path.
- **Directional bias:** long_short.md
- **Gating:** blocked_counterfactual.md

## Most likely root cause (hypothesis)

Dominant realized loss mechanism in-window: see top driver above; confirm with shadow replay.

## Disconfirming tests

- If join coverage improves to >95% and driver ranking unchanged → not a pipeline lie.
- If shorts on down days show high block rate → gating hypothesis strengthens.
