# MEMORY_BANK.md — Alpaca SPI update summary (`20260328_190000Z`)

**File:** `MEMORY_BANK.md`  
**Section:** Under `### Alpaca quantified governance (experiment pipeline)`, after **Alpaca Data Sources**, added:

#### Alpaca Signal Path Intelligence (SPI)

Documented:

- Purpose (post-trade path distributions on executed strict/session cohorts).
- Constraints (no strategy/execution/exit/signal changes; default cache-only bars).
- Metric definitions (time-to-threshold, MAE/MFE, MAE before +1%, vol ratio, archetypes).
- Signal bucketing from exit attribution fields.
- **Invariant:** SPI does not authorize behavior change.
- Implementation map: `src/analytics/alpaca_signal_path_intelligence.py`, `scripts/audit/alpaca_pnl_massive_final_review.py`, `data/bars_loader.py`, strict gate / truth runner references.

No shadow docs; single source of truth remains `MEMORY_BANK.md`.
