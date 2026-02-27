# Path to Profitability — Using the New Stack

You now have **full observability** (Phases 0–5) and **governed tuning** (Phase 6). This doc is the bridge: **how to use it to get better and closer to profitability.**

---

## The loop you can run

```
Evidence (Phase 5) → Hypothesis → Change proposal → Backtest compare → Paper/Canary → Lock or Revert
         ↑                                                                                    |
         └─────────────────────────── same metrics, next period ───────────────────────────┘
```

**Every change is:** traceable to evidence, config-only (reversible), and measured before/after.

---

## Step 1: Generate evidence (Phase 5)

You need **one baseline** of decision-grade metrics before changing anything.

**From live/paper logs (attribution + exit_attribution):**
```bash
python scripts/analysis/run_effectiveness_reports.py --start 2026-02-01 --end 2026-02-17 --out-dir reports/effectiveness_baseline
```

**From a backtest run:**
```bash
python scripts/analysis/run_effectiveness_reports.py --backtest-dir backtests/30d_YYYYMMDD_HHMMSS --out-dir reports/effectiveness_baseline
```

**Output:** `signal_effectiveness.json`, `exit_effectiveness.json`, `entry_vs_exit_blame.json`, `counterfactual_exit.json`, plus CSV and `EFFECTIVENESS_SUMMARY.md`.

---

## Step 2: Read the reports — where to look for profit

Use the reports to decide **what to change first**. Priority order:

| Priority | Report | What to look for | Tunable lever |
|----------|--------|-------------------|---------------|
| **1** | **entry_vs_exit_blame** | If most losers are **weak entry** → raise entry bar (threshold) or down-weight bad signals. If most are **exit timing** (high giveback, had MFE) → tune **exit** weights (e.g. flow_deterioration, score_deterioration). | `entry_thresholds`, `entry_weights_v3`, `exit_weights` |
| **2** | **signal_effectiveness** | Signals with **low win_rate**, **high avg_MAE**, **high avg_profit_giveback** → reduce weight or require stronger confirmation. Signals with **high win_rate**, good MFE/MAE → consider boosting (carefully). | `entry_weights_v3` in tuning overlay |
| **3** | **exit_effectiveness** | Exit reasons with **high avg_profit_giveback** or **low % left_money** → those exits are leaving money on the table; increase the corresponding exit weight so we exit earlier. Reasons that **save loss** well → keep or slightly reduce weight. | `exit_weights` in tuning overlay |
| **4** | **counterfactual_exit** | **hold_longer_would_help** → we’re exiting too early on winners. **exit_earlier_would_save** → we’re holding losers too long. | Exit weights, time_exit, trail/stop logic (future overlays) |

**Rule of thumb:** Fix **entry** if blame says “we’re picking bad trades.” Fix **exit** if blame says “we’re closing good trades too early or bad trades too late.”

---

## Step 3: Propose one small change (Phase 6)

1. Copy `docs/templates/change_proposal.md` to e.g. `reports/change_proposals/your_change_YYYYMMDD.md`.
2. Fill: **What** (exact config diff), **Why** (which report + metric), **Expected impact**, **Falsification criteria**, **Rollback**.
3. Add a **tuning overlay** (e.g. `config/tuning/active.json` or a file in `config/tuning/examples/`) with that single change. See `config/tuning/schema.json` for allowed fields.

**Example:** “entry_vs_exit_blame says 60% of losers are exit timing; exit_effectiveness says profit exits have high giveback” → increase `exit_weights.flow_deterioration` by 0.02 (example overlay: `config/tuning/examples/exit_flow_weight_plus_0.02.json`).

---

## Step 4: Backtest compare + regression guards

1. Run **baseline** backtest (no overlay or current production config).
2. Run **proposed** backtest with your overlay (e.g. `GOVERNED_TUNING_CONFIG=config/tuning/examples/your_overlay.json`).
3. Compare:

```bash
python scripts/governance/compare_backtest_runs.py --baseline backtests/30d_baseline --proposed backtests/30d_proposed --out reports/governance_comparison
```

4. Run guards:

```bash
python scripts/governance/regression_guards.py
```

**Decision:** If comparison shows improvement (or no material regression) on PnL, win rate, giveback, and blame mix — and guards pass — move to paper/canary. If not, revert the overlay and iterate with a different hypothesis.

---

## Step 5: Paper / canary with the same metrics

- Run paper (or limited canary) with the **proposed** config.
- Keep collecting **attribution** and **exit_attribution** as you do now.
- After a set period (e.g. 7–14 days), run **Phase 5 again** on that period and **compare** to baseline (same comparison script if you export effectiveness dirs).
- If **falsification criteria** from your proposal are hit (e.g. win rate drops >2%, giveback worsens), **revert** the overlay. Otherwise, **lock** the change (e.g. promote overlay to active, or document as new baseline).

---

## What “getting closer to profitability” means in practice

1. **Fewer bad entries**  
   Use `entry_vs_exit_blame` + `signal_effectiveness` to raise the bar or down-weight weak signals → **higher win rate**, **smaller drawdowns**.

2. **Better exits**  
   Use `exit_effectiveness` + blame to exit **winners** with less giveback and **losers** sooner → **higher avg_pnl per trade**, **less “left money on the table.”**

3. **No silent regressions**  
   Every change is in config, compared in backtest, guarded by invariants, and re-measured in paper → **improvements are real**, and you can revert if they’re not.

---

## Suggested first 2–3 cycles

| Cycle | Focus | Evidence to generate | Likely lever |
|-------|--------|----------------------|---------------|
| 1 | Establish baseline | Run effectiveness on last 30d (logs or backtest); read blame + exit_effectiveness | None yet — just document numbers |
| 2 | Exit quality | If blame says “exit timing” and exit_effectiveness shows high giveback on profit → small increase in 1 exit weight | `exit_weights` overlay |
| 3 | Entry quality | If blame says “weak entry” and signal_effectiveness shows 1–2 signals with bad win_rate → reduce their weight or raise threshold | `entry_weights_v3` or `entry_thresholds` overlay |

After that, repeat: new effectiveness report → new hypothesis → one change → compare → paper → lock or revert. The stack is built so you **use** the reports to **drive** governed, reversible changes and only keep what improves the numbers.

---

## Droplet: run profitability on the latest backtest

After a 30d backtest completes on the droplet, the **profitability pipeline** (effectiveness + baseline + recommendation) runs automatically if the script includes step 4.6 (see `board/eod/run_30d_backtest_on_droplet.sh`). If you need to run it on an **existing** backtest dir (e.g. one that was created before the pipeline was added), SSH to the droplet and run:

```bash
cd /root/stock-bot   # or stock-bot-current
bash board/eod/run_profitability_on_backtest_dir.sh backtests/30d_after_signal_engine_block3g_YYYYMMDD_HHMMSS
```

Replace with the actual backtest dir name (e.g. `30d_after_signal_engine_block3g_20260218_002100`). This writes:

- `$DIR/effectiveness/` — signal_effectiveness.json, exit_effectiveness.json, entry_vs_exit_blame.json, counterfactual_exit.json
- `$DIR/profitability_baseline.json` — aggregates and recommendation
- `$DIR/profitability_recommendation.md` — next steps and suggested overlay

Then use the recommendation to add a tuning overlay and (on the next backtest or in paper) compare.
