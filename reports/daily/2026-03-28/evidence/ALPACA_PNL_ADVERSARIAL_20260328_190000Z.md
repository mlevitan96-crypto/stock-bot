# Adversarial (20260328_190000Z)

- Cohort: explicit `complete_trade_ids` + session epochs.
- Reconciliation: `reconciliation_delta` should be 0 when `ledger_pnl` matches computed net.
- Fixture trades are synthetic (MKT1/MKT2) — do not treat as live edge.
