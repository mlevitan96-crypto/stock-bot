# Post-REVERT restart — proof (2026-02-18)

## Multi-model review (restart plan)

| Lens | Note |
|------|------|
| **Adversarial** | Killing tmux is destructive; capture state first. Clearing state file is safe if we then restart; otherwise paper is stopped with no process. |
| **Quant** | Canonical source is state file; tmux command must match (no GOVERNED_TUNING_CONFIG). Re-run effectiveness after deploy to get unclassified_pct. |
| **Product** | Restart without overlay restores baseline behavior; verification docs are the audit trail. |

---

## Step 1 — Current truth (before changes)

### git
```
1b1a218f77088179bb86bc2e3615493fd9c4458d
---
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   data/uw_flow_cache.json
	modified:   profiles.json

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	backtests/30d_after_intel_overhaul_20260214_204538/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3b_20260214_213034/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3c_20260215_002515/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3d_20260215_003157/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3d_20260215_004825/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3e_20260215_010031/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3f_20260215_153119/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3g_20260215_155617/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3g_20260215_155714/
	backtests/30d_after_signal_engine_block3g_20260215_160826/
	backtests/30d_after_signal_engine_block3g_20260215_185932/
	backtests/30d_after_signal_engine_block3g_20260215_232007/
	backtests/30d_after_signal_engine_block3g_20260215_232934/
	backtests/30d_after_signal_engine_block3g_20260216_032942/
	backtests/30d_after_signal_engine_block3g_20260218_002100/backtest_run_summary.json
	backtests/30d_after_signal_engine_scaffolding_20260214_211701/backtest_run_summary.json
	backtests/30d_after_signal_overhaul_20260214_210246/backtest_run_summary.json
	backtests/30d_after_signal_overhaul_block2_20260214_210746/backtest_run_summary.json
	backtests/30d_baseline_20260218_032951/backtest_run_summary.json
	backtests/30d_proposed_20260218_032957/backtest_run_summary.json
	backtests/30d_tune_baseline_20260218_040651/backtest_run_summary.json
	backtests/30d_tune_baseline_20260218_040651/effectiveness/
	backtests/30d_tune_flow022_20260218_040706/backtest_run_summary.json
	backtests/30d_tune_score028_20260218_040930/backtest_run_summary.json
	config/tuning/
	reports/daily_report_2026-02-17.json
	reports/dashboard_audits/2026-02-14/
	reports/dashboard_audits/2026-02-15/
	reports/dashboard_audits/2026-02-16/
	reports/dashboard_audits/2026-02-17/
	reports/dashboard_audits/2026-02-18/
	reports/effectiveness_baseline_blame/
	reports/effectiveness_baseline_blame_v2/
	reports/effectiveness_from_logs_2026-02-18/
	reports/effectiveness_paper_score028_current/
	reports/effectiveness_paper_score028_gate50/
	reports/report_2026-02-14.html
	reports/report_2026-02-14.json
	reports/report_2026-02-15.html
	reports/report_2026-02-15.json
	reports/report_2026-02-16.html
	reports/report_2026-02-16.json
	reports/report_2026-02-17.html
	reports/report_2026-02-17.json
	reports/report_2026-02-18.html
	reports/report_2026-02-18.json
	reports/wheel_actions_2026-02-13.json
	reports/wheel_actions_2026-02-17.json
	reports/wheel_daily_review_2026-02-13.md
	reports/wheel_daily_review_2026-02-17.md
	reports/wheel_governance_badge_2026-02-13.json
	reports/wheel_governance_badge_2026-02-17.json
	reports/wheel_watchlists_2026-02-13.json
	reports/wheel_watchlists_2026-02-17.json
	scripts/analysis/
	scripts/governance/

no changes added to commit (use "git add" and/or "git commit -a")
```

### state/live_paper_run_state.json
```json
{
  "status": "live_paper_run_started",
  "timestamp": 1771431099,
  "details": {
    "trading_mode": "paper",
    "process": "python3 main.py",
    "session": "stock_bot_paper_run",
    "governed_tuning_config": "config/tuning/overlays/exit_score_weight_tune.json"
  }
}
```

### tmux ls
```
clawdbot: 1 windows (created Thu Jan 29 23:28:35 2026)
stock_bot_paper_run: 1 windows (created Fri Feb 13 02:27:03 2026)
trading: 1 windows (created Sat Dec 13 20:52:28 2025)
```

### tmux command / pane (stock_bot_paper_run)
```
"cd /root/stock-bot-current 2>/dev/null || cd /root/trading-bot-current 2>/dev/null || cd /root/stock-bot; LOG_LEVEL=INFO python3 main.py"
```

