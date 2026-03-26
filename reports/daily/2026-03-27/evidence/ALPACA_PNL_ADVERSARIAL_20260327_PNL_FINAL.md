# Adversarial review (20260327_PNL_FINAL)

## Cohort selection

- **Attack:** `complete_trade_ids` missing from published CERT_OK JSON → cannot verify the 44-trade set equals `forward_trades_complete`.
- **Evidence:** `reports/ALPACA_LAST_WINDOW_TRUTH_20260327_LAST_WINDOW.json` only includes three `chain_matrices_complete_sample` rows.

## PnL reconciliation

- **Attack:** No fills/fees in workspace → any PnL table would be fabricated.
- **Defense:** Reconciliation CSV intentionally empty; STOP-GATE engaged.

## Shadow / blocked lookahead

- **Attack:** Without timestamped shadow ledger aligned to decision clock, path PnL on blocked names risks lookahead.
- **Mitigation:** Require `decision_ledger` + bar timestamps strictly ≤ decision_ts.

## Survivorship

- **Attack:** Strict complete cohort excludes messy chains — survivorship bias vs all submits.
- **Mitigation:** Report parallel `ALL_SUBMITTED` cohort with incompleteness flags (do not mix).

## Interaction overfitting

- **Attack:** Pairwise slices on n=44 will be noise-heavy.
- **Mitigation:** Holdout windows + Bonferroni / pre-registration of pairs.
