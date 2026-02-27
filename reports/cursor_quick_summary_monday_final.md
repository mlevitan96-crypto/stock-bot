Checking FINAL_VERDICT...
FINAL_VERDICT: BACKTEST_RUN_OK
Collecting key artifacts list...
total 104
drwxr-xr-x 15 root root 4096 Feb 22 18:03 .
drwxr-xr-x 24 root root 4096 Feb 22 17:41 ..
-rw-r--r--  1 root root   71 Feb 22 18:03 ERROR.txt
-rw-r--r--  1 root root   31 Feb 22 18:03 FINAL_VERDICT.txt
-rw-r--r--  1 root root  471 Feb 22 18:03 NEXT_STEPS.md
drwxr-xr-x  2 root root 4096 Feb 22 17:53 ablation
drwxr-xr-x  2 root root 4096 Feb 22 18:03 adversarial
drwxr-xr-x  2 root root 4096 Feb 22 17:53 attribution
drwxr-xr-x  2 root root 4096 Feb 22 17:53 baseline
drwxr-xr-x  2 root root 4096 Feb 22 18:03 blocked_analysis
-rw-r--r--  1 root root  243 Feb 22 17:41 bootstrap_stdout.log
-rw-r--r--  1 root root  159 Feb 22 17:41 config.json
-rw-r--r--  1 root root  129 Feb 22 17:53 customer_advocate.md
-rw-r--r--  1 root root   58 Feb 22 17:41 data_snapshot.txt
drwxr-xr-x  2 root root 4096 Feb 22 17:53 effectiveness
drwxr-xr-x  2 root root 4096 Feb 22 17:53 event_studies
drwxr-xr-x  3 root root 4096 Feb 22 17:53 exec_sensitivity
drwxr-xr-x  2 root root 4096 Feb 22 18:03 exit_sweep
drwxr-xr-x  3 root root 4096 Feb 22 18:03 multi_model
drwxr-xr-x  2 root root 4096 Feb 22 18:03 param_sweep
drwxr-xr-x  2 root root 4096 Feb 22 17:41 patches
-rw-r--r--  1 root root 1350 Feb 22 17:41 preflight.txt
-rw-r--r--  1 root root    2 Feb 22 17:41 preflight_ok
-rw-r--r--  1 root root  350 Feb 22 17:41 provenance.json
-rw-r--r--  1 root root   44 Feb 22 17:41 run_meta.txt
drwxr-xr-x  2 root root 4096 Feb 22 18:03 summary
drwxr-xr-x  2 root root  4096 Feb 22 18:03 alpaca_monday_final_20260222T174120Z

# Quick Cursor Summary for alpaca_monday_final_20260222T174120Z

Baseline metrics:
{
  "net_pnl": 18811.44,
  "trades_count": 10715,
  "win_rate_pct": 51.18,
  "gate_p10": null,
  "gate_p50": null,
  "gate_p90": null
}

Schema smoke test (sample up to 200 trades):
sample_count 200
missing_fields_sample []

