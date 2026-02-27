# Artifact index for followup_diag_20260222T225611Z

Base run: reports/backtests/alpaca_monday_final_20260222T174120Z
Follow-up dir: reports/backtests/followup_diag_20260222T225611Z

| Artifact | Path |
|----------|------|
| Exec sensitivity | reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/exec_sensitivity.json |
| Multi-model | reports/backtests/followup_diag_20260222T225611Z/multi_model/ (board_verdict.md, board_verdict.json) |
| Exit sweep | reports/backtests/followup_diag_20260222T225611Z/exit_sweep/exit_sweep_summary.json |
| Experiments compare | reports/backtests/followup_diag_20260222T225611Z/experiments/compare_summary.md |
| Base attribution | reports/backtests/alpaca_monday_final_20260222T174120Z/attribution/per_signal_pnl.json |
| Base ablation | reports/backtests/alpaca_monday_final_20260222T174120Z/ablation/ablation_summary.json |
| Base metrics | reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/metrics.json |

Tail of /tmp/followup_diag.log (last 50 lines):
Running simulation for slippage 0.0 -> reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0...
[SIMULATION BACKTEST] Done.
  Trades: 10715, Exits: 10715
  P&L: $16623.74, Win rate: 51.47%
  Wrote: reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0/backtest_trades.jsonl, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0/backtest_exits.jsonl, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0/backtest_summary.json, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0/metrics.json, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0/trades.csv
wrote /tmp/exec_sens_cfg_followup_diag_20260222T225611Z_0.0005.json
Running simulation for slippage 0.0005 -> reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0005...
[SIMULATION BACKTEST] Done.
  Trades: 10715, Exits: 10715
  P&L: $16623.74, Win rate: 51.47%
  Wrote: reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0005/backtest_trades.jsonl, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0005/backtest_exits.jsonl, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0005/backtest_summary.json, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0005/metrics.json, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.0005/trades.csv
wrote /tmp/exec_sens_cfg_followup_diag_20260222T225611Z_0.001.json
Running simulation for slippage 0.001 -> reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.001...
[SIMULATION BACKTEST] Done.
  Trades: 10715, Exits: 10715
  P&L: $16623.74, Win rate: 51.47%
  Wrote: reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.001/backtest_trades.jsonl, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.001/backtest_exits.jsonl, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.001/backtest_summary.json, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.001/metrics.json, reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/slippage_0.001/trades.csv
exec_sensitivity summary written to reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/exec_sensitivity.json
Re-running multi_model with --out and evidence...
Multi-model -> reports/backtests/followup_diag_20260222T225611Z/multi_model (prosecutor_output.md, defender_output.md, sre_output.md, board_verdict.json, board_verdict.md)
'reports/backtests/alpaca_monday_final_20260222T174120Z/multi_model/evidence/backtest_summary.json' -> 'reports/backtests/followup_diag_20260222T225611Z/multi_model/evidence/backtest_summary.json'
'reports/backtests/alpaca_monday_final_20260222T174120Z/multi_model/evidence/backtest_trades.jsonl' -> 'reports/backtests/followup_diag_20260222T225611Z/multi_model/evidence/backtest_trades.jsonl'
'reports/backtests/alpaca_monday_final_20260222T174120Z/multi_model/evidence/uw_expanded_intel.json' -> 'reports/backtests/followup_diag_20260222T225611Z/multi_model/evidence/uw_expanded_intel.json'
'reports/backtests/alpaca_monday_final_20260222T174120Z/multi_model/evidence/uw_flow_cache.json' -> 'reports/backtests/followup_diag_20260222T225611Z/multi_model/evidence/uw_flow_cache.json'
Running exit sweep...
Exit optimization (stub) -> reports/backtests/followup_diag_20260222T225611Z/exit_sweep
Running experiment tune_dark_pool_minus25 -> reports/backtests/followup_diag_20260222T225611Z/experiments/tune_dark_pool_minus25 (config merge; simulation uses base config if overlay not supported)...
[SIMULATION BACKTEST] Done.
  Trades: 10715, Exits: 10715
  P&L: $16623.74, Win rate: 51.47%
  Wrote: reports/backtests/followup_diag_20260222T225611Z/experiments/tune_dark_pool_minus25/backtest_trades.jsonl, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_dark_pool_minus25/backtest_exits.jsonl, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_dark_pool_minus25/backtest_summary.json, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_dark_pool_minus25/metrics.json, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_dark_pool_minus25/trades.csv
Wrote /root/stock-bot/reports/backtests/followup_diag_20260222T225611Z/experiments/tune_dark_pool_minus25/summary/summary.md, /root/stock-bot/reports/backtests/followup_diag_20260222T225611Z/experiments/tune_dark_pool_minus25/summary/metrics.json
Running experiment tune_freshness_smooth -> reports/backtests/followup_diag_20260222T225611Z/experiments/tune_freshness_smooth (config merge; simulation uses base config if overlay not supported)...
[SIMULATION BACKTEST] Done.
  Trades: 10715, Exits: 10715
  P&L: $16623.74, Win rate: 51.47%
  Wrote: reports/backtests/followup_diag_20260222T225611Z/experiments/tune_freshness_smooth/backtest_trades.jsonl, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_freshness_smooth/backtest_exits.jsonl, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_freshness_smooth/backtest_summary.json, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_freshness_smooth/metrics.json, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_freshness_smooth/trades.csv
Wrote /root/stock-bot/reports/backtests/followup_diag_20260222T225611Z/experiments/tune_freshness_smooth/summary/summary.md, /root/stock-bot/reports/backtests/followup_diag_20260222T225611Z/experiments/tune_freshness_smooth/summary/metrics.json
Running experiment tune_exit_trail -> reports/backtests/followup_diag_20260222T225611Z/experiments/tune_exit_trail (config merge; simulation uses base config if overlay not supported)...
[SIMULATION BACKTEST] Done.
  Trades: 10715, Exits: 10715
  P&L: $16623.74, Win rate: 51.47%
  Wrote: reports/backtests/followup_diag_20260222T225611Z/experiments/tune_exit_trail/backtest_trades.jsonl, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_exit_trail/backtest_exits.jsonl, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_exit_trail/backtest_summary.json, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_exit_trail/metrics.json, reports/backtests/followup_diag_20260222T225611Z/experiments/tune_exit_trail/trades.csv
Wrote /root/stock-bot/reports/backtests/followup_diag_20260222T225611Z/experiments/tune_exit_trail/summary/summary.md, /root/stock-bot/reports/backtests/followup_diag_20260222T225611Z/experiments/tune_exit_trail/summary/metrics.json
DONE. Key artifacts:
  Exec sensitivity: reports/backtests/followup_diag_20260222T225611Z/exec_sensitivity/exec_sensitivity.json
  Multi-model: reports/backtests/followup_diag_20260222T225611Z/multi_model/
  Exit sweep: reports/backtests/followup_diag_20260222T225611Z/exit_sweep/
  Experiments: reports/backtests/followup_diag_20260222T225611Z/experiments/compare_summary.md
  Index: reports/backtests/followup_diag_20260222T225611Z/ARTIFACT_INDEX.md
