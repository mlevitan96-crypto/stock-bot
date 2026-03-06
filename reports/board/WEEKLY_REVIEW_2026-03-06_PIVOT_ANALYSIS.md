# Weekly Review — Pivot Analysis (Stocks vs Options/Wheel)

**Date:** 2026-03-06

Evidence-based answers; no hand-waving. Tie claims to weekly evidence and known constraints.

---

## 1. Is the current stock signal→trade pipeline structurally capable of profitability?

**Answer:** Conditional.

- **Evidence:** Weekly ledger shows executed vs blocked vs CI-blocked; CSA verdict and board review inform edge (exit reasons, hold-time, signal quality). Profitability requires: (1) positive expectancy in the cohort we trade, (2) execution that does not leak edge, (3) exits that capture more than they give back, (4) sizing and constraints that do not over-concentrate or over-block.
- **Constraint:** We do not yet have a single "do-nothing" or buy-hold baseline in the board comparison; opportunity cost of blocked trades (when shadow would have profited) is not yet measured. Until those exist, "structurally capable" is not proven.

---

## 2. What is the bottleneck: signal edge, execution, exits, sizing, regime, universe, or constraints?

**Answer:** To be filled from weekly evidence.

- **Signal edge:** If win rate or expectancy in last387/30d is weak, signal is the bottleneck.
- **Execution:** If validation_failed rate is high or fill quality is poor, execution is a bottleneck.
- **Exits:** If early exits or decay/stop behavior lose more than they save, exits are the bottleneck.
- **Sizing:** If max_positions or displacement blocks dominate blocked reasons, sizing/constraints are the bottleneck.
- **Regime/Universe:** If edge exists only in certain regimes or names, regime/universe filtering is the bottleneck.

**Action:** Use top_blocked_reasons and top_ci_reasons from the weekly ledger summary; CSA value_leaks and required_next_experiments; and board review exit/blocked distributions to assign the primary bottleneck. Update this section when the weekly run is executed with real data.

---

## 3. Would options/wheel improve edge capture or just add complexity?

**Answer:** Options/wheel can improve edge capture only if:

- The stock edge is real but under-captured (e.g. we exit too early; options allow holding for theta or defined risk).
- Theta or volatility edge is additive after stock edge is proven.

Otherwise, options/wheel add complexity (assignment, liquidity, margin, monitoring) without addressing the primary bottleneck (e.g. signal or exits). **Recommendation:** Do not add options until (1) stock pipeline shows clear positive expectancy in a controlled cohort, and (2) a documented options MVP (e.g. one-name wheel 30d paper) is designed with success criteria.

---

## 4. What prerequisites must be true before options/wheel is rational?

- **Liquidity:** Liquid options chain for chosen names; spread and open interest acceptable.
- **Assignment handling:** Process and system for assignment; no unmanaged risk.
- **Risk controls:** Position limits, margin monitoring, and kill switch for options.
- **Monitoring:** Dashboard and alerts for options positions and Greeks.
- **Evidence:** At least one paper-trade or backtest showing options/wheel improves risk-adjusted outcome vs stock-only for the same cohort.

---

## 5. Recommendation: stay course vs hybrid vs pivot — 30/60/90 plan

| Recommendation | Condition | 30d | 60d | 90d |
|----------------|-----------|-----|-----|-----|
| **Stay course (stocks)** | Bottleneck is signal, exits, or sizing; fix in pipeline first | Close required_next_experiments; add 14d/30d ledger sanity checks | Shadow/board stability; opportunity-cost proxy | Real-money readiness checklist or explicit defer |
| **Hybrid** | Stock edge proven; options only for hedging or theta on same names | Design options MVP (one name, paper); document prerequisites | Run options MVP 30d; compare to stock-only | Expand only if MVP meets success criteria |
| **Pivot** | Structural inability of stock pipeline (e.g. no edge in any cohort) | Document; run pivot analysis with full evidence | Pilot alternative (e.g. wheel on 1 name) with strict gates | Full pivot only if pilot succeeds and stock path is formally deprecated |

**Default this week:** **Stay course.** No change to trading logic. Use weekly packet to prioritize experiments and instrumentation (opportunity cost, baselines). Revisit pivot after bottleneck is identified and at least one full experiment cycle is completed.

---

*Generated for weekly board audit. Update bottleneck section after running weekly evidence and ledger.*
