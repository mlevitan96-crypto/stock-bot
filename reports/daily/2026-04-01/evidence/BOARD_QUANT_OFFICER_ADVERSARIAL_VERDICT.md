# Quant Officer adversarial memo — integrity closure

## Causal validity for learning

**Improved when `arm_epoch_utc` is set** under `integrity_armed`: milestone counts use a defined post-arm floor (`compute_canonical_trade_count`), aligning Telegram milestones with the same integrity precheck used for checkpoint messaging.

## Bias / timing risk

- **Session vs era strict mismatch:** learning audits using **era** cohorts may show BLOCKED while **intraday** integrity is ARMED — promotion experiments must declare which strict snapshot governs the hypothesis.
- **Arm timestamp:** counts include only exits **after** `arm_epoch_utc`; historical PnL attribution is unchanged but **milestone deltas** are conditional on arm moment.

## Guardrails before promotion experiments

1. Freeze **coverage artifact path + DATA_READY** in experiment appendix.
2. Record **`session_anchor_et`** and **`arm_epoch_utc`** alongside cohort SQL / JSON.
3. Reject experiment promotion if **integrity precheck** fails on the same UTC day as the experiment window.
