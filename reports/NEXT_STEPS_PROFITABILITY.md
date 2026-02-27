# Next Steps — Speed Toward Profitability

**Reality check:** Nothing is fully confirmed until **live data flows during live trading starting Monday.** Backtest and score-vs-profitability are inputs to decisions; live P&L and attribution are the proof.

Below: highest-leverage next steps, ordered by impact vs effort and how they support Monday validation.

---

## 1. Before Monday: Prep for Live Validation (Do These)

| Step | Action | Why |
|------|--------|-----|
| **1.1** | **Confirm live pipeline is emitting what we need** | Monday we need: `attribution` (entry_score, attribution_components if possible), `exit_attribution` (exit_reason, exit_quality_metrics), and orders/trades flowing. Without these, we can’t run effectiveness or blame on live data. |
| **1.2** | **Lock min_exec_score for Monday** | Latest backtest: profitable band (1.5, 2.0], current 1.8 is fine. Don’t change the gate right before Monday unless you have a deliberate override; use 1.8 so we get a clean “live vs backtest” read. |
| **1.3** | **One baseline from live/paper (if you have recent data)** | If droplet has attribution + exit_attribution for a recent window, run effectiveness once so we have a “pre-Monday” baseline to compare to after live runs: `python scripts/analysis/run_effectiveness_reports.py --start YYYY-MM-DD --end YYYY-MM-DD --out-dir reports/effectiveness_pre_monday`. |
| **1.4** | **Define “success” for the first live week** | E.g. “Trades execute; attribution and exit_attribution are written; no crashes; we can run effectiveness on the week’s data by Friday.” Avoid committing to P&L targets until we see volume and quality of live data. |

**Best way to implement 1.1:** Audit the live path: order flow → position open/close → where `attribution` and `exit_attribution` are written (logs/state). Ensure the same schema as backtest where possible (entry_score, context.attribution_components, exit_reason, exit_quality_metrics). Fix or document gaps so Monday isn’t “we have no data to analyze.”

---

## 2. High-Impact Backtest → Live (From ACTIONABLE Framework)

These make backtest results **actionable** and directly support “speed toward profitability” once live data exists.

| Priority | Idea | What to do | Outcome |
|----------|------|------------|---------|
| **P1** | **Emit attribution_components in simulation** | In `run_simulation_backtest_on_droplet.py`, when you have merged/res from `compute_composite_score_v2`, write a component breakdown into each trade’s `context.attribution_components` (list of `{ "signal_id", "contribution_to_score" }`). Match names to what effectiveness expects. | Backtest drives **signal_effectiveness**; we see which signals help/hurt. Same structure can be used for live. |
| **P2** | **Effectiveness on every backtest run** | Already wired: orchestration runs `run_effectiveness_reports.py --backtest-dir .../baseline --out-dir .../effectiveness`. Ensure it doesn’t get skipped on failure; fix any path/import issues so each run gets entry_vs_exit_blame and exit_effectiveness. | Every run produces levers (entry vs exit blame; exit quality). |
| **P3** | **Multi-model sees effectiveness + customer advocate** | In `multi_model_runner.py` (or board prompt), pass paths to effectiveness summary and customer_advocate.md so prosecutor/defender/board can cite “what the numbers say” and “what would help the customer.” | Verdicts grounded in evidence; fewer heuristic-only conclusions. |

**Best way to implement P1:**  
- In the simulation, after computing composite score, call or mimic whatever produces per-signal contributions (e.g. from scoring engine or UW response).  
- Write `context.attribution_components = [ {"signal_id": "flow", "contribution_to_score": 0.4}, ... ]` on each trade.  
- Run one backtest, then run effectiveness and confirm `signal_effectiveness.json` is no longer empty for that run.

---

## 3. Once Live Data Is Flowing (Monday Onward)

| Step | Action | Why |
|------|--------|-----|
| **3.1** | **Daily or weekly effectiveness from live logs** | On droplet, run effectiveness on the live window (e.g. last 7 days): `run_effectiveness_reports.py --start ... --end ... --out-dir reports/effectiveness_live_YYYY-MM-DD`. Compare to backtest and pre-Monday baseline. | Tells us if live entries/exits match backtest quality or if something is different (e.g. fills, timing, missing signals). |
| **3.2** | **Score vs profitability on live trades** | Reuse the same script we use for backtest: point it at live closed trades (with entry_score and pnl_usd). Run weekly: `score_vs_profitability.py --trades <live_trades_path> --out reports/score_analysis_live_YYYY-MM-DD`. | Confirms whether the (1.5, 2.0] band stays profitable in live data or if we need to adjust min_exec_score. |
| **3.3** | **Blocked-trades analysis on droplet** | Wire blocked-trade analysis into the pipeline (e.g. after EOD or weekly): load `state/blocked_trades.jsonl`, run `estimate_blocked_outcome` / opportunity cost, write `reports/blocked_opportunity_cost_YYYY-MM-DD.md`. | Answers “what we could have made” and whether the gate is too tight or too loose. |
| **3.4** | **One small tuning cycle (PATH_TO_PROFITABILITY)** | Use evidence → one change → backtest compare → paper/live. Example: if effectiveness says “exit timing” blame and high giveback, add a small exit-weight overlay; run backtest compare; if OK, enable on paper/live for a week; then lock or revert. | Improves P&L with traceable, reversible changes. |

---

## 4. What “Speed Toward Profitability” Means Here

1. **Before Monday:** Prep so live data is decision-grade (attribution + exit_attribution), min_exec_score is set from backtest (1.8), and we have a clear “first week success” definition (data flowing, effectiveness runnable).  
2. **Implementation focus:** Attribution_components in simulation (P1) and multi-model + effectiveness in the loop (P2, P3) so that backtest and live both feed the same evidence pipeline.  
3. **After Monday:** Use live effectiveness and score-vs-profitability to validate or adjust the gate and to run the governed tuning loop (evidence → one change → compare → live → lock or revert).

**Nothing is fully confirmed until we see live data flowing starting Monday.** These steps maximize the chance that when live runs, we can measure, compare, and tune with the same rigor as in backtest.

---

---

## 5. More Backtests and Signal Tweaks Now?

**Limited additional value.** We already have a solid backtest (10k+ trades, profitable band, min_exec_score 1.8, attribution, effectiveness, score-vs-profitability). Running more backtests and tweaking entry/exit signals *before* Monday risks overfitting to the same snapshot and doesn't tell us how live behaves. **Better:** Execute the pre-Monday plan (audit, lock gate, define success), get **live data** flowing, then use **live + backtest together** for one evidence-based tuning cycle. We **can** get better and get more data by: (1) ensuring we capture live attribution + exit_attribution, (2) running effectiveness on the first live week, (3) doing one small tuning cycle from that evidence.

---

*Aligned with ACTIONABLE_BACKTEST_FRAMEWORK_AND_IDEAS.md, DROPLET_BACKTEST_RUN_SUMMARY.md, and PATH_TO_PROFITABILITY.md.*
