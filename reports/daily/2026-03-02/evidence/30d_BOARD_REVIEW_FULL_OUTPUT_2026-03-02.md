# 30-Day Board Review — Full Output (Droplet Data Ingested)

**Generated:** 2026-03-02  
**Data source:** Droplet production. Bundle built on droplet and fetched via `python scripts/run_30d_board_review_on_droplet.py`.

---

## Part 1 — Ingested 30-day data (from droplet)

**Window:** 2026-02-01 to 2026-03-02 (30 days).

### PnL & activity

| Metric | Value |
|--------|--------|
| Total PnL (attribution) | **-$76.53** |
| Total PnL (exit attribution) | **-$237.15** |
| Executed trades | 2,067 |
| Exits | 2,562 |
| Win rate | **16.1%** |
| Avg hold (minutes) | **5.8** |
| Blocked trades | 2,023 |

### Exit reason distribution (top)

| Exit reason | Count |
|-------------|--------|
| unknown | 2,067 |
| signal_decay(0.92) | 168 |
| signal_decay(0.91) | 130 |
| signal_decay(0.90) | 117 |
| signal_decay(0.89) | 108 |
| signal_decay(0.93) | 107 |
| signal_decay(0.75) | 86 |
| signal_decay(0.76) | 82 |
| signal_decay(0.77) | 73 |
| signal_decay(0.88) | 73 |
| … (further signal_decay thresholds 0.74–0.93) | … |

- **Signal_decay exit rate (30d):** 99.65% (2,553 of 2,562 exits).  
- **Conclusion:** Almost all exits are signal_decay; hold time is very short (5.8 min avg).

### Blocked trade reasons

| Reason | Count |
|--------|--------|
| expectancy_blocked:score_floor_breach | 1,811 |
| max_new_positions_per_cycle | 194 |
| order_validation_failed | 18 |

### Architecture (current, from bundle)

- **Entry:** Composite score (UW + flow + dark pool + gamma + vol + option volume), expectancy gate, capacity/displacement/momentum gates.  
- **Exit:** signal_decay, time stop, trailing stop, regime-based exits; exit pressure v3.  
- **Universe:** Daily universe from UW + survivorship; sector/regime filters.  
- **Execution:** Alpaca paper; cooldowns, concentration limits, max positions per cycle.  
- **Data:** attribution.jsonl, exit_attribution.jsonl, master_trade_log.jsonl, blocked_trades.jsonl; EOD root cause, exit effectiveness v2, governance loop.

---

## Part 2 — Board process

- **Input:** reports/board/30d_comprehensive_review.json, 30d_comprehensive_review.md (droplet-built).  
- **Process:** Each persona (Equity Skeptic, Wheel Advocate, Risk Officer, Promotion Judge, Customer Advocate, Innovation Officer, SRE) produced 3 ideas; Board agreed on top 5.  
- **Output:** reports/board/30d_TOP_5_AGREED_RECOMMENDATIONS.md.

---

## Part 3 — Top 5 agreed recommendations (summary)

| # | Recommendation | Owner | Evidence from 30d data |
|---|----------------|--------|-------------------------|
| 1 | Reduce signal_decay churn; extend minimum hold | Exit logic | 99.65% signal_decay exits, 5.8 min avg hold |
| 2 | Raise score floor or fix expectancy gate | Entry gates | 1,811 score_floor_breach blocks, 16% win rate |
| 3 | Designate trades for replay; run scenario backtests before live changes | Backtest pipeline | 2,067 trades, -$76.53 attribution; need comparable scenarios |
| 4 | Run exit effectiveness v2 and tuning weekly; apply recommendations | Exit review | Close loop: exits → effectiveness → tuning → config |
| 5 | Board consumes 30d bundle; track top 5 commitments | Board / EOD | Weekly refresh; 1/3/5-day commitment tracking |

Full text for each recommendation (owner, metric, 3/5-day success criteria, rationale) is in **reports/board/30d_TOP_5_AGREED_RECOMMENDATIONS.md**.

---

## Part 4 — Artifacts

| Artifact | Path |
|----------|------|
| 30d bundle (JSON) | reports/board/30d_comprehensive_review.json |
| 30d bundle (MD) | reports/board/30d_comprehensive_review.md |
| Board instructions | reports/board/30d_board_instructions.md |
| Top 5 agreed | reports/board/30d_TOP_5_AGREED_RECOMMENDATIONS.md |
| This full output | reports/board/30d_BOARD_REVIEW_FULL_OUTPUT_2026-03-02.md |

To refresh with latest droplet data:  
`python scripts/run_30d_board_review_on_droplet.py`