Top per-signal contributors (top 10) if available:
{
  "flow": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "dark_pool": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "insider": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "iv_skew": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "smile": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "whale": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "event": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "motif_bonus": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "toxicity_penalty": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "regime": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "congress": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "shorts_squeeze": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "institutional": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "market_tide": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "calendar": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "greeks_gamma": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "ftd_pressure": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "iv_rank": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "oi_change": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "etf_flow": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "squeeze_score": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  },
  "freshness_factor": {
    "trade_count": 10715,
    "total_pnl_usd": 18811.44,
    "win_rate_pct": 51.18,
    "avg_pnl_usd": 1.76,
    "wins": 5484,
    "losses": 5123
  }
}
Ablation fragility check (top flips) if available:
[
  {
    "signal_id": "calendar",
    "zero": {
      "trades_dropped": 0,
      "pnl_dropped_usd": 0.0
    },
    "invert": {
      "trades_dropped": 0,
      "pnl_dropped_usd": 0.0
    }
  },
  {
    "signal_id": "congress",
    "zero": {
      "trades_dropped": 0,
      "pnl_dropped_usd": 0.0
    },
    "invert": {
      "trades_dropped": 0,
      "pnl_dropped_usd": 0.0
    }
  },
  {
    "signal_id": "dark_pool",
    "zero": {
      "trades_dropped": 1497,
      "pnl_dropped_usd": 7929.71
    },
    "invert": {
      "trades_dropped": 2353,
      "pnl_dropped_usd": 11650.27
    }
  },
  {
    "signal_id": "etf_flow",
    "zero": {
      "trades_dropped": 221,
      "pnl_dropped_usd": -871.46
    },
    "invert": {
      "trades_dropped": 957,
      "pnl_dropped_usd": 6407.87
    }
  },
  {
    "signal_id": "event",
    "zero": {
      "trades_dropped": 1649,
      "pnl_dropped_usd": 9136.83
    },
    "invert": {
      "trades_dropped": 3533,
      "pnl_dropped_usd": 8967.52
    }
  },
  {
    "signal_id": "flow",
    "zero": {
      "trades_dropped": 10715,
      "pnl_dropped_usd": 18811.44
    },
    "invert": {
      "trades_dropped": 10715,
      "pnl_dropped_usd": 18811.44
    }
  },
  {
    "signal_id": "freshness_factor",
    "zero": {
      "trades_dropped": 6253,
      "pnl_dropped_usd": 10910.45
    },
    "invert": {
      "trades_dropped": 10715,
      "pnl_dropped_usd": 18811.44
    }
  },
  {
    "signal_id": "ftd_pressure",
    "zero": {
      "trades_dropped": 221,
      "pnl_dropped_usd": -871.46
    },
    "invert": {
      "trades_dropped": 957,
      "pnl_dropped_usd": 6407.87
    }
  },
  {
    "signal_id": "greeks_gamma",
    "zero": {
      "trades_dropped": 854,
      "pnl_dropped_usd": 5704.8
    },
    "invert": {
      "trades_dropped": 1236,
      "pnl_dropped_usd": 7135.04
    }
  },
  {
    "signal_id": "insider",
    "zero": {
      "trades_dropped": 973,
      "pnl_dropped_usd": 6215.73
    },
    "invert": {
      "trades_dropped": 1482,
      "pnl_dropped_usd": 7800.06
    }
  }
]

Execution sensitivity (0x vs 2x) if available:
exec_sensitivity.json missing

Exit sweep summary (MFE/MAE) if available:
{
  "status": "stub",
  "runs": []
}

Multi-model verdict and evidence:
multi_model/board_verdict.md missing

Plugins manifest:
no_plugins

Customer advocate summary (first 40 lines):
# Customer advocate

## Verdict
Run shows positive PnL.

## Metrics
Net PnL: 18811.44, Win rate: 51.18, Trades: 10715

## Levers

NEXT_STEPS (first 40 lines):
NEXT STEPS
1. Review attribution/per_signal_pnl.json and ablation/ablation_summary.json.
2. Confirm exec_sensitivity shows acceptable degradation at 2x slippage.
3. Inspect exit_sweep for MFE/MAE and choose exit rule candidate.
4. Review param_sweep/best_config.json and run walk-forward on top candidates.
5. Confirm multi_model/board_verdict.md endorses next action.
6. If all checks pass, create change_proposal.md with tuning overlay and run paper->canary on Monday.

Governance report path:

Summary written to reports/backtests/alpaca_monday_final_20260222T174120Z/cursor_quick_summary.md
Tail of orchestration log (last 200 lines):
'configs/overlays/paper_lock_overlay.json' -> 'reports/backtests/alpaca_monday_final_20260222T174120Z/patches/paper_lock_overlay.json'
Snapshot: data/snapshots/alpaca_1m_snapshot_20260222T174120Z.tar.gz
Provenance updated with snapshot
[SIMULATION BACKTEST] Done.
  Trades: 10715, Exits: 10715
  P&L: $18811.44, Win rate: 51.18%
  Wrote: reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/backtest_trades.jsonl, reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/backtest_exits.jsonl, reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/backtest_summary.json, reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/metrics.json, reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/trades.csv
