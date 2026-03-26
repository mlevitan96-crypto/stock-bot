# Scenario Lab Summary

**Date:** 2026-03-12
**Scope:** Parallel analysis-only scenarios. Experiment #1 remains canonical; no ledger writes.

## Scenario ranking (by expectancy / PnL)

- **1. scenario_004** — expectancy: 2000.00, total_pnl: 18000.00, trades: 9
- **2. scenario_002** — expectancy: 1750.00, total_pnl: 63000.00, trades: 36
- **3. scenario_003** — expectancy: 1750.00, total_pnl: 63000.00, trades: 36

## CSA_REVIEW

- **Why this might be misleading:** Scenario replay uses the same historical logs; ranking reflects in-sample variation only. Best scenario may not hold out-of-sample. Selection bias if logs are incomplete or non-representative.
- **Fragile assumptions:** Entry/exit/session filters are applied ex post; real execution would have different liquidity and slippage. No transaction cost or capacity constraints in replay.

## SRE_REVIEW

- **Data completeness:** Replay fidelity depends on exit_attribution.jsonl / attribution.jsonl being complete for the window. Gaps or partial writes invalidate comparisons.
- **Replay fidelity:** Logic is simplified (score filter, min-hold, session window). Production exit logic and risk checks are not fully replayed.
- **Failure modes:** Missing logs → scenario returns no_data. No broker or ledger writes; rollback is N/A (read-only).
