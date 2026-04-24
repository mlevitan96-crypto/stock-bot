# BOARD_QUANT_BLOCKED_WHY_VERDICT

Mandatory questions:

1. **Sample sizes per cluster — sufficient?**  
   - `displacement_blocked` **n=5705** covered — **large**.  
   - `max_new_positions_per_cycle` **n=180** — **small** for fine splits.  
   - Negative-exit cohort **n=195** — **small** for granular exit-reason modeling (`BLOCKED_WHY_DIAGNOSIS.json`).

2. **Stability across splits (day/time/symbol)?**  
   **Not computed** in this bundle — **gap logged:** next test = day-of-week or symbol-decile split on `pnl_60m` for `displacement_blocked` only.

3. **Tail risk — blocked winners hiding fat-tail losers?**  
   **Partially addressed:** `pnl_60m_tail_risk_p05_pnl` per reason in `BLOCKED_GATE_SCORECARD.json` (e.g. `displacement_blocked` p05 **-3.926003** USD at 60m Variant A).

4. **Experiment overfit to this window?**  
   **Offline share metric** (`PAPER_EXPERIMENT_RESULTS.json`) is **descriptive** on one frozen JSON snapshot — **high overfit risk** if interpreted as forward edge.

5. **Minimal next test for generalization?**  
   **One test:** walk-forward 5 trading days — re-fetch bars + recompute only `displacement_blocked` **expectancy** and **p05**; compare to this window’s `BLOCKED_GATE_SCORECARD.json` values.

**STOP:** **not** issued.
