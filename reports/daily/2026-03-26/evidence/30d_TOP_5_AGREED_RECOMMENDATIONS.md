# 30-Day Board Review — Top 5 Agreed Recommendations

**Data source:** Droplet production (30-day window 2026-02-01 to 2026-03-02). Bundle built and fetched via `python scripts/run_30d_board_review_on_droplet.py`.

**Ingested 30d summary (real data):**
- **Total PnL (attribution):** -$76.53  
- **Total PnL (exit attribution):** -$237.15  
- **Executed trades:** 2,067 | **Exits:** 2,562 | **Win rate:** 16.1%  
- **Avg hold time:** 5.8 minutes (exits are very fast)  
- **Blocked trades:** 2,023 (expectancy_blocked:score_floor_breach: 1,811; max_new_positions_per_cycle: 194; order_validation_failed: 18)  
- **Exit reasons:** ~99.65% signal_decay (various thresholds 0.74–0.93); 2,067 rows tagged "unknown" in attribution.

Each persona contributed 3 ideas; the Board agreed on the following 5.

---

## 1. Fix exit dominance: reduce signal_decay churn and extend minimum hold

| Field | Value |
|--------|--------|
| **Owner** | Exit logic + exit pressure v3 |
| **Metric** | Signal_decay exit rate (target &lt; 85% in 30d window); avg hold minutes (target ≥ 15); 30d PnL (exit attribution) improving. |
| **3/5-day success** | Day 3: Exit effectiveness v2 run on droplet; one parameter change applied (e.g. min_hold_minutes or signal_decay threshold relaxed). Day 5: Next 30d window shows lower signal_decay_exit_rate and higher avg_hold_minutes. |
| **Rationale** | Real data: 99.65% of exits are signal_decay, avg hold 5.8 min. We are exiting far too quickly; relaxing decay or adding a minimum hold should let winners run and reduce round-trip cost. |

---

## 2. Raise score floor or fix expectancy gate to reduce low-edge fills

| Field | Value |
|--------|--------|
| **Owner** | Entry gates (expectancy gate, score_floor_breach) |
| **Metric** | Blocked reason "expectancy_blocked:score_floor_breach" count (1,811 in 30d); win rate of executed trades (target &gt; 25%); 30d attribution PnL. |
| **3/5-day success** | Day 3: Analyze score distribution of executed vs blocked (score_floor_breach); decide whether to raise floor or fix gate logic. Day 5: One config change applied and backtested on 30d cohort. |
| **Rationale** | 1,811 blocks from score_floor_breach but we still have 16% win rate on 2,067 trades—many low-quality entries are getting through. Tighten entry or align gate with expectancy so we take fewer, higher-quality trades. |

---

## 3. Designate trades for replay and run scenario backtests before changing live behavior

| Field | Value |
|--------|--------|
| **Owner** | Backtest / replay pipeline |
| **Metric** | Backtest runs with replay_cohort + scenario_id; comparison of PnL/win rate across scenarios (e.g. baseline vs min_hold_15 vs score_floor_raised). |
| **3/5-day success** | Day 3: replay_cohort and scenario_id in 30d backtest config and backtest_summary.json. Day 5: Two scenarios run on droplet (e.g. current vs extended hold); comparison doc in reports/board/. |
| **Rationale** | With 2,067 trades and -$76.53 attribution (-$237 exit), we must test exit/entry changes on the same cohort before going live; designation enables comparable scenario backtests. |

---

## 4. Run exit effectiveness v2 and tuning weekly; apply recommendations

| Field | Value |
|--------|--------|
| **Owner** | Exit review (run_exit_review_on_droplet.py, suggest_exit_tuning) |
| **Metric** | Weekly run of exit review on droplet; exit_effectiveness_v2.md and exit_tuning_recommendations.md reviewed; at least one parameter change per month when data supports it. |
| **3/5-day success** | Day 3: Exit review run; reports fetched to reports/exit_review/. Day 5: One exit parameter updated from recommendations and documented. |
| **Rationale** | Closing the loop: exits → effectiveness v2 → tuning suggestions → config change. Without weekly review we cannot correct "exiting very quickly" with evidence. |

---

## 5. Close the organism loop: Board consumes 30d bundle and tracks top 5

| Field | Value |
|--------|--------|
| **Owner** | Board / EOD pipeline |
| **Metric** | 30d bundle refreshed from droplet at least weekly; Board runs 3 ideas per persona → agree on top 5; top 5 commitments tracked (1/3/5-day). |
| **3/5-day success** | Day 3: This 30d review and top 5 committed. Day 5: At least one of the five has "done" or "in progress" and next 30d refresh scheduled. |
| **Rationale** | Intelligence → signals → entries → exits → learning → intelligence requires using real 30d data in Board decisions and following through on the agreed five. |

---

## Summary (real data)

| # | Recommendation | Owner |
|---|----------------|--------|
| 1 | Reduce signal_decay churn; extend min hold (evidence: 99.65% signal_decay exits, 5.8 min avg hold) | Exit logic |
| 2 | Raise score floor or fix expectancy gate (evidence: 1,811 score_floor_breach blocks, 16% win rate) | Entry gates |
| 3 | Trade designation + scenario backtests before live changes | Backtest pipeline |
| 4 | Weekly exit effectiveness v2 + tuning; apply recommendations | Exit review |
| 5 | Board consumes 30d bundle; track top 5 commitments | Board / EOD |

All five are actionable and tied to the ingested droplet 30d data.
