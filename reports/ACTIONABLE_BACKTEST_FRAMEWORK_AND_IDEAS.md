# Actionable Backtest Framework & Top Ideas (Work Backwards from Profit)

**Date:** 2026-02-22  
**Goal:** Turn backtest runs into **actionable** changes (entry/exit/timing/size, signals, long vs short) so the bot makes money.  
**Perspectives:** Multi-model (prosecutor/defender/SRE/board), customer advocate (profit), blocked-trades angle, all angles checked.

---

## 1. Work-Backwards Framework

**Target:** Decisions that move P&L and win rate in the right direction.

```
Actionable result (e.g. "boost signal X in regime Y")
    ← Evidence (effectiveness reports, blame, counterfactuals)
        ← Joined trades with entry + exit + components
            ← Backtest (or live) must EMIT: direction, attribution_components, exit_reason, quality_metrics
```

**Current reality:**

- **Backtest simulation** produces: `entry_score`, `entry_price`, `pnl_usd`, `hold_minutes`, `exit_reason: "hold_bars"` only. It does **not** emit:
  - **Direction** (long/short) — simulation is long-only by construction; no bearish path.
  - **Attribution components** (per-signal contribution to score) — so effectiveness reports see **no** per-signal breakdown from backtest.
  - **Exit diversity** — every exit is `hold_bars`; no flow_deterioration, score_deterioration, stop, target, etc.
- **Effectiveness pipeline** exists and is designed for action: `signal_effectiveness`, `exit_effectiveness`, `entry_vs_exit_blame`, `counterfactual_exit`. It expects `entry_attribution_components` and exit_quality_metrics; backtest doesn’t provide them.
- **Governed tuning** path exists: change proposal → tuning overlay → backtest compare → paper/canary (see `docs/PATH_TO_PROFITABILITY.md`, `docs/GOVERNED_TUNING_WORKFLOW.md`). It is underused because **backtest output is not yet decision-grade**.

So: we are not “not getting results” because the framework is missing; we are not getting **actionable** results because **the backtest (and/or live) does not yet emit the fields the framework needs**.

---

## 2. What We’re Seeing (Gaps vs. Desired)

| Need | For action | Current backtest | Gap |
|------|------------|------------------|-----|
| Which signals help/hurt | Signal effectiveness → weight up/down | No `attribution_components` on trades | Simulation doesn’t write component breakdown |
| Entry vs exit blame | Fix entry vs fix exit | Single exit reason; no MFE/MAE/giveback | No exit_quality_metrics in simulation |
| Long vs short | When to short vs long | Long-only (pnl = (exit−entry)/entry) | No direction; no short leg in sim |
| Blocked-trade value | “What we could have made” | Blocked logs on droplet/live; not in backtest | Counterfactual/opportunity cost not wired to backtest run |
| Timing / size | Hold period, position size | Fixed hold_bars; no size in sim | Param sweep varies params but sim doesn’t emit size/timing attribution |

**Existing assets (use them):**

- **Effectiveness reports:** `scripts/analysis/run_effectiveness_reports.py` (supports `--backtest-dir`); `attribution_loader.load_from_backtest_dir` joins trades + exits. It will give empty signal breakdown until backtest writes `context.attribution_components`.
- **Blocked-trade analysis:** `counter_intelligence_analysis.estimate_blocked_outcome`, `counterfactual_analyzer.analyze_blocked_trades`, `friday_eow_audit.analyze_opportunity_cost`, `generate_comprehensive_trading_review` (counter-intelligence on blocked). These use `state/blocked_trades.jsonl` and similar; run on droplet/live data.
- **Direction:** `DirectionalConvictionEngine` (adaptive_signal_optimizer) produces LONG/SHORT from net_conviction; not used in simulation.
- **Governed tuning:** Change proposals, overlays, backtest compare, regression guards are documented and partially implemented.

---

## 3. Top 5–10 Vetted Ideas (Prioritized)

**Vetting:** Aligned with “work backwards from profit,” existing code paths, and customer outcome (make money). Adversarial note: each idea can be challenged (e.g. “more complexity / more to break”); the list is ordered by impact vs effort and traceability.

1. **Emit attribution_components from simulation (high impact, medium effort)**  
   - In `run_simulation_backtest_on_droplet.py`, when we have `merged` (and optionally `res` from `compute_composite_score_v2`), write a **component breakdown** (e.g. flow, trend_signal, momentum_signal, regime_signal, etc.) into each trade’s `context.attribution_components` (list of `{ "signal_id": name, "contribution_to_score": value }`).  
   - **Why:** Unlocks signal_effectiveness from backtest. One run then tells you which signals appear in winners vs losers.  
   - **Adversarial:** Need to ensure component names match what effectiveness and tuning expect (e.g. schema in `config/tuning`).

