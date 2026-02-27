# Ledger vs order layer reconciliation

Generated: 2026-02-20 18:54 UTC
Window: last 24h

## Counts (same window)

- Ledger entries (last 24h): **3037** (path: `reports/decision_ledger/decision_ledger.jsonl`)
- Ledger entries blocked at expectancy_gate (first fail): **3037**
- Candidates reaching order layer (SUBMIT_ORDER_CALLED): **0**
- Submit calls (same): **0**

## Mismatch explanation

- **Mismatch:** Ledger has candidates but SUBMIT_ORDER_CALLED = 0. So no candidate in this window reached the broker submit. They are blocked earlier (e.g. expectancy_gate in ledger, or submit_entry guards before _submit_order_guarded). The 396 order-related lines seen in a prior run were likely from a different log (e.g. log_order from audit_dry_run or other action), not from the real submit path.
