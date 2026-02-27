# Action Plan Execution + Backtest Value

## 1. More Backtests and Signal Tweaks Now?

**Limited additional value.** We already have: 10k+ trades, profitable band (1.5, 2.0], min_exec_score 1.8, attribution, effectiveness, score-vs-profitability, multi-model. More backtests on the same/similar snapshot risk overfitting; they don't tell us how live behaves (fills, latency, real gate). **Better move:** Execute pre-Monday plan, get live data, then use live + backtest together for one evidence-based tuning cycle.

## 2. Get Better and Get More Data

**More data:** Live pipeline audit so we capture attribution + exit_attribution; run live one week; run effectiveness on that week. **Get better:** After live effectiveness, one small tuning cycle (one overlay, backtest compare, guards, paper, lock or revert). More backtest-only tuning before live is not validated until live confirms.

## 3. Action Plan Status

| Step | What | Status |
|------|------|--------|
| 1 | Live pipeline audit | Audit doc created from codebase trace. |
| 2 | Multi-model + effectiveness/customer advocate | Done in multi_model_runner.py. |
| 3 | Lock min_exec_score 1.8 | backtest_config.json set to 1.8; orchestration uses 1.8; live source in audit. |
| 4 | First live week + effectiveness | Define success; run effectiveness when week of data exists. |
| 5 | One tuning cycle | After first live week: evidence → overlay → compare → paper. |
| 6 | Blocked report on droplet | Run run_blocked_trade_analysis.py weekly. |