2. **Run effectiveness reports on every backtest run and publish in run dir**  
   - After baseline simulation (and optionally param_sweep/exits), run `run_effectiveness_reports.py --backtest-dir reports/backtests/<RUN_ID>/baseline --out-dir reports/backtests/<RUN_ID>/effectiveness`.  
   - **Why:** Makes “what to tune” visible next to each run; supports governed tuning and multi-model review.  
   - **Adversarial:** Until idea 1 is done, signal_effectiveness will be sparse; exit_effectiveness and entry_vs_exit_blame can still add value once we have more exit reasons.

3. **Add direction (long/short) to simulation and backtest output**  
   - Use existing conviction/direction logic (e.g. from bar-based signals or UW): if “bearish”/negative conviction, treat trade as short: `pnl_pct = (entry_price - exit_price) / entry_price * 100`.  
   - Emit `direction` (long/short) and, if available, `side` on each trade and exit.  
   - **Why:** “How we know when to short or long” becomes measurable; long/short effectiveness and regime breakdown become possible.  
   - **Adversarial:** Requires a clear, reproducible rule for direction (e.g. sign of composite, or DirectionalConvictionEngine output); document it in provenance.

4. **Wire blocked-trades analysis into the pipeline (droplet + optional backtest)**  
   - On droplet: after orchestration (or in a scheduled job), run `counter_intelligence_analysis` / `analyze_opportunity_cost` (or a thin script that calls them) on `state/blocked_trades.jsonl` and executed trades; write summary to e.g. `reports/backtests/<RUN_ID>/blocked_analysis.json` and a short `blocked_opportunity_cost.md`.  
   - **Why:** Directly addresses “what we could have made” and whether we’re too conservative or too aggressive.  
   - **Adversarial:** Blocked trades are live/paper; backtest doesn’t “block” the same way. So this is “all angles” for live, not a substitute for backtest signal/exit tuning.

5. **One “customer advocate” report per run**  
   - Add a small step (script or section in summary): “Customer advocate” view: (a) net P&L and win rate in plain language; (b) “What would help the customer make money next?” (e.g. “Reduce losers from weak entries” vs “Improve exit timing on winners” from entry_vs_exit_blame); (c) top 2–3 concrete levers (e.g. “Raise min_exec_score”, “Increase exit weight for flow_deterioration”).  
   - **Why:** Forces a profit-oriented, simple narrative and next steps.  
   - **Adversarial:** Can be subjective; keep it short and tied to metrics so prosecutor can challenge.

6. **Diverse exit reasons in simulation**  
   - In simulation, besides fixed `hold_bars`, add at least one or two exit paths: e.g. “stop” (price move against), “target” (profit cap), or “score_drop” (simplified score deterioration). Emit `exit_reason` and, if feasible, simple exit_quality_metrics (e.g. mfe_pct, mae_pct).  
   - **Why:** Exit effectiveness and counterfactual_exit become meaningful; we can see which exit reasons save loss vs leave money.  
   - **Adversarial:** More logic and parameters; start with one extra reason and document assumptions.

7. **Param sweep → “best” config as a single-line recommendation**  
   - After param_sweep, compare net_pnl (and optionally win rate / drawdown) across configs; write `reports/backtests/<RUN_ID>/param_sweep/best_config.json` and one sentence in summary: “Best param set in this run: …”.  
   - **Why:** Directly actionable “try this config next” for paper or canary.  
   - **Adversarial:** Overfitting to one backtest; label as “suggested” and require out-of-sample or paper validation.

8. **Multi-model verdict must reference effectiveness and customer summary**  
   - When generating board_verdict and SRE/prosecutor/defender outputs, include (or link) the effectiveness summary and the customer-advocate one-liner when present.  
   - **Why:** Adversarial view and board verdict stay grounded in “what the numbers say” and “what would help the customer.”  
   - **Adversarial:** Keeps multi-model from being purely heuristic.

9. **Regime-aware signal breakdown in effectiveness**  
   - Effectiveness already supports regime/hour breakdown where data exists. Ensure backtest (and live) emit `entry_regime` (and optionally hour) so that “signal X in regime Y” is visible.  
   - **Why:** Enables “increase/decrease signals by regime” and avoids applying one fix everywhere.  
   - **Adversarial:** Regime must be defined and reproducible (e.g. from bars or UW); document in provenance.

10. **Scheduled “blocked + executed” opportunity-cost report on droplet**  
    - Weekly or post-EOD: run blocked-trade analysis + opportunity cost; commit a short report (e.g. `reports/blocked_opportunity_cost_YYYY-MM-DD.md`) and push so it’s visible in the repo.  
    - **Why:** Recurring view of “what we could have made” and whether gates are too tight or too loose.  
    - **Adversarial:** Depends on blocked_trades.jsonl being populated; ensure logging is on and retention is defined.

---

## 4. Blocked Trades: “What We Could Have Made”