### GOVERNED_TUNING_CONFIG in state?
```
8:    "governed_tuning_config": "config/tuning/overlays/exit_score_weight_tune.json"
8:    "governed_tuning_config": "config/tuning/overlays/exit_score_weight_tune.json"
```

## Step 2 — Hard stop

Killed session `stock_bot_paper_run`. After: `tmux ls`:
```
clawdbot: 1 windows (created Thu Jan 29 23:28:35 2026)
trading: 1 windows (created Sat Dec 13 20:52:28 2025)
```

## Step 3 — State cleared (no overlay)

Ran Python one-liner to set `details.governed_tuning_config = ""`. (If the captured snapshot below still shows the old path, the clear may have run in a different cwd; Step 4’s state_py definitively writes empty overlay next.)

## Step 4 — Restart paper (no overlay)

Command: git pull, EOD sanity, kill tmux, start tmux with `LOG_LEVEL=INFO python3 main.py` (no GOVERNED_TUNING_CONFIG), write state with governed_tuning_config=''.
Exit code: 0

### stdout
```
1) Git
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   data/uw_flow_cache.json
	modified:   profiles.json

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	backtests/30d_after_intel_overhaul_20260214_204538/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3b_20260214_213034/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3c_20260215_002515/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3d_20260215_003157/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3d_20260215_004825/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3e_20260215_010031/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3f_20260215_153119/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3g_20260215_155617/backtest_run_summary.json
	backtests/30d_after_signal_engine_block3g_20260215_155714/
	backtests/30d_after_signal_engine_block3g_20260215_160826/
	backtests/30d_after_signal_engine_block3g_20260215_185932/
	backtests/30d_after_signal_engine_block3g_20260215_232007/
	backtests/30d_after_signal_engine_block3g_20260215_232934/
	backtests/30d_after_signal_engine_block3g_20260216_032942/
	backtests/30d_after_signal_engine_block3g_20260218_002100/backtest_run_summary.json
	backtests/30d_after_signal_engine_scaffolding_20260214_211701/backtest_run_summary.json
	backtests/30d_after_signal_overhaul_20260214_210246/backtest_run_summary.json
	backtests/30d_after_signal_overhaul_block2_20260214_210746/backtest_run_summary.json
	backtests/30d_baseline_20260218_032951/backtest_run_summary.json
	backtests/30d_proposed_20260218_032957/backtest_run_summary.json
	backtests/30d_tune_baseline_20260218_040651/backtest_run_summary.json
	backtests/30d_tune_baseline_20260218_040651/effectiveness/
	backtests/30d_tune_flow022_20260218_040706/backtest_run_summary.json
	backtests/30d_tune_score028_20260218_040930/backtest_run_summary.json
	config/tuning/
	reports/daily_report_2026-02-17.json
	reports/dashboard_audits/2026-02-14/
	reports/dashboard_audits/2026-02-15/
	reports/dashboard_audits/2026-02-16/
	reports/dashboard_audits/2026-02-17/
	reports/dashboard_audits/2026-02-18/
	reports/effectiveness_baseline_blame/
	reports/effectiveness_baseline_blame_v2/
	reports/effectiveness_from_logs_2026-02-18/
	reports/effectiveness_paper_score028_current/
	reports/effectiveness_paper_score028_gate50/
	reports/report_2026-02-14.html
	reports/report_2026-02-14.json
	reports/report_2026-02-15.html
	reports/report_2026-02-15.json
	reports/report_2026-02-16.html
	reports/report_2026-02-16.json
	reports/report_2026-02-17.html
	reports/report_2026-02-17.json
	reports/report_2026-02-18.html
	reports/report_2026-02-18.json
	reports/wheel_actions_2026-02-13.json
	reports/wheel_actions_2026-02-17.json
	reports/wheel_daily_review_2026-02-13.md
	reports/wheel_daily_review_2026-02-17.md
	reports/wheel_governance_badge_2026-02-13.json
	reports/wheel_governance_badge_2026-02-17.json
	reports/wheel_watchlists_2026-02-13.json
	reports/wheel_watchlists_2026-02-17.json
	scripts/analysis/
	scripts/governance/

no changes added to commit (use "git add" and/or "git commit -a")
main
4) Start tmux (no overlay)
5) Verify
clawdbot: 1 windows (created Thu Jan 29 23:28:35 2026)
stock_bot_paper_run: 1 windows (created Wed Feb 18 17:25:11 2026)
trading: 1 windows (created Sat Dec 13 20:52:28 2025)
6) State
live_paper_run_state.json written
DONE
```

### stderr
```
error: cannot pull with rebase: You have unstaged changes.
error: Please commit or stash them.
```

### After successful start: state
```json
{
  "status": "live_paper_run_started",
  "timestamp": 1771435516,
  "details": {
    "trading_mode": "paper",
    "process": "python3 main.py",
    "session": "stock_bot_paper_run",
    "governed_tuning_config": ""
  }
}
```

