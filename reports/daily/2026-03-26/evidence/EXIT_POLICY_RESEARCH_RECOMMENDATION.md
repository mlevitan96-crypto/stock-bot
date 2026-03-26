# Exit Policy Research — Board-Grade Recommendation

**Source:** Exit replay grid run on droplet (2026-02-01 to 2026-03-02). Same 30d cohort as 30d board review.  
**Artifacts:** `reports/exit_research/exit_replay_grid_summary.json`, `exit_replay_ranked_scenarios.json`, `scenarios/<name>/summary.json`.

---

## 1. Baseline (current live exit behavior)

| Metric | Value |
|--------|--------|
| **Window** | 2026-02-01 to 2026-03-02 |
| **Total PnL** | **-$248.54** |
| **Expectancy per trade** | **-0.0928** |
| **Win rate** | 33.2% |
| **Avg hold (minutes)** | 5.6 |
| **Trades** | 2,678 |
| **Tail loss (5th pct)** | -$1.00 |
| **Exit reason distribution** | Dominated by signal_decay (0.74–0.93); ~100% decay-driven exits |

**Per-regime (baseline):**  
- mixed: 1,696 trades, -$120.89, expectancy -0.0713  
- NEUTRAL: 799 trades, -$119.55, expectancy -0.1496  
- unknown: 183 trades, -$8.11, expectancy -0.0443  

---

## 2. Top 2–3 recommended exit policies (from replay)

Scenarios with **zero trades** (component-removal ablations) are **not deployable**—they indicate that under current data, removing those components would have prevented all exits in the window. Recommendations below use only scenarios with **≥ 50 trades** and **numeric evidence**.

### Recommendation 1 — **minhold_5** (primary promote)

| Param | Value |
|--------|--------|
| min_hold_minutes | 5 |
| signal_decay_threshold | 0 (no extra filter) |
| remove_components | [] |

| Metric | Baseline | minhold_5 | Δ vs baseline |
|--------|----------|-----------|----------------|
| Total PnL | -$248.54 | **-$27.00** | +$221.54 (less loss) |
| Expectancy/trade | -0.0928 | **-0.0562** | +0.0366 (better) |
| Win rate | 33.2% | **38.5%** | +5.3 pts |
| Avg hold (min) | 5.6 | **24.5** | +18.9 min |
| Trades | 2,678 | 480 | Cohort: only trades that held ≥ 5 min |

**Per-regime (minhold_5):** mixed 234 trades +$0.87 (positive); NEUTRAL 209 trades -$30.76; unknown 37 trades +$2.89.

**Evidence:** Enforcing a 5-minute minimum hold keeps the same exit logic but excludes very early signal_decay exits. Expectancy improves and total loss drops sharply with a smaller, higher-quality cohort.

---

### Recommendation 2 — **minhold_15** (backup / higher-quality cohort)

| Param | Value |
|--------|--------|
| min_hold_minutes | 15 |
| signal_decay_threshold | 0 |
| remove_components | [] |

| Metric | Baseline | minhold_15 | Δ vs baseline |
|--------|----------|------------|----------------|
| Total PnL | -$248.54 | **-$12.62** | +$235.92 (less loss) |
| Expectancy/trade | -0.0928 | **-0.0631** | +0.0297 (better) |
| Win rate | 33.2% | **41.5%** | +8.3 pts |
| Avg hold (min) | 5.6 | **46.3** | +40.7 min |
| Trades | 2,678 | 200 | Cohort: only trades that held ≥ 15 min |

**Per-regime (minhold_15):** mixed 82 trades +$11.66 (positive); NEUTRAL 102 trades -$26.26; unknown 16 trades +$1.98.

**Evidence:** Stronger win rate and lowest total loss among actionable scenarios; fewer trades (200) so higher variance. Suitable as backup or next step after minhold_5.

---

### Recommendation 3 — **minhold_15_decay_086** (tighter: min hold + higher decay bar)

| Param | Value |
|--------|--------|
| min_hold_minutes | 15 |
| signal_decay_threshold | 0.86 |
| remove_components | [] |

| Metric | Baseline | minhold_15_decay_086 | Δ vs baseline |
|--------|----------|----------------------|----------------|
| Total PnL | -$248.54 | **-$9.87** | +$238.67 (less loss) |
| Expectancy/trade | -0.0928 | -0.1073 | Worse per trade |
| Win rate | 33.2% | **40.2%** | +7.0 pts |
| Avg hold (min) | 5.6 | **47.6** | +42 min |
| Trades | 2,678 | 92 | Small N |

**Evidence:** Smallest total loss and good win rate but only 92 trades; expectancy per trade is worse than baseline. Use as **backup candidate** once more data is available, or for a regime-specific test.

---

## 3. Clear recommendation

1. **Promote scenario minhold_5 to live** for the next **100–200 trades** under governance.  
   - Implement: **minimum hold 5 minutes** before any signal_decay (or pressure) exit.  
   - No change to TP/SL/trail or entry logic in this block.

2. **Keep minhold_15 as backup candidate.**  
   - After 100+ trades on minhold_5, re-run the grid and compare. If minhold_15 continues to show better win rate and lower total loss with sufficient N, consider promoting minhold_15 next.

3. **Do not promote** component-removal scenarios (remove_exit_time_decay, remove_exit_flow_deterioration, etc.)—they produced **0 trades** in this cohort and are not applicable for live deployment without bar-level simulation.

4. **Constraints**  
   - **One exit policy at a time in live.**  
   - **Governance loop** evaluates over **100+ trades** before LOCK/REVERT.  
   - **No live config or overlay changes in this research block**—this document is recommendation only; deployment is a separate governance step.

---

## 4. Per-regime and per-component notes

- **mixed regime:** In minhold_5 and minhold_15, mixed regime is **positive PnL** (+$0.87 and +$11.66). NEUTRAL regime remains negative; consider regime-conditioned min_hold or decay in a future grid.
- **Component ablation:** remove_exit_time_decay, remove_exit_flow_deterioration, remove_exit_score_deterioration all yielded 0 trades—exit pressure in this cohort is dominated by signal_decay; effective score after removing one component still exceeded threshold, so no trades would have “stayed open” in the replay. Full TP/SL/trail simulation would require bar data.

---

## 5. Artifacts

| Artifact | Path |
|----------|------|
| Grid summary (JSON) | reports/exit_research/exit_replay_grid_summary.json |
| Ranked scenarios (JSON) | reports/exit_research/exit_replay_ranked_scenarios.json |
| Grid summary (MD) | reports/exit_research/exit_replay_grid_summary.md |
| Per-scenario summary | reports/exit_research/scenarios/<scenario_name>/summary.json |
| This recommendation | reports/board/EXIT_POLICY_RESEARCH_RECOMMENDATION.md |

To re-run the grid on droplet:  
`python scripts/exit_research/run_exit_replay_grid_on_droplet.py`