- **Existing:**  
  - `counter_intelligence_analysis.estimate_blocked_outcome(blocked_signal, executed_trades)` estimates win rate and avg PnL for a blocked signal using similar executed trades (same symbol, similar score).  
  - `friday_eow_audit.analyze_opportunity_cost(blocked_trades, executed_trades)` highlights high-score blocked count vs executed PnL; notes that full opportunity cost needs counterfactual price simulation.  
  - `counterfactual_analyzer.analyze_blocked_trades()` groups by reason and score; no PnL simulation yet.  
  - `generate_comprehensive_trading_review` runs “counter-intelligence” (estimate_blocked_outcome) on a sample of blocked and classifies missed_opportunities vs valid_blocks vs uncertain.

- **Gap:**  
  - No single pipeline that: loads latest `state/blocked_trades.jsonl` (and UW blocked if any), runs estimate_blocked_outcome + opportunity_cost, and writes a standard report under `reports/backtests/<RUN_ID>/` or a dedicated `reports/blocked_opportunity_cost/`.  
  - Backtest runs don’t produce “blocked” trades; blocked analysis is a **live/paper** angle.

- **Recommendation:**  
  - Implement **idea 4** (wire blocked analysis into pipeline on droplet) and **idea 10** (scheduled opportunity-cost report).  
  - Optionally: in backtest, we could simulate “would-have-been-blocked” by applying a stricter gate and comparing PnL of those bars to “executed” — that would be a separate, smaller project.

---

## 5. Customer Advocate (Profit Perspective)

- **Intent:** Every run should answer: “Is this helping the customer make money? What should we do next?”

- **Concrete:**  
  - **One report/section:** “Customer advocate” with (1) net P&L and win rate; (2) one-sentence verdict (e.g. “Run is not yet profitable; main lever: improve entry quality”); (3) top 2–3 levers from evidence (entry threshold, exit weights, or “run blocked-trade analysis”).  
  - **Source of truth for levers:** entry_vs_exit_blame, signal_effectiveness, exit_effectiveness, and (when available) blocked_opportunity_cost.  
  - **Multi-model:** Board verdict and prosecutor/defender should be able to cite this so the “customer make money” angle is explicit and challengeable.

- **Ideas that serve this:** 5 (customer advocate report), 8 (verdict references effectiveness + customer summary), 1–2 (evidence for levers), 4 and 10 (blocked “what we could have made”).

---

## 6. Multi-Model & Adversarial Use

- **Current:** Prosecutor/defender/SRE/board run on metrics (trades_count, net_pnl, win_rate). They don’t yet see effectiveness summaries or customer-advocate text.

- **Improvement:**  
  - Feed multi-model with: (a) baseline metrics, (b) path to effectiveness summary (or key stats), (c) path to customer-advocate summary.  
  - Prosecutor can argue: “Signal effectiveness is empty; we can’t trust any signal lever.”  
  - Defender can argue: “Once we emit components (idea 1), we can tune; run is reproducible.”  
  - Board verdict: “Accept run for reproducibility; require idea 1 and 2 before promoting any weight change.”

- **Adversarial discipline:** Every “actionable” idea should have a falsification criterion (e.g. “If signal_effectiveness is still empty after emitting components, revert and fix schema”).

---

## 7. Plugins / Marketplace

- You mentioned enabling plugins through the marketplace. In the repo we have references to **compound-engineering-context** (MCP) for documentation/code lookup.  
- **Use for this work:** When implementing ideas (e.g. adding attribution_components, or exit reasons), use the plugin to pull current schemas (`config/tuning/schema.json`), attribution contract, or Phase 5 docs so that emitted fields match what effectiveness and governance expect.  
- No plugin was identified that “runs” the backtest or the effectiveness reports; those remain our scripts. Plugins are best used to keep implementation consistent with existing contracts and docs.

---

## 8. Summary: What to Do Next

| Priority | Action | Outcome |
|----------|--------|---------|
| 1 | Implement **idea 1** (emit attribution_components in simulation) | Backtest drives signal_effectiveness and signal-level tuning. |
| 2 | Implement **idea 2** (run effectiveness on every backtest run) | Each run produces entry_vs_exit_blame and exit_effectiveness; baseline for governed tuning. |
| 3 | Implement **idea 5** (customer advocate report per run) | Clear “what would help the customer make money” and next levers. |
| 4 | Implement **idea 4** (blocked-trades analysis in pipeline on droplet) | “What we could have made” and gate sanity check. |
| 5 | Add **direction** to simulation (**idea 3**) | Long/short visibility and future short-side tuning. |
| 6 | Multi-model reads effectiveness + customer summary (**idea 8**) | Verdicts grounded in evidence and profit lens. |
| 7 | Optional: diverse exits in sim (**idea 6**), param_sweep best-config output (**idea 7**), scheduled blocked report (**idea 10**) | Richer exits, one-line config suggestion, recurring blocked view. |

---

*Generated for actionable backtest results; vetted with multi-model and customer-advocate perspective; aligned with PATH_TO_PROFITABILITY and GOVERNED_TUNING_WORKFLOW.*