postprocess complete
'reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/backtest_trades_pp.jsonl' -> 'reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/backtest_trades_diagnostic.jsonl'
Event studies (stub) -> reports/backtests/alpaca_monday_final_20260222T174120Z/event_studies
Per-signal attribution -> /root/stock-bot/reports/backtests/alpaca_monday_final_20260222T174120Z/attribution/per_signal_pnl.json (22 signals)
Wrote reports to /root/stock-bot/reports/backtests/alpaca_monday_final_20260222T174120Z/effectiveness
Wrote /root/stock-bot/reports/backtests/alpaca_monday_final_20260222T174120Z/customer_advocate.md
Ablation suite -> /root/stock-bot/reports/backtests/alpaca_monday_final_20260222T174120Z/ablation/ablation_summary.json
Traceback (most recent call last):
  File "/root/stock-bot/scripts/run_exec_sensitivity.py", line 82, in <module>
    sys.exit(main())
             ^^^^^^
  File "/root/stock-bot/scripts/run_exec_sensitivity.py", line 57, in main
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=600)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/subprocess.py", line 550, in run
    stdout, stderr = process.communicate(input, timeout=timeout)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/subprocess.py", line 1209, in communicate
    stdout, stderr = self._communicate(input, endtime, timeout)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/subprocess.py", line 2116, in _communicate
    self._check_timeout(endtime, orig_timeout, stdout, stderr)
  File "/usr/lib/python3.12/subprocess.py", line 1253, in _check_timeout
    raise TimeoutExpired(
subprocess.TimeoutExpired: Command '['/usr/bin/python3', 'scripts/run_simulation_backtest_on_droplet.py', '--bars', 'data/snapshots/alpaca_1m_snapshot_20260222T174120Z.tar.gz', '--config', '/tmp/tmpv3xf0eet.json', '--out', '/root/stock-bot/reports/backtests/alpaca_monday_final_20260222T174120Z/exec_sensitivity/slippage_0.0', '--lab-mode', '--min-exec-score', '1.8']' timed out after 600 seconds
Exit optimization (stub) -> reports/backtests/alpaca_monday_final_20260222T174120Z/exit_sweep
Param sweep (stub) -> reports/backtests/alpaca_monday_final_20260222T174120Z/param_sweep
Adversarial (stub) -> reports/backtests/alpaca_monday_final_20260222T174120Z/adversarial
Blocked-trade analysis -> /root/stock-bot/reports/backtests/alpaca_monday_final_20260222T174120Z/blocked_analysis/blocked_opportunity_summary.json
'data/uw_flow_cache.json' -> 'reports/backtests/alpaca_monday_final_20260222T174120Z/multi_model/evidence/uw_flow_cache.json'
'data/uw_expanded_intel.json' -> 'reports/backtests/alpaca_monday_final_20260222T174120Z/multi_model/evidence/uw_expanded_intel.json'
'reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/backtest_trades_diagnostic.jsonl' -> 'reports/backtests/alpaca_monday_final_20260222T174120Z/multi_model/evidence/backtest_trades.jsonl'
'reports/backtests/alpaca_monday_final_20260222T174120Z/baseline/backtest_summary.json' -> 'reports/backtests/alpaca_monday_final_20260222T174120Z/multi_model/evidence/backtest_summary.json'
usage: multi_model_runner.py [-h] --backtest_dir BACKTEST_DIR [--roles ROLES]
                             --out OUT [--evidence EVIDENCE]
multi_model_runner.py: error: the following arguments are required: --out
Wrote /root/stock-bot/reports/backtests/alpaca_monday_final_20260222T174120Z/summary/summary.md, /root/stock-bot/reports/backtests/alpaca_monday_final_20260222T174120Z/summary/metrics.json
Backtest governance: PASS
Run ID: alpaca_monday_final_20260222T174120Z
KEY_METRICS: {"gate_p10": null, "gate_p50": null, "gate_p90": null, "net_pnl": 18811.44, "trades_count": 10715}
DONE. Artifacts under reports/backtests/alpaca_monday_final_20260222T174120Z and reports/governance/alpaca_monday_final_20260222T174120Z
