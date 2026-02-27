# Expectancy gate fix — Restart proof

**Date:** 2026-02-18

## Git pull
- Exit code: 0
- HEAD: 539c5f902b2b
- Fix present (composite_exec_score + score_floor_breach): **True**
```
From https://github.com/mlevitan96-crypto/stock-bot
 * branch            main       -> FETCH_HEAD
   085537a..539c5f9  main       -> origin/main
Updating 085537a..539c5f9
Fast-forward
 main.py                                       | 16 +++++-
 reports/expectancy_gate_fix/plan_review.md    | 56 ++++++++++++++++++
 reports/expectancy_gate_fix/restart_proof.md  | 83 +++++++++++++++++++++++++++
 reports/expectancy_gate_fix/results_review.md | 35 +++++++++++
 reports/expectancy_gate_fix/score_trace.md    | 51 ++++++++++++++++
 reports/expectancy_gate_fix/unblock_proof.md  | 45 +++++++++++++++
 6 files changed, 283 insertions(+), 3 deletions(-)
 create mode 100644 reports/expectancy_gate_fix/plan_review.md
 create mode 100644 reports/expectancy_gate_fix/restart_proof.md
 create mode 100644 reports/expectancy_gate_fix/results_review.md
 create mode 100644 reports/expectancy_gate_fix/score_trace.md
 create mode 100644 reports/expectancy_gate_fix/unblock_proof.md

```

## Restart (no overlay, EXPECTANCY_DEBUG=1)
- Restart exit code: 0
- No GOVERNED_TUNING_CONFIG in state: **True**

## tmux ls
```
clawdbot: 1 windows (created Thu Jan 29 23:28:35 2026)
stock_bot_paper_run: 1 windows (created Wed Feb 18 19:31:50 2026)
trading: 1 windows (created Sat Dec 13 20:52:28 2025)
```

## tmux capture-pane (stock_bot_paper_run)
```
[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=
$150,000
2026-02-18 19:31:53,940 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
[MOCK-SIGNAL] Mock signal injection loop started (every 15 minutes)
[MAIN] Mock signal injection loop started
DEBUG: Worker loop STARTED (thread 123820983285440)
DEBUG: SIMULATE_MARKET_OPEN=False, stop_evt.is_set()=False
DEBUG: Worker loop iteration 1 (iter_count=0)
DEBUG WORKER: Starting iteration 1
DEBUG WORKER: About to check market status...
======================================================================
  STARTUP CONTRACT CHECK
======================================================================
✅ Composite scoring smoke test passed (score: 2.111)
✅ V2 components present in scoring output
DEBUG WORKER: is_market_open_now() returned: True
DEBUG WORKER: Market open check: True (SIMULATE_MARKET_OPEN=False)
DEBUG WORKER: After market check, market_open=True, about to check if block...
```

## state/live_paper_run_state.json
```
{
  "status": "live_paper_run_started",
  "timestamp": 1771443113,
  "details": {
    "trading_mode": "paper",
    "process": "python3 main.py",
    "session": "stock_bot_paper_run",
    "governed_tuning_config": ""
  }
}
```