# PROFIT_V2_ACTION_PLAN

Machine-readable twin: `PROFIT_V2_ACTION_PLAN.json`.

## Evidence anchors

- Direction: `ALPACA_DIRECTIONAL_PNL_ANALYSIS.md` — LONG **sum_pnl ≈ 28.85** (n=280) vs SHORT **≈ -17.45** (n=152).  
- Exit horizons: `PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS.md` — mean (horizon − realized) slightly negative at +1m…+30m, **+0.15 USD** at +60m (n=432).  
- Signal ranking: `ALPACA_SIGNAL_RANKING.json` — `flow` median-split shows **negative** delta mean on matched n=63 (exploratory).  
- Blocks: `PROFIT_V2_BLOCKED_MISSED_CAUSAL.json` — top reason **`displacement_blocked`** (5719 in tail sample).

## Ranked actions (summary)

1. **Direction (shadow):** test SHORT gate/size cap vs LONG-first bias — **verification** shadow ledger; **rollback** flag off.  
2. **Exit timing (shadow/research):** use horizon replay to pick **one** scenario for paper — **rollback** discard JSON.  
3. **UW / signal pruning (shadow):** component ablation on low-ranked signals — **rollback** git restore weights.  
4. **Gate lab (read-only):** blocked trades × bars at block timestamp — **rollback** N/A.  
5. **Telemetry:** restore `signal_context` rows or hard-link snapshot ids — **rollback** `ALPACA_SIGNAL_CONTEXT_EMIT=0`.

No production tuning is executed in this mission.
