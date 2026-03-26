# Scenario Comparison (Last-387 Baseline)

**Generated (UTC):** 2026-03-04T23:03:34.732755+00:00

## Ranked by expected improvement

1. **A3** — Lower expectancy score floor by one notch → **Test (score floor; backtest recommended)**
2. **B1** — Extend minimum hold by +15 min → **Test (exit behavior; replay validation)**
3. **B2** — Remove early signal_decay exits → **Test (exit behavior; replay validation)**
4. **B3** — Favor TP over time-based exits → **Test (exit behavior; replay validation)**
5. **A1** — Ignore displacement_blocked → **Test (gate relaxation; run in paper first)**
6. **A2** — Ignore max_positions_reached → **Test (gate relaxation; run in paper first)**
7. **C1** — Re-rank block reasons by realized opportunity cost → **Promote (re-rank informs which gate to relax first)**
8. **C2** — Identify blocks that correlate with positive counterfactual PnL → **Test (C2 needs full counter-intel run)**

## Recommendations (Promote / Test / Discard)

- **A1:** Test (gate relaxation; run in paper first)
- **A2:** Test (gate relaxation; run in paper first)
- **A3:** Test (score floor; backtest recommended)
- **B1:** Test (exit behavior; replay validation)
- **B2:** Test (exit behavior; replay validation)
- **B3:** Test (exit behavior; replay validation)
- **C1:** Promote (re-rank informs which gate to relax first)
- **C2:** Test (C2 needs full counter-intel run)

## Risk notes

- **A1:** Displacement relaxation increases exposure; monitor drawdown.
- **A2:** Max positions increase concentration risk.
- **A3:** Lower score floor may admit worse entries; validate with backtest.
- **B1:** Min hold extension may increase drawdown in fast reversals.
- **B2:** Removing early signal_decay may hold losers longer.
- **B3:** TP favor requires rule change; test on replay.
- **C1:** Opportunity cost is proxy; use for prioritization only.
- **C2:** Full C2 requires estimate_blocked_outcome per block.

## Board persona verdicts (which scenario to test first)

### Adversarial

Test A3 first (lower score floor): if the blocked score band is profitable, we are over-blocking; if not, we keep the floor. No live change until backtest.

### Quant

Test C1 first: re-ranking by opportunity cost gives a clear order for which gate to relax; then validate with A1/A2/A3 tests.

### Product Operator

Test B2 first (remove early signal_decay): quickest exit-policy change to validate on replay; if early decay exits are net negative, removing them improves expectancy.

### Risk

Test A2 last; prioritize B1 or B3 (exit behavior) over gate relaxation to avoid concentration. Promote C1 for decision order.

### Execution Sre

Test B1 first (extend min hold): single parameter, easy rollback; then C1 for prioritization. No live config change until tests pass.