### tmux ls
```
clawdbot: 1 windows (created Thu Jan 29 23:28:35 2026)
stock_bot_paper_run: 1 windows (created Wed Feb 18 17:25:11 2026)
trading: 1 windows (created Sat Dec 13 20:52:28 2025)
```

### tmux pane (last 50 lines) — confirm no GOVERNED_TUNING_CONFIG
```
✅ V2 components present in scoring output
DEBUG WORKER: is_market_open_now() returned: True
DEBUG WORKER: Market open check: True (SIMULATE_MARKET_OPEN=False)
DEBUG WORKER: After market check, market_open=True, about to check if block...
DEBUG: Market is OPEN - calling run_once()
✅ Live cache smoke test passed (AAPL: 8.000)

----------------------------------------------------------------------
⚠️   Warnings (1):
   Contract validator not available: No module named 'internal_contract_validato
r'

======================================================================
  ✅ STARTUP CHECK PASSED - READY TO TRADE
======================================================================
✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $98,150.04, Equity: $49,661.
65
WARNING NIO: Position reconciled with entry_score=0.00 - this should never happe
n
2026-02-18 17:25:15,681 [CACHE-ENRICH] INFO: State loaded successfully: 8 positi
ons
2026-02-18 17:25:15,707 [CACHE-ENRICH] WARNING: Positions in local state but not
 in Alpaca: {'XLE', 'NFLX', 'GOOGL', 'XOM', 'F', 'COIN', 'XLK', 'AMD'}
2026-02-18 17:25:15,714 [CACHE-ENRICH] WARNING: Positions in Alpaca but not in l
ocal state: {'NIO'}
2026-02-18 17:25:15,721 [CACHE-ENRICH] INFO: Reconciliation complete: 1 position
s from Alpaca
DEBUG: About to call run_once() - entering try block
DEBUG: run_once() ENTRY
/root/stock-bot/main.py:9752: DeprecationWarning: datetime.datetime.utcnow() is
deprecated and scheduled for removal in a future version. Use timezone-aware obj
ects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  "ts": datetime.utcnow().isoformat() + "Z"
/root/stock-bot/main.py:13207: DeprecationWarning: datetime.datetime.utcnow() is
 deprecated and scheduled for removal in a future version. Use timezone-aware ob
jects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  "entry_ts": datetime.utcnow().isoformat() + "Z",  # Unknown exact time
/root/stock-bot/main.py:13229: DeprecationWarning: datetime.datetime.utcnow() is
 deprecated and scheduled for removal in a future version. Use timezone-aware ob
jects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  reconcile_event["_dt"] = datetime.utcnow().isoformat() + "Z"
/root/stock-bot/main.py:13243: DeprecationWarning: datetime.datetime.utcnow() is
 deprecated and scheduled for removal in a future version. Use timezone-aware ob
jects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  "timestamp": datetime.utcnow().isoformat()
CRITICAL: Exit checker thread STARTED
CRITICAL: Exit checker thread started
Starting Flask server on port 8080...
 * Serving Flask app 'main'
 * Debug mode: off
✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $98,150.04, Equity: $49,661.
65
2026-02-18 17:25:17,010 [CACHE-ENRICH] INFO: WARNING: This is a development serv
er. Do not use it in a production deployment. Use a production WSGI server inste
ad.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8080
 * Running on http://104.236.102.57:8080
2026-02-18 17:25:17,022 [CACHE-ENRICH] INFO: Press CTRL+C to quit
2026-02-18 17:25:17,524 [CACHE-ENRICH] INFO: State loaded successfully: 8 positi
ons
2026-02-18 17:25:17,549 [CACHE-ENRICH] WARNING: Positions in local state but not
 in Alpaca: {'XLE', 'NFLX', 'GOOGL', 'XOM', 'F', 'COIN', 'XLK', 'AMD'}
2026-02-18 17:25:17,556 [CACHE-ENRICH] WARNING: Positions in Alpaca but not in l
ocal state: {'NIO'}
2026-02-18 17:25:17,556 [CACHE-ENRICH] INFO: Reconciliation complete: 1 position
s from Alpaca
WARNING: hmmlearn not installed. Regime detection will use fallback method.
2026-02-18 17:25:18,409 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with
 computed signals
2026-02-18 17:25:18,409 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbo
ls
DEBUG: Running autonomous position reconciliation V2...
```

## Step 5 — Deploy + baseline v2

### git pull
```
From https://github.com/mlevitan96-crypto/stock-bot
 * branch            main       -> FETCH_HEAD
Already up to date.
```

Effectiveness exit code: 0
```
Wrote reports to /root/stock-bot/reports/effectiveness_baseline_blame_v2
```
